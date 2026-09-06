# T-KBc — nauty-free ordered walk (option C of the refinement brief)

**Status:** OPEN (future work; not for the TKDE campaign) · declared
2026-09-06 21:11 CEST by the Isal-refinement orchestrator.

## What

The ordered walk `w°` reads nauty's rank only in the last component of its
V-key, to break ties among new members with equal local signature that the
structural keys cannot separate (`theorem_c_ordered_walk.tex` Def. 3.2,
Remark 6.4). The Isal-native replacement is: keep the structural keys, and
at a residual tie branch tie-completely over the tied facts with the
stabiliser-orbit oracle of `wstar_orbit`, taking the shortlex-min completion
(a restricted lex-min over the ordered-walk family). Completeness follows
from Lemma `lem:forest` of `theorem_a_completeness.tex` applied to the
ordered-walk emitter; the value differs from `w°`.

## Why it is filed, not done

It re-introduces a search (with the oracle's cost) exactly where the
ordered walk removed one, and the paper's four-cell ablation
(`ISAL_VARIANT_DESIGN.md` §3b) already separates the order's contribution
from the oracle's. Worth doing only if a reviewer asks for a nauty-free
canonical form with `w°`'s locality.
