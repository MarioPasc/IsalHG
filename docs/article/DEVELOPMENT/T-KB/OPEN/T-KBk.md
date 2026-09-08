# T-KBk — the data section's corpus numbers do not match the built corpus

**Status:** OPEN · declared 2026-09-08 16:20 CEST by the Isal-refinement
orchestrator, from the [IsalHG-Fable] review of the RQ1 corpus counts.

Nothing here changes a measured result. The RQ1 corpora are what they always
were and `scripts/tkde/freeze_corpora.py` already audits them against the
supplement (ndc_classes 10 mismatched / **0 unexplained**; wd50k66 2 / **0**).
What is wrong is what the *prose* prints and what a reader can verify.

## The frozen envelope

`src/isalhg/datasets/kb/base.py::Envelope` — `n_max = 24`, `m_min = 3`,
`m_max = 110`, `k_max = 10`.

## 1. Code — record the drop that the explanation cites (blocking a claim)

`census.json` records `n_dropped_over_arity_cap` but **not**
`n_dropped_below_m_min`, and the wd50k66 audit explanation asserts that
"`n_records + n_dropped_below_m_min` reproduces the published count". That
arithmetic is therefore not checkable from the frozen artifact.

Add the field in `freeze_corpora.py::observed` and re-freeze. **Not during a
running campaign** — re-freezing rewrites the corpus directory that live
analyses read.

Until the field exists the WD50K sentence says "3,988 of 3,994 in-envelope
members; 6 fall below the fact floor of 3" and does **not** claim the
arithmetic is reproduced from the artifact.

What *is* verifiable cross-checks exactly: `n_dropped_over_arity_cap = 14` for
wd50k66 matches the supplement's "14 dropped for a statement of arity above the
alphabet cap".

## 2. Prose — three obligations for the data section

**(a) NDC-classes: state both exclusion rules and both counts.** The supplement
gives 1,432 members; the built corpus has **1,381**. Two rules remove the
difference, and the larger exclusion is not mentioned in the supplement at all:

- *Singleton products are not facts.* A fact has arity ≥ 2 by definition
  (DESIGN G2), so a single-product entry is not a hyperedge; members left with
  fewer than `m_min = 3` facts leave the collection. This accounts for the −51
  and propagates consistently through every derived count (consecutive pairs
  555 → 528, Δ=1 120 → 117, constant-preserving pairs 140 → 128, runs ≥ 3
  45 → 42).
- *The arity cap.* **519 members** are dropped for containing a fact of arity
  above `k_max = 10`. This is an order of magnitude larger than the 51 and the
  supplement is silent on it. It is an exclusion the *alphabet* imposes, and a
  scope claim that does not state it overstates the corpus.

**(b) WD50K(66): both numbers, and which one the claims are over.** 3,988
members in the envelope, of which **3,162 are n-ary** (at least one fact of
arity ≥ 3) and **826 purely binary**. Every RQ1 claim is over the 3,988. The
premise sentence — facts of arity three and above are what make the object a
hypergraph — must not read as a corpus filter, because it is not one.

**(c) The arity histogram must name its denominator.** The supplement's NDC
passage gives "66.9 % of in-envelope hyperedges have arity ≥ 3 (4,548 of arity
3, 3,787 of 4, 3,960 of 5, 6,393 of 6–10)" — about 18,700 facts of arity ≥ 3,
implying ~27,900 hyperedges. The built corpus has **5,092 facts in total**
across 1,381 members (mean `m` = 3.687, median 3). The two reconcile only if
that histogram is over the **22,892 in-envelope class-quarters** the same
section names, not over the 1,432 encodable members. As written a reader
attaches those counts to the members and infers a corpus 3.7× denser than the
one measured. Print the denominator, and print the built corpus's own fact
count beside it.

This quantity is not among the 13 audited, which is why nothing caught it —
consider adding the fact total and the per-member median to `EXPECTED`.

## Acceptance

`census.json` carries `n_dropped_below_m_min`; the data section states, for each
corpus, the built member count, every exclusion rule with its count, and the
denominator of every ratio it prints; no sentence claims an arithmetic
reconciliation that the census cannot supply.
