# T-M3a — `NautyLeviEditDistance` (contrast baseline)
**Declared:** 2026-07-08 13:40 CEST (split from T-M3)
**Status:** OPEN
**Depends on:** T-M1a
**Context to read first:**
- `docs/article/COMPETITORS.md` §2–§3 — the *contrast* role (iso-only, no navigable geometry)
- `src/isalhg/iso_backends/pynauty_levi.py` + `src/isalhg/core/levi_reduction.py` (post-M1a)
- `.claude/rules/coding_rules.md` — always
**Description:** `HypergraphDistance` computing string-edit distance between the
nauty canonical forms of the Levi graphs. The deliberate contrast that *fails*
A4 (shortest path). Register in `metric_space/registry.py`.
**Acceptance:** `matrix()` runs on the correlation corpus; distance 0 on
isomorphic pairs; guarded `pynauty` import raises `RepresentationDependencyMissingError`.
**Out of scope here:** the head-to-head study (T-M5a).

---

**Appended by T-TAe (2026-07-09 13:22 CEST).** The nauty canonical form of a Levi
graph is *not* a complete invariant of a labelled hypergraph: `pynauty.certificate`
ignores the colouring, and the ordered partition nauty receives loses absolute
label identity. Build the canonical form as
`LeviGraph.color_signature() + pynauty.certificate(...)`, exactly as
`PynautyLeviBackend.fingerprint` now does — otherwise `matrix()` returns distance
0 on non-isomorphic labelled pairs and the "distance" is not a metric. On an
unlabelled corpus the signature is 20 bytes wide and encodes `(|V|, |E|)`: it is
byte-identical for any two hypergraphs of the same order and size, and otherwise
contributes at most 20 to their Levenshtein. Decide explicitly whether that
prefix belongs inside the edit distance or should be stripped after the
equality check, and record the choice — it shifts every `D_est` entry between
hypergraphs of different order.
