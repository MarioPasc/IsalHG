# RQ1 addressing — the verified fact base

Every number `prose.md` may quote for RQ1, with the artefact that produced it.
Same rule as the other entries: **a number with no entry here is struck, not
kept**, and this is a precondition on the T-KBg fold rather than a step inside it.

RQ1 is the most-cited experiment in the paper — **19 `prose.md` mentions**, more
than any other — so it is also the largest single opportunity for the defect
class this file exists against.

## Provenance — recorded in the artefact, not reconstructed

| | |
|---|---|
| deliverable | `results/IEEETKDE/RQ1_isal/merged/` — **read-only since 2026-09-11** |
| contents | **483 files**: 465 row files + **18 deliverable files** |
| tables | `published_tables.md` (M1, M2), `tables.md`, `rq1_statistics{,_ndc_classes,_synthetic_rq1,_wd50k66}.{md,json}`, `verification_checks.md`, `summary.json`, `stats.json` |
| provenance record | `merge_manifest.json` |
| README | `results/IEEETKDE/RQ1_isal/FROZEN.README.md` |
| pointer | `results/frozen/rq1_isal_merged.POINTER.md` (the deliverable predates that convention by three days) |

**The count to quote is 18, not 483 and not 17.** The deliverable is 18 files;
the directory is 483; `HANDOFF_2026-09-07` says "17" and is off by one. All three
numbers are true of *something* and only one is what a reader means.

### Which campaign the rows came from

`merge_manifest.json`, which exists because `RQ1_addressing` once held **two**
campaigns and a bare concatenation double-counted **904,442 of 2,506,837** rows
(T-KBe / T-KBh / T-KBn):

| | |
|---|---|
| tags **available** under `addressing` | `47c8a42c` (155 files) **and** `c3fb21de` (155) |
| tags **used** | **`47c8a42c` only** — the Isal campaign |
| Isal arms | `addressing_cpp`, tag `ebda0b71` |
| `wstar_rank` | `addressing_rank`, tag `28536068` |
| arm dropped | `fact_rank_roles` (fails the M0 relabelling-invariance gate) |

**Duplicate audit — 0 duplicate rows in all five tables**, each with its key
declared and `rows == unique_observations`:

| table | rows | key |
|---|---|---|
| `m0items` | 88,428 | `collection, seed, member_id, arm` |
| `m1` | **1,673,904** | `collection, seed, base_id, edit_kind, edit_idx, arm` |
| `m2` | 66,336 | `collection, seed, series, pair_id, arm` |
| `m3` | 88,428 | `collection, seed, member_id, arm` |
| `m4` | 36,000 | `collection, seed, series, pair_id, arm` |

So the double-count is **provably absent here** rather than presumed absent: the
merge saw both campaigns and took one.

### The gate that produced it had authority

Traced link by link, because a stated gate that cannot stop anything is not a
gate:

| link | |
|---|---|
| `verify_rq1_join.py` | `if all_problems: … return 1`, and `sys.exit(main())` |
| `build_rq1_isal_table.sh` | **`set -euo pipefail` at line 35**, before the gate at line 57 |
| consequence | an unsound join **aborts before the merge**, as the script's own comment claims |

Both halves were required and neither is visible from the other file.

### Nothing has written since

Every write under `merged/` falls inside the merge window
**2026-09-08 12:55–16:04**; the RQ1 array `2247394` ended before it. It was
**483 of 483 files writable** until 2026-09-11 and is now read-only.

## Coverage of the prose — screened, not yet audited

Every figure within ±1 line of an RQ1 mention in `prose.md`, matched against all
17 md/json deliverable files after whitespace flattening:

| | |
|---|---|
| figures near RQ1 mentions | **33** |
| resolve to the RQ1 deliverable | **30** |
| resolve to `rq6_generation_facts.md` | **3** — `98.10 %`, `98.98 %` (incidence-list rejection) and `0.1260` (WD50K connectivity), pulled in by the ±1-line window from the neighbouring Prop row |
| **unsourced** | **0** |

**What this claim is, stated so its reach can be judged:** *no figure adjacent to
an RQ1 mention in `prose.md` fails to appear, as a digit string after whitespace
flattening, in either the RQ1 deliverable or another campaign fact base.*

**What it is not.** It is a **screen**: it proves no figure unsourced and proves
none correct, and it does not read the **noun** beside any number — a sentence
attaching a true figure to the wrong object sources identically to the right one.
That is the fold's **predicate pass**, and it is the one class no tool here
reaches. The 33 are **located, not adjudicated**.

The ±1-line window is also why three RQ6 figures appear above: proximity is not
attribution, and a figure's neighbours in a table row belong to other rows.
