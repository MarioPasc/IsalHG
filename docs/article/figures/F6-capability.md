# F6 — Capability matrix

**Spine position:** Usefulness — the opener, placed *before* the task-metric
tables.
**Status:** to build. Authoring only; no compute. Supersedes the planning note
`REVIEW/CAPABILITY_MATRIX.md`, whose numbers are pre-S7.

---

## 1. Why this figure

The paper's value proposition is not a task-metric win — on the current corpus
it is not even a task-metric lead (F7). It is an **intersection of properties
no other representation holds simultaneously**: complete, decodable, navigable,
one metric driving every task. An intersection claim is a grid, not a
paragraph, and it must be met before the reader reaches a table where IsalHG
places mid-field, or the tables will be read as the paper's verdict.

## 2. The matrix

Rows = capabilities, columns = representations. Render ✓ / ~ / ✗ as a grid.

| Capability | IsalHG | WL-hist | NetLSD | HyperCOT | HPD | nauty-edit | Deg-seq | `|Δn|+|Δm|` |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| Complete invariant (`d = 0 ⟺ ≅`) | ✓ | ✗ | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ |
| True metric (triangle inequality) | ✓ | ✓ | ✓ | ✓ | ✗ (JSD) | ✓ | ✓ | ✓ |
| Decodable (representation → hypergraph) | ✓ | ✗ | ✗ | ✗ | ✗ | ~ | ✗ | ✗ |
| Ambient decodability (every intermediate on an edit path is a hypergraph) | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Navigable (bounded single-edit `s(e)`) | ✓ (IQR 3–9) | — | — | — | — | ✗ (IQR 20–37) | — | — |
| Scales to `n ≳ 10²` | ✗ (symmetry-gated) | ✓ | ✓ | ✗ (`O(n³)`) | ✓ | ~ | ✓ | ✓ |
| One metric drives A1–A4 | ✓ | ✓ | ✓ | ✓ | ~ | ✓ | ✓ | ✓ |

**Changes from the planning note.** (i) The naive size baseline is added as a
column — it is in every other comparison surface (F7) and its presence here
makes the "what does completeness buy" gradient run the full width of the
grid, naive → lossy-vector → transport → complete. (ii) *Ambient decodability*
is a new row, and it is the row where IsalHG is alone: it is what F3 measures
and what the shipped pool-based A4 result did **not** establish. (iii)
`s(e)` quartiles updated to the S7 measurement (3–9 versus 20–37; the note
carried the pre-S7 2–8 versus 10–20). (iv) nauty's plain *Decodable* is ~ not
✗: its canonical string does decode to the Levi graph, hence to the hypergraph
— the property it lacks is the *ambient* one, which is why the two rows are
separated.

## 3. The two rows that carry the paper

- **Complete ∧ decodable ∧ navigable** is IsalHG-only. nauty is complete but
  not navigable (F5) and not ambiently decodable; every scalable embedding is
  neither complete nor decodable; the naive baselines are metrics with no
  inverse.
- **Ambient decodability** is IsalHG-only and is the sharpest single statement
  in the article, because it is a property of the *alphabet*, provable in two
  lines (F3 §2), and structurally unavailable to a vector representation — a
  point in `ℝ^d` between two NetLSD signatures is a point in `ℝ^d`, not a
  hypergraph, and there is no map back.

## 4. Placement

Adjacent to F3. The matrix *claims* ambient decodability; F3 *shows* eleven
decoded intermediates. Neither works as well alone.

## 5. Caption obligations

State the HPD not-a-metric point explicitly (JSD fails the triangle
inequality; its square root does not), and state IsalHG's ✗ on scaling in the
same breath as its ✓s — the figure is a trade-off map, and a grid that showed
only wins would be read as marketing.

## 6. Acceptance check

1. Every ✓/✗/~ traces to a proof, a pinned witness, or a cited measurement,
   listed in the figure's caption or the accompanying paragraph.
2. The §Usefulness prose reaches this figure before it reaches any task-metric
   number.
3. No cell asserts a capability the article has not measured — in particular
   the *ambient decodability* row cites F3, not the pool-based A4 run.
