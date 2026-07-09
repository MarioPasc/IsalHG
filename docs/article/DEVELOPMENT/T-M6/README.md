# Scope T-M6 — optional package reparent

Cosmetic, and deliberately last. The isomorphism machinery (`iso_backends/`, the
iso protocols, the correctness and partition metrics) predates the metric-space
work and now sits as a sibling of it rather than as the separate concern it is.
Moving it under `isalhg/isomorphisms/` would make the article's dependency story
— `metric_space` depends on `core`, never on the isomorphism layer — visible in
the tree rather than only in the docs. It is a pure move plus import rewrite with
no behavioural change, so it must not land before the experiments do; a churned
import path during the experimental phase buys nothing and risks everything.
