"""Post-hoc analysis of orchestrator outputs.

Aggregation, statistical tests, and figure generation. None of these modules
runs backends; they consume the ``RunLog`` JSONs produced by
:mod:`experiments.orchestrator`.
"""

from __future__ import annotations
