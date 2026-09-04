# F4 follow-on — is there a third point? Positional addressing inside a locally determined class

2026-09-04, follow-on to `probe_f4_topology.md` and `probe_f4_followup.md`. The two failures measured there have opposite causes: **E-C**'s address is *content* and a
refinement colour is global (one edit moves 92–98 % of the colours); **E-B**'s address is *positional* and a global rank order renumbers when the set it orders changes. This
probe adds the missing point — an address that is positional **within a locally determined class** — and measures whether it lands between them. Everything is in this
directory; no repository file outside it was touched.

## 1. Design as implemented

**E-D — local-key addressing.** `κ(c) = (type(c), sorted multiset over facts incident to c of (predicate label, arity))` — strictly depth 0: it reads `c`'s own incidences and
never a neighbour's key. `addr(c) = (κ(c), idx)` with `idx` the position of `c` among the constants sharing `κ(c)`, ordered by the **same nauty canonical rank E-B uses**
(`f4_encodings.canonical_ranks`). Word = address-keyed type prefix in increasing address order, then one `F[ℓ; addr₁ … addr_a]` per fact with operands sorted by address and
fact tokens sorted lexicographically — layout identical to E-C, so only the address differs. **E-D1 — coarse local-key addressing.** Same, with `κ(c) = (type(c), degree(c))`.
E-B is the degenerate single-class member of the same family. Symbol equality is equality of the whole `(κ, idx)` structure; `κ` is an ordinary tuple compared by value, never
hashed, so no refinement history can leak in. Code: `f4_local_key.py`.

**Choices the specification left open.** (1) *Type-prefix token* = `("T", addr, type)`, address inside the token, mirroring E-C — the type is already determined by `κ`, so the
field is redundant and distance-neutral, but it keeps the layouts token-for-token comparable and makes a degree-0 constant recoverable. (2) *Address order* = lexicographic on
the serialized `(κ, idx)`; iso-invariant, otherwise arbitrary. (3) *Arity* in `κ` counts the constant itself. (4) *Regime rule* = **preserving iff the edit neither adds nor
strands a constant**, i.e. `kind ≠ insert_fact_new_constant` and `n(K') = n(K)` — exact, because `f4_corpora.compact` drops exactly the stranded constants. (5) *E-A and E-C
distances come from the earlier probe's caches* (`m1_rows_*.json`, `m2_rows_ndc.json`, `m3_results.json`); nothing here re-runs `canonical_string`. The M1 corpora and job list
are rebuilt by replaying `run_probe.stage_m1`'s RNG consumption, and the replay is **verified**: the `(base, kind)` sequence matches the cached rows on all 31,279 pairs and
recomputed `d_B`/`d_C` equal the cached values (0 mismatches). (6) *N3 needs the old→new constant correspondence*, which `compact` destroys by renumbering, so
`f4_local_key.apply_edit_traced` replays `apply_edit` consuming the RNG identically and returns the map; equivalence asserted on 2,000 `(KB, kind)` draws — 0 result mismatches,
**identical final RNG state**. (7) N3 fractions are over *surviving* constants only; an inserted constant has no predecessor and is excluded. Corpora, edit kinds and instances
are exactly the earlier probe's (§1 of `probe_f4_topology.md`).

## 2. N0 — correctness

Isomorphism invariance under a random relabelling, and completeness against `pynauty_levi.fingerprint` as a partition comparison, on the same M0 corpora.

| corpus | N | iso classes (nauty) | classes E-D | classes E-D1 | iso violations D/D1 | false merges D/D1 | false splits D/D1 |
|---|---|---|---|---|---|---|---|
| synthetic | 2000 | 2000 | 2000 | 2000 | 0/0 | 0/0 | 0/0 |
| NDC-classes | 500 | 325 | 325 | 325 | 0/0 | 0/0 | 0/0 |
| WD50K(66) | 500 | 489 | 489 | 489 | 0/0 | 0/0 | 0/0 |

The real corpora carry genuine collisions (500 → 325 classes), so the test is not vacuous. **Both new encodings are complete isomorphism invariants in measurement.**

## 3. N1 — single-edit response, split by regime

31,279 single-edit pairs. Absolute response in tokens as min/p25/**med**/p75/p90/max; "nrm" is the median of `d / |w(base)|`. The pooled figures of `probe_f4_topology.md` §3 average a 1:3 regime mix and are **not** repeated. Full 20-row per-kind grid: `tables_local_key.md`.

| corpus | regime | n | E-A abs | nrm | E-B abs | nrm | E-C abs | nrm | E-D abs | nrm | E-D1 abs | nrm |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| synth | preserving | 11597 | 1/6/**16**/26/34/61 | .486 | 1/1/**1**/8/14/21 | **.071** | 10/20/**25**/28/31/37 | 1.000 | 4/12/**15**/18/21/26 | .643 | 3/8/**12**/16/20/26 | .500 |
| synth | changing | 3280 | 1/8/**18**/28/36/61 | .526 | 2/9/**13**/17/19/22 | .556 | 6/20/**25**/29/32/38 | 1.062 | 3/9/**11**/15/18/25 | **.500** | 2/10/**14**/17/20/26 | .588 |
| NDC | preserving | 5187 | 1/3/**4**/7/10/30 | .500 | 1/1/**1**/3/4/30 | **.111** | 6/11/**13**/15/18/55 | 1.000 | 4/8/**9**/11/13/45 | .727 | 3/4/**5**/8/11/46 | .412 |
| NDC | changing | 3098 | 1/1/**3**/7/10/33 | **.429** | 2/4/**5**/6/7/32 | .375 | 6/12/**13**/16/19/56 | 1.105 | 3/7/**9**/11/13/42 | .714 | 2/5/**8**/10/12/43 | .611 |
| WD50K | preserving | 4744 | 1/3/**4**/7/11/39 | .600 | 1/1/**3**/6/9/21 | **.207** | 6/10/**16**/23/33/44 | 1.000 | 4/7/**10**/13/17/33 | .667 | 3/6/**7**/11/14/31 | .500 |
| WD50K | changing | 3373 | 1/1/**2**/5/8/35 | **.333** | 2/4/**6**/8/11/23 | .389 | 6/10/**16**/23/32/45 | 1.000 | 3/6/**8**/11/15/33 | .562 | 2/5/**7**/10/13/31 | .500 |

Median at `insert_fact` (synth / NDC / WD50K): E-B **1 / 1 / 1** token, E-D **14 / 9 / 8**, E-D1 **16 / 9 / 8**; at `insert_fact_new_constant`: E-B **13 / 5 / 6**, E-D **12 / 9 / 7**, E-D1 **14 / 8 / 7**. **The decisive statistic is the fraction of pairs within 1 and 2 tokens.**

| corpus | regime | n | E-A ≤1 / ≤2 | E-B ≤1 / ≤2 | E-C ≤1 / ≤2 | E-D ≤1 / ≤2 | E-D1 ≤1 / ≤2 |
|---|---|---|---|---|---|---|---|
| synth | preserving | 11597 | .082 / .107 | **.506 / .581** | .000 / .000 | **.000 / .000** | .000 / .000 |
| synth | changing | 3280 | .033 / .080 | .000 / .088 | .000 / .000 | **.000 / .000** | .000 / .011 |
| NDC | preserving | 5187 | .062 / .185 | **.515 / .701** | .000 / .000 | **.000 / .000** | .000 / .000 |
| NDC | changing | 3098 | .326 / .424 | .000 / .126 | .000 / .000 | **.000 / .000** | .000 / .101 |
| WD50K | preserving | 4744 | .032 / .156 | **.379 / .435** | .000 / .000 | **.000 / .000** | .000 / .000 |
| WD50K | changing | 3373 | .310 / .531 | .000 / .095 | .000 / .000 | **.000 / .000** | .000 / .012 |

**E-D is never within 2 tokens of a one-edit neighbour — 0 of 31,279 pairs.** E-D1 reaches ≤ 2 on 10.1 % of NDC changing pairs and essentially nowhere else. E-B is one-token-local on 38–52 % of preserving pairs.

## 4. N2 — the NDC natural variant series, both regimes

555 consecutive encodable quarterly pairs, split 140 preserving / 415 changing exactly as `followup_ndc_regime.py` does (`Δ` = fact-level difference on named ARB simplex ids);
the E-A/E-B/E-C rows reproduce the follow-up verbatim.

| split | enc | n | ρ | r | med d at Δ = 0/1/2/3–5/>5 | Δ=1 n | ≤2 | ≤5 | med d/\|w\| |
|---|---|---|---|---|---|---|---|---|---|
| preserving | E-A | 108 | 0.965 | 0.760 | 0 / 5 / 5 / — / — | 18 | .167 | .556 | .561 |
| preserving | **E-B** | 140 | 0.962 | 0.817 | 0 / **1** / 2 / — / — | 35 | **.771** | **1.000** | **.077** |
| preserving | E-C | 140 | 0.903 | 0.827 | 0 / 14 / 11 / — / — | 35 | .000 | .000 | 1.000 |
| preserving | E-D | 140 | 0.940 | 0.876 | 0 / 11 / 11 / — / — | 35 | .000 | .086 | .889 |
| preserving | E-D1 | 140 | 0.903 | 0.722 | 0 / 10 / 5 / — / — | 35 | .000 | .086 | .769 |
| changing | E-A | 365 | 0.511 | 0.510 | — / **4** / 3 / 6 / 13 | 75 | **.400** | **.707** | **.400** |
| changing | E-B | 415 | 0.281 | 0.315 | — / 7 / 6 / 8 / 9 | 85 | .000 | .059 | .533 |
| changing | E-C | 415 | 0.307 | 0.367 | — / 16 / 13.5 / 17 / 20 | 85 | .000 | .000 | 1.125 |
| changing | **E-D** | 415 | **0.602** | **0.580** | — / 10 / 11 / 14 / 18 | 85 | .000 | .000 | .692 |
| changing | E-D1 | 415 | 0.315 | 0.331 | — / 9 / 7 / 11 / 14 | 85 | .000 | .000 | .692 |

Correlation between constants moved (`|V_t △ V_{t+1}|`, median 6) and each distance over the 415 changing pairs — E-B's 0.503 is the number E-D had to beat: **E-A 0.430 · E-B
0.503 · E-C 0.390 · E-D 0.599 · E-D1 0.399** (n = 365 for E-A, 415 for the rest). **E-D does not beat it — it is the worst of the five.** Its one genuine win is monotone
response: on the changing split E-D orders `Δ` better than any other encoding (ρ 0.602 against E-A's 0.511 and E-B's 0.281). It is better *ordered* and worse *localized* —
median distance at Δ = 1 is 10 tokens against E-B's 7 and E-A's 4.

## 5. N3 — key diversity, and the mechanism

Per-KB key statistics over the M1 base corpora (300 / 200 / 200 KBs).

| corpus | key | distinct keys med/p90 | keys per constant med | class size med/p90/max | frac. constants in a singleton class med/mean |
|---|---|---|---|---|---|
| synth | E-D | 9 / 14 | 1.000 | 1 / 1 / 3 | 1.000 / 0.974 |
| synth | E-D1 | 8 / 10 | 0.800 | 1 / 2 / 6 | 0.625 / 0.621 |
| NDC | E-D | 7 / 9 | 0.750 | 1 / 2 / 7 | 0.556 / 0.603 |
| NDC | E-D1 | 6 / 8 | 0.667 | 1 / 3 / 11 | 0.444 / 0.462 |
| WD50K | E-D | 5 / 8 | 0.600 | 1 / 3 / 11 | 0.353 / 0.443 |
| WD50K | E-D1 | 3 / 4 | 0.333 | 1 / 9 / 22 | 0.167 / 0.180 |

The full key is nearly a fingerprint: on synthetic **97.4 %** of constants sit alone in their class, so E-D is almost pure content addressing with no positional component left
to protect it. Coarsening moves it the right way (E-D1 max class 6–22). Over the same 31,279 edits, mean fraction of *surviving* constants whose ingredient moved, and fraction
of edits where **none** moved (`frac 0`):

| corpus | regime | n edits | E-B rank | E-D key | E-D addr | E-D1 key | E-D1 addr |
|---|---|---|---|---|---|---|---|
| synth | preserving | 11597 | 0.197 / **0.572** | 0.376 / 0.000 | 0.380 / 0.000 | 0.219 / 0.000 | 0.317 / 0.000 |
| synth | changing | 3280 | 0.518 / 0.088 | 0.223 / 0.000 | 0.229 / 0.000 | 0.215 / 0.027 | 0.343 / 0.013 |
| NDC | preserving | 5187 | 0.239 / **0.429** | 0.525 / 0.000 | 0.595 / 0.000 | 0.272 / 0.000 | 0.406 / 0.000 |
| NDC | changing | 3098 | 0.520 / 0.089 | 0.437 / 0.000 | 0.516 / 0.000 | 0.317 / 0.214 | 0.482 / 0.090 |
| WD50K | preserving | 4744 | 0.485 / **0.216** | 0.382 / 0.000 | 0.530 / 0.000 | 0.221 / 0.000 | 0.632 / 0.000 |
| WD50K | changing | 3373 | 0.625 / 0.073 | 0.209 / 0.000 | 0.330 / 0.000 | 0.169 / 0.153 | 0.570 / 0.007 |

**This explains everything.** The key *is* local — mean 0.21–0.53 of constants, and under `insert_fact` the constants whose key moves are exactly the `a` members of the new
fact. But `frac 0 = 0.000` in every preserving row: **no edit among 21,528 constant-preserving edits left the E-D or E-D1 address map intact**, because a fact insertion *is* a
change to the incidence data its members' keys are read from. E-B's rank profile is instead **bimodal** — it moves nothing at all on 57 / 43 / 22 % of preserving edits
(distance 1) and a lot when it moves; locality is won by the edits that cost zero, not by a low average. `addr ≥ key` in all 12 comparisons: the index adds churn on top (WD50K
E-D1 0.221 → 0.632, where classes are largest).

## 6. N4 — tokens and cost

| corpus | N | n med | m med | tokens A med/p90 | B = D = D1 | secs A med/p90 | B | D | D1 |
|---|---|---|---|---|---|---|---|---|---|
| synthetic | 300 | 9 | 15 | 38 / 62 | 25 / 32 | .0017 / .0081 | 3.9e-5 | 5.5e-5 | 4.5e-5 |
| NDC-classes | 200 | 9 | 3 | 7 / 15 | 13 / 17 | .0013 / 2.24 | 1.9e-5 | 2.9e-5 | 2.4e-5 |
| WD50K(66) | 200 | 9 | 5 | 7 / 21 | 15 / 29 | .0011 / 8.29 | 2.2e-5 | 3.2e-5 | 2.7e-5 |

Confirmed: **one nauty call plus a linear pass**. E-D/E-D1 cost 1.2–1.4× E-B (the key build is `O(Σ_c deg c)`), still two orders below E-A's median and five below its p90, and
neither censors. Token counts are identical to E-B and E-C by construction (`n` type + `m` fact tokens); only symbol identity differs.

## 7. Seeds and commands

Seeds: corpus 20260904, edits 20260905, permutations 20260906, trace-equivalence check 20261004 (`SEED_EDITS + 99`). `~/.conda/envs/isalhg/bin/python`, `pynauty` 2.8.8.1,
`rapidfuzz`. Stage wall-clock: n0 1.6 s, n1 8.7 s, n2 0.5 s, n3 5.8 s, n4 0.5 s — the probe reuses the cached E-A arm throughout.

```
cd scripts/diagnostics/d_art3_probes_2026-09-03/f4_topology ; PY=~/.conda/envs/isalhg/bin/python
for s in n0 n1 n2 n3 n4; do $PY run_local_key.py --stage $s; done   # -> n*_results.json
$PY render_local_key.py > tables_local_key.md
```

Artifacts: `f4_local_key.py`, `run_local_key.py`, `render_local_key.py`, `n{0..4}_results.json`, `n1_rows_<corpus>.json`, `n2_rows_ndc.json`, `tables_local_key.md`; re-running
every stage after a lint pass reproduced `n0`–`n3` byte-identically (`n4` carries wall-clock only).

## 8. Verdict

**(1) Where does E-D sit against E-B in each regime — dominate, trade, or lose?** **It loses in the regime that matters and trades in the other.** *Preserving*: E-B dominates
E-D at every quantile on all three corpora (synthetic 1/1/**1**/8/14/21 against 4/12/**15**/18/21/26), and the gap is categorical, not gradual — E-B is within one token on
38–52 % of pairs, E-D on **0 of 21,528**. *Changing*: E-D is marginally ahead on synthetic (median 11 vs 13, nrm .500 vs .556) and behind on both real corpora (NDC 9 vs 5,
WD50K 8 vs 6); on the NDC natural series it has one real advantage — the best `Δ`-ordering of any encoding on the changing split — bought with uniformly larger distances and
the *worst* sensitivity to moved constants (ρ 0.599 vs E-B's 0.503). **The hypothesis that a locally-keyed address lands between E-B and E-C is falsified in the direction that
mattered**: E-D does land between them on magnitude (nrm .41–.73 against E-C's 1.00 and E-B's .07–.21), but it inherits E-C's *qualitative* defect — the address map never
survives an edit intact.

**(2) Does key granularity move it along the trade-off as predicted, and in which direction?** **Yes, toward E-B, monotonically, and not far enough.** Coarsening the key (E-D →
E-D1) shrinks key diversity (singleton fraction 0.974 → 0.621 synthetic, 0.443 → 0.180 WD50K), lowers the mean key churn in every N3 row (NDC preserving 0.525 → 0.272), and
improves the preserving normalized median on all three corpora (.643 → .500, .727 → .412, .667 → .500) — the predicted direction, with E-B as the single-class limit; it also
gives a little back in the changing regime on synthetic (.500 → .588), also as predicted. But the family is continuous in the wrong coordinate: even `(type, degree)` changes at
every constant the edit touches, so E-D1 still reaches ≤ 2 tokens on 0–10 % of pairs against E-B's 44–70 % in the preserving regime. The E-B endpoint is not approached smoothly
— it is discontinuous, because at a single class the key stops reading the structure at all.

**(3) Is any of the five one-token-local under both fact insertion and constant insertion — and if not, what is the obstruction?** **None is, and the measurements name the
obstruction.** Let `A: V(K) → Σ` be injective and isomorphism-invariant; the word is an `A`-keyed type prefix plus fact tokens over `A`-images, so `d(K, K') ≥ Σ_{c : A(c) ≠
A'(c)} (1 + deg c)`. Then:

- If `A(c)` **reads `c`'s own incidence data** (E-C, E-D, E-D1), a fact insertion over `S` changes `A(c)` for every `c ∈ S` *by definition* — the insertion is precisely a
  change to that data — so the word moves by at least `Σ_{c∈S}(1 + deg c)` tokens. Measured: `frac 0 = 0.000` over 21,528 constant-preserving edits, response `Θ(incidence mass
  at the edit site)` = .41–.73 of the word. Fact-insertion locality is **impossible**, not merely unattained.
- If `A(c)` **ignores `c`'s incidence data**, injectivity plus isomorphism-invariance force `A` to separate constants by position in an isomorphism-invariant total order on
  `V(K)` (E-B). Inserting a constant changes that order's domain, and no isomorphism-invariant order need restrict to itself on the old domain. Measured: rank churn 0.52–0.63
  with `frac 0` 0.07–0.09 on constant-changing edits.
- Hybrids `(κ, idx)` inherit **both**: `addr ≥ key` in all 12 comparisons, and the index renumbers inside whichever class the key churn or the new constant lands in.

The escape would be an extrinsic identifier carried with the constant (a URI, an insertion timestamp) — exactly what isomorphism-invariance forbids. So the proposition to build
is a frontier statement, not a construction: *for any complete (injective, isomorphism-invariant) address map, `O(1)` word response cannot hold simultaneously for fact
insertion and for constant insertion; a scheme chooses which it pays for, at `Θ(incidence mass at the edit site)` for content keys and `Θ(|w|)` with probability `1 − p` for
positional keys, where `p` (0.22–0.57 measured for nauty ranks) is a property of the canonical-order algorithm, not of the encoding.* This is the completeness–stability
frontier the metric-space paper states for `w*_c`, localized to the addressing layer. **E-B remains the adopted scheme**; E-D and E-D1 join E-C in the supplement, with the
mechanism above as the reason no fourth point rescues the trade-off.
