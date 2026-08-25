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

Publication is intentionally blocked until the repository declares a license.
