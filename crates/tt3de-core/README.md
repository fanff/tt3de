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

Cranelift compiles the post-SSA CFG (`compile_ttsl` / `compile_ttsl_json`) to
native code. `ShaderMaterial` executes that compiled function each shaded cell.

## TTSL execution benchmark

`benches/ttsl/` times the Cranelift path on demo shaders under `demos/`. Arms
lower the SSA snapshot taken after `PassSSARenamer` (constants as immediates,
values in SSA, loads only for seeded inputs).

```bash
cargo bench -p tt3de-core --bench all -- ttsl
```

Each shader reports `jit` (dispatch only) and `jit_cell` (the seed register
restore `ShaderMaterial` performs per pixel, plus dispatch). A separate
`ttsl_compile` group times `compile_ttsl_json`, since compilation is per
material while execution is per cell.

Criterion prints one noisy block per arm. After a run, print a table and
gnuplot bar chart from the saved JSON (gnuplot must be on `PATH`):

```bash
uv run --no-sync python scripts/ttsl_criterion_report.py
```

That writes `target/criterion/ttsl_exec_times.svg`. Criterion's own HTML
(violin plots per shader) is `target/criterion/report/index.html`. To make
Criterion use gnuplot instead of plotters for those pages:

```bash
cargo bench -p tt3de-core --bench all -- ttsl --plotting-backend gnuplot
```

The IR path lowers the SSA ops those demos actually emit
(`JitError::UnsupportedIr` otherwise).

Fixtures are generated, not handwritten. Regenerate them after editing a demo
shader or the TTSL compiler:

```bash
make gen-ttsl-bench-fixtures
```

Publication is intentionally blocked until the repository declares a license.
