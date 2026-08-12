# Theory — the proof obligations under v5.1

*Extends `../theoretical/{stability,geometry}.md`. Status: proposal, pending PI.*
*Revised 2026-08-12: P4 is demoted (isomorph-free generation is a borrowed
framework in which `nauty` is the better invariant), and P6 — soundness of the
move operator and of ball enumeration — is added, because that is the component
a certificate does not supply.*

Under v3 the theory *described* a space. Under v5.1 the theory **licenses a
search**: P1 makes the ambient space well defined, P6 makes the move operator
well defined, P3 makes the cost order admissible, and P2/P5 are the honest
statements about what the metric will and will not do inside the loop.
Theorem A makes the points of the space well defined — it is *not* sold as a
deduplication advantage, since nauty is complete too and faster. Nothing already
proved is re-opened.

**Alphabet-parametricity (important for D3′).** Theorem A's proof structure —
an isomorphism-invariant seed set, tie-complete branching over an
iso-invariant token order, shortlex lex-min — does not depend on the specific
token list; each new token or token field adds cases to the tie-break cascade
and to the completeness argument. The same holds for P1 (an induction over
prefixes, requiring only that every construction token attaches to something
already present) and for P3. This is why designing a purpose-built `Σ_FO`
(`logic_models/encoding.md` §3) is an *extension* of the theory rather than a restart —
and why the theory should be *written* alphabet-parametrically, with `Σ_HG` as
the instantiating example.

Notation as in `../theoretical/geometry.md`: `H` a connected labelled
hypergraph, `w*_c(H)` the frozen tie-complete canonical string,
`d_I(H,H') = d_Lev(w*_c(H), w*_c(H'))`, `n = |V|`, `m = |E|`, `k` the max arity /
pointer count.

---

## 0. Standing (proved; no new work)

- **Theorem A (completeness).** `w*_c(H) = w*_c(H') ⇔ H ≅ H'` over the augmented
  fingerprint `F(H) = (seed vertex label, w*_c(H))`. Proof volume:
  `theorem_a_completeness.{tex,pdf}`. *Consumer under v5:* the dedup key is
  **exact** — zero false merges and zero false splits, by theorem rather than by
  measurement. This is what B4's false-merge experiment measures the
  competitors against.
- **Corollary A (metric).** `d_I` is a metric on isomorphism classes.
  *Consumer:* metric-space indexing is applicable (triangle-inequality pruning,
  pivot tables, M-tree); Euclidean ANN is not (`geometry.md` §2).
- **Length lemma + envelope.** `|w*_c| ≤ m(1+kn)` and
  `d_I ≤ m(1+kn)·HGED` unconditionally. *Consumer:* key-size bound, and the
  candidate filtering bound P5.
- **D-CONN1.** The domain of discourse is connected hypergraphs; `Σ_HG` provably
  cannot express disconnection. *Consumer:* the FOL encodings must produce
  connected structures by construction — see `logic_models/encoding.md` §1 (the anchor
  vertex).

---

## P1 — Ambient decodability (proposition; low risk)

**Statement.** For every word `w ∈ Σ_HG(k)*`, `S2H(w)` is a well-defined
**connected** hypergraph. Consequently every point of the ambient space —
including every non-canonical intermediate on a Levenshtein alignment path
between two canonical strings — is a connected hypergraph.

**Proof sketch** (unchanged from the v4 draft §4). Induction over the prefix of
`w` on the VM invariant "the primal graph of `H_t` is connected". Base: the
initial state is a single vertex. Step: `V_{i,j}` creates an edge over `i ≥ 1`
pointer-resolved existing vertices and `j` fresh vertices, so every fresh vertex
enters inside an edge containing an existing vertex; `C_i` adds an edge over
existing vertices or no-ops; `P_i`/`N_i`/`W` do not touch `H`. The first
edge-creating token necessarily covers the initial vertex. Totality is the
closed-alphabet invariant (`S2H` never rejects alphabet-valid input).

**Measured illustration (already in hand).** 62/62 intermediates on five design
pairs spanning `d_I` 3–22 decode and are connected; 52/62 are non-canonical.

**Role under v5 — promoted.** P1 is no longer "A4's differentiator upgraded from
a demo": it is the statement that **the search space of B1/B2 is closed under
the search operators**. A generator that mutates strings, or a search that walks
alignment paths, cannot produce an invalid object. Vector representations have
no such property (a point between two signatures in `ℝ^d` is a point in `ℝ^d`),
and adjacency-string canonical forms are decodable but not closed under edits.

**Deliverables.** Proposition + proof in the paper; a pinned unit test
(random-word decodability + connectivity, Hypothesis-driven); the 62/62
measurement retained as the illustration.

---

## P2 — Drift / avalanche lower bound (proposition; moderate risk, time-boxed)

**Statement (draft).** There exists a family of connected 3-uniform hypergraphs
`{H_n}` with `|w*_c(H_n)| = Θ(n)` and single incidence swaps `σ_n` such that
`d_Lev(w*_c(H_n), w*_c(σ_n H_n)) = Ω(|w*_c(H_n)|)`.

**Status and crux.** Unchanged from the v4 draft §5: the mechanism analysis is in
`../theoretical/stability.md` §3 (pointer-run **drift**, tie/seed
**avalanche**); the candidate construction is a long anchored path whose swap
moves the decoration to the opposite end; the genuinely open step is showing
that *any* alignment leaves `Ω(n)` token mismatches. Pre-agreed fallbacks:
(i) state the bound for a move-free alignment model, or (ii) state a displacement
theorem plus the measured Levenshtein universality. The pinned family becomes a
frozen test either way.

**Role under v5 — explanatory, not load-bearing.** P2 explains *why the search
must not be guided by distance-to-target*: if one structural edit costs a
constant fraction of the string, then `d_I(current, target)` is a poor heuristic
and the enumeration must be organized by **cost level** (`applications.md` B1),
not by proximity. That makes P2 a design justification with a measured
counterpart (the ≈30–50 % single-edit response) rather than the paper's payload.
If P2 stalls, the design justification survives on the measurement alone.

---

## P3 — Cost/size accounting (lemma; low risk, small)

**Statement (two parts).**
1. *Boundedness.* `|w*_c(H)| ≤ m(1 + kn)` (existing length lemma), and
   empirically `|w*_c|` scales with incidence mass `Σ_e |e|` (measured: bits
   subsection, r > 1 on 320/320).
2. *Level-monotone enumeration.* Define the generation cost of a structure by
   the application's own objective (for MIN-CM: `cost(𝔐) = |D| + Σ_i |P_i^𝔐|`;
   for plain hypergraph enumeration: `n + m`). Every extension operator of B1
   strictly increases `cost`, so enumerating by non-decreasing `cost` visits
   every object exactly once per level and the first level containing a
   solution contains a minimum-cost solution.

**Explicit non-claim (important).** `|w*_c|` is **not** claimed to be monotone in
`cost`: pointer-movement tokens make string length a function of layout as well
as of size, and shortlex order therefore only *approximates* cost order. The
enumeration is organized by `cost`, and shortlex is used for deterministic
tie-breaking and for the canonical form itself. The pleasant remark that
`d_Lev(ε, w) = |w|` — so shortlex enumeration is breadth-first search in the
Levenshtein ball around the empty word — is stated as intuition, not as a
correctness argument.

**Deliverables.** One lemma, one paragraph, one pinned test that the extension
operator strictly increases `cost`.

---

## P6 — The move operator and ball enumeration (proposition; low risk) — **the one that matters**

**Statement.** Define the *move* relation on words by single-token edits
(insert, delete, substitute a token of `Σ_HG(k)`). Then:

1. *Closure.* Every word reachable by any sequence of moves decodes to a
   connected hypergraph — immediately from P1, since the move relation stays
   inside `Σ_HG(k)*`.
2. *Ball enumeration.* The Levenshtein ball `B_r(w) = {w' : d_Lev(w,w') ≤ r}` is
   finite, effectively enumerable, and `S2H(B_r(w))` is a finite multiset of
   connected hypergraphs. The map `B_r(w) → {isomorphism classes}` is
   many-to-one, and its *collapse ratio* is a measurable property of the
   representation (`geometry.md` §1, the ball-growth invariant).
3. *Reachability.* Any connected hypergraph is reachable from any other by a
   finite move sequence — the alignment path between their canonical strings
   witnesses it, and every intermediate is an object (P1).

**Why this is the load-bearing proposition of v5.1.** It is the formal content of
"a certificate is not a space". For a canonical-labelling engine there is no
analogue of (1): the image of the canonical map has no description other than
"canonize and compare", so an edited certificate is generally not a certificate
and the ball around a certificate is not a set of objects. Statement (2) is what
makes "enumerate every countermodel within radius `r`" a computable query
(`logic_models/problems.md`), and statement (3) is what makes navigation (C3) total
rather than best-effort.

**Deliverables.** A short proposition with the three parts, a Hypothesis-driven
test that random moves from random words always decode to connected
hypergraphs, and the measured collapse ratio (which is a geometry result, not a
proof obligation).

---

## P4 — Canonical augmentation is sound and complete (**demoted**; borrowed, not claimed)

**Statement.** Let `X_c` be the set of isomorphism classes of objects of cost
`c`, and let `ext` be the extension operator of B1 (add one hyperedge over
existing vertices; add one hyperedge introducing `j` fresh vertices; in the FOL
instantiation: add one domain element or one ground fact). Then the procedure

> generate all `ext`-children of every accepted object of cost `c`; accept a
> child `Y` iff `w*_c(Y)` equals the canonical form computed from the
> canonically-chosen parent of `Y`

visits **every** isomorphism class of cost `c+1` exactly once.

**Two implementable variants, both stated.**
- **(a) Generate-and-dedup.** Accept a child iff `F(Y)` is not already in a hash
  set of seen keys. Trivially sound and complete by Theorem A; memory is
  `Θ(|X_{c+1}|)` keys. This is the baseline, and it is the variant whose key size
  the compactness result prices.
- **(b) Canonical construction path** (McKay 1998; Kaski & Östergård 2006).
  Accept a child iff the augmentation that produced it is *the* canonical one for
  that child, determined from `w*_c(Y)` alone. Constant memory in the number of
  objects; requires a canonical-parent rule derived from the canonical string —
  the natural candidate being "the last construction token of `w*_c(Y)`",
  which needs proof that removing it yields a valid, connected parent.

**Risk sits in (b).** The canonical-parent rule must be well defined *and*
iso-invariant. Removing the last construction token of `w*_c(Y)` can disconnect
the object (it may be the token that introduced the last vertices) — the rule
must therefore be stated over the *reverse deletion* that P1's induction
guarantees to keep connectivity, i.e. delete the vertices introduced by the last
`V` token together with it. Whether the resulting parent is unique up to
isomorphism, and whether the child is reachable from it by a canonical
augmentation, is the proof obligation. **Fallback:** ship variant (a) only, state
the memory cost honestly, and record (b) as future work. Variant (a) is
sufficient for every experiment proposed in `applications.md`.

**Status under v5.1 — demoted from claim to borrowed component.** McKay's
framework is representation-agnostic: it works with any complete invariant, and
**nauty's Levi certificate is the better invariant for it** — faster, equally
exact, and already the state of the art. The paper therefore does not claim
isomorph-free generation as a contribution and does not need variant (b) at all;
it uses hash-set dedup (variant a) inside the C1 loop, states that a Levi-nauty
key can be substituted, and moves the weight of the argument onto P1/P6, which
nauty cannot supply.

What survives as a *remark* rather than a claim: in our representation the
invariant and the construction sequence are the same object, so the generator
needs no separate encoding of "how this object was built" — the gSpan argument
(min-DFS code over an external certificate). Worth one paragraph; not worth a
proof obligation, and P4 accordingly drops off the critical path.

---

## P5 — The envelope as a filtering bound (candidate; measure before claiming)

**Observation.** The unconditional envelope `d_I ≤ m(1+kn)·HGED` rearranges to a
**lower bound on HGED**:

```
HGED(H,H')  ≥  d_I(H,H') / (m(1 + k n))
```

so in a threshold query "return all `H'` with `HGED(H,H') ≤ τ`", any candidate
with `d_I > τ · m(1+kn)` can be pruned without calling the oracle. This is the
standard filter-and-verify pattern of the similarity-search literature and is
exactly the kind of use a TKDE reader will look for.

**Honest prior expectation: the bound is very likely too weak to prune anything.**
The constant `m(1+kn)` is enormous (hundreds to thousands on our corpora), so the
pruning predicate almost never fires. The measured E1' relation (Spearman
ρ = 0.622) says the *ordering* carries real signal even though the *bound* is
loose, which suggests the useful object might be an empirical, non-certified
filter — which is not a bound and must never be presented as one.

**Protocol (pre-registered).** Measure, on the frozen E1' mini-corpus, the
fraction of pairs pruned by the certified bound at a range of thresholds `τ`. If
the pruning rate is negligible (the expected outcome), report it in one sentence
in the discussion as a negative result and do not build on it. If it is
non-negligible, it becomes a short subsection. Either way, no claim precedes the
measurement.

---

## 6. Obligation summary

| # | Statement | Risk | Licenses | Fallback |
|---|---|---|---|---|
| Thm A | completeness | proved | the points of the space are well defined; the census is exact. **Not** claimed as a dedup advantage (nauty ties, faster) | — |
| Cor A | metric | proved | triangle-inequality pruning; C2's distances; C3's paths | — |
| **P6** | move operator closed; balls enumerable; reachability | low | **the whole C1 framework**; C2's radius-`r` queries; C3's totality | measurement only |
| P1 | ambient decodability + connectivity | low | P6's part (1); C3's intermediates | measurement only (62/62) |
| P3 | cost accounting, level monotonicity | low | C1's order and the minimality argument | — |
| P2 | drift/avalanche lower bound | moderate | *why* the search moves in string space and orders by cost, not by distance | move-free bound, or displacement + measurement |
| P4 | canonical augmentation | **demoted** | nothing on the critical path — borrowed framework, nauty is the better invariant | ship hash-set dedup; state the pluggable key |
| P5 | envelope as certified filter | measurement | (candidate) HGED-threshold search | report as negative |

**Critical path:** P6 → P1 → P3, then P2 as the explanatory layer. P4 and P5 are
off it.
