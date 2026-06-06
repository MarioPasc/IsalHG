"""Optional bridges to external hypergraph libraries.

Each adapter guards its external import; importing this package does NOT
require any of the optional deps to be installed.

Supported backends: HyperNetX (PNNL), XGI (UVM), HyperGraphX. DHG was
considered and rejected during scaffolding due to abandoned-package signals
(deprecated sklearn shim + torch 1.13 pin); see project memory
``feedback_adapter_vetting.md``.
"""
