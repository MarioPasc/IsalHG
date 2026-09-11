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

## Acceptance

1. **Establish the lineage** of the walkthrough's paragraph — which results root
   and job produced 864 s / 2,724 s — before any number is changed. If it is a
   superseded root, the paragraph is restated from
   `rq7_envelope_facts.md` §8 and marked with its source.
2. **Report both tokenisations** wherever a certificate comparison appears, per
   D-ART4: `nauty_cert` (bytes) **and** `nauty_cert_rows` (one symbol per
   canonical adjacency row, 13.87 s at N=3,988). Neither quoted bare.
3. **Strike or re-derive the "12–30 × longer" attribution.** As written it
   compares tokens against bytes. If a length claim is wanted, it needs one
   tokenisation applied to both sides; otherwise the timing stands on its own
   with the serialisation named and no mechanism asserted.
4. **Sweep the rest of the file** the same way — it quotes `nauty_cert` four
   times and `nauty_cert_rows` zero times, so items 2–3 may apply more than once.

**Out of scope:** re-running anything; the RQ7 numbers themselves, which are
measured and filed.
