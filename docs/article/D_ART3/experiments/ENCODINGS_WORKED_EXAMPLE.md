# The three encodings on one real record — a worked example

*Written 2026-09-06 for the first author. Every string below was produced by
the shipped encoders on a frozen record; reproduce with
`scripts/diagnostics/encodings_worked_example.py` (environment `isalhg`,
~10 s). Companion to `RESULTS_AUDIT_2026-09-06.md` §1.2 item 1.*

## 1. The data

A knowledge base is one Wikidata entity with its statements. Record
`Q1002100` of `wd50k66` (class label: film):

```
P1411(Q1002100, Q1659591)     nominated for
P161 (Q1002100, Q23794603)    cast member
P161 (Q1002100, Q89284)       cast member
P364 (Q1002100, Q652)         original language
P86  (Q1002100, Q967230)      composer
```

Six *constants* (the film and five entities it points to) and five *facts*
(a predicate over a set of constants). The Wikidata ids are carried for
evaluation only; the methods never read them. Two knowledge bases are the
same object when one becomes the other by renaming constants, so every
representation must ignore names. In `ndc_classes` the constants are a
pharmacologic class and its products, the facts are co-formulation sets;
same shape.

Terminology used everywhere: **constant** = vertex (its *type* is the vertex
label; WD50K has one type, "untyped"); **fact** = hyperedge (its *predicate*
is the edge label); **knowledge base** = labelled hypergraph.

## 2. The three encodings of this record

### 2.1 The fact-rank word (adopted, arm `fact_rank`)

```
T T T T T T  F[P1411;0,1] F[P161;1,4] F[P161;1,5] F[P364;1,2] F[P86;1,3]
```

One `T` token per constant, in *rank* order, carrying its type. One `F`
token per fact: the predicate and the ranks of its constants, sorted. The
ranks here are

```
Q1659591 → 0   Q1002100 → 1   Q652 → 2   Q967230 → 3   Q23794603 → 4   Q89284 → 5
```

and they come from `pynauty.canon_label` on the coloured Levi graph of the
record (`iso_backends/canonical_order.py::canonical_ranks`). The film gets
rank 1 because of its structure (it touches every fact), never because of
its name. Length `n + m = 11`. The decoder is total: any sequence of `T` and
`F` tokens decodes to a knowledge base (`core/fact_word.py`).

### 2.2 The nauty certificate (arm `nauty_cert`)

132 bytes: the canonical adjacency matrix of the same Levi graph (11 nodes:
6 constants + 5 fact-nodes), packed by nauty, prefixed by the colour
signature. As rows (`nauty_cert_rows`): `((0,6), (0,6,7,8,9,10), (0,9), …)`
— row 1 is the film, adjacent to all five fact-nodes 6–10. **Same canonical
labelling as 2.1, written as a matrix instead of a fact list.** No decoder:
an edited byte string is the certificate of nothing.

### 2.3 The pointer word `w*_c` (arm `pointer` / `isalhg_levenshtein`)

```
V[56;1;1;0] V[78;1;1;0] V[78;1;1;0] V[212;1;1;0] V[336;1;1;0]
```

Five instructions for the IsalHG machine (20 symbols once the fields are
split): "create a fact with predicate 56 over 1 existing node and 1 new node
of type 0", and so on. This is the program `H2S` emits, canonicalised by the
tie-complete lex-min over iso-invariant seeds; Theorem A is about this
string. **It is computed by `core/canonical.py` alone and never calls nauty
or the ranks of 2.1** — the pointer alphabet addresses nodes by moving
pointers, so it needs no names and no ranks at all. Only `V` appears here
because the record is a star of binary facts, each reaching a fresh node;
the edited record below shows `N` and `C`.

### 2.4 Invariance check

Rename the six constants by the permutation `[4, 0, 5, 3, 1, 2]` and
re-encode: the fact word, the certificate and the pointer word all come back
byte-identical. All three are complete isomorphism invariants; each by its
own theorem (2.1 and 2.2 by nauty's canonical labelling; 2.3 by Theorem A).

## 3. One edit

**Insert `P161(Q1002100, Q652)` over existing constants.**

| encoding | before | after | Levenshtein | what changed |
|---|---|---|---|---|
| fact-rank word | 11 tokens | 12 | **3** | one new `F` token, plus `F[P364;1,2]→F[P364;1,3]` and `F[P86;1,3]→F[P86;1,2]` because nauty's order of `Q652` and `Q967230` swapped (the *order shift* RQ1 flags; with no shift the cost is exactly 1) |
| nauty certificate | 132 bytes | 140 | 16 | matrix rows re-packed |
| certificate as rows | 11 rows | 12 | 8 | |
| pointer word | 20 symbols | 24 | 5 | the program becomes `V[56;1;1;0] V[78;1;1;0] V[78;1;1;0] V[78;1;1;0] V[336;1;1;0] N[1] N[1] C[212;2]`: the walk changed, a pointer retreats twice and the last fact is closed with `C` over existing nodes |

**Insert `P161(Q1002100, NEW)` that adds a constant.**

| encoding | Levenshtein |
|---|---|
| fact-rank word | **2** (one `T`, one `F`; no order shift) |
| nauty certificate | 25 bytes |
| certificate as rows | 8 |
| pointer word | 4 |

On this six-constant record the pointer alphabet is not dramatically worse;
the campaign averages are (normalised single-edit response, constant set
preserved): fact-rank 0.16–0.23, pointer 0.49–0.79, and above ~20 facts the
pointer word times out where the fact word costs 0.3 ms.

## 4. What this shows

- **`fact_rank` and `nauty_cert` are two serialisations of one canonical
  form.** Both start from the same `canon_label` call. They differ in
  granularity (one token per fact vs packed matrix bytes) and in having a
  decoder (total vs none). Every RQ1 stability number is the granularity;
  every RQ3/RQ6 result is the decoder.
- **The pointer word is a third, independent invariant.** It is the Isal
  machine. It needs neither nauty nor ranks. It lost RQ1 on stability and
  RQ7 on cost, which is why the PI approved replacing it.
- **What the paper may claim.** The language (closed alphabet, total decoder,
  Levenshtein metric on isomorphism classes) and the fact-granular
  serialisation. Not the canonical form, which is nauty's in the shipped
  encoder.

## 5. Three questions from the first author, answered

**Q1. Why is the rank needed? What happens without it?** An `F` token must
say *which* constants a fact is over. If it says so by name (`Q652`), the
word changes under renaming, distance to a renamed copy is not zero, and
the representation is neither an invariant nor a metric on isomorphism
classes (RQ1 M0 would show false splits everywhere). So the address must be
a function of structure alone. Three ways to get one: (i) a canonical order
of the constants — the rank (from nauty here); (ii) a content hash of the
constant — degree key, local key, refinement colour (RQ1 arms C, D, D1: all
exact, all far less stable, because the hash of every constant changes at
every edit); (iii) **no address at all** — the pointer alphabet, which never
names a node and reaches it by moving pointers. That third way *is* the
original IsalHG idea; its price is that the string is a path, and a path
changes globally under a local edit.

**Q2. An ablation with IsalHG's own canonical order instead of nauty's.**
Worth running, and cheap to specify. The pointer word `w*_c` visits the
constants in a definite order (the order in which `V` creates them), and
that order is iso-invariant up to an automorphism in exactly the sense
nauty's is, so `fact_rank_isal := encode_fact_word(H, order from w*_c)` is
also a complete invariant. The two words will **differ**: canonical is not
unique, it is one canonical form per convention, so the rank vectors and
therefore the `F` tokens differ, and three things must be measured rather
than assumed — exactness (M0, expected clean), single-edit stability (M1;
expected worse, because the seed cascade of `H2S` moves under edits — the
avalanche measured at T-M4b), and cost (M3; expected seconds and 6–12 %
censoring on WD50K, since it inherits `w*_c`'s envelope). If the isal-ordered
word matched nauty's stability, the paper would be nauty-free; if it does
not, the ablation answers the reviewer's "is nauty doing the work?" with a
number. Either outcome is worth a table in the supplement. Scope: the RQ1
M0/M1/M3 pass with one added arm, restricted to the constant-preserving
subset if the budget is tight.

**Q3. "The representation must always be the pointer word, and we must show
fact-rank + pointer-word beats fact-rank, otherwise IsalHG is useless."**
Two corrections and one reframing.

- *There is no "fact-rank + pointer-word".* The pointer word does not use
  the rank (verified: the pointer encoder never imports nauty or the rank
  helper). They are alternatives, not layers. The only composite that
  exists is the one in Q2, which goes the other way (isal order → fact
  word).
- *Running every experiment on the pointer word contradicts the ratified
  scope and the measurements.* The PI set the criterion (similar knowledge
  bases at small Levenshtein distance) and authorised the alphabet change
  when the pointer word failed it (0.57 vs 0.20 normalised response). The
  pointer word is also censored on 6–12 % of WD50K members and times out
  above ~20 facts (RQ7), so an all-pointer campaign could not even cover the
  corpora. RQ1 is the experiment that establishes this, and it is in the
  main text as the motivation.
- *IsalHG is not the virtual machine; it is the thesis "a hypergraph is a
  word, and every word is a hypergraph".* The pointer alphabet was its first
  instantiation (procedural: a program). The fact alphabet is its second
  (declarative: a fact list under a canonical address map), and it keeps
  every property the thesis needs — closed alphabet, total decoder,
  Levenshtein metric on isomorphism classes — while gaining the locality
  the PI asked for. What the paper must prove is not "pointer beats
  rank" but "a *language* beats a *certificate*": that is RQ3 (a consensus
  that is a decoded word no member wrote), RQ6 (generation with validity by
  theorem, alignment interiors that decode) and the capability matrix,
  against `nauty_cert`, which has the same canonical form and no language.
  Those are the experiments where IsalHG is or is not useful, and they are
  the strongest results of the campaign. Whether the fact alphabet should
  still carry the name "instruction set" is a naming decision for the PI;
  scientifically it is an Isal language without the machine.
