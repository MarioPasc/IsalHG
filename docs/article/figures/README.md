# Article figures — index and rationale

**Status:** ACTIVE (opened 2026-08-09). One `.md` per proposed figure; rendered
artifacts and their generating code live under `src/`.

## Layout

```
figures/
  README.md          this file — the figure set, the spine mapping, the cut list
  F<n>-<slug>.md     one file per figure: what it shows, why, data provenance,
                     panel spec, caption draft, acceptance check
  src/               rendered figures (.pdf/.png) produced by
                     experiments/analysis/figures/<module>.py
```

**Generation rule.** Every figure is produced by a routine in
`experiments/analysis/figures/`, reading only from
`/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/` (the authoritative
result tree; see its `RESULTS_MANIFEST.md`). Any figure that draws a
hypergraph, a CDLL, or an instruction strip does so through `src/isalhg/viz`
— never by hand-rolling matplotlib primitives. Each `.md` names the exact
result files its numbers come from, so a figure can be regenerated and
re-checked against the prose.

## The set

| # | Figure | Spine position | Status | Source |
|---|---|---|---|---|
| [F1](F1-word.md) | A hypergraph is a word — the VM in one page | Foundation | to build | `viz` + `known_design_catalog` |
| [F2](F2-metric-space.md) | Hypergraph space → metric space | Foundation → geometry | to build | `T-M7d/d_matrix` |
| [F3](F3-decoding-corridor.md) | The decoding corridor (interpolation) | Usefulness (A4) | to build — **new evidence** | new routine + `viz` |
| [F4](F4-geometry.md) | The measured geometry (4 panels) | Geometry | to build | `T-M7d/{stats,d_matrix}` |
| [F5](F5-sensitivity.md) | Navigable vs avalanche | Geometry (G2) | to build | `T-M7q/g2_catalog_sensitivity` |
| [F6](F6-capability.md) | Capability matrix | Usefulness (opener) | to build | no compute |
| [F7](F7-task-metrics.md) | Task metrics under a size control | Usefulness (A2/A3) | to build — **needs new control** | `T-M7d/{stats,d_matrix}` |
| [F8](F8-discussion.md) | Compactness + the HGED footprint | Compactness + discussion | partly rendered | `T-M5a/` |
| [F9](F9-frontier.md) | The feasibility frontier | Limits | to build | `T-M7h/` |

Main text targets F1–F7; F8–F9 may move to the supplement if the venue's
figure budget binds. The cut order, if forced, is F9 → F2(a) → F8.

## Two findings that reshape the figure set

Both were measured while planning these figures (2026-08-09); both are recorded
in the individual figure files and require ledger follow-up.

1. **The A4 decodability claim as currently measured is vacuous.** The shipped
   A4 experiment routes the path through a *pool of pre-existing hypergraphs*
   and then decodes those pool members' canonical strings. `all_valid = True`
   is round-trip soundness (`S2H(w*_c(H)) ≅ H`), not a discovery, and the
   competitor contrast fails: WL/NetLSD/HPD paths also visit pool members,
   which are hypergraphs and are equally exhibitable. F3 replaces this with the
   genuine claim — decoding the *ambient* strings along a Levenshtein alignment,
   which no competitor can do because no competitor has an ambient space whose
   every point is a hypergraph.

2. **The primary corpus is size-heterogeneous, and the A2/A3 ranking tracks
   size.** `d_I` is Spearman-0.867 coupled to the canonical-length gap
   (`theoretical/geometry.md` §5), PC1 of the MDS map correlates 0.960 with
   `|w*_c|` and 0.956 with `m` (§4), and the three leading representations on
   A2/A3 are mutually highly correlated (IsalHG↔degree-seq ρ = 0.799,
   NetLSD↔degree-seq ρ = 0.707). F7 therefore reports task metrics against an
   explicit size-only reference and within size-matched strata.
