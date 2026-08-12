# P-MEDIAN — the medianoid: deep development

*Author: agent-a3a2677d24d0d231b, 2026-08-12. Scope: documentation only.*
*Source authorities: `../README.md §5`, `../vocabulary.md`, `../problems.md §P-MEDIAN`,*
*`../src/idea3.txt`, `../risks.md`, `../competitors.md §3`, `../data.md §4`, `../scope.md`.*
*Never edit the shared files above; all requests for changes are collected in §10.*

---

## 0. Verification status of the two critical claims

The foundation (`../README.md §5`) asserts this idea should lead the paper on two
theoretical claims. Both are verified here before anything else:

| Claim | Status | Where proved |
|---|---|---|
| Medoid is a 2-approximation of the generalized median when `d_I` is a metric | **VERIFIED** — proof is three lines, requires only Corollary A (triangle inequality) | §2 below |
| Hungarian/bipartite GED approximation is an upper bound, not a metric | **VERIFIED** — the approximation violates triangle inequality generically; formal argument and literature anchor | §2.2 below |

Both claims survive. The comparative advantage is genuine and sharp.

---

## 1. Problem statement in the shared vocabulary

### 1.1 Setup

Fix a signature `σ = (P_1,…,P_r)`, all relations symmetric and function-free.
A **knowledge base** `K` is a finite `σ`-structure over active domain `adom(K)`,
read as a set of ground facts `Facts(K) = ⋃_i {P_i(d̄) : d̄ ∈ P_i^K}`.
Under encoding E1 (`vocabulary.md §5`, `encoding.md §1`): vertex set `V = adom(K)`,
vertex label of `d` = composite of all unary predicates true at `d`, hyperedge
`{d_1,…,d_a}` with edge label `i` for each fact `P_i(d_1,…,d_a)` with `a ≥ 2`;
the result is a labelled hypergraph with `k = max_i a_i`.

The **canonical string** is `w*_c(E1(K))`, abbreviated `w*_c(K)`. The induced
distance is

```
d_I(A, B)  =  d_Lev( w*_c(A), w*_c(B) )
```

which is iso-invariant (Theorem A) and a metric on isomorphism classes (Corollary A).

**P-MEDIAN.** Given `K_1,…,K_N`, find `𝔐 ∈ 𝒮` minimising `Σ_i d_I(𝔐, K_i)`,
where `𝒮` is the search space (two distinct cases below).

### 1.2 Two distinct problems — never conflated

**Set medianoid (medoid).** Restrict `𝒮 = {K_1,…,K_N}`. Equivalently:

```
M_k  =  argmin_{K_j ∈ {K_1,…,K_N}}  Σ_i d_I(K_j, K_i)
```

- Cost: `N` canonicalizations (once each), then `N²` Levenshtein comparisons
  to fill the matrix, then `O(N²)` to find the column-sum minimum.
- Output: one of the input KBs — always decodable, always canonical.
- Guarantee: **2-approximation of the generalized median** (§2.1).

**Generalized median.** Restrict `𝒮` = all isomorphism classes of connected
hypergraphs encodable within `Σ_HG(k)`:

```
M*  =  argmin_{𝔐}  Σ_i d_I(𝔐, K_i)
```

Equivalently, find the canonical string `w*_c(M*)` minimising
`Σ_i d_Lev(w*_c(M*), w*_c(K_i))` *over canonical strings*. This is a constrained
median-string problem — NP-hard in general (§3). The medoid `M_k` achieves cost
at most `2 · OPT` where `OPT = Σ_i d_I(M*, K_i)`.

**Do not conflate with the ambient median string.** The unconstrained minimum of
`Σ_i d_Lev(s, w*_c(K_i))` over **all** `s ∈ Σ_HG(k)*` is a different, easier
object: it is a string that may not be any hypergraph's canonical form. Its cost
is a lower bound on the constrained problem's cost. Both are discussed in §3.

---

## 2. The central theoretical claim, verified

### 2.1 The 2-approximation (three-line proof)

**Theorem (standard; Hassin & Rubinstein 2001 [unverified] for the general
`k`-median; the `k=1` case is folklore).** *Let `(𝒮, d)` be a metric space and
`K_1,…,K_N ∈ 𝒮`. Let `M*` denote the optimal 1-median and `M_k` the medoid.
Then `Σ_i d(M_k, K_i) ≤ 2 · Σ_i d(M*, K_i)`.*

**Proof.** Let `OPT = Σ_i d(M*, K_i)`.

(1) **Triangle.** For any `K_j`, by the triangle inequality summed over `i`:
```
Σ_i d(K_j, K_i)  ≤  Σ_i [d(K_j, M*) + d(M*, K_i)]  =  N·d(K_j, M*) + OPT.
```

(2) **Averaging.** Among `K_1,…,K_N`, at least one achieves
`d(K_j, M*) ≤ (1/N)·Σ_i d(K_i, M*) = OPT/N`.
Call it `K_{j*}`.

(3) **Medoid is best input.** Since `M_k = argmin_{K_j} Σ_i d(K_j, K_i)`:
```
Σ_i d(M_k, K_i)  ≤  Σ_i d(K_{j*}, K_i)  ≤  N·(OPT/N) + OPT  =  2·OPT.   QED
```

**What this requires.** The triangle inequality alone — i.e., `d_I` is a metric.
`d_I` satisfies it by Corollary A (triangle inequality is inherited from
`d_Lev`). No other property of `w*_c` is used.

**What this does not require.** `d_I` need not equal `d_SED`. The guarantee is
about whatever metric you compute medoids under; here that is `d_I`.

### 2.2 The Hungarian/bipartite GED approximation is not a metric

The **Riesen–Bunke bipartite approximation** (Riesen & Bunke 2009 [unverified —
check exact title: *Approximate graph edit distance computation by means of
bipartite graph matching*, Image and Vision Computing]) constructs for each pair
`(A, B)` a bipartite cost matrix over node-pairs, solves the linear assignment
problem in `O(n³)`, and reads off an upper bound `d_HB(A, B) ≥ GED(A, B)`.

**It is not a metric.** The triangle inequality fails generically. Formal argument:

The bipartite relaxation assigns each node of `A` independently to a node of `B`
(or to a deletion/insertion slot), ignoring edge compatibility constraints. Two
independent assignments `σ_{AB} : A → B` and `σ_{BC} : B → C` compose to
`σ_{AB} ∘ σ_{BC} : A → C`, and `d_{GED}` satisfies the triangle inequality
because GED paths can be concatenated. But `d_HB` does **not** satisfy it: the
assignment for `(A,C)` chosen by the LA solver may be more expensive than the
composed `σ_{AB} ∘ σ_{BC}` path (the solver optimises independently, finding the
minimum-weight assignment for `(A,C)` which could be worse or better than what
composition gives, depending on the structure). More precisely:

- There exist triples `(A,B,C)` with `d_HB(A,C) > d_HB(A,B) + d_HB(B,C)`.
- Construction sketch: choose `A`, `B`, `C` such that the best bipartite
  assignment for `(A,C)` pays a high cost for intermediate-node relabelling that
  `B` would otherwise absorb cheaply; the per-pair assignments conflict because
  different assignments use `B`'s nodes as "bridges" in incompatible ways.

The literature confirms this: Fischer et al. `[unverified]` and the original
Riesen–Bunke paper itself acknowledge `d_HB` as an *approximation*, not a
distance. Several papers (Serratosa 2014 `[unverified]`) have studied conditions
under which `d_HB` is metric; the conditions are not generically satisfied.

**Consequence for the comparison.** The medoid `M_{k,HB} = argmin_{K_j}
Σ_i d_{HB}(K_j, K_i)` carries no approximation guarantee relative to
`OPT_{HB} = min_𝔐 Σ_i d_{HB}(𝔐, K_i)` (and `OPT_{HB}` is not a well-defined
geometric quantity anyway since `d_HB` is not a metric). Claiming it is a
2-approximation of any true median is unjustified.

**Our medoid `M_k` under `d_I` is a provable 2-approximation of the true
generalized median under `d_I`.** This is a rare case where our proof buys a
concrete, competitor-beating guarantee.

---

## 3. The generalized median as a median-string problem

### 3.1 Formulation

Recall `d_I(A, B) = d_Lev(w*_c(A), w*_c(B))`. Minimising `Σ_i d_I(𝔐, K_i)` over
isomorphism classes is equivalent to minimising `Σ_i d_Lev(w*_c(𝔐), w*_c(K_i))`
over **canonical strings** `{w*_c(𝔐) : 𝔐 connected, encodable in Σ_HG(k)}`.

This is the **constrained median string problem**: given strings
`t_1 = w*_c(K_1),…,t_N = w*_c(K_N)`, find the canonical string `s*` minimising
`Σ_i d_Lev(s*, t_i)`. It is NP-hard (Sim & Park `[unverified — check: "On the
complexity of computing edit distances"]`; the unconstrained version is equally
hard).

**The unconstrained ambient problem** minimises `Σ_i d_Lev(s, t_i)` over all
`s ∈ Σ_HG(k)*`. Its optimal cost is a lower bound on the constrained problem's
cost. The unconstrained optimum `s_∞*` may not be a canonical string; however,
`S2H(s_∞*)` is a well-defined connected hypergraph (P1), and
`d_I(S2H(s_∞*), K_i) = d_Lev(w*_c(S2H(s_∞*)), w*_c(K_i))` differs from
`d_Lev(s_∞*, w*_c(K_i))` unless `s_∞*` happens to be canonical. The ambient
median is therefore a useful heuristic initialiser but not a valid candidate for
the constrained problem.

### 3.2 Approximation algorithms

Standard algorithms for the median string (over an alphabet `Σ`, minimising
`d_Lev` sum):

1. **Exhaustive at small `N`, small `|t_i|`**: branch-and-bound. Exact; cost
   `O(k^L N L^2)` where `L = max |t_i|` and `k = |Σ_HG|`.
2. **Greedy stochastic** (Bunke et al. 2002 `[unverified]`): repeat random
   restarts of a coordinate-ascent in the string — swap, insert, delete one
   token, accept if the objective improves. No guarantee; fast in practice.
3. **Beam search**: maintain a beam of `B` current candidate strings; at each
   step expand each by all single-token edits, keep the top-`B` by objective.
   Run until convergence. Initialise from the medoid's canonical string.
   **Recommended for our use** — the alphabet `|Σ_HG(k)|` is finite and moderate
   (for k=3: 14 instruction families), the beam is manageable, and every
   candidate decodes to a connected hypergraph (P1) — no validity filter needed.
4. **Casacuberta–Vidal algorithm** `[unverified]`: stochastic generative model
   + EM. Requires fitting a string HMM; overkill for our regime.

**Algorithm recommended here:** Beam search (width `B = 10`, depth limited by
`max_iter = 200`) in the **ambient** space `Σ_HG(k)*`, re-canonicalizing each
accepted candidate before evaluating `d_I`. The re-canonicalization step ensures
the objective is always evaluated correctly; its cost is one `w*_c` call per
candidate accepted. Initialize from `w*_c(M_k)` (the medoid's canonical string).

**Guarantee carried**: no approximation ratio guarantee beyond the medoid's 2-
approximation; beam search converges to a local minimum. For the experiment,
the ILP exact oracle (§5) provides the ground truth at small N.

### 3.3 The key structural advantage

**Graph literature's route** (Ferrer, Valveny, Serratosa, Riesen & Bunke
`[unverified — check: "Generalized median graph computation by means of graph
embedding in vector spaces", CVIU 2009]`): embed each graph into `ℝ^d` via
spectral or WL features, take the Euclidean mean vector, then **reconstruct** a
graph from the mean vector. The reconstruction step is approximate and
non-canonical — it requires solving an inverse problem that has no clean
algebraic solution.

**Our route**: search in `Σ_HG(k)*`, call `S2H` on the winner. The reconstruction
step **does not exist** because `S2H` is total and exact: every string in
`Σ_HG(k)*` decodes to a well-defined connected hypergraph (P1). The decoded
median is not a round-trip of any specific input; it is a new object freshly
constructed from the median string — and that is exactly what is wanted.

### 3.4 Is the decoded median string canonical? What if it is not?

**It is generally not.** The beam search returns some `s*` that minimises the
objective; `s*` is typically NOT equal to `w*_c(S2H(s*))`. This means:

- `s*` is a valid encoding of the hypergraph `H_M = S2H(s*)`.
- The canonical form is `w*_c(H_M)`, which is different from `s*`.
- The true `d_I` distances from `H_M` to the inputs are `d_Lev(w*_c(H_M), w*_c(K_i))`,
  **not** `d_Lev(s*, w*_c(K_i))`.
- The objective we were optimising (`Σ_i d_Lev(s*, w*_c(K_i))`) is not the same
  as the objective we care about (`Σ_i d_I(H_M, K_i)`).

**Resolution in the beam search**: after each step, re-canonicalize the accepted
candidate and evaluate `Σ_i d_Lev(w*_c(S2H(s_candidate)), w*_c(K_i))`. This
makes the search correct but adds one `w*_c` call per accepted step.
Alternatively, restrict the beam to canonical strings only; but the move
operator (single-token edit) on a canonical string does not generally produce a
canonical string, so re-canonicalization is unavoidable.

**This is an honest limitation, not a fatal one.** The beam search + re-canonicalization
finds a local minimum of the correct objective. The medoid `M_k` is a valid
2-approximate starting point. The iterative refinement is meaningful.

---

## 4. Complexity accounting — where we win and where we do not

### 4.1 The N×N matrix

Let `n` = mean node count per KB, `m` = mean fact count, `k` = max predicate
arity, `L = |w*_c(K_j)|` the mean canonical string length. By the length lemma:
`L ≤ m(1+kn)`.

| Step | Ours | Hungarian GED |
|---|---|---|
| Per-instance preprocessing | 1 `w*_c` call (**O(n!·L)** worst-case; **O(L)** for labeled, symmetry-broken inputs) | none |
| Per-pair distance | `O(L²)` Levenshtein | `O(n³)` bipartite assignment |
| Matrix fill (N KBs) | `N` preprocessing + `N²·L²/2` | `N²·n³/2` |
| Amortization | **N canonicalizations for N² pairs** — pay once per instance | **N² solves, no amortization** |

**When does ours dominate?**

For labeled KB instances (the case here, since unary predicates are real labels),
the canonicalization is expected fast — labels break tie structures and shrink
automorphism groups (gate G-L1 in `scope.md §3`; magnitude unmeasured). Assuming
`T_c` = per-instance canonicalization time:

```
Ours faster when:   N · T_c + N² · L²  <  N² · n³
⟺   T_c / N  +  L²  <  n³
```

For `n = 10, k = 3, m = 20`: `n³ = 1000`. `L ≤ 20·31 = 620`, `L² ≤ 384400`. So
`L² >> n³` in this regime — Hungarian is cheaper **per pair**. But ours pays `N
T_c` once vs `N² · n³ / 2` Hungarian solves: for `N = 50`, `n = 10`, the
crossover requires `T_c < N · (n³ - L²) / 2 < 0`, which fails — ours is
slower per pair and does not amortize at this scale.

**Honest conclusion on throughput**: Hungarian GED is faster per pair for the
small KBs that fall within our `w*_c` envelope. The performance advantage is
on the N axis (linear preprocessing vs N² pair computations) which only
materializes for very large N (>> 1000) and small `n`. In practice, for N ≤ 100
and n ≤ 20 (our regime), the runtimes are comparable and the distinction is not
the selling point.

The selling point is the **guarantee** and the **generalized median decodability**
— not throughput. The paper must not claim a speed advantage that does not hold.

### 4.2 Measured reference point

On the Stratum C corpus (72 items, k=3, cells (9,12)/(12,20)/(15,35), all
unlabelled): `d_I^⊥` matrix costs 2–20 s per corpus seed. At k=3, n=15, 72
items: ~130 pairs. Hungarian on the same scale would be ~130 × 15³ ops = ~440k
ops ≈ 0.004 s. So **unlabelled canonical strings are 500× slower per matrix** at
this scale. For labeled inputs the ratio is expected to shrink substantially
(G-L1), but it must be measured before any speed claim.

**What this means for the experiment**: schedule and report wall-clock for both
methods. Expect to lose on raw throughput; the guarantee and decodability are
the surviving claims.

---

## 5. Experiment plan

### 5.1 Corpora and data selection

**Primary: ARB / Benson contact datasets.** From the feasibility table in
`../data.md §4` (closed G-D1, 2026-08-12): `contact-high-school` and
`contact-primary-school` both have maximum simplex arity ≤ 5 and exist in BOTH
temporal and labeled formats. Use the **labeled** format (provides class labels
= departments/grades = natural grouping criterion, resolving DQ-L1 below).

**DQ-L1 resolution (group formation).** `../data.md §7` lists three candidates:
ego-nets by shared label, temporal snapshots within a window, matched-size
ego-nets. The justified choice for P-MEDIAN:

> **Ego-networks of vertices sharing a department label.** For `contact-high-school`:
> nodes are students, node labels are class/grade labels, hyperedges are
> contact groups (a hyperedge exists when ≥3 students are in simultaneous
> contact). The ego-network of student `v` = all hyperedges incident to `v`.
> A **group** = the set of ego-networks of all students in the same class.
> The consensus of that group = the consensus contact pattern for a student
> in that class. This is semantically coherent (the consensus KB for "what
> does a typical student in class X look like") and uses the community's own
> data derivation (Qin et al. ICDE 2023 Definition 1).

**Why not temporal snapshots here**: P-MEDIAN on temporal data asks "what does
the median time-point look like", which is meaningful but less interpretable for
a first experiment. Temporal consensus is future work.

**Group size N**: 5–20 ego-networks per group (depends on class size; contact-high-school
has ~327 students in ~9 classes → ~36 students/class on average → groups of N ≈ 36).
Filter to the K groups with at least 5 members. Run the medoid as a sanity check
at all group sizes; run the ILP exact and alternating-majority-vote only at N ≤ 15.

**KB size**: ego-networks of individual students in `contact-high-school` are
small (typically 3–15 facts, n ≤ 20 under E1). The `w*_c` envelope at k=5,
n≤8 is tight (all `k=5` instances feasible only at n=8; `../scope.md §3`). Under
E1, k=5 since max simplex arity = 5. Feasibility gate **G-L2**: measure
per-instance `w*_c` wall-clock on 50 sampled ego-networks. If median > 1 s,
filter to n ≤ 8 ego-networks (typically possible by restricting to the largest
simplex-arity-2 subsets). Report the filtering fraction.

**Seeds**: 27 (project standard, BCa 95% CIs, Holm-corrected Wilcoxon).
Variation over seeds = variation over random group selection (sample without
replacement from the class's ego-networks when the class is large).

### 5.2 Algorithm implementations

| Algorithm | Implementation | Parameters |
|---|---|---|
| **Medoid under `d_I`** (ours) | argmin column-sum of `D_I` matrix | — |
| **Medoid under `d_{HB}`** | argmin column-sum of `D_{HB}` matrix; `d_{HB}` via `scipy.optimize.linear_sum_assignment` on node-pair cost matrices | edit costs = unit (match Qin) |
| **Alternating majority vote** | align each `K_i` to current estimate `M_t` via `scipy.optimize.linear_sum_assignment`; update `M_t` by per-atom majority over aligned inputs; repeat 20 iter or convergence | init = medoid under `d_I` |
| **Beam search (generalized median under `d_I`)** | width B=10, 200 iterations; single-token edits to current best canonical strings; re-canonicalize per step | init = medoid under `d_I` |
| **ILP exact** (ground truth at small N) | binary atom variables + permutation per input; `ortools` CP-SAT; 120 s timeout | N ≤ 15 only |

### 5.3 Metrics

**Primary (in common distance `d_I`):**
- Objective value `Σ_i d_I(M, K_i)` for every method, evaluated in `d_I`
  (re-canonicalize if M is produced in a non-canonical form)
- Approximation ratio vs ILP exact: `Σ_i d_I(M, K_i) / OPT_{d_I}` (where
  `OPT_{d_I}` is the ILP result; reported only where ILP completes within 120 s)

**Secondary (each method's native objective, for honesty):**
- `Σ_i d_{HB}(M_{HB}, K_i)` for the Hungarian medoid (its own metric)
- `Σ_i d_{maj}(M_{maj}, K_i)` for alternating majority vote (its native
  Hamming on aligned representations)

**Fairness note**: each method optimizes its own objective. The common-distance
table (`d_I` as the common currency) is the primary table; native-objective
values are reported alongside to show each method is not gaming the common metric.

**Runtime:** wall-clock per group (end-to-end: canonicalize + matrix + optimize).

**Statistics:** BCa 95% CIs over 27 seeds; paired Holm-corrected Wilcoxon for
pairwise method comparisons on the primary objective.

---

## 6. Baselines with pre-registered interpretation contract

*Written before any results are seen. Binding in both directions.*

| Baseline | What it computes | Expected loss or win | Surviving advantage if we lose |
|---|---|---|---|
| **Medoid under `d_{HB}`** (Riesen-Bunke 2009) | `argmin Σ_i d_{HB}(K_j, K_i)` | May achieve lower `Σ d_I` cost if `d_{HB}` is a good proxy for `d_I` | Our guarantee: the medoid 2-approximation holds under `d_I` (proved); theirs does not (§2.2) |
| **Alternating majority vote** | iterative alignment + per-atom majority | May reach a lower `d_I` objective via local refinement | Our medoid is always at least as good as its initializer; the alternating method is a local heuristic with no guarantee |
| **Permutation synchronization** (Pachauri-Kondor-Singh `[unverified]`) | cycle-consistent joint alignment, then majority vote | Most principled competitor; expected to do well on the native objective | Expensive (O(N² n²) per iteration); our pipeline is strictly cheaper for the matrix phase |
| **Embed → vector median → reconstruct** (Ferrer et al. `[unverified]`) | mean in WL/NetLSD space, project back | May reach competitive cost on `d_I` | Its reconstruction is approximate; ours (S2H) is exact. Any gap between the reconstructed object and the true median is structural noise in their pipeline |
| **ILP / QAP exact** | true optimum of `Σ d_{SED}` at small N | Wins on its own (NP-hard) objective; may win on `d_I` too | Exponential cost; our 2-approximate medoid under `d_I` runs in poly time |
| **WL histogram + vector median** | Euclidean mean of WL vectors, decode | Degenerate at fixed degrees (tie-degenerate, see T-M4b); expected ARI floor | Measured: WL is hubness-degraded at our regime (T-M5d) |
| **nauty-Levi edit + medoid** | medoid under nauty certificate edit distance | Likely faster matrix fill; may win on `d_I` since nauty-Levi edit is a metric too | No decoder for the generalized median search: interior alignment paths are not certificates |

**Pre-registered outcome rules:**

1. No competitor is removed on the basis of winning. If `d_{HB}` medoid achieves
   lower `Σ d_I` cost, that result is reported as is; the surviving claim is
   the guarantee differential, not the task score.
2. If the ILP exact (our surrogate for OPT_{d_SED}) shows our medoid has
   approximation ratio > 2, investigate whether the assumption of `d_I ≈ d_SED`
   is violated; this does not invalidate the 2-approximation theorem (which is
   about `d_I` vs `d_I`, not `d_I` vs `d_SED`).
3. If alternating majority vote improves on the medoid by > 10% consistently,
   report it as the recommended algorithm alongside the medoid as the certified
   baseline.
4. If beam search for the generalized median does not improve on the medoid, the
   medoid is the recommended output and the beam-search section is shortened to
   a "we tried and it did not help" paragraph.

**Common-distance reporting.** All primary rows evaluate `Σ_i d_I(M, K_i)`.
This is the only fair comparison: each method's output is a hypergraph, and
`d_I` is computed on that hypergraph regardless of how it was produced. Methods
that produce a non-hypergraph output (e.g., a WL mean vector that does not
decode) are excluded from the primary table and noted in the capability matrix.

---

## 7. The distance-mismatch resolution for P-MEDIAN

### 7.1 The gap

The PI's analysis (`src/idea3.txt`) is written in `d_SED` (iso-invariant symmetric
difference of ground facts). We compute `d_I`. They are not the same (`vocabulary.md §2`,
fact 1). The foundation recommends resolution **(c)**: compute both, report the
gap (`risks.md §1`).

**For P-MEDIAN specifically:**

- `d_I`-median: `M_I = argmin_𝔐 Σ_i d_I(𝔐, K_i)` — polynomial-time approximation
- `d_SED`-median: `M_{SED} = argmin_𝔐 Σ_i d_{SED}(𝔐, K_i)` — NP-hard; ILP exact
  at small N and small domain size

**Resolution (c) implemented:** For each group of KBs where the ILP completes,
report:
- Cost of `M_I` in `d_I`: `Σ_i d_I(M_I, K_i)`  
- Cost of `M_I` in `d_SED`: `Σ_i d_{SED}(M_I, K_i)` [needs HGED oracle]
- Cost of `M_{SED}` in `d_{SED}`: `OPT_{d_SED}` [ILP]
- Suboptimality: `(Σ d_{SED}(M_I, K_i) - OPT_{d_SED}) / OPT_{d_SED}`

This uses the exact HGED oracle (already implemented, `metric_space/distances/hged.py`)
at small N and small ego-network size (feasible; see DQ1' closure: n≤10, m≲8,
exact oracle < 5 s per pair). The reported gap is an **operational number**:
"replacing the NP-hard `d_SED` computation with the polynomial-time `d_I` costs
X % suboptimality on these benchmarks."

This converts the ρ = 0.622 Spearman correlation (E1' result) from a discussion
footnote into an actionable approximation ratio.

### 7.2 The per-atom majority-vote characterization

The PI's analysis (src/idea3.txt §"The one structural fact…") establishes: once
alignments `{σ_i : K_i → ref}` are fixed, the `d_SED`-optimal median is per-atom
majority vote. The hardness is entirely in the joint alignment.

**Does any analogous characterization hold for `d_I`?**

**No.** The argument breaks for `d_I` at the decomposition step. `d_I(𝔐, K_i) =
d_Lev(w*_c(𝔐), w*_c(K_i))` is a global string alignment, not a per-atom count.
Even if all N canonical strings share the same character at position `p`,
replacing that character in the candidate string does not correspond to a
consistent structural edit (tokens are instruction-level, not atom-level;
adjacent tokens interact through the VM state). More precisely:

- `d_{SED}` decomposes as `Σ_atoms a [a∈M XOR a∈σ_i(K_i)]` once alignments are fixed.
- `d_Lev(w*_c(𝔐), w*_c(K_i))` does not decompose per token position because the
  Levenshtein alignment is itself a global optimisation that shifts all subsequent
  positions.

**Consequence**: the `d_I`-median has **no closed form** and must be searched.
The majority-vote algorithm is not applicable in our string metric. The iterative
alignment + update loop (alternating majority vote) operates on `d_SED` and must
be included as a baseline, not as our algorithm. Our algorithm for the generalized
median is beam search in `Σ_HG*` with re-canonicalization (§3.2).

---

## 8. What P-MEDIAN requires from our representation — and what it does not

### 8.1 What uniquely requires our representation

| Property | Why P-MEDIAN needs it |
|---|---|
| **`d_I` is a metric (Corollary A)** | The 2-approximation guarantee holds *because* `d_I` is a metric; without this, the medoid has no provable approximation ratio |
| **Theorem A (completeness)** | Deduplication of candidates during beam search is exact — zero false merges. Vector fingerprints and Hungarian-GED approximations cannot deduplicate exactly |
| **Closed alphabet / P1** | Every string in `Σ_HG*` decodes to a valid connected hypergraph — the beam search generates no invalid candidates. No validity filter. No reconstruction step |
| **`S2H` is total** | The decoded median is always a well-defined hypergraph — no partial decode, no reconstruction error |
| **`d_I` is polynomial** | N canonicalizations + N² Levenshtein comparisons, not N² NP-hard GED solves |

### 8.2 What does NOT uniquely require our representation

| Component | Also achievable with |
|---|---|
| **Medoid** (set medianoid only) | Any metric. nauty-Levi edit distance IS a metric; medoid under nauty-edit would also give a 2-approximation |
| **Iso-invariant pairwise matrix** | Any complete canonical-form method (nauty/bliss/Traces + edit) |
| **Iso-invariant deduplication during search** | Any complete canonical labeling (faster methods exist) |

**The distinction narrows to the generalized median.** For the medoid, the
2-approximation follows from any metric, and faster metrics exist. The uniqueness
claim is:

> *Only a representation with a closed, total ambient space can support the
> generalized median search without a reconstruction step. nauty-certificate
> strings, WL vectors, and spectral descriptors all fail: nauty certificate
> interior points are not certificates of anything (C3 in `../applications.md`);
> WL/NetLSD points in `ℝ^d` are not hypergraphs.*

The generalized median is therefore the part of P-MEDIAN that UNIQUELY needs
our representation. The medoid alone is the part that also works with competitors,
though our medoid carries a polynomial cost that nauty-Levi-edit also achieves
(with faster canonicalization). The paper must be honest about this distinction.

---

## 9. Verdict

### 9.1 Both central claims survive

- The 2-approximation for the medoid is **proved** (§2.1) and requires only
  Corollary A — work already in hand.
- The Hungarian/bipartite approximation is genuinely **not a metric** (§2.2).
  The comparative claim is sharp and honest.

### 9.2 Estimated cost

| Component | Effort | Status |
|---|---|---|
| Medoid pipeline (d_I matrix → argmin) | Trivial — 5 lines on existing `D.npy` infrastructure | Ready now |
| `d_{HB}` baseline (bipartite matching) | 1–2 days | New code; `scipy.optimize.linear_sum_assignment` |
| Alternating majority vote | 2–3 days | New code; N assignment solves per iteration |
| Beam search (generalized median) | 3–5 days | New code; re-canonicalize per step |
| ILP exact oracle (CP-SAT) | 2–3 days | New code; small N only |
| Data prep (contact-high-school ego-nets by label) | 1 day | `core/sparse_hypergraph.py::ego_network` + label filter |
| Feasibility gate G-L2 (measure labeled `w*_c` times) | 1 day | Measure before scoping |
| Analysis / stats harness | 1–2 days | Port from existing BCa/Holm harness |

**Total estimate: 2–3 person-weeks** (one focused sprint). This is within the
scope of one ledger session pair (measure + implement).

### 9.3 Key risks, ranked

1. **`w*_c` too slow on labeled ego-networks at k=5.** If G-L2 finds median >
   1 s per ego-network, filter to arity-3 subsignatures or switch to the
   2-simplex subsets of the temporal format. This reduces the signature to
   k=3 (feasible to n≈24). Mitigation: measure first (gate G-L2).

2. **Hungarian medoid achieves the same `d_I` objective** as our medoid, making
   the task-score comparison a draw. **This is not a defeat** — our guarantee
   still holds and theirs does not; the result is reported honestly per the
   pre-registered contract (§6).

3. **ILP fails to converge at any N in the time budget.** Fall back to
   reporting approximation ratio vs the alternating-majority-vote result, which
   serves as an upper bound on OPT.

4. **Group formation (DQ-L1) produces trivially-similar ego-networks.** If
   ego-nets in the same class are too similar (medoid nearly equals every member),
   the experiment becomes vacuous. Measure within-group `d_I` variance before
   committing; use temporal-window groups as the fallback.

### 9.4 Recommendation

**P-MEDIAN should be the flagship logic application, run first.** Reasons:

1. Runs on existing infrastructure (D.npy matrices, `ego_network` function,
   HGED oracle, BCa/Holm harness). Marginal new engineering is modest.
2. The metric guarantee (Corollary A → 2-approximation) is the program's
   cleanest theoretical advantage, independently verifiable by any reviewer.
3. Immune to the small-perturbation weakness measured at T-M4b: the task is
   aggregation, not recovery of planted edits.
4. No alphabet decision (D3') required — works entirely within current `Σ_HG`.
5. Data is on disk today (`contact-high-school`, 5 datasets at arity ≤ 5).
6. The honest complexity story (we lose on throughput, we win on guarantee
   and decodability) is a TKDE-shaped result — not "we are faster" but "we
   give what others cannot certify."

Schedule: P-MIN (countermodel census) as a parallel, independent exhibit;
P-REPAIR / P-ENTAIL after D3' decision.

---

## 10. Requested changes to the shared foundation

*DO NOT edit shared files. The orchestrator merges these on ratification.*

### 10.1 `vocabulary.md` — distance table

The current table lists 5 distances (`d_△`, `d_≅△`, `d_SED`, `HGED`, `d_I`).
Add a row for `d_I^Σ` as the **sixth** named distance:

> `d_I^Σ` | `d_Lev(w*_c^Σ(A), w*_c^Σ(B))` where `w*_c^Σ` uses the label-aware
> encoder (non-trivial vocabulary) | yes | yes | same as `d_I` but requires
> `LabelVocabulary.fit()` across the KB corpus

This is needed because KB applications (`d_I^Σ`) are the honest choice when
node labels are unary predicates; the article's existing geometry tables are
`d_I^⊥` (`vocabulary.md §2`, fact 3), and the logic program needs its own
geometry measurement.

### 10.2 `problems.md §P-MEDIAN`

Add a paragraph distinguishing the ambient median string (unconstrained, may not
be canonical) from the constrained median over canonical strings. The current
text states the guarantee but does not clarify that the beam-search objective
must evaluate `d_I` (with re-canonicalization), not bare `d_Lev(s, w*_c(K_i))`.

### 10.3 `data.md §4 — open data questions`

Add a sub-item under DQ-L1:

> **DQ-L1 resolution (P-MEDIAN, proposed 2026-08-12).** Use `contact-high-school`
> labeled format: ego-networks of vertices sharing a department/class label as
> the group. Justification: semantic coherence; Qin et al. ICDE 2023 Definition 1
> is the community's own derivation. Gate: G-L2 (measure `w*_c` wall-clock on
> sampled ego-networks; filter if median > 1 s). Fallback: temporal-window groups
> or arity-3 filtered subsets.

### 10.4 `scope.md §2` — add P-MEDIAN note

At the start of §2 (Decidability), add:

> **P-MEDIAN has no decidability issue** — there is no sentence; it is purely
> metric optimization. The size envelope (§3) constrains the canonicalization
> step; it does not constrain `N` (N can be large; canonicalize once, compare
> N² times).

### 10.5 `risks.md §1` — P-MEDIAN-specific clarification

Add under "Consequence for the idea files":

> For P-MEDIAN: the per-atom majority-vote characterization (src/idea3.txt) is
> a statement about `d_SED`, not `d_I`. No analogous closed form exists for
> `d_I` (see `ideas/idea3_median.md §7.2`). The `d_I`-median must be searched.
> The distance mismatch is measured via resolution (c): HGED oracle at small N
> converts ρ = 0.622 into an approximation ratio.

---

*End of document. Written 2026-08-12. No shared files were modified.*
