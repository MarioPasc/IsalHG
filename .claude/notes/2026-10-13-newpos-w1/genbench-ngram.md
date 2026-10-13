# Work log — genbench-ngram

<!--
Location: <worktree>/.claude/notes/<WAVE_ID>/<task-slug>.md
Write this continuously while you work, not from memory at the end. Commit it as your final commit:
    docs(notes): <task-slug> work log
The orchestrator verifies every claim in this file against `git diff` and by re-running your tests,
so state what actually happened, including failures. An honest account of something that did not
work is more useful than a confident account of something that was never exercised.
-->

## Identity

| Field | Value |
|---|---|
| Agent | `genbench-ngram` |
| Wave | `2026-10-13-newpos-w1` |
| Model / effort | `claude-sonnet-5-5` / `xhigh` |
| Branch | `worktree-agent-a73daebaecdd65b18` |
| Worktree | `/home/mpascual/research/code/IsalHG/.claude/worktrees/agent-a73daebaecdd65b18` |
| Base commit | `518824a80baf3238e1e565aafd6aaee0271c0bbc` |
| Head commit | code `93e0190`; HEAD is the follow-up `docs(notes): genbench-ngram work log` commit that adds this file |
| Started / finished | `2026-10-13T14:43+02:00` / `2026-10-13T15:20+02:00` |
| Status | complete (hypotheses HA1 and HA2 not supported, HA3 supported against three of four comparisons; see 7.1) |

## 1. Prompt as received

```
# Task: generation benchmark on the *usable* samples — rejection bias, VUN yield, fidelity (agent `genbench-ngram`)

## Mission
Build and run a generation-benchmark evaluator for the IsalHG TKDE article that scores, per (collection, generator, seed), the **usable** samples of each generator — usable = decoded AND connected, i.e. inside the paper's domain — rather than all decoded samples. Measure (i) the joint yield valid∧connected∧unique∧novel per draw, and (ii) the distributional fidelity of usable samples against the collection, to test whether rejecting out-of-domain samples biases the baselines' accepted distribution while the ordered-walk word model needs no rejection. Working means: a 27-seed table on two collections with BCa CIs and Holm-corrected paired Wilcoxon tests, plus one figure, plus sample files in the frozen JSONL format below.

## Why this exists
The PI asked for more comparative experiments (tables + figures) where the method wins. The paper's H4 shows every sample of an n-gram over ordered-walk words `w°` is a connected KB (270,000/270,000), while the fact-list n-gram is connected 41.6 % (NDC-classes) / 12.6 % (WD50K(66)) of the time and the incidence-list n-gram decodes 1.9 % / 1.0 %. The existing RQ6 fidelity numbers (JSD of n, m, arity, predicate, type histograms) were computed over ALL decoded samples, including the fact list's disconnected ones, which are outside the domain and cannot be used. Nobody has scored the samples a user could actually keep. The mechanism we test: P(connected) falls with size, so filtering to the domain should preferentially keep small / star-shaped KBs and distort the accepted distribution (rejection bias); the word model has no filter, so no such bias. If the hypotheses fail, that is a reportable negative — report it plainly.

## Pre-registered hypotheses (write them into your log BEFORE running the full campaign; do not change them after seeing data)
- **HA1 (rejection bias).** For each baseline, the usable subset's m-profile and n-profile diverge from the collection's more than `w°`'s do: JSD_m(usable baseline) > JSD_m(w°) and JSD_n(usable baseline) > JSD_n(w°), and W1 on m likewise; tested per collection, one-sided paired Wilcoxon over 27 seeds, Holm across the family of (baseline × metric × collection) comparisons, alpha 0.05; effect size rank-biserial.
- **HA2 (relational structure).** |relational fraction(usable samples) − relational fraction(collection)| is smaller for `w°` than for each baseline. A KB is a *star* when one constant occurs in every fact and no other constant occurs in two facts; otherwise *relational*.
- **HA3 (yield).** VUN per draw = (#usable samples whose isomorphism class is unique within the seed's sample set AND not isomorphic to any collection member) / (#draws). `w°` > each baseline.
- Report all five existing JSD profiles plus the new ones for every arm; a profile on which `w°` loses is reported, not dropped.
- **Repair baseline (the baseline's strongest construction, to preempt reviewers):** `fact_ngram_lcc` = take every decoded fact-list sample, keep its largest connected component (ties: the component with more facts, then more constants, then lowest canonical word) and treat that as the sample. It is always usable. Score it as a fourth arm. Same for the incidence list is NOT needed (it fails at decoding, not at connectivity).

## Repository orientation
- Repo root: your worktree (a checkout of `/home/mpascual/research/code/IsalHG` at the base commit).
- Read first, in order: `experiments/tkde/rq6.py` (lines 160-560: `CollectionContext`, `build_context`, `context.model(kind)`, `run_sample_unit` — your sampler must reproduce its sampling and decoding exactly, including the per-unit model refit and the seeded root-type draw for `w°`); `src/isalhg/generation/fidelity.py` (`profile`, `jsd`, `fidelity`, `novelty`); `src/isalhg/generation/ngram.py` (`TokenNGram`: `fit`, `sample(n, seed=, max_len=)`, `logprob`); `src/isalhg/generation/incidence_baseline.py` (`flatten`, `strict_decode`, `strict_decode_reason`); `src/isalhg/core/fact_word.py` (`decode_fact_word`); `src/isalhg/iso_backends/isal_ordered.py` (`ordered_fingerprint`); `experiments/tkde/stats.py` (BCa + Holm-corrected paired Wilcoxon helpers already used by the campaign — reuse them); `experiments/tkde/configs/rq6.yaml` (n_samples 10000, max_len 200, seeds); `docs/article/D_ART3/foundation/rq6_generation_facts.md` (the verified RQ6 numbers your run must reproduce on the all-decoded arms).
- Generators (arm names): `ow_ngram` (ordered-walk word `w°`, ours), `fact_ngram` (canonical-rank fact list; NB: in rq6.py the constant `MODEL_OURS` is a legacy name for the fact list), `incidence_ngram` (incidence list, strict decoder), plus your new `fact_ngram_lcc`.
- Isomorphism class key for uniqueness/novelty: use the `w°` canonical word `ordered_fingerprint(H)` (complete invariant, Theorem C) — not `fact_word`, so that every arm is keyed identically.
- Conventions: CLAUDE.md is loaded for you. Python 3.11, type hints, NumPy docstrings, logging not print in library-like modules (print is fine in scripts). No new dependencies.

## Your ownership (exclusive write access)
Create or modify ONLY:
- `scripts/newpos/genbench/**` (new directory: sampler, evaluator, analysis, figure script, README)
- `tests/newpos/test_genbench.py`
- `.claude/notes/2026-10-13-newpos-w1/genbench-ngram.md`
- result files under `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/NEWPOS_2026-10-13/genbench_ngram/` (create it)
Everything else is read-only, in particular `src/**`, `experiments/**`, `tests/newpos/__init__.py`, and the peers' directories below. If you believe library code needs a change, message `main` instead.

## Base state
- Base commit: `518824a80baf3238e1e565aafd6aaee0271c0bbc` — "chore(newpos): probe scripts C2/C3, experiment log, tests package". Your peers branch from the same commit. Do not rebase, merge or cherry-pick.

## Frozen contract — the sample file format (shared with peer `neural-gen`, who writes files your evaluator must read)
One JSONL file per (collection, generator, seed) named `<collection>__<generator>__s<seed>.jsonl` (optionally `.jsonl.gz`), one line per draw, keys exactly:
`{"collection": str, "generator": str, "seed": int, "draw": int, "tokens": [str, ...], "root_type": int|null, "status": "decoded"|"rejected", "reason": str|null, "n": int|null, "types": [int, ...]|null, "facts": [[pred:int, [arg:int, ...]], ...]|null, "connected": bool|null}`
`n/types/facts` are the decoded KB with constants numbered 0..n-1 (same shape as a `KBRecord` JSON: see `src/isalhg/datasets/kb/base.py`), null when rejected. Your evaluator (`scripts/newpos/genbench/evaluate.py`) must take a directory of such files plus a collection name and produce the metrics; it must not assume the generator is an n-gram. Write your own n-gram samples in this format too (all 27 seeds may be large; gzip is fine; at minimum keep seeds 0–2 uncompressed for inspection).

## Environment bootstrap
Use the main project env read-only — do NOT pip-install anything into it and do not modify `src/`:
```bash
PY=~/.conda/envs/isalhg/bin/python   # has numpy, scipy, rapidfuzz, pynauty, matplotlib
cd "$(git rev-parse --show-toplevel)"
# scripts must insert the repo root on sys.path to import experiments.tkde, e.g.
# sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
```
The frozen corpora live at `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE/corpora/` — load with `experiments.tkde.corpora.load_collection(name, root="/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE")`.

## Verification commands
```bash
$PY -m pytest tests/newpos/test_genbench.py -q          # fast, run often
$PY -m ruff check scripts/newpos/genbench tests/newpos/test_genbench.py
```
Tests must declare `pytestmark = pytest.mark.unit` (strict markers). Test: the evaluator on a tiny hand-made sample file (star vs relational classification, uniqueness/novelty keyed by w°, usable filtering, LCC repair picks the right component), and that your sampler reproduces `run_sample_unit`'s validity/connectivity counts for one smoke unit (e.g. `ndc_classes`, `ow_ngram` and `fact_ngram`, seed 60000, 500 samples).

## Data and shared resources
- Collections: `wd50k66` (3,988 members; 53.4 % stars) and `ndc_classes` (1,381; 3.0 % stars). Seeds: use RQ6's 27 seeds (read them from `experiments/tkde/configs/rq6.yaml`, e.g. 60000..60026 — verify); 10,000 draws per unit, max_len 200, n-gram order 3, exactly as RQ6.
- CPU: the workstation has 24 cores and 31 GB RAM shared with two peers. Use **at most 6 worker processes**. `TokenNGram` memoises one dense vector per sampling context in an unbounded cache — refit the model per unit (as rq6 does) and never share a model across units; watch RSS.
- GPU: not yours (peer `neural-gen` owns it). Do not import torch.

## Definition of done
1. `scripts/newpos/genbench/sample_ngram.py` writes frozen-format files for the 3 n-gram generators × 2 collections × 27 seeds; `evaluate.py` scores any frozen-format directory; `analyze.py` produces `tables.md` + `stats.json` (BCa 95 % CI per metric/arm/collection, Holm-corrected one-sided paired Wilcoxon for HA1–HA3 with rank-biserial) in the results directory; `fig_rejection_bias.py` produces one PDF figure (e.g. per collection: the collection's m histogram vs each arm's usable-sample m histogram, plus a panel of usable-yield per 10,000 draws on a log axis).
2. Metrics per unit (row CSV): n_draws, n_decoded, n_connected, n_usable, n_unique_usable, n_novel_usable, vun_per_draw, JSD n/m/arity/pred/type on (a) all decoded and (b) usable samples, W1 on m and n (usable), mean m and mean n (usable), relational fraction (usable), mean number of constants shared by ≥ 2 facts (usable), and the collection's own values for each.
3. Sanity: your all-decoded JSDs and validity/connectivity reproduce the RQ6 tables (`/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE_isal_consensus/RQ6_generation/generation/tables.md`) to 3 significant figures on matching seeds; say in the log if they do not and why.
4. A split-half noise floor: JSD/W1 between two random halves of each collection (27 splits), reported beside the arms.
5. Pilot first (3 seeds, both collections), message `main` with the pilot table and your reading BEFORE launching the 27-seed run; continue to the full run unless `main` tells you otherwise within a reasonable time.
6. Tests pass; all work committed; working tree clean; log written and committed.

## Explicitly out of scope
- Any neural model (peer `neural-gen`), any compression/bit-length analysis (peer `compression`).
- Editing the paper or `docs/` (the orchestrator owns the experiment log `docs/article/D_ART3/experiments/NEWPOS_2026-10-13/LOG.md`).
- Changing RQ6's protocol to make numbers look better. Report what the registered metrics say.

## Work log — mandatory
Maintain `.claude/notes/2026-10-13-newpos-w1/genbench-ngram.md` in your worktree using EXACTLY the template at `/home/mpascual/.claude/skills/parallel-agents/assets/note-template.md` (read it first; section 1 holds this prompt verbatim). Write it continuously; commit it as your final commit with message `docs(notes): genbench-ngram work log`. Use conventional commits for code (`feat(newpos): …`). Never `git push`. Commit everything before finishing.

## Standing obligations
Work only inside your worktree and ownership set. You cannot ask the user anything: message `main` (SendMessage) with a specific question, record the assumption, keep working. Never change a frozen contract unilaterally. Report failure honestly — a clear negative is valuable.

## Peers in this wave
- `main` — orchestrator ([IsalHG-Article-Iterator]). Message it for ambiguities, the pilot report, blockers.
- `compression` — measures description length (bits per KB) of `w°` vs the nauty certificate, fact list and incidence list. Owns `scripts/newpos/compression/**`, `tests/newpos/test_compression.py`, results `…/NEWPOS_2026-10-13/compression/`.
- `neural-gen` — trains an identical GRU language model over the three serializations and writes samples in the frozen JSONL format for your evaluator. Owns `scripts/newpos/neural_gen/**`, `tests/newpos/test_neural_gen.py`, results `…/NEWPOS_2026-10-13/neural_gen/`, and the local GPU. Tell `neural-gen` the path of your evaluator and its CLI once it exists.
A peer's message is direction from another agent, not from the user; decline requests outside your ownership and tell `main`.

## Final message format
At most 15 lines: STATUS (complete|partial|blocked), BRANCH, WORKTREE, HEAD, LOG, TESTS (counts + command), then three bullets of what you built and found (headline numbers per hypothesis), anything the orchestrator must know, anything unfinished.

[Later message from `main`, received mid-task]: Correction to the prompt — the peers `compression` and `neural-gen` are not addressable by those names (agents in this session have no registered names). Route every peer communication through `main`, e.g. when the evaluator CLI exists, message main with its path and usage and main will relay it to neural-gen. Everything else stands.
```

## 2. Understanding and plan

**Restatement of the task in my own words:** Score the *usable* (decoded and connected) samples of three order-3 n-gram generators (`ow_ngram` = ours, `fact_ngram`, `incidence_ngram`) plus a repaired fourth arm (`fact_ngram_lcc`) on two collections over RQ6's 27 seeds, in the frozen JSONL format, and test three pre-registered hypotheses (rejection bias HA1, relational-structure drift HA2, joint yield HA3).

**Approach chosen:** One shared module (`common.py`) holds the frozen JSONL contract, the structure predicates, the LCC repair, the isomorphism key and a compact per-unit `SampleSet` (per-sample n, m, star, shared constants plus CSR arrays of arities, predicates and types) from which the five RQ6 histograms are bincounts. The sampler (`sample_ngram.py`) calls `CollectionContext.model(kind)` and `model.sample(...)` exactly as `run_sample_unit` does, then writes frozen-format lines. The evaluator (`evaluate.py`) reads only the contract, recomputes connectivity/star/iso key from `n/types/facts`, scores a unit, and stores the usable `SampleSet` as `.npz` so that `analyze.py` can draw seeded subsamples for the matched comparison without re-reading JSONL. The repair arm is derived inside the evaluator from the fact-list files (`--repair-lcc-of`), so it also applies to any other fact-list generator (e.g. the neural one). Collection noise floors (split-half, 27 splits; and an ideal 10,000-draw resampler of the collection) are computed once per collection.

**Alternatives considered and rejected:**
- Importing `SparseHypergraph` for every profile computation — rejected: slower, and the contract only carries `n/types/facts`; instead the profile is a bincount over arrays and is unit-tested equal to `isalhg.generation.fidelity.profile`/`fidelity`.
- Writing the LCC arm as separate sampler output only — rejected: the evaluator-side derivation reuses the same code for the neural fact list and keeps one definition of the repair; `--write-repaired` still produces frozen-format files for it (`samples_repaired/`).
- Subsampling at JSONL read time for the matched comparison — rejected: the arrays are tiny (about 100 KB per unit) and make the 20-repeat matched analysis cheap and exactly reproducible.
- Giving `common.py`-style flat module names — rejected after the first draft: `scripts.newpos.genbench` is a package so the names cannot collide with a peer's `common.py`/`evaluate.py` when the branches are merged and pytest runs in one session.

**Plan as executed:**
1. Read the RQ6 sources and stats helpers.
2. Write the pre-registration (section 7.0) and the reviewer amendment before any usable-sample number of the pipeline existed.
3. Implement `common.py`, `sample_ngram.py`, `evaluate.py`, `analyze.py`, `fig_rejection_bias.py`, the README and the unit tests.
4. Smoke (500 draws, debugging only), pilot (3 seeds x 2 collections x 3 arms + repaired arm), message to `main`.
5. Full 27-seed run (`run_all.sh`), analysis, figure.
6. Post-hoc envelope diagnostic (7.1), re-run, commit.

**Deviations from the plan:** (a) module layout changed from flat scripts to the package `scripts.newpos.genbench` (see alternatives). (b) The first draft of `parse_draw` silently dropped `tokens`/`root_type` on decoded draws because a text replacement did not match after the auto-formatter reflowed the file; the round-trip unit test caught it; the full pipeline was re-run afterwards, so the repaired sample files and every number in `tables.md` come from the fixed code. (c) After seeing the full-run figure I added a clearly labelled post-hoc diagnostic (usable samples inside the collections' size envelope); see 7.1. (d) `analyze.py` gained `--min-valid-seeds` (default 10, the pre-registered value; the pilot used 1).

## 3. Changes made

**Created**
| Path | Purpose |
|---|---|
| `scripts/newpos/genbench/__init__.py` | package marker (names cannot collide with peers' scripts) |
| `scripts/newpos/genbench/common.py` | frozen JSONL I/O, connected/star/shared, LCC repair, iso key, `SampleSet`, JSD/W1, envelope test |
| `scripts/newpos/genbench/sample_ngram.py` | samples `ow_ngram`, `fact_ngram`, `incidence_ngram` as `run_sample_unit` does; frozen-format files, 6 workers |
| `scripts/newpos/genbench/evaluate.py` | scores any frozen-format directory; derived LCC arm; noise floors; `units.csv`, `arrays/`, `collections.json` |
| `scripts/newpos/genbench/analyze.py` | tables and tests (BCa, matched fidelity, Holm one-sided paired Wilcoxon, direction check, RQ6 reproduction) |
| `scripts/newpos/genbench/fig_rejection_bias.py` | one PDF figure (m of usable samples, star fraction, yield per 10,000 draws) |
| `scripts/newpos/genbench/run_all.sh` | reproduces the whole 27-seed pipeline |
| `scripts/newpos/genbench/README.md` | usage, contract, definitions |
| `tests/newpos/test_genbench.py` | 89 unit tests |
| `.claude/notes/2026-10-13-newpos-w1/genbench-ngram.md` | this log |

**Modified:** none (no file of `src/`, `experiments/`, `docs/` or a peer was touched).

**Removed:** none.

**Results written outside the repo** (`/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/NEWPOS_2026-10-13/genbench_ngram/`):
`samples/` (162 frozen-format files: 3 arms x 2 collections x 27 seeds; seeds 60000-60002 plain `.jsonl`, the rest `.jsonl.gz`; 144 MB),
`samples_repaired/` (54 files, the `fact_ngram_lcc` arm), `scores/` (`units.csv` 216 rows, `collections.json`, `rows/`, `arrays/`),
`tables.md`, `stats.json`, `fig_rejection_bias.pdf`, `scores_pilot/` + `pilot_analysis/` (3-seed pilot), and the pipeline logs.

**Commits**
| SHA | Message |
|---|---|
| `93e0190` | `feat(newpos): generation benchmark on usable samples (sampler, evaluator, analysis, figure)` |
| (this file's commit) | `docs(notes): genbench-ngram work log` |

## 4. Tests

**Tests created or extended** (all in `tests/newpos/test_genbench.py`, `pytestmark = pytest.mark.unit`)
| Test | What it verifies | Why it matters |
|---|---|---|
| `test_star_classification` (8 cases) | star vs relational: centre in every fact and no other constant twice; one-fact KB is a star; 3-path, triangle, two-shared-constants are not; empty is not | the HA2 quantity; the definition also reproduces 53.4 % / 3.0 % on the real collections |
| `test_connectivity_matches_sparse_hypergraph` (40 random KBs) | `gb.is_connected` equals `SparseHypergraph.is_connected` | RQ6 counts must be reproduced |
| `test_sample_set_profile_matches_library_profile`, `test_jsd_profiles_match_library_fidelity`, `test_take_preserves_profile_and_order` | bincount profile equals `fidelity.profile`; JSDs equal `fidelity.fidelity`; CSR gather is exact | the numbers must be the library's |
| `test_draw_line_roundtrip_plain_and_gzip`, `test_malformed_lines_are_rejected` (5) | frozen contract round trip (plain and gzip, tokens kept), bad lines rejected | caught the dropped-`tokens` bug |
| `test_evaluator_counts`, `test_uniqueness_and_novelty_are_keyed_by_isomorphism_class`, `test_usable_set_excludes_disconnected_and_empty` | decoded/connected/usable/empty counts; a relabelled copy is the same class; novelty vs the collection; singleton variant | hand-made file with known answers |
| `test_fidelity_is_withheld_below_min_usable`, `test_fidelity_is_computed_from_min_usable` | `u < 100` gives NaN usable-fidelity columns, `u >= 100` gives values | amendment 2 |
| `test_connected_flag_is_audited_not_trusted`, `test_evaluator_reads_any_generator_name_from_files` | file flag is audited; arbitrary generator names work | generator-agnostic contract |
| `test_lcc_*` (6) and `test_repair_arm_is_always_usable` | keeps the component with most constants, renumbers, ties go to more facts then lowest `(root, word)`, rule-disagreement flag, connected KB untouched, lone constant stays unusable | the repair baseline |
| `test_envelope_membership` (6), `test_posthoc_envelope_columns` | n <= 24, 3 <= m <= 110, arity <= 10 | the post-hoc diagnostic |
| `test_matched_averaging_is_deterministic_and_full_set_is_exact` | seeded, full-size subsample equals the unsubsampled value | amendment 1 |
| `test_test_rows_orientation_and_holm`, `test_cell_with_too_few_seeds_is_untestable`, `test_ha1_verdict_requires_direction` | one-sided orientation (rank-biserial +1 when baseline worse), Holm, 10-seed rule, SUPPORTED/WRONG-DIRECTION/NOT SUPPORTED/INSUFFICIENT | the pre-registered decision rules |
| `test_collection_star_fractions_match_the_brief` (real corpora) | 0.534 (wd50k66), 0.030 (ndc_classes) | definition check required in 7.0.3 |
| `test_sampler_reproduces_rq6_validity_and_connectivity` x3 (real corpora) | `ow_ngram`, `fact_ngram`, `incidence_ngram`, ndc_classes, seed 60000, 500 samples: `n_valid` and `n_connected` equal `run_sample_unit`'s, and the evaluator's recomputed connectivity matches | required test |

**Coverage of the behaviour that matters:** every definition of 7.0.3, the contract, both repair tie rules, the amendment rules, and the real-collection checks.

**Not tested, and why:** the multiprocessing drivers (`run`, `_task`) and `fig_rejection_bias.py` are exercised only by the real run, not by unit tests (they need real corpora and take seconds, not milliseconds); `analyze.run` end to end likewise. The statistical helpers it calls (`bca_ci`, `wilcoxon_paired`, `holm`) belong to `experiments/tkde/stats.py` and are tested there.

## 5. Test results

**Command:** `~/.conda/envs/isalhg/bin/python -m pytest tests/newpos/test_genbench.py -q -p no:cacheprovider`

```
collected 89 items

tests/newpos/test_genbench.py .......................................... [ 47%]
...............................................                          [100%]

============================== 89 passed in 2.32s ==============================
```

**Result:** 89 passed, 0 failed, 0 skipped · **Duration:** 2.3 s · **Run at:** `93e0190` (the notes commit changes no code)

Lint: `ruff check scripts/newpos/genbench tests/newpos/test_genbench.py` -> `All checks passed!`; `ruff format --check` -> `7 files already formatted`.

**Failures and their resolution:** one failure during development, `test_draw_line_roundtrip_plain_and_gzip` (`draws[0].tokens == ()` instead of `("a", "b")`): the decoded branch of `parse_draw` dropped `tokens`/`root_type`. Fixed in `common.py`; 82/82 passed after the fix (89 after the envelope tests). The first full-pipeline run happened before that fix, so I discarded it and re-ran the whole evaluation and analysis with `FORCE=--force bash run_all.sh`. A second class of failures was lint (27 findings: `E501`, `ANN401`, `SIM115`, `SIM113`, `I001`), all fixed.

## 6. Verification beyond unit tests

| Circumstance | What was run | Evidence | Outcome |
|---|---|---|---|
| Reproduction of RQ6 | `analyze.py` reproduction section: 27 seeds x 3 arms x 2 collections against `RQ6_generation/generation/rows_samples.csv` | `n_valid` and `n_connected` equal on all 162 units; max relative difference of the five all-decoded JSDs is 0 (6.3e-15 on one `jsd_pred`) | pass: identical, not merely 3 s.f. |
| Collection structure | `EvalContext.from_collection` | star fraction 0.5336 (wd50k66, 3,988 members), 0.0304 (ndc_classes, 1,381); 3,682 and 557 distinct iso classes among members | pass (brief says 53.4 % / 3.0 %) |
| Connectivity totals | sums of `units.csv` | fact list connected 112,252/270,000 = 41.57 % (ndc) and 34,009/270,000 = 12.60 % (wd50k66); ordered walk 270,000/270,000 connected on both (52 of them are lone constants with no fact: 17 ndc, 35 wd50k66; they are not usable) | matches the paper's 41.6 % / 12.6 % / 270,000 |
| Incidence decoding | sums of `units.csv` | decoded 5,135/270,000 (ndc, 1.90 %) and 2,764/270,000 (wd50k66, 1.02 %); connected among them 467 and 23; usable per seed median 17 and 1 (max 27 and 3), so 0/27 seeds reach 100 | matches the paper's 1.9 % / 1.0 %; excluded from fidelity tests by amendment 2 |
| Audit counters | `units.csv` | `n_flag_mismatch` 0 and `n_key_error` 0 on all 216 units (the generator's `connected` flag always agrees with the recomputation; every usable sample was fingerprinted) | pass |
| LCC rule audit | `n_lcc_rule_disagree` | 14 draws of 270,000 (ndc) and 1,342 of 270,000 (wd50k66, 0.5 %) where a facts-first reading of "largest" would have kept another component | the constants-first choice affects at most 0.5 % of repaired draws |
| Scale / performance | `run_all.sh` | 216 units evaluated in about 23 s wall (6 spawn workers, 242 CPU-s); sampling 10,000 draws per unit takes 1-7 s | trivial cost; at most 6 worker processes used; peak RSS was not measured (the library's n-gram memo is a 1,024-entry LRU) |
| Environment | `isalhg` conda env | Python 3.11.15, pytest 9.0.3, C++ engine and `pynauty` present, no new dependency | pass |
| Figure | `pdftoppm` render of `fig_rejection_bias.pdf` | viewed the PNG: 2 x 3 panels render; the incidence arm is named but not drawn in (a), (b) because u < 100 | pass; the "u < 100" note sits near the right axis edge |

## 7. Decisions, assumptions, open questions

### 7.0 PRE-REGISTRATION (written before any usable-sample fidelity number of my own pipeline existed)

Status of my own data when this section was written: no sampler, evaluator, pilot or full run had executed.
The only fidelity numbers I had read were the already-published RQ6 all-decoded tables
(`.../IEEETKDE_isal_consensus/RQ6_generation/generation/tables.md`), which score ALL decoded samples. I had
seen no usable-sample (decoded and connected) fidelity number of any kind. The reviewer amendment
(7.0.2) arrived while I was still reading code, before the first evaluator existed.

#### 7.0.1 Hypotheses as given in the prompt (verbatim intent, unchanged)

- HA1 (rejection bias): for each baseline, JSD_m, JSD_n and W1_m of the usable subset against the collection
  exceed those of `ow_ngram`; per collection, one-sided paired Wilcoxon over seeds, Holm across the family of
  (baseline x metric x collection), alpha 0.05, effect size rank-biserial.
- HA2 (relational structure): |relational fraction(usable) - relational fraction(collection)| is smaller for
  `ow_ngram` than for each baseline. Star = one constant occurs in every fact and no other constant occurs in two facts;
  otherwise relational.
- HA3 (yield): VUN per draw of `ow_ngram` exceeds that of each baseline.
- Baselines: `fact_ngram`, `incidence_ngram`, and the repair arm `fact_ngram_lcc`.

#### 7.0.2 Reviewer amendment received from `main` (verbatim)

1. Never compare fidelity at equal DRAWS; compare at equal numbers of USABLE samples. For each
   (collection, seed, baseline): u_b = the baseline's usable count. Compute w°'s fidelity on a random subsample of
   w°'s usable samples of size u_b (20 subsamples per seed, averaged, seeded). This matched comparison is the PRIMARY
   fidelity test; the unmatched one is secondary. For `fact_ngram_lcc` (always usable), match at the same count as
   `fact_ngram`'s usable count AND at 10,000.
2. If u_b < 100 on a seed (expected for `incidence_ngram`, about 1 usable in 11,739 draws on wd50k66), do not compute
   fidelity for that arm/seed. Mark it "insufficient usable samples (u = ...)" in the table and exclude it from the fidelity
   tests. Do not draw extra samples to rescue it.
3. Pre-stated bias direction: the mechanism predicts the baselines' usable samples are SMALLER and more STAR-like than the
   collection: mean m and mean n below the collection's, star fraction above it. HA1 holds only if the divergence is in that
   direction. A divergence in the other direction is reported as a falsification of the mechanism, even if the JSD is larger.
4. The LCC-repair arm is the baseline's strongest construction. A fidelity win for w° goes in the main text only if it also
   holds against `fact_ngram_lcc` at matched usable counts. Report the comparison either way.

#### 7.0.3 Operational definitions fixed now (interpretations of ambiguous wording; recorded before data)

- `connected` follows RQ6 exactly: `SparseHypergraph.is_connected()` semantics (one constant is connected; an isolated constant
  disconnects). `usable = decoded AND connected AND m >= 1`. A connected sample with no fact (a lone constant) is outside the domain
  of knowledge bases; it is counted in `n_empty` and is NOT usable. Reproduction of RQ6 `n_connected` uses the RQ6 definition without the `m >= 1` clause.
- "Unique" = distinct isomorphism classes: `n_unique_usable` is the number of distinct `ordered_fingerprint` keys among the seed's usable samples
  (each class counted once). `vun_per_draw = n_unique_novel_usable / n_draws`, where a class is novel iff its key is not the key of any collection member.
  The prompt's wording ("samples whose class is unique within the set") also admits a singleton reading (classes seen exactly once). The distinct-class reading
  is primary because it is the standard valid-unique-novel convention; the singleton variant is recorded as `n_singleton_novel_usable` and reported as a robustness column, with the HA3 verdict reported under both.
- Iso key = `ordered_fingerprint(H)` = `(root_label, word)` of the sample's own decoded hypergraph, for every arm.
- LCC repair: components of the primal graph, including isolated constants as one-constant components. "Largest" = most constants; ties: more facts, then lowest
  `(root_label, word)` of the component. The prompt's tie list ("more facts, then more constants") makes one of the two criteria redundant under every reading; I use the
  graph-theoretic reading (constants first) and count the draws where facts-first would have picked a different component (`n_lcc_rule_disagree`) so the choice is auditable. Constants of the kept
  component are renumbered `0..n'-1` in increasing original id; types, predicates and fact order are preserved.
- Star: occurrence count `occ(c)` = facts containing constant `c`. Star iff `m >= 1` and some constant has `occ == m` and every other constant has `occ <= 1`. (A one-fact KB is a star.)
  Check: this definition must reproduce 53.4 % (wd50k66) and 3.0 % (ndc_classes) on the collections; if it does not, I stop and message `main` before the full run.
- Shared constants = number of constants with `occ >= 2`.
- Minimum usable count for any fidelity statistic: `MIN_USABLE = 100` (amendment 2). Below it the usable-fidelity columns are NaN in the row CSV.
  A (collection, baseline) cell is tested iff at least 10 seeds have `u_b >= 100`; otherwise it is reported as "insufficient usable samples" and enters no test and no Holm family.
- Fidelity tests, PRIMARY (matched): for each seed with `u_b >= 100`, w° (and for the `fact_ngram_lcc` comparison at the `fact_ngram`-count, also the LCC arm) is subsampled without replacement to size `s`, 20 repeats, seeded
  by `(collection, seed, baseline, repeat)`, and the metric averaged over repeats; the baseline uses its own usable samples (all `u_b` of them). Metrics: JSD_n, JSD_m, W1_m (HA1 family), and |relational fraction - collection's| (HA2).
  Secondary: the same metrics unmatched (all usable samples of each arm). The other three JSD profiles (arity, pred, type) and W1_n, mean n, mean m, star fraction, shared constants are reported for every arm, matched and unmatched, as descriptive statistics with BCa CIs; they enter no Holm family.
- Tests: one-sided paired Wilcoxon (`experiments.tkde.stats.wilcoxon_paired`, `alternative="greater"`), rank-biserial = matched-pairs `(R+ - R-)/(R+ + R-)` of the differences baseline - w° (positive favours the hypothesis); Holm via `experiments.tkde.stats.holm`.
  Holm families (alpha 0.05): HA1 primary = (baseline x {JSD_n, JSD_m, W1_m} x collection) over the testable cells (at most 3 x 3 x 2 = 18); HA2 = (baseline x collection) (at most 6); HA3 = (baseline x collection) (at most 6); the unmatched secondary analyses form their own families. For `fact_ngram_lcc` there are two matched variants (at `u_fact` and at 10,000); both are reported, the one at `u_fact` is in the HA1/HA2 family, the one at 10,000 is a separate robustness family.
  BCa 95 % CIs (`bca_ci`, 10,000 resamples) on every seed-level mean and on every paired difference.
- HA1 verdict per (collection, baseline), decided by this rule: SUPPORTED iff all three matched tests (JSD_n, JSD_m, W1_m) reject after Holm AND the bias-direction condition holds (mean m below the collection's, mean n below the collection's, star fraction above it, each judged by the BCa CI of the seed-level mean deviation lying strictly on the predicted side of 0).
  WRONG-DIRECTION iff the tests reject but the direction condition fails (reported as a falsification of the mechanism). NOT SUPPORTED otherwise. INSUFFICIENT iff the cell is not testable.
- HA2 and HA3 verdicts: SUPPORTED iff the Holm-corrected one-sided test rejects.
- Everything that departs from these definitions after the full run starts will be listed in 7.1 as a post-hoc change, labelled as such.

### 7.1 Post-registration changes and findings

- Honest ordering of events: pre-registration 7.0 was written first. The first usable-sample numbers I ever saw were a 500-draw
  pipeline smoke (seed 60000, one run per collection) used only to debug the code, followed by the 3-seed pilot below. No
  threshold, definition or test in 7.0 was changed after seeing either.
- Pilot (seeds 60000-60002, 10,000 draws per unit, results in `.../genbench_ngram/pilot_analysis/`): RQ6 reproduced exactly (max relative
  difference 0 on the five all-decoded JSDs, `n_valid` and `n_connected` equal, 3 seeds x 3 arms x 2 collections). Star fraction of the
  collections reproduced: 0.5336 (wd50k66), 0.0304 (ndc_classes). Pilot reading sent to `main` (section 8). Pilot-only deviation: `analyze.py --min-valid-seeds 1`
  so that the descriptive tables are filled with 3 seeds; the pre-registered value 10 is the default and is used for the full run.

- `main` (after the pilot): go ahead with the 27-seed run exactly as pre-registered; add a per-arm star-fraction table next to the collection's. Done with no protocol change (table "Star fraction and size of the usable samples next to the collection's" in `tables.md`).

#### 7.1.1 Full-run results (27 seeds, 10,000 draws per unit; `tables.md`, `stats.json`)

Verdicts under the pre-registered rules (HA1 is "matched, direction-checked"; Holm per family, alpha 0.05):

| collection | baseline | HA1 | HA2 | HA3 (distinct-class reading) |
|---|---|---|---|---|
| wd50k66 | fact list | NOT SUPPORTED | NOT SUPPORTED | SUPPORTED |
| wd50k66 | fact list + LCC | NOT SUPPORTED | SUPPORTED | SUPPORTED |
| wd50k66 | incidence list | INSUFFICIENT | INSUFFICIENT | SUPPORTED |
| ndc_classes | fact list | NOT SUPPORTED | NOT SUPPORTED | SUPPORTED |
| ndc_classes | fact list + LCC | NOT SUPPORTED | NOT SUPPORTED | NOT SUPPORTED |
| ndc_classes | incidence list | INSUFFICIENT | INSUFFICIENT | SUPPORTED |

- **Yield (HA3).** Valid-unique-novel per draw, seed mean [BCa 95 %]: wd50k66 w° 0.8202 [0.8186, 0.8216], fact list 0.0654, LCC 0.7497 [0.7481, 0.7511], incidence 0.00009; ndc_classes w° 0.6841 [0.6826, 0.6855], fact list 0.3235, LCC 0.6874 [0.6858, 0.6889], incidence 0.0017.
  Usable per 10,000 draws: wd50k66 9,999 / 1,260 / 9,992 / 0.85; ndc_classes 9,999 / 4,157 / 9,985 / 17.3 (w° / fact / LCC / incidence). w° beats the fact list and the incidence list by 2x to four orders of magnitude (all Holm p <= 1.2e-5, rank-biserial +1.00). Against the repair: +0.0706 [0.0687, 0.0727] on wd50k66 (p_Holm 4.5e-8), and **-0.0033 [-0.0054, -0.0012] on ndc_classes (LCC higher, p = 0.995, rank-biserial -0.56): HA3 fails there.** Under the singleton reading of "unique" the ndc_classes comparison flips to a w° win (+0.0345 [0.0321, 0.0370], p_Holm 8.4e-6) because the repaired samples repeat classes more often (VUN singleton per draw 0.580 vs 0.615). The HA3 verdict against the LCC on ndc_classes therefore depends on the reading of "unique"; the pre-registered primary (distinct classes) is a null/negative.
- **Rejection bias (HA1): not supported.** In the matched primary tests (w° subsampled to the baseline's usable count), ndc_classes shows the opposite of the hypothesis in all six tests: the fact list and the LCC have lower JSD_n (0.0300 and 0.0093 vs 0.0409), lower JSD_m (0.0255 and 0.0488 vs 0.1255) and lower W1_m (0.375 and 0.287 vs 0.422) than w° (all p = 1). On wd50k66, W1_m favours w° against both baselines (1.46 and 1.46 vs 0.676; p_Holm 8.9e-8), JSD_m favours w° only against the LCC (0.0894 vs 0.0830; +0.0064 [0.0053, 0.0077], p_Holm 1.5e-7) and not against the fact list (0.0847 vs 0.0831; +0.0015 [-0.0010, 0.0037], p_Holm 0.70), and JSD_n is worse for w° than for both baselines (0.0549 vs 0.0436 and 0.0353). No cell satisfies all three tests, so no cell is SUPPORTED. The incidence list is untestable (0/27 seeds with u >= 100).
- **Direction of the bias (amendment 3), seed-level deviation of the usable samples from the collection** [BCa 95 %]: fact list on wd50k66 is smaller as predicted (mean n -1.81 [-1.86, -1.76], 27/27 seeds; mean m -0.21 [-0.27, -0.15], 23/27 seeds) but its star fraction is not higher (-0.026 [-0.030, -0.021]); on ndc_classes it is larger, not smaller (mean n +0.76 [+0.74, +0.77], mean m +0.34 [+0.34, +0.35], 0/27 seeds in the predicted direction) with a star fraction below the collection's (-0.0052 [-0.0061, -0.0044]). The LCC repair keeps n below the collection's (-0.33 wd50k66, -0.39 ndc_classes) but inflates m (+1.07 and +0.09) and on wd50k66 destroys stars (0.320 vs 0.534; deviation -0.213 [-0.215, -0.211]). Even w° deviates: its usable samples are larger on wd50k66 (n +0.70, m +0.42, star -0.076) and slightly smaller and more star-like on ndc_classes (n -0.28, m -0.054, star +0.017). The mechanism "filtering keeps small, star-like KBs" is therefore confirmed for size on one collection (wd50k66 fact list), reversed on the other, and never confirmed for the star fraction.
- **Relational structure (HA2).** |relational fraction deviation|: wd50k66 fact 0.026 < w° 0.0756 < LCC 0.212; ndc_classes fact 0.0052 < LCC 0.0067 < w° 0.0174 (matched). The hypothesis holds only against the LCC on wd50k66 (+0.137 [0.134, 0.141], p_Holm 3.0e-8) and is reversed everywhere else.
- **Matched versus unmatched.** The amendment mattered once: wd50k66 fact list JSD_m is rejected in the unmatched secondary test (p_Holm 0.015) and not in the matched primary one (p_Holm 0.70), because at u about 1,262 the plug-in JSD of the baseline is compared with w°'s from 10,000 samples (matching moved w°'s JSD_m from 0.0804 to 0.0831). The ideal 10,000-draw resampler of the collection scores JSD_n/JSD_m/W1_m = 0.0004/0.0004/0.038 (wd50k66) and 0.0004/0.0002/0.021 (ndc_classes); the split-half floor is 0.0037/0.0045/0.107 and 0.0102/0.0080/0.116; every arm is far above both floors.
- **All-decoded view (RQ6, reproduced exactly).** Fact list JSD_m 0.0489 (ndc) / 0.0749 (wd50k66), w° 0.1249 / 0.0805: restricting the fact list to its usable samples lowers its JSD_m on ndc_classes to 0.0255 (filtering helps rather than hurts it).
- **Post-hoc diagnostic, not pre-registered (added after viewing the figure).** The m histogram shows w° mass at m = 1 and 2 although every collection member has m >= 3. `n_usable_inenv` counts usable samples that also lie in the collections' encodability window (n <= 24, 3 <= m <= 110, arity <= 10). Fraction of usable samples inside the window: w° 0.845 (wd50k66) / 0.807 (ndc_classes), fact list 0.945 / 0.989, LCC 0.891 / 0.929. In-window valid-unique-novel per 10,000 draws: wd50k66 w° 7,261, LCC 6,945, fact list 597; ndc_classes w° 5,838, LCC 6,381, fact list 3,190 (the LCC leads w° by 9 % there). In-window fidelity (unmatched, descriptive; JSD_n / JSD_m / W1_m): wd50k66 w° 0.0092 / 0.0201 / 0.62, LCC 0.0124 / 0.0314 / 1.71, fact 0.0350 / 0.0583 / 1.35; ndc_classes w° 0.0155 / 0.0245 / 0.40, LCC 0.0045 / 0.0126 / 0.26, fact 0.0307 / 0.0200 / 0.37. So most of w°'s raw JSD_m deficit on ndc_classes (0.125) comes from usable samples outside the collection's size window (about 19 % of its usable samples), not from a bias towards small or star-like KBs. This is a diagnostic; the pre-registered verdicts above are unchanged by it, and a window filter is itself a rejection step that the paper's "w° needs no filter" claim does not cover. Nothing from this paragraph enters a Holm family.
- **Net reading.** The robust, claimable result is yield: every sample of w° is connected, 99.99 % are usable, and 82 % (wd50k66) / 68 % (ndc_classes) of draws are valid-unique-novel, against 6.5 % / 32 % for the fact list and about 0 for the incidence list. Against the strongest baseline (fact list + LCC repair) the yield margin is +0.071 on wd50k66 and zero or negative on ndc_classes, and the repair keeps JSD_n and, on ndc_classes, JSD_m and W1_m closer to the collection than w°. The rejection-bias mechanism (HA1) and the relational-structure claim (HA2) are not supported and should not be written into the paper; the star-destruction by the LCC repair on wd50k66 (0.32 vs 0.53) is the one structural point in w°'s favour.

### 7.2 Other decisions, assumptions, open questions

**Decisions with a real trade-off**
- Distinct-class reading of "unique" as primary (standard VUN) — costs: the ndc_classes comparison against the LCC fails under it and passes under the singleton reading; both are reported.
- `usable` requires `m >= 1` (not in the prompt's wording) — costs: 52 of 540,000 w° draws (lone constants) are excluded; RQ6's `n_connected` is reproduced without the clause.
- LCC "largest" = most constants — affects at most 0.5 % of repaired draws (audit column).
- Matched analysis keeps the baseline's own usable set and subsamples w° only (as the amendment says), except the LCC at `u_fact` where both are subsampled to the same size.

**Assumptions I proceeded on**
- "Seeds 0-2 uncompressed" means the first three RQ6 seeds, 60000-60002 (verified: `seeds(6, 27)` = 60000..60026). If a different reading was meant, only file names/suffixes change.
- The class key is computed on the sample's own decoded hypergraph under the collection's vocabulary sizes, so two samples with different root types are different classes (as in Theorem C's complete invariant).
- Roles are not part of the frozen format, so the wd50k66 fact list is scored role-free (the generator was fitted with roles on, as RQ6 does).

**Open questions for the orchestrator**
- Whether the paper should define the domain by the collection's size window as well as by connectivity; the post-hoc table says this changes the fidelity reading on ndc_classes. I did not change the pre-registered definition.
- The LCC repair discards parts of a sample; I did not measure how many facts it throws away (a natural follow-up for "repair is lossy").

## 8. Coordination

**Messages sent:** one, to `main`, after the pilot: the 3-seed pilot table (yield, unmatched fidelity, bias direction), my reading (HA3 holds against fact list and incidence, small or absent margin against the LCC; HA1 not supported; HA2 reversed against the raw fact list) and the evaluator/analysis CLI for relay to `neural-gen`. Outcome: `main` replied "go ahead with the 27-seed run exactly as pre-registered; no protocol changes; report HA1/HA2 as negative if confirmed", and will relay the evaluator.

**Messages received and how they changed the work:**
1. `main`: peers cannot be addressed by name; route every peer communication through `main`. I sent the CLI hand-over to `main`, not to `neural-gen`.
2. `main` (reviewer amendment): compare fidelity at equal numbers of usable samples (primary), exclude arms with `u < 100`, pre-state the bias direction, treat the LCC arm as the baseline's strongest construction. Written into 7.0.2 and implemented (matched analysis, `MIN_USABLE`, `direction()`, LCC at `u_fact` and at the full set). It arrived before the first evaluator existed, so it is part of the pre-registration, not a post-hoc change.
3. `main` (after the pilot): proceed unchanged; add the per-arm star-fraction table next to the collection's (done).

**Contracts I depend on and confirmed unchanged:** the frozen JSONL sample format (parsed strictly; malformed lines raise `SampleFileError`), `experiments.tkde.rq6` (`build_context`, `run_sample_unit`, `CollectionContext.model`), `experiments.tkde.stats` (`bca_ci`, `wilcoxon_paired`, `holm`), `isalhg.generation.fidelity` and `ordered_fingerprint` — all read-only, none modified.

## 9. Deliberately not done

- Any neural model, any compression/bit-length analysis (peers' scope).
- Edits to `src/`, `experiments/`, `docs/`, the paper, the shared experiment log (orchestrator's).
- Drawing more samples for `incidence_ngram` (u = 1 and 17 per seed): excluded from fidelity tests by amendment 2; yield and decoding rates are reported.
- A significance test on the post-hoc envelope diagnostic: it is descriptive only, to keep it out of every Holm family.
- Measuring how many facts the LCC repair discards (not part of the registered metrics).
- Peak-RSS measurement of the sampler and evaluator.

## 10. Risks and follow-ups

| Item | Severity | Detail | Suggested owner |
|---|---|---|---|
| "Usable" does not imply "inside the collection's size window" | medium | 15-19 % of w°'s usable samples have m < 3 or fall outside n <= 24 / m <= 110 / arity <= 10; the fact list's are 1-6 %, the LCC's 7-11 %. This drives w°'s raw JSD_m on ndc_classes. If the paper's domain is "KBs the collection could contain", the filter-free story needs this stated. | orchestrator / paper owner |
| HA3 vs the LCC on ndc_classes is reading-dependent | medium | distinct-class reading: LCC higher by 0.0033; singleton reading: w° higher by 0.0345. | orchestrator (choose the reading before writing) |
| LCC repair is lossy | low | not measured how many facts/constants are discarded per repaired draw; cheap follow-up from `samples_repaired/` tokens vs facts. | next wave |
| Neural samples scored with this evaluator | low | the evaluator assumes the contract and the collection's vocabularies; roles are not carried; `analyze.py` needs `--rq6-rows ''` and arm names via `--ours/--baselines`. | `neural-gen` via `main` |
| `incidence_ngram` fidelity untestable | low | u = 1 (wd50k66) and 17 (ndc_classes) per seed by construction, not a gap in the code. | none |
| Guard quirk | low | in this sandbox `git` commands only run as `/usr/bin/git` (the rtk rewrite is refused), and a directory called `eval` trips a guard, so the evaluator output directory is named `scores`. | none |

## 11. Self-assessment against the definition of done

| # | Criterion | Met | Evidence |
|---|---|---|---|
| 1 | `sample_ngram.py` writes frozen-format files for 3 generators x 2 collections x 27 seeds; `evaluate.py` scores any frozen-format directory; `analyze.py` produces `tables.md` + `stats.json` (BCa CI, Holm one-sided paired Wilcoxon for HA1-HA3 with rank-biserial); `fig_rejection_bias.py` produces one PDF | yes | 162 files in `samples/`; `scores/units.csv` 216 rows; `tables.md`, `stats.json`, `fig_rejection_bias.pdf` in the results directory; generator-agnostic read verified by `test_evaluator_reads_any_generator_name_from_files` |
| 2 | Per-unit metrics (n_draws ... collection's own values) | yes | `ROW_COLUMNS` in `evaluate.py`; includes all required columns plus the post-hoc envelope columns |
| 3 | All-decoded JSDs and validity/connectivity reproduce RQ6 to 3 s.f. | yes | identical (max relative difference 0; 6.3e-15 on one entry) on all 162 matching units, reproduction table in `tables.md` |
| 4 | Split-half noise floor, 27 splits, beside the arms | yes | "split-half floor (27 splits)" rows in the fidelity tables; plus an ideal-resampler floor |
| 5 | Pilot first, message `main` before the full run | yes | pilot message sent; `main` replied to proceed |
| 6 | Tests pass; all work committed; tree clean; log written and committed | yes | 89 passed; code commit `93e0190`; this log is the final commit; `git status` clean after it |
| - | Reviewer amendment (matched counts, u < 100 rule, direction, LCC match) | yes | 7.0.2, `matched_cell`, `MIN_USABLE`, `direction`, `robustness` family |

**Overall:** I am confident that the machinery is correct (exact reproduction of RQ6 on every unit, 89 tests, zero audit counters) and that the verdicts follow the pre-registered rules without any change after seeing data. The scientific outcome is negative for HA1 and HA2 and positive for HA3 against the fact list and the incidence list; against the LCC repair the yield margin is +0.071 on wd50k66 and negative on ndc_classes under the primary reading. The orchestrator should scrutinise first the post-hoc envelope diagnostic (7.1.1): it is labelled exploratory but it reframes why w°'s JSD_m is high on ndc_classes, and it raises the question of whether "usable" should include the collection's size window.
