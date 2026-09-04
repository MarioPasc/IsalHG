"""wd50k_66 entity-type follow-up: derive entity lists, top up the P31 TSV, report."""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

from probe_hyperrel import ENV_M, ENV_N, K_MAX, MIN_STATEMENTS, build_star, load

SCRATCH = Path(
    "/tmp/claude-1000/-home-mpascual-research-code-IsalHG/"
    "b1064998-d2d4-4d37-b206-e4206ec0bb6c/scratchpad"
)
TSV = Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/data/wd50k/types/p31_types.tsv")
API = "https://www.wikidata.org/w/api.php"
UA = "IsalHG-research-probe/1.0 (https://github.com/MarioPasc; mario.pg02@gmail.com)"


def api_get(params: dict[str, str], attempts: int = 5) -> dict:
    url = API + "?" + urllib.parse.urlencode(params)
    delay = 2.0
    for i in range(attempts):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=120) as fh:
                return json.loads(fh.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 500, 502, 503, 504) and i < attempts - 1:
                time.sleep(delay)
                delay *= 2
                continue
            raise
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            if i < attempts - 1:
                time.sleep(delay)
                delay *= 2
                continue
            raise
    raise RuntimeError("unreachable")


def p31_of(ent: dict) -> list[str]:
    out = []
    for claim in ent.get("claims", {}).get("P31", []):
        dv = claim.get("mainsnak", {}).get("datavalue")
        if dv and dv.get("type") == "wikibase-entityid":
            qid = dv["value"].get("id")
            if qid:
                out.append(qid)
    return out


def read_tsv() -> dict[str, list[str]]:
    types: dict[str, list[str]] = {}
    for line in TSV.read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or "\t" not in line:
            continue
        q, _, v = line.partition("\t")
        types[q] = [x for x in v.split(",") if x]
    return types


def lists_wd50k66() -> tuple[list[str], list[str]]:
    stmts = load("wd50k_66", "csv", ("train.txt", "valid.txt", "test.txt"))
    by: dict[str, list] = {}
    for s in stmts:
        by.setdefault(s.subject, []).append(s)
    stars = [build_star(e, ss) for e, ss in by.items() if len(ss) >= MIN_STATEMENTS]
    env = [s for s in stars if s.n <= ENV_N and s.m <= ENV_M and s.max_arity <= K_MAX]
    return [s.entity for s in env], [s.entity for s in env if s.max_arity >= 3]


def labels(qids: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for i in range(0, len(qids), 50):
        data = api_get(
            {
                "action": "wbgetentities",
                "ids": "|".join(qids[i : i + 50]),
                "props": "labels",
                "languages": "en",
                "format": "json",
            }
        )
        for q, v in data.get("entities", {}).items():
            out[q] = v.get("labels", {}).get("en", {}).get("value", "?")
        time.sleep(1.0)
    return out


def report(name: str, ents: list[str], types: dict[str, list[str]], lab: dict, top: int) -> Counter:
    have = {e: types[e] for e in ents if e in types}
    with_t = {k: v for k, v in have.items() if v}
    cnt = Counter(t for v in with_t.values() for t in v)
    big = {t for t, c in cnt.items() if c >= 20}
    members = sum(1 for v in with_t.values() if any(t in big for t in v))
    print(f"\n### {name}")
    print(f"- entities: {len(ents):,} (fetched {len(have):,})")
    print(f"- with >= 1 P31: {len(with_t):,} ({100 * len(with_t) / max(1, len(ents)):.1f} %)")
    print(f"- distinct P31 types: {len(cnt):,}; types with >= 20 members: **{len(big)}**")
    print(
        f"- entities covered by such a type: {members:,} ({100 * members / max(1, len(ents)):.1f} %)"
    )
    if top:
        print("\n| # | QID | label | entities |\n|---|---|---|---|")
        for i, (t, c) in enumerate(cnt.most_common(top), 1):
            print(f"| {i} | {t} | {lab.get(t, '?')} | {c:,} |")
    return cnt


def main() -> None:
    env66, nary66 = lists_wd50k66()
    (SCRATCH / "wd50k66_entities.json").write_text(json.dumps({"env": env66, "nary": nary66}))
    types = read_tsv()
    todo = [e for e in env66 if e not in types and e[0] == "Q" and e[1:].isdigit()]
    print(
        f"[wd50k_66] env={len(env66)} n-ary={len(nary66)} already={len(env66) - len(todo)} todo={len(todo)}",
        flush=True,
    )

    t0 = time.time()
    with TSV.open("a", encoding="utf-8") as fh:
        for i in range(0, len(todo), 50):
            chunk = todo[i : i + 50]
            data = api_get(
                {
                    "action": "wbgetentities",
                    "ids": "|".join(chunk),
                    "props": "claims",
                    "format": "json",
                }
            )
            ents = data.get("entities", {})
            for q in chunk:
                e = ents.get(q)
                vals = p31_of(e) if isinstance(e, dict) else []
                types[q] = vals
                fh.write(f"{q}\t{','.join(vals)}\n")
            fh.flush()
            if (i // 50) % 10 == 0:
                print(f"[req] {i + len(chunk)}/{len(todo)} {round(time.time() - t0)}s", flush=True)
            time.sleep(1.0)
    print(
        f"[fetch] +{len(todo)} in {round(time.time() - t0)}s; TSV now {len(types):,} rows",
        flush=True,
    )

    raw = json.loads((SCRATCH / "types_raw.json").read_text())
    env100 = [e for e, s in raw["source"].items() if s == "wd50k_100"]
    union = list(dict.fromkeys(env66 + env100))

    c66 = Counter(t for e in env66 if types.get(e) for t in types[e])
    cna = Counter(t for e in nary66 if types.get(e) for t in types[e])
    cun = Counter(t for e in union if types.get(e) for t in types[e])
    want = sorted(
        {t for t, _ in c66.most_common(20)}
        | {t for t, _ in cna.most_common(20)}
        | {t for t, _ in cun.most_common(20)}
    )
    lab = labels(want)

    report("wd50k_66 in-envelope", env66, types, lab, 20)
    report("wd50k_66 in-envelope, n-ary subset (max arity >= 3)", nary66, types, lab, 20)
    report("union wd50k_66 + wd50k_100 in-envelope", union, types, lab, 20)

    # ---- single-label policy: most frequent P31 across the population, ties by QID order
    def qid_key(q: str) -> int:
        return int(q[1:])

    assign: dict[str, str] = {}
    for e in env66:
        v = types.get(e) or []
        if v:
            assign[e] = min(v, key=lambda t: (-c66[t], qid_key(t)))
    dist = Counter(assign.values())
    big = [(t, c) for t, c in dist.most_common() if c >= 20]
    lab2 = labels(sorted({t for t, _ in big} - set(lab)))
    lab.update(lab2)
    print(
        "\n### Single-label policy (argmax population frequency; ties by QID) — wd50k_66 in-envelope"
    )
    print(
        f"- labelled entities: {len(assign):,} / {len(env66):,}; distinct single labels: {len(dist):,}"
    )
    print(
        f"- classes with >= 20 members: **{len(big)}** covering {sum(c for _, c in big):,} entities "
        f"({100 * sum(c for _, c in big) / len(env66):.1f} % of in-envelope)"
    )
    print("\n| # | QID | label | members |\n|---|---|---|---|")
    for i, (t, c) in enumerate(big, 1):
        print(f"| {i} | {t} | {lab.get(t, '?')} | {c:,} |")


if __name__ == "__main__":
    sys.exit(main())
