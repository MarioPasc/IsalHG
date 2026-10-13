"""The GRU language model, its trainer and its batched ancestral sampler.

One architecture and one training recipe serve all three serializations; only the
vocabulary size differs. Padding and BOS columns of the output layer are fixed at
``-inf`` so the softmax normaliser, and hence the held-out bits, run over real
symbols and EOS only.
"""

from __future__ import annotations

import copy
import logging
import math
import os
import random
import time
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import torch
from ng_data import BOS, EOS, PAD, Batch, epoch_batches
from torch import nn

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GRUConfig:
    """Hyperparameters shared by every unit (fairness is the point of the experiment)."""

    embedding: int = 128
    hidden: int = 256
    layers: int = 2
    dropout: float = 0.2
    lr: float = 2e-3
    weight_decay: float = 0.01
    batch_size: int = 64
    clip: float = 1.0
    max_epochs: int = 60
    patience: int = 6
    temperature: float = 1.0
    sample_chunk: int = 2500

    def as_dict(self) -> dict[str, Any]:
        """JSON-ready view."""
        return asdict(self)


def seed_everything(seed: int, *, deterministic: bool = True) -> None:
    """Seed python, numpy and torch (CPU and CUDA) for one unit.

    Parameters
    ----------
    seed : int
        Unit seed.
    deterministic : bool, optional
        Ask cuDNN and torch for deterministic kernels. Bitwise reproducibility on a
        GPU is still best effort; the seeds are what is pinned.
    """
    random.seed(seed)
    np.random.seed(seed % (2**32))
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    if deterministic:
        os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
        torch.use_deterministic_algorithms(True, warn_only=True)


class GRULM(nn.Module):
    """Embedding -> dropout -> 2-layer GRU -> dropout -> linear, over ids with PAD/BOS/EOS."""

    def __init__(self, vocab_size: int, config: GRUConfig) -> None:
        super().__init__()
        self.embed = nn.Embedding(vocab_size, config.embedding, padding_idx=PAD)
        self.drop = nn.Dropout(config.dropout)
        self.gru = nn.GRU(
            config.embedding,
            config.hidden,
            num_layers=config.layers,
            dropout=config.dropout if config.layers > 1 else 0.0,
            batch_first=True,
        )
        self.out = nn.Linear(config.hidden, vocab_size)
        mask = torch.zeros(vocab_size)
        mask[PAD] = float("-inf")
        mask[BOS] = float("-inf")
        self.register_buffer("column_mask", mask)

    def forward(
        self, x: torch.Tensor, h: torch.Tensor | None = None
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Return ``(logits, hidden)``; ``logits`` has shape ``(B, T, V)``."""
        y, h_out = self.gru(self.drop(self.embed(x)), h)
        return self.out(self.drop(y)) + self.column_mask, h_out


def _to_tensors(batch: Batch, device: torch.device) -> tuple[torch.Tensor, ...]:
    inputs = torch.tensor(batch.inputs, dtype=torch.long, device=device)
    targets = torch.tensor(batch.targets, dtype=torch.long, device=device)
    lengths = torch.tensor(batch.lengths, dtype=torch.long, device=device)
    return inputs, targets, lengths


def sequence_nll(
    model: GRULM, batch: Batch, device: torch.device
) -> tuple[torch.Tensor, torch.Tensor]:
    """Per-sequence negative log-likelihood in nats, EOS included.

    Returns
    -------
    tuple[torch.Tensor, torch.Tensor]
        ``(nll, lengths)``, each of shape ``(B,)``.
    """
    inputs, targets, lengths = _to_tensors(batch, device)
    logits, _ = model(inputs)
    width = inputs.shape[1]
    valid = torch.arange(width, device=device)[None, :] < lengths[:, None]
    # Pads in the target are redirected to EOS so the gather stays finite; the mask
    # removes them from the sum.
    safe = targets.masked_fill(~valid, EOS)
    log_probs = torch.log_softmax(logits.float(), dim=-1)
    token_nll = -log_probs.gather(-1, safe.unsqueeze(-1)).squeeze(-1)
    return (token_nll * valid).sum(dim=1), lengths


@torch.no_grad()
def evaluate(
    model: GRULM,
    id_sequences: Sequence[Sequence[int]],
    device: torch.device,
    batch_size: int = 256,
) -> dict[str, float]:
    """Held-out NLL of a list of sequences.

    Returns
    -------
    dict[str, float]
        ``nats_per_kb`` (mean over sequences of the summed token NLL, EOS included),
        ``bits_per_kb``, ``bits_per_token`` and the counts.
    """
    model.eval()
    total_nats = 0.0
    total_tokens = 0
    for batch in epoch_batches(id_sequences, batch_size, None):
        nll, lengths = sequence_nll(model, batch, device)
        total_nats += float(nll.sum().item())
        total_tokens += int(lengths.sum().item())
    n = len(id_sequences)
    return {
        "n_sequences": float(n),
        "n_tokens": float(total_tokens),
        "nats_per_kb": total_nats / n,
        "bits_per_kb": total_nats / n / math.log(2.0),
        "bits_per_token": total_nats / total_tokens / math.log(2.0),
    }


def fit(
    model: GRULM,
    train_ids: Sequence[Sequence[int]],
    val_ids: Sequence[Sequence[int]],
    config: GRUConfig,
    seed: int,
    device: torch.device,
) -> dict[str, Any]:
    """Train with AdamW, gradient clipping and early stopping on validation NLL per KB.

    The best-validation weights are restored before returning.

    Returns
    -------
    dict[str, Any]
        ``epochs_run``, ``best_epoch`` (1-based), ``best_val_nats_per_kb``,
        ``stopped_early``, ``train_secs`` and the per-epoch ``history``.
    """
    started = time.perf_counter()
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=config.lr, weight_decay=config.weight_decay
    )
    shuffle_rng = random.Random(f"newpos-gru-shuffle|{seed}")
    best_val = math.inf
    best_epoch = 0
    best_state: dict[str, torch.Tensor] = {}
    bad_epochs = 0
    history: list[dict[str, float]] = []
    epochs_run = 0

    for epoch in range(1, config.max_epochs + 1):
        model.train()
        loss_sum = 0.0
        token_sum = 0
        for batch in epoch_batches(train_ids, config.batch_size, shuffle_rng):
            nll, lengths = sequence_nll(model, batch, device)
            n_tokens = lengths.sum()
            loss = nll.sum() / n_tokens
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), config.clip)
            optimizer.step()
            loss_sum += float(nll.sum().item())
            token_sum += int(n_tokens.item())
        val = evaluate(model, val_ids, device)["nats_per_kb"]
        epochs_run = epoch
        history.append(
            {
                "epoch": float(epoch),
                "train_nats_per_token": loss_sum / token_sum,
                "val_nats_per_kb": val,
            }
        )
        if val < best_val:
            best_val, best_epoch, bad_epochs = val, epoch, 0
            best_state = copy.deepcopy(model.state_dict())
        else:
            bad_epochs += 1
            if bad_epochs >= config.patience:
                break

    model.load_state_dict(best_state)
    return {
        "epochs_run": epochs_run,
        "best_epoch": best_epoch,
        "best_val_nats_per_kb": best_val,
        "stopped_early": epochs_run < config.max_epochs,
        "train_secs": time.perf_counter() - started,
        "history": history,
    }


@torch.no_grad()
def sample_sequences(
    model: GRULM,
    n_draws: int,
    max_len: int,
    device: torch.device,
    seed: int,
    config: GRUConfig,
) -> tuple[list[list[int]], list[bool]]:
    """Ancestral sampling at ``config.temperature``, ``max_len`` tokens at most.

    Rows that emitted EOS leave the batch, so the cost follows the sampled lengths.

    Parameters
    ----------
    model : GRULM
        Trained model.
    n_draws : int
        Number of sequences.
    max_len : int
        Token cap (EOS excluded). A row that has emitted ``max_len`` tokens without
        EOS is returned as it stands and flagged capped.
    device : torch.device
        Sampling device.
    seed : int
        Seed of the sampling generator.
    config : GRUConfig
        Supplies temperature and chunk size.

    Returns
    -------
    tuple[list[list[int]], list[bool]]
        Token-id sequences (no BOS/EOS) and the capped flags, both in draw order.
    """
    model.eval()
    generator = torch.Generator(device=device)
    generator.manual_seed(seed)
    sequences: list[list[int]] = []
    capped: list[bool] = []
    for start in range(0, n_draws, config.sample_chunk):
        rows = min(config.sample_chunk, n_draws - start)
        chunk_seqs: list[list[int]] = [[] for _ in range(rows)]
        active = list(range(rows))
        x = torch.full((rows, 1), BOS, dtype=torch.long, device=device)
        h: torch.Tensor | None = None
        for _ in range(max_len):
            logits, h = model(x, h)
            probs = torch.softmax(logits[:, -1, :].float() / config.temperature, dim=-1)
            drawn = torch.multinomial(probs, 1, generator=generator)
            tokens = drawn.squeeze(1).tolist()
            keep = [pos for pos, tok in enumerate(tokens) if tok != EOS]
            for pos in keep:
                chunk_seqs[active[pos]].append(tokens[pos])
            if not keep:
                active = []
                break
            if len(keep) < len(active):
                index = torch.tensor(keep, dtype=torch.long, device=device)
                h = h.index_select(1, index)
                drawn = drawn.index_select(0, index)
                active = [active[pos] for pos in keep]
            x = drawn
        still_active = set(active)
        sequences.extend(chunk_seqs)
        capped.extend(i in still_active for i in range(rows))
    return sequences, capped
