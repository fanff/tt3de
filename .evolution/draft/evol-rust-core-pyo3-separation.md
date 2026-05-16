# Evolution: Rust core and PyO3 binding separation

```yaml
id: evol-rust-core-pyo3-separation
created: 2026-05-11
authors: [fanf]
supersedes: []
superseded-by: ""
related:
  - Cargo.toml
  - src/lib.rs
  - source/index.rst
  - source/high_level_api.rst
  - source/low_level_api.rst
```

## Summary

Restructure tt3de so the Rust rendering engine can be built, tested, and distributed as a pure Rust crate, while the Python/PyO3 wrapper remains available as an optional package layered on top. Today core engine types and Python bindings live in the same Rust crate and many modules mix `#[pyclass]`, `#[pymethods]`, conversion helpers, and native rendering logic. This evolution proposes a staged split: first isolate binding code behind clear module boundaries, then make PyO3 optional and non-invasive, and finally support separate distribution paths for Rust consumers and Python users without changing the high-level Python API unnecessarily.

## Motivation and context

- **Current behavior** — tt3de is a mixed Rust/Python project built with `maturin`. The docs present the library primarily as a Python/Textual engine, while `source/low_level_api.rst` documents native-style buffers such as Transform, Geometry, Primitive, Texture, Material, and Drawing buffers. The Rust crate currently exposes the engine modules from `src/lib.rs`, but the same crate also defines the Python module and imports PyO3 directly.
- Several Rust modules combine native data structures and Python wrappers in one file. Examples include `src/geombuffer/mod.rs`, `src/drawbuffer/mod.rs`, `src/material/mod.rs`, `src/primitivbuffer/mod.rs`, and `src/texturebuffer/mod.rs`. Other areas already hint at a better split, such as `src/vertexbuffer/vertex_buffer.rs` next to `src/vertexbuffer/vertex_buffer_py.rs` and `src/material/materials.rs` next to `src/material/materials_py.rs`.
- **Problem today** — A Rust user cannot reason about tt3de as a clean engine crate without also inheriting PyO3 concepts, Python conversion utilities, and wrapper naming. This makes distribution, documentation, compile features, and future embedders harder than necessary.
- **Reference comparison** — Many Rust projects expose a small native core crate and separate language bindings (`*-py`, `*-ffi`, `*-wasm`, etc.). That shape keeps the core API stable and testable while letting wrappers adapt to each host language's conventions.
- This fits tt3de's scope because the renderer is already a CPU-only software engine with explicit buffers and deterministic pipeline stages. Those are natural Rust library concepts independent of Textual or Python. Python remains the main app-facing workflow, but it should not be the only viable packaging target.
- **Reasoning** — A big-bang workspace split is risky because PyO3 types currently appear across many modules. An incremental refactor can first move wrappers beside native modules, then tighten feature gates, then decide whether a full Cargo workspace split is worth the churn.

## Goals

- **Core API separation**: Define a PyO3-free Rust engine surface for buffers, materials, rasterization, primitive building, textures, TTSL execution, and utility math conversions that do not require Python objects.
- **Binding isolation**: Move or keep all PyO3-specific wrappers in clearly named `*_py.rs` files or a dedicated binding crate/module tree. Native modules should not need `pyo3` imports.
- **Optional Python build**: Make `pyo3` and Python module registration compile only when the Python binding feature is enabled.
- **Distribution clarity**: Support a pure Rust build path for downstream Rust consumers and a Python wheel path for existing Python/Textual users.
- **API stability for Python users**: Preserve the existing import shape (`tt3de.tt3de`, `materials`, `toglyphmethod`) unless a separate migration document explicitly changes it.
- **Documentation**: Update low-level docs so readers can distinguish Rust engine concepts from Python wrapper classes.
- **Tests and CI**: Verify both build modes: pure Rust without Python bindings, and Python bindings through maturin/pytest.

## Non-goals

- Rewriting the renderer, rasterizer, material system, or TTSL semantics.
- Changing the public Python high-level scene graph API in the same step.
- Replacing PyO3 with another FFI technology.
- Creating C ABI, WASM, or Node bindings as part of this evolution. The split should make those easier later, not implement them now.
- Renaming every Rust type for aesthetics. Rename only when required to remove misleading `Py` suffixes from native concepts or to clarify wrapper boundaries.
- Guaranteeing zero-copy Python interop everywhere. Clean layering is the first goal; performance-specific wrapper optimizations can follow.

## User-visible functionality

- Rust users can depend on the engine crate and use core buffers/pipeline functions without enabling or linking PyO3.
- Python users continue installing and importing tt3de through the existing package flow. Runtime behavior should remain unchanged for demos and applications.
- Maintainers get a clearer release story: publish/test the Rust core independently, and build Python wheels as a wrapper distribution.
- This is intended to be additive and compatibility-preserving. Any Python API break should be treated as a separate accepted decision with migration notes.

## Technical approach

### Baseline (current architecture)

- `Cargo.toml` declares a single `tt3de` package with PyO3 as a dependency and features `python-binding` and `extension-module`.
- `src/lib.rs` exports core modules and also defines the `#[pymodule] fn tt3de(...)` registration function.
- Native code and PyO3 code are partially separated in some areas (`vertex_buffer.rs` / `vertex_buffer_py.rs`, `materials.rs` / `materials_py.rs`) but mixed in others (`geombuffer/mod.rs`, `drawbuffer/mod.rs`, `texturebuffer/mod.rs`, `primitivbuffer/mod.rs`, `raster/mod.rs`, `primitiv_building/mod.rs`).
- Python conversion helpers in `src/utils/mod.rs` convert Python/pyglm values to Rust math types. Those helpers are useful for the wrapper but should not be required by the core engine.
- The Sphinx docs describe Python-first usage while the low-level page documents engine buffers without yet making the binding/core distinction explicit.

### Proposed change

1. **Inventory and boundaries**
   - Create a short map of native modules vs PyO3 wrapper modules.
   - Treat any module importing `pyo3` as binding-layer code unless it is only the Python module registration file.
   - Name the target native surface explicitly: buffer structs, material enums, raster functions, primitive builders, TTSL VM, texture/glyph methods, and math types.
2. **Move wrappers out of mixed modules**
   - For each mixed module, keep native structs and algorithms in neutral files (`mod.rs`, `*.rs`) and move `#[pyclass]`, `#[pymethods]`, `#[pyfunction]`, Python dict/list conversion, and pyglm conversion glue into `*_py.rs` files.
   - Re-export wrapper types only under `#[cfg(feature = "python-binding")]`.
   - Keep wrapper names stable (`GeometryBufferPy`, `DrawingBufferPy`, etc.) even if native names are cleaned up.
3. **Feature-gate PyO3 correctly**
   - Change `pyo3` to an optional dependency tied to the `python-binding` feature.
   - Gate `use pyo3::...`, `#[pymodule]`, wrapper modules, and Python-only utilities with `#[cfg(feature = "python-binding")]`.
   - Ensure `cargo check --no-default-features --all-targets` succeeds without compiling PyO3.
4. **Decide package shape**
   - **Minimum viable shape**: one crate, default features keep Python binding for current maturin behavior, pure Rust consumers disable default features.
   - **Preferred future shape if churn is acceptable**: Cargo workspace with a core crate (for example `tt3de-core`) and a Python extension crate/package that depends on it.
   - Keep this decision explicit after the first separation pass, based on how invasive the module split becomes.
5. **Docs and examples**
   - Update `source/low_level_api.rst` to mark which APIs are Rust-core concepts and which names are Python wrapper classes.
   - Add a small Rust example or test showing a pure Rust buffer/raster/material path without Python.
   - Keep Python docs focused on day-to-day Textual usage and link to the Rust-core section for advanced embedding.

### Future / optional phases

- Publish a separate Rust crate name if desired (`tt3de-core` or similar), with the Python wheel depending on it internally.
- Add non-Python bindings after the core boundary is stable.
- Introduce a stable facade module (`tt3de::engine` or `tt3de_core::*`) that hides internal file layout from downstream Rust users.
- Add `no_std` or reduced-dependency experiments only if a real target needs them; the current engine can remain `std`.

### Alternatives considered

- **Do nothing** — Lowest short-term cost, but keeps pure Rust distribution and API clarity blocked.
- **Full workspace split immediately** — Clean final architecture, but high risk because PyO3 code is currently spread across modules.
- **Feature-gate current mixed files only** — Fastest compile fix, but leaves architecture confusing and likely creates fragile `cfg` tangles.
- **Make Python wrappers generated** — Potentially elegant later, but premature before the native/wrapper boundary is explicit.

### Affected subsystems

- Rust crate layout and module exports.
- PyO3 wrapper classes/functions and `#[pymodule]` registration.
- Cargo features and maturin packaging configuration.
- Rust tests, Python tests, and CI build matrix.
- Low-level documentation and possible Rust examples.

## Usability and documentation

- Python users should not need to learn the split unless they read low-level docs or packaging notes.
- Rust users should have an obvious starting point, ideally a short example that creates the relevant buffers and runs part of the pipeline without Python.
- Documentation should use consistent naming:
  - **Rust core** for native structs/functions and rendering pipeline concepts.
  - **Python wrapper** for `*Py` classes, pyglm conversion, and `tt3de.tt3de` module registration.
- Update `source/low_level_api.rst`, `source/index.rst`, and possibly `README.md` with one canonical explanation rather than scattering packaging details everywhere.

## Testability

- Add or update Rust tests that compile and exercise core modules with `--no-default-features`.
- Run `cargo check --all-targets` for the default developer configuration.
- Run `cargo check --no-default-features --all-targets` to prove PyO3 is not required by the engine core.
- Run `uv run maturin develop` and `uv run pytest` for the Python wrapper path.
- Add at least one smoke test or example that imports the Python module and constructs representative wrapper classes after the split.
- Use `rg "pyo3|pyclass|pymethods|pyfunction|pymodule" src` as a lightweight review gate: expected hits should be in binding modules or registration code only.

## Complexity and scope

- **Estimated size**: Large if taken to full workspace split; Medium for the first safe separation pass.
- **Risk hotspots**:
  - Python import compatibility and submodule registration (`materials`, `toglyphmethod`).
  - PyO3 feature-gating mistakes that break maturin wheels or Rust-only builds.
  - Accidental public Rust API churn while moving files.
  - Python conversion helpers that currently live near native logic and may need cleaner adapter types.
- **Incremental shipping path**:
  1. Document and commit the target architecture.
  2. Move one subsystem at a time to native + `*_py.rs` layout.
  3. Make PyO3 optional and prove `--no-default-features` builds.
  4. Decide whether the one-crate feature model is enough or a workspace split is justified.
- **Rollback story**: Each subsystem move can be reverted independently if wrapper registration or tests fail. The final optional-dependency change should land only after all mixed imports are removed or gated.

## A priori performance analysis

- The restructuring should not change rasterization, shading, clipping, or buffer algorithms, so runtime frame performance should be neutral.
- Pure Rust builds may compile faster and link fewer dependencies when PyO3 is disabled.
- Python wrapper calls should keep the same overhead unless conversion code is accidentally moved into hotter loops. Keep conversion at API boundaries, not inside per-pixel/per-fragment loops.
- Likely cost ranking for implementation options:
  1. Move PyO3 wrappers into sibling `*_py.rs` files within the existing crate.
  2. Make PyO3 optional and gate wrapper exports.
  3. Introduce a public Rust facade module.
  4. Split into a Cargo workspace with a core crate and wrapper crate.
- Validate later with build timings, `cargo check --no-default-features`, default `cargo test`, Python demo smoke tests, and any existing rendering benchmarks.

## Risks and open questions

- Should the final published Rust crate be named `tt3de`, `tt3de-core`, or something else?
- Should default Cargo features keep `python-binding` enabled for current developer convenience, or should pure Rust become the default and maturin opt into Python explicitly?
- Which current `*Py` types are wrappers around truly native objects, and which are Python-only convenience APIs that should not be mirrored in Rust?
- How much Rust API stability is promised immediately after the split? A clean boundary may expose design issues that deserve another evolution before a stable Rust API is advertised.
- Maturin packaging may need careful configuration if the crate type or workspace layout changes.

## Decision record

- **Resolution**: Open. Initial direction is to separate native Rust engine code from PyO3 wrappers incrementally, preserving Python compatibility while enabling pure Rust builds.

## References

- `Cargo.toml` — crate type, PyO3 dependency, and feature declarations.
- `src/lib.rs` — current module exports and Python module registration.
- `source/index.rst` — project scope: CPU-only software 3D engine for terminal/Textual applications.
- `source/high_level_api.rst` — current Python-facing user workflow.
- `source/low_level_api.rst` — buffer-level rendering concepts that should map cleanly to the Rust core.
