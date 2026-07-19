# T-DQ3' — Measure `w*` wall-clock on a HIC instance (real-anchor gate)
**Declared:** 2026-07-08 12:20 CEST
**Status:** DONE (verdict NO-GO — declared fallback applies; closed 2026-07-19)
**Depends on:** T-M0 (DONE — seed-optimized `w*`), T-M4' (HIC loader)
**Note (2026-07-08):** raised in value — since applications are now HGED-free,
`w*` wall-clock is the *only* gate on running MDS/clustering/kNN at real scale,
so this one measurement decides how large the application corpora can be.
**Context to read first:**
- `docs/article/DATA.md` §2 + §6 (DQ3') — why this decides the real anchor (declared fallback recorded there)
- `src/isalhg/datasets/hic_atlas.py` — the (stubbed) loader
- `src/isalhg/core/canonical.py` — the `w*` entry point to time
- `.claude/rules/coding_rules.md` — always
**Description:** Time `canonical_string` on one real HIC IMDB instance (post
T-M0 + C++). One number decides whether a real-world anchor (A1/A2 at scale) is
in scope or the paper stays on synthetic + small designs.
**Acceptance:** a reported wall-clock (seconds/minutes/DNF) on a named HIC
instance, with a go/no-go recommendation for the real anchor.
**Out of scope here:** building the full HIC application pipeline (deferred to T-M5b–e).

---

## Closing note — 2026-07-19 (orchestrator, S2)

**Verdict: NO-GO for HIC as the primary real anchor. The declared fallback
(`DATA.md` §2) applies: the real anchor is the small real designs + the
planted-family corpora, and the applications' claims are synthetic-scale
claims.**

All measurements on `IMDB-Dir-Form` (N=1869 post-LCC instances), default
`algorithm="canonical"` (`w*_c`, C++ variant 7 unless stated), this
workstation (RTX-4060 Debian-12 box, single-threaded CPU encode).

### 1. Corpus-level `k` is structurally out of reach

`d_I` across a corpus needs a common `k` = max arity over the corpus
(`IsalHGLevenshtein._resolve_corpus_k`). For IMDB-Dir-Form that is
**k = 110**, but:
- the C++ encoder is compiled with `K_MAX = 10` (`token.hpp`, PROPOSAL B12)
  → raises `IsalHGError: k exceeds K_MAX`;
- the Python backend at `k=110` on the **median** instance
  (`hic:IMDB-Dir-Form:000429`, n=12, m=26) was killed at **330 s with no
  result (DNF)**.

### 2. The arity-capped sub-corpus (`required_k ≤ 10`, encode at `k=10`)

Survival: **1471/1869 (78.7%)**; per-class retention **89.0% / 71.1% /
71.0%** (label-correlated censoring, must be reported). Named probe
instances (survivor size quantiles):

| instance | n | m | wall-clock |
|---|---|---|---|
| `hic:IMDB-Dir-Form:001481` (median) | 11 | 13 | **0.026 s** |
| `hic:IMDB-Dir-Form:000336` (p90) | 20 | 47 | **0.132 s** |
| `hic:IMDB-Dir-Form:000392` (p99) | 34 | 130 | **DNF > 330 s** |
| `hic:IMDB-Dir-Form:000236` (max) | 46 | 95 | **DNF > 330 s** |

Budgeted sweep (seeded 100-instance sample of survivors, 10 s/instance,
forked workers): **73/100 complete** — t[med 0.007 s, p90 1.37 s, max
9.2 s]; **27 DNF**, and the DNFs are *not* size-concentrated (n=10, m=5
and n=11, m=4 DNF while n=22, m=79 completes; DNF range n∈[10,43]).
The blow-up is automorphism/tie branching on near-symmetric instances —
exactly the redundancy that D-TA2's only sanctioned speedup
(stabiliser-orbit pruning, Prop. 6.0) attacks — so **no size gate separates
feasible from infeasible**, and a wall-clock filter would censor by
structural symmetry. Combined yield ≈ 0.787 × 0.73 ≈ **57%** of the
dataset under two layers of label-correlated censoring: not a defensible
primary anchor.

### 3. Ancillary facts for S4

Arity-cap survival across all 12 HIC datasets (`required_k ≤ 10`):
RHG-Table/Pyramid 100%, RHG-10 89.1%, IMDB variants 74–84%,
Twitter-Friend 63.1%, RHG-3 74.8%, **Steam-Player 24.8%**.

### 4. Re-test condition + PI option

The gate is re-testable after stabiliser-orbit pruning lands (the DNFs are
symmetry-driven, the one value-preserving lever). Separately, a *secondary*
censored-subset HIC exhibit (all representations on the identical computable
subset, censoring reported per class) is a PI decision — filed in
`DECISIONS.md` (OD6), not assumed.

Acceptance clause check: wall-clock on a named HIC instance — reported
(four named instances + DNFs); go/no-go recommendation — **NO-GO**,
fallback executed in `DATA.md` §2.
