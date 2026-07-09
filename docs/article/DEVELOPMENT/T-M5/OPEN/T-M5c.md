# T-M5c — Clustering + dendrogram (HGED-free)
**Declared:** 2026-07-08 13:40 CEST (split from T-M5)
**Status:** OPEN
**Depends on:** T-M1b, T-M3a–d, T-M4 (+ T-M4' for the real anchor)
**Context to read first:**
- `docs/article/empirical/applications.md` §A2 — k-medoids + dendrogram, metrics
- `.claude/rules/coding_rules.md` — always
**Description:** k-medoids (PAM) + agglomerative dendrogram on `D_I` and
competitors; silhouette/Dunn/DB + ARI/NMI vs planted labels; cophenetic
correlation. Report metrics vs density (ties back to Theorem B). **No HGED.**
**Acceptance:** reproduces `applications.md` §A2 criteria; figures render.
**Out of scope here:** MDS/kNN/path; new `src/` code.
