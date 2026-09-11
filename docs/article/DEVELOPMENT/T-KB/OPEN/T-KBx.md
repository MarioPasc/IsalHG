# T-KBx — RESULTS_WALKTHROUGH's N-scaling paragraph carries the tokenisation confound, and its numbers disagree with the live campaign by 35×
**Declared:** 2026-09-11 03:26 CEST
**Status:** OPEN
**Delegation:** agent
**Why out of scope:** found by an absence sweep while correcting the same defect
in RQ7's headline. It is a second occurrence in a different document, not part of
reading RQ7.

**Context to read first:**
- `docs/article/D_ART3/experiments/RESULTS_WALKTHROUGH.md` lines ~333–337
- `docs/article/DEVELOPMENT/DECISIONS.md` D-ART4, the two-tokenisations clause
- `docs/article/D_ART3/foundation/rq7_envelope_facts.md` §8 (the current numbers)

## Two defects in one paragraph

**1. The tokenisation confound, stated outright.** The paragraph reads:

> N-scaling of the all-pairs matrix on WD50K (N = 3,988): `fact_rank` 1.5 s of
> pair distances plus 0.31 s of canonicalisation; **`nauty_cert` 864 s (its
> strings are 12–30 × longer)**; …

It quotes the bytes-tokenised certificate alone **and** attributes the gap to a
length ratio — and that ratio is measured across two units (`tokens_or_bytes`
holds *tokens* for our arms, *bytes* for the certificate). D-ART4 requires the
certificate baseline in **two standard tokenisations** because "the bytes-only
comparison is a tokenisation confound (audit §1.2 item 2)". `nauty_cert_rows`
does not appear anywhere in the file.

Since a pairwise Levenshtein is `O(L₁ × L₂)`, the timing claim and the length
claim are the same claim, so the unit objection disqualifies both.

**2. Two arms disagree with the live campaign; the rest are stable at matched N.**

`[IsalHG-Fable]` challenged the first draft of this section for comparing
whole-matrix times without establishing the `N` behind each one — the same defect
one level up from the one this task is about. Checked: the paragraph **declares**
`N = 3,988` for the sentence and annotates its two exceptions inline ("HPD
1,670 s **at N = 2,000**", "NetLSD 2,724 s **at N = 1,000**"), so the `N` is
recoverable per row. Compared at matched `N` against
`IEEETKDE_isal/RQ7_envelope` (job 2271960, 74/74, read 2026-09-11):

| arm | N | walkthrough | campaign | ratio |
|---|---|---|---|---|
| `bipartite_ged_assign` | 3,988 | 525 s | 634.0 s | 0.8× |
| `bipartite_ged_path` | 3,988 | 913 s | 952.5 s | 1.0× |
| `hpd_jsd` | 2,000 | 1,670 s | 1,485.6 s | 1.1× |
| `degree_seq_l1` | 3,988 | 43 s | 12.6 s | 3.4× |
| `nauty_cert` | 3,988 | 864 s | **24.2 s** | **35.7×** |
| `netlsd` | 1,000 | 2,724 s | **4.1 s** | **661.6×** |

**Three arms agree within ~20 % at matched `N`**, which rules out an engine-wide
or corpus-wide change: a faster machine or a smaller corpus would have moved
those too. So the reading is **partial supersession** — `nauty_cert` and
`netlsd` moved, everything else did not.

`netlsd` also changed **qualitatively**: the walkthrough says it was *censored
above* `N = 1,000`, while the campaign completes `N = 3,988` in 40.61 s with
**zero** censored or skipped reps. `hpd_jsd` is the control — censored at 3,988
in both, and within 11 % at N = 2,000.

*(The first draft of this task said "two orders" for `netlsd` by comparing
2,724 s at N = 1,000 against 40.61 s at N = 3,988 — itself an unmatched
comparison, and understating it. Matched, it is 662×.)*

### The discrepancy is per arm, not shared — and NetLSD is solved

`[IsalHG-Fable]` observed that `degree_seq_l1`'s 3.4× belongs to neither
category, and proposed that the discrepancies might order inversely with each
arm's intrinsic per-pair work — the signature of a **shared** change (a faster
matrix loop or edit-distance primitive) rather than per-arm re-runs. Tested,
because it is cheap:

| arm | ratio | old s/pair | new s/pair |
|---|---|---|---|
| `netlsd` | 661.6× | 2.724e-03 | 4.118e-06 |
| `nauty_cert` | 35.7× | 5.433e-05 | 1.521e-06 |
| `degree_seq_l1` | 3.4× | 2.704e-06 | 7.934e-07 |
| `hpd_jsd` | 1.1× | 4.175e-04 | 3.714e-04 |
| `bipartite_ged_path` | 1.0× | 5.741e-05 | 5.989e-05 |
| `bipartite_ged_assign` | 0.8× | 3.301e-05 | 3.986e-05 |

**Refuted, by a direct counterexample.** `bipartite_ged_path` and `nauty_cert`
have the same old per-pair cost to within 6 % — 5.741e-05 against 5.433e-05 —
and ratios of **1.0× and 35.7×**. No single shared change produces both. The
ordering is not monotone in per-pair cost either (3.4×, 0.8×, 35.7×, 1.0×, 1.1×,
662× as cost rises). So the lineage question stays *"which arms were re-run"*,
not *"which commit replaced the shared path"*.

**NetLSD's 662× is explained, and it is not a re-run.** The old per-pair cost and
the campaign's per-**item** descriptor cost are the same number:

| | |
|---|---|
| campaign canon phase, N=3,988 | 10.757 s over 3,988 items → **2.697e-03 s per item** |
| walkthrough, 2,724 s at N=1,000 | over 1,000,000 pairs → **2.724e-03 s per pair** |
| ratio | **1.010** |

The old run computed **one full NetLSD descriptor per pair** where the campaign
computes `N` of them and reuses them — an `N²` → `N` change in the descriptor
phase. That predicts a speedup of order `N`, which at `N = 1,000` is the observed
662× (the model `N·d/(d + N·c)` with the measured `d` and `c` gives ≈ 590), and it
explains the qualitative flip from *censored above N = 1,000* to completing
N = 3,988 in 40.61 s. The campaign's own pair phase, 1.877e-06 s per pair, is a
cheap vector op — exactly what remains once the descriptor is hoisted.

So **`netlsd`'s walkthrough figure measures a missing cache, not a slower
machine and not a different corpus.** It should not be quoted at all.

**Still open: `nauty_cert` (35.7×) and `degree_seq_l1` (3.4×).** Neither is
explained by the shared-path account, and an explanation that covers 662× while
leaving 3.4× unmentioned is the one a reader tests first. `nauty_cert`'s new
figure implies 1.52e-06 s per pair over certificates of ~11,692 bytes, which is
fast enough to want checking on its own — a length-difference early exit, a
dedupe of equal certificates, or a shorter certificate would each explain it, and
they are distinguishable.

## Acceptance

0. **Confirm the `N` behind every row on both sides, before anything else.** Done
   for the table above — the paragraph declares `N = 3,988` and annotates its two
   exceptions — but redo it for any row added later. Whole-matrix times at
   different `N` are not comparable, and a 16× difference in pairs can
   manufacture an apparent agreement or conceal a real one. This step decides
   what the lineage question is even looking for. *(Raised by `[IsalHG-Fable]`
   against the first draft of this task, which compared six arms after
   establishing `N` for only one of them.)*
1. **Establish the lineage** of the walkthrough's paragraph — which results root
   and job produced 864 s and 2,724 s — before any number is changed. Only
   `nauty_cert` and `netlsd` need explaining; the other four are stable at
   matched `N`. If it is a superseded root, the paragraph is restated from
   `rq7_envelope_facts.md` §8 and marked with its source.
2. **Report both tokenisations** wherever a certificate comparison appears, per
   D-ART4: `nauty_cert` (bytes) **and** `nauty_cert_rows` (one symbol per
   canonical adjacency row, 13.87 s at N=3,988). Neither quoted bare.
3. **Strike the "12–30 × longer" attribution — its likely source is now
   measured.** As written it compares tokens against bytes. On `wd50k66`
   (400-member sample) the certificate averages **159.7 bytes** against the
   walk's **13.8 tokens**, a ratio of **11.5×** — in the quoted range, and the
   confounded comparison. But **400 of 400 certificate lengths are divisible by
   4**: the certificate is a sequence of 4-byte big-endian integers, so its
   natural symbol count is `bytes/4`. In natural units the ratio is **2.9×**, and
   a 4× inflation from integer width is the whole difference between the two
   figures. Re-derive or strike; do not carry the bytes ratio.
3b. **The length attribution is a *correct* mechanism at the wrong granularity —
   do not file it as refuted.** A first draft of this task recorded it as
   disconfirmed, on the grounds that 2.9× of length cannot produce a 24.7× time
   ratio. That used the certificate's **natural** symbol count while `rapidfuzz`
   is handed its **bytes**, and a runtime is governed by what the algorithm
   iterates over. Measured directly (500 wd50k66 members, `process.cdist`):

   | handed to rapidfuzz as | mean L | s/pair | ratio to the walk |
   |---|---|---|---|
   | bytes | 160.5 | 6.23e-07 | **20.9×** |
   | 4-byte integers | 40.1 | 7.95e-08 | **2.67×** |
   | walk tokens | 13.7 | 2.98e-08 | 1× |

   **Granularity alone accounts for 7.83× of the certificate's cost**, and at its
   own symbol granularity the ratio is 2.67× — essentially the 2.9× length ratio.
   So the mechanism is length; what was wrong in the walkthrough is the *ratio*
   (11.5× bytes-vs-tokens, quoted as "12–30 ×"), not the attribution. Correct the
   ratio and state the granularity; do not record the mechanism as refuted.
   *(Caught by `[IsalHG-Fable]` against this task's own first draft.)*
4. **Sweep the rest of the file** the same way — it quotes `nauty_cert` four
   times and `nauty_cert_rows` zero times, so items 2–3 may apply more than once.

**Out of scope:** re-running anything; the RQ7 numbers themselves, which are
measured and filed.
