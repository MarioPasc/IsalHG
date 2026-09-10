# RQ3's consensus returns an object the Isal language can write

Work log. Worktree `agent-a259ea3746fb32806`, branch
`worktree-agent-a259ea3746fb32806`, base `44c48e3`. Code commit `60c9b98`,
made **before** any campaign number was looked at (§6 was measured afterwards,
against the committed tree).

## 1. Environment

```
conda create -y -n isalhg-consensus --clone isalhg
~/.conda/envs/isalhg-consensus/bin/python -m pip install -e ".[dev]" --no-deps --no-build-isolation
```

The editable install failed exactly as the brief warned:

```
pip._vendor.pyproject_hooks._impl.BackendUnavailable: Cannot import 'scikit_build_core.build'
```

Fixed by installing the build backend into the clone first — a conda clone does
not carry the pip-only build requirements:

```
~/.conda/envs/isalhg-consensus/bin/python -m pip install scikit-build-core nanobind cmake ninja
# Successfully installed cmake-4.4.3 nanobind-3.0.1 ninja-1.13.2 scikit-build-core-1.0.3
~/.conda/envs/isalhg-consensus/bin/python -m pip install -e ".[dev]" --no-deps --no-build-isolation
# Successfully built isalhg / Successfully installed isalhg-0.0.1
```

Verified the env imports **this** worktree before anything else was run:

```
$ ~/.conda/envs/isalhg-consensus/bin/python -c "import isalhg, isalhg.language.consensus as m; print(isalhg.__file__); print(m.__file__)"
/home/mpascual/research/code/IsalHG/.claude/worktrees/agent-a259ea3746fb32806/src/isalhg/__init__.py
/home/mpascual/research/code/IsalHG/.claude/worktrees/agent-a259ea3746fb32806/src/isalhg/language/consensus.py
$ ~/.conda/envs/isalhg-consensus/bin/python -c "import isalhg.core._core as c; print(c.__file__)"
/home/mpascual/.conda/envs/isalhg-consensus/lib/python3.11/site-packages/isalhg/core/_core.cpython-311-x86_64-linux-gnu.so
```

One oddity worth recording: pytest tracebacks report `hypothesis` from
`~/.conda/envs/isalhg/lib/...`, i.e. the *source* env's path, presumably a clone
artefact for pip-installed packages. `isalhg` itself resolves to the worktree,
which is the thing that matters, and the C++ extension is the one built from
this worktree.

## 2. Per-file changes (commit `60c9b98`)

### `src/isalhg/language/consensus.py`

- Module docstring: the objective's third criterion is now the Isal fingerprint;
  new sections say **why the dedup key stays the fact word while the tie break
  does not** (dedup is invariant-neutral, a tie break selects), and what the
  domain is. It also states, in one sentence, that `reach.py` keys remainders on
  the fact word deliberately, so nobody "fixes" that next.
- `IsalKey` = `tuple[VertexLabel, str]`; `ConsensusDomainError(ConsensusError)`.
- `in_language_domain(H)` — `H.n_nodes >= 1 and H.is_connected()`. Both
  conditions, not one; see §5(a).
- `isal_fingerprint(H)` — `canonical_fingerprint_orbit(H)`, i.e.
  `F = (seed label, w*_c)` through the stabiliser-orbit-pruned tie-complete
  search: value-preserving (Prop. 6.0), so this *is* the frozen `w*_c` of D-TA2,
  the article's representation under D-ART5.
- `_Pool` (frozen dataclass) replaces the bare dict returned by
  `_candidate_pool`: `entries` plus `out_of_domain`, the deduplicated keys of the
  classes generated outside the domain. `_candidate_pool` gained one nested
  `offer()` so members and transfers are admitted by the same rule.
- `coverage_consensus`: raises `ConsensusDomainError` when nothing in-domain
  survives; computes `min` over `(-coverage, sum_reach)`, collects the tied
  words, and calls `isal_fingerprint` **only when more than one candidate is
  tied**. `n_ties = len(tied) - 1`, unchanged in meaning.
- `ConsensusResult` gained `origin`, `connected`, `n_disconnected`, `n_excluded`.
- `CandidateScore.word`'s docstring no longer claims it is the tie-break value.

The lazy tie break is the load-bearing design choice: a run with a unique
optimum never canonicalizes with the Isal engine, so it is invariant-neutral by
construction rather than by argument, and it costs nothing (§6.4).

### `experiments/tkde/rq3.py`

- `CONSENSUS_COLUMNS` (the six coverage-only columns) and `NO_CONSENSUS` (their
  blanks). `VARIANT_COLUMNS` and `NATURAL_COLUMNS` splat the former; the seven
  non-coverage row builders splat the latter, instead of repeating four literals
  each.
- `ConsensusOutcome` gained `winner_origin`, `winner_connected`,
  `n_disconnected`, `n_excluded`, with a NumPy docstring it did not have.
- The coverage row writes all four.
- **`run_guarded(..., cpp_engine=True)` on the consensus call**, and its
  docstring corrected — see §5(c). This is not optional bookkeeping: the flag is
  what makes a censored consensus row mean what it says.

### `experiments/tkde/configs/rq3.yaml`

- Corpus A: `consensus_budget_s: null` → `1800`, with the reason in the comment.
  Forced by the change; see §5(c).

### `tests/unit/language/test_consensus_domain_tiebreak.py` (new, 13 tests)

Pins both changes. `old_objective` / `mid_objective` reproduce the two earlier
behaviours by substituting the module-level hooks, so every "before" is the code
as it stood rather than a description of it. Three collections are pinned
(found by a search over random variant collections, seed 20260910): a
disconnected old winner, an **empty** old winner, and a three-way tie the two
words resolve differently. Edge cases parametrized: every candidate out of
domain (raises), single candidate, every candidate tied, a disconnected member
that is a scoring target but not a candidate. The tie-free invariance is
measured over a sample and the sample asserted non-empty.

### `tests/unit/language/test_consensus.py`, `tests/property/test_language_properties.py`

Two existing assertions encoded the old objective; both are corrected, not
weakened — see §5(f) and §5(g).

### `scripts/diagnostics/rq3_consensus_domain_audit.py` (new)

The instrument for §6, alongside the existing
`scripts/diagnostics/rq3_consensus_forensics.py`. It reproduces Corpus A's
construction exactly (`enumerate_units_a`, `eligible_sources`,
`cell_source_window`, `variant_collection`, the runner's seed schedule and
per-unit RNG) and scores each collection under all three objectives. It carries
a self-check that `old_objective` reproduces the pre-change rule
(`min` by `(-coverage, sum_reach, fact word)` over the candidates); the check
passed on all 323 collections.

## 3. Verification — tests

Baseline at `44c48e3`, measured here rather than taken on trust:

```
$ ~/.conda/envs/isalhg-consensus/bin/python -m pytest tests/ -q -p no:randomly
===== 9 failed, 2928 passed, 30 skipped, 21 warnings in 1956.16s (0:32:36) =====
FAILED tests/experiments_tkde/test_rq36_smoke.py::TestUnitEnumeration::test_rq6_units_are_unique
FAILED tests/experiments_tkde/test_rq36_smoke.py::TestModelIsNotSharedAcrossUnits::test_each_call_returns_a_fresh_model
FAILED tests/experiments_tkde/test_rq36_smoke.py::TestModelIsNotSharedAcrossUnits::test_the_fresh_model_samples_identically
FAILED tests/experiments_tkde/test_rq36_smoke.py::TestModelIsNotSharedAcrossUnits::test_a_used_model_is_not_reachable_from_the_context
FAILED tests/experiments_tkde/test_rq36_smoke.py::TestDeployStamps::test_the_stamps_name_the_imported_package
FAILED tests/experiments_tkde/test_rq36_smoke.py::TestEndToEnd::test_rq3_is_idempotent_per_unit
FAILED tests/experiments_tkde/test_rq45_smoke.py::TestSmokeIsolation::test_deploy_stamps_name_both_trees
FAILED tests/integration/test_cpp_orbit_corpus.py::test_orbit_matches_unpruned_wstar_c[wd50k66]
FAILED tests/integration/test_cpp_orbit_corpus.py::test_orbit_matches_unpruned_wstar_c[ndc_classes]
```

(The brief said "~8 pre-existing in `test_rq36_smoke.py` / `test_rq45_smoke.py` /
`test_rq127_smoke.py`". Measured: 9, and none of them in `test_rq127_smoke.py`;
two are in `test_cpp_orbit_corpus.py`, which the brief did not mention.)

Post-change full suite: §7 — **8 failed, 2942 passed**, a strict subset of the
baseline's nine failures.

Targeted suites on the changed tree:

```
$ ~/.conda/envs/isalhg-consensus/bin/python -m pytest tests/unit/language/ tests/property/test_language_properties.py -q -p no:randomly
tests/unit/language/test_consensus_domain_tiebreak.py .............      [ 48%]
======================= 108 passed in 196.12s (0:03:16) ========================

$ ~/.conda/envs/isalhg-consensus/bin/python -m pytest tests/experiments_tkde/ -q -p no:randomly -rf
================== 6 failed, 343 passed in 416.03s (0:06:56) ===================
```

The six are the baseline's six in that directory
(`test_rq3_is_idempotent_per_unit` passes in isolation and fails in the full
run — order-dependent, and it fails at baseline too).

Lint and types on the touched files:

```
$ ~/.conda/envs/isalhg-consensus/bin/python -m ruff check src/isalhg/language/ experiments/tkde/rq3.py tests/unit/language/test_consensus_domain_tiebreak.py scripts/diagnostics/rq3_consensus_domain_audit.py
All checks passed!
$ ~/.conda/envs/isalhg-consensus/bin/python -m ruff format --check ...
11 files already formatted
$ ~/.conda/envs/isalhg-consensus/bin/python -m mypy src/isalhg/language/
Success: no issues found in 6 source files
```

Repo-wide `ruff check` reports 3 errors, all pre-existing and in files this
change does not touch (`iso_backends/isalhg_backend.py:53`,
`viz/instruction_view.py:135`, `tests/unit/core/algorithms/test_registry.py:48`).

## 4. Verification — the fork-health hazard, measured

Three lines in a scratch process: `cpp_fork_is_healthy(recheck=True)`, then one
`isal_fingerprint` on a four-constant path, then `cpp_fork_is_healthy(recheck=True)`
again.

```
fork healthy BEFORE any in-parent canonicalization: True
isal_fingerprint in the parent -> (2, 'V[0;1;1;1];V[1;1;1;1];P[1];V[0;1;1;0]')
the C++ canonicalizer has already run in this process, so a forked child deadlocks on it; every budgeted cpp call here would be reported censored without having been computed
fork healthy AFTER  in-parent canonicalization: False
```

## 5. What in the brief is wrong, or missing

### (a) The domain is not just "connected" — it is connected **and non-empty**

The brief frames item 2 as excluding *disconnected* candidates. Measured, the
domain has two walls, and `canonical_string` raises a different exception at
each:

```
empty               connected= True  -> RAISED DegenerateHypergraphError  canonical_string requires n >= 1; the empty hypergraph (n=0) produces the empty string --- identical to the single-vertex case --- which breaks identity of indiscernibles for d_I.
single-node-no-edge connected= True  -> (1, '')
disconnected        connected= False -> RAISED DisconnectedHypergraphError canonical_orbit requires a connected hypergraph (decision B11)
```

The empty knowledge base is reachable: `A'` may take every fact of the host.
It is not a corner case either — in the random-collection search it **won
outright**, because the empty base is within reach `r = 2` of every two-fact
member and so covers the whole collection while every member covers only itself:

```
=== OLD WINNER OUT OF DOMAIN ===
  member: 4 [(0, [0, 1, 2]), (0, [0, 2, 3])] types [1, 0, 1, 1]
  member: 4 [(0, [1, 2]), (1, [0, 2, 3])] types [1, 0, 1, 1]
  old winner connected: False n_nodes 0 cov 2 sum 4 n_ties 5
  new winner connected: True                cov 1 sum 3 n_disc 10 origin member:1
```

Implemented predicate: `H.n_nodes >= 1 and H.is_connected()`. Both are pinned
(`EMPTY_WINNER` and `DISCONNECTED_WINNER` fixtures). Excluding only the
disconnected ones would have left the worse of the two defects in place.

### (b) The audit number is **zero** on the measured Corpus A subset

The brief expects the exclusion's blast radius to be "the count of
currently-invalid rows … that nobody has". Measured over 323 real Corpus A
collections spanning all 24 cells: **0 out-of-domain winners, on both corpora**,
and `moved_by_exclusion = 0`. The reason is in `variant_collection`'s own
contract — since D-KBf5 every member "stays connected" — and out-of-domain
candidates are generated in quantity (731 classes across the 323 collections)
but are all losers, which is precisely the no-op asymmetry the brief predicted.

So the exclusion is a correctness *guarantee* with a measured cost of nothing
on Corpus A, not a repair of existing rows. That is a weaker claim than the
brief anticipated and it should be stated that way in the ledger. Corpus B is
not covered — §8.

### (c) The change creates a silent-corruption hazard the brief does not mention

With the tie break on `w*_c` the consensus reaches the C++ canonicalizer.
Corpus A runs the consensus **unguarded, in the runner's own process**
(`consensus_budget_s: null`, chosen so `secs` is the method's own time), and
`wstar_orbit` — a `CPP_ENGINE_ARM` — is one of RQ3's medoid arms. The measured
consequence (§4) is that the first tie break of the run would leave every later
guarded fork deadlocking, and `medoid_matrix`'s guarded build is inside the
medoid loop's `except Exception`, so those rows would be written
`censored = 1` **without having been computed**. On the 8,914-row Corpus A that
is a corrupted censoring column, not a crash.

Two things were needed and both are in the commit: `cpp_engine=True` on the
consensus guard (which `run_guarded`'s own docstring demanded — "the flag must
be set the day a consensus key becomes an Isal word"), and a Corpus A budget so
the consensus runs in a child. `_apply_smoke` merges `corpus_a`, so the smoke
inherits it.

While there: `run_guarded`'s docstring asserted that "the medoid loop above,
which does reach the engine through `wstar_rank`, poisons this process before
these calls". **That is false**, and `medoid_matrix`'s own docstring twelve
lines earlier says the opposite and is right: an engine arm's build runs in a
child that then dies, and `censored_members` screens in children too, so nothing
canonicalizes in the parent. Corrected in place. Had the false sentence been
believed, the obvious "fix" would have been to leave `cpp_engine=False` — the
one choice that produces the corruption silently.

### (d) The `n_ties` bound holds, and the invariance is stronger than "at most"

Confirmed in shape on the subset: 301 of 323 collections (93.2 %) at
`n_ties = 0`, against the brief's 94.7 % on the full Corpus A. Stronger than the
brief's phrasing, though: the `n_ties` histogram is **identical before and
after** (the tie break does not change *which* candidates tie, only which of
them is returned), and all 221 tie-free-and-unexcluded collections came out
bit-identical — word, objective values, and the full candidate-score tuple.

### (e) A scope narrowing worth ruling on

D-ART4 (3) reads "candidate key = the Isal string". Taken literally that is the
*dedup* key as well, not only the tie break. The brief narrows it to the tie
break and keeps `fact_word` for keying; I followed the brief, and the narrowing
is defensible — dedup by any complete invariant induces the same classes, while
keying the pool on `w*_c` would canonicalize every candidate (median 118 per
run, max 1,330 — `T-KBf` forensics) instead of the ≤ 6 % that tie. Recorded so
the author can rule rather than inherit it.

### (f) A pre-existing test defect, surfaced not created

`test_consensus.py::TestRecoversTheSource::test_insertion_only_t2` failed after
the change. Attributed by running the three objectives on its own seed:

```
trial 6 REGRESSION
  source connected: False n 8
  old  recovers: True  n_ties 0
  mid  recovers: False n_ties 2 excl 39
  new  recovers: False n_ties 2 excl 39 origin transfer:0,2
  CAUSE: exclusion
```

The source's *compaction* is disconnected — `random_kb` produces one about one
time in eight — so the test was asserting recovery of a knowledge base the
language cannot write, and calling it a success. Fixed by requiring the source
to be writable (`source_is_writable`), which is what Corpus A enforces anyway
(R3, D-KBf5), not by lowering `recovered == trials`. Measured connectivity of
the compacted sources: seed 211 → 8/8, seed 212 → 7/8, seed 213 → 7/8, so
`trials >= 6` still holds without touching the loop count.

### (g) A property test asserted the retired representation

`test_language_properties.py` asserted
`(-coverage, sum_reach, word) == min(... over candidates)` — i.e. that the
winner is the **fact-word** minimum. That is the rule D-ART4 (3) retired. It now
asserts the winner attains the optimum of the first two criteria, is among the
candidates that attain it, and that `n_ties` equals the size of that set minus
one; which of them wins is pinned in the new file, where the tie break belongs.

## 6. Measurements (all made after `60c9b98` was committed)

Command:

```
PYTHONPATH=. python scripts/diagnostics/rq3_consensus_domain_audit.py \
    --collections 400 --seeds-per-cell 2
```

323 collections audited, 24 of 24 Corpus A cells, 2 of 27 seeds per cell,
254.4 s. Full JSON in the run output; the numbers:

### 6.1 The disconnected-winner audit, per corpus

| corpus | collections | old winner out of domain | of which empty | of which disconnected |
|---|---|---|---|---|
| `ndc_classes` | 160 | **0** | 0 | 0 |
| `wd50k66` | 163 | **0** | 0 | 0 |

Out-of-domain candidate **classes generated** and dropped: 407 (ndc) + 324
(wd50k) = 731 across the 323 collections — so the exclusion is doing work, and
all of it on losers.

### 6.2 How many results move, split by cause

| corpus | moved by exclusion | moved by tie break | moved at all |
|---|---|---|---|
| `ndc_classes` | **0** | **7** of 160 (4.4 %) | 7 |
| `wd50k66` | **0** | **6** of 163 (3.7 %) | 6 |
| pooled | **0** | **13** of 323 (4.0 %) | 13 |

Read against the tie counts: 22 collections had `n_ties > 0`, and the tie break
returned a different candidate in 13 of them (59 %). So when it fires it usually
matters, and it fires rarely.

Where the 13 moved *to*, scored on RQ3's own axis (identity-addressed fact
distance to the source):

| corpus | moved | closer to truth | further | same distance | exact recovery gained | lost |
|---|---|---|---|---|---|---|
| `ndc_classes` | 7 | 0 | 1 | 6 | 0 | 0 |
| `wd50k66` | 6 | 3 | 0 | 3 | 3 | 0 |
| pooled | 13 | 3 | 1 | 9 | **3** | **0** |

So on this subset the change is mildly favourable — three recoveries gained,
none lost, nine winners at the same distance as before. **This is not a tuning
claim and must not be reported as one**: n = 13, the objective was fixed in
advance, and nothing about the Isal string was chosen for this outcome. The
useful content is the negative one — moving the tie break to the paper's
representation does not damage RQ3's headline.

### 6.3 `n_ties`, before and after

| corpus | `n_ties = 0` before | after | histogram (identical both sides) |
|---|---|---|---|
| `ndc_classes` | 147/160 (91.9 %) | 147/160 | `{0: 147, 1: 11, 2: 1, 5: 1}` |
| `wd50k66` | 154/163 (94.5 %) | 154/163 | `{0: 154, 1: 7, 2: 1, 3: 1}` |

Tie-free-and-unexcluded collections that came out **bit-identical**: 108/108
(ndc) and 113/113 (wd50k) — 221 of 221. The brief's claim that the fix cannot
move a run with `n_ties = 0` is confirmed, and by construction: the tie break is
never evaluated there.

### 6.4 Cost of the tie break (162 collections, one seed per cell)

```
n_ties == 0: n=152 fact-word median 153.9 ms max 1461.5 ms | isal median 151.1 ms max 1492.9 ms
n_ties  > 0: n=10  fact-word median  60.5 ms max  293.8 ms | isal median  64.0 ms max  305.2 ms
```

Tie-free runs are unchanged (the difference is noise); tied runs pay about
3.5 ms at the median. The 2 h 40 m re-run estimate is unaffected.

### 6.5 The columns, end to end, through the guarded path

```
$ PYTHONPATH=. python -m experiments.tkde.rq3 --config experiments/tkde/configs/rq3.yaml \
      --smoke --out <tmp> --log-level WARNING
```

Corpus A, `rows_variants.csv`, 8 coverage rows, all `censored = 0` — so the
consensus ran in a forked child under `cpp_engine=True` and the canary did not
refuse, which is the config change working:

```
{'method': 'coverage', 'radius': '2', 'censored': '0', 'fact_dist': '0', 'n_candidates': '126', 'n_ties': '0', 'winner_origin': 'transfer:0,1', 'winner_connected': '1', 'n_disconnected_candidates': '0',  'n_excluded_candidates': '0'}
{'method': 'coverage', 'radius': '2', 'censored': '0', 'fact_dist': '0', 'n_candidates': '142', 'n_ties': '0', 'winner_origin': 'transfer:0,1', 'winner_connected': '1', 'n_disconnected_candidates': '10', 'n_excluded_candidates': '10'}
a medoid row blanks: {'n_candidates': '', 'n_ties': '', 'winner_origin': '', 'winner_connected': '', 'n_disconnected_candidates': '', 'n_excluded_candidates': ''}
```

Corpus B, `rows_natural.csv` — two units, and both are worth recording because
§8.1 says Corpus B is unmeasured otherwise:

```
{'T': '14', 'N': '13', 'censored': '0', 'secs': '0.302', 'fact_dist': '2', 'n_candidates': '199', 'n_ties': '0', 'winner_origin': 'member:8', 'winner_connected': '1', 'n_disconnected_candidates': '0', 'n_excluded_candidates': '0'}
{'T': '36', 'N': '35', 'censored': '0', 'secs': '1.478', 'fact_dist': '2', 'n_candidates': '319', 'n_ties': '0', 'winner_origin': 'member:2', 'winner_connected': '1', 'n_disconnected_candidates': '0', 'n_excluded_candidates': '0'}
```

Both return a **member** — the consensus behaving as a medoid on the natural
series, which is the regime `D-KBf5a` gated to the supplement — and neither
generated an out-of-domain candidate. Two of 69 units is not a measurement of
Corpus B, but it is the first evidence either way.

### 6.6 A number RQ3 wanted and could not state

`winner_origin`, now persisted: **302 of 323 (93.5 %)** Corpus A consensus
winners are `transfer:` — an object no member wrote — against 21 (6.5 %) that
are a member. That is RQ3's central claim, previously inferred from the fact
distance rather than reported.

## 7. Post-change full suite

```
$ ~/.conda/envs/isalhg-consensus/bin/python -m pytest tests/ -q -p no:randomly
FAILED tests/experiments_tkde/test_rq36_smoke.py::TestUnitEnumeration::test_rq6_units_are_unique
FAILED tests/experiments_tkde/test_rq36_smoke.py::TestModelIsNotSharedAcrossUnits::test_each_call_returns_a_fresh_model
FAILED tests/experiments_tkde/test_rq36_smoke.py::TestModelIsNotSharedAcrossUnits::test_the_fresh_model_samples_identically
FAILED tests/experiments_tkde/test_rq36_smoke.py::TestModelIsNotSharedAcrossUnits::test_a_used_model_is_not_reachable_from_the_context
FAILED tests/experiments_tkde/test_rq36_smoke.py::TestDeployStamps::test_the_stamps_name_the_imported_package
FAILED tests/experiments_tkde/test_rq45_smoke.py::TestSmokeIsolation::test_deploy_stamps_name_both_trees
FAILED tests/integration/test_cpp_orbit_corpus.py::test_orbit_matches_unpruned_wstar_c[wd50k66]
FAILED tests/integration/test_cpp_orbit_corpus.py::test_orbit_matches_unpruned_wstar_c[ndc_classes]
===== 8 failed, 2942 passed, 30 skipped, 21 warnings in 1955.59s (0:32:35) =====
```

| | baseline `44c48e3` | after `60c9b98` |
|---|---|---|
| failed | 9 | **8** |
| passed | 2928 | 2942 |
| skipped | 30 | 30 |

The eight are a **strict subset** of the baseline's nine, so there are no new
failures. The arithmetic closes exactly: +13 passed from the new test file, +1
from `test_rq36_smoke.py::TestEndToEnd::test_rq3_is_idempotent_per_unit`, which
fails at baseline in a full run and passes now. The plausible reason is the
config change — Corpus A's consensus now runs in a forked child, so the two
runs of the idempotency check no longer differ in in-process state — but that is
an inference from the change, not something this measured, and it is a
pre-existing failure either way.

**Replicated.** The suite was run twice over the same commit, once alongside the
audit / smoke / cost probe and once alone (1955.59 s and 1963.13 s). Both give
**8 failed, 2942 passed, 30 skipped** with the *identical* eight failures, so
the count is not an artefact of load. Mid-run the first attempt looked dead —
its output file sat at 14 % and `ps` showed no `pytest` — and this log first
recorded it as having been killed by memory pressure; **that was wrong**, it was
still running and finished normally. The `ps` reading was the mistake: the
sandbox this agent runs commands in does not list the background job's
processes, so "no process" was not evidence of one. Corrected here rather than
quietly dropped, since the same reading could be used to explain away a genuine
hang.

## 8. Residual risk

1. **Corpus B is not measured.** 69 natural NDC runs, `N` up to 40 over `m` up
   to 110, budgeted at 1800 s each — outside "no heavy compute". Its members
   come from a natural series, not from a generator that guarantees
   connectivity, so out-of-domain candidates (and possibly winners) are more
   plausible there than on Corpus A. The re-run's new columns will say; until
   then §6.1's zero is a Corpus A statement only.
2. **Subset caveat.** 323 of roughly 5,184 Corpus A collections, 2 of 27 seeds
   per cell. Every cell is covered, which is what matters for the deletion
   cells, but a rare event at 1-in-1000 would not appear.
3. **The tie break can now censor.** `w*_c` carries R2's symmetry cost, and a
   symmetric tied candidate could exceed the budget where the fact word never
   would. Measured cost on Corpus A is 3.5 ms (§6.4), and with the config change
   the failure mode is a censored row rather than a hang, but the possibility is
   new.
4. **`n_disconnected` and `n_excluded` are equal by construction** today. They
   are separate fields so that a change of exclusion policy shows up as a
   divergence instead of silently; a reader should not take their equality as
   two independent measurements.
5. **The consensus row still carries `"arm": "fact_rank"`** in `rq3.py`. After
   D-ART4 that label names the retired representation, and it is now doubly
   wrong since the objective's tie break is the Isal string. Renaming it would
   change row identity and break the analyzers and the comparison against the
   pre-`reach'` rows, so it is left alone and filed here.
6. **`T-KBj` (`spawn`) was not touched**, as instructed, and neither were
   `rq1/2/4/5/6/7.py`, `matrices.py`, `budget.py`, `reach.py`'s remainder
   keying, `prose.md`, or any results tree.
