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
| Head commit | (filled at the final commit) |
| Started / finished | `2026-10-13T14:45+02:00` / (filled at the end) |
| Status | in progress |

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

**Plan as executed:** (see section 3 / 6 as the work proceeds)
1. Clone env, install torch, verify CUDA.
2. Write this log with the pre-registered hypotheses and commit before any model is trained.
3. Implement `train_sample.py` (data, model, trainer, sampler, decoder, writer), `run.py` (driver with shards), `summarize.py` (tables, stats).
4. Tests, ruff.
5. Time one unit per serialization; run the 18-unit pilot; report to `main`.
6. Full 27 seeds if the estimate is below 10 h and `main` does not object.

**Deviations from the plan:** none yet.

## 2b. Pre-registered hypotheses and operational definitions (written before any model was trained)

Written at 2026-10-13T14:50+02:00, before any GRU training run. Frozen from this point.

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

(filled as work proceeds)

## 4. Tests

(filled as work proceeds)

## 5. Test results

(filled as work proceeds)

## 6. Verification beyond unit tests

(filled as work proceeds)

## 7. Decisions, assumptions, open questions

(filled as work proceeds)

## 8. Coordination

(filled as work proceeds)

## 9. Deliberately not done

(filled as work proceeds)

## 10. Risks and follow-ups

(filled as work proceeds)

## 11. Self-assessment against the definition of done

(filled at the end)
