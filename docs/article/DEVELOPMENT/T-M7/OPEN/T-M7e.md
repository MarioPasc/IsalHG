# T-M7e — Design-seeded ladders: Stratum C re-seed + G2/A4 re-run
**Declared:** 2026-07-22 11:56 CEST
**Status:** OPEN
**Depends on:** T-M7a (design seed catalog), T-M2c (connectivity-preserving
edit machinery), T-M5g (G2 pipelines), T-M5e (A4 pipeline).
**Origin:** 2026-07-22 REVIEW pass (`docs/article/REVIEW/DATA.md` §2C, §3),
directed by Mario. Current ladders are seeded from standalone random bases;
re-seeding from Stratum A designs makes A4's decoded intermediates and the G2
symmetric-regime profiles drawable and recognizable, and ties G2/A4 to the
master corpus.
**Context to read first:**
- `docs/article/REVIEW/DATA.md` §2C, §3 (slice map rows G2/A4), §8 (acceptance
  bullets)
- `experiments/article/configs/{g2_sensitivity,g2_ladder}.yaml` — the configs
  to re-point (keep the `qin_edit_cost` budget accounting — HGED-free by
  construction)
- `docs/article/DEVELOPMENT/T-M5/CLOSED/{T-M5g,T-M5e}.md` — the measured
  baselines being superseded and the closing-note format
- `docs/article/theoretical/stability.md` §4.2 — the three-regime prediction
  whose 2/7 falsification the arity-≥4 design cells may resolve
**Description:** Re-seed the perturbation ladders from Stratum A design bases
(one ladder family per admitted design, arities 3–5) plus a matched random
control per size, two seeds each, budgets and rung counts per the existing
ladder protocol. Re-run: (1) **G2 sensitivity** on the design-seeded cells —
including arity-4/5 designs, which exercise the edit types the k=3 cells could
not (the stated suspect for the §4.2 partial falsification; report whether the
heavy-tail prediction revives at higher arity); (2) **G2 ladder response**;
(3) **A4 shortest path** with the design-seeded pool — decoded S2H
intermediates now drawable next to recognizable endpoints. Keep the nauty
contrast in G2. Realized-parameter logging throughout.
**Acceptance:** ladder configs point at catalog-derived bases (no standalone
random bases except the labeled controls); G2 profiles + nauty contrast + ladder
response re-emitted on the new cells with acceptance-rate reporting; the
arity-≥4 sensitivity cells exist and the three-regime confrontation is
re-scored (confirm/falsify per regime, appended to the G2 artifact); A4 re-run
emits monotonicity, recovery, and ≥ 3 decoded intermediates on a design-seeded
path; all prior G2/A4 pins that still apply stay green.
**Out of scope here:** re-running E1′ on catalog-seeded bases (E1′ closed at
S5; `REVIEW/DATA.md` §2D applies only if E1′ is ever regenerated — note this in
the closing note); the G3 experiment (T-M7f); prose folding into
`theoretical/stability.md` §4.2 (doc pass follows the measurement).
