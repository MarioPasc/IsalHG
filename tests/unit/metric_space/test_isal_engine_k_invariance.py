"""The screen/matrix agreement the censored matrix build rests on.

``build_matrix_censored`` screens each member through
``HypergraphDistance.fingerprint`` and then rebuilds the survivors through
``HypergraphDistance.matrix``. For the Isal engine arms the two resolve their
parameters differently -- ``fingerprint`` takes ``k = required_k(H)`` and the
seed-prefix flag from the member, ``matrix`` takes ``k`` as the corpus maximum
and the flag from the whole corpus. The censoring census is therefore only the
census of the matrix that gets built if the two agree.

Measured 2026-09-09 on both campaign corpora (43 ndc members stratified over
``required_k`` 2-9 against the corpus ``k`` of 10): identical words, cost ratio
median 0.96 and max 1.03. The encoder never names a pointer index above the
widest edge's, so surplus pointers are neither written nor searched. These
tests pin that, because a regression would silently make the RQ4/RQ5 matrix a
different search from the RQ1 census that licenses its budget.
"""

from __future__ import annotations

import pytest

from isalhg.core.canonical import required_k
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.metric_space.distances.isal_engine import IsalEngineLevenshtein

pytestmark = pytest.mark.unit

ENGINES = ("rank", "orbit")


def _hypergraph(
    edges: list[tuple[int, ...]], *, n: int, labels: list[int] | None = None
) -> SparseHypergraph:
    """Build a small hypergraph over ``n`` vertices, optionally vertex-labelled."""
    n_labels = 1 if labels is None else max(labels) + 1
    return SparseHypergraph(
        n_nodes=n,
        hyperedges=[frozenset(e) for e in edges],
        n_vertex_labels=n_labels,
        n_edge_labels=1,
        vertex_labels=[0] * n if labels is None else list(labels),
        edge_labels=[0] * len(edges),
    )


@pytest.fixture
def star() -> SparseHypergraph:
    return _hypergraph([(0, 1), (0, 2), (0, 3), (0, 4)], n=5)


@pytest.fixture
def mixed_arity() -> SparseHypergraph:
    return _hypergraph([(0, 1, 2), (0, 3), (1, 2, 3, 4), (2, 4)], n=5)


@pytest.fixture
def labelled() -> SparseHypergraph:
    return _hypergraph([(0, 1, 2), (1, 3), (2, 3, 4)], n=5, labels=[0, 1, 1, 2, 0])


@pytest.mark.parametrize("engine", ENGINES)
@pytest.mark.parametrize("fixture", ["star", "mixed_arity", "labelled"])
@pytest.mark.parametrize("surplus", [0, 1, 3, 6])
def test_word_is_invariant_to_surplus_pointers(
    engine: str, fixture: str, surplus: int, request: pytest.FixtureRequest
) -> None:
    """A ``k`` above ``required_k`` leaves the word unchanged.

    This is what lets the per-member screen certify a member for a corpus-``k``
    matrix build: the two compute the same string.
    """
    H = request.getfixturevalue(fixture)
    own_k = required_k(H)
    per_member = IsalEngineLevenshtein(engine).fingerprint(H)
    at_corpus_k = IsalEngineLevenshtein(engine, k=own_k + surplus).fingerprint(H)
    assert per_member == at_corpus_k


@pytest.mark.parametrize("engine", ENGINES)
def test_matrix_agrees_with_fingerprint_on_a_uniform_label_corpus(
    engine: str, star: SparseHypergraph, mixed_arity: SparseHypergraph
) -> None:
    """``matrix`` distances equal the pairwise distances of the screened words.

    ``matrix`` resolves ``k`` and the seed-prefix flag over the corpus while
    ``fingerprint`` resolves them per member. On a corpus whose members carry a
    uniform number of vertex labels -- which both campaign corpora do, ndc at 4
    and wd50k66 at 1 -- the flag agrees and only ``k`` differs, so the two must
    produce the same matrix.
    """
    from rapidfuzz.distance import Levenshtein

    corpus = [star, mixed_arity]
    distance = IsalEngineLevenshtein(engine)
    built = distance.matrix(corpus)

    words = [distance.fingerprint(H) for H in corpus]
    alphabet = {symbol: index for index, symbol in enumerate({s for w in words for s in w})}
    encoded = [[alphabet[s] for s in w] for w in words]

    assert built[0][1] == pytest.approx(Levenshtein.distance(encoded[0], encoded[1]))
    assert built[0][0] == 0.0


@pytest.mark.parametrize("engine", ENGINES)
def test_seed_prefix_follows_the_label_count(engine: str, labelled: SparseHypergraph) -> None:
    """The augmented fingerprint carries the seed label only on a non-trivial vocabulary.

    The prefix is omitted at ``|Sigma_V| = 1`` (D-TA2 / T-TAb), which is why the
    corpus-level and member-level flags agree on wd50k66 (every member single
    -labelled) and on ndc_classes (every member four-labelled).
    """
    trivial = _hypergraph([(0, 1, 2), (1, 3), (2, 3, 4)], n=5)
    assert trivial.n_vertex_labels == 1
    assert labelled.n_vertex_labels > 1

    distance = IsalEngineLevenshtein(engine)
    first_trivial = distance.fingerprint(trivial)[0]
    first_labelled = distance.fingerprint(labelled)[0]

    assert first_labelled == ("seed", pytest.approx(first_labelled[1]))
    assert first_labelled[0] == "seed"
    assert not (isinstance(first_trivial, tuple) and first_trivial[0] == "seed")
