# tt3de-core

`tt3de-core` is the Python-independent Rust rendering core for
[TT3DE](https://github.com/fanff/tt3de). It contains the geometry, raster,
material, texture, buffer, and TTSL runtime modules without PyO3.

Build and test the core from the repository root:

```bash
cargo check -p tt3de-core --all-targets
cargo test -p tt3de-core
```

See [`examples/minimal.rs`](examples/minimal.rs) for a small Rust-only usage
example. Python users should install the `tt3de` Python package instead.

Cranelift is linked so TTSL can later compile bytecode to a native function.
Shaders still execute through the `run_ttsl` interpreter; the current JIT
entry only compiles a dummy function and is not used on the render path.

## TTSL execution benchmark

`benches/ttsl/` times the interpreter against the Cranelift path on bytecode
compiled from the demo shaders under `demos/`:

```bash
cargo bench -p tt3de-core --bench all -- ttsl
```

Each shader reports `interp_vm` (dispatch only), `interp_cell` (the seed
register restore `ShaderMaterial` performs per pixel, plus dispatch), and the
matching JIT arms. A separate `ttsl_compile` group times `compile_ttsl`, since
compilation is per material while execution is per cell.

While `ttsl::jit::LOWERS_BYTECODE` is `false`, `compile_ttsl` emits a dummy
function, so the JIT arm is named `jit_stub_floor` and measures the native call
overhead rather than shader work. Flipping that constant when lowering lands
renames the arm and turns on the interpreter equivalence assertion.

Fixtures are generated, not handwritten. Regenerate them after editing a demo
shader or the TTSL compiler:

```bash
make gen-ttsl-bench-fixtures
```

Publication is intentionally blocked until the repository declares a license.
