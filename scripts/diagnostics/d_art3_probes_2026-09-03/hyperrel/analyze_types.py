"""Task B analysis: P31 coverage, top-30 types (with labels), usable class count."""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

SCRATCH = Path(
    "/tmp/claude-1000/-home-mpascual-research-code-IsalHG/"
    "b1064998-d2d4-4d37-b206-e4206ec0bb6c/scratchpad"
)
UA = "IsalHG-research-probe/1.0 (https://github.com/MarioPasc; mario.pg02@gmail.com)"


def labels(qids: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for i in range(0, len(qids), 50):
        url = "https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(
            {
                "action": "wbgetentities",
                "ids": "|".join(qids[i : i + 50]),
                "props": "labels",
                "languages": "en",
                "format": "json",
            }
        )
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=60) as fh:
            data = json.loads(fh.read().decode())
        for q, v in data.get("entities", {}).items():
            out[q] = v.get("labels", {}).get("en", {}).get("value", "?")
        time.sleep(1.0)
    return out


def block(name: str, types: dict[str, list[str]], lab: dict[str, str] | None = None) -> Counter:
    with_t = {k: v for k, v in types.items() if v}
    cnt = Counter(t for v in with_t.values() for t in v)
    big = {t for t, c in cnt.items() if c >= 20}
    members = sum(1 for v in with_t.values() if any(t in big for t in v))
    print(f"\n### {name}")
    print(f"- entities queried: {len(types):,}")
    print(f"- with >= 1 P31: {len(with_t):,} ({100 * len(with_t) / max(1, len(types)):.1f} %)")
    print(f"- distinct P31 types: {len(cnt):,}")
    print(f"- types with >= 20 in-envelope entities: {len(big):,}")
    print(
        f"- entities carrying such a type: {members:,} ({100 * members / max(1, len(types)):.1f} %)"
    )
    if lab is not None:
        print("\n| # | QID | English label | entities |")
        print("|---|---|---|---|")
        for i, (t, c) in enumerate(cnt.most_common(30), 1):
            print(f"| {i} | {t} | {lab.get(t, '?')} | {c:,} |")
    return cnt


def main() -> None:
    d = json.loads((SCRATCH / "types_raw.json").read_text())
    types, source = d["types"], d["source"]
    t100 = {k: v for k, v in types.items() if source.get(k) == "wd50k_100"}
    twd = {k: v for k, v in types.items() if source.get(k) == "wd50k"}

    cnt_all = Counter(t for v in types.values() for t in v)
    cnt_100 = Counter(t for v in t100.values() for t in v)
    want = sorted({t for t, _ in cnt_all.most_common(30)} | {t for t, _ in cnt_100.most_common(30)})
    lab = labels(want)
    block("wd50k_100 in-envelope anchors", t100, lab)
    block("WD50K in-envelope anchors (remainder, cap 10,000 total)", twd)
    block("pooled", types, lab)


if __name__ == "__main__":
    main()
