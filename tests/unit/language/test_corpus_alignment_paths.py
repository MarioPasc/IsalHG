"""The decodability exhibit on real corpora (`DESIGN.md` RQ6 step 4, H6c).

Fifty random pairs of real members from each of ``wd50k66`` and
``ndc_classes``: take the two canonical words, walk one optimal Levenshtein
alignment, and decode every interior word.  Totality is a theorem, so the
assertion is the point --- a single failure would mean the decoder is not what
`DESIGN.md` G2 claims.  What the run *measures*, and prints for the record, is
the shape of those interiors: path length, number of interior words, and the
fraction that decode to a *connected* knowledge base (the language allows
disconnected ones, and on real pairs most interiors are disconnected, which is
the honest version of the figure's caption).

Marked ``slow`` and skipped when the frozen corpora are not on this machine.
"""

from __future__ import annotations

import os
import random
from pathlib import Path

import pytest

from isalhg.core.fact_word import decode_fact_word
from isalhg.language.alignment import alignment_path
from isalhg.metric_space.distances.fact_levenshtein import fact_word, word_distance

pytestmark = pytest.mark.slow

pytest.importorskip("pynauty")
pytest.importorskip("rapidfuzz")

N_PAIRS = 50


def corpus_root() -> Path | None:
    """Return the frozen-corpora root, or ``None`` when it is not present."""
    raw = os.environ.get(
        "ISALHG_RESULTS_ROOT",
        "/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/IEEETKDE",
    )
    root = Path(raw) / "corpora"
    return root.parent if root.is_dir() else None


@pytest.mark.parametrize("name", ["wd50k66", "ndc_classes"])
def test_every_interior_word_decodes(name: str) -> None:
    root = corpus_root()
    if root is None:
        pytest.skip("frozen corpora are not available on this machine")
    from experiments.tkde.corpora import load_collection

    collection = load_collection(name, root)
    records = list(collection)
    assert len(records) >= 2

    rng = random.Random(12345)
    n_types, n_preds = collection.n_types, collection.n_preds
    words = {}

    def word_of(index: int):
        if index not in words:
            record = records[index]
            words[index] = fact_word(record.to_hypergraph(n_types=n_types, n_preds=n_preds))
        return words[index]

    interiors = 0
    connected = 0
    path_lengths: list[int] = []
    for _ in range(N_PAIRS):
        i, j = rng.sample(range(len(records)), 2)
        first, second = word_of(i), word_of(j)
        distance = word_distance(first, second)
        interior = alignment_path(first, second)
        assert len(interior) == max(distance - 1, 0)
        path_lengths.append(distance)
        for step in interior:
            decoded, _ = decode_fact_word(step, n_types=n_types, n_preds=n_preds)
            interiors += 1
            connected += int(decoded.is_connected())

    assert interiors > 0
    print(
        f"\n{name}: {N_PAIRS} pairs, path length min/median/max "
        f"{min(path_lengths)}/{sorted(path_lengths)[len(path_lengths) // 2]}/{max(path_lengths)}, "
        f"{interiors} interior words, all decoded, "
        f"{connected} connected ({connected / interiors:.3f})"
    )
