
### M0a -- isomorphism invariance

| corpus | N | E-A checked / viol | E-B | E-C |
|---|---|---|---|---|
| synthetic | 2000 | 2000 / 0 | 2000 / 0 | 2000 / 0 |
| NDC-classes | 500 | 465 / 0 | 500 / 0 | 500 / 0 |
| WD50K(66) | 500 | 474 / 0 | 500 / 0 | 500 / 0 |

### M0b -- completeness against pynauty-Levi

| corpus | enc | N | iso classes (nauty) | classes (enc) | false merges | false splits |
|---|---|---|---|---|---|---|
| synthetic | E-A | 2000 | 2000 | 2000 | 0 | 0 |
| synthetic | E-B | 2000 | 2000 | 2000 | 0 | 0 |
| synthetic | E-C | 2000 | 2000 | 2000 | 0 | 0 |
| NDC-classes | E-A | 465 | 298 | 298 | 0 | 0 |
| NDC-classes | E-B | 500 | 325 | 325 | 0 | 0 |
| NDC-classes | E-C | 500 | 325 | 325 | 0 | 0 |
| WD50K(66) | E-A | 474 | 463 | 463 | 0 | 0 |
| WD50K(66) | E-B | 500 | 489 | 489 | 0 | 0 |
| WD50K(66) | E-C | 500 | 489 | 489 | 0 | 0 |

E-A arm: 5838 canonicalizations, 5723 ok, 115 censored at 60 s (0.0197), secs med 0.0016 / p90 0.0158 / max 51.0

### M1 -- single-edit response, absolute tokens (min/p25/med/p75/p90/max)


**synthetic** -- 300 base KBs, 14877 single-edit pairs

| edit kind | n | E-A abs | E-A norm med | E-B abs | E-B norm med | E-C abs | E-C norm med |
|---|---|---|---|---|---|---|---|
| insert_fact | 3000 | 1 / 5 / 15 / 26 / 35 / 58 | 0.471 | 1 / 1 / 1 / 9 / 14 / 21 | 0.062 | 10 / 21 / 25 / 29 / 32 / 37 | 1.038 |
| delete_fact | 2882 | 1 / 5 / 14 / 24 / 33 / 57 | 0.438 | 1 / 1 / 1 / 9 / 14 / 21 | 0.062 | 8 / 20 / 24 / 28 / 31 / 36 | 1.000 |
| add_constant | 3000 | 1 / 7 / 17 / 27 / 35 / 61 | 0.500 | 1 / 1 / 2 / 8 / 13 / 20 | 0.077 | 12 / 20 / 24 / 28 / 32 / 36 | 1.000 |
| remove_constant | 2995 | 1 / 8 / 18 / 27 / 35 / 58 | 0.517 | 1 / 1 / 2 / 8 / 13 / 21 | 0.080 | 11 / 20 / 24 / 28 / 31 / 36 | 1.000 |
| insert_fact_new_constant | 3000 | 1 / 8 / 18 / 28 / 36 / 61 | 0.535 | 2 / 9 / 13 / 17 / 20 / 22 | 0.567 | 6 / 20 / 25 / 29 / 32 / 38 | 1.069 |
| **pooled** | 14877 | 1 / 6 / 16 / 26 / 35 / 61 | 0.500 | 1 / 1 / 4 / 11 / 16 / 22 | 0.188 | 6 / 20 / 25 / 28 / 32 / 38 | 1.000 |

E-A coverage: 15466 canonicalizations, 0 censored (0.0000); pairs scored under E-A: 14877.

**NDC-classes** -- 200 base KBs, 8285 single-edit pairs

| edit kind | n | E-A abs | E-A norm med | E-B abs | E-B norm med | E-C abs | E-C norm med |
|---|---|---|---|---|---|---|---|
| insert_fact | 1960 | 1 / 5 / 7 / 10 / 13 / 30 | 0.800 | 1 / 1 / 1 / 3 / 4 / 30 | 0.111 | 7 / 11 / 14 / 16 / 18 / 55 | 1.077 |
| delete_fact | 725 | 1 / 1 / 2 / 4 / 7 / 16 | 0.312 | 1 / 1 / 5 / 6 / 8 / 30 | 0.357 | 6 / 11 / 13 / 16 / 19 / 54 | 1.000 |
| add_constant | 1777 | 1 / 3 / 4 / 5 / 7 / 27 | 0.556 | 1 / 1 / 2 / 2 / 3 / 11 | 0.118 | 6 / 11 / 13 / 15 / 18 / 54 | 1.000 |
| remove_constant | 1823 | 1 / 1 / 2 / 4 / 6 / 14 | 0.333 | 1 / 1 / 2 / 4 / 5 / 26 | 0.200 | 6 / 11 / 13 / 15 / 17 / 54 | 1.000 |
| insert_fact_new_constant | 2000 | 1 / 3 / 6 / 9 / 12 / 33 | 0.667 | 2 / 4 / 5 / 5 / 7 / 32 | 0.385 | 7 / 12 / 14 / 16 / 19 / 56 | 1.154 |
| **pooled** | 8285 | 1 / 2 / 4 / 7 / 10 / 33 | 0.500 | 1 / 1 / 3 / 5 / 6 / 32 | 0.211 | 6 / 11 / 13 / 16 / 18 / 56 | 1.000 |

E-A coverage: 2467 canonicalizations, 215 censored (0.0872); pairs scored under E-A: 2672.

**WD50K(66)** -- 200 base KBs, 8117 single-edit pairs

| edit kind | n | E-A abs | E-A norm med | E-B abs | E-B norm med | E-C abs | E-C norm med |
|---|---|---|---|---|---|---|---|
| insert_fact | 2000 | 1 / 4 / 5 / 8 / 11 / 39 | 0.800 | 1 / 1 / 1 / 4 / 7 / 21 | 0.143 | 7 / 10 / 14 / 21 / 29 / 44 | 1.045 |
| delete_fact | 1091 | 1 / 1 / 1 / 4 / 8 / 33 | 0.211 | 1 / 4 / 6 / 8 / 11 / 23 | 0.333 | 6 / 12 / 18 / 26 / 34 / 43 | 1.000 |
| add_constant | 1852 | 2 / 3 / 4 / 5 / 8 / 31 | 0.583 | 1 / 1 / 3 / 6 / 9 / 20 | 0.273 | 6 / 10 / 15 / 22 / 32 / 43 | 1.000 |
| remove_constant | 1174 | 1 / 1 / 2 / 5 / 9 / 38 | 0.308 | 1 / 4 / 5 / 8 / 11 / 21 | 0.312 | 8 / 15 / 18 / 25 / 34 / 43 | 1.000 |
| insert_fact_new_constant | 2000 | 1 / 2 / 3 / 6 / 10 / 35 | 0.571 | 2 / 4 / 6 / 8 / 11 / 22 | 0.400 | 7 / 10 / 13 / 21 / 30 / 45 | 1.071 |
| **pooled** | 8117 | 1 / 2 / 4 / 6 / 10 / 39 | 0.500 | 1 / 2 / 4 / 7 / 10 / 23 | 0.300 | 6 / 10 / 16 / 23 / 33 / 45 | 1.000 |

E-A coverage: 8501 canonicalizations, 612 censored (0.0720); pairs scored under E-A: 7336.

### M2 -- variant series: distance vs known fact-level difference


**NDC-classes quarterly, natural consecutive pairs** -- 555 pairs

| enc | n | Spearman | Pearson | med d @ D=0 | 1 | 2 | 3-5 | >5 |
|---|---|---|---|---|---|---|---|---|
| E-A | 473 | 0.683 | 0.628 | 0 | 4 | 3.0 | 6 | 13.0 |
| E-B | 555 | 0.632 | 0.620 | 0 | 7.0 | 5.0 | 8 | 9 |
| E-C | 555 | 0.583 | 0.642 | 0 | 14.0 | 13.0 | 17 | 20 |

| enc | D=1 pairs | frac d<=2 | frac d<=5 | frac d>=25% of word | med d/\|w\| |
|---|---|---|---|---|---|
| E-A | 93 | 0.355 | 0.677 | 0.656 | 0.429 |
| E-B | 120 | 0.225 | 0.333 | 0.742 | 0.462 |
| E-C | 120 | 0.000 | 0.000 | 1.000 | 1.000 |

Stratum sizes: D=0: 85, D=1: 120, D=2: 134, D=3-5: 191, D=>5: 25

**WD50K(66), synthetic ladders t=1..5** -- 1000 pairs

| enc | n | Spearman | Pearson | med d @ D=0 | 1 | 2 | 3-5 | >5 |
|---|---|---|---|---|---|---|---|---|
| E-A | 950 | 0.563 | 0.510 | 0 | 5 | 8 | 10 | -- |
| E-B | 1000 | 0.633 | 0.566 | 0.0 | 1.0 | 4.0 | 6.0 | -- |
| E-C | 1000 | 0.286 | 0.276 | 0.0 | 12.0 | 13.0 | 15.0 | -- |

| enc | D=1 pairs | frac d<=2 | frac d<=5 | frac d>=25% of word | med d/\|w\| |
|---|---|---|---|---|---|
| E-A | 253 | 0.075 | 0.601 | 0.972 | 1.000 |
| E-B | 264 | 0.595 | 0.905 | 0.295 | 0.131 |
| E-C | 264 | 0.000 | 0.000 | 1.000 | 1.067 |

Stratum sizes: D=0: 34, D=1: 264, D=2: 242, D=3-5: 460, D=>5: 0

### M3 -- compactness and cost

| corpus | N | n med | m med | tokens A med/p90 | tokens B | tokens C | secs A med/p90 | secs B | secs C | A DNF |
|---|---|---|---|---|---|---|---|---|---|---|
| synthetic | 300 | 9 | 15 | 38 / 62 | 25 / 32 | 25 / 32 | 0.0017 / 0.0081 | 0.00004 / 0.00005 | 0.00006 / 0.00007 | 0.0000 |
| NDC-classes | 200 | 9 | 3 | 7 / 15 | 13 / 17 | 13 / 17 | 0.0013 / 2.2374 | 0.00002 / 0.00003 | 0.00003 / 0.00005 | 0.0621 |
| WD50K(66) | 200 | 9 | 5 | 7 / 21 | 15 / 29 | 15 / 29 | 0.0011 / 8.2921 | 0.00003 / 0.00006 | 0.00004 / 0.00008 | 0.0600 |

### M4 -- proximity to the nauty-certificate distance

| pair set | pairs | rho(nauty, d_B) | rho(nauty, d_C) | rho(d_B, d_C) | med nauty bytes | med d_B | med d_C |
|---|---|---|---|---|---|---|---|
| ndc_consecutive | 555 | 0.949 | 0.844 | 0.844 | 36 | 7 | 14 |
| synthetic_single_edit | 1200 | 0.751 | 0.284 | 0.143 | 25 | 3 | 24 |
| synthetic_random | 591 | 0.617 | 0.704 | 0.821 | 81 | 21 | 27 |
| ndc_classes_quarter_single_edit | 1192 | 0.786 | 0.320 | 0.276 | 19 | 3 | 13 |
| ndc_classes_quarter_random | 597 | 0.808 | 0.813 | 0.838 | 42 | 8 | 14 |
| wd50k66_single_edit | 1146 | 0.694 | 0.453 | 0.494 | 29 | 4 | 14 |
| wd50k66_random | 590 | 0.962 | 0.872 | 0.935 | 87 | 12 | 19 |

### E-C-roles (WD50K(66) only)

200 base KBs, 7936 single-edit pairs.
Token count: E-C med 12, E-C-roles med 12; distinct symbols per word: E-C med 12, E-C-roles med 12.

| edit kind | n | E-C abs | E-C norm med | E-C-roles abs | E-C-roles norm med |
|---|---|---|---|---|---|
| insert_fact | 2000 | 7 / 9 / 12 / 18 / 29 / 41 | 1.059 | 7 / 9 / 12 / 18 / 29 / 41 | 1.059 |
| delete_fact | 986 | 7 / 11 / 17 / 25 / 33 / 40 | 1.000 | 7 / 11 / 17 / 25 / 33 / 40 | 1.000 |
| add_constant | 1820 | 7 / 9 / 13 / 21 / 29 / 40 | 1.000 | 7 / 9 / 13 / 21 / 29 / 40 | 1.000 |
| remove_constant | 1130 | 7 / 12 / 17 / 24 / 31 / 40 | 1.000 | 7 / 12 / 17 / 24 / 31 / 40 | 1.000 |
| insert_fact_new_constant | 2000 | 7 / 9 / 12 / 19 / 30 / 42 | 1.080 | 7 / 9 / 12 / 19 / 30 / 42 | 1.080 |
| **pooled** | 7936 | 7 / 10 / 13 / 22 / 30 / 42 | 1.000 | 7 / 10 / 13 / 22 / 30 / 42 | 1.000 |
