# F4 topology probe — does a fact-addressed encoding make similar knowledge bases close?

2026-09-04. Decisive probe for the alphabet change (`logic_models/encoding.md` §3.1, absolute
vs relative addressing), against one criterion: **knowledge bases one fact apart must be at
small Levenshtein distance**. Everything lives in this directory; no repository file outside it
was touched.

## 1. Design as implemented

A knowledge base `K` is a labelled hypergraph — constants are vertices with a type label, facts
are hyperedges with a predicate label and are sets of constants (`f4_encodings.KB`). All
distances are unweighted Levenshtein over atomic symbols (rapidfuzz): one token = one symbol,
equality is equality of the whole `(kind, label, tuple)` triple.

**E-A — status quo.** `canonical_string(H, k, algorithm="canonical", backend="cpp")`; distance
over `instructions.parse(w*_c)` with the `("seed", label)` prefix when the vertex vocabulary is
non-trivial, mirroring `metric_space/distances/isalhg_levenshtein.py`; `k` = pair max of
`required_k`. **E-B — F4, global canonical ranks.** `pynauty.canon_label` on the coloured Levi
graph (`core/levi_reduction.to_levi`: vertex colour = type, edge colour = `|Σ_v| + predicate`),
restricted to the constant-side nodes in canonical order; `rank[v]` is `v`'s position there.
Word = type prefix `T[type(π⁻¹(r))]`, `r = 0 … n−1`, then one `F[ℓ; r_1 < … < r_a]` per fact,
fact tokens sorted by `(ℓ, rank tuple)`. `canon_label` returns a permutation, so there were no
residual ties to break. **E-C — F4, local addresses.** `addr[v] = (wl_hash(H,
max_rounds=3)[v], index)`, the index ordering same-coloured constants by their E-B rank. Word =
type prefix in increasing address order, then `F[ℓ; (col,idx)_1 … (col,idx)_a]`, operands sorted
by address, fact tokens sorted lexicographically.

**Choices the specification left open — all of them.** (1) *E-C type prefix* = `T[(col,idx); type]`, address inside the token: in E-B the
key is the rank and position carries it, and an address-keyed prefix is what makes E-C demonstrably complete (a degree-0 constant is
otherwise unrecoverable). (2) *WL depth `h = 3`* = `max_rounds=3` (`core/hypergraph_wl`, C++); colours are raw FNV-1a values, not ranks
among those present, so an address means the same thing in two different KBs. (3) *Normalizer* = `d / |w(base)|`. (4) *Deletions*: a
knowledge base *is* its set of facts, so `delete_fact` / `remove_constant` drop now-isolated constants and renumber
(`f4_corpora.compact`); edits with a disconnected result are rejected and resampled, since `canonical_string` rejects disconnected input
and all arms must see identical instances. (5) *Edit budget*: "up to 10 edits per KB" read as up to 10 **per edit kind**, ≤ 50 per base
KB. (6) *Labels*: NDC types = 4 values (`[epc]`, `[moa]`, `[pe]`, untyped), ids from sorting those names, one predicate; WD50K(66)
predicate = `s.relation` (unfolded, as `probe_hyperrel.star_spec`), constants untyped. (7) *WD50K ladders (M2)*: no natural series
exists, so ladders are synthetic **constant-set-preserving** fact insert/delete walks, `t = 1…5` — fixing the constant ids makes
`Δ = |F_0 △ F_t|` exact, as the named ARB node ids do for NDC. (8) *E-A subsampling*: M1 scores E-A on the first 300 / 60 / 200 base KBs,
E-B and E-C on every pair; censoring is 60 s per instance via a killed forked child (`f4_exec.py`). The full-scale arm went to Picasso.

**Corpora.** synthetic — 2,000 (M0) / 300 (M1), `n ∈ [6,16]`, `m ∈ [6,20]`, arity 2–4, 3 types, 3 predicates, rejection sampling.
NDC-classes quarterly — 1,432 encodable / 200 sampled, `arb_temporal_lib` star KBs, envelope `3 ≤ m ≤ 110`, `n ≤ 24`, arity ≤ 10.
WD50K(66) — 3,988 encodable / 200 sampled, `probe_hyperrel` subject-ego star KBs, same envelope. The NDC derivation reproduces §6 of
`probes_2026-09.md` exactly — 1,432 encodable KBs, 555 consecutive pairs, `Δ` histogram 85 / 120 / 134 / 191 / 25 over
`0 / 1 / 2 / 3–5 / >5` — the loader's own correctness check.

## 2. M0 — correctness (3,000 instances)

**Isomorphism invariance**, `w(K)` vs `w(permute(K, σ))` for random `σ`: **0 violations** for
all three encodings (E-A 2,939 instances checked, the rest censored; E-B, E-C 3,000 each).
**Completeness** against `pynauty_levi.fingerprint`, as a partition comparison:

| corpus | N (A / B,C) | iso classes nauty (A / B,C) | classes E-A / E-B / E-C | false merges | false splits |
|---|---|---|---|---|---|
| synthetic | 2000 / 2000 | 2000 / 2000 | 2000 / 2000 / 2000 | 0 | 0 |
| NDC-classes | 465 / 500 | 298 / 325 | 298 / 325 / 325 | 0 | 0 |
| WD50K(66) | 474 / 500 | 463 / 489 | 463 / 489 / 489 | 0 | 0 |

The real corpora carry genuine collisions (500 NDC KBs → 325 classes), so the test is not
vacuous. E-A arm: 5,838 canonicalizations, 115 censored at 60 s (1.97 %), secs med 0.0016 / p90
0.016 / max 51.0. **Both new encodings are complete isomorphism invariants in measurement.**

## 3. M1 — single-edit response (the PI's criterion)

Absolute response in tokens as min/p25/**med**/p75/p90/max; "nrm" is the median of
`d / |w(base)|`. E-A coverage: synthetic 15,466 canonicalizations, 0 censored, 14,877 pairs
scored; NDC 2,467, 8.7 % censored, 2,672 pairs; WD50K 8,501, 7.2 % censored, 7,336 pairs.

| corpus | edit kind | n | E-A abs | nrm | E-B abs | nrm | E-C abs | nrm |
|---|---|---|---|---|---|---|---|---|
| synth | insert_fact | 3000 | 1/5/**15**/26/35/58 | .471 | 1/1/**1**/9/14/21 | **.062** | 10/21/**25**/29/32/37 | 1.038 |
| synth | delete_fact | 2882 | 1/5/**14**/24/33/57 | .438 | 1/1/**1**/9/14/21 | **.062** | 8/20/**24**/28/31/36 | 1.000 |
| synth | add_constant | 3000 | 1/7/**17**/27/35/61 | .500 | 1/1/**2**/8/13/20 | **.077** | 12/20/**24**/28/32/36 | 1.000 |
| synth | remove_constant | 2995 | 1/8/**18**/27/35/58 | .517 | 1/1/**2**/8/13/21 | **.080** | 11/20/**24**/28/31/36 | 1.000 |
| synth | insert+new_const | 3000 | 1/8/**18**/28/36/61 | .535 | 2/9/**13**/17/20/22 | .567 | 6/20/**25**/29/32/38 | 1.069 |
| synth | **pooled** | 14877 | 1/6/**16**/26/35/61 | .500 | 1/1/**4**/11/16/22 | **.188** | 6/20/**25**/28/32/38 | 1.000 |
| NDC | insert_fact | 1960 | 1/5/**7**/10/13/30 | .800 | 1/1/**1**/3/4/30 | **.111** | 7/11/**14**/16/18/55 | 1.077 |
| NDC | delete_fact | 725 | 1/1/**2**/4/7/16 | .312 | 1/1/**5**/6/8/30 | .357 | 6/11/**13**/16/19/54 | 1.000 |
| NDC | add_constant | 1777 | 1/3/**4**/5/7/27 | .556 | 1/1/**2**/2/3/11 | **.118** | 6/11/**13**/15/18/54 | 1.000 |
| NDC | remove_constant | 1823 | 1/1/**2**/4/6/14 | .333 | 1/1/**2**/4/5/26 | .200 | 6/11/**13**/15/17/54 | 1.000 |
| NDC | insert+new_const | 2000 | 1/3/**6**/9/12/33 | .667 | 2/4/**5**/5/7/32 | .385 | 7/12/**14**/16/19/56 | 1.154 |
| NDC | **pooled** | 8285 | 1/2/**4**/7/10/33 | .500 | 1/1/**3**/5/6/32 | **.211** | 6/11/**13**/16/18/56 | 1.000 |
| WD50K | insert_fact | 2000 | 1/4/**5**/8/11/39 | .800 | 1/1/**1**/4/7/21 | **.143** | 7/10/**14**/21/29/44 | 1.045 |
| WD50K | delete_fact | 1091 | 1/1/**1**/4/8/33 | .211 | 1/4/**6**/8/11/23 | .333 | 6/12/**18**/26/34/43 | 1.000 |
| WD50K | add_constant | 1852 | 2/3/**4**/5/8/31 | .583 | 1/1/**3**/6/9/20 | **.273** | 6/10/**15**/22/32/43 | 1.000 |
| WD50K | remove_constant | 1174 | 1/1/**2**/5/9/38 | .308 | 1/4/**5**/8/11/21 | .312 | 8/15/**18**/25/34/43 | 1.000 |
| WD50K | insert+new_const | 2000 | 1/2/**3**/6/10/35 | .571 | 2/4/**6**/8/11/22 | .400 | 7/10/**13**/21/30/45 | 1.071 |
| WD50K | **pooled** | 8117 | 1/2/**4**/6/10/39 | .500 | 1/2/**4**/7/10/23 | **.300** | 6/10/**16**/23/33/45 | 1.000 |

E-A's pooled normalized median is **0.500 on all three corpora** — the ≈50 % drift/avalanche
figure of `encoding.md` §2, reproduced independently. E-B falls to a fifth or a third of that;
E-C rewrites the whole word.

## 4. M2 — variant series against a known fact-level difference

**NDC-classes quarterly, 555 natural consecutive pairs** (`Δ` from named ARB node ids); strata
85 / 120 / 134 / 191 / 25.

| enc | n | Spearman | Pearson | med d at Δ = 0/1/2/3–5/>5 | Δ=1: ≤2 | ≤5 | ≥25 % | med d/\|w\| |
|---|---|---|---|---|---|---|---|---|
| E-A | 473 | 0.683 | 0.628 | 0 / 4 / 3 / 6 / 13 | .355 | .677 | .656 | .429 |
| E-B | 555 | 0.632 | 0.620 | 0 / 7 / 5 / 8 / 9 | .225 | .333 | .742 | .462 |
| E-C | 555 | 0.583 | 0.642 | 0 / 14 / 13 / 17 / 20 | .000 | .000 | 1.000 | 1.000 |

**WD50K(66), 1,000 synthetic constant-set-preserving ladders `t = 1…5`** — the difference from
NDC, stated: these edits are ours, not the data's, and never change the constant set. Strata
34 / 264 / 242 / 460 / 0.

| enc | n | Spearman | Pearson | med d at Δ = 0/1/2/3–5 | Δ=1: ≤2 | ≤5 | ≥25 % | med d/\|w\| |
|---|---|---|---|---|---|---|---|---|
| E-A | 950 | 0.563 | 0.510 | 0 / 5 / 8 / 10 | .075 | .601 | .972 | 1.000 |
| E-B | 1000 | **0.633** | 0.566 | 0 / **1** / 4 / 6 | **.595** | **.905** | .295 | **.131** |
| E-C | 1000 | 0.286 | 0.276 | 0 / 12 / 13 / 15 | .000 | .000 | 1.000 | 1.067 |

## 5. M3 — compactness and cost

| corpus | N | n med | m med | tokens A med/p90 | B | C | secs A med/p90 | B | C | A DNF |
|---|---|---|---|---|---|---|---|---|---|---|
| synthetic | 300 | 9 | 15 | 38 / 62 | 25 / 32 | 25 / 32 | .0017 / .0081 | 4e-5 / 5e-5 | 6e-5 / 7e-5 | .000 |
| NDC-classes | 200 | 9 | 3 | 7 / 15 | 13 / 17 | 13 / 17 | .0013 / 2.24 | 2e-5 / 3e-5 | 3e-5 / 5e-5 | .062 |
| WD50K(66) | 200 | 9 | 5 | 7 / 21 | 15 / 29 | 15 / 29 | .0011 / 8.29 | 3e-5 / 6e-5 | 4e-5 / 8e-5 | .060 |

E-B and E-C have identical token counts by construction (`n` type + `m` fact tokens), differing
only in symbol identity. Both cost one nauty call — 20–60 µs, two orders of magnitude below
E-A's median and five below its p90 — and neither censors, where E-A censors 6 % of real
instances at 60 s. On the dense synthetic corpus the F4 word is **shorter** than `w*_c` (25 vs
38 tokens); on the sparse real corpora about twice as long, because F4 pays `n` type tokens up
front where the pointer encoding amortizes constants into the `V` tokens that create them.

## 6. M4 — how close is E-B to the nauty certificate?

Spearman ρ against the byte-level Levenshtein of `color_signature ++ pynauty.certificate` (the
construction of `metric_space/representations/nauty_levi_edit.py`).

| pair set | pairs | ρ(nauty, d_B) | ρ(nauty, d_C) | ρ(d_B, d_C) | med nauty / d_B / d_C |
|---|---|---|---|---|---|
| NDC consecutive | 555 | **0.949** | 0.844 | 0.844 | 36 / 7 / 14 |
| synthetic, single edit | 1200 | **0.751** | 0.284 | 0.143 | 25 / 3 / 24 |
| synthetic, random | 591 | **0.617** | 0.704 | 0.821 | 81 / 21 / 27 |
| NDC, single edit | 1192 | **0.786** | 0.320 | 0.276 | 19 / 3 / 13 |
| NDC, random | 597 | **0.808** | 0.813 | 0.838 | 42 / 8 / 14 |
| WD50K, single edit | 1146 | **0.694** | 0.453 | 0.494 | 29 / 4 / 14 |
| WD50K, random | 590 | **0.962** | 0.872 | 0.935 | 87 / 12 / 19 |

E-B tracks the nauty-certificate distance closely (ρ 0.62–0.96, ≥ 0.75 on five of seven pair
sets) — expected, since both are a canonical labelling serialized to a string. E-C tracks it far
more weakly on single-edit pairs (0.28–0.45) and comparably on random pairs.
**Why E-C fails — the mechanism** (`probe_wl_locality.py`; 100 base KBs per corpus, ~1,900 edits
each): mean fraction of constants whose address ingredient moves under one edit,

| corpus | WL h=1 | h=2 | h=3 | h=64 | nauty rank | edits, zero WL-h3 shift | zero rank shift |
|---|---|---|---|---|---|---|---|
| synthetic | .356 | .926 | .928 | .928 | .028 | .000 | .847 |
| NDC-classes | .517 | .980 | .982 | .982 | .102 | .000 | .681 |
| WD50K(66) | .371 | .865 | .919 | .919 | .042 | .001 | .743 |

Depth-3 hypergraph-WL colours are **not local**: two rounds already reach every constant of a
connected KB this size, so one fact edit changes 92–98 % of the colours and **no edit among
5,724 left the colour multiset intact**. Every address changes, every token changes, and the E-C
distance degenerates to `max(|w_1|, |w_2|)`. The nauty canonical rank order is by contrast
*entirely unchanged* for 68–85 % of edits.

**E-C-roles** (coordinator addendum, WD50K(66) only). Fact tokens carry `(role, address)` pairs,
role ∈ {subject, object, qualifier} from the statement (a constant in two roles takes the
smaller), sorted by `(role, address)`. 200 base KBs, 7,936 single-edit pairs. **Every statistic
is identical to E-C's** to the last digit: token count med 12 both, pooled response
7/10/**13**/22/30/42 both, normalized median 1.000 both. The words genuinely differ (verified
token by token), but E-C is already saturated — a KB and its one-edit neighbour share **zero**
symbols — so the distance is fixed by word length alone. **Roles cost nothing in tokens and buy
nothing in stability on top of an addressing scheme already at total rewrite**; worth repeating
on E-B, where there is a signal to lose.

## 7. Full-scale E-A on Picasso

`run_ea_full.py` enumerates the complete E-A task list — **32,920 canonicalizations** covering
every M1 base and single-edit neighbour at full corpus size (300 / 200 / 200 base KBs), all 555
NDC consecutive pairs and all WD50K ladders — and computes a contiguous block per array task,
keyed by SHA-1 of `(n, types, facts, k)` so shards merge with no index bookkeeping
(`merge_ea_shards.py`). **Submitted: array `2206622`, 4 tasks**, `--cpus-per-task=4 --mem=8G
--time=0-12:00:00 --constraint=sd --account=tic_163_uma`, started 2026-09-04 19:39:47; tasks 0
and 1 COMPLETED (66 s, 22 min), tasks 2–3 still RUNNING at 20:56. Results
`…/fscratch/results/f4_topology/ea/ea_shard_<task>.json`, logs
`…/execs/f4_topology/logs/f4-ea_2206622_<task>.{out,err}`; merge with `rsync -a
picasso:<results>/ ./ea_shards/ && python merge_ea_shards.py --shards ./ea_shards`. It yields
`w*_c`, seed label and wall-clock for all 32,920 instances at a 60 s budget, lifting the M1 E-A
subsampling (§1 choice 8) and giving cluster-grade M3 timings on one pinned node family.
Two caveats. **The first attempt failed**: array `2206615`, pinned to `--constraint=sr`, died on
all four tasks in 8 s with `Illegal instruction (core dumped)` — Picasso's `isalhg` C++ extension
was built on the login node (Xeon Gold 6230R, AVX-512) and `sr` is AMD EPYC without it, and a
login-node smoke test cannot catch this because the login node *has* AVX-512. **The blocks are
imbalanced** (not a correctness problem): contiguous over a list beginning with the near-free
synthetic corpus, so task 0 finished in 66 s while tasks 2–3 carry the real work; a shuffled or
cost-weighted partition would honour SCBI's two-hour floor on every task, this one does not on
task 0.

## 8. Seeds and commands

Seeds: corpus 20260904; edits 20260905 (M1), 20260906 (M2 ladders), 20260907 (WL locality),
20260908 (roles); permutations 20260906. `~/.conda/envs/isalhg/bin/python`, C++ engine,
`pynauty` 2.8.8.1, 16 concurrent forked workers, 60 s per-instance budget. Stage wall-clock:
m0 599 s, m1 ~62 min, m2 388 s, m34 161 s, roles 3 s.

```
cd scripts/diagnostics/d_art3_probes_2026-09-03/f4_topology ; PY=~/.conda/envs/isalhg/bin/python
for s in m0 m1 m2 m34 roles; do $PY run_probe.py --stage $s; done   # -> m*_results.json
$PY probe_wl_locality.py ; $PY render_tables.py > tables.md
bash slurm/f4_ea_launcher.sh                                        # Picasso array 2206622
```

## 9. Verdict

**(1) Does either fact-addressed encoding make one-fact-apart KBs close, against E-A's ~50 %?** **E-B yes, substantially; E-C no,
catastrophically.** E-A's pooled single-edit response is exactly 50 % of the word on all three corpora — the drift/avalanche figure,
reproduced. E-B cuts it to a normalized median of 0.188 (synthetic), 0.211 (NDC), 0.300 (WD50K), and for the purest one-fact edits it is
genuinely **one token**: median 1 for `insert_fact` on all three corpora, 1–2 for `delete_fact` and `add_constant` on synthetic. On the
WD50K ladders, constant set held fixed, 59.5 % of one-fact-apart pairs sit within 2 tokens under E-B against 7.5 % under E-A. E-C moves
the whole word: normalized median 1.000 everywhere, 0 of 384 Δ=1 pairs within 5 tokens. **The gain is real but not uniform**: E-B wins on
edits that leave the constant set alone, and when an edit adds or strands a constant the canonical order renumbers and E-B falls back to
E-A's level or below — `insert_fact_new_constant` (nrm 0.385–0.567), `delete_fact` on the real corpora (0.333–0.357). On the NDC
*natural* series, where consecutive quarters routinely change the constant set and words run ~13 tokens, E-B's Δ=1 normalized median
(0.462) is no better than E-A's (0.429). Ball enumeration at radius 1–2 would find one-fact repairs under E-B for constant-preserving
edits and still miss those that introduce a constant.

**(2) Does E-C's local addressing beat E-B's global ranks, and where?** **Nowhere** — worse than E-B on every corpus, every edit kind and
both M2 series, and worse than the status quo E-A on the single-edit criterion. The mechanism is measured, not conjectured (§6): depth-3
hypergraph-WL colours are global functions of a connected KB this size, while the nauty canonical rank order is untouched by 68–85 % of
edits. Lowering the depth does not save it — even `h = 1` moves 36–52 % of colours. The hypothesis behind E-C is falsified.

**(3) What breaks or degrades?** *Completeness*: nothing — both F4 encodings are complete isomorphism invariants in measurement (0 false
merges, 0 false splits over 3,000 instances with real collisions) and isomorphism-invariant (0 violations). *Compactness*: mixed — F4 is
shorter than `w*_c` on dense KBs (25 vs 38 tokens at `m` med 15), about twice as long on the sparse real corpora (13–15 vs 7 at `m` med
3–5). *Cost*: strictly better — one nauty call (20–60 µs) against `w*_c`'s median 1.1–1.7 ms, p90 2.2–8.3 s and a 6 % censor rate at
60 s. *Differentiation from nauty*: the real casualty. E-B correlates with the nauty-certificate edit distance at ρ = 0.62–0.96 (≥ 0.75
on five of seven pair sets) — expected, because E-B *is* a canonical labelling serialized to a fact list. E-C is the arm that stays
distinct from nauty (ρ 0.28–0.45 on single-edit pairs), and it is distinct by being useless. Under the pre-registered rule (best measured
local stability wins even if its distance is statistically indistinguishable from the nauty-certificate distance), **the measurement
selects E-B** — and the differentiation argument must then rest on the language (decodability, ball enumeration, generation), not on the
distance differing from nauty's.
