"""Unit tests of the NEWPOS GRU generator experiment (scripts/newpos/neural_gen/)."""

from __future__ import annotations

import gzip
import itertools
import json
import math
import random
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

pytestmark = pytest.mark.unit

_REPO_ROOT = Path(__file__).resolve().parents[2]
for _path in (str(_REPO_ROOT / "scripts" / "newpos" / "neural_gen"), str(_REPO_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import ng_data  # noqa: E402
import ng_decode  # noqa: E402

SPEC = ng_decode.DecodeSpec(n_types=4, n_preds=1, k=10)
# Tokens and decoded knowledge base of a sample the real decoder produced.
OW_TOKENS = ("V[0;1;1;0]", "N[2]", "V[0;2;2;0,1]", "V[0;2;2;0,1]")
OW_ROOT = 3


class TestVocabulary:
    def test_round_trip_returns_the_original_objects(self) -> None:
        sequences = [[("T", 0), ("F", 1, (0, 1))], [("T", 0), ("T", 2)], []]
        vocab = ng_data.Vocabulary.fit(sequences)
        assert len(vocab) == 3 + 3
        for sequence in sequences:
            assert vocab.decode(vocab.encode(sequence)) == tuple(sequence)

    def test_ids_follow_first_appearance_after_the_specials(self) -> None:
        vocab = ng_data.Vocabulary.fit([["b", "a"], ["c", "b"]])
        assert vocab.encode(["b", "a", "c"]) == [3, 4, 5]

    def test_special_ids_and_unknown_tokens_are_rejected(self) -> None:
        vocab = ng_data.Vocabulary.fit([["a"]])
        with pytest.raises(ng_data.VocabularyError):
            vocab.decode([ng_data.EOS])
        with pytest.raises(ng_data.VocabularyError):
            vocab.encode(["zzz"])


class TestSplitAndBatches:
    @pytest.mark.parametrize("n", [20, 100, 1381, 3988])
    def test_split_is_a_partition_with_80_10_10_sizes(self, n: int) -> None:
        train, val, test = ng_data.split_members(n, "c", 7)
        assert sorted([*train, *val, *test]) == list(range(n))
        assert len(val) == len(test) == round(0.1 * n)

    def test_split_is_deterministic_and_seed_dependent(self) -> None:
        a = ng_data.split_members(200, "c", 1)
        assert a == ng_data.split_members(200, "c", 1)
        assert a != ng_data.split_members(200, "c", 2)
        assert a != ng_data.split_members(200, "other", 1)

    def test_split_too_small_raises(self) -> None:
        with pytest.raises(ng_data.SplitError):
            ng_data.split_members(2, "c", 0)

    def test_batch_layout(self) -> None:
        batch = ng_data.make_batch([[5, 6], [7]])
        assert batch.inputs == [[ng_data.BOS, 5, 6], [ng_data.BOS, 7, ng_data.PAD]]
        assert batch.targets == [[5, 6, ng_data.EOS], [7, ng_data.EOS, ng_data.PAD]]
        assert batch.lengths == [3, 2]

    def test_empty_sequence_is_a_single_eos_target(self) -> None:
        batch = ng_data.make_batch([[]])
        assert batch.inputs == [[ng_data.BOS]]
        assert batch.targets == [[ng_data.EOS]]


class TestDecodeAndRecords:
    def test_hand_made_ow_tokens_decode_to_a_connected_kb(self) -> None:
        decoded = ng_decode.decode_draw("ow", OW_TOKENS, SPEC, OW_ROOT)
        assert decoded.status == "decoded"
        assert decoded.connected is True
        n, types, facts = ng_decode.kb_fields(decoded.hypergraph)
        assert n == 6
        assert types == [3, 0, 0, 1, 0, 1]
        assert facts == [[0, [0, 1]], [0, [0, 1, 2, 3]], [0, [0, 1, 4, 5]]]

    def test_empty_ow_word_is_the_single_constant_kb(self) -> None:
        decoded = ng_decode.decode_draw("ow", (), SPEC, 2)
        assert decoded.connected is True
        assert ng_decode.kb_fields(decoded.hypergraph) == (1, [2], [])

    def test_incidence_rejection_names_the_rule(self) -> None:
        tokens = (("N", 2), ("T", 0), ("T", 0), ("FACT",), ("P", 0), ("C", 0), ("C", 5), ("END",))
        decoded = ng_decode.decode_draw("incidence", tokens, SPEC, None)
        assert decoded.status == "rejected"
        assert decoded.reason == "constant_id"
        assert decoded.hypergraph is None and decoded.connected is None

    def test_fact_word_with_an_isolated_constant_is_decoded_but_not_connected(self) -> None:
        word = (("T", 0), ("T", 0), ("T", 0), ("F", 0, (0, 1)))
        decoded = ng_decode.decode_draw("fact", word, SPEC, None)
        assert decoded.status == "decoded"
        assert decoded.connected is False

    def test_record_has_exactly_the_frozen_keys_for_both_statuses(self) -> None:
        ok = ng_decode.process_draw("c", "ow", "gru_ow", 60000, 0, OW_TOKENS, OW_ROOT, SPEC)
        bad = ng_decode.process_draw(
            "c", "incidence", "gru_incidence", 60000, 1, (("END",),), None, SPEC
        )
        for outcome in (ok, bad):
            assert tuple(outcome.record) == ng_decode.RECORD_KEYS
        assert ok.record["root_type"] == OW_ROOT and ok.record["tokens"] == list(OW_TOKENS)
        assert bad.record["status"] == "rejected" and bad.record["n"] is None
        assert bad.record["tokens"] == ["('END',)"]
        assert not bad.usable and bad.key is None

    def test_writer_round_trips_through_gzip(self, tmp_path: Path) -> None:
        ok = ng_decode.process_draw("c", "ow", "gru_ow", 60000, 0, OW_TOKENS, OW_ROOT, SPEC)
        path = tmp_path / "c__gru_ow__s60000.jsonl.gz"
        ng_decode.write_samples_atomic(path, [ok])
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            lines = [json.loads(line) for line in handle]
        assert lines == [ok.record]
        assert list(lines[0]) == list(ng_decode.RECORD_KEYS)
        assert not list(tmp_path.glob("*.tmp"))


class TestTally:
    @staticmethod
    def _outcome(key: tuple[int, str] | None, *, usable: bool = True, status: str = "decoded"):
        record = {
            "status": status,
            "reason": None if status == "decoded" else "x",
            "connected": usable,
        }
        return ng_decode.DrawOutcome(
            record=record, usable=usable, key=key, key_error=None, n_nodes=3, n_edges=2
        )

    def test_counts_follow_the_frozen_definitions(self) -> None:
        a, b, c, d = (0, "a"), (0, "b"), (0, "c"), (0, "d")
        outcomes = [
            self._outcome(a),  # copy of a training member
            self._outcome(a),
            self._outcome(b),  # copy of a held-out member
            self._outcome(c),  # new class, appears twice
            self._outcome(c),
            self._outcome(d),  # new class, once
            self._outcome(None, usable=False),  # decoded, disconnected
            self._outcome(None, usable=False, status="rejected"),
        ]
        counts = ng_decode.tally(outcomes, [False] * 7 + [True], {a}, {b})
        assert counts["n_draws"] == 8
        assert counts["n_decoded"] == 7 and counts["n_rejected"] == 1
        assert counts["n_usable"] == 6 and counts["n_zero_fact_usable"] == 0
        assert counts["n_unique_usable"] == 4
        assert counts["n_novel_usable"] == 3
        assert counts["n_vun"] == 2
        assert counts["n_copy_train"] == 2 and counts["n_copy_heldout"] == 1
        assert counts["n_capped"] == 1
        assert counts["usable_per_draw"] == pytest.approx(6 / 8)
        assert counts["residual_ood_rate"] == pytest.approx(2 / 8)
        assert counts["vun_per_draw"] == pytest.approx(2 / 8)
        assert counts["uniqueness"] == pytest.approx(4 / 6)
        assert counts["novelty"] == pytest.approx(3 / 6)


torch = pytest.importorskip("torch")

import ng_model  # noqa: E402


class TestSampler:
    def test_sample_law_matches_the_exact_sequence_probabilities(self) -> None:
        torch.manual_seed(0)
        config = ng_model.GRUConfig(embedding=8, hidden=8, layers=2, dropout=0.0, sample_chunk=7000)
        n_tokens, max_len = 3, 3
        model = ng_model.GRULM(ng_data.N_SPECIAL + n_tokens, config)
        model.eval()
        # Scaled weights make the next-token law depend strongly on the history, so a
        # sampler that feeds the wrong token or hidden row back is detected.
        with torch.no_grad():
            for name, parameter in model.named_parameters():
                parameter.mul_(12.0 if "weight_hh" in name else 4.0)
        token_ids = list(range(ng_data.N_SPECIAL, ng_data.N_SPECIAL + n_tokens))

        def next_probs(prefix: tuple[int, ...]) -> torch.Tensor:
            x = torch.tensor([[ng_data.BOS, *prefix]])
            with torch.no_grad():
                logits, _ = model(x)
            return torch.softmax(logits[0, -1], dim=-1)

        exact: dict[tuple[int, ...], float] = {}
        for length in range(max_len + 1):
            for seq in itertools.product(token_ids, repeat=length):
                p = 1.0
                for i, tok in enumerate(seq):
                    p *= float(next_probs(seq[:i])[tok])
                if length < max_len:
                    p *= float(next_probs(seq)[ng_data.EOS])
                exact[seq] = p
        assert sum(exact.values()) == pytest.approx(1.0, abs=1e-6)

        n_draws = 100_000
        draws, capped = ng_model.sample_sequences(
            model, n_draws, max_len, torch.device("cpu"), seed=1, config=config
        )
        assert len(draws) == len(capped) == n_draws
        counts: dict[tuple[int, ...], int] = {}
        for seq in draws:
            counts[tuple(seq)] = counts.get(tuple(seq), 0) + 1
        tv = 0.5 * sum(abs(counts.get(s, 0) / n_draws - p) for s, p in exact.items())
        assert tv < 0.01
        assert set(counts) <= set(exact)
        assert all(flag == (len(seq) == max_len) for seq, flag in zip(draws, capped, strict=True))

    def test_pad_and_bos_have_zero_probability(self) -> None:
        config = ng_model.GRUConfig(embedding=4, hidden=4, layers=1, dropout=0.0)
        model = ng_model.GRULM(6, config)
        with torch.no_grad():
            logits, _ = model(torch.tensor([[ng_data.BOS, 3]]))
        probs = torch.softmax(logits, dim=-1)
        assert float(probs[..., ng_data.PAD].max()) == 0.0
        assert float(probs[..., ng_data.BOS].max()) == 0.0
        assert float(probs.sum(-1).min()) == pytest.approx(1.0, abs=1e-6)

    def test_evaluation_bits_equal_the_teacher_forced_sum(self) -> None:
        config = ng_model.GRUConfig(embedding=4, hidden=4, layers=1, dropout=0.0)
        model = ng_model.GRULM(7, config)
        sequences = [[3, 4], [5], []]
        result = ng_model.evaluate(model, sequences, torch.device("cpu"), batch_size=2)
        total = 0.0
        for seq in sequences:
            x = torch.tensor([[ng_data.BOS, *seq]])
            with torch.no_grad():
                logits, _ = model(x)
            lp = torch.log_softmax(logits[0], dim=-1)
            targets = [*seq, ng_data.EOS]
            total += -sum(float(lp[i, t]) for i, t in enumerate(targets))
        assert result["bits_per_kb"] == pytest.approx(total / 3 / math.log(2.0), rel=1e-5)
        assert result["n_tokens"] == 2 + 1 + 1 + 1 + 1


def _tiny_collection(n_members: int = 20) -> SimpleNamespace:
    pytest.importorskip("pynauty")
    from experiments.tkde.rq6 import _ow_tokens, _ow_word
    from isalhg.core.canonical import required_k
    from isalhg.core.sparse_hypergraph import SparseHypergraph
    from isalhg.generation.incidence_baseline import flatten
    from isalhg.metric_space.distances.fact_levenshtein import fact_word

    rng = random.Random(3)
    hypergraphs = []
    for _ in range(n_members):
        n = rng.randint(3, 6)
        edges = [frozenset({v, rng.randrange(v)}) for v in range(1, n)]
        edges += [frozenset(rng.sample(range(n), 3)) for _ in range(rng.randint(0, 2))]
        hypergraphs.append(
            SparseHypergraph(
                n,
                edges,
                n_vertex_labels=2,
                n_edge_labels=1,
                vertex_labels=[rng.randrange(2) for _ in range(n)],
                edge_labels=[0] * len(edges),
            )
        )
    ordered = [_ow_word(H) for H in hypergraphs]
    return SimpleNamespace(
        name="tiny",
        hypergraphs=hypergraphs,
        words=[fact_word(H, None) for H in hypergraphs],
        flat=[flatten(H) for H in hypergraphs],
        ow_words=[_ow_tokens(word) for _root, word in ordered],
        ow_roots=[root for root, _word in ordered],
        n_types=2,
        n_preds=1,
        k=max(required_k(H) for H in hypergraphs),
    )


class TestSmokeUnit:
    @pytest.mark.parametrize("serialization", ng_data.SERIALIZATIONS)
    def test_one_epoch_train_sample_decode_write(self, serialization: str, tmp_path: Path) -> None:
        import train_sample

        bundle = train_sample.CollectionBundle.from_context(_tiny_collection())
        unit = train_sample.UnitSpec("tiny", serialization, 60000)
        config = ng_model.GRUConfig(embedding=16, hidden=16, layers=2, max_epochs=1)
        summary = train_sample.run_unit(
            bundle, unit, tmp_path, config, n_draws=60, device=torch.device("cpu")
        )
        assert summary["epochs_run"] == 1 and summary["best_epoch"] == 1
        assert summary["n_train"] == 16 and summary["n_val"] == 2 and summary["n_test"] == 2
        assert summary["n_draws"] == 60
        assert summary["n_usable"] <= summary["n_connected"] <= summary["n_decoded"] <= 60
        assert summary["test_bits_per_kb"] > 0
        if serialization == "ow":
            assert summary["n_decoded"] == summary["n_connected"] == 60
        sample_file = train_sample.sample_path(tmp_path, unit)
        assert sample_file.name == f"tiny__gru_{serialization}__s60000.jsonl.gz"
        with gzip.open(sample_file, "rt", encoding="utf-8") as handle:
            lines = [json.loads(line) for line in handle]
        assert len(lines) == 60
        assert all(tuple(line) == ng_decode.RECORD_KEYS for line in lines)
        assert [line["draw"] for line in lines] == list(range(60))
        assert all(line["generator"] == f"gru_{serialization}" for line in lines)
        again = train_sample.run_unit(
            bundle, unit, tmp_path, config, n_draws=60, device=torch.device("cpu")
        )
        assert again["skipped"] is True

    def test_members_round_trip_through_vocabulary_and_decoder(self) -> None:
        bundle = __import__("train_sample").CollectionBundle.from_context(_tiny_collection())
        for serialization in ng_data.SERIALIZATIONS:
            sequences = ng_data.serialization_sequences(bundle.ctx, serialization)
            vocab = ng_data.Vocabulary.fit(sequences)
            for i, sequence in enumerate(sequences):
                tokens = vocab.decode(vocab.encode(sequence))
                root = bundle.ctx.ow_roots[i] if serialization == "ow" else None
                outcome = ng_decode.process_draw(
                    "t", serialization, "g", 0, i, tokens, root, bundle.spec
                )
                assert outcome.key == bundle.keys[i]


class TestSummarize:
    def test_hc1_flags_a_violation(self) -> None:
        import summarize

        good = {
            "collection": "c",
            "serialization": "ow",
            "seed": 1,
            "n_draws": 10,
            "n_decoded": 10,
            "n_connected": 10,
            "n_rejected": 0,
        }
        bad = {**good, "seed": 2, "n_decoded": 9, "n_connected": 9, "n_rejected": 1}
        assert summarize.hc1_check([good])["holds"] is True
        result = summarize.hc1_check([good, bad])
        assert result["holds"] is False and len(result["violations"]) == 1

    def test_ci95_uses_student_t_on_three_seeds(self) -> None:
        import summarize

        interval = summarize.ci95([0.1, 0.2, 0.3])
        assert interval["method"] == "student_t"
        assert interval["low"] < 0.2 < interval["high"]
        assert summarize.ci95([0.5, 0.5, 0.5])["method"] == "degenerate"
