# P-REPAIR — nearest model of the axioms

*Source: `src/idea1.txt` (PI idea 1). Status: analysis, pending D3′ decision.*
*Relations: `problems.md` §P-REPAIR; `risks.md` §1–2; `encoding.md` §2–3;
`competitors.md` §2; `data.md` §2–3.*

---

## 1. Problem statement

**Formal setup.** Let `Σ` be a set of first-order sentences (equality-free,
function-free, relational, closed-world; `scope.md` §1). Let `K` be a
knowledge base — a finite set of ground atoms over a finite active domain
`adom(K)` — satisfying `K ⊭ Σ`. The problem is:

> **P-REPAIR.** Find `argmin_{𝔐 ∈ Mod(Σ)} d(K, 𝔐)`, where `Mod(Σ)` is
> the set of finite models of `Σ` and the domain of `𝔐` may grow beyond
> `adom(K)` (by introducing fresh anonymous elements) or shrink below it
> (by removing existing constants).

**Template position** (`problems.md` §0): nearest point of the set `Mod(Σ)`,
with query point `K`. The domain is variable-size, so the search space is
the disjoint union of all finite relational structures over extensions of
`adom(K)`, ordered by the chosen distance.

### 1.1 The metric fork — resolved

`src/idea1.txt` identifies two readings of "distance" once the domain can
vary:

- **(a) Fact-level / active-domain.** `d(K, 𝔐) = |Facts(K) △ Facts(𝔐)|`
  where `Facts` is the set of true ground atoms under the shared active-domain
  naming. A bare element (constant with no facts) simply does not exist.
  Domain shrink = deleting all facts mentioning a constant, which falls out of
  the symmetric difference automatically. This is the Dalal lift restricted to
  active domains: no new cost notion needed.
- **(b) Element-level + fact-level.** Adding or removing a constant is charged
  separately from adding or removing facts. A Boolean `present(e)` predicate
  per constant mediates the charge; pure-existence and cardinality axioms
  constrain `present(·)` directly. This is the cost model that handles
  cardinality-0 constants as first-class objects.

**Which fork does `HGED` instantiate?**
`correlation.md` (HGED definition) quotes Qin et al. (ICDE 2023) Definition 3
verbatim: atomic operations are (i) insert/delete a *cardinality-0* node or
hyperedge; (ii) extend/reduce a hyperedge by one node; (iii) substitute a
label — all at unit cost. Operation (i) explicitly charges the insertion or
deletion of a bare node independently of any hyperedge edits. **`HGED` is
therefore fork (b).** Fork (a) is the restriction of `HGED` to structures
with no bare nodes (cardinality-0 nodes never appear), which is the common
case for plain relational facts but is strictly weaker.

The PI's metric fork is **pre-resolved**: the exact oracle we already own
operates in fork (b), at unit-cost Qin edits. `d_SED` (`vocabulary.md` §2) is
the iso-invariant lift of that model to a metric on isomorphism classes. No
design choice remains on the metric side.

**Which distance is which.** The PI's "closest KB" is `d_SED`. Our algorithm
produces `d_I`-nearest candidates. The relation between them is ρ = 0.622
(Spearman, E1′ mini-corpus, N = 6,921 pairs); no bi-Lipschitz bound is
achievable (`risks.md` §1). The two distances are not the same; §7 below
resolves what to do about it.

**Label family.** Because KB predicates are *labels* on the encoded structure
(unary predicates as node labels, relation names as hyperedge labels), the
relevant member of the `d_I` family is `d_I^Σ`, not the trivial-vocabulary
`d_I^⊥` under which the article's current geometry tables are measured. The
logic program needs its own geometry measurement.

---

## 2. The algorithm in our representation

Under the current encoding E2 (`encoding.md` §1.2, anchored incidence), a KB
`K` is mapped to a labelled hypergraph `E(K)` with:

- `n' = 1 + |adom(K)| + |Facts(K)|` nodes (one anchor, one per constant, one
  per ground atom),
- one hyperedge per argument slot (arity `a` fact → `a` hyperedges of size 2
  linking the fact-node to each argument-node).

The encoded hypergraph `E(K)` has a canonical string `w*_c(E(K))`. The
ball-enumeration algorithm is:

```
r ← 0
incumbent ← None
while no termination:
    for each w in B_r(w*_c(E(K))) ∩ image(w*_c ∘ E):
        𝔐 ← S2H(w)          # decode; total on Σ_HG (P1)
        if 𝔐 ⊨ Σ:
            if incumbent is None or d_SED(K, 𝔐) < d_SED(K, incumbent):
                incumbent ← 𝔐
    if incumbent found: break (or continue to bound fresh elements)
    r ← r + 1
```

**Termination argument.** If the best repair found so far has `d_SED`-cost `C`,
then no repair needs more than `C` genuinely participating fresh elements,
since each fresh element that takes part in the repair contributes at least one
inserted fact, hence at least unit cost. The domain of any competing repair
therefore lies within `adom(K) ∪ {c₁, ..., c_C}`, so the search domain is
bounded by `|adom(K)| + C`. `src/idea1.txt` establishes this bound for
MaxSAT/ILP over the fresh-element pool; it **transfers to ball enumeration
unchanged**, because the radius `r` upper-bounds the total edit budget and
hence the number of active fresh elements. The algorithm is a semi-decision
procedure for arbitrary FO `Σ` (Trakhtenbrot; `scope.md` §2) and a decision
procedure for `d_SED(K, M) ≤ r` under a cost ceiling.

**Membership in `image(w*_c ∘ E)`.** Not every word in `B_r` is in the image
of `w*_c ∘ E`; checking membership requires re-encoding the decoded structure
and verifying the canonical form matches. Under `Σ_HG` this is feasible for
small structures. Under a purpose-built `Σ_FO` the same loop applies
alphabet-parametrically.

---

## 3. The feasibility blocker — honest assessment

### 3.1 The argument in `risks.md` §2

The `risks.md` argument proceeds as follows:

1. Under E2, a single ground fact `R(c₁,...,cₐ)` encodes as `1 + a` structural
   elements (one node for the atom, `a` hyperedges for the argument slots).
2. The measured single-edit `d_I` response on unanchored substrates is
   **≈30–50 % of the string** (avalanche/drift; `docs/article/D_ART3/theory.md`
   P2; quantified in `results/T-M4b/`).
3. Composing: a one-fact repair (cost 1 in `d_SED`) sits at `(1+a) × 30–50 %`
   of the string away in `d_I` — a substantial fraction for any realistic arity.
4. Ball enumeration at radius `r` in `d_I` will therefore **not reach
   a one-fact repair** unless `r` is a large fraction of `|w*_c(E(K))|`, at
   which point the ball contains exponentially many candidates and the search is
   infeasible on those grounds.

**Is the argument correct?** Yes, on the terms stated. Point (2) is a measured
fact on unlabelled random substrates; point (3) is an arithmetic consequence.
The only qualifier is that KB-encoded structures carry heavy labelling (predicate
names, argument-position labels), and `scope.md` §3 notes that heavy labels
strengthen tie-breaking and may shrink the avalanche. However:

- The measured ≈30–50 % figure is from *planted-corpus substrates that already
  carry swap-edit structure*, not from purely structureless random graphs.
  Labelling reduces the *symmetry group*, which is the root cause of avalanche,
  so the direction of the mitigation is correct — but the *magnitude* is
  unmeasured. Gate G-L1 (`logic_models/proposal.md` §5) is precisely the gate
  that measures this.
- Even if labelling halves the response to ≈15–25 %, a one-fact repair still
  sits well beyond any radius where ball enumeration is computationally feasible
  on structures of realistic size.
- The blocker is therefore **real and binding** under `Σ_HG` for any
  semantically meaningful repair (cost measured in `d_SED`). It is not merely a
  quantitative concern about the constant in the exponent.

### 3.2 Is there a route around the blocker without a new alphabet?

One route exists, but it changes the problem:

**Resolution (a): redefine the objective as `d_I`-minimal repair.** Ball
enumeration in `d_I` is feasible by construction — the radius `r` bounds the
search. Every point of `B_r(w*_c(E(K)))` that decodes to a model of `Σ` is a
valid `d_I`-repair candidate. The termination argument of §2 above still applies
because `d_I ≤ m(1+kn) · HGED` (the unconditional envelope) gives a loose
upper bound on domain growth. Claim: "the `d_I`-nearest model of `Σ` to `K`."

**What changes.** The notion of "nearest" is now *constructive minimality*
(fewest edits to the construction program `w*_c`) rather than *semantic
minimality* (fewest changed ground facts). A belief-revision reviewer will ask
what this means; the honest answer is that `d_I`-minimality is a new operator
in the Katsuno–Mendelzon sense — a different, tractable revision operator
defined by a different but well-motivated distance. The operator is
*polynomial-time* (ball enumeration is tractable at small radii; the encoding
and decoding are polynomial); the competing operators all require NP-hard
solvers.

**Assessment.** This is a legitimate contribution if argued on its own terms.
It is *not* a proxy for `d_SED`-minimality, and the suboptimality gap must be
reported (§7). The claim "we find the `d_I`-nearest model" is defensible and
clean; the claim "we find the closest KB" without qualification is not.

**No other route avoids the new alphabet.** Resolution (b) from `risks.md` §1
(use `d_I` as a filter) fails because the envelope constant `m(1+kn)` is too
large to prune meaningfully. The encoder cannot be modified to make `d_I` agree
with `d_SED` without redesigning the alphabet — that is exactly what D3′ does.

### 3.3 Consequence

**P-REPAIR in its intended semantics (`d_SED`-minimal repair) is gated on
decision D3′** (`Σ_FO`, `encoding.md` §3). A purpose-built alphabet in which
one ground fact is one token (design option F4) reduces the per-fact `d_I`
response from `(1+a) × ≈30–50%` to `1/|w*_c(K)|` — a single token edit in a
string of length `|K|`. This is the precondition that makes ball-enumeration
reach one-fact repairs at feasible radii.

Under the `d_I`-minimality reframing (§3.2), P-REPAIR can proceed **under
`Σ_HG` now** as a clean theoretical contribution, paired with the
suboptimality measurement of §7.

---

## 4. The one measurement worth running regardless

**The symmetry-deduplication experiment.** `src/idea1.txt` establishes that
without symmetry breaking, the MaxSAT route re-derives the same repair under
every permutation of the fresh anonymous element pool. In our representation,
permuted fresh elements map to the same canonical object (Theorem A), so
duplicate-repair emission is **zero by construction** — no symmetry-breaking
machinery needed.

**Experiment design.**

*Corpus.* Small KBs `K` of `|adom(K)| ∈ {4, 6, 8}` constants and `|Facts(K)| ∈
{8, 16, 24}` facts, constructed by taking a known `M ⊨ Σ` and applying `c ∈
{1, 2, 3}` Qin edits to produce `K ⊭ Σ`. Use `c` edit operations that
introduce `f ∈ {1, 2}` fresh elements in the repair (the repair `M` is a
witness). Generate 20 instances per `(|adom|, |Facts|, c, f)` cell → 20 × 3 × 2
× 3 = 360 instances. Repair cost `c` is known by construction.

*Axioms `Σ`.* Denial constraints of the form `∀x∀y (R(x,y) → ¬S(y,x))` and
universal restrictions of the form `∀x (P(x) → ∃y R(x,y))` — Bernays–Schönfinkel
`∃*∀*` fragment (`scope.md` §2), which has the finite model property and is
the natural home of integrity constraints. This ensures the search terminates
and that the fragment is common in database-repair literature (`related_work.md`
§2).

*Metric.* For each method and each instance, enumerate **all distinct output
repairs** (the output set, exhaustive within the method's budget). Count:
- `N_total`: total number of repair structures returned.
- `N_iso`: number of iso-classes among those structures (computed via `w*_c`).
- `dup_rate = (N_total - N_iso) / N_total`: fraction of redundant outputs.

*Methods compared.*
- MaxSAT + soft "keep atom" + hard `Σ` + fresh-element pool, **without** BreakID
  (no symmetry breaking).
- MaxSAT + BreakID / lex-leader over the fresh block.
- ASP (`clingo`) with weak constraints, no SB.
- ASP with `#symmetry` pragma or manual lex-leader.
- Ours (ball enumeration in `d_I` under `Σ_HG`, `d_I`-minimality framing).

*Expected outcomes.*
- MaxSAT without SB: `dup_rate` grows steeply with `f`; on `f = 2` fresh
  elements, `dup_rate ≈ 1 - 1/2! = 0.5` in the worst case.
- MaxSAT with BreakID: `dup_rate` reduced but non-zero (lex-leader breaks
  the *static* fresh order; assignment-dependent symmetries remain).
- ASP without SB: same as MaxSAT without SB.
- ASP with SB: partial improvement.
- Ours: `dup_rate = 0` by construction. **This is the claim; it is
  cheap and binary.** The experiment also measures whether `N_iso` (our output
  count) matches the ground-truth repair-class count — the completeness check.

*What each outcome means.*
- If MaxSAT-noSB `dup_rate` ≈ 0 (degenerate): the fresh elements happen to be
  grounded differently, symmetry is not the dominant cost — report this
  as a negative finding.
- If ours `dup_rate > 0`: Theorem A has not been properly applied to the
  encoding step — this would be a correctness bug, not a scientific finding.
- If ours is **slower** than MaxSAT + SB while producing the same iso-class
  set: the construction-overhead cost is the honest price of zero-machinery
  iso-invariance. Report the tradeoff.
- If ours **misses** a repair iso-class: this is a completeness failure of
  the d_I-ball at the tested radius — report the radius at which completeness
  is recovered.

This experiment is **alphabet-independent**: it can be run under `Σ_HG` with the
`d_I`-minimality framing (§3.2) without waiting for D3′. It is the
highest-confidence measurement the program can deliver before the alphabet
decision.

---

## 5. Baselines — pre-registered interpretation contract

*Written before results are seen. Binding in both directions. No baseline
removed for winning on any metric.*

| Baseline | Algorithm | Expected regime | Conceded in advance |
|---|---|---|---|
| **MaxSAT-noSB** | soft "keep atom" + hard `Σ`, fresh pool, no symmetry breaking | reference for `dup_rate` | will produce duplicates; expected to be fast per solve call |
| **MaxSAT-SB** | same + BreakID / lex-leader over fresh block | near-zero `dup_rate`; the standard tool | expected to **dominate wall-clock** on `d_SED`-exact search; we concede this in the introduction |
| **ASP (`clingo`)** | weak constraints, generate–test–optimize | same regime as MaxSAT-SB; natural fit for database repair constraints | also expected to dominate wall-clock; the most natural tool for the problem class |
| **Kodkod / Alloy** | relational bounded-scope, built-in SB | iso-invariant by SAT-level SB; the closest existing tool to iso-invariant nearest-model search | competitive on toy scope; unclear on real KB sizes |
| **FPT BST** | bounded-search-tree branching, `k`-parameter = edit budget | **universal / forbidden-pattern `Σ` only** (denial constraints); FPT in the edit budget; *automatically iso-invariant* (target class closed under iso); a genuine FPT algorithm, not a heuristic | **we expect to lose to this on the denial-constraint fragment**; this must be stated explicitly and the contest must be run on that fragment |
| **A\* / Riesen–Bunke** | exact `d_SED` via partial-matching lower bound | correct but exponential; the thing we claim to avoid | the correctness reference; wall-clock dominated on all but tiny instances |
| **Our ball enumeration** | `d_I`-ball over `Σ_HG` (`d_I`-minimality framing) or `Σ_FO`-ball (`d_SED`-minimality; gated D3′) | zero duplicates; all iso-classes to depth `r`; polynomial per radius step | slower than MaxSAT/ASP on wall-clock (expected); suboptimal vs `d_SED` (measured, §7) |

**Surviving claims regardless of who wins wall-clock:**
1. `dup_rate = 0` without any SB machinery (§4).
2. Every intermediate of a repair path decodes to an inspectable structure (P1;
   `theory.md`).
3. The repair path itself is a valid `d_I`-edit sequence of the construction
   program — a kind of explanation the SAT-level tools do not produce.
4. The `d_I` vs `d_SED` suboptimality gap is measured and reported (§7).

**FPT BST special clause.** The FPT baseline is the one where we expect a
structural loss. The paper must include a results row for the denial-constraint
fragment showing the FPT baseline's `k`-bounded wall-clock against our
ball-enumeration time. If the FPT baseline achieves the same iso-class set at
lower cost, the text says so.

---

## 6. Data

**Synthetic (ground truth by construction).** Take a known model `M ⊨ Σ` (built
by hand from `data.md` §1 hand-written fixtures or by the planted-family
generator for trivially labelable structures). Apply `c ∈ {1, ..., C_max}`
Qin-cost edits to produce `K ⊭ Σ`. The repair budget is `c` by construction
(`correlation.md`, perturbation-ladder protocol); `HGED(K, M) ≤ c` holds under
the official cost model, and for carefully chosen edits `HGED(K, M) = c`
exactly (minimal-budget violations). The ground-truth repair class is the
orbit `{M' : M' ≅ M}` — verified by computing `w*_c(M)`.

**Axiom families.**
- *Denial constraints* — `∀x∀y¬(R(x,y) ∧ S(y,x))` — the FPT fragment; also
  correspond to forbidden patterns in the hyperedge incidence structure.
- *Functional dependencies* — `R(x,y) ∧ R(x,z) → y = z` — equality-free
  encoding requires MACE-style flattening; out of scope for first pass
  (equality excluded, `scope.md` §1).
- *TGD-style existential rules* — `∀x(P(x) → ∃y R(x,y))` — the grow direction;
  fresh elements arise naturally here.

**Real provenance at feasible size.** `data.md` §4 proposes ARB/Benson
ego-hypergraphs derived by the Qin et al. (ICDE 2023) protocol (already
implemented in-repo). These provide real KB *provenance* (actual
co-authorship / cooccurrence structures) at sizes reachable by the `w*_c`
envelope (`scope.md` §3). The encoding adds labels; gate G-L1 measures
whether labelled instances are cheaper than unlabelled random instances of
the same structural size.

**Open data question DQ-L3** (`data.md` §7): perturbation-ladder edits for
P-REPAIR ground truth — which edit types, and does Qin cost or fact-level cost
define the budget? Answer: Qin cost (`correlation.md`, Definition 3 adopted
verbatim), because that is the oracle we own and the model under which
`HGED(K, M) ≤ c` holds by construction.

---

## 7. Distance-mismatch resolution

**The situation.** P-REPAIR is stated in `d_SED` (`vocabulary.md` §2). We
compute `d_I`. Measured correlation ρ = 0.622; no bi-Lipschitz relation;
`argmin d_I ≠ argmin d_SED` in general.

**Resolution for P-REPAIR specifically.**

Adopt resolution (c) from `risks.md` §1: on instances where exact `d_SED` /
`HGED` is computable, compute both the `d_I`-optimal repair and the true
`d_SED`-minimal repair, and measure the **suboptimality gap**:

```
gap(K, Σ) = d_SED(K, M_dI) / d_SED(K, M_dSED) − 1
```

where `M_dI` is the repair returned by our ball enumeration and `M_dSED` is
the repair returned by the exact oracle. `gap = 0` iff our repair is also
fact-minimal. `gap > 0` measures the cost of using a tractable surrogate.

**What the experiment looks like.**
1. Generate the synthetic corpus of §6 with known `c`-edit violations.
2. For each instance `(K, Σ, M_true)`:
   - Run our ball enumeration to find `M_dI`.
   - Run the exact `HGED` oracle (already implemented) to find `M_dSED`.
   - Compute `gap(K, Σ)`. Report mean ± IQR over the corpus.
3. If `gap = 0` consistently (our repair is also `d_SED`-minimal): the two
   distances agree on this problem family, and the framing simplifies. Report
   the finding.
4. If `gap > 0`: report the distribution. The paper's claim becomes: "our
   method finds the `d_I`-nearest model; on this corpus the `d_SED`-suboptimality
   is `X %`."

**Scope of the oracle.** The exact oracle peaked at 8.5 h / 55 GB per
630-pair block on the E1′ corpus. For single instances from the synthetic
corpus (small `|adom|`, small `|Facts|`), oracle calls will be orders of
magnitude cheaper. Gate: run oracle on pilot batch before committing to corpus
size.

**This experiment does not require D3′.** It can be run under the
`d_I`-minimality framing (§3.2) with the current `Σ_HG` alphabet. The outcome
of D3′ would change the interpretation (under `Σ_FO`, the `d_I`-optimal repair
is also `d_SED`-near), not the experimental protocol.

---

## 8. Verdict

**Bottom line: P-REPAIR is a strong follow-up paper, not a near-term article
contribution.** The reasoning:

**What works now.**
- The iso-deduplication measurement (§4) can be run immediately under the
  `d_I`-minimality framing. It produces a clean, cheap, legible result that
  demonstrates the structural advantage of iso-invariant representation.
- The suboptimality gap experiment (§7) can be run immediately on the synthetic
  corpus. It turns the ρ = 0.622 figure from a discussion footnote into an
  operational number with a concrete interpretation.
- The `d_I`-minimality framing (§3.2) is a legitimate theoretical contribution —
  a new revision operator that is polynomial-time, iso-invariant by construction,
  and produces inspectable intermediate structures. This is a publishable idea
  on its own.

**What is blocked.**

The intended semantics — `d_SED`-nearest model of `Σ` via ball enumeration —
requires D3′ (`Σ_FO` with a FACT token). Without it, the ball-enumeration
method cannot reach one-fact repairs at feasible radii (§3.1; the argument in
`risks.md` §2 is correct and the mitigation from heavy labelling is
unmeasured). D3′ requires re-proving Theorem A for `Σ_FO`, re-implementing the
encoder in Python and C++, and re-running the geometry pipeline. This is
months of work.

**Recommendation.**
- If the PI ratifies D3′ and schedules `Σ_FO` engineering: P-REPAIR is the
  primary showcase for the new alphabet. File it as a second article once
  `Σ_FO` has Theorem A and the encoder.
- If D3′ is **not** ratified (i.e., the article proceeds under `Σ_HG`): include
  P-REPAIR as a one-page demonstration of the `d_I`-minimality operator, backed
  by the iso-deduplication measurement and the suboptimality gap. This fits in
  the C3 navigation pillar (`applications.md` §C3) without requiring D3′.
- Do **not** claim `d_SED`-minimal repair under `Σ_HG`. That claim requires
  D3′ or it is false.

**Estimated cost.**
- Iso-deduplication measurement (§4): 2–3 days of experiment design + 1 day of
  code (MaxSAT baseline setup) + pipeline run. Output: one table.
- Suboptimality gap (§7): 1 day corpus generation + oracle pilot + 1 day
  analysis. Output: one column added to the same table.
- Full P-REPAIR with `d_SED` semantics: ≥ 3 months (D3′ engineering + proof
  + geometry re-run + full baseline comparison).

---

## 9. Requested changes to the shared foundation

*Do not edit these files directly. The orchestrator merges requested changes.*

1. **`vocabulary.md` §2, fact 4.** The statement "Qin's Definition 3 charges
   cardinality-0 node insertion/deletion at unit cost independently of hyperedge
   edits, so `HGED` is fork (b)" is correct. No change needed — it already
   appears in the current draft. Confirm it as the binding statement that
   resolves the PI's metric fork for all three ideas.

2. **`problems.md` §P-REPAIR.** Add a sentence: "The adopted distance for the
   exact criterion is `d_SED` (vocabulary.md §2). Ball enumeration produces
   `d_I`-nearest candidates; the suboptimality relative to `d_SED` is measured
   via the oracle (`risks.md` §1(c)). The two framings — `d_I`-minimality and
   `d_SED`-minimality — must be distinguished in every claim."

3. **`risks.md` §2.** Extend the feasibility-blocker entry to note that the
   `d_I`-minimality reframing (§3.2 above) provides a route under `Σ_HG`
   at the cost of changing the optimization objective. The current text stops at
   "gated on D3′" without acknowledging the reframing option. Both should appear
   so the PI can decide.

4. **`data.md` §7, DQ-L3.** Mark as resolved: edit-type = Qin Definition-3
   ops; budget = accumulated Qin cost; `HGED ≤ budget` by construction via the
   perturbation-ladder protocol.

5. **`encoding.md` §3.** Add an explicit statement that a `Σ_FO` FACT token
   brings the per-fact `d_I` response from `(1+a) × ≈30–50%` to `1/|w*_c(K)|`
   — making this the quantitative motivation, not just a structural one. This
   belongs in the honest-price section (§3.2 of `encoding.md`) so the PI sees
   the measured benefit before deciding D3′.
