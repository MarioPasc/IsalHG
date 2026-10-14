# Draft spawn prompt — wave 2 (`harness-isal`), to be sent after wave 1 merges

*Orchestrator draft, 2026-09-06. Fill BASE_SHA with the merge commit of wave 1
on `feature/isal-kb-word`; WAVE_ID = `2026-09-06-isal-kb-w2`. One agent,
opus5-xhigh, model pinned `opus`, `isolation: worktree`. Same standing
obligations, bootstrap (`isalhg-harness` env), log template and final-message
format as the wave-1 prompts (copy from `summary.md` / the wave-1 prompts).*

## Mission
Register the Isal arms in the TKDE harness so that every RQ runner can produce
an Isal row, and run the RQ1 measurement locally on subsamples end to end.
Arms: `isal_ow_struct`, `isal_ow_rank`, `isal_ow_rank0` (ordered walk; fast;
`get_distance(name).fingerprint(H)` returns the seed-prefixed token tuple),
`wstar_rank` (`iso_backends/orbit_oracle.py::canonical_fingerprint_rank`,
Python greedy, ms), `wstar_orbit` (`canonical_fingerprint_orbit`, Python
tie-complete with the oracle — needs the forked-child budget), beside the
existing `isalhg_levenshtein` (= `wstar`, C++ 60 s), `nauty_cert`,
`nauty_cert_rows`, `fact_rank` (record only).

## Ownership
- `experiments/tkde/matrices.py` (WORD_ARMS + DEFAULT_SPECS for wd50k66,
  ndc_classes, wd50k100), `experiments/tkde/rq1.py` (+ `analyze_rq1.py`,
  `configs/rq1.yaml`), `experiments/tkde/rq7.py` (+ config: the `|Aut|` axis
  from `pynauty.autgrp` on the coloured Levi graph), `experiments/tkde/rq3.py`
  (`MEDOID_ARMS`), `rq4.py` (`DEFAULT_ARMS`, `EXACT_ARMS`), `rq6.py`
  (`_ow_word`, interiors for the OW word; an n-gram generator over the OW
  token alphabet mirroring `fact_ngram`, validity by `S2H` + connectivity
  check), `experiments/tkde/budget.py` (a `python_word(H, fn, seconds)`
  forked-child wrapper generalising `pointer_word`; instruction-granularity
  distance beside `symbol_distance`), `slurm/tkde/rq1_*` launcher/worker if
  the arm list is baked there, tests under `tests/unit/experiments/` (if that
  tree exists; else `tests/integration/test_tkde_arms.py`), the log.
- Read-only: everything under `src/isalhg/` (wave 1 owns it; propose changes
  to `main`).

## Frozen contracts
- RQ1 `member_word(arm, H, roles, *, k, budget)`: OW arms → `fingerprint(H)`
  (no budget needed; time it); `wstar_rank` → `python_word` with the budget;
  `wstar_orbit` → `python_word` with the budget; distances via
  `symbol_distance` on the symbol tuples AND at instruction granularity
  (one symbol per token — for the OW/wstar arms the fingerprint tuple already
  is instruction-granular; the campaign's field-split `pointer_symbols`
  granularity is the second column). Report both; L11 raw first.
- New M1 columns: `zero_shift` (nauty order intact under the edit — compare
  `canonical_ranks` restricted to surviving constants), `aut_bucket`
  (`|Aut|` of the coloured Levi graph: <10³, 10³–10⁶, ≥10⁷), `n_instr`.
- Censoring: per (arm, m-bucket, |Aut|-bucket), L15.
- Nothing about the retired addressing arms is removed (D-ART4 (1)).

## Definition of done
1. `python -m experiments.tkde.rq1 --config configs/rq1.yaml --limit 60`
   (or the runner's subsample flag) runs locally end to end on the three
   corpora with all arms and writes `tables.md`/`stats.json`/`manifest.json`
   under a scratch results root; numbers reported in the log (M0, M1 medians
   per arm and regime, M3 medians, censoring).
2. `matrices.py` builds an N×N `isal_ow_struct` matrix for `ndc_classes`
   (N = 1,381) locally; time reported.
3. RQ3/RQ4/RQ6/RQ7 runners accept the new arms (smoke on ≤ 30 members each).
4. The RQ6 OW n-gram generator samples 1,000 words; validity 1,000/1,000 and
   connectivity 1,000/1,000 by construction (Prop. C.4) — assert.
5. Tests; lint; log; commits.

## Then (orchestrator)
Sync the branch to Picasso (`scripts/tkde/sync_to_picasso.sh`; FSCRATCH file
count is over the soft quota — check `quota` first; results root on HOME),
submit RQ1 with `picasso-sbatch`, harvest, select by the pre-registered rule,
then RQ2–RQ7 with the adopted arm.
