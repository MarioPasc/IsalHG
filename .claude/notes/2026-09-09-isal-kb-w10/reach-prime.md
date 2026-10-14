# `reach′` on compacted remainders — D-KBf5

Worktree `agent-a70a4b2e746c770d8`, branch `worktree-agent-a70a4b2e746c770d8`,
base `967d6fe`. Env `isalhg-reachprime` (cloned from `isalhg`, then
`pip install -e ".[dev]"` inside the worktree; `scikit-build-core`, `nanobind`,
`cmake` and `ninja` had to be installed first — the clone did not carry them,
so the documented `--no-build-isolation` line fails on a fresh clone).

`reach′_F(K, K′) = min{|A| + |B| : compact(K − A) ≅ compact(K′ − B)}`.

---

## 1. What changed, per file

### `src/isalhg/language/reach.py`

* **New `compact_constants(H) -> (kb, survivors)`** — drops the constants of
  degree 0, renumbers densely, and returns the surviving original ids in the
  new order. Returns `H` itself when nothing is dropped. It is the
  hypergraph-level twin of `datasets/kb/base.py::compact`; it lives here rather
  than in `core/sparse_hypergraph.py` because it encodes a language-layer
  semantic ("a knowledge base is its set of facts"), and because it sits beside
  `remove_facts`, which is already a hypergraph operation living in this module.
* **`RemainderIndex.level`** now canonicalises `compact(H − A)`, not `H − A`.
* **`RemainderIndex.ranks(subset)` → `RemainderIndex.remainder(subset)`**,
  returning the new frozen `Remainder(word, ranks, survivors, n_source)`. The
  ranks alone are no longer enough: a map between two remainders has to be
  lifted back through `survivors` on both sides.
* **`node_map_from_ranks` → `node_map_from_remainders`**, returning
  `tuple[int | None, ...]` over the *source* constants of the right-hand
  knowledge base. `None` means "stranded by `B`, no counterpart".
* **`Alignment.node_map`** is that partial map.
* **`fact_key_of(H)` compacts first**, so a knowledge base's key equals its own
  level-0 remainder key — required, or `min_deletions()[fact_key_of(H)] == 0`
  would fail on any input carrying a constant that names nothing.
* **`compatible(K, K2, r_max)`** — `r_max` is now required, and the
  constant-count test is gone. Two necessary conditions replace it:

  1. *Fact profile.* Isomorphic knowledge bases carry the same multiset `P` of
     `(predicate, arity)`; deletion only removes elements. The common profile
     `Q` of the two remainders is contained in `P(K)` and in `P(K2)`, hence in
     `P(K) & P(K2)`, so `|A| + |B| = m + m2 − 2|Q| ≥ m + m2 − 2|P(K) & P(K2)|`.
     Reject when that lower bound exceeds `r_max`.
  2. *Undeletable types.* A constant of degree `> r_max` keeps a fact under
     every deletion set the budget allows, so it survives compaction and its
     type is in the remainder's type multiset; and the remainder's constants are
     a subset of the *other* side's occurring constants. So
     `{type(v) : deg_K(v) > r_max}` must be contained, as a multiset, in
     `{type(v) : deg_{K2}(v) > 0}`, and symmetrically.

  Both are stated in the docstring with that reasoning. Both are symmetric, so
  `reach′` stays symmetric.

### `src/isalhg/language/consensus.py`

* **`_transfer` admits a partial `node_map` and creates constants.** A donor
  fact naming a constant with no image gets a fresh constant in the host's
  space carrying the **donor's type**; the candidate is then compacted, because
  a constant that `drop` stranded is not part of the candidate. Returns the new
  private `_Candidate(kb, host_of, donor_of)`.
* **`ConsensusResult.constant_origin`** (new): `(member index, constant of that
  member)` per candidate constant — where the constant, and therefore its
  evaluation identity, came from.
* **`ConsensusResult.node_map` is `tuple[int | None, ...]`** and is no longer
  the identity. The docstring said "Always the identity, because every candidate
  is built inside its anchor's constant space"; both halves of that are now
  false (compaction renumbers; a transfer can create a constant).
* Members are compacted before entering the pool, so a member's pool key equals
  its level-0 remainder key.
* `_Scorer.score` calls `compatible(candidate, H, self._r)`.
* `_pair_alignments` reads `RemainderIndex.remainder`.

### `src/isalhg/datasets/kb/ladders.py`

* **`_variant_member`** builds each rung with `compact(...)` (connectivity
  required) instead of `make_record(..., require_connected=False)` pinned to
  `source.n`.
* It now reads `working.types` / `working.constant_ids`, **not** `source.*`.
  This is not optional: after the first compacting step the working record is
  renumbered, so feeding the source's type table to the second step would
  mis-type the constants.
* `meta["constant_set_preserved"]` is `working.n == source.n` rather than a
  hard-coded `True`.
* `meta["delta"]` is computed on **identities** (`_identity_facts`), because
  constant numbers are not stable across a compaction and the old
  `source.fact_set() ^ working.fact_set()` would over-count.
* The "the member must differ from the source" guard became
  `working.n == source.n and working.facts == source.facts`.
* Module docstring, `variant_collection` docstring: "constant-preserving" and
  "isolated constants are legal" removed. `VARIANT_KINDS` itself is unchanged —
  the three kinds still mean what they meant.

### `experiments/tkde/rq3.py`

* New `consensus_identities(result, identities)` and one changed line in
  `consensus_outcome`. Without it the truth axis breaks: the old call read every
  identity out of `identities[result.anchor]`, and a created constant has no
  index there. This file was not on the do-not-touch list; `rq4.py`, `rq5.py`,
  `matrices.py`, `budget.py`, `prose.md` and the results tree were not touched.

### Tests

`tests/unit/language/_builders.py` gains `transported_remainder`, which
re-expresses a partial `node_map` as a permutation of the compacted remainder so
`permute` can still be used as the isomorphism check.

| file | change |
|---|---|
| `tests/unit/language/test_reach.py` | brute-force reference compacts; `TestReachPrimeSanity` (the four pinned properties + edge cases); `TestTheGateStaysNecessary`; `TestDeletionMembersWereUnreachableBefore`; `test_different_constant_count_is_unreachable` → `test_a_constant_naming_nothing_is_not_part_of_the_knowledge_base` (now reach 0) plus a genuine profile-incompatible pair; `ranks` → `remainder` |
| `tests/unit/language/test_alignment.py` | G1 pin moved from the 4-path to a **4-cycle** (see §5); new `test_compaction_identifies_the_two_stranded_remainders`; incompatible-pair test rebuilt on disjoint predicates |
| `tests/unit/language/test_consensus.py` | `TestTransferCreatesAConstant` (3 tests); result-shape test rewritten against `constant_origin` |
| `tests/property/test_language_properties.py` | node-map property uses `transported_remainder` |
| `tests/unit/datasets/test_kb_generators.py` | variant members may shrink; containment read off identities; new `test_deletion_members_may_lose_a_constant` |

### `docs/article/D_ART3/experiments/DESIGN.md` §4

`reach` → `reach′` with the 2026-09-09 date and the one-sentence rationale; the
candidate definition says `π` is partial and names `insert_fact_new_constant`;
"Truth and the axis" says a created constant keeps the donor's identity; Corpus A
renamed **"fact-edit variant collections over real members"**. `prose.md` untouched.

### `scripts/diagnostics/reach_prime_corpus_b_probe.py` (new)

`--mode gate` (the 1,146/1,400/60 sweep) and `--mode timing` (one run's
consensus). The gate adapter accepts both `compatible` signatures, so the same
file measures before and after.

---

## 2. Corpus B feasibility — the three numbers

`ndc_classes`, 69 runs of `T ≥ 4`, members = `kb_ids[:-1]`, 1,400 unordered
member pairs, `r = 2`.

```
$ python scripts/diagnostics/reach_prime_corpus_b_probe.py --mode gate
```

| | frozen reach (`967d6fe`) | `reach′` |
|---|---|---|
| pairs the gate rejects outright | **1,146 / 1,400 (81.9 %)** | **387 / 1,400 (27.6 %)** |
| pairs with no finite reach at `r = 2` | 1,148 (82.0 %) | **446 (31.9 %)** |
| runs with ≥ 1 gate-rejected pair | **60 / 69** | **44 / 69** |
| runs with ≥ 1 unreachable pair | 60 / 69 | 51 / 69 |
| sweep wall-clock | 0.0 s | 0.5 s |

The brief's three numbers (1,146 / 81.9 % / 60 of 69) reproduce **exactly**.
Pairs with a finite reach go 252 → 954, a 3.8× increase.

---

## 3. Consensus cost — the gate that had to clear 1,800 s

```
$ python scripts/diagnostics/reach_prime_corpus_b_probe.py --mode timing --rank -1   # worst
$ python scripts/diagnostics/reach_prime_corpus_b_probe.py --mode timing --rank 34   # median
```

Runs ordered by `(T, max member m, total m)`. Worst = class **389**, `T = 36`,
35 members, max `m` 6, max `n` 17, 595 member pairs. Median = class **53**,
`T = 5`, 4 members, 6 pairs. The frozen column is the same shipped code with
`compact_constants` set to the identity and `compatible` set back to the
constant-count test, so only the definition differs.

| worst run (class 389) | frozen | `reach′` |
|---|---|---|
| member pairs at finite reach | 112 / 595 | **495 / 595** |
| candidates generated | 103 | **319** |
| coverage of the winner | 13 / 35 | **34 / 35** |
| `sum_reach` of the winner | 70 | **37** |
| **consensus seconds at `r = 2`** | 0.4 | **1.4** |

| median run (class 53) | frozen | `reach′` |
|---|---|---|
| member pairs at finite reach | 1 / 6 | 2 / 6 |
| candidates generated | 12 | 48 |
| coverage of the winner | 2 / 4 | 3 / 4 |
| `sum_reach` of the winner | 7 | 8 |
| consensus seconds at `r = 2` | 0.0 | 0.0 |

**The worst run clears the guard with three orders of magnitude to spare:
1.4 s against `consensus_budget_s = 1800`. The array is safe.** The step change
the coordinator predicted is real (3.5× time, 3.1× candidates, coverage 13 → 34
of 35 members) but starts from a very small number.

---

## 4. Prop. 5, old vs new — and a correction

**The Prop. 5 numbers were not measured with `language/reach.py`.** The probe
behind them is the `R3` block of
`scripts/diagnostics/d_art3_probes_2026-09-03/sigma_plus/t6_followup.py`, which
measures the **Σ⁺ token-level indel ball** (`sigma_plus.decode_plus` over
`canonical_string`). Verified: nothing under
`scripts/diagnostics/d_art3_probes_2026-09-03/` imports `isalhg.language`
(`grep -rn "isalhg.language" .` → no hits); its only `isalhg` imports are
`core.cdll`, `core.instructions`, `core.pointers`, `core.sparse_hypergraph`,
`core.canonical` and `datasets.synthetic._random_hg`, none of which this change
touches.

**I re-ran that same probe** (`r3()` only, 48 profiles, 19 s), as instructed.

| published (`probes_2026-09.md`, R3 row) | re-run under `reach′` |
|---|---|
| family I `t=1`: `cov₁^indel(H₀) = 7/7` | 7.00 in both cells |
| family I `t=1`: best copy 0.00–0.17 | 0.17 (8,10) / 0.00 (10,12) |
| family I `t=1`: unique maximiser **12/12** | 6/6 + 6/6 = **12/12** |
| family I `t=1`: copy→copy at `r=1` 0.00–0.01 | 0.01 / 0.00 |
| family I `t=2`: `cov₂^indel(H₀) = 7/7` | 7.00 in both cells |
| family I `t=2`: unique maximiser **12/12** | **12/12** |
| family I `t=2`: copy→copy at `r ≤ 2` 0.00–0.02 | 0.00 / 0.02 |

**Identical.** Family D reproduces its recorded caps as well (`t=2` D:
`cov₁ = 0.00`, `cov₂` 2.00–2.83).

Because "member-to-member reach" in `prose.md` §4 could be read as `reach_F`, I
also measured the fact-level analogue on the *same* 48 profiles, under both
semantics in one process:

| `reach_F`, both semantics | cell (8,10) | cell (10,12) |
|---|---|---|
| family I `t=1`: `cov_t(H₀)` | 7.00 | 7.00 |
| family I `t=1`: best copy | 0.17 | 0.00 |
| family I `t=1`: unique | 6/6 | 6/6 |
| family I `t=1`: copy→copy | 0.01 | 0.00 |
| family I `t=2`: `cov_t(H₀)` | 7.00 | 7.00 |
| family I `t=2`: unique | 6/6 | 6/6 |
| family I `t=2`: copy→copy | 0.01 | 0.02 |

`frozen == prime on all 48 profiles: True`, `differing profiles: 0`.

**Prop. 5 is unchanged, and the reason is structural**: on these origins no
remainder inside the radius ever strands a constant, so compaction is the
identity throughout. Nothing in `prose.md` §4 needs to move on account of this
change. (`prose.md` was not edited — that is T-KBg's.)

---

## 5. Corpus A still builds

The generator was re-measured on the pre-registered cells (2 collections × `N ∈
{5,9}` × `t ∈ {1,2}` × 3 kinds, 8 sources × 3 seeds = 24 attempts per cell),
frozen vs `reach′`:

* **Drop counts are identical in every one of the 24 cells.** The connectivity
  requirement `_variant_member` now imposes cost nothing on this sample. The
  only non-zero drops are pre-existing pool limits: `ndc_classes N=9 del` has an
  empty source pool (needs `m ≥ 10` inside the window), `wd50k66 N=9 t=1 del`
  builds 3/24, `wd50k66 N=5 t=1 del` 18/24, `wd50k66 N=9 t=2 del` 21/24 — all
  the same before and after.
* What changes is what those members *are*: `members_that_lost_a_constant` goes
  from **0 everywhere** to, e.g., 108/120 (`ndc_classes N=5 t=2 del`), 117/120
  (`wd50k66 N=5 t=2 del`), 144/216 (`wd50k66 N=9 t=2 mix`). Under the frozen
  gate every one of those members was at *infinite* reach from its source, so
  H3a was false by definition rather than by evidence. That is the D-KBf5 claim,
  measured on the real generator.

---

## 6. Things in the brief that are wrong

**(a) The suggested replacement gate is not a necessary condition.** The brief
offers "compare the type multiset of constants that occur in at least one fact".
Compaction can *remove* an occurring constant, so those multisets need not agree
even at reach 1. Measured counterexample, now pinned as
`TestTheGateStaysNecessary::test_occurring_type_multisets_are_not_a_necessary_condition`:

```
K  : constants (type 0, type 0, type 1), facts p(0,1), q(1,2)   occurring types [0,0,1]
K2 : constants (type 0, type 0),         fact  p(0,1)           occurring types [0,0]
reach_prime(K, K2) = 1          (delete q; constant 2 is stranded and goes)
occurring-type equality would have rejected the pair.
```

The shipped gate uses the fact-profile budget plus the *undeletable*-type
containment described in §1, both of which survive compaction.

**(b) "Prop. 5 … were measured under the old reach" — no.** See §4. They were
measured on the Σ⁺ token ball and never went through `language/reach.py`.

**(c) "at infinite reach" is not a notion `reach′` has.** Under `reach′` every
pair is at *finite* reach at a large enough budget: delete every fact on both
sides and both compact to the empty knowledge base, so
`reach′(K, K′) ≤ m + m′` always. The comparable statistic is "no finite reach
within `r = 2`", which is what §2 reports beside the gate rejections. The gate
stays meaningful only because it is now radius-aware.

**(d) `_variant_member`: "stop pinning `source.n`" is not sufficient on its
own** — `source.types` and `source.constant_ids` had to go with it, or the
second edit of a `t = 2` member types its constants from a stale table.

**(e) `ConsensusResult.node_map` cannot carry the change by itself.** It indexes
the anchor's identity list, and a created constant has no entry there. Hence
`constant_origin` and the one-line rewire in `experiments/tkde/rq3.py`.

**(f) The documented env recipe fails on a fresh clone.** `pip install -e
".[dev]" --no-deps --no-build-isolation` dies with `BackendUnavailable: Cannot
import 'scikit_build_core.build'`; the clone of `isalhg` carries neither
`scikit-build-core` nor `nanobind`/`cmake`/`ninja`. Installing those four first
fixes it.

**(g) Non-issue, recorded so nobody chases it.** Tracebacks in this env print
frames as `/home/mpascual/.conda/envs/isalhg/lib/...` even though the module
loaded is the clone's: `conda create --clone` hardlinks the `__pycache__`
`.pyc` files, whose `co_filename` was baked in the base env. Checked:
`sys.path` contains no `/envs/isalhg/` entry, and `hypothesis.__file__`,
`pytest.__file__`, `rapidfuzz.__file__` all resolve inside
`isalhg-reachprime`. `isalhg.__file__` and `isalhg.core._core.__file__` resolve
to this worktree and this env respectively.

---

## 7. Verification

Baseline at `967d6fe`, measured in this worktree before any edit:

```
$ python -m pytest tests/ -q -p no:randomly
8 failed, 2909 passed, 30 skipped, 21 warnings in 1923.69s (0:32:03)
FAILED tests/experiments_tkde/test_rq36_smoke.py::TestUnitEnumeration::test_rq6_units_are_unique
FAILED tests/experiments_tkde/test_rq36_smoke.py::TestModelIsNotSharedAcrossUnits::test_each_call_returns_a_fresh_model
FAILED tests/experiments_tkde/test_rq36_smoke.py::TestModelIsNotSharedAcrossUnits::test_the_fresh_model_samples_identically
FAILED tests/experiments_tkde/test_rq36_smoke.py::TestModelIsNotSharedAcrossUnits::test_a_used_model_is_not_reachable_from_the_context
FAILED tests/experiments_tkde/test_rq36_smoke.py::TestDeployStamps::test_the_stamps_name_the_imported_package
FAILED tests/experiments_tkde/test_rq45_smoke.py::TestSmokeIsolation::test_deploy_stamps_name_both_trees
FAILED tests/integration/test_cpp_orbit_corpus.py::test_orbit_matches_unpruned_wstar_c[wd50k66]
FAILED tests/integration/test_cpp_orbit_corpus.py::test_orbit_matches_unpruned_wstar_c[ndc_classes]
```

After, same command, same worktree:

```
$ python -m pytest tests/ -q -p no:randomly
8 failed, 2927 passed, 30 skipped, 21 warnings in 2017.58s (0:33:37)
```

The two `FAILED` lists are byte-identical (`diff base_failed.txt
after_failed.txt` → no output): **no new failures**, and 18 more tests pass
because 18 were added. The 8 are the pre-existing ones listed above.

Targeted suites:

```
$ python -m pytest tests/unit/language/test_reach.py -q -p no:randomly
31 passed in 0.63s
$ python -m pytest tests/unit/language/test_alignment.py -q -p no:randomly
12 passed in 0.25s
$ python -m pytest tests/unit/language/test_consensus.py -q -p no:randomly
19 passed in 4.78s
$ python -m pytest tests/unit/datasets/test_kb_generators.py -q -p no:randomly
57 passed in 0.16s
$ python -m ruff check src/isalhg/language/ src/isalhg/datasets/kb/ladders.py \
      experiments/tkde/rq3.py tests/unit/language/ tests/property/test_language_properties.py \
      tests/unit/datasets/test_kb_generators.py scripts/diagnostics/reach_prime_corpus_b_probe.py
All checks passed!
$ python -m mypy src/isalhg/language/ src/isalhg/datasets/kb/ladders.py
Success: no issues found in 7 source files
```

`ruff check src/isalhg/` and `mypy src/isalhg/` report 2 and 20 pre-existing
findings respectively, all in files this task did not touch
(`core/hypergraph_to_string.py`, `core/canonical.py`,
`iso_backends/isalhg_backend.py`, a figure module).

---

## 7b. Out of scope, but caused by this change: `experiments/tkde/rq6.py`

**`Reach1Index` is unsound under `reach′` and was left alone** (RQ6 is not in
this task's scope; nothing was edited there). It hard-codes the *frozen* reach
precondition:

```python
def _shape(H):                      # rq6.py:308
    """The reach precondition: constant count and sorted type multiset."""
    return H.n_nodes, tuple(sorted(H.vertex_label(v) for v in range(H.n_nodes)))
```

`within_one` buckets the members by `_shape` and never looks outside the
sample's bucket, so a sample whose constant count differs is answered without
calling `reach` at all. That was exactly the gate D-KBf5 removed. It also mixes
key spaces: `_member_key` uses `fact_word` (no compaction) while
`_deletion_keys` now returns *compacted* remainder words, which agree only while
the object has no constant naming nothing — a decoded sample can have one.

Reproduced:

```python
src    = hub {0,1} + three private-predicate pendants          # 5 constants
sample = compact(src - pendant_1)                              # 4 constants
reach(sample, src, r_max=1)          -> 1
Reach1Index([src]).within_one(sample) -> None      # never calls reach
```

`reach()` and `RemainderIndex.min_deletions()` kept their signatures, so
`rq6.py` still imports and runs; what changed is the answer it records.
RQ6's `reach1` column and its `within_one` precondition rows need re-deriving
before the next RQ6 array. Suggested fix for whoever owns it: drop `_shape`
bucketing in favour of `isalhg.language.reach.compatible(sample, member, 1)`,
and key both sides with `fact_key_of` rather than `fact_word`.

## 8. Residual risk

* **API breakage, deliberate (no shims, per the coding rules).**
  `compatible()` gained a required `r_max`; `RemainderIndex.ranks` became
  `remainder`; `node_map_from_ranks` became `node_map_from_remainders`;
  `Alignment.node_map` and `ConsensusResult.node_map` admit `None`. Every
  in-tree caller was found by grep and updated. Anything outside the tree — a
  notebook, a Picasso deploy of an older `src/` — breaks loudly.
* **Every RQ3 result on disk is stale.** No results tree was touched, but
  `rows_variants` and `rows_natural` under
  `.../results/IEEETKDE/RQ3_representative/` were produced under the frozen
  definition and must be regenerated.
* **A transfer candidate can still be disconnected**; nothing rejects it, and
  the fact word tolerates it (that is why `RemainderIndex` keys on the fact word
  and not on `F°`). Unchanged from before, flagged because the new
  constant-creating path makes it easier to reach.
* **The `wd50k66 N=9 t=1 del` cell builds 3 of 24** — a pre-existing pool limit,
  identical before and after, but it is the cell most likely to be
  `pool_limited` when the full array runs.
* **The Corpus A measurement in §5 is 8 sources × 3 seeds, not 27 seeds.** It
  shows the cells are not newly infeasible; it is not the pre-registered sweep.
* **The consensus timing is one worst run and one median run**, as asked. The
  full 69-run array was not timed.
