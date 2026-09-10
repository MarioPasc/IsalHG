"""Operations that exist because every word of the fact alphabet is a knowledge base.

The distance layer (:mod:`isalhg.metric_space`) treats a knowledge base as a
point.  This layer treats it as a *word*: it deletes and re-inserts facts,
walks the interior of an edit path, enumerates a ball of strings and reads every
one of them back as a knowledge base.  Nothing here has an analogue for a
representation that is a certificate or a vector, which is the capability
argument the article makes.

What is here
------------
``reach`` --- exact fact-level reach at a bounded radius, by delete-and-match;
``alignments`` --- the deletion pairs that make two knowledge bases isomorphic,
each with an honest isomorphism between the remainders;
``string_ball`` / ``decoded_classes`` --- the ball and its decoded interior;
``alignment_path`` --- the interior words of one optimal Levenshtein alignment;
``coverage_consensus`` --- a representative that is a decoded word rather than
one of the inputs; ``majority_merge`` --- the identity-using reference the
consensus is measured against.

Layering.  This package imports :mod:`isalhg.core`,
:mod:`isalhg.iso_backends.canonical_order` and
:mod:`isalhg.metric_space.distances.fact_levenshtein` (the article's addressing
and its distance, which must have one source of truth) and nothing else inside
the project; in particular it never imports :mod:`isalhg.datasets`, so a corpus
is always something a caller hands in.  ``pynauty`` and ``rapidfuzz`` are
reached through those modules' own guarded imports.
"""

from __future__ import annotations

from isalhg.language.alignment import AlignmentError, alignment_path
from isalhg.language.ball import BallError, decoded_classes, string_ball
from isalhg.language.consensus import (
    BUDGETS,
    AlignmentBudget,
    CandidateScore,
    ConsensusDomainError,
    ConsensusError,
    ConsensusResult,
    IsalKey,
    coverage_consensus,
    in_language_domain,
    isal_fingerprint,
)
from isalhg.language.majority import MajorityMergeError, majority_merge
from isalhg.language.reach import (
    Alignment,
    FactSubset,
    LanguageError,
    ReachError,
    Remainder,
    RemainderIndex,
    alignments,
    compact_constants,
    fact_key_of,
    reach,
    remove_facts,
)

__all__ = [
    "BUDGETS",
    "Alignment",
    "AlignmentBudget",
    "AlignmentError",
    "BallError",
    "CandidateScore",
    "ConsensusDomainError",
    "ConsensusError",
    "ConsensusResult",
    "FactSubset",
    "IsalKey",
    "LanguageError",
    "MajorityMergeError",
    "ReachError",
    "Remainder",
    "RemainderIndex",
    "alignment_path",
    "alignments",
    "compact_constants",
    "coverage_consensus",
    "decoded_classes",
    "fact_key_of",
    "in_language_domain",
    "isal_fingerprint",
    "majority_merge",
    "reach",
    "remove_facts",
    "string_ball",
]
