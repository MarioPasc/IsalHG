# T-TB — Stability (Theorem B) incl. Lemma B1
**Declared:** 2026-07-08 12:20 CEST
**Status:** OPEN
**Depends on:** T-TA (metric property), informed by T-M5a (empirical `s(e)` data)
**Context to read first:**
- `docs/article/theoretical/stability.md` §2–§4 — statement, reduction, avalanche, theory↔empirics
- `docs/article/RELATED_WORK.md` — TMD (proof template), co-OT (Levi-Lipschitz), FSW-GNN (one-sided justification)
- `src/isalhg/core/hypergraph_to_string.py::_encode_from`, `src/isalhg/core/cdll.py` — the CDLL-index hazard (Lemma B1)
- `.claude/rules/coding_rules.md` — always
**Description:** Prove `d_I(H,H') ≤ C(k,Δ)·HGED(H,H')`; resolve Lemma B1's
CDLL-index hazard (relative vs absolute order); if the worst-case bound is
unattainable, prove the average-case / high-probability form.
**Acceptance:** a written proof (or conditional/average-case theorem) whose
predicted `C(k,Δ)` Δ-dependence matches the T-M5a density-sweep data.
**Out of scope here:** implementing the experiments (T-M5a–e).
