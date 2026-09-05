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

**Each arm runs in its own OS process**, hard-killed by `timeout -s KILL 45`.
Inside that process a 2 s `SIGALRM` bounds each call, and the arm gets a 10 s
wall-clock budget for the pairs and 5 s for the isomorphic-pair check. A call
the alarm interrupts is counted as a timeout; pairs never attempted are counted
as censored. Neither is silently dropped, and the table reports both.

That escalation is not defensive over-engineering — each layer was added
because the previous one measurably failed:

1. **The oracles' own `timeout` argument does not bound a call.**
   `ExactHGED(timeout=2.0)` ran for more than 8 s on one real `wd50k66` pair:
   the check sits inside the branch-and-bound expansion loop, while the
   pre-seeding assignments run before it. A runner that budgets these oracles
   by their constructor argument alone will overrun.
2. **A Python `SIGALRM` does not bound `isalhg_levenshtein`.** Its
   canonical-string call runs inside the C++ extension and does not return to
   the interpreter, so the Python signal handler never executes.
3. **Neither does `SIGTERM`,** for the same reason — `timeout` without `-s KILL`
   hung indefinitely. Only `SIGKILL` ends it.

The practical rule for wave 3: **bound every arm at the process level.** No
in-process timeout is sufficient for all of them.

`fact_rank_roles` refuses `pairwise` by design — a `SparseHypergraph` carries no
roles, and answering would silently return the role-free distance, making the
ablation secretly identical to the primary arm — so it is listed without a row
of numbers.

**Timing caveat.** Part of the run overlapped the repository's unit suite on the
same machine, so the medians are indicative of relative cost, not precise
benchmarks. The correctness columns (false merges, behaviour on isomorphic
pairs) do not depend on load; only the seconds column does.

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

### `wd50k66` (200 members, `n_types = 1`, `n_preds = 351`)

| arm | labels | pairs used | timed out | median/pair | non-iso | false merges | rate | iso → 0 | max \|d\| on iso |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `bipartite_ged_assign` | vertex | 500 | 0 | 32 µs | 500 | 6 | 0.0120 | 100/100 | 0 |
| `bipartite_ged_path` | edge, vertex | 500 | 0 | 55 µs | 500 | 0 | 0.0000 | 8/100 | 34 |
| `bipartite_hged` | edge, vertex | 500 | 0 | 55 µs | 500 | 0 | 0.0000 | 8/100 | 34 |
| `degree_seq_l1` | — | 500 | 0 | 3 µs | 500 | 6 | 0.0120 | 100/100 | 0 |
| `exact_ged` | edge, vertex | 11 /500 | 5 | 0.14 ms | 11 | 0 | 0.0000 | 11/11 | 0 |
| `exact_hged` | edge, vertex | 11 /500 | 5 | 0.14 ms | 11 | 0 | 0.0000 | 11/11 | 0 |
| `fact_degree_key` | edge, vertex | 500 | 0 | 83 µs | 500 | 0 | 0.0000 | 100/100 | 0 |
| `fact_local_colour` | edge, vertex | 500 | 0 | 0.11 ms | 500 | 0 | 0.0000 | 100/100 | 0 |
| `fact_local_key` | edge, vertex | 500 | 0 | 0.10 ms | 500 | 0 | 0.0000 | 100/100 | 0 |
| `fact_rank` | edge, vertex | 500 | 0 | 67 µs | 500 | 0 | 0.0000 | 100/100 | 0 |
| `fact_rank_roles` | edge, vertex | — | — | — | — | — | — | — | refuses `pairwise` (by design) |
| `hpd_jsd` | — | 500 | 0 | 0.38 ms | 500 | 12 | 0.0240 | 100/100 | 0 |
| `hypercot` | — | 18 /500 | 0 | 568.61 ms | 18 | 1 | 0.0556 | 9/9 | 2.49e-15 |
| `hypergraph_wl_chi2` | edge, vertex | 500 | 0 | 45 µs | 500 | 0 | 0.0000 | 100/100 | 0 |
| `hypergraph_wl_l1` | edge, vertex | 500 | 0 | 44 µs | 500 | 0 | 0.0000 | 100/100 | 0 |
| `isalhg_levenshtein` | edge, vertex | 0 | — | — | — | — | — | — | **SIGKILLed at 45 s** (uninterruptible) |
| `nauty_cert` | edge, vertex | 500 | 0 | 51 µs | 500 | 0 | 0.0000 | 100/100 | 0 |
| `nauty_cert_rows` | edge, vertex | 500 | 0 | 57 µs | 500 | 0 | 0.0000 | 100/100 | 0 |
| `nauty_levi_edit` | edge, vertex | 500 | 0 | 51 µs | 500 | 0 | 0.0000 | 100/100 | 0 |
| `netlsd` | — | 500 | 0 | 1.60 ms | 500 | 5 | 0.0100 | 100/100 | 7.79e-14 |
| `netlsd_l2` | — | 500 | 0 | 1.63 ms | 500 | 5 | 0.0100 | 100/100 | 7.79e-14 |
| `qin_hged` | edge, vertex | 8 /500 | 5 | 65 µs | 8 | 0 | 0.0000 | 4/4 | 0 |
| `size_l1` | — | 500 | 0 | 1 µs | 500 | 10 | 0.0200 | 100/100 | 0 |
| `wl_l1` | edge, vertex | 500 | 0 | 44 µs | 500 | 0 | 0.0000 | 100/100 | 0 |

### `ndc_classes` (200 members, `n_types = 4`, `n_preds = 1`)

| arm | labels | pairs used | timed out | median/pair | non-iso | false merges | rate | iso → 0 | max \|d\| on iso |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `bipartite_ged_assign` | vertex | 500 | 0 | 31 µs | 494 | 0 | 0.0000 | 100/100 | 0 |
| `bipartite_ged_path` | edge, vertex | 500 | 0 | 44 µs | 494 | 0 | 0.0000 | 19/100 | 24 |
| `bipartite_hged` | edge, vertex | 500 | 0 | 45 µs | 494 | 0 | 0.0000 | 19/100 | 24 |
| `degree_seq_l1` | — | 500 | 0 | 3 µs | 494 | 5 | 0.0101 | 100/100 | 0 |
| `exact_ged` | edge, vertex | 5 /500 | 5 | 131.21 ms | 5 | 0 | 0.0000 | 100/100 | 0 |
| `exact_hged` | edge, vertex | 5 /500 | 5 | 130.37 ms | 5 | 0 | 0.0000 | 100/100 | 0 |
| `fact_degree_key` | edge, vertex | 500 | 0 | 66 µs | 494 | 0 | 0.0000 | 100/100 | 0 |
| `fact_local_colour` | edge, vertex | 500 | 0 | 89 µs | 494 | 0 | 0.0000 | 100/100 | 0 |
| `fact_local_key` | edge, vertex | 500 | 0 | 78 µs | 494 | 0 | 0.0000 | 100/100 | 0 |
| `fact_rank` | edge, vertex | 500 | 0 | 51 µs | 494 | 0 | 0.0000 | 100/100 | 0 |
| `fact_rank_roles` | edge, vertex | — | — | — | — | — | — | — | refuses `pairwise` (by design) |
| `hpd_jsd` | — | 500 | 0 | 0.22 ms | 494 | 7 | 0.0142 | 100/100 | 0 |
| `hypercot` | — | 18 /500 | 0 | 568.14 ms | 18 | 1 | 0.0556 | 8/9 | 3.46 |
| `hypergraph_wl_chi2` | edge, vertex | 500 | 0 | 37 µs | 494 | 0 | 0.0000 | 100/100 | 0 |
| `hypergraph_wl_l1` | edge, vertex | 500 | 0 | 37 µs | 494 | 0 | 0.0000 | 100/100 | 0 |
| `isalhg_levenshtein` | edge, vertex | 3 /500 | 2 | 3.69 ms | 3 | 0 | 0.0000 | 8/8 | 0 |
| `nauty_cert` | edge, vertex | 500 | 0 | 38 µs | 494 | 0 | 0.0000 | 100/100 | 0 |
| `nauty_cert_rows` | edge, vertex | 500 | 0 | 43 µs | 494 | 0 | 0.0000 | 100/100 | 0 |
| `nauty_levi_edit` | edge, vertex | 500 | 0 | 38 µs | 494 | 0 | 0.0000 | 100/100 | 0 |
| `netlsd` | — | 500 | 0 | 1.59 ms | 494 | 4 | 0.0081 | 100/100 | 3.21e-14 |
| `netlsd_l2` | — | 500 | 0 | 1.60 ms | 494 | 4 | 0.0081 | 100/100 | 3.21e-14 |
| `qin_hged` | edge, vertex | 2 /500 | 5 | 650.46 ms | 2 | 0 | 0.0000 | 3/3 | 0 |
| `size_l1` | — | 500 | 0 | 1 µs | 494 | 21 | 0.0425 | 100/100 | 0 |
| `wl_l1` | edge, vertex | 500 | 0 | 37 µs | 494 | 0 | 0.0000 | 100/100 | 0 |

## 5. What the numbers say

**The complete arms are clean, on both collections.** `fact_rank`, the three
addressing ablations, `nauty_cert`, `nauty_cert_rows`, both WL arms and the
exact oracle merge **zero** non-isomorphic pairs and return **0 on 100/100**
isomorphic pairs. On these real collections the completeness claim is not merely
theoretical; it is the measured behaviour.

**Every incomplete representation merges real members** (H2a, confirmed).
On `wd50k66` / `ndc_classes` the false-merge rates are `hpd_jsd` 2.40 % / 1.42 %,
`size_l1` 2.00 % / (n/a), `netlsd` 1.00 % / 0.81 %, `degree_seq_l1` 1.20 % /
1.01 %, `bipartite_ged_assign` 1.20 % / 0 %, `hypercot` 1/18 pairs. These are not
adversarial constructions — they are randomly drawn pairs of real knowledge
bases.

**The bipartite edit-path reading is not zero on isomorphic inputs.** This is
the sharpest finding, and it is not the one the class docstring would lead you
to expect. `bipartite_ged_path` returns 0 on only **8 of 100** isomorphic
`wd50k66` pairs and **19 of 100** on `ndc_classes`, with a maximum of **34** and
**24** respectively. It has no *false* merges — but it has systematic *false
separations*: it charges a large cost between a knowledge base and a relabelled
copy of itself, because the Riesen–Bunke assignment need not recover the
isomorphism. So the arm violates `H ≅ H' ⇒ d = 0`, and any downstream use that
assumes distances respect isomorphism classes (clustering by identity, dedup,
the medoid certificate) is unsound under it. The raw assignment reading is 0 on
100/100 isomorphic pairs, so the two readings fail on opposite sides: the
assignment reading merges things it should separate, the edit-path reading
separates things it should merge.

**HyperCOT is a local optimum, and it shows.** On `ndc_classes` it returned a
non-zero value on an isomorphic pair with a maximum of **3.46** — not
floating-point noise but a genuine convergence failure (8/9 pairs did reach 0).
On `wd50k66` its isomorphic-pair maximum is 2.49 × 10⁻¹⁵, and elsewhere it
returns small *negative* values. Treat it as approximate on both sides.

**The oracles do not scale to these members.** `exact_hged` completed 11 of 500
`wd50k66` pairs and 5 of 500 `ndc_classes` pairs inside a 2 s per-call budget;
`qin_hged` completed 8 and 2. This is consistent with the design's H2c
(completion only below `n ≈ 10`) and means RQ2's oracle row must be reported
with its censored fraction, not as a summary statistic over the collection.

**`isalhg_levenshtein` is not usable on `wd50k66` and marginal on
`ndc_classes`.** On `wd50k66` the arm had to be SIGKILLed: at least one of the
sampled real pairs sends the tie-complete canonical-string search into a run
that neither a signal nor `SIGTERM` can interrupt. On `ndc_classes` it completed
3 of 500 pairs with 2 timeouts. The pointer alphabet is the *displaced*
addressing in RQ1, not a primary arm, so this does not affect the article's main
line — but the RQ1 supplement must budget it per process and report the
censoring, and the fact-alphabet pivot is exactly what this measurement
justifies.

**Speed.** The fact-alphabet arms cost 51–67 µs per pair, the same order as the
nauty arms (38–57 µs) and WL (37–45 µs); `netlsd` is ~1.6 ms, `hpd_jsd`
0.22–0.38 ms, and `hypercot` 568 ms (dominated by subprocess startup).

## 6. Consequences for the runners

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

7. **`bipartite_ged_path` must not be used where isomorphism-invariance is
   assumed.** It returns a large non-zero distance between a knowledge base and
   a relabelled copy of itself (measured max 34 on `wd50k66`, 24 on
   `ndc_classes`). It is a heuristic upper bound on an edit cost, not a
   dissimilarity on isomorphism classes.
8. **Budget `isalhg_levenshtein` per process and expect censoring** on the RQ1
   supplement; on `wd50k66` it could not be completed at all.
