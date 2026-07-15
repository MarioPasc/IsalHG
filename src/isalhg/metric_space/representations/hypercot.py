"""``HyperCOTDistance`` — HyperCOT baseline via pinned conda-env subprocess.

HyperCOT (Chowdhury, Needham, Semrad, Wang, Zhou.  "Hypergraph co-optimal
transport: metric and categorical properties."  J. Appl. Comput. Topol.
7:1–60, 2023; companion paper 2024.  arXiv:2112.03904) defines a genuine
metric on hypergraph space via co-optimal transport on the probability
distributions over vertex and hyperedge sets.  It is a **fair** competitor
(metric by construction; distance 0 on isomorphic pairs) and also the
theoretical anchor cited in ``docs/article/theoretical/stability.md`` §2.0
for the arity-``k``-dependent Lipschitz constant.  See ``COMPETITORS.md``
§2 for the dual-role discussion.

Because HyperCOT pins ``hypernetx==1.2`` and ``POT==0.8.0``, both
incompatible with the main ``isalhg`` environment (which carries
``hypernetx>=2``), this class shells out to a dedicated conda environment
named ``isalhg-hypercot``.  The serialisation / subprocess pattern mirrors
:class:`isalhg.iso_backends.subprocess_base.SubprocessIsoBackend`.

Setup (one-time)
----------------
::

    conda env create -f envs/hypercot.yml
    git clone https://github.com/samirchowdhury/HyperCOT /tmp/HyperCOT
    ~/.conda/envs/isalhg-hypercot/bin/pip install -e /tmp/HyperCOT

After that, every call to :meth:`matrix` or :meth:`pairwise` runs
transparently inside ``isalhg-hypercot``.

References
----------
Chowdhury, S., Needham, T., Semrad, E., Wang, B., Zhou, Y.
"Hypergraph co-optimal transport: metric and categorical properties."
*J. Appl. Comput. Topol.* 7:1–60 (2023).  arXiv:2112.03904.
DOI:10.1007/s41468-023-00134-9.

See Also
--------
:class:`isalhg.metric_space.representations.subprocess_base.SubprocessRepresentation`
:mod:`scripts.hypercot_worker`
"""

from __future__ import annotations

from pathlib import Path

from isalhg.metric_space.registry import register_distance
from isalhg.metric_space.representations.subprocess_base import SubprocessRepresentation
from isalhg.types import DistanceName

# Worker script lives four levels above this file's package root
# (src/isalhg/metric_space/representations/ → src/ → repo root → scripts/).
_WORKER: Path = Path(__file__).parents[4] / "scripts" / "hypercot_worker.py"


class HyperCOTDistance(SubprocessRepresentation):
    """HyperCOT pairwise distance via pinned ``isalhg-hypercot`` conda env.

    Distance 0 on isomorphic pairs; ``O(n³)`` per pair; the full corpus matrix
    is computed in a single subprocess call to amortise startup overhead.

    Parameters
    ----------
    timeout_s : float or None, optional
        Wall-clock budget (seconds) for the subprocess call.  ``None`` inherits
        :attr:`SubprocessRepresentation.DEFAULT_TIMEOUT_S` (1 hour).

    Raises
    ------
    isalhg.errors.SubprocessRepresentationError
        If the ``isalhg-hypercot`` conda env is absent, the worker script is
        missing, or the subprocess exits non-zero or times out.  The error
        message contains the setup hint shown in the module docstring.
    """

    PINNED_ENV = "isalhg-hypercot"
    WORKER_SCRIPT = str(_WORKER)

    @property
    def name(self) -> DistanceName:
        return "hypercot"


register_distance("hypercot", HyperCOTDistance)
