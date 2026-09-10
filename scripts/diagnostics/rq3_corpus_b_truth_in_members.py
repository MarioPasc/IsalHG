"""How often Corpus B's held-out quarter already sits among the earlier ones.

The RQ3 natural corpus splits a class's consecutive quarters into members
``1..T-1`` and a held-out truth ``T``. Consecutive quarters are frequently
identical, so the truth is often already present as a member -- and on those
runs *any* method that returns one of its inputs can recover the truth for free,
while on the complement no such method can recover it at all.

That complement is the natural-series analogue of Corpus A's structural floor.
It is defined from the **data** (does the truth appear among the members?) rather
than from a method's output (what origin did the winner have?), so it is
pre-statable and carries none of the confounding that conditioning on the
winner's origin would.

The predicate is the one the measurement itself uses for ``exact_recovery``:
``fact_distance(identity_facts_of_record(x), truth_facts) == 0`` -- equality of
identity-fact sets, **not** graph isomorphism. Using anything else here would
make the floor a claim about a different relation than the one being floored.

Raised by the ``[IsalHG-Fable]`` session against the reading that the three
transfer-and-recovered runs were an existence curiosity rather than a floor.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from collections.abc import Callable
from pathlib import Path

import yaml

from experiments.tkde import corpora
from experiments.tkde.rq3 import (
    enumerate_units_b,
    fact_distance,
    identity_facts_of_record,
)


def truth_present(config: dict[str, object], root: Path | None) -> dict[str, bool]:
    """For each Corpus B unit, whether any member equals the held-out truth.

    Parameters
    ----------
    config : dict
        The RQ3 config; only its ``corpus_b`` block is read.
    root : Path or None
        Data root holding ``corpora/``.

    Returns
    -------
    dict
        ``collection_id -> True`` when some member's identity facts equal the
        truth's. The key matches the ``collection_id`` written into
        ``rows_natural.csv`` (``"<class_id>|run<run_index>"``), so the result
        joins directly onto the rows.
    """
    block = config["corpus_b"]
    name = str(block["collection"])  # type: ignore[index]
    collection = corpora.load_collection(name, root)
    by_id = corpora.records_by_id(collection)
    out: dict[str, bool] = {}
    for unit in enumerate_units_b(config, root):
        records = [by_id[kb_id] for kb_id in unit.kb_ids]
        members, truth = records[:-1], records[-1]
        truth_facts = identity_facts_of_record(truth)
        out[f"{unit.class_id}|run{unit.run_index}"] = any(
            fact_distance(identity_facts_of_record(m), truth_facts) == 0 for m in members
        )
    return out


def report(rows_path: Path, present: dict[str, bool]) -> None:
    """Cross the truth-present flag against winner origin and exact recovery."""
    with rows_path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))

    def num(value: str | None) -> float | None:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    cov = [r for r in rows if r.get("method") == "coverage" and num(r.get("censored")) != 1.0]
    unknown = [r for r in cov if r.get("collection_id", "") not in present]
    if unknown:
        print(f"WARNING: {len(unknown)} coverage rows have no matching unit; join is incomplete")

    tab: Counter[tuple[str, str, str]] = Counter()
    for r in cov:
        cid = r.get("collection_id", "")
        if cid not in present:
            continue
        flag = "truth_in_members" if present[cid] else "TRUTH_ABSENT"
        origin = str(r.get("winner_origin", "")).split(":")[0] or "?"
        rec = "recovered" if num(r.get("exact_recovery")) == 1.0 else "not"
        tab[(flag, origin, rec)] += 1

    print(f"joined coverage runs: {sum(tab.values())} of {len(cov)}")
    for key in sorted(tab):
        print(f"   {key[0]:17s} {key[1]:10s} {key[2]:10s} {tab[key]:5d}")

    absent = sum(v for k, v in tab.items() if k[0] == "TRUTH_ABSENT")
    absent_rec = sum(v for k, v in tab.items() if k[0] == "TRUTH_ABSENT" and k[2] == "recovered")
    print()
    print(f"runs where the truth matches NO member: {absent}")
    print(f"   any input-returning method recovers: 0 of {absent} BY CONSTRUCTION")
    print("      (that zero is the definition of the stratum, not a measurement:")
    print("       a member cannot equal a truth that equals no member)")
    print(f"   the coverage consensus recovers:     {absent_rec} of {absent}  <- measured")
    if absent_rec:
        print("   -> the claim is the asymmetry: the constraint binds one method, not the other")
    _stratum_distance(rows, present, num)


def _stratum_distance(
    rows: list[dict[str, str]],
    present: dict[str, bool],
    num: Callable[[str | None], float | None],
) -> None:
    """Paired ``fact_dist``, consensus vs each medoid arm, on the hard stratum.

    On the TRUTH_ABSENT runs both methods emit an output at nonzero fact
    distance, so comparing them there has no structural constraint doing the
    work -- unlike the recovery axis, where the stratum's definition forces the
    medoid to zero. This is the one non-tautological comparison the stratum
    makes available.

    **Exploratory.** The stratum is defined from the data and is pre-statable in
    principle, but it was defined after the full-set null was seen. It cannot
    move D-KBf5a, whose gate is committed on the full set and stays there
    whatever this shows.
    """
    from math import comb

    by: dict[tuple[str, str, str], float | None] = {}
    for r in rows:
        if num(r.get("censored")) == 1.0 or r.get("method") == "medoid_survivors":
            continue
        by[(r.get("collection_id", ""), r.get("method", ""), r.get("arm", ""))] = num(
            r.get("fact_dist")
        )
    hard = sorted(u for u, absent in present.items() if not absent)
    arms = sorted({k[2] for k in by if k[1] == "medoid" and k[2]})
    print()
    # `hard` counts UNITS; a unit whose coverage row is censored contributes no
    # pair, so the printed n comes from the pair list, never from len(hard).
    print(f"EXPLORATORY -- paired fact_dist on the TRUTH_ABSENT stratum"
          f" ({len(hard)} units, censored rows excluded per arm below)")
    print("   (defined post hoc after the full-set null; cannot move D-KBf5a)")
    for arm in arms:
        pairs = [
            (by[(u, "coverage", "fact_rank")], by[(u, "medoid", arm)])
            for u in hard
            if by.get((u, "coverage", "fact_rank")) is not None
            and by.get((u, "medoid", arm)) is not None
        ]
        if not pairs:
            continue
        better = sum(1 for c, m in pairs if c < m)
        worse = sum(1 for c, m in pairs if c > m)
        disc = better + worse
        p = 1.0
        if disc:
            tail = min(better, disc - better)
            p = min(1.0, 2 * sum(comb(disc, i) for i in range(tail + 1)) / 2**disc)
        c_mean = sum(c for c, _ in pairs) / len(pairs)
        m_mean = sum(m for _, m in pairs) / len(pairs)
        mark = "*" if p < 0.05 else " "
        print(
            f"   {arm:22s} consensus {c_mean:5.3f} vs medoid {m_mean:5.3f}"
            f" | discordant {disc:3d}/{len(pairs)} ({better} better, {worse} worse)"
            f"  p = {p:.3g} {mark}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--rows", required=True, type=Path, help="rows_natural.csv")
    parser.add_argument("--data-root", type=Path, default=None)
    args = parser.parse_args()

    with args.config.open() as handle:
        config = yaml.safe_load(handle)
    present = truth_present(config, args.data_root)
    n_present = sum(1 for v in present.values() if v)
    print(f"Corpus B units: {len(present)} | truth already among members: {n_present}")
    report(args.rows, present)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
