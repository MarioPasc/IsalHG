"""Task B: fetch Wikidata P31 ("instance of") for in-envelope star-KB anchors.

Reads the entity lists produced by ``probe_hyperrel.py`` (key ``_env_entities``),
queries the Wikidata ``wbgetentities`` action in batches of 50, and writes a TSV
``entity<TAB>type1,type2,...``.  Non-QID anchors (literals, dates) are skipped.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SCRATCH = Path(
    "/tmp/claude-1000/-home-mpascual-research-code-IsalHG/"
    "b1064998-d2d4-4d37-b206-e4206ec0bb6c/scratchpad"
)
OUT_DIR = Path("/media/mpascual/Sandisk2TB/research/ISAL/isalhg/data/wd50k/types")
API = "https://www.wikidata.org/w/api.php"
UA = "IsalHG-research-probe/1.0 (https://github.com/MarioPasc; mario.pg02@gmail.com)"
BATCH = 50
DELAY_S = 1.0
CAP_ENTITIES = 10_000
CAP_SECONDS = 60 * 60


def is_qid(s: str) -> bool:
    return len(s) > 1 and s[0] == "Q" and s[1:].isdigit()


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


def p31_of(entity: dict) -> list[str]:
    out: list[str] = []
    for claim in entity.get("claims", {}).get("P31", []):
        snak = claim.get("mainsnak", {})
        dv = snak.get("datavalue")
        if dv and dv.get("type") == "wikibase-entityid":
            qid = dv["value"].get("id")
            if qid:
                out.append(qid)
    return out


def main() -> None:
    res = json.loads((SCRATCH / "probe_hyperrel_results.json").read_text())
    extra = SCRATCH / "results_wd50k_100.json"
    if extra.exists():
        res.update(json.loads(extra.read_text()))

    order: list[str] = []
    seen: set[str] = set()
    source: dict[str, str] = {}
    for coll in ("wd50k_100", "wd50k"):
        for e in res.get(coll, {}).get("_env_entities", []):
            if e in seen or not is_qid(e):
                continue
            seen.add(e)
            source[e] = coll
            order.append(e)
            if len(order) >= CAP_ENTITIES:
                break
        if len(order) >= CAP_ENTITIES:
            break

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tsv = OUT_DIR / "p31_types.tsv"
    t0 = time.time()
    types: dict[str, list[str]] = {}
    if tsv.exists():  # resume: keep what was already fetched
        for line in tsv.read_text(encoding="utf-8").splitlines():
            if line.startswith("#") or "\t" not in line:
                continue
            q, _, v = line.partition("\t")
            types[q] = [x for x in v.split(",") if x]
        order = [e for e in order if e not in types]
        print(f"[resume] {len(types)} already fetched, {len(order)} to go", flush=True)
    n_req = 0
    with tsv.open("a" if types else "w", encoding="utf-8") as fh:
        if not types:
            fh.write("# entity\ttypes(P31 QIDs, comma-separated)\n")
        for i in range(0, len(order), BATCH):
            if time.time() - t0 > CAP_SECONDS:
                print(f"[cap] time cap hit after {i} entities", flush=True)
                break
            chunk = order[i : i + BATCH]
            data = api_get(
                {
                    "action": "wbgetentities",
                    "ids": "|".join(chunk),
                    "props": "claims",
                    "format": "json",
                }
            )
            n_req += 1
            ents = data.get("entities", {})
            for q in chunk:
                ent = ents.get(q)
                vals = p31_of(ent) if isinstance(ent, dict) else []
                types[q] = vals
                fh.write(f"{q}\t{','.join(vals)}\n")
            fh.flush()
            if n_req % 10 == 0:
                print(
                    f"[req {n_req}] {i + len(chunk)}/{len(order)} "
                    f"elapsed={round(time.time() - t0)}s",
                    flush=True,
                )
            time.sleep(DELAY_S)

    (SCRATCH / "types_raw.json").write_text(
        json.dumps({"types": types, "source": source}, indent=0)
    )
    print(f"[done] {len(types)} entities, {n_req} requests, {round(time.time() - t0)}s -> {tsv}")


if __name__ == "__main__":
    sys.exit(main())
