# Development utilities

Manual, runnable helpers for local development. They stay in this repo under `scripts/`; they are **not** packaged into `pip install tt3de` (only [`python/tt3de/`](../python/tt3de/) is shipped via maturin, and [`pyproject.toml`](../pyproject.toml) should not register these as `[project.scripts]`).

## Opcode regeneration

After edits to [`python/tt3de/ttsl/ttisa/low_level_def.py`](../python/tt3de/ttsl/ttisa/low_level_def.py):

```bash
bash scripts/gen_opcodes.sh
```

```powershell
powershell -ExecutionPolicy Bypass -File scripts/gen_opcodes.ps1
```

Equivalent: **`make gen-opcodes`** (runs `bash scripts/gen_opcodes.sh`).

## `dev_tt3de_screenshot.py`

Headless SVG snapshot using Textual’s **`run_test`** / **`export_screenshot`**.

**Default behavior:** a **single SVG** that shows **two** TT3DE-style panels in one terminal: taxi car model | city block (`screenshot_apps.dual_panel:DualPanelDemoApp`). Default `--width` 200, `--height` 56.

```text
uv run python scripts/dev_tt3de_screenshot.py -o artifacts/dual_panel.svg --height 30
```

Committed SVG shown in Sphinx lives at [`source/_static/screenshots/dual_panel.svg`](../source/_static/screenshots/dual_panel.svg); refresh whenever you edit `dual_panel` or related widgets.

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
  -o source/_static/screenshots/dual_panel.svg --width 200 --height 56
```

Optional: `uv run --no-sync python scripts/dev_regen_doc_screenshot.py` runs the same capture with `COLORTERM` set for truecolor-friendly exports.

### Packaged examples (`screenshot_apps/`)

Custom `TT3DViewStandAlone` scenes should call **`screenshot_apps.canvas_bg.seed_material0_void`** (or equivalently define **material slot 0** as a black / space glyph) before adding visible materials. The engine ties cleared depth samples to **`material_id == 0`**; otherwise the **first** `add_static` (often red **`R`**) floods the canvas.

Individual apps (use with `--app` when you want **one** scene per run):

| `--app` | Description |
|---------|-------------|
| `screenshot_apps.dual_panel:DualPanelDemoApp` | **Default** — two side-by-side columns (taxi + city block) |
| `screenshot_apps.red_triangle:TexturedCubeDemoApp` | Textured cube (OBJ + BMP) |
| `screenshot_apps.multi_triangle:TaxiModelDemoApp` | Taxi car 3D model |
| `screenshot_apps.city_scene:CityBlockDemoApp` | City block, top-down |
| `screenshot_apps.with_header:CubeHeaderDemoApp` | Textured cube + `Header` |

### Choosing any App: `--app`

Format: **`LEFT:CLASS`** (`rpartition(":")` — safe for absolute Windows paths to `.py` files).

1. **Dotted module:** `screenshot_apps.red_triangle:TexturedCubeDemoApp`
   The directory [`scripts/`](.) is placed on `sys.path` automatically so **`screenshot_apps`** imports.

2. **Python file path:** `demos/3d/triangle_test.py:Demo3dView`
   Resolved relative to current working directory after **`--chdir`**. Many demos need **`models/*.bmp`** and repo-root **`--chdir`**.

### `--delay`

Extra wait in seconds after paint stabilization before **`export_screenshot`**.

### Other flags

- **`--title`**: title string passed to `export_screenshot` (default `tt3de_dev_screenshot`).
- **`--width` / `--height`**: synthetic terminal size (defaults **200 × 56** for the dual-panel app).

### Release artifact check

Build with `uv build`, open the `.whl` as a ZIP, read `*.dist-info/RECORD`: only installable `tt3de` paths should appear (no `scripts/` payload for end users).
