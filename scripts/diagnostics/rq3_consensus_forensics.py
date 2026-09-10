"""What the RQ3 consensus rows say about the word tie-break and the winner's origin.

Five questions, all answerable from rows already on disk, asked before anything is
re-run:

1. how often the winning candidate is a member rather than a transferred object
   -- if it is a member, Corpus B never exercised RQ3's claim;
2. the ``n_ties`` distribution -- a run with ``n_ties = 0`` never invoked the
   lexicographic word rule and is therefore invariant-neutral, so it stands
   unchanged under any complete invariant;
3. the discordant-pair count on the recovery axis, with paired SD and
   rank-biserial, so a null is reported with an effect size;
4. how many candidates are disconnected, i.e. outside the representation's
   domain (R3, Prop. C.4);
5. whether the medoid carries a lexicographic tie-break of its own.

Raised by the ``[IsalHG-Fable]`` session against the D-KBf5a gate.
"""

from __future__ import annotations

import argparse
import csv
import inspect
import statistics as st
from collections import Counter
from pathlib import Path
from typing import Any


def _num(value: Any) -> float | None:
    """Return ``value`` as a float, or None when it is blank or unparsable."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def load(path: Path) -> list[dict[str, str]]:
    """Read one rows CSV."""
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def n_ties_report(rows: list[dict[str, str]], label: str) -> None:
    """Print how often the word tie-break could have decided the winner."""
    cons = [r for r in rows if r.get("method") == "coverage" and r.get("censored") != "1"]
    ties = [_num(r.get("n_ties")) for r in cons]
    ties = [t for t in ties if t is not None]
    if not ties:
        print(f"[{label}] no consensus rows carrying n_ties")
        return
    zero = sum(1 for t in ties if t == 0)
    dist = Counter(int(t) for t in ties)
    print(f"[{label}] consensus rows: {len(cons)}  with n_ties: {len(ties)}")
    print(f"[{label}]   n_ties == 0 (tie-break never fired): {zero} of {len(ties)}")
    print(f"[{label}]   distribution: {dict(sorted(dist.items())[:10])}")
    cands = [_num(r.get("n_candidates")) for r in cons]
    cands = [c for c in cands if c is not None]
    if cands:
        print(f"[{label}]   candidates per run: median {st.median(cands):.0f} max {max(cands):.0f}")


def recovery_forensics(rows: list[dict[str, str]], label: str) -> None:
    """Paired discordance, SD and rank-biserial for consensus vs each medoid arm."""
    by: dict[tuple[str, str, str], tuple[float | None, float | None]] = {}
    for r in rows:
        if r.get("censored") == "1" or r.get("method") == "medoid_survivors":
            continue
        by[(r.get("collection_id", ""), r.get("method", ""), r.get("arm", ""))] = (
            _num(r.get("fact_dist")),
            _num(r.get("exact_recovery")),
        )
    units = sorted({k[0] for k in by})
    arms = sorted({r["arm"] for r in rows if r.get("method") == "medoid" and r.get("arm")})
    common = [
        u
        for u in units
        if by.get((u, "coverage", "fact_rank"))
        and by[(u, "coverage", "fact_rank")][0] is not None
        and all(by.get((u, "medoid", a)) and by[(u, "medoid", a)][0] is not None for a in arms)
    ]
    if not common:
        print(f"[{label}] no common units")
        return
    print(f"[{label}] common units: {len(common)}")
    for arm in ("wl_l1", "wstar_orbit"):
        if arm not in arms:
            continue
        # fact distance: lower is better. recovery: higher is better. The sign
        # convention differs per axis and getting it wrong inverts the reading.
        for idx, name, lower_is_better in ((0, "fact_dist", True), (1, "recovery", False)):
            cons = [by[(u, "coverage", "fact_rank")][idx] for u in common]
            med = [by[(u, "medoid", arm)][idx] for u in common]
            diffs = [c - m for c, m in zip(cons, med, strict=True)]
            better = sum(1 for d in diffs if (d < 0) is lower_is_better and d != 0)
            worse = sum(1 for d in diffs if d != 0) - better
            disc = better + worse
            sd = st.pstdev(diffs) if len(set(diffs)) > 1 else 0.0
            rb = (better - worse) / disc if disc else 0.0
            print(
                f"[{label}]   {arm:12s} {name:10s} mean {st.mean(cons):.3f} vs {st.mean(med):.3f}"
                f" | discordant {disc:4d}/{len(common)} (consensus better {better}, worse {worse})"
                f"  SD {sd:.3f}  rank-biserial {rb:+.3f}"
            )


def medoid_tie_break() -> None:
    """State whether the medoid carries a lexicographic fallback of its own."""
    import importlib

    from isalhg.metric_space.toolkit import medoid as medoid_fn

    module = importlib.import_module(medoid_fn.__module__)
    source = inspect.getsource(medoid_fn)
    lex = any(token in source for token in ("lexicograph", "word", "tie_break", "tiebreak"))
    print(f"[medoid] defined in: {module.__file__}")
    print(f"[medoid] mentions a lexicographic/word tie-break: {lex}")
    for line in source.splitlines():
        if any(t in line for t in ("argmin", "min(", "argsort", "[0]")):
            print("   ", line.strip()[:110])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-a", type=Path, help="rows_variants.csv")
    parser.add_argument("--corpus-b", type=Path, help="rows_natural.csv")
    args = parser.parse_args()

    for label, path in (("corpus_a", args.corpus_a), ("corpus_b", args.corpus_b)):
        if path is None or not path.is_file():
            print(f"[{label}] absent")
            continue
        rows = load(path)
        print(f"\n===== {label}: {len(rows)} rows =====")
        n_ties_report(rows, label)
        recovery_forensics(rows, label)

    print()
    try:
        medoid_tie_break()
    except Exception as exc:  # noqa: BLE001 - diagnostic, report and continue
        print(f"[medoid] could not inspect: {exc!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
