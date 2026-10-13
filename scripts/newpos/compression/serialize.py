"""Serializations of a labelled knowledge base as per-arm symbol sequences.

One function, :func:`encode_member`, maps a connected labelled hypergraph to the
symbol sequence of every *arm* of the description-length experiment. The five
arms the experiment is specified on are the exact sequences the registered
distances compare (``w_o`` = ``isal_ow_struct``, ``cert_bytes`` = ``nauty_cert``,
``cert_rows`` = ``nauty_cert_rows``, ``fact`` = ``fact_rank``) plus the
incidence list ``flatten``. The remaining arms are the "best honest rendering"
supplements: other granularities of the certificate (``cert_u32``, ``cert_ints``,
``cert_ints_ut``), type-elided fact/incidence lists on trivial type vocabularies
(``fact_noT``, ``incid_noT``) and field-level slot-tagged streams (``w_flat``,
``fact_flat``).

A *slot-tagged* arm writes each symbol as ``(slot, value)``; the slot names the
grammar field the value fills, so a fixed-width coder can charge ``log2`` of the
slot's own alphabet (:func:`fixed_width_bits`). Every other arm is single-slot.

Completeness (each arm is a lossless code of the labelled isomorphism class):
``w_o`` by Theorem C; ``cert_*`` by the colour signature plus the canonical
certificate (rows carry the colour); ``fact`` by the injective canonical
addressing of :func:`isalhg.iso_backends.canonical_order.canonical_ranks`;
``incid`` carries the whole labelled hypergraph under that same canonical labelling.
"""

from __future__ import annotations

import math
import struct
from collections.abc import Hashable, Sequence
from dataclasses import dataclass
from math import comb
from typing import Any

from isalhg.core.instructions import (
    Token,
    TokenC,
    TokenN,
    TokenP,
    TokenV,
    TokenW,
    serialize,
)
from isalhg.core.sparse_hypergraph import SparseHypergraph, permute
from isalhg.generation.incidence_baseline import flatten
from isalhg.iso_backends.canonical_order import (
    canonical_ranks,
    nauty_certificate_bytes,
    nauty_certificate_rows,
)
from isalhg.iso_backends.isal_ordered import ordered_symbols
from isalhg.metric_space.distances.fact_levenshtein import fact_word

Symbol = Hashable
SEP = -1
SINGLE_SLOT = "_"

#: Arms in reporting order. The first six are the pre-registered primary set.
ARMS: tuple[str, ...] = (
    "w_o",
    "cert_bytes",
    "cert_rows",
    "cert_ints",
    "fact",
    "incid",
    "cert_u32",
    "cert_ints_ut",
    "fact_noT",
    "incid_noT",
    "w_flat",
    "fact_flat",
)

#: Arms that exist only on a trivial vertex (type) vocabulary.
TRIVIAL_TYPES_ONLY: frozenset[str] = frozenset({"fact_noT", "incid_noT"})

#: Arms written as ``(slot, value)`` symbols, with the slot(s) that may start a token.
SLOTTED_HEADS: dict[str, tuple[str, ...]] = {
    "w_flat": ("op",),
    "fact_flat": ("op",),
    "cert_ints_ut": ("c",),
}

#: Arms whose bytes form a self-delimiting stream (length fixed by the signature).
BINARY_ARMS: frozenset[str] = frozenset({"cert_bytes", "cert_u32"})

FACT_BINS: tuple[tuple[str, int, int], ...] = (
    ("m=3", 3, 3),
    ("m=4-5", 4, 5),
    ("m=6-8", 6, 8),
    ("m=9-12", 9, 12),
    ("m>=13", 13, 10**9),
)


class CompressionError(Exception):
    """Root of the description-length experiment's error hierarchy."""


@dataclass(frozen=True)
class CollectionInfo:
    """Collection-scoped constants the alphabets depend on.

    Attributes
    ----------
    name : str
        Collection name.
    k : int
        Pointer count / arity cap (``k_max`` of the collection).
    n_v, n_e : int
        Type and predicate vocabulary sizes.
    n_max : int
        Largest constant count over the members.
    big_n_max : int
        Largest Levi node count ``n + m`` over the members.
    """

    name: str
    k: int
    n_v: int
    n_e: int
    n_max: int
    big_n_max: int


def arm_available(arm: str, n_v: int) -> bool:
    """Whether ``arm`` is defined for a collection with ``n_v`` vertex labels."""
    return not (arm in TRIVIAL_TYPES_ONLY and n_v > 1)


def is_slotted(arm: str) -> bool:
    """Whether the symbols of ``arm`` are ``(slot, value)`` pairs."""
    return arm in SLOTTED_HEADS


def head_slots(arm: str) -> tuple[str, ...]:
    """Slots that may begin a token of ``arm`` (the end marker competes there)."""
    return SLOTTED_HEADS.get(arm, (SINGLE_SLOT,))


def slot_of(arm: str, symbol: Symbol) -> str:
    """The grammar slot ``symbol`` fills."""
    if is_slotted(arm):
        return str(symbol[0])  # type: ignore[index]
    return SINGLE_SLOT


# ---------------------------------------------------------------------------
# Strata
# ---------------------------------------------------------------------------


def is_star(H: SparseHypergraph) -> bool:
    """True iff one constant lies in every fact and every other constant lies in exactly one.

    ``m == 1`` is a star by convention (nothing can lie in two facts).
    """
    m = H.n_edges
    degrees = sorted((H.degree(v) for v in range(H.n_nodes)), reverse=True)
    if m <= 1:
        return True
    return degrees[0] == m and all(d == 1 for d in degrees[1:])


def fact_bin(m: int) -> str:
    """Label of the fact-count bin of ``m``."""
    for label, low, high in FACT_BINS:
        if low <= m <= high:
            return label
    return FACT_BINS[0][0]


# ---------------------------------------------------------------------------
# Arm encoders
# ---------------------------------------------------------------------------


def _w_flat(symbols: Sequence[Any], n_v: int, n_e: int) -> tuple[Symbol, ...]:
    """Field-level stream of the ordered walk; singleton-valued label fields are elided."""
    out: list[Symbol] = []
    for sym in symbols:
        if isinstance(sym, tuple):  # ("seed", root label)
            out.append(("s", sym[1]))
        elif isinstance(sym, TokenW):
            out.append(("op", "W"))
        elif isinstance(sym, (TokenN, TokenP)):
            out.extend((("op", "N" if isinstance(sym, TokenN) else "P"), ("i", sym.i)))
        elif isinstance(sym, TokenC):
            out.append(("op", "C"))
            if n_e > 1:
                out.append(("le", sym.edge_label))
            out.append(("i", sym.i))
        elif isinstance(sym, TokenV):
            out.append(("op", "V"))
            if n_e > 1:
                out.append(("le", sym.edge_label))
            out.extend((("i", sym.i), ("j", sym.j)))
            if n_v > 1:
                out.extend(("ln", label) for label in sym.new_node_labels)
        else:
            raise CompressionError(f"unknown ordered-walk symbol {sym!r}")
    return tuple(out)


def _fact_flat(word: Sequence[tuple[Any, ...]], n_v: int, n_e: int) -> tuple[Symbol, ...]:
    """Field-level canonical incidence list; the type prefix is dropped on trivial vocabularies."""
    out: list[Symbol] = []
    for tok in word:
        if tok[0] == "T":
            if n_v > 1:
                out.extend((("op", "T"), ("ty", tok[1])))
            continue
        out.append(("op", "F"))
        if n_e > 1:
            out.append(("pr", tok[1]))
        out.extend(("rk", r) for r in tok[2])
    return tuple(out)


def _cert_ints(rows: Sequence[tuple[int, ...]]) -> tuple[int, ...]:
    """Rows flattened to ``colour, neighbours..., SEP`` per Levi node."""
    out: list[int] = []
    for row in rows:
        out.extend(row)
        out.append(SEP)
    return tuple(out)


def _cert_ints_ut(rows: Sequence[tuple[int, ...]]) -> tuple[Symbol, ...]:
    """Slot-tagged rows keeping each neighbour once (positions above the row's own)."""
    out: list[Symbol] = []
    for position, row in enumerate(rows):
        out.append(("c", row[0]))
        out.extend(("p", q) for q in row[1:] if q > position)
    return tuple(out)


def _cert_u32(cert: bytes) -> tuple[int, ...]:
    """The certificate bytes read as 4-byte big-endian words."""
    if len(cert) % 4:
        raise CompressionError(f"certificate length {len(cert)} is not a multiple of 4")
    return struct.unpack(f">{len(cert) // 4}I", cert)


def canonical_incidence_hypergraph(H: SparseHypergraph) -> SparseHypergraph:
    """Relabel ``H`` by canonical rank and insert its facts sorted by ``(predicate, operands)``.

    ``flatten`` of the result is a function of the isomorphism class: the
    canonical addressing is the one of the fact word, and the fact order is the
    fact word's own sort key.
    """
    ranks = canonical_ranks(H)
    relabelled = permute(H, ranks)
    facts = sorted((label, tuple(sorted(members))) for _, members, label in relabelled.iter_edges())
    return SparseHypergraph(
        n_nodes=relabelled.n_nodes,
        hyperedges=[frozenset(members) for _, members in facts],
        n_vertex_labels=relabelled.n_vertex_labels,
        n_edge_labels=relabelled.n_edge_labels,
        vertex_labels=[relabelled.vertex_label(v) for v in range(relabelled.n_nodes)],
        edge_labels=[label for label, _ in facts],
    )


def encode_member(H: SparseHypergraph, arms: Sequence[str] = ARMS) -> dict[str, tuple[Symbol, ...]]:
    """Return the symbol sequence of every requested arm for one knowledge base.

    Parameters
    ----------
    H : SparseHypergraph
        A connected labelled hypergraph (vertex label = type, edge label = predicate).
    arms : Sequence[str], optional
        Arms to compute; arms undefined for ``H``'s vocabulary are skipped.

    Returns
    -------
    dict[str, tuple[Hashable, ...]]
        Arm name to symbol sequence.

    Raises
    ------
    CompressionError
        If an arm name is unknown.
    """
    unknown = set(arms) - set(ARMS)
    if unknown:
        raise CompressionError(f"unknown arms {sorted(unknown)}")
    n_v, n_e = H.n_vertex_labels, H.n_edge_labels
    wanted = [a for a in arms if arm_available(a, n_v)]
    out: dict[str, tuple[Symbol, ...]] = {}
    shared: dict[str, Any] = {}

    def need(key: str) -> Any:
        if key not in shared:
            shared[key] = {
                "w": lambda: ordered_symbols(H),
                "bytes": lambda: nauty_certificate_bytes(H),
                "rows": lambda: nauty_certificate_rows(H),
                "fact": lambda: fact_word(H),
                "incid": lambda: flatten(canonical_incidence_hypergraph(H)),
            }[key]()
        return shared[key]

    for arm in wanted:
        if arm == "w_o":
            out[arm] = tuple(need("w"))
        elif arm == "w_flat":
            out[arm] = _w_flat(need("w"), n_v, n_e)
        elif arm == "cert_bytes":
            out[arm] = tuple(need("bytes"))
        elif arm == "cert_u32":
            out[arm] = _cert_u32(need("bytes"))
        elif arm == "cert_rows":
            out[arm] = tuple(need("rows"))
        elif arm == "cert_ints":
            out[arm] = _cert_ints(need("rows"))
        elif arm == "cert_ints_ut":
            out[arm] = _cert_ints_ut(need("rows"))
        elif arm == "fact":
            out[arm] = tuple(need("fact"))
        elif arm == "fact_noT":
            out[arm] = tuple(tok for tok in need("fact") if tok[0] != "T")
        elif arm == "fact_flat":
            out[arm] = _fact_flat(need("fact"), n_v, n_e)
        elif arm == "incid":
            out[arm] = tuple(need("incid"))
        elif arm == "incid_noT":
            out[arm] = tuple(tok for tok in need("incid") if tok[0] not in ("N", "T"))
    return out


# ---------------------------------------------------------------------------
# Alphabets
# ---------------------------------------------------------------------------


def observed_alphabet(arm: str, sequences: Sequence[Sequence[Symbol]]) -> dict[str, int]:
    """Distinct symbols per slot over a collection (a single ``"_"`` slot for atomic arms)."""
    seen: dict[str, set[Symbol]] = {}
    for seq in sequences:
        for sym in seq:
            seen.setdefault(slot_of(arm, sym), set()).add(sym)
    return {slot: len(values) for slot, values in seen.items()}


def walk_alphabet_size(k: int, n_v: int, n_e: int) -> int:
    """``|Sigma_HG(k)|`` with labels, from the token grammar of ``core.instructions``.

    ``V[le; i; j; l_1..l_j]`` ranges over ``1 <= i, j <= k-1`` and ``2 <= i+j <= k``
    (so ``k - j`` values of ``i`` for each ``j``), ``n_e`` predicates and ``n_v**j``
    label tuples; ``C[le; i]`` has ``k * n_e`` forms; ``P_i`` and ``N_i`` have ``k``
    each; ``W`` is one symbol. The root-type ``("seed", t)`` symbols add ``n_v``
    when the vertex vocabulary is non-trivial.
    """
    v_forms = n_e * sum((k - j) * n_v**j for j in range(1, k))
    base = 1 + 2 * k + k * n_e + v_forms
    return base + (n_v if n_v > 1 else 0)


def theoretical_alphabet(arm: str, info: CollectionInfo) -> dict[str, int]:
    """Size of the full symbol range of ``arm`` per slot, given the collection's envelope.

    Sizes depend on the collection only through ``k``, the two vocabulary sizes,
    the largest constant count and the largest Levi graph (documented in the
    work log). ``cert_rows`` counts ``colour x 2**N_max`` adjacency rows.
    """
    k, n_v, n_e = info.k, info.n_v, info.n_e
    arity_sets = sum(comb(info.n_max, a) for a in range(2, k + 1))
    sizes: dict[str, dict[str, int]] = {
        "w_o": {SINGLE_SLOT: walk_alphabet_size(k, n_v, n_e)},
        "cert_bytes": {SINGLE_SLOT: 256},
        "cert_u32": {SINGLE_SLOT: 2**32},
        "cert_rows": {SINGLE_SLOT: (n_v + n_e) * 2**info.big_n_max},
        "cert_ints": {SINGLE_SLOT: max(n_v + n_e, info.big_n_max) + 1},
        "cert_ints_ut": {"c": n_v + n_e, "p": info.big_n_max},
        "fact": {SINGLE_SLOT: n_v + n_e * arity_sets},
        "fact_noT": {SINGLE_SLOT: n_e * arity_sets},
        "incid": {
            SINGLE_SLOT: info.n_max + n_v + 1 + n_e + info.n_max + 1,
        },
        "incid_noT": {SINGLE_SLOT: 1 + n_e + info.n_max + 1},
    }
    w_flat = {"op": 5, "i": k, "j": k - 1}
    if n_v > 1:
        w_flat.update({"s": n_v, "ln": n_v})
    if n_e > 1:
        w_flat["le"] = n_e
    fact_flat = {"op": 2 if n_v > 1 else 1, "rk": info.n_max}
    if n_v > 1:
        fact_flat["ty"] = n_v
    if n_e > 1:
        fact_flat["pr"] = n_e
    sizes["w_flat"] = w_flat
    sizes["fact_flat"] = fact_flat
    return sizes[arm]


def fixed_width_bits(
    arm: str,
    sequence: Sequence[Symbol],
    sizes: dict[str, int],
) -> float:
    """Fixed-width code length of ``sequence`` with the end marker, in bits.

    For a single-slot arm this is ``(L + 1) * log2(|A| + 1)``. For a slot-tagged
    arm every symbol is charged ``log2`` of its own slot's alphabet, the end
    marker competes in the head slot(s), so a head symbol is charged
    ``log2(|A_slot| + 1)`` and the end marker ``log2(|A_head| + 1)`` with ``A_head``
    the (first) head slot.

    Parameters
    ----------
    arm : str
        Arm name (decides slotting).
    sequence : Sequence[Hashable]
        Symbols of one knowledge base.
    sizes : dict[str, int]
        Slot alphabet sizes, observed or theoretical.

    Returns
    -------
    float
        Bits.
    """
    heads = set(head_slots(arm))
    first_head = head_slots(arm)[0]
    total = math.log2(sizes[first_head] + 1)
    for sym in sequence:
        slot = slot_of(arm, sym)
        total += math.log2(sizes[slot] + (1 if slot in heads else 0))
    return total


# ---------------------------------------------------------------------------
# Literal text (dictionary-free rendering for the generic compressors)
# ---------------------------------------------------------------------------


def _compact(value: Any) -> str:
    if isinstance(value, Token):
        return value.serialize()
    if isinstance(value, tuple):
        return ",".join(f"[{_compact(v)}]" if isinstance(v, tuple) else _compact(v) for v in value)
    return str(value)


def symbol_text(arm: str, symbol: Symbol) -> str:
    """Literal text of one symbol of ``arm``."""
    if is_slotted(arm):
        slot, value = symbol  # type: ignore[misc]
        return f"{slot}{value}"
    if arm == "w_o" and isinstance(symbol, tuple):
        return f"S{symbol[1]}"
    return _compact(symbol)


def literal_line(arm: str, sequence: Sequence[Symbol]) -> bytes | str:
    """Literal serialization of one knowledge base (no dictionary needed to read it).

    ``w_o`` uses the registered ``serialize`` of its tokens; the byte arms are the
    raw bytes (self-delimiting, so no separator); integer streams are
    space-separated; everything else is ``;``-separated.
    """
    if arm == "cert_bytes":
        return bytes(sequence)  # type: ignore[arg-type]
    if arm == "cert_u32":
        return struct.pack(f">{len(sequence)}I", *sequence)
    if arm == "cert_ints":
        return " ".join(str(s) for s in sequence)
    if arm == "w_o":
        seed = [f"S{s[1]}" for s in sequence if isinstance(s, tuple)]
        body = serialize([s for s in sequence if not isinstance(s, tuple)])  # type: ignore[arg-type]
        return ";".join([*seed, body]) if body else ";".join(seed)
    sep = " " if is_slotted(arm) else ";"
    return sep.join(symbol_text(arm, s) for s in sequence)
