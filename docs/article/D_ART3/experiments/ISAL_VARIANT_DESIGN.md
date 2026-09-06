# The Isal instruction word for knowledge bases — pre-registered design

*Written 2026-09-06 by the Isal-refinement agent, before any measurement, as
the working annex of D-ART4 (`../../DEVELOPMENT/DECISIONS.md`) and the answer
to `ISAL_REFINEMENT_BRIEF.md` §8 deliverable 1. Everything here is either a
definition, a theorem sentence with its proof file, a directional hypothesis,
or a selection rule fixed before the numbers exist. Companion proof:
`/media/mpascual/Sandisk2TB/research/ISAL/isalhg/proofs/completeness/theorem_c_ordered_walk.tex`.*

---

## 0. What is being decided, and the constraint that decides it

The paper's representation of a knowledge base is an **instruction string for
the Isal machine** — the CDLL, `k` pointers, `Σ_HG = {V, C, P, N, W}`, decoded
by `S2H` — and nothing else (D-ART4; the fact-rank word is out because it has
no machine). Two measured restrictions keep the family's canonical string
`w*_c` (the tie-complete lex-min over walks) from serving the knowledge-base
tasks: **R1 locality** (one edit rewrites 49–79 % of the word) and **R2
symmetric-input cost** (censored on 41–100 % of members with `|Aut| ≥ 10³`).

Both restrictions have the same root: `w*_c` is the *minimum* of a
presentation-dependent search. The minimum is discontinuous under edits (R1)
and the search must explore every ordering of automorphic constants because it
cannot tell they are automorphic (R2). The design below removes the search
from the *representation* and keeps it, orbit-pruned, as the family's own
canonical algorithm:

- **The representation (option B of the brief): the ordered walk `w°`.** A
  deterministic Isal program emitted along a canonical labelling of the
  constants. No lex-min, no branching. Complete by Theorem C; cost = one
  canonical-labelling call + linear emission; locality is a property of the
  emission policy and is measured, not assumed.
- **The family's canonical algorithm made computable (option A): `w*_c` with
  stabiliser-orbit pruning.** Value-preserving (Proposition 6.1 of the
  completeness proof), so D-TA2 stands untouched; it removes R2 from `w*_c`
  and leaves R1 as the measured reason `w*_c` is not the paper's
  representation.

Where nauty enters: in `w°` it supplies the canonical order (individualisation
–refinement, McKay–Piperno 2014); in orbit-pruned `w*_c` it supplies the
automorphism group of the placed prefix. In both cases nauty is a subroutine of
an Isal encoder whose output is an Isal program; the paper's sentence is fixed
in §7.

**Assumptions taken from the principals' record, flagged for confirmation.**
(A1) "nauty inside the Isal methodology" is accepted (first author, D-ART4
addendum). (A2) `Σ_HG` is unchanged — no new instruction; every variant is a
choice of *canonical program*, not of alphabet. (A3) The PI must supersede
D-TA2 only if the paper's *representation* changes value; `w°` is a new
canonical form beside the frozen `w*_c`, not a replacement of its definition.
(A4) An RQ whose Isal row cannot beat the certificate rows is reported as a
characterisation and moved to the supplement (the author's rule of 2026-09-06).

---

## 1. Definitions (the objects the theorems are about)

**Knowledge base.** A connected labelled hypergraph `H = (V, E, ℓ_V, ℓ_E)`:
constants `V` with type labels, facts `E ⊆ 2^V` (each of arity `2 ≤ |e| ≤ k`)
with predicate labels; no two facts share `(label, member set)`. Isomorphism
is a type-preserving bijection of constants carrying facts to facts with equal
predicates.

**Canonical relabelling `H_ρ`.** Let `B(H)` be the coloured Levi graph
(`core/levi_reduction.py::to_levi`: constant nodes coloured by type, fact nodes
by `|Σ_V| + predicate`). Let `ρ = canon_label(B(H))` (nauty) and let
`rank(v)` be the position of constant `v` among constant nodes in `ρ`-order
(`iso_backends/canonical_order.py::canonical_ranks`). `H_ρ` is `H` with
constants renamed to their ranks. **Lemma C.1:** `H ≅ H' ⟺ H_ρ = H'_ρ` as
labelled structures (canonical-form property of `canon_label` + the Levi
correspondence, which is bijective because facts are deduplicated).

**The ordered walk `OW_π(H_ρ, k)`.** A deterministic emitter driven by a
policy `π = (root rule, V-key, C-key, move rule)`. It simulates the Isal VM
and never searches:

```
state: L (CDLL), p_1..p_k (slots), placed ⊆ V with creation index c(·),
       consumed ⊆ E
root r := argmax_v (deg_E(v), ℓ_V(v)); ties → min rank          [root rule]
L = [r]; all pointers on r; c(r) = 0

V-phase — while placed ≠ V:
    cand := { e ∉ consumed : e ∩ placed ≠ ∅ and e \ placed ≠ ∅ }
    e*   := argmin_{cand} K_V(e)                                  [V-key]
    anchor a := placed member of e* with min c;  others := the rest, by c ↑
    move p_1 → a, p_2..p_i → others (i = |e* ∩ placed|)           [move rule]
    new  := e* \ placed ordered by (ℓ_V, rank) ↑
    emit  moves · V[ℓ_E(e*); i; |new|; ℓ_V(new_1..new_j)]
    (S2H inserts new_1..new_j right after p_1, in that order)
    assign c(new_t) := next creation indices; consumed ∪= {e*}

C-phase — for e in (E \ consumed) sorted by K_C(e):               [C-key]
    targets := members of e by c ↑ ;  move p_t → targets_t
    emit  moves · C[ℓ_E(e); |e|]
```

Default policy **`ow-struct`** (structural keys first, canonical rank last):

- `K_V(e) = ( c(a(e)), ℓ_E(e), |e ∩ placed|, |e \ placed|,
  [c(v)]_{v ∈ e∩placed} ↑, [sig(u)]_{u ∈ e\placed} ↑, [rank(u)]_{u ∈ e\placed} ↑ )`
  — facts hanging from earlier-created constants first (a breadth-first walk
  from the root), then by predicate, arity split, the placed members'
  creation indices, the new constants' **local signature**
  `sig(u) = (ℓ_V(u), sorted multiset of (ℓ_E(e'), |e'|) over e' ∋ u)` — an
  invariant that changes only when `u`'s own facts change — and only then
  their ranks. In a binary star the signature classes are automorphism
  classes, so the rank never reaches the word (Prop. C.5).
- `K_C(e) = ( [pos(v)]_{v ∈ e} ↑ , ℓ_E(e) )` where `pos(v)` is the number of
  backward steps from the root's slot to `v`'s slot at the start of the
  C-phase — a sweep of the closing facts in CDLL order; `p_t` takes the
  `t`-th member by `pos`. In a star `pos = c` (creation order), so the sweep
  is monotone and a leaf insertion changes exactly one run.
- Move rule (**no crossing**, revised 2026-09-06 after the emitter agent
  measured the "shorter direction" rule: a run rendered forward has length
  `N − gap`, grows under every insertion and flips at `N/2` — max cost 22 on
  400 random binary stars vs exactly 2 in the backward regime): every move
  is computed in backward-position coordinates from the root's slot without
  wrapping, `Δ = pos(target) − pos(current)`; `Δ > 0` → `Δ` tokens `N`,
  `Δ < 0` → `|Δ|` tokens `P`. No move passes over the root; every run length
  is the number of slots between the two positions on the root-free arc, so
  an insertion elsewhere never changes it. Rendered in the H2S convention
  (all `N` by pointer index, then all `P`).

Ablation policies (option D of the brief): **`ow-rank`** — `K_V` with the
new constants' ranks *before* the predicate (the order is nauty's, the
structure second); **`ow-rank0`** — root = the constant of rank 0 instead of
the hub rule. Both are complete by the same theorem; they exist to show which
part of the policy buys locality.

**Fingerprint and distance.** `F°(H) = (ℓ_V(r), w°(H))` — the root's type is
not emitted by any `V` (same reason as `F = (seed label, w*_c)`, `rem:augment`
of the completeness proof). `d°(H, H') = d_Lev` on the root-label-prefixed
token sequence, at instruction granularity (one symbol per `V`/`C`/`P`/`N`)
and, for the campaign's matched tokenisation, at field granularity
(`experiments/tkde/budget.py::symbol_distance`). Both are reported; the
instruction-level number is the paper's (L7, L11).

**Orbit-pruned `w*_c`.** The tie-complete search of `hypergraph_to_string.py`
(`tie_branch=True`) with, at every residual tie `T(σ)`, the branch set reduced
to one representative per orbit of `G_σ := Stab_{Aut(H)}(dom μ)` acting on
`T(σ)`, and per representative `e` one label-respecting ordering of `U(e)` per
orbit of `G_σ ∩ Stab_set(e)`. `G_σ` is obtained as `autgrp` of `B(H)` with the
placed constants individualised in prefix order. Seeds are likewise reduced to
one per `Aut(H)`-orbit of `S(H)`. Output: `w*_c`, bit-identical.

---

## 2. Theorem sentences (proof file: `theorem_c_ordered_walk.tex`)

| id | statement | status |
|---|---|---|
| Lemma C.1 | `H ≅ H' ⟺ H_ρ = H'_ρ` | standard (McKay–Piperno) + Levi correspondence; proved in the file |
| Lemma C.2 | `OW_π` terminates on every connected `H` with arity ≤ `k`, every emitted token is alphabet-valid, and pointers `p_1..p_i` are on distinct slots at every `V`/`C` | proved |
| Lemma C.3 (round trip) | `S2H(w°(H); k, ℓ_V(r)) ≅ H` via `c^{-1}` | proved (the emitter *is* an S2H run) |
| **Theorem C** | for connected labelled `H, H'` encoded with the same `k` and vocabularies: `F°(H) = F°(H') ⟺ H ≅ H'`, for every policy `π` | proved (⇐ C.1 + determinism; ⇒ C.3) |
| Corollary C | `d°` is a metric on isomorphism classes | from Theorem C as Corollary A from Theorem A |
| Proposition C.4 (closed, connected language) | every `w ∈ Σ_HG(k)*` decodes, and `S2H(w)` is connected with no isolated constant beyond the trivial word | proved (induction on `V`: each new constant is created inside a fact containing `val(p_1)`) — the "easy induction" `START_HERE.md` §2 promised |
| Proposition C.5 (star locality) | on a *binary star* (every fact binary and containing the root `r`, `r` of unique maximum degree): a leaf insertion changes `w°` by one `V` instruction and at most one unit of one `N` run (`d_Lev ≤ 2`); a closing-fact insertion whose predicate does not precede the leaf's creator costs one `C` and one split run (`d_Lev ≤ 2` when a later leaf is already targeted); a creator flip costs a constant number of instructions plus the leaf's displacement in the creation order — never the tokens of facts not incident to the edited leaf | proved for `ow-struct`; the arity ≥ 3 channel (rank flips inside a signature class) is named and left to measurement (zero-shift) |
| Proposition C.6 (name-freedom) | `w°` depends on `ρ` only through the relative order of constants inside each `K_V`-class and the induced `c`; a change of `ρ` that permutes constants within classes whose emitted sub-programs coincide and preserves the `c`-order of the members of every closing fact leaves `w°` unchanged, whereas every rank-addressed serialisation changes in every row that names a re-ranked constant | proved; the mechanism behind hypothesis H-M1c |
| Proposition C.7 (orbit pruning is value-preserving) | the orbit-pruned tie-complete search returns `w*_c`; `autgrp` of the prefix-individualised Levi graph is `G_σ` | proved from `prop:coherent` + `lem:forest` of the completeness proof + the individualisation lemma |

What is **not** claimed: any Lipschitz relation to fact-level edit distance
(the frontier prose stands; Theorem B's refutations stand); locality outside
the star hypothesis of C.5 (measured, not proved); that `w°` is Isal-native
without nauty (the tie-complete search with orbit pruning over the residual
refinement ties is the nauty-free reading — option C of the brief — and is
future work, stated as such).

---

## 3. Hypotheses (directional, fixed now)

Arms on every RQ1 table: `wstar` (= `w*_c`, C++ engine, 60 s), `wstar_600`
(the same on the 60 s-censored tail at 600 s), `wstar_orbit` (the orbit-pruned
Python engine, 60 s), `ow_struct`, `ow_rank`, `ow_rank0`, `nauty_cert`,
`nauty_cert_rows`; `fact_rank` stays on the table as the record (D-ART4 (1)),
not as ours. Corpora: `synthetic_rq1`, `ndc_classes`, `wd50k66` (the RQ1 three).

| id | hypothesis | direction | decides |
|---|---|---|---|
| H-M0 | every `ow_*` and `wstar_orbit` arm is exact and relabelling-invariant: 0 false merges / 0 false splits / 0 invariance violations on all three corpora | equality | acceptance gate (non-negotiable) |
| H-M1a | constant-set-preserved single-edit response of `ow_struct`, in absolute instructions: median ≤ 2 on `insert_fact` / `delete_fact`; normalised response below `wstar`'s on all three corpora; "within ≤ 2 instructions" fraction above `wstar`'s | lower / higher | the R1 lift |
| H-M1b (relative addressing) | on `insert_fact_new_constant` and `add_constant`, the `ow_struct` response is bounded (median ≤ 2 instructions, no growth with `m`), while `nauty_cert_rows` grows with the number of rows after the shifted rank | bounded vs growing | the Isal-specific advantage of D-ART4 (2a)(i) |
| H-M1c (name-freedom) | restricted to edits where nauty's order shifts (`zero_shift = 0`), `ow_struct`'s response is below `nauty_cert_rows`' at matched tokenisation | lower | Proposition C.6 made visible |
| H-M1d (policy) | `ow_struct` ≤ `ow_rank` ≤ `ow_rank0` in median response on every corpus | ordering | which part of the policy matters |
| H-M2 | monotonicity `ρ(budget, d°)` on NDC natural series and WD50K ladders ≥ `wstar`'s (0.961 / 0.553) | higher | the ladder axis |
| H-M3 | `ow_*` cost: median < 10 ms, 0 censoring at 60 s on all corpora and in every `|Aut|` bucket; `wstar_orbit` completes more of the `|Aut| ≥ 10³` members than `wstar` at 60 s | lower / higher | R2 |
| H-M4 | Spearman ρ(`d°`, `d_cert_rows`) ≥ 0.6 on every corpus (the two are serialisations of one canonical labelling; the residual is the emission) | ≥ | the "is nauty doing the work" reading |
| H-A (bit-exactness) | `wstar_orbit` reproduces the frozen `w*_c` on Fano, STS(9), `C_13(0,1,3)`, GQ(2,2), the `n=4` counterexample, both STS(13); and equals the unpruned Python engine on ≥ 500 random labelled hypergraphs (`n ≤ 8`) | equality | acceptance gate for option A |

### 3b. The nauty ablation (author's ruling, 2026-09-06)

The author accepted both uses of nauty and asked for a four-cell ablation —
*no nauty / order only / oracle only / both*. The cells, as canonical
programs of the same machine (every one decoded by `S2H`):

| cell | arm | canonical program | nauty's job | completeness | expected R1 / R2 |
|---|---|---|---|---|---|
| no nauty | `wstar` | tie-complete lex-min over walks (`w*_c`, C++ engine) | none | Theorem A | non-local / censored on symmetric inputs |
| oracle only | `wstar_orbit` | the same `w*_c`, search pruned to one branch per stabiliser orbit | automorphism oracle at ties and seeds | Theorem A (value preserved, Prop. C.7) | non-local / computable |
| order only | `isal_ow_struct` (+ `ow_rank`, `ow_rank0`) | deterministic ordered walk along the canonical order | supplies the order | Theorem C | local (measured) / microseconds |
| both | `wstar_rank` | the family's greedy walk (displacement search + 7-rung cascade) with the residual tie set and the new-vertex order resolved by rank — D-ART4 option (2a)(i) | the order, used *inside* the Isal search as the tie key (`lem:pruning`); the oracle is unnecessary because ties collapse | Theorem C's argument (deterministic function of `H_ρ` that round-trips) | between `wstar` and `ow` on both axes (measured) |

Reading the table answers the reviewer's "is nauty doing the work?" twice:
the oracle cell shows what symmetry handling alone buys (R2, not R1); the
rank cell shows what borrowing only the *tie key* buys while keeping the
family's own walk. `wstar_rank` is a new canonical value, not `w*_c`.

**Selection rule (pre-registered).** Among the `ow_*` arms passing H-M0 with
0 censoring, adopt the one with the highest constant-set-preserved
"within ≤ 2 instructions" fraction pooled over the three corpora, ties broken
by the lower median absolute response. Report the losers in the same table.
If no `ow_*` arm beats `nauty_cert_rows` on H-M1a, the paper argues from the
language alone (D-ART4 (1) already anticipates it) and the number is printed.

---

## 4. Measurement protocol (RQ1 re-run; `DESIGN.md` §2 M0–M4 unchanged)

- **M0** exactness: relabelling invariance (27 random relabellings per member
  under the corpus seed) + nauty-partition false-merge/false-split census, per
  corpus. *Pass = 0/0/0.*
- **M1** single-edit response: the five edit kinds of `DESIGN.md`
  (`insert_fact`, `delete_fact`, `add_constant`, `remove_constant`,
  `insert_fact_new_constant`), regime flag `constant_set_preserved` stamped
  from constant identities; per (arm, corpus, kind, regime): absolute median
  in instructions and in campaign symbols, normalised median, within-≤ 2
  fraction, `zero_shift` fraction (nauty order intact). Paired Wilcoxon +
  Holm across arms, rank-biserial effect, 27 seeds, BCa 95 % (G5).
- **M2** monotonicity: NDC consecutive quarters (natural series, exact Δ) and
  WD50K constant-preserving ladders; Spearman ρ(budget, d) per arm.
- **M3** cost and censoring: per member wall-clock under the forked-child
  budget; censoring per `(m bucket, |Aut| bucket)` (the probe's table), with
  `|Aut|` from `pynauty.autgrp` on the coloured Levi graph.
- **M4** ρ against `nauty_cert` and `nauty_cert_rows` on the same pairs.
- Tokenisation: every response is reported at instruction granularity and at
  `symbol_distance` granularity; every certificate comparison is made against
  `nauty_cert_rows` as well as `nauty_cert` (audit §1.2 item 2).
- Persisted under `results/IEEETKDE/RQ1_isal/` with `tables.md`,
  `stats.json`, `manifest.json`, provenance stamps naming the tree that served
  the library.

---

## 5. After RQ1: the encoder swap for RQ2–RQ7

The RQs are encoder-agnostic (D-ART4 (3)); the adopted `ow_*` arm (and
`wstar_orbit` where its envelope allows) gets a row in each:

| RQ | what the Isal row needs | expected reading (pre-stated) |
|---|---|---|
| RQ2 well-posedness | Theorem C + M0; identity timing | exact, metric, polynomial; identity slower than the certificate engines (R6, conceded) |
| RQ3 representative | canonical key = `F°`; decoder = `S2H` (interiors connected by construction, Prop C.4) | carries over; the consensus is a decoded Isal program no member wrote |
| RQ4 screen | `N×N` matrix of `d°` | iso-twin exactness consequence holds; standard-corruption AUC at the certificate's level (characterisation, supplement) |
| RQ5 patterns | `N×N` matrix; `ν`, hubness | licences reported; no type recovery (supplement) |
| RQ6 generation | token model over `w°`; decodability of interiors | validity 1 *and connectivity* by theorem; stronger than the fact list's 68.6 % connected interiors |
| RQ7 envelope | cost sweep over `(m, k, |Aut|)` | `ow_*` inherits nauty's envelope; `wstar_orbit` moves the `w*_c` frontier from `|Aut|` to `m` |

Order of work (D-ART4 note (d)): RQ1 → choose → RQ2–RQ7.

---

## 6. Implementation map (what goes where; `CODE_DESIGN.md` §1 leaves)

| piece | location | layer rule |
|---|---|---|
| ordered-walk emitter (stdlib; consumes a rank sequence) | `src/isalhg/core/algorithms/ordered_walk.py` — `OrderedWalkPolicy` (frozen dataclass), `ordered_walk(H, ranks, k, policy) -> (root_label, TokenSequence)` | `core/` stays stdlib-only: ranks are injected |
| nauty-backed entry point | `src/isalhg/iso_backends/isal_ordered.py` — `ordered_word(H, k=None, policy=...)`, `ordered_fingerprint(H, ...)` | imports `pynauty` inside the body via `canonical_ranks` |
| orbit oracle protocol + pruned branch | `core/hypergraph_to_string.py` (the `tie_branch` V-branch takes an optional `orbit_oracle`), `core/canonical.py` (`algorithm="canonical_orbit"`, Python backend) | oracle is a `Protocol` in `core`; no nauty import there |
| pynauty orbit oracle | `src/isalhg/iso_backends/orbit_oracle.py` — individualised Levi colouring → `autgrp` → orbits on tied edges and on new-vertex orderings | |
| harness arms | `experiments/tkde/matrices.py` (`DEFAULT_SPECS`), `experiments/tkde/rq1.py`, `rq7.py` (the `|Aut|` axis) | mirrors the `pointer` arm |
| tests | `tests/unit/core/test_ordered_walk.py` (round trip vs pynauty iso, invariance under 200 random relabellings per fixture, alphabet validity, golden `(len, sha256)` pins per fixture, Prop C.5 as a unit test on a synthetic star), `tests/unit/core/test_orbit_pruning.py` (frozen pins bit-exact; differential vs unpruned on ≥ 500 random instances; branch-count collapse on a 12-leaf symmetric star), `tests/property/test_ordered_walk_roundtrip.py` (hypothesis) | |

Golden pins for `w°` get their **own** table (never the `w*_c` table: they
are different strings by construction).

---

## 7. The sentence the paper uses for nauty

> The canonical order of the constants is computed by nauty's
> individualisation–refinement on the coloured incidence graph; the Isal
> encoder then emits, along that order, a program for the Isal machine.
> nauty decides *which* constant comes first; the language decides *what* is
> written, and every string of that language decodes to a knowledge base.

For the orbit-pruned `w*_c`: "nauty supplies the automorphism group of the
placed prefix, which the family's tie-complete search uses to explore one
branch per orbit; the string returned is the frozen `w*_c`."

---

## 8. Points that need the PI (flagged, not decided here)

1. **D-TA2 and the representation.** `w°` is a second canonical form of the
   family beside `w*_c`. If the paper's tables run on `w°`, the PI ratifies
   that the paper's canonical string is `w°` and that `w*_c` is reported as
   the family's search-based form with its measured restriction. D-TA2 itself
   (the definition of `w*_c`) is not touched.
2. **nauty as order vs nauty as oracle.** Both uses are in this design; the
   PI chooses the sentence (§7) that goes in the paper, or both.
3. **Roles (R4).** A per-slot role pattern folded into the fact label
   (`(predicate, role of p_1, …, role of new_j)`) with an incidence-subdivided
   Levi colouring is representable without touching `Σ_HG`; it is *not* in
   this pre-registration's measured arms and is filed as a ledger task.
