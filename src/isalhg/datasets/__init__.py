"""Hypergraph dataset loaders.

Every dataset (synthetic, real-world, atlas) implements
:class:`isalhg.datasets.base.HypergraphDataset` and yields
:class:`isalhg.datasets.schemas.DatasetItem` instances. Concrete loaders are
registered in :mod:`isalhg.datasets.registry`.

This package may import from :mod:`isalhg.core` and :mod:`isalhg.adapters` but
not from :mod:`isalhg.iso_backends`, :mod:`isalhg.protocols`, or
:mod:`isalhg.metrics`.
"""

from __future__ import annotations
