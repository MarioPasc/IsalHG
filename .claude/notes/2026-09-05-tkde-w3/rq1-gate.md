# rq1-gate — the RQ1 pointer-arm reproduction gate (0.60 measured vs 0.500 target)

- **Agent** `rq1-gate`, wave `2026-09-05-tkde-w3`, orchestrator `main`.
- **Worktree** `/home/mpascual/research/code/IsalHG/.claude/worktrees/agent-aa6b56af065f0e645`
- **BASE_SHA** `522e7023d2cbf58cef679bc77800e11a41c8c8d6` (branch `integration/2026-09-05-tkde-w1`)
- **Env** `~/.conda/envs/isalhg-rq1gate` (clone of `isalhg`, editable install inside this worktree)
- **Date** 2026-09-06 00:41 CEST

## Verdict — (b), a definitional/implementation difference, and the probe is the wrong side of it

The pipeline is right; **the gate target 0.500 is a measurement artifact of a defect
in the probe's distance function**, not of anything in `experiments/tkde/`.

The probe (`scripts/diagnostics/d_art3_probes_2026-09-03/f4_topology/f4_encodings.py`)
measures the E-A response with

```python
def token_levenshtein(w1: Word, w2: Word) -> int:
    return int(_levenshtein().distance(w1, w2))     # rapidfuzz, raw tuples of tokens
```

`rapidfuzz.distance.Levenshtein.distance` compares elements of a generic Python
sequence **by their hash**. `isalhg.core.instructions` tokens are frozen dataclasses,
so `TokenP(i=1)` (advance pointer 1) and `TokenN(i=1)` (retreat pointer 1) satisfy

```
hash(TokenP(i=1)) == hash(TokenN(i=1))   ->  True
TokenP(i=1) == TokenN(i=1)               ->  False
Levenshtein.distance((TokenP(i=1),), (TokenN(i=1),)) == 0     # true answer: 1
```

Pointer moves are the most frequent symbols in `w*_c`, so every advance is silently
matched against every retreat and the probe's E-A distance is **systematically
under-reported**: 67.3 % of pointer-arm pairs on the probe's own corpus. The pipeline
uses `experiments/tkde/budget.py::symbol_distance`, which builds a private alphabet
keyed on **equality** (`encode_symbols`) before calling rapidfuzz on `str`, and is
exact.

This is corpus- and edit-independent and fully accounts for the gap.

**It does not touch the `fact_rank` gate**: E-B words are `("T", …)` / `("F", …)`
tuples with no hash-colliding pair in them — measured 0/2400 pairs under-reported,
identical medians under both distance functions. That is why `fact_rank` reproduces
(0.200 vs 0.188; 0.2308 vs 0.211) and `pointer` does not.

## The four checks

### 1. Reproducing 0.60 from the rows

24 tagged `rows_m1__<8hex>-*.csv` files under
`/media/mpascual/Sandisk2TB/…/RQ1_addressing/addressing/` (306,582 rows, 6 arms).
Normalizer used by `analyze_rq1.m1_response`: `normalized = d_abs / len_base`,
censored and NaN rows dropped.

| collection | arm | n used | median `d_abs` | median `len_base` | median normalized |
|---|---|---|---|---|---|
| synthetic_rq1 | isalhg_levenshtein | 39,998 | 19 | 37 | **0.6071** |
| ndc_classes | isalhg_levenshtein | 10,869 | 4 | 7 | **0.6111** |
| synthetic_rq1 | fact_rank | 39,998 | 4 | 24 | 0.2000 |
| ndc_classes | fact_rank | 11,099 | 3 | 11 | 0.2308 |

Per edit kind, pointer arm, absolute median (pipeline vs probe §9):

| collection | edit kind | pipeline abs | probe abs | pipeline nrm |
|---|---|---|---|---|
| synthetic_rq1 | insert_fact | 17 | 15 | 0.5625 |
| synthetic_rq1 | delete_fact | 16 | 14 | 0.5217 |
| synthetic_rq1 | add_constant | 19 | 17 | 0.6129 |
| synthetic_rq1 | remove_constant | 20 | 18 | 0.6364 |
| synthetic_rq1 | insert_fact_new_constant | 22 | 18 | 0.6615 |
| ndc_classes | insert_fact | 7 | 7 | 1.0000 |
| ndc_classes | delete_fact | 3 | 2 | 0.3750 |
| ndc_classes | add_constant | 4 | 4 | 0.6000 |
| ndc_classes | remove_constant | 3 | 2 | 0.4000 |
| ndc_classes | insert_fact_new_constant | 6 | 6 | 0.8750 |

Word length is not the driver: `len_base` median 37 (pipeline) vs `len_A` median 38
(probe, which counts the extra seed symbol) — the same 37 parse tokens.

Normalizer variants on the harvested rows (pooled median, pointer arm):

| denominator | synthetic_rq1 | ndc_classes |
|---|---|---|
| `len_base` (shipped) | 0.6071 | 0.6111 |
| `len_base + 1` (probe's `len_A`, seed symbol counted) | 0.5882 | 0.5556 |
| `max(len_base, len_edit)` | 0.5769 | 0.5000 |
| `mean(len_base, len_edit)` | 0.6019 | 0.5882 |

No normalizer choice reaches 0.500 on `synthetic_rq1`.

### 2. Re-running the probe's method on the same members and edits

The probe script is runnable in this env. Four cells, all scored with the probe's
own `word_A` (C++ `algorithm="canonical"`, `k` = pair max, seed prefix), 120 base
members × 5 edit kinds × 4 edits = 2,400 pairs each:

| cell | corpus | edits | distance fn | abs med | nrm `d/len_A` |
|---|---|---|---|---|---|
| A | probe `gen_synthetic(2000, 20260904)[:120]` | probe `sample_edits` | probe `token_levenshtein` | 16 | **0.4902** (reproduces the probe's 0.500) |
| B | frozen `synthetic_rq1` | pipeline `ladders.single_edits` | probe `token_levenshtein` | 16 | 0.4963 |
| C | frozen `synthetic_rq1` | probe `sample_edits` | probe `token_levenshtein` | 15 | 0.5000 |
| A′ | probe corpus | probe edits | **`symbol_distance`** | **18** | **0.5769** (0.600 with the pipeline denominator) |

Cell A reproduces the published 0.500, so the probe is faithfully re-executed.
Cells B and C show the **corpus and the edit sampler are not the cause** — the probe's
number survives on the pipeline's own corpus and its own edits. Cell A′ is the single
definitional change that moves the number: swapping the distance function moves
0.4902 → 0.5769 (probe denominator) / 0.600 (pipeline denominator) on the probe's own
corpus. That is the pipeline's measurement, reproduced end to end.

Head-to-head on 800 identical `(base, edit)` pairs from the frozen `synthetic_rq1`,
same `k`, same `augment`, verified-identical symbol sequences, with a pure-Python
Levenshtein as the referee (160-pair subset):

```
probe token_levenshtein  == true Levenshtein:   40 / 160
pipeline symbol_distance == true Levenshtein:  160 / 160
pooled medians (800 pairs):  pipeline 19  |  probe 16     (nrm 0.6286 vs 0.5233)
```

### 3. Censoring

Censoring cannot explain either collection, and on NDC it pushes the median the
wrong way:

| collection | pairs | censored | median, censored excluded | censored := max observed nrm (5.000) | censored := 1.0 |
|---|---|---|---|---|---|
| synthetic_rq1 | 39,998 | 0 (0.00 %) | 0.6071 | — | — |
| ndc_classes | 11,099 | 230 (2.07 %) | 0.6111 | 0.6250 | 0.6250 |

`synthetic_rq1` has zero censored pairs, so the whole 0.107 gap there is censoring-free.

### 4. Canonical variant, `k`, seed set, augment

All identical between the two paths — this was verified, not assumed:

- **Variant.** Probe: `canonical_string(H, k=kk, algorithm="canonical", backend="cpp")`.
  Pipeline `budget._pointer_payload`: `canonical_string(H, k=k, algorithm="canonical")`
  (backend left at the default). On 240 words from the frozen corpus the two calls
  returned **byte-identical strings, 0 differences** — same tie-complete `w*_c`, same
  neighbour-degree seed cascade, same structural depth 3.
- **`k`.** Probe `stage_m1`: `max(required_k(base), required_k(edit))`. Pipeline
  `rq1._pair_k`: the same expression. Base and edit are both encoded at the pair `k`
  in both.
- **Seed prefix.** Probe `word_A` decides per member (`H.n_vertex_labels > 1`);
  pipeline `rq1._augment` decides per pair (`max(...) > 1`). Measured 0 asymmetric
  pairs in the sample, so this is a latent, not an active, difference.
- **Edit kinds.** `ladders.EDIT_KINDS` and `f4_corpora.EDIT_KINDS` are the same five,
  with the same semantics (cells B and C above confirm this behaviourally).

## Secondary finding — the pipeline's M1 normalizer counts a symbol its denominator omits

`rq1.arm_distance` measures over `pointer_symbols(word, seed_label, augment=…)`, which
prepends `("seed", label)`; `rq1.word_tokens` returns `len(parse(word[0]))`, which does
not. So for the pointer arm on any collection with more than one vertex label — both
RQ1 collections — the emitted `normalized = d_abs / len_base` is `d / (|w| − 1)`,
not `d / |w|`. The probe's `len_A = len(word_A(...))` counts the seed symbol, and
DESIGN §2 says "normalized by `|w(base)|`", so the probe's reading is the intended one.

Effect, measured on the harvested rows: `synthetic_rq1` 0.6071 → 0.5882,
`ndc_classes` 0.6111 → 0.5556. It does not change the verdict (synthetic still fails
a 0.500 target by 0.088) and it is worth at most 0.06.

**Not fixed here, deliberately.** `word_tokens` also feeds the `rows_m3` `tokens`
column (word length as a *language* property, where the seed symbol should not count)
and the `rows_m2` / `rows_m4` length columns. A correct fix therefore changes the
`rows_m1` schema or adds a column, and re-runs the 24 completed M1 units. That is an
orchestrator/PI call about a campaign already in flight, not a scoped patch.
Recommended shape if adopted: keep `word_tokens` as it is, and in `run_m1` emit
`len_base` / `len_edit` as the length of the sequence the distance was measured over
(`word_tokens(...) + int(augment)` for the pointer arm), then re-run RQ1 M1.

## Proposed DESIGN.md amendment (§2, "Gate and fallback") — not applied

> **Gate and fallback.** The pipeline must reproduce the probe within tolerance
> (pooled normalized median of `fact_rank` within ±0.05 of 0.188 / 0.211 / 0.300).
> The `pointer` target is **0.61 / 0.61 / (wd50k66: to be measured)**, not the
> 0.500 / 0.500 / 0.500 of `../foundation/probes_2026-09.md` §9. That row is
> superseded: the probe scored E-A with
> `rapidfuzz.distance.Levenshtein.distance` applied directly to tuples of
> `Sigma_HG` tokens, and rapidfuzz compares generic Python sequence elements by
> hash. `TokenP(i)` and `TokenN(i)` are hash-equal frozen dataclasses, so pointer
> advances and retreats were matched against each other and the E-A response was
> under-reported on 67.3 % of pairs. Re-scoring the probe's own corpus and edits
> with an equality-keyed alphabet (`experiments/tkde/budget.py::symbol_distance`)
> gives 0.577 under the probe's normalizer and 0.600 under the pipeline's — which
> is what the pipeline measures (0.6071 / 0.6111). The `fact_rank` targets are
> unaffected (0/2400 pairs under-reported on E-B words) and stand. The
> qualitative selection conclusion — `fact_rank` responds to a single edit at a
> fifth to a third of the pointer alphabet's response — is unchanged and in fact
> strengthened. A discrepancy is still a bug until explained. No scientific
> fallback: the selection is closed.

`analyze_rq1.GATE_POINTER` (= 0.500) mirrors the DESIGN constant and was left
untouched pending that amendment.

## Files

- `tests/experiments_tkde/test_rq127_smoke.py` — two regression tests in
  `TestSymbolDistance`: `test_hash_equal_but_unequal_pointer_tokens_are_kept_apart`
  pins `symbol_distance((TokenP(i=1),), (TokenN(i=1),)) == 1` (the exact defect);
  `test_the_private_alphabet_agrees_with_a_reference_levenshtein` checks
  `symbol_distance` against a pure-Python Levenshtein on 50 random token sequences
  over a `V/C/P/N` alphabet.

Nothing else was modified. `src/**`, `DESIGN.md` and the results root were not touched.

## Verification

```
$ ~/.conda/envs/isalhg-rq1gate/bin/python -m pytest tests/experiments_tkde/test_rq127_smoke.py -q -k SymbolDistance
5 passed, 55 deselected in 0.11s
```

Analysis scripts (scratchpad, not committed):
`step1.py`/`step2.py` (row reproduction, normalizer variants), `step3.py`/`step3b.py`
(cells A/B/C), `step4b.py`/`step5.py`/`step6.py` (head-to-head, backend equality,
pure-Python referee), `step7.py` (hash-collision census), `step8.py` (cell A′),
`step10.py` (censoring), under
`/tmp/claude-1000/-home-mpascual-research-code-IsalHG/968d7c55-7aac-4378-b6a1-ebe4c7508734/scratchpad/`.
