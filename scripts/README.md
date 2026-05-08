# Development utilities

Manual, runnable helpers for local development. They stay in this repo under `scripts/`; they are **not** packaged into `pip install tt3de` (only [`python/tt3de/`](../python/tt3de/) is shipped via maturin, and [`pyproject.toml`](../pyproject.toml) should not register these as `[project.scripts]`).

## `dev_tt3de_screenshot.py`

Headless SVG snapshot using Textual’s **`run_test`** / **`export_screenshot`**.

**Default behavior:** a **single SVG** that shows **three** TT3DE-style panels in one terminal: minimal red triangle | multi RGB triangles | `Header` plus red triangle (`screenshot_apps.triple_panel:TriplePanelDemoApp`). Wider terminal by default (`--width` 132) so each column has room.

```text
uv run python scripts/dev_tt3de_screenshot.py -o artifacts/triptych.svg --height 30
```

Committed SVG shown in Sphinx lives at [`source/_static/screenshots/triple_panel.svg`](../source/_static/screenshots/triple_panel.svg); refresh whenever you edit `triple_panel` or related widgets.

**Recommended shortcuts** (skip `uv sync` / maturin reinstall churn):

```text
make regen-doc-screenshot
```

```powershell
powershell -ExecutionPolicy Bypass -File scripts/regen_doc_screenshot.ps1
```

```bash
bash scripts/regen_doc_screenshot.sh
```

Equivalent one-liner (repo root):

```text
uv run --no-sync python scripts/dev_tt3de_screenshot.py ^
  -o source/_static/screenshots/triple_panel.svg --width 132 --height 28
```

`uv run tt3de-regen-doc-screenshot` runs the same job but **`uv run` may sync/rebuild the editable package first** because the command is wired through `[project.scripts]`.

### Packaged examples (`screenshot_apps/`)

Individual apps (use with `--app` when you want **one** scene per run):

| `--app` | Description |
|---------|-------------|
| `screenshot_apps.triple_panel:TriplePanelDemoApp` | **Default** — all three demos in one screenshot |
| `screenshot_apps.red_triangle:RedTriangleDemoApp` | Single red triangle only |
| `screenshot_apps.multi_triangle:MultiTriangleDemoApp` | Three RGB-flat triangles only |
| `screenshot_apps.with_header:RedTriangleHeaderDemoApp` | Red triangle + `Header` only |

### Choosing any App: `--app`

Format: **`LEFT:CLASS`** (`rpartition(":")` — safe for absolute Windows paths to `.py` files).

1. **Dotted module:** `screenshot_apps.red_triangle:RedTriangleDemoApp`
   The directory [`scripts/`](.) is placed on `sys.path` automatically so **`screenshot_apps`** imports.

2. **Python file path:** `demos/3d/triangle_test.py:Demo3dView`
   Resolved relative to current working directory after **`--chdir`**. Many demos need **`models/*.bmp`** and repo-root **`--chdir`**.

### `--delay`

Extra wait in seconds after paint stabilization before **`export_screenshot`**.

### Other flags

- **`--title`**: title string passed to `export_screenshot` (default `tt3de_dev_screenshot`).
- **`--width` / `--height`**: synthetic terminal size (`--width` default 132).

### Release artifact check

Build with `uv build`, open the `.whl` as a ZIP, read `*.dist-info/RECORD`: only installable `tt3de` paths should appear (no `scripts/` payload for end users).
