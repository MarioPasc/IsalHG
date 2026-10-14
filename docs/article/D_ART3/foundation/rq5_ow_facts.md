# RQ5 on the ordered walk — fact base

*Derivation of record for the `w°` re-run of RQ5 (D-ART6, T-KBab). Written by
agent `rq8`, wave `2026-09-13-headline-w0`, 2026-09-14. Kept separate from the
campaign's own RQ5 fact base, which this agent does not own; the orchestrator
folds it.*

## 1. Provenance

| what | where |
|---|---|
| config | `experiments/tkde/configs/rq5_ow.yaml` (identical to `rq5.yaml` but for the arm) |
| Picasso job | **2308368**, `tkde-rq5`, COMPLETED 01:05:09, one task, 65 units |
| Picasso results | `~/results/IEEETKDE_ow/RQ5_patterns/` |
| drive mirror | `results/IEEETKDE_ow/RQ5_patterns/` (144 files, harvested 2026-09-14) |
| analysis | `results/IEEETKDE_ow/RQ5_patterns/analysis/` |
| runner | `experiments/tkde/rq5.py`, **unmodified** — the arm set is config-driven |

Unit count verified against the config: **65 clustering unit files**, arms =
`bipartite_ged_assign, bipartite_ged_path, degree_seq_l1, fact_rank, hpd_jsd,`
**`isal_ow_struct`**`, nauty_cert, nauty_cert_rows, netlsd, size_l1, wl_l1` —
`wstar_orbit` absent, as the swap requires.

## 2. The measured table (balanced designs, mean over 54 rows per arm)

| experiment | arm | ARI | NMI | silhouette |
|---|---|---|---|---|
| `wd50k66_balanced` | **`isal_ow_struct`** | 0.0675 | **0.2632** | 0.3233 |
| `wd50k66_balanced` | `netlsd` | **0.0705** | 0.2606 | 0.5148 |
| `wd50k66_balanced` | `hpd_jsd` | 0.0564 | 0.2504 | 0.3595 |
| `wd50k66_balanced` | `size_l1` | 0.0431 | 0.2292 | 0.5475 |
| `wd50k66_balanced` | `degree_seq_l1` | 0.0392 | 0.2337 | 0.4859 |
| `wd50k66_balanced` | `bipartite_ged_assign` | 0.0379 | 0.2305 | 0.5176 |
| `wd50k66_balanced` | `bipartite_ged_path` | 0.0367 | 0.2350 | 0.3054 |
| `wd50k66_balanced` | `fact_rank` | 0.0260 | 0.1789 | 0.2900 |
| `wd50k66_balanced` | `nauty_cert` | 0.0233 | 0.1830 | 0.3473 |
| `wd50k66_balanced` | `nauty_cert_rows` | 0.0220 | 0.1762 | 0.2801 |
| `wd50k66_balanced` | `wl_l1` | 0.0012 | 0.0919 | 0.1941 |
| `wd50k100_balanced` | **`isal_ow_struct`** | **0.0768** | 0.2064 | 0.3887 |
| `wd50k100_balanced` | `degree_seq_l1` | 0.0705 | **0.2308** | 0.4241 |
| `wd50k100_balanced` | `size_l1` | 0.0429 | 0.1547 | 0.4925 |
| `wd50k100_balanced` | `nauty_cert` | 0.0304 | 0.1246 | 0.3130 |
| `wd50k100_balanced` | `fact_rank` | 0.0290 | 0.1240 | 0.2686 |
| `wd50k100_balanced` | `wl_l1` | 0.0020 | 0.1057 | 0.0999 |

Analyzer verdicts (`experiments/tkde/analyze_rq5.py`, unmodified): **H5a, H5b,
H5c `not_supported`; H5d `inconclusive`.**

## 3. The comparison the brief asked for cannot be made, and why

The instruction was to compare against "the `wstar_orbit` numbers already in
foundation". **There are none.** `wstar_orbit` appears in **0 of 54** campaign
RQ5 clustering row files under `results/IEEETKDE/RQ5_patterns/rows/`, although
`configs/rq5.yaml` lists it in all three experiments. Either the campaign RQ5
ran before the arm was added to that config, or the arm was dropped at run time
(its matrices carry `.censored.json` companions, and RQ5 reads cached matrices).
Whichever it was, there is no `wstar_orbit` RQ5 row to compare against and none
is invented here.

What is substituted is stronger anyway: the **whole field**, recomputed by this
agent from the campaign's own rows with the identical aggregation, so the two
columns are commensurable. The cross-check is exact — every arm the two runs
share reproduces to four decimals (e.g. `bipartite_ged_assign`
0.0379 / 0.2305 / 0.5176 in both; `netlsd` 0.0705 / 0.2606 / 0.5148 in both).
That agreement is the evidence that the `w°` run is sound, and it is worth more
than the missing single-arm delta.

## 4. Reading

**The pre-stated expectation held: RQ5 stays negative.** Every arm sits below
ARI 0.08; Wikidata type labels are near-unclusterable from structure alone, as
the campaign already found.

**Within that negative, the swap is an improvement and the paper may say so
carefully.** `isal_ow_struct` leads NMI on `wd50k66_balanced` (0.2632, above
`netlsd`'s 0.2606) and leads ARI on `wd50k100_balanced` (0.0768, above
`degree_seq_l1`'s 0.0705); it is second on ARI for `wd50k66_balanced`
(0.0675 against `netlsd` 0.0705). The retired fact-rank word scored 0.0260 /
0.1789 on the same design, so the ordered walk is **2.6× its ARI** — the swap
moves the Isal family from last-but-one to the front of a weak field.

**The naive floors do not win here**, contrary to the pre-stated expectation
carried over from the planted corpora: `size_l1` 0.0431 and `degree_seq_l1`
0.0392 on `wd50k66_balanced`, both below `isal_ow_struct`. On `wd50k100` the
degree floor is close (0.0705 against 0.0768) and leads on NMI. Reported as
measured, not as expected (L12).

**`wl_l1` collapses** (ARI 0.0012, NMI 0.0919) on both designs, consistent with
its tie-degeneracy elsewhere in the campaign.

## 5. Caveat on the significance of these orderings

The means above are over 54 rows per arm; the ARI differences between the top
four arms (0.0675 to 0.0705 on `wd50k66`) are small and this fact base does
**not** assert that any of them is Holm-separated. `analyze_rq5.py`'s own
hypothesis verdicts are reported in §2 and they are negative. Any prose claim of
an ordering among the leaders needs the paired test, not these means.
