"""The synthetic RQ1 corpus.

2,000 random connected labelled knowledge bases, ``n in [6, 16]``,
``m in [6, 20]``, arities 2-4, 3 constant types, 3 predicates, obtained by
rejection sampling under a fixed seed. It is the only fully synthetic member
of the addressing comparison, and it is the probe's corpus: ported verbatim
from ``scripts/diagnostics/d_art3_probes_2026-09-03/f4_topology/f4_corpora.py``
(``gen_synthetic``) so that the RQ1 gate compares like with like.
"""

from __future__ import annotations

import random

from isalhg.datasets.kb.base import Fact, KBCollection, KBRecord, make_record

N_RANGE = (6, 16)
M_RANGE = (6, 20)
ARITY_RANGE = (2, 4)
N_TYPES = 3
N_PREDS = 3

TYPE_NAMES = tuple(f"t{i}" for i in range(N_TYPES))
PRED_NAMES = tuple(f"p{i}" for i in range(N_PREDS))

_FACT_GUARD = 400
_TRIES_PER_ITEM = 200


def sample_record(kb_id: str, rng: random.Random) -> KBRecord | None:
    """Draw one candidate; ``None`` when the draw is rejected."""
    n = rng.randint(*N_RANGE)
    m = rng.randint(*M_RANGE)
    types = [rng.randrange(N_TYPES) for _ in range(n)]
    facts: set[Fact] = set()
    guard = 0
    while len(facts) < m and guard < _FACT_GUARD:
        guard += 1
        arity = rng.randint(*ARITY_RANGE)
        facts.add((rng.randrange(N_PREDS), tuple(sorted(rng.sample(range(n), arity)))))
    if len(facts) != m:
        return None
    return make_record(
        kb_id,
        n,
        types,
        sorted(facts),
        meta={"n_types": N_TYPES, "n_preds": N_PREDS},
        require_connected=True,
    )


def corpus(n_items: int = 2000, seed: int = 20260905) -> KBCollection:
    """Rejection-sample the synthetic RQ1 collection.

    Parameters
    ----------
    n_items : int, optional
        Number of members. Default 2,000.
    seed : int, optional
        Seed of the local ``random.Random``; the collection is a pure function
        of ``(n_items, seed)``.

    Returns
    -------
    KBCollection
        Members named ``syn{i:05d}``, three types, three predicates, no roles,
        no labels.
    """
    rng = random.Random(seed)
    records: list[KBRecord] = []
    tries = 0
    while len(records) < n_items and tries < _TRIES_PER_ITEM * n_items:
        tries += 1
        record = sample_record(f"syn{len(records):05d}", rng)
        if record is not None:
            records.append(record)
    return KBCollection(
        name="synthetic_rq1",
        records=tuple(records),
        type_names=TYPE_NAMES,
        pred_names=PRED_NAMES,
        role_names=(),
        k_max=ARITY_RANGE[1],
        meta={
            "source": "generated",
            "generator": "isalhg.datasets.kb.synthetic_rq1.corpus",
            "seed": seed,
            "n_items_requested": n_items,
            "n_range": list(N_RANGE),
            "m_range": list(M_RANGE),
            "arity_range": list(ARITY_RANGE),
            "n_types": N_TYPES,
            "n_preds": N_PREDS,
            "tries": tries,
            "derivation": (
                "rejection sampling: draw n, m, types and m distinct facts of arity 2-4; "
                "keep the draw iff every constant occurs and the primal graph is connected"
            ),
        },
    )
