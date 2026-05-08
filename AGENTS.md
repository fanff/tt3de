# Agent Guidelines for tt3de

## Build

This is a mixed Rust/Python project using [maturin](https://www.maturin.rs/).

- **Compile locally**: `uv run maturin develop` (dev profile) or `uv run maturin develop --profile release`
- **Rust check (all targets)**: `cargo check --all-targets` — use this to surface all warnings, including from tests and benchmarks.
- **Rust tests**: `cargo test`
- **Python tests**: `uv run pytest`
- **Regenerate TTSL opcodes**: `uv run tt3de-gen-opcodes` — this regenerates `src/ttsl/opcodes.rs` (auto-formatted with `rustfmt`), `python/tt3de/ttsl/ttisa/ttisa_opcodes.py`, and `source/opcode_reference.md`. Run it after any change to `python/tt3de/ttsl/ttisa/low_level_def.py`.

## Platform Notes

- On Windows/PowerShell, redirect cargo stderr with: `cmd /c "cargo check --all-targets 2> output.txt"` (PowerShell `2>&1` piping mangles cargo output).

## Documentation

- The `source/` folder is a [Sphinx](https://www.sphinx-doc.org/) documentation project. Generated docs (e.g. `source/opcode_reference.md`) are written there so Sphinx can include them in the built site.

- **Screenshots tracked in Sphinx static assets**: the triptych used in the docs lives under `source/_static/screenshots/`. After changing [`scripts/screenshot_apps/triple_panel.py`](scripts/screenshot_apps/triple_panel.py) or dependencies it renders, regenerate from the repository root:

  ```bash
  uv run tt3de-regen-doc-screenshot
  ```

  This writes `triple_panel.svg` under `source/_static/screenshots/`. Sphinx and the README embed that SVG.

  This is the canonical command. It invokes [`python/tt3de/dev_regen_doc_screenshot.py`](python/tt3de/dev_regen_doc_screenshot.py) which calls `scripts/dev_tt3de_screenshot.py` with the correct `--width`, `--height`, and output path.

  Other shortcuts with the same effect: **`make regen-doc-screenshot`**, **`scripts/regen_doc_screenshot.sh`**, **`scripts/regen_doc_screenshot.ps1`**.

  GitHub Actions documentation workflow regenerates these after `maturin develop`, before **`sphinx-build`**. Commit updated screenshots when you touch the triptych so local **`sphinx-build`** stays accurate offline too.

## Dependencies

- **Runtime (`[project] dependencies`)**: keep absolutely minimal — every addition here is pulled in by every user. Only add a package when there is no reasonable way to avoid it.
- **Dev (`[dependency-groups] dev`)**: adding tooling, linters, doc-build helpers, and test utilities here is fine. Use `uv add --dev <pkg>` (never manual edits to the list).
- When proposing a new runtime dependency, justify the need and check whether an existing dependency already covers the use case.

## Conventions

- Keep changes scoped; avoid unrelated refactors in the same edit.
- Run `cargo check --all-targets` after Rust edits to verify zero warnings.
- Run `uv run pytest` after changes that touch Python bindings.
