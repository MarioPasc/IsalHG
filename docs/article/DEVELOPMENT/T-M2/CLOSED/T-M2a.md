# T-M2a — Faithful Qin-et-al. HGED re-implementation + PS/HS/MO validation (+ C++ if too slow)
**Declared:** 2026-07-08 18:45 CEST (handoff from T-M2)
**Status:** DONE
**Depends on:** T-M2 (DONE)
**Why out of scope:** T-M2 delivered a working exact-HGED oracle under a
**whole-edge** unit convention (deleting a `k`-edge = 1 op), chosen so the
perturbation-ladder guarantee `t ≥ HGED` holds. Making HGED **bit-for-bit
faithful to Qin et al. (2023)** and *proving* the fidelity by reproducing the
paper on its own datasets — plus a possible C++ port — is a distinct, larger
reproduction + performance effort, not T-M2's "build a working oracle" scope.
**Context to read first:**
- `docs/references/Explainable Hyperlink Prediction.pdf` — Qin et al., ICDE 2023. Read: **Def 3** (edit taxonomy — op (i) insert/delete a *cardinality-0 / empty-shell* node **or** hyperedge; op (ii) extend/reduce a hyperedge by one node; op (iii) node/hyperedge label substitution — all unit cost, so deleting a `k`-node hyperedge costs **k+1**); **§III** (hypergraph model, `NEI`/`DEG`, the `EGO` ego-network); **Alg. 1 + Procedure EDC-INAC**, **Alg. 2 (EDC** via bipartite `B_G`**)**, **Alg. 3 (HGED-BFS** + Strategy 1 re-rank / Strategy 2 upper bound / Strategy 3 lower bound**)**; **Def 5** (label-multiset LB `Ψ(S₁,S₂)=max(|S₁|,|S₂|)−|S₁∩S₂|`); **Def 6** (hyperedge-cardinality LB); **Example 2** (`HGED(EGO(u₄),EGO(u₅)) = 6` — the one published numeric anchor); **Table II** (HGED-BFS seconds / 1000 node-pairs on PS/HS/MO with `n`, `m`, mean-cardinality columns).
- `src/isalhg/metric_space/distances/hged.py::{ExactHGED, _partial_edge_lb, _edge_cost, _vertex_cost, _bipartite_matching}` — the T-M2 **whole-edge** oracle to reconcile/replace; its cost model differs from Qin's (whole-edge delete = 1 vs Qin's `k+1`).
- `src/isalhg/core/sparse_hypergraph.py::{SparseHypergraph, delete_hyperedge, insert_hyperedge, edit_path}` — the model + the ladder's whole-edge delete/insert (the exact source of the convention mismatch: `edit_path`'s `t ≥ HGED` guarantee holds only under whole-edge unit costs).
- `docs/article/theoretical/stability.md` §2 (Theorem B — HGED on the RHS), **§2.0 line ~78** ("HGED itself is the one from Qin et al. — same edit taxonomy, unit cost" → the article theory already assumes Qin's convention), §2.1 (single-edit reduction — the proof is built on Qin's taxonomy), §4 (density sweep). This is the **intended use** that defines "too slow" *and* the taxonomy the stability proof assumes.
- `docs/article/empirical/correlation.md` §HGED — the oracle tiering; how HGED feeds Exp E2 (pairwise-over-corpus + density sweep = the real workload).
- **Datasets** (Benson node-labeled format; each dir has a `README.txt`): `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/misc/HGED/data/{contact-primary-school → **PS**, contact-high-school → **HS**, mathoverflow-answers → **MO**}`. Format: `hyperedges-<name>.txt` (one hyperedge per line, comma-separated node indices), `node-labels-<name>.txt` (label per node line), `label-names-<name>.txt`. **PS = 242 nodes / 12704 hyperedges — matches the paper's Table II exactly**, confirming the mapping.
- `src/isalhg/datasets/arb_benson.py` — the ARB/Benson loader (currently a 3×`NotImplementedError` stub) to implement/extend for the node-labeled PS/HS/MO triples; `src/isalhg/datasets/schemas.py::LabelVocabulary.fit` (also deferred) for the real node-label vocabulary.
- **C++ build to mirror** (only if the C++ route is taken): `src/isalhg/core/_native/{bindings.cpp, src/*.cpp}`, root `CMakeLists.txt`, `pyproject.toml` `[build-system]` + `[tool.scikit-build]` (scikit-build-core ≥ 0.9 + nanobind ≥ 2.0).
- `.claude/rules/coding_rules.md` — always.
**Description:** Re-implement HGED so it is **faithful to Qin et al. (2023)** and
prove the fidelity by reproducing the paper on its own datasets; port to C++ only
if the Python speed fails the article's intended use. Step by step:
1. **Faithful cost model + algorithm.** Implement Qin's **HGED-BFS** (Alg. 3) with
   the **EDC** inner cost (Alg. 2) over Qin's *empty-shell* taxonomy: deleting/
   inserting a `k`-node hyperedge costs **k+1** (k incidence reduces + 1 empty-shell
   delete), incidence extend/reduce = 1, node/hyperedge label substitution = 1;
   with Strategies 1–3 and the Def 5 (label-multiset `Ψ`) + Def 6 (hyperedge-
   cardinality) admissible lower bounds. This is a *different metric* from T-M2's
   whole-edge `ExactHGED`.
2. **Convention decision (flag for PI, blocking design choice).** Qin's `k+1`
   convention **breaks** the ladder guarantee `t ≥ HGED` (`edit_path` deletes a
   whole edge at unit cost, Qin scores it `k+1`). Decide with the PI whether the
   **article's HGED oracle adopts Qin's convention** (then `edit_path`/the ladder
   and the T-TB single-edit reduction must be reworked to Qin's finer ops), or the
   faithful implementation lives **alongside** the whole-edge oracle as a
   validation reference only. Land accordingly: a `QinHGED` sibling class *or* an
   `edit_model={"qin_empty_shell","whole_edge"}` switch on `ExactHGED`; register it.
3. **Ego-network scope + labeled loading.** The paper computes `HGED(EGO(u),EGO(v))`
   between node ego-networks (closed-neighborhood induced sub-hypergraphs, `NEI`/
   `DEG` per §III) on *node-labeled* hypergraphs. Implement ego-network extraction
   and node-label-aware loading of PS/HS/MO (extend `arb_benson.py`; fit the
   `LabelVocabulary`).
4. **Paper reproduction (the fidelity proof).** (a) Unit fixture: reconstruct
   Example 2 and assert `HGED(EGO(u₄),EGO(u₅)) == 6`. (b) Reproduce **Table II**:
   for PS/HS/MO, sample node pairs, compute HGED via HGED-BFS, and report
   **seconds / 1000 node-pairs** next to the paper's numbers (same `n`/`m`/mean-
   cardinality columns); state the wall-clock factor and the hardware. Fidelity =
   "the algorithm reproduces the published anchor(s) and our timings track the
   paper's regime." (c) Add any further numeric anchor reconstructable from the paper.
5. **Slowness gate (against the *intended use*).** Judge the Python speed against
   how the article uses HGED (`stability.md` §2/§4 + `correlation.md` §HGED):
   pairwise HGED over the Layer-1 correlation corpus + the density sweep (T-M5a).
   Define the concrete workload (corpus size × per-item `n`,`m` × HPC parallelism)
   and decide, **with numbers**, whether Python HGED-BFS is fast enough.
6. **C++ port (only if step 5 says "too slow").** Convert `distances/hged.py` → a
   `distances/hged/` **package**: a Python entry point (`__init__.py` re-exporting
   the `HypergraphDistance` subclasses) + a **nanobind** C++ extension under
   `distances/hged/_native/` (`bindings.cpp` + `src/*.cpp`), wired through the root
   `CMakeLists.txt` and `pyproject.toml` `[tool.scikit-build]`, mirroring
   `core/_native/`. The C++ path must return **identical** HGED values to the
   reference Python on every check (fixtures, Example 2, PS/HS/MO) and report the
   speedup.
**Acceptance:**
- Qin-faithful HGED reproduces the paper's published anchor — at minimum
  `HGED(EGO(u₄),EGO(u₅)) = 6` (Example 2) — and its taxonomy is verifiably Qin's
  (hand fixture: whole-edge delete of a `k`-edge = `k+1`, **not** 1).
- **Table II regime reproduced on PS, HS, and MO**: a reported seconds/1000-pairs
  table vs the paper, with hardware and the factor, plus a written statement that
  the implementation matches the paper.
- Speed-vs-intended-use decision documented with numbers.
- If the C++ extension is built, it passes **every** correctness check through the
  Python entry point and its speedup over the reference Python is reported.
- Full suite + ruff + mypy green; if Qin's convention is adopted for the oracle,
  the ladder / `t ≥ HGED` property tests and the T-TB reduction are reconciled
  (otherwise the reference-only path leaves T-M2's whole-edge oracle + its green
  tests untouched).
**Out of scope here:** the correlation experiment (T-M5a), competitors (T-M3*),
applications (T-M5b–e); *proving* the stability theorem (T-TB) — though this
task's convention decision is a **direct input** to T-TB (§2.1 assumes Qin's
taxonomy), so record the outcome there; Qin's downstream HEP hyperlink-prediction
model — we validate the *distance*, not their prediction pipeline.
**Closing (2026-07-08 22:46 CEST):**
- *Convention decision (step 2, PI via AskUserQuestion):* **reference-only** —
  `QinHGED` (registered `qin_hged`) is the paper-faithful validation reference +
  citable anchor; the whole-edge `ExactHGED` stays the article's oracle. Relation
  recorded in `stability.md` §2.0: `HGED_we ≤ HGED_qin ≤ (k+1)·HGED_we` pointwise
  with identical zero sets, so Theorem B over the whole-edge set *implies* the
  Qin-form bound with the same constant; only the whole-edge set carries the
  ladder guarantee `t ≥ HGED`. Ladder / T-M2 tests untouched. Also decided:
  MO multi-labels = **composite tag-set** symbols; C++ gate = decide-after-numbers.
- *Deliverables:* `metric_space/distances/qin_hged.py` (stdlib-only: EDC mapping
  cost, Def 5 `Ψ` + Def 6 bounds, ReRank, FIFO HGED-BFS with Strategies 1–3,
  `upper_bound` thresholded mode, `timeout`/`max_expansions` → `HGEDComputationError`,
  `_dfs_reference` = Alg 1+2 exhaustive test oracle); `core/sparse_hypergraph.py::
  ego_network` (Qin Def 1, full-containment induced); `datasets/arb_benson.py`
  node-labeled loader (1-based ids + label indices, composite MO labels, dedup
  reporting) + `LabelVocabulary.fit` implemented; `scripts/bench_qin_hged_table2.py`
  + `scripts/bench_qin_hged_gate.py`. Fig. 1 fixture (`qin_fig1_hypergraph`)
  derived from the paper's textual anchors and visually verified on a 300-dpi
  render of Fig. 1(b) — the E₁={u1,u2,u4}, E₃={u2,u3,u5}, E₄={u4,u5,u7,u8}
  memberships are pinned by LB-tightness (a 4-member E₁ forces Def5+6 LB > 6).
- *Acceptance (a) anchors:* `HGED(EGO(u₄),EGO(u₅)) == 6` (Example 2) ✔; Example 7
  mapping decomposition 1+2+3=6 ✔; Def 6 worked example = 3 ✔; k-edge delete = k+1
  (=4, vs whole-edge 1) and degree-h node delete = h+1 ✔; BFS ≡ exhaustive DFS on
  30 random labelled tiny pairs ✔; `ExactHGED ≤ QinHGED` + identical zero sets
  under Hypothesis ✔. Loader vs Table I: PS 242/12,704/11, HS 327/7,818/9,
  MO 73,851/5,446→5,445 (one duplicate member-set merged) ✔.
- *Acceptance (b) Table II regime* (i7-13700KF ≈ 2× the paper's i5-8400 single-
  thread; Python 3.11; 1,000 pairs/dataset, seed 0): the paper's own remarks
  (upper bound "10 in most situations", h_v,h_e ≤ 10) identify Table II as a
  **clamped** regime. Clamp-10 random pairs: PS 0.0020 s/pair (paper 0.23, ≈115×),
  HS 0.0003 (0.14, ≈450×), MO 0.0007 (10.3, ≈15,000×), 100% resolved at the root
  by the Def 5+6 bound, 0 DNF. HEP-style neighbor pairs (MO): 26% finite —
  259/264 exactly 0 (isomorphic egos), rest 4–10 — 72% >bound, 16/1000 DNF at
  60 s. Unclamped exact on real egos: PS/HS 20/20 DNF, MO 15/20 (10 s) —
  search-infeasible for any implementation, confirming the clamped reading. Same
  algorithm and bounds; our 2–4 orders of magnitude come from root/incremental
  bound evaluation vs (evidently) per-candidate from-scratch evaluation, whose
  n·m·log m cost matches the paper's 0.14/0.23/10.3 ordering. Full report:
  `/media/.../ISAL/isalhg/misc/HGED/docs/T-M2a_fidelity_report.md`; raw JSON/md in
  `.../HGED/results/`.
- *Acceptance (c) speed gate with numbers (D3):* Layer-1 corpus (n∈[4,7], 435
  pairs): QinHGED median 13.3 ms/pair, 0 DNF (whole-edge 0.94 ms) — Python amply
  covers the validation role. Density sweep: QinHGED unclamped DNFs 15/15 in
  every cell from n=10 at every density (unlabelled ⇒ Def 5 node bound ≡ 0 ⇒ no
  node-phase pruning), while the whole-edge oracle solves the sparse cells
  (n=12 m=6: 0.64 s) and saturates from m/n=1 at n≥12 (DQ1-consistent).
  **Recommendation: no C++ port** — the bottleneck is search space, not
  language; were Qin's convention ever adopted as oracle (T-TB's call), the fix
  is LSAP-style admissible bounds, not C++. PI decides per D3.
- *Closing checks:* `pytest tests/unit tests/property tests/integration -m "not
  slow" --hypothesis-seed=0` → **556 passed, 8 skipped, 2 deselected, 0 failed**
  (+42 vs T-M2's 514 = 8 ego + 22 qin + 9 loader + 3 property). Property suite
  re-run (core changed): 53 passed. ruff **3 == baseline**; mypy **21 == baseline**
  (none in new modules). No C++ change → no rebuild.
- *Docs:* progress log + fidelity/gate report in `/media/.../HGED/docs/`;
  `docs/article/CODE_DESIGN.md` distances map + `stability.md` §2.0 updated.
