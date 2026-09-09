"""End-to-end cover for RQ4's and RQ5's units against a censored arm (D-KBf2).

The pure helpers are pinned elsewhere; what this file exercises is the code that
turns a survivor set into matrix rows -- ``arm_rows = [row_of[id] ...]`` -- which
is where indexing a short matrix by position in the frozen order would silently
score the wrong members. The collection is synthetic and injected into the
runners' per-process cache, so no corpus and no cached campaign matrix is
needed.

The load-bearing assertion is a *differential* one: a censored arm whose
survivors carry the same distances must score exactly what an uncensored arm
restricted to those same members scores. Reading a short matrix positionally
passes neither.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from experiments.tkde import rq5
from experiments.tkde.matrices import censoring_path, collection_cache_dir
from isalhg.datasets.kb.base import KBCollection, make_record
from isalhg.metric_space.toolkit.matrix import cache_paths, member_order_sha1

pytestmark = pytest.mark.unit

COLLECTION = "toy"
# Above geometry_row's hubness floor (k = 10 needs 11 rows) even after
# censoring, so the test measures the id alignment rather than that boundary.
N_MEMBERS = 24
LABELS = ("Q5", "Q11424")


@pytest.fixture
def collection() -> KBCollection:
    """A dozen tiny connected records over two Wikidata-like classes."""
    records = []
    for index in range(N_MEMBERS):
        record = make_record(
            f"m{index:02d}",
            4,
            (0,) * 4,
            ((0, (0, 1)), (0, (1, 2)), (0, (2, 3))),
            constant_ids=tuple(f"m{index:02d}c{c}" for c in range(4)),
            label=LABELS[index % len(LABELS)],
            meta={"n_types": 1, "n_preds": 1},
        )
        assert record is not None
        records.append(record)
    return KBCollection(
        name=COLLECTION, records=tuple(records), type_names=("t",), pred_names=("p",)
    )


def _distances(ids: tuple[str, ...]) -> np.ndarray:
    """A metric whose value depends only on the member ids, never on position."""
    codes = [int(kb_id[1:]) for kb_id in ids]
    matrix = np.zeros((len(ids), len(ids)), dtype=np.float32)
    for i, a in enumerate(codes):
        for j, b in enumerate(codes):
            if i != j:
                matrix[i, j] = float(abs(a - b) + 1)
    return matrix


def _write_arm(root: Path, arm: str, kept: tuple[str, ...], censored: tuple[str, ...]) -> None:
    cache_dir = collection_cache_dir(root, COLLECTION)
    cache_dir.mkdir(parents=True, exist_ok=True)
    matrix_path, manifest_path = cache_paths(cache_dir, arm)
    np.save(matrix_path, _distances(kept))
    manifest_path.write_text(
        json.dumps({"arm": arm, "n": len(kept), "member_order_sha1": member_order_sha1(kept)}),
        encoding="utf-8",
    )
    if censored:
        censoring_path(cache_dir, arm).write_text(
            json.dumps(
                {
                    "arm": arm,
                    "n_requested": len(kept) + len(censored),
                    "n_censored": len(censored),
                    "member_ids": list(kept),
                    "censored_ids": list(censored),
                    "member_order_sha1": member_order_sha1(kept),
                }
            ),
            encoding="utf-8",
        )


ALL_IDS: tuple[str, ...] = tuple(f"m{i:02d}" for i in range(N_MEMBERS))


class TestRq5Unit:
    @staticmethod
    def _unit(collection: KBCollection, arms: tuple[str, ...], seed: int = 0) -> Any:
        experiment = rq5.Experiment(
            name="toy_full",
            collection=COLLECTION,
            design="full",
            min_class_size=2,
            per_class=N_MEMBERS,
            n_seeds=1,
            arms=arms,
        )
        return rq5.Unit(index=0, experiment=experiment, seed=seed, arm=None)

    def _run(self, collection: KBCollection, root: Path, arms: tuple[str, ...]) -> Any:
        return rq5.run_unit(
            self._unit(collection, arms),
            matrices_root=root,
            corpora_root=None,
            collection_cache={COLLECTION: collection},
        )

    def test_a_censored_arm_scores_what_the_survivor_block_scores(
        self, collection: KBCollection, tmp_path: Path
    ) -> None:
        survivors = tuple(kb_id for kb_id in ALL_IDS if kb_id not in {"m03", "m07"})
        # `short` censors two members; `restricted` is complete over exactly the
        # same survivors. Identical member sets must give identical numbers.
        _write_arm(tmp_path, "wstar_orbit", survivors, ("m03", "m07"))
        short = self._run(collection, tmp_path, ("wstar_orbit",))

        trimmed = KBCollection(
            name=COLLECTION,
            records=tuple(r for r in collection.records if r.kb_id in set(survivors)),
            type_names=collection.type_names,
            pred_names=collection.pred_names,
        )
        other = tmp_path / "complete"
        _write_arm(other, "wstar_orbit", survivors, ())
        restricted = rq5.run_unit(
            self._unit(trimmed, ("wstar_orbit",)),
            matrices_root=other,
            corpora_root=None,
            collection_cache={COLLECTION: trimmed},
        )

        left = [row for row in short["clustering"] if row["method"] == "pam"][0]
        right = [row for row in restricted["clustering"] if row["method"] == "pam"][0]
        assert left["n_members"] == right["n_members"] == len(survivors)
        assert left["ari"] == pytest.approx(right["ari"])
        assert left["pam_cost"] == pytest.approx(right["pam_cost"])
        assert left["silhouette"] == pytest.approx(right["silhouette"])
        assert left["n_censored_members"] == 2
        assert right["n_censored_members"] == 0

    def test_the_intersection_is_taken_across_arms(
        self, collection: KBCollection, tmp_path: Path
    ) -> None:
        _write_arm(tmp_path, "wstar_orbit", tuple(i for i in ALL_IDS if i != "m03"), ("m03",))
        _write_arm(tmp_path, "size_l1", tuple(i for i in ALL_IDS if i != "m07"), ("m07",))
        tables = self._run(collection, tmp_path, ("wstar_orbit", "size_l1"))
        pam = [row for row in tables["clustering"] if row["method"] == "pam"]
        assert {row["arm"] for row in pam} == {"wstar_orbit", "size_l1"}
        # Both arms lose both members, so both score the same 10.
        assert {row["n_members"] for row in pam} == {N_MEMBERS - 2}
        assert {row["n_censored_members"] for row in pam} == {2}

    def test_an_uncensored_run_is_unchanged(self, collection: KBCollection, tmp_path: Path) -> None:
        _write_arm(tmp_path, "size_l1", ALL_IDS, ())
        tables = self._run(collection, tmp_path, ("size_l1",))
        pam = [row for row in tables["clustering"] if row["method"] == "pam"][0]
        assert pam["n_members"] == N_MEMBERS
        assert pam["n_censored_members"] == 0

    def test_the_per_class_census_is_reported_by_type(
        self, collection: KBCollection, tmp_path: Path
    ) -> None:
        # m03 and m07 are both odd, so both carry LABELS[1].
        _write_arm(
            tmp_path,
            "wstar_orbit",
            tuple(i for i in ALL_IDS if i not in {"m03", "m07"}),
            ("m03", "m07"),
        )
        tables = self._run(collection, tmp_path, ("wstar_orbit",))
        by_class = {row["class"]: row for row in tables["per_class"] if row["method"] == "pam"}
        assert by_class[LABELS[1]]["n_censored_class"] == 2
        assert by_class[LABELS[0]]["n_censored_class"] == 0
        # abs, not rel: the census rounds its rate to six decimals.
        assert by_class[LABELS[1]]["censor_rate_class"] == pytest.approx(
            2 / (N_MEMBERS // 2), abs=1e-6
        )

    def test_too_few_survivors_for_k_classes_is_censored_not_crashed(
        self, collection: KBCollection, tmp_path: Path
    ) -> None:
        _write_arm(tmp_path, "wstar_orbit", ("m00",), tuple(i for i in ALL_IDS if i != "m00"))
        tables = self._run(collection, tmp_path, ("wstar_orbit",))
        assert all(row["censored"] == 1 for row in tables["clustering"])
