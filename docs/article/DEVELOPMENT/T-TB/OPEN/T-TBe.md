# T-TBe — Crossing-peak conjecture: bound `max_u X(u)` for `w*_c` (stretch theory)
**Declared:** 2026-07-17 20:30 CEST
**Status:** OPEN
**Depends on:** T-TBb (conjecture stated; probe data exists)
**Delegation:** agent
**Stretch / non-blocking.** Does not gate any experiment; strengthens the raw-metric drift story only partially.
**Note (D-ART2, 2026-07-18):** demoted further — with the conditional-bound
program out of the article, this serves follow-up work only. Work it after
every article-critical task, or not at all.
**Why out of scope:** Surfaced in the 2026-07-17 way-forward analysis; it is the one remaining clean theoretical question about the raw metric's pointer-run drift, but the article does not depend on it.
**Context to read first:**
- `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/proofs/stability/pointer_run_amortization.tex` — `conjecture:peak` (statement + Rosenkrantz–Stearns–Lewis rationale) and §Measured (probe: `max_u X(u) ≈ Δ` on random instances)
- `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/proofs/stability/theorem_b_stability.tex` — Def. layout (iv) span-boundedness, Thm. averaging
- `scripts/probe_pointer_runs.py` — `boundary_crossings` measurement to extend
- `docs/article/theoretical/stability.md` §2.2 — (iv) status
- `.claude/rules/coding_rules.md` — always
**Description:** Prove or refute `max_u X(u) = O(k(Δ + log m))` for `w*_c` on connected `H` (the total unit crossings of any single CDLL boundary). If proved, span-boundedness (iv) holds unconditionally for vertex insertions in the **raw** metric — `T_span` is bounded without transcoding — tightening the raw drift story. Must handle multi-head gathers and C-candidacy availability dynamics (the two gaps flagged in the conjecture). **Note the ceiling:** this bounds `T_span` only; `R(e)` (orphaned introducer, T-TBc territory) remains `Θ(n)` in the raw metric, so proving (iv) does *not* by itself clean up the raw worst-case bound.
**Acceptance:** a proof or an explicit bounded-degree counterexample family in the proofs volume; `stability.md` §2.2 (iv) status updated; if refuted, the consequence for the paper's raw-metric claim written down.
**Out of scope here:** run-locality (v) / `R(e)` (transcoding, T-TBc); B-avg; any change to `w*_c`; running E2b (only its `X(u)` logging spec, already in the probe).
