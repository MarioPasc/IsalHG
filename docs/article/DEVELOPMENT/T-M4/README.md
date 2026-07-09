# Scope T-M4 — corpora and scoring primitives

The applications need hypergraphs whose class structure is known and *not*
trivially recoverable. The obvious shortcut — take iso-class representatives and
generate `permute()` copies as class members — is invalid: permuted copies are
isomorphic, so `d_I = 0` within class by construction and any clustering or kNN
scores perfectly for a reason that says nothing about the metric's geometry. Hence
the planted-family generator: seed motifs plus independent seed-stable
perturbations, giving non-isomorphic within-family members at small controllable
HGED, with family as the label. This scope also owns the real-world anchor (the
HIC atlas, the only cohort member with genuine whole-hypergraph class labels and
many instances per class) and the `metric_space/metrics/` primitives the
experiments score with: association, information content in bits, and the
classical-MDS solve.
