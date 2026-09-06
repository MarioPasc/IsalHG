# The Isal instruction string as the paper's representation — answers to the PI

*2026-09-06. The PI ruled that the paper must use the instruction string of
the Isal family, and asked three questions. Every number below is measured
(campaign tables under `results/IEEETKDE/`, or the two probes named in §4).
Companion documents: `ENCODINGS_WORKED_EXAMPLE.md` (what the three encodings
look like on one record) and `RESULTS_AUDIT_2026-09-06.md`.*

## 1. "Why is the canonical fact-rank needed for the Isal representation to be correct?"

It is not needed. The Isal canonical string `w*_c` is a complete isomorphism
invariant on its own (Theorem A, tie-complete variant), and its encoder
(`core/canonical.py`, `H2S`, the C++ engine) never calls nauty and never uses
a rank: verified in the source, and verified on a record (renaming the
constants of `Q1002100` leaves `w*_c` unchanged with no rank involved). The
Isal alphabet does not name constants at all; it reaches them by moving
pointers, which is exactly why it is invariant under renaming.

The rank exists only because the *fact-list* alphabet adopted on 2026-09-04
has no pointers: an `F` token must say which constants a fact is over, and
saying so by name would break invariance, so a structural address was
required, and nauty's canonical labelling supplied it. That alphabet is not
an Isal representation. Under the ruling it stops being ours; it can remain
in the paper as one more serialisation to compare against (with the nauty
certificate), or be dropped.

The only Isal-compatible use of an external order is the design in §3(d):
emit the Isal program in nauty's constant order instead of searching for the
lex-min walk. That keeps the CDLL, the alphabet and `S2H`, and trades the
family's canonical *algorithm* for a borrowed order. It is optional and
needs the PI's word on whether "the instruction string of the family" means
the family's language or the family's canonical algorithm.

## 2. "Is locality the only thing keeping the Isal representation from being perfect?"

No. The inventory, with the measured numbers:

| property | Isal `w*_c` | status |
|---|---|---|
| exactness (word equality ⇔ isomorphism) | Theorem A; fingerprint `(seed label, w*_c)` on labelled inputs | **fine**, our own theorem |
| closed language, total decoder | `S2H` decodes every string, always to a *connected* hypergraph | **fine, stronger than the fact list** (whose alignment interiors are connected only 68.6 % of the time) |
| local stability under one edit | normalised response 0.49–0.79 vs 0.16–0.23 (fact list) when the constant set is preserved; within two tokens 0.03–0.86 vs 0.59–0.85 | **the first real limit**; mechanism: the canonical string is the lex-min over walks, and an edit changes the seed and the ties, so the walk is rewritten (the avalanche measured at T-M4b: 30–50 % of the string per edit on unanchored substrates). Intrinsic to lex-min-over-walk canonical forms, not a bug |
| cost and coverage | C++ engine, 60 s process budget (already the campaign setting): censored on 5.7 % of WD50K members, 12.3 % of NDC classes; 39.5 % of the RQ7 sweep; every instance above ~120 facts | **the second real limit, and it is symmetry, not size** (table below) |
| isolated constants | not representable: every non-initial node is created inside an edge | domain restriction to state; the fact list allowed them, RQ3's deletion variants produce them |
| argument roles / direction | not carried (facts are sets) | shared with the fact list (whose roles variant is not even invariant); future work |
| alphabet scoping | one `k` per collection; distances not comparable across `k` | already the design |
| identity speed vs nauty | orders of magnitude slower | conceded in the introduction, not a correctness matter |

**Cost is a symmetry problem.** Joining the RQ1 cost rows (C++ engine, 60 s)
with the automorphism group of each member's Levi graph, on WD50K:

| fact count | members | censored, `\|Aut\| < 10³` | censored, `\|Aut\| ≥ 10³` | median s (completed) |
|---|---|---|---|---|
| ≤ 8 | 3,297 | 0.00 | 0.15 | 0.004 |
| 9–12 | 447 | 0.02 | 0.53 | 0.35 |
| 13–16 | 187 | 0.24 | 0.68 | 1.7 |
| 17–20 | 46 | 0.28 | 0.86 | 2.6 |
| > 20 | 11 | 0.25 | 1.00 | 28 |

By symmetry alone: censored 0.00 at `|Aut| ≤ 10`, 0.09 at 10², 0.41–0.48
at 10³–10⁶, 0.72 at 10⁷, 1.00 at ≥ 10⁸. Real knowledge bases are symmetric
by nature: a film with five interchangeable cast members, a drug class with
twenty interchangeable products. The tie-complete search branches as
`(j!)^E` over those symmetries; the C++ log names the only value-preserving
fix, stabiliser-orbit pruning (Prop. 6.0 of the completeness proof), as the
open research item — it is not implemented.

So: exactness and the language are fine; locality and symmetric-input cost
are the two limits; isolated constants and roles are representational
restrictions to state.

## 3. "Raise the time-out to 60 s and make sure the C++ engine is used"

Both were already the case. `experiments/tkde/configs/rq{1,2,7}.yaml` set
`pointer_budget_s: 60.0`; the arm calls
`canonical_string(H, algorithm="canonical")`, whose backend defaults to
`"cpp"`; the budget is enforced by a forked child killed at 60 s. Every
censoring figure above is at that setting.

What each option would buy:

- **(a) A 600 s budget on the censored tail only.** Helps the low-symmetry
  size tail (medians 1.7–28 s at 13–24 facts), not the symmetric tail, whose
  branching is exponential. Cost: the censored members are ~6–12 % of the
  corpora, ≈ 500 members × 600 s ≈ 80 core-hours on Picasso. Worth doing as
  the first step: it measures exactly what budget buys.
- **(b) Stabiliser-orbit pruning in the C++ engine.** The principled fix for
  symmetric inputs, value-preserving by the proof. Research work, not a
  constant factor; not a two-week item.
- **(c) Restrict the corpora to the computable region and state it.** The
  campaign already reports yield per size bucket; the article would carry
  the Isal arm inside its envelope with the tail censored and declared.
- **(d) The Isal program in nauty's order.** No canonical search: constants
  enter through `V` in rank order, facts in rank-tuple order through `V` or
  `C`, pointers moved with `P`/`N`. Isal syntax, Isal decoder, completeness
  immediate, cost in microseconds, locality expected between the fact list
  and `w*_c` (a few tokens per edit — to be measured, not assumed). The
  canonical order is borrowed, so it must be presented as "an Isal word
  over a canonical labelling", and the PI must accept that trade.

## 4. Proposed next step (no re-run of the whole campaign yet)

Run RQ1 only, with the Isal arms side by side: `w*_c` at 60 s and at 600 s
on its censored tail, the Isal program in nauty's order (d), and the fact
list and the nauty certificate as the non-Isal serialisations. That one
table gives the PI exactness, locality, coverage and cost for every option
on the same records, and the primary representation is chosen from it. The
rest of the campaign is an encoder swap once that choice is made: the
corpora, competitors, questions, statistics harness, consensus (fact-level,
decoder-agnostic), generator and envelope sweep are unchanged.

Expect, honestly: RQ2 exactness and RQ7 speed under (d) are nauty's again;
RQ3 and RQ6 carry over under any Isal arm; RQ4 and RQ5 stay negative under
any canonical-string metric, because the nauty certificate already behaves
like the fact list on them.

Probes: `scripts/diagnostics/pointer_timeout_symmetry_probe.py` (the
symmetry table), `scripts/diagnostics/encodings_worked_example.py` (the
three encodings on one record).
