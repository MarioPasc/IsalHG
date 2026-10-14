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
    *,
    daemon: bool = True,
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
    daemon : bool, optional
        Whether the child is daemonic. Default True, which ties its lifetime to
        this process. Pass False when ``fn`` itself budgets something -- a
        daemonic process may not have children, so a nested budget raises
        ``AssertionError: daemonic processes are not allowed to have children``
        from inside the child and surfaces as a unit that produced no result
        (measured: job 2264827, ``wd50k66/wstar_orbit``). A non-daemonic child
        is still killed here on time-out, and SLURM's cgroup reaps it if this
        process dies outright.

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
    process = ctx.Process(target=_child, args=(fn, tuple(args), child_conn), daemon=daemon)
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


def _engine_payload(H: Any, k: int, engine: str) -> tuple[str, int]:
    """``(word, seed vertex label)`` of one nauty-assisted Python engine.

    The two engines return the fingerprint the other way round -- ``(seed
    label, word)`` -- because that is the shape the completeness proof states;
    the tuple is flipped here so every budgeted engine, C++ or Python, hands
    back one shape and :func:`pointer_symbols` reads all of them.
    """
    import importlib

    module = importlib.import_module("isalhg.iso_backends.orbit_oracle")
    entry = {
        "rank": "canonical_fingerprint_rank",
        "orbit": "canonical_fingerprint_orbit",
    }[engine]
    seed_label, word = getattr(module, entry)(H, k=k)
    return str(word), int(seed_label)


#: The engines :func:`engine_word` can drive, in the order the design lists them.
ENGINES: tuple[str, ...] = ("cpp", "rank", "orbit")


def _runs_in_python(engine: str) -> bool:
    """Whether ``engine`` executes the pure-Python search in the forked child.

    Both nauty-assisted engines run in the C++ extension when it is importable
    (their entry points default to that backend) and in Python otherwise; only
    the Python case needs the memory guard.
    """
    if engine in ("rank", "orbit"):
        try:
            import isalhg.core._core  # noqa: F401
        except ImportError:
            return True
        return False
    return False


#: Largest ``min(k, max arity)`` the pure-Python engines accept. The Python
#: displacement search materialises ``(2r+1)^k`` tuples per frame (the C++
#: engine's Round-11 inversion does not), so arity-5 members already ask for
#: 1e8--7e11 tuples and exhaust memory (measured 2026-09-07 on wd50k66). Above
#: this bound the Python engines are refused up front and the row is censored
#: with the reason in ``error``, instead of taking the machine down.
PYTHON_ENGINE_MAX_K: int = 4

#: Largest displacement-tuple count ``(2(n-1)+1)^min(k, max arity)`` the
#: pure-Python engines accept; about 0.4 GB of tuples, measured on the
#: workstation that went out of memory at 5.8e6 (k = 4, n = 24).
PYTHON_ENGINE_MAX_TUPLES: int = 2_000_000

_CPP_FORK_HEALTH: bool | None = None

_POISONED = (
    "the C++ canonicalizer has already run in this process, so a forked child "
    "deadlocks on it and every result here would be a false censoring; route "
    "every cpp canonicalization through engine_word, or run this measurement in "
    "a fresh process"
)


def _canary() -> str:
    """The cheapest possible C++ canonicalization: two vertices, one edge."""
    from isalhg.core.canonical import canonical_string
    from isalhg.core.sparse_hypergraph import SparseHypergraph

    return canonical_string(
        SparseHypergraph(2, [frozenset({0, 1})]), k=2, algorithm="canonical", backend="cpp"
    )


def cpp_fork_is_healthy(*, recheck: bool = False) -> bool:
    """Whether a forked child of *this* process can still run the C++ engine.

    **A forked child cannot use the C++ canonicalizer if the parent has already
    used it.** Measured 2026-09-07: a first ``canonical_string(...,
    backend="cpp")`` in the parent leaves the extension in a state the child
    inherits and deadlocks on, so every subsequent budgeted call runs to its
    budget and is reported ``censored=True`` -- a *false* censoring,
    indistinguishable in the rows from a genuine one. A child of the same
    poisoned parent computing the *python* backend, or anything else at all, is
    unaffected; only the C++ path hangs.

    The campaign's runners route every C++ canonicalization through
    :func:`engine_word`, so the parent never touches the engine and the hazard
    does not arise there. It arises in any process that mixes the two -- a
    notebook, a probe, or a pytest session whose earlier tests exercised the
    engine directly.

    This canary is a single fork of a two-vertex hypergraph, memoised per
    process, so it costs milliseconds once and converts a silently corrupted
    censoring column into a loud failure. Poisoning is one-way and permanent, so
    a ``True`` verdict can go stale but a ``False`` one cannot;
    :func:`engine_word` therefore rechecks on -- and only on -- a censored
    result, which is the one outcome the two states are confusable in.

    Parameters
    ----------
    recheck : bool, optional
        Re-run the canary instead of answering from the memo.

    Returns
    -------
    bool
        True when a forked child completed the canary.
    """
    global _CPP_FORK_HEALTH
    if recheck or _CPP_FORK_HEALTH is None:
        _CPP_FORK_HEALTH = run_with_budget_detail(_canary, (), seconds=20.0).ok
        if not _CPP_FORK_HEALTH:
            logger.error(
                "the C++ canonicalizer has already run in this process, so a forked "
                "child deadlocks on it; every budgeted cpp call here would be "
                "reported censored without having been computed"
            )
    return _CPP_FORK_HEALTH


#: Arms whose representation is computed by the C++ engine, and which a forked
#: child therefore cannot compute in a poisoned process. The predicate a caller
#: needs for ``cpp_engine`` below; every other arm's child is unaffected by
#: poisoning (measured -- only the C++ path hangs).
CPP_ENGINE_ARMS: tuple[str, ...] = ("isalhg_levenshtein", "wstar_rank", "wstar_orbit")


def guarded_budget_call(
    fn: Callable[..., Any],
    args: Sequence[Any] = (),
    seconds: float = 60.0,
    *,
    cpp_engine: bool = True,
    daemon: bool = True,
) -> BudgetResult:
    """:func:`run_with_budget_detail` under the fork-health canary.

    The canary discipline is the same in every runner that forks a child which
    may reach the C++ engine, so it lives here once rather than in each of them:
    check before the fork, and -- because a censoring is the only outcome a
    deadlocked child and a genuinely slow one produce alike -- recheck on a
    censored result and refuse rather than report a censoring that never
    happened.

    The discipline applies only to a child that reaches the engine. Poisoning
    hangs the C++ path and nothing else, so a child computing a fact word, a
    nauty certificate or a vector fingerprint runs correctly in a poisoned
    process and its censoring is genuine; guarding those would refuse work that
    would have succeeded. ``cpp_engine`` is therefore the caller's declaration
    of what the child does, not a switch to be turned off for convenience.

    Parameters
    ----------
    fn : callable
        The computation, run in a forked child.
    args : Sequence, optional
        Positional arguments.
    seconds : float, optional
        Wall-clock budget.
    cpp_engine : bool, optional
        Whether the child may reach the C++ engine. Default True.
    daemon : bool, optional
        Passed through to :func:`run_with_budget_detail`. Pass False when ``fn``
        budgets something of its own, since a daemonic process may not fork.

    Returns
    -------
    BudgetResult
        Exactly what :func:`run_with_budget_detail` returned.

    Raises
    ------
    TkdeBudgetError
        If ``cpp_engine`` and the engine has already run in this process, in
        which case a censored result here would be a fiction.
    """
    if not cpp_engine:
        return run_with_budget_detail(fn, args, seconds, daemon=daemon)
    if not cpp_fork_is_healthy():
        raise TkdeBudgetError(_POISONED)
    result = run_with_budget_detail(fn, args, seconds, daemon=daemon)
    if result.censored and not cpp_fork_is_healthy(recheck=True):
        raise TkdeBudgetError(_POISONED)
    return result


def _arm_fingerprint(arm: str, H: Any) -> Any:
    from isalhg.metric_space.registry import get_distance

    return get_distance(arm).fingerprint(H)


def arm_fingerprint_screen(arm: str, seconds: float = 60.0) -> Callable[[Any], bool]:
    """A censoring screen for one arm, in the shape ``build_matrix_censored`` takes.

    The whole-matrix builder is a corpus-level operation and has no budget of
    its own; this is the per-member budget it is handed, so that a member whose
    representation does not finish is dropped and counted (L15) instead of
    hanging the build. The screen answers only *whether* the member finished:
    the value it computed is discarded, because the builder recomputes the
    surviving members' representations through the arm's own ``matrix`` and
    must produce exactly the values it would have produced without a screen.

    Measured 2026-09-08: ``wstar_rank``'s C++ entry point poisons the process
    for later forks exactly as ``canonical_string(backend="cpp")`` does (the
    ordered-walk emitter does not), so a caller that screens one arm and then
    builds in the same process cannot screen a second one. Run the whole build
    in a child -- which is what :mod:`experiments.tkde.matrices` does.

    Parameters
    ----------
    arm : str
        Registered distance name.
    seconds : float, optional
        Per-member wall-clock budget. Default 60, the design's value.

    Returns
    -------
    callable
        ``(H) -> bool``: True when this member's fingerprint completed.
    """

    engine = arm in CPP_ENGINE_ARMS

    def screen(H: Any) -> bool:
        return guarded_budget_call(_arm_fingerprint, (arm, H), seconds, cpp_engine=engine).ok

    return screen


def engine_word(H: Any, k: int, seconds: float = 60.0, engine: str = "cpp") -> BudgetResult:
    """A canonical ``Sigma_HG`` word under a process-level budget.

    Three engines produce a ``Sigma_HG`` word that cannot be bounded from inside
    Python: ``"cpp"`` (``w*_c`` in the C++ extension -- the SIGALRM handler never
    runs), and the two nauty-assisted Python engines ``"rank"`` and ``"orbit"``,
    whose search is a deep recursion with no time check of its own. All three go
    through the same forked child, so a censored row means the same thing for
    each.

    Parameters
    ----------
    H : SparseHypergraph
        A **connected** knowledge base; the arms raise on disconnected input
        (decision B11, restated in ``COMPETITOR_AUDIT.md`` §3).
    k : int
        Pointer count. Two knowledge bases compared through their strings must
        be encoded with the same ``k`` (``DESIGN.md`` RQ1 arm A: the pair
        maximum).
    seconds : float, optional
        Budget. Default 60, the design's value.
    engine : {"cpp", "rank", "orbit"}, optional
        Which engine computes the word. Default ``"cpp"``.

    Returns
    -------
    BudgetResult
        ``value`` is ``(word, seed_vertex_label)``.

    Raises
    ------
    TkdeBudgetError
        If ``engine`` is not one of the three, ``seconds`` is not positive, or
        the C++ engine has already run in this process (see
        :func:`cpp_fork_is_healthy`) -- in which case every censored row this
        call could produce would be a fiction, so it refuses instead.
    """
    if engine not in ENGINES:
        raise TkdeBudgetError(f"unknown engine {engine!r}; expected one of {ENGINES}")
    if engine != "cpp" and not _runs_in_python(engine):
        # The rank (wave 3) and orbit (wave 4) engines default to the C++
        # extension: they need the fork-health check of the cpp path, not the
        # Python memory guard.
        return guarded_budget_call(_engine_payload, (H, k, engine), seconds)

    if engine != "cpp":
        from isalhg.core.canonical import required_k

        k_eff = min(int(k), required_k(H))
        # The displacement search enumerates (2r+1)^k_eff tuples per frame with
        # r up to n-1, and the orbit engine caches the enumeration per (k, r);
        # 5.8e6 tuples (k=4, n=24) already cost ~1 GB, so both bounds are
        # needed: the arity bound and a tuple-count bound.
        # The search enumerates radius 1, 2, ... up to n-1 and the orbit engine
        # caches every radius, so the bound must be the SUM over radii, not the
        # largest term: with the largest-term bound alone, k=4, n=24 members
        # grew to 9.8 GB inside their 60 s budget and the node's memory limit
        # killed whole array tasks (RQ1 array 2247394, tasks 5/7/8, 2026-09-07).
        n_tuples = sum((2 * r + 1) ** k_eff for r in range(1, max(2, H.n_nodes)))
        refused = (
            f"k_eff={k_eff} > {PYTHON_ENGINE_MAX_K}"
            if k_eff > PYTHON_ENGINE_MAX_K
            else f"sum_r(2r+1)^k_eff={n_tuples} > {PYTHON_ENGINE_MAX_TUPLES}"
            if n_tuples > PYTHON_ENGINE_MAX_TUPLES
            else None
        )
        if refused is not None:
            logger.warning(
                "python engine %r refused (%s); the row is censored with the reason",
                engine,
                refused,
            )
            return BudgetResult(
                value=None,
                secs=0.0,
                censored=True,
                error=f"python engine refused: {refused}",
            )
        return run_with_budget_detail(_engine_payload, (H, k, engine), seconds)

    return guarded_budget_call(_pointer_payload, (H, k), seconds)


def pointer_word(H: Any, k: int, seconds: float = 60.0) -> BudgetResult:
    """Canonical pointer string ``w*_c(H)`` under a process-level budget.

    The ``engine="cpp"`` case of :func:`engine_word`, kept as its own name
    because that is what the campaign's existing rows were measured under.

    Parameters
    ----------
    H : SparseHypergraph
        A **connected** knowledge base.
    k : int
        Pointer count.
    seconds : float, optional
        Budget. Default 60, the design's value.

    Returns
    -------
    BudgetResult
        ``value`` is ``(w_star, seed_vertex_label)``.
    """
    return engine_word(H, k, seconds, engine="cpp")


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
