# T-M2c — Restrict the article to connected hypergraphs (domain gap, resolved)
**Declared:** 2026-07-08 23:25 CEST (handoff from T-M2b)
**Rewritten:** 2026-07-09 12:46 CEST — P1/P2/P3 resolved by the PI; scope narrowed
from "blocking theoretical fork" to "generator engineering + one lemma handed to T-TB"
**Status:** DONE
**Depends on:** — (gates T-M5a E1/E3; hands a lemma to T-TB)
**Why out of scope:** found while assessing HGED completeness for Theorem B at
T-M2b close; fixing it touches corpus generators and the dataset loaders, not the
HGED metric itself.

---

## Resolution (PI, 2026-07-09)

**The alphabet does not change. The article's domain is the connected hypergraphs.**

**(P3) — answered: no gluing mechanism is needed, and none is adopted.** `Σ_HG`
provably cannot express disconnection (every `V_{i,j}` has `i ≥ 1`; `C_i` spans
only existing nodes; no token creates an isolated vertex), so the S2H-reachable set
*is* the connected hypergraphs. That is the alphabet's shape, not an oversight —
it is why decision B11 exists. Both candidate glues are **rejected**: (iii-b)
alphabet extension would reopen Theorem A *and* invalidate the C++ tie-complete
encoder shipped at T-TAa; (iii-a) the sorted-tuple fingerprint is cheap but costs
the paper its central claim — "a hypergraph is a word" would become "a hypergraph
is a tuple of words", and invariants #2/#3 (closed alphabet, round-trip) would hold
only per component. Precedent: the IsalGraph sibling restricts to connected graphs.
Theorem A is in any case *stated* only over connected hypergraphs (Assumption 1.3),
so the proof exists nowhere else.

**(P2) — resolved to (ii-a): restrict the generators; take the LCC for real data.**
This is the whole engineering content of the task now. Two honest consequences that
**must be stated in the paper**, not silently absorbed:
- Conditioning a random generator on connectivity **changes the ensemble**. The
  density sweep (E2) then samples *connected* Erdős–Rényi, not ER, and the
  conditioning bites hardest exactly where it matters, at low `m/n`. Write
  "connected ER" and report the acceptance rate.
- Rejecting disconnecting edits biases the perturbation ladder's edit distribution
  and confines it to a submanifold. The `HGED ≤ budget` guarantee **survives** (a
  valid Qin edit sequence of exactly that cost still exists), but the sampling
  claim changes.
For real corpora (HIC, T-M4'), take each instance's **largest connected component**
and report the retention fraction (vertices, hyperedges) *per class* — standard
practice in graph/hypergraph ML, and reviewers expect the number, not a defence. If
retention varies by class, say so: fragmentation correlated with the label would
bias the classification task. Note that connectivity was never the gate on the real
anchor — `w*_c` wall-clock is (T-DQ3').

**(P1) — handed to T-TB as a *path-normalization lemma*, and it costs nothing.**
The earlier reading ("an optimal path through connected states likely does not
exist, so P1 needs the P3 mechanism") **conceded too much**. Theorem B's statement
mentions only the endpoints; it is the *proof technique* — telescoping `d_I` along
an optimal HGED path — that needs `w*_c` at every intermediate. But the triangle
inequality bounds `d_I` along **any** path, not just an optimal one. It therefore
suffices to exhibit *some* path from `H` to `H'` whose intermediates are all
connected and whose total Qin cost is `≤ c·HGED(H,H')`; then
`d_I ≤ (max_e s(e))·c·HGED`. Such a path exists with **`c = 1`** (no loss in the
constant), by two normalizations, each of which preserves the op count because
Qin's ops are unit-cost:
1. **Insert before delete.** Reorder the optimal path so every insertion and
   extension happens first — reaching `H ∪ H'` under the optimal correspondence `π`
   — and only then every reduction and deletion.
2. **Never materialize an isolated vertex.** Pair each vertex insertion with its
   first incidence addition; pair each vertex deletion with its last incidence
   removal, and delete leaf-first.
Every intermediate on the first leg then contains `H` (connected, spanning) plus
material attached to it; every intermediate on the second leg contains `H'` plus
material attached to it. Residual hypothesis to discharge in the proof: `H ∪ H'` is
connected, i.e. `π` identifies at least one vertex — which fails only in the
degenerate near-maximal-HGED case, where the bound is slack anyway and can be
handled separately. Recorded as `stability.md` §6, item **T-B0**.

---

## Original diagnosis (2026-07-08, retained as the record)

**Context to read first:**
- `src/isalhg/core/canonical.py::_python_canonical_string` (and the C++ twin `_native/src/canonical.cpp`) — raise `DisconnectedHypergraphError` on any disconnected input (decision B11); `SparseHypergraph.is_connected` counts an isolated vertex as disconnection
- `src/isalhg/core/sparse_hypergraph.py::{random_edit, edit_path, insert_vertex}` — `insert_vertex` is always applicable, so ladder snapshots can be disconnected; `delete_hyperedge`/`remove_incidence` can disconnect too
- `src/isalhg/datasets/synthetic/_random_hg.py::random_hypergraph` — no connectivity guarantee, so `correlation_corpus` items can be disconnected
- `src/isalhg/datasets/synthetic/{perturbation_ladder,correlation_corpus}.py` — the two generators to make connectivity-preserving
- `src/isalhg/datasets/hic_atlas.py` — where the LCC restriction lands (with T-M4')
- `docs/article/theoretical/stability.md` §2.1, §6 (T-B0) — the decomposition and the lemma this task hands it
- `docs/article/empirical/correlation.md` §Experiments (E1/E3) — the runs that raise today
- `docs/article/DATA.md` §1, §3 — the corpora whose ensembles this changes
- `.claude/rules/coding_rules.md` — always

`d_I = d_Lev(w*, w*)` is only defined on connected hypergraphs (decision B11). The
entry held **three distinct problems**; each had its own fix surface:

- **(P1) Transient disconnection inside the theorem's proof — theory only.**
  Optimal Qin HGED edit paths pass through disconnected *intermediate* states
  (every vertex insertion starts isolated; incidence removals can disconnect),
  so Theorem B's §2.1 decomposition `d_I(H,H') ≤ Σ d_I(H_{i-1}, H_i)` has
  undefined terms even when both *endpoints* are connected.
- **(P2) Native disconnected inputs to the framework — the thing that crashes
  today.** `random_hypergraph` gives no connectivity guarantee (corpus items for E1
  can be disconnected) and ladder snapshots can be disconnected (`insert_vertex`
  always applicable), so T-M5a's E1/E3 raise `DisconnectedHypergraphError`.
- **(P3) The theoretical crux for any native support: does concatenation of
  IsalHG instruction strings decode to the right hypergraph? Answer: NO** — naive
  concatenation is provably the wrong gluing. Appending component B's string after
  component A's decodes as *growing component A further*: B's `V`/`C` instructions
  bind to A's nodes through the shared CDLL/pointer state, yielding a connected
  hypergraph, not the disjoint union.

---

**Description (post-resolution):** Make every generator and loader in the article's
pipeline emit connected hypergraphs, and record the ensemble consequences.
Concretely: `random_hypergraph` grows a connected backbone (or rejection-samples,
reporting the acceptance rate); `random_edit` / `edit_path` reject edits that
disconnect, and `insert_vertex` is only ever applied paired with an incidence;
`perturbation_ladder` and `correlation_corpus` inherit both; the HIC loader
(T-M4') restricts each instance to its largest connected component. Do **not**
touch `Σ_HG`, `canonical.py`, or the C++ encoder.
**Acceptance:** (a) `correlation_corpus` and `perturbation_ladder` emit only
connected items under Hypothesis, and an E1/E3 dry-run no longer raises; (b) the
ladder's `HGED ≤ budget` property test still passes under connectivity-preserving
edits; (c) the acceptance rate / backbone bias of the connected generator is
measured and reported, and `DATA.md` §1 says "connected ER"; (d) `stability.md` §6
item T-B0 records the path-normalization lemma above as P1's discharge, with the
`H ∪ H'` connectivity hypothesis flagged; (e) if T-M4' has landed, the HIC loader
reports per-class LCC retention.
**Out of scope here:** proving the normalization lemma (T-TB / T-B0); the stability
bound itself (T-TB); the HGED oracles (unaffected — they are defined on
disconnected inputs already); the degenerate `n = 0` vs single-vertex collision
(T-M1c).

---

## Closing check — 2026-07-09 (worktree agent-abdc04243e869e750)

**Implementation summary:**

- `src/isalhg/datasets/synthetic/_random_hg.py`: added `_backbone_connected_hypergraph`
  and `random_connected_hypergraph(*, ..., max_attempts=200) -> tuple[SparseHypergraph, int]`.
  Returns `(H, n_attempts)`; `n_attempts == max_attempts + 1` signals backbone fallback.
  Single-vertex case handled directly (trivially connected).
- `src/isalhg/core/sparse_hypergraph.py`: added `random_connected_edit(H, rng) -> tuple[SparseHypergraph, str]`.
  Candidates: `insert_vertex_and_edge` (always), `insert_hyperedge`, `add_incidence`,
  `delete_hyperedge` (filtered by `is_connected()`), `remove_incidence` (filtered).
  `delete_vertex` never offered — connected H has no isolated vertices.
- `src/isalhg/datasets/synthetic/perturbation_ladder.py`: base drawn via
  `random_connected_hypergraph`; steps via `random_connected_edit`. Step-0 `extra`
  carries `acceptance_attempts`.
- `src/isalhg/datasets/synthetic/correlation_corpus.py`: each item drawn via
  `random_connected_hypergraph`; `extra` carries `acceptance_attempts`.
- `docs/article/DATA.md §1`: added "connected ER" paragraph — rejection-sampling,
  backbone fallback, acceptance-rate reporting requirement, ensemble-change note.
- `docs/article/theoretical/stability.md §6 T-B0`: already `[x]` (proved at T-TB
  2026-07-09) — no change needed.
- `src/isalhg/datasets/hic_atlas.py` LCC restriction: out of scope (T-M4' agent).

**Pre-fix failure verified:** `random_hypergraph` with `n=5, n_edges=1, arity=(2,2)`
produced a disconnected hypergraph in 10/10 seeds — confirms tests had teeth before
the fix.

**Acceptance criteria:**

- (a) `correlation_corpus` and `perturbation_ladder` emit only connected items: PASS
  (`TestConnectivity` classes in both test files; Hypothesis property test over 30/20
  seeds; all green).
- (b) ladder `HGED ≤ budget` property still passes under connectivity-preserving edits:
  PASS (`test_budget_is_upper_bound_for_hged` passes for all ladders).
- (c) acceptance rate reported in `extra["acceptance_attempts"]`; `DATA.md §1` says
  "connected ER": PASS.
- (d) `stability.md §6 T-B0` already `[x]` from T-TB: PASS (no edit needed).
- (e) HIC loader LCC restriction: out of scope (T-M4').

**Test suite (env isalhg-T-M2c, worktree):**

```
pytest tests/ -q --tb=no
643 passed, 5 skipped in 159.29s
```

**Ruff:** 3 pre-existing errors (isalhg_backend.py:52, viz/instruction_view.py:135,
tests/unit/core/algorithms/test_registry.py:48) — none in files I modified.

**Mypy:** 20 errors in 6 files (baseline 21 — matched / improved by 1).
Errors are all pre-existing in canonical.py, isalhg_backend.py.
