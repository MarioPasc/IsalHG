# G3 OFAT geometry-response artifacts

## Rendering convention (ONE convention for all drawn hypergraphs)

Every drawn hypergraph in this directory — and every downstream figure that
reuses this convention (T-M8b capability-matrix figure, A4 intermediate
decoding exhibit) — uses the following uniform protocol:

**Layout**: 2D spring layout computed on the incidence bipartite graph
(vertex-nodes and hyperedge-nodes as graph nodes; vertex v is connected
to hyperedge e iff v is a member of e). Implemented via `networkx.spring_layout`
with 80 iterations. Seed fixed per figure for reproducibility.

**Hyperedge patches**:
- Arity >= 3: filled convex-hull polygon (`scipy.spatial.ConvexHull`);
  alpha=0.25, edge-color matched to fill-color.
- Arity 2: thick line segment between the two vertex positions; alpha=0.6.

**Vertex dots**: filled black circles (`matplotlib.pyplot.scatter`), s=30,
zorder=3 (drawn above edge patches).

**Colors**: `matplotlib.cm.tab10` palette, cycled over hyperedge index.

**Prior convention (superseded)**: T-M5e structural-profile plots showed
`n_nodes` and `n_edges` as a function of ladder position (no topology drawn).
This G3 convention supersedes that for any figure that needs to exhibit
actual hypergraph topology. T-M5e's ladder-analysis plots remain valid for
the scalar time-series they show.

**Implementation**: `experiments.article.g3_analysis.draw_hypergraph(H, ax, ...)`.
One function call per frame; the caller is responsible for figure/axes creation.

---

## JSON schema (v2, T-M7f review round 2)

Each `result_{axis}_{base}.json` file contains the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `axis` | str | OfatAxis.value |
| `base_design` | str | Config base name |
| `T_achieved` | int | Sequence steps generated (sequence generator) |
| `budgets` | list[int] | Qin edit budget per step |
| `n_nodes` | list[int] | n per step |
| `n_edges` | list[int] | m per step |
| `distances` | dict[str, list] | d_rep(H_0, H_t) per representation per step |
| `monotone_fractions` | dict[str, float] | Per-rep monotone fraction |
| `d_matrix_isalhg` | list[list[float\|null]] | Full (T+1)×(T+1) pairwise d_I matrix |
| `d_matrix_nauty` | list[list[float\|null]] | Full (T+1)×(T+1) pairwise nauty distance matrix |
| `mds_coords_isalhg` | list[list[float]]\|null | 2D MDS embedding coords (T+1, 2) for IsalHG |
| `mds_coords_nauty` | list[list[float]]\|null | 2D MDS embedding coords for nauty |
| `continuity_isalhg` | dict | MDS jump stat: `max_jump`, `median_step`, `ratio` (IsalHG) |
| `continuity_nauty` | dict | MDS jump stat: `max_jump`, `median_step`, `ratio` (nauty) |
| `nu_trajectory` | list[float\|null] | ν per prefix [H_0..H_t] from d_matrix_isalhg |
| `nu_sign` | str\|null | Direction label: `increases`, `decreases`, `near_zero`, `mixed` |
| `vm_k` | int\|null | Fixed VM k for M3 sequences (None for M1/M2/M4/M5) |
| `wall_clock_s` | float | Total analysis time |
| `extra` | dict | Supplementary data (e.g. canonical cost justification) |

### M3 vm_k discipline

All M3 sequences use a **fixed VM k=10** (the package default) for all members
of the sequence. This ensures d_I values are comparable across steps: encoding
H_0 (arity 5) and H_t (arity 6) both at k=10 puts their canonical strings in
the same alphabet (Sigma_HG(10)) and makes Levenshtein distances meaningful.
The vm_k field records this fixed k in each JSON.

### loose_path_k5_n13: partial d_I matrix (quantitative cost justification)

The `loose_path_k5_n13` M3 sequence generator achieves **T=10 steps** (the
sequence does NOT terminate early). However, the tie-complete canonical encoder
is infeasible beyond arity 6 locally:

- Step 0 (arity 5): ~0.05s per d_I call
- Step 1 (arity 6): ~6s per d_I call
- Step 2+ (arity 7+): >90s per d_I call (DNF at 45s timeout)

Root cause: the loose path structure (3 edges sharing only 1 vertex each) has
high local symmetry at higher arities, causing exponential branching in the
tie-complete encoder. The tight path (4 shared vertices per edge) is faster at
comparable n.

The JSON records `T_achieved=10` (sequence generator) with
`extra.T_achieved_distance=1` (d_I computed for steps 0..1 only) and
`extra.canonical_cost_note` with the measured timing. The partial 2×2 pairwise
d_I matrix (steps 0 and 1) and full nauty matrix (all 11 steps) are in the JSON.
Full d_I matrix requires HPC or C++ engine.

---

## Axes and bases

| Axis | Code | Base | n | m | k_base | T_seq | T_dist_isal | vm_k | IsalHG mf | nu_sign | jump_isal | jump_nauty |
|------|------|------|---|---|--------|-------|------------|------|-----------|---------|-----------|------------|
| M1 vertex growth      | M1 | tight_cycle_k3_n5    | 5  | 5  | 3 | 10 | 10 | — | 1.00 | increases | 7.72 / 1.64 = 4.70 | 5.66 / 2.83 = 2.00 |
| M2 densification      | M2 | loose_path_k3_n9     | 9  | 4  | 3 | 10 | 10 | — | 0.80 | near_zero | 3.46 / 1.27 = 2.72 | 5.00 / 2.00 = 2.50 |
| M3 arity increase k=3 | M3 | fano_plane_k3        | 7  | 7  | 3 | 7  | 7  | 10 | 0.57 | mixed     | 11.78 / 1.81 = 6.51 | 15.86 / 13.00 = 1.22 |
| M3 arity increase k=4 | M3 | tight_path_k4_n6     | 6  | 3  | 4 | 3  | 3  | 10 | 1.00 | near_zero | (4 pts) | (4 pts) |
| M3 arity increase k=5 tight | M3 | tight_path_k5_n7 | 7  | 3  | 5 | 3  | 3  | 10 | 0.67 | near_zero | (4 pts) | (4 pts) |
| M3 arity increase k=5 loose | M3 | loose_path_k5_n13 | 13 | 3  | 5 | 10 | 1  | 10 | — | — | null (partial) | (full) |
| M4 incidence edit     | M4 | sts9_k3              | 9  | 12 | 3 | 10 | 10 | — | 0.30 | decreases | 18.78 / 5.70 = 3.30 | 25.67 / 19.34 = 1.33 |
| M5 symmetry break     | M5 | gq22_k3              | 15 | 15 | 3 | 10 | 10 | — | 0.80 | decreases | 28.30 / 4.64 = 6.10 | 45.04 / 15.52 = 2.90 |

Legend: `T_seq` = sequence steps generated; `T_dist_isal` = steps for which d_I pairwise matrix is complete;
`vm_k` = fixed VM k for M3 (always 10); `IsalHG mf` = IsalHG monotone fraction; `jump` = max_jump / median_step ratio.

All bases are ADMITTED designs (feasibility pilot 30s budget passed locally;
see `artifacts/feasibility_pilot/`). PENDING_CLUSTER designs (STS13, AG24,
PG23, PG24) excluded per T-M7a instruction.

## Key findings (summary for T-M8b)

- **M1 (vertex growth)**: perfectly monotone IsalHG response (mf=1.00); ν
  increases monotonically from 0 to ~0.04 at T=10 (licensed: non-Euclidean
  character grows with the sequence). Jump ratio 4.70 vs nauty 2.00 — IsalHG
  shows more unequal step sizes.
- **M2 (densification)**: mf=0.80; ν stays near 0 (max ~0.012) — densification
  produces a more Euclidean-like metric profile. Jump ratio 2.72 vs nauty 2.50.
- **M3 (arity increase)**: sequence terminates early for tight paths (all
  vertices consumed in 3–5 steps); loose path achieves T=10 but d_I infeasible
  beyond arity 6 locally (exponential canonical cost). ν near-zero for tight
  paths; mixed for Fano. Jump ratio high for Fano (6.51) — one dominant
  arity-expansion step.
- **M4 (incidence edit)**: lower monotone fraction (mf=0.30 after new run);
  ν decreases from small positive values (~0.009) after T=7 — edit-type
  asymmetry in the sequence drives the non-monotone behaviour. Jump ratio 3.30.
- **M5 (symmetry break on GQ(2,2))**: mf=0.80; non-monotone steps are the
  avalanche events at near-symmetric states — exactly the mechanism named in
  the discussion. ν decreases from 0.022–0.030 at T=9,10. Jump ratio 6.10 —
  the highest IsalHG jump ratio, reflecting the avalanche.

## Nauty contrast (R2 finding)

For every axis, `continuity_nauty` is computed alongside `continuity_isalhg`.
The nauty_levi_edit trajectory is notably smoother in most axes (lower
max_jump / median_step ratio): M1 2.00 vs IsalHG 4.70; M5 2.90 vs IsalHG 6.10.
The exception is M3/Fano where nauty has a near-uniform jump pattern (ratio 1.22)
while IsalHG shows a dominant single arity-expansion event (ratio 6.51). This
profile difference is the mechanism described in `PROPOSAL.md §5` (Discussion):
IsalHG's complete invariant is discontinuous at symmetry-breaking points whereas
nauty's canonical relabeling avalanches everywhere.

## File naming

`filmstrip_{axis}_{base}.png` — 5-frame filmstrip H_0..H_T (PNG; not in git)
`response_curve_{axis}_{base}.png` — d_rep(H_0, H_t) vs step t for all 6 representations (PNG; not in git)
`mds_traj_{axis}_{base}.png` — 2D classical-MDS trajectory (IsalHG + nauty panels) (PNG; not in git)
`nu_traj_{axis}_{base}.png` — ν(prefix [H_0..H_t]) trajectory (PNG; not in git)
`result_{axis}_{base}.json` — full numeric record (in git)
