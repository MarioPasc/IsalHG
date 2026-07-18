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
  SESSIONS.md            orchestrator session plan — checklist, ∥/→ structure,
                         per-session notes (orchestrator-only to edit)
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

- **Run a session** with the `task-orchestrator` skill: it reads
  [`SESSIONS.md`](SESSIONS.md), executes the first unticked session row
  (respecting its ∥ parallel / → sequential structure), verifies and merges
  each worker, then ticks the row and appends to that session's
  "Orchestrator notes" block.
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
| [`T-M2`](T-M2/) | HGED — oracle for E1' + Qin ladder budgets | 0 | 4 |
| [`T-M3`](T-M3/) | Competing representations (5, NetLSD full member) | 0 | 4 |
| [`T-M4`](T-M4/) | Corpora + scoring primitives | 1 | 2 |
| [`T-M5`](T-M5/) | The experiments (body + discussion evidence) | 7 (+1 blocked) | 0 |
| [`T-M6`](T-M6/) | Optional package reparent | 1 | 0 |
| [`T-TA`](T-TA/) | Theorem A — completeness of `w*_c` | 1 | 9 |
| [`T-TB`](T-TB/) | Theorem B — the HGED-relation record | 2 (+1 blocked) | 5 |
| [`T-DQ`](T-DQ/) | Data questions gating corpus scale | 1 | 0 |

## Where HGED is (and is not) needed — the v3 scope decision (D-ART2, 2026-07-18)

Supersedes the 2026-07-08 decision (which kept HGED load-bearing for Theorem B,
the Layer-1 correlation, and the competitor head-to-head). Under D-ART2, the
**oracle** is called in exactly one place: **E1'**, the single ours-only
correlation figure in the closing discussion (T-M5a, small connected
mini-corpus, HPC). The **Qin cost model** (no oracle) prices the
perturbation-ladder budgets that the HGED-free body uses everywhere
(`HGED ≤ budget` by construction): the G2 ladder response (T-M5g) and the A4
path scoring (T-M5e). Everything else — the geometry table, MDS, clustering,
kNN, the sensitivity profiles — never touches HGED and is gated only by `w*_c`
(and competitor) wall-clock (T-DQ3'). Retired at D-ART2: the density sweep,
the competitor HGED head-to-head, MI, and BP-HGED's cross-check role.

## Public code to leverage (standing policy)

**Rule — prefer maintained public code over reimplementation.** Every task that
wraps an existing library MUST use it, not hand-roll. Only two pieces are bespoke
because no library provides them: the **six edit ops + HGED solvers**
(`core/sparse_hypergraph.py` + `metric_space/distances/hged.py`, matching Qin's
op-set exactly) and the **planted-family generator** (encodes the
non-isomorphic constraint no library offers). Everything else is a thin
wrapper. Verified repo URLs + licenses are in `../RELATED_WORK.md` —
§Competitors and §Implementation dependencies.

| Task | Leverage (public code) | Note |
|---|---|---|
| T-M1a | — (structural glue) | mirror the in-repo `iso_backends` ABC/registry pattern |
| T-M1b | **`rapidfuzz`** (C++ Levenshtein) · in-repo `core/hypergraph_wl.py` | raw edit distance primary |
| T-M2 | `scipy.optimize.linear_sum_assignment` (LSAP bounds). **No public HGED exists** — bespoke solvers, DONE | oracle serves E1' only in v3 |
| T-M3a | **`pynauty`** + `rapidfuzz` | + in-repo `core/levi_reduction` / `pynauty_levi` |
| T-M3b | **`cosimoagostinelli/Hor_dissimilarity_measures`** (MIT) | vendor with a provenance header |
| T-M3c | **`netlsd`** (`pip install netlsd`, MIT) | full member since D-ART2 |
| T-M3d | **`samirchowdhury/HyperCOT`** (MIT) + `POT` + `hypernetx==1.2` | pinned conda env, subprocess; small/mid corpora only |
| T-M4 | `scipy.stats` (spearmanr/pearsonr/skew) · `scipy.linalg.eigh` (classical-MDS solve) | the generator itself is bespoke |
| T-M4' | **`iMoonLab/HIC`** (Apache-2.0) | adapt their dataset loaders |
| T-M5a | `scipy.stats` · `matplotlib` | E1' figure + bits table |
| T-M5b | **`sklearn.manifold.MDS`** (SMACOF) · `scipy` (classical MDS) | emits the geometry table |
| T-M5c | **`scikit-learn-extra` `KMedoids`** (or `pyclustering` PAM) · `scipy.cluster.hierarchy` · `sklearn.metrics` | silhouette / DB / ARI / NMI / cophenetic |
| T-M5d | **`sklearn.neighbors.KNeighborsClassifier(metric='precomputed')`** | read against the G1 profile |
| T-M5e | **`networkx`** / `scipy.sparse.csgraph` | shortest path on the `D`-derived graph; S2H decodes intermediates |
| T-M5f/g | `scipy` (eigh, stats) · in-repo edit machinery | geometry helpers + profiles |

T-TA / T-TB are proofs (no code).

## Milestone dependency graph

```
T-M0 ✔ seed optimization (DONE)

T-M1a ✔ metric_space foundation (DONE)
   ├─► T-M1b ✔ d_I + WL distances (DONE)
   │      └─► T-M1c  metric-axiom suite + n=0 domain bug + ablation honesty
   ├─► T-M2  ✔ HGED oracle (DONE; T-M2a/T-M2b Qin unification DONE)
   │      └─► T-M2c ✔ connected-only domain (D-CONN1): generators + LCC
   │                 (DONE 2026-07-09) [gates T-M5a E1' + T-M5g/e ladders — satisfied]
   ├─► T-M3a..d ✔ competitors (nauty-edit / HPD / NetLSD / HyperCOT) (DONE 2026-07-15)
   └─► T-M4 ✔ planted families + scoring primitives (DONE 2026-07-09; v3 deltas —
              geometry-sweep params + `geometry.py` helpers — owned by T-M5f)

T-M4' ✔ HIC atlas loader (DONE 2026-07-09) ─► real anchor + gates T-DQ3'

canonical-form track (the metric's foundation): T-TA ✔ complete (9/9 closed)

the body (HGED-free, characterize → exploit):
   T-M5f  static geometry: helpers + per-corpus table spec   ← M1b ✔, M4 ✔
   T-M5g  sensitivity + ladder profiles (incl. nauty contrast) ← M1b ✔, M2c ✔, M3a ✔, M4 ✔
   T-M5b  MDS flagship + geometry table  ← M1b ✔, M3a–d ✔, M4 ✔, M5f (+ M4' ✔ real)
   T-M5c  clustering + dendrogram · T-M5d kNN (reads G1) ← same
   T-M5e  shortest path (ladder-scored, decoded intermediates) ← M2c ✔, M3a ✔, M5g

discussion evidence (small, last):
   T-M5a  E1' figure (exact HGED, ours only) + bits  ← M1b ✔, M2 ✔, M2c ✔, M4 ✔
          [v2 pipeline executed + closed pre-rescope (`experiments/article/`,
           2026-07-09); that closure is superseded at D-ART2 — see the rescope
           note in T-M5a; T-M5a' (full-scale v2 harvest) parked in BLOCKED/]

theory record (article-facing work done; remainder is housekeeping/stretch):
   T-TB ✔ closed (conditional analysis = the discussion's source)
   T-TBb ✔ closure merged at the S1 reconciliation (T-TBf, 2026-07-18)
   T-TBc BLOCKED (parked at D-ART2, pending PI — transcoding ablation)
   T-TBe stretch (crossing peak; follow-up only) · T-TBg doc disentangle

last:  T-M6 isomorphisms/ reparent (optional)
```

**Critical path (v3, updated at the 2026-07-18 S1 reconciliation merge).** The
canonical-form track is closed and the theory record needs no article-side
work. T-M2c, T-M3a–d, T-M4, and T-M4' all closed pre-rescope (2026-07-09/15)
on the then-main line and were adopted at the reconciliation merge; their v3
deltas (geometry-sweep parameterization, `geometry.py` helpers, NetLSD's
promoted acceptance) are owned by T-M5f and the S2-verification pass. The path
to a submittable body now runs: **T-M5f/T-M5g (the characterization) →
T-M5b–e (the applications)**, with **T-DQ3'** deciding the real anchor's
reach (declared fallback in `DATA.md` §2). T-M5a (discussion evidence) runs
last and small. T-M1c hardens the metric-axiom foundation and should land
before the paper's methods section is drafted.

**Runnable in parallel right now:** T-M1c, T-M5f, T-M5g, T-TBg (+ T-M0b
filler); T-DQ3' is orchestrator-only and unblocked (T-M4' closed). Use
isolated git worktrees for agents that touch overlapping `core/` files.

**Article reframe lineage.** D-ART1 (2026-07-17) moved the headline from the
stability bound to the geometry, keeping HGED-faithfulness as a "capstone"
pillar. **D-ART2 (2026-07-18, PI-RATIFIED same day — `DECISIONS.md`) retired
that pillar**: the article is *characterize → exploit*
(foundation → compactness → geometry → usefulness → discussion), HGED appears
only in the closing discussion (envelope + impossibility + one ours-only
figure), E2b/E3 were recast as HGED-free geometry profiles (T-M5g), NetLSD was
promoted, MI dropped, and T-TBc parked. Scope dirs and task ids unchanged
except: T-M5g added, T-M5a rescoped, T-TBc → BLOCKED. **Convention
(`CLAUDE.md` §Doc split):** reasoning prose lives in
`docs/article/{PROPOSAL,theoretical,empirical}`; engineering tracking (tasks,
`D-*`, statuses, dates) lives here in `DEVELOPMENT/`.

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
