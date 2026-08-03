"""Dataset-audit helpers with no import-time I/O or output."""

from __future__ import annotations

from typing import Any

import pandas as pd


def audit_dataset(dataframe: pd.DataFrame) -> dict[str, Any]:
    """Return core quality and coverage metrics for a processed dataset."""
    if dataframe.empty:
        raise ValueError("Cannot audit an empty DataFrame.")

    rows_by_year = (
        dataframe["Year"].value_counts().sort_index()
        if "Year" in dataframe.columns
        else pd.Series(dtype="int64")
    )
    missing_percentages = dataframe.isna().mean().mul(100).sort_values(ascending=False)

    return {
        "rows": len(dataframe),
        "columns": len(dataframe.columns),
        "duplicate_rows": int(dataframe.duplicated().sum()),
        "rows_by_year": rows_by_year,
        "missing_percentages": missing_percentages,
        "sample": dataframe.head(3).copy(),
    }
