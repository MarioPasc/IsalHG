# Work log — harvest

## Identity

| Field | Value |
|---|---|
| Agent | `harvest` |
| Wave | `2026-10-04-harvest` |
| Model / effort | `claude-opus-5-5` / `xhigh` |
| Branch | `worktree-agent-a9c34e6bb3d1fadbf` |
| Worktree | `/home/mpascual/research/code/IsalHG/.claude/worktrees/agent-a9c34e6bb3d1fadbf` |
| Base commit | `3615c00` |
| Head commit | the commit that adds this file (`docs(notes): harvest work log`); content commits `213f93d`, `aec270a`, `996721f`, `9a6998a`, `1051b04` |
| Started / finished | `2026-10-04T09:45+0200` (approx.) / `2026-10-04T10:30+0200` |
| Status | partial — every work item done; RQ3 v2 coverage is incomplete by measurement, not by omission (§10) |

## 1. Prompt as received

```
# Task: close the owed harvest work of the headline campaign (agent `harvest`)

You are agent **`harvest`**, the only agent of wave `2026-10-04-harvest` in the IsalHG article campaign (IEEE TKDE, "knowledge bases as words"). The orchestrator is **`main`** (reach it with `SendMessage`). You cannot ask the user anything: record assumptions in your log, message `main` only for a decision that changes an outcome, and continue. **Harvest and analysis only: you submit NO new Picasso jobs and run no new campaign.**

First message to `main`: `git rev-parse --show-toplevel` (must be under `.claude/worktrees/`), `git rev-parse --short HEAD` (must be `3615c00`), and your model/effort.

## Mission

Jobs submitted on 2026-09-13/14 have finished. Harvest them, analyse them against the hypotheses that were pre-registered before they ran, write the fact bases, and fill the remaining `\todo` cells of the capability table. A separate session is writing the paper from these fact bases, so every number you write must carry its run root, job id and table path, and anything that cannot be closed must be stated as not closed.

Read first, in order: `docs/article/D_ART3/experiments/HEADLINE_DESIGN_2026-09-13.md` (the pre-registration; §3 RQ3 v2, §5 the w° swap, §6 the table, §8 the deviations log — binding), `docs/article/D_ART3/SESSION_LOG.md` §8–§10, `docs/article/D_ART3/experiments/RQ3V2_PILOT.md`, `docs/article/D_ART3/foundation/rq3v2_facts.md`, `rq2_ow_facts.md`, `rq5_ow_facts.md`, `rq8_facts.md` (for format), `docs/article/DEVELOPMENT/T-KB/IN-PROGRESS/T-KBz.md` and `T-KBab.md`, `docs/article/DEVELOPMENT/T-KB/OPEN/T-KBad.md`, `.claude/notes/2026-09-13-headline-w0/rq3v2.md` and `rq8.md` (the previous agents' logs: tags, analyzer flags, pitfalls), `experiments/tkde/analyze_rq3v2.py`, `experiments/tkde/analyze_rq2.py`, `slurm/tkde/README.md`, `scripts/tkde/harvest_from_picasso.sh`.

## State you start from (measured by `main` on 2026-10-04 via sacct)

| job | what | state |
|---|---|---|
| 2308421 | RQ3 v2 first pass, tag `ef0c58b4`, 60 s exact-HGED judge | 85 COMPLETED / 37 TIMEOUT; 358 units |
| 2311518 | RQ3 v2 light pass, 40 units, tag `ef0c58b4` | 40/40 COMPLETED |
| 2311519 | RQ3 v2 structurally empty ndc star cells, 79 units | COMPLETED |
| 2311520 | RQ3 v2 heavy pass, 189 units (7 cells × 27 seeds), tag `1efdcf54`, 8 s judge, 6 h wall | **11 COMPLETED / 178 TIMEOUT** |
| 2311593 + 2311604 | RQ2 on `w°` (third attempt, after the empty-output fix) | 13/13 + 9/9 COMPLETED |
| 2308368 | RQ5 on `w°` | harvested and analysed on 2026-09-14 (`rq5_ow_facts.md`) |

Picasso results root: `~/results/IEEETKDE_ow/` (`RQ3v2_golden_record/` 490 row files, `RQ2_wellposedness/` 85 row files). Drive mirror: `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE_ow/` (existing subdirs `RQ2_ow/ RQ3v2/ RQ5_ow/ RQ5_patterns/ RQ8/ RQ8_completion/` from earlier harvests — look before you copy; rsync additively, never delete on either side; the cluster is read-only for you). SSH alias `picasso` works non-interactively.

## Work items

1. **RQ3 v2.** Harvest. Build the coverage table per corpus × stratum × N × t × tag (units present of 27). Run `analyze_rq3v2` under the two-tag rules (`--supersede-tag ef0c58b4` drops the old tag only where the new one covers the cell; the analyzer refuses a cell split across judge budgets). **Test H3.1–H3.6 only on cells with complete coverage (27 seeds under one tag)**; for partially covered cells report n and the descriptive numbers, labelled censored, and do not pool them into any test. If the heavy pass left the seven heavy cells incomplete, say exactly which cells the paper can and cannot claim. Spend at most 30 minutes establishing from the 2311520 logs why the heavy units still exceeded 6 h at an 8 s judge budget (which component dominates) and write the cause in one paragraph; do not resubmit anything. Write `foundation/rq3v2_facts.md` in full: per-hypothesis verdict (supported / not supported / not testable), the exact numbers with BCa CIs, Holm p and rank-biserial, the per-cell judge fallback rates, the certified ratios (consensus vs `medoid[isal_ow_indel]`), pool sizes and wall-clock, every one with source path. State the scope conditions in words (non-star stratum, t, N, the r = 2 envelope).
2. **RQ2 on `w°`.** Harvest, verify unit counts against `configs/rq2_ow.yaml`, run the RQ2 analyzer, and fill `foundation/rq2_ow_facts.md` §4: false merges and the induced partition for `isal_ow_struct` on `ndc_classes`, `ndc_substances`, `wd50k66` (expected by Theorem C: 0 merges, partitions 530 / 1,086 / 3,677 — report what is measured), and every other arm's census from this run beside the campaign's (`foundation/rq2_wellposedness_facts.md`) as a cross-check.
3. **T-KBad.** Run the provenance check that task file specifies (where did the `wstar_orbit` RQ5 numbers quoted in T-KBf come from, given that arm is in 0 of 54 campaign RQ5 row files). Write the finding into the task file; `git mv` it to `CLOSED/` if resolved, otherwise leave it OPEN with what remains.
4. **The capability table** `docs/article/D_ART3/tables/tab_kb_representation_properties.tex`. Fill every remaining `\todo`: the `w°` consensus cell from item 1 (with a footnote in the style of the existing `\S` footnote: what is supported, where, with numbers and scope); the WL matrix time and the HyperCOT merges only if a measured number exists on disk (`foundation/rq7_envelope_facts.md`, `rq2_wellposedness_facts.md`, the RQ7/RQ2 result trees) — otherwise replace `\todo` by `n/m` with a footnote saying not measured. Keep the header comment's column-source list in sync. No number enters the table without a source path in the comment block.
5. Update `T-KBz.md` and `T-KBab.md` with closing evidence; move to `CLOSED/` only the ones whose acceptance is met.

## Ownership (exclusive write access)

`docs/article/D_ART3/foundation/{rq3v2_facts,rq2_ow_facts}.md`; `docs/article/D_ART3/experiments/RQ3V2_PILOT.md` (append only); `docs/article/D_ART3/tables/tab_kb_representation_properties.tex`; `docs/article/DEVELOPMENT/T-KB/**/T-KB{z,ab,ad}.md`; `.claude/notes/2026-10-04-harvest/harvest.md`; `experiments/tkde/analyze_rq3v2.py` and `tests/experiments_tkde/test_rq3v2*.py` **only if a defect blocks the analysis** (then: failing-first regression test, note it in the log, message `main`). Everything else is read-only, including `src/`, every other runner and analyzer, `DEVELOPMENT/README.md`, `SESSION_LOG.md`, `prose.md`, the design doc, and every results tree of an earlier campaign.

## Environment

No source edits are expected, so do not clone an env. Run from your worktree root with the shared interpreter: `~/.conda/envs/isalhg/bin/python -m experiments.tkde.<module> …`. Before any analysis, assert that `experiments.tkde.analyze_rq3v2.__file__` resolves inside your worktree (the env's `isalhg` package resolves to the main checkout, which is identical to yours for `src/`). Never `pip install` into that env. Verification if you touch code: `~/.conda/envs/isalhg/bin/python -m pytest tests/experiments_tkde/ -q -k "rq3v2 or rq8"` (192 passed at base), ruff baseline 38, mypy baseline 20.

## Rules that matter here

A partial table must not be read as a result. Nothing is dropped for winning or losing (lesson L12). A hypothesis that cannot be tested is reported as not testable, with the reason. Do not tune, re-run with different settings, or submit jobs. Commit everything on your branch (conventional commits; end each message with `Claude-Session: https://claude.ai/code/session_016rWF7Me4RKWxHHQ1Msi8nF`); no push, merge or rebase.

## Work log and final message

Write `.claude/notes/2026-10-04-harvest/harvest.md` from `/home/mpascual/.claude/skills/parallel-agents/assets/note-template.md` (§1 = this prompt verbatim); commit it last. Final message: first line `STATUS: complete | partial | blocked`; branch, worktree, head SHA; then (a) the RQ3 v2 coverage table and the H3.1–H3.6 verdict table with numbers, (b) the RQ2_ow census table, (c) the T-KBad finding in two sentences, (d) the table cells you filled and with what, (e) what could not be closed and why.
```

(The message was followed by a tool-usage block, `<context_window_protection>`,
instructing the use of the context-mode MCP tools for large outputs, the native
Write/Edit tools for files, and a final response under 500 words. It is
harness guidance, not task scope, and is not repeated here.)

## 2. Understanding and plan

**Restatement.** Bring the 2026-09-13/14 campaigns onto the drive, analyse RQ3 v2
and RQ2_ow strictly against what was registered before they ran, testing only on
fully covered cells, and write fact bases a paper-writing session can cite
number by number. Resolve the T-KBad provenance question, fill the capability
table, and close only the tasks whose acceptance is met.

**Approach chosen.** Harvest by `rsync -a` (additive) into the drive mirror under
the remote's own directory names (the precedent the 2026-09-14 harvest set with
`RQ8_completion/` and `RQ5_patterns/`), build the coverage table from file names
and rows, run the analyzer with `--supersede-tag ef0c58b4`, write analysis
outputs to a sibling directory so the mirrored Picasso `summary.json` is not
overwritten, then read every number from the analyzer's own outputs.

**Alternatives considered and rejected.**
- Filtering complete cells in a scratch script instead of in the analyzer —
  rejected: the paper session must be able to reproduce every number from the
  repo, and the analyzer crashed on the real tree anyway, so it had to change.
- Pooling the two tags' seeds for exact recovery in `ndc` N9 t2 (recovery is
  judge-independent, verified on 1,897 overlapping rows) — rejected: the union is
  still 16/27, and the ruling forbids mixing budgets inside a cell.

**Plan as executed.**
1. Start message to `main`; read the binding documents.
2. Harvest RQ3 v2 (493 files) and RQ2 (257 files) to the drive.
3. Coverage table from 490 row files; tag/row consistency check.
4. Run the analyzer → crash → failing-first tests → fixes → rerun.
5. 2311520 log analysis (≈15 min): per-collection walls joined to rows.
6. RQ3 v2 fact base; append to `RQ3V2_PILOT.md`.
7. RQ2_ow analysis, cross-check against the campaign, fact base §4.
8. T-KBad provenance search across every `IEEETKDE*` root, drive and Picasso.
9. Capability table; T-KBz / T-KBab; commits; this log.

**Deviations from the plan.** The analyzer edit (step 4) was not expected by the
prompt; it was forced by a crash and by the missing coverage gate (§7). The
coordinator's mid-task request (§8) added two RQ2 verifications.

## 3. Changes made

**Created**
| Path | Purpose |
|---|---|
| `.claude/notes/2026-10-04-harvest/harvest.md` | this log |

**Modified**
| Path | Change | Reason |
|---|---|---|
| `experiments/tkde/analyze_rq3v2.py` | `coverage_by_cell`, `complete_cells`, `design_cells`, `certified_ratio_table`, `_by_n`; budget-set fix in `check_one_tag_per_cell`; H3.1 `not_testable`/`verdict`; H3.2 family = every medoid with rows; H3.3–H3.5 `paired`; H3.6 `by_series`; per-cell `cost_table`; `--expected-seeds`, `--config` | defects that blocked the analysis (§7) |
| `tests/experiments_tkde/test_rq3v2_analysis.py` | 10 tests in 5 classes | failing-first regressions for each defect |
| `docs/article/D_ART3/foundation/rq3v2_facts.md` | provenance; new §6–§12 (coverage, verdicts, per-cell tables, certificate, judge footnote, cost, capability, heavy-pass cause) | work item 1 |
| `docs/article/D_ART3/experiments/RQ3V2_PILOT.md` | appended § "The harvest" | work item 1 (append only) |
| `docs/article/D_ART3/foundation/rq2_ow_facts.md` | §1 status, §2 provenance, §3 attempt 3, §4 measured table | work item 2 + coordinator request |
| `docs/article/DEVELOPMENT/T-KB/OPEN/T-KBad.md` | status update, Finding, What remains | work item 3 |
| `docs/article/D_ART3/tables/tab_kb_representation_properties.tex` | three `\todo` filled; bipartite-path merges cell 17 → 157; dagger footnote; two new footnotes; header comment | work item 4 + coordinator request |
| `docs/article/DEVELOPMENT/T-KB/IN-PROGRESS/T-KBz.md` | acceptance boxes; closing evidence | work item 5 |
| `docs/article/DEVELOPMENT/T-KB/CLOSED/T-KBab.md` (moved from `IN-PROGRESS/`) | status DONE; RQ2_ow closing evidence | work item 5 |

**Removed** — none.

**Commits**
| SHA | Message |
|---|---|
| `213f93d` | `fix(rq3v2): analyzer coverage gate, pandas-3 crash, every medoid in H3.2` (also carries the staged `git mv` of T-KBab, 0 content lines — staged before this commit by mistake; not rewritten) |
| `aec270a` | `docs(rq3v2): harvest fact base -- 11 complete cells, H3.1-H3.6 verdicts` |
| `996721f` | `docs(rq2_ow): w° census -- 0 merges, exact partition, 0 censored; close T-KBab` |
| `9a6998a` | `docs(t-kbad): T-KBf's "wstar_orbit" RQ5 numbers are fact_rank's` |
| `1051b04` | `docs(table): fill the capability table's last todo cells` |
| (last) | `docs(notes): harvest work log` |

**Outside the repo (results drive, additive only).** `IEEETKDE_ow/RQ3v2_golden_record/`
(493 files, mirror) plus `…/anonymous_consensus/_analysis_ef0c58b4+1efdcf54/`
(analysis outputs); `IEEETKDE_ow/RQ2_wellposedness/` (257 files, mirror) plus
`summary.json`, `stats.json`, `tables.md` written beside the rows by
`analyze_rq2` (absent on Picasso, so nothing mirrored was overwritten). Nothing
was deleted anywhere; nothing was written on Picasso.

## 4. Tests

**Tests created**
| Test | File | What it verifies | Why it matters |
|---|---|---|---|
| `TestMissingBudget::test_a_row_without_a_budget_does_not_break_the_report` | `test_rq3v2_analysis.py` | a cell mixing `60.0` and NaN budgets reports `["60.0"]` | the crash on the real tree |
| `TestCoverageGate::test_each_cell_is_complete_partial_or_empty` | same | status per cell | the gate's classification |
| `TestCoverageGate::test_only_complete_cells_survive_the_gate` | same | partial and empty cells dropped | no test on a partial cell |
| `TestCoverageGate::test_a_partial_cell_is_reported_not_testable_and_never_tested` | same | H3.1 keys exclude N15, `not_testable` names it, verdict says so | "every N" not silently narrowed |
| `TestCoverageGate::test_a_design_cell_with_no_row_is_absent_and_not_testable` | same | design cells with no rows appear as `absent` | three heavy cells wrote nothing |
| `TestCoverageGate::test_the_two_tags_are_not_pooled_into_one_count` | same | after supersession a cell's seeds count within its tag | union of budgets ≠ coverage |
| `TestH36Series::test_a_rise_within_the_series_holds_although_the_pooled_mean_falls` | same | verdict reads series, not pooled | composition confound |
| `TestH36Series::test_a_fall_within_the_series_fails` | same | a fall within a series fails | the verdict can fail |
| `TestCertifiedRatio::test_consensus_is_read_against_the_indel_medoid` | same | pairing, means, fraction below | the certificate table |
| `TestEveryMedoidInH32::test_the_indel_medoid_is_in_the_h32_family` | same | `medoid:isal_ow_indel` in H3.2 | "every medoid" |

**Not tested.** `analyze()` end-to-end on a synthetic tree (exercised instead on
the real 490-file tree); the H3.3–H3.5 `paired` fields (exercised on real data).

## 5. Test results

**Before the fix** (`pytest tests/experiments_tkde/test_rq3v2_analysis.py -q`):
`8 failed, 7 passed` — TypeError (budget sort), 4× AttributeError
(`coverage_by_cell`/`complete_cells`), KeyError `by_series`, AttributeError
(`certified_ratio_table`), AssertionError (indel medoid missing). The absent-cell
test was added after the first fix round and failed on the missing
`design_cells` argument before its implementation.

**After** — command `~/.conda/envs/isalhg/bin/python -m pytest tests/experiments_tkde/ -q -k "rq3v2 or rq8"`:

```
===================== 202 passed, 490 deselected in 28.46s =====================
```

**Result:** 202 passed (192 at base + 10 new), 0 failed. `ruff check src/ tests/ experiments/`:
`Found 38 errors` (baseline 38; both touched files clean). `mypy src/isalhg/`:
`Found 20 errors in 6 files` (baseline 20). `mypy experiments/tkde/analyze_rq3v2.py`:
the same two errors as the base file (pandas stubs; the pre-existing
`list[dict]` on `_paired`), checked by type-checking `git show HEAD:` of the base
file.

## 6. Verification beyond unit tests

| Circumstance | What was run | Evidence | Outcome |
|---|---|---|---|
| Real data, RQ3 v2 | `analyze_rq3v2 --root <drive>/IEEETKDE_ow --out …/_analysis_ef0c58b4+1efdcf54 --supersede-tag ef0c58b4 --expected-seeds 27` | 328,162 rows loaded, 12,000 superseded, 316,162 analysed; 11 complete / 4 partial / 3 absent / 6 empty | pass |
| Tag integrity | file-name tag vs row tag, 490 files | 490/490 equal | pass |
| Judge independence of the primary metric | the two seeds both tags measured (ndc ns N9 t2: 320013, 320025) | exact recovery identical on 1,897/1,897 rows; fact_dist differs on 2 | pass |
| Certificate construction | consensus ratio ≤ same-metric medoid ratio | fraction 1.000 in all 15 measured cells, both metrics | pass |
| Real data, RQ2_ow | `analyze_rq2 --root <drive>/IEEETKDE_ow`; census rows vs campaign | 30/30 shared rows identical to tag `a5ff6092` | pass |
| Heavy-pass cause | 189 `.err` logs (6,252 collections) joined to the 13 written units (650 collections) | ball 99.1–99.7 % of unit wall; residual 2–7 s/unit; 145 judge timeouts total | finding (`rq3v2_facts.md` §11) |
| Table compiles | `pdflatex` of the table in an IEEEtran stub | no error, no overfull box reported | pass |
| Environment | `analyze_rq3v2.__file__` and `analyze_rq2.__file__` in the worktree; `src/` identical to the main checkout (`diff -rq`, no output) | Python 3.11, pandas 3.0.3 | pass |

## 7. Decisions, assumptions, open questions

**Decisions with a real trade-off.**
- *Analyzer edits.* Four defects blocked a valid analysis: (1) the pandas-3 crash;
  (2) no coverage gate; (3) H3.2's family missing the indel medoid; (4) H3.6's
  pooled-by-N verdict is composition-confounded once only complete cells are
  read. The H3.6 rule (within corpus × stratum × t series, non-decreasing in every
  series with ≥ 2 complete N) was fixed **before** any per-`N` consensus number
  was read; I had seen only the campaign-wide pooled means per method
  (`consensus_ow` 0.41, `consensus_fact` 0.98, oracle 0.94) from a first
  exploration of the rows. Additions beyond defect fixes, made because the fact
  base the prompt specifies needs them reproducibly: `certified_ratio_table`, the
  per-cell `cost_table`, the seed-paired interval/p/`r_rb` printed beside the
  H3.3–H3.5 margin verdicts (verdict rules unchanged). Messaged to `main`.
- *H3.6's verdict of record.* The analyzer's `held` reads only the monotonicity
  clause; the sub-record clause has no registered threshold. The fact base
  reports H3.6 "not supported as stated" because the measured sub-record shares
  are below one half in every series. A reader who takes the clause as
  descriptive only would call it "monotonicity supported"; both readings are
  written down.
- *Analysis output location.* RQ3 v2 outputs go to a sibling `_analysis_…`
  directory so the mirrored Picasso `summary.json` is not overwritten (the RQ8
  `_tag_*` precedent). RQ2 outputs were written in place, as the campaign's were,
  because Picasso holds none of those files.
- *The bipartite-path merges cell.* Changed "splits 17" to "splits 157": the
  column is defined on `wd50k66`, and 17 was the `ndc_classes` split. This goes a
  step beyond the coordinator's footnote request; flagged in the report.

**Assumptions.** The drive mirror is the citable copy and remote names are kept
(`RQ3v2_golden_record/`, `RQ2_wellposedness/`) per the 2026-09-14 harvest
precedent, although the design names the sub-root `RQ3v2/`. The `38b1b14` stamp
on recovery-pass rows denotes the tree that became `033b9fd` (§Provenance of the
fact base); the remote deploy tree `~/repos/IsalHG-rq3v2` no longer exists, so
byte identity could not be checked there.

**Open questions for the orchestrator.**
1. The seven heavy cells: resubmit (≈1.1–2.9× the 6 h wall per unit at the
   registered ball) or state the claim at its measured scope?
2. `pattern_vote` recovers 0.02–0.05 of star sources against the design's
   premise of exact recovery; audit before H3.4 is quoted.
3. H3.5: a representation-free fact-space consensus (0.984, and cheaper) beats
   the word-space one (0.433). The declared fallback reduces RQ3's language claim
   to the decoded output and the certificate; the H2 headline status needs a
   ruling.
4. `consensus_ow_coverage` beats the registered indel median on 6 of 11 complete
   cells (all `t = 2`); reported, not acted on.
5. T-KBad item 2: `wstar_orbit` leads RQ5 (ARI 0.156–0.171) where `w°` stays
   below 0.08 — a mechanism is needed before either is quoted.
6. `HEADLINE_DESIGN` §8 ends at item 8, while `SESSION_LOG.md` §10 cites the
   recovery ruling as "§8 item 9"; the ruling is recorded in `RQ3V2_PILOT.md`
   and T-KBz D-KBz8 but not in the design doc (read-only for me).

## 8. Coordination

**Messages sent.** (1) Start: worktree, `3615c00`, model/effort. (2) The
analyzer defects and the heavy-pass cause, with the coverage table. (3) The
outcome-changing findings: H3.5, H3.4 caveat, coverage-objective reading, the
RQ2 split's collection and member set, the 157 cell change, HyperCOT never ran,
T-KBad's misattribution.

**Messages received.** The coordinator asked, mid-task, (1) to establish the
collection and member subset of the "574 where 557" split, write it in
`rq2_ow_facts.md` §4 and correct the dagger footnote; (2) to report
`isal_ow_struct`'s class count with its member count beside `wstar_orbit`'s
1,661-member figure. Both done: `rq2_ow_facts.md` §4.1–§4.2, the table's dagger
footnote.

**Contracts confirmed unchanged.** `src/` (identical to the main checkout);
`rq3v2.py`, `rq2.py`, `analyze_rq2.py`, all configs untouched.

## 9. Deliberately not done

- No Picasso submission, no rerun of anything, no tuning.
- `rq2_wellposedness_facts.md` (campaign) not edited — not mine; its pooled-tag
  table and the HyperCOT timing row are flagged in `rq2_ow_facts.md` §4.2–§4.3.
- T-KBf not edited (its RQ5 paragraph needs correcting; T-KBad says how).
- `configs/rq5.yaml` not edited (T-KBad check 4 is a decision).
- The `pattern_vote` construction was not audited, only flagged.
- 2308421's judge share was not re-derived from its own logs (not asked; the
  30-minute box was for 2311520).

## 10. Risks and follow-ups

| Item | Severity | Detail | Suggested owner |
|---|---|---|---|
| Seven RQ3 v2 cells incomplete | high | H3.1's "every N" undecided; nothing at relational N = 15 | orchestrator |
| H3.5 failure | high | the word-space consensus is beaten by a representation-free one on accuracy and cost | orchestrator / PI |
| `pattern_vote` on stars | medium | 0.02–0.05 recovery contradicts the design's premise; H3.4 unquotable until audited | next RQ3 owner |
| T-KBf misattribution; unexplained `wstar_orbit` RQ5 lead | medium | see T-KBad | T-KBf owner / orchestrator |
| HyperCOT never ran on Picasso | medium | every RQ2 and RQ3 v2 HyperCOT row is an environment error; "gated" timing rows are time-to-failure | orchestrator |
| Table: size baseline matrix "12.6" | low | `rq7_envelope_facts.md` §8 gives `size_l1` 2.81 s (`degree_seq_l1` 12.62 s); the rows of tag `4c8b759f` give a `degree_seq_l1` median of 16.0 s. Not my cells; not changed | table owner |
| Table header "38 % asym., 1.4 % triangle" for bipartite path | low | RQ2 measures 44–58 % asymmetry and 0.14–0.52 % triangle violations; the header cites Prop 8, a different source | table owner |
| Lost unit | low | `ndc` ns N9 t2 s320008 finished after the cancel and was not copied back; a worker should finish or abandon before the wall minus copy-back time | `slurm/tkde` owner |

## 11. Self-assessment against the definition of done

| # | Criterion | Met | Evidence |
|---|---|---|---|
| 1 | RQ3 v2 harvested, coverage table, analyzer under two-tag rules, tests on complete cells only | yes | `rq3v2_facts.md` §6–§7; analysis dir |
| 2 | Partial cells descriptive, censored, unpooled; which cells can/cannot be claimed | yes | §6, §8 |
| 3 | Heavy-pass cause in one paragraph within 30 min | yes (≈15 min) | `rq3v2_facts.md` §11 |
| 4 | Fact base in full (verdicts, BCa, Holm, r_rb, judge fallback, certified ratios, pools, wall-clock, sources, scope) | yes | §7–§11 |
| 5 | RQ2_ow harvested, unit counts verified, analyzer run, §4 filled with cross-check | yes | `rq2_ow_facts.md` §4 |
| 6 | T-KBad provenance check, finding written, OPEN/CLOSED decided | yes (left OPEN, reasons stated) | `T-KBad.md` |
| 7 | Every `\todo` filled with sources | yes | table + header comment; no `\todo` remains |
| 8 | T-KBz / T-KBab updated; CLOSED only where acceptance is met | yes (T-KBab closed; T-KBz stays IN-PROGRESS) | the two files |
| 9 | Commits on branch, no push/merge/rebase | yes | §3 |

**Overall.** The harvest and analysis are complete and reproducible from the
repo and the drive; every number in the fact bases is read from the analyzers'
own outputs or a named row file. What is not complete is the experiment: seven
RQ3 v2 cells never filled, so the headline's "every N" is undecided. The
orchestrator should scrutinise first the four analyzer changes (they decide what
was tested) and the H3.6 verdict wording, then the three outcome-level findings
(H3.5, `pattern_vote`, T-KBad's `wstar_orbit` lead).
