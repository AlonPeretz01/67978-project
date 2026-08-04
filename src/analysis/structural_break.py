"""Broken-stick fitting utility retained for the reported placebo scan."""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm


# Retained because AUDIT.md documents the former fixed intervention years.
THEORETICAL_INTERVENTION_YEARS = (2020, 2022)


def _fit_broken_stick(
    sample: pd.DataFrame, year_column: str, metric: str, knot_year: int
) -> object:
    """Fit a continuous two-slope linear model at a supplied candidate knot."""
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
