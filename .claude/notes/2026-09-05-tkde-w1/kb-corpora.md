# Work log — kb-corpora

## Identity

| Field | Value |
|---|---|
| Agent | `kb-corpora` |
| Wave | `2026-09-05-tkde-w1` |
| Model / effort | Opus 5 (1M) / high |
| Branch | `worktree-agent-a115a1c540ce48e82` |
| Worktree | `/home/mpascual/research/code/IsalHG/.claude/worktrees/agent-a115a1c540ce48e82` |
| Base commit | `7590df4c1624e0a885cead3d5d0479b12cd29510` |
| Head commit | `f7f95a2` + the log commit below |
| Started / finished | `2026-09-05 12:55 CEST` / `2026-09-05 13:40 CEST` |
| Status | complete |

## 1. Prompt as received

```
# Task: kb-corpora — knowledge-base records, the two real collections, and the derived-corpus generators

You are agent `kb-corpora` in wave `2026-09-05-tkde-w1` of the IsalHG TKDE experiments. You work in an isolated git worktree on your own branch, in parallel with two peers who own different files. You never see the orchestrator's conversation; everything you need is in this prompt and the repository. Confirm at the start that `git rev-parse --show-toplevel` is NOT `/home/mpascual/research/code/IsalHG` (the main checkout); you must be in a worktree under `.claude/worktrees/`.

## Mission
Turn the probe-era loaders into package code: a frozen `KBRecord`/`KBCollection` data model with JSONL persistence, the WD50K entity-knowledge-base loader (subsets 66 / 100 / all, with roles and Wikidata P31 class labels) and the NDC quarterly co-formulation loader (classes and substances, with constant identities, consecutive-pair `Δ` and the constant-preserving regime flag), plus the seeded generators the experiments need (constant-preserving edit ladders and variant collections, corruptions including the iso-twin, the operating-envelope random grid), and the script that freezes every collection to `results/IEEETKDE/corpora/`. "Working" means the loaders reproduce the census numbers of `docs/article/D_ART3/supplementary_data.md` and every generator is deterministic under its seed and honours its rejection rules.

## Why this exists
Every runner of the article (`DESIGN.md` RQ1–RQ7) reads only the frozen JSONL corpora you produce and calls your generators; the statistics rest on your `Δ`, regime flags and identities. The derivations are already specified and were measured once (`docs/article/D_ART3/foundation/probes_2026-09.md` §5–§7, §9); you port, you do not redesign.

## Read first, in this order
1. `CLAUDE.md` (loaded), `.claude/rules/coding_rules.md`, `docs/engineering/CODE_DESIGN.md` §1–5 (datasets ABC, registry, layering).
2. `docs/article/D_ART3/experiments/DESIGN.md` — G4 (corpora), RQ1 M1/M2 (edit kinds, rejection), RQ3 Corpus A/B (variant collections, natural series), RQ4 corruptions, RQ7 grid; and `CODE_PLAN.md` §0–2 (your contract is §2.4).
3. `docs/article/D_ART3/supplementary_data.md` S1–S4 (the derivations and the census numbers you must reproduce).
4. Reference implementations to port: `scripts/diagnostics/d_art3_probes_2026-09-03/hyperrel/probe_hyperrel.py` (WD50K star KBs, `star_spec`, envelope), `hyperrel/wd50k66_types.py` and `hyperrel/fetch_types.py` (P31 labels), `arb_temporal/arb_temporal_lib.py` (NDC quarterly KBs, consecutive pairs, `Δ`), `f4_topology/f4_corpora.py` (edit kinds, `compact`, rejection rules, ladders), `f4_topology/followup_ndc_regime.py` (the regime split).
5. `src/isalhg/datasets/base.py`, `schemas.py`, `registry.py`, `arb_benson.py`, `synthetic/_random_hg.py`, `synthetic/mixed_arity_erdos_renyi.py`, `synthetic/perturbation_ladder.py`, `core/sparse_hypergraph.py` (edit primitives that exist: `permute`, the degree-preserving incidence swap from T-M4b, connectivity helpers).

## Your ownership (exclusive write access)
Create or modify ONLY:
- `src/isalhg/datasets/kb/**` (new package: `__init__.py`, `base.py`, `io.py`, `wd50k.py`, `ndc_quarterly.py`, `ladders.py`, `corruptions.py`, `envelope_sweep.py`, `synthetic_rq1.py`)
- `src/isalhg/datasets/registry.py` (registration lines only)
- `experiments/tkde/__init__.py` (empty, new) and `experiments/tkde/corpora.py` (new: load a frozen collection → records, hypergraphs, roles maps, identities, labels)
- `scripts/tkde/freeze_corpora.py` (new)
- `tests/unit/datasets/test_kb_records.py`, `test_kb_wd50k.py`, `test_kb_ndc.py`, `test_kb_generators.py`
- `.claude/notes/2026-09-05-tkde-w1/kb-corpora.md` (your work log)
Everything else is read-only — in particular `src/isalhg/core/**`, `src/isalhg/datasets/schemas.py`, `src/isalhg/metric_space/**` (peer `fact-alphabet`), `slurm/**`, `scripts/tkde/*.sh` (peer `picasso-env`).

## Base state
- Base commit: `7590df4` — "docs(tkde): pre-registered experimental design and engineering plan for the TKDE article". Do not rebase, merge or cherry-pick.

## Frozen contracts
```python
# src/isalhg/datasets/kb/base.py
@dataclass(frozen=True)
class KBRecord:
    kb_id: str
    n: int
    types: tuple[int, ...]                                   # per constant, ids in [0, n_types)
    facts: tuple[tuple[int, tuple[int, ...]], ...]           # (pred_id, sorted distinct constant ids), arity >= 2, no duplicate facts
    roles: tuple[tuple[int, ...], ...] | None = None         # per fact, one role id per operand, aligned with the operand tuple; None when the collection has no roles
    constant_ids: tuple[str, ...] | None = None              # external identities — EVALUATION ONLY, never read by a method
    label: str | None = None                                 # class label (RQ5), None otherwise
    meta: Mapping[str, Any] = field(default_factory=dict)    # e.g. {"class_id": ..., "quarter": "2015Q3", "series": ..., "source_id": ...}
    def to_hypergraph(self) -> SparseHypergraph              # n_vertex_labels = collection n_types, n_edge_labels = collection n_preds; edge order = facts order
    def roles_map(self) -> Mapping[int, Mapping[int, int]] | None   # {edge_id: {node_id: role_id}} in to_hypergraph()'s edge order
@dataclass(frozen=True)
class KBCollection:
    name: str; records: tuple[KBRecord, ...]; type_names: tuple[str, ...]; pred_names: tuple[str, ...]; role_names: tuple[str, ...]; k_max: int; meta: Mapping[str, Any]
# io.py: write_jsonl(collection, dir) writes <dir>/records.jsonl (one JSON object per record, keys = the dataclass fields) + <dir>/vocab.json
#        (name, type_names, pred_names, role_names, k_max, meta, n_records) + <dir>/census.json; read_jsonl(dir) -> KBCollection.
# Pairs/series metadata for NDC live in vocab.json["meta"]: consecutive_pairs = [{a: kb_id, b: kb_id, delta: int, constant_preserving: bool}],
#        runs = {class_id: [kb_id ordered by quarter]}.
```
Generators (all seeded, all returning `KBRecord`s with `constant_ids` carried when the source has them, all pure functions of their inputs):
- `ladders.single_edits(record, kind, count, seed, *, require_connected: bool, envelope) -> list[KBRecord]` for `kind ∈ {insert_fact, delete_fact, add_constant, remove_constant, insert_fact_new_constant}` exactly as `f4_corpora.py` defines them; result non-isomorphic to the base (pynauty fingerprint), distinct among themselves; record the regime flag `constant_set_preserved` and the edit description in `meta`.
- `ladders.constant_preserving_ladder(record, t_max, seed) -> list[KBRecord]` (RQ1 M2: `t = 1..t_max` cumulative fact insert/delete walks, constants fixed, `Δ` exact in `meta`).
- `ladders.variant_collection(source, N, t, kind ∈ {ins, del, mix}, seed) -> list[KBRecord] | None` (RQ3 Corpus A rules: constants fixed, isolated constants legal, members pairwise non-isomorphic and non-isomorphic to the source, 50 attempts else None).
- `corruptions.corrupt(record, kind ∈ {spurious_fact, missing_fact, wrong_argument, iso_twin}, budget, seed) -> KBRecord | None` (RQ4 rules; iso-twin = degree-preserving 2-fact swaps until non-isomorphic, same n, m, arity histogram, degree sequence, type multiset, predicate multiset; `meta["wl1_equal"]` flag; every output verified non-isomorphic to the original).
- `envelope_sweep.grid()` and `envelope_sweep.random_kb(m, k, n_edge_labels, n_vertex_labels, density ∈ {"sparse","dense"}, seed) -> KBRecord` (RQ7 grid: connected, `n = ceil(1.5 m)` sparse or `ceil(0.5 m) + k` dense).
- `synthetic_rq1.corpus(n_items=2000, seed) -> KBCollection` (the probe's synthetic corpus: n ∈ [6,16], m ∈ [6,20], arity 2–4, 3 types, 3 predicates, connected, rejection sampling).

## Environment bootstrap (the editable install is path-pinned — you MUST clone the env)
```bash
cd "$(git rev-parse --show-toplevel)"
conda create -y -n isalhg-kbcorp --clone isalhg
~/.conda/envs/isalhg-kbcorp/bin/python -m pip install -e ".[dev]" > /tmp/claude-1000/build-kbcorp.log 2>&1; echo "PIP EXIT: $?"
PY=~/.conda/envs/isalhg-kbcorp/bin/python
$PY -c "import isalhg, isalhg.core._native; print(isalhg.__file__)"   # must print a path INSIDE your worktree
export ISALHG_DATA_ROOT=/media/mpascual/Sandisk2TB/research/ISAL/isalhg/data
export ISALHG_RESULTS_ROOT=/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE
```
Use only `$PY`. Read the data root from `ISALHG_DATA_ROOT` (default to that path); never hard-code it in library code.

## Verification commands
```bash
$PY -m pytest tests/unit/datasets/test_kb_records.py tests/unit/datasets/test_kb_generators.py -q -m unit      # frequently
$PY -m pytest tests/unit/datasets -q -m unit                                                                    # loaders (mark real-data tests so they skip when the data root is absent)
$PY -m pytest tests/unit -q -m unit                                                                             # before the final commit
$PY -m ruff check src/ tests/ experiments/tkde scripts/tkde && $PY -m ruff format --check src/ tests/ experiments/tkde scripts/tkde
$PY -m mypy src/isalhg/
$PY scripts/tkde/freeze_corpora.py --collections wd50k66 wd50k66_full wd50k100 ndc_classes ndc_substances synthetic_rq1 --out "$ISALHG_RESULTS_ROOT/corpora"
```

## Data (read-only)
- WD50K: `$ISALHG_DATA_ROOT/wd50k_66/{train,valid,test}.txt`, `wd50k_100/`, `wd50k/` (statement files: `s, r, o, (q_r, q_v)*` per line); P31 types TSV per `supplementary_data.md` (`$ISALHG_DATA_ROOT/wd50k/types/p31_types.tsv` — locate and verify). Derivation: one KB per subject entity; hyperedge = {subject, object, qualifier values} labelled by the main relation; roles S/O/Q per operand (a constant in two roles takes the smaller role id); qualifier relations dropped; entities with < 3 statements dropped; envelope `3 ≤ m ≤ 110`, `n ≤ 24`, max arity ≤ 10; constants untyped (single type); label = most frequent P31 over the population, ties by identifier order.
- NDC: `$ISALHG_DATA_ROOT/arb_benson/temporal/NDC-classes/` and `NDC-substances/` (`-nverts.txt`, `-simplices.txt`, `-times.txt`, `-node-labels.txt`). Derivation: KB of class `c` in quarter `t` = distinct co-formulation simplices containing `c` marketed in `t`; constant type from the name suffix (`[epc]`, `[moa]`, `[pe]`, untyped) for classes, single type for substances; one predicate; `constant_ids` = node ids; consecutive pairs with `Δ = |F_t △ F_{t+1}|` and the constant-preserving flag; encodable envelope as above.
- Expected census (acceptance, exact where the supplement is exact, ±1 % otherwise): WD50K(66) all entities 4,554; in-envelope ≈ 3,994 (3,167 with an arity-≥3 fact; 14 dropped for arity > 10); 14 classes with ≥ 20 members covering 87.5 %. NDC-classes: 1,432 encodable members, 555 consecutive pairs with `Δ` histogram 85 / 120 / 134 / 191 / 25 over `0 / 1 / 2 / 3–5 / >5`, 140 constant-preserving vs 415 changing, 45 classes with runs ≥ 3 and 20 with ≥ 5. NDC-substances: 2,222 members, 1,106 pairs, 35 one-edit. WD50K(100): ≈ 1,847 in-envelope. Report every number you get beside the expected one in `census.json` and in your log; a mismatch is investigated, not papered over.
- No GPU, no cluster. Writing to `$ISALHG_RESULTS_ROOT/corpora/` is allowed (it is outside the repo).

## Definition of done
1. `KBRecord`/`KBCollection` + JSONL round-trip (write → read → equal) tested, including roles, identities, labels, meta.
2. Loaders reproduce the census above; `census.json` written per collection with expected vs obtained.
3. All generators deterministic under seed (same inputs → identical output), honour their rejection rules (tested: connectivity when required, non-isomorphism via pynauty fingerprint, constant set preserved, budgets), and carry `constant_ids` and `meta` as specified. Iso-twin invariants tested (n, m, arity histogram, degree sequence, type and predicate multisets equal; non-isomorphic).
4. `experiments/tkde/corpora.py` exposes `load_collection(name, root) -> KBCollection` and helpers to get hypergraphs, roles maps, identities and labels in member order.
5. Frozen corpora written to `$ISALHG_RESULTS_ROOT/corpora/<name>/{records.jsonl,vocab.json,census.json}` for the six collections; sizes and wall-clock recorded in the log.
6. Real-data verification in the log: a printed sample of 3 records per collection (with human-readable names from the vocab), the arity histogram, the size quantiles vs `supplementary_data.md`.
7. Existing suite green; ruff and mypy clean; everything committed; log committed.

## Explicitly out of scope
- The fact-token encoder/decoder, canonical ranks, distances (peer `fact-alphabet`) — do not import them; use the pynauty fingerprint for isomorphism checks.
- Distance matrices, statistics, runners, SLURM (later waves / peer `picasso-env`).
- Fetching anything from the network (all data is on disk; if the P31 TSV is missing, message `main`).

## Work log — mandatory
Maintain `.claude/notes/2026-09-05-tkde-w1/kb-corpora.md` in your worktree from your first action, using **exactly** the template at `/home/mpascual/.claude/skills/parallel-agents/assets/note-template.md` (read it, copy its skeleton verbatim, fill every section, paste this prompt verbatim in §1). Commit it last with message `docs(notes): kb-corpora work log`. Standing obligations: work only inside your worktree and ownership set; commit everything before finishing; never `git push`, never touch a peer's branch; you cannot ask the user — on ambiguity message `main`, record the assumption, keep working; never change a frozen contract yourself; report failure honestly.

## Peers in this wave
- `main` — the orchestrator.
- `fact-alphabet` — the fact-token encoder, total decoder, canonical ranks (`iso_backends/canonical_order.py`), distances `fact_rank` and the ablation arms, `LabelVocabulary.fit`. Owns `src/isalhg/core/fact_word.py`, `src/isalhg/iso_backends/canonical_order.py`, `src/isalhg/metric_space/distances/fact_*.py`, `src/isalhg/datasets/schemas.py`. It consumes `SparseHypergraph` + `RolesMap = Mapping[EdgeId, Mapping[NodeId, RoleId]]` — your `roles_map()` must produce exactly that shape.
- `picasso-env` — HPC environment. Owns `slurm/tkde/**`, `scripts/tkde/{sync_to_picasso,harvest_from_picasso,picasso_env_setup}.sh`, `docs/article/D_ART3/experiments/PICASSO.md`. Its sync script will push your frozen `corpora/` directory to Picasso; keep the directory self-contained.

## Final message format (≤ 15 lines)
- STATUS / BRANCH / WORKTREE / HEAD / LOG
- TESTS: pass/fail counts and the exact commands
- CENSUS: the obtained numbers for wd50k66 and ndc_classes beside the expected ones
- Three bullets: what you built; anything the orchestrator must know; anything unfinished.
```

## 2. Understanding and plan

**Restatement of the task in my own words:** Promote the 2026-09-03 probe scripts into installable package code — a frozen `KBRecord`/`KBCollection` value type with JSONL persistence, two real loaders (WD50K entity star knowledge bases with roles and P31 labels; NDC quarterly co-formulation series with exact `Δ` and the constant-preserving regime flag), and five seeded generators (single edits, constant-preserving ladders, RQ3 variant collections, RQ4 corruptions including the iso-twin, the RQ7 envelope grid, the synthetic RQ1 corpus) — then freeze the six collections to the results drive with an expected-vs-obtained census. Port, do not redesign.

**Approach chosen:** One package `isalhg.datasets.kb` with `base.py` as the single home of the value types, the envelope and the structural helpers (`is_connected`, `compact`, `make_record`, `iso_fingerprint`), and one module per concern beside it. The loaders are re-implementations in stdlib Python of the probes' derivations (no numpy dependency, no import of the diagnostic scripts, which are not installable). Rejection oracles use `PynautyLeviBackend.fingerprint` imported inside function bodies. `experiments/tkde/corpora.py` is a thin read layer over the frozen directory so every runner has exactly one input.

**Alternatives considered and rejected:**
- Importing `arb_temporal_lib.py` from `scripts/diagnostics/` — rejected: the diagnostics tree is not on the package path, is numpy-heavy, and hard-codes the data root; the grouping is fifty lines of stdlib.
- Adding `n_types` / `n_preds` as `KBRecord` fields so `to_hypergraph()` can size the vocabularies — rejected: that changes the frozen contract. They are stamped into `meta` by `KBCollection.__post_init__` and read back by `to_hypergraph()`, which also accepts keyword overrides.
- Keeping the record's fact order as given — rejected: `__post_init__` sorts facts by `(predicate, operands)` and permutes the roles rows with them, so two records built from the same statements in different orders compare equal and the edge order is deterministic.
- Registering one dataset name per collection — rejected: the collections are data, not generators. One registry entry, `kb_collection`, takes a frozen directory.

**Plan as executed:**
1. Read `DESIGN.md`, `CODE_PLAN.md` §2.4, `supplementary_data.md` S1–S4 and the four probe reference implementations.
2. `base.py` + `io.py`, tested by `test_kb_records.py` (24 tests) before any loader existed.
3. `wd50k.py`, measured against S1; `ndc_quarterly.py`, measured against S2.
4. `ladders.py`, `corruptions.py`, `envelope_sweep.py`, `synthetic_rq1.py`, tested by `test_kb_generators.py` (51 tests).
5. `experiments/tkde/corpora.py`, `scripts/tkde/freeze_corpora.py` with the expected-vs-obtained audit.
6. Froze the six collections, ran the real-data verification, the full unit suite, ruff and mypy.

**Deviations from the plan:** Two, both forced by the data, both reported to `main` (§7), and both **ruled on by the orchestrator** mid-task (§8):
- The probes counted arity-1 "facts" (singleton drug products, WD50K self-statements). `KBRecord` and DESIGN G2 require arity ≥ 2, so those are dropped; the NDC census shifts and the loader records the probe-equivalent count that reproduces the published number exactly. **Ruling: arity ≥ 2 stays**; the encodable NDC collections are 1,381 / 528 and 1,745 / 885, and the Δ histogram, regime split and run counts are to be recorded in `census.json` for RQ3 sizing.
- Every *sparse* `k = 2` cell of the RQ7 grid was structurally impossible (a connected KB of `m` facts of arity ≤ `k` spans at most `m(k-1)+1` constants; sparse asked for `⌈1.5m⌉`). **Ruling: the sparse rule changes** to `n = min(⌈1.5m⌉, m(k-1)+1)`, so every cell is feasible and the `k = 2` sparse cells are trees (`n = m + 1`). Applied; the feasibility flag and the `KBGenerationError` path are retained for hand-built cells.

**Post-ruling changes (step 7 of the plan):**
7. Applied the new sparse rule (`constants_for`, new `max_constants`, docstrings); added `KBCollection.series_census()` so the RQ3 sizing numbers sit in an explicit `census["series"]` block; added tests for both; re-froze the six collections; re-ran the full suite.

## 3. Changes made

**Created**
| Path | Purpose |
|---|---|
| `src/isalhg/datasets/kb/__init__.py` | Package docstring, layering note, re-exports. |
| `src/isalhg/datasets/kb/base.py` | `KBRecord`, `KBCollection`, `Envelope`, exception hierarchy, `is_connected` / `compact` / `make_record` / `iso_fingerprint`, census + quantile helpers. |
| `src/isalhg/datasets/kb/io.py` | `write_jsonl` / `read_jsonl` / `read_census`, `KBCollectionDataset` + `kb_collection` registry factory. |
| `src/isalhg/datasets/kb/wd50k.py` | WD50K statement parser, star-KB derivation with S/O/Q roles, P31 label policy, envelope filter, `data_root()`. |
| `src/isalhg/datasets/kb/ndc_quarterly.py` | ARB temporal reader, canonical-simplex dedup, windowing, class-type suffix, consecutive pairs with `Δ` + regime flag, runs, quarter labels. |
| `src/isalhg/datasets/kb/ladders.py` | `single_edits`, `constant_preserving_ladder`, `variant_collection`, `fact_distance`. |
| `src/isalhg/datasets/kb/corruptions.py` | `corrupt` (4 kinds), `wl1_histogram`, the degree-preserving swap. |
| `src/isalhg/datasets/kb/envelope_sweep.py` | `grid`, `constants_for` (capped sparse rule), `max_constants`, `is_feasible`, `random_kb`. |
| `src/isalhg/datasets/kb/synthetic_rq1.py` | `corpus`, `sample_record`. |
| `experiments/tkde/__init__.py` | Package marker. |
| `experiments/tkde/corpora.py` | `load_collection` + member-order helpers (`hypergraphs`, `roles_maps`, `identities`, `labels`, `consecutive_pairs`, `runs`, `consecutive_runs`, `subset`). |
| `scripts/tkde/freeze_corpora.py` | Derive → audit → write the six collections; `MANIFEST.json`. |
| `tests/unit/datasets/test_kb_records.py` | 24 tests: contract, bridges, helpers, envelope, collection, JSONL round-trip, registry. |
| `tests/unit/datasets/test_kb_generators.py` | 51 tests: determinism, rejection rules, iso-twin invariants, grid feasibility, synthetic corpus. |
| `tests/unit/datasets/test_kb_wd50k.py` | 14 tests: parser, roles, label policy, real census (skips without the data root). |
| `tests/unit/datasets/test_kb_ndc.py` | 12 tests: windowing, quarter labels, real census (skips without the data root). |
| `.claude/notes/2026-09-05-tkde-w1/kb-corpora.md` | This log. |

**Modified**
| Path | Change | Reason |
|---|---|---|
| `src/isalhg/datasets/registry.py` | One `_LAZY_MODULES` line: `"kb_collection": "isalhg.datasets.kb.io"` | Registration line only, as owned. |

**Removed** — none.

**Commits**
| SHA | Message |
|---|---|
| `f7f95a2` | `feat(datasets): knowledge-base records, real loaders and seeded generators` |
| (final) | `docs(notes): kb-corpora work log` |

## 4. Tests

**Tests created or extended**
| Test | File | What it verifies | Why it matters |
|---|---|---|---|
| `TestStructure` (8) | `test_kb_records.py` | Facts sorted with their roles; arity, degree, connectivity; six malformed shapes rejected | A silently reordered roles row would mis-address every operand for the fact-word encoder. |
| `TestBridges` (3) | `test_kb_records.py` | `to_hypergraph` edge order and vocabulary sizes; `roles_map` shape `{edge_id: {node_id: role_id}}` | This is the exact interface peer `fact-alphabet` consumes. |
| `TestRoundTrip` (3) | `test_kb_records.py` | write → read → `==`, every field preserved, registry dataset yields hypergraphs | The frozen directory is the only runner input; a lossy round-trip would be invisible until analysis. |
| `TestSingleEdits` (17) | `test_kb_generators.py` | Determinism per kind; distinct, connected, non-isomorphic results; regime flag; identity extension; upper walls | RQ1 M1's rejection rules are the measurement. |
| `TestLadder` (3) | `test_kb_generators.py` | Determinism; `meta["delta"] == fact_distance(base, rung)`; `delta <= t` | RQ1 M2's ground truth is the recorded `Δ`. |
| `TestVariantCollection` (7) | `test_kb_generators.py` | Determinism; constants fixed; pairwise non-isomorphic; `ins` grows / `del` shrinks by exactly `t`; impossible cell → `None` | RQ3's H3a is scored against the source; a leaked isomorphic member would inflate recovery. |
| `TestCorruptions` (14) | `test_kb_generators.py` | Determinism; non-isomorphy verified; budgets move `m` correctly; iso-twin preserves `n`, `m`, arity histogram, degree sequence, type and predicate multisets; `wl1_histogram` permutation-invariant | RQ4's H4a is precisely the claim that the twin is invisible to coarse statistics. |
| `TestEnvelopeSweep` (21) | `test_kb_generators.py` | Grid shape 288 + 6; **every cell feasible**; **sparse `k=2` cells are trees (`n = m + 1`)**; every `m = 10` cell actually realises; `random_kb` matches its cell and is deterministic; the infeasibility guard still fires under monkeypatch; unknown density raises | A silently-dropped or unrealisable cell would make the RQ7 frontier look better than it is. |
| `TestSyntheticRQ1` (1) | `test_kb_generators.py` | Determinism and range compliance | RQ1's third corpus. |
| `TestRealCensus` (6) | `test_kb_wd50k.py` | 4,554 entities; 3,988 + 6 = 3,994; 14 over the arity cap; medians 8 / 5; 0.547 arity-≥3 facts; 14 label classes at 87.6 %; roles well-formed on 200 members | The acceptance criterion. |
| `TestRealClasses` / `TestRealSubstances` (8) | `test_kb_ndc.py` | 49,724 simplices; probe-equivalent encodable 1,432 / 2,222; 528 pairs; `Δ` histogram; 128/400 regime split; runs; FDA suffix types; **`census["series"]` carries the RQ3 sizing numbers** | The acceptance criterion, and the block RQ3 configs are sized from. |

**Coverage of the behaviour that matters:** every generator's determinism and every rejection rule; the record contract in both directions (construction and JSONL); both loaders against the published census, on the real files. Deliberately not covered: the C++ canonicalization path (not mine), the fact-word encoder (peer's), and wall-clock behaviour of the loaders beyond the timings in §6.

**Not tested, and why:**
- `load_wd50k("all")` and `load_wd50k("33")` are reachable but not exercised; the supplement publishes no census for them and `wd50k_all` is not in the frozen six.
- `random_kb` is not exercised at `m = 1280` in the unit suite (it is ~1 s per instance); the largest tested cell is `m = 40`.
- `quarter_label` is pinned on one synthetic instant and on the real corpus range (1899Q1–2016Q3); it is not validated against an authoritative NDC date table, because none is on disk.
- `KBCollectionDataset.metadata` is exercised only through the round-trip test.

## 5. Test results

**Command:** `~/.conda/envs/isalhg-kbcorp/bin/python -m pytest tests/unit -q -m unit`

```
=========== 1461 passed, 6 skipped, 20 warnings in 284.00s (0:04:44) ===========
```

Owned files only (final, after the orchestrator's rulings):

```
$ ISALHG_DATA_ROOT=<drive> $PY -m pytest tests/unit/datasets/test_kb_records.py \
      tests/unit/datasets/test_kb_generators.py tests/unit/datasets/test_kb_wd50k.py \
      tests/unit/datasets/test_kb_ndc.py -q -m unit
108 passed in 1.56s

$ ISALHG_DATA_ROOT=/nonexistent/data $PY -m pytest tests/unit/datasets/test_kb_wd50k.py tests/unit/datasets/test_kb_ndc.py -q -m unit
13 passed, 13 skipped in 0.08s
```

Before the rulings the same four files were 24 + 51 + 14 + 12 = 101 green; the
seven added tests cover the new sparse rule and the series census.

**Result:** 1461 passed, 0 failed, 6 skipped · **Duration:** 284 s · **Run at:** the tree that became the `feat` commit.

**Lint and types**

```
$ $PY -m ruff check src/isalhg/datasets/kb tests/unit/datasets/test_kb_*.py experiments/tkde scripts/tkde src/isalhg/datasets/registry.py
All checks passed!
$ $PY -m ruff format --check src/isalhg/datasets/kb experiments/tkde scripts/tkde tests/unit/datasets
37 files already formatted
$ $PY -m mypy src/isalhg/    # 0 errors in datasets/kb
Found 20 errors in 6 files (checked 122 source files)
```

`ruff check src/ tests/` reports 3 errors and `mypy src/isalhg/` reports 20, **all pre-existing on the base commit and all in files I do not own** (`iso_backends/isalhg_backend.py`, `viz/instruction_view.py`, `core/{structural_tuples,hypergraph_wl,hypergraph_to_string,canonical}.py`, `core/_core.pyi`, `tests/unit/core/algorithms/test_registry.py`). Zero come from my files; I fixed the two mypy errors my first draft introduced (`KBCollection.__iter__` annotation, `read_census` return type).

**Failures and their resolution:** Two during development, both fixed before the suite run.
1. `load_ndc` crashed on `zip(windows, windows[1:], strict=True)` — the sequences differ in length by one. Fixed to `zip(windows[:-1], windows[1:], strict=True)`.
2. `make_record` rejected every NDC member containing a singleton product (and 13 WD50K entities with self-statements), because an arity-1 hyperedge is not a fact. Resolved by filtering arity-1 simplices/statements *before* the envelope test and recording both the resulting count and the probe-equivalent count. See §7.

## 6. Verification beyond unit tests

| Circumstance | What was run | Evidence | Outcome |
|---|---|---|---|
| Real data — freeze | `python scripts/tkde/freeze_corpora.py --collections wd50k66 wd50k66_full wd50k100 ndc_classes ndc_substances synthetic_rq1 --out $ISALHG_RESULTS_ROOT/corpora` | 6 collections, 1.63 s wall-clock total; wd50k66 3,988 rec / 1.60 MB / 0.28 s; wd50k66_full 4,554 / 2.55 MB / 0.37 s; wd50k100 1,837 / 0.85 MB / 0.16 s; ndc_classes 1,381 / 0.85 MB / 0.14 s; ndc_substances 1,745 / 1.29 MB / 0.29 s; synthetic_rq1 2,000 / 0.65 MB / 0.17 s. Total 7.78 MB. | pass — **0 unexplained** audited quantities across all six |
| Real data — census reconciliation | `census.json` audit blocks | wd50k66: 4,554 entities **exact**, 14 over arity cap **exact**, `3988 + 6 (m<3) = 3994` **exact**, median n = 8 / m = 5 **exact**, 0.5473 vs 0.547 arity-≥3, 14 classes ≥ 20 covering 87.56 % vs 87.5 %, Q5 = 1,830 and Q11424 = 1,092 **exact**. wd50k66_full reproduces S1's whole-population census **exactly**: 42,459 facts (= 42,472 − 13 self-statements), arity histogram 12,488 / 19,375 / 9,085 / 859 / 303 / 252 / 26 / 11 / 60-at-≥10, 70.59 % arity ≥ 3, n quantiles 3/6/9/15/27/377, m 2/3/5/9/18/303, max-arity 2/3/3/4/5/67. ndc_classes: 49,724 simplices **exact**, probe-equivalent encodable **1,432 exact**, obtained 1,381. ndc_substances: probe-equivalent **2,222 exact**, obtained 1,745. | pass |
| Real data — 3 samples per collection with human-readable names | scratchpad `verify_frozen.py` through `experiments.tkde.corpora` | wd50k66 `Q100` n=7 m=6 k=3 label=Q1549591, `P1376(Q100, Q771)` roles `[S, O]`; `Q1000` n=21 m=12 `P1552(Q1000, Q1417780, Q47185282)` roles `[S, Q, O]`; `Q1001` n=10 m=6 k=4 `P20(Q1001, Q1353, Q1381516, Q1775277)` roles `[S, Q, O, Q]`. ndc_classes `3@401` 1999Q2 "antiarrhythmic [epc]" n=11 m=3 k=6; `3@437` 2008Q2 n=9 m=3 k=4; `3@440` 2008Q4 n=13 m=3 k=10, facts printed with FDA class names. First pair `{a: 3@443, b: 3@444, delta: 4, constant_preserving: False, n_constants_moved: 15}`. | pass |
| Real data — helper surface | same script | `hypergraphs` → `[(7,6),(21,12),(10,6),(6,5),(7,4)]`; `roles_maps(c)[0]` → `{0: {0: 0, 6: 1}}`; `identities(c)[0][:3]` → `('Q100','Q2079909','Q21518270')`; `labels(c)[:3]` → `['Q1549591','Q3624078','Q5']`; `available_collections()` lists all six | pass |
| Edge cases | unit suite | `n_max` and `m_max` walls; `t_max = 0`; a 2-constant record refusing a `del` variant collection; over-budget deletion refused; unknown kind / subset / window / density all raise typed errors | pass |
| Failure paths | unit suite + development | infeasible RQ7 cell raises `KBGenerationError`; missing P31 table raises `KBCorpusError`; missing split file raises `KBCorpusError`; `vocab.json`/`records.jsonl` count mismatch raises `KBCollectionError` | pass |
| Scale / performance | freeze run, this workstation | Largest input NDC-substances: 112,405 simplices → 9,906 canonical → 46,038 groups → 1,745 records in 0.29 s, pure Python. WD50K(66): 49,167 statements → 4,554 stars in 0.28 s. Whole freeze 1.63 s. | pass |
| Environment | Debian 12, Python 3.11.15, conda env `isalhg-kbcorp` (clone of `isalhg` + `pip install -e ".[dev]"` in this worktree); `import isalhg` resolves to `<worktree>/src/isalhg/__init__.py` and `isalhg.core._native` imports; pytest 9.0.3, hypothesis 6.155.2 | | pass |

## 7. Decisions, assumptions, open questions

**Decisions with a real trade-off:**

1. **Arity-1 "facts" are dropped before the envelope test.** `KBRecord` and DESIGN G2 both require arity ≥ 2, but the probes counted singleton drug products and WD50K self-statements as facts. Dropping them costs exact agreement with the published NDC counts (1,381 vs 1,432 members; 528 vs 555 pairs; 1,745 vs 2,222 substances members) and buys a collection every member of which is encodable in the adopted alphabet. To keep the deviation auditable, the loader records `n_encodable_counting_singleton_products`, which reproduces **1,432** and **2,222 exactly** — so the grouping is verified correct and only the fact definition differs. Every downstream count shifts consistently (`Δ` histogram 77/117/129/180/25 vs 85/120/134/191/25; regimes 128/400 vs 140/415; runs ≥3 42 vs 45, ≥5 19 vs 20).
2. **The `m ≥ 3` floor of DESIGN G4 is applied to WD50K.** S1's 3,994 applied no fact floor. With the floor, wd50k66 = 3,988 and `3988 + n_dropped_below_m_min(6) = 3994`; wd50k100 = 1,837 and `1837 + 10 = 1847`. I followed the frozen DESIGN envelope over the supplement's prose. Reversible in one line if `main` prefers the published count.
3. **`m_min` is *not* applied to edit results.** `single_edits` and the ladders enforce `n_max`, `m_max`, `k_max` and `m ≥ 1`, but not `m_min`. The median ndc_classes member holds exactly 3 facts; enforcing `m_min` on results would make `delete_fact` impossible there and would not reproduce the probe the RQ1 gate is measured against (`f4_corpora.apply_edit` only required `m > 1`). Documented in the module docstring. `insert_fact_new_constant` may reach `max(n_max, n + 1)` for the same reason.
4. **Non-isomorphy to the base is enforced on single edits**, which the probe's `sample_edits` did not do (it deduplicated structurally only). DESIGN M1 states the rule explicitly, so I followed the design over the probe. It costs a pynauty call per candidate.
5. **`n_types` / `n_preds` travel in `meta`**, stamped by `KBCollection.__post_init__`, rather than becoming record fields. Keeps the frozen contract intact; the cost is that a record built outside a collection must carry them itself (every generator does, copying from its source).
6. **Facts are sorted canonically in `__post_init__`**, with the roles rows permuted alongside. Makes records order-insensitive and the edge order deterministic; the cost is that a caller cannot choose a fact order.

**Assumptions I proceeded on (all messaged to `main`):**
- Role ids are `S = 0, O = 1, Q = 2`, so "a constant in two roles takes the smaller role id" means subject wins. If the intended order were lexicographic over the names, `O` would win — breaks nothing structurally but changes the roles arm's words.
- NDC timestamps are milliseconds since 0000-01-01 proleptic Gregorian; `quarter_label` inverts that. The corpus maps to 1899Q1–2016Q3, which is right for FDA first-marketing dates. If the epoch convention were different, only the human-readable `meta["quarter"]` is wrong — `meta["window"]` is the authoritative index and no computation reads the label.
- The frozen `corpora/` directory must be self-contained for `picasso-env`'s sync, so the NDC node-name table is embedded in `vocab.json` (142 KB for substances).

**Open questions for the orchestrator:**
- ~~RQ7's 36 sparse `k = 2` cells are structurally impossible.~~ **Resolved** by `main`: the sparse rule is now `n = min(⌈1.5m⌉, m(k−1)+1)` and every cell is feasible; the `k = 2` sparse cells are trees.
- `supplementary_data.md` S2 has two counts swapped, measured: NDC-classes is 1,161 nodes / 1,088 distinct products (not "1,088 classes"), NDC-substances is 5,311 nodes / 9,906 distinct products (not "9,906 substances, 5,311 products"). **Acknowledged by `main`** for the prose fold; I did not touch the file.
- `frac_facts_arity_ge3` for NDC is not comparable to S2's 66.9 % / 48.7 %: those are over the *in-envelope* class-quarters (22,892 of them), mine over the 1,381 *encodable* members. I removed it from the audit rather than record a false mismatch.

## 8. Coordination

**Messages sent:** one to `main`, covering (i) the arity-≥2 rule and the exact reconciliation numbers, (ii) the `m ≥ 3` floor decision, (iii) the infeasible RQ7 sparse `k = 2` cells, (iv) the two swapped counts in S2, and (v) the `roles_map()` shape and role-id order for peer `fact-alphabet`.

**Messages received and how they changed the work:** one from `main`, ruling on all four points.
1. *Arity ≥ 2 stays* — accepted as built; additionally record the Δ histogram, the constant-preserving/changing split and the runs ≥ 3 / ≥ 5 in `census.json`, because RQ3 configs are sized from them. **Done**: `KBCollection.series_census()` emits an explicit `census["series"]` block (`n_consecutive_pairs`, `delta_histogram`, both regime counts, `n_classes_run_ge3/ge5`, `n_runs_ge3/ge5`, `max_run`, `n_classes_with_any_member`), pinned by `test_series_census_carries_the_rq3_sizing_numbers` and by a synthetic case in `test_kb_records.py`. `supplementary_data.md` not touched (`main` will correct it).
2. *The `m ≥ 3` floor stays* (3,988 / 1,837) — no change.
3. *The RQ7 sparse rule changes* to `n = min(⌈1.5m⌉, m(k−1)+1)`, dense unchanged. **Done**: `constants_for` capped, `max_constants` added, docstrings updated, feasibility flag and `KBGenerationError` path retained. New tests: every grid cell feasible; the `k = 2` sparse cells are trees (`n = m + 1`); every `m = 10` cell actually realises through `random_kb`; the guard still fires under monkeypatch. `main` is amending DESIGN.md RQ7 to match.
4. *The swapped S2 counts* — noted for the prose fold, not my scope.
`main` also confirmed the `roles_map()` contract matches what `fact-alphabet` built (edge id = index in `to_hypergraph()` edge order; `S=0, O=1, Q=2`; smaller id on conflict).

**Contracts I depend on and confirmed unchanged:** `SparseHypergraph.__init__` (edge order preserved, `n_vertex_labels`/`n_edge_labels`/`vertex_labels`/`edge_labels`); `PynautyLeviBackend.fingerprint(H) -> bytes`; `HypergraphDataset` ABC; `DatasetItem` / `DatasetMetadata` / `LabelVocabulary(vertex_symbols, edge_symbols)` in `datasets/schemas.py` (peer `fact-alphabet` owns that file — I only read it; `LabelVocabulary.fit` is already implemented there, contrary to the note in `CODE_DESIGN.md` §2.2); `register_dataset` / `_LAZY_MODULES` in `datasets/registry.py`.

## 9. Deliberately not done

- The fact-token encoder, canonical ranks and any distance — peer `fact-alphabet`. Isomorphism checks use the pynauty fingerprint only.
- Distance matrices, statistics, runners, SLURM — later waves.
- `envelope_sweep` produces no frozen collection: the RQ7 sweep is generated per seed by its runner, and `grid()` + `random_kb` are the contract for that. Freezing 7,776 random instances to disk was not asked for.
- No network access; the P31 table was found on disk at `$ISALHG_DATA_ROOT/wd50k/types/p31_types.tsv` (204 KB) and only read.
- No documentation edits outside this log (`supplementary_data.md`'s two swapped counts are reported, not corrected — the file is not mine).
- The three pre-existing `ruff` errors and twenty pre-existing `mypy` errors in files I do not own were left alone.

## 10. Risks and follow-ups

| Item | Severity | Detail | Suggested owner |
|---|---|---|---|
| NDC census differs from the supplement by the arity-≥2 rule | medium | 1,381 vs 1,432 members and 528 vs 555 pairs. RQ3 Corpus B has fewer natural runs (42 classes at ≥3, 19 at ≥5) than the design assumed (45 / 20). The supplement's S2 prose and DESIGN G4's table should be updated to the encodable-with-arity-≥2 numbers. | orchestrator |
| RQ7 sparse `k = 2` cells are now trees | low (was medium) | Resolved by `main`'s ruling: the sparse target is capped at `m(k−1)+1`, so all 288 + 6 cells are feasible and `k = 2` sparse means `n = m + 1`. The paper must describe the sparse rule as the capped one; DESIGN.md RQ7 is being amended by `main`. | `rq-1-2-7` |
| `m_min` not enforced on edit results | low | Deliberate and documented, but it is a rejection-rule choice the RQ1 gate depends on. If the probe's 0.188 / 0.211 / 0.300 medians are not reproduced, this is the first thing to check. | `rq-1-2-7` |
| Role-id order assumption | low | `S < O < Q`. Only affects the `fact_rank_roles` ablation arm. | `fact-alphabet` |
| `quarter` label derivation | low | Human-readable only; nothing computes on it. | — |
| NDC `runs` helper naming | low | `consecutive_runs(c, 3)` counts *runs* (107) while `meta["n_classes_run_ge3"]` counts *classes* (42). Both are correct and documented; a careless reader could conflate them. | `rq-3-6` |

## 11. Self-assessment against the definition of done

| # | Criterion | Met | Evidence |
|---|---|---|---|
| 1 | `KBRecord`/`KBCollection` + JSONL round-trip tested, including roles, identities, labels, meta | yes | `TestRoundTrip::test_write_then_read_is_equal`, `::test_round_trip_preserves_every_field` (24 tests green) |
| 2 | Loaders reproduce the census; `census.json` with expected vs obtained | yes, with two documented deviations | `census.json` `audit` block per collection: 0 unexplained across all six; wd50k66_full reproduces S1's population census exactly; NDC's probe-equivalent counts are 1,432 / 2,222 exactly |
| 3 | Generators deterministic, rejection rules honoured, identities and meta carried; iso-twin invariants tested | yes | `test_kb_generators.py`, 51 tests |
| 4 | `experiments/tkde/corpora.py` exposes `load_collection` + helpers in member order | yes | module + scratchpad verification run in §6 |
| 5 | Six collections frozen with sizes and wall-clock recorded | yes | §6 row 1; `MANIFEST.json` beside the collections |
| 6 | Real-data verification: 3 samples per collection with readable names, arity histogram, size quantiles | yes | §6 rows 2–4 |
| 7 | Suite green; ruff and mypy clean; everything committed | yes | 1454 passed / 6 skipped; ruff and mypy clean on owned files, pre-existing findings elsewhere named in §5 |

**Overall:** I am confident in the record contract, the JSONL round-trip, the generators' determinism and rejection rules, and the WD50K derivation — the full-population census of S1 is reproduced to the unit, including the arity histogram and every size quantile, which is a strong check that the star-KB derivation matches the probe's. I am confident the NDC grouping is right for the same reason: the probe-equivalent encodable counts are 1,432 and 2,222 exactly. Both points I flagged were ruled on mid-task and both rulings are implemented and tested: arity ≥ 2 stands (with the RQ3 sizing numbers now explicit in `census["series"]`), and the RQ7 sparse rule is capped so every cell is realisable.

What the orchestrator should scrutinise first is the **downstream consequence of the arity-≥2 rule for RQ3 Corpus B**: the natural NDC series now offers 42 classes with a run ≥ 3 and 19 with ≥ 5 (design assumed 45 / 20), and only 128 of 528 pairs are constant-preserving. Second, the **`m_min`-not-enforced-on-edits** choice in `ladders.py` (§7 decision 3) is the rejection rule the RQ1 probe-reproduction gate depends on; if the 0.188 / 0.211 / 0.300 medians do not come back, check that first. What I have *not* exercised is `random_kb` at the extension sizes (`m = 1280`) and any interaction with the fact-word encoder, which did not exist in my worktree.
