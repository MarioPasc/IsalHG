# Coding rules

Generic, project-agnostic rules for code refactors, scaffolding, and
maintenance. Applies whenever a task involves changing the shape of a
codebase, adding new components alongside existing patterns, or producing
new modules from scratch. Reference this file from project-specific guides
(`CLAUDE.md`, `CODE_DESIGN.md`) rather than copy-pasting it.

These rules assume Python 3.10+. Adapt syntactic specifics for other
languages while keeping the discipline.

---

## 1. Architecture

### 1.1 One concept per package, one ABC per concept

Each top-level concept ("isomorphism backend", "dataset loader", "benchmark
protocol", ...) lives in its own sub-package and exposes one abstract base
class as the single point of extension. The package is named after the
concept; the ABC lives in `<package>/base.py`.

Concrete subclasses live as siblings of `base.py`. The package's `__init__.py`
documents the dependency direction (what it may and may not import from
sibling packages).

If a new concept needs adding, that is a design discussion -- not a refactor
that adds files to a random folder.

### 1.2 Registries

Each extension-point package ships a `registry.py` exposing:

```python
def register_<thing>(name, factory): ...
def get_<thing>(name, params): ...
def available_<things>() -> tuple[<name_type>, ...]: ...
```

Concrete classes register themselves at *their own* module import time, not
eagerly at package import. Configuration files (YAML, JSON, argparse) refer
to extensions by name; the registry's `get_<thing>` performs the lazy import
when the name is requested.

This pattern keeps optional dependencies out of the import path and gives
configurations a single naming authority.

### 1.3 One-way dependency direction

Draw the dependency graph between sub-packages explicitly and document it
in `__init__.py`. Cycles are bugs.

A common pattern: a stdlib-only `core/` package holding the in-memory data
model; an `adapters/` layer that bridges external libraries; "logic" packages
(backends, protocols, metrics, ...) that consume `core` and `adapters` and
each other in a documented partial order.

If you find yourself needing an upward import (e.g. `core` importing from
`backends`), the code is mis-located. Move it instead of widening the
dependency.

### 1.4 Core has zero non-stdlib dependencies

The package holding the central data model imports only the standard
library plus typing/abc. External libraries (numpy, networkx, scipy, ...)
enter through adapter packages, not through `core`.

This keeps the package importable without optional dependencies and makes
the central algorithm portable and testable in isolation.

### 1.5 Adapters guard their imports

Every adapter imports its external library inside method bodies (not at
module top level) so the package remains importable when the dependency is
missing. The first call raises a custom
`AdapterDependencyMissingError` (or its analogue) with a concrete install
hint.

```python
def from_external(self, obj):
    try:
        import some_library
    except ImportError as e:
        raise AdapterDependencyMissingError(
            "some_library is required; install via `pip install <pkg>[extras]`"
        ) from e
    ...
```

---

## 2. Refactoring protocol

### 2.1 No backward-compatibility shims unless asked

When the user authorises a refactor, do not preserve old import paths,
deprecated method names, or "old"/"new" parallel APIs unless the user
explicitly asks for backward compatibility. Backward-compat shims accumulate
silently and become impossible to remove later.

Delete the old code, rename outright, and let import errors surface in
follow-up commits. Communicate the breakage in the commit message.

### 2.2 Scaffold first, fill second

A refactor that touches the shape of a codebase should land in two visible
steps:

1. Move files, create new packages, write ABCs and registries, write
   docstrings and `raise NotImplementedError` stubs. Tests are placeholders
   that `pytest.skip("not implemented yet")`. Lint, type-check, and
   test-collection all pass.
2. Fill stubs module by module, each landing with its own passing tests.

This separation makes the shape change reviewable on its own and avoids
mixing structural diffs with algorithmic ones.

### 2.3 Plan -> Test -> Implement -> Verify

For each non-trivial module:

1. Write the acceptance-criteria checklist in a comment block at the top of
   the file or in a sibling `.md`.
2. Write the failing test.
3. Implement.
4. Read the test output and explain what the diff confirms.

Do not close on "looks right". A test that passes is the closure event.

### 2.4 Track removals explicitly

When you delete a module during a refactor, record it in the project's
`DEVELOPMENT.md` or equivalent so future readers understand the absence is
intentional. Empty placeholders are harder to navigate than a documented
removal.

---

## 3. Code style

### 3.1 Type hints on every signature

Every public function, method, and dataclass field declares its types. Use
modern syntax: `X | None`, `list[int]`, `tuple[str, ...]`, `Iterator[T]`.
`TypeAlias` for any structured primitive.

Sigil-style annotations on private helpers are encouraged but not required.

### 3.2 NumPy-style docstrings

```
"""One-line summary.

Longer description if needed.

Parameters
----------
x : int
    What x is.

Returns
-------
y : int
    What y is.

Raises
------
SomeError
    When it raises.
"""
```

No usage examples in docstrings -- examples live in unit tests. Inline
comments explain *why*, never *what*: well-named identifiers carry the
"what". A comment that paraphrases the next line of code is noise.

### 3.3 Custom exception hierarchy per module

One root exception per package (`<Package>Error(Exception)`) and one
descendant per failure mode. Never raise bare `Exception`, `RuntimeError`,
or `ValueError` in library code; reserve those for genuinely unclassifiable
failures.

### 3.4 One class per file when the class exceeds about 100 lines

Below that, group small classes by topic in a single file. Above that,
split. The threshold is a heuristic; the underlying rule is "if a reader
opening the file has to scroll past the class they came to read, split."

### 3.5 Frozen dataclasses for value types

Use `@dataclass(frozen=True)` for any structured value that crosses
function boundaries. Mutable containers (lists, dicts) inside frozen
dataclasses are acceptable for performance-sensitive paths but must be
documented.

### 3.6 Logging over print

All `print` calls in library code go through `logging`. `print` is OK in
scripts and notebooks. Loggers are module-scoped:
`logger = logging.getLogger(__name__)`.

### 3.7 Comments are the exception, not the default

Default to no comments. Write a comment only when the *why* is non-obvious:
a hidden constraint, a subtle invariant, a workaround for a specific bug.
Do not explain *what* the code does (the code does that) or reference the
task that introduced the change (that belongs in the commit message).

---

## 4. Testing

### 4.1 pytest, parametrized

`pytest` is the sole test runner. Use `@pytest.mark.parametrize` for edge
cases: empty inputs, NaN, boundary dimensions, single-element batches.

### 4.2 Markers

Every test file declares its marker(s) at module level:

```python
pytestmark = pytest.mark.unit
```

Standard markers: `unit`, `integration`, `property`, `slow`. Add
project-specific markers when needed and declare them in
`pyproject.toml`'s `[tool.pytest.ini_options].markers` with
`--strict-markers` enabled.

### 4.3 Scientific assertions

Use library-grade tolerances:
`np.testing.assert_allclose(actual, expected, rtol=...)` or
`torch.testing.assert_close`. Never assert exact floating-point equality.

### 4.4 Property tests

For invariants that should hold across an input distribution (round-trip,
isomorphism-invariance, ...), use `hypothesis`. Property tests live under
`tests/property/` with their own marker.

### 4.5 Fixtures

Shared fixtures live in `conftest.py` at the lowest level they apply to
(repo root for repo-wide, package root for package-wide). Fixtures are
small structural builders, not data dumps from disk.

---

## 5. Configuration and experiments

### 5.1 YAML + dataclass

Experiment configurations live in human-readable YAML. The orchestrator
deserialises them into `@dataclass(frozen=True)` objects with a
`from_yaml(path)` classmethod. No pydantic, no hydra, no schema framework
unless the project scales to dozens of distinct config families.

### 5.2 Idempotent runs

The orchestrator skips cells whose result JSON already exists and
JSON-validates. Atomic writes (temp file + rename) prevent zero-byte
files on interrupt.

### 5.3 Pin and report seeds

Every stochastic run pins its random seed and includes the seed in its
result record. The seed enters the result file's content, not just its
filename.

### 5.4 Report wall-clock and memory alongside correctness

Every benchmark measures wall-clock time and peak resident-set size. A
run report that does not show both is incomplete.

---

## 6. Version-control hygiene

### 6.1 Conventional commits

`feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`. The subject line
is imperative and under 72 characters. The body explains *why* for any
non-trivial change.

### 6.2 No large binaries

Models, datasets, log dumps, and figures with embedded raster data go in
`.gitignore` or Git LFS, never the main tree.

### 6.3 Commit small refactor steps

A refactor that touches many files lands as a sequence of commits, one
per coherent step. Reviewers cannot reason about a 50-file shape change
landed in a single commit.

---

## 7. Documentation hygiene

### 7.1 Three documents, three audiences

- `README.md` -- one-paragraph project summary plus install/run pointers.
  Audience: someone who just landed on the repo.
- `CLAUDE.md` (or equivalent agent-instruction file) -- project identity,
  mindset, invariants. Audience: a coding agent picking up work without
  prior context.
- `CODE_DESIGN.md` (or equivalent design map) -- where each kind of code
  goes. Audience: an agent about to write code who needs to find the
  right file.

Generic patterns belong in `.claude/rules/coding_rules.md` (this file)
referenced from `CLAUDE.md`.

### 7.2 Doc paths in source comments are forbidden

A comment that says "see CODE_DESIGN.md section 3" rots when the section
is renumbered. Cite via stable anchors (class name, function name) or
inline the relevant sentence.

### 7.3 No status comments in code

`# TODO`, `# FIXME`, and `# removed` comments accumulate. Track work in
`DEVELOPMENT.md` or an issue tracker, not in the source tree.

---

## 8. Heuristics for borderline cases

- If you cannot decide between two locations for new code, prefer the
  package whose name explicitly mentions the concept.
- If you cannot decide between adding a new ABC and extending an existing
  one, stop and ask. A second ABC is harder to justify than a wider
  existing one.
- If you cannot decide whether a piece of state belongs in the package or
  in the experiment harness, ask "does a downstream user importing this
  package need it?" If yes, in the package; if no, in the harness.
- If you cannot decide between a registry entry and a hard-coded import,
  use the registry when the orchestrator references the thing by name in
  a config file, and a hard-coded import otherwise.

Always prefer the smaller change. A refactor that touches three files is
easier to land than one that touches thirty.
