"""Theory-driven piecewise linear trend analysis for annual survey metrics."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from matplotlib.figure import Figure


THEORETICAL_INTERVENTION_YEARS = (2020, 2022)
DEFAULT_PLOT_DIRECTORY = Path("outputs/figures")


def analyze_theoretical_slope_changes(
    data: pd.DataFrame,
    *,
    year_column: str = "Survey_Year",
    metric_columns: Sequence[str] | None = None,
    intervention_years: Sequence[int] = THEORETICAL_INTERVENTION_YEARS,
    truncated_start_year: int = 2014,
    alpha: float = 0.05,
    output_directory: str | Path = DEFAULT_PLOT_DIRECTORY,
) -> tuple[pd.DataFrame, dict[str, Figure]]:
    """Test theory-specified changes in trend with continuous broken sticks.

    The model is ``metric = intercept + slope_before * time + slope_change *
    max(0, time)``. It tests only the difference in slope at a specified knot;
    it does not allow an abrupt level jump. Results include full-data and
    2014-onward sensitivity estimates. Each intervention is rendered as a
    separate visual-only figure.
    """
    if year_column not in data.columns:
        raise ValueError(f"Missing required year column: {year_column}")
    if not intervention_years:
        raise ValueError("At least one intervention year is required.")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1.")

    metrics = _resolve_metrics(data, year_column, metric_columns)
    intervention_years = tuple(sorted(set(int(year) for year in intervention_years)))
    primary_sample_name = f"{truncated_start_year}+ Truncated Sample"
    results: list[dict[str, object]] = []
    fits: dict[tuple[str, str, int], tuple[pd.DataFrame, object]] = {}
    series_by_metric: dict[str, pd.DataFrame] = {}

    for metric in metrics:
        full_series = _clean_metric_data(data, year_column, metric)
        truncated_series = full_series.loc[
            full_series[year_column] >= truncated_start_year
        ].reset_index(drop=True)
        series_by_metric[metric] = full_series
        for sample_name, sample in (
            ("Full Dataset", full_series),
            (primary_sample_name, truncated_series),
        ):
            for knot_year in intervention_years:
                model = _fit_broken_stick(sample, year_column, metric, knot_year)
                results.append(
                    _summarize_slope_change(
                        model, sample, year_column, metric, sample_name, knot_year, alpha
                    )
                )
                fits[(metric, sample_name, knot_year)] = (sample, model)

    sensitivity_table = pd.DataFrame(results).sort_values(
        ["metric", "knot_year", "sample"], ignore_index=True
    )
    destination_directory = Path(output_directory)
    destination_directory.mkdir(parents=True, exist_ok=True)
    figures = _save_slope_change_figures(
        series_by_metric,
        fits,
        year_column,
        intervention_years,
        primary_sample_name,
        destination_directory,
    )
    return sensitivity_table, figures


def format_sensitivity_table(sensitivity_table: pd.DataFrame) -> pd.DataFrame:
    """Return a compact, presentation-ready table for console output."""
    table = sensitivity_table.rename(
        columns={
            "metric": "Metric",
            "sample": "Sample",
            "knot_year": "Intervention Year",
            "slope_change": "Delta Slope",
            "slope_change_p_value": "p-value",
        }
    ).copy()
    table["Delta Slope"] = table["Delta Slope"].map("{:.4f}".format)
    table["95% CI"] = table.apply(
        lambda row: (
            f"[{row['slope_change_ci_lower']:.4f}, "
            f"{row['slope_change_ci_upper']:.4f}]"
        ),
        axis=1,
    )
    table["p-value"] = table["p-value"].map("{:.4g}".format)
    table["_sample_order"] = table["Sample"].eq("Full Dataset").map({True: 0, False: 1})
    return (
        table.sort_values(["Metric", "Intervention Year", "_sample_order"])
        .loc[:, ["Metric", "Sample", "Intervention Year", "Delta Slope", "95% CI", "p-value"]]
        .reset_index(drop=True)
    )


def _resolve_metrics(
    data: pd.DataFrame, year_column: str, metric_columns: Sequence[str] | None
) -> list[str]:
    if metric_columns is None:
        metrics = [
            column for column in data.columns
            if column != year_column and pd.api.types.is_numeric_dtype(data[column])
        ]
    else:
        metrics = list(metric_columns)
    missing_metrics = set(metrics).difference(data.columns)
    if missing_metrics:
        raise ValueError(f"Missing metric columns: {sorted(missing_metrics)}")
    if not metrics:
        raise ValueError("At least one numeric metric column is required.")
    return metrics


def _clean_metric_data(data: pd.DataFrame, year_column: str, metric: str) -> pd.DataFrame:
    if not pd.api.types.is_numeric_dtype(data[metric]):
        raise ValueError(f"{metric} must be numeric.")
    cleaned = data.loc[:, [year_column, metric]].dropna().copy()
    cleaned[year_column] = pd.to_numeric(cleaned[year_column], errors="raise")
    cleaned = cleaned.sort_values(year_column).reset_index(drop=True)
    if not np.isfinite(cleaned[[year_column, metric]].to_numpy(dtype=float)).all():
        raise ValueError(f"{metric} and {year_column} must contain only finite values.")
    if not np.equal(cleaned[year_column], np.floor(cleaned[year_column])).all():
        raise ValueError(f"{year_column} must contain integer years.")
    if cleaned[year_column].duplicated().any():
        raise ValueError(f"{year_column} values must be unique for {metric}.")
    return cleaned


def _fit_broken_stick(
    sample: pd.DataFrame, year_column: str, metric: str, knot_year: int
) -> object:
    pre_count = int((sample[year_column] < knot_year).sum())
    post_count = int((sample[year_column] >= knot_year).sum())
    if pre_count < 2 or post_count < 2:
        raise ValueError(
            f"The {knot_year} intervention needs at least two observations on each side "
            f"in the analysed sample; received {pre_count} pre and {post_count} post."
        )
    if len(sample) <= 3:
        raise ValueError("At least four observations are required for piecewise regression.")
    time = sample[year_column].astype(float) - knot_year
    design = pd.DataFrame({"time": time, "slope_change": np.maximum(time, 0.0)})
    return sm.OLS(
        sample[metric].astype(float), sm.add_constant(design, has_constant="add")
    ).fit()


def _summarize_slope_change(
    model: object,
    sample: pd.DataFrame,
    year_column: str,
    metric: str,
    sample_name: str,
    knot_year: int,
    alpha: float,
) -> dict[str, object]:
    confidence_interval = model.conf_int(alpha=alpha).loc["slope_change"]
    slope_before = float(model.params["time"])
    slope_change = float(model.params["slope_change"])
    return {
        "metric": metric,
        "sample": sample_name,
        "knot_year": knot_year,
        "observations": len(sample),
        "pre_knot_observations": int((sample[year_column] < knot_year).sum()),
        "post_knot_observations": int((sample[year_column] >= knot_year).sum()),
        "slope_before": slope_before,
        "slope_change": slope_change,
        "slope_after": slope_before + slope_change,
        "slope_change_ci_lower": float(confidence_interval.iloc[0]),
        "slope_change_ci_upper": float(confidence_interval.iloc[1]),
        "slope_change_p_value": float(model.pvalues["slope_change"]),
        "df_resid": int(model.df_resid),
        "significant_at_alpha": bool(float(model.pvalues["slope_change"]) < alpha),
    }


def _save_slope_change_figures(
    series_by_metric: dict[str, pd.DataFrame],
    fits: dict[tuple[str, str, int], tuple[pd.DataFrame, object]],
    year_column: str,
    intervention_years: Sequence[int],
    primary_sample_name: str,
    output_directory: Path,
) -> dict[str, Figure]:
    """Save one clean standalone figure per metric and intervention year."""
    figures: dict[str, Figure] = {}
    with plt.rc_context({"font.size": 11, "axes.titlesize": 14, "legend.fontsize": 10}):
        for metric, full_series in series_by_metric.items():
            for knot_year in intervention_years:
                figure, axis = plt.subplots(figsize=(8, 5.5), constrained_layout=True)
                axis.plot(
                    full_series[year_column], full_series[metric], color="#1f4e79",
                    marker="o", linewidth=2, markersize=6, label="Observed data",
                )
                axis.axvline(
                    knot_year, color="red", linestyle="--", linewidth=2,
                    label=f"Intervention ({knot_year})",
                )
                sample, model = fits[(metric, primary_sample_name, knot_year)]
                fitted = model.predict(_design_for_years(sample[year_column], knot_year))
                axis.plot(
                    sample[year_column], fitted, color="#e76f51", linewidth=2.4,
                    label=f"{primary_sample_name} fit",
                )
                axis.set_title(
                    f"{metric.replace('_', ' ')} - Intervention: {knot_year}",
                    fontweight="bold",
                )
                axis.set_xlabel("Survey Year")
                axis.set_ylabel(metric.replace("_", " "))
                axis.grid(True, linestyle=":", alpha=0.5)
                axis.legend(loc="best", frameon=False)
                filename = f"{_filename_stem(metric)}_break_{knot_year}.png"
                figure.savefig(output_directory / filename, dpi=300, bbox_inches="tight")
                figures[filename] = figure
    return figures


def _filename_stem(metric: str) -> str:
    """Create a filesystem-safe, readable metric name for figure filenames."""
    return "_".join(metric.lower().split()).replace("_", "_")


def _design_for_years(years: pd.Series, knot_year: int) -> pd.DataFrame:
    time = years.astype(float) - knot_year
    return sm.add_constant(
        pd.DataFrame({"time": time, "slope_change": np.maximum(time, 0.0)}),
        has_constant="add",
    )
