# Capability matrix — the main figure that carries "usefulness"

**Status:** planning note (not yet a ledger task). Authoring-only — every fact
below is already established; no new measurement is required. Highest
impact-per-effort item in the revision.

**Why.** On the pure task metrics (A2 clustering, A3 kNN) IsalHG is a strong
*second* to HPD-JSD. The paper's real value proposition is not "best clustering"
— it is **complete + decodable + navigable, driven by a single metric**. The
capability matrix is where that proposition becomes a one-glance claim, so it
should be a first-class main figure, not buried in prose.

---

## The matrix

Rows = the six representations; columns = capabilities. Render as a
checkmark / partial / cross grid (✓ / ~ / ✗), not a paragraph.

| Capability | IsalHG | WL-hist | NetLSD | HyperCOT | HPD | nauty-edit |
|---|:--:|:--:|:--:|:--:|:--:|:--:|
| **Complete invariant** (exact iso: `d = 0 ⇔ ≅`) | ✓ | ✗ | ✗ | ✗ | ✗ | ✓ |
| **True metric** (triangle inequality) | ✓ | ✓ | ✓ | ✓ | ✗ (JSD) | ✓ |
| **Decodable** (recover the hypergraph from the representation) | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **Navigable geometry** (bounded single-edit sensitivity `s(e)`) | ✓ (IQR 2–8) | — | — | — | — | ✗ (IQR 10–20) |
| **Scales to `n ≳ 10²`** | ✗ (symmetry-gated) | ✓ | ✓ | ✗ (`O(n³)`) | ✓ | ~ |
| **Single metric drives all 4 tasks** (A1–A4) | ✓ | ✓ | ✓ | ✓ | ~ | ✓ |

### The two rows where IsalHG stands alone

- **Complete + Decodable + Navigable simultaneously** is IsalHG-only. nauty is
  complete but neither decodable nor navigable (avalanche-everywhere geometry);
  everyone else is scalable but neither complete nor decodable. That
  intersection *is* the paper's thesis in one glance.
- Pair the matrix directly with the **A4 decoded-intermediates figure**
  (`T-M5e/a4_decodability_demo.pdf`): the matrix *claims* "decodable," the figure
  *shows* three intermediate strings decoded via S2H to valid hypergraphs, next
  to WL collapsing to a 2-node hop and NetLSD/HPD having no decoder at all.

---

## Column-by-column justification (all already measured / proved)

- **Complete invariant.** IsalHG: Theorem A (tie-complete `w*_c`). nauty:
  canonical form over the Levi reduction (complete by construction). WL / NetLSD
  / HyperCOT / HPD: lossy embeddings — non-isomorphic hypergraphs can collide.
- **True metric.** `d_I`, WL-L1, NetLSD-L2, HyperCOT (transport metric), nauty-
  edit all satisfy the triangle inequality. **HPD uses Jensen–Shannon
  divergence, which is not a metric** (its square root is) — a free correctness
  point in IsalHG's favour; state it explicitly.
- **Decodable.** Only `w*_c` has an inverse (S2H); the alphabet is closed, so
  every canonical string — and every intermediate on an edit path — decodes to a
  valid hypergraph. Vector / spectral / transport / portrait representations have
  no decoder. nauty's canonical string is decodable to the *graph* but its
  avalanche geometry makes path intermediates meaningless.
- **Navigable geometry.** Measured single-edit sensitivity: IsalHG IQR 2–8
  tokens (no heavy tail); nauty-Levi IQR 10–20 across all seven regimes (ratio
  1.25–9.5× ours). Vector reps have no natural single-edit-in-representation-space
  notion — marked "—".
- **Scales to `n ≳ 10²`.** WL / NetLSD / HPD are polynomial and run on the HIC
  real corpora. HyperCOT is `O(n³)`/pair (small/mid only). IsalHG is
  symmetry-gated (the HIC NO-GO: arity 110 + near-symmetric blow-up). nauty
  scales on most inputs but is worst-case exponential — marked "~".
- **Single metric drives all 4 tasks.** IsalHG / WL / NetLSD / HyperCOT / nauty
  each expose one distance that feeds A1–A4 uniformly. HPD is "~" because JSD is
  not a metric, so MDS/k-medoids/kNN-with-precomputed-metric are only
  approximately licensed.

---

## Recommended ledger framing

One authoring task (no compute). Deliverables:
1. The matrix as a main-text figure (rendered grid, not a table if the venue
   prefers).
2. Placement adjacent to the A4 decodability figure.
3. A one-paragraph caption stating the IsalHG-only intersection and the HPD
   not-a-metric point.
4. Cross-reference from the §Usefulness intro so the reader meets the capability
   framing *before* the task-metric tables where IsalHG places second.

Acceptance check: the "usefulness" section leads with capability (where IsalHG
is unique) and reports task metrics as "competitive," with no sentence claiming
task-metric dominance.
