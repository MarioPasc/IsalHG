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
from pathlib import Path
from typing import Any

import yaml

from experiments.tkde import corpora
from experiments.tkde.rq3 import (
    enumerate_units_b,
    fact_distance,
    identity_facts_of_record,
)


def truth_present(config: dict[str, Any], root: Path | None) -> dict[str, bool]:
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
    name = str(config["corpus_b"]["collection"])
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
    print(f"   any input-returning method recovers: 0 of {absent} (by construction)")
    print(f"   the coverage consensus recovers:     {absent_rec} of {absent}")
    if absent_rec:
        print("   -> the floor argument holds on the natural series")


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
