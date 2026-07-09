# T-TAg — Harden the canonical surface: rename, guard `metric_space`, budget the search
**Declared:** 2026-07-09 11:25 CEST (handoff from the T-TAa/T-TAd assessment)
**Status:** OPEN
**Depends on:** T-TAd (the flip), T-TAf (the freeze)
**Why out of scope:** T-TAd is the three-line default flip plus golden
regeneration. Making the *class of bug* unrepeatable — and making the complete
search fail loudly instead of hanging — is separate engineering, and it must not
delay the flip.
**Context to read first:**
- `docs/article/DEVELOPMENT/T-TA/OPEN/T-TAd.md` — the flip this hardens
- `src/isalhg/core/algorithms/greedy_min_complete.py` and `core/algorithms/registry.py` — the variant to rename
- `src/isalhg/metric_space/distances/isalhg_levenshtein.py::IsalHGLevenshtein` — currently accepts any `algorithm`; `d_I` over a greedy `w*` is not a metric
- `src/isalhg/errors.py::DistanceComputationError` — the exception to raise
- `src/isalhg/metric_space/distances/hged.py::ExactHGED` — the `timeout` / `max_expansions` pattern to mirror for the encoder budget
- `src/isalhg/iso_backends/isalhg_backend.py::_DEFAULT_ISALHG_ALGORITHM` — the `ISALHG_ALGORITHM` override the preprint pipeline pins
- `experiments/preprint/` — configs that must pin the greedy variant explicitly
- `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/proofs/theorem_a_completeness.tex` — Lemma 2.1 (exactly `m` emissions, but the branching factor is unbounded)
- `.claude/rules/coding_rules.md` — always
**Description:** Four hardenings, in order of value.
(a) **Guard `metric_space`.** `IsalHGLevenshtein` must compute `w*_c` and raise
`DistanceComputationError` if handed a non-complete algorithm. The default flip
alone does not prevent the bug — anyone passing `algorithm=` reintroduces a
non-metric `d_I` silently.
(b) **Budget the search.** The proof bounds the number of structural emissions
(exactly `m`) but *not* the branching factor `|T(σ)| × orderings`; GQ(2,2)-shaped
input already costs 1.09 s at n=15. Add a branch/expansion budget that raises
rather than hangs, mirroring `ExactHGED`'s `timeout` / `max_expansions`. A raised
error is a result; a hung sweep is not.
(c) **Rename** `greedy_min_complete` → `canonical` (or `tie_complete`). It is not
greedy, and the present name invites reading it as one variant among six rather
than as *the* canonical form.
(d) **Pin the preprint.** The greedy variants are the completed iso-benchmark
paper's measurement apparatus, so they are kept, not deleted (`coding_rules` §2.1's
no-shims rule does not cover published scientific artefacts). Re-document them as
one-sided iso heuristics — equal fingerprints certify isomorphism, unequal ones are
inconclusive, unusable for `d_I` — and pin `experiments/preprint/` configs to
`ISALHG_ALGORITHM=greedy_min_nbrdeg`.
**Acceptance:** `IsalHGLevenshtein(algorithm="greedy_min_nbrdeg")` raises;
`d_I` on both presentations of the pinned n=4 counterexample is `0.0` (it is `4.0`
today); a synthetic high-automorphism input exceeds the branch budget and raises
instead of hanging; the renamed variant is registered and the old name is gone from
`src/` (a grep for `greedy_min_complete` returns only the ledger and the proof);
the preprint configs reproduce their published fingerprints; full suite + ruff +
mypy at their recorded baselines.
**Out of scope here:** the flip itself (T-TAd); the definitional freeze (T-TAf);
deleting the greedy variants (explicitly rejected — see (d)); the WL-pruned
variants' docstrings (T-TAc).
