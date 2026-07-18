# Scope T-M2 — HGED, the structural edit distance (rescoped role at D-ART2)

Hypergraph edit distance's v3 role is twofold and modest: the exact oracle
(`exact_hged`, with the fidelity twin `qin_hged`) produces the article's single
discussion figure E1' (ours-only ρ on a small connected mini-corpus), and the
Qin cost model (ICDE 2023, Definition 3 verbatim — deleting an arity-`a`
hyperedge costs `a + 1`) prices the perturbation-ladder budgets that the
HGED-free body relies on (`HGED ≤ budget` by construction; G2 ladder response,
A4 scoring). The v2 role — ground truth of a load-bearing correlation study
and head-to-head axis vs competitors — is retired (D-ART2). No public HGED
solver exists, so both solvers here are bespoke; both are property-tested to
agree. This scope also owned the domain gap HGED exposed (optimal edit paths
pass through disconnected hypergraphs, on which `d_I` is undefined) — resolved
by D-CONN1: connected domain, connectivity-preserving generators (T-M2c), and
the path-normalization lemma handed to the stability record.
