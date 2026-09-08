# rq1-stats — confidence intervals and corrected tests for the RQ1 tables

Wave `2026-09-08-isal-kb-w7`. Branch `worktree-agent-a81c40ef5040868a6`
(cut from `feature/isal-kb-word`).

## What was built

Two new files, nothing else touched:

- `scripts/tkde/rq1_statistics.py` — the analysis script.
- `tests/unit/experiments/test_rq1_statistics.py` — 31 unit tests on synthetic
  frames.

The script puts intervals and Holm-corrected tests on the M1, M2 and M4 rows of
`RQ1_addressing/addressing`, after two corrections the published tables do not
make: it restricts every comparison to the units all published arms completed,
and it resamples clusters rather than rows.

## The exact CLI

```bash
~/.conda/envs/isalhg/bin/python scripts/tkde/rq1_statistics.py \
  --root  <results root> \
  --experiment addressing \
  --out   <results root>/RQ1_addressing/addressing/rq1_statistics.md \
  --json  <results root>/RQ1_addressing/addressing/rq1_statistics.json \
  --resamples 2000 \
  --seed 0
```

Optional flags: `--measures m1 m2 m4` (subset), `--arms ...` (override the
published set), `--reference wstar_orbit`, `--no-strict-cluster-structure`
(downgrade the inventory assertions to warnings — use only if the campaign is
re-run at a different size).

The script reads `<root>/RQ1_addressing/<experiment>/rows_{m1,m2,m4}__*.csv`
and writes only the two output paths. It never writes into the rows tree.

## Statistical choices

**The restriction.** `restrict_to_common_units` keeps a unit only when every
published arm has a row for it with a finite response (censored rows are dropped
first). Without it each arm is scored on its own completed subset, and
`wstar_orbit` is compared against arms measured on easier instances. The
per-arm unit counts before the intersection and the intersection size are
printed in every section, so the cost of the restriction is visible. An arm that
is absent from the rows entirely is dropped from the requirement and named in
the report rather than emptying the intersection.

**Cluster keys** (measured inventory supplied by the coordinator, asserted by
the script, not inferred):

| table | cluster | key |
|---|---|---|
| m1 | entity | `collection :: base_id.split("@")[0]` |
| m2 `ladder` | ladder | `pair_id.split("|")[0]` |
| m2 `natural` | entity | `pair_id.split("@")[0]` |
| m4 | pair | `pair_id` |

M1 and M2-natural keys are namespaced by collection (and series) because entity
ids are only unique inside a collection and the M1 cells pool collections.

The M2 ladder key was read off `rq1.py:946`, `pair_id = f"{base.kb_id}|t{t}"`,
so the prefix before `"|"` is the base knowledge base. The natural key was read
off `rq1.py:891`, `pair_id = f"{a_id}|{b_id}"` with `a_id = "<entity>@<quarter>"`
— the cluster is the entity, not the pair, because one entity contributes up to
37 consecutive-quarter pairs.

**Structural assertions.** `check_m1_structure` asserts 171 / 2000 / 3988
entities for ndc_classes / synthetic_rq1 / wd50k66, plus the sibling check that
ndc_classes must strictly coarsen (clusters < members). `check_m2_structure`
asserts 1,000 ladders of exactly 5 rungs each with `seed` inducing the identical
partition, and 61 natural entities (50 in regime 0, 39 in regime 1). Both raise
by default. `guard_parse_failure` raises whenever an M2 group has as many
clusters as rows on ≥ 3 rows, which is what a key that failed to parse looks
like. It is scoped to M2: M4's cluster legitimately is the row.

**M1 aggregation.** Two steps before any resampling, per the coordinator's
correction: rows → `(member, edit_kind)` (median `d_instr`; fraction of that
member's edits within two tokens) → entity (median of the member-level values).
Entities are the resampling unit and the pairing key.

**M1 intervals.**
- Median `d_instr`: point is the pooled median over rows (the number the
  published table prints); the interval is `bca_ci(per-entity values,
  stat="median")`. This is exactly the repo's own `analyze_rq1.cluster_median_ci`
  convention. The two are not the same functional when clusters differ in size,
  so the `method` string says which one the bounds came from.
- Within-≤2 fraction: a genuine cluster bootstrap of the *ratio*. Each replicate
  draws entities with replacement and recomputes `Σ successes / Σ rows` over the
  drawn entities; BCa from the replicate bias correction plus a
  leave-one-entity-out jackknife acceleration. **Why not compose `bca_ci` over
  per-cluster fractions**, as the brief suggested: the unweighted mean of
  per-entity fractions is a different estimand from the pooled fraction whenever
  entity sizes differ, and on ndc_classes they differ by a factor of 47, so the
  interval would not bound the point estimate the table reports. The ratio
  bootstrap is fully vectorised (chunked `(replicates, clusters)` integer draws,
  no per-row Python loop).

**M1 tests.** Paired Wilcoxon of `wstar_orbit` against each other arm on the
per-entity values, Holm-corrected across the arms *within one (regime, edit_kind,
statistic) family* — the reference is never compared against itself. Effect size
is the matched-pairs rank-biserial from `stats.wilcoxon_paired`. Two families per
cell: the response (per-entity median `d_instr`) and the within-≤2 fraction.
`paired_cluster_family` composes `wilcoxon_paired` + `bca_ci` + `holm` the way
`stats.paired_family` does, but honours `--resamples`/`--seed` instead of that
function's hardcoded 10,000 (which would have been ~40 min of bootstrap on the
real entity counts for no gain).

**M2.** Per `(collection, series, regime)`: `stats.spearman_ci(delta, d,
clusters=...)` per arm; then the paired difference `ρ_ref − ρ_arm` with a cluster
bootstrap that draws clusters once per replicate and recomputes **both**
correlations on that same resample — the point of a paired difference. Interval
is percentile; the p-value is the standard two-sided bootstrap p,
`2·min(#{Δ≤0}, #{Δ≥0}) + 1) / (R+1)`, Holm-corrected across the arms of the
group. Spearman inside the bootstrap is computed as Pearson on midranks
(`spearman_rho`) rather than through `scipy.stats.spearmanr`, whose p-value
machinery is dead weight at 4,000 calls per arm; the test suite pins it against
scipy.

**M4.** Per collection, `spearman_ci` of each arm's `d` against
`nauty_cert_rows`' `d` on the same pairs, clustered on `pair_id`. Because M4 has
one row per pair per arm this cluster bootstrap coincides with the i.i.d. one;
it is kept for uniformity of the reported `method`. `nauty_cert_rows` appears as
a ρ = 1.000 sanity row.

**Coverage guard.** Every interval is widened to contain its point estimate.
This only ever binds on a near-degenerate discrete statistic (all replicates
equal); it is recorded here because it is a deliberate departure from raw
percentile output.

**Expected non-significance.** The three `isal_ow_*` arms are expected not to
separate — the script reports that as a non-rejection, and no alternative test
was substituted to manufacture one.

## What was tested

`tests/unit/experiments/test_rq1_statistics.py`, `pytestmark =
pytest.mark.unit`, 31 tests, all on synthetic frames built in the file. The
script is imported by path (`scripts/` is not a package), with the module
registered in `sys.modules` before execution so `@dataclass` can resolve its
annotations.

Covered: the restriction really intersects (an arm censored on some units shrinks
every arm's n to the same value; a missing arm is reported rather than required;
an empty intersection raises); the entity/ladder keys and each structural guard,
including the "one cluster per row means the key did not parse" raise and its
strict/non-strict behaviour; clustering widens the interval (a frame whose
cluster rows are identical gives a strictly wider fraction CI than treating the
rows as independent); Holm is applied across the right family with the reference
excluded, and the smallest raw p is multiplied by the family size; the within-≤2
CI is inside [0, 1] and covers the point; degenerate inputs (one cluster,
constant `delta`, empty input, constant predictor) return `None` or a
`degenerate_*` payload rather than raising; `spearman_rho` matches scipy;
identical arms give p = 1 and no rejection; the rendered Markdown carries
`n_clusters`, the seed and the units sentence under every table.

An end-to-end CLI run was also exercised against a synthetic tree written to the
scratchpad (not committed): 840 m1 rows / 300 m2 rows / 75 m4 rows, five arms,
`--resamples 300`. It produced the full Markdown and JSON, including the M2
ladder and natural sections and the M4 table.

## Verification

```
python -m pytest tests/unit/experiments/test_rq1_statistics.py -q   31 passed
python -m pytest tests/unit/experiments/ -q                         54 passed
python -m ruff check scripts/tkde/rq1_statistics.py \
                     tests/unit/experiments/test_rq1_statistics.py  All checks passed!
python -m mypy scripts/tkde/rq1_statistics.py                       clean for this file
```

mypy reports two pre-existing errors in `experiments/tkde/stats.py:359`
(`paired_family` passes ndarrays where `wilcoxon_paired` declares
`Sequence[float]`); that file is not mine and was not touched. Repo-wide `ruff
check` reports 312 pre-existing errors elsewhere; none in the two new files.

Environment: `~/.conda/envs/isalhg-rq1stats` (cloned from `isalhg`, editable
install inside this worktree).

## Residual risk

1. **The inventory constants are hardcoded.** 171 / 2000 / 3988 entities, 1,000
   ladders × 5 rungs, 61 / 50 / 39 natural entities. If the campaign is re-run at
   a different corpus size, every assertion fires. That is deliberate — the
   alternative is a key that silently mis-parses — but the operator needs
   `--no-strict-cluster-structure` to know it is the escape hatch.
2. **The median CI's estimand.** Point pooled over rows, interval over
   per-entity medians. Inherited from `analyze_rq1.cluster_median_ci` for
   consistency with the rest of the campaign, but it is not a bootstrap of the
   pooled median. The `method` string names it; a reviewer who wants the pooled
   median bootstrapped exactly needs a weighted-quantile replicate, which was not
   built.
3. **The M2 difference p-value is a bootstrap p, not an exact test.** With 2,000
   replicates the floor is p ≈ 1.0 × 10⁻³, so a genuinely tiny difference-p
   cannot be resolved below that. Raise `--resamples` if a Holm-corrected
   M2 difference lands near the floor and the exact magnitude matters.
4. **Untested against the real tree.** Everything here ran on synthetic frames
   only, by instruction. The first real run may hit an inventory assertion or a
   column-dtype surprise (`censored` is object-typed in the shards and is
   normalised defensively, but `d_instr`/`d`/`delta` coercion is
   `errors="coerce"`, so a malformed value becomes a silently dropped unit
   rather than an error).
5. **Runtime.** Dominated by `stats.spearman_ci`, whose replicate loop is
   per-cluster Python; on the 1,000-ladder group at 2,000 resamples expect a few
   minutes per arm. The M1 path is vectorised and fast.
