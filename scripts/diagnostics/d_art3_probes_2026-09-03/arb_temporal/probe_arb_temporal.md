# ARB temporal star knowledge bases — feasibility probe

2026-09-04. All artifacts live in this directory; nothing else in the repository
was touched. Companion to `§4` of
`docs/article/D_ART3/foundation/probes_2026-09.md` (ARB *labeled* ego-networks),
which set the canonicalization frontier at `m ≲ 110`.

**Setup.** `~/.conda/envs/isalhg/bin/python` (3.11) · C++ engine
(`canonical_string(H, k=required_k(H), algorithm="canonical", backend="cpp")`) ·
token length `len(instructions.parse(w))` · census
`PynautyLeviBackend.fingerprint` · data root
`/media/mpascual/Sandisk2TB/research/ISAL/isalhg/data/arb_benson/temporal/` ·
seeds `random.Random(20260903)` (census sample) and `random.Random(20260904)`
(timing sample) · timing 30 s per instance enforced by killing a forked child, a
bucket-mode abandoned after 3 timeouts, whole run capped at 1400 s. Compute
spent: 42 s for tasks 1–4 over all 12 datasets, 1,323 s for task 5 — 23 min of
the 40-minute budget. Nothing was left unfinished.

```
cd scripts/diagnostics/d_art3_probes_2026-09-03/arb_temporal
PY=~/.conda/envs/isalhg/bin/python
for d in email-Enron contact-high-school email-Eu DAWN NDC-classes \
         contact-primary-school NDC-substances tags-math-sx tags-ask-ubuntu \
         threads-ask-ubuntu coauth-MAG-History congress-bills; do
  $PY probe_stats.py $d; done          # tasks 1-4 -> stats_<d>.json, spec_<d>.json
$PY check_contact_join.py                                     # -> contact_join.json
$PY probe_timing.py --budget 30 --deadline 1400 --max-dnf 3   # -> timing.json
$PY aggregate.py > tables.md ; $PY aggregate_timing.py > timing_tables.md
```

**Definitions.** `S_t(v)` = the distinct simplices containing `v` timestamped in
window `t`, read as a hypergraph on the union of their members (multiplicity
dropped, one hyperedge per distinct simplex). Every hyperedge contains `v`, so
**every star KB is connected by construction** — the `w*_c` domain restriction
costs no filtering. `Δ_t(v) = |S_t(v) △ S_{t+1}(v)|` is computed on named ARB
node ids over strictly consecutive window indices with both windows non-empty;
it is exact ground truth and needs no isomorphism computation.

**Envelope** `n ≤ 24`, `m ≤ 110`. Two refinements change the answer and are
reported separately: **substantive** adds `m ≥ 3` (a 1-fact KB is not a
knowledge base, and six corpora have median `m` exactly 1); **encodable** adds
`max arity ≤ 10`, because the compiled encoder raises `IsalHGError: max_arity
(12) exceeds K_MAX (10)` — **arity is a second hard admissibility wall**, and it
removes 4–54 % of in-envelope KBs on the high-arity corpora (§2, last column).

**Labels.** Every `<dataset>-node-labels.txt` under `temporal/` is a *name* map
(one distinct string per node), not a categorical vocabulary; "identity-labelled"
below means each vertex carries its own colour — the named-entity regime a real
KB has. True *categorical* labels exist only for the two contact corpora, and the
join is verified: the `labeled/` family is exactly the deduplicated temporal
hyperedge set (7,818 = 7,818 and 12,704 = 12,704) with **identical per-node
degree vectors on all 327 / 242 ids, 0 mismatches**, so the 9 and 11 class labels
join by raw node id (`contact_join.json`).

## 1. Corpus facts and window granularity (task 1)

`cands` gives the median `m` of non-empty star KBs at every candidate window.

| dataset | unit | simplices | distinct | nodes | arity | node-label file | cands (gran:med m) | chosen |
|---|---|---|---|---|---|---|---|---|
| email-Enron | ms since year 0 | 10,883 | 1,512 | 143 | 1-18 | names (148) | day:1, week:2, month:3, quarter:5, year:10 | year, quarter |
| contact-high-school | s (20 s resolution) | 172,035 | 7,818 | 327 | 2-5 | none | 5min:1, 15min:2, hour:4, 4hour:8, day:16 | 4hour, day |
| email-Eu | s (Unix epoch) | 234,760 | 25,027 | 998 | 1-25 | none | day:2, week:4, month:8, quarter:15, year:16 | month, quarter |
| DAWN | quarter code (year*4+quarter) | 2,272,433 | 141,087 | 2,558 | 1-16 | names (2558) | quarter:3, year:4, 2year:5 | 2year, year |
| NDC-classes | ms since year 0 | 49,724 | 1,088 | 1,161 | 1-24 | names (1161) | day:1, week:1, month:1, quarter:1, year:1 | year, quarter |
| contact-primary-school | s (20 s resolution) | 106,879 | 12,704 | 242 | 2-5 | none | 5min:3, 15min:5, hour:13, 4hour:27, day:74 | hour, 15min |
| NDC-substances | ms since year 0 | 112,405 | 9,906 | 5,311 | 1-25 | names (5556) | day:1, week:1, month:1, quarter:1, year:1 | year, quarter |
| tags-math-sx | ms (relative) | 822,059 | 170,476 | 1,629 | 1-5 | names (1629) | hour:1, day:1, week:2, month:5, quarter:8, year:17 | quarter, year |
| tags-ask-ubuntu | ms (relative) | 271,233 | 147,222 | 3,029 | 1-5 | names (3029) | hour:1, day:1, week:1, month:2, quarter:3, year:7 | year, quarter |
| threads-ask-ubuntu | ms (relative) | 192,947 | 166,999 | 125,602 | 1-14 | none | hour:1, day:1, week:1, month:1, quarter:1, year:1 | year, quarter |
| coauth-MAG-History | year | 1,812,511 | 895,439 | 1,014,734 | 1-25 | names (1034876) | year:1, 2year:1, 5year:1, 10year:1 | 10year, 5year |
| congress-bills | days since year 0 | 260,851 | 84,799 | 1,718 | 1-25 | names (1718) | month:3, quarter:8, year:28, 2year:51 | quarter, year |

## 2. Sizes, arity, envelope yield (task 2)

Percentiles are min/p25/med/p75/p90/max over all non-empty `(v, t)`.

| dataset | gran | #KB | n | m | max arity | KB arity>=3 | env (n<=24, m<=110) | env frac | env arity>=3 | env arity<=10 |
|---|---|---|---|---|---|---|---|---|---|---|
| email-Enron | year | 392 | 1/7/12/20/31/66 | 1/4/10/21/34/82 | 1/4/8/12/16/18 | 0.872 | 321 | 0.819 | 0.844 | 0.838 |
| email-Enron | quarter | 1,046 | 1/4/8/13/20/50 | 1/2/5/10/16/43 | 1/3/5/10/13/18 | 0.778 | 989 | 0.946 | 0.765 | 0.840 |
| contact-high-school | 4hour | 3,679 | 2/5/8/12/17/40 | 1/4/8/14/21/51 | 2/2/3/3/4/5 | 0.599 | 3,627 | 0.986 | 0.593 | 1.000 |
| contact-high-school | day | 1,557 | 2/9/14/21/27/50 | 1/9/16/26/37/82 | 2/3/3/4/4/5 | 0.786 | 1,326 | 0.852 | 0.749 | 1.000 |
| email-Eu | month | 13,246 | 1/7/17/29/45/141 | 1/3/8/18/32/159 | 1/4/10/19/23/25 | 0.827 | 8,714 | 0.658 | 0.737 | 0.751 |
| email-Eu | quarter | 5,311 | 1/9/24/42/66/208 | 1/4/15/35/63/266 | 1/5/13/21/24/25 | 0.854 | 2,693 | 0.507 | 0.712 | 0.768 |
| DAWN | 2year | 8,021 | 1/3/12/56/182/861 | 1/2/5/27/136/10759 | 1/2/6/12/16/16 | 0.747 | 4,960 | 0.618 | 0.590 | 0.928 |
| DAWN | year | 14,067 | 1/2/10/42/142/706 | 1/2/4/19/88/6417 | 1/2/5/12/16/16 | 0.715 | 9,399 | 0.668 | 0.574 | 0.927 |
| NDC-classes | year | 12,162 | 1/2/4/7/14/90 | 1/1/1/2/4/79 | 1/2/4/7/12/24 | 0.679 | 11,745 | 0.966 | 0.668 | 0.906 |
| NDC-classes | quarter | 23,292 | 1/2/4/7/12/82 | 1/1/1/1/3/79 | 1/2/4/6/10/24 | 0.650 | 22,892 | 0.983 | 0.644 | 0.915 |
| contact-primary-school | hour | 3,950 | 2/6/12/21/29/51 | 1/6/13/26/37/72 | 2/2/3/3/4/5 | 0.703 | 3,265 | 0.827 | 0.641 | 1.000 |
| contact-primary-school | 15min | 12,231 | 2/4/6/10/15/35 | 1/3/5/11/17/40 | 2/2/2/3/3/5 | 0.492 | 12,162 | 0.994 | 0.490 | 1.000 |
| NDC-substances | year | 27,351 | 1/1/3/17/38/443 | 1/1/1/2/5/134 | 1/1/3/14/22/25 | 0.501 | 23,055 | 0.843 | 0.408 | 0.819 |
| NDC-substances | quarter | 46,038 | 1/1/3/16/31/288 | 1/1/1/2/4/134 | 1/1/3/14/22/25 | 0.517 | 39,818 | 0.865 | 0.442 | 0.793 |
| tags-math-sx | quarter | 27,929 | 1/6/13/30/67/500 | 1/3/8/26/74/1831 | 1/4/5/5/5/5 | 0.947 | 19,376 | 0.694 | 0.923 | 1.000 |
| tags-math-sx | year | 9,354 | 1/8/22/56/118/717 | 1/5/17/60/181/4891 | 1/4/5/5/5/5 | 0.970 | 4,976 | 0.532 | 0.944 | 1.000 |
| tags-ask-ubuntu | year | 16,980 | 1/6/12/30/70/1592 | 1/2/7/20/62/6016 | 1/4/5/5/5/5 | 0.936 | 11,840 | 0.697 | 0.908 | 1.000 |
| tags-ask-ubuntu | quarter | 47,024 | 1/4/7/16/37/1093 | 1/1/3/9/25/2401 | 1/3/5/5/5/5 | 0.898 | 39,597 | 0.842 | 0.879 | 1.000 |
| threads-ask-ubuntu | year | 148,076 | 1/1/2/3/5/1397 | 1/1/1/1/3/1221 | 1/1/2/3/3/14 | 0.256 | 146,203 | 0.987 | 0.246 | 1.000 |
| threads-ask-ubuntu | quarter | 169,582 | 1/1/2/3/5/607 | 1/1/1/1/3/502 | 1/1/2/3/3/14 | 0.258 | 167,564 | 0.988 | 0.249 | 1.000 |
| coauth-MAG-History | 10year | 1,310,307 | 1/1/1/3/6/522 | 1/1/1/1/2/401 | 1/1/1/3/5/25 | 0.253 | 1,303,696 | 0.995 | 0.250 | 0.963 |
| coauth-MAG-History | 5year | 1,467,160 | 1/1/1/2/5/419 | 1/1/1/1/1/316 | 1/1/1/2/5/25 | 0.238 | 1,461,848 | 0.996 | 0.236 | 0.965 |
| congress-bills | quarter | 67,566 | 1/36/66/96/158/398 | 1/4/8/15/26/248 | 1/19/23/25/25/25 | 0.978 | 10,525 | 0.156 | 0.859 | 0.463 |
| congress-bills | year | 18,906 | 1/98/145/221/301/472 | 1/16/28/52/88/409 | 1/24/25/25/25/25 | 0.998 | 275 | 0.015 | 0.847 | 0.505 |

Arity histogram over (KB, distinct edge) incidences, in-envelope KBs, chosen granularity:

| dataset | gran | a=1 | a=2 | a=3 | a=4 | a=5 | a=6-10 | a>10 | share a>=3 |
|---|---|---|---|---|---|---|---|---|---|
| email-Enron | quarter | 130 | 3,128 | 1,150 | 576 | 349 | 645 | 184 | 47.1% |
| contact-high-school | 4hour | 0 | 25,943 | 7,280 | 853 | 34 | 0 | 0 | 23.9% |
| email-Eu | month | 1,869 | 31,512 | 7,987 | 4,332 | 3,099 | 7,135 | 3,999 | 44.3% |
| DAWN | year | 7,581 | 12,924 | 6,474 | 3,134 | 1,488 | 2,077 | 716 | 40.4% |
| NDC-classes | quarter | 596 | 10,077 | 4,548 | 3,787 | 3,960 | 6,393 | 2,889 | 66.9% |
| contact-primary-school | 15min | 0 | 69,518 | 17,951 | 1,466 | 44 | 0 | 0 | 21.9% |
| NDC-substances | quarter | 21,866 | 7,691 | 6,113 | 4,481 | 2,451 | 6,034 | 8,985 | 48.7% |
| tags-math-sx | quarter | 5,289 | 27,835 | 41,710 | 27,859 | 16,345 | 0 | 0 | 72.2% |
| tags-ask-ubuntu | quarter | 8,964 | 32,728 | 46,648 | 36,819 | 26,726 | 0 | 0 | 72.6% |
| threads-ask-ubuntu | quarter | 60,030 | 129,756 | 42,130 | 11,088 | 3,280 | 1,366 | 27 | 23.4% |
| coauth-MAG-History | 10year | 819,728 | 325,642 | 139,703 | 72,941 | 41,641 | 77,351 | 50,088 | 25.0% |
| congress-bills | quarter | 5,104 | 2,767 | 1,555 | 1,501 | 1,131 | 4,774 | 6,005 | 65.5% |

## 3. Variants: Delta over consecutive windows (task 3)

Both KBs of the pair inside the envelope; chosen granularity.

| dataset | gran | pairs non-empty | pairs in env | d=0 | d=1 | d=2 | d=3-5 | d>5 | nodes run>=3 | nodes run>=5 | nodes >=3 one-edit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| email-Enron | quarter | 849 | 763 | 13 (0.017) | 22 (0.029) | 66 (0.087) | 176 (0.231) | 486 (0.637) | 127 | 96 | 0 |
| contact-high-school | 4hour | 2,155 | 2,086 | 5 (0.002) | 18 (0.009) | 36 (0.017) | 254 (0.122) | 1,773 (0.850) | 310 | 0 | 1 |
| email-Eu | month | 11,044 | 5,684 | 209 (0.037) | 235 (0.041) | 457 (0.080) | 1,295 (0.228) | 3,488 (0.614) | 614 | 431 | 17 |
| DAWN | year | 10,722 | 6,052 | 509 (0.084) | 589 (0.097) | 1,011 (0.167) | 1,838 (0.304) | 2,105 (0.348) | 1,193 | 734 | 44 |
| NDC-classes | quarter | 12,395 | 11,877 | 5,389 (0.454) | 2,196 (0.185) | 2,446 (0.206) | 1,722 (0.145) | 124 (0.010) | 496 | 345 | 202 |
| contact-primary-school | 15min | 10,862 | 10,726 | 297 (0.028) | 464 (0.043) | 775 (0.072) | 2,265 (0.211) | 6,925 (0.646) | 242 | 241 | 77 |
| NDC-substances | quarter | 20,216 | 14,069 | 6,174 (0.439) | 1,369 (0.097) | 3,232 (0.230) | 2,482 (0.176) | 812 (0.058) | 1,067 | 438 | 149 |
| tags-math-sx | quarter | 24,041 | 14,646 | 66 (0.005) | 97 (0.007) | 1,047 (0.071) | 3,228 (0.220) | 10,208 (0.697) | 1,302 | 1,039 | 2 |
| tags-ask-ubuntu | quarter | 37,354 | 28,798 | 91 (0.003) | 132 (0.005) | 3,344 (0.116) | 9,363 (0.325) | 15,868 (0.551) | 2,199 | 1,608 | 1 |
| threads-ask-ubuntu | quarter | 22,865 | 20,665 | 1,423 (0.069) | 719 (0.035) | 6,310 (0.305) | 6,965 (0.337) | 5,248 (0.254) | 3,239 | 725 | 9 |
| coauth-MAG-History | 10year | 235,400 | 230,820 | 91,449 (0.396) | 31,060 (0.135) | 58,122 (0.252) | 40,727 (0.176) | 9,462 (0.041) | 47,481 | 5,880 | 498 |
| congress-bills | quarter | 64,349 | 3,033 | 91 (0.030) | 174 (0.057) | 671 (0.221) | 1,774 (0.585) | 323 (0.106) | 369 | 90 | 11 |

Same, restricted to the **encodable** envelope (`n<=24`, `3<=m<=110`, max arity `<=10`):

| dataset | gran | #KB encodable | pairs encodable | d=0 | d=1 | d=2 | d=3-5 | d>5 | nodes run>=3 | nodes run>=5 | nodes >=3 one-edit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| email-Enron | quarter | 528 | 320 | 0 (0.000) | 2 (0.006) | 5 (0.016) | 50 (0.156) | 263 (0.822) | 68 | 26 | 0 |
| contact-high-school | 4hour | 3,045 | 1,559 | 1 (0.001) | 2 (0.001) | 10 (0.006) | 91 (0.058) | 1,455 (0.933) | 240 | 0 | 0 |
| email-Eu | month | 4,208 | 2,229 | 4 (0.002) | 20 (0.009) | 45 (0.020) | 333 (0.149) | 1,827 (0.820) | 314 | 156 | 2 |
| DAWN | year | 3,656 | 1,886 | 0 (0.000) | 1 (0.001) | 19 (0.010) | 320 (0.170) | 1,546 (0.820) | 422 | 176 | 0 |
| NDC-classes | quarter | 1,432 | 555 | 85 (0.153) | 120 (0.216) | 134 (0.241) | 191 (0.344) | 25 (0.045) | 45 | 20 | 14 |
| contact-primary-school | 15min | 9,159 | 6,992 | 26 (0.004) | 53 (0.008) | 172 (0.025) | 967 (0.138) | 5,774 (0.826) | 240 | 217 | 1 |
| NDC-substances | quarter | 2,222 | 1,106 | 26 (0.024) | 35 (0.032) | 107 (0.097) | 315 (0.285) | 623 (0.563) | 55 | 37 | 4 |
| tags-math-sx | quarter | 12,626 | 8,986 | 0 (0.000) | 0 (0.000) | 10 (0.001) | 235 (0.026) | 8,741 (0.973) | 991 | 711 | 0 |
| tags-ask-ubuntu | quarter | 19,619 | 12,516 | 0 (0.000) | 0 (0.000) | 4 (0.000) | 231 (0.018) | 12,281 (0.981) | 1,160 | 799 | 0 |
| threads-ask-ubuntu | quarter | 15,095 | 2,852 | 0 (0.000) | 0 (0.000) | 1 (0.000) | 117 (0.041) | 2,734 (0.959) | 503 | 100 | 0 |
| coauth-MAG-History | 10year | 39,493 | 6,854 | 4 (0.001) | 6 (0.001) | 106 (0.015) | 1,994 (0.291) | 4,744 (0.692) | 1,119 | 125 | 0 |
| congress-bills | quarter | 1,299 | 62 | 0 (0.000) | 0 (0.000) | 2 (0.032) | 24 (0.387) | 36 (0.581) | 2 | 0 | 0 |

## 4. Isomorphism census over in-envelope KBs (task 4)

pynauty-Levi; sample of at most 1,500 in-envelope KBs, seed 20260903. Every
dataset finished well inside the one-minute cap (worst case 0.1 s).

| dataset | gran | in envelope | census N | sampled | distinct unlabelled | distinct identity-labelled | distinct fact sets | secs |
|---|---|---|---|---|---|---|---|---|
| email-Enron | quarter | 989 | 989 | no | 590 | 941 | 941 | 0.1 |
| contact-high-school | 4hour | 3,627 | 1,500 | yes | 588 | 1,482 | 1,482 | 0.1 |
| email-Eu | month | 8,714 | 1,500 | yes | 921 | 1,469 | 1,469 | 0.1 |
| DAWN | year | 9,399 | 1,500 | yes | 511 | 1,477 | 1,477 | 0.1 |
| NDC-classes | quarter | 22,892 | 1,500 | yes | 213 | 680 | 680 | 0.1 |
| contact-primary-school | 15min | 12,162 | 1,500 | yes | 436 | 1,448 | 1,448 | 0.1 |
| NDC-substances | quarter | 39,818 | 1,500 | yes | 221 | 1,243 | 1,243 | 0.1 |
| tags-math-sx | quarter | 19,376 | 1,500 | yes | 934 | 1,499 | 1,499 | 0.1 |
| tags-ask-ubuntu | quarter | 39,597 | 1,500 | yes | 666 | 1,498 | 1,498 | 0.1 |
| threads-ask-ubuntu | quarter | 167,564 | 1,500 | yes | 124 | 1,498 | 1,498 | 0.0 |
| coauth-MAG-History | 10year | 1,303,696 | 1,500 | yes | 90 | 1,500 | 1,500 | 0.0 |
| congress-bills | quarter | 10,525 | 1,500 | yes | 577 | 1,443 | 1,443 | 0.1 |

## 5. Labelled vs unlabelled `w*_c` wall-clock (task 5)

Stratified by `m`-bucket, at most 4 encodable instances per bucket (<=16 per
dataset), 30 s budget. Columns are `labelled / unlabelled`; medians and p90 are
over completions only, so read the DNF column first.

| dataset | gran | bucket | N | med n | med m | med s L/U | p90 s L/U | DNF L/U | skip L/U | med tokens L/U |
|---|---|---|---|---|---|---|---|---|---|---|
| email-Enron | quarter | 1-10 | 4 | 8 | 6 | 0.0008 / 0.0218 | 0.1194 / 0.0588 | 0/4 · 1/4 | 0 · 0 | 16 / 17 |
| email-Enron | quarter | 11-30 | 4 | 12 | 12 | 0.0034 / 0.4039 | 0.0435 / 14.2233 | 0/4 · 0/4 | 0 · 0 | 30 / 30 |
| email-Enron | quarter | 31-60 | 3 | 17 | 32 | 0.0084 / 0.2200 | 0.0474 / 0.2932 | 0/3 · 1/3 | 0 · 0 | 85 / 91 |
| contact-high-school | 4hour | 1-10 | 4 | 8 | 8 | 0.0006 / 0.0009 | 0.0006 / 0.1923 | 0/4 · 0/4 | 0 · 0 | 10 / 10 |
| contact-high-school | 4hour | 11-30 | 4 | 16 | 16 | 0.0008 / - | 0.0009 / - | 0/4 · 3/4 | 0 · 1 | 32 / - |
| contact-high-school | 4hour | 31-60 | 4 | 22 | 33 | 0.0026 / 11.1807 | 0.0091 / 11.1807 | 0/4 · 3/4 | 0 · 0 | 86 / 86 |
| email-Eu | month | 1-10 | 4 | 10 | 6 | 0.0006 / 0.0009 | 0.0018 / 0.0723 | 0/4 · 0/4 | 0 · 0 | 10 / 8 |
| email-Eu | month | 11-30 | 4 | 14 | 14 | 0.0060 / 3.7425 | 0.4036 / 5.7815 | 0/4 · 2/4 | 0 · 0 | 26 / 26 |
| email-Eu | month | 31-60 | 4 | 21 | 32 | 2.9623 / 3.8049 | 18.7375 / 5.6498 | 0/4 · 2/4 | 0 · 0 | 112 / 125 |
| email-Eu | month | 61-110 | 1 | 21 | 63 | - / - | - / - | 1/1 · 1/1 | 0 · 0 | - / - |
| DAWN | year | 1-10 | 4 | 10 | 7 | 0.0006 / 0.0011 | 0.0010 / 0.0053 | 0/4 · 0/4 | 0 · 0 | 10 / 9 |
| DAWN | year | 11-30 | 4 | 19 | 16 | 0.0020 / 5.0846 | 0.0029 / 7.1968 | 0/4 · 2/4 | 0 · 0 | 26 / 22 |
| DAWN | year | 31-60 | 4 | 20 | 36 | 0.1513 / 3.0185 | 0.6252 / 9.8191 | 0/4 · 1/4 | 0 · 0 | 134 / 112 |
| NDC-classes | quarter | 1-10 | 4 | 8 | 4 | 0.0030 / 2.0261 | 0.0262 / 4.0887 | 0/4 · 0/4 | 0 · 0 | 12 / 9 |
| NDC-classes | quarter | 11-30 | 4 | 20 | 22 | 0.7543 / - | 1.3630 / - | 0/4 · 3/4 | 0 · 1 | 74 / - |
| contact-primary-school | 15min | 1-10 | 4 | 6 | 5 | 0.0006 / 0.0006 | 0.0007 / 0.0012 | 0/4 · 0/4 | 0 · 0 | 6 / 6 |
| contact-primary-school | 15min | 11-30 | 4 | 14 | 16 | 0.0008 / 0.0464 | 0.0017 / 18.5862 | 0/4 · 1/4 | 0 · 0 | 33 / 25 |
| contact-primary-school | 15min | 31-60 | 4 | 20 | 31 | 0.0022 / - | 0.0025 / - | 0/4 · 3/4 | 0 · 1 | 78 / - |
| NDC-substances | quarter | 1-10 | 4 | 4 | 4 | 0.0006 / 0.0005 | 0.0006 / 0.0006 | 0/4 · 0/4 | 0 · 0 | 6 / 5 |
| NDC-substances | quarter | 11-30 | 4 | 8 | 16 | 0.0009 / 0.0026 | 0.0014 / 0.0118 | 0/4 · 0/4 | 0 · 0 | 34 / 30 |
| NDC-substances | quarter | 31-60 | 4 | 13 | 34 | 0.0083 / 0.2608 | 0.0319 / 0.6357 | 0/4 · 0/4 | 0 · 0 | 82 / 91 |
| tags-math-sx | quarter | 1-10 | 4 | 11 | 10 | 0.0008 / 0.0013 | 0.0038 / 0.0014 | 0/4 · 1/4 | 0 · 0 | 20 / 18 |
| tags-math-sx | quarter | 11-30 | 4 | 21 | 20 | 0.0031 / 2.5572 | 0.0051 / 8.9664 | 0/4 · 0/4 | 0 · 0 | 44 / 52 |
| tags-math-sx | quarter | 31-60 | 4 | 24 | 34 | 0.0066 / 0.6750 | 0.0141 / 1.2598 | 0/4 · 0/4 | 0 · 0 | 94 / 104 |
| tags-ask-ubuntu | quarter | 1-10 | 4 | 12 | 6 | 0.0006 / 0.0014 | 0.0009 / 0.1270 | 0/4 · 0/4 | 0 · 0 | 6 / 7 |
| tags-ask-ubuntu | quarter | 11-30 | 4 | 23 | 14 | 0.0049 / 5.6532 | 0.0061 / 10.1387 | 0/4 · 2/4 | 0 · 0 | 38 / 30 |
| tags-ask-ubuntu | quarter | 31-60 | 4 | 24 | 32 | 0.0219 / 1.1162 | 0.0242 / 1.7693 | 0/4 · 1/4 | 0 · 0 | 113 / 109 |
| threads-ask-ubuntu | quarter | 1-10 | 4 | 4 | 3 | 0.0005 / 0.0005 | 0.0006 / 0.0011 | 0/4 · 0/4 | 0 · 0 | 4 / 3 |
| threads-ask-ubuntu | quarter | 11-30 | 4 | 20 | 15 | 0.0006 / 0.3600 | 0.0008 / 0.3600 | 0/4 · 3/4 | 0 · 0 | 18 / 11 |
| coauth-MAG-History | 10year | 1-10 | 4 | 5 | 4 | 0.0006 / 0.0006 | 0.0066 / 1.4565 | 0/4 · 0/4 | 0 · 0 | 6 / 6 |
| coauth-MAG-History | 10year | 11-30 | 4 | 20 | 11 | 0.0015 / 4.3787 | 13.8082 / 4.3787 | 0/4 · 3/4 | 0 · 0 | 22 / 13 |
| congress-bills | quarter | 1-10 | 4 | 16 | 4 | 0.0009 / 0.3445 | 0.3996 / 5.0931 | 0/4 · 1/4 | 0 · 0 | 8 / 4 |
| congress-bills | quarter | 11-30 | 2 | 22 | 11 | 0.0713 / - | 0.1073 / - | 0/2 · 2/2 | 0 · 0 | 32 / - |

Paired completions (both modes finished): N=87; median speedup unlabelled/labelled = **10.53x**; labelled faster in 72/87; aggregate 154.9 s vs 1.9 s.

Reading of §5. **Identity labels change the regime, not just the constant.**
Across all 12 datasets the labelled mode completed 125 of its 126 instances, with
a single timeout (email-Eu, `m = 63`); the unlabelled mode completed 87 of the
same 126 and timed out 36 times. On the 87 instances where both finished, median
speedup is **10.53×** (labelled faster in 72/87; aggregate 154.9 s vs 1.9 s,
81× in total). The §4 ego-network probe measured 1.91× with a 9-symbol class
vocabulary; naming every entity is worth an order of magnitude more, because the
seed set and the residual `V`-branch ties collapse to singletons. Token length is
unaffected (the `L / U` token columns agree to a few percent), so this is search
cost, not encoding cost.

## 6. Ranked recommendation

**1 — `NDC-classes`, quarter windows.** The only corpus with a *high rate* of
real one-edit variants. In the encodable envelope: 1,432 KBs, 555 consecutive
pairs, **120 at Δ = 1 (21.6 %)**, 134 at Δ = 2, 85 at Δ = 0, and only 4.5 % above
Δ = 5 — versus 0–3.2 % at Δ = 1 everywhere else. 14 nodes carry ≥ 3 one-edit
pairs and 20 nodes have ≥ 5 consecutive in-envelope windows. Arity ≥ 3 on 66.9 %
of in-envelope edges (a = 3: 4,548; a = 4: 3,787; a = 5: 3,960; a = 6–10: 6,393).
Node labels: 1,161 pharmacologic-class names. Labelled canonicalization finished
8/8 (median 0.003 s at `m ≤ 10`, 0.754 s at `m` 11–30) while the unlabelled mode
managed 4/8. Structural redundancy is real here — 1,500 sampled in-envelope KBs
fall into only **213 unlabelled isomorphism classes** (7.0 KBs per class), where
the tags and contact corpora give 1.6–3.4. Caveat: the corpus is
first-marketing dates, so the *overall* median `m` is 1 at every granularity; the
usable corpus is the 1,432 encodable-substantive KBs, not the 22,892 in-envelope
ones.

**2 — `NDC-substances`, quarter windows.** Same family, complementary profile:
2,222 encodable KBs, 1,106 pairs, **35 at Δ = 1 (3.2 %)** and 26 at Δ = 0, 4
nodes with ≥ 3 one-edit pairs, 37 nodes with ≥ 5 consecutive windows. Arity ≥ 3
on 48.7 % of in-envelope edges, and 5,556 substance names as labels. Decisive on
criterion (iv): it is **the only dataset in the set where every timing instance
completed in both modes** — 12/12 labelled *and* 12/12 unlabelled, median
0.0006–0.0083 s labelled and 0.0005–0.26 s unlabelled. If the experiment must
also run without labels, this is the corpus that supports it.

**Runner-up — `contact-primary-school`, 15-minute windows.** Wins on volume and
on labels: 9,159 encodable KBs, 6,992 consecutive pairs, 217 nodes with ≥ 5
consecutive in-envelope windows, 100 % of in-envelope KBs encodable (max arity 5),
labelled timing 12/12 with median ≤ 0.0022 s, and the **only true categorical
vocabulary** in the whole temporal family (11 verified-joinable classes). It
loses on criterion (i): only 53 pairs at Δ = 1 (0.8 %), one node with ≥ 3
one-edit pairs, and 82.6 % of pairs above Δ = 5 — contacts churn almost
completely between adjacent windows. Take it if the experiment needs many KBs
and class labels; not if it needs one-edit series.

**Rejected, with the number that rejects them.** `email-Enron` (2 one-edit pairs,
16 % of in-envelope KBs unencodable), `contact-high-school` (2), `email-Eu` (20
pairs but 0.9 %, no node labels, 5/13 unlabelled DNF), `DAWN` (1 one-edit pair
out of 1,886), `tags-math-sx` and `tags-ask-ubuntu` (**0** one-edit pairs in
12,626 and 19,619 encodable KBs; tags churn wholesale — 97–98 % of pairs above
Δ = 5), `threads-ask-ubuntu` and `coauth-MAG-History` (0 and 6 one-edit pairs;
median `m` = 1 at every granularity, and 1,500 sampled KBs collapse to 124 and 90
unlabelled isomorphism classes — near-trivial stars), `congress-bills` (62
encodable pairs in total; only 46 % of in-envelope KBs pass the arity wall).

**Coverage.** All 12 datasets in the priority list were completed for tasks 1–5;
none was left unfinished. `tags-stack-overflow`, `threads-stack-overflow`,
`coauth-DBLP`, `threads-math-sx` and `coauth-MAG-Geology` were **not loaded**
(348 MB–506 MB each), per the standing instruction to skip them.
