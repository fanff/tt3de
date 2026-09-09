# -*- coding: utf-8 -*-
"""Summarize TTSL Criterion results as a table and a gnuplot chart.

Reads ``target/criterion/ttsl_exec_*/**/new/estimates.json`` from a prior
``cargo bench -p tt3de-core --bench all -- ttsl`` run.

Typical workflow (repository root)::

    cargo bench -p tt3de-core --bench all -- ttsl --plotting-backend gnuplot
    uv run --no-sync python scripts/ttsl_criterion_report.py
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ARMS = ("jit", "jit_cell")


def repo_root() -> Path:
    here = Path(__file__).resolve().parent.parent
    if not (here / "crates" / "tt3de-core").is_dir():
        raise SystemExit("ttsl_criterion_report.py: expected repo root with crates/tt3de-core")
    return here


def load_ns(estimates: Path) -> float:
    data = json.loads(estimates.read_text(encoding="utf-8"))
    return float(data["mean"]["point_estimate"])


def collect_rows(criterion_dir: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for group_dir in sorted(criterion_dir.glob("ttsl_exec_*")):
        if not group_dir.is_dir():
            continue
        shader = group_dir.name.removeprefix("ttsl_exec_")
        row: dict[str, object] = {"shader": shader}
        for arm in ARMS:
            path = group_dir / arm / "new" / "estimates.json"
            row[arm] = load_ns(path) if path.is_file() else None
        if any(row[arm] is not None for arm in ARMS):
            rows.append(row)
    return rows


def fmt_ns(value: object) -> str:
    if value is None:
        return "—"
    ns = float(value)
    if ns >= 1000:
        return f"{ns / 1000:.2f} µs"
    return f"{ns:.2f} ns"


def print_table(rows: list[dict[str, object]]) -> None:
    headers = ("shader", "jit", "jit_cell")
    body: list[list[str]] = []
    for row in rows:
        body.append(
            [
                str(row["shader"]),
                fmt_ns(row["jit"]),
                fmt_ns(row["jit_cell"]),
            ]
        )
    widths = [len(h) for h in headers]
    for line in body:
        for i, cell in enumerate(line):
            widths[i] = max(widths[i], len(cell))

    def fmt_row(cells: list[str]) -> str:
        return "  ".join(
            cells[i].ljust(widths[i]) if i == 0 else cells[i].rjust(widths[i])
            for i in range(len(headers))
        )

    print(fmt_row(list(headers)))
    print("  ".join("-" * w for w in widths))
    for line in body:
        print(fmt_row(line))


def write_gnuplot(
    rows: list[dict[str, object]], out_dir: Path, gnuplot: str
) -> list[Path]:
    dat = out_dir / "ttsl_exec_compare.dat"
    gp = out_dir / "ttsl_exec_compare.gp"
    times_svg = out_dir / "ttsl_exec_times.svg"

    lines = ["# shader  jit  jit_cell"]
    for row in rows:
        vals = []
        for arm in ARMS:
            v = row[arm]
            vals.append("NaN" if v is None else f"{float(v):.6f}")
        lines.append(f'"{row["shader"]}" ' + " ".join(vals))
    dat.write_text("\n".join(lines) + "\n", encoding="utf-8")

    script = f"""
set encoding utf8
set terminal svg size 960,480 font "Arial,12" background rgb "white"
set output "{times_svg.as_posix()}"
set style data histogram
set style histogram clustered gap 1
set style fill solid 0.75 border -1
set boxwidth 0.9
set ylabel "ns / cell (mean)"
set xlabel "shader"
set key top left
set grid ytics
set yrange [0:*]
plot "{dat.as_posix()}" using 2:xtic(1) title "jit", \\
     "" using 3 title "jit_cell"
"""
    gp.write_text(script, encoding="utf-8")
    subprocess.run([gnuplot, str(gp)], check=True)
    return [times_svg]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--criterion-dir",
        type=Path,
        default=None,
        help="Criterion output dir (default: <repo>/target/criterion)",
    )
    parser.add_argument(
        "--no-plot",
        action="store_true",
        help="Print the table only; skip gnuplot",
    )
    args = parser.parse_args()

    root = repo_root()
    criterion_dir = args.criterion_dir or (root / "target" / "criterion")
    if not criterion_dir.is_dir():
        print(
            f"no Criterion output at {criterion_dir}\n"
            "run: cargo bench -p tt3de-core --bench all -- ttsl",
            file=sys.stderr,
        )
        return 1

    rows = collect_rows(criterion_dir)
    if not rows:
        print(f"no ttsl_exec results under {criterion_dir}", file=sys.stderr)
        return 1

    print_table(rows)
    print()
    print(f"Criterion HTML: {(criterion_dir / 'report' / 'index.html').resolve()}")

    if args.no_plot:
        return 0

    gnuplot = shutil.which("gnuplot")
    if gnuplot is None:
        print(
            "gnuplot not on PATH; table only.\n"
            "install gnuplot, or re-run cargo bench with --plotting-backend gnuplot",
            file=sys.stderr,
        )
        return 0

    out_dir = criterion_dir
    written = write_gnuplot(rows, out_dir, gnuplot)
    print("gnuplot:")
    for path in written:
        print(f"  {path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
