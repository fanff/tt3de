# Evolution: Engine profiling benchmark suite (relocated, consolidated scripts)

```yaml
id: evol-engine-profiling-benchmarks
created: 2026-05-16
updated: 2026-05-19
authors: []
supersedes: []
superseded-by: ""
related:
  - scripts/bench_material.sh
  - scripts/bench_to_textual.sh
  - scripts/dev_material_bench_report.py
  - scripts/enrich_benchmark_json.py
  - benchs/
  - benches/
  - .github/workflows/fast-checks.yml
  - AGENTS.md
  - README.md
```

## Summary

Reorganize **existing** engine performance benchmarks so they are **outside the pytest test tree**, invoked only through a **small set of bash scripts** (`scripts/bench_*.sh`), and always end with **human-readable terminal output** (Rich tables, same spirit as `bench_material.sh` + `dev_material_bench_report.py`). Remove PowerShell bench wrappers; document how to run benchmarks in **`AGENTS.md`** and **`README.md`**. **Default CI** (`uv run pytest`) no longer collects or runs long `pytest-benchmark` work—no new benchmark scenarios and no changes to inner timing loops (`FRAME_LOOPS`, parametrization grids, etc.) beyond path and wiring updates.

## Motivation and context

- **Current behavior** — Benchmarks live under `tests/benchs/` and are discovered by normal `uv run pytest` in `.github/workflows/fast-checks.yml`. Two bash entry points exist (`scripts/bench_material.sh`, `scripts/bench_to_textual.sh`); material also has `scripts/bench_material.ps1`. Material benches get a **Rich KPI report**; `bench_to_textual.sh` writes JSON and runs `enrich_benchmark_json.py` but does **not** print a compact summary table. Other modules (`test_bench_triangle_raster.py`, `test_bench_ttsl.py`) are only runnable via manual pytest paths.

- **Problem** — Mixing long-running benchmarks into `tests/` couples perf work to CI and unit-test mental models. Multiple partial scripts and one `.ps1` duplicate the “how do I bench?” story. Raw JSON under `benchmarks/` is not enough for quick local comparisons unless you already know which report script to run.

- **Fit with tt3de** — CPU-only, small-scene engine (`source/index.rst`). Benchmarks stay **representative** of today’s parametrization; this evolution is **packaging and ergonomics**, not new coverage.

- **Reasoning** — **Relocating** benches out of `tests/` is simpler and more reliable than a `slow_benchmark` marker: CI needs no marker discipline, and `pytest` stays a correctness suite. Reuse **pytest-benchmark** + JSON export; consolidate **bash-only** drivers and **shared Rich reporting**. Rust **Criterion** benches under `benches/` remain a separate, documented axis.

## Goals

- **Relocate benchmarks** — Move `tests/benchs/**` to a top-level tree (proposed: `benchs/`, mirroring current layout: `benchs/r_code/`, `benchs/ttsl/`). Update script and doc paths; keep existing test modules and parametrization **unchanged in behavior** (moves and import path fixes only).

- **Bash-only entry points** — Delete `scripts/bench_material.ps1`. Document running benchmarks via `bash scripts/...` from the repository root (Windows: Git Bash / WSL per `AGENTS.md` platform notes). **No new `.ps1` bench scripts.**

- **Few consolidated scripts** — Replace ad-hoc per-module pytest invocations with a **small canonical set** (target **three** suite scripts plus one optional aggregator):

  | Script | Covers (existing modules only) |
  |--------|--------------------------------|
  | `scripts/bench_material.sh` | Material apply (`test_bench_r_pix_shader.py`) |
  | `scripts/bench_r_code.sh` | Triangle raster + Textual export (`test_bench_triangle_raster.py`, `test_bench_to_textual.py`) |
  | `scripts/bench_ttsl.sh` | TTSL VM (`test_bench_ttsl.py`) |
  | `scripts/bench_all.sh` *(optional)* | Runs the three scripts sequentially; timestamped JSON under `benchmarks/` |

  Retire `scripts/bench_to_textual.sh` as a separate public entry point once its suite is covered by `bench_r_code.sh` (or keep as thin alias that calls the consolidated script—implementation choice; **one** documented path per suite in docs).

- **Human-readable output for every suite** — Each `bench_*.sh` must: run `pytest` with `--benchmark-only` and `--benchmark-json=…`, then invoke a **report step** that prints Rich tables (~100-column friendly), matching material’s UX. Refactor `dev_material_bench_report.py` into shared helpers + suite-specific or parameterized reporters; **no suite should end on JSON-only** unless JSON is explicitly secondary (printed path + table above).

- **Contributor docs** — Add a **Benchmarks** subsection to `AGENTS.md` (commands, output location, when to run before perf PRs). Update **`README.md`** to remove `.ps1` references and point to the consolidated bash scripts and `benchs/` layout.

- **CI unchanged in intent** — `fast-checks.yml` continues `uv run pytest` with **no** benchmark collection after relocation. No wall-time gates on runners.

## Non-goals

- **Adding new benchmark scenarios** — No new parametrizations, sizes, shaders, or hotspot coverage beyond what exists today.
- **Deep changes to bench inner loops** — Do not change `FRAME_LOOPS`, `ROUND_LOOPS`, `SIZES`, triangle counts, `PASS_CONFIG`, or the functions under measurement except as required by file moves/import paths.
- **PowerShell bench scripts** — Remove existing `.ps1`; do not replace them.
- **`slow_benchmark` pytest marker** — Superseded by relocation; not part of this evolution.
- **Hard SLA / perf gates in CI** — No timing assertions on shared runners.
- **New Rust Criterion benches** or **pyinstrument** guide — Optional follow-up only.
- **Sphinx `source/` pages** — Unless a single cross-link is trivial; primary docs are `AGENTS.md` + `README.md`.
- **Rewriting demos** as benchmarks.

## User-visible functionality

- **Maintainers** — Run `bash scripts/bench_material.sh`, `bash scripts/bench_r_code.sh`, or `bash scripts/bench_ttsl.sh` from the repo root; see Rich summary in the terminal; optional JSON under `benchmarks/` for history.
- **Library consumers** — No public API changes.
- **CI** — Faster, clearer separation: pytest = tests; `scripts/bench_*.sh` = performance.

## Technical approach

### Baseline (current architecture)

| Piece | Role today |
|-------|------------|
| `tests/benchs/**` | `pytest-benchmark` modules; collected by default CI pytest |
| `tests/benchs/r_code/conftest.py` | Compact benchmark columns when r_code benches collected |
| `scripts/bench_material.sh` | Material bench + JSON + Rich via `dev_material_bench_report.py` |
| `scripts/bench_material.ps1` | Windows duplicate of material script (**to remove**) |
| `scripts/bench_to_textual.sh` | Textual bench + JSON + `enrich_benchmark_json.py` (**no Rich table**) |
| `benches/*.rs` | Criterion microbenches (unchanged) |
| CI | `uv run pytest` collects `tests/benchs/` |

### Proposed change

**Phase 1 — Relocate**

1. Move `tests/benchs/` → `benchs/` (preserve `r_code/`, `ttsl/`, `conftest.py` structure).
2. Add `benchs/conftest.py` if needed for shared pytest-benchmark column defaults (lift from `tests/benchs/r_code/conftest.py` or keep under `benchs/r_code/` only).
3. Ensure scripts set `PYTHONPATH` to include `python/` (and repo root if tests imported from `tests.*` today—adjust to minimal imports: `tt3de` only).
4. Delete empty `tests/benchs/` after move; grep repo for `tests/benchs` (README, skills, evolution links, CHANGELOG) and update.

**Phase 2 — Scripts and reporting**

1. Delete `scripts/bench_material.ps1`.
2. Implement `scripts/bench_r_code.sh` and `scripts/bench_ttsl.sh`; update `bench_material.sh` paths to `benchs/…`.
3. Extract shared JSON → Rich utilities (e.g. `scripts/bench_report_lib.py` or refactor `dev_material_bench_report.py`); add reporters for raster and Textual suites (group by existing `benchmark` group / params: `size`, `pattern`, `mode`, etc.).
4. Merge or alias `bench_to_textual.sh` into `bench_r_code.sh`; document one path.
5. Optional `scripts/bench_all.sh` calling the three suite scripts.

**Phase 3 — Documentation**

1. **`AGENTS.md`** — New bullets under Testing (or dedicated Benchmarks): prerequisite `uv run maturin develop`; table of scripts → what they measure → units (per batch vs per invocation); `benchmarks/` output; note that CI pytest excludes `benchs/`; relative comparisons for PRs, not absolute ms SLAs.
2. **`README.md`** — Replace material-only + `.ps1` section with the three bash commands and pointer to `AGENTS.md` for detail.

### Target layout (after implementation)

```text
benchs/
  r_code/
    conftest.py
    test_bench_r_pix_shader.py
    test_bench_triangle_raster.py
    test_bench_to_textual.py
  ttsl/
    test_bench_ttsl.py
benchmarks/          # JSON artifacts (gitignored or committed per existing policy)
scripts/
  bench_material.sh
  bench_r_code.sh
  bench_ttsl.sh
  bench_all.sh       # optional
  dev_material_bench_report.py  # thin CLI or merged into shared report module
```

### Alternatives considered

| Alternative | Decision |
|-------------|----------|
| `slow_benchmark` marker + `pytest -m "not slow_benchmark"` | **Rejected** — relocation avoids marker drift on every new bench file. |
| `--ignore=tests/benchs` in CI | **Rejected** — benches should not live under `tests/` at all. |
| Keep benchmarks in `tests/` + ignore | **Rejected** — same as above; wrong directory semantics. |
| PowerShell `.ps1` wrappers | **Rejected** — bash-only; Git Bash on Windows. |
| JSON-only output for some suites | **Rejected** — all suite scripts print Rich summary. |
| `python -m tt3de.bench` CLI | **Deferred** — scripts sufficient. |

### Affected subsystems

`benchs/` (new location), `scripts/`, `AGENTS.md`, `README.md`, grep cleanup in `.cursor/skills/` and `.opencode/skills/` if they reference `tests/benchs/` or `.ps1`. **No Rust hot-path changes** unless import paths in bench files require it. CI YAML unchanged except benefiting from faster pytest. `pyproject.toml` unchanged unless a `[tool.pytest.ini_options] testpaths` tweak is needed (default discovery should not include `benchs/`).

## Usability and documentation

- **`AGENTS.md`** — Canonical benchmark commands; maturin develop prerequisite; explain `benchmarks/*.json` + terminal report; Windows: `bash scripts/bench_material.sh`.
- **`README.md`** — Short “Performance benchmarks” subsection listing the three scripts (no `.ps1`).
- **PR workflow** — When claiming perf changes: run relevant `bench_*.sh`, paste Rich output or attach JSON; compare **relative** speedups on the same machine.

## Testability

- Bench modules keep **no absolute timing assertions**; behavior under measurement unchanged.
- **Regression**: after relocation, each `bench_*.sh` exits 0 and prints expected groups; `uv run pytest` does not list `benchs/` nodes (`pytest --collect-only` sanity).
- **Optional**: a one-line CI check that `pytest --collect-only 2>&1 | grep -q benchs` fails (no accidental reintroduction under `tests/`).

## Complexity and scope

- **Size: M** — File moves, script consolidation, report refactor, doc updates; low risk to engine correctness.
- **Risk hotspots** — Stale `tests/benchs` paths in docs/skills; forgotten `.ps1` references; `bench_r_code.sh` grouping wrong pytest nodeids after move.
- **Incremental ship** — (1) relocate + fix material script, (2) r_code + ttsl scripts + Rich for all suites, (3) docs + delete `.ps1` + optional `bench_all.sh`.

## A priori performance analysis

- **Hot paths** (unchanged) — `apply_material_*`, `raster_all_py`, `ttsl_run`, `DrawingBufferPy.to_textual_2`.
- **Expectations** — Numbers should match pre-move runs within noise; document machine line in Rich output for cross-machine humility.
- **Validation** — Run `bench_material.sh` before and after Phase 1; compare JSON means for one `n` and serial mode.

## Risks and open questions

- **Skill/doc drift** — `tt3de-low` and `ttsl-implementation` skills mention `tests/benchs/`; update in the same PR series as the move.
- **`opcode_speedtest.py`** under `tests/benchs/ttsl/` — Confirm whether it is a bench or dev script; move with `benchs/ttsl/` or leave/delete if dead (inventory during Phase 1).
- **Open (minor)** — Whether `bench_all.sh` is worth shipping in v1 or documented as `for s in scripts/bench_*.sh; do bash "$s"; done`.

## Decision record

- **2026-05-19 — Scope refinement (authoritative)**  
  - **In:** bash-only; consolidate to few `scripts/bench_*.sh`; move benches out of `tests/`; human-readable Rich output for every suite; update `AGENTS.md` + `README.md`.  
  - **Out:** new benchmark scenarios; deep inner-loop changes; `.ps1` scripts; `slow_benchmark` marker approach.

- **2026-05-19 — Relocation over markers**  
  Store benchmarks under top-level `benchs/` so default `pytest` excludes them. Reject `slow_benchmark` + `pytest -m "not slow_benchmark"` from the 2026-05-16 draft.

- **2026-05-19 — Script consolidation**  
  Target three suite scripts (`bench_material.sh`, `bench_r_code.sh`, `bench_ttsl.sh`) plus optional `bench_all.sh`. Remove `bench_material.ps1` and standalone `bench_to_textual.sh` as the primary documented path.

- **2026-05-19 — Reporting**  
  Every suite script ends with Rich terminal output; generalize helpers from `dev_material_bench_report.py` rather than leaving JSON-only workflows.

- **Superseded (2026-05-16 draft)** — `slow_benchmark` CI exclusion; adding new `bench_*.sh` for *new* hotspots; PowerShell parity; optional `workflow_dispatch` perf job (remain optional follow-up, not in scope).

## References

- `scripts/bench_material.sh`, `scripts/bench_to_textual.sh`, `scripts/dev_material_bench_report.py`
- `tests/benchs/` (to become `benchs/`)
- `benches/` (Criterion)
- `.github/workflows/fast-checks.yml`
- [`AGENTS.md`](../../AGENTS.md), [`README.md`](../../README.md)
