"""Aggregate probe_timing.json into per-bucket median/p90 wall-clock and DNF fraction."""

from __future__ import annotations

import json
import statistics
from pathlib import Path

OUT = Path(__file__).resolve().parent


def pct(xs: list[float], p: float) -> float:
    if not xs:
        return float("nan")
    s = sorted(xs)
    i = min(len(s) - 1, max(0, int(round(p * (len(s) - 1)))))
    return s[i]


def main() -> None:
    d = json.loads((OUT / "probe_timing.json").read_text())
    print(f"engine: {d['engine']}  seed={d['seed']}  budget={d['budget_s']}s")
    for name, buckets in d["datasets"].items():
        print("=" * 96)
        print(name)
        hdr = (
            f"{'bucket':>8} {'avail':>5} {'smp':>3} {'mode':>10} "
            f"{'med_s':>9} {'p90_s':>9} {'DNF':>7} {'tok_med':>7} {'n_med':>5} {'m_med':>6}"
        )
        print(hdr)
        for key, b in buckets.items():
            if not b.get("sampled"):
                print(f"{key:>8} {b.get('available', 0):>5}   -  {'(none)':>10}")
                continue
            rows = b["rows"]
            for mode in ("labelled", "unlabelled"):
                res = [r[mode] for r in rows if isinstance(r.get(mode), dict)]
                ok = [r for r in res if r.get("ok")]
                dnf = [r for r in res if r.get("dnf")]
                secs = [r["sec"] for r in ok]
                toks = [r["tokens"] for r in ok]
                med = f"{statistics.median(secs):.4f}" if secs else "-"
                p90 = f"{pct(secs, 0.9):.4f}" if secs else "-"
                tm = f"{int(statistics.median(toks))}" if toks else "-"
                nm = int(statistics.median([r["n"] for r in rows]))
                mm = int(statistics.median([r["m"] for r in rows]))
                frac = f"{len(dnf)}/{len(res)}"
                print(
                    f"{key:>8} {b['available']:>5} {b['sampled']:>3} {mode:>10} "
                    f"{med:>9} {p90:>9} {frac:>7} {tm:>7} {nm:>5} {mm:>6}"
                )
        # paired labelled-vs-unlabelled speedup on instances where both completed
        pairs = []
        for b in buckets.values():
            for r in b.get("rows", []):
                lab, unl = r.get("labelled"), r.get("unlabelled")
                if (
                    isinstance(lab, dict)
                    and isinstance(unl, dict)
                    and lab.get("ok")
                    and unl.get("ok")
                ):
                    pairs.append((r["n"], r["m"], lab["sec"], unl["sec"]))
        if pairs:
            ratios = [u / l for _, _, l, u in pairs if l > 0]
            faster = sum(1 for _, _, l, u in pairs if l < u)
            print(
                f"  paired both-complete: {len(pairs)}; labelled faster in {faster}; "
                f"median speedup unlab/lab = {statistics.median(ratios):.2f}x; "
                f"total lab {sum(l for *_, l, _u in pairs):.1f}s vs unlab {sum(u for *_, _l, u in pairs):.1f}s"
            )


if __name__ == "__main__":
    main()
