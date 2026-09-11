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

Measured on `wd50k66`, 400 identical members, same machine:

| | matrix secs |
|---|---|
| `nauty_cert_rows.matrix()` as shipped | 0.104 |
| the same fingerprints via `process.cdist` | **0.005** |
| `isal_ow_struct.matrix()` | 0.024 |

**A 20× implementation penalty**, and it inverts the comparison: as shipped the
walk looks 4.3× faster than the row-tokenised certificate; like-for-like the
certificate is **4.5× faster than the walk** (rows/walk = 0.22×).

## Why it matters beyond a benchmark

D-ART4 designates `nauty_cert_rows` as the **non-confounded** certificate
comparator — the bytes serialisation is a finer granularity than the
representation's own symbols, so the row tokenisation is the one meant to carry
any comparison. That comparator is the one with the slow matrix, so **the
designated-fair arm is the one being timed unfairly**, in the direction that
flatters us.

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
