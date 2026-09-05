# ngram-cache — bound the `TokenNGram` distribution memo

**Agent** `ngram-cache` · **Wave** `2026-09-05-tkde-w3` · **Orchestrator** `main`
**Worktree** `/home/mpascual/research/code/IsalHG/.claude/worktrees/agent-a3554e620c7eb2d0d`
**BASE_SHA** `21da071e9cc7333fbb61550fc690c644c3fa2893`
**Env** `~/.conda/envs/isalhg-ngram` (cloned from `isalhg`, `pip install -e ".[dev]"` inside
this worktree; `isalhg.__file__` resolves to the worktree's `src/`, so the editable install
is correctly re-pinned)
**Opened** 2026-09-05 23:47 CEST

## Understanding

`TokenNGram` expands the Kneser-Ney recursion once into a dense `float64` vector over the
whole vocabulary, per sampling context, and memoises that vector. The memo is the right
idea — a sampler revisits contexts constantly, and `_sample_one` would otherwise rebuild
the same array for every emitted token. What was wrong is only its *size policy*: the memo
was a plain `dict`, unbounded, and cleared only inside `fit()`.

The memo is a pure cache of a deterministic function of the context. Nothing downstream
mutates a returned row (`_sample_one` reads it through `np.cumsum`; `logprob` indexes it),
so an entry may be dropped and recomputed at any time without changing a single sampled or
scored value. That is what makes an LRU the correct fix rather than a behaviour change.

## Root cause

`_distribution` (pre-fix line ~276) stored one dense vector per distinct context in
`self._cache`, with no eviction. Measured on Picasso, job 2213221, RQ6 on `wd50k66`,
10,000 samples per unit:

- **+2.7 GB RSS per unit**, 19,980 MB after 7 units, **OUT_OF_MEMORY at 20.4 GB**.
- `tracemalloc` attributed **731 of 733 MB per unit** to that single line.

Cross-check of that 731 MB against the measured vocabulary: `wd50k66` fact words fit
`|V| = 8,489`, so one row costs `8,489 × 8 = 67,912` bytes, and `731 × 10⁶ / 67,912 ≈ 10,800`
distinct contexts per 10,000-sample unit. The leak is not pathological — it is simply that a
long-lived sampler keeps finding new contexts, one per ~2.6 emitted tokens.

The RQ6 runner worked around this by refitting the model per unit (`CollectionContext.model`,
`experiments/tkde/rq6.py`), which is out of my ownership and left untouched. The library
defect remained for any long-lived sampler.

## Measured vocabulary sizes (the input to the default)

Fitted `TokenNGram(order=3)` vocabularies over every frozen TKDE collection, both arms,
read from `/media/mpascual/Sandisk2TB/.../results/IEEETKDE/corpora`:

| collection | members | \|V\| fact | \|V\| flat |
|---|---:|---:|---:|
| ndc_classes | 1381 | 1074 | 52 |
| ndc_substances | 1745 | 2311 | 51 |
| synthetic_rq1 | 2000 | 3681 | 36 |
| wd50k100 | 1837 | 4912 | 177 |
| wd50k66 | 3988 | 8489 | 338 |
| **wd50k66_full** | 4554 | **21263** | 827 |

## Per-entry size arithmetic and the default

One memo entry is one dense `float64` row over the vocabulary, so it costs `8 · |V|` bytes.

- Largest frozen vocabulary: `wd50k66_full` fact words, `|V| = 21,263`.
- Per entry: `21,263 × 8 = 170,104` B ≈ **166.1 KiB**.
- Budget: **256 MiB** = `268,435,456` B → `268,435,456 / 170,104 ≈ 1,578` entries.
- **`DEFAULT_CACHE_SIZE = 1024`** (round, comfortably inside the budget):
  `1024 × 170,104 = 174,186,496` B ≈ **166.1 MiB** < 256 MiB. ✔
- On the collection that actually OOM'd, `wd50k66` (`|V| = 8,489`):
  `1024 × 67,912 = 69,541,888` B ≈ **69.5 MB**, against the 731 MB the unbounded memo
  accumulated in one unit. Well under the 1 GB the mission asked for, even allowing the
  ~3.7× allocator-fragmentation factor implied by 731 MB tracemalloc vs 2.7 GB RSS.

Performance note: eviction adds recomputation, not an order of growth. `_sample_one`
already pays an `O(|V|)` `np.cumsum` for *every* emitted token regardless of whether the
row was cached, so a miss adds one `np.zeros(|V|)` plus a handful of scatter-adds on top of
work that was already `O(|V|)`. The bound costs a constant factor, not a complexity class.

## Changes

`src/isalhg/generation/ngram.py` (the only source file touched):

- `DEFAULT_CACHE_SIZE: int = 1024`, module-level, with the arithmetic above in a comment
  and in the `cache_size` parameter docstring. Added to `__all__`.
- `TokenNGram.__init__` takes `cache_size: int | None = DEFAULT_CACHE_SIZE`. `None` means
  unbounded (the historical behaviour, now opt-in). Below 1 raises `GenerationError` — the
  invariant is that the row just computed is always retained.
- `self._cache` is an `OrderedDict`. `_distribution` calls `move_to_end` on a hit and, after
  a store, evicts with `popitem(last=False)` until `len(self._cache) <= self.cache_size`.
  Explicit LRU, as instructed: `functools.lru_cache` is unusable here (method with array
  values, and no way to inspect or reset the footprint).
- Public `reset_cache()`; `fit()` now calls it instead of rebinding a bare `dict`.
- Module docstring gained a paragraph stating the bound, the `8·|V|` per-entry cost, the
  measured 731 MB / 20.4 GB incident, and — the load-bearing point — that eviction cannot
  change a sampled sequence because the memo caches a deterministic function of the context.

Deliberately *not* re-exported from `src/isalhg/generation/__init__.py`: that file is
outside my ownership.

## Tests

`tests/unit/generation/test_ngram.py`, new `TestDistributionCache` (11 tests) plus a
`_wide_words` fixture builder (3,000 symbols, each seen exactly once, so almost every
order-3 context is distinct and the sampler pressures the cache immediately):

| requirement | test |
|---|---|
| (a) identical samples across cache sizes | `test_samples_are_identical_across_cache_sizes[None/1/7/1024]` — 200 samples, seed 11, token-for-token equality against the `cache_size=None` reference |
| (a) extended to scoring | `test_logprobs_are_identical_across_cache_sizes[None/1/1024]` — exact float equality on 20 words |
| (b) `len(_cache) <= cache_size` | `test_the_cache_never_exceeds_its_bound` (+ `test_an_unbounded_cache_grows_past_that_bound`, which pins the defect so the bound test cannot pass vacuously) |
| (c) `reset_cache()` | `test_reset_cache_empties_it_and_sampling_is_unchanged`, `test_reset_cache_before_any_use_is_harmless`, `test_fit_resets_the_cache` |
| (d) byte footprint | `test_the_byte_footprint_stays_under_the_bound_over_many_samples` — 5,000 samples, `|V| = 3,001`, `cache_size=32`, asserts `sum(row.nbytes) <= 32 × 3001 × 8` |
| validation | `test_rejects_a_cache_size_below_one[0/-1]` |

**Non-vacuity, measured** (`scratchpad/cache_probe.py`, same corpus and seed as test (d),
5,000 samples, 27,783 emitted tokens, mean word length 5.56):

| cache_size | entries | bytes |
|---|---:|---:|
| 32 | 32 | 768,256 |
| None | 18,766 | 450,534,128 |

That is the RQ6 leak reproduced in a unit test: **586× smaller resident memo**, identical
samples.

## Verification (verbatim)

```
$ ~/.conda/envs/isalhg-ngram/bin/python -m pytest tests/unit/generation/ -q --no-header
============================= 117 passed in 1.02s ==============================

$ ~/.conda/envs/isalhg-ngram/bin/python -m pytest tests/experiments_tkde/test_rq36_smoke.py -q --no-header
============================= 54 passed in 11.46s ==============================

$ ~/.conda/envs/isalhg-ngram/bin/python -m ruff check src/isalhg/generation/ngram.py tests/unit/generation/test_ngram.py
All checks passed!

$ ~/.conda/envs/isalhg-ngram/bin/python -m ruff format --check src/isalhg/generation/ngram.py tests/unit/generation/test_ngram.py
2 files already formatted

$ ~/.conda/envs/isalhg-ngram/bin/python -m mypy src/isalhg/generation/
Success: no issues found in 5 source files
```

mypy reports zero findings, so there are no new ones.

## Deliberately not done

- **`experiments/tkde/rq6.py` left untouched.** Its `CollectionContext.model` docstring now
  describes the defect as live ("a cache that is unbounded and reset only by `fit`") and
  justifies refitting per unit on that basis. With the bound in place that justification is
  stale, and the per-unit refit is now a redundant 0.15 s. It is still *correct* — refitting
  changes no result — so nothing is broken, but the orchestrator may want a follow-up to
  either update the docstring or drop the workaround. `experiments/**` is outside my
  ownership, so I did not touch it.
- **`src/isalhg/generation/__init__.py` not updated** to re-export `DEFAULT_CACHE_SIZE`.
  Outside ownership; tests import from `isalhg.generation.ngram` directly.
- No change to the smoothing, the unrolled distribution, the sampler, or `max_len`.

## Risks

- **Behavioural risk: none identified.** Eviction recomputes an identical vector; this is
  pinned by the four `cache_size` values in test (a) and by exact-float `logprob` equality.
  The one way it could bite is if a caller mutated a row returned by `_distribution` in
  place and relied on the mutation persisting — no such caller exists in the repo
  (`_sample_one` and `logprob` are the only consumers, both read-only), and such a caller
  was already broken under `fit()`'s reset.
- **Performance risk: bounded and small.** On a working set larger than 1024 contexts the
  hit rate drops; the added cost is one `np.zeros(|V|)` + scatter-adds per miss, on top of
  the `O(|V|)` `cumsum` the sampler already pays per token. Not measured on the real RQ6
  workload (Picasso, out of scope for this agent) — flagged for the orchestrator in case the
  wave wants a wall-clock check before the next submission.
- **Default is a policy choice.** 1024 is sized for the largest *frozen* vocabulary. A future
  collection with `|V| ≫ 21,263` would push the memo past 256 MiB at the same entry count;
  the docstring states the `8·|V|` arithmetic so the number can be re-derived rather than
  guessed.
