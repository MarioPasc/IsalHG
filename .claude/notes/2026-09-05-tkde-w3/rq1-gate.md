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

---

# Follow-up (2026-09-06) — wd50k66 has no seed symbol, so the unconditional `+1` is wrong there

Coordinator's question: re-score the probe's pointer number on `wd50k66`, put the
three corpora on one normalizer definition, and say whether the pipeline's 0.500 on
`wd50k66` is consistent. Harvest at the time of writing: 86 tagged `rows_m1` files
(`ndc_classes` 25,104 pairs/arm, `synthetic_rq1` 39,998, `wd50k66` 38,987).

## The structural finding

`experiments/tkde/budget.py::pointer_symbols` prepends `("seed", label)` **only when
`augment` is true**, and `rq1._augment` is `max(n_vertex_labels) > 1`. Measured on the
frozen corpora:

| collection | `n_vertex_labels` | `_augment` | seed symbol in the pointer word? |
|---|---|---|---|
| synthetic_rq1 | 3 | True | yes |
| ndc_classes | 4 | True | yes |
| **wd50k66** | **1** | **False** | **no** |

The probe agrees: `run_probe.ArmA.word` prepends the seed iff `kb.n_types > 1`, and
`f4_corpora.load_wd50k66` leaves WD50K constants untyped.

Consequences for the normalizer now in `analyze_rq1`:

1. On `wd50k66` the pointer arm has **no seed token**, so `d_abs / (len_base + 1)`
   divides by a symbol that is not in the measured sequence. With median
   `len_base = 6` that deflates the response by ~14 % — exactly what turns the
   honest 0.5833 into the reported 0.5000.
2. The `+1` is also being applied to **every non-pointer arm**, which never carries a
   seed symbol (`arm_distance` for those arms measures over the bare word). That is
   confirmed by the coordinator's own number: `fact_rank` on `wd50k66` reads 0.300
   under `+1`, whereas `d/len_base` gives 0.3333.

The correct rule is **`normalized = d / |w_measured(base)|`**: parse tokens `+ 1`
for the pointer arm on a collection with more than one vertex label, and parse
tokens exactly otherwise.

## Pipeline, all three corpora, both normalizers (86-file harvest)

Pointer arm (`isalhg_levenshtein`), censored rows excluded:

| collection | n used | censored | abs med | `len_base` med | `d/len_base` | `d/(len_base+1)` | **correct (`d/|w_measured|`)** |
|---|---|---|---|---|---|---|---|
| synthetic_rq1 | 39,998 | 0 / 39,998 | 19 | 37 | 0.6071 | 0.5882 | **0.5882** (augment) |
| ndc_classes | 22,311 | 2,793 / 25,104 (11.1 %) | 4 | 6 | 0.6000 | 0.5556 | **0.5556** (augment) |
| wd50k66 | 36,464 | 2,523 / 38,987 (6.5 %) | 3 | 6 | 0.5833 | 0.5000 | **0.5833** (no augment) |

`fact_rank`, no censoring on any collection:

| collection | n | abs med | `len_base` med | `d/len_base` = **correct** | `d/(len_base+1)` | probe target |
|---|---|---|---|---|---|---|
| synthetic_rq1 | 39,998 | 4 | 24 | **0.2000** | 0.1898 | 0.188 |
| ndc_classes | 25,104 | 3 | 12 | **0.2222** | 0.2000 | 0.211 |
| wd50k66 | 38,987 | 4 | 13 | **0.3333** | 0.3000 | 0.300 |

`fact_rank` passes the ±0.05 gate on the correct definition too (|Δ| = 0.012 / 0.011 /
0.033), so the `+1` is not needed to make that arm reproduce.

`wd50k66` pointer arm per edit kind — the absolute medians match the probe's §9 row
exactly, while the normalized ones sit uniformly above it (the hash-collision
signature, unchanged from the main analysis):

| edit kind | n | pipeline abs | probe abs | pipeline `d/len_base` | probe nrm |
|---|---|---|---|---|---|
| insert_fact | 7,951 | 5 | 5 | 1.0000 | 0.800 |
| delete_fact | 7,094 | 1 | 1 | 0.2500 | 0.211 |
| add_constant | 7,995 | 4 | 4 | 0.6667 | 0.583 |
| remove_constant | 5,441 | 2 | 2 | 0.3333 | 0.308 |
| insert_fact_new_constant | 7,983 | 3 | 3 | 0.6667 | 0.571 |

## Probe re-scored on its own members and edits, all three corpora

`run_probe.stage_m1` replayed exactly — same corpus construction, same
`SEED_CORPUS`/`SEED_EDITS` streams, same `EDITS_PER_KIND = 10`, same `k` = pair
maximum, same 60 s budget, same `ArmA.word` seed rule — scoring the first `EA` base
KBs (the probe's own `ea_kbs` mechanism). Two distance functions on the identical
words: the probe's `token_levenshtein` (rapidfuzz on raw token tuples) and the
correct `symbol_distance`.

| corpus | EA | pairs | censored | `n_types` | probe as published (`d_buggy/|w|`) | **corrected (`d/|w_measured|`)** | corrected `/(parse+1)` | under-reported |
|---|---|---|---|---|---|---|---|---|
| synthetic | 40 | 1,973 | 0 | 3 | 0.4783 | **0.5686** | 0.5686 | 67.3 % |
| ndc_classes_quarter | 12 | 419 | 60 | 4 | 0.5000 | **0.5556** | 0.5556 | 33.4 % |
| wd50k66 | 25 | 975 | 65 | **1** | 0.5000 | **0.6000** | 0.5000 | 22.8 % |

The published-column values reproduce §9's 0.500 / 0.500 / 0.500 (synthetic at
0.478 on a 40-base prefix of the 300 the probe used). For `wd50k66` the two
right-hand columns differ because `n_types = 1`: `|w_measured| = parse tokens`,
so the `+1` there is spurious — and it lands exactly on 0.500, which is why the
unconditional `+1` made the pipeline's `wd50k66` cell *look* like the published
figure while moving it away from the truth.

## The three targets on one definition, and the answer on `wd50k66`

Definition: `normalized = d / |w_measured(base)|` — parse tokens plus the seed
symbol iff the pointer arm is measured on a collection with more than one vertex
label.

| corpus | corrected probe | pipeline | Δ | within ±0.05 |
|---|---|---|---|---|
| synthetic_rq1 | 0.5686 | 0.5882 | +0.020 | yes |
| ndc_classes | 0.5556 | 0.5556 | 0.000 | yes |
| wd50k66 | 0.6000 | 0.5833 | −0.017 | yes |

**The pipeline reproduces the corrected probe on all three corpora.** NDC agrees to
four decimals; the two others to within 0.02.

**Is 0.500 on `wd50k66` consistent with the other two? No — and it should not be
read as a failure of the pipeline.** 0.500 is what the unconditional `+1`
produces on a collection whose pointer word has no seed symbol; the honest
pipeline value there is **0.5833**, which agrees with the corrected probe's
0.6000. Under the correct denominator the three pointer values are mutually
consistent (0.556–0.600 probe, 0.556–0.588 pipeline); under the unconditional
`+1` they are 0.588 / 0.556 / 0.500, with `wd50k66` pulled 0.083 below its own
corrected target purely by the arithmetic.

Recommended per-collection pointer targets, on the correct definition:
**synthetic_rq1 0.57, ndc_classes 0.56, wd50k66 0.60** (±0.05). `fact_rank` keeps
0.188 / 0.211 / 0.300 and passes on `d/len_base` without any `+1`
(0.2000 / 0.2222 / 0.3333; |Δ| = 0.012 / 0.011 / 0.033); its published targets are
unaffected by the probe's defect (0/2,400 pairs under-reported on E-B words).

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
