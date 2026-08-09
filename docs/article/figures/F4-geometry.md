# F4 — The measured geometry

**Spine position:** Geometry — the article's central characterization.
**Status:** to build. All numbers exist; the panels assemble cached results.

---

## 1. Why this figure

The paper's contribution claim is that it *characterizes* the geometry of a
hypergraph metric space, and that each measured invariant *licenses* a
downstream method (the no-orphan-geometry rule). A table of six numbers does
not communicate that. Four panels do, because each panel is visibly the
precondition for a later section.

## 2. Panel specification

**Panel (a) — non-Euclideanness.** The eigenvalue spectrum of the
double-centred Gram matrix `B = −½ J D² J` for `d_I^⊥`, positive eigenvalues
up, negative down and shaded. Annotate `ν = Σ_{λ<0}|λ| / Σ|λ| = 0.097`
[0.096, 0.099] and "not PSD". *Licenses:* k-medoids over any centroid method in
A2 — with an indefinite Gram matrix there is no Euclidean mean to compute.
Overlay the competitor `ν` values as a small strip (NetLSD 0.000, HPD 0.000,
WL 0.030, nauty 0.024, degree-seq 0.103, HyperCOT 0.250) so the reader sees
IsalHG is not an outlier.

**Panel (b) — intrinsic dimension.** Cross-validated out-of-sample
reconstruction error against embedding dimension `D`, one curve per
representation, each minimum marked. IsalHG turns at `D̂ = 17` [16, 17];
NetLSD at 4; degree-seq at 3; HyperCOT at 1. WL, HPD and nauty-Levi **never
turn** — their curves ride monotonically to the `D = 40` search cap and are
drawn dashed and labelled *censored*. This panel is where "censored" stops
being a footnote and becomes visible.

**Panel (c) — concentration and hubness.** Left: the pairwise-`d_I` histogram
with the diameter/median ratio annotated (2.72). Right: the `k`-occurrence
distribution `N_10` per representation with its skewness. WL's 2.37 versus
IsalHG's 0.907 is the panel's payload. *Licenses:* A3 — and it **predicts A3's
outcome before the classifier runs**, which is the strongest methodological
move in the paper (WL's AUC collapses to 0.495, chance).

**Panel (d) — faithfulness to known structure.** The budget-coloured Shepard
diagram: `d_I` against embedded distance, points coloured by the accumulated
Qin edit budget `t` of the perturbation ladders. Annotate Spearman
`ρ(t, d_I^⊥) = 0.39` (56 ladders, 560 steps, p < 10⁻²⁰) and stress-1 at `D̂`
(0.046). HGED-free by construction — the budget is known because the edits were
applied.

## 3. The interpretive point the caption must carry

**`D̂ = 17` is not a defect, and low `D̂` is not a virtue.** The article should
say this explicitly, because the naive reading (and the current wording in
`theoretical/geometry.md` §3, "a lower faithful `D̂` … argues `d_I` captures
hypergraph structure more compactly") points the wrong way:

- A representation that separates every isomorphism class **cannot** be
  low-dimensional. Dimension here counts retained structural degrees of
  freedom. Degree-seq sits at `D̂ = 3` and is provably incomplete (its own
  pinned witness: two non-isomorphic hypergraphs at distance 0). NetLSD sits at
  4 and is incomplete. HyperCOT at 1 pays for it with stress 0.275. `D̂` orders
  the representations by information retained, and completeness is at the top
  of that order. **High `D̂` is the signature of completeness, not a cost.**
- The genuine costs of high `D̂` are two, and both are measured, so both should
  be stated rather than argued: a two-dimensional map is lossy (stress rises
  0.046 → 0.288, retaining 56.2% of positive eigenvalue mass), and high
  intrinsic dimension is the standard precondition for hubness. The second cost
  did **not** materialise — `d_I` shows only moderate hubness (0.907) and
  moderate concentration (2.72), and its kNN AUC is 0.915. The pathological
  case is WL: censored `D̂` *and* hubness 2.37 *and* chance-level kNN. The
  lesson the panel teaches is that dimension alone predicts nothing; dimension
  together with hubness does.
- `D̂ ≥ 40` for WL / HPD / nauty is **not** "even more informative". A censored
  curve means the estimator found no low-dimensional structure at all — a
  qualitatively worse condition than a well-determined `D̂ = 17`.

## 4. Is `D̂` measured correctly? (checked 2026-08-09)

Two checks were run against the shipped CV estimator
(`experiments/article/analysis/mds.py::cv_dimension_selection`); both pass.

**Calibration on known ranks (N = 85, matching the corpus).** On noiseless
Euclidean clouds the estimator is exact:

| true `D` | 2 | 3 | 5 | 10 | 17 | 25 |
|---|---|---|---|---|---|---|
| `D̂` recovered | 2 | 3 | 5 | 10 | 17 | 25 |
| `D̂` at 10% distance noise | 4 | 5 | 9 | 15 | 23 | 28 |

So the estimator is unbiased where ground truth exists, and noise inflates it
upward — meaning 17 is, if anything, an upper reading.

**Convergence in `N`** (subsampling the real `d_I` matrix, 8 draws per size):

| `N` | 30 | 45 | 60 | 75 | 85 |
|---|---|---|---|---|---|
| `D̂` | 12.5 ± 1.0 | 14.5 ± 1.0 | 16.6 ± 1.0 | 16.9 ± 0.8 | 17.0 |

The estimate **plateaus** — increments 2.0, 2.1, 0.3, 0.1. `D̂ = 17` is
converged at this corpus size, which retires the concern raised by the earlier
planted-corpus series (21 at `N = 60` climbing to 26 at `N = 240`): that series
was still on its rising limb at `N = 60`, and its own plateau at `N ≥ 240` is
consistent with what is seen here.

One caveat to state: at `D̂ = 17` and `N = 85` the embedding has 1,445 free
coordinates against 3,570 pairwise constraints (0.405 parameters per
constraint). That is a thin but not degenerate regime, and it is the reason the
leave-out-points CV protocol (Gower out-of-sample placement) rather than
entry-masking is the correct estimator — entry-masking would be in-sample and
would ride to the cap. The censored competitors sit at 0.952 parameters per
constraint, i.e. saturated, which is exactly why their curves never turn.

## 5. Data provenance

- `results/T-M7d/stats/stratum_a_stats.json` — `ν`, `D̂`, stress, hubness, all
  with BCa CIs over 27 seeds.
- `results/T-M7d/d_matrix/stratum_a/seed*/<rep>/D.npy` — for the spectrum and
  the CV curves.
- `results/T-M7q/g2_design_ladder/` — ladder budgets for panel (d).
- Calibration/convergence numbers: `scratchpad/dhat_calib.py` (to be
  productionised as a test, see §6).
- Generating routine: `experiments/analysis/figures/geometry_panel.py`.
- Output: `docs/article/figures/src/F4_geometry.pdf`.

## 6. Acceptance check

1. Panel values match `stratum_a_stats.json` to the printed precision.
2. Censored curves are visually distinct and labelled; no censored `D̂` is
   quoted as a number without its `≥`.
3. The calibration table of §4 is reproduced by a unit test (exact recovery on
   noiseless ranks 2, 3, 5, 10, 17, 25 at `N = 85`).
4. No sentence in the article claims lower `D̂` is better without the
   completeness argument of §3 attached.
