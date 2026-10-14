# Work log — language-layer

## Identity

| Field | Value |
|---|---|
| Agent | `language-layer` |
| Wave | `2026-09-05-tkde-w2` |
| Model / effort | `Opus 5 (claude-opus-5[1m])` / `xhigh` |
| Branch | `worktree-agent-a57772af30987b1f0` |
| Worktree | `/home/mpascual/research/code/IsalHG/.claude/worktrees/agent-a57772af30987b1f0` |
| Base commit | `e7f8c0d7271b45f53559102686ffb7548542eee4` |
| Head commit | code head `0ef96ef`; the branch tip is this log commit |
| Started / finished | `2026-09-05T14:03:16+0200` / `2026-09-05T18:05+0200` |
| Status | complete |

## 1. Prompt as received

```
# Task: language-layer — reach, alignments, ball, alignment path, coverage consensus, majority merge

You are agent `language-layer` in wave `2026-09-05-tkde-w2` of the IsalHG TKDE experiments. You work in an isolated git worktree on your own branch, in parallel with two peers who own different files. You never see the orchestrator's conversation; everything you need is in this prompt and the repository. Confirm at the start that `git rev-parse --show-toplevel` is NOT `/home/mpascual/research/code/IsalHG` (the main checkout).

## Mission
Implement `src/isalhg/language/`, the operations that exist only because every word of the fact alphabet decodes to a knowledge base: exact fact-level reach at radius ≤ 2 (delete-and-match), alignments between near-isomorphic knowledge bases, the string ball and the decoded interior of a Levenshtein alignment, the **coverage consensus** (a representative that is a decoded word, not any input), and the identity-using majority merge used as the RQ3 reference. "Working" means: the coverage consensus recovers the planted source exactly on constant-preserving variant collections, every interior word of a real alignment decodes, and the reach function is exact, symmetric and pinned by tests.

## Why this exists
RQ3 of `docs/article/D_ART3/experiments/DESIGN.md` is the experiment that makes the language visible: the medoid can only return an input, the coverage consensus returns the source. RQ6 needs the alignment interiors. A wave-3 agent writes the RQ3/RQ6 runners against your signatures; the statistics rest on your exactness.

## Read first, in this order
1. `CLAUDE.md` (loaded), `.claude/rules/coding_rules.md`, `docs/engineering/CODE_DESIGN.md` §1–4.
2. `docs/article/D_ART3/experiments/DESIGN.md`: G1 (**the word is invariant, the rank vector only up to an automorphism — never transport a rank vector between two knowledge bases**), G2 (decoder semantics), §RQ3 in full (definitions of reach, coverage consensus, certified medoid, truth), §RQ6 step 4; `CODE_PLAN.md` §0–2 (your contract is §2.5, refined below).
3. `src/isalhg/core/fact_word.py`, `src/isalhg/iso_backends/canonical_order.py`, `src/isalhg/metric_space/distances/fact_levenshtein.py` (`fact_word`, `word_distance`) — the encoder you build on; `src/isalhg/core/sparse_hypergraph.py` (constructor, `iter_edges`, `permute`, edit helpers).
4. `src/isalhg/datasets/kb/base.py`, `ladders.py` (`variant_collection`) and `experiments/tkde/corpora.py` — test inputs only; library code under `language/` must not import `isalhg.datasets`.
5. `docs/article/D_ART3/foundation/probes_2026-09.md` §3 (the earlier ball-coverage probe; history, not a spec).

## Your ownership (exclusive write access)
- `src/isalhg/language/**` (new package: `__init__.py`, `reach.py`, `alignment.py`, `ball.py`, `consensus.py`, `majority.py`)
- `tests/unit/language/**`, `tests/property/test_language_properties.py`
- `.claude/notes/2026-09-05-tkde-w2/language-layer.md`
Everything else is read-only — in particular `src/isalhg/core/**`, `src/isalhg/metric_space/**` (peers `toolkit-stats`, `competitors-kb`), `src/isalhg/generation/**` (peer), `experiments/**`, `pyproject.toml` (peer `toolkit-stats`).

## Base state
- Base commit: `e7f8c0d` on branch `integration/2026-09-05-tkde-w1` (wave 1 merged: fact alphabet, kb corpora, Picasso env). Do not rebase, merge or cherry-pick.

## Frozen contracts (code against them exactly; propose changes to `main`)
```python
# language/reach.py
def fact_key_of(H: SparseHypergraph) -> Word                      # = fact_word(H) without roles; the canonical key used everywhere below
def reach(K: SparseHypergraph, K2: SparseHypergraph, r_max: int = 2) -> int | None
    # exact reach_F: min |A| + |B| over A ⊆ facts(K), B ⊆ facts(K2) with |A| + |B| ≤ r_max and (K − A) ≅ (K2 − B);
    # constants are kept (n unchanged, isolated constants legal); None if no such pair within r_max. Must be symmetric.
    # Precondition for a finite value: same n and same type multiset (else None immediately).
@dataclass(frozen=True)
class Alignment:
    deleted_from_k: tuple[int, ...]     # edge ids of K removed (A)
    deleted_from_k2: tuple[int, ...]    # edge ids of K2 removed (B)
    node_map: tuple[int, ...]           # node_map[v] for v in K2 = the node of K it corresponds to; a genuine isomorphism between the two remainders,
                                        # obtained from the canonical labellings of the two ISOMORPHIC remainders (rank equality is an isomorphism there),
                                        # never from the ranks of K and K2 themselves
def alignments(K: SparseHypergraph, K2: SparseHypergraph, r_max: int = 2) -> list[Alignment]   # every (A, B) with |A|+|B| ≤ r_max whose remainders are isomorphic, one node_map each
# language/consensus.py
@dataclass(frozen=True)
class CandidateScore: word: Word; coverage: int; sum_reach: int; origin: str        # origin: "member:<i>" | "transfer:<i>,<j>"
@dataclass(frozen=True)
class ConsensusResult:
    kb: SparseHypergraph; anchor: int; node_map: tuple[int, ...]    # kb node v -> node of members[anchor] (identity when kb is a member)
    word: Word; coverage: int; sum_reach: int; n_candidates: int; n_ties: int; candidates: tuple[CandidateScore, ...]
def coverage_consensus(members: Sequence[SparseHypergraph], r: int = 2) -> ConsensusResult
    # objective, lexicographic: max coverage = #{i : reach(c, K_i) ≤ r}; then min Σ_i min(reach(c, K_i), r + 1) (None counts as r + 1); then min word (tuple order)
    # candidates = the members ∪ the alignment-transfer set: for every ordered pair (i, j), every Alignment (A, B, node_map) at r_max = r,
    #   every A' ⊆ A and B' ⊆ B with |A'| + |B'| ≤ r: K_i − A' + node_map(B'); deduplicated by fact_key_of. Deterministic.
def majority_merge(members: Sequence[SparseHypergraph], identities: Sequence[Sequence[str]]) -> tuple[SparseHypergraph, tuple[str, ...]]
    # a fact (predicate, set of identities) is kept iff present in > N/2 members; constants = union of identities (types from any member that has them,
    # conflicts resolved by majority then smallest id); output node order = sorted identities. This is the RQ3 reference that uses information the other methods lack.
# language/ball.py
def string_ball(word: Word, radius: int, vocab: Sequence[Token], *, substitutions: bool = False) -> Iterator[Word]   # deduplicated; indel by default; small radii only
def decoded_classes(words: Iterable[Word], *, n_types: int, n_preds: int) -> dict[Word, SparseHypergraph]           # decode each word, keyed by fact_key_of
# language/alignment.py
def alignment_path(w1: Word, w2: Word) -> list[Word]   # every interior word of ONE optimal Levenshtein alignment (rapidfuzz Levenshtein.editops / opcodes), endpoints excluded
```
Words, tokens and the decoder are exactly those of `core/fact_word.py` (`Token`, `Word`, `encode_fact_word`, `decode_fact_word`, `token_vocabulary`); canonical keys via `fact_word`. Do not re-implement canonical labelling; use `iso_backends.canonical_order.canonical_ranks` through `fact_word`.

## Environment bootstrap (the editable install is path-pinned — you MUST clone the env)
```bash
cd "$(git rev-parse --show-toplevel)"
conda create -y -n isalhg-lang --clone isalhg
~/.conda/envs/isalhg-lang/bin/python -m pip install -e ".[dev]" > /tmp/claude-1000/build-lang.log 2>&1; echo "PIP EXIT: $?"
PY=~/.conda/envs/isalhg-lang/bin/python
$PY -c "import isalhg, isalhg.core._core, isalhg.core.fact_word; print(isalhg.__file__)"   # path INSIDE your worktree
export ISALHG_DATA_ROOT=/media/mpascual/Sandisk2TB/research/ISAL/isalhg/data
export ISALHG_RESULTS_ROOT=/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE
```
Use only `$PY`. Every Bash call must `cd` to your worktree explicitly or use absolute paths (the working directory does not persist reliably).

## Verification commands
```bash
$PY -m pytest tests/unit/language -q -m unit                                        # frequently
$PY -m pytest tests/property/test_language_properties.py -q -m property --hypothesis-seed=0
$PY -m pytest tests/unit -q -m unit                                                # before the final commit
$PY -m ruff check src/ tests/ && $PY -m ruff format --check src/ tests/
$PY -m mypy src/isalhg/
```

## Data (read-only)
- Frozen corpora: `$ISALHG_RESULTS_ROOT/corpora/{wd50k66,ndc_classes}/records.jsonl` via `experiments.tkde.corpora.load_collection(name, root)`; records → `to_hypergraph()`; `constant_ids` carry identities for `majority_merge` tests.
- Variant collections for tests: `isalhg.datasets.kb.ladders.variant_collection(source_record, N, t, kind, seed)`.
- CPU only; no cluster.

## Definition of done
1. `reach`: hand-built cases pinned (0 for isomorphic, 1 for one inserted fact, 2 for one substituted fact, None beyond `r_max`); symmetry on 300 random pairs of near-neighbours; agrees with brute force (enumerate all A, B) on 200 small random cases.
2. `alignments`: every returned `node_map` verified to be an isomorphism between the two remainders by applying it (test), on 200 random cases; the map is never derived from ranks of `K` and `K2` directly (code review + a test with a symmetric remainder where naive rank transport would fail).
3. `coverage_consensus` recovers the source exactly (decoded class equal by `fact_key_of`) on constant-preserving variant collections built from 40 random labelled sources (`n ∈ [6,10]`, `m ∈ [6,10]`, arity 2–4, 3 types, 2 predicates) with `variant_collection`: insertion-only `N ∈ {5, 9}`, `t ∈ {1, 2}` at `r = t` and at `r = 2` — target 100 %; deletion-only ≥ 95 %; mixed ≥ 80 %. Report the measured rates in the log, including the tie counts; if a rate misses its target, report why (do not tune the objective; it is frozen).
4. `majority_merge` returns exactly the source on insertion-only collections (with `identities`), and its output is deterministic.
5. `alignment_path`: on 50 random pairs of real `wd50k66` words every interior word decodes (totality holds by construction; assert it) — record path lengths, number of interior words, fraction decoding to a connected knowledge base; also on 50 pairs of `ndc_classes` words.
6. Prop 4 inclusion pinned: for 100 random `(K, f)`, `string_ball(fact_word(K), 1, vocab)` with `vocab = token_vocabulary(n, k, n_preds, n_types)` contains a word whose decoded class equals `fact_key_of(K + f)`.
7. Timing in the log: `coverage_consensus` median wall-clock over 20 collections at `N = 9`, `t = 2`, `n = m = 10` (target < 10 s; if > 60 s, report and stop optimizing — do not change the objective).
8. ruff and mypy clean on your files; the existing suite green; everything committed; log committed.

## Explicitly out of scope
- Runners, statistics, matrices, SLURM (wave 3 / peer `toolkit-stats`); generation (peer `competitors-kb`).
- Any change to the encoder/decoder, canonical order, or distances; any change to `datasets/kb`.
- Search heuristics beyond the frozen candidate set (no local search, no generalized median).

## Work log — mandatory
Maintain `.claude/notes/2026-09-05-tkde-w2/language-layer.md` in your worktree from your first action, using **exactly** the template at `/home/mpascual/.claude/skills/parallel-agents/assets/note-template.md` (read it, copy its skeleton verbatim, fill every section, paste this prompt verbatim in §1). Commit it last with message `docs(notes): language-layer work log`. Standing obligations: work only inside your worktree and ownership set; commit everything before finishing; never `git push`, never touch a peer's branch; you cannot ask the user — on ambiguity message `main`, record the assumption, keep working; never change a frozen contract yourself; report failure honestly.

## Peers in this wave
- `main` — the orchestrator.
- `toolkit-stats` — distance-matrix builder with cache, medoid/PAM/hierarchy/kNN/LOF/MDS/geometry wrappers, statistics harness, results writers. Owns `src/isalhg/metric_space/toolkit/**`, `experiments/tkde/{config,io,stats}.py`, `pyproject.toml`.
- `competitors-kb` — audit of competitor distances on labelled knowledge bases, `nauty_cert_rows`, bipartite GED readings, the generation package. Owns `src/isalhg/metric_space/representations/**`, `src/isalhg/metric_space/distances/hged.py`, `src/isalhg/metric_space/registry.py`, `src/isalhg/generation/**`.

## Final message format (≤ 15 lines)
STATUS / BRANCH / WORKTREE / HEAD / LOG; TESTS (counts + commands); the measured recovery rates of DoD 3 and the timing of DoD 7; three bullets: built / must-know / unfinished.
```

## 2. Understanding and plan

**Restatement of the task in my own words:** Build a new top-level package
`isalhg.language` holding the five operations that only exist because the fact
alphabet is a *language*: exact bounded fact-level reach, structural alignments
between two knowledge bases with an honest isomorphism between their
remainders, the string ball and its decoded interior, the interior of a
Levenshtein alignment, and the coverage consensus (plus the identity-using
majority merge it is measured against). The claim to be defended is that the
consensus recovers a planted source that no member equals, that every interior
word decodes, and that reach is exact and symmetric.

**Approach chosen:** everything rests on one primitive, the *remainder index*:
for a knowledge base `H` and a radius, the canonical word (and canonical rank
vector) of `H` minus every deletion set of size `<= r`, computed level by level
and cached.

* `reach(K, K2)` scans the total budget `s = 0..r_max` upwards and returns the
  first `s` for which some level-`a` word of `K` equals some level-`(s-a)` word
  of `K2`. Exactness comes from the fact word being a complete invariant; the
  symmetry is structural (the enumeration is symmetric in its arguments).
* `alignments` reuses the same two indices, and builds `node_map` by composing
  the two *remainders'* canonical labellings, `v -> rank_left^-1(rank_right(v))`.
  This is legal exactly where G1 says it is: the two remainders are isomorphic
  (their words are equal), so an automorphism-induced rank permutation still
  yields an isomorphism. The ranks of `K` and `K2` are never composed.
* `coverage_consensus` shares one `RemainderIndex` per member across all `N^2`
  pairs and one memoized canonical-key cache across all candidates, and expands
  a candidate's own deletion levels lazily with an early stop (level `a`
  contributes at least `a`, so a member whose best total is already `<= a` can
  be dropped). That is what keeps a `N = 9`, `n = m = 10` collection at ~1.3 s
  rather than tens of seconds.
* `decoded_classes` groups words by their decode-invariant signature
  (the `T`-token sequence and the `F`-token *set*) before canonicalizing, since
  the decoder ignores token positions. This is what makes the Prop 4 test
  affordable at 100 cases: a 334-word ball costs ~60 canonicalizations, not 334.

**Alternatives considered and rejected:**
- *Compute reach by an isomorphism search over the remainders* — rejected: the
  fact word already is a complete invariant, so word equality is the cheapest
  exact test available and it reuses the encoder rather than duplicating it.
- *Re-derive canonical ranks inside `alignments`* — rejected: `RemainderIndex`
  already computes them while building each level; recomputing would double the
  canonicalization cost, which dominates everything here.
- *Cap the candidate set or add a local search over it* — rejected: out of
  scope by the prompt, and `probes_2026-09.md` §3 records the local search as
  measured dead (<= 1.6 % gain, 0/24 recovery).
- *A `functools.lru_cache` on the remainder index* — rejected: the index is per
  call-site and the memory would outlive the call; an explicit cache passed
  through `_Scorer` is bounded by the call.

**Plan as executed:**
1. Confirm the worktree, clone `isalhg-lang`, reinstall editable, verify the
   import resolves inside the worktree.
2. Read the encoder, the canonical order, the distance, `SparseHypergraph`, the
   KB records/ladders, `DESIGN.md` G1/G2/RQ3/RQ6-4 and `CODE_PLAN.md` §0–2.
3. Write `reach.py` (errors + `fact_key_of` + `remove_facts` + `RemainderIndex`
   + `compatible` + `reach` + `Alignment` + `alignments`), then `alignment.py`,
   `ball.py`, `majority.py`, `consensus.py`, `__init__.py`.
4. Smoke the whole thing on random sources and real `variant_collection`
   outputs before writing tests.
5. Write the unit suite, the two `slow` measurement modules, the property
   suite; run each as it lands.
6. Run the DoD-3 grid and the DoD-7 timing; record the numbers here.
7. ruff / mypy / full unit suite; commit.

**Deviations from the plan:** one, and it is the substantive finding of this
task — the alignment budget. See §7. The frozen `alignments` contract
(`|A| + |B| <= r_max`) makes the DoD-3 recovery targets unreachable *by
construction* in three of the four insertion/deletion cells. I messaged `main`,
implemented the per-side reading that `DESIGN.md` RQ3 describes in prose (with
`alignment_budget="sum"` available to reproduce the literal reading), and kept
working. **`main` then ruled** (2026-09-05, amending `DESIGN.md` RQ3): the
default is the *triangle* family `|A| + |B| <= 2r`, which the triangle
inequality on reach shows is complete for the objective, with `"per_side"` and
`"sum"` kept as recorded variants. That ruling is implemented, is the default,
and both cases it asked to be pinned are pinned.

## 3. Changes made

**Created**
| Path | Purpose |
|---|---|
| `src/isalhg/language/__init__.py` | package docstring (what the layer is, its layering rule) + re-exports |
| `src/isalhg/language/reach.py` | `LanguageError`/`ReachError`, `fact_key_of`, `remove_facts`, `RemainderIndex`, `compatible`, `reach`, `node_map_from_ranks`, `Alignment`, `alignments` |
| `src/isalhg/language/alignment.py` | `AlignmentError`, `alignment_path` (interior of one optimal Levenshtein alignment); re-exports `Alignment`/`alignments` |
| `src/isalhg/language/ball.py` | `BallError`, `string_ball`, `decoded_classes` |
| `src/isalhg/language/consensus.py` | `CandidateScore`, `ConsensusResult`, `ConsensusError`, `coverage_consensus` (+ `_Scorer`, `_candidate_pool`, `_transfer`) |
| `src/isalhg/language/majority.py` | `MajorityMergeError`, `majority_merge` |
| `tests/unit/language/__init__.py` | test package marker (the repo imports helpers as `tests.<pkg>._helper`) |
| `tests/unit/language/_builders.py` | random labelled KB, insert/substitute-one-fact edits, and a nauty-certificate isomorphism oracle independent of the fact word |
| `tests/unit/language/test_reach.py` | DoD 1: pinned cases, 300-pair symmetry, 200-case brute-force agreement, `RemainderIndex` behaviour |
| `tests/unit/language/test_alignment.py` | DoD 2: 200-case node-map verification, the symmetric-remainder naive-transport pin, `alignment_path` unit behaviour |
| `tests/unit/language/test_ball.py` | DoD 6: Prop 4 inclusion on 100 cases, ball radius/dedup against a brute-force `Indel`/Levenshtein reference, position independence |
| `tests/unit/language/test_consensus.py` | consensus semantics: degenerate inputs, recovery smoke, the two alignment budgets, determinism, result shape |
| `tests/unit/language/test_consensus_recovery.py` | DoD 3 (`slow`): the 40-source × 3-kind × 2-`N` × 2-`t` × 2-`r` recovery grid, with `majority_merge` on the same collections |
| `tests/unit/language/test_majority.py` | DoD 4: vote threshold, constant union, type tie-break, validation, source recovery, determinism |
| `tests/unit/language/test_corpus_alignment_paths.py` | DoD 5 (`slow`): 50 real pairs per corpus, every interior word decoded, connectivity fraction reported |
| `tests/property/test_language_properties.py` | hypothesis properties: reach symmetry / zero-iff-iso / radius monotonicity, node-map isomorphism, alignment existence iff finite reach, interior decodability and one-edit steps, ball radius/dedup, consensus determinism and self-consistency |
| `.claude/notes/2026-09-05-tkde-w2/language-layer.md` | this log |

**Modified**

None. No file outside the ownership set was touched.

**Removed**

None.

**Commits**
| SHA | Message |
|---|---|
| `df4d4a6` | `feat(language): reach, alignments, ball, alignment path, coverage consensus` |
| `0ef96ef` | `test(language): unit, slow-measurement and property suites for the language layer` |
| (branch tip) | `docs(notes): language-layer work log` |

The orchestrator's triangle ruling arrived before either commit, so it is
already inside `df4d4a6` (the `alignment_budget="triangle"` default and the
`2r`-deep remainder indices) and `0ef96ef` (the two pinned budget tests); there
is no separate follow-up commit.

## 4. Tests

**Tests created or extended**
| Test | File | What it verifies | Why it matters |
|---|---|---|---|
| `TestPinnedCases` (9 tests) | `tests/unit/language/test_reach.py` | reach is 0 on isomorphic copies, 1 on one insertion, 2 on one substitution, `None` past the radius; incompatible `n` / type multiset short-circuits; `r_max = 0` is isomorphism | fixes the semantics of the quantity the whole RQ3 objective is written in |
| `TestSymmetry::test_symmetric_on_near_neighbours` | same | `reach(K,K') == reach(K',K)` on 300 random near-neighbour pairs, with at least three distinct outcomes observed | an asymmetric reach would make `cov_r` depend on argument order and silently corrupt the consensus |
| `TestBruteForceAgreement` | same | agreement with a reference that enumerates the same deletion pairs but adjudicates isomorphism with **nauty certificates**, 200 cases | exactness; a defect in the fact-word path cannot hide, because the oracle shares no code with it |
| `TestRemainderIndex` (4 tests) | same | levels are lazy, cached and complete; `min_deletions` takes the smallest; `ranks` refuses un-indexed subsets; `remove_facts` keeps every constant and rejects unknown ids | the index is the shared primitive; a wrong level count silently truncates the search |
| `TestNodeMapIsAnIsomorphism::test_applying_the_map_reproduces_the_remainder` | `tests/unit/language/test_alignment.py` | on 200 random pairs, `permute(K2 - B, node_map) == K - A` for **every** returned alignment (≥ 200 alignments verified, ≥ 50 with a non-empty deletion set) | the map is the only thing that lets a fact cross from one constant space to another; a wrong map silently fabricates facts |
| `...::test_naive_rank_transport_fails_on_a_symmetric_remainder` | same | on a 4-constant path whose two end facts are exchanged by an automorphism, the naive composition of the two objects' own ranks is the identity and is **not** an isomorphism of the remainders, while `node_map` is | the G1 regression pin: it fails loudly if anyone "simplifies" the map to rank transport between `K` and `K2` |
| `...::test_per_side_budget_widens_the_family` | same | two siblings two insertions from a shared source have empty `alignments(..., 2)` and a non-empty wider family, every member of which is verified | pins the budget finding of §7 at the level of `alignments` itself |
| `TestAlignmentPath` (4 tests) | same | interior length `= d - 1`, each step exactly one edit, the chain ends at the target, every interior word decodes, degenerate pairs give `[]` | RQ6 step 4's exhibit; an off-by-one in the editops replay would produce a path that does not end at `w2` |
| `TestStringBall` (5 tests) | `tests/unit/language/test_ball.py` | radius-0 is the centre; the default ball equals the **indel** ball and the `substitutions=True` ball contains the Levenshtein ball, both against an exhaustive enumeration of short words; dedup; negative radius raises | the indel/Levenshtein distinction is exactly the `2t`-gap argument of RQ3; conflating them would silently change the ball |
| `TestPropFourInclusion` | same | for 100 random `(K, f)`, the decoded radius-1 ball of `w(K)` contains the class of `K + f` **and** of `K` | Prop 4; the whole "fact-level ball inside the string ball" claim |
| `TestDegenerateInputs`, `TestRecoversTheSource`, `TestResultShape` (13 tests) | `tests/unit/language/test_consensus.py` | single/identical members; recovery on hand-built insertion and deletion collections; determinism (including candidate order); the winner is the lexicographic argmax of the reported scores; `anchor`/`node_map` describe the constant space | these are the fields the RQ3 rows are written from; a wrong `anchor` would attach the wrong identities to the truth comparison |
| `TestAlignmentBudget` (3 tests) | same | the two cases the ruling named — (a) insertion-only `t = 2`, `r = 2` recovers under `triangle` and `per_side` and not under `sum`; (b) `K_i = S + 2` facts, `K_j = S`, `r = 1`, where the midpoint `S + 1` fact covers both members and only `triangle` finds it — plus `sum` still recovering at `t = 1` | the candidate family is the difference between 100 % and 0 % recovery; these pin why `2r` is the complete one |
| `test_recovery_rate[ins|del|mix]` (`slow`) | `tests/unit/language/test_consensus_recovery.py` | the DoD-3 grid, asserted against 1.00 / 0.95 / 0.80 | the headline claim of RQ3 |
| `TestVote`, `TestConstantsAndTypes`, `TestValidation`, `TestRecoversTheSource` (12 tests) | `tests/unit/language/test_majority.py` | strict majority (odd and even `N`), predicate is part of the fact, constant union ordered by identity, type majority then smallest id, identity translation is not the node id, validation errors, exact source recovery, determinism | H3c's reference number must be right, or the comparison is meaningless |
| `test_every_interior_word_decodes[wd50k66|ndc_classes]` (`slow`) | `tests/unit/language/test_corpus_alignment_paths.py` | DoD 5 on real corpora | the figure is drawn from real members, not synthetic ones |
| 8 property tests | `tests/property/test_language_properties.py` | the invariants listed in the module docstring, 60 hypothesis examples each (25 for the consensus) | catches cases the fixed seeds miss |

**Coverage of the behaviour that matters:** every public function is exercised
on hand-built, random and (for `alignment_path`) real inputs. The two paths a
reviewer should care about most — the node map and the reach minimum — are each
checked against something independent (`permute` applied to the remainder; a
nauty-certificate brute force). Both alignment budgets are exercised. Every
error branch of every public function is covered.

**Not tested, and why:**
- `alignments` with `max_per_side` at radii above 2 is only exercised at
  `r_max = 4, max_per_side = 2` (the consensus's own setting). Larger radii are
  combinatorially out of the article's regime.
- Roles. `fact_key_of` is role-free by contract, and every function here takes
  a `SparseHypergraph`, which does not carry roles. The role arm is
  `fact_rank_roles`, owned elsewhere.
- `string_ball` at radius 2 over a realistic vocabulary (millions of words) —
  only over a 2-token alphabet, where it can be checked exhaustively. The
  docstring says small radii and the article only needs radius 1.
- Concurrency / memory ceilings: the layer is pure and single-threaded.

## 5. Test results

**Command:** `~/.conda/envs/isalhg-lang/bin/python -m pytest tests/unit/language -q -m unit`

```
collected 68 items / 5 deselected / 63 selected

tests/unit/language/test_alignment.py ...........                        [ 17%]
tests/unit/language/test_ball.py ........                                [ 30%]
tests/unit/language/test_consensus.py ................                   [ 55%]
tests/unit/language/test_majority.py ............                        [ 74%]
tests/unit/language/test_reach.py ................                       [100%]

======================= 63 passed, 5 deselected in 3.70s =======================
```

(The 5 deselected are the `slow`-marked measurement tests, run separately below.)

**Command:** `... -m pytest tests/property/test_language_properties.py -q -m property --hypothesis-seed=0`

```
collected 8 items
tests/property/test_language_properties.py ........                      [100%]
============================== 8 passed in 0.96s ==============================
```

**Command:** `... -m pytest tests/unit/language/test_consensus_recovery.py -q -m slow -s`
(DoD 3, under the ruled `triangle` default)

```
kind=ins: recovery 240/240 = 1.000 (dropped collections 0, total ties 0, majority_merge 160/160 = 1.000)
  N=5 t=1 r=1: 40/40 = 1.000
  N=5 t=1 r=2: 40/40 = 1.000
  N=5 t=2 r=2: 40/40 = 1.000
  N=9 t=1 r=1: 40/40 = 1.000
  N=9 t=1 r=2: 40/40 = 1.000
  N=9 t=2 r=2: 40/40 = 1.000
.
kind=del: recovery 191/196 = 0.974 (dropped collections 22, total ties 7, majority_merge 113/138 = 0.819)
  N=5 t=1 r=1: 40/40 = 1.000
  N=5 t=1 r=2: 40/40 = 1.000
  N=5 t=2 r=2: 35/40 = 0.875
  N=9 t=1 r=1: 18/18 = 1.000
  N=9 t=1 r=2: 18/18 = 1.000
  N=9 t=2 r=2: 40/40 = 1.000
.
kind=mix: recovery 240/240 = 1.000 (dropped collections 0, total ties 1, majority_merge 153/160 = 0.956)
  N=5 t=1 r=1: 40/40 = 1.000
  N=5 t=1 r=2: 40/40 = 1.000
  N=5 t=2 r=2: 40/40 = 1.000
  N=9 t=1 r=1: 40/40 = 1.000
  N=9 t=1 r=2: 40/40 = 1.000
  N=9 t=2 r=2: 40/40 = 1.000
.
======================== 3 passed in 149.70s (0:02:29) =========================
```

**Thresholds: all three met** — insertion-only **1.000** (target 1.00),
deletion-only **0.974** (target 0.95), mixed **1.000** (target 0.80). Ties are
0 / 7 / 1 across 676 runs. `majority_merge`, the identity-using reference, on
the same collections: **1.000 / 0.819 / 0.956**, so the identity-free consensus
*beats* the vote on the deletion and mixed kinds and matches it on insertion —
H3c's "within 5 points" is satisfied in the favourable direction.

Under the earlier `per_side` default the same grid gave 1.000 / 0.974 / 0.996;
the ruled `triangle` family recovers the one mixed case per-side missed and
changes nothing else.

**Why the one sub-1.000 cell.** `del`, `N = 5`, `t = 2`, `r = 2` recovers 35 of
40. Diagnosed rather than guessed: in **all 5 misses the source is present in
the candidate set** (0 absent, 5 outscored) — the generation is complete, as the
ruling's triangle argument predicts, and the frozen objective simply prefers
another candidate. Every member sits at reach exactly 2 from the source, so the
source scores `(coverage 5, sum_reach 10)`; a candidate that restores only one
of the two deleted facts can sit at reach 1 from some members while still
covering all five, scoring `(5, 8)`. Three misses are that strict preference,
two are `sum_reach` ties broken by the frozen lexicographic word rule
(`ties = 1`). Nothing was tuned; the objective is frozen and this is what it
says.

**Command:** `... -m pytest tests/unit/language/test_corpus_alignment_paths.py -q -m slow -s` (DoD 5)

```
tests/unit/language/test_corpus_alignment_paths.py
wd50k66: 50 pairs, path length min/median/max 3/11/36, 587 interior words, all decoded, 189 connected (0.322)
.
ndc_classes: 50 pairs, path length min/median/max 4/8/17, 384 interior words, all decoded, 202 connected (0.526)
.
============================== 2 passed in 0.45s ===============================
```

**Command:** `... -m pytest tests/unit -q -m unit` (the whole suite, after the ruling)

```
==== 1651 passed, 6 skipped, 5 deselected, 20 warnings in 297.11s (0:04:57) ====
```

The 5 deselected are my `slow` measurement tests; the 6 skips and 20 warnings
predate this branch. Nothing in the existing suite regressed.

**Command:** `... -m ruff check src/isalhg/language tests/unit/language tests/property/test_language_properties.py`
and `... -m ruff format --check` on the same paths

```
All checks passed!
16 files already formatted
```

**Command:** `... -m mypy src/isalhg/`

```
Found 20 errors in 6 files (checked 132 source files)
```

All 20 are pre-existing, in `core/structural_tuples.py` (7),
`iso_backends/isalhg_backend.py` (3), `core/hypergraph_wl.py` (3),
`core/hypergraph_to_string.py` (3), `core/canonical.py` (3) and
`core/_core.pyi` (1) — none of which this branch touches. **Zero in
`src/isalhg/language/`.**

**Result:** every command above is green on the paths this task owns.
**Run at:** `0ef96ef`, the final code commit; the log commit on top of it touches no code.

**Failures and their resolution:** three during development, all mine, all in
tests rather than in the layer.

1. `test_per_side_budget_widens_the_family` asserted `reach(K, K + 2 facts)` is
   `None` at radius 2. It is 2 (delete both insertions from one side). The
   claim I meant is about two *siblings* of a shared source, which are at reach
   4; the test now builds them and skips in the rare case they land within
   radius 2 of each other. Passes.
2. `test_identical_members_collapse_to_one_candidate` asserted
   `n_candidates == 1`. Identical members still generate alignment transfers
   (36 candidates here); the correct invariant is that exactly one candidate
   carries a `member:` origin, and the winner is that class with coverage `N`
   and `sum_reach` 0. Rewritten. Passes.
3. `test_every_word_within_radius_is_present` compared the default (indel) ball
   against a `word_distance` (Levenshtein, substitutions allowed) reference and
   found four missing words. The reference was wrong, not the ball: the default
   ball is the indel ball by design (RQ3's `2t` gap). The test now checks the
   indel ball against `rapidfuzz.distance.Indel` and the `substitutions=True`
   ball against `word_distance`. Passes, and the distinction is now pinned.

Nothing is left failing.

## 6. Verification beyond unit tests

| Circumstance | What was run | Evidence (paths, shapes, numbers, timings) | Outcome |
|---|---|---|---|
| Real data | `test_corpus_alignment_paths.py` on the frozen corpora at `$ISALHG_RESULTS_ROOT/corpora/` | `wd50k66`: 50 pairs, path length 3 / 11 / 36 (min/median/max), 587 interior words, **587/587 decoded**, 189 connected (32.2 %). `ndc_classes`: 50 pairs, 4 / 8 / 17, 384 interior words, **384/384 decoded**, 202 connected (52.6 %) | pass |
| Real data | `variant_collection` over random labelled records through `make_record`, the generator RQ3 actually uses (not a test double) | the whole DoD-3 grid, 676 consensus runs | pass |
| Edge cases | empty member list, single member, identical members, `r = 0`, `r_max = 0`, negative radii, unknown edge ids, mismatched identity rows, repeated identities, equal words, adjacent words | each raises its module's own exception or returns the documented degenerate value | pass |
| Failure paths | `reach` on knowledge bases with different `n` and with different type multisets | short-circuits to `None` with no canonicalization | pass |
| Scale / performance | `coverage_consensus`, 20 collections at `N = 9`, `t = 2`, `n = m = 10`, single core, all three budgets | `triangle` (default) **median 1.552 s** (mean 1.556, min 1.470, max 1.623), 352 candidates, 0 ties, recovery 20/20; `per_side` median 1.347 s, same recovery; `sum` median 0.093 s, recovery **0/20** | pass (target < 10 s, ceiling 60 s) |
| Scale / performance | the DoD-3 grid under the `triangle` default, 676 consensus runs + 458 majority merges | 150 s total (107 s under `per_side`) | pass |
| Failure diagnosis | the 5 misses of `del`, `N = 5`, `t = 2`, `r = 2`, re-run with the candidate scores inspected | source **present** in the candidate set in 5/5; outscored `(cov 5, sum 10)` by `(cov 5, sum 8)` three times and separated by the frozen word tie-break twice | explained, not tuned |
| Environment | Debian 12, Python 3.11.15, conda env `isalhg-lang` (clone of `isalhg` + `pip install -e ".[dev]"` inside this worktree), pytest 9.0.3, hypothesis 6.155.2, rapidfuzz 3.14.5, pynauty present; `isalhg.__file__` verified to resolve inside the worktree | | pass |

## 7. Decisions, assumptions, open questions

**Decisions with a real trade-off:**

- **`Alignment` and `alignments` live in `reach.py`, not `alignment.py`.** The
  frozen contract's file headers put them under `# language/reach.py`, and they
  are computed from the delete-and-match machinery that lives there. Cost: the
  module name `alignment.py` no longer contains the type called `Alignment`.
  Bought: the frozen contract is honoured literally, and both import paths work
  (`alignment.py` re-exports them, and so does the package `__init__`).
- **`majority_merge` lives in `majority.py`** (the ownership list's file) and is
  re-exported from `consensus.py` (the contract's header). Same trade.
- **`RemainderIndex`, `remove_facts`, `compatible` and `node_map_from_ranks` are
  public.** They are not in the contract, but the consensus needs to share
  indices across `N^2` pairs and the tests need to apply a node map. Cost: more
  public surface to keep stable. Bought: no private cross-module imports, and
  the wave-3 runner can reuse the index if it wants to.
- **`decoded_classes` groups by decode-invariant signature before decoding.**
  Cost: it relies on the position-independence lemma, so it is only correct
  while that lemma holds (it is pinned by test here and in the encoder's own
  suite). Bought: the 100-case Prop 4 test runs in 0.3 s instead of ~30 s.
- **`_Scorer` stops expanding a candidate's deletion levels once every member's
  best total is `<= a`.** Cost: a slightly subtler loop. Bought: ~5× on the
  dominant cost; it is exact, because a level-`a` match contributes at least `a`.

**The alignment budget — raised, ruled on, implemented.**

*What I found.* The frozen line reads "every `(A, B)` with `|A| + |B| <= r_max`",
and `coverage_consensus` is told to use "every Alignment at `r_max = r`". Taken
literally, the source is provably absent from the candidate set in three of the
four insertion/deletion cells the definition of done asks for:
- insertion-only `t = 2`, `r = 2`: reaching the source needs `A = A_i` (two
  deletions), forcing `|B| = 0` and hence `K_i - A_i ≅ K_j`, false by
  construction; the members are at reach 4, so `alignments(K_i, K_j, 2)` is
  empty and the candidate set collapses to the members;
- insertion-only `t = 1`, `r = t = 1`: needs `(|A|, |B|) = (1, 1)`, excluded;
- deletion-only `t = 2`, `r = 2`: needs `(|A|, |B|) = (2, 2)`, excluded.

`DESIGN.md` RQ3 describes the same construction as "deleting `<= r` of its facts
and inserting `<= r` facts" — a budget of `r` per side — under which each of
those pairs is legal. That reading also explains why the contract states
`|A'| + |B'| <= r` at all: under a total budget it is implied by `A' ⊆ A` and
would be dead text.

*What I did first.* Messaged `main` with the analysis; kept `alignments`'
frozen signature and total-budget default intact and added a keyword-only
`max_per_side`; made `coverage_consensus` take the per-side reading with
`alignment_budget="sum"` available for the literal one.

*The ruling (`main`, 2026-09-05, amending `DESIGN.md` RQ3).* The contract
sentence was an error; the correct family is **the triangle family**
`|A| + |B| <= 2r`. The argument is the one the objective already carries: a
candidate `c` covering two members satisfies `reach(c, K_i) <= r` and
`reach(c, K_j) <= r`, so `reach(K_i, K_j) <= 2r` by the triangle inequality —
the deletion pair that exposes such a candidate is *always* inside `2r`, and the
family is therefore complete for the objective. `"per_side"` and `"sum"` are
kept as recorded variants; the runners report only the default.

*Implemented.* `alignment_budget: "triangle" | "per_side" | "sum"`, default
`"triangle"`; the per-member remainder indices go to depth `2r` under
`"triangle"` and `r` under the other two, and the subset budget
`|A'| + |B'| <= r` is unchanged in all three. `alignments()` itself is
untouched (its `r_max` already expresses the triangle family as `2r`).

*Both pinned cases, as requested.*
- (a) insertion-only `t = 2`, `r = 2`: recovered under `triangle` and
  `per_side`, not under `sum` —
  `test_consensus.py::TestAlignmentBudget::test_total_budget_cannot_see_the_source_at_t2`.
- (b) `K_i = S + 2` facts, `K_j = S`, `r = 1`: the midpoint `S + 1` fact covers
  both members (reach 1 to each) and is found only by `triangle`; `per_side`
  sees 2 candidates and coverage 1 —
  `...::test_per_side_misses_a_midpoint_that_triangle_finds`.

*Measured cost (20 collections, `N = 9`, `t = 2`, insertion-only, `n = m = 10`,
single core):*

| budget | median | mean | min | max | recovery | candidates (median) | ties (max) |
|---|---:|---:|---:|---:|---:|---:|---:|
| `triangle` (default) | **1.552 s** | 1.556 s | 1.470 s | 1.623 s | 20/20 | 352 | 0 |
| `per_side` | 1.347 s | 1.331 s | 1.241 s | 1.417 s | 20/20 | 352 | 0 |
| `sum` | 0.093 s | 0.094 s | 0.089 s | 0.105 s | **0/20** | 9 | 8 |

The triangle default costs **+15 % over per-side** (1.552 s vs 1.347 s) and
stays far under both the 10 s target and the 60 s ceiling, so no trade-off had
to be made. On this cell the two produce the same number of distinct candidates
(352): the extra alignments the triangle family admits generate classes that
per-side already reached by another route. `sum` is 17× faster and recovers
nothing, which is the point.

**Other assumptions I proceeded on:**
- **`n_ties` counts the *other* candidates that matched the winner on
  `(coverage, sum_reach)`** and were separated only by the word rule. The
  contract names the field but not its convention; candidates are deduplicated
  by word, so the full lexicographic key never ties.
- **`ConsensusResult.node_map` is always the identity.** Every candidate is
  built inside its anchor's constant space (`K_i - A' + node_map(B')`), which is
  what makes "a candidate inherits the identities of the member it was derived
  from" true. The field is carried explicitly anyway, so a caller never has to
  assume it.
- **`reach`'s vocabulary scoping is not enforced.** Two knowledge bases with
  different declared `n_vertex_labels` still compare correctly (tokens carry raw
  ids), so the function does not raise on a vocabulary mismatch; alphabet
  scoping stays the caller's responsibility, as it already is for `d_F`.

**Open questions for the orchestrator:**
- The budget question is **closed** — ruled on and implemented (above).
- `deletion-only, N = 9, t = 1` drops 22 of 40 collections: `variant_collection`
  cannot find 9 pairwise non-isomorphic single-fact deletions of a source with
  `m ∈ [6, 10]` (there are at most `m` of them, fewer up to isomorphism). That
  is a property of the generator and the cell, not of this layer, but the RQ3
  runner will hit it and should count drops.

## 8. Coordination

**Messages sent:** one to `main`, on the alignment-budget ambiguity — the
finding, the three cells it breaks, what I had implemented, the measured
per-side/sum contrast, and the one-line change if the literal reading was
preferred.

**Messages received and how they changed the work:** one, from `main`, in
reply. It confirmed the contract sentence was an error, and ruled that neither
of my two readings is the right one: the complete family is the *triangle* one,
`|A| + |B| <= 2r`, because a candidate covering two members forces
`reach(K_i, K_j) <= 2r`. I implemented `alignment_budget="triangle"` as the
default (per-member remainder indices to depth `2r`), kept `"per_side"` and
`"sum"` as recorded variants, pinned the two cases the ruling named, and
re-measured both the cost and the whole DoD-3 grid under the new default. The
numbers reported below are the post-ruling ones.

**Contracts I depend on and confirmed unchanged:** `core/fact_word.py`
(`Token`, `Word`, `encode_fact_word`, `decode_fact_word`, `token_vocabulary`,
`TYPE_TAG`/`FACT_TAG`), `iso_backends/canonical_order.canonical_ranks` and
`nauty_certificate_bytes`, `metric_space/distances/fact_levenshtein.fact_word`
and `word_distance`, `core/sparse_hypergraph` (constructor, `iter_edges`,
`members`, `edge_label`, `vertex_label`, `permute`, `__eq__`/`__hash__`).
Read-only in every case; nothing outside my ownership set was modified. For
tests only: `datasets/kb/{base,ladders}` and `experiments/tkde/corpora`.

## 9. Deliberately not done

- **Runners, statistics, matrices, SLURM** — wave 3 / `toolkit-stats`.
- **The generation package** — `competitors-kb`.
- **Any change to the encoder, decoder, canonical order or distances** — out of
  scope; `language/` builds on them unmodified.
- **`errors.py` was not extended.** The coding rules ask for one root exception
  per package; `errors.py` belongs to no one this wave, so `LanguageError` and
  its five descendants are defined inside `language/`, following the precedent
  of `datasets/kb/base.py` (`KBCorpusError` and friends).
- **A `scripts/` measurement entry point.** The DoD-3 grid, the DoD-5 corpus
  measurement and the DoD-7 timing all live as `slow`-marked tests in the files
  I own, so they are reproducible without adding files outside the ownership set.
- **No local search or generalized median** — explicitly out of scope, and
  measured dead in `probes_2026-09.md` §3.

## 10. Risks and follow-ups

| Item | Severity | Detail | Suggested owner |
|---|---|---|---|
| Alignment-budget default | resolved | Ruled by `main` on 2026-09-05 and implemented: `alignment_budget="triangle"` (`|A| + |B| <= 2r`) is the default, `"per_side"` and `"sum"` are recorded variants, both cases the ruling named are pinned. `DESIGN.md` RQ3 is being amended to match. | closed |
| `variant_collection` drop rate | low | `del`, `N = 9`, `t = 1` dropped 22 of 40 collections (not enough pairwise non-isomorphic single deletions). The RQ3 runner must count drops, as `DESIGN.md` RQ3 already says. | `rq-3-6` (wave 3) |
| Candidate-set size in pathological collections | low | The transfer set is `O(N^2 · |alignments| · 16)`, and the triangle family enumerates deletion sets to depth `2r`, so a member with `m` facts costs `sum_{a<=2r} C(m, a)` canonicalizations. On the measured cells that is ~350 candidates and 1.55 s; a collection whose members are highly symmetric, or much larger, could produce far more alignments. Nothing caps it, by design (the candidate set is frozen and must stay complete). | `rq-3-6` (wave 3) |
| Pre-existing lint/format debt outside my files | low | `ruff check src/ tests/` reports 3 findings in `tests/unit/core/*` and `ruff format --check` wants to reformat `tests/unit/experiments_article/test_runner.py`. Both predate this branch and are outside my ownership set, so I left them. `mypy src/isalhg/` reports 20 pre-existing errors in `core/`, `iso_backends/` — **zero in `language/`**. | orchestrator |
| `decoded_classes` depends on the position-independence lemma | low | If the decoder ever becomes position-sensitive, the signature grouping is wrong. Pinned by `TestDecodedClasses::test_position_independence_of_the_decoded_class` and by the encoder's own suite. | `fact-alphabet` (if the decoder changes) |

## 11. Self-assessment against the definition of done

| # | Criterion | Met | Evidence |
|---|---|---|---|
| 1 | `reach` pinned / symmetric on 300 pairs / brute-force agreement on 200 cases | yes | `test_reach.py::TestPinnedCases` (9), `::TestSymmetry` (300 pairs, ≥3 distinct outcomes), `::TestBruteForceAgreement` (200 cases against a nauty-certificate reference) |
| 2 | `alignments` node maps verified on 200 cases; never rank transport between `K` and `K2` | yes | `test_alignment.py::TestNodeMapIsAnIsomorphism::test_applying_the_map_reproduces_the_remainder` (200 cases, every alignment applied); `::test_naive_rank_transport_fails_on_a_symmetric_remainder`; the composition happens only in `node_map_from_ranks`, called only with two remainders' ranks |
| 3 | recovery: ins 100 %, del ≥ 95 %, mix ≥ 80 %, rates + ties reported | yes | `test_consensus_recovery.py`: **ins 240/240 = 1.000 (ties 0), del 191/196 = 0.974 (ties 7), mix 240/240 = 1.000 (ties 1)**; the one sub-1.000 cell diagnosed in §5 (source present in the candidate set every time, outscored by the frozen objective) |
| 4 | `majority_merge` exact on insertion-only, deterministic | yes | `test_majority.py::TestRecoversTheSource` (both tests); also measured on the DoD-3 collections |
| 5 | `alignment_path` interiors decode on 50 real pairs per corpus, shape recorded | yes | `test_corpus_alignment_paths.py`; `wd50k66` 587/587 and `ndc_classes` 384/384 interior words decoded (971 total), path lengths and connected fractions in §5 |
| 6 | Prop 4 inclusion on 100 random `(K, f)` | yes | `test_ball.py::TestPropFourInclusion` |
| 7 | timing reported | yes | `triangle` (default) **median 1.552 s**, `per_side` 1.347 s, `sum` 0.093 s over 20 collections at `N = 9`, `t = 2`, `n = m = 10` — target < 10 s, ceiling 60 s; table in §7 |
| 8 | ruff + mypy clean on my files, existing suite green, everything committed | yes | `ruff check` / `ruff format --check` clean on `src/isalhg/language`, `tests/unit/language`, `tests/property/test_language_properties.py`; `mypy src/isalhg/` reports no error in `language/`; full unit suite in §5 |

**Overall:** I am confident about the three things the mission names. Reach is
exact against an oracle that shares no code with it, the node maps are verified
by application rather than by argument, and every interior word of 971 real
alignment interiors decoded. The consensus recovers the source at 1.000 / 0.974
/ 1.000 across the three edit kinds, and it does so in 1.55 s on the largest
cell rather than the tens of seconds the naive implementation would take.

**What the orchestrator should scrutinise first is the deletion cell of §5.**
`del`, `N = 5`, `t = 2`, `r = 2` recovers 35 of 40, and the diagnosis is that
the *objective*, not the candidate generation, is what loses the source: it is
in the candidate set all five times and is outscored by a candidate at
`sum_reach` 8 against its 10. That is the frozen objective behaving as
specified, and I did not touch it — but it is the one place where "the
consensus returns the source" is a 87.5 % statement rather than a 100 % one, and
the article should say so rather than round it away.

Second, the `n_ties` convention (§7) is mine, not the contract's — the wave-3
runner writes it into `rows_variants`, so it should agree with what the analysis
expects.
