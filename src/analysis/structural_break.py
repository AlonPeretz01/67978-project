"""Structural break detection for early-career developer survey proportions."""

from __future__ import annotations

from typing import Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import ruptures as rpt
from matplotlib.figure import Figure


def detect_early_career_structural_breaks(
    data: pd.DataFrame,
    *,
    penalty: float = 0.01,
    min_size: int = 2,
) -> Tuple[list[int], Figure]:
    """Detect structural breaks in early-career developer proportions.

    The PELT algorithm with the L2 cost model identifies changes in the
    ``Junior_Proportion`` time series. Survey years are plotted at equally
    spaced categorical positions, so omitted years do not create gaps on the
    x-axis.

    Args:
        data: A DataFrame containing unique ``Survey_Year`` integer values and
            finite ``Junior_Proportion`` float values.
        penalty: PELT penalty controlling detection sensitivity. Larger values
            yield fewer breaks and should be tuned to the data's scale/noise.
        min_size: Minimum observations permitted in every detected segment.

    Returns:
        A tuple of detected break years and the generated matplotlib Figure.
        Each detected year is the first survey year in the post-break segment.

    Raises:
        ValueError: If input columns or values are invalid, or insufficient
            data is supplied for the requested minimum segment size.
    """
    required_columns = {"Survey_Year", "Junior_Proportion"}
    missing_columns = required_columns.difference(data.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {sorted(missing_columns)}")

    cleaned = (
        data.loc[:, ["Survey_Year", "Junior_Proportion"]]
        .dropna()
        .sort_values("Survey_Year")
        .reset_index(drop=True)
    )

    if cleaned["Survey_Year"].duplicated().any():
        raise ValueError("Survey_Year values must be unique.")
    if not pd.api.types.is_integer_dtype(cleaned["Survey_Year"]):
        raise ValueError("Survey_Year must use an integer dtype.")
    if not pd.api.types.is_numeric_dtype(cleaned["Junior_Proportion"]):
        raise ValueError("Junior_Proportion must be numeric.")
    if not np.isfinite(cleaned["Junior_Proportion"].to_numpy(dtype=float)).all():
        raise ValueError("Junior_Proportion must contain only finite values.")
    if min_size < 1:
        raise ValueError("min_size must be at least 1.")
    if len(cleaned) < 2 * min_size:
        raise ValueError(
            f"At least {2 * min_size} observations are required for min_size={min_size}."
        )
    if penalty <= 0:
        raise ValueError("penalty must be positive.")

    years = cleaned["Survey_Year"].astype(int).tolist()
    proportions = cleaned["Junior_Proportion"].to_numpy(dtype=float)
    x_positions = np.arange(len(years))

    # PELT returns segment endpoints, including len(proportions). A break at
    # endpoint i means that years[i] begins the following segment.
    endpoints = rpt.Pelt(model="l2", min_size=min_size).fit(proportions).predict(
        pen=penalty
    )
    break_indices = [endpoint for endpoint in endpoints if endpoint < len(years)]
    break_years = [years[index] for index in break_indices]

    with plt.rc_context(
        {
            "font.size": 14,
            "axes.titlesize": 18,
            "axes.labelsize": 16,
            "xtick.labelsize": 14,
            "ytick.labelsize": 14,
            "legend.fontsize": 14,
        }
    ):
        figure, axis = plt.subplots(figsize=(12, 7))
        axis.plot(
            x_positions,
            proportions,
            color="#1f4e79",
            linewidth=3,
            marker="o",
            markersize=8,
            label="Early-career developer proportion",
        )

        for line_number, break_index in enumerate(break_indices):
            axis.axvline(
                x=break_index,
                color="red",
                linestyle="--",
                linewidth=2.5,
                alpha=0.9,
                label="Detected structural break" if line_number == 0 else None,
            )

        axis.set_xticks(x_positions)
        axis.set_xticklabels(years)
        axis.set_title(
            "Structural Break Detection: Early-Career Developer Proportion",
            fontweight="bold",
        )
        axis.set_xlabel("Survey Year", fontweight="bold")
        axis.set_ylabel("Junior Developer Proportion", fontweight="bold")
        axis.grid(True, linestyle=":", linewidth=0.8, alpha=0.55)
        axis.legend()
        figure.tight_layout()

    return break_years, figure

