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
from math import log
from pathlib import Path


def _num(value: str | None) -> float | None:
    """Return ``value`` as a float, or None when it is blank or unparsable."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _sign_test_p(better: int, disc: int) -> tuple[float, float]:
    """Exact two-sided binomial sign test on the discordant pairs, p0 = 1/2.

    The tail is summed in log space. At the Corpus A counts (disc ~ 3,700) the
    direct ratio underflows to exactly ``0.0``, and printing "p = 0" would be a
    false statement rather than a very small one.

    Parameters
    ----------
    better : int
        Discordant pairs on which the consensus is the better of the two.
    disc : int
        Total discordant pairs; ties contribute to neither side.

    Returns
    -------
    p : float
        Two-sided p-value, or ``0.0`` when it underflows double precision.
    log_two_sided : float
        Natural log of the same quantity, always finite. Report this whenever
        ``p`` has underflowed.
    """
    if disc == 0:
        return 1.0, 0.0
    from math import comb, exp

    tail = min(better, disc - better)
    terms = [log(comb(disc, i)) - disc * log(2.0) for i in range(tail + 1)]
    peak = max(terms)
    log_two_sided = peak + log(sum(exp(t - peak) for t in terms)) + log(2.0)
    p = exp(log_two_sided) if log_two_sided > -745.0 else 0.0
    return min(1.0, p), log_two_sided


def _wilson(successes: int, trials: int, z: float = 1.959963985) -> tuple[float, float]:
    """Wilson score interval -- valid at the small discordant counts seen here."""
    if trials == 0:
        return (0.0, 1.0)
    phat = successes / trials
    denom = 1 + z**2 / trials
    centre = (phat + z**2 / (2 * trials)) / denom
    half = z * ((phat * (1 - phat) / trials + z**2 / (4 * trials**2)) ** 0.5) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


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
            # Discordant pairs only: the exact two-sided sign test. Design §9
            # item 8 forbids reading a direction off a point estimate, and a
            # rank-biserial of +-0.1 on <10 discordant pairs is indistinguishable
            # from a coin. The p-value is what decides whether a direction may
            # be written down at all.
            pval, log_p = _sign_test_p(better, disc)
            lo, hi = _wilson(better, disc)
            verdict = "DIRECTIONAL" if pval < 0.05 else "null (no direction)"
            p_str = f"{pval:.3g}" if pval > 1e-300 else f"1e{log_p / log(10.0):.0f}"
            print(
                f"[{label}]   {arm:12s} {name:10s} mean {st.mean(cons):.3f} vs {st.mean(med):.3f}"
                f" | discordant {disc:4d}/{len(common)} (consensus better {better}, worse {worse})"
                f"  SD {sd:.3f}  rank-biserial {rb:+.3f}"
            )
            print(
                f"[{label}]   {'':12s} {'':10s} sign test p = {p_str}"
                f"  95% CI on P(consensus better | discordant) [{lo:.3f}, {hi:.3f}]"
                f"  -> {verdict}"
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


def winner_origin_report(rows: list[dict[str, str]], label: str) -> None:
    """Winner origin, connectivity and the pre-registered transfer bound.

    Every field here is float-serialised in the CSV (``'1.0'``, not ``'1'``), so
    the comparison goes through :func:`_num`. Three ad-hoc one-liners in this
    campaign compared such a field against an integer string and silently
    matched nothing; one of them reported a recovery rate of zero for a corpus
    whose true value was 0.279. The coercion is the point of this function.

    The pre-registered bound (T-KBf, committed before the field was read): on
    Corpus A the transfer fraction must be at least the exact-recovery rate,
    because members are non-isomorphic to the source by construction, so a run
    recovering the source exactly cannot have won with a member.

    **The bound is a check on Corpus A only.** On Corpus B the members are
    quarters 1..T-1 of a natural series and consecutive quarters are frequently
    identical, so a member winner *can* recover the truth exactly and the
    inequality is implied by nothing. It is printed for Corpus B as a
    description; its holding there is a coincidence, not a passed test.

    Parameters
    ----------
    rows : list of dict
        One RQ3 rows file.
    label : str
        Corpus name, for the printed lines.
    """
    cov = [r for r in rows if r.get("method") == "coverage" and _num(r.get("censored")) != 1.0]
    if not cov:
        print(f"[{label}] no uncensored coverage rows")
        return
    origins = Counter(str(r.get("winner_origin", "")).split(":")[0] for r in cov)
    n = len(cov)
    transfer = origins.get("transfer", 0) / n
    recovered = sum(1 for r in cov if _num(r.get("exact_recovery")) == 1.0) / n
    connected = {_num(r.get("winner_connected")) for r in cov}
    print(f"[{label}] uncensored coverage rows: {n}")
    print(f"[{label}]   winner_origin: {dict(origins)}")
    print(f"[{label}]   transfer fraction {transfer:.4f} | exact recovery {recovered:.4f}")
    print(f"[{label}]   PRE-REGISTERED transfer >= recovery: {transfer >= recovered - 1e-9}")
    print(f"[{label}]   winner_connected values: {connected}")


def structural_floor_report(rows: list[dict[str, str]], label: str) -> None:
    """Test whether the medoid axis is pinned by corpus construction, not by metric.

    On Corpus A every member is exactly ``cell_t`` constant-preserving fact edits
    from the source, so every member sits at fact distance ``t`` and none is the
    source. Any method restricted to returning an input therefore scores
    ``fact_dist = t`` and ``exact_recovery = 0`` regardless of the representation
    it ranks with. Two consequences are checked here, both falsifiable:

    1. **all** medoid arms agree on both axes in every unit -- two arms agreeing
       is consistent with coincidence, eleven agreeing is the structural claim;
    2. per-cell median ``fact_dist`` equals that cell's ``t``; a cell that
       deviates had edits cancel and needs a look.

    Raised by ``[IsalHG-Fable]`` against the reading that arm agreement said
    something about representations. It does not: it says the axis is constant.
    """
    med: dict[str, dict[str, dict[str, str]]] = {}
    for r in rows:
        if r.get("method") != "medoid" or _num(r.get("censored")) == 1.0:
            continue
        med.setdefault(r.get("collection_id", ""), {})[r.get("arm", "")] = r
    arms = sorted({a for d in med.values() for a in d})
    full = {u: d for u, d in med.items() if len(d) == len(arms)}
    print(f"[{label}] medoid arms: {len(arms)} | units with all arms: {len(full)}")
    for field in ("fact_dist", "exact_recovery"):
        agree = sum(1 for d in full.values() if len({_num(r.get(field)) for r in d.values()}) == 1)
        flag = "STRUCTURAL FLOOR" if agree == len(full) and full else "arms differ"
        print(
            f"[{label}]   all {len(arms)} arms identical on {field:15s}"
            f" {agree:5d}/{len(full)}  -> {flag}"
        )
    by_cell: dict[tuple[str, float | None], list[float]] = {}
    for d in full.values():
        row = next(iter(d.values()))
        key = (row.get("cell", ""), _num(row.get("cell_t")))
        val = _num(row.get("fact_dist"))
        if val is not None:
            by_cell.setdefault(key, []).append(val)
    if all(t is None for _, t in by_cell):
        # A natural series carries no planted edit budget, so there is no t to
        # check against and no floor to expect. Saying "DEVIATES" here would
        # invent a failure out of a corpus that simply has no such column.
        print(f"[{label}]   no cell_t: natural corpus, the floor argument does not apply")
        return
    print(f"[{label}]   per-cell median fact_dist vs the cell's t:")
    for (cell, t), vals in sorted(by_cell.items()):
        med_v = st.median(vals)
        ok = "ok" if t is not None and abs(med_v - t) < 1e-9 else "DEVIATES"
        print(f"[{label}]     {cell:28s} t={t}  median={med_v:.3f}  n={len(vals):5d}  {ok}")


def origin_recovery_crosstab(rows: list[dict[str, str]], label: str) -> None:
    """Cross-tabulate winner origin against exact recovery -- an existence check.

    A single run that both won with a *transfer* and recovered the truth exactly
    is a decoded knowledge base no member wrote that reproduces the held-out
    quarter -- something no member-returning method can do at all. Existence
    needs n = 1, not power, so this is a cross-tab and deliberately not a test.
    """
    cov = [r for r in rows if r.get("method") == "coverage" and _num(r.get("censored")) != 1.0]
    tab: Counter[tuple[str, str]] = Counter()
    for r in cov:
        origin = str(r.get("winner_origin", "")).split(":")[0] or "?"
        rec = _num(r.get("exact_recovery"))
        tab[(origin, "recovered" if rec == 1.0 else "not")] += 1
    print(f"[{label}] winner_origin x exact_recovery over {len(cov)} uncensored runs:")
    for key in sorted(tab):
        print(f"[{label}]     {key[0]:10s} {key[1]:10s} {tab[key]:5d}")
    hits = tab[("transfer", "recovered")]
    if hits:
        print(
            f"[{label}]   EXISTENCE HOLDS: {hits} run(s) won with a transfer AND "
            f"recovered the source exactly -- unreachable by any member-returning method"
        )
    else:
        print(f"[{label}]   existence FAILS: transfers occur but never land on the truth")


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
        winner_origin_report(rows, label)
        origin_recovery_crosstab(rows, label)
        structural_floor_report(rows, label)
        recovery_forensics(rows, label)

    print()
    try:
        medoid_tie_break()
    except Exception as exc:  # noqa: BLE001 - diagnostic, report and continue
        print(f"[medoid] could not inspect: {exc!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
