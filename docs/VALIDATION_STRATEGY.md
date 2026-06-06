# IsalHG validation strategy (proposal, 2026-06-06)

## Context and gap

The PI's framing rules out the obvious biomedical applications: protein-protein and chemical-reaction hypergraphs have pre-identified named nodes, so the isomorphism question never arises. Validation has to be **structural / theoretical**: prove and empirically demonstrate that IsalHG computes an isomorphism-invariant canonical string efficiently, faster than the standard `H → bipartite incidence graph → graph-iso tool` reduction.

The literature confirms the gap is real and citable:

- **No peer-reviewed, exact, native hypergraph canonical labeling tool exists in 2026.** The closest published work — Feng et al., *Hypergraph Isomorphism Computation*, IEEE TPAMI 46(5), 2024 [DOI:10.1109/TPAMI.2024.3353199] — is a *Weisfeiler–Leman kernel* method (HIC). WL is incomplete (Cai–Fürer–Immerman 1992), so HIC is a similarity discriminator, not a canonical-string oracle. This is precisely the gap IsalHG fills.
- **The bipartite reduction is theoretically sound but practically penalized by hyperedge count.** Arvind, Das, Köbler & Toda, *Hypergraph Isomorphism for Groups with Restricted Composition Factors*, ACM TALG 18(2), 2022 [DOI:10.1145/3527667] gives the current best bound `(n+m)^O((log(n+m))^c)`. The paper explicitly states: *"with m appearing in the exponent, this running time seems far from optimal for large numbers of hyperedges."* This sentence is the headline that IsalHG's empirical advantage targets.

## Theoretical claim (the publication target)

For every hypergraph `H`, IsalHG produces a canonical string `w*_H` such that

```
w*_{H_1} = w*_{H_2}  ⇔  H_1 ≅ H_2.
```

The "⇐" direction (invariance) is direct from the structure-tuple seeding. The "⇒" direction (completeness) is the **proof obligation** the PI's seed proposal explicitly defers — see `idea_060626.md` open question 5. This proof is the load-bearing theoretical contribution of the paper. Without it, IsalHG is at most a heuristic.

## Validation design — three tiers

The benchmark mirrors the structure of Bläsius, Friedrich & Schirneck, *Benchmark Graphs for Practical Graph Isomorphism*, ESA 2017 [arXiv:1705.03686], adapted to hypergraphs.

### Tier 1 — Correctness (small, exhaustive)

**Goal.** Catch implementation bugs in S2H / H2S / canonical. Verify both directions of the iso equivalence on instances small enough to enumerate.

**Instances.**
- All connected hypergraphs on `n ∈ {3, 4, 5, 6}` vertices with arity `k ∈ {2, 3, 4}`, generated exhaustively by canonical enumeration of `xgi.generators.uniform.uniform_erdos_renyi_hypergraph(n, k, p)` over the full `p`-range.
- The **Fano plane** STS(7) = PG(2, 2): 7 vertices, 7 triples, |Aut| = 168. The smallest non-trivial automorphism-group-rich case.
- STS(9) = AG(2, 3): 9 vertices, 12 triples, |Aut| = 432.
- Two non-isomorphic STS(13). [Heinlein, *Enumerating Steiner Triple Systems*, JCD 31(7), 2023, arXiv:2303.01207.]

**Acceptance criteria.**
1. `S2H(H2S(H)) ≅ H` for every instance (Hypothesis property test).
2. `canonical(H) = canonical(π(H))` for 100 random vertex permutations `π` per instance.
3. `canonical(H_1) ≠ canonical(H_2)` for every published non-isomorphic pair.

### Tier 2 — Runtime scaling

**Goal.** Produce time-vs-size curves of IsalHG vs. the pynauty-over-bipartite baseline. This is the empirical-complexity argument.

**Sweep.** `n ∈ {50, 100, 250, 500, 1000, 2500}`, uniform arity `r ∈ {3, 4, 5}`, hyperedge count `m` chosen to fix `m/n ∈ {1, 5, 25}` (sparse / medium / dense). 10 random seeds per `(n, r, m)` cell.

**Generators.** `xgi.generators.uniform.uniform_erdos_renyi_hypergraph(n, r, p)` for uniform random; `xgi.generators.random.chung_lu_hypergraph` for heavy-tailed degree sequences (model from Chodrow, *Configuration Models of Random Hypergraphs and their Applications*, J. Complex Networks 8(3), 2020, arXiv:1902.09302).

**Metric.** Wall-clock time (median ± IQR over 10 seeds) and length of the canonical string. Report a fit `T ~ n^α m^β r^γ` for IsalHG and for the baseline, side by side.

**Predicted outcome.** Per fairness analysis (lit-search agent 3): IsalHG should be roughly competitive in the sparse regime (small `m`) and pull ahead as `m` grows — exactly the regime Arvind et al. 2022 calls out as suboptimal for the reduction approach. The headline number is the crossover `m`.

### Tier 3 — Hardness stress test (the headline experiment)

**Goal.** Demonstrate IsalHG handles cases where the bipartite-reduction baseline either times out or scales catastrophically due to large automorphism groups.

**Instances.**

| Family | Construction | Why hard for the baseline |
|---|---|---|
| Projective planes `PG(2, q)` for `q ∈ {2, 3, 4, 5, 7, 8, 9}` | SageMath `designs.projective_plane(q)` | `(q+1)`-uniform, highly regular; baseline bipartite `B(H)` is `(q²+q+1) + (q²+q+1)` vertices, all edge-vertices share degree `q+1` ⇒ nauty's refinement stalls. `|Aut PG(2, 7)| ≈ 1.8 × 10^6`. |
| Non-isomorphic `PG(2, 9)` quadruple | 4 non-isomorphic planes of order 9, available via GAP+FinInG | The 4 are pairwise non-isomorphic but bipartite-iso indistinguishable at first refinement; require deep IR backtracking. |
| Steiner triple systems STS(13), STS(15), STS(19) | SageMath `designs.steiner_triple_system(n)` for `n ≤ 21`; pre-computed databases (Kaski & Östergård) for `n = 19` | Small STS have large automorphism groups; 80 non-iso STS(15); 11,084,874,829 non-iso STS(19). Exhaustive pairwise distinction is impossible — but IsalHG should distinguish published non-iso pairs while nauty+bipartite struggles. |
| Generalized quadrangle GQ(2, 2) (the "doily") | GAP+FinInG | 15 points, 15 lines, `|Aut| = 720` on 15 nodes — classic small hard case. |
| Latin squares as 3-uniform hypergraphs | SageMath `latin.LatinSquare` | `H(L) ≅ H(L') ⇔ L, L' isotopic`; Cayley tables of cyclic groups have large autotopy groups. |

**Generation pipeline.** SageMath subprocess wrapper inside `experiments/hard_cases/`, output as JSON hypergraph dumps (`xgi`-compatible) so the iso-comparison runner doesn't depend on SageMath.

**Acceptance criteria.**
- IsalHG returns the correct iso decision on every documented non-isomorphic pair within a 600-second timeout.
- The bipartite + pynauty baseline either takes ≥ 10× longer or times out on at least three families.

### Optional Tier 4 — Real-world structural calibration (not for iso testing)

Real datasets are useful only for tuning generator parameters in Tier 2 so that synthetic instances have realistic arity and degree distributions. **Not used for iso testing** per the PI's framing.

Sources: Austin Benson's ARB collection (`cornell.edu/~arb/data/`), `xgi.load_xgi_data("email-Enron")` and other XGI-DATA loaders [Landry et al., *XGI: A Python package for higher-order interaction networks*, JOSS 8(85), 2023, DOI:10.21105/joss.05162]. One pass over `email-Enron`, `contact-high-school`, `congress-bills`: extract arity histogram, degree distribution, density. Use to set the Tier 2 sweep's `(n, m, r)` ranges so they cover the real regime.

## Baseline stack (locked)

**Primary.** `pynauty 2.8.8.1` (wraps McKay's nauty 2.8.8) over the bipartite incidence graph, with 2-coloring (node-side vs edge-side) and an additional color per hyperedge cardinality to preserve arity. Reference: McKay & Piperno, *Practical Graph Isomorphism, II*, J. Symbolic Computation 60, 2014, DOI:10.1016/j.jsc.2013.09.003. Last pynauty release: 2024-06-06; installed and smoke-tested in the `isalhg` env.

**Secondary.** `python-igraph` (bliss canonical permutation), for cross-validation on a subset of Tier 2 instances. Reference: Junttila & Kaski, *Engineering an Efficient Canonical Labeling Tool for Large and Sparse Graphs*, ALENEX 2007, DOI:10.1137/1.9781611972870.13.

**Theoretical comparator (cited, not run).** Arvind, Das, Köbler & Toda, ACM TALG 18(2), 2022, DOI:10.1145/3527667. Cited as the current best theoretical bound; never implemented.

**Not used.** saucy3 (no canonical label, automorphism group only), conauto (iso decision only), nishe (abandoned, Miyazaki-specialized), HIC (WL-kernel, incomplete). Each gets one citation in related-work.

### Bipartite reduction (canonical reference)

The standard reduction is the **Levi incidence graph** [Berge, *Graphs and Hypergraphs*, 1973]. For a hypergraph `H = (V, E)`:

```
B(H) = (V ⊔ {v_e : e ∈ E},  {(v, v_e) : v ∈ e}),   2-colored, edge-vertex color refined by |e|.
```

Polynomial-time iso-equivalence of `H` and `B(H)` is folklore; the formal statement is Beigel & Bernasconi, *Hypergraph Isomorphism and Structural Equivalence of Boolean Functions*, STOC 1999, DOI:10.1145/301250.301427. We will cite this in the methods section as the baseline justification.

## Metrics

| Tier | Metric | Reporting |
|---|---|---|
| 1 | Correctness (binary) per instance pair | Pass / fail matrix; hypothesis-shrunk failing case if any. |
| 2 | Wall-clock per instance (`T_isalhg`, `T_baseline`) | Median ± IQR over 10 seeds; log-log plot vs `(n, m, r)`; fitted exponents. |
| 2 | Canonical string length `|w*_H|` | Distribution; comparison vs `|edges(B(H))|` as a compactness proxy. |
| 3 | Wall-clock; correctness; timeouts | Per-family table with median time and timeout count. |
| 3 | Speedup `T_baseline / T_isalhg` | Geometric mean across families; per-family box plot. |

## Reproducibility

- **Seeds.** Every random generator call pins a seed; seed is part of the instance metadata stored on disk.
- **Storage.** Instances and timings written under `experiments/<tier>/<run-id>/` as JSONL. SLURM workers on Picasso for Tier 2 + Tier 3 sweeps (generated via the `picasso-sbatch` skill).
- **Versions.** `pyproject.toml` pins `pynauty>=2.8`. The exact resolved versions are dumped via `pip freeze` per run.
- **Statistical tests.** Tier 2 cells with ≥ 30 paired observations (across seeds) report Wilcoxon signed-rank `p` value and Cohen's `d` on `log(T_baseline / T_isalhg)`.

## Phase 1 deliverables (next 8–12 weeks)

1. Port `core/cdll.py` and `core/sparse_hypergraph.py` from IsalGraph's templates (already linked in `CLAUDE.md`).
2. Implement `core/instructions.py`, `core/string_to_hypergraph.py`, `core/hypergraph_to_string.py` (greedy with the full tie-breaking cascade from `idea_060626.md`).
3. Implement `core/structural_tuples.py` and `core/canonical.py`.
4. Hypothesis property tests for `S2H ∘ H2S = id` and canonical invariance over `n ≤ 10` random hypergraphs.
5. `adapters/xgi_adapter.py` (highest priority — XGI is the source of truth for all synthetic generators in Tiers 1–3).
6. `experiments/baselines/pynauty_bipartite.py` — the wrapped baseline. ~80 lines of Python; sketch already in lit-search agent 3 output.
7. **Tier 1 run** end-to-end: this is the first publishable artifact (correctness on Fano + STS(9) + small random).

Defer to Phase 2: the formal completeness proof (paper section), Tier 2 sweep on Picasso, Tier 3 hard-case generators (SageMath subprocess wrapper).

## Open research questions (carry-over from `idea_060626.md`)

These remain unresolved and shape the validation experiments:

1. **Backtracking procedure for tie-breaking.** Without it, the greedy is not deterministic on instances with symmetric pointer configurations. Tier 1 will surface failing cases that pinpoint where backtracking is needed.
2. **Value of `k`.** The Tier 2 sweep over `r ∈ {3, 4, 5}` constrains `k = r` per run; the question of a global `k` is deferred until we measure how alphabet-size growth affects encoding length.
3. **Structural-tuple depth.** Default 3 (from IsalGraph). Tier 3's Steiner systems will tell us whether depth-3 distinguishes published non-iso pairs of STS(15) and STS(19); if not, depth ≥ 4 is required.
4. **Complexity bound.** The Tier 2 fitted exponents `α, β, γ` are the empirical evidence we present in lieu of a theoretical bound. A theoretical bound is a stretch goal.
5. **Completeness proof.** The publication blocker. Drafted in Phase 2.

## Recommended target venues

| Venue | Why |
|---|---|
| Journal of Symbolic Computation | Direct home for canonical labeling work (IsalGraph and McKay-Piperno both publish here). Strong fit. |
| Discrete Applied Mathematics | Combinatorial designs + algorithms; broader audience. |
| SIAM Journal on Discrete Mathematics | Theoretical-leaning sibling. Requires the completeness proof. |
| Journal of Combinatorial Designs | If Tier 3 (Steiner systems / projective planes) becomes the headline. |

PI's stated preference: a "good Computational Mathematics journal." All four above qualify.

## What this strategy does *not* commit to

- Real-world biomedical applications. Out of scope per the PI's clarification.
- Comparison with HIC (Feng et al. 2024). HIC is WL-kernel-based and does not produce canonical strings; comparison is apples-to-oranges. We cite it as the gap statement, not as a baseline.
- Comparison with the Babai 2016 / Arvind et al. 2022 algorithms. Neither is implemented. Cited as theoretical ceiling.
- A theoretical complexity bound for IsalHG. Stretch goal; the empirical exponents in Tier 2 carry the practical-complexity argument.

## References

Inline citations above. Full bibliography lives in `docs/refs.bib` (to be created). Highest-priority entries:

- Babai, L. (2016). *Graph Isomorphism in Quasipolynomial Time.* STOC 2016. arXiv:1512.03547.
- Arvind, V., Das, B., Köbler, J., Toda, S. (2022). *Hypergraph Isomorphism for Groups with Restricted Composition Factors.* ACM TALG 18(2):14. arXiv:2002.06997.
- McKay, B.D., Piperno, A. (2014). *Practical Graph Isomorphism, II.* J. Symbolic Computation 60:94–112. arXiv:1301.1493.
- Feng, Y., Han, J., Ying, S., Gao, Y. (2024). *Hypergraph Isomorphism Computation.* IEEE TPAMI 46(5):3880–3893. arXiv:2307.14394.
- Chodrow, P.S. (2020). *Configuration Models of Random Hypergraphs and their Applications.* J. Complex Networks 8(3):cnaa018. arXiv:1902.09302.
- Heinlein, D. (2023). *Enumerating Steiner Triple Systems.* J. Combinatorial Designs 31(7):449–475. arXiv:2303.01207.
- Landry, N.W. et al. (2023). *XGI: A Python package for higher-order interaction networks.* JOSS 8(85):5162.
- Cai, J.-Y., Fürer, M., Immerman, N. (1992). *An Optimal Lower Bound on the Number of Variables for Graph Identification.* Combinatorica 12(4):389–410.
- Bläsius, T., Friedrich, T., Schirneck, M. (2017). *Benchmark Graphs for Practical Graph Isomorphism.* ESA 2017. arXiv:1705.03686.
- Beigel, R., Bernasconi, A. (1999). *Hypergraph Isomorphism and Structural Equivalence of Boolean Functions.* STOC 1999. DOI:10.1145/301250.301427.
