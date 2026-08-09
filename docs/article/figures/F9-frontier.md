# F9 — The feasibility frontier

**Spine position:** Limits — end of the usefulness section, or the discussion.
**Status:** to build. Data complete in `results/T-M7h/` (`envelope_final:
true`). Candidate for the supplement if the figure budget binds.

---

## 1. Why this figure exists

`w*_c` is the binding constraint on everything the article can claim, and the
envelope is already measured. Reporting it as a figure rather than a sentence
does three things a sentence cannot: it makes the claim scope
self-evident, it pre-empts the reviewer question "why is your corpus so
small?", and it turns the arity cap into a stated result rather than an
unexplained absence.

Concealing this would be the single easiest thing for a reviewer to catch,
because the corpus sizes advertise it.

## 2. Measured content

- **`k = 3`:** feasible to `n ≈ 24` at low edge density; `n ≤ 16` at medium
  density; times out at `n = 16` high density and `n = 24` medium density.
- **`k = 5`:** only `n = 8`, low density.
- **`k = 7`, `k = 10`:** measured infeasible at every tested `n`. The
  advertised arity cap of 10 is **not reachable at any tested vertex count**.
- Three admitted random cells (`er_uniform_k3_n16_rho4`,
  `er_uniform_k3_n24_rho2`, `er_uniform_k5_n8_rho2`) exceeded a 4-hour wall for
  IsalHG while **all six competitors completed**; excluded whole-cell, flagged
  in every table.
- Consequently the random-instance arity axis covers `k ∈ {3, 5}` — two
  points, not three — a measured outcome, not a design choice.

**Symmetry, not size, is the driver.** Two measurements made while planning
these figures make this concrete on the Steiner family, where `n` grows slowly
but symmetry grows fast: `w*_c` costs 0.00 s at STS(7), 0.08 s at STS(9),
**29.6 s at STS(13)**, and STS(15) (`n = 15`, `m = 35`, arity 3, 3-regular)
had not returned after 20 minutes. Two vertices of growth cost three orders of
magnitude. This is the same mechanism as the HIC real-data NO-GO
(`DATA.md` §2) and it belongs in the figure, because it explains *why* the
frontier is shaped the way it is rather than merely where it lies.

## 3. Panel specification

**Panel (a) — the envelope.** Heatmap over `(k, n, ρ)` with cells coloured by
median `w*_c` wall-clock and timeouts hatched. The three excluded random cells
marked.

**Panel (b) — symmetry versus size.** Wall-clock against `n` on two series: the
Steiner series (highly symmetric, `k = 3`) and matched-size Erdős–Rényi
instances (generic). Log `y`. The gap between the two curves at equal `n` is
the symmetry penalty, isolated.

## 4. What the caption must say

The scope sentence, stated plainly: **application claims in this article are
module-scale claims** — small connected hypergraphs within the measured
envelope — and the practitioner scenarios opening A1–A4 are phrased to match
(motif- and module-scale, not metabolome-scale). Pair this with the runtime
reading: among the geometrically capable representations `d_I^⊥` is
competitive with NetLSD and faster than HPD *on small-to-moderate instances*,
and the cost claim carries its size dependence rather than being stated
universally.

## 5. Data provenance

- `results/T-M7h/` — the admission sweep (`envelope_final: true`).
- `results/T-M7d/stats/*_stats.json` — the excluded cells carry
  `wilcoxon: {}`.
- Steiner timings: `scratchpad/sts_feas2.py` (to be productionised alongside
  the F7 corpus work, which needs the same measurement).
- Generating routine: `experiments/analysis/figures/frontier.py`.
- Output: `docs/article/figures/src/F9_frontier.pdf`.

## 6. Acceptance check

1. The `k = 7` / `k = 10` infeasibility is visible in the figure, not only in
   prose.
2. The three excluded cells are marked, and the accompanying text states that
   all six competitors completed them.
3. Every application section's scope language is consistent with the envelope
   drawn here.
