# F5 — Navigable versus avalanche

**Spine position:** Geometry (G2) — the licence for every neighbourhood method
and for F3's corridor.
**Status:** to build. Data complete in `results/T-M7q/`.

---

## 1. Why this figure

Both IsalHG and nauty-Levi produce a **complete** canonical form. If the paper
cannot show a difference between them, its whole framing collapses into "we
built another canonical labelling." The difference is not completeness — it is
what a *single structural edit* does to the string. This figure is the measured
proof that structure-incremental encoding buys a usable local geometry, and it
is the single most convincing result in the article because the contrast is
large, mechanical, and reproducible on demand.

It is also the honest place to show that IsalHG's own profile has a tail.

## 2. Measured content

Seventeen design regimes, 100 connectivity-preserving single Qin edits per
design × 2 seeds = **1,700 edits**, `s(e) = d(H, H⊕e)` computed under both
distances on the same edits.

| | Q1 | median | Q3 |
|---|---|---|---|
| IsalHG `d_I^⊥` | 3 | 5 | 9 |
| nauty-Levi edit | 20 | — | 37 |

Pooled means from `g2_catalog_sensitivity.json`: `s(e)` 7.22 (IsalHG) versus
27.20 (nauty), medians 5.0 versus 29.0. Overall 4–8× wider across regimes.

The per-edit records carry `op` and `qin_cost` alongside both `s_e` values,
which is what makes panel (b) possible.

## 3. Panel specification

**Panel (a) — the profiles.** Overlaid histograms of `s(e)`, IsalHG versus
nauty-Levi, pooled over all 1,700 edits, log-count `y`. IQR boxes annotated.
The visual message is one compact mode against one broad high mass.

**Panel (b) — response versus edit cost.** `s(e)` against the edit's Qin cost,
split by operation type (`insert_vertex_and_edge`, `insert_hyperedge`, …), for
both distances. IsalHG's response should track incidence cost — a small edit
moves the point a short distance; nauty's should be flat and large, because the
relabelling is global and independent of how small the edit was. **This panel
is the mechanism, not just the outcome**, and it is what earns the word
"navigable". A worked instance from the data: on `loose_path_k4`, an
`insert_vertex_and_edge` of Qin cost 4 moves `d_I` by 1–5 tokens while moving
the nauty string by 34 every time.

**Panel (c) — the honest tail.** Per-regime heavy-tail fraction for IsalHG,
with the three-regime prediction of `theoretical/stability.md` §4.2 marked
confirmed (16/17) or falsified (1/17 — tight-path arity 4,
heavy_tail_frac = 0.210 against a unimodal prediction). GQ(2,2) is shown as the
predicted heavy-tailed regime, confirmed at 0.230.

## 4. What the caption must not claim

Not "we are stable and they are not." IsalHG's profile has an avalanche regime
too — near-symmetric inputs with incoherent ties — and that is the price *any*
complete invariant pays, because deterministic symmetry breaking is
discontinuous exactly where objects are nearly symmetric
(`stability_reformulations.md` §6). The defensible claim is the measured one:
**our profile is compact outside a characterized regime; theirs is broad
everywhere.** Panel (c) is what makes that sentence honest rather than
defensive, and it is stronger than the overclaim because it survives contact
with a reviewer who probes the symmetric cases.

The one falsified prediction is reported as falsified, in the figure, not only
in the text.

## 5. Data provenance

- `results/T-M7q/g2_catalog_sensitivity/g2_catalog_sensitivity/*/seed*/
  g2_catalog_sensitivity.json` — per-edit records with `op`, `s_e_isalhg`,
  `s_e_nauty`, `qin_cost`.
- `results/T-M7q/g2_catalog_sensitivity/regime_confrontation.json` — the
  per-regime prediction/outcome table for panel (c).
- Generating routine: `experiments/analysis/figures/sensitivity_contrast.py`.
- Output: `docs/article/figures/src/F5_sensitivity.pdf`.

## 6. Acceptance check

1. Quartiles in panel (a) match the manifest values (IsalHG 3/5/9; nauty
   20/–/37).
2. Panel (c) shows 16 confirmed and 1 falsified, with the falsified regime
   named.
3. The caption contains no "stable versus unstable" phrasing; the avalanche
   symmetry point is present.
