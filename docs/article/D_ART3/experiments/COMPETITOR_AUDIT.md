# Competitor audit — the distance arms on labelled knowledge bases

**Read this first, if you are writing a runner.** Neither labelled collection
carries both label kinds. `wd50k66` has `n_types = 1` and `n_preds = 351`
(edge labels only); `ndc_classes` has `n_types = 4` and `n_preds = 1` (vertex
labels only). Each label kind is therefore exercised on exactly one real
collection, and any test that needs *both* kinds non-trivial must use a
synthetic hypergraph. This is a property of the frozen corpora, not of the
representations.

Every earlier IsalHG corpus was unlabelled. RQ2, RQ4 and RQ5 compare `fact_rank`
against these competitors on labelled real collections that none of them had
ever run on, so the first question a reviewer will ask is whether a competitor
is quietly ignoring the predicates — which would make the comparison unfair in
our favour. This document answers that question with measurements rather than
with readings of the source.

## 1. What was measured, and how

For each registered arm, on 200 members of `wd50k66` and 200 of `ndc_classes`:

- **finiteness** — `pairwise` on 500 random member pairs (seed 0), counting
  non-finite results and exceptions;
- **false merges** — among those pairs that are non-isomorphic by the `pynauty`
  Levi fingerprint, how many the arm places at distance 0 (`|d| < 10⁻⁹`);
- **exactness at zero** — 100 isomorphic pairs built with
  `permute(H, σ)` under a shuffled σ, counting how many return 0;
- **median wall-clock per pair.**

Arms are given a hard wall-clock budget per collection; an arm that exceeds it
stops early and the untried pairs are reported as censored rather than silently
dropped. `fact_rank_roles` refuses `pairwise` by design — a `SparseHypergraph`
carries no roles, and answering would silently return the role-free distance,
making the ablation secretly identical to the primary arm — so it is listed
without a row of numbers.

Reproduction: `registry.available_distances()` for the arm list,
`experiments.tkde.corpora.load_collection` for the members,
`isalhg.core.sparse_hypergraph.permute` for the isomorphic pairs.

## 2. The label declarations

Every distance class now carries `labels_used: frozenset[str] ⊆ {"vertex",
"edge"}` (default: the empty set, on the `HypergraphDistance` ABC), and
`registry.labels_used(name)` reads it. The declarations are **measured, not
asserted**: `tests/unit/metric_space/test_representations_kb.py` relabels one
vertex and one hyperedge of a fixed doubly-labelled probe and requires the
distance to move for exactly the kinds the arm declares, and not to move for the
kinds it does not. A declaration cannot drift from behaviour in either
direction without the suite failing.

**Both label kinds** — `fact_rank`, `fact_rank_roles`, `fact_local_colour`,
`fact_local_key`, `fact_degree_key`, `isalhg_levenshtein`,
`nauty_levi_edit`/`nauty_cert`, `nauty_cert_rows`, `hypergraph_wl_l1`,
`hypergraph_wl_chi2`, `exact_hged`, `bipartite_hged`/`bipartite_ged_path`,
`qin_hged`.
**Vertex only** — `bipartite_ged_assign`.
**Label-blind** — `netlsd_l2`, `hpd_jsd`, `hypercot`, `size_l1`,
`degree_seq_l1`.

**No arm needed a wiring fix to see labels, and the four label-blind
competitors are blind by method, not by defect.** No label term was faked for
any of them.

## 3. Per-arm findings

**`fact_rank` / `fact_rank_roles` (ours).** Both kinds, and both written
explicitly into the word rather than inferred: the type prefix emits one
`("T", type)` token per constant, and every fact token is
`("F", predicate, operands)`. Unchanged by this audit. The roles arm reads a
third kind of information — the argument role of each incidence — that no
competitor sees at all, which is exactly why the primary arm on every table is
the role-free one: the comparison must be information-matched.

**`isalhg_levenshtein` (pointer).** Both kinds, through two mechanisms that are
worth stating because the `Σ_HG` alphabet appears at first sight to have no
label fields. A `V` token is `V[edge_label; i; j; new vertex labels]`, so every
predicate, and the type of every constant introduced by a fact, is written into
the string. The one constant no `V` token introduces is the seed, whose type
arrives through the `("seed", label)` prefix that Corollary A prepends (emitted
only when `n_vertex_labels > 1`). Between them, every label of a connected
input is recorded. **Caveat for the runners:** this arm raises
`DisconnectedHypergraphError` on disconnected input (decision B11). All 400
audited real members are connected, so it is safe on the frozen corpora — but
the fact language permits disconnected knowledge bases, so decoded or generated
objects must not be fed to it.

**`nauty_levi_edit` / `nauty_cert`.** Both kinds. `to_levi` colours a constant
node with its type and a fact node with `|Σ_V| + predicate`, so both label kinds
reach nauty through the colouring, and `color_signature` restores the absolute
colour identity that the ordered partition drops. Unchanged; `nauty_cert`
added as an alias.

**`nauty_cert_rows` (new).** Both kinds. The second tokenization of the *same*
canonical form: one symbol per Levi node — the row
`(colour, *sorted canonical positions of the neighbours)` — instead of one
symbol per certificate byte. Because both arms read one canonical form, any
difference between their distances is attributable to the tokenization alone,
which is what makes this the supplementary ablation of the certificate member
rather than an independent competitor. The colour travels inside each row, so
equal row sequences determine the whole *coloured* canonical graph: the arm is
exact at zero, and the tests confirm it agrees with `nauty_cert` on the
isomorphism partition pair-for-pair.

**`hypergraph_wl_l1` / `hypergraph_wl_chi2`.** Both kinds, verified on both the
`cpp` and `python` backends: `wl_hash` seeds each vertex colour with
`H.vertex_label(v)` and mixes `H.edge_label(e)` into every edge signature, so
labels enter the refinement from round 0. Unchanged; `wl_l1` added as an alias.

**`exact_hged` / `exact_ged`, `qin_hged`.** Both kinds, with labelled unit
costs already in place: `_vertex_cost` charges 1 for each matched vertex pair
whose types differ, and the substitution block of `_edge_cost` adds 1 to a
matched edge pair whose predicates differ. `qin_hged` gained only its
declaration. Both are NP-hard and are the audit's censoring cases on real
members.

**`bipartite_hged` / `bipartite_ged_path`, and `bipartite_ged_assign` (new).**
The literature reports two different numbers under the name "bipartite graph
edit distance", and RQ2 needs both because they fail differently.
*The edit-path reading* (`bipartite_ged_path`, the existing `bipartite_hged`)
fixes the Riesen–Bunke vertex correspondence and re-prices it as an actual edit
with the same labelled unit costs as the exact oracle; it therefore
upper-bounds that oracle, and the tests check this on real pairs.
*The raw assignment reading* (`bipartite_ged_assign`) returns the LSAP's own
optimum, whose substitution block scores a matched pair by
`[types differ] + |deg(u) − deg(v)|`. That is not an edit cost — the degree
proxy is a stand-in for structure, not a count of operations — so it neither
bounds the exact distance nor vanishes only on isomorphic pairs. It has
**false zeros** by construction: nothing in its matrix records *which* vertices
share a hyperedge, so any two hypergraphs whose vertices pair up with matching
types and equal degrees score 0. A minimal witness is pinned by test (two
3-facts sharing a vertex pair versus a 3-edge path, both with degree sequence
`[2, 2, 1, 1]`). It reads vertex types but no predicate appears anywhere in its
matrix, hence `labels_used = {"vertex"}`.

**`netlsd_l2` / `netlsd`.** Label-blind, and not fixably so. The heat trace is
a function of the Laplacian spectrum of the *uncoloured* Levi graph, and NetLSD
defines no coloured variant, so `_levi_to_scipy_adj` keeps `levi.edges` and
drops `levi.colors`. Two knowledge bases differing only in their types or
predicates receive distance 0. Note also that NetLSD is a spectral invariant
computed in floating point: isomorphic pairs land at ~10⁻¹⁵, not exactly 0.

**`hpd_jsd`.** Label-blind on both sides of the pipeline: `XGIAdapter`
carries members only (the XGI hypergraph it builds has empty node attributes),
and the hyperedge portrait itself indexes purely on hyperedge *cardinality* and
line-graph distance, so there is no slot for a type or a predicate even if the
adapter carried them. Adding one would be a new method, not a wiring fix.

**`hypercot`.** Label-blind. The subprocess payload carries `vertex_labels`,
but the worker never reads them: it builds
`hnx.Hypergraph({edge_int: members})` and hands HyperCOT the incidence
structure with uniform vertex and hyperedge measures. Co-optimal transport is
defined on those measures and the incidence matrix and has no label term, so
the payload field is vestigial. **One measured hazard for the matrix builder:**
the cost is a numerical optimum, not an exact count, and on an isomorphic pair
it returned **−9.9 × 10⁻¹⁶** — a small *negative* number. Any downstream
`sqrt`, or a non-negativity assertion, will fail on a correct result. Clamp at
zero and compare with a tolerance. Pinned by test.

**`size_l1`, `degree_seq_l1`.** Label-blind by definition — the fingerprints
are `(n, m)` and a multiset of integers, and there is nowhere in either to put
a label. That is the point: they are the structural floor every labelled
representation must clear.

## 4. Measured table

<!-- AUDIT-TABLE -->

## 5. Consequences for the runners

1. **Report `labels_used` beside every competitor row.** Five arms compare
   strictly less information than `fact_rank` does. That is a fair and stated
   handicap, not a hidden one, and the tables should say so rather than letting
   a reader assume parity.
2. **Clamp HyperCOT at zero** and compare it with a tolerance.
3. **Compare the real-valued embeddings with a tolerance too** — `netlsd_l2`
   and `hpd_jsd` reach ~10⁻¹⁵ on isomorphic pairs, never exact 0. The
   `< 10⁻⁹` convention of RQ2's false-merge census already accounts for this.
4. **Do not feed `isalhg_levenshtein` anything that may be disconnected.**
5. **Gate the oracles.** `exact_hged` and `qin_hged` need a per-pair budget and
   a censored-fraction column on real members.
6. **Key the matrix cache off the requested arm string**, not off
   `distance.name`: five names are aliases and resolve to a class whose `name`
   is the canonical one.
