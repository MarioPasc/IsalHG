# D-ART3 draft — rescope: from "characterize → exploit" to "enumerate, deduplicate, decode, navigate"

**Status:** DRAFT, pending PI. **Revision v5, 2026-08-12** — supersedes the v4
draft below after the PI's feedback (venue, the first-order-logic application,
the indispensability criterion for applications, the ARB/Benson corpora). The
v4 analysis is retained verbatim in §§1–7 because it still stands: its
diagnosis, its constraint on any reframe, and its two proof obligations are
carried into v5 unchanged. What v5 changes is the **destination**.

Originally written 2026-08-09 at the PI's request after the T-M4b close ("maybe
we need to re-think the paper as a more theoretical paper"). Nothing in
`docs/article/{PROPOSAL,theoretical,empirical}` changes until this is ratified;
the v3 scope (D-ART2) remains the active scope. Companion evidence:
`T-M4/CLOSED/T-M4b.md`, `results/T-M4b/`, D-M4b.

> **⇒ The full v5 proposal lives in [`../D_ART3/`](../D_ART3/)** — nine files
> mirroring the article's own documents (`proposal.md`, `venue.md`, `theory.md`,
> `logic_models/`, `applications.md`, `data.md`, `geometry.md`,
> `competitors.md`, hub in `README.md`). This file remains the decision record;
> that folder is the scope.

---

## 0. Revision v5 — the PI's input and what it changes

Four inputs arrived together on 2026-08-12.

1. **Venue: IEEE TKDE** (ISSN 1041-4347), not *Information Sciences*. This
   settles §6 below, which had deferred the venue question. It also changes what
   the paper must deliver: an algorithm, a scalability envelope, real corpora,
   and baselines from the data-engineering community rather than from ML.
   → `../D_ART3/venue.md`
2. **A problem where isomorphism-invariance is the whole job.** Every finite
   model of a first-order formula is a labelled hypergraph (constants →
   vertices, ground facts → predicate-labelled hyperedges); search exhaustively
   for the **smallest countermodel** of a formula, minimizing domain size plus
   the number of true ground atoms. The PI's rationale is the IsalSR precedent:
   our advantage is most visible under *exhaustive*, not random, search.
   → `../D_ART3/logic_models/`
3. **The criterion for what counts as an application.** *"Hay que buscar
   aplicaciones en las que sea imprescindible o muy ventajoso lo que diferencia
   IsalHG […] Lo ideal serían problemas en los que enumerar los vecinos de un
   hipergrafo, o hallar el camino más corto entre dos hipergrafos, sea muy
   relevante."* Supervised/unsupervised leadership is explicitly not the goal —
   which is exactly what T-M4b measured. Shortest path is to be **kept and
   promoted**, not abandoned. → `../D_ART3/applications.md`
4. **Real corpora.** The ARB/Benson collection (28 datasets). The v3 objection
   ("one giant network, no instances") does not survive: the v5 workloads need
   many *small* hypergraphs, and Qin et al. (ICDE 2023) — whose HGED definition
   this article already adopts verbatim — derive ego-networks from these very
   datasets, a derivation already implemented in-repo
   (`core/sparse_hypergraph.py::ego_network`, `datasets/arb_benson.py`).
   → `../D_ART3/data.md`

**Resulting thesis (v5).** The three properties the representation was actually
built for — completeness, closure/decodability, constructivity — make the *space
of hypergraphs* enumerable, deduplicable, decodable and navigable. The paper
proves what makes that well defined, measures the geometry that governs how well
it behaves, and demonstrates it on exhaustive minimal-countermodel search and on
real hypergraph corpora. The v4 diagnosis is unchanged and becomes the paper's
*boundary statement* rather than its destination: small-perturbation task
geometry is where this encoding is weak, and §2 below still governs how that may
honestly be said.

**What v5 keeps from v4.** The constraint of §2 (the culprit is the encoding
format, not completeness), P1 (ambient decodability), P2 (drift/avalanche — now
the justification for cost-ordered rather than distance-guided search), the
"nothing is re-run" discipline, and the risk analysis of §7. **What v5 adds:**
P3 (cost accounting), P5 (the envelope as a candidate filtering bound, to be
measured before any claim), purpose-specific competitor sets, and the ARB data
program.

### Revision v5.1, same day — two author corrections

1. **The alphabet is not fixed.** The v5.0 text constrained the FOL encodings to
   the existing `Σ_HG` "so Theorem A transfers unchanged". That constraint is
   lifted. D-TA2 froze *which tie-complete lex-min* is canonical **for `Σ_HG`**;
   it did not decide that `Σ_HG` is the only alphabet. A purpose-built `Σ_FO` —
   options F1 (ordered `V`/`C`), F2 (incidence labels), F3 (sorts), **F4 (a
   native `FACT` token)** — is a first-class option, and the geometry pipeline
   can be re-run on it because the harness is representation-agnostic. F4 is the
   recommendation, as a **conservative extension** that degenerates to today's
   `Σ_HG` on the unlabelled hypergraph fragment: every frozen result stays true
   of the fragment, Theorem A extends rather than restarts (its proof is
   alphabet-parametric), and the change becomes a *measurement* — does aligning
   the token with the unit of semantic change reduce the ≈30–50 % single-edit
   response? This becomes decision **D3′**, replacing D3, and it is now the
   largest technical decision in the rescope. Detail: `../D_ART3/logic_models/`
   §3.2.
2. **Deduplication is not a claim.** The v5.0 spine put isomorph-free
   enumeration first. That is a losing frame: Levi-`{nauty, bliss, Traces}`
   deduplicate faster than `w*_c` and with identical exactness, and
   `nauty`-based canonical augmentation is the state of the art for isomorph-free
   generation. Deduplication is demoted to a **correctness precondition** with
   nauty named in the paper as a faster pluggable key, and the pillars are
   rebuilt on what a certificate does not supply. The operative formulation:
   **a certificate is not a space** — nauty identifies a point, while `Σ_HG`
   supplies a ground set, a move operator that never leaves the space, a native
   cost order, a total decoder and a metric, so a *search* can run inside it.
   Applications become C1 (the search-space framework), C2 (minimal
   countermodels **and the geometry of model space** — distances between
   countermodels, radius-`r` neighbourhoods, repair paths, diversity), C3
   (navigation, promoted), C4 (black-box structural optimization, where both a
   solver and nauty are inapplicable) and C5 (real data, with the
   completeness-price measurement reported as a *tie* with nauty). New
   obligation **P6** (move-operator closure, ball enumerability, reachability)
   replaces P4 on the critical path; P4 is demoted to a borrowed framework. The
   geometry gains one new invariant — **ball growth and its collapse onto
   isomorphism classes** — which is the branching factor of the search and the
   tightest geometry→application link the article has had.

---

## v4 draft (retained; §§1–8 below)

## 1. Why the question is live

T-M4b repaired the size confound and measured the honest outcome: on the
size-controlled corpus both naive baselines sit at exactly the structural
floor, and the purely structural task ranking is nauty-Levi edit (ARI up to
0.614 [0.571, 0.657]) > HPD > NetLSD > IsalHG (ARI 0.016–0.028, above the
floor at p ≤ 7.5 × 10⁻³ but below every leader at p ≤ 0.028). The mechanism
is measured, not conjectured: a single edit — incidence swap or Qin op,
indistinguishably — moves `w*_c` by ≈30–50 % of the string on every
unanchored substrate probed. Under v3, A2/A3 were the "exploit" pillar; as
measured, they are a limit result. The v3 skeleton absorbs this honestly
(that is what T-M4b folded into the prose), but the paper's center of mass
has objectively moved from *usefulness* toward *characterization and
mechanism*. The question is whether to move the framing with it.

## 2. The constraint on any theoretical reframe (read this first)

**The measured culprit is the encoding, not completeness.** The A2/A3 leader,
nauty-Levi edit, is *itself a complete isomorphism invariant*: its canonical
adjacency serialization localizes the same edits that the instruction
string's positional coupling amplifies. A reframe built on "completeness
necessarily destroys task geometry" would be refuted by our own tables. What
the data supports is sharper:

- *Worst-case, any complete invariant:* no bi-Lipschitz relation to HGED
  (literature + our drift/avalanche mechanisms) — unchanged from v3's
  discussion.
- *Measured, our encoding specifically:* the sequential instruction format —
  pointer moves are relative, ties resolve globally — has single-edit
  response Θ(string) in practice on unanchored substrates, while an
  adjacency-format complete invariant does not pay this on the same corpus.

The defensible theoretical thesis is therefore about **encoding format**: what
a *program-like, closed-alphabet* canonical form buys (decodability,
compactness, an ambient space made of hypergraphs) and what it costs (local
instability), with both sides proved where we can and measured where we
cannot.

## 3. Narrative spine v4 (deltas from v3 marked)

*[Superseded at v5 — the current spine is `../D_ART3/proposal.md` §2. The v4
spine below is retained as the record; its steps 0–2 survive unchanged, step 3
becomes the geometry's search-heuristic consumer, step 4 is replaced by the
enumeration engine, and step 5 is promoted to a pillar.]*

0. **Foundation** — Theorem A + Corollary A. *(unchanged)*
1. **Compactness** — bits, r > 1 on 320/320 legacy + 100 % of Stratum C
   items. *(unchanged; Stratum C rows strengthen it)*
2. **Geometry** — the six invariants, now measured on the controlled corpus
   (ν falling with cell size; censored D̂ read as concentration).
   *(unchanged role; content already updated at T-M4b)*
3. **Stability of the encoding** — *(NEW theory section, promoted from the
   discussion)*: Proposition P2 (drift/avalanche lower bound, §5 below), the
   measured ≈30–50 % universal single-edit response, and the measured
   encoding-format contrast (adjacency canonical form localizes; instruction
   canonical form does not). This section *predicts* §4's outcome before it
   is shown.
4. **Tasks under control — the instrument** — *(recast from "exploit")*: the
   size-controlled corpus construction + the `size_l1` falsifier as a
   reusable benchmark methodology (any hypergraph-representation comparison
   can run it; a naive row above floor falsifies the corpus, one line of
   code); the S=27 tables; the ranking read through §3. The pre-registered
   contract and its two-way discharge are the section's spine.
5. **Capability** — *(elevated)*: Proposition P1 (ambient decodability, §4
   below) + the measured A4 results; the differentiator no vector or
   adjacency serialization shares, now theory-backed rather than
   demonstration-only.
6. **Discussion** — envelope + impossibility + E1' (ρ = 0.622) + the
   corrected frontier statement (completeness is not the culprit; format is)
   + future work: whether a stable-yet-decodable canonical format exists is
   an open problem this paper sharpens.

Order rationale: what is proved (0), what is short (1), what is measured
(2), what is proved-and-measured about change (3), what the theory predicts
happening on tasks (4), what only this representation can do (5), what
remains open (6). Every v3 asset survives; nothing is re-run.

## 4. Proof obligation P1 — ambient decodability (proposition, low risk)

**Statement (draft).** For every word `w ∈ Σ_HG(k)*`, `S2H(w)` is a
well-defined **connected** hypergraph. Consequently the token-level
Levenshtein ball around any canonical string contains only decodable
connected objects, and every intermediate string on an alignment path
between two canonical strings decodes — including the non-canonical
interior (measured: 62/62 intermediates decode and are connected; 52/62 are
non-canonical).

**Sketch.** Induction over the prefix of `w` on the VM invariant "the primal
graph of `H_t` is connected". Base: the initial state is a single vertex
(connected by convention). Step: `V_{i,j}` creates an edge over `i ≥ 1`
pointer-resolved *existing* vertices and `j` fresh vertices, so every fresh
vertex enters inside an edge containing an existing vertex — connectivity is
preserved; `C_i` adds an edge over existing vertices (or no-ops);
`P_i`/`N_i`/`W` do not touch `H`. The first edge-creating token necessarily
covers the initial vertex (it is the only vertex until a `V` fires), closing
the only isolated-vertex case; a word with no `V`/`C` decodes to the
single-vertex hypergraph. The closed alphabet gives totality (the S2H
interpreter never rejects — invariant 2 of the codebase); the constraint
`i ≥ 1` gives connectivity. Formalization cost: low; the argument is the
one already stated informally in `empirical/applications.md` §A4, and the
62/62 measurement becomes its illustration, pinned by a unit test.

**Why it matters for v4.** It converts A4's differentiator from a
demonstration into a property of the alphabet: `ℝ^d` interiors are not
hypergraphs and adjacency-string interiors are not valid serializations,
but every point of our ambient space is a connected hypergraph.

## 5. Proof obligation P2 — drift/avalanche lower bound (proposition, moderate risk)

**Statement (draft).** There exists a family of connected 3-uniform
hypergraphs `{H_n}` (with `|w*_c(H_n)| = Θ(n)`) and single incidence swaps
`σ_n` such that
`d_Lev(w*_c(H_n), w*_c(σ_n H_n)) = Ω(|w*_c(H_n)|)`.
That is: the tie-complete instruction encoding admits no local stability —
one degree-preserving edit can cost a constant fraction of the string.

**Sketch and status.** The mechanism analysis exists in
`theoretical/stability.md` §3: pointer-run **drift** is Θ(n) in adversarial
layouts, and tie/seed **avalanche** re-anchors the traversal near
symmetric inputs. The candidate construction is a long anchored path (the
seed cascade fixes the traversal origin at a decorated end) whose swap moves
the decoration to the opposite end: the canonical traversal reverses
orientation, and the pointer offsets along the run differ position-by-
position between the two encodings. **The crux — the genuinely new proof
work — is the Levenshtein step:** displacement arguments bound positional
difference, but an alignment may re-synchronize, so the proof must show that
*any* alignment leaves Ω(n) token mismatches. The intended argument is
token-content divergence along the runs (the `P_i`-run lengths and `V`
operand indices form different sequences under the reversed traversal, so no
window of one string matches a window of the other beyond O(1) length).
Fallback if the Levenshtein step resists: state the bound for the
edit-distance-with-moves-free alignment (still meaningful) or as a
displacement theorem plus the measured Levenshtein universality — weaker,
honest, and still section-carrying. The pinned family becomes a frozen unit
test either way (same discipline as the `w*_c` pins).

**Scope honesty.** P2 is a worst-case statement. The measured ≈30–50 %
response across random substrates is evidence the phenomenon is generic; an
average-case theorem over fixed-degree ensembles is flagged as open, not
promised.

## 6. What is explicitly not proposed

- ~~**No venue change is decided here.**~~ **[SUPERSEDED at v5, 2026-08-12 — the
  PI has decided the venue: IEEE TKDE.]** The v4 reasoning below is retained as
  the record of why the question was left open. Note that the v4 argument
  ("Theorem A + two propositions is thin payload for a theory venue; the
  differentiating asset is the measured honesty chain, which an applied venue
  values") is *consistent* with TKDE and in fact points at it: TKDE wants an
  algorithm with an envelope and real data, which is what v5 supplies. Analysis:
  `../D_ART3/venue.md`.
  > Information Sciences remains the
  > target under v4 (characterization + methodology + honest benchmark reads
  > well there). Re-targeting to a theory venue becomes a separate decision
  > only if P2 lands strongly — Theorem A + two propositions alone are thin
  > payload for TPAMI-class theory, and the paper's differentiating asset is
  > its measured honesty chain, which an applied venue values.
- No new experiments; no changes to the competitor set, the E1'/bits frozen
  results, the corpus, or T-M5m's scope.
- No claim that IsalHG's task scores improve under any reframe. They are
  what they are; v4 explains them instead of apologizing for them.

## 7. Risks and the fallback

(a) **P2 stalls at the Levenshtein step** → fallback in §5; v3's framing
with T-M4b's honest tables remains fully defensible, so the downside is
bounded. (b) **Reviewer reads "your method loses its own benchmark"** → the
winner is the contrast baseline we introduced, on a corpus we built to be
falsifiable, under a contract we pre-registered; v4 makes that the
methodological point. (c) **Scope creep** → P1 and P2 are the only new
obligations; both have their evidence and mechanism analysis already in the
tree.

## 8. If ratified — execution plan (ledger-ready, not yet filed)

*[Superseded at v5 — the current plan is `../D_ART3/README.md` §7, which adds the
three blocking gates (G-L1, G-D1, G-B1), P3/P4, the enumeration engine and the
two instantiations. Items 1–3 below survive inside it as T-P1, T-P2 and the
prose fold.]*

1. `T-TC1` — P1: proposition + proof + pinned decodability unit test
   (owner: theory track; est. small).
2. `T-TC2` — P2: formalize the §3 drift analysis into the pinned family +
   the Levenshtein argument; frozen witness test (est. the one genuinely
   open proof; time-boxed, with the §5 fallback pre-agreed).
3. `T-M8h` — prose fold v4: PROPOSAL.md spine, geometry.md §6 cross-refs,
   applications.md section reordering, stability.md promotion of the
   mechanism content into the new §3-of-the-paper. No numbers change.
4. D-ART3 recorded as ratified in `DECISIONS.md`; scope docs updated in the
   same session as the fold.

**Recommendation (v4, superseded).** Adopt v4 as scoped here (T3+T2 hybrid:
reframe inside the current skeleton, add the two propositions), decide venue
after T-TC2 resolves. This converts T-M4b's negative result into the paper's
theoretical spine without discarding any measured asset or re-running anything.

---

## 9. Recommendation (v5, current)

Adopt **v5** as scoped in [`../D_ART3/`](../D_ART3/). It keeps everything v4
kept — every measured asset, both propositions, the encoding-format constraint —
and changes only where the paper is aimed: from a limit result about a metric to
a capability result about a *space*. Concretely it (a) answers the PI's
indispensability criterion, since enumeration, exact deduplication and decodable
navigation are things no competing hypergraph representation can do at all;
(b) promotes the shortest-path work the PI asked to keep; (c) supplies a real
data anchor with a community-standard derivation, replacing the failed HIC gate;
and (d) fits TKDE, whose community already owns the objects the paper uses
(HGED — Qin et al., ICDE 2023; constructive canonical forms for mining — gSpan;
metric-space indexing — ACM CSUR 2001).

**Six decisions are needed from the PI** before ledger tasks are filed; they are
listed with recommendations in `../D_ART3/README.md` §5 (flagship vs second
pillar; one paper or two; which FOL encoding is official; the P2 time-box;
whether to retire the HIC exhibit; the A2/A3 disposition).

**Three gates must run before scope is committed** (`../D_ART3/README.md` §7):
G-L1 (`w*_c` cost on encoded models), G-D1 (ARB arity/size feasibility), G-B1
(enumeration ceiling). None is large; all three are blocking, and none of the
v5 claims may be written down before its gate reports.

**The largest honest risk is unchanged in character but different in target:**
the enumeration pillar has mature competitors (nauty-based canonical
augmentation; MACE-style SAT model finders with partial symmetry breaking), and
the expected outcome is that they win on wall-clock. The pre-registered
contracts in `../D_ART3/competitors.md` §§2–3 bind us to report that in whichever
direction it falls, exactly as the corpus contract did at T-M4b — and, as there,
the surviving claim is stated in advance rather than reconstructed afterwards.
