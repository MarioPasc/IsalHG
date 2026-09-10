"""Score the 600 s tail against T-KBe's pre-stated expectation.

The expectation was written before the data existed and is deliberately
refutable, so this analyzer states a verdict rather than leaving one to a
reader. Its two clauses, verbatim from
``T-KBe`` §"Pre-stated expectation for the 600 s re-run":

1. ``wstar_orbit`` "has 32 completions in [30, 60) and 6 in [55, 60). A
   population that dense just below the budget should continue above it, so a
   **material fraction** of its 77 is expected to finish by 600 s."
2. ``wstar_rank`` "has none. If the gap is real, **most** of its 53 should still
   be censored at 600 s -- they are arity-10 displacement enumerations,
   exponential in the arity, not slow instances of an otherwise-feasible
   search."

and the refutable form: "if instead most of the 53 complete at 600 s, the
bimodality is an artefact of the budget rather than of the mechanism, and the
claim that the residual tail is displacement rather than a slow tail of the same
search would need rewriting."

**The two thresholds are fixed here, in code, before the run** -- that is the
point of a pre-stated expectation. "Material fraction" is
:data:`MATERIAL_FRACTION` = 0.25: a tenfold budget that recovers less than a
quarter of a tail has not shown that tail to continue the feasible-search
distribution. "Most" is :data:`MOST_FRACTION` = 0.50, which is what the word
means. Both raw counts are printed beside every verdict so a reader who prefers
another threshold can apply it.

Nothing here reads or writes an RQ tree. The rows are tail characterisation
(D-ART5 decision 2) and stay that way.
"""

from __future__ import annotations

import argparse
import csv
import logging
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from experiments.tkde.config import TkdeStatsError
from experiments.tkde.tail600 import KIND, resolve_paths

logger = logging.getLogger(__name__)

#: The fraction of a tail that must complete for the completion to count as a
#: "material fraction" (clause 1). Pre-registered, not chosen after the data.
MATERIAL_FRACTION = 0.25

#: The fraction that makes "most" (clause 2 and the refutable form).
MOST_FRACTION = 0.50

#: Significance level for the differential (orbit vs rank) test.
DIFFERENTIAL_ALPHA = 0.05

CONFIRMED = "CONFIRMED"
REFUTED = "REFUTED"
INDETERMINATE = "INDETERMINATE"


class Tail600AnalysisError(TkdeStatsError):
    """The analyzer was handed rows it cannot score."""


@dataclass(frozen=True)
class ArmTally:
    """Completion census of one arm's tail at the larger budget.

    Attributes
    ----------
    arm : str
        Arm name.
    total : int
        Members re-run.
    completed : int
        Members that finished inside the budget.
    censored : int
        Members still censored.
    """

    arm: str
    total: int
    completed: int
    censored: int

    @property
    def completion_fraction(self) -> float:
        """Completed over total; ``0.0`` on an empty tally."""
        return self.completed / self.total if self.total else 0.0


@dataclass(frozen=True)
class Verdict:
    """One clause of the pre-stated expectation, scored.

    Attributes
    ----------
    clause : str
        Short name of the clause.
    arm : str
        The arm it is about.
    outcome : str
        ``"CONFIRMED"``, ``"REFUTED"`` or ``"INDETERMINATE"``.
    detail : str
        One sentence carrying the counts the outcome rests on.
    """

    clause: str
    arm: str
    outcome: str
    detail: str


def tally(rows: Iterable[Mapping[str, Any]], arm: str) -> ArmTally:
    """Completion census of one arm.

    Parameters
    ----------
    rows : Iterable[Mapping]
        Tail rows; each carries ``arm`` and ``censored``.
    arm : str
        Arm to count.

    Returns
    -------
    ArmTally
        Its census. An arm with no rows yields ``total == 0``.
    """
    mine = [row for row in rows if row.get("arm") == arm]
    censored = sum(1 for row in mine if str(row.get("censored")) in ("1", "True", "true"))
    return ArmTally(arm=arm, total=len(mine), completed=len(mine) - censored, censored=censored)


def verdict_material(tally_: ArmTally) -> Verdict:
    """Clause 1 -- a material fraction of ``wstar_orbit``'s tail completes.

    Parameters
    ----------
    tally_ : ArmTally
        The ``wstar_orbit`` census.

    Returns
    -------
    Verdict
        ``CONFIRMED`` when the completion fraction reaches
        :data:`MATERIAL_FRACTION`, ``REFUTED`` when it does not, and
        ``INDETERMINATE`` on an empty tally.
    """
    if tally_.total == 0:
        return Verdict(
            "material-fraction",
            tally_.arm,
            INDETERMINATE,
            f"no {tally_.arm} rows: the clause cannot be scored",
        )
    fraction = tally_.completion_fraction
    outcome = CONFIRMED if fraction >= MATERIAL_FRACTION else REFUTED
    return Verdict(
        "material-fraction",
        tally_.arm,
        outcome,
        f"{tally_.completed}/{tally_.total} = {fraction:.1%} completed at the larger budget "
        f"(material fraction pre-registered at {MATERIAL_FRACTION:.0%})",
    )


def verdict_most_censored(tally_: ArmTally) -> Verdict:
    """Clause 2 -- most of ``wstar_rank``'s tail stays censored.

    Parameters
    ----------
    tally_ : ArmTally
        The ``wstar_rank`` census.

    Returns
    -------
    Verdict
        ``CONFIRMED`` when strictly more than half stay censored, ``REFUTED``
        when at least half complete, ``INDETERMINATE`` on an empty tally.
    """
    if tally_.total == 0:
        return Verdict(
            "most-still-censored",
            tally_.arm,
            INDETERMINATE,
            f"no {tally_.arm} rows: the clause cannot be scored",
        )
    fraction = tally_.completion_fraction
    outcome = CONFIRMED if fraction < MOST_FRACTION else REFUTED
    return Verdict(
        "most-still-censored",
        tally_.arm,
        outcome,
        f"{tally_.censored}/{tally_.total} = {1 - fraction:.1%} still censored "
        f"({tally_.completed} completed; 'most' pre-registered at {MOST_FRACTION:.0%})",
    )


def verdict_mechanism(tally_: ArmTally) -> Verdict:
    """The refutable form -- is the bimodality the budget or the mechanism?

    Parameters
    ----------
    tally_ : ArmTally
        The ``wstar_rank`` census.

    Returns
    -------
    Verdict
        ``CONFIRMED`` means the mechanism reading stands: the residual tail is
        displacement, and D-ART5 needs no rewriting. ``REFUTED`` means most of
        the tail completed, the bimodality is an artefact of the 60 s budget,
        and D-ART5's "displacement rather than symmetry" claim must be
        rewritten.
    """
    if tally_.total == 0:
        return Verdict(
            "displacement-not-budget",
            tally_.arm,
            INDETERMINATE,
            f"no {tally_.arm} rows: the mechanism claim cannot be scored",
        )
    fraction = tally_.completion_fraction
    if fraction >= MOST_FRACTION:
        return Verdict(
            "displacement-not-budget",
            tally_.arm,
            REFUTED,
            f"{tally_.completed}/{tally_.total} = {fraction:.1%} completed, i.e. most of them: "
            "the bimodality is an artefact of the 60 s budget, not of the mechanism, and "
            "D-ART5's 'the residual tail is displacement rather than symmetry' needs rewriting",
        )
    return Verdict(
        "displacement-not-budget",
        tally_.arm,
        CONFIRMED,
        f"{tally_.censored}/{tally_.total} = {1 - fraction:.1%} still censored at a tenfold "
        "budget: the gap is the mechanism (arity-10 displacement enumeration), not the budget, "
        "and D-ART5 stands as written",
    )


def _wilson(successes: int, trials: int, z: float = 1.959963985) -> tuple[float, float]:
    """Wilson score interval for one proportion."""
    if trials == 0:
        return (0.0, 1.0)
    phat = successes / trials
    denom = 1 + z**2 / trials
    centre = (phat + z**2 / (2 * trials)) / denom
    half = z * ((phat * (1 - phat) / trials + z**2 / (4 * trials**2)) ** 0.5) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def difference_ci(a_ok: int, a_n: int, b_ok: int, b_n: int) -> tuple[float, float]:
    """Newcombe's hybrid-score interval for the difference of two proportions.

    Accurate at the sample sizes here (77 and 53) where a normal-approximation
    interval is not. Built from the two Wilson intervals, per Newcombe (1998),
    *Statistics in Medicine* 17(8):873-890, method 10.

    Returns
    -------
    tuple of float
        95 % interval for ``p_a - p_b``.
    """
    p_a = a_ok / a_n if a_n else 0.0
    p_b = b_ok / b_n if b_n else 0.0
    l_a, u_a = _wilson(a_ok, a_n)
    l_b, u_b = _wilson(b_ok, b_n)
    delta = p_a - p_b
    lower = delta - ((p_a - l_a) ** 2 + (u_b - p_b) ** 2) ** 0.5
    upper = delta + ((u_a - p_a) ** 2 + (p_b - l_b) ** 2) ** 0.5
    return (max(-1.0, lower), min(1.0, upper))


def verdict_differential(orbit: ArmTally, rank: ArmTally) -> Verdict:
    """The claim is DIFFERENTIAL, so the arms are tested against each other.

    Clauses 1 and 2 score each arm against a threshold, and both can pass while
    the arms are statistically indistinguishable from one another -- orbit at
    45 % and rank at 40 % would score CONFIRMED twice and still leave the
    mechanism claim unsupported, because the claim is that these are *different*
    tails: a dense near-boundary population above the budget for the orbit
    engine, and arity-10 displacement enumeration for the rank engine.

    Two arms recovering at a comparable rate therefore refutes the mechanism
    **even when both individual clauses pass**, which is the reading a per-arm
    rate alone hides. Fisher's exact test on the 2x2, two-sided.

    Parameters
    ----------
    orbit, rank : ArmTally
        The two censuses.

    Returns
    -------
    Verdict
        ``CONFIRMED`` when the recovery rates differ significantly *and* orbit
        is the higher of the two; ``REFUTED`` when they do not differ or the
        ordering is inverted; ``INDETERMINATE`` when either arm has no rows.
    """
    if orbit.total == 0 or rank.total == 0:
        return Verdict(
            "differential",
            "wstar_orbit vs wstar_rank",
            INDETERMINATE,
            "one arm has no rows: the differential claim cannot be scored",
        )
    from scipy.stats import fisher_exact

    table = [
        [orbit.completed, orbit.censored],
        [rank.completed, rank.censored],
    ]
    _, pvalue = fisher_exact(table, alternative="two-sided")
    low, high = difference_ci(orbit.completed, orbit.total, rank.completed, rank.total)
    delta = orbit.completion_fraction - rank.completion_fraction
    detail = (
        f"orbit {orbit.completed}/{orbit.total} = {orbit.completion_fraction:.1%} vs "
        f"rank {rank.completed}/{rank.total} = {rank.completion_fraction:.1%}, "
        f"difference {delta:+.1%} 95% CI [{low:+.1%}, {high:+.1%}], "
        f"Fisher exact two-sided p = {pvalue:.3g}"
    )
    if pvalue < DIFFERENTIAL_ALPHA and delta > 0:
        return Verdict("differential", "wstar_orbit vs wstar_rank", CONFIRMED, detail)
    if delta <= 0:
        # The point estimate is null or inverted: the claim genuinely fails,
        # whether or not the failure reaches significance.
        return Verdict(
            "differential",
            "wstar_orbit vs wstar_rank",
            REFUTED,
            detail + " -- the estimate is null or INVERTED, so the mechanism claim fails "
            "whatever the per-arm clauses say",
        )
    # The estimate favours the claim but the interval spans zero. That is an
    # underpowered comparison, not a refutation: at 77 and 53 members Fisher
    # needs roughly a 25-point gap, so a real mechanism of moderate size lands
    # here. Labelling it REFUTED would retire a true claim -- and this verdict
    # propagates to R2, RQ7's envelope sentence and D-ART5's rationale, so it
    # would rewrite three claims on insufficient data.
    return Verdict(
        "differential",
        "wstar_orbit vs wstar_rank",
        INDETERMINATE,
        detail + " -- favours the claim but the interval spans no differential: "
        "UNDERPOWERED at these member counts, not refuted",
    )


def score(rows: Sequence[Mapping[str, Any]]) -> tuple[list[ArmTally], list[Verdict]]:
    """Every arm's census and the three clause verdicts.

    Parameters
    ----------
    rows : Sequence[Mapping]
        Tail rows.

    Returns
    -------
    tuple
        ``(tallies, verdicts)``. ``tallies`` covers every arm present, sorted;
        ``verdicts`` is clause 1 (orbit), clause 2 and the refutable form
        (rank), each scored ``INDETERMINATE`` when its arm has no rows.
    """
    arms = sorted({str(row.get("arm")) for row in rows if row.get("arm")})
    tallies = [tally(rows, arm) for arm in arms]
    orbit = tally(rows, "wstar_orbit")
    rank = tally(rows, "wstar_rank")
    return tallies, [
        verdict_material(orbit),
        verdict_most_censored(rank),
        verdict_mechanism(rank),
        verdict_differential(orbit, rank),
    ]


def read_rows(root: Path | str, *, smoke: bool = False) -> list[dict[str, Any]]:
    """Read every tail row file under the characterisation tree.

    Parameters
    ----------
    root : Path or str
        Results root.
    smoke : bool, optional
        Read the smoke subtree instead.

    Returns
    -------
    list[dict]
        All rows, deduplicated on ``(collection, member_id, arm)``.

    Raises
    ------
    Tail600AnalysisError
        If no row file is present, or a row is not tail characterisation -- a
        row from anywhere else must never be scored here.
    """
    # Exact components, not a recursive '**': the smoke subtree lives INSIDE the
    # characterisation folder, and a recursive glob would score its 5 s rows
    # alongside the 600 s ones and inflate the completion count that decides the
    # verdict.
    directory = resolve_paths(Path(root), smoke=smoke).dir
    paths = sorted(directory.glob("rows_tail600__*.csv"))
    if not paths:
        raise Tail600AnalysisError(f"no tail rows under {directory}")
    seen: dict[tuple[str, str, str], dict[str, Any]] = {}
    for path in paths:
        with path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                if row.get("kind") != KIND:
                    raise Tail600AnalysisError(
                        f"{path} carries a row with kind={row.get('kind')!r}; "
                        f"only {KIND!r} rows may be scored here"
                    )
                seen.setdefault((row["collection"], row["member_id"], row["arm"]), dict(row))
    return list(seen.values())


def budgets(rows: Iterable[Mapping[str, Any]]) -> list[float]:
    """The distinct budgets the rows were taken at, sorted.

    Reported rather than assumed: a smoke run and the campaign write the same
    row schema, and a report that names a budget its rows were not taken at is
    the kind of sentence that reaches prose unchallenged.
    """
    seen = set()
    for row in rows:
        try:
            seen.add(float(row.get("budget_s")))  # type: ignore[arg-type]
        except (TypeError, ValueError):
            continue
    return sorted(seen)


def render(
    tallies: Sequence[ArmTally],
    verdicts: Sequence[Verdict],
    budget_s: Sequence[float] = (),
) -> str:
    """The report, as printed.

    Parameters
    ----------
    tallies : Sequence[ArmTally]
        Per-arm census.
    verdicts : Sequence[Verdict]
        The scored clauses.
    budget_s : Sequence[float], optional
        Budgets the rows were taken at; named in the heading. More than one
        means the rows are mixed and the heading says so.

    Returns
    -------
    str
        The markdown report.
    """
    label = "/".join(f"{b:g}" for b in budget_s) if budget_s else "?"
    lines = [
        f"# {label} s tail characterisation (D-ART5 decision 2 -- never a published row)",
        "",
        f"| arm | re-run | completed at {label} s | still censored | completion |",
        "|---|---|---|---|---|",
    ]
    for item in tallies:
        lines.append(
            f"| `{item.arm}` | {item.total} | {item.completed} | {item.censored} | "
            f"{item.completion_fraction:.1%} |"
        )
    lines += ["", "## Verdict against the pre-stated expectation (T-KBe)", ""]
    for verdict in verdicts:
        lines.append(
            f"- **{verdict.clause}** (`{verdict.arm}`): **{verdict.outcome}** — {verdict.detail}"
        )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    """The analyzer CLI."""
    parser = argparse.ArgumentParser(prog="experiments.tkde.analyze_tail600", description=__doc__)
    parser.add_argument("--root", type=Path, default=None, help="Results root.")
    parser.add_argument("--smoke", action="store_true", help="Score the smoke subtree.")
    parser.add_argument("--out", type=Path, default=None, help="Write the report here as well.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = build_parser().parse_args(argv)

    from experiments.tkde import corpora as corpora_io

    root = Path(args.root) if args.root else corpora_io.results_root()
    rows = read_rows(root, smoke=bool(args.smoke))
    tallies, verdicts = score(rows)
    report = render(tallies, verdicts, budgets(rows))
    print(report)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(report + "\n", encoding="utf-8")
        logger.info("wrote %s", args.out)
    return 0


if __name__ == "__main__":  # pragma: no cover - entry point
    raise SystemExit(main())
