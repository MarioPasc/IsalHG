# Verified literature — the citations the new article may use

*Foundation sheet for the D-ART3 re-scope. Produced 2026-09-03 by a
web-verified literature pass (Semantic Scholar, IEEE Xplore, ACM DL, arXiv,
ScienceDirect, DBLP, JMLR). Only entries whose identifier resolved are listed;
"existence only" means the venue/volume was confirmed but no DOI resolved.
This replaces `../logic_models/related_work.md`, whose entries were flagged
`[unverified]`. Migrate entries to `docs/article/RELATED_WORK.md` only from
here.*

**Novelty verdict (the reason this file exists).**

1. **A canonical-string Levenshtein metric on isomorphism classes of
   (hyper)graphs or relational structures is not in the literature.** gSpan
   uses a canonical string for enumeration, nauty/Traces produce canonical
   labellings with no distance defined on them, HyperCOT is a metric via
   optimal transport. The only hit is our own preprint. *Not pre-empted.*
2. **Consensus (median) of knowledge bases up to isomorphism has not been
   treated.** Distance-based belief merging (Konieczny & Pino Pérez) works over
   interpretations with a fixed, named vocabulary. *Not pre-empted.*
3. **Non-metricity of bipartite GED is in print** (Serratosa 2019). We cite it
   and add an explicit counterexample and a measured violation rate
   (`probes_2026-09.md`), rather than claiming the result.
4. **HyperCOT is a true metric competitor** (Chowdhury et al. 2024) and must be
   engaged directly on per-pair cost, on the need for an external measure, on
   the non-convexity of its computation, and on decodability — not on metric
   axioms.

---

## A. Median / consensus of structures and strings

- **[A1] Jiang, Münger & Bunke.** *On Median Graphs: Properties, Algorithms,
  and Applications.* IEEE TPAMI 23(10):1144–1151, 2001.
  DOI 10.1109/34.954604. Defines the set median (best input) and the
  generalized median (unconstrained minimiser of the sum of distances) and
  proves by the triangle inequality that the set median is a 2-approximation
  of the generalized median. **The citable source for our medoid guarantee;
  the guarantee is standard, not a novelty claim.**
- **[A2] de la Higuera & Casacuberta.** *Topology of Strings: Median String is
  NP-Complete.* Theoretical Computer Science 230(1–2):39–48, 2000.
  DOI 10.1016/S0304-3975(97)00240-5. The generalized median string under edit
  distance is NP-complete. **Our generalized median over `Σ_HG*` inherits
  this hardness; the medoid plus certified search is the practical target.**
- **[A3] Ferrer, Valveny, Serratosa, Riesen & Bunke.** *Generalized Median
  Graph Computation by Means of Graph Embedding in Vector Spaces.* Pattern
  Recognition 43(4):1642–1655, 2010. DOI 10.1016/j.patcog.2009.10.013. Embed
  graphs, take the vector median, reconstruct a graph. **The pipeline whose
  lossy reconstruction step we do not need.**
- **[B1] Konieczny & Pino Pérez.** *Merging Information Under Constraints: A
  Logical Framework.* Journal of Logic and Computation 12(5):773–808, 2002
  (existence verified; DOI unresolved). Distance-based merging operators
  `Δ^d` over interpretations with a fixed vocabulary. **The closest prior
  notion of KB consensus; it is not isomorphism-invariant.**
- Katsuno & Mendelzon, *Propositional knowledge base revision and minimal
  change*, Artificial Intelligence 52:263–294, 1991,
  DOI 10.1016/0004-3702(91)90069-V (verified; the licence for defining a
  belief-change operator by a chosen distance).

## B. Distances between structures and their metric properties

- **[C1] Serratosa.** *Graph Edit Distance: Restrictions to be a Metric.*
  Pattern Recognition 90:250–256, 2019. DOI 10.1016/j.patcog.2019.01.043.
  Bipartite-assignment GED can violate the triangle inequality; metricity of
  GED depends on the cost function. **Cite for the non-metricity of the
  Hungarian pipeline's distance.**
- **[C8] Riesen & Bunke.** *Approximate Graph Edit Distance Computation by
  Means of Bipartite Graph Matching.* Image and Vision Computing
  27(7):950–959, 2009. DOI 10.1016/j.imavis.2008.04.004. The bipartite
  (Hungarian) approximation: an upper bound on GED in `O(n³)` per pair.
- **[C2] Blumenthal, Boria, Gamper, Bougleux & Brun.** *Comparing Heuristics
  for Graph Edit Distance Computation.* VLDB Journal 29(1):419–458, 2020.
  DOI 10.1007/s00778-019-00544-1. All polynomial GED algorithms are heuristics
  without metric guarantees; approximation error grows with density and
  symmetry.
- **[C6] Blumenthal & Gamper.** *On the Exact Computation of the Graph Edit
  Distance.* Pattern Recognition Letters 134:46–57, 2020.
  DOI 10.1016/j.patrec.2018.05.002. Exact GED solvers and their exponential
  behaviour.
- **[C5] Qin, Li, Yuan, Wang & Dai.** *Explainable Hyperlink Prediction: A
  Hypergraph Edit Distance-Based Approach.* ICDE 2023, pp. 245–257,
  DOI 10.1109/ICDE55515.2023.00386 (already in `docs/article/RELATED_WORK.md`).
  Defines HGED (our adopted cost model) and the ego-network derivation
  (Definition 1). In-community prior work for TKDE.
- **[C3] Chowdhury, Needham, Semrad, Wang & Zhou.** *Hypergraph Co-Optimal
  Transport: Metric and Categorical Properties.* Journal of Applied and
  Computational Topology 8:1171–1230, 2024. DOI 10.1007/s41468-023-00142-9,
  arXiv 2112.03904. A metric on (measure-)hypergraph classes via optimal
  transport. **Competitor with a genuine metric; its computation is a
  non-convex transport problem solved to local optima, it needs a probability
  measure on nodes and hyperedges, and it has no decoder.** Previously gated
  at `N ≤ 20` in this project.
- **[C4] Cai, Fürer & Immerman.** *An Optimal Lower Bound on the Number of
  Variables for Graph Identification.* Combinatorica 12(4):389–410, 1992.
  DOI 10.1007/BF01305232. `k`-WL is incomplete for every fixed `k`.
- **[C7] Huang & Yang.** *UniGNN: A Unified Framework for Graph and
  Hypergraph Neural Networks.* IJCAI 2021, pp. 2563–2569, arXiv 2105.00956.
  Message-passing hypergraph networks are bounded by generalized WL, hence
  incomplete. (Feng et al. HGNN, AAAI 2019, DOI 10.1609/aaai.v33i01.33013558,
  and Morris et al. k-GNN, AAAI 2019, DOI 10.1609/aaai.v33i01.33014602, are
  verified and subsumed.)
- Already verified in `docs/article/RELATED_WORK.md` and reusable: Sverdlov et
  al., *FSW-GNN* (LoG 2025, arXiv 2410.09118 — canonical/WL representations
  are generically not lower-Lipschitz); Chen et al., *The Weisfeiler–Lehman
  Distance* (TAG-ML @ ICML 2023, arXiv 2302.00713); Bourgain 1985
  (DOI 10.1007/BF02776078); Khot & Naor 2006 (DOI 10.1007/s00208-005-0745-0);
  Marzal & Vidal, IEEE TPAMI 15(9), 1993 (normalized edit distance is not a
  metric).

## C. Metric-space analytics (the toolkit's own literature)

- **[D1] Chávez, Navarro, Baeza-Yates & Marroquín.** *Searching in Metric
  Spaces.* ACM Computing Surveys 33(3):273–321, 2001.
  DOI 10.1145/502807.502808. Intrinsic dimensionality `ρ = μ²/(2σ²)` of the
  distance histogram; the venue's own vocabulary for "how indexable is this
  space".
- **[D2] Radovanović, Nanopoulos & Ivanović.** *Hubs in Space: Popular
  Nearest Neighbors in High-Dimensional Data.* JMLR 11:2487–2531, 2010.
  Hubness (`k`-occurrence skewness); licenses the kNN-based outlier scores.
- Schubert & Rousseeuw, *Fast and eager k-medoids clustering* (FasterPAM),
  Information Systems 101:101804, 2021, DOI 10.1016/j.is.2021.101804
  (implementation reference for PAM).
- Sokal & Rohlf, cophenetic correlation, Taxon 11:33–40, 1962,
  DOI 10.2307/1217208 (dendrogram fidelity).
- Pękalska & Duin, *The Dissimilarity Representation for Pattern
  Recognition*, World Scientific 2005, ISBN 9789812565303 (non-Euclidean
  dissimilarities, negative eigenfractions).
- Still to verify before use: Knorr & Ng (distance-based outliers, VLDB
  1998); Breunig et al. (LOF, SIGMOD 2000); Kaufman & Rousseeuw (PAM, 1990);
  de Leeuw (SMACOF); Torgerson (classical MDS); the median-string
  approximation algorithms (Kohonen 1985; Martínez-Hinarejos et al.;
  Casacuberta & de Antonio). None of these is load-bearing for a claim.

## D. Data

- **[F1] Galkin, Trivedi, Maheshwari, Usbeck & Lehmann.** *Message Passing
  for Hyper-Relational Knowledge Graphs.* EMNLP 2020,
  DOI 10.18653/v1/2020.emnlp-main.596. Introduces WD50K: Wikidata statements
  with qualifiers, i.e. **n-ary ground facts = labelled hyperedges**. The
  candidate "KB-shaped" real corpus beyond ARB. (Rosso et al., HINGE, WWW 2020,
  DOI 10.1145/3366423.3380257, verified; alternative datasets JF17K/FB-AUTO.)
- Benson, Gleich & Leskovec, *Higher-order organization of complex networks*,
  Science 353:163–166, 2016, DOI 10.1126/science.aad9029 (verified); the ARB
  collection itself is cited through Benson et al., PNAS 2018 (already in
  `docs/article/RELATED_WORK.md`).

## E. Positioning only

- **[G1] Yan & Han.** *gSpan: Graph-Based Substructure Pattern Mining.* ICDM
  2002, DOI 10.1109/ICDM.2002.1184038. A canonical string (minimum DFS code)
  used as pattern identity for enumeration — not as a metric.
- **[G2] McKay & Piperno.** *Practical Graph Isomorphism, II.* Journal of
  Symbolic Computation 60:94–112, 2014, DOI 10.1016/j.jsc.2013.09.003.
  Canonical labellings; no distance on certificates is defined.
- Junttila & Kaski, bliss, ALENEX 2007 (existence verified; DOI unresolved).
