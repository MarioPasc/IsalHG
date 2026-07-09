"""Fixed-width-code information-content estimator.

Ports the sibling IsalGraph paper's methodology (Table 1) to the
hypergraph setting.  The estimator is a **uniform fixed-width code**,
not Shannon self-information and not compressed length — this sidesteps
the "distribution model" problem and directly models the code-length
comparison between the IsalHG instruction string and a competitor
incidence-list encoding (PROPOSAL.md §3).

All functions are stdlib + ``math`` only; no numpy or scipy at import time.
"""

from __future__ import annotations

import math


def alphabet_size_isalhg(k: int) -> int:
    """Number of distinct token types in the ``Σ_HG(k)`` instruction alphabet.

    Counts, for the trivial (unlabelled) vocabulary:

    * ``V_{i,j}`` — one token per valid ``(i, j)`` pair satisfying
      ``1 ≤ i, j ≤ k-1`` and ``2 ≤ i+j ≤ k``.  The count equals
      ``k*(k-1)//2`` (triangle number ``T_{k-1}``).
    * ``C_i`` — ``k`` tokens (``i = 1 … k``).
    * ``P_i`` — ``k`` tokens (``i = 1 … k``).
    * ``N_i`` — ``k`` tokens (``i = 1 … k``).
    * ``W`` — 1 token.

    Total: ``k*(k-1)//2 + 3*k + 1``.

    For labelled vocabularies (``n_vertex_labels > 1`` or
    ``n_edge_labels > 1``), the V and C token counts expand by a factor of
    the label combination space; this function returns the unlabelled count
    (the experimental default).

    Parameters
    ----------
    k : int
        Maximum supported hyperedge arity (>= 2).

    Returns
    -------
    int
        Total number of distinct tokens in the unlabelled ``Σ_HG(k)``.

    Raises
    ------
    ValueError
        If ``k < 2``.
    """
    if k < 2:
        raise ValueError(f"k must be >= 2, got {k}")
    v_count = k * (k - 1) // 2
    return v_count + 3 * k + 1


def bits_isalhg(length: int, k: int) -> float:
    """Fixed-width code bits for an IsalHG instruction string of given length.

    ``B_IsalHG(w) = |w| · log₂ |Σ_HG(k)|``

    Parameters
    ----------
    length : int
        Token-sequence length ``|w|`` (number of instruction tokens).
    k : int
        Maximum supported hyperedge arity (>= 2).

    Returns
    -------
    float
        Bit count under the uniform fixed-width code.
    """
    if length == 0:
        return 0.0
    return length * math.log2(alphabet_size_isalhg(k))


def bits_incidence_list(n_nodes: int, arities: list[int]) -> float:
    """Competitor incidence-list encoding bit count.

    Generalises the IsalGraph sibling's formula
    ``B_GED = (N-1+M) + 2M·⌈log₂ N⌉`` (arity-2 edges) to arbitrary arity:

    * ``n_nodes - 1`` bits for vertex insertions.
    * Per hyperedge: ``1`` type bit  +  ``arity · ⌈log₂(n_nodes)⌉``
      endpoint-address bits.

    ``log₂(1) = 0``, so single-vertex graphs contribute 0 address bits.

    Parameters
    ----------
    n_nodes : int
        Number of vertices ``n``.
    arities : list[int]
        Arity of each hyperedge (one entry per edge).

    Returns
    -------
    float
        Total bit count under the incidence-list model.
    """
    vertex_bits = 0.0 if n_nodes <= 1 else float(n_nodes - 1)

    addr_bits = math.ceil(math.log2(n_nodes)) if n_nodes > 1 else 0
    edge_bits = sum(1 + a * addr_bits for a in arities)
    return vertex_bits + float(edge_bits)


def compression_ratio(bits_comp: float, bits_isalhg_val: float) -> float:
    """Compression ratio ``r = B_comp / B_IsalHG``.

    ``r > 1`` means IsalHG represents the hypergraph in fewer bits than the
    competitor incidence-list model.  A one-sided Wilcoxon signed-rank test
    on the vector ``r - 1`` over the corpus is the statistical test reported
    in the paper (PROPOSAL.md §3).

    Parameters
    ----------
    bits_comp : float
        Competitor bit count ``B_comp``.
    bits_isalhg_val : float
        IsalHG bit count ``B_IsalHG``.

    Returns
    -------
    float
        The compression ratio.

    Raises
    ------
    ValueError
        If ``bits_isalhg_val`` is zero (undefined ratio).
    """
    if bits_isalhg_val == 0.0:
        raise ValueError("bits_isalhg_val must be > 0 to compute a compression ratio")
    return bits_comp / bits_isalhg_val
