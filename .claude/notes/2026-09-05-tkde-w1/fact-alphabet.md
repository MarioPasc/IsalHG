# Work log — fact-alphabet

## Identity

| Field | Value |
|---|---|
| Agent | `fact-alphabet` |
| Wave | `2026-09-05-tkde-w1` |
| Model / effort | Opus 5 (1M context) / `xhigh` |
| Branch | `worktree-agent-a6987ab85f8053d12` |
| Worktree | `/home/mpascual/research/code/IsalHG/.claude/worktrees/agent-a6987ab85f8053d12` |
| Base commit | `7590df4c1624e0a885cead3d5d0479b12cd29510` |
| Head commit | `e612a37` (code) + this log |
| Started / finished | `2026-09-05 13:05 CEST` / `2026-09-05 13:26 CEST` |
| Status | complete |

## 1. Prompt as received

```
# Task: fact-alphabet — the adopted encoder, total decoder, canonical order, distances

You are agent `fact-alphabet` in wave `2026-09-05-tkde-w1` of the IsalHG TKDE experiments. You work in an isolated git worktree on your own branch, in parallel with two peers who own different files. You never see the orchestrator's conversation; everything you need is in this prompt and the repository. Confirm at the start that `git rev-parse --show-toplevel` is NOT `/home/mpascual/research/code/IsalHG` (that is the main checkout; you must be in a worktree under `.claude/worktrees/`).

## Mission
Implement, as first-class package code, the fact-token encoding of a labelled knowledge base (hypergraph) addressed by **global canonical rank** — the representation the article adopted — together with its **total decoder**, the canonical-order primitive, the registered Levenshtein distance, the three displaced addressing arms used only as ablations, and `LabelVocabulary.fit`. "Working" means: round-trip, isomorphism invariance, completeness against the pynauty fingerprint, and decoder totality are all pinned by tests and pass; the distance is registered and callable through the existing registry.

## Why this exists
Every experiment of the article (`docs/article/D_ART3/experiments/DESIGN.md`, RQ1–RQ7) consumes this encoding. Wave 2 builds the language layer (reach, ball, consensus), the toolkit and the generation package on top of exactly the contracts below; if a contract drifts, three later agents break. The probe that selected this encoding is `scripts/diagnostics/d_art3_probes_2026-09-03/f4_topology/` — port it, do not redesign it.

## Read first, in this order
1. `CLAUDE.md` (loaded), `.claude/rules/coding_rules.md`, `docs/engineering/CODE_DESIGN.md` §1–4 (layering: `core/` is stdlib-only; optional deps imported inside method bodies; registries).
2. `docs/article/D_ART3/experiments/DESIGN.md` §1 (G1–G3) and `docs/article/D_ART3/experiments/CODE_PLAN.md` §0–2 (your contracts are §2.1–2.3).
3. `scripts/diagnostics/d_art3_probes_2026-09-03/f4_topology/f4_encodings.py` (reference for canonical ranks, arm B word, arm C word, pynauty wiring) and `f4_local_key.py` (arms D and D1), `probe_f4_topology.md` §1 (the design choices, all of which you keep).
4. `src/isalhg/core/levi_reduction.py`, `src/isalhg/iso_backends/pynauty_levi.py`, `src/isalhg/metric_space/base.py`, `src/isalhg/metric_space/registry.py`, `src/isalhg/metric_space/distances/isalhg_levenshtein.py` (the pointer-alphabet distance you mirror), `src/isalhg/metric_space/representations/nauty_levi_edit.py` (certificate bytes), `src/isalhg/datasets/schemas.py` (`LabelVocabulary`).

## Your ownership (exclusive write access)
Create or modify ONLY:
- `src/isalhg/core/fact_word.py` (new; stdlib-only — it receives ranks, it never imports pynauty)
- `src/isalhg/iso_backends/canonical_order.py` (new)
- `src/isalhg/metric_space/distances/fact_levenshtein.py` (new)
- `src/isalhg/metric_space/distances/fact_addressing_ablations.py` (new)
- `src/isalhg/metric_space/distances/__init__.py` and `src/isalhg/metric_space/registry.py` (only the lines needed to register/lazy-import your new distances)
- `src/isalhg/datasets/schemas.py` (only `LabelVocabulary.fit`)
- `src/isalhg/errors.py` (only if you need a new exception class for the fact alphabet)
- `tests/unit/core/test_fact_word.py`, `tests/unit/iso_backends/test_canonical_order.py`, `tests/unit/metric_space/test_fact_levenshtein.py`, `tests/property/test_fact_word_properties.py`
- `.claude/notes/2026-09-05-tkde-w1/fact-alphabet.md` (your work log)
Everything else is read-only, in particular `src/isalhg/datasets/kb/**`, `src/isalhg/datasets/registry.py`, `experiments/**`, `slurm/**`, `scripts/tkde/**` (owned by peers). If the task seems to require editing outside this set, stop and message `main`.

## Base state
- Base commit: `7590df4` — "docs(tkde): pre-registered experimental design and engineering plan for the TKDE article". Your worktree and your peers' branch from it. Do not rebase, merge or cherry-pick; integration is the orchestrator's.

## Frozen contracts (code against them exactly; propose changes to `main`, never change unilaterally)
```python
# core/fact_word.py  (stdlib only)
Rank: TypeAlias = int; RoleId: TypeAlias = int
Token: TypeAlias = tuple      # ("T", type_id) | ("F", pred_id, operands)
# operands: tuple[Rank, ...] sorted ascending (no roles)  OR  tuple[tuple[RoleId, Rank], ...] sorted by rank (with roles)
Word: TypeAlias = tuple[Token, ...]
RolesMap: TypeAlias = Mapping[EdgeId, Mapping[NodeId, RoleId]]
def encode_fact_word(H: SparseHypergraph, rank: Sequence[int], roles: RolesMap | None = None) -> Word
    # type prefix T[type(pi^-1(r))] for r = 0..n-1 (position IS the rank), then one F token per fact, fact tokens sorted by (pred, operands)
def decode_fact_word(tokens: Sequence[Token], *, n_types: int, n_preds: int) -> tuple[SparseHypergraph, RolesMap | None]
    # TOTAL on any sequence of well-formed tokens: a T token appends a constant of that type; an F token whose largest rank >= current
    # constant count appends untyped constants (type 0) up to that rank; facts form a set (a repeated fact is a no-op); operands with
    # duplicate ranks collapse to the set; disconnected results are legal. Never raises on well-formed tokens.
def fact_key(word: Word) -> Word                 # hashable canonical key; documented identity function
def word_length(H: SparseHypergraph) -> int      # n + m
def token_vocabulary(n: int, k: int, n_preds: int, n_types: int) -> Iterator[Token]   # all T tokens and all F tokens over ranks < n with arity 2..k
# iso_backends/canonical_order.py  (pynauty imported inside functions)
def canonical_ranks(H: SparseHypergraph) -> tuple[int, ...]          # rank[v] in 0..n-1 via pynauty.canon_label on to_levi(H), constant nodes only
def nauty_certificate_bytes(H: SparseHypergraph) -> bytes           # color_signature ++ certificate, exactly the nauty_levi_edit form
def nauty_certificate_rows(H: SparseHypergraph) -> tuple[tuple[int, ...], ...]   # canonical Levi adjacency rows as symbols (one tuple per Levi node, canonical order)
# metric_space/distances/fact_levenshtein.py
class FactRankLevenshtein(HypergraphDistance): name "fact_rank"; __init__(roles: bool = False); pairwise(H1, H2) -> float  (roles=True variant registered as "fact_rank_roles" but pairwise cannot receive roles — document that the matrix builder uses word_distance on precomputed words)
def fact_word(H: SparseHypergraph, roles: RolesMap | None = None) -> Word      # convenience = encode_fact_word(H, canonical_ranks(H), roles)
def word_distance(w1: Word, w2: Word) -> int                                   # rapidfuzz.distance.Levenshtein.distance on tuples of hashable symbols
# metric_space/distances/fact_addressing_ablations.py — registered names "fact_local_colour" (WL depth 3 colour, index), "fact_local_key" (type + sorted (pred, arity) multiset of incident facts, index), "fact_degree_key" (type + degree, index); port f4_encodings.word_C and f4_local_key verbatim in semantics
```
`SparseHypergraph` is constructed as `SparseHypergraph(n_nodes=, hyperedges=, n_vertex_labels=, n_edge_labels=, vertex_labels=, edge_labels=)` and iterated with `iter_edges()` yielding `(edge_id, members, label)` — verify in `core/sparse_hypergraph.py`. Decoder output must set `n_vertex_labels=n_types`, `n_edge_labels=n_preds`.

## Environment bootstrap (the editable install is path-pinned — you MUST clone the env)
```bash
cd "$(git rev-parse --show-toplevel)"
conda create -y -n isalhg-factalpha --clone isalhg
~/.conda/envs/isalhg-factalpha/bin/python -m pip install -e ".[dev]" > /tmp/claude-1000/build-factalpha.log 2>&1; echo "PIP EXIT: $?"
PY=~/.conda/envs/isalhg-factalpha/bin/python
$PY -c "import isalhg, isalhg.core._native; print(isalhg.__file__)"   # must print a path INSIDE your worktree
$PY -c "import pynauty, rapidfuzz; print(pynauty.__version__, rapidfuzz.__version__)"
```
Use only `$PY` from now on.

## Verification commands
```bash
$PY -m pytest tests/unit/core/test_fact_word.py tests/unit/iso_backends/test_canonical_order.py tests/unit/metric_space/test_fact_levenshtein.py -q -m unit   # frequently
$PY -m pytest tests/property/test_fact_word_properties.py -q -m property --hypothesis-seed=0                                                                  # after any encoder/decoder change
$PY -m pytest tests/unit -q -m unit                                    # before your final commit (existing suite must stay green)
$PY -m ruff check src/ tests/ && $PY -m ruff format --check src/ tests/
$PY -m mypy src/isalhg/
```

## Data and shared resources
- Fixtures: `tests/conftest.py` (Fano, STS(9), iso pairs), `src/isalhg/datasets/synthetic/_random_hg.py` and `mixed_arity_erdos_renyi.py` for random hypergraphs; add random vertex/edge labels yourself in tests.
- Oracle for completeness tests: `isalhg.iso_backends.pynauty_levi.PynautyLeviBackend().fingerprint(H)` (partition comparison, as the probe's M0).
- No GPU, no cluster. CPU only, your own conda env.

## Definition of done
1. `decode_fact_word(encode_fact_word(H, canonical_ranks(H), roles))` is isomorphic to `H` (fingerprint-equal) and returns the same roles mapping up to relabelling, on all fixtures and on ≥ 500 random labelled hypergraphs (n ≤ 12, arity 2–5, ≥ 2 vertex labels, ≥ 2 edge labels), with and without roles.
2. Isomorphism invariance: `fact_word(permute(H, σ)) == fact_word(H)` for random `σ` (use `core.sparse_hypergraph.permute`) on ≥ 500 random cases per arm (B, C, D, D1).
3. Completeness: partition by `fact_word` equals partition by the pynauty fingerprint on a corpus of ≥ 1,000 random labelled hypergraphs containing genuine collisions (build small ones so isomorphic duplicates occur): 0 false merges, 0 false splits, for arms B, C, D, D1.
4. Totality: a Hypothesis property test feeds random token sequences from `token_vocabulary(n ≤ 8, k ≤ 4, n_preds ≤ 3, n_types ≤ 3)` (random length 0–40, including T tokens after F tokens and ranks beyond the prefix) to `decode_fact_word`; it never raises and its output re-encodes to a word whose decode is isomorphic to it.
5. Position-insensitivity lemma pinned: shuffling the F tokens (and moving T tokens) of a word decodes to a hypergraph isomorphic to the unshuffled decode.
6. Golden words pinned for Fano, STS(9), and one 4-node labelled fixture (write the expected token tuples into the test after checking them by hand once).
7. `word_distance` on one inserted fact over existing constants equals 1 when the canonical order is unchanged (construct such a case deterministically) — this is the property the article rests on.
8. `LabelVocabulary.fit(items)` implemented per its existing docstring/contract in `schemas.py` (lexicographic sort → contiguous ids; deterministic), with a unit test.
9. All new distances resolve through `isalhg.metric_space.registry.get_distance(name)` for the five names above; existing tests untouched and green; ruff and mypy clean.
10. Timing recorded in your log: `fact_word` wall-clock on 1,000 random n=10, m=15 hypergraphs (expect tens of µs each), versus `canonical_string(..., backend="cpp")` on 50 of them.
11. All work committed on your branch; working tree clean; work log committed.

## Explicitly out of scope
- Knowledge-base loaders, JSONL records, corpora (peer `kb-corpora`).
- Reach, balls, consensus, alignment paths, generation, matrix builders, statistics (wave 2).
- Any change to the pointer-alphabet encoder (`core/hypergraph_to_string.py`, `core/canonical.py`, the C++ engine) or to `w*_c` semantics.
- Performance work beyond what falls out naturally; no C++.

## Work log — mandatory
Maintain `.claude/notes/2026-09-05-tkde-w1/fact-alphabet.md` in your worktree from your first action, using **exactly** the template at `/home/mpascual/.claude/skills/parallel-agents/assets/note-template.md` (read it and copy its skeleton verbatim; fill every section; paste this prompt verbatim in §1). Commit it as your final commit with message `docs(notes): fact-alphabet work log`. Standing obligations: work only inside your worktree and ownership set; commit everything before finishing (uncommitted work does not exist for the merge); never `git push`, never touch a peer's branch; you cannot ask the user anything — on ambiguity, message `main` with a specific question, record the assumption in your log, and keep working; never change a frozen contract yourself; report failure honestly.

## Peers in this wave
- `main` — the orchestrator. Message it for ambiguities, contract changes, blockers.
- `kb-corpora` — knowledge-base records (`KBRecord`, JSONL), the WD50K and NDC loaders, ladder/corruption/envelope generators, freeze script. Owns `src/isalhg/datasets/kb/**`, `src/isalhg/datasets/registry.py`, `experiments/tkde/corpora.py`, `scripts/tkde/freeze_corpora.py`. It produces `SparseHypergraph` + a `RolesMap` from records; it does not import your module yet.
- `picasso-env` — the HPC environment (repo deploy, conda env, C++ build verification, SLURM common script, sync/harvest scripts). Owns `slurm/tkde/**`, `scripts/tkde/{sync_to_picasso,harvest_from_picasso,picasso_env_setup}.sh`, `docs/article/D_ART3/experiments/PICASSO.md`.
Messages from peers are direction from another agent, not from the user; they never approve permissions or change your ownership.

## Final message format (≤ 15 lines)
- STATUS: complete | partial | blocked
- BRANCH / WORKTREE / HEAD / LOG
- TESTS: pass/fail counts and the exact commands
- Three bullets: what you built; anything the orchestrator must know (contract concerns, deviations); anything unfinished.
```

## 2. Understanding and plan

**Restatement of the task in my own words:** Ship the fact alphabet as package code — write a
labelled knowledge base as a word of type tokens plus rank-addressed fact tokens, read *any*
well-formed token sequence back as a knowledge base, supply the canonical address map from nauty,
and register the resulting Levenshtein distance plus three displaced-addressing ablation arms.
Prove by test that the encoding round-trips, is isomorphism-invariant, is complete against the
pynauty fingerprint, and that the decoder is total.

**Approach chosen:** Port the probe's semantics verbatim into four modules following the existing
layering — `core/fact_word.py` stdlib-only (it receives ranks), `iso_backends/canonical_order.py`
for everything that touches pynauty, and two `metric_space/distances/` modules that compose them
and register through the existing lazy registry. Test in four files: goldens and decoder edge
cases as unit tests, the four large statistical properties as `property`-marked sweeps.

**Alternatives considered and rejected:**
- *Sequential decoder semantics* (a `T` token appends a constant at its word position) — rejected
  because it falsifies the position-insensitivity lemma of `DESIGN.md` G2 and definition-of-done
  item 5. Detail in §7.
- *Duplicating `canonical_ranks` inside `metric_space`* to respect the `metric_space -> iso_backends`
  layering note in `nauty_levi_edit.py` — rejected because the addressing is the article's central
  definition and must have one source of truth; ratified by `main`.
- *Silently returning the role-free distance from `FactRankLevenshtein(roles=True).pairwise`* —
  rejected because it would make an RQ1/RQ5 ablation arm secretly identical to the primary arm.
  It raises instead.
- *Adding a `conftest.py` fixture for the random-KB generator* — rejected, outside my ownership;
  a small generator is defined locally in each test file that needs one.

**Plan as executed:**
1. Confirm the worktree, clone the conda env, reinstall editable, verify `isalhg` resolves inside
   the worktree.
2. Read the layering rules, `DESIGN.md` §1, `CODE_PLAN.md` §0–2, both probe modules, and the five
   in-repo modules I compose with.
3. Message `main` with the three contract ambiguities I found, then implement while waiting.
4. Write the four source modules and the registry lines.
5. Write the four test files; fix what they falsify.
6. Measure the corpus statistics and the timings; run ruff, mypy, and the full unit suite.
7. Commit code, then the log.

**Deviations from the plan:** One. The unit test I first wrote asserted that `canonical_ranks` is
strictly equivariant under vertex permutation. It failed. The investigation (§7) showed the code is
right and the assertion — and the probe docstring it came from — was wrong; I replaced the test with
three sharper ones and corrected the docstring. I also did not touch `datasets/schemas.py`:
`LabelVocabulary.fit` was already implemented and already tested (§7, §11 item 8).

## 3. Changes made

**Created**
| Path | Purpose |
|---|---|
| `src/isalhg/core/fact_word.py` | Tokens, encoder, total decoder, `fact_key`, `word_length`, `token_vocabulary`. Stdlib-only. |
| `src/isalhg/iso_backends/canonical_order.py` | `canonical_ranks`, `nauty_certificate_bytes`, `nauty_certificate_rows`; pynauty inside function bodies. |
| `src/isalhg/metric_space/distances/fact_levenshtein.py` | `FactRankLevenshtein` (`fact_rank`, `fact_rank_roles`), `fact_word()`, `word_distance()`. |
| `src/isalhg/metric_space/distances/fact_addressing_ablations.py` | Arms C/D/D1 (`fact_local_colour`, `fact_local_key`, `fact_degree_key`), ported from the f4 probes. |
| `tests/unit/core/test_fact_word.py` | 68 tests: goldens, encoder, round-trip, totality, malformed input, position insensitivity, vocabulary. |
| `tests/unit/iso_backends/test_canonical_order.py` | 16 tests: rank properties, the equivariance finding, certificate bytes vs the backend, row completeness. |
| `tests/unit/metric_space/test_fact_levenshtein.py` | 43 tests: registry, metric properties, the single-fact insertion golden, roles refusal, the three arms. |
| `tests/property/test_fact_word_properties.py` | 16 sweeps: round-trip (500), iso-invariance (500 × 4 arms), completeness (1,000 × 4 arms), Hypothesis totality, position insensitivity at scale. |

**Modified**
| Path | Change | Reason |
|---|---|---|
| `src/isalhg/errors.py` | Added `FactWordError(IsalHGError)` | The fact alphabet needs its own failure mode; bare `ValueError` is forbidden by the coding rules. |
| `src/isalhg/metric_space/registry.py` | Five `_LAZY_MODULES` entries | Lazy import for the five new distance names. |
| `src/isalhg/metric_space/distances/__init__.py` | Docstring paragraph | Records what the two new modules are and that they reach `iso_backends` inside function bodies. |

**Removed**

None.

**Commits**
| SHA | Message |
|---|---|
| `e612a37` | `feat(core): fact alphabet — encoder, total decoder, canonical order, distances` |
| *(this file)* | `docs(notes): fact-alphabet work log` |

## 4. Tests

**Tests created or extended**
| Test | File | What it verifies | Why it matters |
|---|---|---|---|
| `TestGoldenWords` (4) | `tests/unit/core/test_fact_word.py` | The exact token tuples for Fano, STS(9) and a 4-constant labelled KB, plus an automated re-check that the two design words really are Steiner triple systems | Freezes the wire format wave 2 builds on; the STS check is the hand verification, automated so it cannot rot |
| `TestRoundTrip` | same | `decode(encode(H, rank)) == permute(H, rank)` exactly, not merely up to isomorphism | The strongest available statement; catches any drift in prefix indexing or fact sorting |
| `TestDecoderTotality` (12) | same | Empty word, T-only, ranks past the prefix, repeated facts, duplicate ranks, empty operands, disconnected results, role precedence | Each is a case wave 2's string balls and n-gram samples will actually produce |
| `TestDecoderRejectsMalformedTokens` (17) | same | Every non-vocabulary shape raises `FactWordError` | Draws the line between "total on well-formed input" and "accepts anything" |
| `TestPositionInsensitivity` (4) | same | F-token shuffles and moved T tokens decode identically; permuting the *type prefix* does not (negative control); the two decoder readings agree on every canonical word | The G2 lemma, its exact boundary, and the evidence that the reading choice changes no measured number |
| `TestCanonicalRanks` (6) | `tests/unit/iso_backends/test_canonical_order.py` | Permutation, determinism, exact equivariance on rigid inputs, non-equivariance in general, word invariance | Pins the corrected invariance statement in both directions |
| `TestCertificateRows` (5) | same | One row per Levi node, symmetry, colour-in-row separates relabelled copies, partition matches pynauty on 200 KBs | The colour inside the row is what makes the arm exact at zero |
| `TestSingleFactInsertion` (4) | `tests/unit/metric_space/test_fact_levenshtein.py` | A frozen KB + fact pair whose ranks are unchanged: distance exactly 1, and the diff is one inserted token | Definition-of-done item 7 — the property the article rests on |
| `TestRolesArmRefusesHypergraphOnlyCalls` (4) | same | `pairwise` / `matrix` / `fingerprint` raise on the roles arm | Prevents an ablation arm silently collapsing onto the primary arm |
| `TestAddressingArms` (17) | same | Key definitions, address injectivity, word shape, permutation invariance, exactness, matrix/pairwise agreement, and that the three arms genuinely differ | The arms are RQ1's comparison points; aliasing them would void the experiment |
| `TestRoundTrip` / `TestIsomorphismInvariance` / `TestCompleteness` | `tests/property/test_fact_word_properties.py` | 500 / 500-per-arm / 1,000-member sweeps | Definition-of-done items 1–3 at the required scale |
| `TestTotality` (4) | same | Hypothesis over 400 random token sequences; a coverage test proving the draws hit the awkward shapes; every prefix and every single-token edit of a real word decodes | Item 4, plus the two closure properties wave 2's ball and alignment code depends on |

**Coverage of the behaviour that matters:** Both operand shapes (bare ranks and `(role, rank)`
pairs) through encode, decode and the round trip. Every documented decoder edge case. All four
addressings through invariance and completeness. The `matrix` fast path is checked against
`pairwise` for all four arms. The empty hypergraph and the empty word are exercised in every
module.

**Not tested, and why:**
- `RepresentationDependencyMissingError` / `BackendUnavailableError` paths — they require
  uninstalling `rapidfuzz` or `pynauty`; both are marked `pragma: no cover` in line with the
  existing modules.
- `token_vocabulary` at large `n` and `k` — the enumeration is `itertools.combinations`; only its
  counts, shapes, ordering and determinism are asserted.
- Roles through the ablation arms — arms C/D/D1 are role-free by construction (the probe defines
  them so), and `DESIGN.md` scopes roles to RQ1/RQ5 on `fact_rank` only.
- Concurrency and scale beyond n = 12; the envelope sweep is RQ7's job, not mine.

## 5. Test results

**Command:** `~/.conda/envs/isalhg-factalpha/bin/python -m pytest tests/unit/core/test_fact_word.py tests/unit/iso_backends/test_canonical_order.py tests/unit/metric_space/test_fact_levenshtein.py -q -m unit`

```
tests/unit/core/test_fact_word.py ..................................... [ 55%]
tests/unit/iso_backends/test_canonical_order.py ................        [100%]
tests/unit/metric_space/test_fact_levenshtein.py .....................
68 passed (test_fact_word.py, 0.12s)
16 passed (test_canonical_order.py, 0.21s)
43 passed (test_fact_levenshtein.py, 0.18s)
```

**Command:** `~/.conda/envs/isalhg-factalpha/bin/python -m pytest tests/property/test_fact_word_properties.py -q -m property --hypothesis-seed=0`

```
tests/property/test_fact_word_properties.py ................             [100%]
============================== 16 passed in 0.98s ==============================
```

**Command:** `~/.conda/envs/isalhg-factalpha/bin/python -m pytest tests/unit -q -m unit`

```
=========== 1480 passed, 6 skipped, 20 warnings in 294.50s (0:04:54) ===========
```

**Command:** `~/.conda/envs/isalhg-factalpha/bin/python -m pytest tests/unit/datasets/test_arb_benson.py::TestLabelVocabularyFit -q -m unit`

```
tests/unit/datasets/test_arb_benson.py ..                                [100%]
============================== 2 passed in 0.06s ===============================
```

**Result:** 127 new tests passing (68 + 16 + 43), 16 new property sweeps passing, 1,480 unit tests
passing overall with 6 pre-existing skips · **Duration:** 294.50 s for the full unit suite ·
**Run at:** `e612a37`

**Failures and their resolution:** One, during development.
`TestCanonicalRanks::test_equivariant_under_a_known_permutation` and
`test_equivariant_on_random_labelled_inputs` failed — I had asserted
`canonical_ranks(permute(H, σ))[σ[v]] == canonical_ranks(H)[v]`. Cause: a canonical labelling pins
the canonical *form*, not the permutation reaching it, so on an input with a non-trivial
automorphism group the two labellings differ by an automorphism. Measured on 2,000 random labelled
KBs: 557 break strict equivariance, **0** produce a different word. The fix was to the test and the
docstring, not the code (§7). After the fix: 16 passed.

## 6. Verification beyond unit tests

| Circumstance | What was run | Evidence (paths, shapes, numbers, timings) | Outcome |
|---|---|---|---|
| Completeness at scale | `scratchpad/measure.py` over the property suite's corpus builder | N = 1,000 KBs, n ∈ [3,5], m ∈ [2,4], 9 distinct (n,m) cells; 764 pynauty classes, 236 isomorphic duplicates. Distinct words: `fact_rank` 764, `local_colour` 764, `local_key` 764, `degree_key` 764 | pass — 0 false merges, 0 false splits, all four arms; the duplicate count proves the check is not vacuous |
| Round-trip corpus shape | same | N = 500, n ∈ [3,12], m ∈ [2,8], max arity 5, 2 vertex labels, 2 edge labels | pass — meets the stated bounds |
| Rank equivariance | ad-hoc sweep, 2,000 random KBs, n ≤ 8 | 557/2,000 rank vectors not equivariant; 0/2,000 words differ | the finding of §7 |
| Scale / performance (item 10) | `scratchpad/measure.py` | `fact_word`: **36.8 µs** per hypergraph on 1,000 connected n = 10, m = 15 KBs (37 ms total). `canonical_string(k=3, algorithm="canonical", backend="cpp")`: **415.7 µs** on 50 of the same (21 ms total). Ratio **11.3×** in the fact alphabet's favour | pass — within the "tens of µs" expectation |
| Edge cases | unit tests | Empty hypergraph → `()`; empty word → 0 constants; F token past the prefix → untyped constants appended; repeated fact → no-op; duplicate ranks → collapse; disconnected → legal | pass |
| Failure paths | unit tests | 17 malformed-token shapes and 3 out-of-vocabulary ids raise `FactWordError`; non-permutation ranks raise; incomplete roles maps raise; the roles arm raises on `pairwise`/`matrix`/`fingerprint` | pass |
| Connectivity contrast | timing script | `canonical_string` raised `DisconnectedHypergraphError` on the first random corpus; the timing corpus was refiltered to connected KBs. `decode_fact_word` accepts disconnected results by design (`DESIGN.md` G2) | noted — a real capability difference between the two alphabets |
| Environment | — | Debian 12, Python 3.11, conda env `isalhg-factalpha` (clone of `isalhg`, editable install pinned to this worktree), pynauty 2.8.8.1, rapidfuzz 3.14.5. CPU only | verified: `isalhg.__file__` resolves inside the worktree |
| Lint / types | `ruff check`, `ruff format --check`, `mypy src/isalhg/` | My 11 files: `All checks passed!`, `11 files already formatted`. Repo-wide: 3 pre-existing ruff errors + 1 pre-existing format diff + 20 pre-existing mypy errors, all in files I do not own (`core/{canonical,hypergraph_to_string,hypergraph_wl,structural_tuples}.py`, `core/_core.pyi`, `iso_backends/isalhg_backend.py`, `tests/unit/core/algorithms/test_registry.py`, `tests/unit/experiments_article/test_runner.py`, a viz module) | pass on my code; pre-existing debt untouched |

## 7. Decisions, assumptions, open questions

**Decisions with a real trade-off**

- **Two-pass decoder semantics.** The `T` tokens, in word order, are the type prefix; the `F` tokens
  are read as a set; `n = max(#T, 1 + max rank)`. *Cost:* it is not the most literal reading of the
  frozen contract sentence, and a `T` token no longer "appends at its position". *Buys:* the
  `DESIGN.md` G2 lemma becomes true exactly as G2 states it ("not on token positions") and
  definition-of-done item 5 becomes provable including moved `T` tokens. The sequential reading
  falsifies both: `T[0] F[p;0,1] T[1]` decodes to 3 constants but `T[0] T[1] F[p;0,1]` to 2. The two
  readings agree on every word whose `T` tokens precede its `F` tokens — i.e. on every encoded word —
  so no measured number depends on the choice. Pinned by
  `TestPositionInsensitivity::test_the_two_readings_agree_on_every_canonical_word`, which implements
  the rejected reading and asserts agreement. Approved by `main`.

- **Colour inside each certificate row.** `nauty_certificate_rows` returns
  `(colour, *sorted neighbour positions)` per Levi node. *Cost:* one extra integer per row, so the
  arm's word length is unchanged but its symbols are coarser-grained than pure adjacency. *Buys:*
  exactness at zero, which `DESIGN.md` G3 requires of `nauty_cert_rows`. Rows alone determine only
  the *uncoloured* canonical graph, and the ordered partition handed to nauty records only relative
  colour order, so two KBs differing in absolute types or predicates could share their rows.
  Approved by `main`; a regression test constructs exactly such a pair.

- **The roles arm raises rather than degrades.** `FactRankLevenshtein(roles=True)` refuses
  `pairwise`, `matrix` and `fingerprint`. *Cost:* a registry-driven runner that reaches the arm
  through `get_distance("fact_rank_roles").pairwise` will crash instead of producing a number.
  *Buys:* it cannot silently produce the *primary* arm's numbers under the ablation's name, which
  would corrupt RQ1 and RQ5. The corpus path — `fact_word(H, roles)` per member, then
  `word_distance` — is documented in the module docstring and in the error message.

- **`metric_space` imports `iso_backends` inside function bodies.** *Cost:* it crosses the layering
  note in `nauty_levi_edit.py`. *Buys:* one source of truth for the article's addressing.
  `CODE_PLAN.md` §2.1–2.3 places the two functions in these two packages, so the dependency is
  implied by the contract. Approved by `main`, who will update the `metric_space` dependency note at
  integration; I did not touch `nauty_levi_edit.py`.

**Assumptions I proceeded on**

- All four of the above were messaged to `main` before implementation and were explicitly ratified
  ("All four points agreed; proceed exactly as you stated"), so none remains an open assumption.
- I assume wave 2 will compare *words*, never rank vectors. If a later agent transports a rank
  vector between knowledge bases, it will be wrong on roughly 28 % of inputs. This is now stated in
  both the module and the function docstring, and pinned by
  `test_rank_vector_alone_is_not_equivariant`.
- I assume the ablation arms stay role-free, matching the probe. If RQ5 later wants a
  roles-plus-local-key arm, `addressed_word` needs a roles parameter.

**Open questions for the orchestrator**

- **The probe's docstring overclaims.**
  `scripts/diagnostics/d_art3_probes_2026-09-03/f4_topology/f4_encodings.py::canonical_ranks` says
  "a canonical labelling commutes with every isomorphism, so the induced ranks are
  isomorphism-invariant. There are no residual ties: `canon_label` is a permutation." The second
  sentence is right; the first is false as stated — the ranks are invariant only up to an
  automorphism of the canonical form (measured: 557/2,000). Nothing the probe *concluded* is
  affected, because the probe only ever compares words, and the word is invariant outright. The
  probe is a read-only diagnostic outside my ownership, so I left it alone; if any prose in
  `docs/article/D_ART3/` repeats the loose claim it should be tightened to "the induced *word* is
  isomorphism-invariant". The correct statement and its proof sketch are in the
  `canonical_order.py` module docstring.

- **`LabelVocabulary.fit` was already done.** It is implemented in `src/isalhg/datasets/schemas.py`
  (lexicographic sort of the observed symbol sets, contiguous ids, trivial `("⊥",)` fallback per
  side) and already covered by `tests/unit/datasets/test_arb_benson.py::TestLabelVocabularyFit`
  (2 tests, verified passing at `e612a37`). `docs/engineering/CODE_DESIGN.md` §2.2 still says it
  "raises `NotImplementedError`, deferred to Phase 6" — that note is stale. `main` has taken the
  doc fix and instructed me not to touch `schemas.py`, so I did not.

## 8. Coordination

**Messages sent:** One, to `main`, before writing code: the two decoder-semantics readings and why
the sequential one falsifies definition-of-done item 5; the colour-in-row question for
`nauty_certificate_rows`; the `metric_space -> iso_backends` layering conflict; and the note that
`LabelVocabulary.fit` already exists. Outcome: all four ratified as I proposed, with three added
instructions — pin a test showing the two readings agree on canonical words, document the
exact-at-zero rationale in the rows docstring, and do not touch `schemas.py` or
`nauty_levi_edit.py`. All three were carried out.

**Messages received and how they changed the work:** `main`'s reply removed the ambiguity before
any of it reached the code, and added the agreement test
(`TestPositionInsensitivity::test_the_two_readings_agree_on_every_canonical_word`) that I would
otherwise not have written.

**Contracts I depend on and confirmed unchanged:**
`SparseHypergraph.__init__` keyword shape and `iter_edges()` yielding `(edge_id, members, label)`
(read in `core/sparse_hypergraph.py`); `add_hyperedge` returning the existing id on a duplicate
`(label, member-set)`, which is what makes "a repeated fact is a no-op" free; `permute` preserving
edge order; `LeviGraph.color_classes()` / `color_signature()`; `HypergraphDistance`'s
`name`/`pairwise`/`matrix`/`fingerprint`; `register_distance` / `_LAZY_MODULES` /
`get_distance`; `PynautyLeviBackend.fingerprint` as the oracle. I changed none of them.

## 9. Deliberately not done

- `datasets/schemas.py` — untouched. `LabelVocabulary.fit` already satisfies its contract and is
  already tested; `main` instructed me to verify rather than rewrite.
- `scripts/diagnostics/.../f4_encodings.py` — the overclaiming docstring is left as found; the probe
  is outside my ownership and read-only. Reported in §7 instead.
- `metric_space/representations/nauty_levi_edit.py` — its layering note is now partly superseded by
  my module, but `main` owns that edit at integration.
- The `nauty_cert_rows` *distance* — I supply the primitive only; the registered distance belongs to
  wave 2's `competitors-kb`.
- Roles on the three ablation arms, and any use of `nauty_certificate_bytes`/`_rows` in a registered
  distance — both out of scope.
- The 3 pre-existing ruff errors, the 1 pre-existing format diff and the 20 pre-existing mypy errors
  in files I do not own — left alone; listed in §6 so their presence is not read as mine.

## 10. Risks and follow-ups

| Item | Severity | Detail | Suggested owner |
|---|---|---|---|
| Rank vectors are not transportable | medium | Wave 2's alignment / reach / consensus code could reasonably assume `canonical_ranks` corresponds across isomorphic inputs. It does not, on ~28 % of inputs. Documented and regression-pinned, but the trap is easy to fall into | `language-layer` (W2-A); flag in its prompt |
| The probe docstring and any prose repeating it | low | "the induced ranks are isomorphism-invariant" should read "the induced *word* is" | orchestrator / doc pass |
| `CODE_DESIGN.md` §2.2 stale on `LabelVocabulary.fit` | low | Says it raises `NotImplementedError`; it does not | `main` (already taken) |
| Roles arm raises on `pairwise` | low | A registry-driven runner reaching `fact_rank_roles` through the hypergraph-only path will crash rather than mislead. Intentional, but the matrix builder must special-case it | `toolkit-stats` (W2-B) |
| Alphabet scoping is by convention, not enforced | low | Nothing stops a caller from comparing words written against different type/predicate vocabularies; the result would be meaningless rather than an error. Documented in the module docstring | `toolkit-stats` (W2-B) matrix builder |
| Arms C/D/D1 words are not decodable | low | Their tokens carry the address inside the token, so `decode_fact_word` does not read them. Documented; they are comparison arms, not a language | — |

## 11. Self-assessment against the definition of done

| # | Criterion | Met | Evidence |
|---|---|---|---|
| 1 | Round-trip on fixtures + ≥ 500 random labelled KBs, with and without roles | yes | `TestRoundTrip` (unit, exact `== permute(H, rank)`) and `tests/property/…::TestRoundTrip` — 3 sweeps × 500 cases, n ∈ [3,12], max arity 5, roles included |
| 2 | Iso-invariance ≥ 500 random cases per arm (B, C, D, D1) | yes | `TestIsomorphismInvariance::test_arm_b_fact_rank` and `::test_displaced_arms[3 arms]`, 500 cases each |
| 3 | Completeness vs pynauty on ≥ 1,000 KBs with genuine collisions; 0 false merges / splits, all four arms | yes | `TestCompleteness`, N = 1,000, 764 classes / 236 duplicates; distinct words = 764 for every arm |
| 4 | Hypothesis totality over `token_vocabulary(n ≤ 8, k ≤ 4, n_preds ≤ 3, n_types ≤ 3)`, length 0–40, re-encode consistent | yes | `TestTotality::test_decoder_never_raises_and_re_encodes_consistently` (400 examples) + `::test_the_generated_sequences_cover_the_awkward_shapes` proving the draws hit T-after-F, ranks-past-prefix and repeated facts |
| 5 | Position-insensitivity lemma pinned, moved T tokens included | yes | `TestPositionInsensitivity` (4 unit tests incl. the negative control and the two-readings agreement) + `TestPositionInsensitivityAtScale` (300 random words) |
| 6 | Golden words for Fano, STS(9), a 4-node labelled fixture | yes | `TestGoldenWords`; hand-checked once (§ the STS pair-incidence count) and re-checked automatically by `test_golden_is_a_steiner_triple_system` |
| 7 | One inserted fact over existing constants costs exactly 1 when the order is unchanged | yes | `TestSingleFactInsertion` — a frozen 7-constant KB, ranks `(2,6,5,4,1,3,0)` before and after, distance 1, diff is one inserted `("F", 0, (5, 6))` token |
| 8 | `LabelVocabulary.fit` implemented with a unit test | yes (pre-existing) | Already implemented in `schemas.py`; `tests/unit/datasets/test_arb_benson.py::TestLabelVocabularyFit` — 2 passed. `main` instructed me not to touch it; `CODE_DESIGN.md`'s note is stale (§7) |
| 9 | Five names resolve through `get_distance`; existing tests green; ruff and mypy clean | yes | `TestRegistry` (5 parametrised + listing test); `1480 passed, 6 skipped`; ruff and mypy clean on my 11 files, pre-existing debt elsewhere itemised in §6 |
| 10 | Timing recorded | yes | `fact_word` 36.8 µs/KB over 1,000 n=10 m=15 KBs; `canonical_string(cpp, k=3)` 415.7 µs over 50; ratio 11.3× |
| 11 | All work committed, tree clean, log committed | yes | `e612a37` (code) + this file as the final commit |

**Overall:** I am confident in the encoder, the decoder and the four addressings: the properties
that matter are measured at the required scale with numbers rather than assertions, and the two
places where I departed from the most literal reading of the contract were raised before
implementation and ratified. The orchestrator should scrutinise two things first. One, the decoder
semantics — the choice is defensible and provably invisible on canonical words, but it is a
definitional commitment that wave 2's ball and alignment code inherits, so it deserves a second
reading of `core/fact_word.py`'s module docstring. Two, the rank-equivariance finding: the code is
right and the tests now say so precisely, but the loose claim it corrects came from the probe and
may have propagated into the article prose. I am least certain about how `fact_rank_roles` will be
driven in practice; I made it fail loudly rather than guess, which pushes the decision onto the
matrix builder in wave 2.
