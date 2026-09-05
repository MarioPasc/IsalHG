# hpd-fix — single-hyperedge IndexError in the vendored HPD portrait

## Identity

- Agent: `hpd-fix` (wave 3, TKDE campaign). Orchestrator: `main`.
- Worktree: `/home/mpascual/research/code/IsalHG/.claude/worktrees/agent-ab2a7d8f76f4c34bf`
- Branch: `worktree-agent-ab2a7d8f76f4c34bf`
- Base SHA: `55ec11f33d0b26ffc3db0b5b40a1580a01cc2aeb`
- Env: `~/.conda/envs/isalhg-hpdfix` (cloned from `isalhg`, `pip install -e ".[dev]"` inside this worktree)
- Declared: 2026-09-05 23:36 CEST

## Understanding

`hyperedge_portrait` in `src/isalhg/metric_space/representations/_hpd_vendor.py`
raised `IndexError: index 1 is out of bounds for axis 0 with size 1` on some
CORRUPTED `ndc_classes` records produced by the RQ4 anomaly-injection
experiment. Pristine members never crashed and the wave-2 competitor audit
never scored corrupted inputs, so the defect had never been exercised.

The `axis 0` in the message is a red herring: the write site is the chained
index `B[m][n][l][k] += 1`, and each `[...]` step produces a fresh view whose
*own* axis 0 is the next dimension of `B`. Every out-of-bounds write on any of
the four dimensions therefore reports "axis 0". The reported extent (`size 1`)
is the only usable signal, and it points at the last dimension.

## Root cause

`B` is allocated as `np.zeros((s_max - 1, s_max - 1, dia + 1, N))`, where `N =
G.number_of_nodes()` is the number of hyperedges of `H` (the line-graph
`H_to_G_mapping(H)` has one node per hyperedge). The index written into the
last axis is `k = counter[n][l]`, the number of hyperedges of size `n + 2` at
line-graph distance `l` from hyperedge `i` — so the extent must bound `k`, not
`N`. The tight bound is `max(1, N - 1)`, not `N - 1`: at `l = 0` the bin
contains `i` alone (`k <= 1`), and at `l >= 1` it excludes `i` (`k <= N - 1`).
The required extent is therefore `max(1, N - 1) + 1 = max(N, 2)`. Upstream's
`N` is exact for every `N >= 2` and **one short at `N == 1`**, where the lone
hyperedge counts itself and writes `k = 1` into an axis of extent `1`.

Offending shapes on the pinned real record (`ndc_classes`, `kb_id = "3@401"`,
corruption `missing_fact` at `budget = 2`, `seed = 0`): the member carries
three facts; dropping two leaves the single fact `(0, (0,1,2,3,4,5))` over
`n = 6` constants, i.e. one hyperedge of size 6. Then `N = 1`, `s_max = 6`,
`dia = 0`, so `B` is allocated `(5, 5, 1, 1)` while the write is
`B[4][4][0][1]` — index `1` against the last axis of extent `1`.

Measured over the frozen `ndc_classes` corpus with all four corruptions at
budgets 1 and 2 and three seeds: **2,577 of 30,178 realised corruptions
crashed, and the crashing set is exactly the set with `N == 1`** (the `n_edges`
histogram's `N = 1` bucket is 2,577, identical to the failure count). All of
them are `missing_fact` at `budget = 2` acting on the 859 members that carry
exactly three facts. No other corruption, budget, or record shape fails, and
no corrupted record reaches `N == 0`.

## Changes

`src/isalhg/metric_space/representations/_hpd_vendor.py`

- Allocation changed to `max(N, 2)` on the `k`-axis, with an inline comment
  deriving the `max(1, N - 1)` bound and naming the upstream assumption it
  repairs. `max(N, 2) == N` for every `N >= 2`, so this is a no-op on every
  portrait upstream could already compute.
- Adaptation 9 added under the MIT provenance header recording the fix; the
  old "no other changes" clause renumbered to 10 and amended.

No change to `hpd.py`, to the HPD parameters, or to the JSD distance itself.

## Tests

New file `tests/unit/metric_space/test_hpd_single_hyperedge.py` (17 tests).

The "before" side is `_upstream_hyperedge_portrait`, a frozen verbatim copy of
the upstream body carrying the original `N` extent, kept local to the test
rather than loaded from `git show HEAD:...`. Reason: this branch will be
merged, at which point `HEAD` contains the fix and a git-sourced reference
would silently become a tautology. The frozen copy is stable under merge and
under rebase.

1. `TestSingleHyperedgeCrash` — the pre-fix body raises the exact
   `IndexError: index 1 is out of bounds for axis 0 with size 1` on the
   smallest hand-made trigger (one 2-node hyperedge), on an arity-3 single
   edge, and on the pinned real `ndc_classes` offender; the shipped body
   returns a portrait of the derived shape `(a-1, a-1, 1, 2)` with the lone
   hyperedge at `(m, m, 0, 1)`. The `pairwise` and `matrix` paths are exercised
   too: an `N = 1` portrait survives `pad_h_portraits` and yields a finite,
   symmetric, zero-diagonal matrix.
2. `TestPortraitUnchangedForComputableInputs` — element-for-element equality
   (shape, dtype, values) between the pre-fix and shipped bodies over a
   deterministic synthetic corpus with `N >= 2`, over **all** 1,381
   `ndc_classes` members, and over the first 50 members of each of the six
   frozen collections. The corpus-backed tests skip when the drive is not
   mounted; the synthetic one always runs.
3. `test_pinned_offender_matches_the_frozen_corpus` — reconstructs the offender
   by running `corrupt(record, "missing_fact", 2, 0)` on `kb_id = "3@401"` from
   the frozen corpus and asserts it equals the inline fixture, so the pinned
   record cannot drift away from what RQ4 actually produces.

Verbatim pass line, `~/.conda/envs/isalhg-hpdfix/bin/python -m pytest tests/unit/metric_space/ -q`:

```
================== 467 passed, 1 skipped, 2 warnings in 9.59s ==================
```

`ruff check` on the three touched files: `All checks passed!`
`mypy src/isalhg/metric_space/representations/`: `Success: no issues found in 10 source files`
(unchanged from base — `_hpd_vendor.py` carries `# mypy: ignore-errors` as vendored code).

## Verification beyond the tests

Sweep script (scratchpad, not committed):
`/tmp/claude-1000/-home-mpascual-research-code-IsalHG/968d7c55-7aac-4378-b6a1-ebe4c7508734/scratchpad/sweep_hpd.py`

HPD run over every RQ4 corrupted variant of `ndc_classes` — all four
corruptions (`spurious_fact`, `missing_fact`, `wrong_argument`, `iso_twin`),
budgets 1 and 2, five seeds (0–4), all 1,381 members:

```
[sweep] corrupted ndc_classes records exercised : 52813
[sweep] corruptions that could not be realised  : 2427
[sweep] exceptions                              : 0
[sweep] per (kind,budget) : {('iso_twin', 1): 5940, ('iso_twin', 2): 5940,
                             ('missing_fact', 1): 6905, ('missing_fact', 2): 6905,
                             ('spurious_fact', 1): 6905, ('spurious_fact', 2): 6905,
                             ('wrong_argument', 1): 6663, ('wrong_argument', 2): 6650}
[sweep] n_edges histogram (low) : [(1, 4295), (2, 6010), (3, 17064), (4, 11784), (5, 8322)]
[sweep] minimum hyperedge size seen : 2
[sweep] finite HPD distances (pristine vs missing_fact b2 s0) : 200
```

**52,813 corrupted records exercised, 0 exceptions** (4,295 of them at `N = 1`,
the formerly crashing shape). The 2,427 `None` returns are corruptions
`corrupt()` itself declined to realise, not failures.

Pristine byte-identity re-checked outside pytest over every member of all six
frozen collections — 15,505 members, no portrait changed:

```
[identity] ndc_classes:   1381 members, 0 portraits changed
[identity] ndc_substances:1745 members, 0 portraits changed
[identity] synthetic_rq1: 2000 members, 0 portraits changed
[identity] wd50k100:      1837 members, 0 portraits changed
[identity] wd50k66:       3988 members, 0 portraits changed
[identity] wd50k66_full:  4554 members, 0 portraits changed
```

## Deliberately not done

- **The size-1 hyperedge wraparound is NOT fixed.** `m = sizes_dict[i] - 2`
  goes negative for a hyperedge of size 1, and Python's negative indexing
  silently folds it onto the size-`s_max` slice instead of raising. No
  exception, wrong portrait. It never fires on these corpora — the sweep
  measured a minimum hyperedge size of 2 across all 52,813 corrupted variants
  — and repairing it would change portraits for any future input that does
  carry an arity-1 fact, breaking the byte-identity guarantee this task was
  scoped around. Flagged for the orchestrator; out of scope here.
- **Edge-less hypergraphs (`N == 0`) still raise**, via `max(lengths)` on an
  empty set (`ValueError`), not the `IndexError` fixed here. `hpd.py` documents
  "each must have at least one hyperedge", and no RQ4 corruption at budgets 1–2
  reaches `N == 0` (min facts per `ndc_classes` record is 3). Left alone.
- Nothing under `experiments/`, `slurm/`, `scripts/`; no other representation;
  no RQ4 re-run; no Picasso work. HPD parameters and the JSD distance untouched.

## Risks

- Low. The fix widens one array axis by one element in exactly the case that
  previously raised, and is provably identity-preserving elsewhere
  (`max(N, 2) == N` for `N >= 2`), which the 15,505-member sweep confirms
  empirically.
- Downstream consumers of `hyperedge_portrait` that assume `B.shape[3] ==
  H.num_edges` would now see `2` instead of `1` at `N = 1`. The only in-repo
  consumer is `pad_h_portraits`, which trims the `k`-axis to the last non-zero
  column before the JSD and is therefore unaffected. No other call site exists.
- RQ4 results computed before this fix, if any HPD numbers were recorded on
  corrupted `ndc_classes` inputs, are incomplete rather than wrong — the cells
  crashed rather than producing bad values. The orchestrator should re-run
  RQ4's HPD arm on `ndc_classes` (and check `ndc_substances`, whose fact counts
  I did not survey).
