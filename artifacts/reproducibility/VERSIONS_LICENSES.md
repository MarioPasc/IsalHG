# Dependencies, versions, and licenses

Exact lockfiles in this directory:
- `isalhg_env.lock.txt` — `conda list --explicit` for the main `isalhg` env.
- `isalhg_hypercot_env.lock.txt` — the pinned HyperCOT env (subprocess-isolated;
  `hypernetx==1.2` + POT, incompatible with the main env's `hypernetx==2.4`).
- `isalhg_pip_freeze.txt` — portable `pip freeze` fallback for the main env.

## Core scientific stack (main env, measured 2026-07-25)

| Package | Version | Role |
|---|---|---|
| numpy | 2.4.6 | arrays, D-matrix algebra |
| scipy | 1.17.1 | `bootstrap` (BCa), `wilcoxon`, `eigh`, `linear_sum_assignment` |
| scikit-learn | 1.9.0 | `MDS` (SMACOF), `KNeighborsClassifier`, metrics |
| networkx | 3.6.1 | shortest path (A4) |
| matplotlib | 3.11.0 | figures |
| hypernetx | 2.4.0 | adapter (main env) |
| xgi | 0.10.2 | dataset loaders |

## Competitor + tooling dependencies (public code we leverage)

| Component | Version | License | Source | Use |
|---|---|---|---|---|
| rapidfuzz | 3.14.5 | MIT | PyPI `rapidfuzz` | C++ Levenshtein for `d_I` |
| pynauty | 2.8.8.1 | (nauty license) | PyPI `pynauty` | iso oracle + nauty-Levi competitor |
| netlsd | 1.0.2 | MIT | `github.com/xgfs/netlsd` | NetLSD competitor (full member) |
| HPD (vendored) | vendored subtree | MIT | `github.com/cosimoagostinelli/Hor_dissimilarity_measures` | Hyperedge Portrait Divergence competitor |
| HyperCOT | pinned env | MIT | `github.com/samirchowdhury/HyperCOT` | co-optimal-transport competitor (subprocess; small/mid corpora) |
| POT | (hypercot env) | MIT | `github.com/PythonOT/POT` | transport solver for HyperCOT |
| HIC loaders | — | Apache-2.0 | `github.com/iMoonLab/HIC` | real-anchor candidate loaders |

**HPD provenance.** The vendored HPD code carries a provenance header in
`src/isalhg/metric_space/representations/_hpd_vendor.py` citing the MIT-licensed
upstream. All licenses above are permissive (MIT / Apache-2.0) and compatible
with redistribution in the artifact.

## Bespoke components (no public equivalent exists)

- The six Qin edit ops + HGED solvers (`core/sparse_hypergraph.py`,
  `metric_space/distances/hged.py`) — match Qin's op-set exactly.
- The planted-family generator (`datasets/synthetic/planted_families.py`) —
  encodes the non-isomorphic-within-class constraint no library provides.
