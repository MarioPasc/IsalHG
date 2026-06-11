"""IsalHG experiment harness.

Mirror of the IsalSR ``experiments/`` repo-root layout. Not part of the
installable ``isalhg`` package; invoked as ``python -m experiments.orchestrator
--config experiments/configs/<tier>.yaml``.

The orchestrator drives the experiment matrix
``Protocol x Backend x Dataset x Seed`` by reading a YAML config and looking
up registered protocols, backends, and datasets from the registries in
:mod:`isalhg.protocols.registry`, :mod:`isalhg.iso_backends.registry`, and
:mod:`isalhg.datasets.registry`.
"""

from __future__ import annotations
