# T-KBad — provenance: where did T-KBf's `wstar_orbit` RQ5 numbers come from?

**Status:** OPEN (2026-09-14 10:02 CEST) · filed by agent `rq8`, wave
`2026-09-13-headline-w0`, on the orchestrator's instruction. **Filed, not
investigated** — this agent was told to record the question and stop.
**Update 2026-10-04 10:20 CEST (agent `harvest`, wave `2026-10-04-harvest`):
provenance located (checks 1–3 done, below); left OPEN because the numbers T-KBf
attributes to `wstar_orbit` are another arm's, the real `wstar_orbit` rows say
something different and unexplained, and check 4 is a decision this agent does
not own.**

## What was found

While re-running RQ5 on the ordered walk (T-KBab) the `wstar_orbit` comparison
the brief asked for could not be made, because:

- **`wstar_orbit` appears in 0 of 54** campaign RQ5 clustering row files under
  `results/IEEETKDE/RQ5_patterns/rows/rows_clustering__*balanced*.csv`.
  Measured by `grep -l wstar_orbit ... | wc -l` → `0`.
- The arms actually present in those rows are: `bipartite_ged_assign`,
  `bipartite_ged_path`, `degree_seq_l1`, `fact_rank`, `fact_rank_roles`,
  `hpd_jsd`, `nauty_cert`, `nauty_cert_rows`, `netlsd`, `size_l1`, `wl_l1`.
  Note `fact_rank_roles` **is** there — an arm D-ART4 (1) retired — which
  suggests these rows predate some config revisions.
- **`experiments/tkde/configs/rq5.yaml` lists `wstar_orbit` in all three
  experiments** (lines 26, 45, 64). So the config and the rows disagree.

## Why it matters

The RQ5 fact base referenced from T-KBf quotes `wstar_orbit` numbers. If those
numbers were not produced by the rows now on the drive, then either they came
from a run whose rows are elsewhere (or were superseded), or they were carried
over from a different experiment. Until that is settled, **any prose that cites a
`wstar_orbit` RQ5 number is citing something whose derivation is not currently
locatable**, which is exactly the failure `docs/article/DEVELOPMENT/README.md`
records for an earlier round ("lost the inputs a table was computed from, and no
reader could recompute it").

This is a provenance question only. Nothing about the `w°` swap depends on it:
T-KBab substituted a full-field comparison recomputed from the campaign's own
rows with identical aggregation, and every arm the two runs share reproduces to
four decimals (e.g. `bipartite_ged_assign` 0.0379 / 0.2305 / 0.5176 in both),
which is a stronger cross-check than the single-arm delta would have been.

## Candidate explanations, none verified

1. **The campaign RQ5 predates the config.** `wstar_orbit` was added to
   `rq5.yaml` after the rows were produced, and no re-run followed. The presence
   of `fact_rank_roles` in the rows is consistent with them being old.
2. **The arm was dropped at run time.** RQ5 reads cached `N × N` matrices;
   `wstar_orbit`'s matrices carry `.censored.json` companions in every
   collection (20–57 KB), so a censored member set may have removed the arm
   rather than the runner refusing.
3. **The T-KBf numbers come from a different results root.** Several exist:
   `IEEETKDE_isal`, `_isal_consensus`, `_isal_merged`, `_isal_preview`,
   `_isal_reach1`, `_isal_reach1b`, `_isal_reachprime`.

## The check the next agent must run

1. Locate every `rows_clustering__*.csv` under **all** `results/IEEETKDE*` roots
   (local drive and `~/results/` on Picasso) that contains `wstar_orbit`, and
   read its `manifest.json` for the job id, git SHA and `run_tag`.
2. Compare that `run_tag` against `run_tag(load_yaml("configs/rq5.yaml"))` at
   the SHA the manifest names. A mismatch says the numbers were produced under a
   different configuration than the one now in the tree.
3. Cross-check the quoted T-KBf values against whatever rows are found. If none
   match, the fact base's `wstar_orbit` RQ5 row must be marked
   **derivation not locatable** rather than silently kept.
4. Decide whether `wstar_orbit` should be re-run for RQ5 at all. Under D-ART6 it
   appears only in RQ1's four-cell ablation, so the answer may be no — in which
   case remove it from `rq5.yaml` so the config stops promising an arm nothing
   produces.

## Context

- T-KBab (the `w°` swap) and `../../../D_ART3/foundation/rq5_ow_facts.md` §3,
  which records the absence and what was substituted.
- The RQ5_ow run that surfaced it: job 2308368, 65 units, COMPLETED.

## Finding (2026-10-04, agent `harvest`)

**Check 1 — where `wstar_orbit` RQ5 rows exist.** `rows_clustering__*.csv`
under every `results/IEEETKDE*` root, drive and Picasso `~/results/` alike
(identical counts on both):

| root | clustering files | containing `wstar_orbit` |
|---|---|---|
| `IEEETKDE` (the campaign this task names) | 66 | 0 |
| **`IEEETKDE_isal`** | 66 (65 under `RQ5_patterns/rows/`) | **55 of the 65** (27 + 27 balanced seed files, 1 full-collection file) |
| `IEEETKDE_ow` | 66 (Picasso 65) | 0 |
| `_isal_consensus`, `_isal_merged`, `_isal_preview`, `_isal_reach1`, `_isal_reach1b`, `_isal_reachprime` | 0 | 0 |

**Check 2 — the run and its configuration.** `IEEETKDE_isal/RQ5_patterns/shard_0_1/manifest.json`:
job **2265389** (T-KBf's "RQ5 full", line 771), git **`afab7c5`**, 65 units,
2026-09-09 11:15–12:20 UTC, `matrices_root …/IEEETKDE_isal`. RQ5 rows carry **no
run tag** (`"tag": ""`), so the `run_tag` comparison this task asked for cannot
be made; the configuration was compared instead. `configs/rq5.yaml` at
`afab7c5` lists `wstar_orbit` in all three experiments. `wstar_orbit` entered
`rq5.yaml` at **`4c3eaeb`** (2026-09-09, "apply the D-ART5 arm set to RQ2-RQ7
configs"). The `IEEETKDE` campaign this task found empty is job **2215162**, git
`3b7ee68`, 2026-09-05, whose `rq5.yaml` lists `fact_rank_roles` and no
`wstar_orbit`. **Candidate explanation 1 is the correct one for `IEEETKDE`, and
candidate 3 for T-KBf's numbers.**

**Check 3 — the quoted values against the rows.** Every RQ5 number in T-KBf
("RQ5 analysed — negative on every clause", lines 1128–1174) is reproduced
exactly by `IEEETKDE_isal/RQ5_patterns/analysis/stats.json` (written 2026-09-10
15:06): ν = 0.1015 with 1,553 negative eigenvalues; hubness skew 5.408; H5b
0.030 vs 0.089 / 0.040 (`wd50k100_balanced`), 0.042 vs 0.053 / 0.049
(`wd50k66_balanced`), `r_rb` −1.000 / −0.878 / −1.000 / −0.952; H5c 0.064
[0.061, 0.068] vs 0.030 [0.025, 0.036]. **But "ours" in that analysis is
`fact_rank`, not `wstar_orbit`**: `experiments/tkde/analyze_rq5.py` sets
`OURS = "fact_rank"` (at `afab7c5` and at HEAD), and its docstring states H5a–H5c
for `fact_rank`. Recomputed from the rows with the analyzer's aggregation (mean
over seeds of the PAM ARI), `fact_rank` is 0.0304 on `wd50k100_balanced` — the
quoted "ours" — while `wstar_orbit` is:

| experiment | `wstar_orbit` ARI / NMI | best other arm, ARI | `fact_rank` ARI |
|---|---|---|---|
| `wd50k100_balanced` (27 seeds, 140 members) | **0.1561** / 0.3435 | `degree_seq_l1` 0.0889 | 0.0304 |
| `wd50k66_balanced` (27 seeds, 280 members) | **0.1707** / 0.4460 | `netlsd` 0.0743 | 0.0418 |
| `wd50k66_full` (1 run, 3,487 of 3,492 members) | **0.0633** / 0.1776 | `hpd_jsd` 0.0167 | 0.0075 |

So T-KBf's sentence "RQ5 finds the degree-sequence floor leading over
`wstar_orbit` on knowledge bases" is **wrong as written**: the floor leads over
`fact_rank`; on the same rows `wstar_orbit` has the highest ARI and NMI of every
arm in every experiment. Separately, H5c's "best competitor 0.064 against ours
0.030" compares `hpd_jsd` on `wd50k66_balanced` with `fact_rank` on
`wd50k100_balanced` (`hpd_jsd` is not in the `wd50k100` design); the
same-experiment `fact_rank` value is 0.042.

**Verdict.** The derivation is locatable; the attribution is not. The T-KBf RQ5
numbers are `fact_rank`'s, from `IEEETKDE_isal/RQ5_patterns/analysis/stats.json`
(job 2265389, `afab7c5`). No fact base this agent read quotes a `wstar_orbit`
RQ5 number with a correct source.

## What remains (why this stays OPEN)

1. **Correct T-KBf's RQ5 paragraph** (its owner; not edited here — T-KBf is
   outside this agent's write set): relabel "ours" as `fact_rank` and drop the
   `wstar_orbit` sentence, or replace it with the rows above.
2. **Explain `wstar_orbit`'s RQ5 lead before quoting it.** `w*_c` and `w°` are
   both complete invariants on the same structures, yet on the same balanced
   design `wstar_orbit` reaches ARI 0.156 / 0.171 where `isal_ow_struct`
   (RQ5_ow, job 2308368) stays below 0.08. A two-fold gap between two complete
   canonical forms of the same objects needs a mechanism (what each arm encodes —
   e.g. vertex labels — and which members each matrix covers) before either
   number enters a table. Until then both "RQ5 is negative for the canonical
   string" and "`w*_c` leads RQ5" are unsupported.
3. **Check 4 — whether `wstar_orbit` belongs in `rq5.yaml` at all** under
   D-ART6 is the orchestrator's / PI's decision; `configs/` is read-only for this
   agent. Item 2 bears on it.
4. The H5c cross-experiment comparison in `analyze_rq5.py` is a separate
   analyzer issue; it should be logged with `task-handoff` by whoever owns RQ5.
