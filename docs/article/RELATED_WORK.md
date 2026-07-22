# Related work — verified bibliography

**Status:** ACTIVE (v3 rescope 2026-07-18; verified citations only, from the
2026-07-08 literature-search sweep). Grouped by the role each plays in the
IsalHG argument. Cited from `theoretical/{geometry,stability}.md`,
`empirical/{applications,correlation}.md`. Geometry-pillar citations
(Schoenberg, Bourgain, Khot–Naor, Torgerson, Mardia, Radovanović) are listed
in `theoretical/geometry.md` §9.

## HGED definition (adopt, do not reinvent)

- **Qin, Li, Yuan, Wang, Dai.** "Explainable Hyperlink Prediction: A Hypergraph
  Edit Distance-Based Approach." *ICDE* 2023. DOI:10.1109/ICDE55515.2023.00386.
  — Formal **HGED** with exactly our edit taxonomy (vertex ins/del, hyperedge
  ins/del, vertex/hyperedge label substitution), branch-and-bound solver. Set
  all costs to 1 to recover our combinatorial unit-cost HGED. Our citable HGED
  definition. (No metric-axiom proof, no complexity lower bound — supply
  independently.)
- **Vasilyeva et al.** "Distances in Higher-Order Networks and the Metric
  Structure of Hypergraphs." *Entropy* 25(6):923, 2023. DOI:10.3390/e25060923.
  — Alternative (line-graph) hypergraph distance. Cite to situate HGED among
  competing hypergraph-distance definitions.

## HGED-relation discussion — impossibility scaffold (v3 role)

*(v2 role: proof scaffold for Theorem B. v3 role: these citations ground the
closing discussion — why no bi-Lipschitz proxy exists for complete
canonical-form invariants, and where our drift/avalanche mechanisms sit in the
literature. See PROPOSAL §5.)*

- **Chuang & Jegelka.** "Tree Mover's Distance: Bridging Graph Metrics and
  Stability of GNNs." *NeurIPS* 2022. arXiv:2210.01906. — **The proof template.**
  Bounds a representation distance by a structural graph distance; Lipschitz
  constant factors into depth, width, and (in our terms) `k`, `Δ`. Proof bounds
  the change in the local computation tree by the number of affected edges —
  our single-edit reduction (`stability.md` §2.1) is the hypergraph analogue.
- **Chowdhury, Needham, Semrad, Wang, Zhou.** "Hypergraph co-optimal transport:
  metric and categorical properties." *J. Appl. Comput. Topol.* 7:1–60, 2023.
  arXiv:2112.03904. — Proves the **Levi/bipartite expansion is Lipschitz with an
  arity-`k`-dependent constant**; the clique expansion is 1-Lipschitz. A proved
  piece of our chain; its `C(k)` mirrors our `C(k,Δ)`. (Measure-enriched metric;
  reduction to unit-cost HGED needs care.)
- **Sverdlov, Davidson, Dym, Amir.** "FSW-GNN: A Bi-Lipschitz WL-Equivalent
  GNN." *LoG* 2025. arXiv:2410.09118. — Proves WL-equivalent / canonical-form
  representations are **generically NOT lower-Lipschitz**. Justifies why we prove
  only the **upper** bound; a matching lower bound is provably impossible for
  arbitrary canonical encodings.
- **Chen, Lim, Mémoli, Wan, Wang.** "The Weisfeiler-Lehman Distance." *PMLR*
  221 (TAG-ML @ ICML 2023). arXiv:2302.00713. — WL distance = counts of
  colour/label changes under refinement; the closest published proxy for our
  Levenshtein-on-canonical-string, with a Lipschitz (upper) result. Strongest
  positive precedent for our bound.
- **Gama, Bruna, Ribeiro.** "Stability Properties of GNNs." *IEEE TSP* 68, 2020.
  arXiv:1905.04497. — Methodological template for structural stability theorems
  (right norm on graph space → single-edit change bounded → compose).

## GED lineage and computability (right-hand side of the bound)

- **Riesen & Bunke.** "Approximate GED by bipartite graph matching." *Image Vis.
  Comput.* 27(7):950–959, 2009. DOI:10.1016/j.imavis.2008.04.004. — The
  Riesen–Bunke Hungarian LSAP approximation; our **BP-HGED** mid-scale oracle.
- **Blumenthal, Boria, Gamper, Bougleux, Brun.** "Comparing heuristics for GED."
  *VLDB J.* 29:419–458, 2020. DOI:10.1007/s00778-019-00544-1. — GED-heuristics
  benchmark; notes **approximation error grows with density and symmetry** —
  matches our avalanche/density story (`stability.md` §3–§4).
- **Bunke.** "On a relation between GED and maximum common subgraph." *Pattern
  Recognit. Lett.* 18(8):689–694, 1997. DOI:10.1016/S0167-8655(97)00060-3. —
  `GED = |V1|+|V2|−2|MCS|` under unit costs; a closed-form bound handle.

## MDS embeddability (applications §A1)

- **Bourgain.** "On Lipschitz embedding of finite metric spaces in Hilbert
  space." *Israel J. Math.* 52:46–52, 1985. DOI:10.1007/BF02776078. — Any
  `N`-point metric embeds with `O(log N)` distortion → MDS on `D_I` is
  theoretically justified even absent negative-type.
- **Khot & Naor.** "Nonembeddability theorems via Fourier analysis." *Math. Ann.*
  334:821–852, 2006. DOI:10.1007/s00208-005-0745-0. — **String edit distance
  needs `(log d)^{1/2−o(1)}` L1 distortion** → classical MDS on `D_I` will show
  non-trivial distortion; the caveat to report per corpus (`stability.md` §5).

## Geometry diagnostics (geometry pillar, G1)

- **Radovanović, Nanopoulos, Ivanović.** "Hubs in Space: Popular Nearest
  Neighbors in High-Dimensional Data." *JMLR* 11:2487–2531, 2010.
  (jmlr.org/papers/v11/radovanovic10a.html) — Hubness (`k`-occurrence
  skewness) as the standard diagnostic for nearest-neighbour reliability in
  high-dimensional metric data; the G1 precondition report for kNN (A3).

## Application motivation — practitioner domains (A1–A4)

Citable precedents for the *task* (not for our method) that open each application
subsection in `empirical/applications.md`. Added at T-M8c (2026-07-22).
All seven entries verified 2026-07-22 via CrossRef API
(`api.crossref.org/works/<DOI>`); title, full author list (given and family names),
container title, year, volume, issue, and page/article-id matched field by field
against the CrossRef response.

- **Klamt, S., Haus, U.-U., and Theis, F.** "Hypergraphs and Cellular Networks."
  *PLOS Computational Biology* 5(5):e1000385, 2009. DOI:10.1371/journal.pcbi.1000385.
  — Establishes hypergraph representations of biochemical reaction and signalling
  networks; motivates structural analysis and comparison of module-scale reaction
  hypergraphs (A1 scenario). *Verified 2026-07-22 via CrossRef: title exact;
  authors Steffen Klamt / Utz-Uwe Haus / Fabian Theis; container "PLoS
  Computational Biology"; 2009-05; vol. 5 issue 5 page e1000385.*
- **Benson, A. R., Gleich, D. F., and Leskovec, J.** "Higher-order organization of
  complex networks." *Science* 353(6295):163–166, 2016. DOI:10.1126/science.aad9029.
  — Introduces higher-order motif analysis of complex networks; motivates the task
  of surveying and structurally triaging a corpus of network motifs (A1 scenario).
  *Verified 2026-07-22 via CrossRef: title exact; authors Austin R. Benson /
  David F. Gleich / Jure Leskovec; container "Science"; 2016-07; vol. 353 issue
  6295 pp. 163–166.*
- **Milo, R., Shen-Orr, S., Itzkovitz, S., Kashtan, N., Chklovskii, D., and Alon, U.**
  "Network Motifs: Simple Building Blocks of Complex Networks." *Science*
  298(5594):824–827, 2002. DOI:10.1126/science.298.5594.824.
  — Establishes the systematic study of recurring higher-order structural patterns
  (motifs) in biological networks; directly motivates grouping network modules by
  structural family and selecting structural representatives (A2 scenario).
  *Verified 2026-07-22 via CrossRef: title exact (CrossRef capitalisation:
  "Network Motifs: Simple Building Blocks of Complex Networks"); authors R. Milo /
  S. Shen-Orr / S. Itzkovitz / N. Kashtan / D. Chklovskii / U. Alon (6 authors);
  container "Science"; 2002-10; vol. 298 issue 5594 pp. 824–827.*
- **Newman, M. E. J.** "The structure of scientific collaboration networks."
  *PNAS* 98(2):404–409, 2001. DOI:10.1073/pnas.98.2.404.
  — Establishes co-authorship networks where each paper is a hyperedge over its
  authors; motivates the structural classification of collaboration hypergraphs
  by type (A3 scenario). *Verified 2026-07-22 via CrossRef: title exact; single
  author given as "M." family "Newman" (CrossRef abbreviates given name; standard
  full name M. E. J. Newman); container "Proceedings of the National Academy of
  Sciences"; 2001-01; vol. 98 issue 2 pp. 404–409.*
- **Chodrow, P. S., Veldt, N., and Benson, A. R.** "Generative hypergraph clustering:
  From blockmodels to modularity." *Science Advances* 7(28):eabh1303, 2021.
  DOI:10.1126/sciadv.abh1303.
  — Studies the problem of classifying hypergraphs into structural community types;
  directly motivates the A3 task of assigning an incoming hypergraph to a structural
  class. *Verified 2026-07-22 via CrossRef: title exact; authors Philip S. Chodrow /
  Nate Veldt / Austin R. Benson; container "Science Advances"; 2021-07; vol. 7
  issue 28 article id eabh1303 (no page range; article-id only).*
- **Holme, P. and Saramäki, J.** "Temporal networks." *Physics Reports*
  519(3):97–125, 2012. DOI:10.1016/j.physrep.2012.03.001.
  — The standard review on temporal network analysis; establishes the task of
  comparing two network-state snapshots and tracing the trajectory between them,
  motivating the A4 path-finding scenario. *Verified 2026-07-22 via CrossRef:
  title exact; authors Petter Holme / Jari Saramäki; container "Physics Reports";
  2012-10; vol. 519 issue 3 pp. 97–125.*
- **Battiston, F., Cencetti, G., Iacopini, I., Latora, V., Lucas, M., Patania, A.,
  Young, J.-G., and Petri, G.** "Networks beyond pairwise interactions: Structure
  and dynamics." *Physics Reports* 874:1–92, 2020. DOI:10.1016/j.physrep.2020.05.004.
  — Comprehensive review of higher-order/hypergraph network science, covering
  temporal dynamics of higher-order interactions; motivates tools that track
  structural transitions between hypergraph states (A4 scenario). *Verified
  2026-07-22 via CrossRef: title exact; all 8 authors confirmed: Federico
  Battiston / Giulia Cencetti / Iacopo Iacopini / Vito Latora / Maxime Lucas /
  Alice Patania / Jean-Gabriel Young / Giovanni Petri; container "Physics
  Reports"; 2020-08; vol. 874 pp. 1–92.*

## Distance-matrix → classification/clustering pipeline (applications §A2–A3)

- **Neuhaus & Bunke.** *Bridging the Gap Between GED and Kernel Machines.* World
  Scientific, 2007. DOI:10.1142/6523. — Full pipeline: pairwise edit distance →
  MDS → k-medoids → SVM/kNN → dendrogram. The precedent we port to hypergraphs.
- **Bunke & Riesen.** "Graph Classification Based on Dissimilarity Space
  Embedding." *SSPR/SPR*, LNCS 5342:996–1007, 2008.
  DOI:10.1007/978-3-540-89689-0_103. — Prototype selection by k-medoids on GED,
  then embed + classify. Direct precedent for A2/A3.
- **Fang, Huang, Su, Kasai.** "Wasserstein Graph Distance Based on
  L1-Approximated Tree Edit Distance between WL Subtrees." *AAAI* 2023.
  DOI:10.1609/aaai.v37i6.25916. arXiv:2207.04216. — WL-history-as-string + edit
  distance → graph metric; structurally identical idea one level down.

## Competitor representations (runnable — the baselines we run)

See `COMPETITORS.md` §2 for the chosen set. Code-verified 2026-07-08.

- **HyperCOT — Chowdhury et al.** (already cited above under *stability*):
  *J. Appl. Comput. Topol.* 8:1411–1472, 2024. Code:
  `github.com/samirchowdhury/HyperCOT` (MIT, Python; pins `hypernetx==1.2`,
  `POT==0.8.0`; `O(n³)`/pair). **Dual role:** theory anchor *and* competitor.
- **Agostinelli, Mancastroppa, Barrat.** "Higher-order dissimilarity measures
  for hypergraph comparison." *J. Complex Networks* 14(1):cnaf048, 2026.
  DOI:10.1093/comnet/cnaf048. arXiv:2503.16959. — Hyper-NetSimile (node-local)
  and **Hyperedge Portrait Divergence** (hyperedge-path tensor → Jensen–Shannon);
  relabeling-invariant, size-agnostic. Code:
  `github.com/cosimoagostinelli/Hor_dissimilarity_measures` (MIT, Python/Jupyter;
  extract from notebook). Our second paper+code competitor.
- **Feng, Han, Ying, Gao.** "Hypergraph isomorphism computation." *IEEE TPAMI*
  46(6):3880–3894, 2024. DOI:10.1109/TPAMI.2024.3353199. arXiv:2307.14394. —
  Hypergraph-WL colour refinement + HG-WL subtree / hyperedge kernels; the
  reference for our **hypergraph-WL** standard baseline. Code:
  `github.com/iMoonLab/HIC` (Apache-2.0). (Subtree variant ≈ our WL — don't
  double-count.)
- **Tsitsulin, Mottin, Karras, Bronstein, Müller.** "NetLSD: Hearing the Shape
  of a Graph." *KDD* 2018. DOI:10.1145/3219819.3219991. arXiv:1805.10712. —
  Laplacian heat-trace spectral signature; `pip install netlsd`
  (`github.com/xgfs/netlsd`, MIT). Optional spectral baseline on Levi/clique
  expansion.
- **Redko, Vayer, Flamary, Courty.** "CO-Optimal Transport." *NeurIPS* 2020.
  arXiv:2002.03731. Code: `github.com/PythonOT/POT` (MIT). Foundational co-OT;
  cite alongside HyperCOT.

### Excluded competitors (cite, do not run)

- **Zhang, Du, Feng, Ying, Gao.** "Reinterpreting hypergraph kernels: insights
  through homomorphism analysis." *IEEE TPAMI* early access, 2025.
  DOI:10.1109/TPAMI.2025.3561041. — HGSCKernel, SOTA structural kernel, **no
  code released** ⇒ related-work citation only (matches `docs/engineering/DEVELOPMENT.md`).
- **Lugo-Martínez, Zeiberg, Gaudelet, Malod-Dognin, Pržulj, Radivojac.**
  "Classification in biological networks with hypergraphlet kernels."
  *Bioinformatics* 37(7):1000–1007, 2021. DOI:10.1093/bioinformatics/btaa869. —
  Hypergraphlet orbit kernel; code is C++/BOOST (`tgaudelet/hypergraphlets`
  GPL-3.0 + `jlugomar/hypergraphlet-kernels` MIT), no Python, ~6k orbits ⇒
  impractical as a primary competitor.

## Implementation dependencies (public tooling we leverage)

Non-competitor, non-theory public code the tasks wrap — the standing
"leverage public code" set from `DEVELOPMENT.md` (§Public code to leverage).
Verified repos/licenses; distinct from the scientific citations above.

**Distances & HGED (T-M1b, T-M2).**
- **rapidfuzz** — fast C++ Levenshtein backing `d_I`. `github.com/rapidfuzz/RapidFuzz`
  (PyPI `rapidfuzz`, MIT). pip.
- **NetworkX** `optimize_graph_edit_distance` / `graph_edit_distance` — pure-Python
  A* GED with full custom-cost callbacks; the **A* scaffold for `ExactHGED`
  (structure only** — graph GED ≠ HGED). `github.com/networkx/networkx` (BSD-3). pip.
- **LijunChang/Graph_Edit_Distance** — exact GED via A* with tight lower bounds;
  **reference for the pruning bounds only** (MIT, C++, uniform cost, maintained
  through 2024). `github.com/LijunChang/Graph_Edit_Distance`.
- **GEDLIB / gedlibpy** — C++ GED library (exact + Riesen–Bunke BP + custom costs);
  the code side of Blumenthal et al. (cited under *GED lineage* above).
  `github.com/dbblumenthal/gedlib` (LGPL-3.0) + bindings `github.com/Ryurin/gedlibpy`.
  **Considered and rejected** for `ExactHGED` — it is the Levi-lift route (owes the
  GED-on-Levi = HGED proof, OD4). Listed for completeness.
- **SciPy** `optimize.linear_sum_assignment` — Hungarian assignment for the
  optional BP-HGED. BSD.
- *(optional)* **GMatch4py** — Cython bipartite GED approximation on NetworkX
  graphs; alternative scaffold for the BP-HGED step. `github.com/jacquesfize/GMatch4py`
  (MIT, maintenance uncertain).

**Datasets (T-M4').**
- **iMoonLab/HIC** — HIC atlas, 12 labelled real hypergraph datasets.
  `github.com/iMoonLab/HIC` (Apache-2.0). (Same repo as the HG-WL reference above.)

**Applications & metrics (T-M4, T-M5b–e).**
- **scikit-learn** — `manifold.MDS` (SMACOF), `neighbors.KNeighborsClassifier(metric='precomputed')`,
  `metrics` (silhouette / Davies–Bouldin / ARI / NMI), MI estimators.
  `github.com/scikit-learn/scikit-learn` (BSD-3). pip.
- **scikit-learn-extra** — `cluster.KMedoids` (PAM). PyPI `scikit-learn-extra`
  (BSD-3). **Maintenance caveat:** intermittent sklearn-version compat; fallback
  **pyclustering** (PyPI, BSD-3) or a small in-repo PAM.
- **SciPy** — `cluster.hierarchy` (dendrogram + cophenetic), `sparse.csgraph`
  (A4 shortest path), `linalg.eigh` (classical-MDS solve). BSD.
- **NetworkX** — shortest path for A4 (reused from above). BSD-3.
- **matplotlib** — figures (experiments only). PSF/BSD.
