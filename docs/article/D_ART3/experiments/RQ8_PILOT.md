# RQ8 — valid completion of a record: the proposition, gate G0, gate G8.1

**Declared:** 2026-09-13, wave `2026-09-13-headline-w0`, agent `rq8`.
Pre-registration: `HEADLINE_DESIGN_2026-09-13.md` §0, §2, §4. Every number below
was measured before the Picasso submission, as the gate requires; nothing here
was tuned, and no threshold was moved after a result was seen.

---

## 1. Proposition C.8 — the prefix property

**Proposition C.8.** Let `K` be a connected knowledge base and `w°(K)` its
ordered-walk program. For every `u ∈ Σ_HG*`, the word `w°(K)·u` decodes, the
decoded knowledge base is connected, and it contains every constant and every
fact of `K`.

*Proof.* The decoder `S2H` is a deterministic machine reading one token at a
time: its state is `(H, L, p_1, …, p_k)` and each token is a total function on
that state. After consuming the prefix `w°(K)` the machine is in the state the
emitter simulated, so `H = K` up to the round-trip isomorphism (Lemma C.3) and
in particular `K` is connected.

It remains to show that no token, applied to a state whose `H` is connected and
contains `K`, can leave a state whose `H` fails either property. The alphabet
has five tokens and the argument is one line each:

* `P_i` and `N_i` move a pointer along `L`. They do not touch `H`, so both
  properties are preserved trivially.
* `W` is a no-op. Same.
* `C_i` adds the hyperedge over the constants at `p_1, …, p_i`, all of which are
  already in `L` and therefore in `H`. It adds a fact and removes none; the
  vertex set is unchanged, and a new edge over existing vertices cannot
  disconnect a connected graph.
* `V_{i,j}` adds one hyperedge over the `i` constants at `p_1, …, p_i` together
  with `j` freshly created constants, which the machine chains into `L`
  immediately after `p_1`. Again no fact and no constant is removed. The `j` new
  constants are not isolated: they lie in the new fact, which also contains the
  constant at `p_1`, an existing one — so each new constant is adjacent in the
  primal graph to a vertex of the already-connected component, and the result is
  connected. (`i ≥ 1` holds by the alphabet's own constraint `1 ≤ i`, which is
  what makes this step work; a token adding only fresh constants would not
  exist in `Σ_HG`.)

No token removes a fact or a constant, and no token disconnects. By induction on
`|u|` the claim holds for every continuation. ∎

**Corollary.** A sequence model over `w°` words, conditioned on `w°(K⁻)` as a
prefix, proposes only valid, connected knowledge bases that extend `K⁻`. Its
validity and connectivity are therefore 1.000 *by theorem*, not by filtering —
which is what H8.3 asserts and what the measurement below confirms. No
certificate and no vector fingerprint admits a completion operation at all,
which is why the non-generative rows of every RQ8 table carry the cell
"no completion definable" rather than a number.

**Empirical row beside the proof.** Two independent checks, both green:

| check | scope | result |
|---|---|---|
| pre-implementation probe | 25 members × 8 random continuations × 2 corpora = 400 | 400/400 decoded, 400/400 connected, 400/400 ⊇ `K⁻`, 0 failures |
| property test in the suite | `tests/experiments_tkde/test_rq8_prefix_property.py`, 4 base knowledge bases × 40 random continuations, plus a hypothesis pass at 60 examples | all green |
| the campaign itself | every `ow_ngram` unit of gate G8.1 | validity 1.0000, connectivity 1.0000 on both corpora |

---

## 2. Gate G0 — the star census

`is_star` as frozen in the design §2: **some constant occurs in every fact, and
every other constant occurs in at most one.** NDC declares no root, so the root
is existentially quantified rather than supplied — which is the design's own
phrasing, and makes the census independent of any root convention.

**Root convention** (used only for the *non-root* qualifier of the
interior/pendant rule, never by the census): the root is the **hub** — highest
fact-degree, ties by smallest constant id. On a star this is exactly the
constant contained in every fact, so nothing in §2 depends on the choice.

| corpus | N | stars | fraction | non-stars | non-star shared constants (median / mean) | non-star shared facts (median / mean) |
|---|---|---|---|---|---|---|
| `ndc_classes` | 1,381 | 42 | **0.0304** | 1,339 | 2 / 2.938 | 3 / 3.500 |
| `wd50k66` | 3,988 | 2,128 | **0.5336** | 1,860 | 3 / 3.254 | 4 / 4.719 |

Substrate pool at `m ≥ 4`, which is what RQ8 draws from:

| corpus | pool | non-star | star | non-stars with ≥ 1 interior fact |
|---|---|---|---|---|
| `ndc_classes` | 522 | 521 | 1 | 521 / 521 |
| `wd50k66` | 2,775 | 1,641 | 1,134 | 1,641 / 1,641 |

**Reading.** The design's pre-stated mechanism is confirmed quantitatively.
WD50K(66) is 53.4 % stars — structure exists in 46.6 % of WD50K entity
descriptions — and NDC-classes is 3.0 % stars, i.e. genuinely relational.
WD50K therefore supplies both strata and is where the star control lives.
**NDC's star stratum is a single member and is not a reportable stratum**; it is
printed as `n = 1, not reportable` rather than silently omitted, and the runner
refuses a stratum below `min_pool` with a logged warning.

The `rq3v2` agent computed its own copy independently and agrees to the member
(42 / 2,128).

---

## 3. Gate G8.1 — the local pilot

**Design, and why it cannot have tuned anything.** Three seeds, 200 interior
units per corpus per seed, every arm. The campaign runs the G7 schedule
`seeds(8, 27) = 80000…80026`; the pilot runs `seed_offset: 900`, i.e.
**80900–80902**, which lie outside it. The 80/20 split is drawn from the seed,
so the pilot's evaluation members and hidden facts are disjoint from every unit
the 27-seed run will score. The offset also enters the run tag, so no pilot row
can ever be served to the campaign.

### hit@10 and pattern@10, interior units, non-star stratum

`hit@10` **is** `usable@10`: a proposal counts only if it decoded, is connected,
and carries the truth's certificate. There is no separate corrected column.

| corpus | arm | N | hit@10 | pattern@10 | validity | connectivity | pattern right, attachment wrong |
|---|---|---|---|---|---|---|---|
| `ndc_classes` | **`ow_ngram` (ours)** | 600 | 0.1067 | 0.3750 | **1.0000** | **1.0000** | 0.716 |
| `ndc_classes` | `ow_ngram_ho` (secondary) | 600 | 0.1417 | 0.3850 | **1.0000** | **1.0000** | 0.632 |
| `ndc_classes` | `pattern_cooc` | 600 | **0.3033** | **0.8917** | 1.0000 | 1.0000 | 0.660 |
| `ndc_classes` | `pattern_freq` | 600 | 0.1867 | 0.4400 | 1.0000 | 1.0000 | 0.576 |
| `ndc_classes` | `fact_ngram` | 600 | 0.0950 | 0.3667 | 1.0000 | 0.8670 | 0.741 |
| `ndc_classes` | `incidence_ngram` | 600 | 0.0117 | 0.2700 | 0.1695 | 1.0000 | 0.957 |
| `ndc_classes` | `random_pattern` | 600 | 0.0267 | 0.0833 | 1.0000 | 1.0000 | 0.680 |
| `wd50k66` | **`ow_ngram` (ours)** | 600 | **0.0150** | 0.7317 | **1.0000** | **1.0000** | 0.979 |
| `wd50k66` | `ow_ngram_ho` (secondary) | 600 | 0.0100 | 0.6350 | **1.0000** | **1.0000** | 0.984 |
| `wd50k66` | `pattern_cooc` | 600 | 0.0133 | 0.7067 | 1.0000 | 1.0000 | 0.981 |
| `wd50k66` | `pattern_freq` | 600 | 0.0083 | 0.5850 | 1.0000 | 1.0000 | 0.986 |
| `wd50k66` | `fact_ngram` | 600 | 0.0050 | 0.7417 | 1.0000 | 0.5116 | 0.993 |
| `wd50k66` | `incidence_ngram` | 600 | 0.0000 | 0.4067 | 0.1427 | 1.0000 | 1.000 |
| `wd50k66` | `random_pattern` | 600 | 0.0000 | 0.0317 | 1.0000 | 1.0000 | 1.000 |

### What the gate decides

**H8.1 fails on `ndc_classes` and is a wash on `wd50k66`.** `pattern_cooc`
scores 0.3033 against our 0.1067 on the corpus the design calls genuinely
relational — the stratum where the headline was stated. On `wd50k66` ours leads
0.0150 to 0.0133, which at these rates is noise. The **pre-registered fallback
therefore applies**: the claim reduces to H8.3 plus the measured gap to the
recommender, and **RQ8 is a supporting exhibit, not a headline**. Ruled by the
orchestrator, 2026-09-13, before submission.

**The §0 attachment mechanism is contradicted by measurement, and this is the
correction to fold into the design doc.** §0 states that on non-stars the
completion must also choose attachments, "which the generator learns and
counting cannot". Measured directly rather than inferred from `hit@10` minus
`pattern@10`: among units where an arm got the hidden fact's *pattern* right,
the fraction where it nonetheless missed the *attachment* is **0.716 for
`ow_ngram` against 0.660 for `pattern_cooc`** on `ndc_classes` — the recommender
attaches better than the generator. On `wd50k66` every arm sits at 0.98–0.99,
i.e. attachment is near-hopeless for all of them. The gap on NDC is a
**pattern-prediction** gap (`pattern@10` 0.375 against 0.892), not an attachment
gap.

The one qualification the higher-order arm adds: `ow_ngram_ho` drops the
attachment-miss rate on NDC to **0.632, below `pattern_cooc`'s 0.660**. So the
§0 mechanism is right about *direction* — more model capacity does buy
attachment — and wrong about *magnitude* and about which arm wins overall.

**The secondary arm was enabled by the pre-registered rule, and it does not
close the gap.** The rule fired: `0.1067 < 0.5 × 0.3033 = 0.1517` on
`ndc_classes`. The design named a one-layer GRU; torch is absent from the
campaign environment and adding a dependency was out of scope, so the
orchestrator substituted **`ow_ngram_ho`** — a higher-order n-gram (order 6,
same interpolated Kneser–Ney smoothing, same training words), declared before
the pilot's second pass so it can never be read as post hoc. Order 6 buys
+0.035 `hit@10` on NDC and loses 0.005 on WD50K, and `pattern@10` barely moves
(0.375 → 0.385). It closes about a sixth of a 3× gap on one corpus and nothing
on the other. The finding is a sentence about sequence models, not about the
language: **the n-gram family is a weaker pattern predictor than item–item
co-occurrence.** The arm stays in the full run regardless.

**H8.3: two clauses hold, the third is inapplicable as written and was not
relaxed.**

* ours valid **1.0000** and connected **1.0000** on both corpora — the theorem,
  clean;
* `fact_ngram` connectivity 0.8670 / 0.5116, below 1 as predicted;
* `incidence_ngram` validity 0.1695 / 0.1427, **not** below the pre-registered
  0.05. **The number was not moved.** The 0.05 ceiling was ported from RQ6,
  where sampling is *unconditional*; under *conditional completion* the prefix
  is itself a well-formed serialization, so a truncated continuation decodes far
  more often and the threshold is measuring a different experiment. The clause
  is reported failed with that reason. The paper's sentence is the measured
  0.17 / 0.14 against 1.000 by theorem, which is enough.

### Two construction decisions that would otherwise have measured the harness

Both were found by reading the first smoke's numbers, both are pinned by
regression tests shown failing against the pre-fix behaviour, and both are
recorded here because each changes a reported column.

1. **The incidence prefix drops its `("END",)` terminator.** Keeping it put
   every continuation after the point the strict decoder stops at, so the arm
   decoded its own prefix every time and reported validity **1.0000** — the
   inverse of the H8.3 contrast. Measured on `ndc_classes`: 1.0000 with the
   terminator, 0.1718 without. The declared constant count *is* kept, because
   that is a real constraint of the flat language: a completion over a new
   constant contradicts it and is rejected.
2. **A counting arm whose attachment reproduces an existing fact emits nothing**
   rather than an invalid proposal. Recorded as invalid, it put a counting
   artefact in the validity column at 0.5 — the column H8.3 is read from.

One baseline-strengthening decision, stated so it is not mistaken for a thumb on
the scale: the attachment heuristic retries one position down the degree ranking
when its top choice repeats an existing fact, and anchors on the hub when no
operand type occurs in the record. Without the retry a deterministic heuristic
emits at most one proposal per pattern and the recommender is capped below `k`;
without the hub anchor it would score the recommender's connectivity instead of
its recommendation. Both strengthen the baseline, never ours (L12).

---

## 4. Provenance

| what | where |
|---|---|
| pilot rows | `results/IEEETKDE_ow/RQ8/pilot/RQ8_completion/pilot_g8_1/` (drive) |
| pilot config | `experiments/tkde/configs/rq8_pilot.yaml` |
| campaign config | `experiments/tkde/configs/rq8.yaml` |
| runner / analyzer | `experiments/tkde/{rq8,analyze_rq8}.py` |
| tests | `tests/experiments_tkde/test_rq8_{units,prefix_property,smoke}.py` (82) |
| ledger | `docs/article/DEVELOPMENT/T-KB/IN-PROGRESS/T-KBaa.md` |
| job ids and campaign tables | `docs/article/D_ART3/foundation/rq8_facts.md` |
