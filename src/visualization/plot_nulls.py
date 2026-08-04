"""Visualization helpers for missing-data analysis."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


PRIMARY_COLOR = "#1F4E79"
GRID_COLOR = "#D9D9D9"
THRESHOLD_COLOR = "#C73E1D"
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


def plot_null_distribution_by_year(df: pd.DataFrame, output_path: Path) -> None:
    """Save yearly distributions of column-level missingness percentages."""
    year_column = "Year"
    if year_column not in df.columns:
        raise ValueError("df must contain a Year column.")

    value_columns = df.columns.drop(year_column)
    if value_columns.empty:
        raise ValueError("df must contain at least one non-Year column.")

    # הלוגיקה המתוקנת של חישוב הנתונים (שומרים עליה כמו שהיא)
    yearly_null_percentages = (
        df.groupby(year_column, sort=True)[value_columns.tolist()]
        .agg(lambda column: column.isna().mean() * 100)
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data_to_plot = [
        yearly_null_percentages.loc[year].dropna().to_numpy()
        for year in yearly_null_percentages.index
    ]

    # הגדרות עיצוב התואמות לתמונה image_bcf747.png
    figure, axis = plt.subplots(figsize=(12, 6))
    
    # צבעי העיצוב הישן
    box_face_color = "#8FB0C6"  # תכלת בהיר-אפרפר
    box_edge_color = "#1F3B5C"  # כחול כהה למסגרות
    median_color = "#D62728"    # אדום לחציון

    boxplot = axis.boxplot(
        data_to_plot,
        labels=yearly_null_percentages.index,
        patch_artist=True,
        medianprops={"color": median_color, "linewidth": 1.5},
        whiskerprops={"color": box_edge_color, "linewidth": 1.2},
        capprops={"color": box_edge_color, "linewidth": 1.2},
        flierprops={
            "marker": "o",
            "markerfacecolor": "none",
            "markeredgecolor": "gray",
            "markersize": 4,
            "alpha": 0.7,
        },
    )
    
    # צביעת הקופסאות עצמן
    for box in boxplot["boxes"]:
        box.set(facecolor=box_face_color, edgecolor=box_edge_color, linewidth=1.2)

    axis.axhline(
        80,
        color="red",
        linestyle="--",
        linewidth=1.5,
        label="80% Threshold Reference",
    )
    
    axis.set_title(
        "Distribution of Null Percentages per Column (2011-2025)",
        fontsize=14,
        fontweight="bold",
    )
    axis.set_xlabel("Survey Year", fontsize=12, fontweight="bold")
    axis.set_ylabel("Percentage of Missing Values (%)", fontsize=12, fontweight="bold")
    
    axis.grid(axis="y", color="#D9D9D9", linestyle="--", alpha=0.7)
    axis.set_axisbelow(True)
    axis.legend(loc="upper right", fontsize=10)
    
    figure.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(figure)
