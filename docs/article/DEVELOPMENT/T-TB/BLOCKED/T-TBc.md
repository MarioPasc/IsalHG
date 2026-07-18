# T-TBc — Displacement-token transcoding of `w*_c`: discharge run-locality, drop the n-factor
**Declared:** 2026-07-17 19:56 CEST
**Status:** BLOCKED (D-ART2, 2026-07-18 17:56 CEST — pending PI)
**Depends on:** T-TB (CLOSED), T-TBb (closed at commit `e6b0af7`, **unmerged** into `perf/canonical-complete-orbit-pruning` — reconcile first, T-TBf), D-ART2 ratification
**Blocked note (2026-07-18):** D-ART2 retired the v2-scale correlation study
that was this ablation's measurement vehicle (`ρ(HGED, d_I')` vs `ρ(HGED, d_I)`
on the pinned T-M5a corpus). The remaining in-article vehicle is the small E1'
mini-corpus — probably too small to resolve the question. Since the
displacement idea is the PI's own (email 2026-07-17), the task is **parked,
not deleted**: it unblocks if the PI either sanctions running the ablation on
the mini-corpus + task-metric axes (does `d_I'` change `D̂`/ARI/accuracy?) or
defers it to the follow-up paper. See D-ART2 ratification point (d) in
`../../DECISIONS.md`.
**Why out of scope:** Found during the 2026-07-17 stability-value discussion (PI email on arithmetic-coded displacements); the current session is chat/documentation, not proof or code work.
**Context to read first:**
- `docs/article/theoretical/stability_reformulations.md` §4 — the full analysis this task executes
- `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/proofs/stability/pointer_run_amortization.tex` — Prop. orphan (the counterexample this recoding collapses), Thm. averaging, conj. peak
- `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/proofs/stability/theorem_b_stability.tex` — Lemma length, Thm b-worst, Def. layout (iv)–(v)
- `src/isalhg/core/instructions.py` + `src/isalhg/core/hypergraph_to_string.py` — unary `P/N` semantics; movement-block grammar (one unidirectional arc per pointer, deterministic rendering order)
- `docs/article/theoretical/stability.md` §1 (D-TA2 freeze) — why the transcoder must be post-canonical
- `.claude/rules/coding_rules.md` — always
**Description:** Define the injective post-canonical transcoder `T` (movement block → displacement tokens `D(l,δ)`) and `d_I' := d_Lev ∘ T`, leaving the frozen `w*_c` untouched. Theory: (a) completeness transfer (one-line injectivity argument over the augmented fingerprint); (b) B-worst′ `d_I' ≤ (1+k)·max(m,m')·HGED` via `|T(w*_c)| ≤ m(1+k)`; (c) restate Lemma B1/B-cond over `d_I'` with `R'(e) ≤ k(1+Δ)` proved unconditionally — hypothesis (v) becomes a lemma; (iv) reduces to the crossing peak `max_u X(u)` (conj. peak). Empirics: implement the Prop.-orphan family generator and assert `s'(e) = O(kΔ)` where `s(e) = Θ(n)`; rerun the T-TBb probe transcoded, including a larger-`n` re-fit of the `M/n` growth law (the `n^0.75` claim rests on a 4× range); measure `ρ(HGED, d_I')` vs `ρ(HGED, d_I)` on the same pinned instances. Ablation: unit vs magnitude-weighted substitution cost (token-space cost must be a metric; Gray-coded bit-level variant is the comparison point). Promotion of `d_I'` to the article's primary distance is a **PI decision** — file it in `DECISIONS.md` with the measured evidence, do not flip defaults.
**Acceptance:** proofs written to the external proofs volume; transcoder + `d_I'` in `metric_space/` with unit tests (round-trip `T⁻¹∘T = id` on encoder outputs; orphan-family sensitivity collapse pinned); probe rerun table (unary vs transcoded) committed; `DECISIONS.md` entry for the primary-distance promotion; `stability.md` §2.2/§6 updated to record which hypotheses `d_I'` discharges.
**Out of scope here:** any change to the frozen `w*_c` or the key cascade (D-TA2); the arithmetic-coding bits estimator (T-M4a); block-move edit distances; the structure-first tour variant (`stability_reformulations.md` §5, recorded not tasked).
