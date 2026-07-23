"""Known-design seed catalog for Stratum A (T-M7a, pruned T-M7m).

Exposes a curated set of named combinatorial designs and uniform hypergraph
families as a registered :class:`HypergraphDataset`.  Every entry is a
mathematically defined structure (not a random sample), which makes the
class labels interpretable and makes ARI/NMI against family labels a
meaningful signal (``REVIEW/DATA.md`` §2A, Gap 3 fix).

Article corpus (Stratum A, v3 — T-M7m pruning + T-M7o arity-fix additions):
  17 admitted families (KEPT_A_IDS), grouped into coarse classes by type × arity.
  9 families are permanently excluded (EXCLUDED_SYMMETRIC): AG(2,4), PG(2,3),
  PG(2,4), both STS(13) iso-classes, STS(15), and the three complete-uniform
  hypergraphs.  Exclusion reason: automorphism groups too large for bounded
  Qin-edit perturbation (≤ 300 retries exhaust without finding a non-isomorphic
  member).  Raw constructors remain importable for scripts and tests.

  T-M7o (2026-07-23) added three longer arity-4/5 tight-cycle designs to make
  cycle_k4 and cycle_k5 coarse classes multi-member for A2/A3 eligibility:
  tight_cycle_k4_n8 (n=8,m=8), tight_cycle_k4_n10 (n=10,m=10),
  tight_cycle_k5_n8 (n=8,m=8).  These are w*_c-feasible (p90 < 30 s per
  artifacts/power_pilot/REPORT.md §3) once the arity-cap bug in
  PlantedFamilyDataset is fixed (self._family_k per-seed instead of self._k=3).

Coarse class scheme (type × arity, within-arity only — never pool d_I across k):
  k=3: design_k3 {sts7, sts9, gq22}, path_k3 {loose_path_k3, tight_path_k3},
        cycle_k3 {loose_cycle_k3, tight_cycle_k3}
  k=4: path_k4 {loose_path_k4, tight_path_k4},
        cycle_k4 {loose_cycle_k4, tight_cycle_k4, tight_cycle_k4_n8, tight_cycle_k4_n10}
  k=5: path_k5 {loose_path_k5, tight_path_k5},
        cycle_k5 {tight_cycle_k5, tight_cycle_k5_n8}

Synthetic vs real roles (DATA_MANIFEST):
  Stratum A — known-design seeds + Qin-perturbation members (this module).
  Stratum B — parametric ER/Chung-Lu sweep (envelope JSON, read-only).
  Real anchor — HIC IMDB genre sub-corpus (censored secondary exhibit).

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
import logging
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

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pruning constants (T-M7m)
# ---------------------------------------------------------------------------

# Nine families excluded from the Stratum A article corpus: feasibility-DNF
# planes/large-Steiner systems and complete uniforms whose automorphism groups
# are so large that Qin-edit perturbation exhausts the retry budget (≤ 300
# attempts) without producing a non-isomorphic member.
EXCLUDED_SYMMETRIC: frozenset[str] = frozenset(
    {
        "ag24",  # AG(2,4): 20 edges, large aut group
        "pg23",  # PG(2,3): 13 edges, large aut group
        "pg24",  # PG(2,4): 21 edges, feasibility-DNF
        "sts13_0",  # STS(13) iso-class 0, n=13 slow
        "sts13_1",  # STS(13) iso-class 1, n=13 slow
        "sts15_0",  # STS(15) iso-class 0, n=15 slow
        "complete_k3_n5",  # K_5^(3): exhausts retries (perturbation space trivial)
        "complete_k4_n6",  # K_6^(4): exhausts retries
        "complete_k5_n6",  # K_6^(5): exhausts retries
    }
)

# Coarse structural class per catalog item (type × arity).
# Kept families only; excluded families get "excluded_<k>" as a placeholder.
# CRITICAL: coarse classes are WITHIN a fixed arity — never pool d_I across k.
COARSE_CLASS_BY_ID: dict[str, str] = {
    # Arity 3 — kept
    "sts7": "design_k3",
    "sts9": "design_k3",
    "gq22": "design_k3",
    "loose_path_k3": "path_k3",
    "tight_path_k3": "path_k3",
    "loose_cycle_k3": "cycle_k3",
    "tight_cycle_k3": "cycle_k3",
    # Arity 3 — excluded (kept importable)
    "sts13_0": "excluded_k3",
    "sts13_1": "excluded_k3",
    "sts15_0": "excluded_k3",
    "complete_k3_n5": "excluded_k3",
    # Arity 4 — kept
    "loose_path_k4": "path_k4",
    "tight_path_k4": "path_k4",
    "loose_cycle_k4": "cycle_k4",
    "tight_cycle_k4": "cycle_k4",
    "tight_cycle_k4_n8": "cycle_k4",  # n=8 m=8 w*_c p90=0.18 s (T-M7o)
    "tight_cycle_k4_n10": "cycle_k4",  # n=10 m=10 w*_c p90=2.34 s (T-M7o)
    # Arity 4 — excluded
    "ag24": "excluded_k4",
    "pg23": "excluded_k4",
    "complete_k4_n6": "excluded_k4",
    # Arity 5 — kept
    "loose_path_k5": "path_k5",
    "tight_path_k5": "path_k5",
    "tight_cycle_k5": "cycle_k5",
    "tight_cycle_k5_n8": "cycle_k5",  # n=8 m=8 w*_c p90=3.61 s (T-M7o)
    # Arity 5 — excluded
    "pg24": "excluded_k5",
    "complete_k5_n6": "excluded_k5",
}

# The 14 kept families (article Stratum A corpus).
KEPT_A_IDS: frozenset[str] = frozenset(COARSE_CLASS_BY_ID) - EXCLUDED_SYMMETRIC

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
    coarse_class: str


def _make_all_designs() -> list[tuple[_CatalogEntry, SparseHypergraph]]:
    """Build all catalog hypergraphs.  Returns (entry, hypergraph) pairs."""
    entries: list[tuple[_CatalogEntry, SparseHypergraph]] = []

    def _add(item_id: str, family_label: str, arity: int, H: SparseHypergraph) -> None:
        cc = COARSE_CLASS_BY_ID.get(item_id, f"unknown_k{arity}")
        entries.append((_CatalogEntry(item_id, family_label, arity, cc), H))

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
    _add("tight_cycle_k4_n8", "TightCycle4-8", 4, tight_cycle(4, 8))
    _add("tight_cycle_k4_n10", "TightCycle4-10", 4, tight_cycle(4, 10))
    _add("complete_k4_n6", "Complete4-6", 4, complete_uniform(6, 4))

    # --- Arity 5 ---
    _add("pg24", "PG24", 5, projective_plane_pg24())
    _add("loose_path_k5", "LoosePath5", 5, loose_path(5, 3))
    _add("tight_path_k5", "TightPath5", 5, tight_path(5, 3))
    _add("tight_cycle_k5", "TightCycle5", 5, tight_cycle(5, 7))
    _add("tight_cycle_k5_n8", "TightCycle5-8", 5, tight_cycle(5, 8))
    _add("complete_k5_n6", "Complete5-6", 5, complete_uniform(6, 5))

    return entries


# Eagerly built at module import.  All constructors are pure; no I/O.
_ALL_ENTRIES: list[tuple[_CatalogEntry, SparseHypergraph]] = _make_all_designs()
_ENTRY_BY_ID: dict[str, tuple[_CatalogEntry, SparseHypergraph]] = {
    e.item_id: (e, H) for e, H in _ALL_ENTRIES
}

# ---------------------------------------------------------------------------
# Feasibility tristate
# ---------------------------------------------------------------------------

# Admitted set: populated by set_admitted_ids().  None = all entries admitted.
_ADMITTED_IDS: frozenset[str] | None = None
# Pending-cluster set: local DNF at 30s budget; final admission deferred to
# the Picasso cluster pilot (T-M7h, 300s ceiling).
_PENDING_CLUSTER_IDS: frozenset[str] = frozenset()

# Status constants (string literals, not an Enum, to stay serialisation-neutral).
STATUS_ADMITTED = "ADMITTED"
STATUS_PENDING_CLUSTER = "PENDING_CLUSTER"
STATUS_EXCLUDED = "EXCLUDED"


def set_admitted_ids(
    ids: frozenset[str],
    *,
    pending_ids: frozenset[str] = frozenset(),
) -> None:
    """Override the admitted and pending subsets after the feasibility pilot.

    Populates the module-level gate used by ``KnownDesignCatalog``,
    ``catalog_seeds``, and ``design_status``.  The module default
    (``_ADMITTED_IDS is None``) treats all entries as admitted.

    Parameters
    ----------
    ids : frozenset[str]
        item_ids that passed the feasibility gate (ADMITTED).
    pending_ids : frozenset[str]
        item_ids whose final admission is deferred to the cluster pilot
        (PENDING_CLUSTER).  These are *not* included in
        ``catalog_seeds(admitted_only=True)``.
    """
    global _ADMITTED_IDS, _PENDING_CLUSTER_IDS
    _ADMITTED_IDS = ids
    _PENDING_CLUSTER_IDS = pending_ids


def design_status(item_id: str) -> str:
    """Return the feasibility tristate for a catalog entry.

    Returns
    -------
    str
        One of ``STATUS_ADMITTED``, ``STATUS_PENDING_CLUSTER``,
        ``STATUS_EXCLUDED``.  When ``set_admitted_ids`` has not been called,
        all entries return ``STATUS_ADMITTED`` (module default).
    """
    if _ADMITTED_IDS is None:
        return STATUS_ADMITTED  # default: everything admitted
    if item_id in _ADMITTED_IDS:
        return STATUS_ADMITTED
    if item_id in _PENDING_CLUSTER_IDS:
        return STATUS_PENDING_CLUSTER
    return STATUS_EXCLUDED


def catalog_seeds(
    *,
    admitted_only: bool = False,
    arities: tuple[int, ...] | None = None,
    exclude_symmetric: bool = False,
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
    exclude_symmetric : bool
        When ``True``, exclude families in ``EXCLUDED_SYMMETRIC`` (the nine
        permanently pruned high-symmetry families).  Default ``False``.

    Returns
    -------
    list[SparseHypergraph]
        Seed hypergraphs in catalog order.
    """
    return [
        H
        for _, H in _filtered_entries(
            admitted_only=admitted_only,
            arities=arities,
            exclude_symmetric=exclude_symmetric,
        )
    ]


def catalog_family_labels(
    *,
    admitted_only: bool = False,
    arities: tuple[int, ...] | None = None,
    exclude_symmetric: bool = False,
) -> list[str]:
    """Return family labels matching :func:`catalog_seeds` order.

    Parameters
    ----------
    admitted_only : bool
        Same as in :func:`catalog_seeds`.
    arities : tuple[int, ...] | None
        Same as in :func:`catalog_seeds`.
    exclude_symmetric : bool
        Same as in :func:`catalog_seeds`.

    Returns
    -------
    list[str]
        Family label strings in catalog order.
    """
    return [
        e.family_label
        for e, _ in _filtered_entries(
            admitted_only=admitted_only,
            arities=arities,
            exclude_symmetric=exclude_symmetric,
        )
    ]


def catalog_item_ids(
    *,
    admitted_only: bool = False,
    arities: tuple[int, ...] | None = None,
    exclude_symmetric: bool = False,
) -> list[str]:
    """Return item_ids matching :func:`catalog_seeds` order."""
    return [
        e.item_id
        for e, _ in _filtered_entries(
            admitted_only=admitted_only,
            arities=arities,
            exclude_symmetric=exclude_symmetric,
        )
    ]


def catalog_coarse_classes(
    *,
    admitted_only: bool = False,
    arities: tuple[int, ...] | None = None,
    exclude_symmetric: bool = False,
) -> list[str]:
    """Return coarse class labels matching :func:`catalog_seeds` order."""
    return [
        e.coarse_class
        for e, _ in _filtered_entries(
            admitted_only=admitted_only,
            arities=arities,
            exclude_symmetric=exclude_symmetric,
        )
    ]


def _filtered_entries(
    *,
    admitted_only: bool,
    arities: tuple[int, ...] | None,
    exclude_symmetric: bool = False,
) -> list[tuple[_CatalogEntry, SparseHypergraph]]:
    result: list[tuple[_CatalogEntry, SparseHypergraph]] = []
    for entry, H in _ALL_ENTRIES:
        if admitted_only and _ADMITTED_IDS is not None and entry.item_id not in _ADMITTED_IDS:
            continue
        if arities is not None and entry.arity not in arities:
            continue
        if exclude_symmetric and entry.item_id in EXCLUDED_SYMMETRIC:
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
    - ``extra["coarse_class"]``: type × arity label (e.g. ``"design_k3"``).

    Parameters
    ----------
    admitted_only : bool
        When ``True``, restrict to the admitted subset set by
        :func:`set_admitted_ids`.  Default ``False``.
    arities : tuple[int, ...] | None
        When not ``None``, include only designs of those arities.
    exclude_symmetric : bool
        When ``True``, exclude the nine permanently pruned high-symmetry
        families (``EXCLUDED_SYMMETRIC``).  Default ``False``.
    """

    def __init__(
        self,
        *,
        admitted_only: bool = False,
        arities: tuple[int, ...] | None = None,
        exclude_symmetric: bool = False,
    ) -> None:
        self._admitted_only = admitted_only
        self._arities = arities
        self._exclude_symmetric = exclude_symmetric
        self._entries = _filtered_entries(
            admitted_only=admitted_only,
            arities=arities,
            exclude_symmetric=exclude_symmetric,
        )

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
                    "coarse_class": entry.coarse_class,
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


# ---------------------------------------------------------------------------
# Stratum A labeled corpus
# ---------------------------------------------------------------------------


def build_stratum_a_corpus(
    *,
    members_per_family: int = 3,
    n_edits: int = 2,
    max_retries: int = 200,
    seed_value: int = 0,
    dedup_backend: str = "isalhg",
    admitted_ids: frozenset[str] | None = None,
    allow_partial: bool = True,
) -> HypergraphDataset:
    """Build the Stratum A labeled corpus from admitted catalog seeds.

    Feeds admitted known-design seeds into :class:`PlantedFamilyDataset`
    with ``family_labels`` set to the catalog family-label strings.  Each
    family contributes one seed plus ``members_per_family - 1`` non-isomorphic
    perturbations (``n_edits`` Qin edits, iso-deduplicated).

    Parameters
    ----------
    members_per_family : int
        Total members per family including the seed.  Default ``3``.
    n_edits : int
        Random Qin edits per non-seed member.  Default ``2``.
    max_retries : int
        Maximum rejection-sampling attempts per member.  Default ``200``.
    seed_value : int
        Master PRNG seed; pinned for reproducibility.  Default ``0``.
    dedup_backend : str
        Iso backend for fingerprint deduplication.  Default ``"isalhg"``.
    admitted_ids : frozenset[str] | None
        Explicit admitted set override.  When ``None`` (default), uses the
        module-level admitted set (set by :func:`set_admitted_ids`); if that
        is also ``None``, uses all 23 catalog entries.
    allow_partial : bool
        When ``True`` (default), families that exhaust the retry budget are
        accepted with however many members were found (at least the seed).
        A warning is logged.  When ``False``, exhaustion raises
        ``RuntimeError``.  Default ``True``.

    Returns
    -------
    PlantedFamilyDataset
        Labeled corpus; ``metadata.realized_params`` is populated.
    """
    # Deferred import keeps the catalog importable without PlantedFamilyDataset.
    from isalhg.datasets.synthetic.planted_families import PlantedFamilyDataset

    # Override admitted set only for this call if explicitly provided.
    if admitted_ids is not None:
        filtered = [(e, H) for e, H in _ALL_ENTRIES if e.item_id in admitted_ids]
        seeds = [H for _, H in filtered]
        labels = [e.family_label for e, _ in filtered]
        coarse_classes = [e.coarse_class for e, _ in filtered]
    else:
        # Default path: the pruned 14-family corpus (exclude_symmetric=True).
        # If set_admitted_ids() has been called, further restrict to that set.
        _use_admitted = _ADMITTED_IDS is not None
        entries = _filtered_entries(
            admitted_only=_use_admitted, arities=None, exclude_symmetric=True
        )
        seeds = [H for _, H in entries]
        labels = [e.family_label for e, _ in entries]
        coarse_classes = [e.coarse_class for e, _ in entries]

    return PlantedFamilyDataset(
        seeds=seeds,
        family_labels=labels,
        coarse_class_labels=coarse_classes,
        members_per_family=members_per_family,
        n_edits=n_edits,
        max_retries=max_retries,
        seed_value=seed_value,
        dedup_backend=dedup_backend,
        allow_partial=allow_partial,
    )


def _stratum_a_factory(params: dict[str, Any]) -> HypergraphDataset:
    admitted_raw = params.get("admitted_ids")
    admitted_ids = frozenset(admitted_raw) if admitted_raw is not None else None
    return build_stratum_a_corpus(
        members_per_family=params.get("members_per_family", 3),
        n_edits=params.get("n_edits", 2),
        max_retries=params.get("max_retries", 200),
        seed_value=params.get("seed_value", 0),
        dedup_backend=params.get("dedup_backend", "isalhg"),
        admitted_ids=admitted_ids,
        allow_partial=bool(params.get("allow_partial", True)),
    )


register_dataset("stratum_a_corpus", _stratum_a_factory)


# ---------------------------------------------------------------------------
# Per-arity pooling guard
# ---------------------------------------------------------------------------


def assert_single_arity_group(hypergraphs: list[SparseHypergraph]) -> None:
    """Raise ``ValueError`` if the corpus spans more than one arity group.

    ``d_I`` values are incomparable across arity groups (different k means
    different alphabet sizes, different string lengths, incommensurable
    distances).  Callers that run A2 (k-medoids) or A3 (kNN) on a pairwise
    matrix must hold k fixed; this guard enforces that at corpus-build time.

    Parameters
    ----------
    hypergraphs : list[SparseHypergraph]
        The corpus to validate.  Uniform hypergraphs (all edges same size)
        are the intended input.

    Raises
    ------
    ValueError
        When edges with two or more distinct sizes are found across the
        corpus, meaning d_I across these objects is being pooled over
        multiple k values.
    """
    if not hypergraphs:
        return
    arities: set[int] = set()
    for H in hypergraphs:
        for _, members, _ in H.iter_edges():
            arities.add(len(members))
    if len(arities) > 1:
        raise ValueError(
            f"Hypergraphs span multiple arity groups {sorted(arities)}. "
            "d_I is incomparable across k; split into per-arity sub-corpora "
            "before running A2/A3."
        )


# ---------------------------------------------------------------------------
# Data manifest
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _DataManifest:
    """Enumerates the corpora the article uses.

    Fields
    ------
    stratum_a_ids : frozenset[str]
        The 14 kept known-design family ids (Stratum A corpus).
    stratum_a_coarse_classes : dict[str, str]
        Coarse structural class per kept family (type × arity).
    stratum_b_envelope_path : str
        Relative path to the Stratum B feasibility envelope JSON (read-only).
    hic_real_corpora : tuple[str, ...]
        HIC dataset identifiers used in the real-anchor exhibit.
    """

    stratum_a_ids: frozenset[str]
    stratum_a_coarse_classes: dict[str, str]
    stratum_b_envelope_path: str
    hic_real_corpora: tuple[str, ...]


DATA_MANIFEST = _DataManifest(
    stratum_a_ids=KEPT_A_IDS,
    stratum_a_coarse_classes={
        item_id: cc for item_id, cc in COARSE_CLASS_BY_ID.items() if item_id in KEPT_A_IDS
    },
    stratum_b_envelope_path="experiments/article/stratum_b_feasibility_envelope.json",
    hic_real_corpora=("imdb_genre",),
)
