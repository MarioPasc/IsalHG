# T-TBd — Reposition the article: metric-geometry headline, Theorem B as the faithfulness engine
**Declared:** 2026-07-17 20:30 CEST
**Status:** DONE (executed 2026-07-17 by the author, Mario; PI confirmation of the demotion still pending — tracked in DECISIONS.md D-ART1, not here)
**Depends on:** T-TB (CLOSED), T-TBb (evidence base for the demotion); **blocked on PI ratification of D-ART1**
**Delegation:** orchestrator-only
**Why out of scope:** Surfaced in the 2026-07-17 way-forward analysis; changing the article's headline claim is definitional (what the paper asserts), not inline doc-editing, and needs PI sign-off.
**Context to read first:**
- `docs/article/theoretical/stability_reformulations.md` §7 ("Recommended way forward") — the full rationale this task executes
- `docs/article/DEVELOPMENT/DECISIONS.md` D-ART1 — the decision to ratify first
- `docs/article/theoretical/README.md` ("Theorem B — ★ core novelty") — the framing to soften
- `docs/article/theoretical/stability.md` §2 ("the core contribution") — same
- `docs/article/PROPOSAL.md` §1–§2 — the thesis + central claim to re-lead
- `docs/article/DEVELOPMENT/README.md` — critical-path paragraph to update
- `.claude/rules/coding_rules.md` — always
**Description:** Once D-ART1 is ratified, rewrite the thesis so the metric space and its **measured geometry** are the headline, and Theorem B is repositioned as the *faithfulness-characterization engine* (the decomposable window/drift/avalanche error budget + the Δ-decay prediction), still the sibling delta but no longer the sole load-bearing claim. Restate the differentiator vs IsalGraph as "regime-characterized bound + named mechanisms + per-instance diagnostics," not "clean Lipschitz theorem." Soften every "core novelty / core contribution" framing accordingly.
**Acceptance:** `PROPOSAL.md` §1–§2, `theoretical/README.md`, and `stability.md` §2 lead with the geometry; no doc calls Theorem B the sole/core novelty; the sibling-delta wording is the honest form; `DEVELOPMENT/README.md` critical path updated; D-ART1 marked resolved with the executed date.
**Out of scope here:** the geometry CONTENT itself (T-M5f); any proof edit; flipping the distance default (stays raw `d_I`); the transcoding promotion (T-TBc, separately gated).

---
**Closing (2026-07-17):** Executed directly with the author (D-ART1 author-adopted; PI confirmation of the Theorem-B demotion is the only residual, tracked in DECISIONS.md D-ART1). New headline doc `theoretical/geometry.md` written. Reframed to the foundation → geometry → usefulness → faithfulness-bound spine: `PROPOSAL.md` (new §0 premise + spine; §2/§4/§5 re-aimed), `theoretical/README.md` (spine diagram + bullets), `theoretical/stability.md` (§2 capstone, §5 → geometry.md), `empirical/{README,correlation,applications}.md` (Layer→Pillar inversion, applications no longer gated on Theorem B), repo `CLAUDE.md` (thesis + context map + the reasoning-vs-tasks convention). The article-reasoning prose was then de-tagged of process artifacts (task ids / `D-*` / timestamps) per the disentanglement directive; the residual legacy pass (stability.md §6 proof checklist + audit notes → ledger) is filed as **T-TBg**. No code touched; no tests to run.
