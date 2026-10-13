"""Generic-compressor renderings, sizes, bootstrap and version deltas.

A collection is written once per arm, one knowledge base per line, in one of
three renderings:

``ids``  space-separated integer ids (ids ranked by descending frequency);
``cp``   one Unicode code point per token (UTF-8, frequency-ranked, surrogates and
         ASCII control characters skipped);
``lit``  the literal serialization of the arm, which needs no dictionary.

``ids`` and ``cp`` need a token dictionary to be decodable. The *spec* number of a
compressor is the better of ``ids``/``cp`` with the dictionary uncharged; the
*self-contained* number is the best of ``ids + dict``, ``cp + dict`` and ``lit``,
where ``dict`` is the compressed literal alphabet table. Every size comes from the
command-line tool (``xz -9e``, ``zstd -19 --ultra``, ``bzip2 -9``) through stdin.
"""

from __future__ import annotations

import subprocess
import tempfile
from collections import Counter
from collections.abc import Hashable, Iterable, Sequence
from itertools import islice
from pathlib import Path

import numpy as np

from scripts.newpos.compression import serialize as ser

Symbol = Hashable

ZSTD_BIN = "/home/linuxbrew/.linuxbrew/bin/zstd"
BZIP2_BIN = "/opt/miniconda/bin/bzip2"
XZ_BIN = "/home/linuxbrew/.linuxbrew/bin/xz"
COMPRESSORS: tuple[str, ...] = ("xz", "zstd", "bzip2")
RENDERINGS: tuple[str, ...] = ("ids", "cp", "lit")


def compress_size_cli(kind: str, data: bytes) -> int:
    """Compressed size of ``data`` through the command-line tool named by the task."""
    if kind == "xz":
        cmd = [XZ_BIN, "-9e", "-c"]
    elif kind == "zstd":
        cmd = [ZSTD_BIN, "-19", "--ultra", "-c", "-q"]
    elif kind == "bzip2":
        cmd = [BZIP2_BIN, "-9", "-c"]
    else:
        raise ValueError(f"unknown compressor {kind!r}")
    return len(subprocess.run(cmd, input=data, capture_output=True, check=True).stdout)


def compress_size(kind: str, data: bytes) -> int:
    """Compressed size of ``data`` (alias of :func:`compress_size_cli`: one code path)."""
    return compress_size_cli(kind, data)


def frequency_ids(sequences: Iterable[Sequence[Symbol]]) -> dict[Symbol, int]:
    """Map each symbol to its rank by descending frequency (ties by first occurrence)."""
    counts: Counter[Symbol] = Counter()
    first: dict[Symbol, int] = {}
    for seq in sequences:
        for sym in seq:
            counts[sym] += 1
            first.setdefault(sym, len(first))
    ordered = sorted(counts, key=lambda s: (-counts[s], first[s]))
    return {sym: rank for rank, sym in enumerate(ordered)}


def codepoint_table(size: int) -> list[int]:
    """The first ``size`` allowed code points: printable ASCII, then above U+00A0, no surrogates."""
    allowed = (
        c for c in range(0x21, 0x110000) if not (0x7F <= c <= 0xA0) and not (0xD800 <= c <= 0xDFFF)
    )
    table = list(islice(allowed, size))
    if len(table) < size:
        raise ValueError(f"alphabet of {size} symbols exceeds the Unicode range")
    return table


def render_cp_line(seq: Sequence[Symbol], ids: dict[Symbol, int], table: Sequence[int]) -> str:
    """One member as a string with one code point per symbol."""
    return "".join(chr(table[ids[s]]) for s in seq)


def render_lines(
    arm: str,
    sequences: Sequence[Sequence[Symbol]],
    rendering: str,
    ids: dict[Symbol, int],
    table: Sequence[int],
) -> list[bytes]:
    """Per-member byte chunks of ``rendering``; concatenating chunks writes the collection.

    Chunks of ``ids``/``cp`` end in a newline; binary ``lit`` chunks are
    self-delimiting and carry no separator.
    """
    if rendering == "ids":
        return [(" ".join(str(ids[s]) for s in seq) + "\n").encode() for seq in sequences]
    if rendering == "cp":
        return [(render_cp_line(seq, ids, table) + "\n").encode("utf-8") for seq in sequences]
    if rendering == "lit":
        chunks: list[bytes] = []
        for seq in sequences:
            line = ser.literal_line(arm, seq)
            chunks.append(line if isinstance(line, bytes) else (line + "\n").encode())
        return chunks
    raise ValueError(f"unknown rendering {rendering!r}")


def dictionary_bytes(arm: str, ids: dict[Symbol, int]) -> bytes:
    """Literal alphabet table, one symbol per line in id order."""
    ordered = sorted(ids, key=ids.__getitem__)
    return ("\n".join(ser.symbol_text(arm, s) for s in ordered) + "\n").encode()


def point_sizes(
    arm: str,
    sequences: Sequence[Sequence[Symbol]],
    compressors: Sequence[str] = COMPRESSORS,
) -> list[dict[str, object]]:
    """Compressed size of the whole collection for every rendering and compressor.

    Returns
    -------
    list[dict]
        Rows with ``arm``, ``rendering``, ``compressor``, ``bytes``, ``dict_bytes``,
        ``raw_bytes`` and ``n_members``.
    """
    ids = frequency_ids(sequences)
    table = codepoint_table(len(ids))
    dictionary = dictionary_bytes(arm, ids)
    rows: list[dict[str, object]] = []
    for rendering in RENDERINGS:
        data = b"".join(render_lines(arm, sequences, rendering, ids, table))
        for kind in compressors:
            rows.append(
                {
                    "arm": arm,
                    "rendering": rendering,
                    "compressor": kind,
                    "bytes": compress_size(kind, data),
                    "dict_bytes": compress_size(kind, dictionary) if rendering != "lit" else 0,
                    "raw_bytes": len(data),
                    "n_members": len(sequences),
                }
            )
    return rows


def choose_renderings(rows: Sequence[dict[str, object]]) -> dict[tuple[str, str], dict[str, str]]:
    """Per ``(arm, compressor)``: the spec-best and the self-contained-best rendering."""
    best: dict[tuple[str, str], dict[str, str]] = {}
    keys = {(str(r["arm"]), str(r["compressor"])) for r in rows}
    for arm, kind in keys:
        sel = [r for r in rows if r["arm"] == arm and r["compressor"] == kind]
        spec = min((r for r in sel if r["rendering"] in ("ids", "cp")), key=lambda r: r["bytes"])  # type: ignore[arg-type,return-value]
        full = min(sel, key=lambda r: int(r["bytes"]) + int(r["dict_bytes"]))  # type: ignore[call-overload]
        best[(arm, kind)] = {
            "spec": str(spec["rendering"]),
            "self_contained": str(full["rendering"]),
        }
    return best


def bootstrap_sizes(
    chunks: Sequence[bytes],
    kind: str,
    index_sets: np.ndarray,
    member_symbols: Sequence[frozenset[int]] | None = None,
    symbol_texts: Sequence[bytes] | None = None,
) -> np.ndarray:
    """Bytes per KB over member resamples, each distinct drawn member recompressed once.

    A resample with replacement repeats about 37 % of its members, and a compressor
    codes an exact repeat of an earlier line almost for free, so the compressed size of
    the raw resample is biased low by 18-29 % (measured on the pilot; the bias differs by
    compressor and representation, which would distort ratios between representations).
    Each replicate therefore compresses the *distinct* members drawn (about 63 % of the
    collection), in collection order, and reports size per distinct KB. When
    ``member_symbols`` and ``symbol_texts`` are given the replicate's own dictionary (the
    symbols its members use) is compressed and charged, as in the point estimate.

    Parameters
    ----------
    chunks : Sequence[bytes]
        Per-member rendering chunks.
    kind : str
        Compressor name.
    index_sets : numpy.ndarray
        ``(reps, n_members)`` resample indices, shared across arms so differences stay paired.
    member_symbols : Sequence[frozenset[int]] or None, optional
        Per member, the dictionary ids it uses (``ids``/``cp`` renderings only).
    symbol_texts : Sequence[bytes] or None, optional
        Literal text of every dictionary id.

    Returns
    -------
    numpy.ndarray
        Compressed bytes per distinct KB, one value per replicate.
    """
    sizes = np.empty(index_sets.shape[0], dtype=np.float64)
    for r, idx in enumerate(index_sets):
        distinct = np.unique(idx)
        total = compress_size(kind, b"".join(chunks[i] for i in distinct))
        if member_symbols is not None and symbol_texts is not None:
            used = sorted(set().union(*(member_symbols[i] for i in distinct)))
            total += compress_size(kind, b"\n".join(symbol_texts[t] for t in used) + b"\n")
        sizes[r] = total / distinct.size
    return sizes


def zstd_patch_size(old: bytes, new: bytes, workdir: Path) -> int:
    """Bytes of ``zstd -19 --patch-from=<old> <new>`` (the delta of ``new`` against ``old``)."""
    old_path = workdir / "old.bin"
    new_path = workdir / "new.bin"
    old_path.write_bytes(old)
    new_path.write_bytes(new)
    cmd = [ZSTD_BIN, "-19", "--ultra", "-q", "-c", f"--patch-from={old_path}", str(new_path)]
    return len(subprocess.run(cmd, capture_output=True, check=True).stdout)


def delta_workdir() -> tempfile.TemporaryDirectory[str]:
    """A private temporary directory for the patch files."""
    return tempfile.TemporaryDirectory(prefix="cmp_delta_")


def percentile_ci(values: np.ndarray, confidence: float = 0.95) -> tuple[float, float]:
    """Percentile interval of bootstrap replicates."""
    tail = (1.0 - confidence) / 2.0
    low, high = np.quantile(values, [tail, 1.0 - tail])
    return float(low), float(high)


