# T-TAe — Levi colouring loses absolute label identity (nauty/bliss/Traces false positives)
**Declared:** 2026-07-09 10:48 CEST (handoff from T-TAb)
**Status:** OPEN
**Depends on:** —
**Why out of scope:** T-TAb fixes the *IsalHG* fingerprint's labelled
completeness. This is the identical defect in the three *baseline* backends,
found only because T-TAb tried to use `PynautyLeviBackend` as its labelled iso
oracle and the oracle disagreed with the truth.
**Context to read first:**
- `src/isalhg/core/levi_reduction.py::LeviGraph.color_classes` — builds the
  colour classes from the colours *present* (`classes.setdefault(colour, ...)`,
  then `sorted(classes.keys())`), so unused label ids vanish and the ordered
  partition no longer identifies which label each cell carries
- `src/isalhg/iso_backends/pynauty_levi.py`, `bliss_levi.py`, `traces_levi.py` —
  the three consumers, each passing `color_classes()` as the colouring
- `/media/mpascual/Sandisk2TB/research/ISAL/isalhg/proofs/theorem_a_completeness.pdf`
  Def. 1.3 (isomorphism) — requires `l_V2(phi(v)) == l_V1(v)`, i.e. *absolute*
  label preservation, not preservation up to a relabelling of the colour classes
- `tests/property/_labelled_oracle.py::brute_force_iso` — the exhaustive
  bijection oracle written at T-TAb precisely because pynauty could not be used
- `.claude/rules/coding_rules.md` — always
**Description:** Machine-verified: over `|Sigma_V| = 2`, the one-edge
hypergraphs with vertex labels `(0, 0)` and `(1, 1)` are non-isomorphic (Def.
1.3) but `PynautyLeviBackend.are_isomorphic` returns `True` — both reduce to the
single vertex-side colour class `{0, 1}`, so the label id is erased. The same
holds for every input whose label ids are not all used, and for the bliss and
Traces backends. The fix must anchor the colour ids, e.g. by attaching one
sentinel node per declared label id (the docstring's "sentinel_offset" language
suggests this was the intent but no sentinel is emitted), or by refusing
labelled inputs. Consequence for the article: on labelled corpora (T-M4' / HIC)
the Levi baselines currently under-count non-isomorphic pairs, so any
partition-agreement or competitor comparison over labelled data is invalid
until this lands. Trivial-vocabulary corpora — every corpus to date, including
the whole preprint — are unaffected (one label id, always used).
**Acceptance:** `PynautyLeviBackend`, `BlissLeviBackend` and `TracesLeviBackend`
all return `False` on the `(0, 0)` vs `(1, 1)` pair and agree with
`tests/property/_labelled_oracle.py::brute_force_iso` on a Hypothesis sweep of
labelled pairs (`n <= 5`, `|Sigma_V| in {2, 3}`); unlabelled partition-agreement
tests unchanged; suite + ruff + mypy green.
**Out of scope here:** the IsalHG fingerprint (done at T-TAb); the labelled HIC
loader (T-M4'); `NautyLeviEditDistance` (T-M3a) beyond repointing it at the
fixed reduction.
