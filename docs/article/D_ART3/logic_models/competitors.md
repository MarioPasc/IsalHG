# Competitors — per problem, with the losses conceded in advance

*Vocabulary: [`vocabulary.md`](vocabulary.md). Contract discipline follows
`../../COMPETITORS.md` §4: interpretation is written before results are seen,
and no baseline is removed for winning.*

---

## 0. Conceded in advance, stated in the introduction

| Task | Winner | Why |
|---|---|---|
| canonize one structure / deduplicate a collection | `nauty`, `bliss`, Traces on the Levi reduction | faster than `w*_c`, equally exact |
| "is there a finite model / countermodel?" | Mace4, Paradox, SEM, cvc5-FMF, Vampire-FMB | SAT/SMT propagation prunes semantically; we prune structurally |
| minimum-**domain** model | the same finders | that is precisely what their domain-size loop optimizes |
| repair/entailment wall-clock at scale | MaxSAT / ASP with weak constraints | mature solvers on our own objective |
| raw distance-matrix throughput on large corpora | Hungarian/bipartite GED approximation | `O(n³)` per pair with no canonicalization — but see §3 |

Conceding these is what makes the remaining claims readable.

## 1. P-MIN — minimal countermodel

| Baseline | Objective it optimizes | Note |
|---|---|---|
| Mace4 / Paradox / SEM / cvc5-FMF / Vampire-FMB | minimum domain size | **different objective** from `\|D\| + Σ\|P_i\|`; state it in every table |
| MaxSAT / ASP encoding of `cost` at fixed domain, iterated upward | **our objective exactly** | the fair fight; we build it ourselves |
| our loop with a Levi-nauty frontier key | — | isolates dedup cost from the rest |

**Surviving claims if we lose wall-clock:** the exact census by cost level
(verifiable against published counts, `data.md` §3), enumeration of *all*
minimal countermodels up to isomorphism, and the decodable model space.

## 2. P-REPAIR and P-ENTAIL

| Baseline | Role |
|---|---|
| **MaxSAT with soft "keep atom `a`" clauses + hard grounded `ψ`** | the reference method from `src/idea1.txt` and `src/idea2.txt`. Includes the fresh-element pool and BreakID/lex-leader symmetry breaking |
| **ASP with weak constraints** (`clingo` / DLV) | the same, in the generate-test-optimize idiom the source material calls most natural |
| **Kodkod / Alloy** | relational, bounded scopes, built-in symmetry breaking — the closest existing tool to iso-invariant nearest-model search |
| **A\* over partial matchings with Riesen–Bunke bipartite lower bound** | the exact `d_SED` route via alignment variables (Justice–Hero; Lerouge et al.) — the thing we claim to avoid |
| **FPT bounded-search-tree branching** | for universal / forbidden-pattern `ψ` only. It is *automatically iso-invariant* (the target class is closed under isomorphism) and is a genuine FPT algorithm, not a heuristic. **On that fragment it is the strongest baseline and we should expect to lose to it.** |
| our ball enumeration over `Σ_FO` | ours, gated on D3′ |

**The measurement that must be run regardless of who wins.** `src/idea1.txt`
states that without symmetry breaking the MaxSAT route re-derives the same
repair under every permutation of the fresh pool. So: **count the isomorphic
duplicate repairs each baseline emits, with and without its symmetry breaking,
against ours, which emits none by construction.** That is a direct, cheap,
legible measurement of what iso-invariance-by-construction is worth, and it is
independent of wall-clock.

**Contract.** If MaxSAT/ASP dominates wall-clock (expected), report it in the
results text. Surviving claims: zero duplicate repairs without any symmetry
breaking machinery; *all* minimal repairs up to isomorphism; every intermediate
of a repair path a valid inspectable structure; and the measured `d_I` vs
`d_SED` suboptimality gap (`risks.md` §1(c)).

## 3. P-MEDIAN — the medianoid

| Baseline | What it is | The honest comparison |
|---|---|---|
| **Set medianoid under Hungarian/bipartite GED** (Riesen & Bunke 2009) | the standard cheap pipeline | faster per pair, **but its distance is an upper bound, not a metric — so the medoid 2-approximation guarantee does not transfer to it.** Ours does. Measure both the guarantee gap and the runtime |
| **Alternating majority vote** (block-coordinate / Weiszfeld analogue) | align each `K_i` to the current estimate, majority-vote, repeat | the workhorse of `src/idea3.txt`. Needs `N` assignment solves per iteration; converges to a local optimum |
| **Permutation synchronization** (Pachauri–Kondor–Singh; MatchLift/MatchALS) | cycle-consistent joint alignment, then majority vote | the most principled competitor, and the most expensive |
| **Embed → vector median → reconstruct** (Ferrer et al.) | graph embedding route | **its final reconstruction step is approximate. Ours does not exist** — the median string decodes exactly |
| **ILP/QAP exact** | binary atom variables + a permutation per input | exact for small `N` and small domains; the ground truth for our approximation quality |
| **WL / NetLSD / HPD embeddings + vector median** | the article's existing competitor set, re-used | incomplete keys: they merge non-isomorphic KBs, so the consensus is over a coarsened set |
| **ours: `d_I` matrix → medoid → median-string search → decode** | — | — |

### 3.1 Per-pair throughput — the arithmetic, corrected

`ideas/idea3_median.md` concludes that we lose per-pair throughput badly,
comparing `L² ≈ 384,400` against Hungarian `n³ = 1,000` at `n = 10, m = 20`.
**That comparison uses the character length, and `d_I` does not run on
characters.** `metric_space/distances/isalhg_levenshtein.py` parses `w*_c` into
a token tuple (`tuple(parse(w_star))`, seed-label prefixed) and hands rapidfuzz
the **token sequence**; `L` is therefore the token count. The frozen,
regression-pinned measurement in `../../empirical/correlation.md` is a **median
of 22 tokens at n = 10** (and 8 at n = 6); the 562–642 figure quoted in
`../../theoretical/geometry.md` is characters at the (15,35) cell.

Corrected orders of magnitude at `n = 10`: `L² ≈ 484` against `n³ = 1,000`,
before accounting for rapidfuzz's bit-parallel Myers kernel and for the fact
that the Hungarian route must also *build* an `n × n` substitution-cost matrix
whose entries compare incident fact sets. **We are comparable per pair, not
~380× slower** — and the asymmetry that matters is structural: our cost is
`N` canonicalizations plus `N²` string comparisons, theirs is `N²` assignment
solves, so our expensive part amortizes as `N` grows and theirs does not.

Honest residue: `L` scales with incidence mass (`Θ(m·a)`), so dense structures
push `L²` above `n³`; and `w*_c` canonicalization is genuinely expensive and is
the real bottleneck. **The throughput claim in either direction is pending a
direct token-count sweep** (a 30-second script: canonical string, `parse`, count,
across the size grid). Until it runs, the paper claims neither a throughput win
nor a throughput loss — it claims the guarantee (§3) and the decodability.

**Contract.** Report (i) distance-matrix wall-clock, (ii) the objective value
`Σ_i d(M, K_i)` achieved by each method **measured in a common distance** —
this is essential, since each method optimizes its own — (iii) the exact optimum
where the ILP runs, and (iv) whether the medoid 2-approximation bound holds
empirically for each. If the Hungarian pipeline reaches a better objective in
less time, report it; the surviving claims are the guarantee, the exactness, and
the absent reconstruction step.

## 4. Cross-cutting: the alphabet comparison

If D3′ adopts `Σ_FO`, the comparison `Σ_HG`-reduction versus `Σ_FO` is run on
the same structures through the existing representation-agnostic harness:
single-edit response, ball growth, `ν`, `D̂`, concentration, `w*_c` wall-clock,
and — for each problem — solution quality. Headline question: *does aligning the
token with the unit of semantic change reduce the ≈30–50 % single-edit
response?* Reported either way.
