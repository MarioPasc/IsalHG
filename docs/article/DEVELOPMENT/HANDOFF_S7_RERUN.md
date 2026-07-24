# S7 handoff — powered re-run on the corrected corpus

**Written:** 2026-07-24, at the end of the S7 data-correction phase.
**Audience:** the agent picking up the S7 powered re-run.
**Status of this doc:** point-in-time handoff. The ledger
(`README.md`, `T-M7/`, `T-M8/`) remains the authority; where they disagree, the
ledger wins.

---

## 1. Where the work stands

The S7 *data-correction* phase is **complete and merged**. The corpus the
article uses is now finalized, documented, and green (`main`, 1430 tests pass;
ruff 3 / mypy 21 are the standing pre-existing baselines — match them, do not
"fix" them).

What was corrected, and why it matters:

| Task | Outcome |
|---|---|
| `T-M7m` | **Pruned** 9 highly-symmetric families (6 feasibility-DNF planes/large-Steiner + 3 perturbation-failing complete uniforms). Added `DATA_MANIFEST`, coarse structural classes, fixed the Chung–Lu arity-cap bug. |
| `T-M7o` | **Arity-cap bug fixed.** `PlantedFamilyDataset` hard-capped edit arity at `k=3`, so *every* perturbation of a k=4/5 seed was rejected — that, not symmetry, is why arity-4/5 families collapsed to one member. Per-family `k` now = the seed's max arity. Added 3 longer tight cycles. **All 17 families now realize 5 members across arity 3/4/5.** |
| `T-M7p` | **Degree-matched corpus: investigated, proven impossible, dropped (PI).** No corpus can be simultaneously degree-matched, non-isomorphic within class, and separable at ARI ≳ 0.5 for regular trivially-labelled hypergraphs — WL is blind (regular + trivial labels ⇒ one colour) and IsalHG's **avalanche** drowns the separation (a 2-edge degree-preserving swap relabels ~30 of ~50 tokens; max ARI 0.234 over 4 constructions). The impossibility is the deliverable; the code was **not merged**. |
| `T-M7h` | **Stratum B feasibility envelope FINAL.** See §2. |
| `T-M8e` | `REVIEW/DATA.md` + `DATA_RIGOR.md` updated with the prune, the hypergraph figures, and the synthetic-vs-real framing. |
| `T-M7n` | Power pilot: **S = 27 seeds** for 80 % power; cost ≈ 2.3 h effective on 32 A100s. Also surfaced the degree confound (§3). |

## 2. The measured feasibility envelope (do not re-litigate)

`experiments/article/stratum_b_feasibility_envelope.json` — `envelope_final: true`.
**10 admitted, 15 cluster-excluded, 0 pending.**

Admitted Stratum B cells: `k3_n8_{rho1,rho2,rho4}`, `k3_n16_{rho1,rho2,rho4}`
(local) + `k3_n24_{rho1,rho2}`, `k5_n8_{rho1,rho2}` (cluster-measured).

Two cluster rounds produced this: array **1629486** (3 h) harvested 7 blocks;
array **1631517** (8 h) — the 12 hardest blocks — **all 12 TIMEOUT at 08:00:23,
zero results**, so they are recorded as measured-infeasible.

**The finding to report, not hide:** the `w*_c` feasibility frontier is
**k = 3 up to n ≈ 24 (low density), and k = 5 only at n = 8**. The advertised
arity cap of 10 is *not* reachable at any tested n — k=7 and k=10 are measured
infeasible. This is the article's scalability envelope.

## 3. Two findings that constrain what the paper may claim

1. **A2/A3 on the design families is degree-solvable.** The naive
   degree-sequence baseline **beats** IsalHG on both clustering (ARI 0.482 vs
   0.297) and kNN (AUC 0.957 vs 0.859); NetLSD also beats it. The families
   separate on degree alone. Evidence: `artifacts/power_pilot/REPORT.md` §2.3.
2. **A degree-controlled fix is impossible** (T-M7p, above) and was dropped.

**Agreed framing (PI):** report A2/A3 **honestly** — IsalHG competitive, the
naive baseline and NetLSD win where the designs also differ in degree — and lead
the usefulness claim on **A4** (decodable + navigable intermediates, a
capability no competitor has) and the **capability matrix**. Do **not** claim
A2/A3 task dominance. This is consistent with D-ART2 and with the pre-existing
article framing.

## 4. What to do next (the actual job)

**Goal:** re-run the HGED-free body on the corrected corpus at powered N, on
Picasso, then fold the measured numbers into the prose.

1. **Regenerate the sbatch task lists.** `slurm/T-M7d_launcher.sh`,
   `T-M7d_worker.sh`, `tasks_fast.tsv`, `tasks_slow.tsv` were generated against
   the *pre-prune* corpus (11 cells, arity-3 fallback, 5 representations). They
   must be regenerated for: the **17-family** Stratum A + the **10 admitted**
   Stratum B cells, **7 representations**, **S = 27** seeds. The sweep runner
   reads the catalog and the envelope at runtime, so the corpus follows
   automatically — it is the *task lists* that are stale.
2. **Validation pass first:** submit at **S = 8** (≈ 0.7 h) to shake out harness
   bugs, confirm all 7 representations flow and the stats attach, then the full
   **S = 27** run (≈ 2.3 h).
3. **Also re-run G2/A4 (the T-M7e pipelines) and G3 (T-M7f)** on the pruned
   design-seeded ladders — their prior result dirs were archived as superseded.
4. **Harvest → fold into prose.** Only artifact tables/curves are produced by
   the runner; the prose pass into `empirical/applications.md` and
   `theoretical/geometry.md` is separate work.
5. **Then** the still-open items: `T-M7g` (real anchor), `T-M8b` (capability
   matrix figure — now the load-bearing usefulness exhibit), `T-M8d`
   (reproducibility artifact, orchestrator-only, last).

## 5. Landmines

- **Worktree base.** A worker once forked from a 4-day-old commit and silently
  rebuilt an obsolete corpus. Make every worker verify
  `git merge-base --is-ancestor <current main> HEAD` **before** working.
- **Bits counting** goes through the bracket-aware parser. A raw
  `w.split(";")` overcounts ≈2× and has *reversed* the bits conclusion twice.
  Reuse the pinned T15 regression tests.
- **Index family.** Never pool raw `d_I` across different `k`. Compare
  dimensionless descriptors and within-`k` rankings only. A guard
  (`assert_single_arity_group`) exists — keep it.
- **E1′ is frozen.** Do not re-open the exact-HGED oracle (>100 GB / 18 h).
- **Heavy compute goes to Picasso** via the `picasso-sbatch` skill; pilots stay
  local.
- **Archived, not deleted:** the superseded N=60/N=240 result dirs are under
  `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/superseded/`. The
  frozen E1′ (`T-M5a`) and the envelope (`T-M7h`) are still live.
- **Ledger counts** in `DEVELOPMENT/README.md` drift constantly. Reconcile them
  against the filesystem at merge; workers should not edit them.
