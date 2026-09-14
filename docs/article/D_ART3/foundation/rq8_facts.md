# RQ8 fact base — valid completion of a record

*The derivation of record for every RQ8 number the prose may cite. Precondition
for T-KBg. Agent `rq8`, wave `2026-09-13-headline-w0`; campaigns harvested and
analysed 2026-09-14. Ledger: `../../DEVELOPMENT/T-KB/IN-PROGRESS/T-KBaa.md`.
Gate evidence and the pre-registration: `../experiments/RQ8_PILOT.md`.*

**Rule for this file.** A number enters here only with the run that produced it.
The pilot's numbers are marked as the pilot's; they are on off-schedule seeds
and are never mixed with the campaign's.

---

## 1. Run roots and provenance

| what | where |
|---|---|
| Picasso results root | `~/results/IEEETKDE_ow/RQ8_completion/completion/` |
| Picasso runner tree | `~/repos/IsalHG-rq8` (HOME, not FSCRATCH — §7) |
| Picasso library tree | `~/fscratch/repos/IsalHG-tkde` (shared, read-only) |
| conda env | `~/fscratch/conda_envs/isalhg-tkde` (shared, not rebuilt) |
| corpora | `~/fscratch/datasets/isalhg_tkde/corpora/` (read-only) |
| drive mirror | `results/IEEETKDE_ow/RQ8_completion/` (333 files, harvested 2026-09-14) |
| pilot rows (gate G8.1) | `results/IEEETKDE_ow/RQ8/pilot/RQ8_completion/pilot_g8_1/` |
| analysis, free-running | `results/IEEETKDE_ow/RQ8_completion/completion/_tag_b327d7c5/` |
| analysis, Amendment A1 | `results/IEEETKDE_ow/RQ8_completion/completion/_tag_c5380cde/` |
| deployed SHA | `9840460` → `107ed20` on `worktree-agent-a1b4083a2935ce6dd`, from BASE_SHA `704e271` |

## 2. Job ids

| job | id | state | what |
|---|---|---|---|
| `tkde-rq8` (cluster smoke) | 2308337 | COMPLETED 00:05:08 | `--smoke`, staged under `_smoke/`; MaxRSS 6.78 MB |
| `tkde-rq8` (free-running) | **2308339** | COMPLETED 00:20:13 | 81 units, 27 seeds, six arms. Run tag **`b327d7c5`** |
| `tkde-rq8` (Amendment A1) | **2308489** | COMPLETED 00:40:14 | 81 units, 27 seeds, nine arms. Run tag **`c5380cde`** |

Both campaigns are retained. They are **different measurements of overlapping
arms**, not a run and a rerun: the free-running arms answer "what does the model
write", the matched arms "what does it write when asked for one fact". The
analyzer refuses to pool them (`--run-tag` is required when two tags are
present) because an arm in both would otherwise contribute twice to what the
Wilcoxon believes are 27 seed-level replications.

**Count check, both tags:** 81 units each = 27 seeds × {`ndc_classes/non_star`,
`wd50k66/non_star`, `wd50k66/star`}, matching `configs/rq8.yaml`. 333 files =
2 × (81 units × 2 tables + 1 census) + 7 config/manifest artefacts.

## 3. Gate G0 — the star census (FINAL, both corpora)

`is_star` = some constant in every fact **and** every other constant in at most
one. Root convention for the interior/pendant rule: the hub (max fact-degree,
ties by smallest id); on a star this *is* the every-fact constant, so the census
does not depend on it.

| corpus | N | stars | fraction | non-stars | shared constants (median/mean) | shared facts (median/mean) |
|---|---|---|---|---|---|---|
| `ndc_classes` | 1,381 | 42 | **0.0304** | 1,339 | 2 / 2.938 | 3 / 3.500 |
| `wd50k66` | 3,988 | 2,128 | **0.5336** | 1,860 | 3 / 3.254 | 4 / 4.719 |

Substrate pool at `m ≥ 4`: `ndc_classes` 522 (521 non-star, 1 star);
`wd50k66` 2,775 (1,641 non-star, 1,134 star). Every non-star in both pools has
at least one interior fact. **NDC's star stratum is a single member and is not
a reportable stratum.** Cross-checked independently by the `rq3v2` agent: agrees
to the member.

**Citable sentence.** Structure exists in 46.6 % of WD50K(66) entity
descriptions; NDC-classes is 97.0 % non-star, i.e. genuinely relational.

## 4. H8.1 — hit@10 on interior units, Holm over 27 seeds

`hit@10` **is** `usable@10`: a proposal counts only if it decoded, is connected,
and carries the truth's certificate (a complete invariant, Theorem C).

The Holm family is **ours against the baselines**. The other ordered-walk arms
are ours too; putting them in the family would inflate the correction and score
our own arms as competitors. Each is instead tested against the same baseline
family in its own right.

### 4.1 The pre-registered arm, `ow_ngram` — NOT SUPPORTED on either corpus

| corpus | mean | vs `pattern_cooc` | vs `pattern_freq` | vs `fact_ngram` | vs `incidence_ngram` | vs `random_pattern` |
|---|---|---|---|---|---|---|
| `ndc_classes` | 0.1028 | 0.3185, p_H = 1.000 | 0.1806, p_H = 1.000 | 0.0913, p_H = 0.089 | 0.0059, **p_H = 1.4e-05** | 0.0339, **p_H = 1.4e-05** |
| `wd50k66` | 0.0146 | 0.0185, p_H = 0.850 | 0.0126, p_H = 0.248 | 0.0037, **p_H = 8.7e-05** | 0.0002, **p_H = 2.5e-05** | 0.0015, **p_H = 2.5e-05** |

**Verdict: not supported.** The pre-registered fallback applies and RQ8 is a
**supporting exhibit**, not a headline.

### 4.2 The Amendment A1 matched arms — the `wd50k66` lead SURVIVES HOLM

| corpus | arm | mean | verdict vs the whole baseline family |
|---|---|---|---|
| `wd50k66` | **`ow_ngram_1f`** | **0.0463** | **SUPPORTED** — beats all five, every p_H = 1.33e-05 |
| `wd50k66` | **`ow_ngram_ho_1f`** | **0.0481** | **SUPPORTED** — beats all five, every p_H = 1.35e-05 |
| `wd50k66` | `ow_ngram_ho` | 0.0167 | not supported (ties `pattern_cooc` 0.0185, p_H = 0.526) |
| `ndc_classes` | `ow_ngram_ho_1f` | 0.1922 | not supported — beats `fact_ngram` (p_H = 1.4e-05), ties `pattern_freq` 0.1806 (p_H = 0.248), loses to `pattern_cooc` 0.3185 |
| `ndc_classes` | `ow_ngram_1f` | 0.1687 | not supported (same shape) |
| `ndc_classes` | `ow_ngram_ho` | 0.1398 | not supported |

Against `pattern_cooc` on `wd50k66` the matched arms lead **0.0463 / 0.0481
against 0.0185** — 2.5–2.6× — with rank-biserial **+0.989** and **+1.000** over
27 paired seeds. This is the one place in RQ8 where ours wins outright, and it
is Holm-clean.

**Citable sentence — the amendment history belongs in the sentence, not a
footnote.** H8.1 **as originally registered**, over the free-running arm, is
**not supported on either corpus**. Under **Amendment A1, registered before
re-measurement**, it is **supported on WD50K(66)'s relational stratum** — a
completion model over the ordered-walk language proposes the true missing fact
in its top ten 2.6× more often than an item–item co-occurrence recommender
(0.048 against 0.019; Holm-corrected paired Wilcoxon over 27 seeds,
p = 1.3 × 10⁻⁵, rank-biserial 1.000) — and **not supported on NDC-classes**,
where the recommender leads 0.3185 to 0.1922 on what the mechanism table (§7)
shows to be a pattern-prediction gap, not an attachment gap.

Any shorter form of this claim that omits "as originally registered" or "under
Amendment A1" misstates what was pre-registered when, and must not be used.

### 4.3 hit@10 with 95 % BCa intervals — interior, non-star

| corpus | arm | hit@10 | 95 % BCa |
|---|---|---|---|
| `ndc_classes` | `ow_ngram` | 0.1028 | [0.0952, 0.1098] |
| `ndc_classes` | `ow_ngram_1f` | 0.1687 | [0.1593, 0.1769] |
| `ndc_classes` | `ow_ngram_ho` | 0.1398 | [0.1293, 0.1491] |
| `ndc_classes` | `ow_ngram_ho_1f` | 0.1922 | [0.1806, 0.2024] |
| `ndc_classes` | `pattern_cooc` | 0.3185 | [0.3076, 0.3280] |
| `ndc_classes` | `pattern_freq` | 0.1806 | [0.1702, 0.1906] |
| `ndc_classes` | `fact_ngram` | 0.0913 | [0.0854, 0.0976] |
| `ndc_classes` | `incidence_ngram` | 0.0059 | [0.0041, 0.0083] |
| `ndc_classes` | `random_pattern` | 0.0339 | [0.0298, 0.0381] |
| `wd50k66` | `ow_ngram` | 0.0146 | [0.0119, 0.0174] |
| `wd50k66` | `ow_ngram_1f` | 0.0463 | [0.0413, 0.0515] |
| `wd50k66` | `ow_ngram_ho` | 0.0167 | [0.0135, 0.0206] |
| `wd50k66` | `ow_ngram_ho_1f` | 0.0481 | [0.0422, 0.0559] |
| `wd50k66` | `pattern_cooc` | 0.0185 | [0.0144, 0.0235] |
| `wd50k66` | `pattern_freq` | 0.0126 | [0.0102, 0.0167] |
| `wd50k66` | `fact_ngram` | 0.0037 | [0.0022, 0.0052] |
| `wd50k66` | `incidence_ngram` | 0.0002 | [0.0000, 0.0009] |
| `wd50k66` | `random_pattern` | 0.0015 | [0.0006, 0.0030] |

## 5. H8.2 — the star control, which did not behave as pre-stated

Design §4 expected `pattern_cooc ≥ ow_ngram` on stars. Measured on
`wd50k66/star`, pendant hidden facts: **ours 0.1156, `pattern_cooc` 0.0000**,
Δ = +0.1156, p = 5.4 × 10⁻⁶ — ours ahead on the control.

**This is reported with its mechanism caveat, not as a win.** `pattern_cooc`
scores exactly zero because on a star the attachment heuristic is starved: a
star's facts frequently share a pattern, the deterministic attachment then
reproduces a fact the record already carries, and the proposal is refused. The
three-deep rank retry does not rescue it because a star has few distinct
constants of matching type. So the 0.0000 measures **this implementation of the
counting baseline on stars**, not counting as such. The honest reading is that
the star control is uninformative as built, and the paper should say so rather
than claim the control was won.

## 6. H8.3 — validity and connectivity

| quantity | point | 95 % BCa | n |
|---|---|---|---|
| `ow_ngram` validity | **1.0000** | [1.0000, 1.0000] | 81 |
| `ow_ngram` connectivity | **1.0000** | [1.0000, 1.0000] | 81 |
| `fact_ngram` connectivity | 0.6918 | [0.6617, 0.7227] | 81 |
| `incidence_ngram` validity | 0.1906 | [0.1811, 0.2009] | 81 |

Clauses 1 and 2 hold: ours is valid and connected at 1.000 **by theorem**
(Proposition C.8), `fact_ngram` connectivity is 0.692, well below 1.

**Clause 3 fails as written and the threshold was not moved.**
`incidence_ngram` validity is 0.1906, not below the pre-registered 0.05. The
ceiling was ported from RQ6, where sampling is *unconditional*; under
conditional completion the prefix is itself a well-formed serialization, so a
truncated continuation decodes far more often. The clause measures a different
experiment. Reported failed with that reason (L12). The paper's sentence is the
measured **0.191 against 1.000 by theorem**, which is enough.

## 7. The mechanism — attachment miss over one-fact proposals

Numerator and denominator both restricted to proposals adding **exactly one**
fact (Amendment A1). Interior units, non-star stratum, 27 seeds.

| corpus | arm | pattern@10 | Δ1 share | Δ̄ | slots filled | **attach-miss ∣ 1f** | denom |
|---|---|---|---|---|---|---|---|
| `ndc_classes` | `ow_ngram` | 0.3848 | 0.342 | 2.81 | 9.1 | **0.327** | 825 |
| `ndc_classes` | `ow_ngram_1f` | 0.2691 | 1.000 | 1.00 | 7.4 | **0.373** | 1,453 |
| `ndc_classes` | `ow_ngram_ho` | 0.3669 | 0.374 | 2.43 | 8.0 | **0.256** | 1,015 |
| `ndc_classes` | `ow_ngram_ho_1f` | 0.2802 | 1.000 | 1.00 | 6.3 | **0.314** | 1,513 |
| `ndc_classes` | `pattern_cooc` | 0.8911 | 1.000 | 1.00 | 9.9 | 0.643 | 4,812 |
| `ndc_classes` | `pattern_freq` | 0.4363 | 1.000 | 1.00 | 10.0 | 0.586 | 2,356 |
| `ndc_classes` | `fact_ngram` | 0.3513 | 0.200 | 4.45 | 8.2 | 0.303 | 707 |
| `wd50k66` | `ow_ngram_1f` | 0.3176 | 1.000 | 1.00 | 8.7 | **0.854** | 1,715 |
| `wd50k66` | `ow_ngram_ho_1f` | 0.3106 | 1.000 | 1.00 | 8.3 | **0.845** | 1,677 |
| `wd50k66` | `pattern_cooc` | 0.7170 | 1.000 | 1.00 | 10.0 | 0.974 | 3,872 |
| `wd50k66` | `pattern_freq` | 0.6041 | 1.000 | 1.00 | 10.0 | 0.979 | 3,262 |

**The design's §0 attachment mechanism is SUPPORTED at full power, on both
corpora.** Every ordered-walk arm attaches better than either recommender:
0.256–0.373 against 0.643 / 0.586 on `ndc_classes`, and 0.845 / 0.854 against
0.974 / 0.979 on `wd50k66`. The earlier "contradicted" reading (D-KBaa3) came
from an unmatched denominator and is withdrawn; see `RQ8_PILOT.md` §3b.

**The `ndc_classes` deficit is therefore a pattern-prediction deficit**, and a
large one: matched `pattern@10` 0.269–0.280 against `pattern_cooc`'s 0.891. The
n-gram family is the better attacher and the much weaker pattern predictor.

## 8. Deployment deviations, with their measured reason

| deviation | reason |
|---|---|
| runner tree on HOME (`~/repos/IsalHG-rq8`) | FSCRATCH measured **read-only** 2026-09-13: 276.3k files against a 250.0k soft quota, grace expired; `mkdir` returns "Disk quota exceeded" |
| shared `isalhg-tkde` env, `--no-build` | this wave changes nothing under `src/**`; `isalhg.*` must keep resolving to the canonical tree, which every worker asserts |
| `ow_ngram_ho` replaces the design's `ow_gru` | torch absent, dependency out of scope; same enabling rule, declared before measurement (D-KBaa1) |
| `ow_ngram_1f` / `ow_ngram_ho_1f` added | Amendment A1, pre-registered before re-measurement (D-KBaa7) |

Run-time write audit: every write target is `$LOCALSCRATCH` (node-local),
`$ISALHG_RESULTS_ROOT` (HOME) or `~/execs/tkde/logs` (HOME).
`TMPDIR=/localscratch/users/tmp`. Nothing writes to FSCRATCH at run time.

## 9. Capability-table cells (for `tab_kb_representation_properties.tex`)

| column | `w°` (ours) | certificates / vectors |
|---|---|---|
| completion definable | **yes** — the prefix property, Prop. C.8 | **no** — "no completion definable"; neither a canonical certificate nor a vector fingerprint admits the operation |
| completion valid ∧ connected | **1.000 by theorem** [1.000, 1.000] | not applicable |
| hit@10, `wd50k66` interior (matched) | **0.0481** [0.0422, 0.0559] | best competitor `pattern_cooc` 0.0185 [0.0144, 0.0235] |
| hit@10, `ndc_classes` interior (matched) | 0.1922 [0.1806, 0.2024] | best competitor `pattern_cooc` 0.3185 [0.3076, 0.3280] |
| hit@10, free-running | 0.0146 [0.0119, 0.0174] (wd50k66) · 0.1028 [0.0952, 0.1098] (ndc) | as above |

The non-generative rows — `nauty_cert`, `nauty_cert_rows`, `wl_l1`, `netlsd`,
`hpd_jsd`, `bipartite_ged_assign`, `bipartite_ged_path`, `hypercot`, `size_l1`,
`degree_seq_l1` — carry **"no completion definable"** in every RQ8 table, never
an empty cell.

## 10. Pilot (gate G8.1) — kept distinct

The pilot ran on **off-schedule seeds 80900–80902** (`seed_offset: 900`),
disjoint from the campaign's 80000–80026, so no unit the campaign scores was
ever seen by the gate. Its tables are in `../experiments/RQ8_PILOT.md` §3 and
§3c. Every direction it showed is reproduced at 27 seeds; the campaign's numbers
supersede it for citation.
