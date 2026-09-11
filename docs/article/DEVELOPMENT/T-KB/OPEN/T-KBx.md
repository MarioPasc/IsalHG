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

**2. The numbers disagree with the live campaign by 35×.** Against
`IEEETKDE_isal/RQ7_envelope` (job 2271960, 74/74 COMPLETE, read 2026-09-11):

| quantity | walkthrough | RQ7 as measured |
|---|---|---|
| `nauty_cert`, whole matrix at N=3,988 | **864 s** | **24.19 s** |
| `fact_rank` | 1.5 s pairs + 0.31 s canon | 0.889 pairs + 0.221 canon (1.11 s) |
| `degree_seq_l1` | 43 s | 12.62 s |
| `bipartite_ged_assign` | 525 s | 634.0 s |
| `bipartite_ged_path` | 913 s | 952.5 s |
| `hpd_jsd` | 1,670 s at N=2,000, censored at 3,988 | censored at 3,988 (1 h cap) |
| `netlsd` | 2,724 s at N=1,000 | 40.61 s at N=3,988 |

The two bipartite arms and HPD **agree closely**, which is what makes the rest
diagnostic: this is not a wholesale re-run of everything. `nauty_cert` (35×) and
`netlsd` (two orders, and at a *larger* N) moved; the arms nobody touched did
not. So the walkthrough is very likely quoting a **superseded** lineage for those
two, not a different machine.

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
