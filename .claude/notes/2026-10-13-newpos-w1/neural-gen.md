# Work log — neural-gen

## Identity

| Field | Value |
|---|---|
| Agent | `neural-gen` |
| Wave | `2026-10-13-newpos-w1` |
| Model / effort | `claude-sonnet-5-5` / `xhigh` |
| Branch | `worktree-agent-a9b5d669578441723` |
| Worktree | `/home/mpascual/research/code/IsalHG/.claude/worktrees/agent-a9b5d669578441723` |
| Base commit | `518824a80baf3238e1e565aafd6aaee0271c0bbc` |
| Head commit | the branch HEAD, i.e. the `docs(notes): neural-gen work log` commit that follows code commit `e150855` (it touches only this file) |
| Started / finished | `2026-10-13T14:45+02:00` / `2026-10-13T15:31+02:00` |
| Status | complete |

## 1. Prompt as received

```
# Task: an identical GRU language model over three KB serializations — does the closed language keep its guarantee and its yield under a neural generator? (agent `neural-gen`)

## Mission
Train the same autoregressive GRU language model, with the same architecture, hyperparameters and training budget, on three serializations of the members of two frozen KB collections — the ordered-walk Isal word `w°` (ours), the canonical-rank fact list, and the incidence list — and sample 10,000 draws per (collection, serialization, seed). Decode every draw with the same decoders the paper's n-gram experiment uses, write every draw in the frozen JSONL sample format below, and report validity, connectivity, usable yield, uniqueness, novelty and held-out bits per KB. Working means: a 3-seed pilot reported to `main`, then (if `main` agrees) the 27-seed run, all files on disk, and a short table.

## Why this exists
The paper (IEEE TKDE draft, "knowledge bases as words") proves that every string over the Isal alphabet decodes to a connected KB (Prop. C.4), and shows it with an order-3 n-gram: 270,000 of 270,000 samples valid and connected, while the fact-list n-gram is connected 41.6 % / 12.6 % and the incidence-list n-gram decodes 1.9 % / 1.0 % (NDC-classes / WD50K(66)). A reviewer will say an n-gram is a toy. The theorem says validity = 1 for `w°` under ANY model; the open questions are (a) how the baselines' usable yield behaves under a stronger model that can learn their syntax and long-range constraints, and (b) whether the yield gap and the novelty/uniqueness of usable samples hold. Either outcome is reported. If the GRU learns the fact list's connectivity well, that is a finding to report, not to hide.

## Pre-registered hypotheses (write into your log BEFORE the pilot; do not edit after seeing data)
- **HC1.** `w°` samples: validity = connectivity = 1.000 on every seed (theorem; any failure is a falsification — record the sample).
- **HC2.** Usable yield per draw (decoded ∧ connected) and VUN per draw (usable ∧ unique within the seed's samples ∧ not isomorphic to any collection member) are higher for `w°` than for each baseline on each collection: one-sided paired Wilcoxon over seeds, Holm across the family, alpha 0.05 (with 3 pilot seeds this is descriptive only; the test runs at 27 seeds).
- **HC3 (descriptive).** Held-out bits per KB (test-split NLL in bits, summed over tokens incl. end-of-sequence) per serialization.

## Protocol (identical across serializations — fairness is the point)
- Token sequences exactly as the n-gram experiment builds them (read `experiments/tkde/rq6.py` lines 160-310 and 420-550): `w°` tokens = `_ow_tokens(word)` for `(root_label, word) = ordered_fingerprint(H)` (`src/isalhg/iso_backends/isal_ordered.py`); fact list = the elements of `fact_word(H)` (`src/isalhg/metric_space/distances/fact_levenshtein.py`); incidence list = the elements of `flatten(H)` (`src/isalhg/generation/incidence_baseline.py`). Build the vocabulary over the whole collection (keep a list of the original token objects so sampled ids map back to them), plus BOS/EOS.
- Split per seed: seeded 80/10/10 member split (train/val/test).
- Model: embedding 128, 2-layer GRU hidden 256, dropout 0.2, AdamW lr 2e-3 (weight decay 0.01), batch 64, gradient clip 1.0, at most 60 epochs, early stopping on validation NLL with patience 6, restore best weights. Same for all three serializations. Seed torch, numpy and python per unit.
- Sampling: temperature 1.0, 10,000 draws per unit, `max_len` = 1.25 × the longest TRAINING sequence of that serialization in that collection (record how many draws hit the cap; a capped draw is still decoded as-is).
- Decoding, identical to rq6: `w°` → `_ow_decode(tokens, k, n_types, n_preds, root)` with the root type drawn from the training members' empirical root-type distribution under a seeded RNG; fact list → `decode_fact_word(word, n_types=..., n_preds=...)` (`src/isalhg/core/fact_word.py`); incidence list → `strict_decode(word, n_types=..., n_preds=...)`, rejected when it returns None (record `strict_decode_reason`). `k` = the collection's max required arity as in `build_context`.
- Isomorphism keys for uniqueness/novelty: the `w°` canonical word `ordered_fingerprint(H)` of the decoded KB, against the full collection's members.
- Seeds: pilot = the first 3 of RQ6's seeds (read `experiments/tkde/configs/rq6.yaml`); full = all 27.

## Frozen contract — sample file format (peer `genbench-ngram`'s evaluator reads these; do not deviate)
One JSONL file per (collection, generator, seed): `<collection>__gru_<serialization>__s<seed>.jsonl.gz` with generator names `gru_ow`, `gru_fact`, `gru_incidence`; one line per draw, keys exactly:
`{"collection": str, "generator": str, "seed": int, "draw": int, "tokens": [str, ...], "root_type": int|null, "status": "decoded"|"rejected", "reason": str|null, "n": int|null, "types": [int, ...]|null, "facts": [[pred:int, [arg:int, ...]], ...]|null, "connected": bool|null}`
`n/types/facts` = the decoded KB with constants 0..n-1 (shape of a `KBRecord` JSON, see `src/isalhg/datasets/kb/base.py`); null when rejected. `tokens` = `str()` of each sampled token object.

## Repository orientation
- Repo root: your worktree (checkout of `/home/mpascual/research/code/IsalHG` at the base commit). Corpora loader `experiments/tkde/corpora.py` (`load_collection(name, root="/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE")`). Verified RQ6 facts: `docs/article/D_ART3/foundation/rq6_generation_facts.md`. Stats helpers: `experiments/tkde/stats.py`. CLAUDE.md is loaded for you (read its "Environment hazard" paragraph).

## Your ownership (exclusive write access)
Create or modify ONLY: `scripts/newpos/neural_gen/**`, `tests/newpos/test_neural_gen.py`, `.claude/notes/2026-10-13-newpos-w1/neural-gen.md`, results under `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/NEWPOS_2026-10-13/neural_gen/` (create it), and the new conda env `isalhg-newpos-gru`. Everything else is read-only (`src/**`, `experiments/**`, peers' directories, the main `isalhg` env).

## Base state
Base commit `518824a80baf3238e1e565aafd6aaee0271c0bbc`. Peers branch from the same commit. No rebase/merge/cherry-pick.

## Environment bootstrap
```bash
conda create -y -n isalhg-newpos-gru --clone isalhg        # never install into the main `isalhg` env
~/.conda/envs/isalhg-newpos-gru/bin/pip install torch      # CUDA wheel; verify torch.cuda.is_available()
PY=~/.conda/envs/isalhg-newpos-gru/bin/python
cd "$(git rev-parse --show-toplevel)"
# Scripts insert the repo root on sys.path to import experiments.tkde. The cloned env's editable
# isalhg install points at the MAIN checkout's src/, which is identical to your base commit -- fine,
# since you must not edit src/.
```
If `conda` is not on PATH use `/opt/miniconda/bin/conda`. If the clone path differs (`conda env list`), use the printed path.

## Verification commands
```bash
$PY -m pytest tests/newpos/test_neural_gen.py -q
~/.conda/envs/isalhg/bin/python -m ruff check scripts/newpos/neural_gen tests/newpos/test_neural_gen.py
```
Tests declare `pytestmark = pytest.mark.unit` (strict markers) and must skip cleanly (`pytest.importorskip("torch")`) when torch is absent. Test: vocabulary round-trip (ids → original token objects), the sample-file writer produces exactly the frozen keys, decoding of a hand-made `w°` token list, a tiny 1-epoch train/sample smoke on 20 members.

## Data and shared resources
- Collections: `wd50k66` (3,988 members) and `ndc_classes` (1,381).
- GPU: the local NVIDIA RTX 3060 (12 GB) is yours alone (`CUDA_VISIBLE_DEVICES=0`). CPU: use at most 4 data-loader/decoding processes (24 cores / 31 GB shared with two peers).
- Long runs: launch them with `nohup ... > log 2>&1 &` inside your worktree or results dir, and poll; do not block a single tool call for hours.

## Definition of done
1. `scripts/newpos/neural_gen/{train_sample.py, run.py, summarize.py}` (names may vary): one command trains + samples + decodes one (collection, serialization, seed) unit and writes the JSONL file plus a per-unit JSON summary (epochs, best val NLL, test bits/KB, n_draws, n_decoded, n_connected, n_usable, n_unique_usable, n_novel_usable, n_capped, wall-clock, peak GPU memory).
2. Pilot: 2 collections × 3 serializations × 3 seeds = 18 units; message `main` the pilot table (validity, connectivity, usable/draw, VUN/draw, novelty, test bits/KB, mean ± sd over seeds) and your reading BEFORE the 27-seed run. Then run 27 seeds unless `main` says otherwise; if 27 seeds would take more than ~10 h on this GPU, tell `main` the estimate and stop after the pilot — main will move it to the HPC cluster.
3. Tests pass; all committed (do not commit sample files or checkpoints into git — they go to the results dir); tree clean; log committed.

## Explicitly out of scope
Fidelity metrics beyond the counts above (peer `genbench-ngram` owns the evaluator — main will run it on your files after the merge), compression analysis (peer `compression`), any change to `src/`, hyperparameter search per serialization (one shared configuration; if it clearly underfits one serialization, report it and ask main before changing anything).

## Work log — mandatory
Maintain `.claude/notes/2026-10-13-newpos-w1/neural-gen.md` using EXACTLY the template at `/home/mpascual/.claude/skills/parallel-agents/assets/note-template.md` (read it first; section 1 = this prompt verbatim). Write continuously; final commit `docs(notes): neural-gen work log`. Conventional commits. Never push. Commit everything before finishing.

## Standing obligations
Work only inside your worktree and ownership set. You cannot ask the user: message `main` (SendMessage) with a specific question, record the assumption, keep working. Report failure honestly.

## Peers in this wave (reachable only through `main`)
- `main` — orchestrator ([IsalHG-Article-Iterator]).
- `genbench-ngram` — n-gram generators + the evaluator for the frozen sample format; owns `scripts/newpos/genbench/**`.
- `compression` — bits per KB of each serialization; owns `scripts/newpos/compression/**`.

## Final message format
At most 15 lines: STATUS, BRANCH, WORKTREE, HEAD, LOG, TESTS, then three bullets (pilot/full headline numbers per hypothesis), anything main must know, anything unfinished.
```

## 2. Understanding and plan

**Restatement of the task in my own words:** Train one shared-configuration GRU language model per (collection, serialization, seed) on an 80 % member split, sample 10,000 draws at temperature 1, decode them with the rq6 decoders, and write frozen-format JSONL plus a per-unit summary. The scientific question is whether the closed-language guarantee (validity = connectivity = 1 for `w°`) and the usable-yield / VUN advantage survive a neural generator that can in principle learn the baselines' syntax.

**Approach chosen:**
- Re-use `experiments.tkde.rq6.build_context` unchanged so the three token sequences, the vocabularies' source alphabets, `k`, `n_types`, `n_preds` and the role-aware fact words on `wd50k66` are exactly the n-gram experiment's.
- One model class (`GRULM`: embedding 128 -> 2-layer GRU 256 -> linear), one trainer, one batched ancestral sampler, one decoder dispatch; the serialization enters only through `(tokens per member, decoder)`.
- Decoding and class-key computation in the same process as the unit; units are sharded over at most 4 worker processes (`run.py --shard i/N`) so the cap of 4 CPU processes holds and the single 3060 is shared.
- Per-unit atomic outputs (`*.jsonl.gz`, `*.summary.json`) so a re-launch skips finished units.

**Alternatives considered and rejected:**
- Vocabulary from the training split only — rejected: the prompt fixes "vocabulary over the whole collection".
- Padding ids in the softmax — rejected in favour of a fixed `-inf` mask on the PAD and BOS columns so the normaliser (and hence the held-out bits) is over real symbols only.
- A multiprocessing decode pool inside one unit — deferred until timing shows decode is the bottleneck; sharded workers are simpler and respect the 4-process cap.

**Plan as executed:** steps 1-6 below were all carried out (see sections 3-6 for what was produced and measured), plus the symmetric lr 5e-4 sensitivity run that `main` added after the pilot.
1. Clone env, install torch, verify CUDA.
2. Write this log with the pre-registered hypotheses and commit before any model is trained.
3. Implement `train_sample.py` (data, model, trainer, sampler, decoder, writer), `run.py` (driver with shards), `summarize.py` (tables, stats).
4. Tests, ruff.
5. Time one unit per serialization; run the 18-unit pilot; report to `main`.
6. Full 27 seeds if the estimate is below 10 h and `main` does not object.

**Deviations from the plan:**
- Before the pilot I ran development probes into a scratch directory (outside the results dir): `ndc_classes` `w°` seed 60000 alone, then the six seed-60000 units, then a members round-trip check. I therefore saw one seed's numbers (six units) before the 3-seed pilot existed. The hypotheses (committed at `6845e65`, before any model was trained) were not edited. The pilot units are regenerated from scratch in the results dir with the committed code, and the seed-60000 summaries are compared with the probe's as a reproducibility check.
- `main` relayed the evaluator contract (usable = decoded AND connected AND m >= 1). My frozen definition of usable has no `m >= 1` clause. Rather than change the pre-registered definition, each unit also records `n_zero_fact_usable` (usable draws with no fact), so both notions are exactly reconcilable.
- Unit cost is ~15-30 s, far below the 10 h budget, so no HPC estimate was needed; the 27-seed run followed the pilot report to `main` and `main`'s go-ahead.

## 2b. Pre-registered hypotheses and operational definitions (written before any model was trained)

Committed as `6845e65` at 2026-10-13T14:46:17+02:00, before any GRU training run; frozen from that point. (At the close I corrected the timestamp this sentence first carried, 14:50, to the commit time; no hypothesis text changed.)

**HC1.** On every seed, collection, the `gru_ow` samples satisfy validity = n_decoded / n_draws = 1.000 and connectivity = n_connected / n_decoded = 1.000. Any violating draw is a falsification of the implementation or of Prop. C.4 and its tokens are recorded.

**HC2.** For each collection, usable-per-draw `u = n_usable / n_draws` and VUN-per-draw `v = n_vun / n_draws` are larger for `gru_ow` than for `gru_fact` and for `gru_incidence`. Test at 27 seeds: one-sided paired Wilcoxon (`alternative="greater"`, ours first) over seeds, family = 2 collections x 2 baselines x 2 metrics = 8 tests, Holm at alpha 0.05. With the 3 pilot seeds the comparison is descriptive.

**HC3 (descriptive).** `test_bits_per_kb` = mean over test-split members of the summed token NLL in bits, EOS included, BOS conditioning only. Reported per serialization and collection with no ordering predicted. Caveat fixed now: the three serializations are different codes of the same objects, so bits are code lengths of different strings; `w°` omits the root type, whose cost under the training empirical root-type distribution is reported separately (`test_root_bits_per_kb`) and not added to the headline.

**Amendment A1 (from `main`, relaying the project's reviewer; received 2026-10-13 after the log above was written and before any pilot number existed. I had trained no model and seen no GRU number at the time it arrived).**
A stronger language model may learn the baselines' syntax (Skinnider et al. 2024, Nat. Mach. Intell., "Invalid SMILES are beneficial rather than detrimental to chemical language models"; citation as relayed by `main`, not checked by me), so fact-list connectivity and incidence-list validity may rise toward 1 under the GRU and the gap to `w°` may shrink. Both outcomes are pre-registered, with the sentence each licenses:
- **(a) Gap persists** (a baseline's residual out-of-domain rate stays clearly above 0): the claim is "guaranteed (`w°`, Prop. C.4) versus learned (baselines), with the residual out-of-domain rate printed".
- **(b) Gap closes** (a baseline's residual rate approaches 0): the claim is "the guarantee is model-independent; the baselines need a model strong enough to learn connectivity, measured at residual rate r".
Required reporting in both cases:
- Per baseline and collection, the residual out-of-domain rate `r = 1 - n_usable / n_draws` with its 95 % CI over seeds (also printed for `w°`, where HC1 predicts `r = 0` exactly).
- Per-unit training cost: epochs run, epoch of best validation NLL, training wall-clock and total wall-clock, summarized per serialization, so the report can say whether a baseline needed more training than `w°` to reach its rate.
- No change to the protocol.
`summarize.py` computes `r` and the CI, and the cost table, from the per-unit summaries.

**Operational definitions (frozen):**
- `n_decoded`: draws whose decoder returned a knowledge base (`w°` and fact list always; incidence only if `strict_decode` is not `None`).
- `n_connected` = `n_usable`: decoded draws with `H.is_connected()`. The same notion as rq6's `connectivity`.
- Class key of a usable draw: `ordered_fingerprint(H)` = `(root type, word)`; member keys from the full collection.
- `n_unique_usable`: number of distinct keys among usable draws. `n_novel_usable`: usable draws (with multiplicity) whose key is not a member key. `n_vun`: distinct keys among usable draws that are not member keys. `vun_per_draw = n_vun / n_draws`.
- `n_capped`: draws that emitted `max_len` tokens without `EOS`; they are decoded as they stand.

## 3. Changes made

**Created**
| Path | Purpose |
|---|---|
| `scripts/newpos/neural_gen/ng_data.py` | Serialization selection, `Vocabulary` (ids <-> original token objects), seeded 80/10/10 split, batching |
| `scripts/newpos/neural_gen/ng_model.py` | `GRULM`, `GRUConfig`, trainer with early stopping, held-out NLL, batched ancestral sampler |
| `scripts/newpos/neural_gen/ng_decode.py` | rq6 decoders (imported, not copied), class keys via `ordered_fingerprint`, frozen record builder, tallies, atomic writers |
| `scripts/newpos/neural_gen/train_sample.py` | One unit: train, sample, decode, write JSONL + summary; CLI for a single unit |
| `scripts/newpos/neural_gen/run.py` | Grid driver (seed-major, `--shard`, `--workers`, `--lr/--patience/--max-epochs`, idempotent) |
| `scripts/newpos/neural_gen/summarize.py` | Tables over seeds, residual-rate CIs, cost table, HC1 check, HC2 tests (Holm), frozen-vs-sensitivity table |
| `scripts/newpos/neural_gen/verify_samples.py` | Format check of every line plus independent re-decode of a subset |
| `tests/newpos/test_neural_gen.py` | 30 unit tests |

**Modified:** none outside the ownership set. `src/**`, `experiments/**`, peers' directories and the main `isalhg` env were only read (the genbench evaluator was run from the peer's worktree, read-only, with the main env's interpreter).

**Removed:** none.

**Results written (not in git):** `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/NEWPOS_2026-10-13/neural_gen/` holds 162 `*.jsonl.gz` + 162 `*.summary.json` (frozen recipe, 27 seeds), `summary.md`, `units.csv`, `stats.json`, `verify_full.log`, `pilot_run.log`, `full_run.log`, `eval_pilot/`, `analysis_pilot/`, `eval_full/`, `analysis_full/`, and `sensitivity_lr5e-4/` (18 units + `comparison_vs_frozen.md`).

**Commits**
| SHA | Message |
|---|---|
| `6845e65` | `docs(notes): neural-gen pre-registration (HC1-HC3 + amendment A1)` |
| `30bf26d` | `feat(newpos): GRU generator over three KB serializations (train, sample, decode, summarize)` |
| `82cabb4` | `feat(newpos): sensitivity-recipe flags and frozen-vs-sensitivity table for the GRU runs` |
| `e150855` | `feat(newpos): --max-epochs flag for the GRU grid runner` |
| (final) | `docs(notes): neural-gen work log` (this file, final text) |

## 4. Tests

**Tests created** (all in `tests/newpos/test_neural_gen.py`, `pytestmark = pytest.mark.unit`, module skips when torch is absent)
| Test | What it verifies | Why it matters |
|---|---|---|
| `TestVocabulary` (3) | ids -> original token objects round trip; first-appearance ids after the three specials; specials/unknown tokens rejected | the sampled id must map back to the exact object the decoder expects |
| `TestSplitAndBatches` (7) | 80/10/10 partition on 20/100/1381/3988 members; deterministic and seed/collection dependent; too-small raises; BOS/EOS/PAD layout; empty sequence | paired splits across serializations; EOS counted in the bits |
| `TestDecodeAndRecords` (6) | hand-made `w°` token list decodes to the pinned connected KB (n=6, types, facts); empty `w°` word is the single-constant KB; incidence rejection names `constant_id`; fact word with an isolated constant is decoded but not connected; both statuses emit exactly the frozen keys in order; gzip round trip | the sample-file contract with the evaluator |
| `TestTally::test_counts_follow_the_frozen_definitions` | usable / unique / novel / VUN / copies / capped / zero-fact counts on a hand-built set | the definitions registered before the pilot |
| `TestSampler::test_sample_law_matches_the_exact_sequence_probabilities` | 100,000 draws of a tiny history-dependent GRU (chunked, EOS-compacted) against the exact sequence probabilities, TV < 0.01 (measured ~0.002); capped flag equals "reached max_len" | catches any error in row compaction, hidden-state indexing or capping |
| `TestSampler` (2 more) | PAD and BOS columns have probability exactly 0 and rows sum to 1; `evaluate` bits equal the teacher-forced sum, EOS included | the held-out bits are over real symbols |
| `TestSmokeUnit` (4) | 1-epoch train/sample/decode/write on 20 tiny members for each serialization, files named per the contract, resume skips; all 20 members round-trip vocabulary -> decoder -> class key to their own key | end-to-end path |
| `TestSummarize` (3), `TestRunGrid` (2) | HC1 violation detection; Student-t CI on 3 seeds; frozen-vs-sensitivity pairing on shared seeds; seed schedule (60000..60026), seed-major unit order, shard validation | the aggregation code |

**Mutation check of the sampler test.** I broke the sampler three ways and confirmed the test fails each time: (A) feed back the wrong token rows after compaction, (B) keep the wrong hidden-state rows, (C) append to the wrong output row. An earlier version of the test (small random weights, 40,000 draws, TV < 0.02) passed mutant (B); I strengthened it (weights scaled so the next-token law depends on the history, 100,000 draws, TV < 0.01) until all three mutants failed. The sources were restored byte-identical afterwards (`diff -q`).

**Not tested, and why:** the CUDA sampler (the sample-law test runs on CPU; the CUDA path is exercised by the real runs and by the re-decode check of their output); multi-process sharding (exercised by the real runs, not by a test); the genbench evaluator (not mine).

## 5. Test results

**Command:** `~/.conda/envs/isalhg-newpos-gru/bin/python -m pytest tests/newpos/test_neural_gen.py -q -p no:cacheprovider`

```
tests/newpos/test_neural_gen.py ..............................           [100%]
============================== 30 passed in 1.83s ==============================
```

**Result:** 30 passed, 0 failed, 0 skipped · **Run at:** `e150855` (code identical to the final commit; only this log changed afterwards).

**Lint:** `~/.conda/envs/isalhg/bin/python -m ruff check scripts/newpos/neural_gen tests/newpos/test_neural_gen.py` -> `All checks passed!`; `ruff format --check` clean.

**Failures and their resolution:** none in the final suite. During development: (1) the sampler test initially passed a mutant (above), fixed by strengthening it; (2) ruff reported 12 findings (ANN401 on `Any` hypergraph arguments, SIM115 on `gzip.open` without a context manager, E501 on markdown template lines), fixed by typing with `SparseHypergraph`, using `with`, and a file-level `E501` waiver on `summarize.py`.

## 6. Verification beyond unit tests

| Circumstance | What was run | Evidence | Outcome |
|---|---|---|---|
| Real data, serialization fidelity | every member of both collections: tokens -> vocabulary -> ids -> tokens -> `decode_draw` -> class key | ndc_classes 1,381 and wd50k66 3,988 members, all three serializations: usable = members and key == member key in every case (12/12 cells exact) | pass: the vocabulary + decoder path reproduces each member's own `w°` fingerprint |
| Real data, sample files | `verify_samples.py` on all 162 frozen-recipe files | exact key set and order on every one of 1,620,000 lines; draws contiguous; counts equal the summaries; 200 random lines per file re-decoded from the stored token strings and byte-equal to the stored record: `162 files, 0 failing` | pass |
| Reproducibility | the six seed-60000 units were produced twice (development probe, then pilot, different process layout) | all summary metrics identical; `wd50k66__gru_fact__s60000.jsonl.gz` decompresses byte-identical | pass (bit-reproducible on this GPU with the deterministic flags) |
| Theorem check | `summarize.py` HC1 | 54 `gru_ow` units, 540,000 draws: 540,000 decoded, 540,000 connected, 0 violations | HC1 holds |
| Independent evaluator | genbench `evaluate.py` + `analyze.py` on the 162 files (+ derived `gru_fact_lcc`), `--workers 4` | `eval_full/`, `analysis_full/tables.md`; its decoded/connected recomputation agrees with my counts (ow decoded 1/1, connected 1/1; fact connected 0.7003 / 0.08552; incidence decoded 0.7465 / 0.6797) | agrees |
| Scale / performance | frozen recipe, 3 worker processes sharing the RTX 3060 | 162 units, sum of unit wall-clock 62.6 min, 15-30 s per unit (train 13-29 s), peak GPU 0.2-0.7 GB, peak RSS ~1.9 GB per worker | far below the 10 h budget; no HPC needed |
| Environment | `isalhg-newpos-gru` (clone of `isalhg`), Python 3.11.15, torch 2.14.1+cu130, CUDA 13.0, RTX 3060 12 GB, `CUDA_VISIBLE_DEVICES=0` | `torch.cuda.is_available()` True | ok |

**Headline numbers (27 seeds, mean ± sd over seeds; frozen shared recipe).** `r` = residual out-of-domain rate = 1 - usable/draw, with 95 % BCa CI over seeds. Full tables: `summary.md`.

| collection | arm | validity | connected / decoded | usable / draw | r [95 % CI] | uniqueness | novelty | VUN / draw | test bits/KB | best epoch |
|---|---|---|---|---|---|---|---|---|---|---|
| ndc_classes | `w°` | 1.0000 | 1.0000 | 1.0000 | 0 | 0.436 | 0.759 | 0.408 ± 0.050 | 17.49 (+1.64 root) | 32.6 |
| ndc_classes | fact | 1.0000 | 0.700 | 0.700 ± 0.067 | 0.300 [0.275, 0.325] | 0.281 | 0.348 | 0.155 ± 0.019 | 23.18 | 39.4 |
| ndc_classes | incidence | 0.747 | 0.810 | 0.607 ± 0.071 | 0.393 [0.369, 0.423] | 0.290 | 0.308 | 0.148 ± 0.027 | 26.25 | 48.7 |
| wd50k66 | `w°` | 1.0000 | 1.0000 | 1.0000 | 0 | 0.888 | 0.888 | 0.842 ± 0.018 | 32.29 (+0 root) | 10.9 |
| wd50k66 | fact (role-aware tokens) | 1.0000 | 0.086 | 0.086 ± 0.024 | 0.915 [0.905, 0.923] | 0.951 | 0.929 | 0.077 ± 0.018 | 80.25 | 4.4 |
| wd50k66 | incidence | 0.680 | 0.531 | 0.361 ± 0.036 | 0.639 [0.627, 0.653] | 0.897 | 0.889 | 0.304 ± 0.032 | 58.28 | 21.1 |

For reference, the n-gram campaign (27 seeds): usable fact 0.416 / 0.126, incidence 0.00173 / 0.000085 (NDC / WD50K).

**HC2 (my registered family: ow > fact, ow > incidence, on usable/draw and VUN/draw, two collections, 8 tests; one-sided paired Wilcoxon over 27 seeds, Holm, alpha 0.05).** All 8 reject (p_Holm between 5.96e-8 and 8.4e-6). `w°` is larger in 27/27 seeds in all 8 cells.

**Training cost (A1).** Epochs to best validation: `w°` 32.6 / 10.9 (NDC / WD50K), fact 39.4 / 4.4, incidence 48.7 / 21.1. Training seconds per unit 13-29. Under the frozen cap of 60 epochs, 3/27 fact and 6/27 incidence NDC units (and 1/27 `w°`) ran all 60 epochs without early stopping, so on NDC some baseline models were still improving when training ended; no WD50K unit reached the cap. The WD50K fact list stops at epoch ~4: train NLL keeps falling (4.1 -> 1.5 nats/token) while validation NLL rises after epoch ~6 (10,936-symbol role-aware alphabet, mostly singleton tokens), i.e. it overfits rather than underfits.

**Exploratory (not registered): LCC repair of the fact list** (genbench `--repair-lcc-of gru_fact`; usable also needs m >= 1):
| collection | arm | usable / 10,000 | VUN / draw | jsd_n | jsd_m | star fraction (collection's) |
|---|---|---|---|---|---|---|
| wd50k66 | `w°` | 9,998 | 0.8416 [0.8347, 0.8482] | 0.0165 | 0.0146 | 0.5426 (0.5336) |
| wd50k66 | fact + LCC | 10,000 | 0.9444 [0.9409, 0.9485] | 0.0365 | 0.0582 | 0.1583 |
| ndc_classes | `w°` | 10,000 | 0.4081 [0.3876, 0.4249] | 0.0071 | 0.0145 | 0.0358 (0.0304) |
| ndc_classes | fact + LCC | 9,998 | 0.3567 [0.3317, 0.3819] | 0.0048 | 0.0070 | 0.0277 |
VUN `w°` minus LCC: WD50K -0.1028 [-0.1104, -0.0963] (the repaired fact list is ahead); NDC +0.0514 [+0.0195, +0.0828], p_Holm 0.0104. The repair buys yield at a structural cost on WD50K: the star fraction of its usable samples is 0.158 against the collection's 0.534, while `w°` matches it (0.543). jsd_n, jsd_m are computed on usable samples, unmatched (evaluator, descriptive).

**Empty-word draws.** Over 540,000 `w°` draws, 76 are the empty word (9 NDC, 67 WD50K): the single-constant, zero-fact KB, connected and decodable. My `usable` counts them (HC1 says 540,000/540,000); the evaluator's `usable` (needs m >= 1) does not, giving 9,998 per 10,000 on WD50K. Both counts are in the per-unit summaries (`n_usable`, `n_zero_fact_usable`).

**Sensitivity recipe (`sensitivity_lr5e-4/`, requested by `main`: lr 5e-4, patience 10, all else unchanged; 3 serializations x 2 collections x 3 pilot seeds).** Same seeds, mean usable/draw, frozen -> sensitivity: NDC fact 0.704 -> 0.486, NDC incidence 0.657 -> 0.322, WD50K fact 0.067 -> 0.051, WD50K incidence 0.347 -> 0.353, `w°` 1.000 -> 1.000 (VUN NDC 0.400 -> 0.522, WD50K 0.831 -> 0.842). Caveat that limits what this run can show: with the epoch cap left at 60, every NDC unit (all three serializations, 3/3 seeds) and the WD50K incidence units ran all 60 epochs at the lower learning rate, so for those cells the sensitivity recipe is a shorter effective training budget, not a longer one. It therefore does not answer "the NDC baselines were undertrained" in either direction; the WD50K fact list, which stops early (best epoch ~4.7) under both recipes, is the one cell where it answers: lowering the learning rate does not raise its yield. A run with a higher epoch cap (`run.py --lr 5e-4 --patience 10 --max-epochs 200 --seeds pilot`) is one command and was not run, because `main` specified the recipe.

## 7. Decisions, assumptions, open questions

**Decisions with a real trade-off:**
- `usable` = decoded AND connected AND >= 1 constant (the vacuously connected empty KB is excluded); the evaluator additionally needs m >= 1. Kept my pre-registered definition and report the delta (76 / 540,000 `w°` draws), rather than changing a definition after seeing data.
- Class key for uniqueness/novelty = `ordered_fingerprint(H)` = `(root type, w°)`, member keys from the full collection (as specified). Extra counts `n_copy_train` / `n_copy_heldout` separate copies of training members from rediscovered held-out ones; novelty is reported against the full collection, as asked.
- Unit-level determinism over speed: `torch.use_deterministic_algorithms(True, warn_only=True)`, cuDNN deterministic. It reproduced byte-identical sample files across two runs; the cost is negligible at this model size.
- Dropout is applied on the embedding output, between the two GRU layers (GRU `dropout=0.2`) and before the output projection; the prompt gave only "dropout 0.2".
- Early stopping criterion: validation NLL per KB (sum over tokens, EOS included, mean over sequences); the gradient loss is the token-mean NLL.
- Sampling cap: a draw is capped if it emitted `max_len` tokens without EOS, `max_len = ceil(1.25 x longest training sequence)`; a draw that would emit EOS exactly at position `max_len + 1` is also flagged (negligible: 10-56 capped draws per 270,000 in every cell).

**Assumptions I proceeded on:**
- The fact-list tokens for `wd50k66` are role-aware (`roles: true` in `rq6.yaml`, as `build_context` builds them), although the prompt wrote `fact_word(H)`; kept for parity with the n-gram experiment as `main` confirmed. If wrong, the WD50K fact-list cell changes (vocabulary 10,936 vs a role-free alphabet).
- The RQ6 seeds are `6 * 10,000 + s`, `s = 0..26` (`experiments.tkde.config.seeds(6)`), pilot = 60000-60002.
- The root type of `w°` draws is drawn from the training members' root types (add-one smoothing is only used for the root-bits line).

**Open questions for the orchestrator:**
- Is a higher-epoch-cap sensitivity run wanted (see section 6)? It is the only way to say whether the NDC baselines were undertrained.
- The LCC-repaired fact list leads `w°` on WD50K VUN (0.944 vs 0.842). How the paper frames that (guarantee without a repair step and without distorting the star fraction, versus raw VUN) is an article decision, not mine.

## 8. Coordination

**Messages sent:** to `main`: the pilot report (table, reading, caveats, question on a fact-list sensitivity run). Outcome: `main` replied with decisions (run 27 seeds under the frozen recipe; symmetric sensitivity run; LCC as exploratory with its fidelity cost; report empty-word draws; keep role-aware tokens).

**Messages received and how they changed the work:**
- Amendment A1 (reviewer): pre-register both outcomes, add residual out-of-domain rate with CI and per-unit training cost; written into the log before any trained-model number was seen (I had trained nothing). Implemented in `summarize.py` and the cost table.
- Evaluator command (genbench): run `evaluate.py` / `analyze.py` with `--repair-lcc-of gru_fact` on the pilot and report its yield/VUN; done for the pilot and again for the 27-seed files. Its usable definition (m >= 1) led to the `n_zero_fact_usable` field.
- Sensitivity decision (above): added `--lr/--patience/--max-epochs` to `run.py` and the frozen-vs-sensitivity table.

**Contracts I depend on and confirmed unchanged:** the frozen JSONL format (checked on all 1,620,000 lines with `verify_samples.py` and by the independent evaluator reading the same files); the decoders in `experiments/tkde/rq6.py`, `src/isalhg/core/fact_word.py`, `src/isalhg/generation/incidence_baseline.py` (imported at the base commit, no edits).

## 9. Deliberately not done

- Fidelity metrics beyond the counts (peer `genbench-ngram` owns the evaluator; I only ran it, unmodified, as instructed).
- Compression analysis (peer `compression`); the bits/KB here are model code lengths on held-out members.
- Any change to `src/**`, `experiments/**`, or per-serialization hyperparameter tuning. The sensitivity run applies one alternative recipe to all arms.
- A higher-epoch-cap sensitivity run (not requested; flag available).
- Committing sample files or checkpoints (results dir only; no checkpoints were saved).

## 10. Risks and follow-ups

| Item | Severity | Detail | Suggested owner |
|---|---|---|---|
| NDC baselines possibly undertrained | medium | 6/27 incidence and 3/27 fact NDC units ran all 60 epochs; the lr 5e-4 run is capped at 60 for every NDC unit, so it does not settle this | `main` decides on a `--max-epochs 200` run (one command) |
| WD50K fact list overfits a 10,936-symbol role-aware alphabet | medium | usable 0.086 is below the n-gram's 0.126; a role-free fact alphabet (not run) would change this cell | `main` / article scope |
| LCC repair leads `w°` on WD50K VUN | medium | 0.944 vs 0.842; the repair distorts the star fraction (0.158 vs 0.534) | article framing |
| Held-out bits are across different codes | low | `w°` omits the root type (+1.64 bits NDC, 0 WD50K, reported separately); incidence is not canonical; compare within a serialization or use the compression peer's accounting | `compression` peer / `main` |
| Pilot uses seeds that were also the dev probe | low | numbers identical to the probe; no hypothesis edited | none |
| Incidence members are in stored node order (not canonical) | low | inherited from `flatten`; same as the n-gram experiment | none |

## 11. Self-assessment against the definition of done

| # | Criterion | Met | Evidence |
|---|---|---|---|
| 1 | scripts train + sample + decode one unit and write JSONL + per-unit summary with the listed fields | yes | `train_sample.py`; summaries contain epochs, best val NLL, test bits/KB, n_draws, n_decoded, n_connected, n_usable, n_unique_usable, n_novel_usable, n_vun, n_capped, wall-clock, peak GPU MB |
| 2 | pilot (18 units) reported to `main` with table and reading before the 27-seed run; 27 seeds run (or estimate sent) | yes | pilot report sent; 27-seed run complete: 162 units, 0 failed, `verify_samples.py` 162/162 OK; cost 62.6 min of unit time |
| 3 | tests pass, everything committed, tree clean, log committed | yes | 30 passed; ruff clean; `git status` clean after the final commit |

**Overall:** The pipeline is verified end to end (member round trips, 1.62 M lines re-checked, bit-reproducible, sampler law tested with mutation checks, independent evaluator agrees on yields). HC1 holds on 540,000 draws. HC2 as registered holds in all 8 cells. The scientific picture is less one-sided than the n-gram result: the GRU learns most of the incidence syntax (usable 0.607 / 0.361 against 0.0017 / 0.000085) and part of the fact list's connectivity on NDC, so the residual gap is a gap of 0.30-0.91, not of 0.98-1.00, and outcome (a) of amendment A1 (gap persists, residual rate printed) is the one realised, in all four baseline cells. Scrutinise first: the NDC training-budget question, the role-aware WD50K fact alphabet, and the LCC-repair comparison, where the raw VUN lead of `w°` does not hold on WD50K.
