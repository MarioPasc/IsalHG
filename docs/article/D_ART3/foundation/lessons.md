# Lessons — what the previous iterations teach the new experiments

*Foundation sheet for the D-ART3 re-scope, 2026-09-03. Standing instruction
from the author (2026-09-03): **prior results are not assets to reuse; every
experiment of the new article may start from zero.** What carries over is the
experience. This file turns that experience into design rules. Each rule names
the episode that taught it (provenance in `measured_facts.md`).*

---

## 1. Corpus design

- **L1 — Size confounds everything.** On the first design corpus a distance
  built from `|Δn| + |Δm|` alone reached ARI 0.442 / AUC 0.932 and beat five
  of seven representations (Stratum A, retracted 2026-08-09). Every corpus
  with class labels must fix `(n, m, k)` — and where possible the degree
  sequence — across classes, and must always include the two naive floors
  `size_l1` and `degree_seq_l1`. A confound guard test exists
  (`tests/integration/test_corpus_confound_guard.py`); port it.
- **L2 — Regular, trivially-labelled substrates are a dead end for `d_I`.**
  On d-regular k-uniform hypergraphs a degree-preserving 2-edge swap rewrites
  ≈30 of ≈50 canonical tokens, and the maximum ARI reachable over four
  constructions was 0.234 (T-M7p, "impossibility record"). WL is also blind
  there (one colour). KB corpora must be **labelled** (unary predicates on
  constants, predicate names on facts) and structurally **anchored**; never
  build a class structure out of small perturbations of an unlabelled regular
  substrate.
- **L3 — Steiner-type and highly symmetric substrates are uncomputable.**
  STS(13) ≈ 160 s per instance, STS(15)/PG/AG designs DNF at 300 s, rigid
  STS(15)/STS(19) > 900 s; the cost driver is the pair-coverage tie structure,
  not `|Aut|`. Do not use combinatorial designs as KB substrates.
- **L4 — The feasibility envelope is the binding constraint, and it is per
  item.** Unlabelled random 3-uniform: p50 1.7 s at `n = 24` low density,
  DNF beyond `n ≈ 24–32`; `k = 5` only at `n = 8`. Canonicalization is paid
  once per KB, so the envelope caps each KB, not `N`. **Measured 2026-09-03
  on real KBs (`probes_2026-09.md` §4–§5): the frontier is the incidence
  mass `m`, not `n`** (an ego-net with `n = 25, m = 150` runs in 0.06 s while
  `n = 14, m = 114` times out; `m ≤ 111` → 20/21 complete, `m ≥ 253` →
  0/15), and **labels are the tie-breaker** (WD50K: labelled milliseconds,
  unlabelled 33 % DNF at `n ≈ 13`; ARB: labelled 1.9× faster). Size KB
  corpora by `m` and always keep the labels.
- **L5 — Corpus-level arity must fit the cap.** HIC failed the gate because
  the corpus-level `k` was 110 against `K_MAX = 10`; the arity-capped
  sub-corpus lost 21 % of items and the DNF tail was symmetry-driven, not
  size-driven. Pick datasets whose *maximum* fact arity is small (ARB tier 1:
  max arity 5) rather than filtering a heavy tail.
- **L6 — Real "single giant network" datasets are collections only after a
  citable derivation.** The ego-network of Qin et al. (ICDE 2023, Def. 1) is
  the citable derivation and is implemented (`core/sparse_hypergraph.py::ego_network`).
  Ego-nets of one dataset are exactly "N knowledge bases over one signature".

## 2. Distance and representation hygiene

- **L7 — `d_I` runs on tokens, not characters.** The idea-3 draft's "384×
  slower" figure used character length; the token length at `n = 10` is
  ≈ 22–44 tokens and `L²` is the same order as `n³` (gate G-L4). Never quote
  character lengths.
- **L8 — Labelled inputs need the augmented fingerprint.** The bare `w*_c`
  omits its own seed vertex's label; `d_I` on labelled inputs is taken over the
  seed-label-prefixed token sequence (one substitution when seed labels
  differ). KBs are always labelled, so the whole article runs on `d_I^Σ`, and
  every prior geometry number (measured on `d_I^⊥`) is from a different
  member of the family — another reason to re-measure rather than reuse.
- **L9 — The nauty contrast baseline is byte-level.** `NautyLeviEditDistance`
  computes Levenshtein over `color_signature ++ pynauty.certificate(B(H))`
  *bytes*. The prior "3/5/9 vs 20/30/37" sensitivity contrast therefore
  compares IsalHG tokens against certificate bytes. If a canonical-labelling
  edit distance stays in the paper, its tokenization must be stated and
  defensible (e.g. one symbol per canonical adjacency row), and the contrast
  re-measured on that basis.
- **L10 — `k` and the tuple depth index the metric family.** `w*_c` depends on
  the pointer count `k` and the structural-tuple depth; distances computed
  under different `(k, h)` live in different spaces. One `k` per comparison
  (the corpus maximum).
- **L11 — Length-normalized edit distance is not a metric.** Keep raw
  Levenshtein primary; report a normalized variant only as an ablation and
  never feed it to an algorithm that needs the triangle inequality.

## 3. Evaluation discipline

- **L12 — Pre-register the interpretation.** Every competitor table carries a
  written contract before results are seen; no baseline is removed for
  winning. This is what made the T-M4b loss reportable without loss of face
  and it is what a TKDE reviewer will check.
- **L13 — Task metrics vs planted labels are where `d_I` lost.** On the FINAL
  size-controlled corpus nauty-Levi edit, HPD and NetLSD beat `d_I` on ARI
  and kNN AUC, all Holm-significant. The new article must not make "recover
  planted small-perturbation classes" the headline evaluation of any
  application. Evaluate what the theory guarantees (metric, exactness,
  certificates, decodability) and what the application delivers (a decoded
  consensus, a certified ratio, a false-merge count), with class-recovery
  reported under contract as a secondary axis.
- **L14 — Statistics harness: 27 seeds, 95 % BCa CIs, bidirectional
  Holm-corrected Wilcoxon.** Reuse the harness, not the numbers. Persist the
  Wilcoxon results explicitly (they were silently never written once).
- **L15 — Censoring must be reported per stratum.** DNFs under a fixed
  per-item budget are dropped and counted, yield reported per size bucket,
  label-correlated censoring stated. Inherited from the HIC exhibit.
- **L16 — Measure the gate before scoping the experiment.** Every prior plan
  that skipped a gate (HIC arity, Stratum A size) paid for it. The gates for
  the new article are the ego-net size/`N` distribution, the labelled
  canonicalization time, and the consensus-search landscape (all probed
  2026-09-03; see `probes_2026-09.md`).

## 4. Claims discipline

- **L17 — Concede identity and deduplication speed to nauty/bliss/Traces**
  in the introduction; `w*_c` is orders of magnitude slower on symmetric
  inputs and equally exact. Never build a claim on canonicalization speed.
- **L18 — Never call `d_I` a proxy for an edit distance.** Spearman ρ = 0.622
  against exact HGED, an unconditional but enormous envelope
  `d_I ≤ m(1+kn)·HGED`, and an impossibility argument for any bi-Lipschitz
  relation. `d_I`-minimal is *constructively* minimal, not fact-minimal; say
  so and measure the gap where an oracle runs.
- **L19 — Decodability claims must be about the ambient space.** The shipped
  A4 "decodability score" was vacuous (it decoded objects that were already
  hypergraphs). The real statement is P1: every word in `Σ_HG*` decodes to a
  connected hypergraph, and the interior of an alignment path is non-canonical
  words that still decode (62/62 measured). Prove it, pin it, and use it
  where it matters: a consensus word that is not any input's canonical form
  still names a knowledge base.
- **L20 — Every geometric invariant needs a consumer.** The v3 geometry grew
  unreadable (PI: "se pierde uno leyendo"). Measure `ν` (licenses
  medoid-type methods and metric MDS over classical MDS), hubness (kNN-based
  outlier scores), and the single-edit response (the limitation), and nothing
  without a consumer.
- **L21 — Apply the PI's criterion literally.** *"Buscar aplicaciones en las
  que sea imprescindible o muy ventajoso lo que diferencia IsalHG: un espacio
  con una distancia definida, formado por puntos que son invariantes frente a
  isomorfismos."* Applications are metric-space operations over collections
  of iso-classes; the differentiators are exactness, metric guarantees,
  polynomial pairwise cost, and a decodable ambient space.

## 5. Engineering

- **L22 — Editable installs are path-pinned.** Any worktree agent must clone
  the conda env; a stale `.so` produces phantom failures (`CLAUDE.md`).
- **L23 — The oracle is expensive and frozen.** Exact HGED peaked at
  > 100 GB / 18 h for one 630-pair block at `n = 10`. Any new oracle use is
  `n ≤ 10, m ≲ 8` per pair, on HPC, and scoped before it is scheduled.
- **L24 — HyperCOT is gated at `N ≤ 20`.** It never ran on the FINAL corpus;
  either drop it or state the gate.
- **L25 — Verify before trusting a "VERIFIED" tag.** The idea-3 development
  marked the non-metricity of bipartite GED as verified on the strength of a
  sketch and unverified citations. This re-scope re-checked it computationally
  (`probes_2026-09.md`). Treat every prior verification tag the same way.
- **L26 — Declare and assert the inputs that decide what a measurement is
  *about*; never let them be inferred.** Three separate defects in one week,
  all the same shape, all producing a confident wrong number, none raising:

  | inferred value | inferred from | what it produced |
  |---|---|---|
  | a results column's dtype | whether any unit in that corpus censored | `'0'`/`'1'` in one corpus and `'0.0'`/`'1.0'` in another; a reader validated on one silently matched nothing on the other and reported a recovery rate of 0.0000 whose true value was 0.279 |
  | a collection's member count | a row count | the 922 figure |
  | the results root a job reads | an unexported environment default | `tail600` would have measured a census carrying no `wstar_rank` arm at all, under the name of the job that is *about* `wstar_rank` |

  Each failed **toward silence** — no match, no error — which is why review did
  not catch any of them. The common cause is not carelessness at the call site;
  it is that the value was never declared anywhere, so there was nothing to
  check against.

  The rule has two halves, and the second is the one that was missing:
  1. declare the input (dtype, count, root) explicitly, and
  2. make the assertion a **precondition**, not a check afterwards.

  Worked example — the `tail600` launcher fix. It previously exported only
  `REPO_DIR` and left the census root to whatever `--export=ALL` happened to
  carry, with `common.sh` defaulting it to a tree whose census lacks the arm
  being measured. It now resolves `RESULTS_ROOT` / `DATA_ROOT` / `CORPORA_ROOT`
  itself, exports them by name, and **fails at submit time** if the census does
  not resolve — rather than on sixteen nodes, or worse, not at all.

  Corollary for readers of data already written: rows on disk keep whatever
  spelling they were written with, so normalise at **read** (coerce the
  known-numeric columns in the loader) as well as fixing the writer. Fixing only
  the call sites that are currently wrong leaves the next one to be discovered
  the same way.

  **Why these are mandatory rather than advisable.** On the alignment-exhibit
  scare, two careful readers reasoned their way to the same wrong conclusion —
  one of them the reader who had written the rule against it four exchanges
  earlier. What settled it was a grep (the pre-registration already forbade the
  proposed fix) and a measurement (0 of 2,736 members in the window were
  censored, so there was nothing to fix). Neither reader caught it by thinking
  harder. Two mechanical checks beat two careful readers on the same item, which
  is the argument for running them by default rather than when something feels
  wrong — the feeling is exactly what was unreliable.

  **A number without a source is not evidence, whichever way it points.** Three
  figures for one generator's connectivity were circulating one sentence apart
  in the prose and one matched no run on disk. When it was re-sourced it moved
  *against* us on one collection — the fact-list generator is better than we had
  been claiming — which is the case that makes the rule stick: the reflex is to
  scrutinise numbers that flatter the competitor and wave through the ones that
  flatter us. Every quoted number gets a `foundation/` entry naming its run root
  and table; anything unsourceable is struck, not kept.

  **Every check reports the number of rows it consumed, and a check whose N
  differs from the expected N fails rather than passes.** A check that passes by
  comparing almost nothing is invisible precisely because passing looks like
  success. Worked example, from the script written to enforce this very lesson:
  its row key omitted `member_id`, so 600 completion rows collapsed onto 6 by
  dict overwrite and it reported *"every column bit-identical (6 rows)"* —
  green, and comparing 1 % of the data. It now raises on key collision rather
  than warning, and the self-test compares 600/60/358 rows where it had reported
  6/3/54. Any check that silently loses rows is reporting an answer it did not
  earn, which is this lesson's own subject.

  **A rate is only quotable beside another rate when both share a denominator.**
  RQ6 writes `connectivity = n_connected / n_valid`, conditional on validity. For
  the arms at validity 1.0000 conditional and unconditional coincide, so the
  distinction is invisible — until an arm at validity 0.0190 reports
  connectivity 0.0909, i.e. *above* its own validity, which is coherent only
  because the denominator is the 1.9 % that decoded. Three such figures quoted
  side by side sit on two different denominators. Report the **joint** rate as
  the headline (valid *and* connected, over samples drawn) and give validity and
  connectivity as its factors.

  **Make the rule a function, not a habit.** Two of these rules each caught a
  defect in the script written to enforce the *other*, both written by the author
  who had just filed the lesson. That is not inattention; it is evidence that a
  rule which must be remembered at every call site will not be. The guards now
  live in `scripts/diagnostics/rowsio.py` and are the only sanctioned way a
  diagnostic reads campaign rows: `num()` coerces instead of string-comparing,
  `key_by()` **raises** when two rows share a key instead of dropping one by
  last-wins, `load_rows()` announces the row count it consumed, and
  `expect_rows()` fails when that count is not the expected one. Tested in
  `tests/experiments_tkde/test_rowsio_guards.py`, including the two silent
  failures themselves. Habits failed twice in one session; the collision error
  is what worked.

  **A silenced error plus an unconditional next step is the same defect in
  shell form.** `git stash push <path>` on an *already-committed* file is a
  no-op; `2>/dev/null` hid the message saying so; and the unconditional `git
  stash pop` that followed then reached for whatever was on top of the stack —
  a three-month-old stash, which landed on the branch with conflict markers in
  fifteen tracked files including the canonical encoder. Nothing was lost
  (a conflicted pop keeps the stash entry, and the work was committed), but the
  failure was silent at exactly the point where it should have raised, which is
  this lesson's subject in a different language. Two guards worked: the
  permission layer refused `git reset --hard`, and a peer session checked the
  tree rather than trusting the report. Never discard stderr on a command whose
  success you are about to depend on.

  **When the data supports three states, a binary hides one of them — and it is
  never the harmless one.** Three verdicts in a single session collapsed a
  distinction the measurement could actually make:

  | collapsed | should have been | what the collapse did |
  |---|---|---|
  | `None` for "no member in the fact-count window" | `False` — a failed *necessary* condition is a proof of "no" | dropped those samples from the denominator, overstating one arm **2.18×** |
  | a blank `reach1` folded to `0` by `fillna` | "not computed", excluded from the denominator | counted an unmeasured value as a measured failure |
  | `REFUTED` for a non-significant differential | `INDETERMINATE` when the estimate favours the claim | would have retired a **true** claim, rewriting three downstream ones |

  The shape is the same each time: a binary where the data supports a trinary.
  And in all three the collapsed state was the one that flattered whichever
  claim was under test, which is why none of them looked wrong while being
  written. The check is mechanical — for any reported rate, ask what the
  denominator excludes and whether "cannot tell" is distinguishable from "no".
  If it is, the verdict has three states and the report carries an interval, not
  just a label.

  **Guard the shape, not the spelling — and make the checks redundant.** By the
  end of the session the count was five: a filter comparing `"1"` to `'1.0'`, a
  key that collapsed 600 rows onto 6, a `fillna(0)` folding blanks into
  failures, a dtype that changed with censoring, and a membership set built from
  *truncated* sha display strings while the rows carried 40-char values. In
  three of the five the empty result was the **comfortable** answer, and twice
  the artefact that broke a rule was the one written to enforce it.

  A helper per spelling — a short-vs-long sha comparator, say — fixes one and
  leaves the sixth. All five share one signature: **an operation silently
  produced fewer results than its input warranted.** So
  `scripts/diagnostics/rowsio.py` guards that shape:
  `classify()` requires a **total** partition (a row matching no bucket raises;
  a bucket receiving nothing raises unless declared empty-able) and `reduced()`
  refuses to return an empty result unless the caller asked for one. The
  truncated-sha audit fails at its first row under that rule instead of
  reporting a comfortable zero across every results root.

  And note what actually caught the fifth: not review, not attention, but **two
  halves of one output contradicting each other**. A single check that can be
  wrong in the reassuring direction is not enough on its own, so the checks are
  worth making redundant as well as structural.

  **A write is not verified by its exit status, only by reading back what it
  wrote.** Two of the session's six silent failures were writes, not reads: an
  anchor-patch script whose anchor did not match because a heredoc had escaped
  the backticks differently, and which returned zero either way. `classify()`
  and `reduced()` guard the data path; the edit path has no equivalent, so
  prefer the tool that **fails when its anchor is absent** over the hand-rolled
  script that succeeds vacuously — and when a script must be used, grep for the
  result rather than trusting the exit code.

  **A reproduction that does not reproduce the *configuration* is not a
  reproduction.** Recomputing RQ6's joint yield on WD50K gave 0.0903, then
  0.0886, then — with the roles map the campaign actually uses — **0.0685**. The
  first two were faithful to a pipeline that does not exist: `wd50k66` sets
  `roles: true`, so the model is fitted on role-aware words, and a script that
  fits role-free words samples from a different model. Nothing in the script was
  wrong.

  **No guard in `rowsio.py` would have caught this one.** The rows were read
  correctly, the keys were total, nothing matched nothing, and no reduction
  collapsed. The only thing that exposed it was a **number already on disk**: the
  reproduction matched the campaign's NDC connectivity to four decimals (0.4157)
  and missed WD50K's (0.1563 against 0.1260). So the rule is to reproduce a
  quantity the campaign already reports *alongside* the new one, and to treat a
  mismatch there as disqualifying the new number — a second recorded opinion
  rather than a second check, which is a different kind of redundancy from the
  structural guards and catches a different class.
