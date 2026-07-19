# Running the competing representations — downstream usage guide

**Audience.** Anyone running the metric-space study (correlation vs HGED,
MDS / clustering / kNN / shortest-path applications) or otherwise needing a
pairwise dissimilarity matrix on a corpus of hypergraphs. This is the *how to
invoke* companion to `COMPETITORS.md` (the *why these four* design rationale)
and `RELATED_WORK.md` §Competitors (citations, code URLs, licenses).

Every competitor and our own method expose the **same interface**
(`HypergraphDistance`) and are reached the **same way** (the distance registry),
so switching representation is a one-line change. All results below are
reproducible on `main` as of 2026-07-19; `scripts/verify_competitors.py`
re-runs the full six-representation check (planted corpus, 18 hypergraphs,
5 planted iso pairs → distance 0 for every representation; the complete
invariants separate all non-isomorphic pairs).

---

## 1. TL;DR — quick start

```python
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.metric_space.registry import get_distance, available_distances

def hg(n, edges):  # minimal unlabelled hypergraph
    return SparseHypergraph(
        n_nodes=n,
        hyperedges=[frozenset(e) for e in edges],
        n_vertex_labels=1, n_edge_labels=1,
        vertex_labels=[0] * n, edge_labels=[0] * len(edges),
    )

corpus = [
    hg(4, [[0, 1, 2], [1, 2, 3]]),   # 0
    hg(4, [[0, 1, 2], [1, 2, 3]]),   # 1  (isomorphic to 0)
    hg(5, [[0, 1, 2], [2, 3, 4]]),   # 2
]

D = get_distance("isalhg_levenshtein").matrix(corpus)   # our method d_I
print(D)                                                 # symmetric, zero diagonal
```

`get_distance(name)` returns a ready-to-use `HypergraphDistance`. Its
`matrix(corpus)` returns a dense symmetric `numpy.ndarray` with a zero diagonal.
Swap `name` for any entry from `available_distances()` to run a competitor
through the identical pipeline.

Observed on the corpus above (distance between item 0 and item 2):

| name | d(0,1) iso pair | d(0,2) | complete invariant? |
|---|---|---|---|
| `isalhg_levenshtein` (ours) | 0 | 2 | yes (`w*_c`) |
| `nauty_levi_edit` (contrast) | 0 | 15 | yes |
| `hypergraph_wl_l1` | 0 | 9 | no (pseudometric) |
| `netlsd_l2` | 0 | 0.191 | no |
| `hpd_jsd` | 0 | 0 | no |

The zero on the isomorphic pair `(0,1)` holds for **every** representation (all
are isomorphism-invariant). The zero that `hpd_jsd` returns on the
*non*-isomorphic pair `(0,2)` is not a bug: HPD, WL and NetLSD are
**pseudometrics** — they can map distinct isomorphism classes to distance 0.
Only `isalhg_levenshtein` (over the frozen `w*_c`) and `nauty_levi_edit` are
complete invariants (distance 0 ⟺ isomorphic). Pick accordingly.

---

## 2. The uniform interface — `HypergraphDistance`

`src/isalhg/metric_space/base.py`. Every distance subclasses it:

| Member | Signature | Notes |
|---|---|---|
| `name` | `-> str` | the registry key |
| `pairwise(H1, H2)` | `-> float` | non-negative dissimilarity; `0` iff the representation cannot separate the two |
| `matrix(corpus)` | `-> np.ndarray` | dense symmetric `(N, N)` `float64`, zero diagonal; overridden where a whole-corpus computation is cheaper |
| `fingerprint(H)` | `-> Any \| None` | optional per-hypergraph summary that amortizes `matrix` (canonical string, WL histogram, spectral signature); `None` when not applicable |

Every consumer uses a registered distance identically: the applications
(MDS, clustering, kNN, shortest path) and the geometry table all read
`D.matrix(corpus)`. HGED enters the paper only through the single ours-only
discussion figure E1' (`d_I` vs `exact_hged` on the mini-corpus); there is no
competitor HGED head-to-head (retired at D-ART2).

---

## 3. The registry

`src/isalhg/metric_space/registry.py`.

```python
from isalhg.metric_space.registry import get_distance, available_distances

available_distances()
# ('bipartite_hged', 'exact_hged', 'hpd_jsd', 'hypercot',
#  'hypergraph_wl_chi2', 'hypergraph_wl_l1', 'isalhg_levenshtein',
#  'nauty_levi_edit', 'netlsd_l2', 'qin_hged')

d = get_distance("hpd_jsd")     # lazy-imports the module; instantiates the distance
```

Lookups are lazy: the module backing a name is imported only when that name is
requested, so an unusable optional dependency (`netlsd` not installed, the
HyperCOT env absent) never breaks `import isalhg`. A missing dependency surfaces
only when you actually *call* the distance, as a typed error (below).

To construct a distance with non-default options, import its class directly
instead of using the registry (see each entry's *Options* below).

---

## 4. Catalogue

Registered names split into three roles.

### 4.1 Our method

| name | class | computes | distance |
|---|---|---|---|
| `isalhg_levenshtein` | `IsalHGLevenshtein` | canonical H2S string `w*_c(H)` | raw Levenshtein (via `rapidfuzz`) |

### 4.2 Competitors (the five in the study)

| name | class | representation | distance | role | optional dep |
|---|---|---|---|---|---|
| `hypergraph_wl_l1` / `hypergraph_wl_chi2` | `HypergraphWLDistance` | hypergraph-WL colour histogram (Feng et al., TPAMI 2024) | L1 / symmetric χ² | fair standard | — (numpy) |
| `nauty_levi_edit` | `NautyLeviEditDistance` | nauty canonical form of the Levi graph | byte Levenshtein | **contrast** (iso-only, no navigable geometry) | `pynauty`, `rapidfuzz` |
| `hpd_jsd` | `HPDDistance` | hyperedge-portrait tensor (Agostinelli et al., JCN 2026) | Jensen–Shannon (√JS = metric) | fair, hyperedge-path-centric | numpy/scipy |
| `hypercot` | `HyperCOTDistance` | hypergraph co-optimal transport (Chowdhury et al., JACT 2024) | transport cost (metric by construction) | fair, mass-transport | **pinned conda env** (§6) |
| `netlsd_l2` | `NetLSDDistance` | NetLSD heat-trace of the Levi expansion (Tsitsulin et al., KDD 2018) | L2 | fair, spectral — **full member** (promoted at D-ART2: the guaranteed at-scale baseline where HyperCOT's `O(n³)`/pair cannot reach) | `netlsd` |

### 4.3 Ground-truth structural distance (discussion figure E1' only)

| name | class | notes |
|---|---|---|
| `exact_hged` | `ExactHGED` | exact HyperGraph Edit Distance (A*/ILP over the six unit ops); small `n` |
| `bipartite_hged` | `BipartiteHGED` | Riesen–Bunke bipartite upper bound; mid-scale |
| `qin_hged` | `QinHGED` | Qin et al. HGED-BFS; fidelity anchor |

HGED is **not** used by the applications (MDS/clustering/kNN/shortest-path) —
those self-validate on task metrics and run at larger scale.

---

## 5. Per-competitor details

### `isalhg_levenshtein` (ours)
Complete invariant over the frozen `w*_c`. Options via the class:
`IsalHGLevenshtein(...)` supports raw vs length-normalized/token-aware costs as
constructor kwargs (raw is the study default; the others are the ablation row).

### `hypergraph_wl_l1` / `hypergraph_wl_chi2`
`HypergraphWLDistance(*, metric="l1"|"chi2", max_rounds=None, backend=None)`.
WL is run **once on the disjoint union** of the corpus so colours are comparable
across graphs (a shared structural role gets the same colour) — this is what
keeps the baseline fair rather than a strawman. Registered factories fix
`metric`; pass `max_rounds`/`backend` by importing the class.

### `nauty_levi_edit` (the deliberate contrast)
`NautyLeviEditDistance()`. Fingerprint =
`LeviGraph.color_signature() ++ bytes(pynauty.certificate(B(H)))`, matching
`PynautyLeviBackend.fingerprint`; distance = raw byte Levenshtein. Included to
*demonstrate* that iso-only canonical labelling yields no navigable geometry
(one edit can permute the whole labelling) — expect low HGED-correlation; that
is the scientific point, not a defect. It structurally cannot do application A4
(shortest path). Needs `pynauty`; raises `RepresentationDependencyMissingError`
if absent.

### `hpd_jsd`
`HPDDistance(*, sqrt_js=True)`. Default returns √JS (a proper metric); set
`sqrt_js=False` for raw JS divergence. Pseudometric (see §1). numpy/scipy only.

### `netlsd_l2`
`NetLSDDistance(*, timescales=None)`. L2 between NetLSD heat-trace signatures of
the Levi expansion. **Spectral**, so the iso-pair distance is ~1e-9 (numerical),
not exactly 0 — assert with a tolerance. Install: `pip install netlsd`
(missing ⇒ `RepresentationDependencyMissingError`).

### `hypercot`
`HyperCOTDistance(timeout_s=None)`. Runs upstream HyperCOT **unmodified** in an
isolated version-pinned conda env via subprocess (§6). A metric by construction.
If the env is absent, raises `SubprocessRepresentationError` with a setup hint;
the guard path is always exercised, the end-to-end tests are `@pytest.mark.slow`.

---

## 6. HyperCOT — the pinned-environment competitor

HyperCOT pins `hypernetx==1.2` + `POT==0.8.0`, incompatible with the main
`isalhg` env, so it lives in a **separate conda env** (`isalhg-hypercot`) that
`HyperCOTDistance` shells out to. The only code we author is the
serialize→subprocess→parse glue (`subprocess_base.py` + `scripts/hypercot_worker.py`);
HyperCOT itself runs as upstream code.

**Build the env once** (needs network; spec + rationale in `envs/hypercot.yml`):

```bash
conda create -y -n isalhg-hypercot python=3.10
~/.conda/envs/isalhg-hypercot/bin/pip install \
    numpy==1.23.5 scipy==1.9.3 POT==0.8.0 hypernetx==1.2 \
    networkx==2.8.8 "pandas<2.1" celluloid decorator igraph \
    scikit-learn matplotlib plotly
git clone https://github.com/samirchowdhury/HyperCOT /tmp/HyperCOT   # MIT
# HyperCOT has NO setup.py — copy its two modules into site-packages:
cp /tmp/HyperCOT/cot.py /tmp/HyperCOT/hypercot.py \
    "$(~/.conda/envs/isalhg-hypercot/bin/python -c 'import site; print(site.getsitepackages()[0])')/"
```

Version pins are load-bearing: `scipy==1.9.3` because POT 0.8.0 imports
`scipy.optimize.linesearch.scalar_search_armijo` (removed in scipy ≥ 1.10);
`numpy<1.24` because `hypercot.get_omega` uses integer array indexing NumPy 1.24
rejects; `networkx<3` for HyperNetX 1.2. Upstream HEAD is
`5045539ac1465626f985813aabcf89489d5c98a4` (2023-01-19; the repo is static —
verified at the 2026-07-19 env rebuild, and pinned in the
`scripts/hypercot_worker.py` header).

**Then use it exactly like any other distance:**

```python
D = get_distance("hypercot").matrix(corpus)   # spawns isalhg-hypercot per matrix() call
```

The worker builds each hypergraph in HyperCOT's convention (nodes `"0".."n-1"`,
edges `0..m-1`), computes `get_hgraph_dual → convert_to_line_graph → get_v →
get_omega(..., "jaccard_index")`, then `cot.cot_numpy(...)` per pair. Verified:
self-distance 0, cross-distance > 0.

---

## 7. Building a corpus

`matrix()` / `pairwise()` take any sequence of `SparseHypergraph`. Three ways to
get one:

**A. Hand-built** — see §1 (`hg(...)`), good for tests and sanity checks.

**B. Synthetic datasets** — via the dataset registry
(`isalhg.datasets.registry.get_dataset`); each yields `DatasetItem`s whose
`.hypergraph` is a `SparseHypergraph`:

```python
from isalhg.datasets.registry import get_dataset
ds = get_dataset("correlation_corpus", {...})          # or planted_families, symmetric_designs, ...
corpus = [item.hypergraph for item in ds]
```

**C. Real HIC hypergraphs** — the 12-dataset atlas (Feng et al. 2024,
Apache-2.0). Point it at the data root and pick a dataset by name:

```python
from pathlib import Path
from isalhg.datasets.hic_atlas import HICAtlasDataset

HIC_ROOT = Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/data/HIC/data/hypergraph")
ds = HICAtlasDataset(root=HIC_ROOT, hic_name="RHG-10")   # loads, extracts largest connected component
corpus = [item.hypergraph for item in ds][:20]           # cap for a quick run
D = get_distance("hpd_jsd").matrix(corpus)
```

Valid `hic_name` values: `RHG-10`, `RHG-3`, `RHG-Table`, `RHG-Pyramid`,
`IMDB-Dir-Form`, `IMDB-Dir-Genre`, `IMDB-Dir-Genre-M`, `IMDB-Wri-Form`,
`IMDB-Wri-Genre`, `IMDB-Wri-Genre-M`, `Steam-Player`, `Twitter-Friend`.

---

## 8. End-to-end: one corpus, all representations

```python
from isalhg.metric_space.registry import get_distance

reps = ["isalhg_levenshtein", "hypergraph_wl_l1", "nauty_levi_edit",
        "hpd_jsd", "netlsd_l2", "hypercot"]        # drop 'hypercot' if env not built

mats = {name: get_distance(name).matrix(corpus) for name in reps}

# E1' (discussion figure): rho between d_I and exact HGED on the mini-corpus.
# Ours-only in the paper — no competitor rows (D-ART2).
from scipy.stats import spearmanr
import numpy as np
Dtrue = get_distance("exact_hged").matrix(corpus)
iu = np.triu_indices(len(corpus), k=1)
rho, _ = spearmanr(mats["isalhg_levenshtein"][iu], Dtrue[iu])
print(f"E1': rho(d_I, HGED) = {rho:.3f}")
```

---

## 9. Environment summary

| Distance | Extra install | Failure mode if missing |
|---|---|---|
| `isalhg_levenshtein`, `hypergraph_wl_*`, `hpd_jsd` | none beyond the `isalhg` env (numpy/scipy/rapidfuzz) | — |
| `nauty_levi_edit` | `pynauty` (already in `isalhg`) | `RepresentationDependencyMissingError` |
| `netlsd_l2` | `pip install netlsd` | `RepresentationDependencyMissingError` |
| `hypercot` | the `isalhg-hypercot` conda env (§6) | `SubprocessRepresentationError` (with build hint) |
| `exact_hged` / `bipartite_hged` / `qin_hged` | none | — |

Missing deps degrade **gracefully**: `import isalhg` and every other distance
keep working; only the specific distance you call raises.

---

## 10. Provenance & licensing (transparency)

We use each external method's own published code, unmodified where run directly:

- **HPD** — vendored verbatim (MIT) into
  `src/isalhg/metric_space/representations/_hpd_vendor.py`, whose header records
  the source repo (`cosimoagostinelli/Hor_dissimilarity_measures`), commit
  `f190266`, retrieval date, full MIT license, the four functions copied (with
  upstream line numbers), and every adaptation. The vendored function bodies are
  AST-identical to upstream.
- **HyperCOT** — run unmodified (MIT, `samirchowdhury/HyperCOT`) in its own
  pinned env; only our serialize/parse glue is authored (§6).
- **nauty** — via the `pynauty` binding (nauty, McKay & Piperno).
- **NetLSD** — via the `netlsd` PyPI package (MIT, `xgfs/netlsd`).
- **hypergraph-WL** — our reimplementation of the Feng et al. HG-WL refinement
  in `core/hypergraph_wl.py` (the one competitor we implement, since it is the
  standard baseline and no drop-in library matches our incidence convention).

Full citations and URLs: `RELATED_WORK.md` §Competitors.

---

## 11. Code map

| Path | Holds |
|---|---|
| `src/isalhg/metric_space/base.py` | `HypergraphDistance` ABC |
| `src/isalhg/metric_space/registry.py` | `get_distance` / `available_distances` |
| `src/isalhg/metric_space/representations/wl.py` | `HypergraphWLDistance` |
| `src/isalhg/metric_space/representations/nauty_levi_edit.py` | `NautyLeviEditDistance` |
| `src/isalhg/metric_space/representations/hpd.py` + `_hpd_vendor.py` | `HPDDistance` + vendored HPD |
| `src/isalhg/metric_space/representations/netlsd.py` | `NetLSDDistance` |
| `src/isalhg/metric_space/representations/hypercot.py` + `subprocess_base.py` | `HyperCOTDistance` + subprocess base |
| `scripts/hypercot_worker.py` | HyperCOT subprocess worker (runs in `isalhg-hypercot`) |
| `envs/hypercot.yml` | pinned HyperCOT env spec + build recipe |
| `src/isalhg/metric_space/distances/{isalhg_levenshtein,hged,qin_hged}.py` | our `d_I` + the HGED oracles |
