"""Traces backend via the Levi bipartite reduction (subprocess to ``dreadnaut``).

Traces ships only as a CLI (``dreadnaut`` from the nauty distribution); there
is no Python binding as of nauty 2.9. This backend serialises the Levi graph
to dreadnaut's input language, invokes the binary in Traces mode, and parses
the canonical labelling (sparse6-encoded) from stdout.

dreadnaut session shape::

    At              -- switch to Traces engine
    c -a            -- enable canonical labelling, suppress automorphism output
    n=<N>           -- vertex count (Levi: |V| + |E| of the hypergraph)
    f=[c0_list | c1_list | ...]  -- vertex colouring partition
    g               -- begin graph entry
    0: nbr nbr ...;
    1: nbr nbr ...;
    ...
    <N-1>: nbr nbr ...
    .               -- end of graph block
    x               -- run Traces (canon graph is computed)
    b6              -- emit canonical graph in graph6/sparse6 ASCII form
    q               -- quit

The ``b6`` line is the canonical *graph*; it carries no trace of the ``f=``
partition, and ``f=`` itself is an ordered partition that has forgotten which
label id each cell holds. The fingerprint is therefore
``LeviGraph.color_signature() + b6``; see :mod:`isalhg.core.levi_reduction` for
why the pair is exact. Two hypergraphs are isomorphic iff those fingerprints
are byte-equal under identical dreadnaut options (mode, getcanon, partition).
"""

from __future__ import annotations

from typing import ClassVar

from isalhg.core.levi_reduction import to_levi
from isalhg.core.sparse_hypergraph import SparseHypergraph
from isalhg.errors import BackendOutputParseError
from isalhg.iso_backends.registry import register_backend
from isalhg.iso_backends.subprocess_base import SubprocessIsoBackend
from isalhg.types import BackendName, Fingerprint


class TracesLeviBackend(SubprocessIsoBackend):
    """Traces isomorphism backend over the Levi bipartite reduction."""

    BINARY_NAME: ClassVar[str] = "dreadnaut"

    @property
    def name(self) -> BackendName:
        return "traces_levi"

    def fingerprint(self, H: SparseHypergraph) -> Fingerprint:
        if H.n_nodes == 0:
            return b""
        return to_levi(H).color_signature() + super().fingerprint(H)

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def _serialize(self, H: SparseHypergraph) -> str:
        levi = to_levi(H)
        n = levi.n_nodes
        # Adjacency, one direction only (dreadnaut undirected mode adds the
        # reverse automatically).
        adjacency: dict[int, list[int]] = {v: [] for v in range(n)}
        for u, v in levi.edges:
            lo, hi = (u, v) if u < v else (v, u)
            adjacency[lo].append(hi)
        for v in adjacency:
            adjacency[v].sort()

        f_clauses = [_compress_range(sorted(cls)) for cls in levi.color_classes()]
        f_directive = "f=[" + " | ".join(f_clauses) + "]"

        # g block.
        g_lines: list[str] = []
        for v in range(n):
            nbrs = adjacency[v]
            terminator = "." if v == n - 1 else ";"
            if nbrs:
                g_lines.append(f"{v}: " + " ".join(str(x) for x in nbrs) + terminator)
            else:
                g_lines.append(f"{v}:{terminator}")

        return f"At\nc -a\nn={n}\n{f_directive}\ng\n" + "\n".join(g_lines) + "\nx\nb6\nq\n"

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------

    def _parse(self, stdout: str) -> Fingerprint:
        # The ``b6`` command emits the canonical graph as a single
        # printable-ASCII line. Stats lines from ``x`` contain spaces /
        # keywords; the graph6 line is the only non-empty space-free
        # printable line. Return the last such line.
        candidates: list[str] = []
        for raw in stdout.splitlines():
            line = raw.strip()
            if not line:
                continue
            if " " in line or "=" in line or ";" in line:
                continue
            if any(line.startswith(ch) for ch in (">", "<")):
                continue
            # graph6 / sparse6 strings consist of printable ASCII (no spaces).
            if all(0x21 <= ord(ch) <= 0x7E for ch in line):
                candidates.append(line)
        if not candidates:
            raise BackendOutputParseError(
                f"no graph6/sparse6 line found in dreadnaut stdout:\n{stdout[:2048]}"
            )
        return candidates[-1].encode("ascii")


def _compress_range(values: list[int]) -> str:
    """Render a sorted unique int list with ``x:y`` range shorthand."""
    if not values:
        return ""
    pieces: list[str] = []
    run_start = values[0]
    prev = run_start
    for v in values[1:]:
        if v == prev + 1:
            prev = v
            continue
        if run_start == prev:
            pieces.append(str(run_start))
        else:
            pieces.append(f"{run_start}:{prev}")
        run_start = v
        prev = v
    if run_start == prev:
        pieces.append(str(run_start))
    else:
        pieces.append(f"{run_start}:{prev}")
    return ",".join(pieces)


# Self-register at import time.
register_backend("traces_levi", lambda: TracesLeviBackend())
