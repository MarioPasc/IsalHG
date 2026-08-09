# D-ART3 draft — theory-forward rescope (v4): from "characterize → exploit" to "characterize → explain → instrument"

**Status:** DRAFT, pending PI. Written 2026-08-09 at the PI's request after the
T-M4b close ("maybe we need to re-think the paper as a more theoretical
paper"). Nothing in `docs/article/{PROPOSAL,theoretical,empirical}` changes
until this is ratified; the v3 scope (D-ART2) remains the active scope.
Companion evidence: `T-M4/CLOSED/T-M4b.md`, `results/T-M4b/`, D-M4b.

---

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

- **No venue change is decided here.** Information Sciences remains the
  target under v4 (characterization + methodology + honest benchmark reads
  well there). Re-targeting to a theory venue becomes a separate decision
  only if P2 lands strongly — Theorem A + two propositions alone are thin
  payload for TPAMI-class theory, and the paper's differentiating asset is
  its measured honesty chain, which an applied venue values.
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

**Recommendation.** Adopt v4 as scoped here (T3+T2 hybrid: reframe inside
the current skeleton, add the two propositions), decide venue after T-TC2
resolves. This converts T-M4b's negative result into the paper's theoretical
spine without discarding any measured asset or re-running anything.
