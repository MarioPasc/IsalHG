# IsalHG: Computational Experiments Proposal

PI-approved 2026-06-08 (E. López-Rubio, Grupo ICAI, UMA). This document is the binding contract for the IsalHG empirical and theoretical validation plan. It supersedes the working drafts `VALIDATION_STRATEGY.md` v1 (2026-06-06), v2 (2026-06-06 evening), v3 (2026-06-08 morning).

**One-sentence summary.** IsalHG is an exact native canonical-string algorithm for hypergraph isomorphism, validated head-to-head against the only practically-available exact baselines — Levi reduction + the `pynauty` / `Traces` / `bliss` engines — across five data regimes (R1–R5) and three runtime tiers, with three theorem targets and a two-paper publication plan (empirical → JEA/ALENEX/JCD; theoretical → JSC/SIDMA).

**Document structure.**
- §"PI directive 2026-06-08" + §"PI sign-off 2026-06-08" — the binding strategic frame.
- §"Competitive frame (v3 lock)" — canonical statement of competitors, metrics, regimes, acceptance criteria.
- §"Context and gap" through §"Tier 5" — full validation design.
- §"Baseline stack" through §"Phase 1 deliverables" — implementation contract.
- §"Decisions resolved" — change log from v1 through v3.
- §"References" — bibliography.

**Companion documents.**
- `docs/DATA.md` — authoritative cohort spec (10 downloadable real-data
  sources + 11 synthetic generators + implementation status + paper
  sentence). Every per-dataset detail referenced in Tier 1-5 below is
  expanded there.
- `docs/CODE_DESIGN.md` — where each kind of code goes.
- `docs/DEVELOPMENT.md` — living phase-by-phase status.
- `docs/research/HANDOFF_hypergraph_benchmarks.md` — resolution
  narrative for the 2026-06-14 cohort investigation (closed 2026-06-16
  by decisions I49 + I50 below).

## PI directive 2026-06-08 (strategic pivot)

E. López-Rubio's reply to the literature-survey memo (full text in project memory `ezequiel_reply_080626.md`) rules out the IsalSR-style classification downstream as a competitive axis. Verbatim points reproduced here as the binding strategic frame:

> "Hay que elegir cuidadosamente qué batallas luchar, para no escoger aquellas que no podemos ganar. Creo que debemos presentar la propuesta como un método exacto para caracterizar hipergrafos de manera que se pueda determinar si dos hipergrafos son isomorfos sin ningún tipo de error. Así que la 'calidad de la deduplicación' en nuestro caso ha de ser siempre perfecta. […] Pero los competidores han de resolver el mismo problema, es decir, determinar sin ningún tipo de posible fallo si dos hipergrafos son isomorfos."

> "El método [Zhang ICML 2025] parece claro que no es exacto. […] Al artículo [Feng TPAMI 2024] creo que le pasa lo mismo, hay casos en los que no determina correctamente el isomorfismo."

> "[Bigraph paper] no son los hipergrafos que vamos a tratar. […] [Bai ICPR 2014] no es un algoritmo nativo para hipergrafos, ya que lo primero que hace es convertir el hipergrafo en un grafo."

**Consequences encoded into v3.**

1. **IsalHG is positioned as an exact native canonical-labelling algorithm.** Competing axis = exactness + native + runtime/scalability. The two-axes "exact iso-decision (Tiers 1–3) + downstream classification (Tier 5)" frame from v2 is dropped because the classification axis is a biased proxy for iso power (Asymmetry 6, retained from v2 as the underlying reason) and because the competitors on that axis (HIC, Zhang) are by their own theorems approximate.
2. **HWL (Feng TPAMI 2024) and k-GWL (Zhang ICML 2025) are reclassified.** They move from "primary Tier-2 baseline columns" + "Tier-5 downstream competitors" to "*reference approximate predecessors*, cited in related work, measured for incompleteness (false-positive rate vs exact ground truth) only as a sidebar in Tier 5."
3. **Tier 5 is reframed** from "kernel + neural classification replication of HIC's protocol" to "**exact iso-equivalence-class atlas on real-world hypergraph corpora**" — same datasets as HIC, completely different metric (deduplication wall-clock + equivalence-class structure + memory, all exact-vs-exact). Win condition is geometric-mean speedup over `Levi + nauty`, not classification accuracy.
4. **Alphabet extension to labels confirmed.** v3 keeps the finite-token two-tier expansion of v2 as the default. Adds a §"Alphabet design for unbounded label spaces" documenting the parameterised-instruction regularity argument as the v2-escape-hatch for future open-ended label sets.
5. **Publication targets narrow.** ICML / ICLR / TPAMI are explicitly off-table per PI ("Es demasiado teórico"). Empirical paper → JEA, ALENEX, or J. Combinatorial Designs. Theoretical paper → JSC or SIDMA. The "future TPAMI extension" line from v2 is removed.

The IsalSR analogy is therefore *partial*, not full: IsalHG inherits IsalSR's theory-first + scalability-shootout structure but **not** the SR-engine plug-and-play downstream demo. This was a viable axis in v2; under the PI directive it is removed.

## PI sign-off 2026-06-08 (validation plan approved)

After the v3 rewrite was relayed to the PI, the response approved the plan and locked the competitor set. Verbatim (full text in project memory `ezequiel_signoff_080626.md`):

> "Adelante con el plan de trabajo que propones. Hemos tenido suerte de que sólo haya dos verdaderos competidores (nauty y bliss) de la propuesta. El artículo de Daniel Neuen (2022) lo citaremos y discutiremos desde el punto de vista teórico solamente, ya que no hay implementación. Esto facilita mucho la tarea de los experimentos…"

**Operational consequences locked at sign-off.**

1. **Validation plan is approved as-is.** Proceed with Tiers 1–5 and Theorems 1–3 as documented below. Any deviation requires explicit PI reauthorisation.
2. **Two software families of true competitors:** the **pallini suite** (nauty + Traces, single dependency, shared `dreadnaut` CLI) and **bliss** (independent). The PROPOSAL keeps three *engines* (`pynauty`, `Traces`, `bliss`) because Traces is essentially free to add — it ships in the same suite as nauty and triangulates the IR-tree exploration on hard symmetric inputs. Traces can be dropped to strict-two in one edit if the paper presentation prefers it.
3. **Neuen 2022 (ACM TALG)** is a *theoretical* comparator only. Cite and discuss in related-work / theoretical-paper sections; do not implement (no public software exists).
4. **The exact-vs-exact framing is now strategically locked.** The PI flags that this *facilitates* the experiments — the narrow competitor set is a strength, not a weakness.

## Competitive frame (v3 lock, 2026-06-08)

This section is the **canonical statement** of who IsalHG is benchmarked against, what we measure, and on what data. It supersedes any contradicting fragments elsewhere in this document. Subsequent tiers (1–5) and the baseline-stack section all derive from this frame.

### Exact-only mandate

Under the PI directive 2026-06-08, **all head-to-head competitive baselines must solve the same problem IsalHG solves**: produce a correct iso-decision (or equivalently a canonical labelling) on every input pair in the v1 scope, with zero false positives and zero false negatives. Approximate methods (the WL family — HWL, k-WL on `B(H)`, k-GWL) are *not run* in any tier; they appear only in related work and as sources of pre-published expressiveness counterexamples (Feng Fig. 3, Zhang Fig. 3(a)/(b)) reused as fixtures in `tests/unit/test_canonical.py`.

### Exactness landscape — is Levi + graph-iso really the only exact route?

[Verified 2026-06-08 against the related-work census in §"Related-work census" below + an independent literature re-check.] **In practice, yes**: every software-implemented exact hypergraph-isomorphism tool reduces the input hypergraph to a coloured graph (the Levi incidence graph or an equivalent encoding) and runs a graph-iso engine on it.

| Method family | Implementation status | Exact? | Reduces to Levi (or equivalent)? |
|---|---|---|---|
| nauty + Levi (`pynauty`) | software, mature | YES | YES |
| Traces + Levi (`dreadnaut` subprocess) | software, mature | YES | YES (same pallini suite as nauty) |
| bliss + Levi (`python-igraph`) | software, mature | YES | YES |
| SageMath `IncidenceStructure.is_isomorphic` | software, mature | YES | YES — internally invokes nauty on the incidence graph |
| GAP + FinInG `IsIsomorphicIncidenceGeometry` | software, design-theory specialist | YES | YES — uses GAP's nauty interface |
| Schweitzer & Wiebking STOC 2019 (HF-set canonicalisation) | **theoretical only — no public implementation** | YES | NO — different framework (hereditarily finite sets) |
| Babai & Codenotti FOCS 2008 (`exp(O(k²√n log n))`) | **theoretical only** | YES | NO — group-theoretic |
| Neuen ACM TALG 2022 (current best bound `(n+m)^O((log d)^c)`) | **theoretical only** | YES | NO — group-theoretic |
| Arvind, Das, Köbler, Toda Algorithmica 2015 (FPT for colored HG) | **theoretical only** | YES | NO — group-theoretic |

**Refined claim (corrected from the original "Levi is the only exact method"):** the only *practically available, software-implemented* exact hypergraph isomorphism method is the Levi reduction + a coloured graph-iso engine. The bottom four rows are exact algorithms in the literature but have no public software implementations; they are cited as theoretical comparators only (related-work scaffolding), not benchmarked against.

The competitive frame for IsalHG is therefore:

- **Run head-to-head as exact iso-decision baselines:** Levi + `{pynauty, Traces, bliss}`. Three engines on one reduction.
- **Cited as theoretical comparators (no software, not run):** Schweitzer-Wiebking 2019, Babai-Codenotti 2008, Neuen 2022, Arvind et al. 2015.
- **Cited as approximate predecessors (do not solve the same problem, not run):** Feng TPAMI 2024 (HWL), Zhang ICML 2025 (k-GWL), Cai-Fürer-Immerman 1992 (k-WL on `B(H)`), Bai ICPR 2014 (line-graph kernel).

### Engine list — note on Traces (2026-06-08)

The user-facing statement of the v3 plan mentions "nauty and bliss"; v3 actually includes a third engine, **Traces**, by default. Reasoning:

- Traces ships in the same pallini suite as nauty (a single `apt install` provides both; `dreadnaut` is the command-line interface to both).
- Traces uses a different individualisation-refinement heuristic from nauty (DFS-style search with a different cell-selector) and *dominates nauty on irregular / hard-symmetric inputs* — this is documented in McKay & Piperno 2014 §6, and it is exactly the regime Tier 3 targets.
- Including Traces is essentially free: one subprocess wrapper, no new dependency.

**Default v3 plan: keep all three engines (`pynauty`, `Traces`, `bliss`).** If you prefer to narrow to two for paper presentation simplicity, this is a one-edit change.

### Headline metrics

Every metric below is computed identically across the four methods (IsalHG, Levi+pynauty, Levi+Traces, Levi+bliss). Paired per-instance reporting allows paired statistical tests (Wilcoxon signed-rank on `log T_baseline / T_isalhg` for Tier-2 cells with `n ≥ 30` instances).

| Metric | Definition | Units | Reported in |
|---|---|---|---|
| **Wall-clock per instance** | Time to compute canonical fingerprint of `H` (or to decide `H_1 ≅ H_2`; the two are equivalent up to a constant via fingerprint equality). Measured with `time.perf_counter()` (monotonic). Median ± IQR over 10 repeats per instance. | seconds | Tier 2, 3, 5 |
| **Peak resident-set size** | Maximum process memory during the operation. `resource.getrusage(RUSAGE_SELF).ru_maxrss` on Linux. | bytes | Tier 2, 3, 5 |
| **Canonical-fingerprint length** | `abs(fp_M(H))` in bytes for method `M`. For IsalHG: canonical-string byte length. For nauty/Traces/bliss: serialised canonical-permutation length. | bytes | Tier 2, 5 |
| **Fingerprint compactness ratio** | `abs(fp_M(H)) / log_2 abs(Auth(H))` — the entropy-relative encoding length introduced in IsalGraph. `abs(Auth(H))` from nauty's automorphism-group output. Only reported when `abs(Auth(H))` is computable within timeout. | dimensionless | Tier 5 |
| **Cross-method verdict agreement** | Did all four methods (IsalHG + 3 Levi engines) produce the same iso verdict on this instance / pair? | binary 0/1 per instance | Tier 2, 3, 5 |
| **Cross-method partition agreement** | Did all four methods produce identical iso-equivalence partitions of the corpus? | binary 0/1 per dataset | Tier 5 |
| **False-positive / false-negative rate** | IsalHG vs. Levi+nauty (oracle). FP = "IsalHG says iso, nauty says non-iso"; FN = reverse. Triangulated against Traces and bliss. **Must be 0 across all tiers.** | rate over `N × repeats` pairs | Tier 2, 3, 5 |
| **Speedup over best-of-Levi** | `T_min(pynauty, Traces, bliss) / T_isalhg` per instance. Reported as geometric mean per dataset / family, plus per-instance distribution box-plot. | dimensionless | Tier 2, 3, 5 |
| **Crossover `(n, m, r)`** | Boundary in the `(n, m, r)` sweep where IsalHG and best-of-Levi cross. Reported as the smallest `m/n` (or `m`, `n`, `r`) above which IsalHG dominates each engine. | composite | Tier 2 |
| **Empirical complexity exponents** | Coefficients `α, β, γ` in `log T = α log n + β log m + γ log r + const` per method, fit by least-squares on Tier-2 data with `R²` reported. | dimensionless | Tier 2 |
| **Hardness atlas entry** | Per-instance wall-clock + verdict on each Tier-3 hard family. Tabulated, not aggregated — sample sizes are too small for significance testing. | composite | Tier 3 |
| **Timeout rate** | Fraction of instances where method exceeded the 600 s wall-clock budget. | percentage | Tier 2, 3, 5 |

The four-way symmetric setup (one canonical fingerprint per method) is what makes the exact-vs-exact comparison clean. Approximate methods would need a separate metric panel (multiset-hash equivalence ≠ canonical-form equality); since we removed them from the run, no separate panel is needed.

### Data regimes — what we run on, in what order

The exact-vs-exact comparison runs across five regimes (R1–R5), in increasing order of hostility to the Levi baseline:

| Regime | Defining property | Generator / source | Tier | Predicted outcome |
|---|---|---|---|---|
| **R1 — small exhaustive** | All connected hypergraphs on `n ∈ {3..6}` vertices, `r ∈ {2,3,4}`, exhaustively enumerated; plus published designs (Fano plane, STS(9), two non-iso STS(13), GQ(2,2)) | XGI `uniform_erdos_renyi_hypergraph` enumeration + SageMath designs | 1 | Both methods trivially fast; correctness is the only test. Primary purpose: verify IsalHG fingerprint equals Levi+nauty canonical form on every iso-equivalent pair and differs on every non-iso pair. |
| **R2 — sparse random** | `n ∈ {50, 100, 250, 500, 1000, 2500}`, `r ∈ {3, 4, 5}`, `m/n = 1`, 10 seeds per cell | XGI `uniform_erdos_renyi_hypergraph` | 2 | Levi-nauty competitive or favoured (small bipartite graph `\|B(H)\| = n + m ≈ 2n`); IsalHG should be within a constant factor. |
| **R3 — medium / dense random** | Same `n, r` as R2; `m/n ∈ {5, 25}` | XGI + Chung-Lu heavy-tailed degree (`chung_lu_hypergraph`) | 2 | Levi penalty grows linearly with `m` (`\|B(H)\| = n + m`). IsalHG predicted to dominate at large `m/n` because it operates directly on `H` without inflating the vertex set. **The crossover `m/n` is the Tier-2 headline number.** |
| **R4 — hard symmetric** | Projective planes `PG(2, q)` for `q ∈ {7,8,9,11,13}`; large-Aut Steiner triple systems; generalized quadrangles GQ(2,4), GQ(3,5); non-group Latin squares with large autotopy; random `r`-uniform `d`-regular HG at threshold density | SageMath `designs.*`, GAP+FinInG, custom rejection-sampler | 3 | Levi+nauty may time out on regular structure (Miyazaki-type behaviour from large `|Aut|`). IsalHG's backtracking-bounded canonical algorithm targets exactly these cases. **Wins here are the qualitative differentiator.** |
| **R5 — real-world corpora** | HIC's 12 datasets used as deduplication workloads (compute iso-equivalence partition of the corpus per method) | Bundled with HIC GitHub repo | 5 | Applied headline: geometric-mean speedup over best-of-Levi across the 12 datasets. Target: ≥ 2× on at least 4 datasets, ≥ 1× on at least 8. |

The paper's empirical section walks the reader through R1 → R5 in this order. Each transition argues a specific claim: R1 = "correct"; R2 = "competitive in the easy regime"; R3 = "dominant when `m` grows"; R4 = "qualitative advantage on symmetric structure"; R5 = "translates to real data".

### Approximate-method comparison policy

Reiterated for clarity (this is *the* contract):

- **Not run head-to-head in any tier.** HWL, k-WL on `B(H)`, k-GWL, HIC kernels, Zhang's k-HNN, Bai's line-graph kernel — none of these is invoked at runtime.
- **Cited in related work.** One paragraph each in the empirical paper's Related Work and one paragraph in the theoretical paper's Related Work. Citations include the published expressiveness theorems (Zhang Thm 5.2/5.3) and counterexample figures (Feng Fig. 3, Zhang Fig. 3(a)/(b)).
- **Reused as test fixtures.** The published counterexamples become hand-coded fixtures in `tests/unit/test_canonical.py`. IsalHG must distinguish each pair; that's the smallest verifiable statement of "IsalHG ≥ HWL / 2-GFWL" expressiveness, without us re-running anything.
- **No runtime comparison.** Even where an approximate method is faster, the comparison is not reported as a competitive number — they solve different problems (see §"Approximate methods: cited, not implemented" for the design-context six-row table).

### Acceptance criteria summary

The success of the empirical paper rests on the conjunction of these per-tier conditions:

| Tier | Pass condition |
|---|---|
| **Tier 1** | IsalHG fingerprint matches Levi+nauty canonical-form-equality on every enumerated `n ≤ 6` hypergraph and every published design. FP = FN = 0. Bijection certificate (E24) valid on every iso pair. HWL and k-GWL fixtures from Feng/Zhang Figure 3 distinguished. |
| **Tier 2** | (a) FP rate = 0 and FN rate = 0 for IsalHG vs Levi+nauty across all `N × 10` pairs (triangulated against Traces and bliss). (b) Empirical complexity exponents `(α, β, γ)` reported for all four methods with `R² ≥ 0.9`. (c) Crossover `m/n` identified per Levi engine. (d) IsalHG dominates best-of-Levi in geometric-mean wall-clock at the largest cell `(n=2500, m/n=25, r=5)`. |
| **Tier 3** | IsalHG completes ≥ 3 hard families on which Levi + best-of-three exceeds the 600 s timeout. No false verdicts on any documented non-iso pair within the families that do complete. |
| **Tier 5** | (a) `P_IsalHG = P_pynauty = P_Traces = P_bliss` on every one of the 12 datasets (correctness invariant). (b) Geometric-mean speedup over best-of-Levi ≥ 2× on at least 4 datasets, ≥ 1× on at least 8. (c) `max_rss(IsalHG) ≤ max_rss(best-of-Levi)` on at least 6 of 12 datasets. |

Failure on any of these collapses the empirical paper's headline. They are the contract IsalHG must meet to ship paper (a).

## Context and gap

The PI's framing rules out the obvious biomedical applications: protein-protein and chemical-reaction hypergraphs have pre-identified named nodes, so the isomorphism question never arises. Validation has to be **structural / theoretical**: prove and empirically demonstrate that IsalHG computes an isomorphism-invariant canonical string efficiently, faster than the standard `H → bipartite incidence graph → graph-iso tool` reduction.

The literature confirms the gap is real, but the gap statement is sharper than the v1 draft claimed (corrected 2026-06-06 after deep-reading Feng et al. 2024; see decision log A4-revised):

- **Two distinct prior-art tracks exist; both fail in different ways.**
  - **Track 1: native but provably incomplete.** Feng, Han, Ying & Gao, *Hypergraph Isomorphism Computation*, IEEE TPAMI 46(5):3880–3893, 2024 [DOI:10.1109/TPAMI.2024.3353199] (HIC) introduces a Hypergraph Weisfeiler–Leman (HWL) refinement that operates **natively on the hypergraph** via incidence-matrix neighbour functions — no bipartite expansion. It is explicitly framed in the paper's abstract and conclusion as "a solution to the hypergraph isomorphism problem." However, the same paper (§4.1, Figure 3) demonstrates a pair of non-isomorphic hypergraphs HWL cannot distinguish, with **no characterisation of the failure family and no false-positive rate reported**. HWL produces a vertex-label multiset, not a canonical string.
  - **Track 2: provably equivalent to graph-iso but `m`-penalised.** Neuen, *Hypergraph Isomorphism for Groups with Restricted Composition Factors*, ACM TALG 18(3), Article 21, 2022 [DOI:10.1145/3527667] (corrected attribution 2026-06-07 after literature census; previously misattributed to Arvind/Das/Köbler/Toda — those authors wrote the *colored*-HG FPT paper in Algorithmica 2015). The current best bound `(n+m)^O((log d)^c)` (where `d` bounds the symmetric-group order of composition factors) has `m` in the input size; the paper notes this is *"far from optimal for large numbers of hyperedges."* All implemented tools (nauty, Traces, bliss, SageMath `IncidenceStructure`, GAP+FinInG) realise this Track-2 reduction practically via the Levi incidence graph.
- **The IsalHG gap statement** is therefore: *no native, exact, canonical-labelling tool exists*. HIC is native but approximate; Track-2 tools are exact but reduce away. IsalHG is both native and exact (subject to Theorem 2). This is the headline contribution. **PI directive 2026-06-08 makes this gap statement the sole positioning claim** — the v2 secondary positioning of "competitive on hypergraph classification" is retired.
- **Axis-A null result (verified 2026-06-07).** A focused literature census across arXiv, ACM DL, IEEE Xplore, Semantic Scholar, and DBLP found **zero prior work** encoding a hypergraph as a sequence of instructions over a virtual-machine alphabet intended to serve as a canonical isomorphism invariant. The structurally closest analog is Grzelak & Aßmann, *A Canonical String Encoding for Pure Bigraphs*, SN Comput. Sci. 2 (2021) Art. 246, DOI:10.1007/s42979-021-00552-5 — but for Milner's bigraphs, a different object class (process topology, not combinatorial hypergraphs). Schweitzer & Wiebking (STOC 2019, arXiv:1806.07466) canonize hypergraphs into integer permutations via hereditarily-finite-set reduction — same logical goal, fundamentally different output representation, no string-length semantics. **IsalHG occupies a structurally unoccupied niche** on the native-canonical-string axis.
- **Axis-C null result (verified 2026-06-07).** No dedicated survey, benchmark paper, or systematic experimental comparison of hypergraph isomorphism algorithms exists in the literature. This makes our Tier-2 + Tier-3 empirical study one of the first such comparisons and increases its standalone value.
- **The community-standard WL → classification pattern is explicitly rejected.** HIC (TPAMI 2024) and Zhang et al. (ICML 2025) both (i) propose a WL-style iso-expressiveness theory, (ii) derive a neural / kernel model, (iii) evaluate on hypergraph-level classification. Their downstream classification is a biased proxy for iso power (see *Fairness analysis* §6 — retained from v2 as the underlying explanation), and their iso tests are approximate (Zhang Theorems 5.2 / 5.3 establish a *strict* hierarchy `(k+1)-GWL ⊋ k-GWL`, which means for every fixed `k` there exist non-isomorphic hypergraph pairs `k`-GWL collapses; HIC's Figure 3 exhibits an explicit HWL-collapsed pair). IsalHG does not enter that proxy battle; per PI directive, our iso-decision axis is exact-vs-exact (Levi+nauty / Traces / bliss / SageMath / GAP), and the same real-world datasets used by HIC/Zhang are reused in Tier 5 only as deduplication workloads under an exact-iso metric.
- **Zhang's named open problem is what IsalHG bypasses.** Verbatim from Zhang et al. §Conclusion: *"developing computationally efficient hypergraph deep learning models with provably high expressivity for a large value of k in k-GWL"*. Their k-GWL pays `O(h · k · n^{k+1})` (exponential in `k`); preprocessing alone takes 12–24 hours for `k = 2` on their public repo. **IsalHG sidesteps the WL hierarchy** via instruction-string canonicalisation, conjectured complete (Theorem 2) — no `k` to choose, no exponential cost. This positioning is **rhetorical, not competitive**: IsalHG is not benchmarked against k-HNN under the PI directive, because the two methods solve different problems (exact vs approximate). The k-GWL hierarchy is, however, the technical machinery cited as the immediate predecessor for Theorem 1 (expressiveness ≥ d-WL).

## Scope of input hypergraphs (v1)

Locked 2026-06-06 (decision log §B):

| Property | v1 | Rationale |
|---|---|---|
| Directionality | undirected only | Directed hypergraphs require a new instruction-set extension; out of seed proposal. |
| Vertex labels | **labelled (revised 2026-06-07)** | Real-world hypergraphs in Tier 5 (IMDB-*, Steam, Twitter) carry semantic vertex labels; stripping them collapses semantically distinct hypergraphs. Two-tier alphabet à la IsalSR. Was "unlabeled" in v1. |
| Edge labels | **labelled (revised 2026-06-07)** | Same justification — hyperedges in real datasets carry one semantic label each (movie metadata, game session ID). Edge weights remain out of scope. |
| Edge weights | unweighted | Weights remain a follow-up. |
| Multi-hyperedges | not supported | The seed proposal's `C_i` is a no-op on duplicates; consistent. |
| Connectivity | connected (v1) | Disconnected requires per-component encoding + lex-min merge; deferred. |
| Max arity `k` | `k ≤ 10` | Covers projective planes up to PG(2, 7); keeps alphabet manageable. |
| Finiteness | finite | Trivially. |

Any input outside this class is rejected at the adapter boundary.

## Theoretical contributions

Three theorem targets are committed to this work-stream (decision log §C). Items 1 and 3 are gating for the theoretical paper (see *Publication strategy*); item 2 is gating for both papers.

### Theorem 1 — Expressiveness vs Weisfeiler–Leman

**Claim.** For every depth `d ≥ 1`, IsalHG with structural-tuple depth `d` distinguishes every pair of hypergraphs that `d`-WL on the bipartite incidence graph distinguishes.

**Proof strategy.** Induction on refinement rounds. The base case is direct (depth-1 IsalHG seed = degree-coloring). Inductive step: each IsalHG refinement step using `(ξ_1, ..., ξ_d)` strictly refines the partition produced by the corresponding WL round on `B(H)`. The WL hierarchy on bipartite graphs is standard (Cai–Fürer–Immerman 1992; Kiefer–Schweitzer–Selman 2015). A modern reference for the strict hierarchy `(k+1)-GWL ⊋ k-GWL` *on hypergraphs* — applicable directly to our claim — is Zhang et al., *Improved Expressivity of Hypergraph Neural Networks through High-Dimensional Generalized Weisfeiler-Leman Algorithms*, ICML 2025 (PMLR v267). Cite as the immediate predecessor and the theorem reviewers will demand backing the expressiveness claim.

**Status.** Proof obligation for the theoretical paper.

### Theorem 2 — Canonical-string completeness

**Claim.** For every pair `(H_1, H_2)` of hypergraphs in the v1 scope: `w*_{H_1} = w*_{H_2} ⇔ H_1 ≅ H_2`.

**Proof strategy.** Port the IsalGraph completeness proof (Theorem 2.12 of López-Rubio & Pascual-González 2026) to **labelled** hypergraphs. The induction tracks hyperedge-set comparisons over `(label, node-set)` pairs instead of pair comparisons; the seed selection uses label-aware `ξ` (count of labelled neighbours at distance `h` per label class). The IsalGraph proof depends on (i) the structural-triplet's stability under isomorphism, (ii) determinism of the greedy under tie-breaking, and (iii) the canonical-seed argument. (ii) requires Theorem 3 below. The labelled extension follows the IsalSR Theorem 3.15 recipe — same proof skeleton, label-preserving isomorphism throughout.

**Failure mode.** If the proof breaks at a specific lemma, the breaking instance is itself a publishable counterexample (companion paper, see §F). Falsification is OK — silent failure is not.

**Status.** Gating for the theoretical paper. The empirical paper can ship before this lands, framed as "completeness conjectured, verified on all N tested instances" (decision log F28).

### Theorem 3 — Backtracking termination and bound

**Claim.** The backtracking step the PI left unspecified terminates in time `O(|Aut(H)| · μ(H))`, where `μ(H)` is the maximum tuple-tie multiplicity over the H2S build sequence. Average-case behavior on random hypergraphs is polynomial.

**Proof strategy.** Each backtrack branch corresponds to a coset of `Aut(H)` acting on the current pointer configuration. The greedy resolves all but `μ(H)` ties; backtracking explores the remaining `μ(H)^k` configurations for `k` pointers, bounded above by `|Aut(H)|` by Cayley's theorem. Random hypergraphs have `|Aut(H)| = 1` almost surely (Erdős–Rényi rigidity); worst case is Tier 3 (large-Aut combinatorial designs).

**Note.** The worst-case bound is concession to the structure of the problem — IR-based tools (nauty, Traces) also have `|Aut(H)|`-type worst cases. The argument is that IsalHG's *average* case beats nauty's worst case on hyperedge-heavy instances.

**Status.** Proof obligation for the theoretical paper. The empirical paper specifies the algorithm and reports empirical backtrack-counts per family.

### What we are NOT proving in this work-stream

- **Worst-case complexity bound on IsalHG.** Empirical-only (decision log C17). Tier 2 fitted exponents `α, β, γ` carry the practical-complexity argument.
- **Hypergraph-CFI construction.** Deferred to companion paper (decision log C14). If the construction reveals a completeness gap, that's a separate contribution worth its own venue.

## Validation design — five tiers

The five tiers (R1–R5 in the Competitive frame above) correspond to Tier 1 (correctness), Tier 2 (R2 + R3, runtime scaling), Tier 3 (R4, hardness stress), Tier 4 (real-world structural calibration), Tier 5 (R5, real-world deduplication atlas). The hardness-stress family selection draws on Neuen & Schweitzer, *Benchmark Graphs for Practical Graph Isomorphism*, ESA 2017 / arXiv:1705.03686 — they establish that random rigid instances are the hardest known for IR-based graph-iso engines, and that previously-known hard families (projective planes, Steiner systems, CFI) are weaker but useful calibration points. We adopt their hard-family motivation for Tier 3 but **not** their experimental protocol: they run a single-instance-per-size scaling sweep with no seeds, no grid, no fitted exponents; our Tier 2 grid `(n, r, m/n) × 10 seeds` is methodologically stricter.

### Tier 1 — Correctness (small, exhaustive)

**Goal.** Catch implementation bugs in S2H / H2S / canonical. Verify both directions of the iso equivalence on instances small enough to enumerate.

**Instances.**
- All connected hypergraphs on `n ∈ {3, 4, 5, 6}` vertices with arity `k ∈ {2, 3, 4}`, enumerated exhaustively by `itertools.combinations` over the candidate-edge universe (`∪_a C(n, a)`), filtered by `SparseHypergraph.is_connected()`, and deduplicated by iso-class via the fingerprint of any registered `IsoBackend` (`pynauty_levi` is the default oracle inside `ExhaustiveSmallHypergraphs`; `isalhg` is selectable for stdlib-only dedup at much lower throughput). Note that "using pynauty as dedup oracle" is *not* circular under the v3 framing: IsalHG is a drop-in alternative engine, not an alternative ground-truth oracle — see `docs/DATA.md` §1 for the full framing. XGI is *not* used to enumerate iso-classes — its generators (`uniform_erdos_renyi_hypergraph`, `chung_lu_hypergraph`) are samplers, not enumerators, and do not guarantee coverage of the iso-class lattice.
- The **Fano plane** STS(7) = PG(2, 2): 7 vertices, 7 triples, `|Aut| = 168`.
- STS(9) = AG(2, 3): 9 vertices, 12 triples, `|Aut| = 432`.
- **The Kaski-Östergård plaintext STS catalogs** (decision I50, 2026-06-16). Files `sts{3,7,9,13,15}.txt` from `https://pottonen.kapsi.fi/sts19/` parsed in pure Python; STS(13) ships 2 non-iso classes, STS(15) ships 80 non-iso classes — together 85 published iso classes with nauty-certified non-isomorphism via the Mathon-Phelps-Rosa 1983 classification (`Ars Combinatoria` 15:3-110). Replaces the prior cyclic-construction STS(13) (Z/13Z, starter blocks `{0, 1, 4}` and `{0, 1, 6}`, non-iso verified empirically against `pynauty_levi` at construction) with the canonical published source. STS(19) `1k_sample` (1000 non-iso classes, custom compressed binary, requires building the `stsc` C decompressor) deferred to Tier 3.
- **Generalized quadrangle GQ(2, 2) ("doily")**: 15 points, 15 lines, `|Aut| = 720`. Small, hard, classic.
- **The HWL failure pair from Figure 3 of Feng et al. TPAMI 2024.** Two non-isomorphic hypergraphs that HWL hashes identically. **Mandatory acceptance criterion (5 below)**: IsalHG must distinguish this pair, or the headline competitive claim fails before submission. *Implementation note*: Per Phase 3 decision D1 (2026-06-13), extraction of the explicit edge lists for the Feng et al. Fig. 3 pair and the Zhang et al. ICML 2025 Fig. 3(a)/(b) pairs is deferred to Phase 3.5; Phases 3 and 4 close on the remaining design-theoretic fixtures.

#### Tier 1c — Three-way comparison on the LLM4Hypergraph corpus (decision I49, 2026-06-16)

A sub-cohort added under Tier 1 to give IsalHG external validity outside the combinatorics tradition. The iMoonLab/LLM4Hypergraph repository (`github.com/iMoonLab/LLM4Hypergraph`, Apache 2.0) accompanying Feng et al. *"Beyond Graphs: Can Large Language Models Comprehend Hypergraphs?"* (ICLR 2025, arXiv:2410.10083) ships an iso-recognition benchmark — pairs of small hypergraphs (n ∈ {5-9, 10-14, 15-19}, edge count Uniform(0.2n, 1.5n), arity geometric) labelled iso / non-iso. Positive pairs come from `HyperGraph.shuffleNode()` (random vertex permutation, semantically identical to our `core.permute(H, σ)`); negative pairs come from resampling with matched arity sequence then filtering for accidental iso via `test_isomo.HGSCKernel`.

**The wrinkle that creates the contribution.** `test_isomo.py` is missing from the public release — the generator crashes at line 1327 of `hypergraph_task.py` as shipped. Substituting `PynautyLeviBackend.are_isomorphic()` for the missing oracle gives the only nauty-certified version of the corpus, and the LLM verdicts from the paper's supplementary (GPT-4, Claude, etc.) give a third column. Concretely:

1. Vendor LLM4Hypergraph under `third_party/llm4hypergraph/` (license-compatible).
2. Patch `IsomorphismRecognition.prepare_examples_dict` to call `PynautyLeviBackend.are_isomorphic()`.
3. Regenerate the cohort with `--random_seed=1234` (their hardcoded test seed).
4. Define `LLM4HypergraphIsoRecognition` as a `HypergraphDataset` subclass under `src/isalhg/datasets/llm4hypergraph.py`.
5. Run IsalHG via the standard `PairwiseIsoProtocol`; the LLM verdicts from the published supplementary give the third column.

**Headline.** Three-way (LLM verdict, nauty ground truth, IsalHG verdict) on the only published hypergraph iso-recognition benchmark in the field. Full per-dataset narrative in `docs/DATA.md` §2.6.

**Acceptance criterion (added to Tier 1).** `IsalHG.verdict == pynauty.verdict` on every pair in the corpus, and the resulting (IsalHG vs LLM) confusion matrix matches the (nauty vs LLM) confusion matrix reproduced from Feng et al. ICLR 2025 supplementary up to rounding.

**Acceptance criteria.**
1. `S2H(H2S(H)) ≅ H` for every instance (Hypothesis property test).
2. `canonical(H) = canonical(π(H))` for 100 random vertex permutations `π` per instance.
3. `canonical(H_1) ≠ canonical(H_2)` for every published non-isomorphic pair.
4. **Bijection certificate** — for every iso pair, the H2S replay produces a vertex bijection `π : V(H_1) → V(H_2)` that is verified independently (decision log E24).
5. **HWL-distinguishability** — `canonical(H_1) ≠ canonical(H_2)` for the Feng et al. Figure 3 pair (where HWL collides). This is the smallest known instance of the IsalHG vs HWL expressiveness gap.
6. **2-GOWL-distinguishability** — distinguish the Zhang et al. Figure 3(a) pair (which 1-GWL/HWL collapses). Demonstrates IsalHG ≥ 2-GOWL expressiveness.
7. **2-GFWL-distinguishability** — distinguish the Zhang et al. Figure 3(b) pair (which 2-GOWL collapses). Demonstrates IsalHG ≥ 2-GFWL expressiveness — above the current ICML state-of-the-art baseline.

#### Isomorphism-pair generation policy (decision I44, 2026-06-11)

Correctness criterion 2 above demands a stream of *isomorphic* pairs `(H, π(H))` with a *known* ground-truth permutation `π`. Criterion 3 demands a stream of *non-isomorphic* pairs that no easy invariant (degree sequence, edge-size distribution) separates. The two streams are sourced differently — bundling them under a single "random generator" is the trap that silently produces too-easy negatives.

**Positive pairs (iso) — `core.permute(H, σ)`, no external library.** Generating an isomorphic copy is a one-function operation: sample `σ ∈ S_n` uniformly with the run's pinned RNG, relabel every hyperedge under `σ` (and, under the labelled v1 scope, carry vertex/edge label maps through unchanged — labels are *preserved* by iso, not permuted). This is ~10 lines on top of `SparseHypergraph` and lives in `isalhg.core.sparse_hypergraph` as a free function `permute(H: SparseHypergraph, sigma: dict[NodeId, NodeId]) -> SparseHypergraph`. We do **not** delegate to `xgi.Hypergraph.relabel_nodes` or `HyperNetX.translate`: importing either pulls an optional dep into a code path that should stay stdlib (`core/` is stdlib-only per `CODE_DESIGN.md` §4), and the existing labelled `SparseHypergraph` is the only ground-truth carrier we can trust for the bijection certificate (E24). The known `σ` is the oracle: the H2S-replay-derived bijection `π̂` is compared cell-by-cell against `σ` (or against `σ ∘ Aut(H)` when `|Aut(H)| > 1`).

**Hard negative pairs — design-theoretic instances + pynauty-certified random sweeps.** Three sources, ordered by strength of guarantee:

1. **Published design-theoretic non-iso pairs with classified iso classes.** For 3-uniform hypergraphs: exactly 2 non-iso STS(13), 80 non-iso STS(15) [Kaski & Östergård 2004, *Math. Comp.* 73(248):2075–2092, DOI:10.1090/S0025-5718-04-01626-6]. Two STS(13) of the same parameters and matching `|Aut|` agree on every easy invariant by construction; they are the gold-standard Tier 1 hard negatives. Embedded as Phase 1 fixtures in `tests/conftest.py`, not regenerated at run-time.
2. **Pynauty-certified random pairs** (used in Tier 2 / Tier 3, not Tier 1). Sample two random hypergraphs from `xgi.uniform_erdos_renyi_hypergraph` or `xgi.chung_lu_hypergraph` with matched degree-and-edge-size sequence; certify non-iso via `pynauty_levi` before adding to the pair stream. This shifts the trust to nauty, which is exactly what the v3 frame already does (pynauty is the oracle in E23). Pairs that nauty cannot certify within 60 s are discarded, not silently accepted.
3. **HG-CFI construction** (open, C14). The hypergraph lift of Cai–Fürer–Immerman would give synthetic hard negatives matched on every WL-bounded invariant. Until C14 produces a construction, this source is empty; the documentation acknowledges the gap rather than substituting random-regular hypergraphs in its place.

Tier 1 uses sources (1) and the Feng / Zhang Figure-3 fixtures only. Tier 2 / Tier 3 introduce source (2). The policy is asymmetric on purpose: positive pairs are cheap and trustworthy, negative pairs are the scientific load-bearing direction and require certification.

**What this rules out.** Random vertex permutation as a stand-alone "iso generator library" is *not* an import dependency — it is a 10-line function on `SparseHypergraph`. Library helpers (`xgi.relabel_nodes`, `nx.relabel_nodes` on the Levi reduction) are noted in related-work footing only; they are not on the critical path.

### Tier 2 — Runtime scaling

**Goal.** Produce time-vs-size curves of IsalHG vs. the full baseline stack. Empirical-complexity argument.

**Sweep.** `n ∈ {50, 100, 250, 500, 1000, 2500}`, uniform arity `r ∈ {3, 4, 5}`, hyperedge count `m` chosen to fix `m/n ∈ {1, 5, 25}` (sparse / medium / dense). 10 random seeds per `(n, r, m)` cell.

**Generators.** `xgi.generators.uniform.uniform_erdos_renyi_hypergraph(n, r, p)` for uniform random; `xgi.generators.random.chung_lu_hypergraph` for heavy-tailed degree sequences [Chodrow 2020, arXiv:1902.09302]. Calibration ranges informed by Tier 4.

**Baselines run on every instance.** pynauty, Traces, bliss (via python-igraph). All three operate on the Levi incidence graph `B(H)` (see §"Bipartite reduction" for the exactness argument). These are the only iso-decision baselines under the PI directive 2026-06-08; approximate WL-track methods are cited but not implemented (see §"Approximate methods: cited, not implemented").

**Correctness cross-check.** Every IsalHG verdict is cross-checked against pynauty. Report false-positive rate (IsalHG says iso, pynauty says non-iso) and false-negative rate (reverse) across all `N × 10` Tier-2 instances (decision log E23). Both rates must be 0 for the exact claim to hold; any non-zero rate is a bug or a Theorem-2 counterexample (publishable in its own right per F28). Triangulation across pynauty / Traces / bliss further hardens this — all three must agree.

**Metrics.** Wall-clock time (median ± IQR over 10 seeds), peak memory `max_rss`, canonical-string length. Report a fit `T ~ n^α m^β r^γ` per algorithm side by side.

**Predicted outcome.** IsalHG should be roughly competitive in the sparse regime (small `m`) and pull ahead as `m` grows — exactly the regime Neuen 2022 (ACM TALG, current best theoretical bound `(n+m)^O((log d)^c)`) calls out as suboptimal for the Levi reduction (which inflates the vertex set by `m`). The headline number is the **crossover `m / n`** above which IsalHG dominates the best of `{pynauty, Traces, bliss}`.

### Tier 3 — Hardness stress test (the headline experiment)

**Goal.** Demonstrate IsalHG handles cases where the bipartite-reduction baselines either time out or scale catastrophically due to large automorphism groups.

**Instances (revised after §D reality check).**

| Family | Construction | Why hard for the baseline |
|---|---|---|
| Projective planes `PG(2, q)` for `q ∈ {7, 8, 9, 11, 13}` | SageMath `designs.projective_plane(q)`; `q = 9` includes the 4 non-Desarguesian planes via GAP+FinInG | Smaller `q` deferred until pynauty timing on `PG(2, 9)` is measured (decision log D18 — runs in Phase 1 before strategy lock). `(q+1)`-uniform, regular; `|Aut PG(2, 7)| ≈ 1.8 × 10^6`. |
| Large-automorphism Steiner triple systems | SageMath `designs.steiner_triple_system(n)` for `n ∈ {7, 9, 13, 15}`, restricted to the explicitly-enumerated large-Aut classes (decision log D19) | The few small-`n` STS with large `|Aut|` are the genuine hardness instances; large-`n` STS are almost all rigid and easy for nauty. We do NOT claim STS(19) hardness. |
| Generalized quadrangles GQ(2, 4), GQ(3, 5) | GAP+FinInG | High regularity + large automorphism groups. |
| Non-group Latin squares with large autotopy | SageMath `latin` + autotopy filter (decision log D20) | Cayley tables of `Z_n` are easy for nauty (regular automorphism); the hard regime is large autotopy groups *without* a regular group action. Construction is research-effort. |
| Random `r`-uniform `d`-regular hypergraphs at threshold density (decision log D21) | Custom rejection-sampler on XGI; `(r, d, n)` swept | Graph-iso solvers behave erratically at the regularity threshold; closest synthetic analog of hard real-world cases. |

**Generation pipeline.** SageMath subprocess wrapper in `experiments/hard_cases/`, output as JSON hypergraph dumps (`xgi`-compatible) so the iso-comparison runner doesn't depend on SageMath. GAP+FinInG and random-regular generation in sibling subdirs.

**Reporting (decision log E25).** Case-by-case "hardness atlas" — per-instance wall-clock table with 95% CI from 10 reruns. No aggregated significance test (sample sizes too small for that). Geometric-mean speedup per family reported separately.

**Acceptance criteria.**
- IsalHG returns the correct iso decision on every documented non-isomorphic pair within a 600-second timeout (decision log E26).
- The Levi + `{pynauty, Traces, bliss}` baselines either take ≥ 10× longer than IsalHG or time out on at least three families. This is the **primary headline** under the PI directive.
- HWL incompleteness is referenced via Feng et al. TPAMI 2024 Figure 3 (their own published counterexample); we do *not* re-implement HWL just to re-derive a number their own paper already publishes (decision I43, 2026-06-08).

### Tier 4 — Real-world structural calibration

Real datasets feed back into Tier 2 sweep ranges so synthetic instances cover the realistic regime (decision log G30). **Not used for iso testing** per PI framing.

Sources: Austin Benson's ARB collection (`cornell.edu/~arb/data/`), `xgi.load_xgi_data("email-Enron")` and other XGI-DATA loaders [Landry et al. 2023, DOI:10.21105/joss.05162]. One pass over `email-Enron`, `contact-high-school`, `congress-bills`: extract arity histogram, degree distribution, density. One-page paper section showing real arity/degree distributions vs the Tier 2 sweep coverage.

### Tier 5 — Exact iso-equivalence-class atlas on real-world hypergraph corpora

**Rewritten 2026-06-08 under PI directive.** v2's "kernel + neural classification replication of HIC's protocol" is dropped. The fairness analysis in v2 already established that classification accuracy is a *biased proxy* for iso power (Asymmetry 6 below — retained as the reason the rewrite was needed). v3 keeps the same 12 real-world datasets HIC and Zhang use, but the metric becomes **exact iso-equivalence partitioning over each dataset treated as an unordered corpus of hypergraphs**.

**Goal.** Demonstrate that IsalHG dominates the Levi-reduction baselines (`pynauty`, `Traces`, `bliss`) on the real-world workload of deduplicating a corpus of hypergraphs up to isomorphism. Same datasets the WL-track papers use, completely different metric: total wall-clock to compute the iso-equivalence partition.

**Datasets.** Identical to v2's Tier 5: all 12 of HIC's hypergraph datasets (Table 5 of Feng et al. 2024) — `RHG-10`, `RHG-3`, `RHG-Table`, `RHG-Pyramid`, `IMDB-Dir-Form`, `IMDB-Dir-Genre`, `IMDB-Dir-Genre-M`, `IMDB-Wri-Form`, `IMDB-Wri-Genre`, `IMDB-Wri-Genre-M`, `Steam-Player`, `Twitter-Friend`. Bundled with the HIC GitHub repo. Class labels are *ignored* — Tier 5 is iso-equivalence only.

**Workload.** For each dataset `D = {H_1, ..., H_N}` and each method `M` ∈ primary baselines (`IsalHG`, `Levi+pynauty`, `Levi+Traces`, `Levi+bliss`):

1. **Canonical-form deduplication.** Compute a canonical fingerprint `fp_M(H_i)` for each `H_i ∈ D`. Build the equivalence partition by grouping on `fp_M`. Wall-clock: `O(N · T_fp)` where `T_fp` is per-hypergraph canonicalisation cost.
2. **Pairwise iso-equivalence (sanity check).** For a stratified subsample (e.g. 200 pairs per equivalence-class size bucket), run pairwise `are_isomorphic(H_i, H_j)` and verify against the partition from step 1.
3. **Output.** Iso-equivalence partition `P_M(D)`, total wall-clock, peak `max_rss`, fingerprint-byte count distribution.

**Correctness invariant.** All exact methods must return identical partitions: `P_IsalHG(D) = P_pynauty(D) = P_Traces(D) = P_bliss(D)` for every dataset. Any disagreement is a bug or a Theorem-2 counterexample (publishable in its own right per F28). This is a strong test on real-world structure — much stronger than synthetic-only Tier-2 cross-checking.

**Approximate methods are NOT run on Tier 5.** HWL, k-WL, and k-GWL are cited as approximate predecessors (see §"Approximate methods: cited, not implemented" for the reasoning); their incompleteness is documented via the published counterexamples in their own papers (Feng Fig. 3; Zhang Fig. 3(a)/(b)). Tier 5 is exclusively a head-to-head of *exact* methods on real-world deduplication workload.

**Acceptance criteria (v3).**
1. `P_IsalHG(D) = P_pynauty(D) = P_Traces(D) = P_bliss(D)` on every one of the 12 datasets — necessary for the exact claim. Zero tolerance; any disagreement is either a bug or a Theorem-2 counterexample.
2. **Geometric-mean speedup over the best of `{pynauty, Traces, bliss}` ≥ 2× on at least 4 datasets, ≥ 1× on at least 8 datasets.** This is the real-world headline.
3. Memory: peak `max_rss(IsalHG) ≤ max_rss(best of Levi+exact)` on at least 6 of 12 datasets.
4. Fingerprint compactness: median `|fp_IsalHG(H)| / log_2 |Aut(H)|` reported (the entropy-relative encoding length, IsalGraph-style metric).

**Generators.** None new. All 12 datasets ship with HIC. No SageMath / GAP / training run / GPU needed; Tier 5 is CPU-only and fits on a workstation.

**What this tier does NOT do.**
- Does not measure classification accuracy. The PI directive is explicit that classification is a biased proxy under the exact-method framing.
- Does not benchmark Zhang's k-HNN or HIC kernel methods. They are cited as approximate predecessors only (decision I43); no FP rate or runtime is measured for them.
- Does not require reproducing Zhang's or HIC's published numbers — those numbers live in different metrics.

**Why this version of Tier 5 survives the PI directive.** It uses the same real-world data the field has converged on (no special-pleading toward synthetic) and competes on the metric the PI committed to (exact iso, runtime, scalability). The IsalSR-style classification angle from v2 is retired; this is a closer analog to the **IsalGraph** paper's structure (canonical labelling speed + correctness on real graph data, no downstream demo).

#### Why the v2 classification design fails the PI's exactness test

Retained from v2 §"Fairness analysis", reframed as the *reason* v2's Tier 5 is gone, not as the *protocol that restored fairness*:

**Asymmetry 6 (the deepest one).** HIC and Zhang use classification accuracy as a proxy for iso-discriminative power. The proxy is biased in favour of approximate methods on noisy real-world data: if two non-isomorphic hypergraphs share a class label, an exact canonical-string method splits them (correctly per iso) while an approximate WL method merges them (incorrectly per iso, conveniently per class) — and the downstream classifier may *generalise better* from the merged representation. So IsalHG can be strictly more powerful at iso decision yet underperform on classification accuracy. v2 tried to absorb this by reporting two axes; the PI directive removes the unfair axis altogether.

The other v2 asymmetries (method-type mismatch, protocol mismatch, re-implementation drift, hyperparameter advantage, hardware mismatch) are also moot under v3 since there is no classification axis to be unfair on.

#### Tier 5 architecture — pluggable IsoBackend (retained)

Adopted from co-author proposal 2026-06-07; v3 keeps the abstraction but drops the `kernel_features` method (classification axis is gone):

```python
# src/isalhg/iso_backends/base.py
class IsoBackend(ABC):
    """Canonical interface for every exact iso-decision / canonical-form method.

    Removed in v3: kernel_features() — Tier 5 no longer runs SVC(kernel='precomputed').
    """

    @abstractmethod
    def fingerprint(self, H: SparseHypergraph) -> bytes:
        """Canonical byte string. Two H produce equal bytes iff H1 ≅ H2."""

    @abstractmethod
    def are_isomorphic(self, H1: SparseHypergraph, H2: SparseHypergraph) -> bool:
        ...

# concrete (exact) implementations — the entire competitor set
class IsalHGBackend(IsoBackend): ...
class PynautyLeviBackend(IsoBackend): ...
class TracesLeviBackend(IsoBackend): ...
class BlissLeviBackend(IsoBackend): ...

# v2 sketched HWLSubtreeBackend / GraphKWLBackend as reference panels;
# both removed under decision I43 (2026-06-08) — approximate methods are cited
# in related work, not implemented.
```

Two evaluation axes share the same backend interface:

- **Axis 1 (Tiers 1–3, iso-decision and runtime).** Calls `are_isomorphic` and `fingerprint`. Metric: FP rate, FN rate, wall-clock, max_rss. FP and FN rates are required to be 0 for all four exact methods (triangulation).
- **Axis 2 (Tier 5, real-world deduplication atlas).** Same calls. Metric: total wall-clock per dataset, equivalence-partition agreement across the four methods, fingerprint-byte-length distribution.

Same backend code, two metric panels — both measure the same thing (exact iso vs runtime), aligned with the PI directive.

#### Hypergraph types we must encode

HIC's Algorithm 2 (and Zhang's k-HNN, for that matter) consume vertex- and hyperedge-labelled undirected hypergraphs with no multi-hyperedges. The Tier-5 dedup task **also needs labels** because real-world hypergraphs in IMDB / Steam / Twitter carry semantic vertex / hyperedge labels, and stripping them would collapse semantically distinct hypergraphs (e.g. two movies with the same cast structure but different genres).

| Dataset class | Structure | IsalHG v1 scope | Action |
|---|---|---|---|
| RHG-* (synthetic) | Unlabeled; only structure | Labelled (label = ⊥) | Runs with trivial labels |
| IMDB-* | Vertex labels (actor / writer IDs), hyperedge labels (movie metadata) | Labelled ✓ | Runs natively |
| Steam-Player, Twitter-Friend | Vertex / hyperedge labels | Labelled ✓ | Runs natively |

Decision-log B8 + B9 (revised 2026-06-07, retained in v3): vertex and edge labels in v1. Alphabet recipe:

| New token | Replaces | Semantics |
|---|---|---|
| `V^{ℓ_e}_{i,j}[ℓ_{n_1} ... ℓ_{n_j}]` | `V_{i,j}` | Insert hyperedge labelled `ℓ_e` connecting `i` existing + `j` new nodes; the `j` new nodes get labels `ℓ_{n_1} ... ℓ_{n_j}`. |
| `C^{ℓ_e}_i` | `C_i` | Insert labelled hyperedge connecting `i` existing nodes. |
| `P_i`, `N_i`, `W` | (unchanged) | Pointer moves stay single-token. |

Alphabet size grows from `O(k²)` to `O(k² · |Σ_v|^k · |Σ_e|)`. Tie-breaking cascade gains: minimise hyperedge-label index, then lex-minimise new-node-label tuple. Structural tuples `ξ, η` become label-aware — count labelled neighbours at distance `h` per `(label, distance)` pair. Theorem 2 proof port now tracks label-preserving isomorphisms (IsalSR Theorem 3.15 recipe).

#### Label vocabulary policy (decision I45, 2026-06-11)

The seed proposal (`docs/isalhg_idea.pdf`) and IsalSR ship with closed semantic alphabets — `{+, −, ×, ÷, sin, …}` in IsalSR's case. IsalHG cannot inherit that closure: the Tier-5 corpora carry domain-specific labels (IMDB actor IDs, Steam game tags, Twitter handles) that are dataset-scoped and not enumerable a priori. The labelling must therefore be *fitted per dataset*, but the fitting must stay deterministic and faithful to the colored-graph standard already established for the Levi baselines (nauty / Traces / bliss accept integer vertex colors via `vertex_coloring=[set_0, set_1, …]`; the semantics-to-color map is the caller's responsibility — see decision log H33 and McKay & Piperno 2014 §2).

**Design (mirrors the nauty / bliss colored-graph contract).**

1. **`SparseHypergraph` never sees strings.** Vertex and hyperedge labels are stored as `int` IDs in compact contiguous ranges `[0, |Σ_v|)` and `[0, |Σ_e|)`. The canonical algorithm, the alphabet, and `ξ` / `η` consume integers. The semantic string ("kinase", "tt0133093") is never seen by `core/`.
2. **`LabelVocabulary` fits the dataset once at load time** (`isalhg.datasets.schemas.LabelVocabulary`):
   ```python
   @dataclass(frozen=True)
   class LabelVocabulary:
       vertex_labels: tuple[str, ...]   # index = int id; vertex_labels[i] is the semantic name of int id i
       edge_labels:   tuple[str, ...]

       @classmethod
       def fit(cls, dataset_items: Iterable[RawHypergraph]) -> "LabelVocabulary":
           v = sorted({lbl for H in dataset_items for lbl in H.vertex_labels.values()})
           e = sorted({lbl for H in dataset_items for lbl in H.edge_labels.values()})
           return cls(tuple(v), tuple(e))
   ```
   Sorting is lexicographic — the only deterministic-across-Python-runs canonical choice (`hash()` salts per process; `id()` is non-reproducible). The fitted vocabulary becomes part of `DatasetMetadata` and is persisted next to every cell's result JSON so reruns are reproducible.
3. **Each `HypergraphDataset` yields `SparseHypergraph` instances pre-encoded against its vocabulary.** Stochastic datasets that synthesise labels (RHG-*, trivial-label case `ℓ = ⊥`) declare a single-symbol vocabulary `{"⊥"}` so the canonical algorithm runs identically on unlabelled and labelled inputs (no special-case branch).
4. **Canonical strings are only iso-comparable within the same vocabulary.** Cross-dataset comparison requires reconciling vocabularies — but this is true of nauty too (its canonical permutations are only comparable when the input colorings agree). The orchestrator's partition-agreement assertion (Tier 5 acceptance criterion 1) compares partitions *within* each dataset; no cross-dataset comparison is in scope.
5. **The Levi reduction carries both color classes.** `iso_backends.levi_reduction` emits a 3-class colouring on `B(H)`: `(v_color = vertex_label_id, e_color = |Σ_v| + edge_label_id + sentinel_offset)`. The sentinel offset guarantees vertex-color and edge-color ranges are disjoint, so the Levi engine cannot map a vertex-witness to an edge-witness. This is the standard "lift colours from H to B(H)" trick used by SageMath's `IncidenceStructure.is_isomorphic` and GAP+FinInG; we reproduce it explicitly so all four backends consume an equivalent colored-graph instance.

**Faithfulness to the Isal framework.** The two-tier alphabet in the table above is unchanged. The new `LabelVocabulary` lives in the *dataset* layer, not in `core/`, so the VM and the canonical algorithm remain dataset-agnostic — exactly the IsalSR pattern where the alphabet was finite + closed and the VM was operator-agnostic. The dataset acts as the IsalSR-equivalent "operator catalog": it tells the VM how many vertex/edge labels exist and which integer maps to which semantic name. The PI's framing of "labels need not be enumerable" (note 2026-06-08, unbounded-label section above) is *also* satisfied: when `|Σ_v|` or `|Σ_e|` grows beyond practical token counts, the dataset loader switches to the parameterised-instruction regular-language form (decision I40), and the same `LabelVocabulary` carries the integer-id mapping over decimal encodings.

**What this rules out.**
- Hash-based label assignment (`hash(lbl) % N`): non-deterministic across Python runs (PYTHONHASHSEED), breaks reproducibility.
- WL-style iterative label *replacement* (Shervashidze et al. 2011, *JMLR* 12): solves a different problem (kernel embedding), not canonicalisation; replacing semantic labels with neighborhood hashes discards the iso-preserving constraint and is wrong for our use case.
- Per-instance vocabularies. Vocabularies are dataset-scoped, not per-hypergraph; otherwise two iso instances in the same dataset could see different integer encodings of the same semantic label and disagree on canonical form.

#### Alphabet design for unbounded label spaces (E. López-Rubio note, 2026-06-08)

The finite-token expansion above suffices when `|Σ_v|, |Σ_e|` are bounded — the case for all 12 Tier-5 datasets. PI's reply 2026-06-08 anticipates the v2 case where the label space is countably infinite (e.g. arbitrary integer IDs, open-ended categorical schemas):

> "Si puede haber infinitas etiquetas distintas, ya no se puede meter en el alfabeto una instrucción para cada operación y etiqueta, porque el alfabeto sería infinito, lo cual no está permitido matemáticamente. Pero no es problema, porque el lenguaje seguirá siendo regular. Por ejemplo, si tengo una instrucción `I <n>` donde `<n>` es un número entero arbitrariamente grande expresado en decimal, el lenguaje sigue siendo regular." — E. López-Rubio, 2026-06-08

**Construction (v2 escape hatch, not implemented in v1).** Replace the finite suffix-token block with parameterised instructions over a finite meta-alphabet:

```
V_{i,j}[L_e, L_n_1, ..., L_n_j]    where each L_x ∈ Decimal* (regex [0-9]+)
C_i[L_e]                            same convention
```

The token surface form is `V_{2,1}[42, 7]` etc., with whitespace as the in-token separator. The alphabet `Σ_finite = {V, C, P, N, W, _, {, }, [, ], 0-9, ,}` is finite; the language is regular because the decimal-integer sub-language `[0-9]+` is regular and regular languages are closed under concatenation (Hopcroft–Ullman 2007, §2.2). The S2H interpreter parses the integer suffixes lazily.

**Practical implications.**
- The greedy tie-breaking cascade extends naturally: compare label-suffix integers lex on the decimal representation (or numerically — both define the same total order up to padding convention; we pick numeric for cleanliness).
- Theorem 2 (label-preserving completeness) ports identically; the inductive case treats label equality as an integer-equality predicate, independent of representation.
- Memory cost per token grows from `O(1)` to `O(log L)` where `L` is the maximum label value seen — negligible in practice.

v1 stays with the finite-suffix-token expansion (sufficient for all current target datasets). v2 should adopt the parameterised-instruction form before any extension to corpora with unbounded label cardinality (e.g. PubMed mesh-term hypergraphs, large-vocabulary knowledge hypergraphs).

## Baseline stack (locked, v3 reorganisation)

Reorganised 2026-06-08 under the PI directive: primary baselines are *exact iso-decision* tools only. Approximate WL-track methods move to a reference panel where they are measured for incompleteness, not raced.

### Primary baselines — exact iso-decision (full Tier-2 + Tier-5 columns)

| Tool | Wrapped via | Reference | Role |
|---|---|---|---|
| **pynauty 2.8.8.1** (nauty 2.8.8) | direct | McKay & Piperno 2014, JSC 60:94–112 | Primary IR baseline; correctness oracle for cross-check (E23 / Tier-5 ground truth). |
| **Traces** (pallini suite) | subprocess wrapper to `dreadnaut` | McKay & Piperno 2014, §6 | Dominates nauty on irregular/hard-symmetric (Tier 3). |
| **bliss 0.77** | `python-igraph.Graph.canonical_permutation()` | Junttila & Kaski 2007, ALENEX | Dominant on large sparse graphs. |

All three are exact, all three operate on the Levi incidence graph `B(H)`, all three run on every Tier-2 instance and every Tier-5 dataset. Reported as three separate columns plus IsalHG.

### Approximate methods: cited, not implemented

Decision I43, 2026-06-08. The WL-track approximate methods (HWL, k-WL on `B(H)`, k-GWL) are mentioned in related work and used as the *source of expressiveness counterexamples* (their own published Figure-3-style witnesses), but **none are implemented or run** in this work. The reasoning is twofold:

1. **They are not iso-decision tools.** The WL family is at heart a *feature-extraction* algorithm whose iso-discrimination guarantee is a theoretical scaffolding for the embedding quality. The actual ML papers that propose them (Feng TPAMI 2024 / Zhang ICML 2025) consume the WL features in a downstream classifier, never as a stand-alone iso check. Comparing them to nauty on iso decision is a category error — they were built for a different consumer (a differentiable, polynomial-time-per-iteration MPNN). Six concrete reasons in the design-context box below.
2. **Their incompleteness is already proved by their own authors.** Feng et al. publish Figure 3 — two non-isomorphic hypergraphs HWL collides on. Zhang et al. publish Figure 3(a) and 3(b) — pairs `1-GWL`/`HWL` collapses and pairs `2-GOWL` collapses. We use these as *fixtures* in `tests/unit/test_canonical.py` (Phase-1 deliverable 13). We do not need to re-implement HWL just to re-derive the same FP-rate-on-paper-examples number their figures already publish.

**Design-context box: why do these methods exist at all if pynauty exists?**

| Concern | Why approximate methods exist anyway |
|---|---|
| **Output type** | nauty returns a permutation; ML pipelines need a feature vector. WL/HWL produce a multiset of refined labels — a vector. Even with free nauty, ML still needs a separate featuriser. |
| **Differentiability** | nauty's discrete canonical form blocks backpropagation. WL/HWL's hash-multiset can be relaxed (GIN, Xu et al. ICLR 2019, arXiv:1810.00826) and trained end-to-end. |
| **Worst-case time** | nauty/Traces/bliss are exponential on Miyazaki-class adversarial inputs (McKay-Piperno §11). WL/HWL is `O(h · m · log n)` regardless of input. ML benchmarks accept wrong-but-polynomial. |
| **Scale** | Million-graph ML benchmarks (OGB) cannot afford an exponential worst case per example. WL/HWL is the only feasible option. |
| **Community framing** | The MPNN expressiveness literature (Morris AAAI 2019, Xu ICLR 2019) takes `k`-WL as the yardstick. "≥ k-WL" is the lingua franca. nauty is invisible to that frame — it is not an MPNN. |
| **Different consumer** | nauty serves combinatorial-design enumeration; WL/HWL serves trainable graph classifiers. Two literatures, two consumers. The "iso" overlap in abstracts is largely rhetorical. |

The PI directive ("competidores han de resolver el mismo problema") is therefore correct in the precise sense: WL-track methods do not solve the same problem IsalHG solves, so they are cited as context, not raced. The relevant comparison is against exact tools — and those are `pynauty`, `Traces`, `bliss` via the Levi reduction.

### Tier-3 supplementary baselines

| Tool | Wrapped via | Use |
|---|---|---|
| **SageMath `IncidenceStructure.is_isomorphic()`** | subprocess wrapper | Design-theory representation baseline; reviewers in JCD will expect it. |
| **GAP + FinInG `IsIsomorphicIncidenceGeometry`** | subprocess wrapper | Designs-community baseline; supplementary. |

### Theoretical comparators (cited, not run — confirmed by PI sign-off 2026-06-08)

| Tool | Reference |
|---|---|
| Neuen, ACM TALG 2022 | Current best theoretical bound `(n+m)^O((log d)^c)`; never implemented. Per PI sign-off: cited and discussed from the theoretical point of view only. |
| Schweitzer & Wiebking STOC 2019 | HF-set canonicalisation framework; no public implementation. |
| Babai & Codenotti FOCS 2008 | `exp(O(k²√n log n))` for rank-`k`; theoretical. |
| Arvind, Das, Köbler & Toda Algorithmica 2015 | FPT for colored hypergraph iso in the number of colors; theoretical. |
| Babai 2016, Babai 2019 | Quasipolynomial graph-iso (graphs only); via the bipartite reduction. |

### Other graph-iso solvers — not adopted

`saucy3` (no canonical label; iso variance reported in Neuen-Schweitzer 2017 Table 2), `conauto` (iso decision only; unmaintained since ~2013), `nishe` (abandoned, Miyazaki-specialized). Neuen-Schweitzer 2017 benchmarked saucy and conauto alongside nauty/Traces/bliss and showed all five fail on the same shrunken-multipede instances at ~1500 vertices — adding them would not change the qualitative finding. Each receives one citation in related-work.

### Bipartite reduction (canonical reference) — formal exactness argument

The exactness of `Levi + {pynauty, Traces, bliss}` rests on a two-step argument. Each step is exact and the composition is exact.

**Step 1 — Levi incidence graph (Berge 1973).** For a hypergraph `H = (V, E)`:

```
B(H) = (V ⊔ {v_e : e ∈ E},  {{v, v_e} : v ∈ e}),   2-coloured: V has colour 0, {v_e : e ∈ E} has colour 1.
```

**Theorem (Berge 1973, formalised algorithmically by Beigel & Bernasconi STOC 1999).** Two hypergraphs `H_1, H_2` are isomorphic if and only if their Levi graphs `B(H_1), B(H_2)` admit a *colour-preserving* graph isomorphism (vertex-class-`V` maps to vertex-class-`V`; hyperedge-witness-class `{v_e}` maps to hyperedge-witness-class `{v_e}`). Both directions of the equivalence are polynomial-time computable.

References:
- Berge, C. (1973). *Graphs and Hypergraphs*. North-Holland. §17. Foundational source of the Levi incidence construction.
- Beigel, R. & Bernasconi, A. (1999). *Hypergraph Isomorphism and Structural Equivalence of Boolean Functions*. STOC 1999, pp. 217–225. DOI:10.1145/301250.301427. Gives the polynomial-time iso-equivalence statement we cite.

**Step 2 — coloured graph-iso canonical labelling.** Each of nauty, Traces, bliss takes a vertex-coloured graph and returns a *canonical labelling* — a permutation `π_G` such that `π_G(G) = π_{G'}(G')` if and only if `G ≅ G'` as coloured graphs (the canonical form is a function of the iso-class, invariant under input permutation). Only colour-preserving permutations are considered, by construction.

| Engine | Correctness reference | Worst case |
|---|---|---|
| **nauty, Traces** | McKay, B.D. & Piperno, A. (2014). *Practical Graph Isomorphism, II*. J. Symbolic Comput. 60:94–112. arXiv:1301.1493. Theorem 2.10: the IR search-tree labelling is a canonical form, proven in §3–4. Original framework: McKay, B.D. (1981). *Practical Graph Isomorphism*. Congressus Numerantium 30:45–87. | Exponential on Miyazaki-class adversarial constructions (Miyazaki 1997; McKay-Piperno §11). Polynomial with bounded search tree on real-world inputs. |
| **bliss** | Junttila, T. & Kaski, P. (2007). *Engineering an Efficient Canonical Labeling Tool for Large and Sparse Graphs*. ALENEX 2007, pp. 135–149. DOI:10.1137/1.9781611972870.13. §3 derives correctness by reduction to the McKay 1981 IR framework and adds component-tree partitioning + sparse-graph optimisations. | Same worst case as nauty (inherited from the IR framework); typically faster on large sparse inputs. |

**Composition.** Define `IsoCheck_M(H_1, H_2) := (canonical_M(B(H_1)) == canonical_M(B(H_2)))` for `M ∈ {nauty, Traces, bliss}`. By Step 1, hypergraph iso ⟺ colour-preserving Levi iso, in both directions. By Step 2, colour-preserving Levi iso ⟺ equal canonical forms under `M`, in both directions. The composition is exact: every iff is bidirectional, no approximation step is introduced. The only observable failure mode is a *timeout* on a Miyazaki-class adversarial input — but a timeout is reported as `T_M = ∞`, never as a wrong answer.

**Triangulation.** We invoke all three engines (`pynauty`, `Traces`, `bliss`) on every Tier-2 and Tier-5 instance. If any two disagree, the disagreement is a bug somewhere; we do not silently accept the majority answer. This redundancy hardens the ground-truth oracle used for the IsalHG cross-check (E23).

**Vertex-colouring sanity test (decision log H33).** The 2-colouring `(V, {v_e})` must be passed to the engine explicitly via `pynauty.Graph(directed=False, number_of_vertices=n+m, adjacency_dict=adj, vertex_coloring=[set_of_V, set_of_edge_witnesses])`. Forgetting the colouring produces an answer that ignores the bipartition — fast but wrong. A 20-line known-answer test verifies the coloured invocation against a hand-computed canonical form on a 4-vertex 3-hyperedge instance. Gates all Tier-2 + Tier-5 runs.

**Sources cited above (added to the bibliography):**
- Berge, C. (1973). *Graphs and Hypergraphs*. North-Holland. §17.
- McKay, B.D. (1981). *Practical Graph Isomorphism*. Congressus Numerantium 30:45–87.
- Miyazaki, T. (1997). *The complexity of McKay's canonical labeling algorithm*. In *Groups and Computation II*, AMS DIMACS 28:239–256. (The hardness witness construction.)

## Metrics

| Tier | Metric | Reporting |
|---|---|---|
| 1 | Correctness (binary) per instance pair | Pass/fail matrix; hypothesis-shrunk failing case if any. |
| 1 | Bijection certificate validity | Pass/fail per iso pair (E24). |
| 2 | Wall-clock per instance (`T_isalhg`, `T_pynauty`, `T_traces`, `T_bliss`) | Median ± IQR over 10 seeds; log-log plot vs `(n, m, r)`; fitted exponents per algorithm. |
| 2 | Peak memory `max_rss` per instance | Logged from Picasso (H34). Second curve on the scaling plot. |
| 2 | Canonical-string length `|w*_H|` | Distribution; comparison vs `|edges(B(H))|` as a compactness proxy. |
| 2 | FP rate, FN rate vs pynauty | Single number per Tier-2 cell, across all `N × 10` pairs (E23). Triangulated against Traces and bliss. Must be 0 for IsalHG. |
| 3 | Wall-clock; correctness; timeouts | "Hardness atlas" — per-instance table with 95% CI from 10 reruns. |
| 3 | Speedup `T_baseline / T_isalhg` (baseline ∈ {pynauty, Traces, bliss}) | Geometric mean per family; per-family box plot. |
| 5 | Total dedup wall-clock per dataset | Mean ± IQR across 5 reruns; column per baseline (IsalHG, pynauty, Traces, bliss). |
| 5 | Iso-equivalence-partition agreement | Binary agreement matrix between exact methods; must be 100% identical (correctness invariant). |
| 5 | Fingerprint byte length `|fp_M(H)|` distribution | Per-method per-dataset histogram; entropy-relative ratio `|fp| / log_2 |Aut(H)|` (when computable). |
| 5 | Geometric-mean speedup `T_{best Levi} / T_IsalHG` | One number per dataset; ≥ 2× on at least 4 datasets is the headline target. |

## Reproducibility

- **Seeds.** Every random generator call uses `np.random.default_rng(seed)` per instance; the seed and the generator's state hash are stored in instance metadata (H35).
- **Storage.** Instances and timings written under `experiments/<tier>/<run-id>/` as JSONL. SLURM workers on Picasso for Tier 2 + Tier 3 sweeps (generated via the `picasso-sbatch` skill).
- **Versions.** `pyproject.toml` pins `pynauty>=2.8`. The exact resolved versions are dumped via `pip freeze` per run; `dreadnaut --version` and `python-igraph.__version__` logged separately.
- **Statistical tests.** Tier 2 cells with ≥ 30 paired observations report Wilcoxon signed-rank `p` and Cohen's `d` on `log(T_baseline / T_isalhg)`. Tier 3 reports CIs only.
- **Memory.** Picasso jobs log `max_rss` per task via the SLURM accounting interface.

## Phase 1 deliverables (next 8–12 weeks)

1. Port `core/cdll.py` and `core/sparse_hypergraph.py` from IsalGraph's templates (linked in `CLAUDE.md`). The `SparseHypergraph` port ships with a free function `permute(H: SparseHypergraph, sigma: dict[NodeId, NodeId]) -> SparseHypergraph` (decision I44) — vertex-permutation oracle for criterion 2 of Tier 1 and for Hypothesis property tests; ~10 lines, stdlib-only, no external relabel helper.
2. Implement `core/instructions.py` with the **labelled two-tier alphabet** (`V^{ℓ_e}_{i,j}[ℓ_{n_1}...ℓ_{n_j}]`, `C^{ℓ_e}_i`, `P_i`, `N_i`, `W`), `core/string_to_hypergraph.py`, `core/hypergraph_to_string.py` (greedy with the full tie-breaking cascade from `idea_060626.md` extended with two label-tie-breaking rules: minimise hyperedge-label index, then lex-minimise new-node-label tuple). All label inputs are `int` IDs in `[0, |Σ|)`; the semantic-string layer lives in `datasets.schemas.LabelVocabulary` (decision I45) and never reaches `core/`.
3. Implement `core/structural_tuples.py` with **label-aware** `ξ` and `η` (count labelled neighbours at distance `h` per label class) and `core/canonical.py`.
4. Implement `core/canonical_pruned.py` with the backtracking procedure (Theorem 3 algorithm).
5. **Bijection certificate extractor** in `core/canonical.py` (E24).
6. Hypothesis property tests for `S2H ∘ H2S = id`, canonical invariance, and certificate correctness over `n ≤ 10` random hypergraphs.
7. `adapters/xgi_adapter.py` (highest priority — XGI is the source of truth for all synthetic generators). The adapter consumes a `LabelVocabulary` (decision I45) and emits `SparseHypergraph` instances with integer-encoded labels; the semantic-string XGI attributes are stored on the side in `DatasetMetadata` and never passed into `core/`.
7b. `datasets/schemas.py` — `LabelVocabulary` dataclass with `LabelVocabulary.fit(items)` (lexicographic sort → int IDs); `DatasetMetadata.vocabulary: LabelVocabulary` field. Tier 5 datasets (HIC's 12) fit one vocabulary per dataset at load time; Tier 1 / Tier 2 / Tier 3 unlabelled instances declare a trivial `LabelVocabulary(("⊥",), ("⊥",))` so the canonical algorithm runs identically on unlabelled and labelled inputs (no special-case branch in `core/`).
8. `experiments/baselines/pynauty_bipartite.py` (~80 lines) + arity-coloring sanity test (H33).
9. `experiments/baselines/traces_runner.py` (subprocess wrapper).
10. `experiments/baselines/bliss_runner.py` (python-igraph).
11. ~~`experiments/baselines/kwl_baseline.py`~~ — *removed 2026-06-08*. k-WL is cited but not implemented under decision I43; see §"Approximate methods: cited, not implemented".
12. ~~`experiments/baselines/hwl.py`~~ — *removed 2026-06-08*. HWL is cited via Feng et al. Figure 3 directly; no re-implementation needed.
13. **Expressiveness fixtures** in `tests/unit/test_canonical.py` — three hand-coded non-isomorphic hypergraph pairs from competitors' own papers: (a) Feng et al. TPAMI 2024 Figure 3 (HWL fails by their own published counterexample); (b) Zhang et al. ICML 2025 Figure 3(a) (1-GWL/HWL fails, 2-GOWL succeeds — Zhang's own example); (c) Zhang et al. ICML 2025 Figure 3(b) (2-GOWL fails, 2-GFWL succeeds — Zhang's own example). IsalHG must distinguish all three — gates Tier-1 acceptance. **We do NOT need to run HWL / k-GWL ourselves to use these fixtures; the original papers prove the collisions analytically.**
14. **PG(2, 9) pynauty timing reality check** (D18) — runs before strategy is locked for Tier 3.
15. **Tier 1 run** end-to-end: the first publishable artifact (correctness on Fano + STS(9) + STS(13) + GQ(2,2) + small random + HWL/k-GWL failure fixtures).
16. `experiments/tier5/dedup_atlas.py` — Tier-5 driver under v3: load HIC's 12 datasets, compute canonical fingerprints with each baseline (IsalHG, pynauty, Traces, bliss), build iso-equivalence partition per method, assert partition agreement, report total wall-clock + memory + fingerprint-length distribution + per-dataset geometric-mean speedup over best-of-Levi.
17. ~~`experiments/tier5/approximate_panel.py`~~ — *removed 2026-06-08*. The HWL FP-rate-on-real-data measurement is dropped along with the HWL re-implementation. Incompleteness evidence comes from Feng / Zhang's own counterexamples (deliverable 13).

Defer to Phase 2: Theorems 1–3 (paper sections), Tier 2 sweep on Picasso, Tier 3 hard-case generators (SageMath / GAP subprocess wrappers), full Tier-5 sweep with statistical re-reruns + bootstrap CIs.

## Open research questions (still active)

These shape the validation experiments and remain unresolved:

1. **Structural-tuple depth.** Default 3 (from IsalGraph). Tier 3 will tell us whether depth-3 distinguishes the large-Aut Steiner systems and non-Desarguesian PG(2,9). If not, depth ≥ 4 is required — and Theorem 2's induction has to be redone.
2. **Value of `k`.** Capped at 10 (decision log B12); the question of whether to make `k` input-dependent inside that cap is open.
3. **Disconnected hypergraphs.** Deferred for v1 (B11). Documented as a known limitation; per-component encoding + lex-min merge is the obvious extension.
4. **Hypergraph-CFI construction.** Companion paper (decision log C14). If IsalHG fails on HG-CFI, Theorem 2 is false.

## Publication strategy

**Two-paper split confirmed (decision log F27; venue list narrowed 2026-06-08 under PI directive).**

| Paper | Content | Target venue |
|---|---|---|
| **(a) Empirical** | Algorithm + Tier 1 + Tier 2 + Tier 3 + Tier 4 calibration + **Tier 5 exact iso-equivalence-class atlas** on HIC's 12 datasets. Completeness conjectured + empirically verified on all `N` tested instances (F28 framing). FP/FN rates vs pynauty as the empirical-completeness story. Tier-5 dedup-speedup as the real-world headline. | ACM Journal of Experimental Algorithmics (JEA) or ALENEX. Alt: Journal of Combinatorial Designs (with Tier 3 reframed as headline). |
| **(b) Theoretical** | Theorems 1, 2, 3 (expressiveness, completeness, backtracking bound). | Journal of Symbolic Computation (primary) or SIAM J. Discrete Mathematics. |
| **(c) Companion (optional)** | Hypergraph-CFI construction + its consequences for canonical-labeling completeness. Separable if discovered. | LICS, ICALP, or Combinatorica depending on depth. |

**Explicitly off-table per PI directive 2026-06-08:** ICML / ICLR / IEEE TPAMI / NeurIPS. The PI's reply states *"tal como veo el enfoque del artículo (un algoritmo exacto para comprobar el isomorfismo de hipergrafos), no lo veo muy utilizable para pedir un proyecto de investigación. Es demasiado teórico."* — the same theoretical framing makes ML-conference venues a poor fit. The v2 "future TPAMI extension" line is removed.

**Minimum publishable for (a)** if Theorem 2 doesn't close: "IsalHG: a sound and empirically-complete native canonical encoding for hypergraphs (completeness conjectured, verified on all N tested instances, geometric-mean speedup ≥ 2× on at least 4 of 12 real-world datasets)". Decision log F28 confirms this framing is acceptable.

## Future work (mentioned, not committed in v1)

- **Subhypergraph isomorphism** (G31). Different problem; useful in chemistry. One-paragraph future-work mention positions IsalHG for a downstream paper.
- **|Aut(H)| atlas on real-world hypergraphs** (G32). Run IsalHG on ARB + XGI-DATA and report the automorphism-group-size distribution across domains. Cheap once IsalHG is implemented; possibly publishable in a network-science venue (e.g., *Journal of Complex Networks*).
- **Vertex- and edge-labeled hypergraphs** (B8, B9). Two-tier alphabet à la IsalSR.
- **Directed hypergraphs** (B7).

## What this strategy does *not* commit to

- Real-world biomedical applications (protein-protein, chemical-reaction networks). Out of scope per the PI's clarification. Note: Tier 5's HIC datasets are **not biomedical** — they are synthetic (RHG-*), movie metadata (IMDB-*), gaming (Steam-Player), and social (Twitter-Friend). Tier 5 is therefore consistent with the PI's framing.
- Worst-case complexity bound on IsalHG. Stretch goal; empirical-only by decision (C17).
- Theorem 2 in the empirical paper (a). Deferred to paper (b) under the two-paper split.

## Decisions resolved 2026-06-06 (co-author review log)

35 items raised in the co-author review; resolutions below. Items prefixed with the section letter from the original raise.

| # | Topic | Resolution |
|---|---|---|
| A1 | Traces as separate baseline | YES include — Tier 2 + Tier 3 column. |
| A2 | bliss as full Tier-2 column | YES include — promoted from secondary. |
| A3 | SageMath `IncidenceStructure.is_isomorphic` | YES include — Tier 3 supplementary. |
| A4 | HIC / HWL comparator | **REVISED 2026-06-06**: re-implement HWL; promote to primary Tier-2 baseline. **REVERSED 2026-06-08 by I43**: HWL is cited only via Feng Fig. 3 counterexample; no implementation. Gap-statement correction (HIC is native, not bipartite-expansion) is retained. |
| A5 | k-WL baseline (k=1,2,3) | YES include. **REVERSED 2026-06-08 by I43**: k-WL is cited as theoretical background only; no implementation. |
| A6 | GAP + FinInG | YES include — Tier 3 supplementary. |
| B7 | Directed hypergraphs | NO drop — v1 undirected only. |
| B8 | Vertex labels | **REVISED 2026-06-07 — YES include.** Required for Tier 5 to compete with HIC on its 8 labelled datasets. Two-tier alphabet à la IsalSR. |
| B9 | Edge labels | **REVISED 2026-06-07 — YES include.** Hyperedge label suffix on `V` and `C` tokens. Edge weights remain out. |
| B10 | Multi-hyperedges | NO drop — confirmed not supported. |
| B11 | Disconnected hypergraphs | DEFER — connected only in v1; documented limitation. |
| B12 | Hard cap on `k` | `k ≤ 10`. |
| C13 | Expressiveness vs WL | YES include — Theorem 1. |
| C14 | Hypergraph-CFI construction | DEFER — companion paper. |
| C15 | Completeness proof port | YES include — Theorem 2. |
| C16 | Backtracking termination + bound | YES include — Theorem 3. |
| C17 | Complexity claim | Empirical only — Tier 2 fitted exponents. |
| D18 | PG(2,9) timing reality check | YES include — runs in Phase 1 before Tier-3 lock. |
| D19 | STS hardness scope | Narrowed to explicitly large-Aut instances only. |
| D20 | Latin squares (non-group) | YES include — invest in finding non-trivial-autotopy non-group instances. |
| D21 | Random regular HG at threshold | YES include — fifth Tier-3 family. |
| D22 | (alias of C14) | — |
| E23 | FP/FN cross-check vs pynauty | YES include — per Tier-2 instance pair. |
| E24 | Bijection certificate extractor | YES include — implemented in Phase 1. |
| E25 | Tier-3 statistical reporting | Hardness atlas — case-by-case CI from 10 reruns. |
| E26 | Timeout | 600 s — match IsalGraph + IsalSR convention. |
| F27 | Two-paper split | YES split — empirical first, theoretical follow-up. |
| F28 | Minimum-publishable framing | YES — "empirically complete, completeness conjectured" acceptable if Thm 2 fails. |
| F29 | (alias of C14) | — |
| G30 | Real-world calibration | YES include — Tier 4 in the paper. |
| G31 | Subhypergraph iso future-work | YES include — one paragraph. |
| G32 | |Aut| distribution side-paper | YES include — Phase 2 follow-up. |
| H33 | pynauty arity-coloring sanity test | YES include — gates Tier-2 runs. |
| H34 | Peak memory `max_rss` reporting | YES include — second curve on scaling plot. |
| H35 | RNG determinism | Committed by default — `np.random.default_rng(seed)` per instance; seed + state hash in metadata. |

### v3 decisions added 2026-06-08 (PI directive)

| # | Topic | Resolution |
|---|---|---|
| I36 | Position IsalHG as exact-only iso method | YES — confirmed by PI. v2's two-axes (iso + classification) frame retired. |
| I37 | Reclassify HWL and k-GWL | Demote from primary baseline columns to *reference panel*. Run only to measure their FP rate vs pynauty ground truth. No head-to-head runtime claim. |
| I38 | Tier 5 redesign | Drop kernel + neural classification. Replace with exact iso-equivalence-class atlas on the same 12 datasets. Headline metric = geometric-mean speedup over best-of-Levi. |
| I39 | Retire IMDB-Dir-Form pilot of Zhang Table 1 | Canceled. Zhang's classification numbers are no longer a reproduction target since the classification axis itself is removed. The `experiments/pilot/` directory mkdir-ed 2026-06-07 stays empty / removed. |
| I40 | Alphabet extension for unbounded labels | v1 stays with finite-suffix-token expansion. v2 escape hatch documented per PI (decimal-encoded parameterised instruction, regular language). |
| I41 | Venue list narrowed | Drop ICML / ICLR / TPAMI / NeurIPS targets. Keep JEA / ALENEX / JCD for empirical; JSC / SIDMA for theoretical. |
| I42 | IsoBackend abstraction kept | Retain `IsoBackend` ABC but drop `kernel_features()` method. The abstraction now spans only `fingerprint` + `are_isomorphic`. |
| I43 | Approximate methods: cited, not implemented | HWL, k-WL on `B(H)`, k-GWL are removed from Phase 1 deliverables (items 11 and 12 struck out). Incompleteness evidence comes from the original papers' own Figure-3-style counterexamples, used as fixtures in `tests/unit/test_canonical.py` (deliverable 13). Rationale: these methods solve a different problem (differentiable feature extraction for MPNNs), not exact iso decision; racing them on runtime is uninformative. Detailed reasoning in §"Approximate methods: cited, not implemented". |
| I44 | Isomorphism-pair generation policy (2026-06-11) | Positive pairs via `core.permute(H, σ)` — stdlib-only free function on `SparseHypergraph`, ~10 lines, no `xgi.relabel_nodes` / `HyperNetX.translate` dependency in `core/`. The pinned `σ` is the bijection-certificate oracle (E24). Hard negatives sourced as (1) published design-theoretic non-iso pairs with classified iso classes (two STS(13) from Kaski & Östergård 2004; STS(15), GQ(2,2) variants) embedded as Tier-1 fixtures, (2) pynauty-certified random pairs (Tier 2 / Tier 3 only), and (3) HG-CFI when C14 produces a construction (currently empty source — documented gap, not silently substituted). Random-vertex-permutation libraries (`xgi`, `nx` on Levi) are noted in related work only. Detailed reasoning in §"Tier 1 — Isomorphism-pair generation policy". |
| I45 | Label vocabulary policy (2026-06-11) | Vertex and edge labels are fitted *per dataset* at load time by `LabelVocabulary.fit(dataset_items)` (sorted lexicographically → contiguous `int` IDs in `[0, \|Σ\|)`). `SparseHypergraph` carries only int IDs; `core/` never sees semantic strings — mirrors nauty / Traces / bliss colored-graph convention. `LabelVocabulary` is part of `DatasetMetadata` and is persisted next to every cell's result JSON. The Levi reduction emits a 3-class colouring with disjoint vertex- vs edge-color ranges. Trivial-label datasets declare `LabelVocabulary(("⊥",), ("⊥",))` so the canonical algorithm runs unchanged on unlabelled inputs. Hash-based assignment, WL-style label rewriting, and per-instance vocabularies are explicitly ruled out. Detailed reasoning in §"Label vocabulary policy". |
| I46 | Token serialisation grammar (2026-06-11, Phase 1) | Each token serialises to a self-delimiting bracketed form: `V[ℓ_e;i;j;ℓ_{n_1},ℓ_{n_2},...,ℓ_{n_j}]`, `C[ℓ_e;i]`, `P[i]`, `N[i]`, `W`. Sequences join tokens with `;` at the top level; the parser is bracket-nesting-aware so the internal `;` separators inside `V[...]` and `C[...]` are not confused with the top-level separator. Lex-comparison of canonical strings runs over **token tuples** (numeric ordering on fields), not over the serialised string — this avoids the `"V[ℓ;10;...]" < "V[ℓ;2;...]"` pitfall under Python str comparison. Implemented in `src/isalhg/core/instructions.py`. |
| I47 | Levi colouring scheme (2026-06-11, Phase 2) | Vertex side carries colour `c_v = ℓ_v` (range `[0, \|Σ_v\|)`); edge side carries colour `c_e = \|Σ_v\| + ℓ_e` (range `[\|Σ_v\|, \|Σ_v\| + \|Σ_e\|)`). Ranges are disjoint by construction, so any graph-iso engine (nauty, Traces, bliss) preserves the vertex/edge distinction without needing a special-case "partition" parameter. Empty-vocabulary collapse: trivial label data yields exactly two colour classes (`{0}` and `{\|Σ_v\|}` = `{1}`). Implemented in `src/isalhg/iso_backends/levi_reduction.py::to_levi`; consumed by `pynauty_levi.py` via `vertex_coloring=levi.color_classes()`. |
| I48 | Iso-equivariance via bounded backtracking in greedy H2S (2026-06-11, Phase 1) | The pure greedy with input-id tie-break on new-input ordering is *not* iso-equivariant for vertex-transitive hypergraphs (Fano, STS(9)) because the "shared with future edges" vertex may be inserted first or last depending on its raw input id. Resolved by branching over label-respecting permutations of new-input vertices inside each `V` emission and taking the lex-min completion. Branching factor per `V` step: `(j!)` (trivially small for `j ≤ 3` in Phase 1 fixtures); displacement and edge selection remain pure greedy. This is local to `core/hypergraph_to_string.py::_encode_from` and does NOT introduce a separate `canonical_pruned.py` (the PI-deferred pruned backtracking for displacement+edge ties remains an open question). Validated by the partition-agreement table in `docs/DEVELOPMENT.md` Phase-2 entry: IsalHG and pynauty agree on every Phase 1 fixture. |
| I49 | LLM4Hypergraph three-way comparison adopted as Tier 1c sub-cohort (2026-06-16) | Vendor `github.com/iMoonLab/LLM4Hypergraph` (Apache 2.0) under `third_party/llm4hypergraph/`; substitute `PynautyLeviBackend.are_isomorphic()` for the missing `test_isomo.HGSCKernel` oracle (the file is absent from the public release, so the generator crashes as shipped — substituting pynauty is the only way to *correctly* reproduce their benchmark). Define `LLM4HypergraphIsoRecognition` under `src/isalhg/datasets/llm4hypergraph.py`. Headline: three-way (LLM verdict from Feng et al. ICLR 2025 supplementary, nauty ground truth, IsalHG verdict) on the only published hypergraph iso-recognition corpus in the field. This is the cheapest source of external validity outside the combinatorics tradition. Full reasoning and per-dataset narrative in `docs/DATA.md` §2.6. |
| I50 | Kaski-Östergård plaintext STS catalog adopted as Tier 1 published-iso-class source (2026-06-16) | Replace the cyclic-construction `sts_13_pair` (Z/13Z with starter blocks `{0,1,4}` and `{0,1,6}`, non-iso verified empirically) with the canonical published source: download `sts{3,7,9,13,15}.txt` from `https://pottonen.kapsi.fi/sts19/`, parse the `{a..o}` 3-character triple format in pure Python, ship as `KaskiOstergardSTSDataset` under `src/isalhg/datasets/catalog/kaski_ostergard.py`. Adds 80 STS(15) classes (Mathon-Phelps-Rosa 1983 classification, 80 non-iso) on top of the 2 STS(13) classes — total 85 published iso classes with nauty-certified provenance. STS(19) `1k_sample` (1000 non-iso classes, custom compressed binary requiring the `stsc` C decompressor) deferred to Tier 3 — fingerprint cost on a single STS(19) under current bounded-backtracking IsalHG is already several seconds (open question #1). Citation: Kaski, Östergård, Pottonen & Kiviluoto 2009 *Bull. Inst. Comb. Appl.* 57:35-41 + Kaski-Östergård 2004 *Math. Comp.* 73:2075-2092. Full per-cohort narrative in `docs/DATA.md` §2.1. |

## Related-work census (compiled 2026-06-07)

A focused census across arXiv, ACM DL, IEEE Xplore, Semantic Scholar, and DBLP. Used as the related-work scaffold for both papers in the two-paper plan. Full per-entry summaries with DOIs and competitor-assessment verdicts are in the source agent report; we reproduce the taxonomy and verdicts here.

**Axis A — Native canonical-string encoding of hypergraphs.** Zero direct competitors. Closest analog: Grzelak & Aßmann 2021 (Milner's bigraphs, different object class). IsalHG occupies an unoccupied niche.

**Axis B — Hypergraph isomorphism testing methods.** ~10–12 substantive entries across four families:

| Family | Representative work(s) | Output | Direct competitor to IsalHG? |
|---|---|---|---|
| **B.1 Levi-graph reduction → graph-iso solver** | McKay & Piperno 2014 (nauty/Traces); Junttila & Kaski 2007 (bliss); SageMath `IncidenceStructure`; GAP+FinInG | Permutation / canonical labelling | Practical baseline — runtime competitor (Tier 2, 3). |
| **B.2 Lossy reduction via line / clique graph** | Bai, Ren & Hancock, *A Hypergraph Kernel from Isomorphism Tests*, **ICPR 2014** (DOI:10.1109/ICPR.2014.667). **Note: previously misattributed to CVPR in some lit-search outputs; corrected here.** | Kernel value | No (lossy; many-to-one). HIC's own baseline. |
| **B.3 Native WL-based test / kernel** | Feng et al. TPAMI 2024 (HIC / HWL); Zhang et al. ICML 2025 (k-GWL hierarchy on hypergraphs) | Multiset hash / kernel value | **No** — approximate by their own theorems (Feng Fig. 3; Zhang Thm 5.2/5.3). Cited only as expressiveness-counterexample sources for Tier-1 fixtures (decision I43) and as theoretical backing for Theorem 1 expressiveness claim. |
| **B.4 Group-theoretic / quasipolynomial** | Schweitzer & Wiebking, STOC 2019, *A unifying method for the design of algorithms canonizing combinatorial objects* (arXiv:1806.07466); Neuen, ACM TALG 18(3):21, 2022, DOI:10.1145/3527667 (current best `(n+m)^O((log d)^c)` bound); Arvind, Das, Köbler & Toda, *Colored Hypergraph Isomorphism is FPT*, Algorithmica 71(1), 2015, DOI:10.1007/s00453-013-9787-y; Babai & Codenotti, FOCS 2008 (`exp(O(k² √n log n))` for rank-`k`); Babai 2016 STOC, Babai 2019 STOC (graphs only); Luks JCSS 1982; Babai & Luks STOC 1983 | Permutation / canonical labelling (no string) | Theoretical comparators (cited only; none implemented). |

**Axis C — Survey or comparison papers specifically on hypergraph isomorphism.** Zero such papers exist as of 2026-06-07. The closest reference is Kaski & Östergård's 2006 monograph *Classification Algorithms for Codes and Designs* (Springer), which covers design-specific isomorph rejection via nauty but is not a benchmark paper. **This makes our Tier-2 + Tier-3 empirical study one of the first systematic experimental comparisons of hypergraph-iso algorithms, increasing the paper's standalone contribution.**

## References

Inline citations above. Full bibliography lives in `docs/refs.bib` (to be created). Highest-priority entries:

- Babai, L. (2016). *Graph Isomorphism in Quasipolynomial Time.* STOC 2016. arXiv:1512.03547.
- Babai, L. (2019). *Canonical Form for Graphs in Quasipolynomial Time.* STOC 2019. DOI:10.1145/3313276.3316356.
- Neuen, D. (2022). *Hypergraph Isomorphism for Groups with Restricted Composition Factors.* ACM TALG 18(3), Article 21. DOI:10.1145/3527667. arXiv:2002.06997. **(Corrected attribution — single author Neuen, not Arvind et al.)**
- Schweitzer, P. & Wiebking, D. (2019). *A unifying method for the design of algorithms canonizing combinatorial objects.* STOC 2019, pp. 1247–1258. arXiv:1806.07466.
- Arvind, V., Das, B., Köbler, J. & Toda, S. (2015). *Colored Hypergraph Isomorphism is Fixed Parameter Tractable.* Algorithmica 71(1):120–138. DOI:10.1007/s00453-013-9787-y.
- Babai, L. & Codenotti, P. (2008). *Isomorphism of Hypergraphs of Low Rank in Moderately Exponential Time.* FOCS 2008. DOI:10.1109/FOCS.2008.80.
- Zhang, D., Zhang, C., Rao, Y., Li, Q., Zhu, C. (2025). *Improved Expressivity of Hypergraph Neural Networks through High-Dimensional Generalized Weisfeiler-Leman Algorithms.* ICML 2025. PMLR v267. OpenReview pD5oklKrDV. Code: github.com/talence-zcq/KGWL. **Theorems cited: 5.1 (k-GWL degenerates to k-WL on graphs), 5.2 (`(k+1)-GOWL ≻ k-GOWL`), 5.3 (`(k+1)-GFWL ≻ k-GFWL`), 5.4 (`(k+1)-GOWL ≅ k-GFWL`). Datasets: 6 of HIC's 12. Their named open problem — "computationally efficient methods with provably high expressivity for large k" — is what IsalHG bypasses by avoiding the WL hierarchy entirely.**
- Grzelak, D. & Aßmann, U. (2021). *A Canonical String Encoding for Pure Bigraphs.* SN Computer Science 2:246. DOI:10.1007/s42979-021-00552-5. **(Closest structural analog on Axis A; different object class.)**
- Bai, L., Ren, P. & Hancock, E.R. (2014). *A Hypergraph Kernel from Isomorphism Tests.* ICPR 2014 (NOT CVPR). DOI:10.1109/ICPR.2014.667.
- Luks, E.M. (1982). *Isomorphism of graphs of bounded valence can be tested in polynomial time.* JCSS 25(1):42–65. DOI:10.1016/0022-0000(82)90009-5.
- Babai, L. & Luks, E.M. (1983). *Canonical labeling of graphs.* STOC 1983. DOI:10.1145/800061.808746.
- McKay, B.D., Piperno, A. (2014). *Practical Graph Isomorphism, II.* J. Symbolic Computation 60:94–112. arXiv:1301.1493.
- Junttila, T., Kaski, P. (2007). *Engineering an Efficient Canonical Labeling Tool for Large and Sparse Graphs.* ALENEX 2007. DOI:10.1137/1.9781611972870.13.
- Feng, Y., Han, J., Ying, S., Gao, Y. (2024). *Hypergraph Isomorphism Computation.* IEEE TPAMI 46(5):3880–3893. arXiv:2307.14394.
- Chodrow, P.S. (2020). *Configuration Models of Random Hypergraphs and their Applications.* J. Complex Networks 8(3):cnaa018. arXiv:1902.09302.
- Heinlein, D. (2023). *Enumerating Steiner Triple Systems.* J. Combinatorial Designs 31(7):449–475. arXiv:2303.01207.
- Landry, N.W. et al. (2023). *XGI: A Python package for higher-order interaction networks.* JOSS 8(85):5162.
- Cai, J.-Y., Fürer, M., Immerman, N. (1992). *An Optimal Lower Bound on the Number of Variables for Graph Identification.* Combinatorica 12(4):389–410.
- Kiefer, S., Schweitzer, P., Selman, E. (2015). *Graphs Identified by Logics with Counting.* LICS 2015. DOI:10.1109/LICS.2015.49.
- Neuen, D., Schweitzer, P. (2017). *Benchmark Graphs for Practical Graph Isomorphism.* ESA 2017. arXiv:1705.03686. **(Corrected attribution: previously misattributed to Bläsius/Friedrich/Schirneck in v1–v3 drafts; verified via direct read of the arXiv preprint, 2026-06-08. Introduces shrunken multipedes as the hardest known IR-resistant family; benchmarks pynauty, Traces, bliss, saucy, conauto and shows all five fail at ~1500 vertices. We adopt the hard-family motivation for Tier 3, not the experimental protocol.)**
- Neuen, D., Schweitzer, P. (2017). *An Exponential Lower Bound for Individualization-Refinement Algorithms for Graph Isomorphism.* arXiv:1705.03283. **(Companion paper to the benchmark above; proves IR algorithms require exponential time on shrunken multipedes. Theoretical backing for "Levi + nauty/Traces/bliss will fail on hard symmetric structure" in Tier 3.)**
- Gurevich, Y., Shelah, S. (1996). *On finite rigid structures.* Journal of Symbolic Logic 61(2):549–562. DOI:10.2307/2275678. **(Mathematical foundation for the rigidity of random graphs used in the multipede construction.)**
- Beigel, R., Bernasconi, A. (1999). *Hypergraph Isomorphism and Structural Equivalence of Boolean Functions.* STOC 1999. DOI:10.1145/301250.301427.
- Payne, S.E., Thas, J.A. (2009). *Finite Generalized Quadrangles* (2nd ed.). European Mathematical Society. DOI:10.4171/066.
- Berge, C. (1973). *Graphs and Hypergraphs*. North-Holland. **(Foundational source for the Levi incidence graph used in Step 1 of the exactness argument.)**
- McKay, B.D. (1981). *Practical Graph Isomorphism*. Congressus Numerantium 30:45–87. **(Original individualisation-refinement framework underlying nauty, Traces, and bliss.)**
- Miyazaki, T. (1997). *The complexity of McKay's canonical labeling algorithm*. In *Groups and Computation II*, AMS DIMACS 28:239–256. **(The hardness construction that establishes the IR-framework worst case.)**
- Xu, K., Hu, W., Leskovec, J., Jegelka, S. (2019). *How Powerful are Graph Neural Networks?* ICLR 2019. arXiv:1810.00826. **(The GIN paper — sets the "≥ 1-WL" community framing under which Zhang and Feng operate.)**
- Morris, C., Ritzert, M., Fey, M., Hamilton, W.L., Lenssen, J.E., Rattan, G., Grohe, M. (2019). *Weisfeiler and Leman Go Neural: Higher-Order Graph Neural Networks*. AAAI 2019, pp. 4602–4609. arXiv:1810.02244. **(The k-WL-as-MPNN-yardstick paper that the Zhang hierarchy extends to hypergraphs.)**
