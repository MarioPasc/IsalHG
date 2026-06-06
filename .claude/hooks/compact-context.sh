#!/usr/bin/env bash
# Compaction recovery hook -- re-injects critical context after /compact

cat <<'CONTEXT'
=== ISALHG COMPACTION RECOVERY ===

PROJECT: IsalHG -- Instruction Set and Language for Hypergraphs
Hypergraphs (hyperedge arity 2..k) with isomorphism-invariant canonical strings.
Sibling projects:
  IsalGraph (/home/mpascual/research/code/IsalGraph)  -- direct precedent
  IsalSR    (/home/mpascual/research/code/IsalSR)     -- DAG sibling

INSTRUCTION SET Sigma_HG (parameterized by k = max hyperedge arity):
  V_{i,j} : new edge linking i existing nodes (p_1..p_i) + j new nodes (after p_1)
            constraints: 1 <= i,j <= k-1 and 2 <= i+j <= k
  C_i     : new edge linking i existing nodes (p_1..p_i); no pointer movement;
            no-op if the edge already exists. constraint: 1 <= i <= k
  P_i     : advance pointer p_i forward in L. constraint: 1 <= i <= k
  N_i     : retreat pointer p_i backward in L. constraint: 1 <= i <= k
  W       : no-op

VM STATE: S = (H, L, p_1, ..., p_k)
  H : partial hypergraph being built
  L : circular doubly-linked list of node IDs
  p_i : index into L (NOT a graph node id)
  Initial: H = {single node}, L = [0], all p_i = 0

CRITICAL INVARIANTS:
  1. Pointers index L, NOT H. Always resolve via cdll.get_value(p_i)
     before passing to any hypergraph operation.
  2. Closed alphabet: every string in Sigma_HG* decodes to a valid hypergraph.
  3. Round trip: S2H(H2S(H)) ~ H (hypergraph isomorphism).
  4. Canonical seed: greedy H2S runs from nodes of MAX lex (xi_1, xi_2, xi_3) only.
  5. V over C in tie-breaking; never swap.
  6. W tokens may appear in canonical strings; do not strip.
  7. Pointer count == k (max arity); mismatch silently corrupts encoding.

CANONICAL ALGORITHM:
  - Node tuple xi(v) = (#neighbors at dist 1, 2, 3).
  - Edge tuple eta(e) = (sum over e's nodes of #neighbors at dist 1, 2, 3).
  - Greedy tie-breaking cascade (in order):
      (a) min lex (sum|delta|, delta_1, ..., delta_k)
      (b) V instructions over C
      (c) among V, min (i, j) lex
      (d) among ties, max eta over the candidate new edge
      (e) same eta rule for C_i (after min i)
      (f) backtracking (algorithm UNSPECIFIED -- open task)
  - Conjecture (UNPROVED): w*_{H1} == w*_{H2} iff H1 ~ H2.

DEPENDENCY RULE:
  isalhg.core     = ZERO non-stdlib deps (stdlib only)
  isalhg.adapters = optional (hypernetx, xgi, hypergraphx)
                    guard imports under try/except ImportError

ENVIRONMENT:
  Conda env: isalhg
  Python:    ~/.conda/envs/isalhg/bin/python
  Tests:     python -m pytest tests/ -v
  Lint:      python -m ruff check src/ tests/
  Types:     python -m mypy src/isalhg/

KEY FILES:
  CLAUDE.md                              -- Project hub
  docs/isalhg_idea.pdf                   -- PI's seed proposal
  src/isalhg/core/                       -- Core implementation (zero deps)
  ~/.claude/projects/-home-mpascual-research-code-IsalHG/memory/
    family_isal_precedents.md            -- Family abstraction summary
    idea_060626.md                       -- Full seed-proposal transcription

OPEN QUESTIONS (from seed proposal):
  1. Backtracking procedure for greedy ties: unspecified.
  2. Value of k: global / input-dependent / adaptive?
  3. Structural-tuple depth: fixed at 3 by analogy with IsalGraph; ablation needed.
  4. Complexity bound for canonical encoding: not derived.
  5. Completeness proof for canonical-string invariant: not produced.

=== END COMPACTION RECOVERY ===
CONTEXT
