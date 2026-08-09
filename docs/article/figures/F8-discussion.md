# F8 — Compactness and the HGED footprint

**Spine position:** two separated uses — panel (a) in the compactness
subsection near the representation's introduction, panel (b) in the closing
discussion. Kept in one file because both are single-panel exhibits already
rendered.

**Status:** partly rendered — `results/T-M5a/bits/info_content.pdf` and
`results/T-M5a/figures/e1prime_figure.pdf` exist; both need restyling to the
venue template and re-captioning.

---

## 1. Panel (a) — compactness

Substantiates "a hypergraph is a *compact* word", the second clause of the
premise. Compression ratio `r(H) = B_incidence(H) / B_IsalHG(w)` with
`B_IsalHG(w) = |w| · log₂|Σ_HG(k)|` against an incidence-list construction
model.

**Measured (N = 320 pooled over three planted corpora):** `r > 1` on
**320/320**; pooled median `r = 1.441` (per-corpus 1.433 / 1.565 / 1.439);
one-sided Wilcoxon `p = 1.6 × 10⁻⁵⁴`; OLS `β = 0.749 < 1`. Median canonical
lengths 22 tokens (`n = 10`) and 8 tokens (`n = 6`) — 81.4 and 29.6 bits at
`log₂ 13 ≈ 3.70` bits/token, against incidence-list codes of 114.0 and 44.5
bits.

Render as a paired scatter (`B_IsalHG` versus `B_incidence`) with the identity
line, plus a marginal histogram of `r`. The identity line makes "every point
below the diagonal" a one-glance claim; 320/320 needs no statistics to be read,
though the Wilcoxon is reported.

**Caption obligation.** State that the estimator is a **uniform fixed-width
code**, not Shannon self-information and not compressed length — a reviewer
who assumes entropy coding will otherwise mis-read the ratio. Note also the
pinned tokenization regression: `;` separates fields *inside* `V[...]`/`C[...]`
as well as between tokens, and a naive split overcounts ≈2× and reverses the
conclusion.

## 2. Panel (b) — the HGED footprint

The article's single exact-HGED exhibit, ours only, in the closing discussion
*after* the envelope and impossibility statements.

**Measured (11-block connected mini-corpus, FROZEN):** Spearman
`ρ = 0.622` over `N = 6,921` pairs with HGED > 0 (Pearson `r = 0.663`; OLS
slope 0.568); per-cell `ρ` 0.48–0.81, largest cells at the top of the range
(`n = 9`: 0.72; `n = 10`: 0.69). **Every HGED = 0 pair has `d_I` = 0** — the
identity-of-indiscernibles cross-check between the two metrics.

Render as a hexbin or 2-D density of `d_I` against HGED with the OLS line, `ρ`
annotated, and the per-cell `ρ` values as a small strip beneath.

**Caption obligations.** Three, all load-bearing:
1. This is **characterization, not validation of a bound**. The article makes
   no proxy claim; `ρ = 0.622` is offered as the measured footprint of a
   relation that provably cannot be bi-Lipschitz.
2. The corpus ceiling is itself the result. The `n = 9–10` cells needed up to
   8.5 h and 55 GB per 630-pair cell; the twelfth block exceeded 100 GB after
   18 h and is excluded **whole-block** (per-pair censoring would bias `ρ`).
   The exact oracle reaches its practical ceiling at the boundary of this
   mini-corpus — which is precisely why the article validates usefulness on
   task metrics instead of on an HGED axis.
3. `ρ = 0.622` is moderate, and the figure should not be sold as agreement.
   It is consistent with F3: the geodesic contracts and rebuilds rather than
   morphing, so `d_I` and HGED are measuring related but distinct things.

## 3. Data provenance

- `results/T-M5a/bits/{pooled_info_content.json, info_content_result.json,
  info_content.pdf}`.
- `results/T-M5a/figures/{e1prime_result.json, e1prime_figure.pdf}` — FROZEN;
  do not re-run the oracle.
- Generating routine: `experiments/analysis/figures/discussion_panels.py`
  (restyle from the cached JSON; do not recompute).
- Outputs: `docs/article/figures/src/F8a_compactness.pdf`,
  `docs/article/figures/src/F8b_hged_footprint.pdf`.

## 4. Acceptance check

1. Numbers match the cached JSON exactly; no recomputation of the E1′ oracle.
2. Panel (a)'s caption names the fixed-width estimator.
3. Panel (b)'s caption contains no proxy or approximation language, and states
   the whole-block exclusion.
