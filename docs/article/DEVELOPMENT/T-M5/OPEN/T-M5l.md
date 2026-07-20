# T-M5l — PI decision: bits subsection premise falsified by measurement
**Declared:** 2026-07-20 16:19 CEST
**Status:** OPEN
**Depends on:** T-M5a (bits harvest, DONE at part-2)
**Delegation:** orchestrator-only
**Why out of scope:** T-M5a's scope is implementing and running the bits pipeline; deciding what the §4 article claim should say after the result is falsified is a PI-level reframe decision.
**Context to read first:**
- `docs/article/PROPOSAL.md` §4 ("Compactness — information content in bits") — the claim to be revised
- `docs/article/empirical/correlation.md` §Information content — the estimator spec + "sibling reference points"
- `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/T-M5a/bits/` — all bits results (planted_main, planted_small, pooled)
- `experiments/article/analysis/bits_harvest.py` — the harvest pipeline (T-M5a)
- `experiments/article/analysis/information_content.py` — Wilcoxon + OLS analysis
- `docs/article/DEVELOPMENT/T-M5/IN-PROGRESS/T-M5a.md` — part-2 closure note (measured numbers)
- `.claude/rules/coding_rules.md` — always
**Description:** The T-M5a part-2 bits harvest measured median compression ratio r = 0.697
(pooled planted_main N=60 + planted_small N=20, both k=3), fraction IsalHG shorter = 0.000,
Wilcoxon p = 1 (one-sided H1: r > 1 rejected), OLS β = 1.265 (IsalHG grows faster than
incidence list). This falsifies PROPOSAL §4's "compact word" premise for the body corpora.
Root cause: for k=3, |Σ| = 13, log₂(13) = 3.70 bits/token; at n=10 the canonical string
averages ~45 tokens × 3.70 = 167 bits vs ~111 bits for the incidence list; breakeven
requires ≤30 tokens, unreachable for n=10, m=10. The sibling (IsalGraph, k=2) saw
r ∈ [1.45, 1.89] because |Σ_graph| = 8, log₂(8) = 3 bits/token and graph strings are
shorter. PI must choose one of: (a) drop §4 compactness subsection; (b) reframe §4 as
"representation cost" characterization (not compression claim); (c) restrict bits
comparison to k=2 (arity-2 sub-corpus); (d) adopt a different bits estimator. Option (b)
is the scientifically honest path that keeps the measurement.
**Acceptance:** PI picks one option; the chosen framing is reflected in `PROPOSAL.md` §4,
`correlation.md` §Information content, and the article bits text; the bits data files
remain unchanged (they are the honest measurement).
**Out of scope here:** re-running the bits computation, changing the harvest code, or
silently dropping the result. The bits pipeline (T-M5a) is closed; this task is the
article-level response to the finding.
