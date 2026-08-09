# F2 — Hypergraph space → metric space

**Spine position:** Foundation → geometry. Follows F1 immediately.
**Status:** to build.

---

## 1. Why this figure

F1 shows *one* hypergraph becoming *one* word. F2 shows what happens when you
do that to a whole corpus: the words inherit a distance, the distance is a
metric on isomorphism classes (Corollary A), and the corpus becomes a point
cloud you can do statistics on. It is the hinge between the foundation and
everything that follows, and it is the figure a reader will screenshot.

## 2. Panel specification

**Panel (a) — the construction, schematically.** Three small hypergraphs on the
left. Each maps by `w*_c` to a token strip. Between two of the strips, a
Levenshtein alignment grid with the traceback highlighted, giving an integer.
The three integers assemble into a 3 × 3 matrix, which becomes three points.
Two annotations carry the theory:
- on the `w*_c` arrow: *complete invariant* — `w*_c(H) = w*_c(H') ⟺ H ≅ H'`
  (Theorem A);
- on the matrix: *hence a metric on isomorphism classes* — identity of
  indiscernibles from completeness, symmetry and triangle inequality from
  `d_Lev` (Corollary A).

This is the only place the paper draws the alignment; it is worth the space
because it fixes for the reader that `d_I` counts **token** edits, which F3's
proposition depends on.

**Panel (b) — the real map.** Classical MDS + SMACOF embedding of the design
corpus under `d_I^⊥`, points coloured by family, hulls or ellipses per family.
Annotate `D̂ = 17`, stress-1 at `D = 2`, and the fraction of positive
eigenvalue mass retained in two dimensions (56.2%).

**The qualification the panel must carry.** On this corpus the leading MDS axis
is very nearly canonical-string length: `|r(PC1, |w*_c|)| = 0.960`,
`|r(PC1, m)| = 0.956`, against `|r(PC1, n)| = 0.462`. A reader must not read the
horizontal spread as structural separation. Two options, in order of
preference:
1. draw PC1 with a secondary axis annotated in `|w*_c|` tokens, making the size
   gradient explicit and turning a confound into an honest reading;
2. or add a small inset of the same embedding on a size-controlled corpus
   (F7 §3), where the size gradient is absent by construction.

Option 1 is free and should ship regardless. Option 2 depends on the F7 corpus
decision.

## 3. Data provenance

- `results/T-M7d/d_matrix/stratum_a/seed0/isalhg_levenshtein/D.npy` (85 × 85).
- `results/T-M7d/stats/stratum_a_stats.json` for `D̂` and stress.
- Panel (a) fixtures: three small designs from `known_design_catalog`
  (suggested `tight_path_k3`, `tight_cycle_k3`, `sts7`, whose `|w*_c|` are
  63, 71, 121 — visibly different lengths, which makes the alignment grid
  readable).
- Drawing: `viz.hypergraph_view`, `viz.instruction_view`; `sklearn.manifold.MDS`
  for panel (b).
- Generating routine: `experiments/analysis/figures/metric_space_figure.py`.
- Output: `docs/article/figures/src/F2_metric_space.pdf`.

## 4. Acceptance check

1. The alignment integer in panel (a) equals
   `IsalHGLevenshtein().pairwise(H_i, H_j)` for the drawn pair — asserted in
   the routine, not eyeballed.
2. Panel (b)'s stress matches `stratum_a_stats.json`.
3. The PC1-versus-`|w*_c|` correlation is stated in the caption; the figure
   does not present the horizontal axis as structural without it.
