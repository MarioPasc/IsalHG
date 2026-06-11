# isalhg.core

Pure-stdlib virtual machine and canonical algorithm. The implementation of
``Sigma_HG``, the S2H / H2S interpreters, and the canonical-string entry
point lives here.

Restriction: **no non-stdlib imports**. External hypergraph libraries are
walled off behind :mod:`isalhg.adapters`; iso baselines live in
:mod:`isalhg.iso_backends`.

See ``docs/CODE_DESIGN.md`` for the per-module mandate and the order in which
modules should be filled in.
