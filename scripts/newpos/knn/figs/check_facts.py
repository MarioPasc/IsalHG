"""Check that knn_facts.tex defines every number and verdict that s5_knn.tex prints.

Greps ``\\KNNTBD{name}`` and ``\\KNNV{name}`` (defined as ``V-name``) in the
section, and ``\\knnfact{name}{value}`` in the facts file; fails when a name the
section uses is undefined, defined twice, defined without a preceding
``% src:`` line, or (for verdict cells) set to anything but ``\\KNNsurv``,
``\\KNNkill`` or ``\\KNNinf``. Names defined but unused are listed, not failed.
Exit status 0 on success, 1 otherwise.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

DEFAULT_TEX = Path(
    "/media/mpascual/Sandisk2TB/research/ISAL/isalhg/article/journal/"
    "6a788a680cdbdddd16e47a6e-lighten/submission/supplementary/sections/s5_knn.tex"
)
DEFAULT_FACTS = Path(
    "/media/mpascual/Sandisk2TB/research/ISAL/isalhg/results/KNN_2026-10-15/full/section/"
    "knn_facts.tex"
)
TBD = re.compile(r"\\KNNTBD\{([^}]+)\}")
VERDICT = re.compile(r"\\KNNV\{([^}]+)\}")
FACT = re.compile(r"^\\knnfact\{([^}]+)\}\{(.*)\}\s*$")
VERDICT_VALUES = {r"\KNNsurv", r"\KNNkill", r"\KNNinf"}


def used_names(tex: str) -> set[str]:
    """Names the section prints (comments stripped)."""
    body = "\n".join(
        line.split("%", 1)[0] if not line.lstrip().startswith("\\providecommand") else ""
        for line in tex.splitlines()
    )
    return set(TBD.findall(body)) | {f"V-{n}" for n in VERDICT.findall(body)}


def defined_facts(facts: str) -> tuple[dict[str, str], list[str]]:
    """``{name: value}`` and the problems found while reading the file."""
    out: dict[str, str] = {}
    problems: list[str] = []
    prev = ""
    for line in facts.splitlines():
        m = FACT.match(line.strip())
        if m:
            name, value = m.groups()
            if name in out:
                problems.append(f"{name}: defined twice")
            if not prev.startswith("% src:"):
                problems.append(f"{name}: no '% src:' line before it")
            out[name] = value
        if line.strip():
            prev = line.strip()
    return out, problems


def check(tex_path: Path, facts_path: Path) -> list[str]:
    """Every problem; empty when the facts cover the section."""
    used = used_names(tex_path.read_text())
    facts, problems = defined_facts(facts_path.read_text())
    problems += [f"{n}: used in {tex_path.name} but not defined" for n in sorted(used - set(facts))]
    problems += [
        f"{n}: verdict value {facts[n]!r} is not \\KNNsurv/\\KNNkill/\\KNNinf"
        for n in sorted(used & set(facts))
        if n.startswith("V-") and facts[n] not in VERDICT_VALUES
    ]
    return problems


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--tex", type=Path, default=DEFAULT_TEX)
    ap.add_argument("--facts", type=Path, default=DEFAULT_FACTS)
    args = ap.parse_args()
    used = used_names(args.tex.read_text())
    facts, _ = defined_facts(args.facts.read_text())
    problems = check(args.tex, args.facts)
    n_v = sum(n.startswith("V-") for n in used)
    print(f"{args.tex.name}: {len(used) - n_v} \\KNNTBD names, {n_v} verdict cells")
    print(f"{args.facts.name}: {len(facts)} facts")
    extra = sorted(set(facts) - used)
    if extra:
        print("defined but unused:", ", ".join(extra))
    for p in problems:
        print("FAIL", p)
    print("OK" if not problems else f"{len(problems)} problem(s)")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
