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

## Axes and bases

| Axis | Code | Base | n | m | k | T | Monotone (IsalHG) |
|------|------|------|---|---|---|---|-------------------|
| M1 vertex growth      | `OfatAxis.M1` | tight_cycle_k3_n5    | 5  | 5  | 3 | 10 | 1.00 |
| M2 densification      | `OfatAxis.M2` | loose_path_k3_n9     | 9  | 4  | 3 | 10 | 0.80 |
| M3 arity increase k=3 | `OfatAxis.M3` | fano_plane_k3        | 7  | 7  | 3 | 7  | 0.57 |
| M3 arity increase k=4 | `OfatAxis.M3` | tight_path_k4_n6     | 6  | 3  | 4 | 3  | 1.00 |
| M3 arity increase k=5 | `OfatAxis.M3` | tight_path_k5_n7     | 7  | 3  | 5 | 3  | 0.67 |
| M4 incidence edit     | `OfatAxis.M4` | sts9_k3              | 9  | 12 | 3 | 10 | 0.50 |
| M5 symmetry break     | `OfatAxis.M5` | gq22_k3              | 15 | 15 | 3 | 10 | 0.80 |

All bases are ADMITTED designs (feasibility pilot 30s budget passed locally;
see `artifacts/feasibility_pilot/`). PENDING_CLUSTER designs (STS13, AG24,
PG23, PG24) excluded per T-M7a instruction.

## Key findings (summary for T-M8b)

- M1 (vertex growth): perfectly monotone IsalHG response (mf=1.00); ν rises
  from 0 at T<4 to ~0.04 at T=10.
- M2 (densification): mf=0.80; ν stays near 0 (max ~0.012) — densification
  produces a more Euclidean-like metric profile.
- M3 (arity increase): terminates early (all vertices consumed by growing
  edge); mf varies 0.57–1.00 depending on base arity.
- M4 (incidence edit): lowest monotone fraction (mf=0.50); alternating
  add/remove edits produce a noisy but positively-drifting d_I response.
- M5 (symmetry break on GQ(2,2)): mf=0.80; non-monotone steps are the
  avalanche events at near-symmetric states — exactly the mechanism named
  in the discussion.

## File naming

`filmstrip_{axis}_{base}.png` — 5-frame filmstrip H_0..H_T (snapshots at 0, T/4, T/2, 3T/4, T)
`response_curve_{axis}_{base}.png` — d_rep(H_0, H_t) vs step t for all 6 representations
`mds_traj_{axis}_{base}.png` — 2D classical-MDS trajectory of the sequence (M1, M2 only)
`nu_traj_{axis}_{base}.png` — ν(prefix [H_0..H_t]) trajectory (M1, M2 only)
`result_{axis}_{base}.json` — full numeric record (budgets, distances, monotone fractions, ν)
