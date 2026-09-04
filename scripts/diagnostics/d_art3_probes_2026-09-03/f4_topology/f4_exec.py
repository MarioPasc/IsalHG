"""Bounded-parallel execution of the E-A arm with a hard per-instance budget.

``canonical_string`` has no interruption point, so the budget is enforced the
way the earlier 2026-09-03 probes enforced it: one forked child per instance,
killed when it overruns. Children are cheap because the parent has already
imported the engine.
"""

from __future__ import annotations

import multiprocessing as mp
import time
from typing import Any

from f4_encodings import KB

from isalhg.core.canonical import canonical_string, required_k, seed_vertex_label


def _child(kb: KB, k: int | None, conn: Any) -> None:
    try:
        H = kb.to_hypergraph()
        kk = required_k(H) if k is None else k
        t0 = time.perf_counter()
        w = canonical_string(H, k=kk, algorithm="canonical", backend="cpp")
        dt = time.perf_counter() - t0
        conn.send({"ok": True, "w": w, "seed": int(seed_vertex_label(H, w)), "secs": dt})
    except Exception as exc:  # noqa: BLE001 - the probe records failures as data
        conn.send({"ok": False, "error": f"{type(exc).__name__}: {exc}"})
    finally:
        conn.close()


def map_word_A(
    tasks: list[tuple[KB, int | None]],
    *,
    budget: float = 60.0,
    workers: int = 16,
    progress: Any = None,
) -> list[dict]:
    """Compute ``w*_c`` for every task, censoring at ``budget`` seconds.

    Parameters
    ----------
    tasks : list[tuple[KB, int or None]]
        Knowledge base and the pointer count ``k`` to encode it with.
    budget : float, optional
        Per-instance wall-clock budget in seconds.
    workers : int, optional
        Maximum concurrent forked children.

    Returns
    -------
    list[dict]
        One record per task: ``{"ok", "w", "seed", "secs"}`` on success,
        ``{"ok": False, "dnf": True}`` on timeout, ``{"ok": False, "error": ...}``
        on failure.
    """
    ctx = mp.get_context("fork")
    results: list[dict | None] = [None] * len(tasks)
    running: dict[int, tuple[Any, Any, float]] = {}
    nxt = 0
    done = 0

    while done < len(tasks):
        while len(running) < workers and nxt < len(tasks):
            kb, k = tasks[nxt]
            parent_conn, child_conn = ctx.Pipe(duplex=False)
            proc = ctx.Process(target=_child, args=(kb, k, child_conn), daemon=True)
            proc.start()
            child_conn.close()
            running[nxt] = (proc, parent_conn, time.monotonic())
            nxt += 1
        if not running:
            break
        time.sleep(0.005)
        for idx in list(running):
            proc, conn, t0 = running[idx]
            payload: dict | None = None
            if conn.poll(0):
                try:
                    payload = conn.recv()
                except EOFError:
                    payload = {"ok": False, "error": "EOF"}
            elif not proc.is_alive():
                payload = {"ok": False, "error": "child died"}
            elif time.monotonic() - t0 > budget:
                proc.terminate()
                payload = {"ok": False, "dnf": True, "secs": budget}
            if payload is None:
                continue
            proc.join(timeout=5)
            if proc.is_alive():
                proc.kill()
                proc.join()
            conn.close()
            results[idx] = payload
            del running[idx]
            done += 1
            if progress is not None and done % max(1, len(tasks) // 20) == 0:
                progress(done, len(tasks))

    return [r if r is not None else {"ok": False, "error": "unscheduled"} for r in results]
