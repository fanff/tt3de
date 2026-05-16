# Evolution: Engine profiling benchmark suite (local / optional CI)

```yaml
id: evol-engine-profiling-benchmarks
created: 2026-05-16
authors: []
supersedes: []
superseded-by: ""
related:
  - scripts/bench_material.sh
  - scripts/dev_material_bench_report.py
  - tests/benchs/r_code/test_bench_r_pix_shader.py
  - tests/benchs/r_code/conftest.py
  - tests/benchs/r_code/test_bench_triangle_raster.py
  - tests/benchs/r_code/test_bench_to_textual.py
  - tests/benchs/ttsl/test_bench_ttsl.py
  - .github/workflows/fast-checks.yml
  - AGENTS.md
```

## Summary

Grow a **small, repeatable set of performance benchmarks** for tt3de’s CPU rasterization and Python/Rust boundaries, using the same ergonomics as today’s **material shading** path: `pytest-benchmark` tests, optional **`--benchmark-json`** export, and a **terminal-friendly Rich summary** (narrow tables, sorted means) for humans comparing runs. **Default CI** stays fast via a **`slow_benchmark` pytest marker**: the fast job runs `pytest -m "not slow_benchmark"`; heavy benchmarks are tagged and run locally (or in an optional manual/scheduled workflow), not on every PR.

## Motivation and context

- **Current behavior** — Several benchmarks already live under `tests/benchs/`:
  - **Material / per-pixel path**: `tests/benchs/r_code/test_bench_r_pix_shader.py` (`test_bench_material_apply`), with compact pytest table settings in `tests/benchs/r_code/conftest.py`.
  - **Triangle raster**: `test_bench_triangle_raster.py` (multiple sizes and passes).
  - **Textual integration**: `test_bench_to_textual.py`.
  - **TTSL VM**: `tests/benchs/ttsl/test_bench_ttsl.py` (`ttsl_run` group).
  The script `scripts/bench_material.sh` runs one focused pytest node with `--benchmark-only`, writes JSON under `benchmarks/`, and pipes it through `scripts/dev_material_bench_report.py` for a **readable KPI layout** (~100-column terminals).

- **Problem** — There is **one polished “bench story”** (material) with a dedicated shell entry point and Rich post-processing. Other hotspots (raster, end-to-end frame, compile vs execute, buffer churn) are less uniformly documented and lack the same **one-command + comparable table** workflow. Separately, **`.github/workflows/fast-checks.yml`** runs `uv run pytest` with **no benchmark-specific flags**, so the full tree including `tests/benchs/` is collected whenever those paths match default discovery—benchmarks therefore participate in **standard CI** today unless individual tests are very fast or externally skipped.

- **Fit with tt3de** — The engine is **CPU-only** and targets **small scenes** (`source/index.rst`). Benchmarks should stress **representative** sizes (several canvas widths, modest triangle counts) and label units clearly (per batch vs per frame), not pretend to be GPU-style megascene tests.

- **Reasoning** — Reuse **pytest-benchmark** (already in dev dependencies) and the **JSON → Rich report** pattern rather than inventing a second timing harness. Keep **Rust `cargo bench`** / Criterion as a separate axis where micro-Rust slices need nanosecond stability; this evolution focuses on **Python-visible** and **mixed Rust/Python** paths.

## Goals

- **Parity scripts** — Add `scripts/bench_*.sh` (or cross-platform `pwsh` companions where the repo already documents Windows flows) for the **highest-value** engine slices, mirroring `bench_material.sh`: `uv run pytest … --benchmark-only`, JSON under `benchmarks/`, then a report command.
- **Report reuse** — Either **generalize** `dev_material_bench_report.py` to accept benchmark group names / titles, or add **small sibling scripts** per suite that share table/bar helpers—whichever keeps diffs readable.
- **Coverage map** — Document (in `AGENTS.md` and/or `source/` testing notes) which script measures **what** (material apply, opaque raster, transparent pass, full raster+material loop if feasible, TTSL compile vs `ttsl_run`, Textual widget tick).
- **CI policy** — Register a **`slow_benchmark`** marker in `pyproject.toml` (`[tool.pytest.ini_options]`). Tag every heavy `pytest-benchmark` test (or module) with `@pytest.mark.slow_benchmark`. **Fast CI** (`fast-checks.yml`): `uv run pytest -m "not slow_benchmark"`. **Local / optional CI**: full suite with `pytest` (no marker filter) or `pytest -m slow_benchmark --benchmark-only` for perf-only runs. Document both commands in `AGENTS.md`. Optional second workflow job or `workflow_dispatch` can run the marked suite with JSON artifacts.
- **Stable knobs** — Where threading or pool sizes matter (as in material parallel passes), keep **explicit parametrization** and stable `FRAME_LOOPS` / warmup commentary so results are comparable across machines (still **hypotheses**, not release gates).

## Non-goals

- **Hard SLA gates** on wall time in default CI (flaky across runners).
- **Replacing** Rust-native microbenches for pure-Rust helpers where Criterion is already the right tool.
- **Distributed** or cloud perf lab; **profiling-as-a-service** is out of scope (local + optional CI artifact is enough).
- **Rewriting** all demos as benchmarks—prefer **minimal synthetic buffers** like existing bench tests.

## User-visible functionality

- **Maintainers and contributors** — One command per benchmark family with **human-readable tables** (and optional JSON for spreadsheets or historical tracking).
- **Library consumers** — **No public API change** required for the benchmarking slice; any new **optional** env vars or markers are contributor-facing only unless the team later exposes a documented `python -m tt3de.bench` entry (defer unless needed).
- **CI** — Default pipeline remains **green without** long benchmark phases; documented command to run the full perf suite before releases or when touching hot paths.

## Technical approach

### Baseline (current architecture)

| Piece | Role today |
|-------|------------|
| `pytest-benchmark` | Drives timed loops; dev dep in `pyproject.toml`. |
| `tests/benchs/r_code/conftest.py` | Tightens default benchmark columns (`min`, `max`, `mean`, `median`, `ops`) and sort for that subtree. |
| `scripts/bench_material.sh` | End-to-end material bench + JSON + Rich. |
| `scripts/dev_material_bench_report.py` | Parses pytest-benchmark JSON, prints Rich tables/panels. |
| CI | `uv run pytest` in `fast-checks.yml` with no benchmark exclusion. |

### Proposed change

1. **Inventory** — List each existing `tests/benchs/**` node and classify: *quick smoke* vs *heavy* (large `parametrize` grids, big buffers). Align naming: `@pytest.mark.benchmark` groups already exist (`material_shading`, `triangle_raster`, `ttsl_run`, etc.).
2. **CI split** — Register **`slow_benchmark`** in pytest config; apply `@pytest.mark.slow_benchmark` to heavy bench tests after inventory. Update **`fast-checks.yml`** to `uv run pytest -m "not slow_benchmark"`. Bench shell scripts continue to target specific nodes with `--benchmark-only` (unaffected by the CI filter). Optionally add one **unmarked** cheap smoke under `tests/benchs/` if the team wants a minimal perf path exercised on every PR.
3. **Scripts + reports** — For 2–4 additional hotspots, add shell entry points and either extend the Rich reporter with **pluggable group filters** or duplicate the minimal JSON parsing with shared helpers in `scripts/` (avoid copy-paste drift if the JSON schema is shared).
4. **Optional full-suite runner** — Single `scripts/bench_all.sh` that invokes the per-suite scripts sequentially and writes timestamped JSON files (optional zip of `benchmarks/` for upload in manual CI).

### Future / optional phases

- **Criterion / `cargo bench`** cross-links in the same doc table where a hotspot is Rust-dominated with little Python.
- **`pyinstrument`** (already a dev dependency)—optional one-pager on how to attach to a bench script for **flame-oriented** investigation after a regression is spotted.
- **Historical tracking** — pytest-benchmark `--benchmark-autosave` / compare mode; document but do not mandate storage.

### Alternatives considered

- **Dedicated Rust harness only** — Rejected as primary: misses PyO3 and Textual integration costs.
- **Always-on CI benchmarks** — Rejected: noisy and slow on shared runners.
- **`--ignore=tests/benchs/` on CI** — Rejected: drops the whole subtree and blocks a future **cheap smoke** test in that folder. **Chosen:** `slow_benchmark` marker + `pytest -m "not slow_benchmark"` on the fast job.
- **Moving benches outside `tests/`** — Possible, but breaks discoverability; not needed with markers.

### Affected subsystems

Python tests, `scripts/`, CI YAML, contributor docs (`AGENTS.md`). Rust code only if new `#[bench]` or exposed C API helpers are added (not required for phase 1).

## Usability and documentation

- **`AGENTS.md` Testing section** — Bullet: “Performance: run `scripts/bench_*.sh` locally; CI runs `pytest -m \"not slow_benchmark\"`.”
- **`source/`** — Short cross-link from developer or testing narrative if one exists; otherwise keep scope in `AGENTS.md` to avoid duplicating Sphinx without need.
- **README** — Optional single line pointing to `bench_material.sh` siblings once they exist.

## Testability

- Bench tests remain **non-asserting on absolute time**; they assert **correctness fixtures** where applicable (existing pattern: build buffers, run function under `benchmark`).
- **Optional cheap smoke** — A single fast test under `tests/benchs/` **without** `slow_benchmark` can stay in default CI (correctness or one timing sample); all heavy parametrized grids get the marker.
- **Regression workflow**: contributor runs full suite locally, attaches JSON or screenshot of Rich output to PR when claiming perf wins.

## Complexity and scope

- **Size: M** — Touches CI, multiple scripts, and possibly refactors report code.
- **Risk hotspots** — Accidentally tagging non-bench tests with `slow_benchmark`, or forgetting the marker on new heavy benches; **verify collection** with `pytest --collect-only -m "not slow_benchmark"` in CI or a dedicated check step.
- **Incremental ship** — (1) CI exclusion + docs, (2) one new bench script + report generalization, (3) remaining suites.

## A priori performance analysis

- **Hot paths** — Per-pixel material (`apply_material_*`), raster passes (`raster_all_py`), TTSL bytecode execution (`ttsl_run`), buffer clears/resizes, Textual render hooks.
- **Expectations** — Parallel material paths depend on core count; document **machine metadata** line (already in Rich report pattern) and prefer **relative** comparisons (serial vs parallel, before vs after patch) over absolute ms claims.
- **Validation** — After changes: run the same script twice, compare JSON or Rich side-by-side; use smaller `SIZES` grids for quick iteration.

## Risks and open questions

- **CI collection drift** — If new heavy bench tests land without `slow_benchmark`, they run on every PR and **slow CI**; code review checklist: “heavy benchmarks marked `slow_benchmark`?”
- **Windows parity** — Bash scripts are fine if documented with `bash scripts/...` on Windows; add `.ps1` wrappers only if the team wants first-class PowerShell without Git Bash.
- **Open question (minor)** — Whether to add one **unmarked** cheap smoke under `tests/benchs/` for CI; default is **no** until a concrete test is identified.

## Decision record

- **CI exclusion (2026-05-16)** — Use pytest marker **`slow_benchmark`** on heavy benchmark tests; **fast CI** runs `pytest -m "not slow_benchmark"`. Reject `--ignore=tests/benchs/` so the folder can host an optional cheap smoke later.
- **Still open when closing** — Whether the Rich reporter was generalized or forked, and which `scripts/bench_*.sh` entry points are canonical beyond material.

## References

- `scripts/bench_material.sh`, `scripts/dev_material_bench_report.py`
- `tests/benchs/` tree and `tests/benchs/r_code/conftest.py`
- `.github/workflows/fast-checks.yml`
- `source/index.rst` (engine scope)
- [`AGENTS.md`](../../AGENTS.md) (build/test commands)
