# Vocabulary — the shared glossary

*Binding for every file in this folder. If an idea file needs a term not defined
here, it adds it here rather than inventing a local synonym. The project's
standing rule against synonym cycling applies with force: one name per object.*

---

## 1. Structures and knowledge bases

**Signature.** `σ = (P_1, …, P_r)` with arities `a_1, …, a_r ≥ 1`. **Function-free**
throughout (all three PI ideas say so explicitly). Function symbols and constants
of a richer signature are removed by the standard MACE-style *flattening* — a
`j`-ary function becomes a `(j+1)`-ary relation plus totality and functionality
axioms — adopted, not re-invented.

**Structure.** `𝔐 = (D, P_1^𝔐, …, P_r^𝔐)`, `D` finite, `P_i^𝔐 ⊆ D^{a_i}`.
Elements of `D` are **constants** (the PI's word) or **domain elements**;
the two are used interchangeably here because the signature is function-free
and every constant is a domain element.

**Ground fact / ground atom.** An element `P_i(d_1,…,d_{a_i})` of `P_i^𝔐`.
`Facts(𝔐) = ⋃_i {P_i(d̄) : d̄ ∈ P_i^𝔐}`.

**Knowledge base (KB).** A finite set of ground facts, i.e. exactly a finite
`σ`-structure under the closed-world reading (§4). `K` denotes a KB, `𝔐` a
structure; they are the same kind of object and the letter signals provenance
(data vs. model theory).

**Active domain.** `adom(K) = ` the constants occurring in some fact of `K`.
A **bare element** is a domain element not in `adom(K)`.

**Isomorphism.** `𝔐 ≅ 𝔑` iff some bijection `D → D'` carries `P_i^𝔐` onto
`P_i^𝔑` for every `i`. **Isomorphism lemma:** `𝔐 ≅ 𝔑 ⇒ (𝔐 ⊨ φ ⇔ 𝔑 ⊨ φ)` for
every first-order sentence `φ` (Ebbinghaus–Flum; Hodges). This is what makes
working modulo isomorphism sound and what makes a *metric on isomorphism
classes* the semantically correct object: structures at distance 0 are
indistinguishable by any sentence.

**Countermodel.** `𝔐` is a countermodel of `φ` iff `𝔐 ⊭ φ`. `Mod(φ)` is the
class of finite models of `φ`, taken **up to isomorphism** throughout.

## 2. The distance family — five distinct objects, never conflated

This is the most important section in the folder. The three PI analyses use
"distance" for objects with very different complexity, and our own distance is a
sixth. Names are binding.

| Name | Definition | Iso-invariant? | Metric? | Cost |
|---|---|---|---|---|
| `d_△` | `\|Facts(A) △ Facts(B)\|` on a **fixed, shared naming** of the domain (Dalal distance, propositional) | no — depends on the naming | yes, on named structures | `O(\|Facts\|)` |
| `d_≅△` | `min_{σ bijection} \|σ(Facts(A)) △ Facts(B)\|` — the iso-invariant lift, for equal domain sizes | **yes** | yes | **NP-hard**; `= 0` test is GI-hard |
| `d_SED` | structure edit distance: `d_≅△` plus charged insertion/deletion of domain elements | **yes** | yes | **NP-hard** |
| `HGED` | Qin et al. (ICDE 2023) Definition 3, unit costs, over hypergraphs: insert/delete a cardinality-0 node or hyperedge; extend/reduce a hyperedge by one node; substitute a label | **yes** | yes | **NP-hard**; our exact oracle peaked at 8.5 h / 55 GB per 630-pair block |
| `d_I` | **ours**: `d_Lev(w*_c(E(A)), w*_c(E(B)))` | **yes** (Theorem A) | **yes** (Corollary A) | one canonicalization per structure, then `O(\|w\|²)` per pair — **no alignment search** |
| `d_I^⊥` / `d_I^Σ` | the structural (trivial-vocabulary) and label-aware members of the `d_I` family | yes | yes | as `d_I` |

**Four facts that must never be blurred.**

1. **`d_SED` is the distance the three PI ideas are written in.** "Closest KB",
   "symmetric difference of ground atoms", "graph edit distance" — all `d_SED`
   or its fixed-size restriction `d_≅△`.
2. **`d_I` ≠ `d_SED`.** Measured: Spearman ρ = 0.622 (`N = 6,921` pairs, E1′
   mini-corpus) against exact `HGED`. There is an unconditional envelope
   `d_I ≤ m(1+kn)·HGED` — very loose — and an argument that **no bi-Lipschitz
   relation is achievable** for any complete invariant. Any claim that `d_I`
   *is* the fact distance is false and would not survive review.
3. **Knowledge bases are labelled**, so the relevant family member is `d_I^Σ`,
   not the `d_I^⊥` under which the article's existing geometry (Stratum C, the
   `ν`/`D̂`/hubness tables) was measured. Those two are members of different
   families and are not comparable. **The logic program needs its own geometry
   measurement.**
4. **Qin's cost model already resolves the PI's metric fork.** `src/idea1.txt`
   asks whether the domain itself is charged: *(a) fact-level / active-domain*
   (only facts cost; a bare element does not exist) versus *(b) element-level +
   fact-level* (adding or removing a constant is charged separately). Qin's
   Definition 3 charges cardinality-0 node insertion/deletion at unit cost
   independently of hyperedge edits, so **`HGED` is fork (b)**, and fork (a) is
   its restriction to structures with no bare elements. We already own an exact
   oracle and a cost model for the harder fork.

**Naming rule.** When a file says "distance" without qualification it means
`d_I`. Every other distance is named.

### 2.1 `d_amb` — the ambient reach distance (added 2026-08-12; do not conflate with `d_I`)

*This entry exists because the first draft of `risks.md` §2 conflated two
quantities and both idea agents inherited the error.*

For a set `X` of structures, the **ambient reach distance** from `K` is

```
d_amb(K, X)  =  min { d_Lev( w*_c(E(K)), w ) : w ∈ Σ*, S2H(w) ∈ X }
```

— the fewest **token edits to the canonical string of `K`** that produce *any*
word decoding into `X`. It is the quantity that governs **search feasibility**
for ball enumeration.

**`d_amb` is not `d_I`, and it can be far smaller.** `d_I(K,K')` compares two
*canonical* strings; `d_amb` allows the target to be reached through a
**non-canonical** word. Since `S2H` is many-to-one, the preimage of `K'` is a
large set of words, and the nearest member of that preimage may sit far closer
to `w*_c(E(K))` than `w*_c(E(K'))` does. There is no contradiction: by the
triangle inequality `d_I(K,K') ≤ d_amb(K,{K'}) + d_Lev(w, w*_c(E(K')))`, and
the second term absorbs the difference.

**Concretely.** Inserting one `C[le;i]` token into `w*_c(E(K))` at a point where
the pointers already sit yields `d_amb = 1` for the structure "`K` plus that one
hyperedge", *even though* `d_I` between the two canonical forms is ≈30–50 % of
the string (the measured avalanche). The avalanche bounds ranking by `d_I`; it
does not bound `d_amb`.

**What does bound `d_amb`: pointer displacement.** A `C` token acts on the
current pointer configuration, so the facts reachable at small `d_amb` are those
whose vertices lie near the pointer trajectory of `w*_c(E(K))`; reaching an
arbitrary fact costs `P`/`N` tokens proportional to CDLL displacement. So
`d_amb` for one-fact neighbours is `1 + (displacement)`, and its distribution is
**measurable by a constructive upper bound** — build the word that inserts the
needed pointer moves plus the construction token and count its length. No search
is required to obtain the bound. This is gate **G-L3** (`data.md` §6).

## 3. Cost functions on structures

- **`cost(𝔐) = |D| + Σ_i |P_i^𝔐|`** — the objective of the original
  minimal-countermodel problem (P-MIN): domain size plus number of true ground
  atoms. This is the PI's original criterion.
- **Weighted variants.** Per-relation atom weights and a separate constant
  weight `c` are the natural generalization (`src/idea2.txt` writes
  `|Facts △ Facts| + c·(domain-size change)`). Out of scope for the first pass;
  named here so idea files do not reinvent it.
- **Cardinality-minimal vs subset-minimal.** Cardinality-minimal gives a single
  clean optimization; subset-minimal gives an incomparable frontier
  (Katsuno–Mendelzon; Winslett's PMA is the subset-minimal variant of Dalal's
  cardinality-minimal operator). **This folder is cardinality-minimal
  throughout** unless a file says otherwise.

## 4. The two semantic readings — decide once, state always

`src/idea2.txt` is right that this fork changes the problem more than any other
choice.

- **Closed-world / model reading.** A KB *is* one structure; `K ⊭ T` means that
  single structure falsifies `T`. Arbitrary first-order `T` is meaningful and the
  target is the nearest *model* of `T`. **This folder is closed-world.** It is
  forced on us: `w*_c ∘ E` encodes one structure, not a theory.
- **Open-world / theory reading.** `K ⊨ T` means every model of the ground facts
  satisfies `T`. By Łoś–Tarski / homomorphism preservation, ground facts can only
  entail sentences preserved under extensions, so the only interesting `T` is
  existential-positive — a union of conjunctive queries — and idea 2 collapses to
  *"add the cheapest set of facts that creates a query match"*, i.e. abduction /
  minimum-cost match completion.

An idea file that changes the reading must say so in its first paragraph.

## 5. Encoding vocabulary

- **`E`** — a faithful encoding of a `σ`-structure as a labelled hypergraph.
  `E1` is the direct/symmetric-fragment encoding, `E2` the anchored incidence
  encoding; see [`encoding.md`](encoding.md).
- **`Σ_HG`** — the current instruction alphabet (`V`, `C`, `P`, `N`, `W`).
- **`Σ_FO`** — a hypothetical purpose-built alphabet for relational structures,
  design options F0–F4 in [`encoding.md`](encoding.md). **Not yet designed; not
  yet decided (D3′).**
- **`w*_c`** — the frozen unpruned tie-complete lex-min canonical string.
  **Alphabet-scoped**: `w*_c` over `Σ_HG` and `w*_c` over `Σ_FO` are different
  objects, and every result is tagged with its alphabet.
- **`F(H) = (seed vertex label, w*_c(H))`** — the augmented fingerprint. On
  labelled inputs (which KBs always are) the seed label is *not* optional;
  comparing bare `w*_c` is a false positive.

## 6. Search vocabulary

- **Ball.** `B_r(w) = {w' ∈ Σ*: d_Lev(w,w') ≤ r}`. Its **collapse ratio** is
  `|B_r(w)|` divided by the number of distinct isomorphism classes among
  `S2H(B_r(w))` — the redundancy of the move operator (gate G-B1).
- **Move operator.** Single-token edit. Closed by P1/P6: every result decodes to
  a connected object.
- **Frontier key.** The value used to deduplicate visited states. Ours is `F(·)`;
  a Levi-nauty certificate is a **faster pluggable alternative** and the paper
  says so.
- **Ambient space.** All of `Σ*`, as opposed to the *canonical image*
  `{w*_c(H)}`. The distinction carries the paper's central argument: a
  certificate space has only the image; ours has the whole alphabet.
