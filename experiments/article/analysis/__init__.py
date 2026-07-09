"""Analysis modules for the T-M5a article experiments.

Each module reads cached runner outputs (JSON / .npy) and produces:
- A summary dict with the key statistics for the paper tables.
- One or more matplotlib figures saved to the same output directory.

Modules
-------
correlation      E1 — Spearman/Pearson ρ + MI of d_I vs HGED.
density_sweep    E2 — ρ vs mean max-degree Δ with Theorem B envelope.
sensitivity      E2b — single-edit s(e) histogram by op type.
ladder           E3 — d_I vs edit budget; per-step increments (T-TBb proxy).
information_content  Bits + Wilcoxon + OLS compression-ratio table.
"""
