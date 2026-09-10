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
from statistics import median

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
    return {cid: min(d) == 0 for cid, d in member_distances(config, root).items()}


def member_distances(config: dict[str, object], root: Path | None) -> dict[str, list[int]]:
    """Per unit, every member's identity-fact distance to the held-out truth.

    This is the object the three derived quantities are read off:

    * ``min`` is the **oracle bound** -- the score of the best member any rule
      could pick, selected using the truth. No method restricted to returning an
      input can beat it, so it replaces a row-per-arm comparison with one
      structural baseline valid on both corpora;
    * ``min == 0`` is the truth-in-members flag;
    * the spread bounds how far apart any two representations' medoids can score,
      because a medoid can only return a member.
    """
    block = config["corpus_b"]
    name = str(block["collection"])  # type: ignore[index]
    collection = corpora.load_collection(name, root)
    by_id = corpora.records_by_id(collection)
    out: dict[str, list[int]] = {}
    for unit in enumerate_units_b(config, root):
        records = [by_id[kb_id] for kb_id in unit.kb_ids]
        members, truth = records[:-1], records[-1]
        truth_facts = identity_facts_of_record(truth)
        out[f"{unit.class_id}|run{unit.run_index}"] = [
            fact_distance(identity_facts_of_record(m), truth_facts) for m in members
        ]
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
    print(
        f"EXPLORATORY -- paired fact_dist on the TRUTH_ABSENT stratum"
        f" ({len(hard)} units, censored rows excluded per arm below)"
    )
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
    dists = member_distances(config, args.data_root)
    present = {c: min(d) == 0 for c, d in dists.items()}
    n_present = sum(1 for v in present.values() if v)
    print(f"Corpus B units: {len(present)} | truth already among members: {n_present}")
    report(args.rows, present)
    oracle_report(args.rows, dists)
    return 0


def oracle_report(
    rows_path: Path,
    dists: dict[str, list[int]],
) -> None:
    """Consensus against the best-achievable-input bound, by shape not by mean.

    Three readings, in the order they answer a reviewer:

    1. **The oracle bound.** ``min_i fact_dist(K_i, truth)`` is the score of the
       best member any selection rule could pick, chosen with knowledge of the
       truth. It upper-bounds every method restricted to returning an input, so
       it replaces one comparison per arm with a single structural baseline --
       and it is the same object as Corpus A's floor, where all members sit at
       ``t`` and the bound *is* ``t``.
    2. **Mass at zero, not the mean.** On the hard stratum the consensus can
       score exactly zero and no member-returning method can, so the capability
       lives in the shape of the distribution. A mean hides it. Reported as the
       fraction at zero beside the median of the nonzero remainder.
    3. **The within-collection spread.** A medoid can only return a member, so
       every arm's achievable mean lies between the best-input and worst-input
       means. That interval is the room the arms *had*; comparing it against the
       spread the arms actually show decides whether a cross-arm null is imposed
       by the corpus or is a fact about the representations.

       Measured on Corpus B, it is **not** imposed: on the TRUTH_ABSENT stratum
       the interval is ``[2.050, 4.225]`` (width 2.175) and the eleven arms span
       ``2.800-3.150`` (width 0.35) -- 16 % of the available room. The
       hypothesis that the corpus floors the medoid axis the way it does on
       Corpus A is therefore falsified here, and the arms' agreement is a
       property of the representations.
    """

    def num(value: str | None) -> float | None:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    with rows_path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    cons = {
        r["collection_id"]: num(r.get("fact_dist"))
        for r in rows
        if r.get("method") == "coverage" and num(r.get("censored")) != 1.0
    }
    hard = [c for c, d in dists.items() if min(d) > 0 and c in cons and cons[c] is not None]
    allu = [c for c in dists if c in cons and cons[c] is not None]

    for label, units in (("all runs", allu), ("TRUTH_ABSENT stratum", hard)):
        c_vals = [cons[c] for c in units]
        o_vals = [float(min(dists[c])) for c in units]
        print()
        print(f"-- {label}: n = {len(units)} --")
        w_vals = [float(max(dists[c])) for c in units]
        for name, vals in (
            ("consensus", c_vals),
            ("oracle bound (best input)", o_vals),
            ("worst input", w_vals),
        ):
            zero = sum(1 for v in vals if v == 0)
            nz = sorted(v for v in vals if v > 0)
            med = median(nz) if nz else float("nan")
            print(
                f"   {name:26s} mean {sum(vals) / len(vals):5.3f}"
                f" | at zero {zero:3d}/{len(vals)} ({zero / len(vals):.3f})"
                f" | median of nonzero {med:5.2f}"
            )
        better = sum(1 for c, o in zip(c_vals, o_vals, strict=True) if c < o)
        worse = sum(1 for c, o in zip(c_vals, o_vals, strict=True) if c > o)
        print(f"   consensus below the bound in {better}/{len(units)}, above in {worse}")
        # Any arm's mean must lie between these two, because a medoid returns a
        # member. If the arms cluster far inside the interval, their agreement is
        # a fact about the representations, NOT a corpus-imposed floor.
        lo = sum(o_vals) / len(o_vals)
        hi = sum(w_vals) / len(w_vals)
        print(
            f"   any input-returning arm's mean must lie in [{lo:.3f}, {hi:.3f}]"
            f"  (width {hi - lo:.3f})"
        )

    spreads = [max(d) - min(d) for c, d in dists.items() if c in cons and len(d) > 1]
    if spreads:
        print()
        print("-- within-unit spread of member-to-truth distance --")
        print(
            f"   range over members: median {median(spreads):.2f}"
            f" | mean {sum(spreads) / len(spreads):.2f} | max {max(spreads)}"
            f" | zero-spread units {sum(1 for s in spreads if s == 0)}/{len(spreads)}"
        )
        print("   every arm's medoid scores inside this range. Compare it against the")
        print("   observed cross-arm spread before concluding the corpus forced the null:")
        print("   a wide within-unit range means the arms HAD room to differ and did not.")


if __name__ == "__main__":
    raise SystemExit(main())
