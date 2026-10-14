# Brief for the Isal-refinement agent — nauty inside the Isal methodology for knowledge bases

*Written 2026-09-06 by the campaign auditor for the agent that will design and
measure an improved Isal representation of knowledge bases. Everything here is
either a decision, a measured number with its file, or a quotation. Read it
end to end before touching code. The decision record is D-ART4 in
`../../DEVELOPMENT/DECISIONS.md`; this brief is its working annex.*

---

## 0. Mandate, in the principals' own words

**The PI (2026-09-06, relayed by the first author):** *"We need to use the
instruction string of the Isal family in the paper."* He asked three
questions — why the canonical fact-rank was needed for the Isal representation
to be correct (it is not; see `PI_QA_2026-09-06_isal_string.md` §1); whether
locality under edits is the only thing keeping the Isal representation from
being "perfect" (it is not; symmetric-input cost is the second limit, §2 there);
and whether raising the time-out to 60 s with the C++ engine would help (that
was already the campaign setting, §3 there).

**The first author (2026-09-06), the scope of your work:**

> "We can integrate nauty inside the Isal methodology without a problem, even
> more, it'd be something interesting, since nauty could help us in (2a, 2b)
> to obtain a better Isal methodology, and, in the paper's comparison, when
> comparing to the nauty certificate, we are comparing something like
> 'nauty+Isal' vs 'nauty', which is really defensible and perfectly scoped,
> but always under the knowledge databases preface and measuring things that
> have an impact, always making sure that the Isal methodology is oriented
> towards the knowledge databases."

**Earlier author decisions that bind you** (D-ART4): (1) the fact-rank word
and its addressing arms leave the paper — do not propose them back; compare
only against standard representations and against competitors that attempt
the same task; (2) the restrictions R1–R6 below are the starting list to
iterate on; (3) the research questions are re-aimed, not restarted.

**The reference framing you are producing evidence for.** The Isal
representation of a knowledge base is an *instruction string for the Isal
machine* (CDLL + `k` pointers + `Σ_HG = {V, C, P, N, W}`), decoded by `S2H`,
which never rejects and always yields a connected hypergraph. Its canonical
form may use nauty. The comparison in the paper is *a language* (nauty-assisted
Isal) against *a certificate* (nauty's canonical form as a string), on
knowledge-base tasks with a real-world reading. Scope is this article only:
do not develop framings beyond it.

---

## 1. Reading list, in order, with what to take from each

| # | file | take from it |
|---|---|---|
| 1 | `ENCODINGS_WORKED_EXAMPLE.md` | what a knowledge base is in the data; the three encodings of one real record; one edit under each; §5 (why an address is needed; the three ways to get one) |
| 2 | `PI_QA_2026-09-06_isal_string.md` | the restriction inventory with numbers; the symmetry table; what a bigger budget buys; the four options (a)–(d) |
| 3 | `../../DEVELOPMENT/DECISIONS.md` → **D-ART4** | the binding decisions; the assessment of (2a) and (2b); the re-aimed RQ set |
| 4 | `RESULTS_AUDIT_2026-09-06.md` | what the campaign measured and how well it is reported; §1.2 (fragilities: tokenisation confound, normalised vs raw); §3.3 (the RQ3 deletion mechanism, which is the objective's and is representation-independent) |
| 5 | `DESIGN.md` | the pre-registered design: G1–G8 (statistics harness, corpora, competitor contract, A → A′ rule); §2 RQ1 (the measurement you will re-run: M0 exactness, M1 single-edit response, M2 monotonicity, M3 cost, M4 relation to the certificate) |
| 6 | `RESULTS_WALKTHROUGH.md` | the measured numbers per RQ under the retired encoding; the pointer-arm numbers are the Isal baseline you must beat |
| 7 | `../START_HERE.md` §2 "headlines", §6.0 | the proved facts, the retracted claims, the PI's earlier rulings (the 2026-09-04 F4 reading is superseded by D-ART4) |
| 8 | `../foundation/proved_facts.md`, `../foundation/lessons.md` | what is proved vs conditional vs refuted; the 25 design rules (L1 floors mandatory, L9 units, L11 raw distance, L12 no baseline removed for winning, L14 seed-level stats, L15 censoring) |
| 9 | `../foundation/probes_2026-09.md` §9 | the first addressing probe: mechanisms (content hash vs positional address; zero-cost-edit mass) — the reasoning survives even though its encoding does not |
| 10 | `../../H2S_S2H.md` | the Isal algorithms: `S2H` semantics, `H2S`, the tie-breaking cascade (`V` over `C`), the seed cascade |
| 11 | `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/proofs/completeness/theorem_a_completeness.tex` (+ `.pdf`) | Theorem A (line ~562); **Lemma "Admissible pruning"** (`lem:pruning`, line ~650): refining the tie set by any iso-invariant key *preserves completeness* but *changes the canonical value*; **Remark `rem:coherence-recursive`** (line ~627): coherence must hold at every reachable tie, the stabiliser shrinks as the search descends |
| 12 | `docs/engineering/CPP_OPTIMIZATION_LOG.md` Rounds 9–11 | what the C++ engine already prunes (seed cascade, structural tuples, cost-class enumeration + bound) and the two open levers (stabiliser-orbit pruning; tie-branch entry count) |
| 13 | `docs/engineering/ALGORITHMS.md`, `docs/engineering/CODE_DESIGN.md` | code-as-built spec; where new code goes |
| 14 | `docs/article/COMPETITORS.md`, `../competitors.md` §0 | the concession paragraph (nauty is faster at identity) and the competitor contract |
| 15 | `.claude/rules/coding_rules.md`, `CLAUDE.md` §Critical invariants | invariants 1–9 (pointers are CDLL indices; `V` over `C`; `W` is meaningful; pointer count = `k`) |

---

## 2. Fixed facts you must not re-derive (files given)

**Corpora** (`results/IEEETKDE/corpora/<name>/{records.jsonl,vocab.json,census.json}`):
`wd50k66` 3,988 entity KBs (3 ≤ m ≤ 110, n ≤ 24, arity ≤ 10, one type, 351
predicates, roles S/O/Q in a side field, P31 class labels); `ndc_classes`
1,381 quarterly co-formulation KBs (4 class types, one predicate, exact Δ
between consecutive quarters, 528 consecutive pairs of which 76 % change the
constant set); `ndc_substances` 1,745 (control); `wd50k100` 1,837 (control);
`synthetic_rq1` 2,000 random labelled KBs. Both real collections are
star-shaped around a hub and **symmetric by nature** (interchangeable leaves).

**The Isal arm as measured** (`isalhg_levenshtein` = `w*_c`, C++ engine,
`algorithm="canonical"`, 60 s process budget; `RQ1_addressing/addressing/tables.md`,
`RQ7_envelope/envelope/tables.md`, `RQ2_wellposedness/wellposedness/tables.md`):

| quantity | value |
|---|---|
| exactness (M0) | 0 false merges / 0 false splits / 0 invariance violations on completed members; censored on 118 (NDC) and 238 (WD50K) members |
| single-edit response, normalised, constant set preserved (M1 means) | 0.661 / 0.494 / 0.793 (NDC / synthetic / WD50K) vs certificate bytes 0.083 / 0.089 / 0.124 |
| single-edit response, constant set changes | 0.599 / 0.555 / 0.481 vs certificate 0.238 / 0.215 / 0.249 |
| within ≤ 2 tokens of the original | 0.03–0.86 by edit kind |
| monotonicity ρ(budget, d), WD50K ladders / NDC natural series | 0.553 / 0.961 (certificate 0.677 / 0.876) |
| cost (M3) | medians 0.3–4.6 s; censored 29–69 % above 17 facts on WD50K |
| identity timing (RQ2 step 5) | 4.7 / 5.0 / 3.5 ms median with 12.3 / 9.7 / 5.7 % not completing |
| RQ7 sweep | time-outs 3,074 / 7,776 (39.5 %); clean up to m = 160 / 160 / 40 / 40 at k = 2 / 3 / 4 / 5 |
| RQ6 alignment interiors | 86 / 86 decode, **100 % connected** (the fact list: 68.6 %) |

**Censoring is symmetry, not size** (`scripts/diagnostics/pointer_timeout_symmetry_probe.py`,
WD50K, |Aut| of the coloured Levi graph via `pynauty.autgrp`):

| facts | members | censored, |Aut| < 10³ | censored, |Aut| ≥ 10³ | median s (completed) |
|---|---|---|---|---|
| ≤ 8 | 3,297 | 0.00 | 0.15 | 0.004 |
| 9–12 | 447 | 0.02 | 0.53 | 0.35 |
| 13–16 | 187 | 0.24 | 0.68 | 1.7 |
| 17–20 | 46 | 0.28 | 0.86 | 2.6 |
| > 20 | 11 | 0.25 | 1.00 | 28 |

By |Aut| alone: 0.00 (≤ 10¹), 0.09 (10²), 0.41–0.48 (10³–10⁶), 0.72 (10⁷),
1.00 (≥ 10⁸).

**Nauty's canonical order under edits** (from the retired fact-rank rows,
still valid evidence about the *order*): it survives 0.68–0.85 of
constant-preserving edits (`zero_shift` flag, RQ1 `rows_m1`); when it shifts,
every rank after the shift renumbers.

**Retracted — do not repeat** (`../START_HERE.md` §2): `d_I` as an HGED proxy;
Theorem B as a stability bound; greedy variants as invariants; bare `w*` on
labelled inputs (the fingerprint is `(seed label, w*_c)`); "k = 7 / 10
measured infeasible" (no timing record); the fact-rank addressing frontier
(now out of the paper, not retracted as a fact).

---

## 3. Theory constraints

1. **Theorem A** holds for the *unpruned* tie-complete lex-min `w*_c`
   (`D-TA2` froze that definition, PI 2026-07-09). Any change of the canonical
   *value* needs the PI to supersede D-TA2 explicitly — say so in your
   proposal.
2. **Lemma `lem:pruning` (admissible pruning).** Refining the tie set by an
   iso-invariant key computed from `(H, σ, e)` preserves every theorem
   (completeness included) but yields a *different* canonical string. Keys
   consulting raw ids are inadmissible. Consequence: using nauty's canonical
   labelling as the tie key is **admissible and complete** — it is exactly
   option (2a)(i), where the tie set collapses to a singleton and no
   branching remains. That is a new canonical form, not `w*_c`.
3. **Stabiliser-orbit pruning** — explore one branch per orbit of the
   automorphism group fixing the placed prefix — is the *value-preserving*
   speed-up (bit-identical `w*_c`). Unimplemented in IsalHG, IsalGraph and
   IsalSR (D-ART4 (2b)). With nauty as an oracle: individualise the placed
   constants in the Levi colouring, call `autgrp`, branch once per orbit.
   Correctness argument: `rem:coherence-recursive` — the stabiliser must be
   recomputed at every tie, not only at the root.
4. **Every complete invariant is discontinuous near symmetric inputs** (the
   avalanche; `../theoretical/stability_reformulations.md` §6; the frontier
   prose of `../prose.md`). Your target is *typical-case* locality, stated as
   the fraction of edits with response ≤ c tokens, never a Lipschitz claim.
5. **Labels.** Vertex colour = type, fact-node colour = `|Σ_V| + predicate`
   in the Levi graph (`core/levi_reduction.py`); the colour classes handed to
   nauty are an ordered partition, so every certificate consumer prepends
   `color_signature()` (T-TAe). The Isal fingerprint on labelled inputs is
   `(seed label, w*_c)`.
6. **Alphabet scoping.** One `k` (pointer count = max arity) per collection;
   distances are never compared across `k`.

---

## 4. The design space you are to explore (with the hypothesis each carries)

Every option below keeps the Isal machine, alphabet and `S2H`. What varies is
how the canonical program is chosen.

| option | definition | what nauty does | completeness | hypothesis to measure |
|---|---|---|---|---|
| **A. `w*_c` + orbit pruning** | unchanged lex-min over walks | automorphism oracle at tie points | Theorem A, value preserved | censoring by |Aut| collapses toward the asymmetric rows (0.00–0.28); locality unchanged (R1 stays) |
| **B. Canonical-order walk** | program emitted deterministically along nauty's constant order (constants enter via `V` in rank order, facts in a fixed order via `V`/`C`, pointers moved by `P`/`N`) | supplies the order | immediate (deterministic function of the ranked structure); `lem:pruning` reading: tie key = rank | locality ≈ order stability (0.68–0.85 zero-shift) with a few-token response; cost = one nauty call + linear emission; **relative addressing**: inserting a constant costs O(1) tokens (pointer moves are relative) where ranks/adjacency rows renumber everything after it — the potential locality *advantage* over every rank-based serialisation, on `add_constant` / `insert_fact_new_constant` edits |
| **C. Restricted lex-min** | lex-min over a tree-shaped walk family rooted at the refinement root with children ordered by nauty colour/orbit (gSpan DFS-code style) | supplies root and child order | by `lem:pruning` | the minimum moves less under edits than the unrestricted lex-min; cost between A and B |
| **D. Emission policies inside B** | same order, different fact emission orders (by predicate, hub-first, by arity, qualifier facts last) and role handling (roles as edge labels / per-incidence label) | none extra | as B | which policy minimises the single-edit response on *real* edits (the NDC natural Δ = 1 pairs; WD50K ladders) |

Non-negotiable acceptance for any variant: exact and relabelling-invariant on
all three corpora (M0: 0/0/0), decodable by `S2H` (every string), a stated
theorem sentence, and its cost/censoring reported by `|Aut|` bucket.

---

## 5. Restrictions to respect and to try to lift (R1–R6, D-ART4)

- **R1 locality** — the target of B/C/D.
- **R2 symmetric-input cost** — the target of A (and sidestepped by B).
- **R3 connected-only domain, no isolated constants** — `canonical_string`
  raises `DisconnectedHypergraphError`; RQ3's variant generator must reject
  deletions that strand a constant; RQ6's interiors are connected by
  construction (an advantage: say so).
- **R4 roles / argument direction** — facts are sets. Candidate lift: encode
  the role in the edge label (predicate × role pattern) or as per-incidence
  labels in the Levi colouring; whichever you propose must pass M0 (the
  fact-rank roles variant failed invariance with 2,104 violations because the
  roles were not in the canonical labelling's colouring — do not repeat that).
- **R5 alphabet scoping and the seed-label prefix** — keep.
- **R6 identity speed** — conceded in the introduction; never the axis.

---

## 6. Code map

| what | where |
|---|---|
| Isal canonical string (Python API, C++ default) | `src/isalhg/core/canonical.py::canonical_string(H, k=, algorithm="canonical", backend="cpp")`, `canonical_fingerprint` |
| C++ engine | `src/isalhg/core/_native/src/{canonical,h2s,s2h,structural_tuples,wl,cdll}.cpp`, bindings in `_native/bindings.cpp`; build notes in `docs/engineering/CPP_*.md` (build on the target node family; `-march=native`; SIGILL hazard) |
| decoder | `src/isalhg/core/string_to_hypergraph.py` (S2H); C++ `s2h.cpp` |
| Levi graph + colouring | `src/isalhg/core/levi_reduction.py::to_levi`, `LeviGraph.color_classes()`, `color_signature()` |
| nauty helpers already written | `src/isalhg/iso_backends/canonical_order.py::{canonical_ranks, nauty_certificate_bytes, nauty_certificate_rows, _to_pynauty}`; `pynauty.autgrp` used in `scripts/diagnostics/pointer_timeout_symmetry_probe.py` |
| the retired fact alphabet (reference for a total decoder and for the M0/M1 test pattern; not to be proposed back) | `src/isalhg/core/fact_word.py` |
| language layer (reach, alignments, coverage consensus, majority merge) — fact-level, needs only a canonical key + decoder | `src/isalhg/language/{reach,consensus,majority,alignment}.py` |
| TKDE harness: arms, matrices, budgets, stats | `experiments/tkde/{matrices.py (DEFAULT_SPECS: the arm list per collection), budget.py (run_with_budget: forked child + SIGKILL; symbol_distance: equality-keyed Levenshtein), stats.py, io.py, corpora.py}` |
| RQ1 runner and analyzer (the measurement to re-run) | `experiments/tkde/rq1.py`, `analyze_rq1.py`, config `experiments/tkde/configs/rq1.yaml` (`pointer_budget_s`) |
| RQ7 runner (envelope; add the |Aut| axis) | `experiments/tkde/rq7.py`, `configs/rq7.yaml` |
| corpora loader | `experiments/tkde/corpora.py::load_collection(name, root)`; records → `KBRecord.to_hypergraph(n_types=, n_preds=)` |
| Picasso | `scripts/tkde/{sync_to_picasso.sh, picasso_env_setup.sh, harvest_from_picasso.sh}`; conventions in `PICASSO.md`; node family `sd`; results root `$HOME/results/IEEETKDE` mirrored to the drive |
| probes to reuse | `scripts/diagnostics/encodings_worked_example.py`, `pointer_timeout_symmetry_probe.py`, `rq3_deletion_boundary_probe.py` |
| sibling engines (for reference only; their pruning is invariant-based, see D-ART4 (2b)) | `/home/mpascual/research/code/IsalGraph/src/isalgraph/core/native/src/canonical.cpp`, `/home/mpascual/research/code/IsalSR/code/src/isalsr/core/native/src/{canonical,wl}.cpp` |

---

## 7. Pitfalls already paid for

- **rapidfuzz compares sequence elements by hash.** `TokenP(i)` and `TokenN(i)`
  hash-equal; the September probe under-reported the pointer response on
  67 % of pairs. Always use `experiments/tkde/budget.py::symbol_distance`
  (equality-keyed alphabet; regression-pinned).
- **Normalisation.** Divide by the length of the sequence the distance was
  measured over (seed-prefixed word on multi-label collections). Report
  *absolute* tokens first: the paper's distance is raw (L11).
- **Tokens vs bytes.** Compare against `nauty_cert_rows` as well as
  `nauty_cert`; never explain a per-token difference by string length without
  the matched tokenisation.
- **Never transport a rank vector between two objects** (`DESIGN.md` G1): a
  canonical labelling is canonical only up to an automorphism; compare words.
- **Process-level budgets.** The C++ call does not return on `SIGALRM`; use
  the forked-child guard. Censored items are excluded from medians and
  counted per stratum (L15).
- **Environment.** The editable install is path-pinned; work in a cloned env
  inside your worktree (`CLAUDE.md` §Environment hazard). Provenance stamps:
  `src_deploy` must name the tree that served the library (the RQ4 refill
  mislabel is documented in `INDEX.md` §2).
- **Symmetric fixtures for correctness.** Fano, STS(9), the cyclic `C_13`
  orbits, GQ(2,2), both true STS(13)s (`tests/unit/core/test_wstar_c_frozen.py`,
  `datasets/synthetic/sts_catalog.py`). Any orbit-pruning implementation must
  reproduce the frozen `w*_c` on all of them bit for bit.

---

## 8. What you must deliver

1. **A written proposal before any measurement** (pre-registration,
   `DESIGN.md` style): the variants (A–D or a subset), the theorem sentence of
   each, the hypotheses with their direction, the corpora (the three RQ1
   corpora), the arms (`w*_c` at 60 s and 600 s on its censored tail; your
   variants; `nauty_cert`; `nauty_cert_rows`), the axes (M0 exactness; M1
   single-edit response in absolute tokens, normalised, within-≤ 2, zero-shift;
   the relative-vs-absolute addressing test on `add_constant` and
   `insert_fact_new_constant`; M2 monotonicity on the NDC natural pairs and
   WD50K ladders; M3 cost and censoring by `|Aut|` bucket; M4 ρ against the
   certificate), and the selection rule (pre-registered: adopt the variant
   with the best typical-case locality among those exact on all corpora and
   with censoring below a stated ceiling). Flag every point that needs the PI
   (D-TA2 supersession; nauty as oracle vs as order).
2. **The implementation** as registered arms in `experiments/tkde/matrices.py`
   and the RQ1 runner, with unit tests: M0 pins, the frozen-`w*_c` fixtures for
   any value-preserving variant, decodability of random strings, a golden
   word per fixture.
3. **The RQ1 table** on Picasso with the full statistics harness
   (`DESIGN.md` G5), persisted under `results/IEEETKDE/RQ1_isal/` with
   `tables.md`, `stats.json`, `manifest.json`.
4. **A one-page reading for the PI**: which variant, why, what it costs, what
   it still cannot do (R-list updated), and the sentence the paper will use to
   describe nauty's role.
5. **A ledger note** under `docs/article/DEVELOPMENT/` (task-handoff style)
   for anything out of scope you find, and a dated summary under
   `.claude/notes/`.

Report failures with the same directness as successes: if no variant beats
the certificate rows on locality, that number goes in the table and the paper
argues from the language alone, as D-ART4 (1) already anticipates.
