# T-KBy — `nauty_cert_rows.matrix()` is a Python double loop, so every timing against it is 20× inflated
**Declared:** 2026-09-11 03:43 CEST
**Status:** OPEN
**Delegation:** agent
**Why out of scope:** found while checking whether RQ7's certificate multiplier
was a tokenisation artefact. It is a defect in a competitor arm's matrix path,
affecting every RQ that times it — not part of reading RQ7.

**Context to read first:**
- `src/isalhg/metric_space/representations/nauty_levi_edit.py` — `NautyCertRowsDistance.matrix()`
- `src/isalhg/metric_space/toolkit/matrix.py` — `_build_from_fingerprints`, `WORD_ARMS`
- `docs/article/DEVELOPMENT/DECISIONS.md` D-ART4 (the two-tokenisations requirement)
- `docs/article/D_ART3/foundation/lessons.md` L17

## The defect

`_build_from_fingerprints` calls each distance's own `matrix()`. Two of the three
canonical-string arms call `rapidfuzz.process.cdist` (C++, vectorised over the
whole table); **`nauty_cert_rows` fills the upper triangle in a Python loop**,
one `Levenshtein.distance` call per pair.

| arm | `matrix()` implementation |
|---|---|
| `isal_ow_struct` | `process.cdist` |
| `nauty_cert` | `process.cdist` |
| **`nauty_cert_rows`** | **Python double loop** |

Measured on `wd50k66`, 400 identical members, same machine, min of 3 reps:

| | secs | s/pair |
|---|---|---|
| `nauty_cert_rows.matrix()` as shipped | 0.0561 | 3.51e-07 |
| the same fingerprints via bare `cdist` | **0.0052** | 3.25e-08 |
| `isal_ow_struct.matrix()` | 0.0236 | 1.47e-07 |
| `isal_ow_struct` via bare `cdist` | 0.0044 | 2.73e-08 |

**A 10.8× penalty** on the rows arm relative to a bare `cdist` over its own
fingerprints, against the walk's 5.4×. As shipped the rows arm is **2.38×** the
walk; at equal implementation the two are **at parity** (1.19× via bare `cdist`;
1.09× in the wider tokenisation sweep).

**It does not invert the comparison.** A first draft of this task said
like-for-like the certificate is "4.5× faster than the walk" — that came from
comparing a bare `cdist` on precomputed row fingerprints against a full
`matrix()` call on the walk, which are different operations. `[IsalHG-Fable]`
caught it. The defect is real and worth fixing; the reversal was an artefact of
the comparison, and **parity is the finding**.

**A third finding, now accounted for.** `matrix()` costs 5.40× a bare `cdist`
for the walk. A first draft attributed that to "corpus `k` resolution, the
augment flag, word recomputation"; `[IsalHG-Fable]` objected that recomputation
could not fit, since the campaign's yield puts a member's canonicalisation at
0.600 ms and 400 of those would be 0.24 s against a whole `matrix()` call of
0.0236 s.

**Both of us were wrong, and for this thread's own reason: that argument compares
a *cluster* per-member cost against a *local* matrix timing.** On this machine
canonicalisation is **0.045 ms/member**, not 0.600 — a 13× machine difference
(Xeon Gold 6230R against a local workstation) — so 400 fingerprints cost 0.018 s
and fit inside the call comfortably. Measured, 400 members, min of 3:

| arm | fingerprints | bare `cdist` | sum | `matrix()` | accounted |
|---|---|---|---|---|---|
| `isal_ow_struct` | 0.0178 | 0.0060 | 0.0238 | 0.0233 | **101.9 %** |
| `nauty_cert_rows` | 0.0092 | 0.0067 | 0.0160 | 0.0555 | **28.7 %** |

So the walk's `matrix()` **is** fingerprints + the pairwise table, accounted to
within 2 %, and there is no unexplained wrapper overhead to chase: the
"overhead" is the canonicalisation, which any honest whole-matrix timing must
include. Word recomputation was the right attribution after all — it was
excluded by an argument that mixed two machines.

The rows arm is the one with a real gap: **28.7 % accounted**, leaving 0.0395 s
unexplained by fingerprints plus a `cdist` it never calls. That residual **is**
the Python loop — ~0.5 µs per pair over 80,000 pairs — which is this task's
subject. Note this also disposes of the "per-call setup" reading: rows
fingerprinting is *cheaper* than the walk's (0.0092 against 0.0178), so a larger
multiple cannot come from fingerprint cost scaling.

**Do not compare local micro-timings against campaign figures.** The 13× machine
gap above is the reason; every number in `rq7_envelope_facts.md` is from the
cluster, and the timings in this task are local and used only in ratios where
both sides are local.



## Why it matters beyond a benchmark

D-ART4 designates `nauty_cert_rows` as the **non-confounded** certificate
comparator — the bytes serialisation is a finer granularity than the
representation's own symbols, so the row tokenisation is the one meant to carry
any comparison. That comparator is the one with the slow matrix, so **the
designated-fair arm is the one being timed unfairly**, in the direction that
flatters us — by 2.38× as shipped, against a true parity.

Any published cost comparison against `nauty_cert_rows` is invalid until this is
fixed. RQ7's has been struck (T-KBf, `rq7_envelope_facts.md` §8); **RQ1, RQ2 and
RQ5 also run this arm** and must be checked for the same exposure.

L17 is the standing rule this violates: *"concede identity and deduplication
speed to nauty/bliss/Traces … never build a claim on canonicalization speed."*
The claim drifted in anyway, and the defect made it look supported.

## Acceptance

1. **Replace the loop with `process.cdist`** over the row fingerprints, matching
   the other two arms. The fingerprints are already tuples of tuples, which
   `cdist` accepts — measured working at 0.005 s for n=400.
2. **Confirm the values are unchanged**, not just the timing: the matrix must be
   identical element-wise to the loop's, since only the driver changes. Pin it
   with a regression test comparing both paths on a small corpus.
3. **Re-check every RQ that times this arm** (RQ1, RQ2, RQ5, RQ7) and restate or
   strike any cost comparison that used it. Values-based results (distances,
   ARI, AUC) are unaffected — this is a timing defect only, which is worth
   stating explicitly so nobody re-runs the science.
4. **Audit the remaining arms for the same asymmetry**: any arm whose `matrix()`
   loops in Python while its competitors vectorise is being timed unfairly, and
   the direction of that unfairness is not always toward us.

**Out of scope:** the tokenisation question itself (D-ART4 settles it); the
`wstar_orbit` comparison, which is walk-against-search in one tokenisation on one
code path and is unaffected.
