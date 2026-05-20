# -*- coding: utf-8 -*-
"""Shared helpers and Rich reporters for pytest-benchmark JSON artifacts."""

from __future__ import annotations

import json
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text


def ensure_repo_root() -> None:
    if not (Path.cwd() / "pyproject.toml").is_file():
        raise SystemExit(
            "bench report: run from the tt3de repository root (expected pyproject.toml)."
        )


def load_payload(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise SystemExit(f"Benchmark JSON not found: {path}")
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def fmt_ms(seconds: float) -> str:
    ms = seconds * 1000.0
    if ms < 100.0:
        return f"{ms:.2f}"
    if ms < 1000.0:
        return f"{ms:.1f}"
    return f"{ms:.0f}"


def throughput_bar(seconds: float, fastest_s: float, width: int) -> Text:
    if seconds <= 0 or fastest_s <= 0:
        return Text("░" * width)
    tp = 1.0 / seconds
    tp_max = 1.0 / fastest_s
    frac = min(1.0, tp / tp_max)
    filled = max(0, min(width, int(round(frac * width))))
    bar = "█" * filled + "░" * (width - filled)
    return Text(bar, style="cyan")


def pick_machine_line(machine_info: dict[str, Any]) -> str:
    cpu = machine_info.get("cpu") or {}
    brand = cpu.get("brand_raw") or machine_info.get("processor") or "unknown CPU"
    node = machine_info.get("node") or "?"
    pyver = machine_info.get("python_version") or "?"
    sysname = machine_info.get("system") or "?"
    return f"{node} · {brand} · {sysname} · Python {pyver}"


def make_console(max_width: int = 100) -> Console:
    term_w = shutil.get_terminal_size(fallback=(max_width, 24)).columns
    width = max(72, min(max_width, term_w))
    return Console(width=width, soft_wrap=True)


def _mean_s(bench: dict[str, Any]) -> float | None:
    stats = bench.get("stats") or {}
    mean = stats.get("mean")
    return float(mean) if mean is not None else None


def filter_benchmarks(
    payload: dict[str, Any],
    *,
    name_contains: str | None = None,
    group: str | None = None,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for b in payload.get("benchmarks", []):
        if name_contains and name_contains not in (b.get("name") or ""):
            continue
        if group is not None and (b.get("group") or "") != group:
            continue
        if _mean_s(b) is None:
            continue
        out.append(b)
    return out


def render_simple_table(
    console: Console,
    *,
    title: str,
    rows: list[tuple[str, float, str | None]],
    bar_w: int,
    subtitle: str | None = None,
) -> None:
    """Render label / mean_ms rows with throughput bars (fastest = full bar)."""
    if not rows:
        return
    fastest_s = min(mean_s for _, mean_s, _ in rows)
    table = Table(
        box=box.SIMPLE_HEAD,
        expand=False,
        show_lines=False,
        pad_edge=False,
    )
    table.add_column("cfg", justify="left", no_wrap=True)
    table.add_column("ms", justify="right", no_wrap=True)
    table.add_column("note", justify="left", no_wrap=True)
    table.add_column("thruput", justify="left", no_wrap=True)

    for label, mean_s, note in sorted(rows, key=lambda r: r[1]):
        table.add_row(
            label,
            fmt_ms(mean_s),
            note or "",
            throughput_bar(mean_s, fastest_s, bar_w),
        )

    inner = Table.grid(padding=(0, 0))
    inner.add_row(table)
    if subtitle:
        inner.add_row(Text.from_markup(subtitle))
    console.print(
        Panel(
            inner,
            title=title,
            border_style="blue",
            expand=False,
        )
    )
    console.print()


def _collect_material_rows(payload: dict[str, Any]) -> dict[int, list[dict[str, Any]]]:
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


def _sort_material_key(row: dict[str, Any]) -> tuple[int, int]:
    if row["mode"] == "serial":
        return (0, 0)
    t = row["threads"] or 0
    return (1, int(t))


def _build_material_table_for_n(
    n: int,
    rows: list[dict[str, Any]],
    bar_w: int,
) -> tuple[Table, dict[str, Any]]:
    rows = sorted(rows, key=_sort_material_key)
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
        else:
            assert threads is not None
            cfg = f"p{threads}t"
            speedup = serial_mean / mean_s if mean_s > 0 else 0.0
            eta = speedup / float(threads)
            eff_txt = f"{eta:.2f}"
            loss_pct = 100.0 * (1.0 - eta)
            loss_txt = f"{loss_pct:+.0f}%"
            if speedup > best_speedup:
                best_speedup = speedup
                best_label = cfg

        xser = f"{speedup:.2f}×"
        bar = throughput_bar(mean_s, fastest_s, bar_w)
        table.add_row(cfg, fmt_ms(mean_s), xser, eff_txt, loss_txt, bar)

    meta = {
        "loops": loops,
        "best_speedup": best_speedup,
        "best_label": best_label,
    }
    return table, meta


def report_material(payload: dict[str, Any], *, max_width: int = 100) -> None:
    by_n = _collect_material_rows(payload)
    if not by_n:
        raise SystemExit(
            "No test_bench_material_apply rows in JSON. "
            "Regenerate with pytest --benchmark-json=..."
        )

    console = make_console(max_width)
    width = console.width
    machine_info = payload.get("machine_info") or {}
    machine_line = pick_machine_line(machine_info)
    if len(machine_line) > width - 4:
        machine_line = machine_line[: width - 7] + "..."

    console.print(Rule("Material apply · threading KPI", style="bold"))
    console.print(Text(machine_line, style="dim"))
    console.print()

    bar_w = max(12, min(22, width - 58))
    for n in sorted(by_n.keys()):
        table, meta = _build_material_table_for_n(n, by_n[n], bar_w)
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
            Panel(inner, title=panel_title, border_style="blue", expand=False)
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


def _rows_from_group(
    benches: list[dict[str, Any]],
    label_keys: tuple[str, ...],
    label_fn: Callable[[dict[str, Any]], str] | None = None,
) -> list[tuple[str, float, str | None]]:
    rows: list[tuple[str, float, str | None]] = []
    for b in benches:
        mean_s = _mean_s(b)
        if mean_s is None:
            continue
        params = b.get("params") or {}
        extra = b.get("extra_info") or {}
        if label_fn:
            label = label_fn(params)
        else:
            parts = [str(params.get(k, extra.get(k, "?"))) for k in label_keys]
            label = "/".join(parts)
        note_parts: list[str] = []
        if extra.get("round_loops"):
            note_parts.append(f"{extra['round_loops']} loops/batch")
        if extra.get("bytecode_size"):
            note_parts.append(f"bc {extra['bytecode_size']} B")
        rows.append((label, mean_s, ", ".join(note_parts) or None))
    return rows


def report_r_code(payload: dict[str, Any], *, max_width: int = 100) -> None:
    console = make_console(max_width)
    width = console.width
    machine_line = pick_machine_line(payload.get("machine_info") or {})
    if len(machine_line) > width - 4:
        machine_line = machine_line[: width - 7] + "..."

    console.print(Rule("R-code benchmarks · raster & Textual export", style="bold"))
    console.print(Text(machine_line, style="dim"))
    console.print(Text(f"JSON: {payload.get('datetime', '?')}", style="dim italic"))
    console.print()

    bar_w = max(12, min(22, width - 52))

    textual = filter_benchmarks(payload, group="to_textual_2")
    if textual:
        by_n: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for b in textual:
            params = b.get("params") or {}
            by_n[int(params["n"])].append(b)
        for n in sorted(by_n):
            rows = _rows_from_group(by_n[n], ("pattern",))
            render_simple_table(
                console,
                title=f"to_textual_2 · n={n}×{n}",
                rows=rows,
                bar_w=bar_w,
                subtitle="Timed batch includes inner round loops (see note column).",
            )

    raster_groups = [
        ("triangle_raster", "triangle_raster · opaque pass"),
        ("triangle_raster_transparent_pass", "triangle_raster · transparent pass"),
        ("triangle_rust_raster", "triangle_rust_raster · depth modes"),
    ]
    for group, title in raster_groups:
        benches = filter_benchmarks(payload, group=group)
        if not benches:
            continue
        if group == "triangle_rust_raster":
            rows = _rows_from_group(benches, ("mode", "tri_count"))
        else:
            rows = _rows_from_group(benches, ("size",))
        render_simple_table(console, title=title, rows=rows, bar_w=bar_w)

    if not textual and not any(
        filter_benchmarks(payload, group=g) for g, _ in raster_groups
    ):
        raise SystemExit(
            "No r_code benchmark rows in JSON. Run scripts/bench_r_code.sh first."
        )

    console.print(Rule(style="dim"))
    console.print(
        Text(
            "ms = pytest-benchmark mean per invocation (whole timed batch). "
            "thruput bar: fastest row in each panel is full width.",
            style="dim",
        )
    )
    console.print()


def report_ttsl(payload: dict[str, Any], *, max_width: int = 100) -> None:
    benches = filter_benchmarks(payload, group="ttsl_run")
    if not benches:
        raise SystemExit(
            "No ttsl_run benchmark rows in JSON. Run scripts/bench_ttsl.sh first."
        )

    console = make_console(max_width)
    width = console.width
    machine_line = pick_machine_line(payload.get("machine_info") or {})
    if len(machine_line) > width - 4:
        machine_line = machine_line[: width - 7] + "..."

    console.print(Rule("TTSL VM · ttsl_run", style="bold"))
    console.print(Text(machine_line, style="dim"))
    console.print()

    bar_w = max(12, min(22, width - 52))
    rows = _rows_from_group(
        benches,
        ("shader_codeidx",),
        label_fn=lambda p: f"shader[{p.get('shader_codeidx', '?')}]",
    )
    render_simple_table(
        console,
        title="ttsl_run · shader variants",
        rows=rows,
        bar_w=bar_w,
        subtitle="One VM invocation per benchmark sample (bytecode compiled once per variant).",
    )
    console.print(Rule(style="dim"))
    console.print()
