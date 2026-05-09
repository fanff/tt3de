# -*- coding: utf-8 -*-
"""Render a compact Rich report from ``pytest-benchmark`` JSON for ``test_bench_material_apply``.

Designed for ~100-column terminals: narrow tables, short headers, small bar charts.

Typical workflow (repository root)::

    ./scripts/bench_material.sh

Manual equivalent::

    mkdir -p benchmarks
    PYTHONPATH=python uv run pytest \\
      tests/benchs/r_code/test_bench_r_pix_shader.py::test_bench_material_apply \\
      --benchmark-only -q --benchmark-json=benchmarks/material_apply.json

    uv run --no-sync python python/tt3de/dev_material_bench_report.py benchmarks/material_apply.json
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text


def _ensure_repo_root() -> None:
    cwd = Path.cwd()
    if not (cwd / "pyproject.toml").is_file():
        raise SystemExit(
            "dev_material_bench_report: run from the tt3de repository root "
            "(expected pyproject.toml)."
        )


def _load_payload(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise SystemExit(f"Benchmark JSON not found: {path}")
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _fmt_ms(seconds: float) -> str:
    ms = seconds * 1000.0
    if ms < 100.0:
        return f"{ms:.2f}"
    if ms < 1000.0:
        return f"{ms:.1f}"
    return f"{ms:.0f}"


def _throughput_bar(seconds: float, fastest_s: float, width: int) -> Text:
    """Horizontal bar: higher throughput (1/t) fills more; fastest in group is full."""
    if seconds <= 0 or fastest_s <= 0:
        return Text("░" * width)
    tp = 1.0 / seconds
    tp_max = 1.0 / fastest_s
    frac = min(1.0, tp / tp_max)
    filled = max(0, min(width, int(round(frac * width))))
    bar = "█" * filled + "░" * (width - filled)
    return Text(bar, style="cyan")


def _pick_machine_line(machine_info: dict[str, Any]) -> str:
    cpu = machine_info.get("cpu") or {}
    brand = cpu.get("brand_raw") or machine_info.get("processor") or "unknown CPU"
    node = machine_info.get("node") or "?"
    pyver = machine_info.get("python_version") or "?"
    sysname = machine_info.get("system") or "?"
    return f"{node} · {brand} · {sysname} · Python {pyver}"


def _collect_rows(payload: dict[str, Any]) -> dict[int, list[dict[str, Any]]]:
    by_n: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for b in payload.get("benchmarks", []):
        name = b.get("name") or ""
        if "test_bench_material_apply" not in name:
            continue
        params = b.get("params") or {}
        stats = b.get("stats") or {}
        if "mean" not in stats:
            continue
        n = int(params["n"])
        mode = str(params["mode"])
        pool_threads = params.get("pool_threads")
        mean_s = float(stats["mean"])
        extra = b.get("extra_info") or {}
        loops = extra.get("frame_loops")
        by_n[n].append(
            {
                "mode": mode,
                "threads": pool_threads,
                "mean_s": mean_s,
                "loops": loops,
            }
        )
    return by_n


def _sort_key(row: dict[str, Any]) -> tuple[int, int]:
    if row["mode"] == "serial":
        return (0, 0)
    t = row["threads"] or 0
    return (1, int(t))


def _build_table_for_n(
    n: int,
    rows: list[dict[str, Any]],
    bar_w: int,
) -> tuple[Table, dict[str, Any]]:
    rows = sorted(rows, key=_sort_key)
    serial_mean = next((r["mean_s"] for r in rows if r["mode"] == "serial"), None)
    if serial_mean is None:
        raise SystemExit(f"Missing serial row for canvas n={n}.")

    fastest_s = min(r["mean_s"] for r in rows)
    loops = next((r["loops"] for r in rows if r["loops"] is not None), None)

    table = Table(
        box=box.SIMPLE_HEAD,
        expand=False,
        show_lines=False,
        pad_edge=False,
    )
    table.add_column("cfg", justify="left", no_wrap=True)
    table.add_column("ms", justify="right", no_wrap=True)
    table.add_column("×ser", justify="right", no_wrap=True)
    table.add_column("η/T", justify="right", no_wrap=True)
    table.add_column("loss", justify="right", no_wrap=True)
    table.add_column("thruput", justify="left", no_wrap=True)

    best_speedup = -1.0
    best_label = ""

    for r in rows:
        mean_s = r["mean_s"]
        mode = r["mode"]
        threads = r["threads"]

        if mode == "serial":
            cfg = "ser"
            speedup = 1.0
            eff_txt = "—"
            loss_txt = "—"
            label = "serial"
        else:
            assert threads is not None
            cfg = f"p{threads}t"
            speedup = serial_mean / mean_s if mean_s > 0 else 0.0
            eta = speedup / float(threads)
            eff_txt = f"{eta:.2f}"
            loss_pct = 100.0 * (1.0 - eta)
            loss_txt = f"{loss_pct:+.0f}%"
            label = cfg
            if speedup > best_speedup:
                best_speedup = speedup
                best_label = cfg

        xser = f"{speedup:.2f}×"
        bar = _throughput_bar(mean_s, fastest_s, bar_w)
        table.add_row(cfg, _fmt_ms(mean_s), xser, eff_txt, loss_txt, bar)

    meta = {
        "loops": loops,
        "best_speedup": best_speedup,
        "best_label": best_label,
        "serial_s": serial_mean,
        "fastest_s": fastest_s,
    }
    return table, meta


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Rich KPI report for test_bench_material_apply benchmark JSON.",
    )
    parser.add_argument(
        "json_path",
        nargs="?",
        default="benchmarks/material_apply.json",
        type=Path,
        help="pytest-benchmark --benchmark-json output (default: benchmarks/material_apply.json)",
    )
    parser.add_argument(
        "--max-width",
        type=int,
        default=100,
        metavar="N",
        help="cap console width for layout (default: 100)",
    )
    args = parser.parse_args()

    _ensure_repo_root()
    payload = _load_payload(args.json_path.resolve())

    term_w = shutil.get_terminal_size(fallback=(args.max_width, 24)).columns
    width = max(72, min(args.max_width, term_w))
    console = Console(width=width, soft_wrap=True)

    by_n = _collect_rows(payload)
    if not by_n:
        raise SystemExit(
            "No test_bench_material_apply rows in JSON. "
            "Regenerate with pytest --benchmark-json=..."
        )

    machine_info = payload.get("machine_info") or {}
    machine_line = _pick_machine_line(machine_info)
    if len(machine_line) > width - 4:
        machine_line = machine_line[: width - 7] + "..."

    console.print(Rule("Material apply · threading KPI", style="bold"))
    console.print(Text(machine_line, style="dim"))
    console.print()

    ns_sorted = sorted(by_n.keys())
    bar_w = max(12, min(22, width - 58))

    for n in ns_sorted:
        table, meta = _build_table_for_n(n, by_n[n], bar_w)
        loops_note = ""
        if meta["loops"] is not None:
            loops_note = f" · {meta['loops']} frame loops / timed batch"
        subtitle = (
            f"Best parallel: [bold]{meta['best_label']}[/bold] "
            f"→ [bold]{meta['best_speedup']:.2f}×[/bold] serial speed "
            f"(wall-clock vs single-threaded path)"
        )
        if meta["best_speedup"] < 1.0:
            subtitle = (
                f"[yellow]Serial wins[/yellow]: best parallel "
                f"[bold]{meta['best_speedup']:.2f}×[/bold] serial speed "
                f"(pool overhead dominates)."
            )

        panel_title = f"n={n}×{n}{loops_note}"
        inner = Table.grid(padding=(0, 0))
        inner.add_row(table)
        inner.add_row(Text.from_markup(subtitle))

        console.print(
            Panel(
                inner,
                title=panel_title,
                border_style="blue",
                width=min(width - 2, width),
                expand=False,
            )
        )
        console.print()

    console.print(Rule(style="dim"))
    gloss = Table.grid(padding=(0, 1))
    gloss.add_row(
        Text("×ser", style="bold"),
        Text("mean_serial / mean_variant (>1 means parallel wins)."),
    )
    gloss.add_row(
        Text("η/T", style="bold"),
        Text("efficiency: speedup ÷ thread count (1.0 = ideal linear scaling)."),
    )
    gloss.add_row(
        Text("loss", style="bold"),
        Text("(1 − η/T)·100%: shortfall vs perfect scaling (0% at ideal)."),
    )
    gloss.add_row(
        Text("thruput", style="bold"),
        Text("bar ∝ 1/mean time; longest bar = fastest config at this canvas size."),
    )
    console.print(Panel(gloss, title="Columns", border_style="dim", expand=False))
    console.print()


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.exit(0)
