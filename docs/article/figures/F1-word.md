# F1 — A hypergraph is a word

**Spine position:** Foundation / methods. The paper's first figure.
**Status:** to build; all machinery exists in `src/isalhg/viz`.

---

## 1. Why this figure

The article's premise is a sentence — *a hypergraph is a word* — and the reader
cannot evaluate a single later claim without having watched the encoder run
once. Everything downstream (`d_I` is a token edit distance; the alphabet is
closed so intermediates decode; `|w*_c|` scales with incidence mass) is
mechanical consequence of the virtual machine. One page of machinery buys the
rest of the paper.

This is didactic, not decorative: it is where the reader learns that the string
is a *construction program*, not a serialization. That distinction is what
makes F3's corridor and F5's bounded sensitivity intelligible.

## 2. Panel specification

**Panel (a) — the object.** One small design hypergraph, drawn with coloured
hyperedges. Use **STS(7) (Fano)**: `n = 7`, `m = 7`, arity 3, `|w*_c| = 121`
characters — recognisable, small enough to read, and it recurs in F3 and F5.

**Panel (b) — the machine.** Four to six columns sampled from the H2S trace.
Each column stacks:
- the CDLL ring `L` with the `k` pointers marked at their current slots
  (`viz.cdll_view.draw_cdll_ring`),
- the token emitted at that step, highlighted in the running strip
  (`viz.instruction_view.draw_instruction_strip`),
- the partial hypergraph built so far (`viz.hypergraph_view.draw_hypergraph`),
with new vertices and the new hyperedge emphasised.

`viz.composite.steps_figure` already composes exactly this; `_sample_indices`
picks the columns.

**Panel (c) — the word.** The complete `w*_c(H)` as one instruction strip,
tokens coloured by the hyperedge each `V`/`C` creates (`viz.style.
color_for_token`), with the pointer-motion tokens in a neutral tone. An
annotation gives `|w*_c|` in tokens and the alphabet size
`|Σ_HG(3)| = 13`, tying directly to the compactness subsection
(`B_IsalHG = |w| · log₂|Σ_HG(k)|`).

**Optional inset — the inverse.** A single arrow `S2H` from the string back to
the hypergraph, captioned "total on `Σ_HG(k)*`". This plants the closed-alphabet
property early so F3 can cash it.

## 3. What the caption must say

The four facts the rest of the paper leans on, in order:
1. The string is a construction program executed against a CDLL + `k` pointers.
2. The alphabet is closed: S2H is total, so *every* word denotes a connected
   hypergraph.
3. `w*_c` is the tie-complete lex-min over an isomorphism-invariant seed set —
   hence a complete invariant (Theorem A), hence `d_I` is a metric on
   isomorphism classes (Corollary A).
4. `d_I` counts **token** edits, not character edits.

## 4. Data provenance and generating code

- Fixture: `isalhg.datasets.synthetic.sts_catalog` (order 7) or
  `known_design_catalog` `sts7`.
- Trace: `isalhg.core.canonical.canonical_string` with trace capture;
  `viz.trace_io.load_trace_for_viz` if replaying a stored trace.
- Drawing: `viz.{cdll_view, instruction_view, hypergraph_view, composite,
  style}`; `viz.style.apply_ieee_style()` for the venue's typography.
- Generating routine: `experiments/analysis/figures/word_figure.py`.
- Output: `docs/article/figures/src/F1_word.pdf`.

## 5. Acceptance check

1. The token count printed in panel (c) equals `len(parse(w*_c))` for the
   fixture, and the character length matches `|w*_c| = 121`.
2. Replaying panel (b)'s tokens through S2H reproduces panel (a) up to
   isomorphism (assert in the generating routine, not by eye).
3. The figure is legible at single-column width in greyscale (hyperedge
   identity carried by hatch or outline, not colour alone).
