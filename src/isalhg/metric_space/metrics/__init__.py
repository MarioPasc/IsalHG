"""Stateless scoring primitives for the metric-space layer.

Non-standard primitives only — standard sklearn / scipy indices
(silhouette, ARI, cophenetic, accuracy) are called directly from
``experiments/`` and are not re-wrapped here (CODE_DESIGN.md §9).

Submodules
----------
association
    Spearman ρ, Pearson r, and mutual information between two distance
    vectors (Layer-1 correlation study).
information
    Fixed-width-code bit-count estimator and incidence-list competitor
    model; compression ratio and Wilcoxon input vector (§3, PROPOSAL.md).
embedding
    Classical (Torgerson–Gower) MDS solve, Kruskal stress-1, and PSD /
    negative-eigenvalue check (A1, PROPOSAL.md §5).
"""
