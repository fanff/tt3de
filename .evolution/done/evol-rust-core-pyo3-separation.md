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

Restructure tt3de as a Cargo workspace with a published, PyO3-free `tt3de-core` crate and a separate, non-published PyO3 extension crate layered on top. The existing pure-Python package remains in `python/tt3de`, the PyPI distribution remains named `tt3de`, and existing imports such as `tt3de.tt3de` remain compatible. The migration is staged by subsystem so native engine logic, Python conversion code, packaging changes, and compatibility verification remain independently reviewable.

## Motivation and context

- **Current behavior** — tt3de is a mixed Rust/Python project built with `maturin`. The docs present the library primarily as a Python/Textual engine, while `source/low_level_api.rst` documents native-style buffers such as Transform, Geometry, Primitive, Texture, Material, and Drawing buffers. The Rust crate currently exposes the engine modules from `src/lib.rs`, but the same crate also defines the Python module and imports PyO3 directly.
- Several Rust modules combine native data structures and Python wrappers in one file. Examples include `src/geombuffer/mod.rs`, `src/drawbuffer/mod.rs`, `src/material/mod.rs`, `src/primitivbuffer/mod.rs`, and `src/texturebuffer/mod.rs`. Other areas already hint at a better split, such as `src/vertexbuffer/vertex_buffer.rs` next to `src/vertexbuffer/vertex_buffer_py.rs` and `src/material/materials.rs` next to `src/material/materials_py.rs`.
- **Problem today** — A Rust user cannot reason about tt3de as a clean engine crate without also inheriting PyO3 concepts, Python conversion utilities, and wrapper naming. This makes distribution, documentation, compile features, and future embedders harder than necessary.
- **Reference comparison** — Many Rust projects expose a small native core crate and separate language bindings (`*-py`, `*-ffi`, `*-wasm`, etc.). That shape keeps the core API stable and testable while letting wrappers adapt to each host language's conventions.
- This fits tt3de's scope because the renderer is already a CPU-only software engine with explicit buffers and deterministic pipeline stages. Those are natural Rust library concepts independent of Textual or Python. Python remains the main app-facing workflow, but it should not be the only viable packaging target.
- **Reasoning** — A big-bang workspace split is risky because PyO3 types currently appear across many modules. An incremental refactor can first move wrappers beside native modules and prove their compatibility, then move already-separated code into the accepted workspace layout.

## Goals

- **Core API separation**: Define a PyO3-free Rust engine surface for buffers, materials, rasterization, primitive building, textures, TTSL execution, and utility math conversions that do not require Python objects.
- **Binding isolation**: Move or keep all PyO3-specific wrappers in clearly named `*_py.rs` files or a dedicated binding crate/module tree. Native modules should not need `pyo3` imports.
- **Physical package separation**: Make `tt3de-core` a workspace member with no PyO3 dependency and put all extension-module code in a second workspace member.
- **Distribution clarity**: Publish `tt3de-core` for downstream Rust consumers while continuing to build the `tt3de` Python wheel from the extension member.
- **API stability for Python users**: Preserve the existing import shape (`tt3de.tt3de`, `materials`, `toglyphmethod`) unless a separate migration document explicitly changes it.
- **Incremental migration**: Preserve native module names and behavior during the move; defer aesthetic Rust API redesign until the boundary is proven.
- **Documentation**: Update low-level docs so readers can distinguish Rust engine concepts from Python wrapper classes.
- **Tests and CI**: Verify both build modes: pure Rust without Python bindings, and Python bindings through maturin/pytest.

## Non-goals

- Rewriting the renderer, rasterizer, material system, or TTSL semantics.
- Changing the public Python high-level scene graph API in the same step.
- Replacing PyO3 with another FFI technology.
- Splitting the pure-Python modules into another repository or PyPI distribution.
- Creating C ABI, WASM, or Node bindings as part of this evolution. The split should make those easier later, not implement them now.
- Renaming every Rust type for aesthetics. Rename only when required to remove misleading `Py` suffixes from native concepts or to clarify wrapper boundaries.
- Declaring the first extracted Rust API permanently stable. The initial release preserves current native concepts and will follow normal semantic-versioning rules while the facade matures.
- Guaranteeing zero-copy Python interop everywhere. Clean layering is the first goal; performance-specific wrapper optimizations can follow.

## User-visible functionality

- Rust users can depend on the `tt3de-core` crate and use core buffers and pipeline functions without enabling or linking PyO3 or requiring a Python interpreter.
- Python users continue installing `tt3de` and importing `tt3de.tt3de`, `tt3de.tt3de.materials`, and `tt3de.tt3de.toglyphmethod`. Runtime behavior remains unchanged for demos and applications.
- Maintainers can test and version the Rust core independently while Python wheels continue bundling the native extension and pure-Python modules.
- This is intended to be additive and compatibility-preserving. Any Python API break should be treated as a separate accepted decision with migration notes.

## Technical approach

### Baseline (current architecture)

- `Cargo.toml` declares a single `tt3de` package with PyO3 as a dependency and features `python-binding` and `extension-module`.
- `src/lib.rs` exports core modules and also defines the `#[pymodule] fn tt3de(...)` registration function.
- Native code and PyO3 code are partially separated in some areas (`vertex_buffer.rs` / `vertex_buffer_py.rs`, `materials.rs` / `materials_py.rs`) but mixed in others (`geombuffer/mod.rs`, `drawbuffer/mod.rs`, `texturebuffer/mod.rs`, `primitivbuffer/mod.rs`, `raster/mod.rs`, `primitiv_building/mod.rs`).
- Python conversion helpers in `src/utils/mod.rs` convert Python/pyglm values to Rust math types. Those helpers are useful for the wrapper but should not be required by the core engine.
- The Sphinx docs describe Python-first usage while the low-level page documents engine buffers without yet making the binding/core distinction explicit.

### Target workspace

```text
Cargo.toml                         # workspace and shared package metadata
crates/
  tt3de-core/
    Cargo.toml                     # package tt3de-core; no pyo3 dependency
    src/                           # native buffers, pipeline, materials, TTSL VM
    examples/                      # minimal pure-Rust rendering path
  tt3de-py/
    Cargo.toml                     # publish = false; pyo3 extension
    src/                           # *Py wrappers, converters, module registration
python/tt3de/                      # unchanged pure-Python package
pyproject.toml                    # builds crates/tt3de-py and tt3de.tt3de
```

The Cargo package is named `tt3de-core` and is imported in Rust as
`tt3de_core`. The binding package is named `tt3de-py`, remains an implementation
detail of the Python distribution, and keeps its library/module name compatible
with `tt3de.tt3de`.

### Ownership rules

- `tt3de-core` owns native buffer storage, geometry and primitive construction,
  clipping and rasterization, material evaluation, texture sampling, glyph
  mapping, the TTSL VM, generated Rust opcodes, and Python-independent math
  helpers.
- `tt3de-py` owns every `pyo3` import and macro, all `*Py` classes, Python
  collection and pyglm conversion, Rich/Textual object construction,
  `#[pymodule]` registration, and compatibility submodule registration.
- `python/tt3de` continues to own scene-graph orchestration, Textual widgets,
  asset loading, and the TTSL compiler. It may import the extension, but neither
  Rust workspace member may import or execute pure-Python modules outside an
  explicit binding call.
- Core functions accept native Rust inputs and return native Rust results.
  Wrappers convert once at the call boundary and delegate; conversion must not
  move into per-triangle, per-fragment, or per-cell loops.
- A dependency check is a hard boundary: `tt3de-core` must not depend directly
  or transitively on PyO3.

### Migration plan

1. **Lock compatibility and establish checks**
   - Record the current extension exports and add Python smoke coverage for all
     registered classes, functions, `materials`, and `toglyphmethod`.
   - Add a pure-Rust smoke example around representative buffers and one
     pipeline stage, using current native APIs before moving files.
   - Add CI commands that will become the acceptance gates for both workspace
     members.
2. **Extract thin adapters by subsystem**
   - Split mixed modules into native code and `*_py.rs` adapters in the current
     crate, starting with leaf buffers and ending with orchestration functions:
     geometry, primitive, texture, material, drawing, primitive building, and
     raster.
   - Split `src/utils/mod.rs` into Python-independent math helpers and
     binding-only pyglm/Python/Rich converters. Move `DrawingBufferPy` Textual
     `Segment` construction to the binding side.
   - Keep `GeometryBufferPy`, `DrawingBufferPy`, `TextureBufferPy`,
     `MaterialBufferPy`, `PrimitiveBufferPy`, and function names unchanged.
   - Require the native half of each migrated subsystem to compile without
     `pyo3`; land subsystem moves as separate commits.
3. **Create the workspace boundary**
   - Convert the root `Cargo.toml` into a workspace and move native modules to
     `crates/tt3de-core`.
   - Create `crates/tt3de-py` with a path dependency on `tt3de-core`; move
     wrappers and `src/lib.rs` module registration there.
   - Configure `pyproject.toml` to build the extension member while retaining
     `python-source = "python/"` and the `tt3de.tt3de` import path.
   - Keep `tt3de-py` out of crates.io publication. Configure `tt3de-core` with
     the metadata and crate types needed by normal Rust consumers.
4. **Repair generated and release paths**
   - Point opcode generation at
     `crates/tt3de-core/src/ttsl/opcodes.rs` while retaining the generated
     Python opcode and documentation outputs.
   - Update scripts, benchmarks, docs, release-please configuration, wheel/sdist
     workflows, and screenshot/docs builds for workspace paths.
   - Version the PyPI package and core crate explicitly; a PyPI release may
     consume an internal workspace version before independent crates.io
     publishing is enabled.
5. **Publish and document**
   - Add a Rust-core quick start and clearly label native concepts versus
     `*Py` wrapper names in `source/low_level_api.rst`.
   - Publish `tt3de-core` only after the core-only CI, package metadata, README,
     license contents, and a crates.io dry run pass.
   - Run the complete Python suite and representative demos before declaring
     import compatibility complete.

### Future / optional phases

- Introduce a smaller stable facade once extracted native APIs have real
  downstream use; do not couple the physical split to an API redesign.
- Add non-Python bindings after the core boundary is stable.
- Add `no_std` or reduced-dependency experiments only if a real target needs
  them; the current engine remains `std`.

### Alternatives considered

- **Do nothing** — Lowest short-term cost, but keeps pure Rust distribution and API clarity blocked.
- **One crate with optional PyO3** — Enables a core-only feature combination but
  keeps ownership, publication, and accidental dependency regressions unclear.
- **Move all code directly into a workspace in one change** — Reaches the target
  layout sooner but combines behavioral extraction with packaging risk and
  makes regressions difficult to isolate.
- **Feature-gate current mixed files only** — Fastest compile fix, but leaves
  architecture confusing and creates fragile `cfg` tangles.
- **Make Python wrappers generated** — Potentially elegant later, but premature before the native/wrapper boundary is explicit.

### Affected subsystems

- Cargo workspace layout, crate metadata, and module exports.
- PyO3 wrapper classes/functions and `#[pymodule]` registration.
- Maturin packaging and Python import placement.
- TTSL opcode generation paths.
- Release versioning and crates.io/PyPI publication.
- Rust tests, Python tests, and CI build matrix.
- Low-level documentation and possible Rust examples.

## Usability and documentation

- Python users should not need to learn the split unless they read low-level docs or packaging notes.
- Rust users should have a `tt3de-core` README and example that creates representative buffers and runs part of the pipeline without Python.
- Documentation should use consistent naming:
  - **Rust core** for native structs/functions and rendering pipeline concepts.
  - **Python wrapper** for `*Py` classes, pyglm conversion, and `tt3de.tt3de` module registration.
- Update `source/low_level_api.rst`, `source/index.rst`, and `README.md` with one canonical explanation rather than scattering packaging details everywhere.
- Keep the Python quick start unchanged and add a separate Cargo dependency snippet for Rust consumers.

## Testability

- Run `cargo check -p tt3de-core --all-targets` and `cargo test -p tt3de-core` without a Python interpreter.
- Inspect `cargo tree -p tt3de-core` in CI and fail if `pyo3`, `pyo3-ffi`, or `pyo3-build-config` appears.
- Run `cargo check --workspace --all-targets` and the binding crate's Rust tests with an explicitly selected Python interpreter where required.
- Run `uv run maturin develop` and `uv run pytest` for the Python wrapper path.
- Add an import-contract test that checks the existing top-level functions/classes and the `materials` and `toglyphmethod` submodules.
- Build an sdist and wheel from the repository root and inspect both for the pure-Python sources and `tt3de.tt3de` extension.
- Run opcode regeneration and fail on a dirty diff, proving all three generated outputs still agree.
- Use `rg "pyo3|pyclass|pymethods|pyfunction|pymodule" crates/tt3de-core` as a review gate with zero expected hits.

## Complexity and scope

- **Estimated size**: Large, split into independently reviewable subsystem and packaging changes.
- **Risk hotspots**:
  - Python import compatibility and submodule registration (`materials`, `toglyphmethod`).
  - Wrapper access to native fields that are currently private or implicitly colocated.
  - Maturin workspace configuration that builds a wheel with the wrong extension path.
  - Accidental public Rust API churn while moving files.
  - Python conversion helpers that currently live near native logic and may need cleaner adapter types.
  - TTSL generator paths and release automation silently targeting the old root crate.
- **Dependencies**: Compatibility tests precede extraction; adapter extraction precedes the physical workspace move; workspace validation precedes crates.io publication.
- **Rollback story**: Each subsystem extraction is independently revertible. The workspace conversion lands only after wrappers are thin, and crates.io publication remains disabled until all core/package gates pass. The existing PyPI package name and imports never need a coordinated user migration.

## A priori performance analysis

- The restructuring should not change rasterization, shading, clipping, or buffer algorithms, so runtime frame performance should be neutral.
- Pure Rust builds should compile faster and link fewer dependencies because PyO3 is absent from the core dependency graph.
- Python wrapper calls should keep the same overhead unless conversion code is accidentally moved into hotter loops. Keep conversion at API boundaries, not inside per-pixel/per-fragment loops.
- Likely cost ranking for implementation options:
  1. Thin adapters delegating directly to borrowed native data.
  2. Adapters that copy Python/pyglm collections once per public call.
  3. Any design that serializes native data or crosses the Python boundary inside a hot loop; this is prohibited without separate evidence and approval.
- Compare existing rendering benchmarks and representative demo frame profiles before and after each subsystem extraction. Also track clean `cargo check -p tt3de-core` time and release artifact size as secondary build/distribution metrics.

## Risks and open questions

- Which current `*Py` types are wrappers around truly native objects, and which are Python-only convenience APIs that should not be mirrored in Rust?
- Which native fields need narrow accessor methods so the binding crate can avoid making core internals public?
- Should `tt3de-core` publication begin in the same release as the workspace split or only after one Python release has exercised the new layout? The default is to defer crates.io publication by one release while keeping the crate fully packageable.
- How should release automation relate the independently visible PyPI and Cargo versions? They need not share a version number, but each release must record the exact core version bundled by the wheel.
- Maturin's final `manifest-path` and `module-name` settings must be proven on Linux, macOS, Windows, wheel, and sdist builds rather than inferred from local editable installs.

## Decision record

- **Resolution**: Adopt a Cargo workspace whose end state contains a published, PyO3-free `tt3de-core` crate and a non-published `tt3de-py` extension crate. Keep the PyPI distribution named `tt3de`, retain the pure-Python package under `python/tt3de`, and preserve `tt3de.tt3de` plus its existing submodule imports. Reach that end state incrementally by locking compatibility, extracting thin adapters subsystem by subsystem, then moving the already-separated code across the physical crate boundary. Rust facade redesign and non-Python bindings are follow-ups, not prerequisites.
- **Implementation**: Completed in the workspace split that moved native engine code to `crates/tt3de-core`, moved PyO3 adapters to `crates/tt3de-py`, and updated maturin, CI, release, generation, tests, and documentation paths. Crates.io publication remains deferred until the repository declares a license.

## References

- `Cargo.toml` — crate type, PyO3 dependency, and feature declarations.
- `pyproject.toml` — maturin mixed-project configuration and Python distribution metadata.
- `src/lib.rs` — current module exports and Python module registration.
- `.github/workflows/fast-checks.yml` — current Rust/Python validation split.
- `.github/workflows/pypi.yml` — current wheel and sdist build entry points.
- `source/index.rst` — project scope: CPU-only software 3D engine for terminal/Textual applications.
- `source/high_level_api.rst` — current Python-facing user workflow.
- `source/low_level_api.rst` — buffer-level rendering concepts that should map cleanly to the Rust core.
