# T-M4b handoff — the corpus does not measure what the article claims

**Written:** 2026-08-09.
**Audience:** the agent executing T-M4b (the corpus redesign).
**Status of this doc:** point-in-time brief. The ledger
(`README.md`, `T-M4/OPEN/T-M4b.md`) is the authority; where they disagree, the
ledger wins.

---

## 0. Read this first, then start with the skill

Start with **`/task-reader T-M4b`**. It puts you in plan mode, resolves the
task file, and forces you to read its cited context before touching anything.
If the work decomposes into independently verifiable pieces (generator ·
feasibility sweep · re-measurement · doc propagation), escalate to
**`/task-orchestrator`** and run them as isolated workers — but only after the
corpus design decision is made, because that decision is the task and must not
be delegated.

The task file is `docs/article/DEVELOPMENT/T-M4/OPEN/T-M4b.md`. This brief adds
the working context around it: how the finding was reached, how to work, and
what the guardrails are.

## 1. The mission in one paragraph

The article's primary corpus — 17 known-design families × 5 members = 85 items
— is size-heterogeneous to the point that family identity is nearly a lookup on
two integers. A distance built from `|Δn| + |Δm|`, carrying no structural
information at all, scores **A2 ARI 0.442 ± 0.040** and **A3 AUC-OvR
0.932 ± 0.008** on that corpus, outranking five of the seven measured
representations on the first metric and four of seven on the second (IsalHG:
0.274 / 0.915). The applications therefore do not compare representations; they
compare how directly each representation encodes size. **Your job is to design,
validate and adopt a corpus that measures higher-order structure, then
re-measure the body on it, and to leave behind a documented corpus policy so
this cannot recur.** You are authorised to supersede prior results.

## 2. How the finding was reached — reproduce it before anything else

Do not take the above on faith. The first thing you run is the reproduction:

```bash
cd /home/mpascual/research/code/IsalHG
PYTHONPATH=. ~/.conda/envs/isalhg/bin/python scripts/diagnostics/size_confound_probe.py
```

~6 min on 5 seeds. Its recorded output is
`scripts/diagnostics/size_confound.log`. If your run disagrees with that log,
**stop and report** — the finding itself is then in question and everything
downstream changes.

Three independent measurements corroborate the mechanism; confirm you
understand each before designing a replacement:

| measurement | value | where |
|---|---|---|
| `d_I` vs canonical-length gap | Spearman 0.867 | `theoretical/geometry.md` §5 |
| MDS PC1 vs `|w*_c|` / vs `m` / vs `n` | 0.960 / 0.956 / 0.462 | `theoretical/geometry.md` §4 |
| `d_I` vs degree-seq L1 · NetLSD vs degree-seq L1 | 0.799 · 0.707 | probe log |
| distinct `(n,m)` cells for 17 families | **14** | probe log |

The corpus spans `n ∈ [5,15]`, `m ∈ [3,15]`, incidence mass CV 0.499, `|w*_c|`
CV 0.561. Note carefully: neither size axis *alone* does the damage (incidence
mass alone gives ARI 0.101, edge count alone 0.111) — it is the **pair** that
resolves the families. Any replacement must therefore control the pair, not one
axis.

## 3. Local-first — this is a hard rule, not a preference

**Anything that runs in under 15 minutes runs on this workstation, and it runs
before any cluster job is written.** Picasso queues cost days; a mistake
discovered on the cluster costs a week. The discipline:

1. Write the smallest version that exercises the code path end to end. Run it
   locally.
2. Scale it to the largest instance that still finishes in 15 minutes. Run it
   locally. Record the wall-clock.
3. Extrapolate the cost curve from those points and *write the extrapolation
   down* before submitting anything.
4. Only then use `/picasso-sbatch` for a long single-job run, and only for work
   whose local wall-clock is measured, not guessed.

Environment: conda env `isalhg`, interpreter
`~/.conda/envs/isalhg/bin/python`, `PYTHONPATH=.` for anything importing
`experiments`. If you work in a git worktree, clone the env
(`conda create -y -n isalhg-T-M4b --clone isalhg`, then `pip install -e ".[dev]"`
inside the worktree) — the editable install is path-pinned to the main
checkout and will silently import the wrong tree otherwise.

Tests, lint and types before any merge: `python -m pytest tests/ -v`,
`ruff check src/ tests/`, `mypy src/isalhg/`. Standing pre-existing baselines
are ruff 3 / mypy 21 — match them, do not fix them as a side quest.

## 4. The pivotal measurement, and why it is pivotal

The ideal replacement corpus already exists in the tree: the **80 non-isomorphic
STS(15)** in `src/isalhg/datasets/synthetic/sts_catalog.py`. Every one has
`n = 15`, `m = 35`, arity 3, and is 3-regular — so `|Δn| + |Δm|` and the
degree-sequence distance are **identically zero on every pair**, both naive
baselines score ARI 0 by construction, and only a complete invariant can
separate the classes. That converts the article's weakest table into its
strongest.

Whether `w*_c` reaches order 15 is the open question and the first thing to
settle. Measured so far on this workstation:

| STS order | `n` | `m` | `w*_c` wall-clock |
|---|---|---|---|
| 7 | 7 | 7 | 0.00 s |
| 9 | 9 | 12 | 0.08 s |
| 13 | 13 | 26 | **29.6 s** |
| 15 | 15 | 35 | **> 30 min, did not return** |

Reproduce with `scripts/diagnostics/sts_feasibility_probe.py`. Two orders of
growth cost three orders of magnitude, and the driver is **symmetry, not size**
— the same mechanism as the HIC real-data NO-GO (`DATA.md` §2) and the measured
frontier (`results/RESULTS_MANIFEST.md`). A Steiner system is close to a
worst case for the tie-complete encoder.

This is the right shape for a long single-job Picasso run: one instance, generous
wall, measured. If one STS(15) is tractable, the budget question is 80 instances
plus 3,160 pairs. If it is not, say so with the number and move to the fallback.

**Fallback (recommended if STS(15) is out of reach):** a new generator producing
non-isomorphic hypergraphs at **fixed `(n, m, k)` and fixed degree sequence**,
with rejection sampling and iso-dedup, scale set by the measured feasibility
envelope rather than by a fixed combinatorial design. `planted_families.py`
already does seed-plus-perturbation with iso-dedup; the new constraint is that
perturbations must be degree- and size-preserving, which the current Qin edit set
does not guarantee. Expect to need a *swap*-style edit (move an incidence, keep
degrees) rather than insert/delete.

Do not settle for the third option (a size-matched sub-corpus of the existing
designs): there are only three `(n,m)`-matched pairs and each differs in arity,
which is itself degree-correlated. Use it as a sanity check, not as the corpus.

## 5. In scope

- Reproducing and, if warranted, sharpening the finding.
- Designing, implementing, registering (`datasets/registry.py`) and documenting
  a size-controlled corpus; deterministic under `(params, seed)`.
- Registering `size_l1` (`|Δn| + |Δm|`) as a distance alongside
  `degree_seq_l1`, so it flows through the sweep harness and carries the same
  BCa CIs and Holm-corrected tests.
- Productionising `size_confound_probe.py` into the harness or `tests/`, so the
  confound cannot silently return.
- Re-measuring G1/A1/A2/A3 on the replacement; superseding
  `results/T-M7d/` under `results/superseded/` with a manifest entry.
- Updating every claim in `theoretical/geometry.md` and
  `empirical/applications.md` that reads from the old corpus — or withdrawing it.
- **A corpus policy section in `DATA.md`**: which corpus each measurement uses
  and why. This is a named deliverable, not a nicety. The current lineage
  (Stratum A designs, Stratum B random cells, planted families at N = 60/240/480,
  ladder corpora, the E1′ mini-corpus, the G3 OFAT bases) is ad hoc and
  inconsistent across experiments, which is how this defect survived. Geometry
  and applications must describe the same objects — `RESULTS_MANIFEST.md`
  already claims they do.

## 6. Out of scope — do not touch

- **`w*_c`, the encoder, the canonical algorithm, S2H.** The definition is
  frozen (D-TA2). If you believe the corpus problem requires changing it, that
  is a decision for the PI, not a change to make.
- **Dropping any competitor.** NetLSD and degree-sequence L1 stay. The
  interpretation contract in `COMPETITORS.md` §4 was pre-registered before
  results were seen precisely to bind this case. A naive baseline winning is a
  reason to fix the corpus, never a reason to remove the baseline — and an agent
  optimising for "make IsalHG look good" will find deletion the cheapest fix.
  It is the one move that would make the paper indefensible.
- **The frozen E1′ oracle results** (`results/T-M5a/`). Do not re-run; the
  measured ceiling is 100 GB / 18 h per block.
- **T-M5m** (the A4 ambient-decodability repair). Separate ticket, independent.
- Real data (HIC) stays a censored secondary exhibit, entering only where
  `w*_c` is computable.

## 7. Recording discipline — audit everything

This task rewrites the article's evidence base. Every number a reader will
eventually see must be traceable to a run you can point at. Concretely:

- **Keep a running log in the task file.** Append, never rewrite. Every session:
  what you ran, the command, the wall-clock, the output path, what it showed.
- **Record decisions with their rationale and their alternatives**, at the moment
  you make them, not reconstructed afterwards. Corpus design is a chain of
  judgement calls (which invariants to hold fixed, which edit set preserves them,
  what `N`, which seeds, what admission threshold) and each one is a place a
  reviewer can push. If a decision is the PI's rather than yours, file it in
  `DECISIONS.md` and proceed on a stated assumption rather than blocking.
- **Record negative results in the same detail as positive ones.** A generator
  design that failed to preserve degrees, a corpus size that proved infeasible, a
  candidate that collapsed under iso-dedup — these are the measurements that
  justify the design you land on, and they are the first thing a reviewer asks
  for. The STS(15) timing above is exactly this kind of result: it is worth more
  written down than discarded.
- **Every result JSON carries its seed** in the content, not just the filename
  (standing rule, `.claude/rules/coding_rules.md` §5.3). Every benchmark reports
  wall-clock and peak RSS.
- **State magnitudes, not adjectives.** "Both naive baselines score ARI 0.000 on
  all 27 seeds" is the acceptance evidence; "the corpus is now well-controlled"
  is not.
- When you touch the reasoning docs, follow the split in `CLAUDE.md`: task ids,
  decision codes, timestamps and status language live in `DEVELOPMENT/`; the
  reasoning prose states what is true and why.

## 8. Acceptance — you are done when

1. The replacement corpus is registered, deterministic, and documented in
   `DATA.md` with the size/degree control stated as a property.
2. On it, `size_l1` and `degree_seq_l1` score at the structural floor
   (ARI ≈ 0 / AUC ≈ chance) — **measured through the same harness**, not argued.
   This is the check that the confound is gone.
3. `size_l1` appears in every comparison surface with the same CIs and tests as
   every other row.
4. The confound probe is productionised so it cannot silently return.
5. The body is re-measured; superseded results are archived under
   `results/superseded/` with a manifest entry; every affected claim in the
   reasoning docs is updated or withdrawn.
6. `DATA.md` carries the corpus policy.
7. Full suite green, ruff/mypy at the standing baselines.

## 9. Context index

| What | Where |
|---|---|
| The ticket | `docs/article/DEVELOPMENT/T-M4/OPEN/T-M4b.md` |
| Full analysis + the four candidate fixes | `docs/article/figures/F7-task-metrics.md` §2–3 |
| The scope invariant that was violated | `docs/article/DEVELOPMENT/T-M4/README.md` |
| Corroborating geometry measurements | `docs/article/theoretical/geometry.md` §4–5 |
| The pre-registered baseline contract | `docs/article/COMPETITORS.md` §4 |
| Current corpus builder | `datasets/synthetic/known_design_catalog.py::build_stratum_a_corpus` |
| Steiner catalog (candidate substrate) | `datasets/synthetic/sts_catalog.py` |
| Perturbation generator | `datasets/synthetic/planted_families.py` |
| Result tree + its two standing hazards | `results/RESULTS_MANIFEST.md` |
| Measured feasibility frontier | `results/T-M7h/`, `docs/article/figures/F9-frontier.md` |
| Reproductions (4 probes + logs) | `scripts/diagnostics/` |
| Coding rules | `.claude/rules/coding_rules.md` |

## 10. One caution

The `w*_c` feasibility envelope is tight — `k = 3` to `n ≈ 24` at low density,
`k = 5` only at `n = 8`, `k = 7` and `k = 10` measured infeasible at every
tested size. A size-controlled corpus that is also *feasible* may be smaller
than the current 85 items. That is acceptable: a small corpus that measures
structure is worth more than a large one that measures size. If you find
yourself trading the control away to keep `N` up, you have reintroduced the
defect — report the trade-off instead and let the PI choose.
