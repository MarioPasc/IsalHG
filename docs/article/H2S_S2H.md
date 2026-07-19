# The IsalHG instruction language: the H2S and S2H algorithms

**Status:** article specification (2026-07-12). This document is the
self-contained, article-facing description of the two algorithms at the core of
IsalHG — **S2H** (the interpreter that turns an instruction string into a
hypergraph) and **H2S** (the encoder that turns a hypergraph into its canonical
instruction string). It fixes notation, states the virtual machine, gives
pseudocode for both directions, and justifies every design decision against
either (a) the isomorphism-invariance requirement that the metric-space thesis
rests on, or (b) a concrete property of the C++/Python implementation. Code is
cited by stable file+symbol anchors (never line numbers, per
`.claude/rules/coding_rules.md` §7.2).

The pair `(H2S, S2H)` is what makes the article's central object well defined:
the canonical string `w*_c(H)` produced by H2S is a **complete isomorphism
invariant** (Theorem A), so the induced string metric
`d_I(H,H') = d_Lev(w*_c(H), w*_c(H'))` is a genuine, iso-invariant distance on
hypergraph isomorphism classes. Everything the article does downstream — the
geometric characterization (intrinsic dimension, non-Euclideanness,
concentration, sensitivity), MDS, k-medoids, dendrograms, kNN, shortest paths,
and the closing HGED-relation discussion — is a function of that distance and
therefore of these two algorithms. §9 makes the alignment explicit.

---

## 1. Context: the Isal family and why a string representation

IsalHG is the third member of the *Isal* family, which represents combinatorial
structures as strings over a compact instruction alphabet executed against a
pointer virtual machine:

- **IsalGraph** — finite simple graphs (Lopez-Rubio & Pascual-González,
  *Representation of Graphs by Sequences of Instructions*, preprint 2026);
- **IsalSR** — labelled DAGs for symbolic-regression deduplication
  (Lopez-Rubio, Pascual-González & Thurnhofer-Hemsi, IEEE TPAMI submission 2026);
- **IsalHG** — hypergraphs of arity `2 ≤ a ≤ k` (seed proposal 2026).

The design decisions in IsalHG's `core/` are ports of the corresponding
IsalGraph modules under the substitution *"edge = pair → hyperedge = set"* and
*"2 pointers → k pointers"*; the port templates are listed in `CLAUDE.md`
(§"Sibling project reference"). Where IsalHG departs from the sibling — the
`k`-pointer VM, the `V[le;i;j;·]` two-part construction step, the arity-aware
tie-break — the departure is noted and justified below.

**Why encode a hypergraph as a string at all.** A string representation buys
three things the article exploits:

1. **A canonical form.** If the encoder is driven from an isomorphism-invariant
   starting configuration and resolves all its choices invariantly, the output
   string depends only on the isomorphism class of the input, not on how the
   vertices/edges happen to be numbered. Two hypergraphs are isomorphic iff
   their canonical strings are equal (Theorem A). This is the same principle
   nauty/Traces/bliss use for graphs (McKay & Piperno 2014; Junttila & Kaski
   2007), realised natively on hypergraphs rather than on a bipartite reduction.

2. **A metric for free.** Strings carry the Levenshtein (edit) distance
   (Levenshtein 1966). Composing it with the iso-invariant canonical map gives
   an iso-invariant hypergraph dissimilarity `d_I` at the cost of one string
   comparison, with no bespoke hypergraph-matching solver
   (`core/metric_space/distances/isalhg_levenshtein.py`).

3. **A structure-faithful geometry.** Because a single hyperedge edit perturbs
   the canonical string by a bounded amount (the stability theorem), the string
   metric tracks true structural distance closely enough to drive standard
   unsupervised/supervised pipelines. This is the article's empirical claim
   (`docs/article/PROPOSAL.md` §2).

---

## 2. Preliminaries and the data model

A **hypergraph** `H = (V, E, ℓ_V, ℓ_E)` has a vertex set `V`, a set `E` of
hyperedges (each a subset of `V` of arity `2 ≤ |e| ≤ k`), a vertex-label map
`ℓ_V : V → {0,…,|Σ_V|−1}`, and an edge-label map `ℓ_E : E → {0,…,|Σ_E|−1}`.
Labels are contiguous integers fitted per corpus by
`core/datasets/schemas.py::LabelVocabulary`; the trivial (unlabelled) vocabulary
uses a single symbol so the algorithms run identically on labelled and
unlabelled inputs (no special-case branch). The in-memory model is
`core/sparse_hypergraph.py::SparseHypergraph` (C++ view:
`core/_native/include/isalhg/sparse_hypergraph.hpp::SHG`), which forbids
duplicate member-sets — a fact the encoder relies on (§6.6).

Two derived structures are used pervasively:

- **Primal (clique-expansion) graph.** `u ∼ v` iff some hyperedge contains both.
  The primal adjacency is cached at `SHG::finalise` (`primal_adj`). It is the
  substrate for the structural tuples and the seed cascades.
- **Vertex incidence.** `SHG::vertex_edges[v]` lists the edges containing `v`,
  sorted by edge id. Used by the encoder's candidate scan (§8).

`k` is the VM pointer count and the maximum supported arity; by decision B12 it
defaults to `max(2, max arity)` (`core/canonical.py::required_k`), or to the
corpus-wide maximum when a whole corpus is encoded under one alphabet
(`isalhg_levenshtein.py::_resolve_corpus_k`).

---

## 3. The instruction set `Σ_HG`

`Σ_HG` is a **closed** alphabet of five token kinds
(`core/instructions.py`). Closed means *every* well-formed string over `Σ_HG`
decodes to a valid hypergraph; the interpreter never rejects alphabet-valid
input (§5). Rejection of malformed tokens is a separate, earlier concern
(`instructions.py::validate`).

| Token | Surface form | Semantics | Constraints |
|---|---|---|---|
| `V` | `V[le;i;j;ln₁,…,lnⱼ]` | New hyperedge of arity `i+j`, edge label `le`, over the `i` existing pointed vertices `p₁…pᵢ` **and** `j` new vertices (labels `ln₁…lnⱼ`) inserted into `L` right after `p₁`. Pointers do not move. | `1 ≤ i,j ≤ k−1`, `2 ≤ i+j ≤ k`, `|{ln}| = j`, labels in range |
| `C` | `C[le;i]` | New hyperedge of arity `i`, label `le`, over the `i` existing pointed vertices `p₁…pᵢ`. No pointer movement. No-op if an identical `(label, member-set)` edge exists. | `1 ≤ i ≤ k`, label in range |
| `P` | `P[i]` | Advance pointer `pᵢ` one step forward in `L`. | `1 ≤ i ≤ k` |
| `N` | `N[i]` | Retreat pointer `pᵢ` one step backward in `L`. | `1 ≤ i ≤ k` |
| `W` | `W` | No-op (alphabet-closure / padding). | — |

**Justification of the token set.**

- **Two construction tokens (`V` and `C`), not one.** A hyperedge either
  introduces new vertices (`V`) or connects only already-present vertices (`C`).
  Splitting the two is what lets the encoder grow the vertex set and close
  cycles independently; it mirrors IsalGraph's edge/close split generalised from
  pairs to sets. `C` is idempotent (no-op when the edge exists) precisely so that
  redundant close attempts during the greedy search cannot corrupt the output —
  a required property for the closed-alphabet guarantee.

- **New vertices inserted after `p₁`, in listed order.** The insertion point is
  fixed (immediately after `p₁` in `L`) and deterministic. This is what makes
  S2H a *total function*: given the token, the resulting CDLL layout is
  determined, so `H2S(S2H(w)) = w` up to canonical normalisation (round-trip,
  invariant 3). The order of the `j` new vertices is the token's own
  `ln₁…lnⱼ` field; the encoder chooses that order invariantly (§6.6).

- **`i ≤ k−1` for `V`, `i ≤ k` for `C`.** A `V` needs at least one new vertex
  (`j ≥ 1`), so it can point at most `k−1` existing ones with `k` pointers; a
  `C` uses no new vertex and may point all `k`. These bounds are enforced in
  `instructions.py::validate` and are the reason the pointer count must equal
  the maximum arity (invariant 7): a `k`-arity edge closed by `C[le;k]` needs
  `k` simultaneously-positioned pointers.

- **Pointer moves are unit steps (`P`/`N`), not jumps.** Encoding a move of
  `δ` steps as `δ` unit tokens (rather than one parametrised jump) is what makes
  Levenshtein distance on the string track structural distance: a small change
  in where an edge attaches changes the move-block length by a small number of
  tokens, which is exactly the locality the stability theorem needs (§9).
  A single "jump to position δ" token would make one structural perturbation
  rewrite an unbounded integer field, breaking edit-locality.

- **`W` is a no-op.** It exists so the alphabet is closed under padding and so
  the VM has a canonical do-nothing instruction (invariant 6: `W` is meaningful
  and must never be stripped during canonicalization). The IsalHG greedy encoder
  emits only movement and construction tokens, so canonical strings produced by
  H2S contain no `W`; S2H nonetheless interprets `W` as a no-op, keeping every
  string in `Σ_HG*` decodable.

**Token order (the total order used for lex-min).** Comparison is over **token
tuples**, never over serialised strings, to avoid the
`"V[le;10;…]" < "V[le;2;…]"` lexicographic pitfall
(`instructions.py::Token.sort_key`; C++ `token.hpp`/`token.cpp::token_cmp`). The
kind ranks are

```
W (0)  <  N (1)  <  P (2)  <  V (3)  <  C (4)
```

with ascending numeric comparison within a kind. Two token *sequences* are
compared by the **shortlex** key `(length, tok₁.sort_key, tok₂.sort_key, …)`
(`instructions.py::sequence_sort_key`; C++ `token.cpp::sequence_cmp`): shorter
strings are always smaller, ties broken position-by-position. Shortlex, not
plain lex, is the article's canonical order because it makes "the simplest
construction" (fewest instructions) canonical, matching IsalGraph's
`min(len(w), w)` convention.

---

## 4. The virtual machine

The VM state is `S = (H, L, p₁, …, p_k)`:

- `H` — the hypergraph built so far (starts as a single seed vertex);
- `L` — a **circular doubly-linked list** (CDLL) of vertex ids
  (`core/cdll.py`; C++ `cdll.hpp`);
- `p₁,…,p_k` — `k` pointers, each an index of a **CDLL slot** (not a vertex id).

**Initial state** (`string_to_hypergraph.py::StringToHypergraph.__init__`;
C++ `state.hpp::EncoderState`): `H` has one vertex (the *seed*) at slot `0`,
`L = [seed]`, and all `k` pointers point to slot `0`.

**Justification of the VM design.**

- **Why a CDLL, not an array or the vertex ids directly.** New vertices are
  inserted *between* existing ones (right after `p₁`) in `O(1)`, and pointers
  advance/retreat in `O(1)`, with no renumbering. Critically, the pointers index
  *CDLL slots*, not hypergraph vertex ids (invariant 1): the same abstract
  hypergraph reached by two different construction orders has two different
  vertex-id assignments but the encoder only ever refers to vertices through
  their *position* in `L`, which is what makes the output a function of the
  positional construction, not of the ids. Every pointer must be resolved via
  `cdll.get_value(pᵢ)` before touching `H`.

- **Why `k` pointers.** `k` equals the maximum arity, so an arity-`a` edge can
  be specified by positioning `a` of the `k` pointers on its members (invariant
  7). Fewer than `k` pointers could not close a maximum-arity edge; more would
  be inert. The article encodes a mixed-arity corpus with the corpus-wide `k`,
  and the encoder exploits the fact that pointers beyond an instance's own
  `max_arity` can never participate in an emission (§8, `k_disp`).

- **Why start from a single seed with all pointers coincident.** The empty
  state is canonical and seed-agnostic; the *choice of seed* is the only
  externally-supplied degree of freedom, and it is chosen from an
  isomorphism-invariant set (§7). Coincident pointers make the first emission's
  displacement cost zero.

---

## 5. S2H — the interpreter (string → hypergraph)

S2H executes a token sequence against the VM and returns the final hypergraph.
It is a **deterministic, total** interpreter: on any alphabet-valid input it
runs to completion without rejection (the closed-alphabet invariant, invariant
2). Implementation: `core/string_to_hypergraph.py::StringToHypergraph` (Python
only — S2H is not on the performance-critical path, so there is no native twin).

**Pseudocode.**

```
S2H(tokens, k, seed_label):
    validate(tokens, k)                       # instructions.py::validate
    H ← hypergraph with one vertex v0 (label seed_label)
    L ← CDLL preallocated to 1 + Σ_{V-tokens} j     # _capacity_for
    slot0 ← L.insert_after(⊥, v0)
    p1 … pk ← slot0                           # all pointers coincide on the seed

    for tok in tokens:
        case tok of
          W:            pass                                    # no-op
          P[i]:         p_i ← L.next(p_i)                       # advance
          N[i]:         p_i ← L.prev(p_i)                       # retreat
          C[le;i]:      members ← [ L.value(p_1), …, L.value(p_i) ]
                        H.add_hyperedge(members, label=le)      # idempotent
          V[le;i;j;ln]: existing ← [ L.value(p_1), …, L.value(p_i) ]
                        anchor ← p_1
                        new ← []
                        for label ℓ in ln:                      # in listed order
                            v ← H.add_vertex(label=ℓ)
                            anchor ← L.insert_after(anchor, v)   # after p_1, chained
                            new.append(v)
                        H.add_hyperedge(existing ++ new, label=le)
                        # pointers do NOT move
    return H
```

This matches `StringToHypergraph._step` verbatim (the `case` arms are the five
`isinstance` branches). Notes and justifications:

- **Preallocation to `1 + Σ j`.** The maximum vertex count is the seed plus one
  per new vertex introduced by a `V` token (`_capacity_for`). Preallocating the
  CDLL to that capacity avoids any reallocation mid-run, keeping slot indices
  stable for the pointers — important because pointers *are* slot indices.

- **`V` inserts the `j` new vertices chained after `p₁`, then builds the edge
  over `existing ++ new`.** The chaining (`anchor ← new_slot` each iteration)
  places `ln₁,…,lnⱼ` in consecutive slots immediately after `p₁`, in the token's
  listed order. Pointers are untouched, so a `V` leaves every `pᵢ` where it was.

- **`C` is idempotent.** `add_hyperedge` is a no-op when the `(label,
  member-set)` already exists (`SparseHypergraph` forbids duplicates). This is
  what lets the encoder attempt closes freely without needing to check
  existence, and it guarantees S2H never fails on a repeated `C`.

- **Totality.** No arm can raise on valid input: `P`/`N` walk a circular list
  (always defined), `C`/`V` add edges over resolvable pointer values, `W` does
  nothing. Hence the closed-alphabet invariant.

**Round-trip.** For every `w` reachable from a valid hypergraph,
`H2S(S2H(w)) = w` up to canonical normalisation; equivalently `S2H(H2S(H)) ≅ H`
for every `H` representable at the chosen `k` (invariant 3). This is asserted as
a property test over Hypothesis-generated hypergraphs
(`tests/property/test_s2h_roundtrip.py`).

---

## 6. H2S — the encoder (hypergraph → string)

H2S solves the inverse problem: given `H` and a seed vertex, produce a token
sequence that S2H maps back to `H`, choosing that sequence to be
**shortlex-minimal** subject to a fixed tie-breaking discipline. It is a greedy
constructive search with bounded backtracking. The production implementation is
C++ (`core/_native/src/h2s.cpp::greedy_h2s_tokens`), a bit-for-bit twin of the
Python reference (`core/hypergraph_to_string.py::_python_greedy_h2s`), which is
retained for differential testing.

### 6.1 Structural tuples `ξ` and `η`

Two isomorphism-invariant projections drive selection
(`core/structural_tuples.py`; C++ `structural_tuples.cpp`):

- `ξ_h(v)` = number of primal-graph vertices at distance **exactly** `h` from
  `v` (`xi`); the label-aware variant `ξ^ℓ` counts per label per shell
  (`xi_labelled`). Depth defaults to `3` (invariant 8, inherited from
  IsalGraph); changing it re-opens the completeness question.
- `η_h(e) = Σ_{v∈e} ξ_h(v)` (`eta`), an edge invariant.

Both are functions of the primal graph and the labels, hence preserved by every
hypergraph automorphism. They are used as **iso-invariant tie-breakers** so that
the encoder's choices do not depend on vertex/edge numbering.

### 6.2 Seed selection (the iso-invariant starting set)

The canonical algorithm runs H2S once per seed in an **isomorphism-invariant
seed set** `S(H)` and takes the shortlex-min over the runs (§7). Invariance of
`S(H)` is the load-bearing property (invariant 4): a non-invariant seed rule
(e.g. "smallest raw id") would make the output a function of the presentation
and break the iso-test. Two admissible cascades are implemented; the package
default since T-M0 is the neighbour-degree cascade
(`structural_tuples.py::max_neighbor_degree_nodes`; C++
`max_neighbor_degree_nodes_compute`):

```
S(H) = argmax_lex over v of
        ( ℓ_V(v),                                  # 1. maximal vertex label
          deg_primal(v),                           # 2. then maximal primal degree
          sorted_desc[ deg_primal(u) : u ∼ v ] )   # 3. then lex-max neighbour-degree list
```

Each rung is an iso-invariant projection of the vertex set, so their common
argmax is iso-invariant. The historical `ξ`-cascade
(`max_xi_nodes`: `argmax_lex (ξ^ℓ(v), ℓ_V(v))`) is equally sound; the
neighbour-degree cascade is preferred because it is cheaper
(`O(n + n·deḡ)` vs the depth-3 BFS `O(n²·depth)`) and typically returns a
*smaller* seed set on non-vertex-transitive inputs (fewer H2S runs). On a
vertex-transitive design (Fano, STS, GQ) both cascades return the full vertex
set, because every vertex has identical invariants — the source of the
worst-case cost in §8.

### 6.3 The per-step choice: shortlex-min emission

From a partial state, one *emission* is chosen and applied, then the encoder
recurses on the smaller remaining problem. An emission is a **move-block**
(a run of `N`/`P` tokens that repositions the pointers) followed by one **main
token** (`V` or `C`). The chosen emission is the shortlex-minimum over all
displacements and all applicable candidates, under the mandatory 7-rung
tie-breaking cascade (`hypergraph_to_string.py` module docstring; invariant 5):

```
1. minimise total displacement cost  Σ|δ_i|                 (fewest move tokens)
2. among equal cost, lex-min the move-block token sequence  (N before P, index ↑)
3. prefer V over C                                          (kind rank V < C)
4. lex-min on (i, j)         [V]   /   (i)   [C]
5. lex-min on edge label  ℓ_E(e)
6. lex-min on the sorted new-vertex-label tuple             [V only]
7. lex-min on η(e)
   (residual: raw edge id — see §6.5)
```

Rungs 1–2 are exactly the shortlex order on the move-block; rungs 3–7 are the
`Token.sort_key` order on the main token composed with the iso-invariant edge
key. Concretely the encoder compares candidates by the key
`( |move_block| + 1 , move_block tokens…, main token )` and keeps the minimum
(`h2s.cpp::encode_from`, the `consider` comparison;
Python `_encode_from`). Justifications:

- **Rung 1 (minimise displacement) ⇒ shortlex minimality.** Each unit of move
  cost is one `N`/`P` token, so minimising `Σ|δ_i|` minimises emission length,
  which is the first component of the shortlex key. This is why "closest
  emittable edge first" is the greedy rule.
- **Rung 2 (`N` before `P`, ascending index).** The move-block is rendered in a
  fixed lex-min order for a given displacement vector
  (`emit_movement_tokens`; Python `_movement_tokens`): all `N` tokens (negative
  moves) in ascending pointer index, then all `P` tokens. Any other order would
  be a larger string for the same displacement.
- **Rung 3 (`V` over `C`).** Encoded structurally in the token ranks
  (`V(3) < C(4)`); at equal move-block the `V` main token sorts first. Switching
  this priority changes the canonical string, so it is non-optional (invariant
  5).
- **Rungs 4–7 (edge selection).** `(i,j)`, edge label, sorted new-vertex labels
  and `η(e)` are all iso-invariant, so ties among genuinely equivalent edges are
  broken by invariant keys — never by raw id, except as the residual §6.5.

### 6.4 The displacement search

At a state with `m` mapped vertices the pointers may move within radius
`r = m` (the whole CDLL). The candidate displacements are the `k`-tuples
`δ ∈ [−r,r]^k`, and the search visits them by ascending cost
`(Σ|δᵢ|, |δ|-vector, δ)`, stopping as soon as the cheapest emittable
displacement is found (`enum_cost_class` + the cost loop in `encode_from`;
Python `_enum_displacements` with the `cost + 1 > best` early-exit). Two
implementation facts that the article's complexity analysis (§8) depends on:

- Only pointers up to the instance's `max_arity` can affect an emission, so the
  search varies only the first `k_disp = min(k, max_arity)` coordinates
  (`h2s.cpp::encode_from`, `k_disp`).
- The per-displacement candidate scan is restricted to edges incident to the
  vertex under pointer 1, since any candidate requires `tentative_inputs[0]` to
  be an edge member (`for_each_v_candidate`, `best_c_for_displacement` iterate
  `vertex_edges[t0]`).

### 6.5 Greedy pseudocode

```
ENCODE_FROM(H, k, state):                      # h2s.cpp::encode_from (greedy path)
    if all vertices mapped and all edges consumed:
        return ε                               # done
    best ← ⊥
    for cost = 0, 1, 2, … :                    # ascending displacement cost
        if best ≠ ⊥ and cost + 1 > |best| : break     # can't improve (shortlex)
        for δ in displacements of this cost:
            position pointers by δ  →  new_slots, move_block
            t0 ← vertex under pointer 1
            for each unconsumed edge e ∋ t0:   # incidence-restricted scan
                if e yields a V candidate here:   # §6.6 defines "yields"
                    cand ← (move_block, V[ℓ_E(e); i; j; sorted new labels])
                    best ← shortlex_min(best, cand)   # rungs 1–7
                if e yields a C candidate here:
                    cand ← (move_block, C[ℓ_E(e); i])
                    best ← shortlex_min(best, cand)
    (move_block, main, e*) ← best
    apply move_block; consume e*; insert e*'s new vertices (if V)
    tail ← ENCODE_FROM(H, k, state)            # recurse on the smaller problem
    undo the application                        # inplace + stack undo (no clone)
    return move_block · main · tail
```

The encoder mutates the state in place and unwinds it with stack-allocated undo
records rather than cloning the CDLL per branch — a port of IsalGraph's inplace
encoder (`state.hpp::EncoderState`; the undo blocks in `encode_from`).

### 6.6 Tie-complete branching — the canonical form `w*_c`

The greedy encoder above still has **one** non-invariant choice: rung 7 leaves a
*residual tie set* — distinct edges can agree on the entire iso-invariant key
`(i, j, ℓ_E, sorted new labels, η)` — and the greedy default resolves it by raw
edge id (insertion order). It also fixes one ordering of the `j` new vertices.
Both are functions of the *presentation*, so the greedy string is **not** a
canonical form: two edge orderings of the same hypergraph can produce different
strings (pinned `n=4` counterexample in
`tests/unit/core/test_canonical_encoder.py`). Under the greedy variants the
IsalHG "iso test" is therefore only one-sided (equal strings certify
isomorphism; unequal strings are inconclusive on tie-degenerate inputs).

The article's canonical algorithm — registered as `"canonical"`, C++
`AlgorithmVariant::GreedyMinComplete` (`canonical.hpp`), selected by
`tie_branch = true` — removes both presentation dependencies by **branching**:

```
V-branch of ENCODE_FROM, tie_branch = true:    # h2s.cpp::encode_from (V branch)
    T ← all unconsumed edges tying with the winner on the iso-invariant
        key-prefix (i, j, ℓ_E, sorted new labels, η)      # collect_tied_v_candidates
    best_tail ← ⊥
    for e in T:                                # branch over the residual tie set
        for π in label-respecting permutations of e's new vertices:
            apply (e, π); tail ← ENCODE_FROM(H, k, state); undo
            best_tail ← shortlex_min(best_tail, tail)      # keep lex-min completion
    return move_block · main · best_tail
```

- **What is branched.** Exactly the two presentation-dependent choices: the
  residual edge-tie set `T` (`collect_tied_v_candidates`; Python
  `_tied_v_candidates`) and, per tied edge, the label-respecting permutations of
  its new vertices (`enumerate_label_perms_cb`; Python
  `_label_respecting_perms`). Displacement and the invariant part of edge
  selection are **not** branched — they are already invariant. For a trivial
  vocabulary the per-`V` permutation factor is `j!` (typically `≤ 6`).
- **Why branching, not a smarter invariant key.** One could try to break the
  residual tie with a deeper invariant key. But refining the tie set returns a
  *different* canonical form (the lex-min over a proper subset need not equal the
  lex-min over the whole set), which would fork the definition of the paper's
  central object. Decision D-TA2 therefore **freezes** `w*_c` as the *unpruned*
  tie-complete shortlex-min — the minimum over the full residual tie set and all
  label-respecting orderings — and forbids invariant-key refinement. The only
  sanctioned future speed-up is stabiliser-orbit pruning, which by Proposition
  6.0 of the completeness proof returns the *same* `w*_c` (tied branches related
  by an automorphism fixing the mapped prefix have equal completions).
- **`C` is never branched.** A `C` requires its members to equal the pointed
  set, and `SparseHypergraph` forbids duplicate member-sets, so the `C` tie set
  is always a singleton — there is no edge-id dependence to remove.

### 6.7 The canonical string and the fingerprint

The canonical driver runs the (tie-complete) encoder from every seed in `S(H)`
and takes the shortlex-min (`canonical.cpp::canonical_string_compute`; the seed
loop is parallelised over a persistent thread pool):

```
w*_c(H) = min_shortlex { greedy_h2s_complete(H, v₀) : v₀ ∈ S(H) }
```

The isomorphism **fingerprint** augments the string with the seed vertex label,
`F(H) = (ℓ_V(seed), w*_c(H))` (`canonical.py::canonical_fingerprint`;
serialised by `iso_backends/isalhg_backend.py` as `b"{label}|{w*}"`, the prefix
omitted when `|Σ_V| = 1`). The seed label is needed because the bare string can
miss it on non-trivial vocabularies; the metric `d_I` measures the
seed-label-prefixed token sequence.

---

## 7. Completeness: why `w*_c` is *the* canonical form

**Theorem A (completeness, resolved T-TA 2026-07-08; proof in
`proofs/theorem_a_completeness.{tex,pdf}`).**

- **Soundness (`⇒`), all variants.** `F(H₁) = F(H₂) ⟹ H₁ ≅ H₂`, unconditionally
  — because `S2H(F)` reconstructs a hypergraph isomorphic to the original
  (round-trip), so equal fingerprints reconstruct isomorphic hypergraphs.
- **Completeness (`⇐`), the `"canonical"` variant only.** For the tie-complete
  `w*_c`, `H₁ ≅ H₂ ⟹ F(H₁) = F(H₂)`. The proof: the seed set `S(H)` is
  iso-invariant; from a matched seed the tie-complete search explores *all*
  presentation-dependent choices and takes the shortlex-min, so its output is an
  isomorphism invariant; the shortlex-min over the iso-invariant seed set is
  therefore a complete invariant. The greedy variants **fail** completeness
  (their raw-edge-id residual makes `w*` depend on edge order), which is exactly
  why the article uses `"canonical"`.

Consequently, with the tie-complete algorithm,

```
iso(H₁, H₂)  ⟺  F(H₁) = F(H₂)
```

is an exact isomorphism test, and — the point for the article — `d_I` is
**well defined on isomorphism classes**: isomorphic hypergraphs have identical
`w*_c`, so `d_I(H,H') = 0 ⟺ H ≅ H'`, the identity-of-indiscernibles axiom of a
metric on the quotient `V_HG / ≅`. `w*_c` is pinned on {Fano, STS(9), the
cyclic partial C13(0,1,3), the `n=4` counterexample} (fast) and on both true
STS(13)s (slow marker; T-M0c) by `tests/unit/core/test_wstar_c_frozen.py`
so any accidental change to the frozen definition fails loudly.

---

## 8. Complexity and the fast implementation

**Cost structure of the tie-complete search.** Two regimes, both measured
(`docs/engineering/CPP_OPTIMIZATION_LOG.md`, rounds 10–11):

- **Branching-bound (automorphism-rich designs).** On vertex-transitive designs
  every seed is kept and many edges tie, so the branch factor of §6.6 compounds:
  the worst case is `∏_emissions (|tie set| · j!)`, i.e. the `(j!)^E`-type blow-up
  that is intrinsic to a canonical-form search on highly symmetric structures.
  GQ(2,2) visits ~4.5·10⁵ recursion nodes for a 276-token string.
- **Displacement-bound (sparse large `n`).** Each recursion node's cost is
  dominated by the displacement search, whose blind enumeration is
  `O(c*^{k_disp})` where `c*` (the first emittable cost) grows with `n` on
  sparse inputs (the next edge is far in the CDLL; `c*` up to ~58 at `n=50`).

**What the C++ core does about it.** Four output-preserving changes (rounds
10–11) attack the per-frame cost; every one leaves `w*_c` **byte-identical** to
the pure-Python reference. Round 10 (three constant-factor cuts to the
per-displacement work in `encode_from`):

- **Incidence-restricted candidate scan.** Any `V`/`C` candidate needs pointer 1
  to land on a member, so the scan iterates `SHG::vertex_edges[t0]` (the edges
  incident to that vertex, sorted by edge id) instead of all `E` edges — the
  candidate set is identical (`for_each_v_candidate`, `best_c_for_displacement`).
  On GQ(2,2) this is 3 incident edges vs 15.
- **No per-cost-class sort.** `enum_cost_class` previously sorted each class; but
  the winner is chosen by an order-independent `(total_len, move-block,
  main-token)` comparison and the move-block token sequence is injective in the
  displacement, so no two displacements tie — the winner is identical for any
  enumeration order, and the sort was pure overhead (`enum_cost_class`).
- **`k_disp = min(k, max_arity)`.** No candidate reads `tentative_inputs` beyond
  `max_arity − 1`, so pointers past the instance's `max_arity` are strictly
  cost-dominated and the displacement search varies only the first `k_disp`
  coordinates (`encode_from`). A no-op when `k = max_arity`, but a real cut on
  the `d_I` corpus path (`isalhg_levenshtein.py::_resolve_corpus_k` encodes every
  hypergraph with the corpus-wide `k`, so a graph inside an arity-5 corpus
  previously enumerated 5-tuples where 2 suffice; `w*_c` verified invariant to
  `k ≥ max_arity` on 600/600 random instances).

Round 11 (the large-`n` lever) replaces the blind cost-class enumeration with a
**hybrid** displacement search:

- **Inverted displacement enumeration.** A `V`/`C` emission of edge `e` is
  *uniquely determined* by placing pointers `1..r` on `r` of `e`'s members
  (`r = #mapped members` for `V`, `= arity` for `C`), so instead of enumerating
  displacement tuples blindly the search enumerates, *per unconsumed edge*, the
  `r!` pointer-to-member bijections and, per pointer, both minimal signed
  displacements reaching its target; unassigned pointers stay put. Every
  generated displacement is a genuine candidate the brute force would also
  produce, all feed the same comparison, and the cost drops from
  `O(c*^{k_disp})` to `O(Σ_e r_e!·2^{r_e})` per frame, independent of `c*`
  (`emit_inverted_candidates`; `O(1)` distances after one `O(N)` CDLL
  position-rank walk).
- **Hybrid, not replacement.** The brute-force loop is cheaper when `c*` is
  small (every design fixture: `c* ≤ 6`), so it runs up to a cost cap
  (`INVERSION_COST_CAP = 8`) and only frames that find nothing by then (sparse,
  far next edge) fall back to the inversion. **The design fixtures therefore stay
  on the byte-identical, same-speed brute path — Round 11 does not change their
  timing at all**; the win is confined to the sparse frames that need it.

**Validation.** The inverted path shares the exact per-displacement comparison
(the `consider` closure), then is checked three independent ways, all
byte-identical `w*_c`: (i) built inversion-only (brute disabled) it passes the
frozen pins, the C++≡Python differential, and the completeness biconditional vs
pynauty; (ii) inversion-only vs brute-only agree on 84/84 sparse instances
(`n=12..36`, including `k=6` mixed-arity encodes); (iii) the shipped hybrid
agrees with brute on the same 84/84. The frozen `w*_c` pins
(`test_wstar_c_frozen`) and the full suite stay green throughout.

**Measured effect** (non-PGO, i7-13620H; `scripts/bench_tie_complete.py`,
`scripts/bench_canonical_vs_competitors.py`):

| Regime | before round 10 | round 10 | round 11 (shipped) |
|---|---:|---:|---:|
| GQ(2,2) doily | 1621 ms | 743 ms | 729 ms |
| STS(9) | 200 ms | 108 ms | 108 ms |
| random corpus n=12 (max) | 61 ms | 34 ms | **8.7 ms** |
| medium sparse n=35 | 44 ms | 44 ms | **6.1 ms** |
| medium sparse n=50 | ~2900 ms | ~2900 ms | **318 ms** |

Round 10 gives ~2× on the designs; Round 11 leaves the designs untouched and
gives up to ~9× on the sparse/large-`n` regime the applications use (the `n=50`
fingerprint went from unusable, ~3 s, to corpus-viable, ~0.3 s), without
changing `w*_c`. The residual gap to Levi + nauty / bliss / Traces (which
fingerprint in `0.02–0.15 ms` across the whole spectrum) is the algorithmic
ceiling: those engines run inside an individualisation–refinement frame that
prunes the symmetric orbits the tie-complete search re-explores; closing it
needs stabiliser-orbit pruning (the one sanctioned value-preserving lever,
§6.6), not a faster encoder.

---

## 9. Alignment with the article scope

The metric-space article
(`docs/article/PROPOSAL.md`) claims that IsalHG induces a **structure-faithful,
isomorphism-invariant metric** on hypergraph space and that this metric drives
standard pipelines. Every load-bearing property of that claim is a direct
consequence of a decision justified above:

| Article requirement | Provided by | Where justified |
|---|---|---|
| `d_I` is a metric on iso classes (identity of indiscernibles) | `w*_c` is a **complete** iso invariant | §7 (Theorem A), §6.6 (tie-complete branching), §6.2 (iso-invariant seed set) |
| `d_I` is computable without a bespoke hypergraph matcher | Levenshtein on the canonical string | §1, §6.7 |
| Stability `d_I ≤ C(k,Δ)·HGED` (Theorem B) | Edit-locality: one hyperedge edit perturbs `w*_c` by a bounded number of tokens | §3 (unit-step moves), §6 (greedy locality); the `Δ`-dependence is the falsifiable density-sweep prediction |
| A single frozen definition so tables never invalidate | `w*_c` frozen as the unpruned tie-complete shortlex-min (D-TA2) | §6.6 |
| Runs at corpus scale (T-M5 experiments) and on larger real hypergraphs (applications) | C++ core; displacement inversion for sparse large-`n` | §8 |
| Identical behaviour on labelled and unlabelled inputs | trivial vocabulary; label-aware `ξ^ℓ`, seed cascade, `V` label field | §2, §6.1–6.2 |

Two design decisions deserve emphasis as *scope-driven*, not incidental:

1. **The tie-complete branching (`w*_c`), despite its cost.** The greedy
   variants are `~15–20×` faster but define **no** canonical form on the
   isomorphism class (§6.6). Without a complete canonical form, `d_I` would not
   be well defined on iso classes and the entire metric-space thesis — the
   stability theorem, MDS, clustering, kNN, shortest paths — would have no
   foundation. The article therefore *must* pay for `"canonical"`, and §8's
   optimisations exist to make that price affordable at corpus scale.

2. **Unit-step pointer moves and local edge attachment.** These are what make a
   single structural edit change the canonical string by a bounded amount, which
   is precisely the Lipschitz-type locality the stability proof exploits
   (the hypergraph analogue of the tree-mover / WL-distance stability templates,
   Chuang & Jegelka 2022; Chen et al. 2023). A jump-based or globally-numbered
   encoding would still be a valid canonical form but would destroy edit-locality
   and with it Theorem B.

---

## 10. Characteristics summary

| Property | Value | Guaranteeing decision |
|---|---|---|
| Alphabet | closed `Σ_HG = {V, C, P, N, W}` | §3; S2H totality §5 |
| Decoding | deterministic, total interpreter (never rejects) | §5 |
| Round-trip | `H2S(S2H(w)) = w`, `S2H(H2S(H)) ≅ H` | §5; invariant 3 |
| Canonical order | shortlex `(length, token tuples)`, `W<N<P<V<C` | §3 |
| Seed set | iso-invariant (neighbour-degree cascade; `ξ` cascade also sound) | §6.2; invariant 4 |
| Canonical form | `w*_c` = unpruned tie-complete shortlex-min, frozen (D-TA2) | §6.6 |
| Fingerprint | `F(H) = (seed label, w*_c(H))` | §6.7 |
| Completeness | `F(H₁)=F(H₂) ⟺ H₁≅H₂` for `"canonical"` | §7 (Theorem A) |
| Induced metric | `d_I = d_Lev(w*_c(H), w*_c(H'))`, iso-invariant | §9 |
| Worst case | `(j!)^E`-type on vertex-transitive designs; `O(edges)`/frame sparse | §8 |
| Implementation | C++ core, byte-identical to Python reference | §6, §8 |

---

## References

- Lopez-Rubio, E. & Pascual-González, M. *Representation of Graphs by Sequences
  of Instructions*. Preprint, 2026. (IsalGraph — the parent representation.)
- Lopez-Rubio, E., Pascual-González, M. & Thurnhofer-Hemsi, K. *Representation
  of Directed Acyclic Graphs by Sequences of Instructions for Symbolic
  Regression*. IEEE TPAMI submission, 2026. (IsalSR — the DAG variant.)
- Lopez-Rubio, E. *IsalHG seed proposal*. 2026. (`docs/isalhg_idea.pdf`.)
- Levenshtein, V. I. *Binary codes capable of correcting deletions, insertions,
  and reversals*. Soviet Physics Doklady 10(8):707–710, 1966. (The string
  metric `d_I` is built on.)
- McKay, B. D. & Piperno, A. *Practical graph isomorphism, II*. J. Symbolic
  Computation 60, 2014. (nauty/Traces — the canonical-form iso paradigm and the
  speed baseline.)
- Junttila, T. & Kaski, P. *Engineering an efficient canonical labeling tool for
  large and sparse graphs*. ALENEX 2007. (bliss — baseline.)
- Feng, Y., Han, J., Ying, S. & Gao, Y. *Hypergraph isomorphism computation*.
  IEEE TPAMI 46(6):3880–3894, 2024. (Hypergraph-WL; the hypergraph-native iso
  context.)
- Qin, L. et al. *Explainable Hyperlink Prediction: A Hypergraph Edit
  Distance-Based Approach*. ICDE 2023. (HGED — the structural distance on the
  right-hand side of the stability bound.)
- Chuang, C.-Y. & Jegelka, S. *Tree Mover's Distance: Bridging Graph Metrics and
  Stability of GNNs*. NeurIPS 2022. (The single-edit stability proof template.)
- Chen, S., Lim, S., Mémoli, F., Wan, Z. & Wang, Y. *The Weisfeiler-Lehman
  Distance*. PMLR 221 (TAG-ML @ ICML), 2023. (Closest published proxy for
  Levenshtein-on-canonical-string with a Lipschitz upper bound.)

*Proof artifacts:* `proofs/theorem_a_completeness.{tex,pdf}` (Theorem A,
admissible-pruning lemma, Proposition 6.0); `proofs/stability/` (Theorem B).
*Code:* `core/{instructions,string_to_hypergraph,hypergraph_to_string,
structural_tuples,canonical}.py` and `core/_native/src/{h2s,canonical,
structural_tuples,sparse_hypergraph}.cpp`.
