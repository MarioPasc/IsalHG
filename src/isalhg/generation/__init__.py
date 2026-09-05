"""Sequence models over the fact alphabet, and the serialization they are compared against.

RQ6 asks whether a collection of knowledge bases can be extended with new,
valid, plausible members. The experiment is a controlled comparison of two
serializations under *one* model class:

* :mod:`isalhg.generation.ngram` fits an order-``n`` token n-gram and samples
  from it. Run over fact words, every sample decodes -- not because the model
  learned to be well-formed but because
  :func:`isalhg.core.fact_word.decode_fact_word` is total on the token
  vocabulary. Validity is a property of the language, not of the fit.
* :mod:`isalhg.generation.incidence_baseline` is the same content written as a
  flat incidence list, whose grammar has constraints a sequence model can and
  does break (an id past the declared constant count, an arity-1 fact, a
  repeated fact, a missing terminator). Its decoder rejects; the rejection rate
  is what the comparison measures.
* :mod:`isalhg.generation.fidelity` scores how close a sample set is to the
  collection it was fitted on, and how much of it is new.

The point of the pairing is that the *only* difference between the two arms is
the serialization. Same model class, same order, same smoothing, same fitting
data, same sampler. A difference in validity is therefore attributable to the
language and to nothing else, which is what makes it evidence rather than a
demonstration.
"""

from __future__ import annotations

from isalhg.generation.fidelity import fidelity, jsd, novelty, profile
from isalhg.generation.incidence_baseline import flatten, strict_decode
from isalhg.generation.ngram import TokenNGram

__all__ = [
    "TokenNGram",
    "fidelity",
    "flatten",
    "jsd",
    "novelty",
    "profile",
    "strict_decode",
]
