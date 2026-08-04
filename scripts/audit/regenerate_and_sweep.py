"""Figure freshness report for the single main-pipeline run."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIGURES_DIRECTORY = ROOT / "outputs" / "figures"
OUTPUT_PATH = ROOT / "outputs" / "audit" / "FIGURE_SWEEP.md"

FIGURE_GENERATORS = {
    "demographic_shift_2011_2025.png": ("plot_demographic_shift", True),
    "null_distribution_boxplot.png": ("plot_null_distribution_by_year", True),
    "null_distribution_plot.png": ("plot_null_percentages", True),
    "robustness_junior_series.png": ("scripts.audit.generate_followup.write_robustness", True),
    "robustness_r_squared_by_break.png": ("scripts.audit.generate_followup.write_robustness", True),
    "post_corona_age_participation.png": ("OUT OF SCOPE: post-corona pipeline", True),
    "post_corona_fulltime_participation.png": ("OUT OF SCOPE: post-corona pipeline", True),
    "post_corona_fulltime_participation_distribution.png": ("OUT OF SCOPE: post-corona pipeline", True),
    "post_corona_participation_by_age.png": ("OUT OF SCOPE: post-corona pipeline", True),
}


def write_figure_sweep(started: datetime) -> Path:
    """List every output figure and identify any stale or unreachable file."""
    rows: list[list[str]] = []
    for path in sorted(FIGURES_DIRECTORY.glob("*.png")):
        modified = datetime.fromtimestamp(path.stat().st_mtime)
        generator, called = FIGURE_GENERATORS.get(path.name, ("NOT AVAILABLE: no generator mapping", False))
        status = "CURRENT" if modified >= started else "FLAG: older than this run"
        rows.append([path.name, modified.isoformat(sep=" ", timespec="seconds"), status, generator, "YES" if called else "NO"])
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    content = "# Figure freshness sweep\n\n"
    content += f"Pipeline run started: `{started.isoformat(sep=' ', timespec='seconds')}`.\n\n"
    content += "| File | Modification timestamp | Freshness | Generating function | Called by `main.py`? |\n| --- | --- | --- | --- | --- |\n"
    content += "\n".join("| " + " | ".join(row) + " |" for row in rows) + "\n\n"
    unreachable = [row[0] for row in rows if row[4] == "NO"]
    content += "Figures not reachable from `main.py`: " + (", ".join(unreachable) if unreachable else "NONE") + ".\n"
    OUTPUT_PATH.write_text(content, encoding="utf-8")
    return OUTPUT_PATH


def main() -> None:
    # Standalone use is inspection-only: it must never invoke the pipeline
    # that produced the files being checked.
    print(write_figure_sweep(datetime.now()))


if __name__ == "__main__":
    main()
