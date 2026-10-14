# Work log — compression

## Identity

| Field | Value |
|---|---|
| Agent | `compression` |
| Wave | `2026-10-13-newpos-w1` |
| Model / effort | `claude-sonnet-5-5` / `xhigh` |
| Branch | `worktree-agent-a1a377c3e23505bac` |
| Worktree | `/home/mpascual/research/code/IsalHG/.claude/worktrees/agent-a1a377c3e23505bac` |
| Base commit | `518824a80baf3238e1e565aafd6aaee0271c0bbc` |
| Head commit | code at `e75e406`; the log commit that follows it is the branch head |
| Started / finished | `2026-10-13T14:30+0200` / `2026-10-13T15:45+0200` |
| Status | complete |

## 1. Prompt as received

````
# Task: description length of a knowledge base — the ordered-walk word vs the nauty certificate and the baseline serializations (agent `compression`)

## Mission
Measure, per member of four frozen KB collections, how many bits each canonical serialization needs to describe the KB's isomorphism class (labels included), under three families of coders: (i) a fixed-width uniform code, (ii) a learned code — held-out cross-entropy under a token n-gram fitted by 5-fold cross-validation, and (iii) generic compressors on the whole collection. Then measure the size of version deltas on the two natural NDC quarterly series. Working means: a per-collection table with medians, BCa CIs and Holm-corrected paired Wilcoxon tests, one figure, and every number traceable to a script and a results file.

## Why this exists
The PI asked for more comparative experiments (tables + figures) where our method wins. Our representation is the *ordered-walk Isal word* `w°`: a program for a pointer machine (alphabet `V_{i,j}`, `C_i`, `P_i`, `N_i`, `W`, with type/predicate labels inside the tokens) emitted along nauty's canonical labelling (Theorem C: it is a complete isomorphism invariant). Its nearest competitor is the nauty certificate itself (the canonical form of the coloured Levi/incidence graph, serialized as bytes or as one symbol per adjacency row): equally exact, but it *names* every vertex by canonical position, whereas the word *never names a constant* (Proposition "name-freedom": it reaches constants by moving pointers). Hypothesis: name-freedom makes the word a shorter description. The draft paper has no measured compactness result; its notes contradict each other ("medians of 6/8 instructions vs 12 certificate rows" vs "a mean of 13.8 walk tokens vs 40 certificate integers on 400 WD50K members"). Your numbers settle it, whichever way they go. A negative result is reported, not hidden.

## Pre-registered hypotheses (write into your log BEFORE the full run; do not edit after seeing results)
- **HB1.** Per KB, `w°` needs fewer bits than the certificate (bytes form and rows form) under the fixed-width code and under the held-out order-3 n-gram code: one-sided paired Wilcoxon over members per collection, Holm across the family, alpha 0.05, rank-biserial effect size; and the whole collection compresses to fewer bytes under xz, zstd and bzip2.
- **HB2.** The same against the canonical-rank fact list and the incidence list.
- **HB3 (versions).** On natural consecutive version pairs of `ndc_classes` (528) and `ndc_substances` (885), the delta from one version to the next is smaller for `w°` than for the certificate, measured as `zstd --patch-from` bytes and as token edit distance; reported separately on constant-preserving and constant-changing pairs (we expect the certificate to win the constant-preserving stratum — report it).
- Stratify every per-KB result by star / relational (star: one constant occurs in every fact and no other constant occurs in two facts) and by fact-count bins.

## Representations (each must be a lossless code of the labelled isomorphism class — verify by decoding or by citing the completeness argument in the code)
1. `w°` — exactly the symbol sequence the registered distance `isal_ow_struct` compares (see `src/isalhg/metric_space/distances/isal_ordered.py` and `src/isalhg/iso_backends/isal_ordered.py::ordered_symbols` / `ordered_fingerprint`), INCLUDING the root type prefix when the vertex vocabulary is non-trivial.
2. certificate bytes — exactly the symbol sequence `nauty_cert` (alias of `nauty_levi_edit`) compares, including any colour signature / partition prefix it prepends (read `src/isalhg/metric_space/representations/nauty_levi_edit.py` and `src/isalhg/core/levi_reduction.py`).
3. certificate rows — the `nauty_cert_rows` symbol sequence (one symbol per Levi node), plus its colour data.
4. fact list — `fact_word(H)` (`src/isalhg/metric_space/distances/fact_levenshtein.py`), the canonical-rank fact list (arm `fact_rank`).
5. incidence list — `flatten(H)` (`src/isalhg/generation/incidence_baseline.py`).
If any representation turns out NOT to carry the labels or the full class, add exactly the missing information as an explicit prefix and say so in the log. Fairness is the point of this experiment: give each competitor its best honest rendering.

## Coders
- **Fixed width:** bits = (L + 1) · log2(|A| + 1), where |A| is that representation's token alphabet over the whole collection and the +1 is an end marker. Also report raw token length L.
- **Learned (primary):** 5-fold CV over members (seeded); fit `TokenNGram(order=3)` (`src/isalhg/generation/ngram.py`) on 4 folds, code the held-out fold: bits(w) = −log2 p(w) including the end-of-word event. Read how `TokenNGram` smooths and handles unseen tokens; if a held-out token is unseen, use one consistent escape scheme for every representation (e.g. escape probability from the model's backoff + log2 of the full-collection alphabet size) and document it. Also report orders 1 and 2 as a robustness row.
- **Generic compressors:** write each collection once per representation as a file, one KB per line; render tokens two ways — (a) space-separated integer ids, (b) one Unicode code point per token (UTF-8) — compress with `xz -9e`, `zstd -19 --ultra` (binary: `/home/linuxbrew/.linuxbrew/bin/zstd`), `bzip2 -9` (`/opt/miniconda/bin/bzip2`); report the better rendering per representation (say which) as bytes per KB; bootstrap CIs by resampling members (≥ 200 reps) and recompressing.
- **Deltas (HB3):** for each consecutive pair (use `experiments.tkde.corpora.consecutive_pairs(col)`; each entry has `a`, `b`, `constant_preserving`), `zstd -19 --patch-from=<old> <new>` bytes on the code-point rendering, and Levenshtein edit distance in tokens (rapidfuzz on code-point strings).

## Repository orientation
- Repo root: your worktree (checkout of `/home/mpascual/research/code/IsalHG` at the base commit).
- Corpora loader: `experiments/tkde/corpora.py` (`load_collection(name, root="/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE")`, `hypergraphs(col)`, `member_ids(col)`, `consecutive_pairs(col)`); records in `src/isalhg/datasets/kb/base.py`.
- Stats helpers (BCa, Holm, paired Wilcoxon, rank-biserial): `experiments/tkde/stats.py` — reuse.
- Context on the representations: `docs/article/D_ART3/experiments/ENCODINGS_WORKED_EXAMPLE.md`; `docs/article/D_ART3/WRITING_BRIEF_2026-10-04.md` §(c) "Compactness".
- Conventions: CLAUDE.md is loaded for you.

## Your ownership (exclusive write access)
Create or modify ONLY: `scripts/newpos/compression/**`, `tests/newpos/test_compression.py`, `.claude/notes/2026-10-13-newpos-w1/compression.md`, and results under `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/NEWPOS_2026-10-13/compression/` (create it). Everything else is read-only (`src/**`, `experiments/**`, `tests/newpos/__init__.py`, peers' directories). If library code needs a change, message `main`.

## Base state
Base commit `518824a80baf3238e1e565aafd6aaee0271c0bbc` ("chore(newpos): probe scripts C2/C3, experiment log, tests package"). Peers branch from the same commit. No rebase/merge/cherry-pick.

## Frozen contracts
None shared with peers except: do not write outside your results subdirectory; results files are CSV/JSON/MD/PDF.

## Environment bootstrap
```bash
PY=~/.conda/envs/isalhg/bin/python     # numpy, scipy, rapidfuzz, pynauty, matplotlib; do NOT pip-install into it
cd "$(git rev-parse --show-toplevel)"
# scripts insert the repo root on sys.path to import experiments.tkde
```

## Verification commands
```bash
$PY -m pytest tests/newpos/test_compression.py -q
$PY -m ruff check scripts/newpos/compression tests/newpos/test_compression.py
```
Tests declare `pytestmark = pytest.mark.unit`. Test: each serializer is deterministic and isomorphism-invariant on a permuted copy of a small KB (`src/isalhg/core/sparse_hypergraph.py::permute`), the fixed-width formula, the n-gram code length equals −log2 of the model probability on a toy corpus, and the escape scheme gives finite bits on an unseen token.

## Data and shared resources
- Collections: `wd50k66` (3,988), `ndc_classes` (1,381) — primary; `wd50k100`, `ndc_substances` (1,745) — controls. Seeds: fold assignment seed 0 primary; repeat the n-gram CV with 5 fold seeds to report CV spread.
- CPU: 24 cores / 31 GB shared with two peers — use at most 4 processes. GPU: not yours.

## Definition of done
1. `scripts/newpos/compression/{serialize.py, measure.py, analyze.py, fig_bits.py}` (names may vary) produce in the results dir: per-KB rows CSV (collection, kb_id, star/relational, n, m, representation, L, bits_fixed, bits_ngram{1,2,3}), a collection-level compressor CSV with bootstrap CIs, a deltas CSV, `tables.md`, `stats.json`.
2. A figure (PDF): per collection, median bits per KB vs fact-count bin for each representation (learned code), plus a panel with collection-level bytes/KB per compressor.
3. Pilot first: run on `ndc_classes` and a 500-member seeded subsample of `wd50k66`, message `main` with the pilot table and your reading BEFORE the full run; continue unless told otherwise.
4. Tests pass; all committed; tree clean; log committed.

## Explicitly out of scope
Generation (peers), neural models, editing `docs/` or the paper, changing any library code, adding dependencies.

## Work log — mandatory
Maintain `.claude/notes/2026-10-13-newpos-w1/compression.md` using EXACTLY the template at `/home/mpascual/.claude/skills/parallel-agents/assets/note-template.md` (read it first; section 1 = this prompt verbatim). Write continuously; final commit `docs(notes): compression work log`. Conventional commits for code. Never push. Commit everything before finishing.

## Standing obligations
Work only inside your worktree and ownership set. You cannot ask the user: message `main` (SendMessage) with a specific question, record your assumption, keep working. Report failure honestly.

## Peers in this wave (reachable only through `main` — they have no addressable names)
- `main` — orchestrator ([IsalHG-Article-Iterator]).
- `genbench-ngram` — scores usable samples of the n-gram generators (fidelity, rejection bias, yield). Owns `scripts/newpos/genbench/**`.
- `neural-gen` — GRU generators over the same serializations; owns `scripts/newpos/neural_gen/**` and the GPU. It will also report held-out neural NLL per KB; main may later ask you to fold that into your table as a fourth coder.

## Final message format
At most 15 lines: STATUS, BRANCH, WORKTREE, HEAD, LOG, TESTS (counts + command), then three bullets (headline bits/KB per representation per collection and the HB1–HB3 verdicts), anything main must know, anything unfinished.
````

## 2. Understanding and plan

**Restatement of the task in my own words:** For four frozen KB collections, compute for every member the code length of its isomorphism class under five serializations (the ordered-walk word `w°`, nauty certificate bytes, nauty certificate rows, the canonical-rank fact list, the incidence list) under three coder families (fixed-width, held-out n-gram, generic compressors), plus version-delta sizes on the two NDC series, with BCa CIs and Holm-corrected paired Wilcoxon tests. Report whichever direction the numbers go.

**Approach chosen:** one `serialize.py` that turns a hypergraph into a per-arm symbol sequence (plus the per-arm observed and theoretical alphabets), one `coders.py` (fixed-width, n-gram with a single escape scheme, compressor drivers), `measure.py` (per-collection per-KB rows, compressor bootstrap, deltas), `analyze.py` (tables, tests, `stats.json`), `fig_bits.py` (PDF). Arms are a registry; the five required arms are the spec'd symbol sequences byte-for-byte, and the extra arms are the "best honest rendering" supplements demanded by the fairness clause and by the amendment from `main`.

**Alternatives considered and rejected:**
- Changing `TokenNGram` to give unseen tokens mass — rejected: library code is read-only; the escape lives in a wrapper that reuses `TokenNGram._distribution` so seen-token probabilities are the library's own.
- Charging the n-gram model parameters (two-part code) — rejected: held-out cross-entropy is the specified learned coder; the two-part variant is mentioned in the caveats only.
- Reporting only the integer-id / code-point renderings for the compressors — rejected as the sole basis: those renderings need a token dictionary that the spec does not charge, which favours large atomic alphabets (w° with labels, fact tuples, rows). A literal-text rendering (no dictionary) is added and the verdict is evaluated on the self-contained number (see pre-registration).

**Plan as executed:**
1. Read the spec'd modules; write the pre-registration (this section) and commit it before any bits are computed.
2. Write `serialize.py`, `coders.py`, tests; check losslessness/invariance.
3. Pilot (`ndc_classes` full, 500-member seeded `wd50k66` subsample); message `main` with the table.
4. Full run on four collections; analysis; figure; log; commit.

**Deviations from the plan** (every one is also in section 7):
1. *Bootstrap of the compressor sizes.* The pre-registration said "resample members with replacement, recompress, percentile CI". The pilot showed that this is biased: a resample repeats about 37 % of its lines, a compressor codes an exact repeat of an earlier line almost for free, and the resampled size per KB came out 18-29 % below the full-collection size (pilot, `wd50k66` 500 members, ratio of replicate mean to point estimate: xz 0.72-0.83, zstd 0.71-0.82, bzip2 0.81-0.88 depending on the arm), by different amounts for different arms, which distorts ratios between arms. The final runs recompress the *distinct* members drawn (about 63 % of the collection, in collection order), charge each replicate its own dictionary, and report the 95 % replicate interval translated to the full-collection point (`ci_low + (point - replicate mean)`). The raw replicate quantiles and the replicate mean are kept in `compressors_*.csv` (`ci_low`, `ci_high`, `boot_mean`). The bootstrap resample indices are shared across arms, so the ratio intervals are paired. 200 replicates, seed 20261013. The pilot directory (`pilot/`) still holds the biased version and is superseded.
2. *No `incid_flat` arm.* The pre-registration listed `fact_flat`/`incid_flat`. In flat form the canonical fact list and the canonical incidence list are the same field stream, so there is one arm, `fact_flat`; it is the flat competitor in HB2.
3. *Strata.* Stratified tests use the two coders `fixed_obs` and `ngram3` only (the other coders are in the medians table); everything else as pre-registered.

### 2.1 PRE-REGISTRATION (written 2026-10-13T14:55+0200, before any code-length, bits, compression or delta number existed; do not edit below this line after results)

**What I had seen before writing this**: collection sizes; per-collection quantiles of `n`, `m`, `max_arity`; vocabulary sizes (`wd50k66`: 1 type / 351 predicates; `wd50k100`: 1 / 204; `ndc_classes`: 4 / 1; `ndc_substances`: 1 / 1; `k_max = 10` everywhere); that 50 `ordered_symbols` calls run in milliseconds; and, for the first `ndc_classes` member only (n=11, m=3), the raw lengths `L(w°)=4` (incl. the seed symbol), `L(cert bytes)=156`, `L(rows)=14`, `L(fact)=14`, `L(incidence)=32`, and the T-KBx note (13.8 walk tokens vs 159.7 bytes vs 40.1 four-byte integers on a 400-member `wd50k66` sample). I had seen no bits, no n-gram score, no compressor size and no delta.

**Arms (symbol sequences).** Required by the spec / amendment (1):
`w_o` (= `ordered_symbols(H)` with policy `struct`, atomic token = one symbol, seed symbol when `|Σ_V| > 1`), `cert_bytes` (= `nauty_certificate_bytes`, colour signature + pynauty certificate, one symbol per byte), `cert_rows` (= `nauty_certificate_rows`, one symbol per Levi node, colour inside the row), `cert_ints` (the integer granularity: the same rows flattened to `colour, nbr_1 < ... < nbr_d, SEP` per Levi node, one symbol per integer), `fact` (= `fact_word(H)`, atomic tokens), `incid` (= `flatten(H)` made isomorphism-invariant, see below).
Supplementary "best honest rendering" arms, all reported, all in the verdict:
- `cert_ints_ut`: as `cert_ints` but each row lists only neighbours with larger canonical position (adjacency is symmetric, so this is lossless and halves the integers);
- `cert_u32`: the `cert_bytes` string read as 4-byte big-endian words (the "40 integers" granularity of T-KBx);
- `fact_noT`, `incid_noT`: on collections with `|Σ_V| = 1` only, the type tokens and the constant count are dropped (lossless: the corpora are connected with `m >= 3`, every constant is in a fact, so `n = 1 + max rank`; the decoder of the fact alphabet already computes `n = max(#T, 1 + max rank)`);
- `w_flat`, `fact_flat`, `incid_flat`: the same three representations written field by field (slot-tagged integer streams), so that "ints vs ints" can be read at equal granularity.
`incid`: `flatten(H)` is not isomorphism-invariant (it uses the record's constant ids and fact order). A code of the isomorphism class may choose its labelling, so I serialize `flatten` of the hypergraph relabelled by `canonical_ranks` with facts sorted by `(predicate, operand tuple)` (the same canonical addressing as `fact`); this is the incidence list's best honest rendering and it makes the arm a function of the class. Lossless by construction (it is the full labelled hypergraph under a canonical labelling).
Losslessness: `w_o` — Theorem C (completeness of `(root type, w°)`), also decoded round-trip on a sample in the tests; `cert_*` — `color_signature` + canonical certificate (`T-TAe`), rows carry the colour; `fact` — completeness of the fact word under the injective canonical addressing; `incid` — contains the whole labelled hypergraph.

**Alphabets (fixed-width code reports BOTH, amendment (2)).**
(a) observed: distinct symbols of that arm over the whole collection; `bits_fixed_obs = (L+1)·log2(|A_obs|+1)`.
(b) theoretical, with `k = k_max = 10`, `nV = |Σ_V|`, `nE = |Σ_E|`, `n_max, N_max = max(n+m)` over the collection:
`|Σ(w_o)| = 1 + 2k + k·nE + nE·Σ_{j=1}^{k-1}(k−j)·nV^j  (+ nV seed symbols if nV > 1)` (the grammar of `core/instructions.py`: `V` ranges over `1 ≤ i,j ≤ k−1`, `2 ≤ i+j ≤ k`, so `k−j` values of `i` per `j`, `nV^j` label tuples, `nE` predicates; `C_i` has `k·nE` forms; `P_i`, `N_i` have `k` each; `W` one);
`|A(cert_bytes)| = 256`; `|A(cert_u32)| = 2^32`; `|A(cert_rows)| = (nV+nE)·2^{N_max}` (colour × an `N_max`-bit adjacency row); `|A(cert_ints)| = |A(cert_ints_ut)| = max(nV+nE, N_max) + 1`; `|A(fact)| = nV + nE·Σ_{a=2}^{k} C(n_max, a)`; `|A(incid)| = n_max + nV + 1 + nE + n_max + 1`; flat arms and `noT` arms: slot-wise, defined in `serialize.py::theoretical_alphabet`. Flat arms are charged slot-wise: each symbol costs `log2(|A_slot|+1)`.
The learned coders and the compressors are the primary coders; both fixed-width variants are reported and both are in the verdict.

**Learned coder.** `TokenNGram(order=o, smoothing="kneser_ney", discount=0.75)`, `o ∈ {1,2,3}`, `o = 3` primary. 5-fold CV over members, fold assignment by a seeded permutation (`numpy.random.default_rng(seed)`, `array_split`), seed 0 primary; seeds 0..4 repeated to give the CV spread of the median. `bits(w) = −Σ log2 p(token | context) − log2 p(EOS | context)`. Escape scheme (one for every arm): for fold training stream with `N` coded events (tokens + one EOS per word) of which `n1` seen-type-once types, `ε = (n1 + 1)/(N + 1)` (Good–Turing missing mass with add-one safety). A held-out token in the training vocabulary `V_tr` costs `−log2((1−ε)·q(t|h))` with `q` the library's own `TokenNGram._distribution`; an unseen token costs `−log2 ε + log2 U`, `U = max(|A_obs| − |V_tr|, 1)` (uniform over the alphabet tokens not seen in training; `|A_obs|` is the same whole-collection alphabet the fixed-width coder is told). A second column prices the unseen tokens with the theoretical alphabet (`U_theo = max(|A_theo| − |V_tr|, 1)`). Unseen tokens in the context window are treated by the library (unseen context ⇒ back off). The model parameters are not charged (held-out cross-entropy).

**Generic compressors.** Per arm and collection, one KB per line, three renderings: `ids` (space-separated integer ids, ids assigned by descending frequency), `cp` (one Unicode code point per token, frequency-ranked, surrogates skipped, UTF-8), `lit` (literal text of the serialization — `serialize(tokens)` for `w_o`, raw bytes for `cert_bytes`/`cert_u32`, `repr` of rows/tuples joined by single separators — no dictionary needed). `xz -9e`, `zstd -19 --ultra` (`/home/linuxbrew/.linuxbrew/bin/zstd`), `bzip2 -9` (`/opt/miniconda/bin/bzip2`). Two numbers per (arm, compressor): the SPEC number = better of `ids`/`cp`, dictionary not charged (the spec's definition), and the SELF-CONTAINED number = best of `ids + dict`, `cp + dict`, `lit`, where `dict` is the compressed literal alphabet table (one literal token per line in id order). Verdicts on compressors use the SELF-CONTAINED number (it cannot be gamed by an uncharged dictionary); the SPEC number is reported alongside. Bootstrap: ≥ 200 member resamples (same resample indices for all arms, so differences are paired), recompress, percentile CI of bytes/KB and of the ratio to `w_o`; the rendering is chosen on the point estimate and fixed during the bootstrap.

**Verdict rule (fixed now).** A comparison `w_o` vs arm X in collection c under per-member coder C is a *win* iff the one-sided paired Wilcoxon `H1: bits(X) − bits(w_o) > 0` has Holm-adjusted `p < 0.05` and the median paired difference is positive. For compressors a win is: bytes/KB of `w_o` smaller than X's on the point estimate and the 95 % bootstrap CI of the paired ratio `bytes(w_o)/bytes(X)` entirely below 1.
- Confirmatory family = the two primary collections (`wd50k66`, `ndc_classes`) × {per-member coders: `fixed_obs`, `fixed_theo`, `ngram1`, `ngram2`, `ngram3`} × competitor arms; Holm is applied across all of them within HB1 (competitors = certificate granularities `cert_bytes`, `cert_u32`, `cert_rows`, `cert_ints`, `cert_ints_ut`) and, separately, within HB2 (competitors = `fact`, `incid`, and `fact_noT`/`incid_noT`/`fact_flat`/`incid_flat` where defined). Controls (`wd50k100`, `ndc_substances`) are a separate replication family with their own Holm. Compressor wins are evaluated for xz, zstd, bzip2 in the same collections.
- **HB1 headline** is claimed ONLY IF `w_o` wins against every one of the five certificate granularities under every coder (`fixed_obs`, `fixed_theo`, `ngram1..3`, `xz`, `zstd`, `bzip2` — self-contained numbers) in both primary collections. I also report the weaker `required-set` flag (bytes, rows, ints only; amendment (1)); the headline needs the full set. If the verdict flips with the tokenization or the coder, I report the whole matrix and claim nothing. HB2 is judged the same way against its competitor set. `w_flat` vs the flat competitors is the equal-granularity robustness table; it enters the verdict as an additional `w_o` rendering (the headline must also hold for `w_flat` vs the integer-granularity certificate arms), because a result that exists only for one tokenization of our own word would not be a result.
- Strata (exploratory, not confirmatory): star vs relational (star: some constant lies in every fact and every other constant lies in exactly one fact; `m = 1` would be star), and fact-count bins `m ∈ {3}, {4–5}, {6–8}, {9–12}, {13+}`; stratum tests use the same machinery, Holm within the stratum family, and are reported only for strata with ≥ 20 members.

**HB3 (versions).** Consecutive pairs `(a, b)` of `ndc_classes` (528) and `ndc_substances` (885), `constant_preserving` stratification from the record. Per pair and arm: (i) `zstd -19 --patch-from=<code-point file of a> <code-point file of b>` output bytes (one KB per file, code points as in `cp`); (ii) Levenshtein distance on the code-point strings (rapidfuzz). Both are reported against the calibration constant "delta of a file against itself" (the frame overhead). Test: paired one-sided Wilcoxon over pairs, `H1: delta(cert_g) − delta(w_o) > 0`, per stratum × granularity × measure, Holm over that family. Pre-registered expectation: certificate wins (smaller delta) on the constant-preserving stratum; unknown on the constant-changing one.

**Reported lengths (amendment (3)).** Median AND mean raw token length `L` per arm, per collection, per stratum (star/relational, fact-count bin), so the "6/8 instructions vs 12 rows" and "13.8 tokens vs 40 integers" statements can be reconciled.

**Not used**: no timing of any arm (known defect T-KBy in the rows arm).

**Amendment from `main` received 2026-10-13 (before any result), incorporated above**: (1) three certificate granularities (bytes, rows, integers) and the rule "claim only if `w_o` wins everywhere"; (2) observed and theoretical alphabets both reported; (3) median and mean `L`. Verbatim text is in section 8.

(End of pre-registration.)

## 3. Changes made

**Created**
| Path | Purpose |
|---|---|
| `scripts/newpos/compression/__init__.py` | package marker |
| `scripts/newpos/compression/serialize.py` | the 12 arms (symbol sequences), strata, observed and theoretical alphabets, fixed-width coder, literal text |
| `scripts/newpos/compression/coders.py` | CV folds, held-out n-gram coder with the single escape scheme |
| `scripts/newpos/compression/compressors.py` | renderings (`ids`, `cp`, `lit`), `xz`/`zstd`/`bzip2` sizes, distinct-member bootstrap, `zstd --patch-from` deltas |
| `scripts/newpos/compression/decode.py` | decoders of every arm back to a hypergraph (losslessness evidence) |
| `scripts/newpos/compression/measure.py` | per-collection driver: per-KB bits, compressor sizes + bootstrap, deltas |
| `scripts/newpos/compression/analyze.py` | tables, paired tests, Holm families, verdict flags and matrices, `tables.md`, `stats.json` |
| `scripts/newpos/compression/fig_bits.py` | the figure (bits vs fact-count bin per collection; compressor bytes per KB) |
| `scripts/newpos/compression/run_all.py` | runs the four collections, then analysis and figure |
| `tests/newpos/test_compression.py` | 33 unit tests |
| `.claude/notes/2026-10-13-newpos-w1/compression.md` | this log |

Results (outside the repo), `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/NEWPOS_2026-10-13/compression/`: `perkb_<c>.csv` (per KB: collection, kb_id, structure, fact_bin, n, m, representation, L, bits_fixed_obs, bits_fixed_theo, bits_ngram{1,2,3}, bits_ngram{1,2,3}_theo, unseen_ngram{1,2,3}), `ngram_seeds_<c>.csv` (CV spread, 5 seeds x 3 orders x 12 arms), `compressors_point_<c>.csv` (every rendering x compressor), `compressors_<c>.csv` (chosen renderings, CIs), `compressors_boot_<c>.npz` (replicates), `deltas_<c>.csv`, `alphabets_<c>.json`, `members_<c>.json`, `tables.md`, `stats.json`, `tests_per_kb.csv`, `fig_bits.pdf`, `log_<c>.txt`, `run_all*.log`; `pilot/` holds the superseded pilot.

**Modified**: none outside the owned paths.

**Removed**: none.

**Commits**
| SHA | Message |
|---|---|
| `9f9ef2d` | `docs(notes): compression pre-registration` |
| `95cc9ef` | `feat(newpos): description-length experiment (serializers, coders, compressors, analysis)` |
| `2b3270d` | `fix(newpos): distinct-member bootstrap for compressor CIs, verdict matrices, lint` |
| `e75e406` | `fix(newpos): translate compressor bootstrap interval to the point estimate` |
| (next) | `docs(notes): compression work log` |

## 4. Tests

**Tests created or extended** (all `pytest.mark.unit`, file `tests/newpos/test_compression.py`)
| Test | What it verifies | Why it matters |
|---|---|---|
| `test_every_arm_is_deterministic_and_isomorphism_invariant` (4 vocabularies) | every arm is identical on a relabelled, fact-reordered copy and on a repeat call | an arm that depends on ids or insertion order is not a code of the class |
| `test_arms_equal_the_symbols_the_registered_distances_compare` | `w_o`, `cert_bytes`, `cert_rows`, `fact` equal the `fingerprint` of `isal_ow_struct`, `nauty_cert`, `nauty_cert_rows`, `fact_rank` | the five spec'd arms are the compared sequences, not re-implementations |
| `test_every_arm_decodes_to_an_isomorphic_knowledge_base` (3 vocabularies) | all arms decode (`decode.py`) to a KB isomorphic to the input | losslessness of every arm, including the supplementary renderings |
| `test_certificate_bytes_have_a_whole_number_of_words` | length divisible by 4 | `cert_u32` is well defined |
| `test_fixed_width_single_slot_formula`, `..._slot_wise_...` | `(L+1) log2(|A|+1)` and the slot-wise rule | the fixed-width coder is the spec'd formula |
| `test_walk_alphabet_size_matches_brute_force_enumeration` | `|Sigma_HG(k)|` from the closed form equals an enumeration validated by `core.instructions.validate` | the theoretical alphabet follows the grammar |
| `test_ngram_code_length_is_minus_log2_of_the_model_probability` | `core_bits == -log2 p` of `TokenNGram.logprob`; escape reserve `(1-eps)` accounted | the learned coder reuses the library probabilities |
| `test_escape_scheme_is_finite_on_an_unseen_token_and_prices_by_alphabet` | finite bits on an unseen token; escape cost `-log2 eps + log2 U`, larger for the larger declared alphabet | the one escape scheme is well defined |
| `test_kfold_assignment_*`, `test_cross_validation_*` | folds partition the members, are seeded; each member is scored by a model that never saw it | no train/test leakage |
| `test_star_classification`, `test_fact_bins` | star definition on sunflower, single fact, path, double overlap; bin edges | strata are the specified ones |
| `test_codepoint_table_*`, `test_frequency_ids_*`, `test_compressor_sizes_and_self_patch`, `test_choose_renderings_charges_the_dictionary` | renderings, compressors, `zstd --patch-from`, spec vs self-contained choice | the compressor numbers measure what they claim |

**Coverage of the behaviour that matters:** serialization invariance and decodability, the coder formulas, the escape, the strata. **Not tested, and why:** the bootstrap, the Wilcoxon/Holm wiring and the Markdown rendering are exercised by the full run (outputs inspected) but have no unit test; the pandas/matplotlib code is script-level; `measure.py` multiprocessing is not unit-tested.

## 5. Test results

**Command:** `~/.conda/envs/isalhg/bin/python -m pytest tests/newpos/test_compression.py -q` and `~/.conda/envs/isalhg/bin/python -m ruff check scripts/newpos/compression tests/newpos/test_compression.py`

```
33 passed in 0.17s
All checks passed!
```

**Result:** 33 passed, 0 failed, 0 skipped · **Duration:** 0.17 s · **Run at:** `e75e406`

**Failures and their resolution:** none in the final suite. Earlier the first test run failed at import (a wrong class name `NautyLevi_EditAlias` I had typed); fixed to the right import.

## 6. Verification beyond unit tests

| Circumstance | What was run | Evidence | Outcome |
|---|---|---|---|
| Real data, losslessness | `decode_arm` of every arm of 300 seeded members per collection (4 collections), isomorphism by `PynautyLeviBackend` | 13,800 arm decodes (3,600 / 3,000 / 3,600 / 3,600) | 0 failures; `ndc_classes` has 10 arms (no type-elided arms, 4 types) |
| Real data, certificate decode | `bytes_to_rows` inverts `nauty_certificate_bytes` (little-endian 64-bit words, MSB-first bits, colour cells in increasing colour order) | rows equal `nauty_certificate_rows` adjacency on the first member, then every decode above | confirmed |
| Full run | `run_all.py` on `wd50k66` (3,988), `ndc_classes` (1,381), `ndc_substances` (1,745), `wd50k100` (1,837), 4 workers | measure 157 / 63 / 102 / 109 s per collection; analysis about 3 min; 5 CV seeds x 3 orders x 12 arms; 200 bootstrap replicates; 29 MB of results | complete |
| Reconciliation of the notes | median/mean `L` per arm | `wd50k66`: `w_o` 6 / 13.5, rows 12 / 15.1, 4-byte integers 35 / 40.0, bytes 140 / 159.9; `ndc_classes`: `w_o` 9 (8 without the root-type symbol) / 15.1, rows 12 / 13.1, 4-byte integers 35 / 36.3 | "6/8 vs 12 rows" is a median comparison against rows; "13.8 vs 40" is a mean comparison against 4-byte integers; both reproduce |
| Pilot vs full | ngram3 medians, 500-member pilot vs 3,988 | `w_o` 31.7 -> 29.1, `cert_rows` 78.6 -> 72.1, `fact` 49.6 -> 48.2 | the pilot was close; the order of the arms did not change |
| Bootstrap bias | pilot replicate mean / point estimate of the compressed size | 0.71-0.88 (with-replacement) | replaced by the distinct-member bootstrap, see section 2 |
| Degenerate intervals | `bca_ci` falls back to percentile when BCa is undefined | 167 medians of discrete data (token lengths, bits) reported with the percentile interval (`method` recorded in `stats.json`) | disclosed |
| Order of events | pre-registration committed (`9f9ef2d`) -> serializers/coders written -> 200-member smoke run of `ndc_classes` (plumbing only; I read its medians) -> 150-member decode check -> pilot -> message to `main` -> full run | the pre-registered hypotheses, arms, coders, verdict rule were not edited after any number was seen | |
| Environment | Python 3.11.15, numpy 2.4.6, pandas 3.0.3, scipy 1.17.1, rapidfuzz 3.14.5, `xz`/`zstd 1.5.7`/`bzip2` binaries | | |

## 7. Decisions, assumptions, open questions

**Decisions with a real trade-off**
- *Self-contained compressor number as the verdict basis.* The spec number (best of `ids`/`cp`, dictionary uncharged) gives large-alphabet arms (`w_o` with labels, `fact`, rows) a free dictionary; the self-contained number charges it (or uses the dictionary-free literal text). Both are reported; the verdict uses the self-contained one. Cost: it is the less favourable basis for `w_o` on some arms; buys: it cannot be gamed by an uncharged table.
- *Distinct-member bootstrap* instead of with-replacement (section 2). Cost: the replicate interval refers to about 63 % of the collection and is translated to the point estimate (an approximation; a larger collection would compress slightly better per KB); buys: removes an 18-29 % downward bias that differs across arms.
- *Observed alphabet is the primary escape/fixed-width basis*, theoretical reported alongside (`ngram*_theo`, `fixed_theo`), as `main` asked.
- *`incid` is `flatten` of the canonical relabelling* (sorted facts), because `flatten(H)` itself uses the record's ids and fact order and is not a code of the class.
- *Certificate integers in three forms* (`cert_ints` plain with separators = the required integer granularity; `cert_ints_ut` upper-triangle, slot-tagged = the best honest integer rendering; `cert_u32` = the T-KBx 4-byte words), all in the verdict, as `main` ruled.

**Assumptions I proceeded on**
- `k = k_max = 10` for the theoretical walk alphabet, and the collection envelope (largest `n`, largest `n + m`) for the size-dependent alphabets (`cert_rows`: `(|Sigma_V|+|Sigma_E|) x 2^{N_max}`). If a different envelope is wanted, `fixed_theo` changes; the learned and compressor verdicts do not.
- The held-out cross-entropy excludes the n-gram's parameters (as specified). A two-part code would charge the model, which favours small alphabets (cert bytes); not measured.
- The `ndc_classes` median `L(w_o) = 9` counts the root-type `("seed", t)` symbol, because `ordered_symbols` prepends it on a non-trivial vocabulary (as the spec requires); without it the median is 8.

**Open questions for the orchestrator**
- Whether the strict rule should include `fixed_theo` against `cert_ints_ut` at all: it is the only reason the pre-registered headline fails against the certificate on `ndc_classes` (w_o 188.3 vs 125.1 bits; 4 types make `|Sigma_HG(10)| = 466,055`, 18.8 bits per walk token). Nothing was changed; the verdict stands as pre-registered.
- A permission block: my `pkill` of the first full run (started with the biased bootstrap) was denied, so I let it finish and re-ran everything with the fixed code; nothing else was affected.

## 8. Coordination

**Messages received (verbatim) :**
> From main — amendment to your pre-registration, to be written into your log BEFORE you look at any result (if you already have pilot numbers, say so in the log and say which you saw): (1) Tokenization dependence (project lesson L9, docs/article/D_ART3/foundation/lessons.md — read it): any certificate comparison depends on symbol granularity. Report the certificate under THREE granularities — bytes (`nauty_cert`), rows (`nauty_cert_rows`, one symbol per Levi node), and integers (the certificate as a sequence of canonical-adjacency integers / neighbour indices, if the code exposes one; otherwise derive it from the canonical labelling and document how). The headline claim is made ONLY if w° wins under every granularity and every coder; if the verdict flips with the tokenization, report all and claim none. Do not use any timing from the rows arm (known defect T-KBy); timings are out of scope anyway. (2) Fixed-width alphabet: state both alphabets in the pre-registration and report both — (a) the observed token alphabet over the collection, and (b) the theoretical alphabet: for w°, |Σ_HG(k)| including labels (all V_{i,j}/C_i/P_i/N_i/W tokens with every admissible label combination for the collection's k, |Σ_V|, |Σ_E|) — compute the count from the token grammar in src/isalhg/core/instructions.py; for the certificate, the full symbol range of its granularity (256 for bytes; the number of possible rows/integers for N Levi nodes). The learned (n-gram) code and the generic compressors are less sensitive to this choice and remain the primary coders. (3) Context: two existing measurements disagree — docs/article/D_ART3/prose.md §2.2 says medians of 6 (WD50K) / 8 (NDC) instructions vs 12 certificate rows; ledger item T-KBx measured a mean of 13.8 walk tokens vs 40 certificate integers on a 400-member WD50K sample. Report median AND mean raw token length per granularity, per collection and stratum, so both statements can be reconciled.

**Messages sent:** (1) to `main`, after the pilot: the pilot table (medians per arm and coder, compressor bytes/KB, length reconciliation, HB3 reading, verdict flags and the two honest negatives); outcome: `main` replied to proceed with the four full collections and stated the verdict rule (every reported granularity counts, including `cert_ints_ut` and `cert_u32`; report per coder, per granularity, per collection; keep the raw HB3 numbers beside the net-of-overhead ones).

**Messages received and how they changed the work:** (a) the amendment above: added the integer certificate granularity (`cert_ints`, `cert_ints_ut`, `cert_u32`), the theoretical alphabets and `fixed_theo`, the median/mean length tables, and the all-granularities verdict rule, all before any result; (b) the reply after the pilot (proceed; every granularity counts; report per coder/granularity/collection; keep raw and net HB3): the verdict matrices in `tables.md` and the raw + net patch columns follow it.

**Contracts I depend on and confirmed unchanged:** `experiments.tkde.corpora` loader and `experiments.tkde.stats` helpers (read-only use); `TokenNGram` private `_distribution`/`_context_of`/`_index` used by the escape wrapper (a library change to those would break `coders.py`).

## 9. Deliberately not done

- Neural-coder fold-in (`neural-gen`'s held-out NLL as a fourth coder) — `main` said it may ask later; the per-KB CSV has the same `kb_id` order as the frozen collection, so a column can be joined.
- Timing of any arm (rows arm has the known defect T-KBy; out of scope).
- A two-part (model-charged) code and an entropy-coded refinement of the fixed-width code.
- `incid_flat` (merged into `fact_flat`, see section 2); a theoretical-alphabet escape for the compressors (not applicable).
- Editing `docs/`, the paper, or any library code (the escape wrapper reads `TokenNGram._distribution`, `_index` and `_context_of`; a change to those private names would break `coders.py`).

## 10. Risks and follow-ups

| Item | Severity | Detail | Suggested owner |
|---|---|---|---|
| `fixed_theo` convention | medium | the strict headline fails only because of it on `ndc_classes` (cert_ints_ut) and `wd50k100` (cert_ints_ut, median diff +11.6 bits but P(w fewer) = 0.525, not significant); the size-dependent theoretical alphabets use the collection envelope | `main`, decide how the paper states the fixed-width coder |
| Large KBs | medium | for `m >= 9` on the WD50K collections the walk has more tokens than the certificate rows or fact list (`wd50k66`, `m >= 13`: `L(w_o)` median 51 vs 35), and under `fixed_obs` w_o does not win there (494.5 vs 477.2 rows, 469.8 fact); under `ngram3` and the compressors it still wins | writing |
| Fact list | medium | HB2 is not won against the fact list: on `ndc_classes` the margin under `ngram3` is 20.6 vs 20.2 median bits, w_o does not win against `fact_noT` under `fixed_obs` on the three trivial-type collections, and edit distance of versions is smaller for the fact list | writing |
| Edit distance across granularities | medium | token edit distance has a different unit for bytes, rows, integers and walk tokens; the zstd patch bytes (unit-free) and the net-of-overhead column are the comparable HB3 measures | writing |
| n-gram order 3 on atomic tokens | low | large atomic alphabets (`fact`, rows) pay for unseen tokens (unseen-event fraction up to 0.22 for `fact_noT`); the flat arms and the orders 1-2 rows show the effect | |
| Pilot directory | low | `pilot/` holds the superseded biased bootstrap | |

## 11. Self-assessment against the definition of done

| # | Criterion | Met | Evidence |
|---|---|---|---|
| 1 | scripts produce per-KB rows CSV, collection-level compressor CSV with bootstrap CIs, deltas CSV, `tables.md`, `stats.json` | yes | `perkb_*.csv`, `compressors_*.csv`, `deltas_*.csv`, `tables.md`, `stats.json` in the results dir (collections: `wd50k66`, `ndc_classes`, `wd50k100`, `ndc_substances`) |
| 2 | figure (PDF): median bits per KB vs fact-count bin per collection (learned code) plus compressor bytes/KB panel | yes | `fig_bits.pdf`, viewed |
| 3 | pilot first, message `main` before the full run | yes | message sent after the pilot; `main` replied to proceed |
| 4 | tests pass, everything committed, tree clean, log committed | yes | 33 passed; ruff clean; commits listed in section 3 |

**Overall:** the numbers are complete and every claim in the summary below traces to a CSV/JSON in the results directory. Result in one paragraph (details in `tables.md`): against every certificate granularity (bytes, 4-byte words, rows, plain integers, upper-triangle integers) `w_o` needs fewer bits under the held-out 3-gram code in all four collections (median bits per KB, `wd50k66` / `ndc_classes` / `wd50k100` / `ndc_substances`: `w_o` 29.1 / 20.6 / 30.0 / 22.8 against rows 72.1 / 25.3 / 94.3 / 71.6, plain integers 117.4 / 103.7 / 155.2 / 112.9, upper-triangle integers 57.1 / 51.0 / 69.2 / 54.1, bytes 206.1 / 195.0 / 234.7 / 179.2) and under xz, zstd and bzip2 (xz bytes per KB `w_o` 6.5 / 3.3 / 6.9 / 6.5 against 10.5 / 5.2 / 11.3 / 10.7 for the best certificate form). The strict pre-registered headline (every granularity, every coder, both primary collections) is NOT met: against `cert_ints_ut` on `ndc_classes` the theoretical-alphabet fixed-width code favours the certificate (188.3 vs 125.1 bits), and the equal-granularity check `w_flat` vs `cert_ints_ut` fails under the order-1 n-gram on `ndc_classes` (120.9 vs 116.1). Against the canonical-rank fact list and the incidence list `w_o` wins on the learned codes and compressors in the primary collections but not convincingly (HB2 not met). HB3: `w_o` deltas are smaller than every certificate form on zstd patch bytes in both strata and both collections (one non-significant cell: `cert_rows`, constant-preserving, `ndc_substances`), but on constant-preserving pairs of `ndc_classes` the certificate has the smaller token edit distance, as predicted; the fact list has smaller deltas than `w_o`. Scrutinise first: the `fixed_theo` convention, the distinct-member bootstrap, and the large-KB strata.
