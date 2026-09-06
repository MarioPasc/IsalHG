# T-KBa — Roles (R4) in the ordered-walk Isal word

**Status:** OPEN · declared 2026-09-06 21:11 CEST by the Isal-refinement
orchestrator (author ruling: "ledger task, later").

## What

Carry argument roles (WD50K: subject / object / qualifier per fact position)
in the Isal word without touching `Σ_HG`. Design already fixed
(`ISAL_VARIANT_DESIGN.md` §8.3, `theorem_c_ordered_walk.tex` does not cover
it):

1. **Fact label = (predicate, role pattern over slots).** The slots of an
   emitted instruction are ordered: `p_1, …, p_i` (placed members in the
   emitter's assignment) then `new_1, …, new_j` (the token's listed order).
   The label written into `V`/`C` is the id of the pair
   `(ℓ_E(e), (role(slot_1), …, role(slot_{i+j})))` in a per-collection
   vocabulary fitted once (like `_resolve_corpus_k`). The decoder assigns
   roles back from the pattern to the nodes it places, so the round trip is
   exact with roles.
2. **nauty's colouring must see the roles**, otherwise the canonical
   labelling is unique only up to role-free automorphisms and the emitted
   patterns are not invariant (the fact-rank roles arm failed M0 with 2,104
   violations for exactly this reason). Extend `core/levi_reduction.py` with
   an incidence-subdivided Levi graph: one node per incidence `(v, e)`
   coloured by `|Σ_V| + |Σ_E| + role`, adjacent to `v` and `e`.
   `canonical_ranks` reads the constant ranks from it unchanged.
3. Theorem C holds verbatim on the role-labelled structure (Lemma C.1 with
   the subdivided Levi graph; the correspondence lemma needs the incidence
   nodes to be determined by their two neighbours, which they are).

## Acceptance

- `ordered_walk(..., roles=...)` round-trips roles on WD50K (300 members,
  pynauty on the subdivided Levi graph as the oracle); invariance under 100
  relabellings; M0 = 0/0/0 on `wd50k66`.
- One RQ1 M1 table on `wd50k66` only: `isal_ow_struct` vs `isal_ow_struct_roles`
  (absolute instructions, normalised, within-≤ 2), so the paper can state the
  price of roles in one sentence.

## Context

`ENCODINGS_WORKED_EXAMPLE.md` §1 (roles in the data), `RESULTS_AUDIT_2026-09-06.md`
§1.2 item 4, D-ART4 R4, `experiments/tkde/corpora.py` (`roles` field:
per-fact list of small ints aligned with argument positions).
