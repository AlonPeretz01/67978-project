"""Visualization helpers for missing-data analysis."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


PRIMARY_COLOR = "#1F4E79"
GRID_COLOR = "#D9D9D9"
EXPORT_DPI = 200


def plot_null_percentages(
    null_summary: pd.DataFrame,
    output_path: Path,
    *,
    max_columns: int = 20,
) -> None:
    """Save a ranked bar chart of the most-missing columns."""
    required_columns = {"Column", "Null_Percentage"}
    if not required_columns.issubset(null_summary.columns):
        raise ValueError("null_summary must contain Column and Null_Percentage columns.")

    display = null_summary.head(max_columns).sort_values("Null_Percentage")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    figure, axis = plt.subplots(figsize=(9, max(5.5, 0.35 * len(display) + 2)))
    axis.barh(display["Column"], display["Null_Percentage"], color=PRIMARY_COLOR)
    axis.set_title("Which columns have the highest missing-data rates?", fontsize=17, fontweight="semibold")
    axis.set_xlabel("Missing values (%)", fontsize=13)
    axis.set_ylabel("Column", fontsize=13)
    axis.tick_params(axis="both", labelsize=11)
    axis.set_xlim(left=0)
    axis.grid(axis="x", color=GRID_COLOR, linestyle=":", alpha=0.7)
    axis.set_axisbelow(True)
    figure.tight_layout()
    figure.savefig(output_path, dpi=EXPORT_DPI, bbox_inches="tight")
    plt.close(figure)
