# Agent Guidelines for tt3de

## Build

This is a mixed Rust/Python project using [maturin](https://www.maturin.rs/).

- **Compile locally**: `uv run maturin develop` (dev profile) or `uv run maturin develop --profile release`
- **Rust check (all targets)**: `cargo check --all-targets` — use this to surface all warnings, including from tests and benchmarks.
- **Rust tests**: `cargo test`
- **Python tests**: `uv run pytest` — see [Testing](#testing) for `PYTHONPATH` when running pytest directly.
- **Regenerate TTSL opcodes**: `bash scripts/gen_opcodes.sh` or `powershell -ExecutionPolicy Bypass -File scripts/gen_opcodes.ps1` — this regenerates `src/ttsl/opcodes.rs` (auto-formatted with `rustfmt`), `python/tt3de/ttsl/ttisa/ttisa_opcodes.py`, and `source/opcode_reference.md`. Run it after any change to `python/tt3de/ttsl/ttisa/low_level_def.py`. Equivalent: **`make gen-opcodes`** (invokes the shell script; requires `bash` on `PATH`). Development-only helpers under `scripts/` are not shipped in the published wheel.

## Platform Notes

- On Windows/PowerShell, redirect cargo stderr with: `cmd /c "cargo check --all-targets 2> output.txt"` (PowerShell `2>&1` piping mangles cargo output).
- Detect or confirm the operating system before suggesting or running commands. Use PowerShell syntax on Windows and bash/zsh on macOS or Linux; do not assume one shell works everywhere.

## Testing

When running pytest directly (not via a wrapper that already sets paths), set `PYTHONPATH` to the repository root so imports like `tests.*` resolve correctly.

- **Windows (PowerShell)**:

```powershell
$env:PYTHONPATH='.'; uv run pytest <test-path-or-args>
```

- **macOS/Linux (bash/zsh)**:

```bash
PYTHONPATH=. uv run pytest <test-path-or-args>
```

## Documentation

- The `source/` folder is a [Sphinx](https://www.sphinx-doc.org/) documentation project. Generated docs (e.g. `source/opcode_reference.md`) are written there so Sphinx can include them in the built site.

- **reStructuredText pages (`.rst`)**: use **only one top-level heading per page** — the title underlined with `=` (same convention as `high_level_api.rst`). Additional sections must use deeper adornments (`-`, then `^`, and so on). Multiple `===`-style headings split the document into parallel top-level sections and break the table of contents / navigation.

- **Screenshots tracked in Sphinx static assets**: the dual-panel composite used in the docs lives under `source/_static/screenshots/`. After changing [`scripts/screenshot_apps/dual_panel.py`](scripts/screenshot_apps/dual_panel.py) or dependencies it renders, regenerate from the repository root:

 **`make regen-doc-screenshot`**, **`bash scripts/regen_doc_screenshot.sh`**, or **`powershell -ExecutionPolicy Bypass -File scripts/regen_doc_screenshot.ps1`**.

 These invoke [`scripts/dev_tt3de_screenshot.py`](scripts/dev_tt3de_screenshot.py) with `--width 200`, `--height 56`, and write `dual_panel.svg` under `source/_static/screenshots/`. Sphinx and the README embed that SVG.

 Optional: `uv run --no-sync python scripts/dev_regen_doc_screenshot.py` runs the same capture with `COLORTERM` set for truecolor-friendly exports.

 GitHub Actions documentation workflow regenerates these after `maturin develop`, before **`sphinx-build`**. Commit updated screenshots when you touch the dual-panel app so local **`sphinx-build`** stays accurate offline too.

## Dependencies

- **Runtime (`[project] dependencies`)**: keep absolutely minimal — every addition here is pulled in by every user. Only add a package when there is no reasonable way to avoid it.
- **Dev (`[dependency-groups] dev`)**: adding tooling, linters, doc-build helpers, and test utilities here is fine. Use `uv add --dev <pkg>` (never manual edits to the list).
- When proposing a new runtime dependency, justify the need and check whether an existing dependency already covers the use case.

## Conventions

- **Python GLM imports**: use `from pyglm import glm` (not `import glm` or `import pyglm as glm`). For TTSL shader source strings, the compiler injects the same prelude.
- Keep changes scoped; avoid unrelated refactors in the same edit.
- Run `cargo check --all-targets` after Rust edits to verify zero warnings.
- Run `uv run pytest` after changes that touch Python bindings.

## Git workflow

Before starting new feature or chore work, update your local base from `master` (for example: pull latest `master` first, then branch).

- Branch naming should usually follow:
  - `feat/<short-description>`
  - `chore/<short-description>`
  - `evol/<evol-description>`
- Commit messages must follow release-standard Conventional Commits, such as:
  - `feat: <what changed>`
  - `chore: <what changed>`
  - `fix: <what changed>`
  - `docs: <what changed>`
- Keep commit message prefixes consistent so release automation and changelog tooling remain reliable.

### Example command sequence (Windows PowerShell)

```powershell
git checkout master
git pull
git checkout -b feat/<short-description>
git add .
git commit -m "feat: <what changed>"
```
