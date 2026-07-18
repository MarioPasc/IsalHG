# T-M5g — G2: sensitivity + ladder profiles, including the measured nauty contrast
**Declared:** 2026-07-18 17:56 CEST (D-ART2 recast of the v2 E2b/E3)
**Status:** OPEN
**Depends on:** T-M1b (`d_I`), T-M2c (connectivity-preserving `random_edit`/`edit_path`), T-M3a (nauty-Levi edit distance, the contrast), T-M4 (corpora)
**Delegation:** agent
**Context to read first:**
- `docs/article/empirical/applications.md` §G2 — the measurement spec
- `docs/article/theoretical/geometry.md` §6 — what each profile licenses
- `docs/article/theoretical/stability.md` §4.2 — the three-regime coherence
  prediction the sensitivity histogram tests (falsification target intact)
- `docs/article/COMPETITORS.md` §3 — the symmetric framing of the contrast
- `src/isalhg/core/sparse_hypergraph.py::{random_edit, edit_path, qin_edit_cost}` — the edit machinery
- `.claude/rules/coding_rules.md` — always
**Description:** The geometry pillar's two dynamic profiles, run in
`experiments/article/`, no `src/` changes. (1) **Sensitivity**: histograms of
`s(e) = d_I(H, H⊕e)` over single edits (all Qin op types), per density regime
and on the four design fixtures (Fano, STS(9), STS(13), GQ(2,2)); log
`R(e)`/`T_span(e)` per edit where cheap, to separate drift from avalanche for
the discussion prose. **Run the identical measurement on the nauty-Levi edit
distance** — the expected avalanche-everywhere profile is the paper's measured
contrast figure. (2) **Ladder response**: `d_I(H_0, H_t)` vs known accumulated
Qin budget `t`, per corpus; monotonicity/near-linearity summarized.
**Acceptance:** reproduces `applications.md` §G2 criteria; the three-regime
prediction of `stability.md` §4.2 is confronted with the design-fixture
histograms (match or falsification reported either way); the ours-vs-nauty
contrast figure renders; ladder-response curves render per corpus.
**Out of scope here:** the E1' figure and bits (T-M5a); the static profiles
`ν`/`D̂`/concentration/hubness (T-M5f spec, measured in T-M5b's runner); any
HGED oracle call; new `src/` code.
