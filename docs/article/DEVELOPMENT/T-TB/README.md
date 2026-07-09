# Scope T-TB — Theorem B, stability

The paper's central contribution: an explicit constant `C(k, Δ)` with
`d_I(H, H') ≤ C(k, Δ) · HGED(H, H')`. This is the continuity direction — the map
`H ↦ w*_c(H)` does not amplify a small structural perturbation into a large string
perturbation — and it is what makes MDS, clustering and kNN on `d_I` well-behaved.
The lower bound is provably out of reach (canonical and WL representations are
generically not lower-Lipschitz), so the upper bound is the strongest achievable
form, not a concession. The proof reduces to bounding the single-edit sensitivity
`s(e) = d_I(H, H ⊕ e)`, which forces two problems into the open: a locality lemma
phrased in *relative* CDLL order rather than absolute index, and the avalanche
regime where an edit flips a tie and the encoder's trajectory diverges from the
start. The theorem's `Δ`-dependence is its falsifiable content and the density
sweep (T-M5a) is what tests it.
