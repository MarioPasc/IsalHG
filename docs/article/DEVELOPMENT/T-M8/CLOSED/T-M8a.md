# T-M8a — Label-conditional metric family: Remark + per-corpus metric annotation
**Declared:** 2026-07-22 11:56 CEST
**Status:** DONE
**Depends on:** nothing code-side (doc task; Theorem A already covers arbitrary
vocabularies). The optional label-stripped HIC computation lives in T-M7g, not
here.
**Origin:** 2026-07-22 REVIEW pass (`docs/article/REVIEW/APPROACH_RIGOR.md`
§2), directed by Mario — including the decision to resolve this as a **small
formal result, not prose** (article length). `d_I` on trivial-vocabulary
synthetic corpora is purely structural; on HIC the labels enter via
`LabelVocabulary`, so the real-data ν/D̂ rows measure a different member of the
metric family than the synthetic rows — currently unstated anywhere.
**Context to read first:**
- `docs/article/REVIEW/APPROACH_RIGOR.md` §2 — the Remark text skeleton and the
  consequential-edits list
- `docs/article/theoretical/stability.md` §1 — Theorem A + Corollary A + the
  existing `d_I^{k,h,Σ}` index-family note (the Remark extends this, it does
  not duplicate it)
- `docs/article/H2S_S2H.md` — the augmented fingerprint `F(H)` and
  `LabelVocabulary` threading (why the family statement is already proved)
- `docs/article/theoretical/geometry.md` §measured tables +
  `docs/article/empirical/applications.md` HIC exhibit — the tables to annotate
**Description:** (1) Draft the **Remark/Proposition (label-conditional metric
family)** and place it in `theoretical/stability.md` §1 immediately after
Corollary A: for each vocabulary `Σ`, `d_I^{k,h,Σ}` is a metric on
label-preserving isomorphism classes of connected `Σ`-labelled hypergraphs of
arity ≤ k; the trivial vocabulary recovers the structural metric on unlabelled
hypergraphs; members from different vocabularies are incomparable. Check the
labelled↔label-forgotten comparison clause: include it only if a one-line
argument or counterexample is immediate; otherwise state the family without it
(the family statement alone is already established by Theorem A over arbitrary
vocabularies — no new proof volume work). (2) Annotate every reported `d_I`
value: geometry table + application tables get a metric column/footnote —
`d_I^⊥` (structural) for all synthetic corpora, `d_I^Σ` (label-aware) for HIC.
(3) One sentence in the HIC exhibit stating the two-objects reading and noting
it as a candidate explanation for the lower real-data D̂ (≈10–11). (4) File the
label-stripped-HIC PI decision in `DEVELOPMENT/DECISIONS.md` (execution owned
by T-M7g).
**Acceptance:** the Remark is in `stability.md` §1 with its status honestly
marked (proved-by-Corollary-A for the family; comparison clause either argued,
counter-exampled, or omitted); every `d_I` value in `geometry.md` and
`applications.md` is unambiguously attributable to `d_I^⊥` or `d_I^Σ`; no
cross-vocabulary values pooled or directly compared anywhere in the prose; the
DECISIONS.md entry exists; process artifacts (task ids, dates) stay out of the
reasoning prose per the doc-split convention.
**Out of scope here:** computing the label-stripped HIC row (T-M7g); any
encoder or `w*_c` change; extending the proof volume.

---

**Closing note (2026-07-22).**

Acceptance checks:

1. **Remark placed** in `stability.md` §1 immediately after Corollary A, before
   the existing Index family paragraph. Proved-by-Corollary-A status stated
   explicitly (Theorem A holds for arbitrary Σ; augmented fingerprint F(H)
   computed under any LabelVocabulary; Corollary A's three axioms carry through
   per fixed (k,h,Σ) with label-preserving isomorphism). Comparison clause
   omitted: the canonical form w*_c itself changes across vocabularies (labels
   enter seed cascade and tie-breaking), so no simple monotone relation between
   d_I^Σ and d_I^⊥ holds in general — not a one-liner.

2. **Metric column added** to geometry.md §3 table: `d_I^⊥` for all four
   planted rows, `d_I^Σ` for both HIC rows. Every reported d_I value in
   applications.md annotated: G1 planted section (d_I^⊥), A1 intro + table
   header row (d_I^⊥), A2 planted (d_I^⊥) and HIC (d_I^Σ) sections, A3
   planted (d_I^⊥) and HIC (d_I^Σ), A4 ladder pool (d_I^⊥), Runtime
   section (d_I^⊥).

3. **Two-objects sentence** added in geometry.md §3 after the planted/HIC
   D̂ comparison: planted rows use d_I^⊥, HIC rows use d_I^Σ; these are
   different family members and are read as two objects; lower real-data D̂
   is consistent with a vocabulary effect as well as structural differences.
   Also stated in applications.md A1 (HIC sentence).

4. **DECISIONS.md OD7 filed**: label-stripped HIC re-run pending PI; execution
   owned by T-M7g if adopted.

5. **No process artifacts** in the reasoning prose (stability.md, geometry.md,
   applications.md): citations reference documents and section names only.
   No task ids or dates appear in those files.

No code changes. No pytest run (doc-only task). No ruff/mypy (no Python changed).
