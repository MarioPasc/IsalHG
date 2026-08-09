# T-M5m — A4's decodability result is vacuous; measure ambient decodability instead
**Declared:** 2026-08-09 18:30 CEST
**Status:** OPEN
**Depends on:** T-M5e (CLOSED — the experiment this repairs). Independent of
T-M4b; the corpus confound does not touch this claim.
**Delegation:** agent
**Why out of scope:** Found while planning `docs/article/figures/F3`, not while
executing T-M5e. T-M5e is closed and its file is append-only; the corrected
claim is a different measurement, so it needs its own task.

**Context to read first:**
- `docs/article/figures/F3-decoding-corridor.md` — the full analysis: the
  proposition, its two-part proof, the measurement, and the panel spec
- `docs/article/DEVELOPMENT/T-M5/CLOSED/T-M5e.md` — the task being repaired
  (scoring criteria (i)–(iii); (iii) is the defective one)
- `experiments/article/analysis/shortest_path.py::run_design_a4_experiment`
  and `::decode_path_intermediates` — where the pool-based decode happens
- `results/T-M7q/a4_design/design_a4/*/seed*/a4_result.json` — the shipped
  results, incl. the `decodability` blocks
- `scripts/diagnostics/ambient_decodability_probe.py` — the replacement
  measurement (5 design pairs, 62 intermediates, all decode + all connected)
- `src/isalhg/core/string_to_hypergraph.py` — S2H, total on `Σ_HG(k)*`
- `src/isalhg/metric_space/distances/isalhg_levenshtein.py` — the module
  docstring establishing that `d_I` is a **token**-level distance, which the
  proposition depends on
- `docs/article/empirical/applications.md` §A4 — the prose to correct
- `.claude/rules/coding_rules.md` — always

**Description:** The shipped A4 decodability score is a tautology. The
experiment builds a **pool** of pre-existing hypergraphs (the ladder's true
intermediates plus distractors), runs Dijkstra on the pool's distance matrix,
and then decodes the canonical strings of the pool members the path visited.
`all_valid: true` is therefore `S2H(w*_c(H)) ≅ H` on objects that were
hypergraphs before the experiment began — round-trip soundness restated, not a
capability demonstrated. The competitor contrast fails identically: NetLSD's
recovered path on `sts9_s1` is `[0, 4, 6, 8, 9, 17, 20]`, i.e. pool indices,
i.e. hypergraphs, which are as drawable as ours. The claim "WL, NetLSD and HPD
have no decoder — they cannot exhibit the intermediate hypergraphs" is not true
*of that construction*.

The genuine claim, which no competitor can match, is about the **ambient**
space: every string on a Levenshtein alignment path between two canonical
strings decodes, whether or not it is anyone's canonical form. Stated as a
proposition:

> **Proposition (ambient decodability).** Let `u_0, …, u_d` be the token strings
> realised by an optimal Levenshtein alignment from `u_0 = w*_c(H_A)` to
> `u_d = w*_c(H_B)`. Then every `u_j ∈ Σ_HG(k)*`, and `S2H(u_j)` is a
> **connected** hypergraph of arity ≤ `k`.

Proof in two parts, both already available: (1) `d_I` runs over the token
sequence, so an alignment edits whole alphabet symbols and every `u_j` is a word
of `Σ_HG(k)*`, on which S2H is total (Critical Invariant 2); (2) `V_{i,j}`
attaches its `j` fresh vertices to an edge containing `i ≥ 1` existing ones and
`C_i` adds no vertices, so by induction from the one-vertex start every prefix —
hence every `u_j` — decodes to a connected hypergraph. The connectivity half
matters: the ambient space decodes exactly onto the article's working domain
(D-CONN1), with no illegal intermediates to explain away.

Measured on five design pairs (`ambient_decodability_probe.py`): **62/62
intermediates decode, 62/62 are connected, and only 10/62 are canonical —
exactly the two endpoints of each path.** No interior point of any geodesic is
canonical, which is the sharp form of the caveat and must be reported with the
result: the geodesic runs through `Σ_HG(k)*`, leaving the sparse canonical
image. The STS7 → TightCycle3 walk (`d_I` = 10) *contracts to a 3-vertex
bottleneck and rebuilds* rather than morphing — a direct, visible illustration
of the closing discussion's point that `d_I` is not an edit-distance proxy.

Keep the pool experiment for what it does measure: path-length monotonicity
(1.00 for every representation) and recovery fraction (IsalHG 0.125, NetLSD
0.257, HPD 0.191, WL 0.000). Only criterion (iii) is defective.

**Acceptance:**
1. `experiments/analysis/figures/decoding_corridor.py` exists, ports the probe,
   and renders F3 panels (a)–(c) via `src/isalhg/viz` (no hand-rolled
   hypergraph drawing).
2. A regression test pins the proposition empirically on the five reference
   pairs: 62/62 decode, 62/62 connected, 10/62 canonical. It must fail if the
   alphabet stops being closed or the distance stops being token-level.
3. The proposition is stated in `docs/article/theoretical/` with both halves —
   decodability *and* non-canonicity of interior points.
4. `empirical/applications.md` §A4 no longer cites the pool-based `all_valid`
   number as evidence of decodability, and no longer claims competitors cannot
   exhibit intermediates *in the pool construction*; the capability-matrix row
   cites this task's measurement instead (`figures/F6-capability.md`).
5. The prose does not describe the geodesic as a structural morph.

**Out of scope here:** re-running the pool-based A4 experiment; changing the
shortest-path scoring criteria (i)–(ii); the corpus question (T-M4b); any change
to S2H, `w*_c`, or the distance.
