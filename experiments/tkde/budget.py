"""Process-level time budgets for the uninterruptible arms.

Two computations of the TKDE design do not return to the interpreter on
time-out and therefore cannot be bounded from inside Python
(``COMPETITOR_AUDIT.md`` §1, measured 2026-09-05):

* the **pointer** alphabet (``isalhg_levenshtein`` / ``canonical_string``) runs
  its tie-complete search inside the C++ extension, so a ``SIGALRM`` handler
  never executes and even ``SIGTERM`` does not end it -- only ``SIGKILL`` does;
* the **oracles** (``exact_ged``, ``qin_hged``) check their own ``timeout``
  argument inside the branch-and-bound loop but not during the pre-seeding
  assignment phase, so a call can overrun its constructor budget several-fold.

The only bound that holds for both is a forked child killed by the parent. That
is what :func:`run_with_budget` provides, in the shape the 2026-09-03 probes
used (``scripts/diagnostics/d_art3_probes_2026-09-03/f4_topology/f4_exec.py``):
one child per call, ``SIGKILL`` at the budget, the value returned over a pipe.

The ``fork`` start method is required and deliberate: the child inherits the
already-imported engine (so a child is cheap) and the callable and its arguments
travel by inheritance rather than by pickling, which is what lets a caller pass
a closure. Only the *returned value* crosses the pipe, so only it must be
picklable.
"""

from __future__ import annotations

import logging
import multiprocessing as mp
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from experiments.tkde.config import TkdeError

logger = logging.getLogger(__name__)

POLL_INTERVAL_S = 0.005
JOIN_GRACE_S = 5.0


class TkdeBudgetError(TkdeError):
    """A budgeted computation could not be started at all."""


@dataclass(frozen=True)
class BudgetResult:
    """Outcome of one budgeted call.

    Attributes
    ----------
    value : Any or None
        What the callable returned; ``None`` when the call was censored or
        raised.
    secs : float
        Wall-clock seconds. On a censored call this is the budget itself.
    censored : bool
        True when the child was killed at the budget.
    error : str or None
        ``"<ExceptionType>: <message>"`` when the callable raised, else
        ``None``. A censored call carries no error.
    """

    value: Any
    secs: float
    censored: bool
    error: str | None = None

    @property
    def ok(self) -> bool:
        """True when the call completed and returned a value."""
        return not self.censored and self.error is None


def _child(fn: Callable[..., Any], args: Sequence[Any], conn: Any) -> None:
    try:
        start = time.perf_counter()
        value = fn(*args)
        conn.send({"ok": True, "value": value, "secs": time.perf_counter() - start})
    except BaseException as exc:  # noqa: BLE001 - a failure is data, not a crash
        conn.send({"ok": False, "error": f"{type(exc).__name__}: {exc}"})
    finally:
        conn.close()


def run_with_budget_detail(
    fn: Callable[..., Any],
    args: Sequence[Any] = (),
    seconds: float = 60.0,
) -> BudgetResult:
    """Run ``fn(*args)`` in a forked child, killed after ``seconds``.

    Parameters
    ----------
    fn : callable
        The computation. Executed in a forked child, so it may be a closure;
        its return value must be picklable.
    args : Sequence, optional
        Positional arguments.
    seconds : float, optional
        Wall-clock budget. Default 60.

    Returns
    -------
    BudgetResult
        ``value`` on success; ``censored=True`` on time-out; ``error`` set when
        the callable raised.

    Raises
    ------
    TkdeBudgetError
        If ``seconds`` is not positive, or the child could not be started.
    """
    if seconds <= 0:
        raise TkdeBudgetError(f"budget must be positive, got {seconds}")

    ctx = mp.get_context("fork")
    parent_conn, child_conn = ctx.Pipe(duplex=False)
    process = ctx.Process(target=_child, args=(fn, tuple(args), child_conn), daemon=True)
    try:
        process.start()
    except OSError as exc:
        raise TkdeBudgetError(f"could not fork a budgeted child: {exc}") from exc
    child_conn.close()

    started = time.monotonic()
    payload: dict[str, Any] | None = None
    while True:
        if parent_conn.poll(POLL_INTERVAL_S):
            try:
                payload = parent_conn.recv()
            except EOFError:
                payload = {"ok": False, "error": "EOFError: child closed the pipe"}
            break
        if not process.is_alive():
            payload = {"ok": False, "error": "ChildDied: child exited without sending"}
            break
        if time.monotonic() - started > seconds:
            # SIGTERM is not enough: the C++ canonicaliser never returns to the
            # interpreter, so only SIGKILL ends it (COMPETITOR_AUDIT.md §1).
            process.kill()
            payload = None
            break

    parent_conn.close()
    process.join(timeout=JOIN_GRACE_S)
    if process.is_alive():  # pragma: no cover - only if SIGKILL itself is slow
        process.kill()
        process.join(timeout=JOIN_GRACE_S)

    if payload is None:
        return BudgetResult(value=None, secs=float(seconds), censored=True)
    if payload.get("ok"):
        return BudgetResult(value=payload["value"], secs=float(payload["secs"]), censored=False)
    elapsed = time.monotonic() - started
    return BudgetResult(
        value=None, secs=float(elapsed), censored=False, error=str(payload.get("error"))
    )


def run_with_budget(
    fn: Callable[..., Any],
    args: Sequence[Any] = (),
    seconds: float = 60.0,
) -> tuple[Any, float, bool]:
    """Frozen three-tuple form of :func:`run_with_budget_detail`.

    Parameters
    ----------
    fn : callable
        The computation.
    args : Sequence, optional
        Positional arguments.
    seconds : float, optional
        Wall-clock budget in seconds.

    Returns
    -------
    tuple
        ``(value | None, secs, censored)``. A call that raised returns
        ``(None, secs, False)`` and logs the exception; use
        :func:`run_with_budget_detail` when the error text is needed.
    """
    result = run_with_budget_detail(fn, args, seconds)
    if result.error is not None:
        logger.warning("budgeted call failed: %s", result.error)
    return result.value, result.secs, result.censored


# ---------------------------------------------------------------------------
# The pointer alphabet, budgeted
# ---------------------------------------------------------------------------


def _pointer_payload(H: Any, k: int) -> tuple[str, int]:
    from isalhg.core.canonical import canonical_string, seed_vertex_label

    word = canonical_string(H, k=k, algorithm="canonical")
    return word, int(seed_vertex_label(H, word))


def pointer_word(H: Any, k: int, seconds: float = 60.0) -> BudgetResult:
    """Canonical pointer string ``w*_c(H)`` under a process-level budget.

    Parameters
    ----------
    H : SparseHypergraph
        A **connected** knowledge base; the arm raises on disconnected input
        (decision B11, restated in ``COMPETITOR_AUDIT.md`` §3).
    k : int
        Pointer count. Two knowledge bases compared through their strings must
        be encoded with the same ``k`` (``DESIGN.md`` RQ1 arm A: the pair
        maximum).
    seconds : float, optional
        Budget. Default 60, the design's value.

    Returns
    -------
    BudgetResult
        ``value`` is ``(w_star, seed_vertex_label)``.
    """
    return run_with_budget_detail(_pointer_payload, (H, k), seconds)


def pointer_symbols(word: str, seed_label: int, *, augment: bool) -> tuple[Any, ...]:
    """Token sequence the pointer distance is measured over.

    Mirrors :meth:`isalhg.metric_space.distances.isalhg_levenshtein.IsalHGLevenshtein._symbols`
    so the budgeted path and the registered arm measure the same thing: the
    seed label is prepended exactly when the vertex vocabulary is non-trivial,
    which is what makes the fingerprint complete (Corollary A).

    Parameters
    ----------
    word : str
        The canonical string.
    seed_label : int
        Vertex label of the seed.
    augment : bool
        Whether either member has more than one vertex label.

    Returns
    -------
    tuple
        The symbol sequence.
    """
    from isalhg.core.instructions import parse

    tokens = tuple(parse(word))
    return (("seed", seed_label), *tokens) if augment else tokens


def encode_symbols(sequences: Sequence[Sequence[Any]]) -> list[str]:
    """Map symbol sequences to strings over a shared private alphabet.

    Levenshtein is invariant under any bijective relabelling of the symbols, so
    a per-call alphabet is sound and lets ``rapidfuzz``'s C++ kernel run on
    strings instead of on Python tuples.

    Parameters
    ----------
    sequences : Sequence[Sequence]
        The symbol sequences, all encoded against one alphabet.

    Returns
    -------
    list[str]
        One string per input sequence.
    """
    alphabet: dict[Any, str] = {}
    encoded: list[str] = []
    for sequence in sequences:
        buffer: list[str] = []
        for symbol in sequence:
            code = alphabet.get(symbol)
            if code is None:
                code = chr(len(alphabet))
                alphabet[symbol] = code
            buffer.append(code)
        encoded.append("".join(buffer))
    return encoded


def symbol_distance(a: Sequence[Any], b: Sequence[Any]) -> int:
    """Levenshtein distance between two symbol sequences.

    Parameters
    ----------
    a, b : Sequence
        Symbol sequences (pointer tokens, certificate rows, fact tokens).

    Returns
    -------
    int
        The raw (never length-normalized -- L11) edit distance.
    """
    from rapidfuzz.distance import Levenshtein

    left, right = encode_symbols([a, b])
    return int(Levenshtein.distance(left, right))
