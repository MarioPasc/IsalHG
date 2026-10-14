"""The RQ7 operating-envelope grid and its random knowledge bases.

Random connected labelled knowledge bases over the pre-registered grid
(``DESIGN.md`` §8, supplementary S4)::

    m       in {10, 20, 40, 80, 120, 160}
    k       in {2, 3, 4, 5}
    |Sigma_E| in {1, 3, 10}
    |Sigma_V| in {1, 4}
    density in {"sparse": n = min(ceil(1.5 m), m (k - 1) + 1),
                "dense":  n = ceil(0.5 m) + k}

plus the fact-alphabet-only extension ``m in {320, 640, 1280}`` at ``k = 3``,
``|Sigma_E| = 3``, ``|Sigma_V| = 1``, both densities.

**The sparse cap.** A connected knowledge base of ``m`` facts of arity at most
``k`` spans at most ``m (k - 1) + 1`` constants, so the unconstrained sparse
target ``ceil(1.5 m)`` is unreachable at ``k = 2``, where it exceeds ``m + 1``.
The sparse rule therefore caps at that structural maximum: every grid cell is
feasible, and the ``k = 2`` sparse cells are trees (``n = m + 1``), the
sparsest connected knowledge base that exists at that arity. The feasibility
machinery is retained -- :func:`grid` reports ``feasible`` per cell and
:func:`random_kb` raises :class:`KBGenerationError` on an infeasible
``(m, k, n)`` -- so a hand-built cell outside the grid still fails loudly.
"""

from __future__ import annotations

import math
import random
from typing import Any

from isalhg.datasets.kb.base import Fact, KBGenerationError, KBRecord, make_record

M_VALUES: tuple[int, ...] = (10, 20, 40, 80, 120, 160)
K_VALUES: tuple[int, ...] = (2, 3, 4, 5)
EDGE_VOCABULARIES: tuple[int, ...] = (1, 3, 10)
VERTEX_VOCABULARIES: tuple[int, ...] = (1, 4)
DENSITIES: tuple[str, ...] = ("sparse", "dense")

EXTENSION_M_VALUES: tuple[int, ...] = (320, 640, 1280)
EXTENSION_K = 3
EXTENSION_EDGE_VOCABULARY = 3
EXTENSION_VERTEX_VOCABULARY = 1

N_SEEDS = 27

_FACT_ATTEMPTS = 64
_BUILD_ATTEMPTS = 32


def max_constants(m: int, k: int) -> int:
    """Largest constant count a connected knowledge base of ``m`` facts of arity <= ``k`` spans."""
    return m * (k - 1) + 1


def constants_for(m: int, k: int, density: str) -> int:
    """Number of constants a cell asks for.

    Parameters
    ----------
    m : int
        Fact count.
    k : int
        Maximum arity.
    density : {"sparse", "dense"}
        ``sparse`` is ``min(ceil(1.5 m), m (k - 1) + 1)`` -- the sparse target,
        capped at the structural maximum a connected knowledge base can span,
        which binds only at ``k = 2`` and yields a tree there. ``dense`` is
        ``ceil(0.5 m) + k``.

    Returns
    -------
    int
        The constant count.

    Raises
    ------
    KBGenerationError
        If ``density`` is not one of the two names.
    """
    if density == "sparse":
        return min(math.ceil(1.5 * m), max_constants(m, k))
    if density == "dense":
        return math.ceil(0.5 * m) + k
    raise KBGenerationError(f"unknown density {density!r}; expected one of {DENSITIES}")


def is_feasible(m: int, k: int, density: str) -> bool:
    """True iff a connected knowledge base with the cell's ``(n, m, k)`` exists.

    Every cell of :func:`grid` satisfies this by construction since the sparse
    rule caps at :func:`max_constants`; the check is kept for hand-built cells.
    """
    return constants_for(m, k, density) <= max_constants(m, k)


def grid(*, include_extension: bool = True) -> tuple[dict[str, Any], ...]:
    """The pre-registered RQ7 cells.

    Parameters
    ----------
    include_extension : bool, optional
        Append the fact-alphabet-only large-``m`` extension. Default ``True``.

    Returns
    -------
    tuple[dict, ...]
        One dict per cell with ``m, k, n_edge_labels, n_vertex_labels,
        density, n, n_seeds, feasible, fact_alphabet_only``.
    """
    cells: list[dict[str, Any]] = []
    for m in M_VALUES:
        for k in K_VALUES:
            for n_edge in EDGE_VOCABULARIES:
                for n_vertex in VERTEX_VOCABULARIES:
                    for density in DENSITIES:
                        cells.append(
                            {
                                "m": m,
                                "k": k,
                                "n_edge_labels": n_edge,
                                "n_vertex_labels": n_vertex,
                                "density": density,
                                "n": constants_for(m, k, density),
                                "n_seeds": N_SEEDS,
                                "feasible": is_feasible(m, k, density),
                                "fact_alphabet_only": False,
                            }
                        )
    if include_extension:
        for m in EXTENSION_M_VALUES:
            for density in DENSITIES:
                cells.append(
                    {
                        "m": m,
                        "k": EXTENSION_K,
                        "n_edge_labels": EXTENSION_EDGE_VOCABULARY,
                        "n_vertex_labels": EXTENSION_VERTEX_VOCABULARY,
                        "density": density,
                        "n": constants_for(m, EXTENSION_K, density),
                        "n_seeds": N_SEEDS,
                        "feasible": is_feasible(m, EXTENSION_K, density),
                        "fact_alphabet_only": True,
                    }
                )
    return tuple(cells)


def _grow(n: int, m: int, k: int, n_edge_labels: int, rng: random.Random) -> list[Fact] | None:
    """Grow a connected fact set: every fact links to what is already covered."""
    order = list(range(n))
    rng.shuffle(order)
    covered = [order[0]]
    uncovered = order[1:]
    facts: list[Fact] = []
    existing: set[Fact] = set()
    for index in range(m):
        remaining_facts = m - index - 1
        need = len(uncovered)
        j_min = max(0, need - remaining_facts * (k - 1))
        if need > 0:
            j_min = max(j_min, 1)
        arity_low = max(2, j_min + 1)
        if arity_low > k:
            return None
        placed = False
        for _ in range(_FACT_ATTEMPTS):
            arity = rng.randint(arity_low, k)
            j_max = min(arity - 1, need)
            if j_min > j_max:
                continue
            j = rng.randint(j_min, j_max)
            old_needed = arity - j
            if old_needed > len(covered):
                continue
            newcomers = uncovered[:j]
            olds = rng.sample(covered, old_needed)
            members = tuple(sorted({*newcomers, *olds}))
            if len(members) < 2:
                continue
            candidate: Fact = (rng.randrange(n_edge_labels), members)
            if candidate in existing:
                continue
            existing.add(candidate)
            facts.append(candidate)
            covered.extend(newcomers)
            del uncovered[:j]
            placed = True
            break
        if not placed:
            return None
    return facts if not uncovered else None


def random_kb(
    m: int,
    k: int,
    n_edge_labels: int,
    n_vertex_labels: int,
    density: str,
    seed: int,
) -> KBRecord:
    """One random connected labelled knowledge base of an RQ7 cell.

    Parameters
    ----------
    m : int
        Number of facts.
    k : int
        Maximum fact arity; arities are drawn from ``2 .. k``.
    n_edge_labels : int
        Predicate-vocabulary size.
    n_vertex_labels : int
        Type-vocabulary size.
    density : {"sparse", "dense"}
        Sets the constant count via :func:`constants_for`.
    seed : int
        Seed of the local ``random.Random``.

    Returns
    -------
    KBRecord
        A connected record with exactly ``m`` distinct facts over
        ``constants_for(m, k, density)`` constants.

    Raises
    ------
    KBGenerationError
        If the cell is structurally infeasible, or if the generator failed to
        realise it within its attempt budget.
    """
    n = constants_for(m, k, density)
    if not is_feasible(m, k, density):
        raise KBGenerationError(
            f"cell m={m} k={k} density={density} asks for n={n} constants, but a connected "
            f"knowledge base of {m} facts of arity <= {k} spans at most {max_constants(m, k)}"
        )
    rng = random.Random(seed)
    kb_id = f"m{m}_k{k}_e{n_edge_labels}_v{n_vertex_labels}_{density}_s{seed}"
    for _ in range(_BUILD_ATTEMPTS):
        facts = _grow(n, m, k, n_edge_labels, rng)
        if facts is None:
            continue
        record = make_record(
            kb_id,
            n,
            [rng.randrange(n_vertex_labels) for _ in range(n)],
            facts,
            meta={
                "m": m,
                "k": k,
                "n_edge_labels": n_edge_labels,
                "n_vertex_labels": n_vertex_labels,
                "density": density,
                "seed": seed,
                "n_types": n_vertex_labels,
                "n_preds": n_edge_labels,
            },
            require_connected=True,
        )
        if record is not None and record.m == m:
            return record
    raise KBGenerationError(
        f"failed to realise cell m={m} k={k} |Sigma_E|={n_edge_labels} "
        f"|Sigma_V|={n_vertex_labels} density={density} at seed {seed}"
    )
