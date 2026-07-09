# T-TAe — Levi colouring loses absolute label identity (nauty/bliss/Traces false positives)
**Declared:** 2026-07-09 10:48 CEST (handoff from T-TAb)
**Status:** DONE (2026-07-09 13:22 CEST)
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

---

## Closing record (2026-07-09 13:22 CEST)

### Two premises of this task were wrong; both are corrected below.

**(1) `BlissLeviBackend` was never affected.** python-igraph hands bliss the
per-node colour *values* (`isomorphic_bliss(color1=…, color2=…)`), not an ordered
partition, and its fingerprint payload already embeds `canon_colors` and the
`(|V|, |E|)` split. Measured before any change: `bliss.are_isomorphic(A, B) ==
False` on the `(0,0)` / `(1,1)` pair, and 0 disagreements with `brute_force_iso`
over 40,000 labelled pairs. Only `pynauty_levi` and `traces_levi` were defective.
bliss's source is unchanged apart from a docstring recording *why* it is exempt.

**(2) The fix this task proposed — "one sentinel node per declared label id" —
does not work.** Sentinels make every declared colour occupy a cell, which
repairs `pynauty.isomorphic`, but **`pynauty.certificate` ignores the colouring
altogether**, so `fingerprint` — the method the partition-agreement protocol keys
on — stays broken. Machine-checked counterexample under the sentinel scheme: the
Levi graphs of `([0,0,0], {{1},{0,2}})` and `([0,1,0], {{1},{0,2}})` over
`|Sigma_V| = 2` have colour-class profiles `(4,1,3,1)` and `(3,2,3,1)` — hence no
colour-preserving bijection can exist — yet `pynauty.certificate` returns
byte-equal certificates. A sentinel scheme that *does* work must encode label
identity structurally (mutually-distinguishing gadget per label id), which
inflates the Levi graph and would corrupt `NetLSDDistance` (T-M3c) and
`NautyLeviEditDistance` (T-M3a), both of which consume the same reduction.

### What landed instead

`LeviGraph.color_signature()` — the byte encoding of the **colour profile**
`((colour, |class|), …)`, an iso-invariant (the label histogram in Levi colour
coordinates). nauty and Traces refine the supplied ordered partition by
*splitting* cells in place and never reorder them, so once two Levi graphs are
known to share a colour profile, cell position and colour id agree cell-by-cell
and the engine's canonical form is exact. Consumers therefore prepend the
signature to the certificate — the same augmentation `core.canonical` applies to
`w*` at T-TAb.

- `core/levi_reduction.py`: `+ color_profile()`, `+ color_signature()`;
  `color_classes()` docstring states the positional-identity caveat.
- `iso_backends/pynauty_levi.py`: `fingerprint = color_signature() + certificate`;
  `are_isomorphic` guards on `color_profile()` before `pynauty.isomorphic`.
- `iso_backends/traces_levi.py`: `fingerprint = color_signature() + b6`;
  `_serialize` now derives `f=[…]` from `color_classes()` rather than rebuilding it.
- `iso_backends/bliss_levi.py`: docstring only.
- `docs/engineering/CODE_DESIGN.md`: the module-table row promised a
  `sentinel_offset` that was never emitted, and pointed at the pre-move path.

The signature is emitted on **every** vocabulary, trivial included (PI decision,
2026-07-09). It costs 20 bytes on an unlabelled fingerprint and buys a *provable*
rather than empirical completeness: a bare certificate does not encode the
`(|V|, |E|)` split of the bipartition, so `fingerprint` was in principle unsound
even on trivial-vocabulary corpora. Exhaustive search over all 650 hypergraphs
with `n <= 4`, `<= 3` edges found no actual trivial-vocab collision, so **no
preprint result is invalidated** — the partition each backend induces is
unchanged on every unlabelled corpus; only the fingerprint bytes grew.

### Acceptance

| Criterion | Status |
|---|---|
| pynauty / bliss / Traces all return `False` on `(0,0)` vs `(1,1)` | met — `test_levi_labelled.py::test_are_isomorphic_respects_absolute_labels` |
| all three agree with `brute_force_iso` on a Hypothesis sweep (`n<=5`, `\|Sigma_V\| in {2,3}`) | met — `test_levi_labelled_oracle.py`, 200 passing examples × 2 properties × 3 backends |
| unlabelled partition-agreement tests unchanged | met — `test_{pynauty,bliss,traces}_roundtrip.py`, `test_orchestrator_tier1.py` green |
| suite + ruff + mypy green | met for every file this task touches (see below) |

`dreadnaut` was absent from the environment, so Traces could not have been
verified; `conda install -c conda-forge nauty` into the `isalhg` env fixed that
and Traces is now exercised by both new test modules. **The env now depends on
the `nauty` conda package for the Traces tests to run rather than skip.**

### Closing check

```
$ python -m pytest tests/unit/core/test_levi_reduction.py \
      tests/integration/test_levi_labelled.py \
      tests/property/test_levi_labelled_oracle.py -q
52 passed in 1.89s

$ python -m pytest tests/ -q
692 passed, 1 failed, 7 skipped
$ python -m ruff check src/ tests/          -> 3 violations
$ python -m ruff format --check src/ tests/ -> clean
$ python -m mypy src/isalhg/                -> 21 errors in 6 files
```

The 1 pytest failure (`test_s2h_roundtrip.py::test_canonical_round_trip`), the 3
ruff violations (`isalhg_backend.py`, `viz/instruction_view.py`,
`test_registry.py`) and all 21 mypy errors (`structural_tuples.py`,
`hypergraph_wl.py`, `hypergraph_to_string.py`, `canonical.py`, `_core.pyi`,
`isalhg_backend.py`) are **pre-existing and outside this diff**. `canonical.py`,
`hypergraph_to_string.py` and `sparse_hypergraph.py` were being modified
concurrently by other in-flight work while this task ran. Every file T-TAe
touches is clean under all four checks.

### Regression evidence

Restoring the pre-fix method bodies in-process (`prefix_off` pytest plugin) makes
the two new test modules report **20 failed, 19 passed**; the failures are
confined to `pynauty_levi` and `traces_levi`, and no `bliss_levi` parametrisation
fails either before or after. Neutralising only `color_signature()` leaves
`traces_levi` wrong on 113 of 400 random labelled pairs.

### Consequence for the article

The blocking statement in the Description holds and is now discharged: labelled
partition-agreement and competitor comparison over labelled corpora (T-M4' / HIC)
were invalid for the nauty and Traces baselines and are valid from this commit.
T-M3a's `NautyLeviEditDistance` must consume `color_signature() + certificate`,
not the bare certificate — the label prefix enters its Levenshtein exactly as the
seed label enters `d_I` at T-TAb.
