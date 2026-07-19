"""Unit tests for experiments.article.analysis.clustering (T-M5c).

Acceptance criteria checked here
---------------------------------
1. dunn_index: correct value on a toy matrix with known clusters.
2. davies_bouldin_precomputed: correct value on a toy matrix with known medoids.
3. silhouette wrapper matches sklearn's precomputed result.
4. cophenetic_from_d returns a correlation in [0, 1] and matches scipy's cophenet.
5. run_kmedoids separates a trivially clusterable D into the right groups.
6. Label-alignment sanity: a 2-cluster toy D produces ARI=1 when perfectly recovered.

Every test is designed to FAIL before the clustering module exists.
"""

from __future__ import annotations

import numpy as np
import pytest

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Toy distance matrices used across tests
# ---------------------------------------------------------------------------


def _toy_d_two_clusters() -> tuple[np.ndarray, list[int], list[int]]:
    """Return a distance matrix with 2 tight clusters (3+2 points) and their labels/medoids.

    Cluster 0: points 0,1,2  (tight, diameter 2)
    Cluster 1: points 3,4    (tight, diameter 1)
    Inter-cluster distances: all >= 10
    """
    D = np.array(
        [
            [0.0, 1.0, 2.0, 10.0, 11.0],
            [1.0, 0.0, 1.0, 11.0, 12.0],
            [2.0, 1.0, 0.0, 12.0, 11.0],
            [10.0, 11.0, 12.0, 0.0, 1.0],
            [11.0, 12.0, 11.0, 1.0, 0.0],
        ],
        dtype=np.float64,
    )
    labels = [0, 0, 0, 1, 1]
    medoids = [1, 4]  # point 1 is centre of cluster 0, point 4 of cluster 1
    return D, labels, medoids


# ---------------------------------------------------------------------------
# Tests for dunn_index
# ---------------------------------------------------------------------------


class TestDunnIndex:
    def test_known_toy(self) -> None:
        """dunn = min_inter / max_intra_diameter.

        Cluster 0 (pts 0,1,2): max intra dist = max(D[0,2], D[0,1], D[1,2]) = 2
        Cluster 1 (pts 3,4):   max intra dist = D[3,4] = 1
        max_intra = 2
        min_inter = min distance between any pt in C0 and any pt in C1 = D[0,3] = 10
        dunn = 10 / 2 = 5.0
        """
        from experiments.article.analysis.clustering import dunn_index

        D, labels, _ = _toy_d_two_clusters()
        result = dunn_index(D, np.array(labels))
        np.testing.assert_allclose(result, 5.0, rtol=1e-9)

    def test_single_point_cluster_diameter_zero(self) -> None:
        """A singleton cluster has diameter 0 — Dunn is inf when all others also."""
        from experiments.article.analysis.clustering import dunn_index

        D = np.array([[0.0, 3.0], [3.0, 0.0]])
        labels = np.array([0, 1])
        val = dunn_index(D, labels)
        # inter = 3, max_intra_diameter = max(0,0) = 0 → inf
        assert val == pytest.approx(float("inf")) or val > 1000.0

    def test_perfect_separation_large(self) -> None:
        """5+5 tight clusters all at distance 100 → large Dunn."""
        from experiments.article.analysis.clustering import dunn_index

        n = 10
        D = np.zeros((n, n))
        # Within each half: dist=1; across halves: dist=100
        for i in range(5):
            for j in range(5):
                if i != j:
                    D[i, j] = 1.0
        for i in range(5, 10):
            for j in range(5, 10):
                if i != j:
                    D[i, j] = 1.0
        for i in range(5):
            for j in range(5, 10):
                D[i, j] = 100.0
                D[j, i] = 100.0
        labels = np.array([0] * 5 + [1] * 5)
        val = dunn_index(D, labels)
        assert val >= 20.0


# ---------------------------------------------------------------------------
# Tests for davies_bouldin_precomputed
# ---------------------------------------------------------------------------


class TestDaviesBouldinPrecomputed:
    def test_known_toy(self) -> None:
        """DB on the toy 2-cluster example with given medoids.

        medoids = [1, 4]
        s_0 = mean(D[{0,1,2}, 1]) = mean(1, 0, 1) = 2/3
        s_1 = mean(D[{3,4}, 4]) = mean(1, 0) = 1/2
        d_01 = D[1, 4] = 12.0
        DB = (1/2) * ((s_0+s_1)/d_01 + (s_1+s_0)/d_10)
           = (1/2) * (7/6/12 + 7/6/12) = 7/(6*12) ≈ 0.0972
        """
        from experiments.article.analysis.clustering import davies_bouldin_precomputed

        D, labels, medoids = _toy_d_two_clusters()
        result = davies_bouldin_precomputed(D, np.array(labels), np.array(medoids))
        # s_0 = (1+0+1)/3 = 2/3, s_1 = (1+0)/2 = 0.5, d_01 = D[1,4] = 12
        expected = (2 / 3 + 0.5) / 12.0  # (7/6)/12 per cluster, symmetrical
        np.testing.assert_allclose(result, expected, rtol=1e-9)

    def test_perfect_two_clusters(self) -> None:
        """A perfectly separated 2-cluster: DB should be very small."""
        from experiments.article.analysis.clustering import davies_bouldin_precomputed

        D = np.array(
            [
                [0.0, 0.1, 100.0, 100.1],
                [0.1, 0.0, 100.1, 100.0],
                [100.0, 100.1, 0.0, 0.1],
                [100.1, 100.0, 0.1, 0.0],
            ],
            dtype=np.float64,
        )
        labels = np.array([0, 0, 1, 1])
        medoids = np.array([0, 2])
        db = davies_bouldin_precomputed(D, labels, medoids)
        assert db < 0.01


# ---------------------------------------------------------------------------
# Tests for silhouette_precomputed (wrapper check)
# ---------------------------------------------------------------------------


class TestSilhouetteWrapper:
    def test_matches_sklearn(self) -> None:
        """Our silhouette wrapper must match sklearn's precomputed result."""
        from sklearn.metrics import silhouette_score

        from experiments.article.analysis.clustering import silhouette_precomputed

        D, labels, _ = _toy_d_two_clusters()
        sklearn_val = silhouette_score(D, labels, metric="precomputed")
        our_val = silhouette_precomputed(D, np.array(labels))
        np.testing.assert_allclose(our_val, sklearn_val, rtol=1e-12)

    def test_high_for_good_clustering(self) -> None:
        from experiments.article.analysis.clustering import silhouette_precomputed

        D, labels, _ = _toy_d_two_clusters()
        s = silhouette_precomputed(D, np.array(labels))
        assert s > 0.7


# ---------------------------------------------------------------------------
# Tests for cophenetic_from_d
# ---------------------------------------------------------------------------


class TestCopheneticFromD:
    def test_range_and_sign(self) -> None:
        """Cophenetic correlation is in [0, 1] for well-separated clusters."""
        from experiments.article.analysis.clustering import cophenetic_from_d

        D, _, _ = _toy_d_two_clusters()
        c = cophenetic_from_d(D, method="average")
        assert 0.0 <= c <= 1.0

    def test_matches_scipy(self) -> None:
        """Our wrapper must match scipy's cophenet directly."""
        import scipy.cluster.hierarchy as sch
        from scipy.spatial.distance import squareform

        from experiments.article.analysis.clustering import cophenetic_from_d

        D, _, _ = _toy_d_two_clusters()
        condensed = squareform(D, checks=False)
        Z = sch.linkage(condensed, method="average")
        c_scipy, _ = sch.cophenet(Z, condensed)
        c_ours = cophenetic_from_d(D, method="average")
        np.testing.assert_allclose(c_ours, c_scipy, rtol=1e-12)


# ---------------------------------------------------------------------------
# Tests for run_kmedoids
# ---------------------------------------------------------------------------


class TestRunKmedoids:
    def test_separates_trivial_clusters(self) -> None:
        """k-medoids on a trivially clusterable D recovers ARI=1."""
        from sklearn.metrics import adjusted_rand_score

        from experiments.article.analysis.clustering import run_kmedoids

        D, true_labels, _ = _toy_d_two_clusters()
        result = run_kmedoids(D, k=2, n_init=5, rng_seed=42)
        # After potentially flipping labels (ARI is permutation-invariant):
        ari = adjusted_rand_score(true_labels, result.labels)
        assert ari == pytest.approx(1.0)

    def test_k1_returns_single_medoid(self) -> None:
        """k=1 degenerate: all points assigned to one cluster."""
        from experiments.article.analysis.clustering import run_kmedoids

        D, _, _ = _toy_d_two_clusters()
        result = run_kmedoids(D, k=1, n_init=1, rng_seed=0)
        assert len(result.medoids) == 1
        assert set(result.labels) == {0}

    def test_n_init_consistency(self) -> None:
        """Multiple inits on easy data should yield consistent loss."""
        from experiments.article.analysis.clustering import run_kmedoids

        D, _, _ = _toy_d_two_clusters()
        r1 = run_kmedoids(D, k=2, n_init=1, rng_seed=0)
        r5 = run_kmedoids(D, k=2, n_init=5, rng_seed=0)
        # Both should find the global optimum on this easy data.
        assert r5.loss <= r1.loss + 1e-9


# ---------------------------------------------------------------------------
# Tests for label-alignment (cache path correctness)
# ---------------------------------------------------------------------------


class TestLabelAlignment:
    def test_planted_main_n60(self) -> None:
        """planted_main D.npy should have 60 rows (N=60, 5 families × 12 members)."""
        import numpy as np

        cache = (
            "/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/T-M5b"
            "/d_matrix/planted_families/planted_main/seed42/isalhg_levenshtein/D.npy"
        )
        D = np.load(cache)
        assert D.shape == (60, 60), f"Expected (60, 60), got {D.shape}"
        assert D.dtype in (np.float32, np.float64, np.float16)

    @pytest.mark.slow
    def test_labels_align_with_planted_main(self) -> None:
        """Loading planted_main with the same params yields 60 labels that align with D."""
        from isalhg.datasets.synthetic.planted_families import PlantedFamilyDataset

        cfg = dict(
            n_families=5,
            members_per_family=12,
            n_nodes=10,
            k=3,
            n_edges=10,
            seed_value=42,
            n_edits=3,
            max_retries=300,
        )
        dataset = PlantedFamilyDataset(**cfg)
        items = list(dataset)
        labels = [int(item.extra.get("family_index", 0)) for item in items]
        assert len(labels) == 60
        assert set(labels) == {0, 1, 2, 3, 4}
