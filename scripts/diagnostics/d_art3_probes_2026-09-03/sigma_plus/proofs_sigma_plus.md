# Proof sketches for `Σ⁺` — Propositions 2⁺ and 4

Notation. VM state `S = (H, L, p_1 … p_k)`; `n(S) = |V(H)|`. Vertices are
numbered in creation order, `rank(v) = ` creation index, seed = rank 0
(`SparseHypergraph.add_node` appends, so `rank ≡ NodeId`). Clamp
`ρ_S(r) = min(max(r,0), n(S)−1)`. `Σ⁺ = Σ_HG(k) ∪ {A, A⁺}`.

## Proposition 2⁺

**(i) Conservativity.** `S2H⁺ ↾ Σ_HG* = S2H`.
*Proof.* The `S2H⁺` step function on `W, P, N, C, V` is defined by the same
operations on the same components as `S2H` (same `CircularDoublyLinkedList`,
same `KPointerSet`, same `add_node` / `add_hyperedge` call sequence, same
CDLL pre-allocation `1 + Σ_V j`). Induction on the token count gives identical
states after every prefix, hence identical outputs. ∎
*Measured:* 2 000 random `Σ_HG(3)` words — 2 000/2 000 identical structural keys;
1 891 canonicalizable, 1 891/1 891 identical `w*_c`.

**(ii) Totality.** Every `w ∈ Σ⁺*` executes without raising.
*Proof.* Induct on prefixes with invariant `I(S)`: `n(S) ≥ 1`, the CDLL holds
exactly the `n(S)` vertices, every `p_i` is a live slot. The initial state (seed
alone) satisfies `I`. Package tokens preserve `I` (Prop. 2 of the preprint).
`A[ℓ; r_1…r_a]`: `ρ_S(r) ∈ [0, n−1]` is a live vertex because `n ≥ 1`; the
support `ρ_S({r_i})` is non-empty because `a ≥ 1`, so `add_hyperedge` is legal;
a repeated `(ℓ, support)` is absorbed by the edge lookup; no CDLL or pointer
change, so `I` holds. `A⁺[ℓ; λ; r_1…r_i]`: the clamp is evaluated at `n ≥ 1`
(**hypothesis A1**, see below), then one vertex is appended and inserted after
the live slot `p_1`, so `I` holds. Capacity is never exceeded: the CDLL is
pre-allocated to `1 + Σ_V j + #A⁺`, exactly the number of vertices `w` can
create. ∎

**(iii) Connectivity.** `S2H⁺(w)` is connected for every `w ∈ Σ⁺*`.
*Proof.* Induction with "every vertex lies in the seed's primal component".
Base: the one-vertex hypergraph. `W, P, N` leave `H` alone. `C` and `A` add an
edge over pre-existing vertices — adding an edge never disconnects. `V` adds
`j` fresh vertices inside one edge that also contains the pre-existing `p_1`
(`i ≥ 1`), so they join `p_1`'s component. `A⁺` adds one fresh vertex inside one
edge that also contains `ρ_S(r_1)`, a pre-existing vertex (`i ≥ 1`), so it joins
that component. ∎
**Hypothesis the design does not state:** `a ≥ 1` for `A` *and* `i ≥ 1` for
`A⁺` are load-bearing. With `i = 0`, `A⁺` would create an isolated vertex and
(iii) would fail. The stated ranges `1 ≤ a ≤ k`, `1 ≤ i ≤ k−1` already give this.
*Measured:* 20 000 random `Σ⁺(3)` words of length 1–40 with arbitrary
(out-of-range 97.3 %, repeated, unsorted) ranks — 0 exceptions, 0 disconnected,
0 duplicate edges.

## Proposition 4 (fact-level simulation, anchored encoding `E1⊤`)

Setting. `K` a knowledge base, `E1⊤(K) = H`: anchor `⊤`, a `dom` edge `{⊤, c}`
per constant, facts as hyperedges labelled `1…r`. `w = w*_c(H)`,
`H_0 = S2H(w) ≅ H` the rank-numbered copy, `a = rank_{H_0}(⊤)`.

**(a) Insertion costs one token.** For a fact `f = (ℓ, S)`, `S ⊆ constants(H_0)`,
`1 ≤ |S| ≤ k`, `f ∉ E(H_0)`: `S2H⁺(w · A[ℓ; S]) = H_0 + f`, and
`d_Lev(w, w·A[ℓ;S]) = 1`.
*Proof.* At the end of `w` the vertex count is `n(H_0)`, and every `s ∈ S` is
the rank of an existing vertex, so no clamp fires (**hypothesis H1**); `A` has
no other effect. ∎ *Measured:* 1 200/1 200 (60 KBs × 20 sampled insertions).

*Position independence (used by the ball argument and by the Task-4 reduction).*
`A` touches neither the CDLL nor the pointers, and edge insertion commutes with
every later operation, so inserting `A[ℓ;S]` at **any** position `p` yields
`S2H⁺(w) + (ℓ, ρ_{S_p}(S))`. Hence the set of objects reachable by inserting one
`A` token equals `{ S2H⁺(w) + (ℓ,S') : |S'| ≤ k }`.

**(b) Deletion of a `C`-created fact costs one token.** If the first token of
`w` that creates `f` is `C` at position `p`, and no other token of `w` creates
`f` (**hypothesis H2**, uniqueness of the creator), then
`S2H⁺(w \ p) = H_0 − f`.
*Proof.* `C` changes neither the CDLL nor the pointers, so removing it leaves
every other token's execution bit-identical; the only difference is the absent
edge. ∎ *Measured:* 710/710 (`t3`) + 463/463 (`t3b`); 0 creator-misses in 1 197
facts, so H2 held everywhere on `w*_c`.

**(c) Deletion of a `V`-created fact costs `j` tokens.** If `f` is first created
by `V[ℓ; i; j; λ_1…λ_j]` at position `p`, then
`w' = w[:p] · A⁺[dom; λ_1; a] ⋯ A⁺[dom; λ_j; a] · w[p+1:]`
satisfies `S2H⁺(w') ≅ H_0 − f`, at token cost `j` (one substitution plus `j−1`
insertions).
*Proof.* Both programs create exactly `j` vertices at position `p` and insert
each of them after the same slot `p_1`, so after position `p` the two CDLLs have
the same length and the same cyclic order *of positions*; let `φ` be the induced
position bijection. Under `φ` the two partial states differ only in that the `V`
run holds the edge `f` while the `A⁺` run holds the `j` edges `{⊤, u_t}`. Under
`E1⊤` each of those `dom` edges is created again later in `w`, so the `A⁺` run's
final edge set is `E(H_0) − {f}`; every later token acts through pointer
positions, which `φ` preserves. ∎
**Hypotheses:** H3 — `⊤` already exists at position `p` (`a < n` there), so the
`A⁺` clamp does not fire; H4 — the `j` fresh vertices are constants, not `⊤`.
**Correction the design needs (measured, not hypothetical).** `A⁺` inserts each
fresh vertex *after `p_1`*, so a run of `j` such tokens lays the block out in the
**reverse** CDLL order from `V`: for `j = 2`, `V` gives CDLL `[0,1,2]` and the
`A⁺` run gives `[0,2,1]` (`t3b` part 1). The witness is nevertheless correct,
because at the instant of creation the `j` fresh vertices are mutually
interchangeable (each carries exactly one new `dom` edge), so `φ` is an
automorphism of the partial state and only *renames* the block. What is **not**
preserved is the block's rank numbering: `φ` reverses it. Consequences: the
witness realizes `H_0 − f` **up to a rank permutation of the `j` fresh
constants**, so an iterated (multi-step) witness must recompute ranks after each
`A⁺` run; and if the design ever wants `S2H⁺(w') = H_0 − f` on the nose rather
than up to isomorphism, `A⁺` must insert after the previously inserted fresh
vertex when it directly follows another `A⁺` (or the block must be emitted in
reverse). *Measured:* 5/5 (`t3`) + 17/17 (`t3b`) `j = 2` witnesses correct
up to isomorphism; 0 failures.

**(d) Ball inclusions.** Write `B_r(w)` for the token-Levenshtein ball and
`reach(K → K') ≤ r` for `class(K') ∈ classes(S2H⁺(B_r(w*_c(K))))`.
1. If `K'` is `K` plus `r` fact insertions, then `reach(K → K') ≤ r`: append the
   `r` `A` tokens of (a); the appends commute and no clamp fires, so the ball of
   radius `r` contains a witness.
2. If `K'` is `K` after `r` fact edits, then `reach(K → K') ≤ (k−1)r`: each
   insertion costs 1 by (a) and each deletion costs `1` or `j ≤ k−1` by (b)/(c).
Both directions are **inclusions only**. The converse fails: a pointer-token
edit rewrites the decoded object globally, so `reach ≤ r` does not bound the
number of fact edits.
*Measured (`t4`, 48 profiles):* family I, `t = 1` — `cov_1(H_0) = 7/7` in 12/12
profiles; family I, `t = 2` — `cov_1(H_0) = 0/7`, `cov_2(H_0) = 7/7` in 12/12.
Exactly the prediction of (d.1).

## Hypotheses the design did not state

1. **A1** — `A⁺` clamps against the vertex count *before* creating the fresh
   vertex (otherwise an out-of-range rank collapses onto the fresh vertex and the
   edge loses arity).
2. `a ≥ 1` / `i ≥ 1` are needed for connectivity (Prop. 2⁺ iii).
3. **H1** (no clamping on insertion witnesses), **H2** (unique creator token),
   **H3**/**H4** (the anchor precedes the replaced `V` token and is not among
   its fresh vertices).
4. The design says "attach each fresh constant to the anchor **at rank 0**".
   The anchor is the canonical seed only when it wins the neighbour-degree
   cascade outright — measured 295/300 (98.3 %) on `E1⊤` KBs with 8–12
   constants; the other 1.7 % put the anchor at rank 1. Witnesses must address
   the anchor by its **measured** rank, not by the constant 0.
5. The rank-reversal caveat of (c).
6. Clause (c) is a theorem **about `E1⊤`**, not about `Σ⁺`. On a non-anchored
   encoding there are no `dom` edges to re-attach the `j` fresh constants to, so
   a `V`-created fact has *no* bounded-cost deletion witness at all — measured
   in `t4`, where family-D coverage is capped by the `C`-created share of the
   edges (mean 4.5–8.2 of 8–14 edges).
