# F3 — The decoding corridor

**Spine position:** Usefulness (A4 — the capability differentiator).
**Status:** to build. Introduces *new* evidence measured 2026-08-09; replaces
the shipped A4 decodability claim, which is vacuous (see §5).

---

## 1. The question this figure answers

> Given two canonical strings `w*_c(H_A)` and `w*_c(H_B)` that are `d` edits
> apart, does every intermediate string along the edit path decode to a valid
> hypergraph?

The answer is **yes, provably and unconditionally** — and the *reason* it is
yes is the property that separates IsalHG from every competing representation.
The figure is the argument made visible.

## 2. The formal content (a proposition the paper should state)

**Proposition (ambient decodability).** Let `u_0, u_1, …, u_d` be the sequence
of token strings realised by any optimal Levenshtein alignment between
`u_0 = w*_c(H_A)` and `u_d = w*_c(H_B)`, so that consecutive strings differ by
one token insertion, deletion, or substitution. Then every `u_j ∈ Σ_HG(k)*`,
and `S2H(u_j)` is a **connected** hypergraph of arity ≤ `k`.

*Proof sketch.* Two ingredients, both already in place.

1. *Closure under single-token edits.* `d_I` is defined on the **token**
   sequence, not the ASCII serialization (`metric_space/distances/
   isalhg_levenshtein.py`; Critical Invariant 2). An alignment therefore
   inserts, deletes, or substitutes whole elements of the alphabet
   `Σ_HG(k) = {V_{i,j}, C_i, P_i, N_i, W}`. Any finite sequence over that
   alphabet is a word of `Σ_HG(k)*`, and the S2H interpreter is total on
   `Σ_HG(k)*` — it never rejects (Critical Invariant 2). So each `u_j`
   decodes.
2. *Connectivity is preserved by the alphabet.* The VM starts from the
   one-vertex hypergraph. `C_i` adds an edge over existing vertices only.
   `V_{i,j}` adds an edge over `i ≥ 1` existing vertices and `j` fresh ones,
   so every new vertex enters inside an edge that already touches the
   component. `P_i`, `N_i`, `W` do not change `H`. By induction on the token
   index, the decoded hypergraph is connected at every prefix, hence for every
   `u_j`. ∎

The connectivity half matters: it says the ambient space `Σ_HG(k)*` decodes
onto exactly the domain the article works in (connected hypergraphs, D-CONN1),
with no illegal or disconnected intermediates to explain away.

**The honest other half — the intermediates are not canonical.** `u_j` decodes,
but in general `w*_c(S2H(u_j)) ≠ u_j`: the ambient point is a *representation*
of a hypergraph, not that hypergraph's canonical form. So the Levenshtein
geodesic runs through `Σ_HG(k)*`, leaving the canonical image `w*_c(𝓗)`, which
is a sparse subset of it. The figure must show this, not hide it — it is the
same fact the closing discussion states as "`d_I` is not an edit-distance
proxy", now visible rather than asserted.

## 3. Measured (2026-08-09)

Optimal alignment paths between the canonical strings of five design pairs,
every intermediate decoded and re-canonicalised. Script:
`scratchpad/interpolation.py` (to be productionised — see §6).

| pair | `d_I` | intermediates | decode | connected | already canonical |
|---|---|---|---|---|---|
| STS7 → TightCycle3 | 10 | 11 | 11/11 | 11/11 | 2/11 |
| LoosePath3 → TightPath3 | 3 | 4 | 4/4 | 4/4 | 2/4 |
| STS9 → GQ(2,2) | 22 | 23 | 23/23 | 23/23 | 2/23 |
| TightPath4 → LooseCycle4 | 5 | 6 | 6/6 | 6/6 | 2/6 |
| TightCycle5 → LoosePath5 | 17 | 18 | 18/18 | 18/18 | 2/18 |
| **total** | | **62** | **62/62** | **62/62** | **10/62** |

Every intermediate decodes; every decoded intermediate is connected. The
"already canonical" count is exactly 2 per path — the two endpoints. **No
interior point of any geodesic is canonical**, which is the sharp version of
the caveat in §2.

The STS7 → TightCycle3 walk, decoded:

| step | `|u_j|` | `n` | `m` | connected | canonical |
|---|---|---|---|---|---|
| 0 | 18 | 7 | 7 | ✓ | ✓ |
| 1 | 17 | 5 | 5 | ✓ | ✗ |
| 2 | 16 | 3 | 3 | ✓ | ✗ |
| 3 | 15 | 3 | 4 | ✓ | ✗ |
| 4 | 15 | 5 | 5 | ✓ | ✗ |
| 5 | 14 | 5 | 6 | ✓ | ✗ |
| 6 | 13 | 5 | 5 | ✓ | ✗ |
| 7 | 12 | 5 | 5 | ✓ | ✗ |
| 8 | 11 | 5 | 5 | ✓ | ✗ |
| 9 | 10 | 5 | 5 | ✓ | ✗ |
| 10 | 10 | 5 | 5 | ✓ | ✓ |

The path **contracts to a 3-vertex bottleneck and rebuilds**. It is not a
structural morph, and the figure says so. That is the most informative thing in
it: the reader sees, in one panel, both that the corridor exists and what
travelling it actually costs.

## 4. Panel specification

**Panel (a) — schematic (drawn, not measured).** The ambient space
`Σ_HG(k)*` as a field; the canonical image `w*_c(𝓗)` as a sparse scatter of
filled points inside it; two of them marked `H_A`, `H_B`; the geodesic drawn
through open points (ambient, non-canonical); a downward arrow from each open
point to a small decoded hypergraph glyph. One annotation: "every point of the
corridor is a connected hypergraph; only the endpoints are canonical."

**Panel (b) — measured.** The STS7 → TightCycle3 walk. A row of 11 hypergraph
drawings (via `isalhg.viz.hypergraph_view.draw_hypergraph`, laid out by
`isalhg.viz.cohort_panel.cohort_grid_figure`), each captioned `(n, m)`; beneath
each, its token string as an instruction strip
(`isalhg.viz.instruction_view.draw_instruction_strip`) with the edited token
highlighted; endpoints boxed and labelled "canonical". A small inset line plot
of `n` and `m` against step index makes the contraction–rebuild visible at a
glance.

**Panel (c) — the contrast, one line.** For the same endpoint pair, what each
competitor can exhibit: WL / NetLSD / HPD / HyperCOT — a vector, no decoder,
nothing to draw; nauty-Levi — a canonical string that is decodable to a graph
but whose single-edit response is the avalanche profile of F5, so its
intermediates are unrelated objects. Render as greyed placeholders next to the
IsalHG row so the asymmetry is visual, not textual.

## 5. Why this replaces the shipped A4 decodability result

The A4 experiment as run (`experiments/article/analysis/shortest_path.py`,
results in `T-M7q/a4_design/`) builds a **pool** of pre-existing hypergraphs —
the ladder's true intermediates plus distractors — runs Dijkstra on the pool's
distance matrix, then decodes the canonical strings of the pool members the
path visited. The reported `all_valid: true`, `n_intermediates: 2.4` is
therefore `S2H(w*_c(H)) ≅ H` on objects that were hypergraphs before the
experiment started: round-trip soundness, restated.

The competitor contrast fails the same way. NetLSD's recovered path on
`sts9_s1` is `[0, 4, 6, 8, 9, 17, 20]` — pool indices, i.e. hypergraphs, which
can be drawn as readily as ours. The claim "WL, NetLSD and HPD have no decoder
— they cannot exhibit the intermediate hypergraphs" is not true *of that
construction*; it only becomes true when the path is allowed to leave the pool,
which is exactly what F3 does.

Keep the pool experiment for what it does measure — path-length monotonicity
(1.00 for all representations) and recovery fraction (IsalHG 0.125, NetLSD
0.257, HPD 0.191, WL 0.000). Move the decodability claim here.

## 6. Data provenance and generating code

- **New routine:** `experiments/analysis/figures/decoding_corridor.py`, porting
  `scratchpad/interpolation.py`. Inputs: design fixtures from
  `isalhg.datasets.synthetic.known_design_catalog`; no result-tree dependency
  (the walk is recomputed deterministically from the fixtures).
- **Drawing:** `isalhg.viz.{hypergraph_view, instruction_view, cohort_panel,
  style}`.
- **Existing results referenced in panel (c):**
  `results/T-M7q/a4_design/design_a4/*/a4_result.json`.
- **Output:** `docs/article/figures/src/F3_decoding_corridor.pdf`.

## 7. Acceptance check

1. The proposition of §2 is stated in the paper with both halves — decodability
   *and* non-canonicity of interior points.
2. Panel (b) is generated from a fresh run and its `(n, m)` sequence matches
   the table in §3 exactly.
3. The prose does not claim the geodesic is a structural morph, and does not
   reuse the pool-based `all_valid` number as evidence of decodability.
4. A regression test pins "every intermediate on the five reference paths
   decodes and is connected" (62/62), so the proposition cannot silently break.
