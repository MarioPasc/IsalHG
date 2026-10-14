# Wave summary — 2026-09-05-tkde-w2

**Date:** 2026-09-05 · **Orchestrator:** main session `[Experimental-Orchestrator]` · **Integration branch:** `integration/2026-09-05-tkde-w1` (continued) · **Base commit:** `e7f8c0d` (wave 1 merged) · **User prompt:** as in `../2026-09-05-tkde-w1/summary.md` (the campaign prompt; no new user prompt for this wave beyond "Continue" after a rate-limit interruption).

## Agents

| Agent | Model / effort | Branch | Head | Verdict | Log |
|---|---|---|---|---|---|
| `language-layer` | Opus 5 / xhigh | `worktree-agent-a57772af30987b1f0` | `3b88a5e` | ACCEPT | `.claude/notes/2026-09-05-tkde-w2/language-layer.md` |
| `toolkit-stats` | Opus 5 / high | `worktree-agent-a57e8b6abc7474e02` | `1f6b0e7` | RETURN → ACCEPT (four extra arms exercised; pool fix) | `.claude/notes/2026-09-05-tkde-w2/toolkit-stats.md` |
| `competitors-kb` | Opus 5 / high | `worktree-agent-adb65fa32e7e16e2c` | `649b013` | ACCEPT (ownership extended twice on request: ABC + five distance modules for `labels_used`) | `.claude/notes/2026-09-05-tkde-w2/competitors-kb.md` |

All three agents were terminated once by an API session rate limit (17:10 Europe/Madrid reset) and resumed with their transcripts intact; `competitors-kb` had no commits at that point and was instructed to commit first.

Verification per agent (orchestrator, in each agent's own env): clean worktrees; ownership sets exact; `merge-base --is-ancestor e7f8c0d` true; tests re-run — language 76 (unit + property), toolkit 141, competitors 193 (+ 481 across `tests/unit/metric_space`).

## Interventions

- `competitors-kb`: `labels_used` goes on the ABC with explicit values on the six arms outside its original ownership (grant), then `qin_hged.py` (second grant); aliases accepted; the cache keys off the requested arm name (relayed to `toolkit-stats`, who added `canonical_name` to the manifest).
- `language-layer`: my contract capped alignments at `|A|+|B| ≤ r`, which provably excludes the source at `t = r`. Ruled the **triangle-complete** budget `|A|+|B| ≤ 2r` as the default (DESIGN.md RQ3 amended, `679cfb0`); "per_side" and "sum" kept as recorded variants.
- `toolkit-stats`: accepted "one registered name per parameterisation" (registry has no params); RETURN to exercise `nauty_levi_edit`, `netlsd_l2`, `hpd_jsd`, `bipartite_hged` through `build_matrix` (all completed; fork-sharing fix applied).

## Merge record

```
29c0614 merge(toolkit-stats)
84e04da merge(language-layer)
57409b2 merge(competitors-kb)
8984388 docs(design): RQ2 exactness-at-zero column, process-level bounds, zero tolerance
9f973af fix(integration): serialise labels_used (frozenset) in the matrix cache manifest
```
Full verification at `57409b2`: unit 1,979 passed / 6 failed (all six = the `labels_used` JSON serialization conflict between the two branches; fixed in `9f973af`, 189 affected tests re-run green); property 119 passed; ruff 1 pre-existing finding; mypy 20 pre-existing errors in untouched core files. Semantic conflict recorded as a decomposition defect: a manifest field introduced by one agent and typed by another — the frozen contract should have fixed the JSON type of `labels_used`.

Picasso: `sync_to_picasso.sh --corpora` deployed `57409b2` + the six frozen corpora; remote rebuild verified (`cpp == python OK`); `9f973af` re-synced after the fix.

## Measured facts worth keeping (from the logs)

- Coverage consensus (triangle default): source recovery ins 240/240, del 191/196, mix 240/240; 1.55 s median per collection at `N = 9`, `t = 2`, `n = m = 10`; 971/971 alignment interiors decode on real words (connected 32 % WD50K, 53 % NDC).
- Complete arms: 0 false merges, 100/100 isomorphic pairs at 0 on both collections. False-merge rates (wd50k66 / ndc): hpd 2.40 / 1.42 %, size 2.00 %, degree_seq 1.20 / 1.01 %, netlsd 1.00 / 0.81 % (with the 1e-9 tolerance; 20× fewer with `== 0`), bipartite_assign 1.20 / 0 %.
- `bipartite_ged_path` is at 0 on only 8/100 and 19/100 isomorphic pairs: false separations; it does not respect isomorphism classes.
- The pointer alphabet's C++ call and the exact oracles cannot be bounded by `SIGALRM` or their own timeout: process-level kill is mandatory.
- HyperCOT: 3.46 on an isomorphic pair (convergence failure), small negatives elsewhere; 568 ms per pair.
- n-gram over fact words: 1,000/1,000 decode on both collections (novelty 0.99); flat incidence baseline rejects 98–99 % (out-of-range ids dominate).
- Matrix builder on 200 members: fact_rank 13 ms, WL 0.23 s, nauty bytes 0.31 s, bipartite 0.80 s, HPD 3.4 s, NetLSD 9.5 s.

## Open follow-ups

- Scratch caches left by `toolkit-stats` under `results/IEEETKDE/matrices/_dev_toolkit*` (deletion denied to the orchestrator; user to remove).
- `variant_collection` drops many `del, N = 9, t = 1` collections; runners count drops.
- `n_ties` convention: candidates equal to the winner on `(coverage, sum_reach)`.
- The integration branch has still not been merged into `main` (user's call).
