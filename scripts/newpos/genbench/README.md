# genbench -- generation benchmark on the usable samples

Scores the samples a user could keep (decoded, connected, at least one fact) of a hypergraph
generator against its collection: yield (valid-unique-novel per draw) and distributional fidelity.
Reads the frozen JSONL sample format, so it works for any generator, n-gram or neural.

## Files

| File | Role |
|---|---|
| `common.py` | frozen-format I/O, structure predicates (connected, star, shared), LCC repair, iso key (`ordered_fingerprint`), `SampleSet` (the five RQ6 histograms), JSD/W1 |
| `sample_ngram.py` | samples the three RQ6 n-gram generators (`ow_ngram`, `fact_ngram`, `incidence_ngram`) exactly as `experiments/tkde/rq6.py::run_sample_unit` does and writes frozen-format files |
| `evaluate.py` | scores a directory of sample files against a collection; writes `rows/`, `arrays/`, `units.csv`, `collections.json` (own values + noise floors) |
| `analyze.py` | tables and tests: BCa CIs, matched-count fidelity tests, Holm-corrected one-sided paired Wilcoxon, bias direction, RQ6 reproduction -> `tables.md`, `stats.json` |
| `fig_rejection_bias.py` | one PDF: m of usable samples, star fraction, usable/VUN yield per 10,000 draws |
| `run_all.sh` | the whole 27-seed pipeline |

## Frozen sample format

One file per unit, `<collection>__<generator>__s<seed>.jsonl[.gz]`, one JSON object per draw with keys
`collection, generator, seed, draw, tokens, root_type, status, reason, n, types, facts, connected`
(`status` is `decoded` or `rejected`; `n/types/facts` are the decoded KB with constants `0..n-1`,
`facts = [[pred, [arg, ...]], ...]`, null when rejected). The `connected` flag is audited, not trusted:
connectivity, star and the isomorphism key are recomputed from `n/types/facts`.

## Usage

```bash
PY=~/.conda/envs/isalhg/bin/python
$PY scripts/newpos/genbench/evaluate.py --samples DIR --collection wd50k66 --collection ndc_classes \
    --out SCORES [--generator NAME ...] [--seeds a,b,c | --n-seeds k] \
    [--repair-lcc-of FACT_GENERATOR [--write-repaired DIR]] [--workers 6]
$PY scripts/newpos/genbench/analyze.py --eval SCORES --out OUT --ours OW_GENERATOR \
    --baselines FACT,FACT_lcc,INCIDENCE [--rq6-rows '']
$PY scripts/newpos/genbench/fig_rejection_bias.py --eval SCORES --out OUT/fig.pdf --arms OW,FACT,FACT_lcc,INCIDENCE
bash scripts/newpos/genbench/run_all.sh          # the n-gram campaign, results under RESULTS=...
```

At most 6 worker processes are used (`--workers` is capped). Pass `--rq6-rows ''` to `analyze.py` for
non-n-gram generators (the reproduction check only applies to the RQ6 arms).

## Definitions (pre-registered)

- usable = decoded AND connected (RQ6's `SparseHypergraph.is_connected`) AND `m >= 1`.
- iso class = `ordered_fingerprint(H)` of the sample's own decoded hypergraph, for every arm.
- VUN per draw = distinct usable iso classes absent from the collection / draws (singleton reading kept as a column).
- star: one constant occurs in every fact and no other constant occurs in two facts; otherwise relational.
- LCC repair (`<generator>_lcc`): keep the component with the most constants (ties: more facts, then lowest `(root type, w°)`).
- Fidelity needs `u >= 100` usable samples on a seed. Primary fidelity tests compare at equal numbers of usable samples
  (the ordered-walk arm subsampled to the baseline's `u`, 20 seeded repeats averaged); unmatched tests are secondary.
- The post-hoc table (usable samples inside the collections' size envelope `n <= 24, 3 <= m <= 110, arity <= 10`) is a diagnostic, not a test.
