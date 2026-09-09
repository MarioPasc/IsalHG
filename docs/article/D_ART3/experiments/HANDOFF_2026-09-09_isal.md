# Handoff — the Isal instruction word for knowledge bases (D-ART5), 2026-09-09

*Written by the `[IsalHG-Refinement-Opusxhigh]` session for the agent that
continues this work. Supersedes `HANDOFF_2026-09-07_isal.md`, whose §5.1–5.2
(RQ1 harvest, table, decision) are **done**. Everything below is on disk (path
given), a job id on Picasso, or a rule the author gave in session. Read it end
to end before touching anything.*

## 0. State in one paragraph

**RQ1 is measured, verified and decided.** The paper's canonical program is the
family's frozen `w*_c` computed by the **stabiliser-orbit-pruned C++ engine**
(D-ART5, recorded 2026-09-09). This is not a new ruling: D-TA2 named orbit
pruning as the one sanctioned speedup, the D-ART4 addendum says supersession is
"required only if the canonical *value* changes", and the value is unchanged —
verified on 7,013/7,013 words, 130,788/130,788 single-edit distances and
5,174/5,174 ladder pairs. The ordered walk `w°` is the order-only cell of RQ1
and the cost floor of RQ7; the rank-keyed walk `w*_ρ` is the "both" cell of RQ1
only. All five RQ1 job groups are terminal; the deliverable is frozen at
`results/IEEETKDE/RQ1_isal/merged/` (17 files) and nothing regenerates it.
**What remains is T-KBf (the RQ2–RQ7 submissions), T-KBg (the prose fold and
the one-page reading), and seven filed follow-ups.** Nothing is submitted.

## 1. Read, in order

| # | file | what it settles |
|---|---|---|
| 1 | `DECISIONS.md` **D-ART5** (and D-TA2, D-ART4 above it) | the representation, the budget, and the fact-arm concession — with the quote chain showing each was already ruled |
| 2 | `D_ART5_DECISION_BRIEF.md` (this directory) | the same three, with every measurement, the case *against* each recommendation, and §5 "what to be sceptical about" |
| 3 | `docs/article/DEVELOPMENT/T-KB/IN-PROGRESS/T-KBe.md` | the full record of the RQ1 campaign: six defects found, three claims withdrawn, the cluster keys, the censoring drift |
| 4 | `ISAL_VARIANT_DESIGN.md` §3, §3b, §7, **§9** | the pre-registration, the four-cell ablation, the nauty sentences, and the measured deviations — §9 item 8 is the rule that governs every remaining reading |
| 5 | `docs/article/DEVELOPMENT/T-KB/OPEN/T-KBf.md`, `T-KBg.md` | the two open tasks, with the corrections this campaign forced |
| 6 | `.claude/notes/2026-09-08-isal-kb-w6/summary.md`, `.../w7/rq1-stats.md` | the two implementation waves: the budgeting audit and the statistics harness |
| 7 | `docs/article/D_ART3/prose.md` §2–§4, §6, §11 | the storyline; §2.3 carries an error the new numbers expose (see T-KBg) |
| 8 | `proofs/completeness/theorem_c_ordered_walk.tex` (on the drive) | Theorem C, Prop. C.4 (closed *and connected*), Prop. C.7 (orbit pruning is value-preserving) |

## 2. Standing rules

Rules 1–7 are the author's, carried forward from the previous handoff. Rules
8–11 are what this campaign learned; ignoring them cost real work.

1. **C++ only in the article.** Every arm in a final table runs on the C++
   engine. Python engines are references and guards, never results.
2. **No heavy local runs.** The workstation went OOM once. Measurement runs on
   Picasso. The cluster **login node** is fine for analysis (the RQ1 analyzer
   takes ~30 min and peaks around 22 GB transiently on a 188 GB node); ask
   before anything heavier than a test file locally.
3. **At most 2 Opus subagents at once; Opus only for implementation and
   monitoring;** Sonnet for briefings and operations; `model:` passed
   explicitly on every spawn.
4. **Worktrees + cloned envs** for every implementation agent
   (`conda create -y -n isalhg-<slug> --clone isalhg`, then
   `pip install -e ".[dev]"` inside the worktree; use only that env's python).
5. **Commits** on `feature/isal-kb-word`, conventional, each ending with your
   own `Claude-Session:` trailer.
6. **The parallel-agents skill** governs waves: file-disjoint ownership,
   committed work logs, verification against the diff before merge, `--no-ff`
   merges from the **main checkout**.
7. **Report failures with the same directness as successes.**
8. **No direction is asserted from point estimates** (design §9 item 8). Three
   directional claims were made this campaign from point estimates and all
   three dissolved under the paired test — two of them were ties. The corpora
   are unbalanced, the arms tie on most entities, and pooled columns are
   mixtures weighted by member counts. If a number has no interval, it does
   not support a direction.
9. **Every cross-arm comparison is on the common unit set, and per corpus.**
   Each arm censors a different subset, so the analyzer's tables score arms on
   different units; and a pooled cell is a mixture (WD50K supplies 3,946 of
   4,535 pendant-deletion clusters). Use
   `scripts/tkde/rq1_extra_checks.py published` and
   `scripts/tkde/rq1_statistics.py --collections`.
10. **Before escalating anything to the author, grep the decision record for
    the object it concerns and read the *reasoning of record*, not only the
    ruling line.** Three questions were put to the author as open decisions
    this session; all three had already been answered — one by a clause inside
    D-TA2, one by the pre-registration, one by D-ART4's own instruction to the
    prose. Escalation is not free: it spends the author's attention and invites
    re-ruling on closed matters.
11. **Cancelling a Picasso job needs the author to name the job id
    explicitly** — the permission guard rejects "cancel what you need to". Ask
    for `cancel job <id>` verbatim.

## 3. What is on disk, and what is frozen

**The RQ1 deliverable — frozen, do not regenerate.**
`results/IEEETKDE/RQ1_isal/merged/` (on the drive,
`/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/`):

| file | what |
|---|---|
| `tables.md`, `stats.json`, `summary.json` | the analyzer output, all six gates passed |
| `rq1_statistics.md/.json` | intervals + Holm-corrected paired tests, pooled |
| `rq1_statistics_{wd50k66,ndc_classes,synthetic_rq1}.md/.json` | the same, per corpus |
| `verification_checks.md` | arm agreement, common-set identity, censoring tail, M4 ρ |
| `m1_instructions_by_kind.md`, `published_tables.md` | the per-kind and common-unit tables |
| `merge_manifest.json` | which arm came from which run, the launch tags, the duplicate audit |

Source rows: `results/IEEETKDE_isal/RQ1_addressing/{addressing,addressing_rank,addressing_cpp}/`.

**Why it is frozen.** Censoring is decided by a wall-clock budget, so the
unpruned engine's count is a property of a *run*: four reads of the same
members at the same budget gave 357, 354, 356, 353. `wstar_orbit` (77),
`wstar_rank` (53) and `isal_ow_struct` (0) were identical in every read, so no
published number moves — but do not re-harvest and expect byte equality.

**The cluster.** All RQ1 jobs terminal (2247394, 2247395 cancelled after
completion, 2248782, 2248907, 2248908). Tree:
`~/fscratch/repos/IsalHG-tkde`, env `~/fscratch/conda_envs/isalhg-tkde`.
Results on **HOME** (`~/results/IEEETKDE/`) on purpose — FSCRATCH is over its
file-count soft quota.

**⚠ The cluster tree is stale.** The T-KBf code (budget.py, matrices.py,
rq3.py, rq5.py, rq7.py, `toolkit/matrix.py`, the configs) exists only locally
plus a few hand-copied scripts. **Run `scripts/tkde/sync_to_picasso.sh` before
any RQ2–RQ7 submission.** It rebuilds the extension on the login node, which
is now safe because no job is running — it would **not** have been safe during
the RQ1 campaign, since running tasks import the shared `.so`.

## 4. The next steps, in order

### 4.1 T-KBf — RQ2–RQ7 with the Isal arm

**The arm set under D-ART5.** One Isal row per table: **`wstar_orbit`**. The
ordered walk `isal_ow_struct` appears additionally in **RQ7** as the cost
floor. `wstar_rank` does not appear outside RQ1. The two certificate
tokenisations (`nauty_cert`, `nauty_cert_rows`) ride along everywhere;
`fact_rank_roles` is out of every table and out of `rq1.py::DEFAULT_ARMS`.

**Before submitting anything:**

- `bash scripts/tkde/sync_to_picasso.sh` (see §3).
- Two research decisions the budgeting audit deliberately left unwired, both of
  which bite in this phase:
  - `rq3.py:473` — the medoid `build_matrix` over `MEDOID_ARMS` is unbudgeted
    and poisons the parent process. A medoid over a *censored subset* is a
    research decision, not a default; decide it before RQ3.
  - Whether `rq2/rq4/rq5` should tolerate a censored arm's short matrix. They
    currently read the full member order and would see a cache miss.
- **Do not land T-KBj (the `spawn` fix) now.** It changes the process model
  under the measurement machinery; landing it between RQ1 and RQ2 makes the
  censoring censuses incomparable. It is filed with its own differential.

**Order** (D-ART4 note (d), T-KBf): matrices (`matrices_launcher.sh`) → RQ2 →
**RQ3, piloting one NDC cell first** (the consensus canonicalises hundreds of
candidates per cell and NDC sources are symmetric) → RQ4 → RQ5 → RQ6 → RQ7
(with the `|Aut|` axis **and** the 600 s re-run of the 77 orbit-censored
members folded in — never as a row; see the pre-stated expectation in T-KBe).

**Launch pattern** (adapt the config and launcher per RQ):

```bash
ssh picasso 'REPO=/mnt/home/users/tic_163_uma/mpascual/fscratch/repos/IsalHG-tkde; cd "$REPO" && \
  RQ2_CONFIG="$REPO/experiments/tkde/configs/rq2.yaml" REPO_DIR="$REPO" bash slurm/tkde/rq2_launcher.sh --smoke'
# then without --smoke
```

**Arm a monitor** on the submitted ids, keyed on job state only (never on file
counts — they change every few minutes), `persistent: true`, and let it
self-terminate on the terminal condition:

```bash
prev=""; while true; do st=$(timeout 60 ssh -o BatchMode=yes picasso 'for j in <IDS>; do echo "$j: $(sacct -j $j -X -n -P -o State 2>/dev/null | sort | uniq -c | tr -s " " | tr "\n" ";")"; done' 2>/dev/null || echo "ssh failed"); if [ "$st" != "$prev" ] && [ "$st" != "ssh failed" ]; then echo "$(date +%H:%M) $(echo "$st" | tr '\n' ' ')"; prev="$st"; fi; if [ "$st" != "ssh failed" ] && ! echo "$st" | grep -q "RUNNING\|PENDING"; then echo "ALL TERMINAL"; break; fi; sleep 300; done
```

**Pre-stated readings** (design §5, D-ART4 (3)): RQ2 exact + metric +
polynomial per pair after canonicalisation; RQ3 carries over with connected
interiors; RQ4/RQ5 at the certificate's level → supplement as characterisation
(author's ruling); RQ6 stronger (validity **and connectivity** by Prop. C.4);
RQ7 the envelope moves from `|Aut|` to `(m, k)`.

### 4.2 T-KBg — the prose fold and the one-page reading

- Fill the four *pending* markers in `prose.md` (§2.3, §3 RQ1, §4) from the
  frozen deliverable. **Every number is per corpus and on the common unit
  set**; there is no pooled column in the main text.
- **`prose.md` §2.3 carries an error**: "the one locality the Isal walk owns
  outright, *deletions*". Against the certificate we own three pendant kinds
  (it is at 0.000 on all of them); against the fact list we do *not* own
  deletions (interior: 57.8 % against 13.9 %). The axis is **pendant vs
  interior**, not deletion vs insertion. Detail in T-KBg.
- Name the regimes in words, never by number: **pendant** = the edit changed
  the constant inventory; **interior** = it did not. State once that
  `add_constant`/`remove_constant` are arity **widening/narrowing of one fact**,
  not inventory changes — a reader will otherwise assume the opposite.
- The caption must say once that the paired-difference **interval is
  per-comparison while the p is Holm-corrected across the family**; several
  rows show an interval excluding zero beside p_Holm > 0.05 and it reads as a
  contradiction otherwise.
- The **one-page PI reading** (brief deliverable 4): which canonical program,
  why, its cost, and the updated R-list — R1 regime-specific and per corpus;
  R2 lifted for symmetry (|Aut| ≥ 10⁷: 36 → 0; WD50K 237 → 7) and not for
  arity (69 of the residual 77 are arity-10 at |Aut| < 10³); R3 proved
  (Prop. C.4); R4 filed; R5 kept; R6 conceded for the search with `w°` the
  sub-millisecond member.
- The nauty sentence: under D-ART5 the **oracle** sentence of design §7 is the
  methods sentence; the **order** sentence is used once, in the RQ1 ablation.
- Apply the `humanizer` skill to any passage over 200 words.
- `START_HERE.md` §0/§0.1/§6.0 and `DESIGN.md` G1 still need the pointer
  update (they predate D-ART4).

## 5. Defects found — do not re-find these

Carried forward, plus this campaign's. The first six are from 2026-09-07.

| defect | resolution |
|---|---|
| Python `canonical_rank` applied ranks at depth 0 only | fixed, pinned (wave 3) |
| Python engines materialise `(2r+1)^k` tuples: 9.8 GB in a 60 s budget | guarded (`2ccc9fa`, `e40b327`) |
| `wstar_rank` ran in-process, unbudgeted (12-min hang) | budgeted (`7ed77aa`, `30067fe`) |
| runner hardcoded the experiment name; a run's rows were lost | `experiment_name(config)` drives paths (`cf391fe`) |
| launchers defaulted to retired per-agent remote trees | shared tree default (`17355b7`) |
| a forked child deadlocks after in-process C++ canonicalisation | `cpp_fork_is_healthy` canary; now `guarded_budget_call` |
| **`RQ1_addressing/addressing` holds TWO campaigns** (tags `c3fb21de` job 2215137, `47c8a42c` jobs 2247394+95). Merging the directory double-counted **904,442 of 2,506,837** rows | `--only-tags` + a duplicate audit that refuses the merge (`314b4a3`) |
| **The merge's per-arm source is load-bearing**: `wstar_orbit` reads **406** censored from the Python-engine experiment against **77** from the C++ one | `--prefer` pins the source per arm; recorded in `merge_manifest.json` |
| the analyzers pool launch tags they were built to separate | filed as **T-KBh** (not fixed) |
| the median interval bounded the median of per-cluster medians while the point was the pooled median — BCa degenerate on all 48 cells | `cluster_median_ci_pooled` (`6dac155`) |
| the reported RQ7 budgeting defect was a **false positive** — `rq7.py` calls `rq1.member_word`, which routes budgeted arms through `engine_word`; the grep missed an indirect call | verified; the real gap was `run_nscaling` (`rq7.py:385`), fixed |
| an unconditional fork canary in `rq3.run_guarded` **refused valid work** — its call site is pure-Python `fact_key_of` | `cpp_engine` is now an explicit declaration, defaulting False there |

## 6. Open follow-ups (ledger)

`T-KBa` roles (later) · `T-KBb`/`T-KBd` code done, close when RQ7/M3 re-measure
lands · `T-KBc` nauty-free ordered walk (future work) · **`T-KBf`** RQ2–RQ7 ·
**`T-KBg`** prose + PI reading · `T-KBh` analyzers pool launch tags ·
`T-KBi` private cross-module import behind the walk's pointer rendering ·
`T-KBj` the fork poison and its `spawn` fix (**not** between RQ1 and RQ2) ·
`T-KBk` the data section's corpus numbers, including the **519 NDC members
dropped by the arity cap** that the supplement never mentions.

`T-KBe` stays IN-PROGRESS until the author acknowledges D-ART5; every
measurement criterion is met.

## 7. When to consult the `[IsalHG-Fable]` session

There is a peer Claude session named **`[IsalHG-Fable]`** (Fable model) that
co-reasoned the D-ART5 decision. Reach it with
`SendMessage({to: "[IsalHG-Fable]", ...})`; check it is alive with
`ListAgents` first, and **assume it has no context** unless it says otherwise —
it has been restarted at least once. Give it a reading list, not a summary.

Consult it when:

- a measured result **contradicts a pre-registered hypothesis** and the
  question is what the paper may now claim;
- a sentence is about to assert a direction and you are unsure the statistics
  support it (it caught three that did not);
- you are about to **escalate something to the author** — it triaged three
  "PI-level" decisions as already settled, correctly;
- the question is *framing*: which corpus carries a claim, what a caption must
  disclose, whether a concession belongs in the main text.

Do **not** consult it for: running jobs, reading files, or anything with a
determinate answer in the repo. Its value is adversarial judgement on claims,
and it is expensive.

It has been right against this session four times and wrong none, so argue with
it on evidence rather than deferring — and tell it when it is wrong. Its
"128 quarters" resampling unit was wrong (the NDC M2 clusters are 61 entities,
one supplying 37 of 400 pendant pairs) and saying so changed the intervals.

## 8. Which model

The reasoning-bound work is done and recorded. What remains is orchestration
(submit, monitor, harvest), a prose fold against numbers that already exist,
and two research decisions in §4.1 that need judgement but not new theory.
**Opus at `xhigh` is sufficient**; use Sonnet for reading and operations.
Re-engage a top-tier session only if an RQ2–RQ7 result contradicts a
pre-stated reading in a way that reopens D-ART5 — then §9 of the design record
is where the re-think starts.
