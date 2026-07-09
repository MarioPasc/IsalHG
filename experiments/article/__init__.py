"""T-M5a article experiment package.

Provides the runner, schemas, and analysis modules for the IsalHG metric-space
article Layer-1 experiments (correlation study, density sweep, single-edit
sensitivity, perturbation-ladder scaling, information-content comparison).

All computation outputs land in an external results directory (configured via
YAML) — never in the git tree. See configs/ for YAML templates.
"""
