# T-KBj — the C++ engine poisons `fork`; the canary is a workaround, not a fix

**Status:** OPEN · declared 2026-09-08 15:05 CEST by the Isal-refinement
orchestrator, from the T-KBf audit and the [IsalHG-Fable] review of the A′
decision.

## The defect

After the C++ canonicalizer has run **in-process**, every subsequently forked
child that reaches the C++ path deadlocks. The budget layer cannot tell that
deadlock from a genuinely slow member: both surface as a censoring, so the
rows record a censoring that never happened.

Measured independently 2026-09-08 (fresh process per mode, 4-vertex input,
20 s budget):

| mode | result |
|---|---|
| poison with `canonical_string(backend="cpp")`, then fork a **pure-Python** child | **completes** |
| poison, then fork a **C++** child | **censored** (the hazard) |
| run `ordered_symbols(backend="cpp")` first, then fork a C++ child | **completes** |

So the poisoning is specific to the C++ canonicalizer, hangs only the C++ path,
and the ordered-walk emitter does not cause it. `canonical_fingerprint_rank`
(the `wstar_rank` arm) poisons exactly as `canonical_string` does.

The mechanism is the classic one: state held across `fork` that the child
inherits in an unusable condition. The current mitigation
(`budget.cpp_fork_is_healthy`, and `guarded_budget_call` since T-KBf) is a
**canary**: it detects the poisoned parent and *refuses* rather than reporting a
fiction. Correct, but it converts the defect into refused work instead of
removing it.

## Why it now matters more

Under D-ART5/A′ the paper's headline arm is `w*_c` on the orbit-pruned C++
engine, so every RQ4/RQ5 N×N matrix, the RQ3 medoid loop and the RQ7 sweep run
through the poisoning path. The ordered walk is the only Isal arm that does
not. The censoring-aware matrix route (T-KBf B) therefore drops members for two
different reasons — genuinely over budget, and poisoned-fork refusal — and only
the first is a property of the representation.

## Proposed fix

Use a **fresh interpreter** rather than a forked one for the budgeted call:
`multiprocessing.get_context("spawn")`, or a plain subprocess per member/batch.
A hang inherited through `fork` is not a hang in a fresh interpreter, so only
true >60 s members censor, and RQ4/RQ5's dropped subset becomes exactly the
census RQ1's M3 already reported instead of a larger one.

Costs to weigh before adopting: `spawn` re-imports and re-pickles, which is
negligible against a 60 s budget but not against the ordered walk's 0.5 ms;
the payload and the hypergraph must be picklable; and the change touches the
measurement machinery, so it needs its own differential (same words, same
censoring set on a corpus where nothing is poisoned) before any campaign row is
recomputed under it.

**Do not land this between RQ1 and RQ2.** RQ1 is measured; changing the process
model mid-campaign would make the RQ1 and RQ2 censoring censuses incomparable.

## Acceptance

A differential showing identical words and identical *genuine* censoring under
fork and under spawn on a corpus with no poisoning; then the poisoned-parent
case completing under spawn where it refuses under fork; the canary retained as
an assertion that must never fire. `CPP_ENGINE_ARMS` and `guarded_budget_call`
can then become a guard against regression rather than a routing decision.
