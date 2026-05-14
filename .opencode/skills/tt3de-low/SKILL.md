---
name: tt3de-low
description: >-
  Implements low-level operations in the tt3de engine — Rust core changes in
  src/ (geometry, raster, materials, buffers, textures, VM helpers) surfaced
  to Python via pyo3 thin bindings (*_py.rs) and matching wrappers under
  python/tt3de/. Runs a thorough design discovery pass first to validate the
  approach (subsystem placement, ownership/lifetimes, hot-path impact,
  parallel variants, Python API shape, error handling, tests), proposing
  reasonable defaults the user can accept by shorthand. Use when adding or
  changing native operations, when the user mentions "low-level", "Rust
  binding", "pyo3", "*_py.rs", "hot path", "raster", "geombuffer",
  "primitivbuffer", "primitiv_building", "vertexbuffer", "drawbuffer",
  "texturebuffer", "material bridge", "MaterialBufferPy", "DrawingBufferPy",
  "render_primitive", "PixInfo", "maturin develop", or asks to expose a Rust
  function/class to Python.
---

# tt3de low-level engine work

## Scope

Native engine changes in `src/**.rs` whose behavior must be **callable from Python**, plus the matching `python/tt3de/` wrappers. Typical subsystems: `drawbuffer/`, `geombuffer/`, `primitivbuffer/`, `primitiv_building/`, `raster/`, `material/`, `texturebuffer/`, `vertexbuffer/`, `utils/`, and the non-language parts of `ttsl/` (VM/runtime, not opcode authoring — see *Boundary* below).

**Boundary**: TTSL language / compiler / opcode work is owned by [`.opencode/skills/ttsl-implementation/SKILL.md`](../ttsl-implementation/SKILL.md). New TTSL builtins that need a Rust hook (geometry, raster context, textures) call this skill from step 3 of that one.

## Contract documents

These rules are the contract for the work; consult them while designing and before implementing:

| Topic | File |
|-------|------|
| Rust safety, hot-path, bindings shape | [`.cursor/rules/rust-standards.mdc`](../../.cursor/rules/rust-standards.mdc) |
| Python API & wrapper conventions | [`.cursor/rules/python-standards.mdc`](../../.cursor/rules/python-standards.mdc) |
| Scoped diffs, public-API + docs sync | [`.cursor/rules/workflow-guardrails.mdc`](../../.cursor/rules/workflow-guardrails.mdc) |
| Test coverage expectations | [`.cursor/rules/testing-standards.mdc`](../../.cursor/rules/testing-standards.mdc) |

Repo-level build, test, and platform notes (PowerShell quoting, `cargo check --all-targets`, `uv run maturin develop`, `PYTHONPATH=.` for pytest) live in [`AGENTS.md`](../../AGENTS.md). Treat its commands as authoritative.

## Design discovery before implementation

**Do not write Rust or wrapper code until the design is validated.** Low-level changes are expensive to undo: they cross an FFI boundary, touch hot paths, and often imply tests in two ecosystems. Always run a thorough discovery pass first.

### How to ask

Present **numbered questions** with a **concise suggested answer** for each, inferred from what the user already said. Explain once how to reply:

- **`n:y`** — accept the suggestion for question `n`.
- **`n:n`** or **`n:no`** — reject the suggestion; the agent asks a brief follow-up or offers alternatives.
- **`n: <free text>`** — custom answer for question `n`.
- Multiple lines or **`1:y, 2:y, 3: custom...`** in one message is fine.

When the **AskQuestion** tool (or equivalent structured UI) is available, mirror the same numbered options as clickable choices — keep wording aligned with the markdown suggestions.

If the user already stated the design unambiguously in their latest message, **still confirm** with one short recap question they can answer with `1:y` to proceed.

### Question themes (pick the subset that fits)

For each, give a **specific** suggested answer grounded in current code, not a generic one. Examples of what a good suggestion looks like — adapt, don't copy verbatim:

1. **Subsystem placement** — Which `src/<module>/` owns this? *Suggest e.g. "extend `src/raster/raster_triangle_tomato.rs`; no new module".*
2. **Pure-Rust core vs binding** — Will the logic live in a plain Rust module and the `*_py.rs` stay thin (per `rust-standards.mdc`)? *Suggest the split, naming the Rust function and the wrapper method.*
3. **Python surface shape** — New `#[pyclass]`, new free `#[pyfunction]`, new method on an existing class, or a function added to a submodule (e.g. `materials`, `toglyphmethod`)? *Suggest the smallest addition; prefer extending an existing class.*
4. **Argument & return types across FFI** — Plain `f32`/`usize`, `Py<PyAny>` glm matrix via `convert_pymat4`, `PyTuple` return, or a Rust struct exposed as `#[pyclass]`? *Suggest the convention used by neighbors (e.g. `convert_pymat4` + `mat4_to_pyglm` round-trip for matrices).*
5. **Ownership & lifetimes** — Does the caller pass a buffer we mutate in place, or do we return a new owned value? Any `&mut` aliasing risk with the existing buffer types? *Suggest in-place mutation through the existing `*BufferPy` handle when one already exists.*
6. **Hot-path impact** — Frame-time call site, or one-shot setup? Allocation budget? Bounds-checking strategy? *If hot, suggest pre-sized buffers and validated indices per `rust-standards.mdc`; if cold, accept ergonomic allocations.*
7. **Parallel variant** — Does it need a `_parallel` sibling like `apply_material_py_parallel`? *Suggest "single-threaded first; add parallel only when a benchmark shows the win".*
8. **Error handling** — Panics (programmer error), `PyResult`/specific Python exceptions (user-facing), or silent clamp? *Suggest `PyResult` with a typed error message for anything reachable from user code.*
9. **Public API & back-compat** — Is any existing Python signature changing? *If yes, surface it explicitly (workflow-guardrails) and propose a migration note.*
10. **Tests** — `cargo test` for pure-Rust semantics, `tests/tt3de/test_r_*.py` for the binding round-trip, both? *Suggest "both" for anything user-callable; "Rust only" for internal helpers.*
11. **Docs** — Does `source/*.md` or a README section mention this surface? *Suggest the file to update in the same change.*
12. **Bench coverage** — Should this land with a `tests/benchs/r_code/` or `benches/*.rs` case? *Suggest "yes" only for hot paths or perf-motivated changes.*

Skip questions that don't apply; do not pad the discovery list.

## After discovery — implementation order

Work through the sequence below; only collapse a step when it genuinely doesn't apply.

1. **Pure-Rust core** in the right `src/<module>/` file. Small composable functions, explicit ownership, validated indices. Keep `mod.rs` exports minimal. (`rust-standards.mdc`)
2. **Rust unit tests** (`#[cfg(test)] mod tests`) for the new core function — at least one happy path and one boundary/invalid case. (`testing-standards.mdc`)
3. **Thin `*_py.rs` binding** — argument conversion (`convert_pymat4`, `find_glyph_indices_py`, etc.), error mapping to `PyResult`, no new business logic. Register the class/function in `src/lib.rs`'s `#[pymodule] fn tt3de` (and the appropriate submodule + `sys.modules` entry if you mirror the `materials` / `toglyphmethod` pattern).
4. **Build & sanity-check Rust** — `cargo check --all-targets` (treat warnings as failures); on Windows redirect via `cmd /c "cargo check --all-targets 2> output.txt"` per `AGENTS.md`. Then `uv run maturin develop` (or `--profile release` when benching).
5. **Python wrapper** under `python/tt3de/` — keep argument names, defaults, and behavior aligned with the Rust-backed implementation (`python-standards.mdc`). Add typed signatures for new public APIs.
6. **Python tests** — focused cases under `tests/tt3de/` (use the `tests/tt3de/test_r_*.py` neighbors as templates for binding tests). Run with `PYTHONPATH=.` per `AGENTS.md`:
   - PowerShell: `$env:PYTHONPATH='.'; uv run pytest <path>`
   - bash/zsh: `PYTHONPATH=. uv run pytest <path>`
7. **Docs sync** — update the closest canonical doc (`README.md`, `source/*.md`) in the same change when behavior or public API moves (`workflow-guardrails.mdc`, docs standard).
8. **Benchmark** (only when motivated) — extend `benches/*.rs` or `tests/benchs/r_code/` so perf claims are reproducible.

## Common patterns to follow

- **Thin bindings**: see [`src/vertexbuffer/transform_pack_py.rs`](../../src/vertexbuffer/transform_pack_py.rs) — the `#[pymethods]` block only converts and dispatches.
- **Submodule registration**: the `materials` and `toglyphmethod` blocks in [`src/lib.rs`](../../src/lib.rs) show the `PyModule::new` + `sys.modules.set_item` pattern needed for nested imports.
- **Function exposure**: `wrap_pyfunction!(...)` entries in `src/lib.rs` for top-level `#[pyfunction]`s.
- **Matrix interop**: `crate::utils::{convert_pymat4, mat4_to_pyglm, mat4_to_slicelist}` — do not re-roll matrix marshalling.
- **Glyph indices**: reuse `find_glyph_indices_py` for any glyph-string input rather than parsing in the new binding.
- **Parallel variant naming**: `<name>_py` and `<name>_py_parallel` (cf. `apply_material_py` / `apply_material_py_parallel`).

## Anti-patterns

- Adding business logic inside `*_py.rs` (violates `rust-standards.mdc` — the binding should stay thin).
- Allocating per-frame inside a raster/geometry loop because it's "easier from Python".
- Exposing internals by widening a `mod.rs` `pub use` instead of adding a focused binding.
- Changing a public Python signature without updating wrappers, demos, and docs in the same change.
- Skipping `cargo check --all-targets` after a binding edit; warnings often surface only at the test/bench target level.
- Running `pytest` without `PYTHONPATH=.` and then debugging the resulting `tests.*` import error.

## Verification checklist

- [ ] Discovery questions answered (or explicitly waived with `1:y`-style confirmation)
- [ ] Pure Rust function lives in the right `src/<module>/` file with bounds/validity checks
- [ ] `*_py.rs` binding is thin (conversion + error mapping only)
- [ ] Class/function registered in `src/lib.rs` (and `sys.modules` if a submodule)
- [ ] `cargo check --all-targets` clean (zero warnings)
- [ ] `cargo test` covers the new core behavior
- [ ] `uv run maturin develop` succeeds
- [ ] Python wrapper has typed signatures and matches Rust argument names/defaults
- [ ] `uv run pytest` (with `PYTHONPATH=.`) covers the binding round-trip
- [ ] Docs (`README.md` / `source/*.md`) updated when public surface changed
- [ ] No unrelated refactors in the diff
