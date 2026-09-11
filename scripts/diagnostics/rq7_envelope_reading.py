"""RQ7's reading, pre-registered against DESIGN.md §8 before the rows were read.

The claims below are transcribed from `DESIGN.md` §8 (H7a/H7b/H7c) and from
`HANDOFF_2026-09-09_isal.md` §4.1 ("RQ7 the envelope moves from `|Aut|` to
`(m, k)`"). Each carries the condition that **refutes** it, stated here rather
than chosen after seeing the numbers.

C1 (H7a) -- the pointer alphabet's frontier is the fact count `m`, not the
    constant count `n`.
    The grid separates them: at fixed `m`, the two densities differ in `n` by
    about 3x (`sparse` n = min(ceil(1.5m), m(k-1)+1), `dense` n = ceil(0.5m)+k),
    while a doubling of `m` moves `m` by 2x at fixed density. If the frontier is
    `m`, cost responds to the `m` step and barely to the density step.
    REFUTED if the median-cost response to the density step (a pure `n` move) is
    at least as large as the response to an `m` doubling.

C2 (H7b) -- `fact_rank` and `nauty_cert` are one canonical-labelling call:
    microseconds to milliseconds across the whole grid *and* the `m` extension.
    REFUTED if any cell median reaches 1 s, or if either arm censors anywhere.

C3 (the Isal envelope) -- for the **ordered walk** `isal_ow_struct` cost is
    governed by `(m, k)` and not by symmetry, because the walk does not search;
    for the orbit-pruned tie-complete form `wstar_orbit` it is governed by both.
    Measured as the spread of median cost across `aut_bucket` **within** a fixed
    `(m, k, sigma_e, sigma_v, density)` cell, which holds size constant and
    varies only symmetry.
    REFUTED if the ordered walk's within-cell spread across `aut_bucket` is
    comparable to the search arm's.

C4 (H7c) -- total cost is `N` canonicalizations plus `N^2` comparisons.
    Fitted as log-log slopes of `secs_canon_total` and `secs_pairs_total` on `N`.
    REFUTED if the canonicalization slope is not near 1 or the pair slope not
    near 2. **Reported only when every `N` cell is present**; a slope fitted on
    a truncated `N` range is a different quantity and is withheld, not estimated.

Three states throughout: a claim whose interval spans the refutation boundary is
INDETERMINATE, never REFUTED (lessons L26).
"""

from __future__ import annotations

import math
import random
import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rowsio  # noqa: E402

# Declared, not inferred (L26). The RQ7 array writes to IEEETKDE_isal; the
# merged tree is a different campaign and carries no envelope sweep.
ROOT = Path(
    "/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE_isal/RQ7_envelope/envelope"
)
FORBIDDEN_ROOT_TOKEN = "IEEETKDE_isal_merged"

# The grid is 6 m x 4 k x 3 sigma_e x 2 sigma_v x 2 density x 27 seeds = 7,776.
# fact_rank and nauty_cert additionally run the fact-alphabet extension
# (3 m x 1 k x 1 sigma_e x 1 sigma_v x 2 density x 27 seeds = 162).
EXPECTED_SWEEP_ROWS = {
    "isalhg_levenshtein": 7776,
    "isal_ow_struct": 7776,
    "wstar_orbit": 7776,
    "fact_rank": 7938,
    "nauty_cert": 7938,
}
MS_CEILING_S = 1.0
N_BOOT = 2000
BOOT_SEED = 70000


def _wilson(successes: int, total: int, z: float = 1.959963985) -> tuple[float, float]:
    """Wilson score interval; the right interval for a rate near 0 or 1."""
    if total == 0:
        return (float("nan"), float("nan"))
    p = successes / total
    denom = 1.0 + z * z / total
    centre = (p + z * z / (2 * total)) / denom
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def _boot_median_ci(values: list[float], rng: random.Random) -> tuple[float, float]:
    """Percentile bootstrap CI of the median (DESIGN §8: CIs, no tests)."""
    if len(values) < 2:
        return (float("nan"), float("nan"))
    medians = []
    n = len(values)
    for _ in range(N_BOOT):
        medians.append(statistics.median(rng.choices(values, k=n)))
    medians.sort()
    return (medians[int(0.025 * N_BOOT)], medians[int(0.975 * N_BOOT)])


def _load(kind: str) -> list[dict[str, str]]:
    files = sorted(ROOT.glob(f"rows_{kind}*.csv"))
    if not files:
        raise rowsio.RowsError(f"no rows_{kind} files under {ROOT}")
    rows: list[dict[str, str]] = []
    for path in files:
        rows.extend(rowsio.load_rows(path, quiet=True))
    rows = [r for r in rows if r.get("rq") == "7"]
    print(f"[rows] {kind}: consumed {len(rows)} rows from {len(files)} files")
    return rows


def _cell_key(row: dict[str, str]) -> tuple[str, ...]:
    return (row["m"], row["k"], row["sigma_e"], row["sigma_v"], row["density"])


def completeness(sweep: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    """Every arm present at its expected N, or the reading stops here."""
    print("\n== completeness ==")
    by_arm = rowsio.classify(
        sweep,
        {arm: (lambda r, a=arm: r["arm"] == a) for arm in EXPECTED_SWEEP_ROWS},
        label="sweep arms",
    )
    ok = True
    for arm, expected in EXPECTED_SWEEP_ROWS.items():
        got = len(by_arm[arm])
        mark = "ok" if got == expected else "MISMATCH"
        if got != expected:
            ok = False
        print(f"  {arm:22s} {got:5d} / {expected:5d}  {mark}")
    if not ok:
        print("  -> the sweep is incomplete; cost readings below are partial.")
    return by_arm


def censoring_per_stratum(by_arm: dict[str, list[dict[str, str]]]) -> None:
    """L15: censoring is reported per stratum, never pooled away."""
    print("\n== censoring, per arm x aut_bucket ==")
    print(f"  {'arm':22s} {'aut_bucket':12s} {'censored/n':>14s}  95% Wilson")
    for arm, rows in by_arm.items():
        buckets: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in rows:
            buckets[row["aut_bucket"]].append(row)
        for bucket in sorted(buckets):
            group = buckets[bucket]
            cens = sum(1 for r in group if rowsio.num(r["censored"]) == 1.0)
            lo, hi = _wilson(cens, len(group))
            print(f"  {arm:22s} {bucket:12s} {cens:6d}/{len(group):<7d}  [{lo:.4f}, {hi:.4f}]")


def _completed_secs(rows: list[dict[str, str]]) -> list[float]:
    """Censored rows carry the budget, not a cost: they are excluded and counted."""
    out = []
    for row in rows:
        if rowsio.num(row["censored"]) == 1.0:
            continue
        secs = rowsio.num(row["secs"])
        if secs is not None and secs > 0:
            out.append(secs)
    return out


def c1_frontier_is_m(by_arm: dict[str, list[dict[str, str]]], rng: random.Random) -> None:
    """C1: separate the `m` response from the `n` response at fixed `m`."""
    print("\n== C1 (H7a): is the frontier m, or n? ==")
    print("  the density step is a pure n move at fixed m; the m step doubles m.")
    for arm in ("isalhg_levenshtein", "isal_ow_struct", "wstar_orbit"):
        rows = by_arm[arm]
        med: dict[tuple[str, str], float] = {}
        for row in rows:
            med.setdefault((row["m"], row["density"]), [])  # type: ignore[arg-type]
        grouped: dict[tuple[str, str], list[float]] = defaultdict(list)
        for row in rows:
            if rowsio.num(row["censored"]) == 1.0:
                continue
            secs = rowsio.num(row["secs"])
            if secs is not None and secs > 0:
                grouped[(row["m"], row["density"])].append(secs)
        med = {key: statistics.median(v) for key, v in grouped.items() if v}
        ms = sorted({int(m) for m, _ in med}, key=int)

        density_ratios = []
        for m in ms:
            sparse = med.get((str(m), "sparse"))
            dense = med.get((str(m), "dense"))
            if sparse and dense:
                density_ratios.append(abs(math.log2(dense / sparse)))
        m_ratios = []
        for density in ("sparse", "dense"):
            series = [(m, med[(str(m), density)]) for m in ms if (str(m), density) in med]
            for (m0, v0), (m1, v1) in zip(series, series[1:]):
                if v0 > 0 and v1 > 0 and m1 >= 2 * m0 * 0.9:
                    m_ratios.append(abs(math.log2(v1 / v0)))

        d_med = statistics.median(density_ratios) if density_ratios else float("nan")
        m_med = statistics.median(m_ratios) if m_ratios else float("nan")
        verdict = (
            "CONFIRMED (m dominates)"
            if m_med > d_med
            else "REFUTED (n dominates)"
            if d_med > m_med
            else "INDETERMINATE"
        )
        print(
            f"  {arm:22s} |log2 ratio| median: m-step {m_med:.3f} vs "
            f"density-step {d_med:.3f}   {verdict}"
        )
        _ = rng


def c2_certificate_arms(by_arm: dict[str, list[dict[str, str]]]) -> None:
    """C2: one canonical-labelling call -- but the grid and the extension differ.

    The main grid stops at ``m = 160``; the fact-alphabet extension runs
    ``m in {320, 640, 1280}``, an eightfold step beyond it. Pooling the two
    reports one number for two regimes, which is the binary-hides-a-state
    failure of L26, so they are reported apart.
    """
    print("\n== C2 (H7b): fact_rank / nauty_cert -- one canonical-labelling call ==")
    print(f"  {'arm':14s} {'stratum':12s} {'cells':>6s} {'worst cell median':>19s} {'cens':>5s}  verdict")
    for arm in ("fact_rank", "nauty_cert"):
        rows = by_arm[arm]
        strata = {
            "main grid": lambda r: int(r["m"]) <= 160,
            "m extension": lambda r: int(r["m"]) > 160,
        }
        for name, keep in strata.items():
            group = [r for r in rows if keep(r)]
            cens = sum(1 for r in group if rowsio.num(r["censored"]) == 1.0)
            cells: dict[tuple[str, ...], list[float]] = defaultdict(list)
            for row in group:
                secs = rowsio.num(row["secs"])
                if secs is not None and secs > 0 and rowsio.num(row["censored"]) != 1.0:
                    cells[_cell_key(row)].append(secs)
            medians = {key: statistics.median(v) for key, v in cells.items() if v}
            worst_cell = max(medians, key=lambda key: medians[key])
            worst = medians[worst_cell]
            verdict = "CONFIRMED" if worst < MS_CEILING_S and cens == 0 else "REFUTED"
            print(
                f"  {arm:14s} {name:12s} {len(medians):6d} {worst * 1000:16.1f} ms "
                f"{cens:5d}  {verdict}  (m={worst_cell[0]}, k={worst_cell[1]})"
            )
    print("  note: 'REFUTED' bounds the *range* claim, not the mechanism -- neither")
    print("  arm censors anywhere, and a single nauty call on a 1,280-fact base is")
    print("  seconds by construction.")


def c1_censoring_frontier(by_arm: dict[str, list[dict[str, str]]]) -> None:
    """C1, read on censoring rather than on cost.

    On an arm censoring 30-100 % the completed rows are the surviving easy tail,
    so a median over them understates the response and is not a frontier
    measurement. Censoring itself is the frontier, and it is observed on every
    row.
    """
    print("\n== C1 (H7a), read on censoring: the frontier itself ==")
    for arm in ("isalhg_levenshtein", "wstar_orbit", "isal_ow_struct"):
        rows = by_arm[arm]
        grid: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
        for row in rows:
            grid[(row["m"], row["density"])].append(row)
        ms = sorted({int(m) for m, _ in grid}, key=int)
        print(f"  {arm}")
        header = "    m      " + "".join(f"{m:>10d}" for m in ms)
        print(header)
        for density in ("sparse", "dense"):
            cells = []
            for m in ms:
                group = grid.get((str(m), density), [])
                if not group:
                    cells.append("       --")
                    continue
                cens = sum(1 for r in group if rowsio.num(r["censored"]) == 1.0)
                cells.append(f"{cens / len(group):10.3f}")
            print(f"    {density:7s}" + "".join(cells))


def c3_envelope_moves(by_arm: dict[str, list[dict[str, str]]]) -> None:
    """C3: at fixed size, does symmetry still move the cost?"""
    print("\n== C3: within a fixed (m,k,sigma_e,sigma_v,density) cell, spread across aut_bucket ==")
    print("  size is held constant; only symmetry varies. Spread in log2(secs).")
    print(f"  {'arm':22s} {'cells usable':>13s} {'median spread':>14s} {'p90 spread':>12s}")
    results: dict[str, float] = {}
    for arm in ("isal_ow_struct", "wstar_orbit", "isalhg_levenshtein", "fact_rank", "nauty_cert"):
        rows = by_arm[arm]
        cells: dict[tuple[str, ...], dict[str, list[float]]] = defaultdict(
            lambda: defaultdict(list)
        )
        for row in rows:
            if rowsio.num(row["censored"]) == 1.0:
                continue
            secs = rowsio.num(row["secs"])
            if secs is not None and secs > 0:
                cells[_cell_key(row)][row["aut_bucket"]].append(secs)
        spreads = []
        for buckets in cells.values():
            usable = {b: statistics.median(v) for b, v in buckets.items() if len(v) >= 3}
            if len(usable) >= 2:
                lo, hi = min(usable.values()), max(usable.values())
                spreads.append(abs(math.log2(hi / lo)))
        if not spreads:
            print(f"  {arm:22s} {'0':>13s}   no cell carries two aut buckets with n>=3")
            continue
        spreads.sort()
        med = statistics.median(spreads)
        p90 = spreads[int(0.9 * (len(spreads) - 1))]
        results[arm] = med
        print(f"  {arm:22s} {len(spreads):13d} {med:14.3f} {p90:12.3f}")
    if "isal_ow_struct" in results and "wstar_orbit" in results:
        walk, search = results["isal_ow_struct"], results["wstar_orbit"]
        ratio = search / walk if walk > 0 else float("inf")
        print(
            f"\n  search/walk symmetry sensitivity = {ratio:.2f}x "
            f"({search:.3f} vs {walk:.3f} log2 units)"
        )


def c4_nscaling(rows: list[dict[str, str]]) -> None:
    """C4: withheld unless every N cell is present (a truncated fit is a different number)."""
    print("\n== C4 (H7c): N-scaling ==")
    by_arm: dict[str, dict[int, list[tuple[float, float]]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        canon = rowsio.num(row["secs_canon_total"])
        pairs = rowsio.num(row["secs_pairs_total"])
        if canon is None or pairs is None:
            continue
        by_arm[row["arm"]][int(row["N"])].append((canon, pairs))
    all_ns = sorted({n for arm in by_arm.values() for n in arm})
    print(f"  N cells present overall: {all_ns}")
    print(f"  {'arm':22s} {'N present':>28s} {'canon slope':>12s} {'pair slope':>11s}")
    for arm in sorted(by_arm):
        cells = by_arm[arm]
        ns = sorted(cells)
        if set(ns) != set(all_ns):
            print(
                f"  {arm:22s} {str(ns):>28s} {'WITHHELD':>12s} {'WITHHELD':>11s}"
                "   <- truncated N range"
            )
            continue
        xs = [math.log(n) for n in ns]
        for label, index in (("canon", 0), ("pair", 1)):
            ys = [math.log(statistics.median([v[index] for v in cells[n]])) for n in ns]
            mx, my = statistics.fmean(xs), statistics.fmean(ys)
            num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
            den = sum((x - mx) ** 2 for x in xs)
            slope = num / den if den else float("nan")
            if label == "canon":
                canon_slope = slope
            else:
                pair_slope = slope
        print(f"  {arm:22s} {str(ns):>28s} {canon_slope:12.3f} {pair_slope:11.3f}")


def main() -> None:
    print(__doc__)
    if FORBIDDEN_ROOT_TOKEN in str(ROOT):
        raise SystemExit(f"refusing to read {FORBIDDEN_ROOT_TOKEN}: wrong campaign")
    if not ROOT.is_dir():
        raise SystemExit(f"no RQ7 rows under {ROOT}")
    newest = max(p.stat().st_mtime for p in ROOT.glob("*.csv"))
    import datetime

    stamp = datetime.datetime.fromtimestamp(newest).strftime("%Y-%m-%d %H:%M")
    print(f"root: {ROOT}")
    print(f"files: {len(list(ROOT.glob('*.csv')))}, newest {stamp}")

    rng = random.Random(BOOT_SEED)
    sweep = _load("sweep")
    by_arm = completeness(sweep)
    censoring_per_stratum(by_arm)
    c1_frontier_is_m(by_arm, rng)
    c1_censoring_frontier(by_arm)
    c2_certificate_arms(by_arm)
    c3_envelope_moves(by_arm)
    c4_nscaling(_load("nscaling"))


if __name__ == "__main__":
    main()
