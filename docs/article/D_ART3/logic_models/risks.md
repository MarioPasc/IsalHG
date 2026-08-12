# Risks — the honest register

*Read before writing any idea file. Every item here is a claim that could sink
the logic program in review; each is stated with its resolution or its
measurement.*

---

## 1. The distance mismatch — the biggest one

**All three PI ideas are written in `d_SED` (iso-invariant symmetric difference
of ground facts). We compute `d_I`. They are not the same distance.**

Measured: Spearman ρ = 0.622 against exact `HGED` on the E1′ mini-corpus
(N = 6,921 pairs); an unconditional but very loose envelope
`d_I ≤ m(1+kn)·HGED`; and a proof-backed argument that **no bi-Lipschitz
relation to an edit distance is achievable by any complete invariant**. So
`argmin d_I` ≠ `argmin d_SED`, and "the closest KB" means something different
under each.

**Three honest resolutions. Do (c).**

- **(a) Redefine the operator by our distance.** Declare `d_I` the well-defined,
  iso-invariant, **polynomial-time** distance criterion and study repair/median
  under it. This is legitimate — Katsuno–Mendelzon explicitly parameterize
  belief-change operators by a distance, so a new tractable distance defines a
  new operator. *Cost:* a belief-revision reviewer will ask what `d_I`-minimality
  *means*, and the honest answer is that it is a **constructive** minimality
  (fewest edits to the construction program) rather than a **semantic** one
  (fewest changed facts). That answer is defensible but it is not free.
- **(b) Use `d_I` as a filter inside an exact `d_SED` search.** The envelope
  gives a certified lower bound `HGED ≥ d_I / (m(1+kn))`, so candidates with
  large `d_I` can be pruned without an oracle call. *Expected to be useless* —
  the constant is enormous, so the predicate almost never fires. Measure it
  (P5), report the negative, move on.
- **(c) Compute both and report the gap.** On instances where exact `d_SED` /
  `HGED` is computable, report the `d_I`-optimal solution *and* the true
  fact-minimal one, and measure the suboptimality:
  *"replacing the NP-hard fact distance with the polynomial-time `d_I` costs
  X % suboptimality on these benchmarks."*
  **This is the right answer.** It is a TKDE-shaped result (approximation
  quality of a cheap surrogate for an intractable objective), it turns the
  ρ = 0.622 measurement from a discussion footnote into an operational number,
  and it is honest in both directions. The exact oracle already exists.

**Consequence for the idea files.** No idea file may write "the closest KB"
without saying *closest in which distance*, and each must state which resolution
it adopts.

**A sharper form of the mismatch, specific to P-MEDIAN (verified 2026-08-12).**
The per-atom majority-vote characterization in `src/idea3.txt` — *once the
alignments are fixed, the optimum is per-atom majority vote* — is a statement
about `d_SED` and **does not transfer to `d_I`**: Levenshtein alignment is
global, token positions interact through VM state, and a position-wise "token
majority" does not in general decode to a valid canonical string. **The
`d_I`-median therefore has no closed form and must be searched.** Consequence
for implementation: a beam search over words, with re-canonicalization at every
accepted step, because the decoded median word is generally **non-canonical**
(`s* ≠ w*_c(S2H(s*))`), so the objective must be evaluated on
`w*_c(S2H(s*))` and not on bare `d_Lev(s*, t_i)`. This is solvable at one `w*_c`
call per step but must be designed in from the start.

## 2. Feasibility of ball enumeration for P-REPAIR / P-ENTAIL

> **⚠ CORRECTED 2026-08-12. The original text of this section was wrong, and
> both idea-agent analyses inherited the error — `ideas/idea1_repair.md` and
> `ideas/idea2_entailment.md` both treat F0 infeasibility as established. It is
> not. Their feasibility verdicts, and only those, must be re-read against this
> section; their other findings stand.**

**The original (incorrect) argument.** A one-fact edit is `1 + a` structural
elements under E2, and one structural edit moves `w*_c` by ≈30–50 % of the
string, therefore a one-fact repair is a large fraction of the string away and
ball enumeration at feasible radii cannot find it.

**Why it is wrong.** It conflates `d_I` with `d_amb` (`vocabulary.md` §2.1).
The ≈30–50 % figure is the distance between **canonical forms**. Ball
enumeration does not travel between canonical forms: it edits `w*_c(E(K))` and
decodes, so it may reach the target through a **non-canonical** word. Inserting a
single `C[le;i]` token where the pointers already sit gives `d_amb = 1` for a
one-fact extension while `d_I` between the canonical forms remains ≈0.4·|w| —
consistent, because `w` and `w*_c(E(K'))` are different words for the same
structure.

**What actually governs feasibility: pointer displacement.** A construction
token acts on the current pointer configuration. Facts whose vertices lie near
the pointer trajectory of `w*_c(E(K))` are reachable in `O(1)` tokens; an
arbitrary fact costs `P`/`N` tokens proportional to CDLL displacement. So the
binding question is the **distribution of `d_amb` over one-fact neighbours**,
not the avalanche.

**Gate G-L3 (new, cheap, decisive).** For a sample of structures `K` and their
one-fact neighbours `K'`, compute a **constructive upper bound** on
`d_amb(K,{K'})` — emit the word that inserts the required pointer moves plus the
construction token, and count. No search needed; the bound suffices to decide
feasibility. Report the distribution.
- Median `O(1)`–`O(log n)` ⇒ **ball enumeration is feasible under F0**, and
  P-REPAIR/P-ENTAIL are not gated on the alphabet.
- Median `Θ(n)` ⇒ D3′ is required, and the F4 `FACT` token with **absolute**
  addressing (`encoding.md` §3.1) drives `d_amb` to exactly 1 per fact — which
  is the strongest argument yet for absolute over relative addressing.

**Status.** F0-feasibility for P-REPAIR/P-ENTAIL is **open, pending G-L3**, not
refuted. What survives unchanged from the original concern: `d_I`-*ranking* of
candidate repairs is uninformative under the avalanche, so the search must be
ordered by `d_amb`/cost, never by `d_I` to a target.

## 3. Scale

Under E2, `n' = 1 + |D| + |F|`, against a measured envelope of `n ≈ 24` at
`k = 3`. Our instances will be small (order 6 constants, 16 facts) unless
G-L1 shows that heavy labelling buys a large factor. The PI's hope that these
ideas are "más cerca del mundo real" is true **of the problems** and must not be
claimed **of the instance sizes**. See `scope.md` §3 for the honest framing and
the two mitigations.

## 4. Decidability

For arbitrary FO `ψ`, finite satisfiability is semi-decidable (Trakhtenbrot), so
P-MIN / P-REPAIR / P-ENTAIL are semi-decision procedures. Fix with a cost
ceiling or a decidable fragment (`scope.md` §2). P-MEDIAN is unaffected — no
sentence, no decidability question.

## 5. Competition we should expect to lose to

Stated in advance, per the project's standing contract discipline:

- **MaxSAT / ASP with weak constraints** on P-REPAIR and P-ENTAIL. Propagation
  prunes semantically; we prune only structurally. Expect to lose wall-clock on
  most instances.
- **Kodkod / Alloy, Paradox, Mace4, SEM, cvc5-FMF** on "is there a model" and on
  minimum-*domain* model finding.
- **`nauty` / `bliss` / Traces** on canonicalization and deduplication — faster
  than `w*_c` and equally exact.
- **Hungarian/bipartite GED approximation** on raw distance-matrix throughput
  for P-MEDIAN, if the corpus is large. But note the two things it cannot claim:
  it is not a metric (so the medoid 2-approximation does not transfer), and it
  gives an upper bound rather than an exact value.

**What must survive every one of those losses:** exactness and
iso-invariance-by-construction, the metric guarantee and what it licenses, the
decodable ambient space (no reconstruction step in the generalized median), and
the questions that are only askable in a metric space of structures.

## 6. Novelty is not yet verified

The claims that these problem formulations are new — the combined
`|D| + Σ|P_i|` objective for P-MIN, and *any* prior metric on isomorphism
classes of finite structures used this way — come from chat-level surveys, not
from a verified `literature-search` pass. **Task L-LIT blocks any novelty claim
entering `RELATED_WORK.md`.** Its highest-value query is whether anyone has
already put a *tractable* metric on finite relational structures modulo
isomorphism; if someone has, the framing changes.

Specific things to check, beyond the obvious:
- generalized median graph under a **canonical-string** distance (has anyone
  done median-string-as-median-graph?);
- belief merging with a **non-rigid** vocabulary;
- repair/update literature where the domain may grow *and* the search is
  iso-invariant.

## 7. Two-paper risk

Four problems, an alphabet redesign, and a real-data program is more than one
TKDE submission. `scope.md` §4 proposes the split. The decision is the PI's and
belongs on the August agenda.
