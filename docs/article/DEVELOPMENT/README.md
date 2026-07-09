# IsalHG metric-space article — task ledger

Living task ledger for the metric-space journal article (target *Information
Sciences*). Scope docs live in `docs/article/`; this tree tracks the *work*.
Distinct from `docs/engineering/DEVELOPMENT.md`, which remains the iso-benchmark /
preprint code-as-built log.

## Layout

One directory per **scope**, one file per **task**, filed under its status:

```
DEVELOPMENT/
  README.md              this file — hub, index, dependency graph
  DECISIONS.md           decisions pending PI
  <SCOPE>/
    README.md            one paragraph: what this scope is for
    OPEN/ IN-PROGRESS/ BLOCKED/ CLOSED/
      T-<id>.md          one task, self-contained
```

A task **moves between status directories**; it is never rewritten in place
except to update its `Status` line and paste closing-check output. `git mv` makes
the transition visible in history. Ids containing `'` are filed with `prime`
(`T-M4'` → `T-M4prime.md`).

## How to use this tree

- **Pick up a task** with the `task-reader` skill (`/task-reader T-M0`). It
  resolves the id to its file, reads the task, its scope `README.md`, all its
  cited context, and the coding rules, then plans before touching code.
- **Add a task** with the `task-handoff` skill when you find out-of-scope work
  mid-development. It writes a new file under `<SCOPE>/OPEN/` with a live
  timestamp and the context pointers the next agent needs. Never solve
  out-of-scope work inline.
- **Timestamps** are wall-clock at declaration, captured via
  `date '+%Y-%m-%d %H:%M %Z'`. Task files are append-only.

## Status legend

`OPEN` — declared, not started · `IN-PROGRESS` — actively worked ·
`BLOCKED` — waiting on a decision/dependency · `DONE` — acceptance check passed
(filed under `CLOSED/`).

## Scopes

| Scope | Concern | Open | Closed |
|---|---|---|---|
| [`T-M0`](T-M0/) | Seed selection for `w*` | 2 | 2 |
| [`T-M1`](T-M1/) | `metric_space/` foundation + first distances | 1 | 2 |
| [`T-M2`](T-M2/) | HGED — the ground-truth structural distance | 1 | 3 |
| [`T-M3`](T-M3/) | Competing representations | 4 | 0 |
| [`T-M4`](T-M4/) | Corpora + scoring primitives | 2 | 0 |
| [`T-M5`](T-M5/) | The experiments | 5 | 0 |
| [`T-M6`](T-M6/) | Optional package reparent | 1 | 0 |
| [`T-TA`](T-TA/) | Theorem A — completeness of `w*_c` | 2 | 7 |
| [`T-TB`](T-TB/) | Theorem B — stability | 2 | 0 |
| [`T-DQ`](T-DQ/) | Data questions gating corpus scale | 1 | 0 |

## Where HGED is (and is not) needed — the scope decision (2026-07-08)

HGED is load-bearing for exactly three things: the **stability theorem** (T-TB,
its right-hand side), the **Layer-1 correlation** that validates the theorem
(T-M5a), and the **head-to-head vs competitors** (the axis on which `d_I` beats
the canonical-form baselines). The **applications — MDS, clustering, kNN,
shortest path (T-M5b–e) — do NOT use HGED**; they self-validate on task metrics
(ARI vs planted labels, accuracy, stress). Consequences:
- The applications can run on **larger real hypergraphs** than the exact-HGED
  ceiling allows — their scale is gated by `w*` (and competitor) wall-clock
  (T-DQ3'), **not** by HGED.
- HGED will be computed on **HPC with high parallelism**, so the exact-oracle
  `n`-ceiling for the density sweep goes **well past n=10** (T-M2 benchmarks it).
  Caveat: T-M2's ceiling table predates the T-M2b Qin re-costing and is stale.
- BP-HGED demotes to an **optional** ladder-cross-check, not a blocker.

## Public code to leverage (standing policy)

**Rule — prefer maintained public code over reimplementation.** Every task that
wraps an existing library MUST use it, not hand-roll. Only two pieces are bespoke
because no library provides them: the **six edit ops**
(`core/sparse_hypergraph.py`, which must match our HGED op-set exactly) and the
**planted-family generator** (encodes the non-isomorphic constraint no library
offers). Everything else is a thin wrapper. Verified repo URLs + licenses are in
`../RELATED_WORK.md` — §Competitors (the four baselines) and §Implementation
dependencies (rapidfuzz, networkx/LijunChang GED scaffolds, sklearn/scipy, HIC).

| Task | Leverage (public code) | Note |
|---|---|---|
| T-M1a | — (structural glue) | mirror the in-repo `iso_backends` ABC/registry pattern |
| T-M1b | **`rapidfuzz`** (C++ Levenshtein) · in-repo `core/hypergraph_wl.py` | raw edit distance primary |
| T-M2 | `scipy.optimize.linear_sum_assignment` (BP-HGED). **No public HGED exists** — read `networkx` `optimize_graph_edit_distance` (A* scaffold, *structure only*) + `LijunChang/Graph_Edit_Distance` (lower bounds) | `ExactHGED` = our own A*/ILP over the six ops on `SparseHypergraph` (OD4 confirmed 2026-07-08) |
| T-M3a | **`pynauty`** + `rapidfuzz` | + in-repo `core/levi_reduction` / `pynauty_levi` |
| T-M3b | **`cosimoagostinelli/Hor_dissimilarity_measures`** (MIT) | vendor with a provenance header |
| T-M3c | **`netlsd`** (`pip install netlsd`, MIT) | |
| T-M3d | **`samirchowdhury/HyperCOT`** (MIT) + `POT` + `hypernetx==1.2` | pinned conda env, subprocess |
| T-M4 | `scipy.stats` (spearmanr/pearsonr) · `sklearn` (MI) · `scipy.linalg.eigh` (classical-MDS solve) | the generator itself is bespoke |
| T-M4' | **`iMoonLab/HIC`** (Apache-2.0) | adapt their dataset loaders |
| T-M5a | `scipy.stats` · `matplotlib` | |
| T-M5b | **`sklearn.manifold.MDS`** (SMACOF) · `scipy` (classical MDS) | |
| T-M5c | **`scikit-learn-extra` `KMedoids`** (or `pyclustering` PAM) · `scipy.cluster.hierarchy` · `sklearn.metrics` | silhouette / DB / ARI / NMI / cophenetic |
| T-M5d | **`sklearn.neighbors.KNeighborsClassifier(metric='precomputed')`** | |
| T-M5e | **`networkx`** / `scipy.sparse.csgraph` | shortest path on the `D`-derived graph |

T-TA / T-TB are proofs (no code). T-M2's `ExactHGED` is the **sole bespoke
algorithm**: the 2026-07-08 search confirmed no public HGED solver exists — we
implement our own A*/ILP over the six ops, scaffolded on `networkx`'s A* loop
(see the T-M2 entry).

## Milestone dependency graph

```
T-M0 ✔ seed optimization (DONE)

T-M1a ✔ metric_space foundation (DONE)
   ├─► T-M1b ✔ d_I + WL distances (DONE)
   │      └─► T-M1c  metric-axiom suite + n=0 domain bug + ablation honesty
   ├─► T-M2  ✔ HGED oracle (DONE; T-M2a/T-M2b Qin unification DONE)
   │      └─► T-M2c  connected-only domain (D-CONN1): generators + LCC   [gates T-M5a]
   ├─► T-M3a..d competitors (nauty-edit / HPD / NetLSD / HyperCOT)
   └─► T-M4   planted-family datasets + scoring primitives

T-M4'  HIC atlas loader (independent) ─► real-anchor apps + gates T-DQ3'

canonical-form track (the metric's foundation):
   T-TA ✔ completeness proof — PI-REVIEWED 2026-07-09 (DONE)
      ├─► T-TAa ✔ C++ tie-complete encoder (DONE)
      ├─► T-TAb ✔ seed-label fingerprint (DONE)
      ├─► T-TAc ✔ WL-pruned variants re-documented + counterexampled (DONE)
      ├─► T-TAe ✔ Levi baselines carry the colour signature (DONE)
      └─► the closing chain, STRICTLY SEQUENTIAL — no parallelism available:
             T-TAf ✔ freeze w*_c (orchestrator, DONE 2026-07-09)
          └► T-TAd ✔ flip the package default to w*_c (orchestrator, DONE 2026-07-09)
          └► T-TAg  harden the canonical surface      (delegable)
          └► T-TAh  remove the unsound wl_colors pruning (shares h2s.cpp with T-TAg)

experiments:
   T-M5a  correlation / density-sweep / info-content   ← M1b, M2, M4     [needs HGED]
   T-M5b MDS · M5c clustering+dendrogram · M5d kNN · M5e shortest-path
                        ← M1b, M3a–d, M4 (+ M4' for the real anchor)      [HGED-free]

theory (parallel):  T-TA ✔ ─► T-TBa restate Lemma B1 over w*_c ─► T-TB stability
last:               T-M6 isomorphisms/ reparent (optional)
```

**Critical path (2026-07-09, post-flip).** T-TAf (freeze) and T-TAd (default
flip) landed 2026-07-09: the package computes the frozen `w*_c` by default and
`d_I` is a metric on isomorphism classes. Remaining on the T-TA chain: T-TAg
(harden the canonical surface) then T-TAh (remove the unsound `wl_colors`
pruning; same worker, shared `h2s.cpp` lane). The article-critical path now
runs through `T-TBa` (restate Lemma B1 over `w*_c`, gating T-TB) and the
T-M5 prerequisites (T-M2c, T-M3a–d, T-M4).

**Runnable in parallel right now:** T-TAg→T-TAh (one worker, strictly after
the flip), T-M2c's P3 decision (theory, no code), T-M4' (HIC loader), T-M3a–d
(competitors). Use isolated git worktrees for agents that touch overlapping
`core/` files.

**The proof review is no longer gated (2026-07-09, T-M0a).** T-M0a suspected the
invalid `gq_2_2_doily` fixture had contaminated `theorem_a_completeness.tex`
Remark 6.1 / §Empirical. It had not: T-TAa measured the *true* doily via
`scripts/bench_tie_complete.py`, and only the true doily reproduces its published
row (61 ms / 1093 ms / 17.8× / `w*_greedy ≠ w*_c`). The proof stands unedited and
the PI may review it. The fixture is fixed and its GQ(2,2) evidence is now pinned
by a regression test rather than a bench script. A sibling defect — the "STS(13)"
fixtures are not Steiner triple systems — is parked as `T-M0c` (naming/citation
only; the objects are still vertex-transitive, which is all Remark 6.1 needs).

Decisions awaiting the PI live in [`DECISIONS.md`](DECISIONS.md).
