# Real-data corpus — broadening the weak anchor

**Status:** planning note (not yet a ledger task). Addresses the "synthetic-scale
claims" soft spot for an applied venue.

**The hard constraint** that killed the HIC IMDB anchor: the paper needs a
corpus of **many small, connected hypergraphs, each with a whole-hypergraph
label, all within the arity cap `k ≤ 10`, and cheap enough for tie-complete
`w*_c`.** IMDB failed on arity (corpus-level `k = 110`) and on near-symmetric
`w*_c` blow-ups; the feasible subset censored *by structural symmetry*, which
correlates with the labels. So the corpus must be filtered *for* the constraint
from the start, and the censoring must be **label-independent**.

---

## Candidate sources, ranked by fit

### 1. Combinatorial designs catalog — best fit, already half-vendored

You already ship the STS catalog (orders 3–15, 85 iso-classes,
`datasets/synthetic/sts_catalog.py`) and design fixtures (Fano, STS(9), cyclic
C13, GQ(2,2)). Extend to a **labeled** corpus: small BIBDs / Steiner systems /
packing designs grouped by design *type* (parameter family `(v, k, λ)`) as the
class label.

- **Pros:** bounded arity by construction; connected; `w*_c` is *proven
  computable* on exactly these objects (they are the Theorem-A regression pins);
  fully reproducible; directly exercises the completeness claim.
- **Cons:** semi-synthetic — real mathematical objects, not real-world networks.
  Honest, but not "real-world data" in the applied-venue sense.
- **Verdict:** the one corpus you can *guarantee* passes the feasibility gate.
  Use it as the bulletproof real anchor.

### 2. Low-arity molecular / reaction hypergraphs — the real-world exhibit

Chemical reaction networks (each reaction = a hyperedge over reactants/products)
and small-molecule hypergraphs have naturally low arity. A corpus of small
molecules or reaction motifs labeled by class (reaction type, molecule family)
fits the mold.

- **Where to look:** the existing `datasets/arb_benson.py` (ARB / Benson
  loaders) and XGI-DATA for low-arity subsets; cheminformatics reaction sets.
- **Pros:** genuinely real-world; low arity is intrinsic, not imposed.
- **Cons:** must confirm the arity distribution and `w*_c` cost *before*
  building the pipeline — do not repeat the HIC sink cost.
- **Verdict:** the intended "real-world networks" exhibit, **gate-first**.

### 3. Ego-hypergraphs sampled from a large real hypergraph — fallback only

Sample `k`-hop ego-nets around vertices of a real hypergraph (email, contact,
coauthorship), each labeled by the ego's category — manufacturing the
"many small labeled hypergraphs" structure from one real network.

- **Cons / risk:** you must cap arity and reject symmetric blow-ups, and
  **disclose the sampling**. The same symmetry-censoring-correlates-with-label
  failure that sank HIC is a live risk here.
- **Verdict:** only if (1) and (2) are insufficient, and only after the gate.

---

## Selection protocol — run before committing to any corpus

Replicate the T-DQ3′ / DQ1′ feasibility gate for each candidate:

1. **Arity distribution vs cap.** Fraction of instances with `max arity ≤ 10`
   (and corpus-level `k`). Reject if the cap discards a large share.
2. **`w*_c` wall-clock** at p50 / p90 under a fixed per-instance budget
   (e.g. 10 s). Report completion fraction.
3. **Yield after the arity + time filter.** Reject below ~85%.
4. **Label-independence of the censoring** — the exact test HIC failed. Compare
   the per-class retention rates; if censoring correlates with the label
   (retention varies sharply by class), the corpus is contaminated and cannot
   rank representations. **This is the decisive test.**

**Promotion rule:** only a corpus that clears **≥ 85% yield with
label-independent censoring** becomes a measured anchor. Anything below is
reported (if at all) as an explicitly censored secondary exhibit, as HIC now is.

---

## Recommendation

- **Ship (1) the designs catalog as a genuinely-computable real anchor** — it is
  guaranteed to pass the gate and it doubles as a completeness-claim
  demonstration.
- **Attempt (2) a low-arity molecular / reaction corpus** as the real-world
  exhibit, **gate-first** — build the A1/A2/A3 pipeline only after the
  feasibility gate clears.

Together these replace the single censored IMDB exhibit with one bulletproof
real corpus + one real-world corpus, materially strengthening the applied claim
without re-incurring the HIC feasibility sink.

## Recommended ledger framing

Two tasks:
- **Corpus-1 (designs catalog labeling):** loader + label scheme on already-
  vendored data; low risk, low cost; reuses the T-M5b/c/d pipelines.
- **Corpus-2 (molecular/reaction), gate-first:** a feasibility-gate task
  (steps 1–4 above) that *gates* a downstream pipeline task; do not open the
  pipeline task until the gate returns GO.

Acceptance check: at least one real corpus passing the ≥85% / label-independent
gate, run through A1/A2/A3 with the stats pass applied, replacing "synthetic-
scale claims" with a real-data claim in `empirical/applications.md`.
