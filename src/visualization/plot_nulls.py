"""Visualization helpers for missing-data analysis."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


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

    figure, axis = plt.subplots(figsize=(13, 8))
    axis.barh(display["Column"], display["Null_Percentage"], color="#1f4e79")
    axis.set_title("Columns with the Highest Missingness", fontsize=18, fontweight="bold")
    axis.set_xlabel("Missing values (%)", fontsize=16, fontweight="bold")
    axis.set_ylabel("Column", fontsize=16, fontweight="bold")
    axis.tick_params(axis="both", labelsize=12)
    axis.grid(axis="x", linestyle=":", alpha=0.5)
    axis.set_axisbelow(True)
    figure.tight_layout()
    figure.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(figure)
