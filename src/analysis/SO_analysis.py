"""Stack Overflow community and visiting trends, 2017-2025."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import pandas as pd


PRIMARY_COLOR = "#1F77B4"
SECONDARY_COLOR = "#FF7F0E"
TERTIARY_COLOR = "#2CA02C"
GRID_COLOR = "#D9D9D9"
YEAR_RANGE = list(range(2017, 2026))
VISIT_YEAR_RANGE = list(range(2019, 2026))
VISIT_INCLUDED = {
    "A few times per month or weekly",
    "A few times per week",
    "Daily or almost daily",
    "Multiple times per day",
}


def _base_axes(ax: plt.Axes, title: str, ylabel: str) -> None:
    """Apply shared styling consistent with project figure conventions."""
    ax.set_title(title, fontsize=17, weight="semibold", pad=14)
    ax.set_xlabel("Survey year", fontsize=13)
    ax.set_ylabel(ylabel, fontsize=13)
    ax.tick_params(axis="both", labelsize=11)
    ax.grid(axis="y", color=GRID_COLOR, linestyle=":", alpha=0.7)
    ax.set_axisbelow(True)
    ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    ax.set_ylim(0.0, 1.0)


def is_part_of_community(df: pd.DataFrame, output_path: str | Path) -> pd.DataFrame:
    """
    Plot yearly shares of respondents who do and do not feel part of the
    Stack Overflow community, using `Part_of_community` answers that contain
    'yes' or 'no' (case-insensitive), for years 2017-2025.
    """
    subset = df.copy()
    subset["Year"] = pd.to_numeric(subset["Year"], errors="coerce")
    subset = subset[subset["Year"].isin(YEAR_RANGE)].copy()
    answers = subset["Part_of_community"].astype("string").str.strip()
    subset = subset.loc[answers.notna() & answers.ne("")].copy()
    answers = subset["Part_of_community"].astype("string").str.strip()

    metrics = (
        subset.assign(
            yes=answers.str.contains(r"yes|(?<!dis)agree", case=False, na=False, regex=True),
            no=answers.str.contains(r"no|disagree", case=False, na=False, regex=True),
        )
        .groupby("Year", as_index=True)
        .agg(
            yes_share=("yes", "mean"),
            no_share=("no", "mean"),
            n_responses=("Year", "size"),
        )
        .reindex(YEAR_RANGE)
    )

    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.plot(metrics.index, metrics["yes_share"], marker="o", linewidth=2, color=PRIMARY_COLOR, label="Feel part of community")
    ax.plot(metrics.index, metrics["no_share"], marker="o", linewidth=2, color=SECONDARY_COLOR, label="Do not feel part of community")
    _base_axes(
        ax,
        "Sense of Stack Overflow community shifted over time, 2017-2025",
        "Share of respondents",
    )
    ax.set_xticks(YEAR_RANGE)
    ax.legend(title="Response group", fontsize=11, title_fontsize=11)
    fig.tight_layout()
    fig.savefig(Path(output_path), dpi=200, bbox_inches="tight")
    plt.close(fig)
    return metrics.reset_index(names="Year")


def visit_over_time(df: pd.DataFrame, output_path: str | Path) -> pd.DataFrame:
    """
    Plot the yearly share of respondents who visit Stack Overflow at least a
   few times per month, for years 2019-2025, using `Participates_in_questions`.
    """
    subset = df.copy()
    subset["Year"] = pd.to_numeric(subset["Year"], errors="coerce")
    subset = subset[subset["Year"].isin(VISIT_YEAR_RANGE)].copy()
    visit_answers = subset["Participates_in_questions"].astype("string").str.strip()
    subset = subset.loc[visit_answers.notna() & visit_answers.ne("")].copy()
    visit_answers = subset["Participates_in_questions"].astype("string").str.strip()

    metrics = (
        subset.assign(
            frequent_visit=visit_answers.isin(VISIT_INCLUDED),
        )
        .groupby("Year", as_index=True)
        .agg(
            frequent_visit_share=("frequent_visit", "mean"),
            n_responses=("Year", "size"),
        )
        .reindex(VISIT_YEAR_RANGE)
    )

    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.plot(
        metrics.index,
        metrics["frequent_visit_share"],
        marker="o",
        linewidth=2,
        color=TERTIARY_COLOR,
        label="Participates at least a few times per month",
    )
    _base_axes(
        ax,
        "Frequent Stack Overflow participation declined over time, 2019-2025",
        "Share of respondents",
    )
    ax.set_xticks(VISIT_YEAR_RANGE)
    ax.legend(fontsize=11)
    fig.tight_layout()
    fig.savefig(Path(output_path), dpi=200, bbox_inches="tight")
    plt.close(fig)
    return metrics.reset_index(names="Year")


# NOTE: `count_null_percentages` used to live here purely to print per-year
# null percentages for `Part_of_community` to the console during the pipeline
# run.  It has been removed twice now, reappearing through a merge the first
# time.  Do not reintroduce it: the FACT CHECK table in
# outputs/audit/AUDIT.md already carries the per-year non-null counts, so the
# console print is redundant output with no reader.
