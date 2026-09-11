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
  *about*; never let them be inferred.**

  **Read this first, because it explains why the rest of this entry keeps
  happening inside the artefacts written to prevent it.** Across one session the
  same pattern appeared four times and each time the author was the person who
  had filed the governing rule, usually hours earlier:

  | the rule | how it was broken |
  |---|---|
  | *declare the expected count* | declared for the sweep, not for the yield forty lines below |
  | *grep for the result, do not trust the exit code* | a check printed `False` and the commit ran anyway, chained by `&&` |
  | *grep the code's own prose first* | a task declared on "no counter exists" against an oracle carrying one |
  | *a number in support of a claim must be from its population* | sweep lengths quoted beside a `wd50k66` timing |

  **A rule you wrote protects you least, because writing it is what makes you
  feel you have already applied it.** That is not irony, it is the mechanism:
  authorship converts a rule from something to *run* into something you *know*,
  and knowing it is exactly what a precondition is supposed to make unnecessary.

  The consequence is structural and is the whole argument for the guards in
  `scripts/diagnostics/rowsio.py`: **a rule that must be remembered at each call
  site will not be, and its author is the least likely person to remember it.**

  **The same mechanism has a second face, and it is the more dangerous one: a
  limitation you filed constrains you most.** Writing a rule makes you feel you
  have applied it; **writing a limitation converts an open question into a settled
  fact** — and then nothing downstream ever contradicts it. Three in one session,
  each dissolved by someone asking what the thing was *for*:

  | filed as | actually |
  |---|---|
  | *"no run records the branch factor"* (T-KBw) | `orbit_oracle.py` already carried `autgrp_calls`, diagnostic-only, in the timed path |
  | *"the near-miss window cannot be tuned"* | a **coverage** gap: extend the freeze audit's compared set and the exact screen becomes complete |
  | *"the counter must not perturb the wall-clock"* (T-KBw) | a **design choice**: branch count is structural, so the counted run needs no time fidelity — run it separately and the constraint does not exist |

  **A wrong limitation produces no failing test, no mismatched count, no
  arithmetic that does not close.** A defect has consequences that accumulate
  until something breaks; a false limitation has none at all — it silently
  removes work from the plan and **looks like rigour while doing it**. That is
  precisely why *"this cannot be fixed"* and *"this is not fixed yet"* are
  indistinguishable from inside the tool.

  The remedy is the one already stated and needs no addition: where a rule cannot
  become a function or a failing test, it must be checked by someone who did not
  write it. **A filed limitation is exactly such a rule, and it is the one least
  likely to be revisited, because the file says it is closed.** (Formulated by
  `[IsalHG-Fable]`, who dissolved all three.)

  **And the distinction every tool below eventually needs: a screen is not an
  audit.** It arose three times in one session, in three unrelated tools — the
  numeric figure screen (proves a value stale, never proves one correct), the
  frozen-rows diff (its `only-live` count is the dangerous one, not `differing`),
  and the check-authority sweep (shows a failure path exists, not that the
  relevant one is wired). Each time the temptation was to report the clean result
  and move on. **A screen narrows the candidate set; only a reader or a trace
  closes it** — and a tool that reports "clean" is asserting something about its
  own reach, which is a claim that has to be stated before the result can be
  used.
  Every rule below should be read as a candidate for becoming a function, a
  failing test, or a tool that refuses — and where it cannot be, as something to
  be checked by someone who did not write it. (Formulated by `[IsalHG-Fable]`,
  2026-09-11.)
 Three separate defects in one week,
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

  **The inverse failure: a source with no number in front of it.** The word
  "novel" appeared **nowhere** in `prose.md`, so an entire RQ6 result *and* its
  caveat existed only in `foundation/`. That is the mirror image of the day's
  other mode — not a quoted number that cannot be sourced, but a sourced result
  that is quoted nowhere — and **T-KBg's fold precondition does not catch it**:
  the precondition audits the numbers the prose already carries, and is silent
  about the ones it should carry and does not. Both directions need checking, so
  the fold's checklist runs the `foundation/` entries against the prose as well
  as the prose against the entries.

  **A pre-registered threshold needs a power statement written at the same
  moment, or it pre-registers a coin flip.** tail600's clause 1 was committed in
  code before any data was read — correct discipline — as "orbit recovers ≥ 25 %
  of its 77". It landed at 19/77 = 24.7 %, whose 95 % Wilson interval is
  [0.164, 0.354]: **the threshold sits inside its own confidence interval**, so
  at n = 77 the clause could never have resolved anything. Report it refuted as
  written and print the interval beside it. Same discipline as refusing to read a
  direction off a null at n = 63, applied to a threshold rather than to a
  comparison.

  **A count is not a liveness signal: every progress figure carries the newest
  mtime beside it.** A stale directory and a live one are **indistinguishable by
  file count** — only a timestamp or a write rate separates them. Every RQ4
  progress figure reported in one session ("stuck at 819", "moved to 974",
  "1,292") came from a results root frozen five days earlier, while the live root
  had 1,106 files and was being written to that minute. The handoff already says
  this for monitors — key on job state, never on file counts — and the reporting
  was doing exactly what that rule forbids.

  It costs one field: `1,106 files, newest 23:33`. Staleness then announces
  itself instead of waiting to be suspected, which would have surfaced this at
  the first report rather than the twentieth.

  **Four of the session's failures had nothing wrong with the method — only with
  what it was pointed at**: the wrong results root, a model fitted without the
  corpus's `roles` flag, a membership set of truncated shas, a check whose key
  omitted `radius`. Alongside "reproduce a campaign quantity beside the new one",
  these say the same thing: **verify the target, not only the method.** A correct
  instrument aimed at the wrong object returns a clean number every time.

  **Take the join; marginals cannot tell you when they are safe.** Two counts
  reported separately were subtracted twice in one session. Once it gave
  "8 branching-only casualties", which the join reduced to 2 — six of the eight
  turned out to carry the very symmetry the claim assumed absent. Once it gave
  "about 15 matched members", which the join confirmed exactly.

  **Both marginals were correct in both cases.** Nothing available before the
  join distinguishes them, which is the argument in its strongest form: it is not
  that marginals are unreliable, it is that the same operation was right once and
  wrong once and **the difference is invisible from the marginals themselves**.

  This is the fourth appearance of the day's dominant failure — a valid operation
  applied to the wrong object. The four differed only in what supplied the wrong
  object: a results path never checked, a config flag not reproduced, a display
  string mistaken for a value, and a grouping never joined. The operation was
  correct every time and no error was raised any time, because **a correct
  operation on the wrong object has nothing to complain about**.

  **Pre-register what must be *reported*, not what you expect to find.** RQ4's
  missing units acquired three successive explanations in one session — "no
  bundle size fixes it", "deferral tracks per-unit cost", and finally the
  measured one (the deadline is computed from the array's submit time, so
  deferral is monotonic in start delay). The first two were asserted without
  measurement and withdrawn.

  What survived all three was an **obligation** written while both parties still
  believed something false about the cause: *report the missing set's
  `(m, max arity, |Aut|)` profile beside the censored set, and if it is
  non-random the AUC carries the caveat.* That requirement is still what will
  settle whether the loss is biased.

  **A diagnosis has to be right to be useful; an obligation to report a
  distribution only has to be asked.** So when something is missing or censored,
  pre-register the *reporting* of its profile rather than an explanation of its
  cause — the explanation can be wrong three times over and the obligation still
  does its work.

  **When the objection is about what a pipeline *does*, grep the code's own prose
  first.** Twice in one session a question was already answered, in as many
  words, by whoever wrote the code:

  - *does novelty's role-free key make a role-differing sample count as novel?*
    — the `novelty` docstring says it passes role-free keys deliberately, *"so
    that a sample reproducing a member up to argument roles still counts as a
    reproduction"*;
  - *can a task past its deadline run a unit on a trimmed budget and record a
    censoring?* — `rq4.py` says *"NEVER trim its budget to make it fit: a unit
    that got a fraction of its time is not comparable with its paired units."*

  Both objections were sound and both had been anticipated. Searching the code's
  comments is cheaper than measuring and faster than reasoning, and it is the
  right first move whenever the question is about **behaviour** rather than about
  a number the behaviour produced.

  **Ask about the uncertainty; being right about it is a lower bar than it
  looks.** Two of the peer session's sharpest interventions tonight rested on
  premises that did not survive: a guess that two matched pairs of counts were
  the same members (they overlapped six of eight), and a claim that the missing
  units were cost-selected (they were selected by task start delay). Both were
  withdrawn. **Both produced the measurement that changed what the paper will
  say** — the arity × symmetry cross-tab, and the per-cell profile that found the
  `iso_twin` depletion.

  A wrong question aimed at a real uncertainty still produces the measurement.
  So the standard for raising something is not "I think this is wrong" but
  "nothing here has been measured" — which is a lower bar, and a far more useful
  one, because a correct challenge and an incorrect one are equally good at
  forcing a number into existence.

  **A result whose inputs remain writable cannot be audited later, however
  stable the numbers turn out to be.** The tail600 verdict — four refuted
  clauses, an inverted differential, three downstream sentences rewritten — was
  computed from rows sitting in the live results tree. tail600 has no idempotent
  skip, so its `afterany` recovery sweep re-ran all sixteen shards and
  **overwrote those rows**. It agreed: zero censoring flips, `secs` the only
  differing column. Had it disagreed, the inputs to the recorded verdict would
  simply have been gone, and no amount of care afterwards could have said which
  run produced the number in the ledger.

  Note what the stability does *not* buy. "It agreed" is a fact about this
  sweep; it is not a property of the artefact, because the next writer need not
  agree and there would again be no record. The fix is cheap and structural —
  copy the rows to a read-only path and name the job that produced them at the
  moment the number is recorded, which is what RQ1's deliverable already does
  and what the tail600 rows now do. **A published number is computed from a
  frozen snapshot, not from a live tree.**

  The same reasoning upgrades the replication claim itself. Zero flips across
  two runs is an observation about two runs; the **distance to the boundary** is
  a property of the distribution. Measured: the slowest orbit completion leaves
  244 s of the 600 s budget unused (41 %), the slowest rank completion 390 s
  (65 %), and **no completion sits within 120 s of the cutoff**. That converts
  "nothing flipped" into "nothing is close enough to flip" — a reason instead of
  a coincidence, and one that does not depend on having happened to run twice.

  **The count reached six, and the sixth was found by being asked for rather
  than by being suspected.** The RQ7 censoring table was marginal in `|Aut|`,
  and read that way it said the orbit-pruned form censors 29 % at low symmetry
  and 92 % at high. The join says **all 427 instances at `|Aut| ≥ 1e7` also
  carry `m ≥ 80`** — every high-symmetry instance in that sweep is a large one,
  so the marginal attributed to symmetry what partly belongs to size.

  What makes this one worth recording separately is that the join did **not**
  dissolve the effect, as it had for the "8 branching-only casualties". Symmetry
  survived it: at fixed `(m, k)`, censoring rises across `aut_bucket` in 9 of 15
  usable cells and **falls in none**. So the join's job is not to debunk the
  marginal — twice tonight it confirmed one — it is that **nothing available
  before the join tells you which of the two it will do.**

  It also produced a third answer where a binary was expected. The prediction
  under test was "divergence tracks arity rather than `|Aut|`". Arity turns out
  to be a **gate** — `k = 2` censors 0.000 at every `m` and every symmetry level,
  including 0 of 22 instances at `m = 160` with `|Aut| ≥ 1e7` — and symmetry
  modulates *inside* the gate. Neither "confirmed" nor "refuted" is the honest
  label, which is the three-states rule arriving somewhere new: not in a verdict
  this time, but in an **attribution**.

  **And a join across two experiments is worth running before a reviewer does
  it.** RQ1 reports orbit pruning taking censoring at `|Aut| ≥ 1e7` from 36 to
  **zero** on real corpora; RQ7 reports **392 of 427** censored in the same
  bucket at the same budget with the same engine. Nought per cent against
  ninety-two. Both are correct: every `≥1e7` sweep instance has `m ≥ 80`, and
  **no member of the four real collections reaches `m ≥ 80` at all** (medians 3
  to 5, maxima 27 to 41). They describe disjoint regions of the grid. Two
  numbers that contradict each other on their face, in two sections of one
  paper, need the reconciling sentence written by the authors — the alternative
  is that it gets written in a review.

  **A declared precondition protects only what it was written for; the same
  script's other half is where the next one lands.** `rq7_envelope_reading.py`
  declared the sweep's expected row counts up front — 7,776 per Isal arm, 7,938
  with the extension — and verified all five. It declared **nothing** for the
  yield pass sitting forty lines below, so `ndc_classes` was reported as
  *"828/828 = 1.000"* when the corpora manifest says **1,381** and only three of
  its five blocks had landed; `wd50k100` was read at 919 of 1,837.

  Two things make this worth its own line rather than another tally mark.

  **The rule was applied where the author had already been burned.** The sweep's
  counts were declared because a previous defect had made row counts feel
  dangerous. The yield's were not, because nothing had gone wrong there yet. That
  is *availability*, not discipline, and it is the failure mode a written rule is
  supposed to remove: a precondition that gets applied where it is remembered is
  a habit wearing a rule's clothes (the same finding as "make the rule a
  function, not a habit", now in the form where the function existed and was
  simply not called on the second input).

  **A partial read is not random, and which end is missing decides what it
  costs.** `run_yield` shards by contiguous `block_slice` over records ordered
  **descending in `m`** — block medians 6, 6, 5, 4, 4, 3 on the collection that
  is complete. So `ndc_classes`'s two absent blocks are its **largest** members,
  the exact population an envelope claim is about, which makes its observed
  `max m = 30` a floor and its "zero members at `m ≥ 80`" unestablished;
  `wd50k100`'s absent block is its *smallest*, so the same statistic there is
  conservative. **One direction stated for both would have been wrong for one of
  them**, so the check names the missing blocks per collection instead of
  asserting an end.

  And it reads the block total out of the **filename** (`002of005`), not out of
  the blocks present: a set of things that arrived cannot report the ones that
  never did. That is the same shape as the count-without-an-mtime — the data you
  have cannot tell you what is absent from it, so the expected extent has to come
  from somewhere the data does not control.

  **A correction is a write, and unverified writes fail the same way the
  original did.** The fix for the partial read replaced the reconciliation's
  population in two documents by string substitution. It matched in one and
  **not** in the other — the sentence had wrapped at a different column — and the
  script reported success, because what it printed was that the *appended note*
  had landed, not that the *replacement* had. The wrong sentence therefore sat
  in `T-KBf.md` through a commit whose message said it had been corrected.

  That is the heredoc-anchor defect again, in the specific place it is least
  expected: **inside the repair of another defect**, where attention is at its
  highest and the sense of having just been careful is strongest. The rule
  already exists — *grep for the result, do not trust the exit code* — and the
  usable form of it is narrower: **verify the assertion you actually care about,
  not a neighbouring one that happens to be true.** Checking that the note
  appended was a real check of the wrong proposition.

  The tool choice does the work that vigilance did not: `Edit` fails when its
  anchor is absent, a bare `str.replace` returns the string unchanged. Where a
  script must substitute, `assert anchor in text` before writing — which is the
  same shape as `classify()` raising on a row that matched no bucket.

  **The operational form, and it is strictly stronger: a replacement is verified
  by the absence of what it replaced, not by the presence of what replaced it.**
  A partially applied replacement leaves *both* — which is precisely what
  happened, the new sentence in one file and the old one still standing in the
  other. Grepping for the new text passes in the file that changed and says
  nothing about the file that did not; grepping for the **old** text fails
  wherever it survives, across every file at once, **without the checker having
  to know which files were supposed to change**. Same grep, no dependence on
  remembering that an anchor might have wrapped. (Raised by `[IsalHG-Fable]`
  after the fact — the absence check is what established that the stale wording
  now survives only inside this entry.)

  This does not replace "verify the proposition you actually care about": it is
  that rule's operational form for this class. After a replacement the
  proposition you care about is a **negative** one — *the old text is gone* — and
  a presence check is structurally incapable of seeing a negative. The same
  reason `classify()` must be total: absence has to be checked for directly,
  because nothing about what is present reports it.

  **And why the self-verification failed, which is the precondition failure
  again in a new place.** A check written at the same moment as the edit, by the
  same author, out of the same intent, tends to confirm **what was meant rather
  than what was done**. No amount of care fixes that, because the care and the
  error come from the same source — which is the argument for verifying against
  the artefact's content rather than against one's own record of having acted.

  **And the replacement was itself wrong, for a third reason.** It said "no
  member of the three collections read whole reaches `m ≥ 80`" while the table
  four lines above listed `wd50k66_full` with **41 members at `m ≥ 80`** — a
  sentence refuted by its own page. Caught by `[IsalHG-Fable]`, whose earlier
  message had cited that exact row. The population was never the count of
  complete collections; it is the two *gated* ones, and the ungated variant is
  the counterexample that forces the qualifier. **A claim that names a
  population must name it by the property that makes the claim true** — "read
  whole" was availability again, this time in the phrasing rather than in the
  guard.

  **A column is named for what someone needed to call it, not for what it
  holds.** `rows_nscaling.secs_pairs_total` is the **whole-matrix** time —
  `_matrix_timing` returns `(canonicalization seconds, whole-matrix seconds)` —
  and an "N² pair slope" fitted to it measures canonicalization wherever
  canonicalization dominates. For `wstar_orbit` that is 1,736 s of a 1,736 s
  total, so the fitted exponent described the wrong phase entirely. The
  docstring saying so had been **read in the same session**, two hours earlier,
  while chasing something else.

  The tell was arithmetic, not suspicion: H7c's `N²` claim is a *count of
  comparisons*, so a measured exponent near 0.7 is not a weak result, it is a
  claim about a different quantity. **When a measurement contradicts something
  that is true by construction, doubt the measurement's subject before its
  value** — the pair phase is `whole − canon`, and where that difference falls
  under the canon pass's own run-to-run spread it is unresolvable rather than
  negative, which is what `wstar_orbit`'s −2.6 s actually was.

  **A round number in a timing column is a budget until proven otherwise.**
  `hpd_jsd` recorded exactly `3600.000` s at N = 3,988 — `censored=1`, and its
  other two reps `skipped=1` — and was one step from being written into a
  published table as "60 minutes". Sixty minutes is not a measurement of that
  matrix; it is a measurement of the cap. The same reading error as reporting a
  censored member's `secs` as its cost, which L15 already forbids for members and
  nothing had yet forbidden for *cells*.

  **A count reconstructed from a rounded rate is not a count.** `wd50k66_full`'s
  members at `m ≥ 80` were reported as 41, from `0.009 × 4,554`. The true count
  is **39**: the displayed 0.009 was a rounded 0.00856. Rounding is what makes a
  rate readable and is exactly what makes it unusable in the other direction, so
  a count is quoted from the count or not at all.

  **And the outcome that justifies holding a claim rather than hedging it.**
  `ndc_classes` was read at 60 % with its two *largest-`m`* blocks missing, so
  its "max `m` = 30, zero at `m ≥ 80`" was a floor that could have moved. When
  the blocks landed it had **not** moved — max 30, still zero. A hedge
  ("probably zero") would have been indistinguishable from this result, and only
  the measurement separates them. That is the argument for holding a number
  until it is earned instead of shipping it with a qualifier: the qualifier
  survives into the paper, the measurement replaces it.

  **A unit objection that disqualifies a measurement disqualifies everything the
  cost model derives from it.** Within one message I declined to say the Isal
  word is shorter than the nauty certificate — `tokens_or_bytes` holds *tokens*
  for one arm and *bytes* for the other, so 3,886 against 11,692 compares two
  units — and then headlined "17.4× faster than the nauty certificate". But a
  pairwise Levenshtein is `O(L₁ × L₂)`: **the matrix time is quadratic in exactly
  the lengths whose units had just been ruled incomparable.** Declining the
  length claim and keeping the timing claim is holding both sides of the same
  fact.

  The rule generalises past this instance: when a quantity is disqualified on
  units, trace what the cost model computes *from* it before keeping any
  downstream number. The arms that are not Levenshtein over a serialisation —
  NetLSD, WL, bipartite GED, HPD — inherit nothing and need no qualification,
  which is what makes the affected set findable rather than a matter of judgement.

  **And the comparison that has no unit problem was available the whole time.**
  `isal_ow_struct` 1.39 s against `wstar_orbit` 28.9 min — same alphabet, same
  tokenisation, same distance, **1,252×** — is the paper's actual claim: the
  search is what costs, and the same language without it is three orders of
  magnitude cheaper. Reaching past it for a cross-representation multiplier
  bought a bigger-sounding number at the price of a confound.

  **A ruling that names a required comparator is checkable, so check it.** D-ART4
  requires the certificate baseline in **two tokenisations** — bytes and one
  symbol per canonical adjacency row — because "the bytes-only comparison is a
  tokenisation confound". `nauty_cert_rows` had **already run** (13.87 s, in the
  same table two files away) and the headline omitted it, quoting the bytes arm
  alone: 17.5× where the row tokenisation gives **10.0×**. The confound the
  ruling exists to prevent, reproduced in the direction that flatters us, in the
  one comparison where the author had already named the comparator. Both are now
  reported and neither is quoted bare. (Caught by `[IsalHG-Fable]`.)

  **L15 extends from members to cells: a round number in a timing column is a
  budget until proven otherwise.** L15 says a censored *member's* recorded time is
  the budget and not a cost. Nothing said it for an aggregate *cell*, and
  `hpd_jsd`'s whole-matrix entry at N = 3,988 read exactly `3600.000` with
  `censored=1` and its other two reps `skipped=1` — one step from a table
  reporting "60 minutes" as the measured cost of that matrix. It is the
  measurement of a cap. Filed as the extension of L15 rather than as a new
  lesson, because the reading error is identical and only the granularity moved.

  **A number you repeat is a number you have asserted.** The 41 that was really
  39 was written by one session and cited back twice by the other as evidence
  from the first one's own table. *"It came from your table"* is not a check —
  both parties had reconstructed a count from a rounded rate and neither counted
  it. Provenance establishes where a number came from, never whether it is right,
  and a figure that has been through a display transform has to be re-derived
  from the source rather than read back out of the rendering.

  **Chaining a commit to its own verification defeats the verification.** The
  T-KBx update ran a substitution, printed `step 0 present: False`, and committed
  anyway — with a message asserting the step was there — because the check and
  the `git commit` were joined by `&&` in one invocation, so the output arrived
  only after the commit had run. The check worked perfectly and changed nothing,
  which is the worst of both: the cost of verifying, none of the benefit.

  This is the same defect as the earlier one-hour `3600.000` and the earlier
  vacuously-successful heredoc, but the mechanism is new and mechanical rather
  than cognitive: **`&&` means "if the previous command exited zero", and a
  `print()` of a failed assertion exits zero.** A check whose result is a
  *printed string* rather than a *non-zero exit* cannot gate anything, however
  clearly it is worded.

  Two fixes, and the second is the one that scales. Make the check exit non-zero
  — `assert`, or `grep -q` whose status `&&` actually reads. And **never put a
  write in the same invocation as the check that is supposed to authorise it**:
  read the output, then decide. The whole point of verifying is to have a moment
  where the answer could change what happens next, and a chained command deletes
  that moment while keeping its appearance.

  Third occurrence tonight of a commit message asserting something the commit did
  not contain. The other two were anchors that did not match; this one was an
  anchor that did not match **and said so**.

  **A check that cannot stop the thing it checks is not a check.** The `&&`
  chaining is one way to strip a verification's authority; `[IsalHG-Fable]`
  named three more, and they are the same defect wearing different clothes:
  printing a result nobody consumes; computing a condition without asserting it;
  and writing an acceptance criterion whose verification needs the very artefact
  it was meant to replace — which is the unfalsifiable instrumentation constraint
  that had to be designed away in T-KBw, two hours earlier, by the same author.

  All four keep the *appearance* of verification and none keep the moment where
  the answer could change what happens next. So "verify before you commit" is not
  the rule. **The rule is that the verification must hold the write hostage**, and
  of the two fixes it is the second that generalises — make the check exit
  non-zero, *and never put the write in the same invocation as the check meant to
  authorise it* — because an exit code only helps if something is waiting on it.

  **Test a proposed mechanism before adopting it; a cheap test can refute a
  plausible story and solve a different one in the same pass.** The six-arm
  discrepancy table looked like it ordered inversely with each arm's per-pair
  work, which would have meant one shared change (a faster matrix loop) rather
  than per-arm re-runs. One arithmetic pass killed it: `bipartite_ged_path` and
  `nauty_cert` have the same old per-pair cost to within 6 % — 5.741e-05 against
  5.433e-05 — and moved by **1.0× and 35.7×**. No single shared change gives
  both.

  The same pass *solved* a different row. NetLSD's old per-pair cost
  (2.724e-03 s) equals the current run's per-**item** descriptor cost
  (2.697e-03 s) to a **ratio of 1.010**: the old run computed one full descriptor
  per pair where the new one computes `N` and reuses them. An `N²` → `N` change,
  which predicts a speedup of order `N` — 662× observed at `N = 1,000` — and
  explains the flip from *censored* to completing. That is a **mechanism with an
  arithmetic identity behind it**, not a story that fits; the difference is that
  it made a numerical prediction which could have failed.

  **And an account that explains the extremes and skips the middle is the one a
  reader tests first.** `degree_seq_l1`'s 3.4× sat between "stable" and "moved"
  and had no home in the first diagnosis — not because it was hard, but because
  the two dramatic rows had absorbed the attention. A residual category of one is
  a category.

  **A supporting measurement must come from the claim's own population, and
  putting one from a different population next to it is an assertion whether or
  not a qualifier is attached.** Discussing why the `wd50k66` matrix costs what it
  does, the text quoted word lengths of **3,886 tokens and 11,692 bytes** — with
  "at `m = 160`" written right there — when `wd50k66`'s members have median
  `m = 5`. The label was correct and useless: a careful reader took the two
  numbers as the lengths entering the matrix and derived, correctly from them,
  that the measured per-pair time was five orders of magnitude too fast to be
  doing the work. The anomaly was real arithmetic on figures that did not belong
  to the corpus under discussion.

  Measured on `wd50k66` itself the lengths are **13.8 tokens** (mean) for the
  ordered walk and **159.7 bytes** for the certificate, and the arithmetic is
  ordinary: 3.0e-09 s/pair as a floor against 1.2e-07 measured, overhead
  dominating on strings this short. **Nothing was wrong except which population
  the supporting numbers came from** — the fifth distinct appearance of a correct
  operation on the wrong object, and the first where the wrong object was
  supplied *to a reader* rather than to a script.

  So the rule is not "label the population"; that was done. It is that a number
  offered in support of a claim must be **from** the claim's population, and a
  figure from elsewhere belongs in a different paragraph or not at all.

  **And the measurement disconfirmed the mechanism it was fetched to check.**
  Counted in bytes against tokens the certificate is 11.5× the walk's length —
  the confounded ratio, and very likely the source of a "12–30 × longer" claim
  elsewhere in the docs. But **400 of 400 certificates have a length divisible by
  4**: it is a sequence of 4-byte integers, so its natural symbol count is
  `bytes/4`, and in natural units the ratio is **2.9×**. The measured pair-phase
  time ratio is **24.7×**, which 2.9× of length cannot produce under any cost
  model. "Its strings are longer" was not merely unestablished; **it is false as
  an explanation**, and it would have been adopted by anyone who fixed the units
  and stopped there. Fixing a confound is not the same as testing the claim the
  confound was hiding.

  **Extra scrutiny for numbers that flatter us is worthless if it only runs one
  way.** Having spent the night applying that rule, the author then accepted —
  and committed — a reversal *against* our own representation ("the
  row-tokenised certificate is 4.5× faster than the Isal word") drawn from
  comparing a bare `cdist` on precomputed fingerprints against a full `matrix()`
  call. Different operations. The like-for-like table **four lines above it in
  the same section** already said 1.09×, i.e. parity, and the arithmetic
  reconciles: the certificate figure matches its own `cdist` entry to 4 %, the
  walk figure is 5× off because `matrix()` does work a bare `cdist` does not.

  A self-damaging number felt like evidence of rigour and so was not checked
  against the table it contradicted. **A claim against your own side is still a
  claim, and the direction it points has no bearing on whether the two things
  compared are the same kind of thing.** Caught by `[IsalHG-Fable]`, who pressed
  the rule symmetrically and was right to.

  The practical form: **when two measurements of the same pair of objects
  disagree, one of them is not measuring what it appears to — find which before
  choosing between them**, and the arithmetic usually says which (here, per-pair
  seconds reconciling with one entry and not the other). Neither "it is more
  recent" nor "it is less convenient for us" is a reason.

  What the conclusion actually needed was **parity**, which both like-for-like
  readings support. The claim it retires — a speed advantage over the certificate
  — was already forbidden by L17, and a retraction does not require a reversal to
  do its work.

  **The freeze rule earned its second save in one session, and again by luck.**
  RQ7's reading was recorded against a live tree while a **second** array —
  2271961, tasks 28–73, held behind 2271960 on a dependency — was writing to the
  same root. It rewrote **66 files** after the reading. Re-reading over its output
  moved **no** published figure: arm completeness, every collection's yield, every
  N-scaling cell identical. Nothing was lost, exactly as with tail600, and for
  exactly the same reason — the re-run agreed.

  Twice in one session is not a coincidence, it is the default state of a
  campaign: **jobs queued behind other jobs write to the same roots, so any tree
  a campaign is still running against is live by default.** The tell is cheap and
  was available both times — `sacct` shows a dependent array, and a newest-mtime
  beside the file count shows writes after the read. The rows are now frozen at
  `results/frozen/rq7_envelope_2271960_reading/`, 382 files, read-only.

  **And a cross-machine comparison slipped in under the same argument.** An
  objection that `matrix()` could not be recomputing its fingerprints rested on
  the campaign's 0.600 ms per member against a local `matrix()` call of 0.0236 s.
  On *this* machine canonicalisation is **0.045 ms** — a **13×** machine gap — so
  400 fingerprints cost 0.018 s and fit inside the call, which measurement
  confirms at **101.9 % accounted**. The attribution was right and the exclusion
  was the error.

  Both parties had spent the session catching exactly this shape in each other:
  a correct operation on quantities from two different populations. So the rule
  wants its widest statement: **before comparing two numbers, ask what produced
  each one — not only which corpus, but which machine, which code path, and which
  operation.** Any of the four differing is enough to make the comparison
  meaningless, and none of them is visible in the numbers themselves.

  **The instance was first filed under the wrong axis, which is its own lesson.**
  It was recorded as "the first where the two populations were *hardware*". They
  were not, mostly. Decomposed once the per-member medians existed:

  | | |
  |---|---|
  | cluster canon-loop vs local canon-loop (machine, same path) | **2.32×** |
  | cluster yield-path vs cluster canon-loop (path, same machine) | **6.29×** |
  | product | 14.6×, against the ~13× observed |

  So the gap was **mostly code path and about a fifth machine** — the yield figure
  carries a forked budget guard per member and the canon loop does not, a 6.3×
  that had been measured two messages earlier and was not applied to the
  diagnosis. "Which code path" was already in the rule; hardware is real at 2.32×
  and is *not* what this instance demonstrates.

  **An instance filed under the wrong axis is a wrong example attached to a right
  rule, and the example is what gets reused.** The cause of the misfiling is
  ordinary and worth naming: the newest and most salient candidate — two
  machines, which had just been discovered — was accepted without decomposing a
  gap that had two factors available and measured. A multiplicative gap should be
  factored before it is attributed, for the same reason a marginal should be
  joined before it is believed. (Caught by `[IsalHG-Fable]`, against its own
  error's filing.)

  **The launcher pattern is not the defect; a recovery sweep without a working
  skip is.** Every RQ launcher submits a recovery sweep behind
  `--dependency=afterany`, so a second array writing to a root that already has
  results is the *normal* end of a campaign rather than an anomaly. What decides
  whether that is harmless is one thing:

  | experiment | skip | consequence |
  |---|---|---|
  | RQ7 | present (`rq7.py:606`) but **did not prevent the re-run** — see the correction below | at 74/74, **22,939 of 39,204** sweep rows re-ran |
  | tail600 | **absent** | re-ran all 16 shards and overwrote the rows its verdict came from |
  | RQ4 | present but **inert** — checks node-local staging (T-KBq) | re-ran completed work |

  **Correction, 2026-09-11 at terminal.** The RQ7 row above originally read
  *"re-submission is a no-op; 14 recovery tasks changed 0 of 39,204 rows"*. That
  was a **mid-flight sample**. At 74/74 the sweep had re-run **22,939 of 39,204**
  sweep rows and **30,455 of 31,407** yield rows, flipping **66 censoring values**
  — and in one cell it destroyed a measurement outright: `wstar_orbit` at
  `N = 3,988` completed three reps at ~1,735 s in the frozen snapshot and, in the
  live tree, is **censored at the 1 h cap with two reps skipped**. The published
  28.9 min figure and the 1,252× comparison exist **only** in the snapshot.

  So a skip's presence in the source is not evidence it fired, and **a re-run
  observed part-way through is not evidence about the whole**. The claim was made
  from 14 of 74 tasks, which is the same error as reading a rate off a partial
  harvest — committed while writing the lesson against it.

  Three experiments, one pattern, three outcomes. Whether an experiment has a
  skip, and whether it checks the durable root, is what says how alarmed to be —
  and the second half is where RQ4's fails, which is why a skip cannot be taken
  on sight.

  **But that is a post-hoc diagnosis, not a pre-flight licence, and an earlier
  draft of this entry made it one.** A skip prevents a job from *re-running work
  already done*; it does nothing about a job writing rows that are legitimately
  **new**. The counterexample is in this campaign's own record:
  `RQ1_addressing/addressing` held **two campaigns** under different launch tags
  (`c3fb21de`, job 2215137; `47c8a42c`, jobs 2247394+95), and concatenating the
  directory double-counted **904,442 of 2,506,837 `(unit, arm)` rows**. Every one
  of those rows was correct new work, and a skip would have permitted all of it,
  because **a second campaign is not a resumption**.

  So the ordering is unchanged and unconditional: **freeze first, then read.**
  The skip question converts "saved by luck" into "saved by a mechanism" *after*
  you discover you read first and froze second — which was the position twice in
  one session — and that distinction is worth having, but it licenses nothing in
  advance.

  The pre-flight that covers both cases is one question rather than three:
  **has anything been written to this root since the rows I am about to read were
  produced?** A newest-mtime beside the file count answers it, which is the
  convention this lesson file already adopted for progress reporting, and which
  would have surfaced the second array *before* the reading instead of after.
  (Qualification raised by `[IsalHG-Fable]` against this entry's first draft.)

  **And verify per row, not by aggregate, however strong the aggregate looks.**
  The first check that the second array had changed nothing compared *summary
  figures* — arm completeness, per-collection yield, per-N cells — and found them
  identical. That is the marginal-versus-join error wearing a third costume:
  sixty-six rewritten files with identical totals can still carry a moved `secs`,
  a censoring flag that flipped where another flipped back, or a member landing
  in a different `(m, k, aut_bucket)` cell — and the readings that took a whole
  session to get right are precisely the per-cell ones. Redone per row, keyed on
  the identifying columns: **0 of 39,204, 0 of 31,407, 0 of 180**. Same
  conclusion, and for the first time it is entitled to it. (Raised by
  `[IsalHG-Fable]`, who noted the tail600 check *had* been per member and asked
  why this one was not.)

  **A snapshot taken while a job is still running is provenance, not a final
  state.** The freeze was called final while the recovery array stood at 14
  COMPLETED, 1 PENDING, 15 RUNNING. It is a correct and useful artefact — it is
  exactly the rows the published numbers were computed from — but it does not
  license "the campaign says this", and the obligation to re-verify at terminal
  has to be written **into** the artefact, since nobody reading it later will
  know a job was in flight.

  **Of the three ways a re-read can disagree, the dangerous one is the one that
  looks like growth.** A frozen-against-live diff has three outcomes and they are
  not equally alarming:

  | outcome | meaning | why |
  |---|---|---|
  | `differing` > 0 | rows moved | bad, and visible — recompute |
  | **`only-live` > 0** | rows **added** | **worse**, and invisible — the reading was computed on a *subset* |
  | `only-frozen` > 0 | rows vanished | a root problem, not a numbers problem |

  The middle case is the one to name explicitly, because it defeats the guard
  that would otherwise catch it: a completeness check asserting "7,776 per arm"
  **passes** against an expectation that is itself too small, and nothing looks
  wrong anywhere. That is the shape the `RQ1_addressing` double-count had —
  904,442 extra rows that every per-file check accepted, because each file was
  internally correct.

  So a re-read reports all three counts, and `only-live` is never folded into a
  summary line that says "no change".

  **A total divided by `N` is a mean, and on a heavy tail a mean is not a
  statement about a member.** The identity-timing concession was quoted from the
  N-scaling pass as "per member" cost. It is `total / N`: 435.6914 ms × 3,988 is
  exactly the recorded 1,737.537 s canon total. For the arms without a tail that
  is harmless — the walk and both certificate arms agree between mean and median
  to within 15 %. For the orbit-pruned search form the **mean is 622× its own
  median** (79.72 ms against 0.1281 ms; p99 1.41 s, max 6.46 s), so the published
  "**7,420×** a certificate call per member" describes the typical member
  **a thousandfold** wrong; the median ratio is **7.5×**.

  Both statistics are right, for different questions, and the fix is to label
  them rather than choose: **the mean is what an `N`-member corpus costs to
  canonicalise** — the right number for a matrix and for planning a run — **and
  the median is what a member costs**, the right number for a sentence about
  per-member speed. A figure that answers one while being quoted for the other is
  the same defect as a rate quoted against the wrong denominator, which L26
  already covers for rates and did not for central tendency.

  The diagnostic is cheap and general: **for any per-unit figure derived by
  division, print the median beside it.** Where they agree, nothing was hidden;
  where they diverge, the divergence *is* the finding — here it is the tail that
  the whole tail600 experiment exists to characterise, arriving in a summary
  statistic that had flattened it. (Raised by `[IsalHG-Fable]` from the
  arithmetic: 435 ms × N reproducing the matrix total exactly is what gives a
  mean away.)

  **And a ratio between two things that share most of their work should be
  decomposed, not reported as a multiple.** `nauty_cert`, `nauty_cert_rows` and
  `isal_ow_struct` all make the *same* canonical-labelling call and differ only
  afterwards, so "the walk costs 1.77× the certificate" hides that both figures
  are dominated by a call they share. Timing the shared call splits it: on a
  median 0.0155 ms `canonical_ranks`, serialising to bytes adds 0.0016 ms,
  to rows 0.0036 ms, and emitting the Isal walk 0.0194 ms.

  The multiple then becomes a quantity — *the language costs about 0.019 ms on
  top of a canonical-labelling call every arm pays anyway* — which is both
  stronger and more falsifiable, and which stops assuming the denominator's own
  serialisation is negligible. **A multiple against a competitor that does part
  of the same work is a comparison with a shared term that nobody has measured.**

  **A subtraction is only meaningful when the term being subtracted is actually
  shared.** The identity-cost decomposition subtracted a median
  `canonical_ranks` call from every arm, as the work they all pay before
  diverging. Four of them do pay it. `wstar_orbit` does not: it is the
  *oracle-only* cell, taking `autgrp` of the prefix-individualised Levi graph at
  every residual tie and **never a canonical labelling** — which is precisely why
  D-TA2 can sanction orbit pruning as value-preserving while forbidding a
  rank-refined tie set, since the pruned search never consults an order.

  Subtracting anyway produced "+0.3237 ms, 9.06× the shared call", which reads as
  *one canonical labelling plus eight more of them in own work* when the truth is
  **a different nauty entry point invoked an unbounded number of times**. The
  arithmetic succeeded only because both quantities were milliseconds — the same
  failure as comparing tokens to bytes, one level up: **units matching is not the
  same as terms corresponding.**

  The fix costs nothing and touches no other row: leave the decomposition blank
  for that arm, say why, and quote its cost absolutely — median 0.364 ms, 8.1×
  the certificate's — which is an arm-to-arm comparison needing no shared term.
  **A decomposition column must state which arms are in it**, because a blank is
  information and a number that does not belong is not.

  And the check was one grep of the repo's own prose: `isal_engine.py` says
  *"nauty is an automorphism oracle only"* and `orbit_oracle.py` says
  *"Stabiliser orbits … via `pynauty.autgrp`"*. Third time tonight that the code's
  comments answered a question faster than measuring or reasoning would have.

  **Ten of the eleven needed a mechanism; the eleventh needed a reader — and
  that one is the whole case for the predicate pass.** The tempting summary of
  this session is that reading caught nothing and only a grep, a census, a diff,
  an arithmetic identity or a second session ever did. It is very nearly true and
  it is **false in the one place that matters**.

  The exception is the noun. A sentence said our generator's novel samples were
  *knowledge bases*; the truth was that they were **connected** knowledge bases,
  which is a stronger and different claim. The number was right. Its provenance
  was right. Every mechanical check passed, and every one of them would pass
  again — a figure with the wrong noun beside it **sources identically to the
  true one**.

  So the accurate tally is *ten mechanisms and one reader*, and the inaccurate
  one is self-defeating: **the predicate pass is reading**, and a session that
  concludes reading never works has argued away its own last line of defence
  while still carrying eight located-but-unadjudicated figures that nothing else
  can settle. (Correction raised by `[IsalHG-Fable]` against this file's own
  closing claim.)

  The rule that survives, in its exact form: **the mechanical checks are the
  first nine-tenths and reading is the residual — but the residual is the class
  no tool reaches, so it is never the part to skip.** A screen locates; only a
  reader knows whether the word beside the number makes it history or error.

  **An absence is only evidence if the search could have found the thing.** The
  RQ1 deliverable was declared missing on the strength of a search of
  `results/frozen/` — a convention that **postdates that deliverable by three
  days** — with a `*.csv` glob that could not see a `merged/` subdirectory of
  non-csv files. The artefact was exactly where the handoff said. What the search
  established was the **convention's coverage**, not the artefact's existence,
  and the two are not the same statement.

  The same sentence one level up covers the numeric screen: reporting a figure
  "unsourced" when the search never opened the wave notes, `DESIGN.md`,
  `DECISIONS.md` or the tests is a statement about the files consulted. **Every
  negative result carries an implicit "…in what I looked at", and the rule is to
  make that clause explicit and then ask whether it is wide enough.**

  Two cheap habits follow. State the search space in the finding itself — *"no
  pre-freeze value appears in the 44 live documents, excluding X and Y"* rather
  than *"clean"*. And when a convention is introduced, **leave a pointer where the
  convention says to look**, for everything that predates it: the reason RQ1 was
  invisible is that it was frozen before there was a place to record freezing, and
  a one-line pointer costs less than remembering that fact forever.

  **Neither a peer's summary nor a prior session's handoff is a check.** The RQ1
  row reached a planning table through four links — the handoff's sentence, a peer
  repeating it, this file's own table, and then a verification that looked where
  the thing could not be — with **no check in any of them**. A summary is a
  compression written by someone with different context; a handoff is a summary
  that has also aged. Both are leads. (Formulated with `[IsalHG-Fable]`, whose
  link in that chain was the second.)

  **And the artefact most worth protecting was the least protected**, purely
  because the convention arrived after it: RQ1 is the paper's most-cited
  experiment, 19 `prose.md` mentions, and was **483 of 483 files writable** until
  2026-09-11 while two lesser artefacts frozen the same night were read-only. When
  a protective convention is adopted, **sweep what predates it** — the ordering of
  the calendar is not a statement about what deserves protecting.

  **Sweeping what predates the check-authority rule: the RQ1 gate holds.**
  "A check that cannot stop the thing it checks is not a check" was filed after a
  `&&` let a printed `False` through. Every pipeline script in the campaign
  predates it, and the class is invisible by construction — a check without
  authority does not fail loudly, it passes quietly. The first target is the one
  underneath the paper's most-cited deliverable, and the chain was traced end to
  end:

  | link | |
  |---|---|
  | `verify_rq1_join.py` | `if all_problems: … return 1`, and `sys.exit(main())` |
  | `build_rq1_isal_table.sh` | **`set -euo pipefail` at line 35**, before the gate at line 57 |
  | consequence | a failed join aborts **before** the merge, as its comment claims |

  So the RQ1 deliverable was built behind a gate with real authority, and the
  manifest's duplicate audit — zero across five tables — is a second, independent
  guard that also fired. Worth having established *before* 19 fact-base entries
  are built on it rather than after. (Sweep proposed by `[IsalHG-Fable]`.)

  **Where the authority lived is the transferable part.** `set -e` in the shell
  and `return 1` in the Python: **both required, neither visible from the other
  file.** The gate would be worthless if `verify_rq1_join.py` printed "JOIN NOT
  SOUND" and returned 0, and equally worthless if the shell lacked `set -e` — and
  each file reads as correct on its own in either case. **A check whose authority
  is split across files cannot be verified by reading either of them**, which is
  why the fix is *tracing* and not inspection, and why the `&&` failure looked
  fine from where it was written too.

  **Gates and reports are different things and want different treatment.** The
  first version of this sweep asked all five remaining scripts for exit codes,
  which is the wrong question for three of them (raised by `[IsalHG-Fable]`, who
  had set the sweep going):

  | kind | what can go wrong | what to do |
  |---|---|---|
  | **gate** — must stop a pipeline | its failure path is not wired | **trace the authority end to end**, every link, before anything rests on the output |
  | **report** — a human reads the number | it computed the *wrong quantity* | **verify the computation**: re-derive, cross-check against a second source, pin as a regression |

  `rq1_extra_checks` is a *report* — its common-set output is what D-ART5's
  rationale quotes (7,013/7,013 words, 130,788/130,788 units, 5,174/5,174 pairs)
  and nothing downstream was gated on it. An exit code would have changed nothing
  there, and its real failure mode is the marginal-versus-join class.
  `rq3_consensus_forensics` and `rq7_envelope_reading` are reports too, and have
  had the second treatment repeatedly — mostly by someone finding they computed
  something *adjacent* to what was asked. `corpus_figure_screen` and
  `rq6_reach1_rederivation_check` are closer to gates and are owed the first.

  **A sweep pointed at the wrong property returns "clean" about something that
  does not matter**, which is the negative-result clause once more: the answer
  would have been true and irrelevant. Choosing the property is the part of a
  sweep that cannot be mechanised.

  **So the property belongs inside the implicit clause, next to the search
  space.** If every negative result carries an unstated *"…in what I looked at"*,
  then **what I looked *for*** sits in that clause as much as **where I looked**.
  The two rules are one, and the statable form of a clean sweep names both:

  > not *"no stale values in 44 documents"* — but *"no integer ≥ 100, by
  > digit-string match after whitespace flattening, sits within 6 % of an obtained
  > census value without equalling it, across 44 live documents, excluding X and
  > Y."*

  The first is a claim. The second is a claim **a reader can find too narrow** —
  which is exactly what happened when the first version of that screen searched
  *built* values and therefore could not, by construction, detect staleness. Put
  that way the unmechanisable part is visible **in the result**, at the moment
  someone uses the number, rather than in a docstring nobody opens then.
  `corpus_figure_screen.py` now prints its claim in that form instead of the word
  "clean". (Formulated by `[IsalHG-Fable]`.)

  **And one class of false negative closed rather than caught a third time.**
  Line breaks defeated prose matching twice — a quoted-forms table missed "one
  time in two" and "one in 578" because the prose wrapped them, and an edit
  verification returned a **false zero** across a line break. Both were noticed
  only because a count failed to match, which is luck. Any tool searching prose
  for a phrase now flattens whitespace first, so a wrapped occurrence and an
  unwrapped one are the same string. It costs one line and it is cheaper than
  catching the same defect a third time.

  **The sweep's own limit, stated so it is not over-read.** *Counting* `sys.exit`
  and `return 1` shows a failure path **exists**, not that the **relevant** one is
  wired to it — a screen, not an audit. Only the RQ1 chain was traced link by
  link.

  **A column-diff must count every differing column, never the first.** The check
  written to be decisive about whether a frozen snapshot still matched the live
  tree `break`-ed out of its column loop on the first mismatch. `secs` precedes
  `censored` in the row schema, so it reported *"only `secs` differs"* — a
  timing-only change, reassuring and wrong — while **66 censoring flips** sat one
  column further along, invisible.

  The bug is one word. What it cost was the correct reading of the one check the
  whole freeze convention exists to support, and it survived because *"only
  timings differ"* is exactly the answer one hopes for. **An early exit in a
  comparison is a silent filter on what the comparison can find**, and it filters
  in the direction of agreement, because the columns that differ most often are
  the ones that differ most harmlessly.
