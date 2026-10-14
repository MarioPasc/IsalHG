"""Decoders that turn every arm back into a labelled hypergraph (losslessness evidence).

These are verification helpers, not part of the measured pipeline: for a sample of
members the tests decode each arm's symbol sequence and check that the result is
isomorphic to the original (coloured Levi graph, absolute labels).
"""

from __future__ import annotations

import struct
from collections.abc import Sequence
from typing import Any

from isalhg.core.fact_word import decode_fact_word
from isalhg.core.instructions import (
    Token,
    TokenC,
    TokenN,
    TokenP,
    TokenV,
    TokenW,
    serialize,
)
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.core.string_to_hypergraph import string_to_hypergraph
from isalhg.generation.incidence_baseline import strict_decode
from scripts.newpos.compression.serialize import SEP, CollectionInfo, CompressionError

Rows = tuple[tuple[int, ...], ...]


def bytes_to_rows(cert: bytes) -> Rows:
    """Invert ``nauty_certificate_bytes``: colour signature + 64-bit-word adjacency bit matrix.

    Positions are grouped into colour cells in increasing colour order (the ordered
    partition handed to nauty); bit ``j`` of row ``i`` is the MSB-first bit ``j`` of
    the little-endian 64-bit words.
    """
    count = struct.unpack(">I", cert[:4])[0]
    profile = [struct.unpack(">II", cert[4 + 8 * i : 12 + 8 * i]) for i in range(count)]
    colours = [c for c, size in profile for _ in range(size)]
    n = len(colours)
    words = (n + 63) // 64
    body = cert[4 + 8 * count :]
    if len(body) != n * words * 8:
        raise CompressionError(f"certificate body has {len(body)} bytes, expected {n * words * 8}")
    rows: list[tuple[int, ...]] = []
    for i in range(n):
        neighbours = []
        for j in range(n):
            word = int.from_bytes(
                body[(i * words + j // 64) * 8 : (i * words + j // 64 + 1) * 8], "little"
            )
            if (word >> (63 - j % 64)) & 1:
                neighbours.append(j)
        rows.append((colours[i], *neighbours))
    return tuple(rows)


def u32_to_bytes(words: Sequence[int]) -> bytes:
    """Invert the 4-byte big-endian grouping of ``cert_u32``."""
    return struct.pack(f">{len(words)}I", *words)


def ints_to_rows(ints: Sequence[int]) -> Rows:
    """Invert ``cert_ints`` (rows terminated by ``SEP``)."""
    rows: list[tuple[int, ...]] = []
    current: list[int] = []
    for value in ints:
        if value == SEP:
            rows.append(tuple(current))
            current = []
        else:
            current.append(value)
    if current:
        raise CompressionError("cert_ints does not end with a separator")
    return tuple(rows)


def ints_ut_to_rows(symbols: Sequence[tuple[str, int]]) -> Rows:
    """Invert ``cert_ints_ut`` by mirroring every upper-triangle neighbour."""
    colours: list[int] = []
    upper: list[list[int]] = []
    for slot, value in symbols:
        if slot == "c":
            colours.append(value)
            upper.append([])
        else:
            upper[-1].append(value)
    adjacency: list[set[int]] = [set() for _ in colours]
    for position, neighbours in enumerate(upper):
        for q in neighbours:
            adjacency[position].add(q)
            adjacency[q].add(position)
    return tuple((colours[i], *sorted(adjacency[i])) for i in range(len(colours)))


def rows_to_hypergraph(rows: Rows, n_v: int, n_e: int) -> SparseHypergraph:
    """Rebuild the labelled hypergraph from canonical Levi rows (colour first, then neighbours)."""
    constants = [i for i, row in enumerate(rows) if row[0] < n_v]
    facts = [i for i, row in enumerate(rows) if row[0] >= n_v]
    index = {pos: j for j, pos in enumerate(constants)}
    return SparseHypergraph(
        n_nodes=len(constants),
        hyperedges=[frozenset(index[q] for q in rows[p][1:]) for p in facts],
        n_vertex_labels=n_v,
        n_edge_labels=n_e,
        vertex_labels=[rows[p][0] for p in constants],
        edge_labels=[rows[p][0] - n_v for p in facts],
    )


def w_flat_to_tokens(
    symbols: Sequence[tuple[str, Any]], n_v: int, n_e: int
) -> tuple[int, list[Token]]:
    """Invert ``w_flat`` to ``(root label, tokens)``."""
    root = 0
    tokens: list[Token] = []
    pos = 0
    if symbols and symbols[0][0] == "s":
        root = symbols[0][1]
        pos = 1

    def take(slot: str) -> int:
        nonlocal pos
        got_slot, value = symbols[pos]
        if got_slot != slot:
            raise CompressionError(f"expected slot {slot!r}, found {got_slot!r}")
        pos += 1
        return int(value)

    while pos < len(symbols):
        op = symbols[pos][1]
        pos += 1
        if op == "W":
            tokens.append(TokenW())
        elif op in ("N", "P"):
            tokens.append((TokenN if op == "N" else TokenP)(i=take("i")))
        elif op == "C":
            le = take("le") if n_e > 1 else 0
            tokens.append(TokenC(edge_label=le, i=take("i")))
        elif op == "V":
            le = take("le") if n_e > 1 else 0
            i, j = take("i"), take("j")
            labels = tuple(take("ln") for _ in range(j)) if n_v > 1 else (0,) * j
            tokens.append(TokenV(edge_label=le, i=i, j=j, new_node_labels=labels))
        else:
            raise CompressionError(f"unknown op {op!r}")
    return root, tokens


def fact_flat_to_word(
    symbols: Sequence[tuple[str, Any]], n_v: int, n_e: int
) -> list[tuple[Any, ...]]:
    """Invert ``fact_flat`` to fact-word tokens (type prefix reconstructed when elided)."""
    word: list[tuple[Any, ...]] = []
    pos = 0
    while pos < len(symbols):
        op = symbols[pos][1]
        pos += 1
        if op == "T":
            word.append(("T", symbols[pos][1]))
            pos += 1
            continue
        pred = 0
        if n_e > 1:
            pred = symbols[pos][1]
            pos += 1
        ranks = []
        while pos < len(symbols) and symbols[pos][0] == "rk":
            ranks.append(symbols[pos][1])
            pos += 1
        word.append(("F", pred, tuple(ranks)))
    if n_v == 1:
        n = 1 + max(r for tok in word for r in tok[2])
        word = [("T", 0)] * n + word
    return word


def decode_arm(arm: str, seq: Sequence[Any], info: CollectionInfo) -> SparseHypergraph:
    """Decode the symbol sequence of ``arm`` into a labelled hypergraph.

    Raises
    ------
    CompressionError
        If the sequence is not decodable.
    """
    n_v, n_e, k = info.n_v, info.n_e, info.k
    if arm in ("w_o", "w_flat"):
        if arm == "w_o":
            root = seq[0][1] if seq and isinstance(seq[0], tuple) else 0
            tokens = [s for s in seq if not isinstance(s, tuple)]
        else:
            root, tokens = w_flat_to_tokens(seq, n_v, n_e)
        return string_to_hypergraph(
            serialize(tokens), k=k, n_vertex_labels=n_v, n_edge_labels=n_e, seed_label=root
        )
    if arm in ("cert_bytes", "cert_u32", "cert_rows", "cert_ints", "cert_ints_ut"):
        if arm == "cert_bytes":
            rows = bytes_to_rows(bytes(seq))
        elif arm == "cert_u32":
            rows = bytes_to_rows(u32_to_bytes(seq))
        elif arm == "cert_rows":
            rows = tuple(tuple(r) for r in seq)
        elif arm == "cert_ints":
            rows = ints_to_rows(seq)
        else:
            rows = ints_ut_to_rows(seq)
        return rows_to_hypergraph(rows, n_v, n_e)
    if arm in ("fact", "fact_noT", "fact_flat"):
        word = fact_flat_to_word(seq, n_v, n_e) if arm == "fact_flat" else list(seq)
        if arm == "fact_noT":
            n = 1 + max(r for tok in word for r in tok[2])
            word = [("T", 0)] * n + word
        return decode_fact_word(word, n_types=n_v, n_preds=n_e)[0]
    if arm in ("incid", "incid_noT"):
        tokens = list(seq)
        if arm == "incid_noT":
            n = 1 + max(tok[1] for tok in tokens if tok[0] == "C")
            tokens = [("N", n), *[("T", 0)] * n, *tokens]
        decoded = strict_decode(tokens, n_types=n_v, n_preds=n_e)
        if decoded is None:
            raise CompressionError("incidence list rejected by the strict decoder")
        return decoded
    raise CompressionError(f"unknown arm {arm!r}")
