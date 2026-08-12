# Competitors v5.1 — what we concede, and what is left to compare

*Proposed replacement for `../COMPETITORS.md`. Status: pending PI.*
*Revised 2026-08-12: the v5.0 draft framed Set B as a fight over isomorph-free
generation. We would lose it. Set B is now a **conceded comparison** — reported
because honesty requires it and because it isolates what the instruction-string
form actually contributes, not because we expect to win it.*

## 0. The conceded comparisons (stated in the introduction, not buried)

| Task | Winner | Evidence |
|---|---|---|
| Decide isomorphism / canonize one object | **`nauty` / `bliss` / Traces on the Levi reduction** | measured: `w*_c` costs 617 s on PG(3,2) and > 900 s on rigid STS(15) where nauty is milliseconds |
| Deduplicate a collection of hypergraphs | **the same engines** — equally exact (both complete), and faster | same |
| Isomorph-free exhaustive generation | **`nauty`-based canonical augmentation** (McKay 1998) | the state of the art; our invariant is the slow one |
| "Does a finite countermodel exist? Find one." | **MACE-style SAT/SMT finders** (Mace4, Paradox, cvc5-FMF, Vampire-FMB) | propagation prunes semantically; enumeration prunes only structurally |
| Small-perturbation task geometry (clustering, kNN) | **nauty-Levi edit**, then HPD, then NetLSD | measured on Stratum C: ARI up to 0.614 vs our 0.016–0.028 |

Conceding these up front is not a weakness of the paper; it is what makes the
remaining claim readable. Everything below compares on what is left.

Under v3 there was one competitor set — five representations plus two naive
floors — compared on one axis family (task metrics on a dissimilarity matrix).
Under v5 there are three workloads with genuinely different fields, and merging
them into one table would be dishonest in both directions: it would flatter us on
enumeration (where representation baselines cannot compete at all) and mislead on
model finding (where the real competitors are not representations).

---

## 1. Set A — representations (retained, re-scoped)

Unchanged membership, unchanged implementations (all four landed at T-M3): WL
colour histogram, NetLSD on the Levi expansion, HyperCOT, Hyperedge Portrait
Divergence, plus the `nauty`-Levi canonical-string edit distance as contrast and
the two naive floors `degree_seq_l1` / `size_l1`.

**What changes is where they appear.**

| Workload | Set A's role |
|---|---|
| Measured limits (A2/A3, Stratum C) | full head-to-head, frozen, reported as measured — and lost |
| Geometry table | full head-to-head on the four invariants |
| **C5 completeness price** | each incomplete representation's key is grouped and its non-isomorphic collisions counted against the `pynauty`-Levi ground truth. **`w*_c` and nauty both score zero — reported as a tie.** The target is the embeddings, not nauty |
| C3 navigation | vector members score path monotonicity only; none has an ambient space whose points are objects |
| C1 search framework | **not applicable** — an incomplete key silently deletes objects from a frontier |

**The nauty-Levi baseline changes status again.** Under v3 it was the "contrast
baseline" meant to show that canonical labelling yields no navigable geometry —
and it then won A2/A3. Under v5.1 it is (i) the **conceded winner** on identity,
deduplication and small-perturbation task geometry, and (ii) a **component we
offer to plug into our own loop** as a faster frontier key. The honest
arrangement: nauty is complete, fast, and localizes edits better than we do;
what it does not supply is a space with freely constructible points.

## 2. Set B — the search-loop component comparison (conceded, run anyway)

The question this set answers is not "who deduplicates faster" — that is settled
above — but "**how much of the C1 loop is ours, and what does the
instruction-string form contribute once the key is factored out?**"

| Configuration | What it isolates |
|---|---|
| C1 loop with `w*_c` as the frontier key | ours, end to end |
| **C1 loop with a Levi-nauty key** | the dedup cost, factored out. If it is faster — expected — the loop is *still ours*: the moves, the order and the decoder do not change |
| `nauty`-canonical augmentation (McKay), standalone | the state-of-the-art generator. Faster; **and it does not provide a move operator in representation space, a decoder for arbitrary points, or a metric** |
| Brute force + `pynauty` dedup | correctness ground truth at small sizes |
| Syntactic (string-only) frontier dedup, no canonicalization | the cheap option: sound for visitation, coarser than exact. Measures how much exactness costs *inside our own loop* |

**Contract (pre-registered).** Report objects/s, duplicates rejected, frontier
bytes and peak memory for every configuration. **The expected and acceptable
outcome is that the nauty-keyed configuration is fastest**; if so it is stated in
the results text, and the framework claim is unaffected because the key is
explicitly a pluggable component. What must survive is the conjunction that no
configuration of nauty provides: a move operator that never leaves the space, a
total decoder, and a native cost order.

**Precedent to cite, not to hide.** gSpan's minimum DFS code (Yan & Han, ICDM
2002) made exactly this trade for graphs — a constructive canonical form over an
external certificate — and became standard because mining pipelines need the
extension operator, not because it canonized faster than nauty. `w*_c` is the
hypergraph analogue, with the property gSpan lacks: totality of the decoder over
the whole alphabet.

## 3. Set C — finite model finders (the C2 competitor)

| Baseline | Objective it actually optimizes | Fairness note |
|---|---|---|
| **Mace4** (McCune) | minimum *domain size*; incomplete symmetry breaking | different objective from MIN-CM — must be stated in every table |
| **Paradox** (Claessen & Sörensson, 2003) | minimum domain size; static symmetry-breaking clauses over constants | the state of the art for the symmetry problem we attack; the honest reference point |
| **SEM** (Zhang & Zhang, 1995) | minimum domain size; least-number heuristic | the classic incomplete isomorph rejection |
| **cvc5 / Vampire finite model building** | minimum domain size, SMT/SAT-based | run if the encoding effort is affordable; otherwise cite |
| **MaxSAT / ASP encoding of MIN-CM** | **our objective exactly**: ground `¬φ` at domain size `d`, unit soft clauses penalising true atoms, iterate `d` upward under an incumbent bound | **the fair fight.** Building this baseline ourselves is the honest move, and it is the one a reviewer will ask for |

**Contract (pre-registered, written before any result).**
1. If the search is competitive in wall-clock with the MaxSAT route on some
   formula class, name the class and the crossover.
2. **If MaxSAT/ASP dominates in wall-clock — the expected outcome on most
   formulas, because propagation prunes semantically while enumeration prunes
   only structurally — report it plainly, in the results text.** The claims that
   survive are the ones no baseline can produce *at all*: the distance between
   countermodels, radius-`r` countermodel neighbourhoods, minimal repair paths
   with valid intermediates, the diversity of the minimal-countermodel set, and
   the verifiable census by cost level.
3. No baseline is removed for winning. Same rule as `../COMPETITORS.md` §4.

**What must not be claimed.** (i) That existing model finders ignore isomorphism
— they symmetry-break incompletely and *deliberately*, because complete
rejection has historically cost more than the duplicates it removes, and our
canonizer is the slow one. (ii) That complete isomorph rejection is our
contribution — it is a correctness precondition, and nauty supplies it better.
The contribution is that model space acquires a metric, a decoder and a move
operator, so questions about the *relative position* of models become
computable.

## 4. Set D — the alphabet comparison (new, if D3′ adopts `Σ_FO`)

If a purpose-built alphabet is adopted (`logic_models/encoding.md` §3), the comparison
that must be run is **`Σ_HG`-reduction versus `Σ_FO`** on the same structures,
through the existing representation-agnostic harness: single-edit sensitivity,
ball growth, `ν`, `D̂`, concentration, and `w*_c` wall-clock. This is a sweep on
built infrastructure, and it converts the alphabet decision from a bet into a
measurement whose headline question is sharp: *does aligning the token with the
unit of semantic change (one ground fact ↔ one token) reduce the ≈30–50 %
single-edit response?* Reported either way.

## 5. Retired axes

- The HGED head-to-head across representations (retired at D-ART2; stays retired).
- Mutual information (retired at D-ART2; stays retired).
- The seven-row single-table comparison as the paper's main competitive surface —
  it survives inside the measured-limits subsection and the geometry table, but it
  is no longer the paper's comparative spine.

## 6. Summary — who competes where

| | Identity / dedup | C1 search loop | C2 model geometry | C3 navigate | C4 black-box `P` | C5 completeness price | Limits (A2/A3) |
|---|---|---|---|---|---|---|---|
| IsalHG `w*_c` | ✔ (slower — conceded) | ✔ (the whole loop) | ✔ (only) | ✔ (only) | ✔ (only) | ✔ 0 merges | ✔ weak, reported |
| nauty / bliss / Traces (Levi) | **✔ wins** | key only (pluggable, and welcome) | — | interiors are not certificates | cannot generate candidates | ✔ 0 merges — **tie** | **✔ leads** |
| WL / NetLSD / HPD / HyperCOT | incomplete | not applicable | — | monotonicity only (no ambient objects) | — | ✔ merge counts measured | ✔ |
| degree-seq / size floors | incomplete | not applicable | — | — | — | ✔ floor | ✔ floor ≡ 0 |
| Mace4 / Paradox / SEM / cvc5-FMF | — | — | — | — | needs `P` in its logic | — | — |
| MaxSAT / ASP | — | — | finds one model (**same objective, wins**) | — | needs `P` in its logic | — | — |

Read the table by column, not by row: we lose the first, tie the sixth, are the
only entry in three of the remaining four, and lose the last. That distribution
*is* the paper's argument.
