"""Missing-data analysis functions."""

from __future__ import annotations

import pandas as pd


def summarize_null_percentages(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Return missingness percentages for every column in descending order."""
    if dataframe.empty:
        raise ValueError("Cannot analyse an empty DataFrame.")

    summary = dataframe.isna().mean().mul(100).rename("Null_Percentage")
    return (
        summary.rename_axis("Column")
        .reset_index()
        .sort_values("Null_Percentage", ascending=False, ignore_index=True)
    )
