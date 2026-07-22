"""Known-design seed catalog for Stratum A (T-M7a).

Exposes a curated set of named combinatorial designs and uniform hypergraph
families as a registered :class:`HypergraphDataset`.  Every entry is a
mathematically defined structure (not a random sample), which makes the
class labels interpretable and makes ARI/NMI against family labels a
meaningful signal (``REVIEW/DATA.md`` §2A, Gap 3 fix).

Families provided (arities 3–5, all connected):

  Arity 3
  -------
  STS7        : Fano plane STS(7) = PG(2,2)       n=7
  STS9        : Unique STS(9) = AG(2,3)            n=9
  STS13-A     : First iso-class of STS(13)         n=13
  STS13-B     : Second iso-class of STS(13)        n=13
  STS15-A     : STS(15) iso-class 0 (out of 80)   n=15  [slow]
  GQ22        : Generalised quadrangle GQ(2,2)     n=15
  LoosePath3  : Loose 3-uniform path, length 4     n=9
  TightPath3  : Tight 3-uniform path, length 4     n=6
  LooseCycle3 : Loose 3-uniform cycle, length 4    n=8
  TightCycle3 : Tight 3-uniform cycle, length 5    n=5
  Complete3-5 : Complete 3-uniform K_5^(3)         n=5

  Arity 4
  -------
  AG24        : Affine plane AG(2,4) over GF(4)    n=16
  PG23        : Projective plane PG(2,3) = S(2,4,13) n=13
  LoosePath4  : Loose 4-uniform path, length 3     n=10
  TightPath4  : Tight 4-uniform path, length 3     n=6
  LooseCycle4 : Loose 4-uniform cycle, length 4    n=12
  TightCycle4 : Tight 4-uniform cycle, length 5    n=5
  Complete4-6 : Complete 4-uniform K_6^(4)         n=6

  Arity 5
  -------
  PG24        : PG(2,4) = S(2,5,21)               n=21  [likely gates out]
  LoosePath5  : Loose 5-uniform path, length 3     n=13
  TightPath5  : Tight 5-uniform path, length 3     n=7
  TightCycle5 : Tight 5-uniform cycle, length 7    n=7
  Complete5-6 : Complete 5-uniform K_6^(5)         n=6

All designs are constructed from first principles or delegated to the
vendored STS catalog.  No randomness; deterministic across Python versions.

References
----------
- AG(2,4): affine plane over GF(4); Lam & van Lint, *Combinatorics*, 1978.
- PG(2,3): projective plane over GF(3); Beutelspacher & Rosenbaum, 1998.
- PG(2,4): projective plane over GF(4) = S(2,5,21); same reference.
- GQ(2,2): Sylvester 1861; Payne & Thas 1984.
- STS catalog: Kaski & Ostergård, Math. Comp. 73, 2004.
- Complete/path/cycle uniform families: Berge, *Hypergraphs*, 1989.
"""

from __future__ import annotations

import itertools
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.datasets.base import HypergraphDataset
from isalhg.datasets.registry import register_dataset
from isalhg.datasets.schemas import DatasetItem, DatasetMetadata, LabelVocabulary, RealizedParams
from isalhg.datasets.synthetic.designs import fano_plane, gq_2_2_doily, sts_9
from isalhg.datasets.synthetic.sts_catalog import steiner_triple_system
from isalhg.types import DatasetName, Seed

# ---------------------------------------------------------------------------
# GF(4) arithmetic (for AG(2,4) and PG(2,4))
# ---------------------------------------------------------------------------
# GF(4) = GF(2)[x]/(x^2+x+1).  Elements: 0, 1, α, α+1 encoded as 0,1,2,3.
# α^2 = α+1 in this field; addition is XOR of the 2-bit representation.

_GF4_ADD: list[list[int]] = [
    [0, 1, 2, 3],
    [1, 0, 3, 2],
    [2, 3, 0, 1],
    [3, 2, 1, 0],
]

# Multiplication: 1*a=a, α*α=α+1, α*(α+1)=1, (α+1)*(α+1)=α
_GF4_MUL: list[list[int]] = [
    [0, 0, 0, 0],
    [0, 1, 2, 3],
    [0, 2, 3, 1],
    [0, 3, 1, 2],
]


def _gf4_add(a: int, b: int) -> int:
    return _GF4_ADD[a][b]


def _gf4_mul(a: int, b: int) -> int:
    return _GF4_MUL[a][b]


# ---------------------------------------------------------------------------
# GF(3) arithmetic (for PG(2,3))
# ---------------------------------------------------------------------------
# Standard mod-3 arithmetic.


def _gf3_add(a: int, b: int) -> int:
    return (a + b) % 3


def _gf3_mul(a: int, b: int) -> int:
    return (a * b) % 3


# ---------------------------------------------------------------------------
# Design builders
# ---------------------------------------------------------------------------


def affine_plane_ag24() -> SparseHypergraph:
    """Affine plane AG(2,4) over GF(4).

    Returns
    -------
    SparseHypergraph
        16 points (GF(4)^2), 20 lines of size 4, 4-uniform.
        Every pair of distinct points lies on exactly one line
        (Steiner system S(2,4,16) is not achievable; AG(2,4) has λ=1).
        Connected (every two points on a unique line).

    Notes
    -----
    Points: pairs (x, y) ∈ GF(4)^2, encoded as 4*x + y (0..15).
    Lines: {(x, a·x + b) : x ∈ GF(4)} for each slope a ∈ GF(4) and
    intercept b ∈ GF(4) (16 non-vertical lines), plus vertical lines
    {(c, y) : y ∈ GF(4)} for each c ∈ GF(4) (4 vertical lines).
    """
    q = 4
    # Points: (x, y) → 4*x + y
    lines: list[frozenset[int]] = []

    # Non-vertical: y = a*x + b
    for a in range(q):
        for b in range(q):
            line = frozenset(_gf4_mul(a, x) ^ b if a != 0 else b for x in range(q))
            # Actually: y = a*x + b in GF(4), point id = 4*x + y
            line = frozenset(4 * x + _gf4_add(_gf4_mul(a, x), b) for x in range(q))
            lines.append(line)

    # Vertical: x = c
    for c in range(q):
        line = frozenset(4 * c + y for y in range(q))
        lines.append(line)

    assert len(lines) == 20, f"AG(2,4) should have 20 lines, got {len(lines)}"
    return SparseHypergraph(n_nodes=q * q, hyperedges=lines)


def projective_plane_pg23() -> SparseHypergraph:
    """Projective plane PG(2,3) over GF(3).

    Returns
    -------
    SparseHypergraph
        13 points (homogeneous coords over GF(3)), 13 lines of size 4, 4-uniform.
        Every pair of distinct points lies on exactly one line.
        Connected (any two points on a unique line).

    Notes
    -----
    Points: canonical representatives of [x:y:z] ∈ PG(2, GF(3)) where the
    first nonzero coordinate is 1.  Encoded 0..12 in the canonical order:
    [1:0:0], [1:1:0], [1:2:0], [1:0:1], [1:1:1], [1:2:1],
    [1:0:2], [1:1:2], [1:2:2], [0:1:0], [0:1:1], [0:1:2], [0:0:1].

    Lines: [a:b:c] normalized, containing all points P with
    a*P_x + b*P_y + c*P_z = 0 mod 3.
    """
    # Enumerate all 13 canonical point representatives.
    points: list[tuple[int, int, int]] = []
    # [1:y:z] for y,z in {0,1,2}
    for y in range(3):
        for z in range(3):
            points.append((1, y, z))
    # [0:1:z] for z in {0,1,2}
    for z in range(3):
        points.append((0, 1, z))
    # [0:0:1]
    points.append((0, 0, 1))
    assert len(points) == 13

    # Enumerate all 13 canonical line representatives [a:b:c].
    line_reps: list[tuple[int, int, int]] = []
    for a in range(3):
        for b in range(3):
            for c in range(3):
                if (a, b, c) == (0, 0, 0):
                    continue
                # Normalize: first nonzero coord is 1, and we keep the
                # lex-smallest scaling (multiply all by inverse of first nonzero).
                first_nonzero = next(v for v in (a, b, c) if v != 0)
                inv = {1: 1, 2: 2}[first_nonzero]  # multiplicative inverse in GF(3)
                # Wait: 2*2=4≡1 mod 3 so inv(2)=2; inv(1)=1.
                norm = tuple(_gf3_mul(inv, v) for v in (a, b, c))
                if norm not in set(line_reps):
                    line_reps.append(norm)  # type: ignore[arg-type]

    assert len(line_reps) == 13, f"PG(2,3) should have 13 lines, got {len(line_reps)}"

    lines: list[frozenset[int]] = []
    for la, lb, lc in line_reps:
        members: list[int] = []
        for i, (px, py, pz) in enumerate(points):
            dot = _gf3_add(_gf3_add(_gf3_mul(la, px), _gf3_mul(lb, py)), _gf3_mul(lc, pz))
            if dot == 0:
                members.append(i)
        assert len(members) == 4, f"line [{la}:{lb}:{lc}] has {len(members)} members, expected 4"
        lines.append(frozenset(members))

    return SparseHypergraph(n_nodes=13, hyperedges=lines)


def projective_plane_pg24() -> SparseHypergraph:
    """Projective plane PG(2,4) = S(2,5,21) over GF(4).

    Returns
    -------
    SparseHypergraph
        21 points (homogeneous coords over GF(4)), 21 lines of size 5, 5-uniform.
        Every pair of distinct points lies on exactly one line.
        n=21, m=21; very high symmetry — expected to gate out in feasibility pilot.

    Notes
    -----
    Points: canonical reps [x:y:z] ∈ PG(2, GF(4)) where first nonzero coord is 1.
    Lines: [a:b:c] containing all points P with a*P_x ⊕ b*P_y ⊕ c*P_z = 0 in GF(4).
    """
    # Enumerate the 21 = (4^3-1)/(4-1) canonical point reps.
    points: list[tuple[int, int, int]] = []
    # [1:y:z] for y,z in GF(4)
    for y in range(4):
        for z in range(4):
            points.append((1, y, z))
    # [0:1:z] for z in GF(4)
    for z in range(4):
        points.append((0, 1, z))
    # [0:0:1]
    points.append((0, 0, 1))
    assert len(points) == 21

    # Enumerate the 21 line reps: same normalization (first nonzero → 1).
    # GF(4) nonzero elements: 1,2,3 with inverses 1,3,2 (since 2*3=1 in GF(4)).
    _gf4_inv = {1: 1, 2: 3, 3: 2}

    seen_lines: set[tuple[int, int, int]] = set()
    line_reps: list[tuple[int, int, int]] = []
    for a in range(4):
        for b in range(4):
            for c in range(4):
                if (a, b, c) == (0, 0, 0):
                    continue
                first_nz = next(v for v in (a, b, c) if v != 0)
                inv = _gf4_inv[first_nz]
                norm = tuple(_gf4_mul(inv, v) for v in (a, b, c))
                if norm not in seen_lines:
                    seen_lines.add(norm)  # type: ignore[arg-type]
                    line_reps.append(norm)  # type: ignore[arg-type]

    assert len(line_reps) == 21, f"PG(2,4) should have 21 lines, got {len(line_reps)}"

    lines: list[frozenset[int]] = []
    for la, lb, lc in line_reps:
        members: list[int] = []
        for i, (px, py, pz) in enumerate(points):
            dot = _gf4_add(
                _gf4_add(_gf4_mul(la, px), _gf4_mul(lb, py)),
                _gf4_mul(lc, pz),
            )
            if dot == 0:
                members.append(i)
        assert len(members) == 5, f"line [{la}:{lb}:{lc}] has {len(members)} members, expected 5"
        lines.append(frozenset(members))

    return SparseHypergraph(n_nodes=21, hyperedges=lines)


def complete_uniform(n: int, k: int) -> SparseHypergraph:
    """Complete k-uniform hypergraph K_n^(k).

    All C(n,k) k-subsets of n vertices form the edge set.

    Parameters
    ----------
    n : int
        Number of vertices.  Must satisfy ``n >= k``.
    k : int
        Uniform arity.  Must satisfy ``2 <= k <= n``.

    Returns
    -------
    SparseHypergraph
        K_n^(k): n nodes, C(n,k) edges, k-uniform.
        Connected whenever k >= 2 and n >= 2.
    """
    if k < 2 or n < k:
        raise ValueError(f"need 2 <= k <= n, got k={k}, n={n}")
    edges = [frozenset(combo) for combo in itertools.combinations(range(n), k)]
    return SparseHypergraph(n_nodes=n, hyperedges=edges)


def loose_path(k: int, length: int) -> SparseHypergraph:
    """Loose k-uniform path of the given length.

    Consecutive edges share exactly one vertex; n = length*(k-1)+1.

    Parameters
    ----------
    k : int
        Uniform arity, k >= 2.
    length : int
        Number of edges, length >= 1.

    Returns
    -------
    SparseHypergraph
        Connected k-uniform path with ``length`` edges and
        ``length*(k-1)+1`` vertices.
    """
    if k < 2:
        raise ValueError(f"k must be >= 2, got {k}")
    if length < 1:
        raise ValueError(f"length must be >= 1, got {length}")
    edges: list[frozenset[int]] = []
    for i in range(length):
        # Edge i shares vertex i*(k-1) with edge i-1.
        start = i * (k - 1)
        edge = frozenset(range(start, start + k))
        edges.append(edge)
    n = length * (k - 1) + 1
    return SparseHypergraph(n_nodes=n, hyperedges=edges)


def tight_path(k: int, length: int) -> SparseHypergraph:
    """Tight k-uniform path of the given length.

    Consecutive edges share k-1 vertices; n = length + k - 1.

    Parameters
    ----------
    k : int
        Uniform arity, k >= 2.
    length : int
        Number of edges, length >= 1.

    Returns
    -------
    SparseHypergraph
        Connected k-uniform tight path with ``length`` edges and
        ``length + k - 1`` vertices.
    """
    if k < 2:
        raise ValueError(f"k must be >= 2, got {k}")
    if length < 1:
        raise ValueError(f"length must be >= 1, got {length}")
    edges: list[frozenset[int]] = []
    for i in range(length):
        edge = frozenset(range(i, i + k))
        edges.append(edge)
    n = length + k - 1
    return SparseHypergraph(n_nodes=n, hyperedges=edges)


def loose_cycle(k: int, length: int) -> SparseHypergraph:
    """Loose k-uniform cycle of the given length.

    Consecutive edges (cyclically) share exactly one vertex; n = length*(k-1).

    Parameters
    ----------
    k : int
        Uniform arity, k >= 2.
    length : int
        Number of edges, length >= 2.

    Returns
    -------
    SparseHypergraph
        Connected k-uniform loose cycle with ``length`` edges and
        ``length*(k-1)`` vertices.
    """
    if k < 2:
        raise ValueError(f"k must be >= 2, got {k}")
    if length < 2:
        raise ValueError(f"length must be >= 2 for a cycle, got {length}")
    n = length * (k - 1)
    edges: list[frozenset[int]] = []
    for i in range(length):
        # The "anchor" vertex shared with the next edge is at position
        # (i+1)*(k-1) mod n.
        start = i * (k - 1)
        shared_next = ((i + 1) * (k - 1)) % n
        interior = frozenset(range(start, start + k - 1))
        edge = interior | {shared_next}
        edges.append(edge)
    return SparseHypergraph(n_nodes=n, hyperedges=edges)


def tight_cycle(k: int, length: int) -> SparseHypergraph:
    """Tight k-uniform cycle of the given length.

    Consecutive edges (cyclically) share k-1 vertices; n = length.

    Parameters
    ----------
    k : int
        Uniform arity, k >= 2.
    length : int
        Number of edges = number of vertices; must satisfy length >= k.

    Returns
    -------
    SparseHypergraph
        Connected k-uniform tight cycle with ``length`` edges and
        ``length`` vertices.
    """
    if k < 2:
        raise ValueError(f"k must be >= 2, got {k}")
    if length < k:
        raise ValueError(f"length must be >= k={k} for a tight cycle, got {length}")
    n = length
    edges: list[frozenset[int]] = []
    for i in range(length):
        edge = frozenset((i + j) % n for j in range(k))
        edges.append(edge)
    return SparseHypergraph(n_nodes=n, hyperedges=edges)


# ---------------------------------------------------------------------------
# Catalog registry
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _CatalogEntry:
    """One entry in the known-design catalog."""

    item_id: str
    family_label: str
    arity: int


def _make_all_designs() -> list[tuple[_CatalogEntry, SparseHypergraph]]:
    """Build all catalog hypergraphs.  Returns (entry, hypergraph) pairs."""
    entries: list[tuple[_CatalogEntry, SparseHypergraph]] = []

    def _add(item_id: str, family_label: str, arity: int, H: SparseHypergraph) -> None:
        entries.append((_CatalogEntry(item_id, family_label, arity), H))

    # --- Arity 3 ---
    _add("sts7", "STS7", 3, fano_plane())
    _add("sts9", "STS9", 3, sts_9())
    _add("sts13_0", "STS13-A", 3, steiner_triple_system(13, 0))
    _add("sts13_1", "STS13-B", 3, steiner_triple_system(13, 1))
    _add("sts15_0", "STS15-A", 3, steiner_triple_system(15, 0))
    _add("gq22", "GQ22", 3, gq_2_2_doily())
    _add("loose_path_k3", "LoosePath3", 3, loose_path(3, 4))
    _add("tight_path_k3", "TightPath3", 3, tight_path(3, 4))
    _add("loose_cycle_k3", "LooseCycle3", 3, loose_cycle(3, 4))
    _add("tight_cycle_k3", "TightCycle3", 3, tight_cycle(3, 5))
    _add("complete_k3_n5", "Complete3-5", 3, complete_uniform(5, 3))

    # --- Arity 4 ---
    _add("ag24", "AG24", 4, affine_plane_ag24())
    _add("pg23", "PG23", 4, projective_plane_pg23())
    _add("loose_path_k4", "LoosePath4", 4, loose_path(4, 3))
    _add("tight_path_k4", "TightPath4", 4, tight_path(4, 3))
    _add("loose_cycle_k4", "LooseCycle4", 4, loose_cycle(4, 4))
    _add("tight_cycle_k4", "TightCycle4", 4, tight_cycle(4, 5))
    _add("complete_k4_n6", "Complete4-6", 4, complete_uniform(6, 4))

    # --- Arity 5 ---
    _add("pg24", "PG24", 5, projective_plane_pg24())
    _add("loose_path_k5", "LoosePath5", 5, loose_path(5, 3))
    _add("tight_path_k5", "TightPath5", 5, tight_path(5, 3))
    _add("tight_cycle_k5", "TightCycle5", 5, tight_cycle(5, 7))
    _add("complete_k5_n6", "Complete5-6", 5, complete_uniform(6, 5))

    return entries


# Eagerly built at module import.  All constructors are pure; no I/O.
_ALL_ENTRIES: list[tuple[_CatalogEntry, SparseHypergraph]] = _make_all_designs()
_ENTRY_BY_ID: dict[str, tuple[_CatalogEntry, SparseHypergraph]] = {
    e.item_id: (e, H) for e, H in _ALL_ENTRIES
}

# Subset that is declared "admitted" after feasibility gating.
# Populated by ``set_admitted_ids``; when None, all entries are admitted.
_ADMITTED_IDS: frozenset[str] | None = None


def set_admitted_ids(ids: frozenset[str]) -> None:
    """Override the admitted subset for downstream use by the pilot.

    Call this after running the feasibility pilot to restrict
    ``KnownDesignCatalog`` and ``catalog_seeds`` to only admitted entries.
    The module default (``None``) treats all entries as admitted.

    Parameters
    ----------
    ids : frozenset[str]
        Set of item_ids that passed the feasibility gate.
    """
    global _ADMITTED_IDS
    _ADMITTED_IDS = ids


def catalog_seeds(
    *,
    admitted_only: bool = False,
    arities: tuple[int, ...] | None = None,
) -> list[SparseHypergraph]:
    """Return one seed hypergraph per admitted catalog entry.

    The order matches :func:`catalog_family_labels` and :func:`catalog_item_ids`.

    Parameters
    ----------
    admitted_only : bool
        When ``True``, restrict to entries in the admitted set (populated by
        :func:`set_admitted_ids`).  Default ``False`` (all entries).
    arities : tuple[int, ...] | None
        When not ``None``, restrict to entries with matching uniform arity.

    Returns
    -------
    list[SparseHypergraph]
        Seed hypergraphs in catalog order.
    """
    return [H for _, H in _filtered_entries(admitted_only=admitted_only, arities=arities)]


def catalog_family_labels(
    *,
    admitted_only: bool = False,
    arities: tuple[int, ...] | None = None,
) -> list[str]:
    """Return family labels matching :func:`catalog_seeds` order.

    Parameters
    ----------
    admitted_only : bool
        Same as in :func:`catalog_seeds`.
    arities : tuple[int, ...] | None
        Same as in :func:`catalog_seeds`.

    Returns
    -------
    list[str]
        Family label strings in catalog order.
    """
    return [
        e.family_label for e, _ in _filtered_entries(admitted_only=admitted_only, arities=arities)
    ]


def catalog_item_ids(
    *,
    admitted_only: bool = False,
    arities: tuple[int, ...] | None = None,
) -> list[str]:
    """Return item_ids matching :func:`catalog_seeds` order."""
    return [e.item_id for e, _ in _filtered_entries(admitted_only=admitted_only, arities=arities)]


def _filtered_entries(
    *,
    admitted_only: bool,
    arities: tuple[int, ...] | None,
) -> list[tuple[_CatalogEntry, SparseHypergraph]]:
    result: list[tuple[_CatalogEntry, SparseHypergraph]] = []
    for entry, H in _ALL_ENTRIES:
        if admitted_only and _ADMITTED_IDS is not None and entry.item_id not in _ADMITTED_IDS:
            continue
        if arities is not None and entry.arity not in arities:
            continue
        result.append((entry, H))
    return result


# ---------------------------------------------------------------------------
# HypergraphDataset implementation
# ---------------------------------------------------------------------------


class KnownDesignCatalog(HypergraphDataset):
    """All entries in the known-design catalog as a HypergraphDataset.

    Deterministic; ``seed()`` is a no-op.  Each item carries:

    - ``item_id``: the design's canonical identifier (e.g. ``"sts7"``).
    - ``iso_class``: unique integer per entry (all designs are pairwise
      non-isomorphic within their arity stratum by construction).
    - ``extra["family_label"]``: the family name string.
    - ``extra["arity"]``: uniform arity.

    Parameters
    ----------
    admitted_only : bool
        When ``True``, restrict to the admitted subset set by
        :func:`set_admitted_ids`.  Default ``False``.
    arities : tuple[int, ...] | None
        When not ``None``, include only designs of those arities.
    """

    def __init__(
        self,
        *,
        admitted_only: bool = False,
        arities: tuple[int, ...] | None = None,
    ) -> None:
        self._admitted_only = admitted_only
        self._arities = arities
        self._entries = _filtered_entries(admitted_only=admitted_only, arities=arities)

    @property
    def name(self) -> DatasetName:
        return "known_design_catalog"

    @property
    def metadata(self) -> DatasetMetadata:
        all_hypergraphs = [H for _, H in self._entries]
        all_arities: list[int] = []
        for H in all_hypergraphs:
            for _, members, _ in H.iter_edges():
                all_arities.append(len(members))

        min_arity = min(all_arities) if all_arities else 0
        max_arity = max(all_arities) if all_arities else 0
        n_vals = [H.n_nodes for H in all_hypergraphs]

        rp = RealizedParams.compute(all_hypergraphs, seeds=())

        return DatasetMetadata(
            name=self.name,
            n_items=len(self._entries),
            arity_range=(min_arity, max_arity),
            n_nodes_range=(min(n_vals) if n_vals else 0, max(n_vals) if n_vals else 0),
            has_iso_labels=True,
            source="known_design_catalog (T-M7a): STS/AG/PG/GQ catalog + uniform families",
            citation=(
                "Kaski & Ostergård, Math. Comp. 73 (2004); "
                "Beutelspacher & Rosenbaum 1998; Sylvester 1861; Berge 1989"
            ),
            label_vocabulary=LabelVocabulary.trivial(),
            realized_params=rp,
        )

    def __iter__(self) -> Iterator[DatasetItem]:
        for class_id, (entry, H) in enumerate(self._entries):
            yield DatasetItem(
                item_id=entry.item_id,
                hypergraph=H,
                iso_class=class_id,
                extra={
                    "family_label": entry.family_label,
                    "arity": entry.arity,
                    "n_nodes": H.n_nodes,
                    "n_edges": H.n_edges,
                },
            )

    def __len__(self) -> int:
        return len(self._entries)

    def seed(self, seed: Seed) -> KnownDesignCatalog:  # noqa: ARG002 — deterministic
        return self


def _factory(params: dict[str, Any]) -> HypergraphDataset:
    admitted_only = params.get("admitted_only", False)
    arities_raw = params.get("arities")
    arities = tuple(arities_raw) if arities_raw is not None else None
    return KnownDesignCatalog(admitted_only=admitted_only, arities=arities)


register_dataset("known_design_catalog", _factory)
