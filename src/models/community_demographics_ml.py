"""Longitudinal demographics and Stack Overflow engagement modelling.

The module exposes reusable functions for demographic summaries, engagement
modelling, and publication-ready figure generation.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier


LOGGER = logging.getLogger(__name__)

YEAR_MIN = 2011
YEAR_MAX = 2025
DEMOGRAPHIC_YEAR_MAX = 2024
RECENT_YEAR_MIN = 2022
RANDOM_STATE = 42

REQUIRED_COLUMNS = {
    "Year",
    "Years_of_Experience",
    "Yearly_Compensation",
    "Education_Level",
    "Part_of_community",
    "Visits_SO_freq",
}

MODEL_FEATURES = [
    "Years_of_Experience",
    "Yearly_Compensation",
    "Education_Level",
]
NUMERIC_FEATURES = ["Years_of_Experience", "Yearly_Compensation"]
CATEGORICAL_FEATURES = ["Education_Level"]

FEATURE_LABELS = {
    "Years_of_Experience": "Professional experience",
    "Yearly_Compensation": "Annual compensation",
    "Education_Level": "Education level",
}

PRIMARY_COLOR = "#1F4E79"
SECONDARY_COLOR = "#E69F00"
TERTIARY_COLOR = "#009E73"
NEUTRAL_COLOR = "#4D4D4D"
GRID_COLOR = "#D9D9D9"
EXPORT_DPI = 200


def experience_interval(value: object) -> tuple[float, float] | None:
    """Return inclusive bounds for a harmonized experience response.

    Early survey exports contain spreadsheet-corrupted forms of ``2-5`` and
    ``6-10``: both date strings (for example, ``2/5/2013``) and Excel serial
    dates. Restoring the original bounds is essential because these survey
    ranges cross the cohort boundaries used in the demographic chart.
    """
    if pd.isna(value):
        return None

    text = str(value).strip().lower().replace("–", "-").replace("—", "-")
    if not text or text in {"nan", "response", "prefer not to say"}:
        return None

    range_match = re.search(
        r"(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)", text
    )
    if range_match:
        lower, upper = map(float, range_match.groups())
        return (lower, upper) if lower <= upper else None

    # Explicit date-like corruptions of the original 2-5 and 6-10 labels.
    if re.fullmatch(r"2/5(?:/\d{4})?", text):
        return 2.0, 5.0
    if re.fullmatch(r"6/10(?:/\d{4})?", text):
        return 6.0, 10.0

    number_match = re.search(r"\d+(?:\.\d+)?", text.replace(",", ""))
    if "less than" in text or text.startswith("<"):
        # These are entirely early-career; retain useful midpoint semantics.
        upper_exclusive = float(number_match.group()) if number_match else 1.0
        return 0.0, max(0.0, upper_exclusive - 0.001)
    if not number_match:
        return None

    number = float(number_match.group())
    if number > 1000:
        try:
            date = pd.Timestamp("1899-12-30") + pd.to_timedelta(number, unit="D")
        except (OverflowError, ValueError):
            return None
        if (date.month, date.day) == (2, 5):
            return 2.0, 5.0
        if (date.month, date.day) == (6, 10):
            return 6.0, 10.0
        return None

    # Open-ended values are represented by their lower bound. They are well
    # above the senior threshold, so no cohort ambiguity is introduced.
    return (number, number) if 0 <= number <= 60 else None


def experience_to_years(value: object) -> float:
    """Convert historical numeric/range experience responses to years.

    Some early CSV exports converted labels such as ``2/5`` and ``6/10`` into
    dates or Excel serial dates. Those known forms are restored to range
    midpoints so that early years remain analytically usable.
    """
    interval = experience_interval(value)
    if interval is None:
        return np.nan
    lower, upper = interval
    return (lower + upper) / 2.0


def experience_cohort_weights(value: object) -> tuple[float, float, float]:
    """Return fractional junior, mid-career, and senior membership.

    Survey responses that span a cohort boundary are allocated uniformly over
    the integer experience years in their inclusive range. This avoids the
    systematic bias caused by assigning a broad category solely by midpoint.
    Exact numeric responses continue to belong to exactly one cohort.
    """
    interval = experience_interval(value)
    if interval is None:
        return np.nan, np.nan, np.nan

    lower, upper = interval
    integer_years = np.arange(np.ceil(lower), np.floor(upper) + 1, dtype=float)
    if integer_years.size == 0:
        integer_years = np.array([(lower + upper) / 2.0])

    return (
        float(np.mean(integer_years <= 3)),
        float(np.mean((integer_years >= 4) & (integer_years <= 7))),
        float(np.mean(integer_years >= 8)),
    )


def build_demographic_summary(data: pd.DataFrame) -> pd.DataFrame:
    """Calculate annual early-, mid-, and senior-career respondent shares."""
    demographic = data[["Year", "Years_of_Experience"]].copy()
    # Parse each unique label once: the 772k-row master contains relatively few
    # distinct experience categories, so this is both faster and auditable.
    unique_values = demographic["Years_of_Experience"].dropna().unique()
    weight_lookup = {
        value: experience_cohort_weights(value) for value in unique_values
    }
    weights = pd.DataFrame(
        demographic["Years_of_Experience"].map(weight_lookup).tolist(),
        index=demographic.index,
        columns=["Early_career_weight", "Mid_career_weight", "Senior_weight"],
    )
    demographic = pd.concat([demographic, weights], axis=1)
    demographic = demographic.dropna(subset=["Early_career_weight"])

    summary = demographic.groupby("Year").agg(
        early_career_share=("Early_career_weight", "mean"),
        mid_career_share=("Mid_career_weight", "mean"),
        senior_share=("Senior_weight", "mean"),
        valid_experience_responses=("Years_of_Experience", "size"),
    )
    summary = summary.reindex(range(YEAR_MIN, DEMOGRAPHIC_YEAR_MAX + 1))
    summary.index.name = "Year"

    # Proxy-based harmonization is preferred. Only if the two historically
    # problematic years still have no usable experience values do we fill the
    # *aggregated* junior time series by interpolation.
    fallback_years = [
        year
        for year in (2015, 2016)
        if year in summary.index and pd.isna(summary.loc[year, "early_career_share"])
    ]
    if fallback_years:
        interpolated_shares = summary[["early_career_share"]].interpolate(
            method="linear", limit_area="inside"
        )
        resolved_years = [
            year
            for year in fallback_years
            if pd.notna(interpolated_shares.loc[year, "early_career_share"])
        ]
        summary.loc[resolved_years, "early_career_share"] = interpolated_shares.loc[
            resolved_years, "early_career_share"
        ]
        if resolved_years:
            LOGGER.info(
                "Professional-experience proxies were unavailable for year(s) %s; "
                "applied linear interpolation to the aggregated Junior_Proportion series as a fallback.",
                ", ".join(map(str, resolved_years)),
            )

    absent = summary.index[summary["valid_experience_responses"].isna()].tolist()
    if absent:
        LOGGER.warning(
            "No professional-experience responses are available for year(s): %s",
            ", ".join(map(str, absent)),
        )
    return summary


def plot_demographic_shift(summary: pd.DataFrame, output_path: Path) -> None:
    """Plot the demographic 'scissor effect' on a single percentage axis."""
    fig, axis = plt.subplots(figsize=(15, 8.5))
    years = summary.index.to_numpy()

    junior_color = SECONDARY_COLOR
    senior_color = PRIMARY_COLOR
    mid_career_color = TERTIARY_COLOR
    reference_color = NEUTRAL_COLOR

    line_junior = axis.plot(
        years,
        summary["early_career_share"] * 100,
        color=junior_color,
        marker="o",
        linewidth=3.5,
        markersize=8,
        label="Early-career / Juniors (0–3 years)",
    )[0]
    line_senior = axis.plot(
        years,
        summary["senior_share"] * 100,
        color=senior_color,
        marker="s",
        linewidth=3.5,
        markersize=8,
        label="Seniors / Experienced (8+ years)",
    )[0]
    line_mid_career = axis.plot(
        years,
        summary["mid_career_share"] * 100,
        color=mid_career_color,
        marker="D",
        linewidth=2.5,
        markersize=6.5,
        alpha=0.9,
        label="Mid-career (4–7 years)",
    )[0]
    axis.set_xlabel("Survey year", fontsize=13)
    axis.set_ylabel("Survey respondents (%)", fontsize=13)
    axis.tick_params(axis="both", labelsize=11)
    axis.set_xticks(years)
    axis.set_xlim(YEAR_MIN - 0.35, DEMOGRAPHIC_YEAR_MAX + 0.35)
    largest_share = (
        summary[["early_career_share", "mid_career_share", "senior_share"]]
        .max()
        .max()
        * 100
    )
    axis.set_ylim(0, max(50, float(largest_share) * 1.15))

    # ChatGPT was released in late 2022; 2022.5 visually separates pre/post eras.
    reference = axis.axvline(
        2022.5,
        color=reference_color,
        linestyle="--",
        linewidth=2.5,
        label="ChatGPT / LLM assistant adoption (2022-23)",
        zorder=0,
    )
    axis.text(
        2022.62,
        0.97,
        "ChatGPT / LLM assistants",
        transform=axis.get_xaxis_transform(),
        fontsize=11,
        ha="left",
        va="top",
        color=reference_color,
    )

    axis.set_title(
        "Early-career and senior respondent shares diverged over time",
        fontsize=17,
        pad=18,
        weight="semibold",
    )
    axis.legend(
        handles=[line_junior, line_senior, line_mid_career, reference],
        loc="upper left",
        fontsize=11,
        frameon=False,
    )
    axis.grid(axis="y", color=GRID_COLOR, linewidth=0.9, alpha=0.8)
    axis.grid(axis="x", visible=False)
    axis.spines[["top", "right"]].set_visible(False)

    fig.text(
        0.5,
        0.025,
        "Note: Gaps (2015–2016) reflect survey instruments without harmonized professional-experience data.",
        ha="center",
        va="bottom",
        fontsize=10.5,
        color=NEUTRAL_COLOR,
        style="italic",
    )
    fig.tight_layout(rect=(0, 0.065, 1, 1))
    fig.savefig(output_path, dpi=EXPORT_DPI, bbox_inches="tight")
    plt.close(fig)


def engagement_target(data: pd.DataFrame) -> tuple[pd.Series, str]:
    """Map the best-covered engagement measure to active (1) / inactive (0)."""
    community_map = {
        "yes, definitely": 1.0,
        "yes, somewhat": 1.0,
        "neutral": 0.0,
        "no, not really": 0.0,
        "no, not at all": 0.0,
    }
    visit_map = {
        "multiple times per day": 1.0,
        "daily or almost daily": 1.0,
        "a few times per week": 1.0,
        "a few times per month or weekly": 0.0,
        "less than once per month or monthly": 0.0,
        "i have never visited stack overflow (before today)": 0.0,
    }

    community = (
        data["Part_of_community"].astype("string").str.strip().str.lower().map(community_map)
    )
    visits = (
        data["Visits_SO_freq"].astype("string").str.strip().str.lower().map(visit_map)
    )
    if community.notna().sum() >= 100 and community.nunique(dropna=True) == 2:
        return community, "Part of the Stack Overflow community"
    if visits.notna().sum() >= 100 and visits.nunique(dropna=True) == 2:
        return visits, "Frequent Stack Overflow visits"
    raise ValueError(
        "Recent survey rows do not contain a binary engagement target with "
        "at least 100 usable responses."
    )


def _mode_or_default(series: pd.Series, default: object) -> object:
    modes = series.dropna().mode()
    return modes.iloc[0] if not modes.empty else default


def encode_model_features(
    data: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, list[str]]]:
    """Median/mode-impute and one-hot encode predictors for the forest."""
    encoded_parts: list[pd.DataFrame] = []
    encoded_groups: dict[str, list[str]] = {}

    for column in NUMERIC_FEATURES:
        values = pd.to_numeric(data[column], errors="coerce")
        if column == "Years_of_Experience":
            values = data[column].map(experience_to_years)
        values = values.replace([np.inf, -np.inf], np.nan)
        median = _mode_or_default(values, 0.0) if values.notna().sum() == 0 else values.median()
        part = values.fillna(median).astype(float).to_frame(column)
        encoded_parts.append(part)
        encoded_groups[column] = [column]

    for column in CATEGORICAL_FEATURES:
        values = data[column].astype("string").str.strip().replace("", pd.NA)
        fill_value = _mode_or_default(values, "Not available")
        values = values.fillna(fill_value)

        prefix = f"{column}="
        part = pd.get_dummies(values, prefix=column, prefix_sep="=", dtype=float)
        if part.shape[1] == 0:
            part[f"{prefix}Not available"] = 1.0
        encoded_parts.append(part)
        encoded_groups[column] = part.columns.tolist()

    encoded = pd.concat(encoded_parts, axis=1)
    if encoded.isna().any().any():
        raise ValueError("Feature encoding unexpectedly produced missing values.")
    return encoded, encoded_groups


def fit_engagement_model(
    data: pd.DataFrame,
) -> pd.Series:
    """Fit a random forest and aggregate one-hot importances by source feature."""
    recent = data[data["Year"].between(RECENT_YEAR_MIN, YEAR_MAX)].copy()
    if recent.empty:
        raise ValueError(f"No survey rows are available from {RECENT_YEAR_MIN} onward.")

    target, target_name = engagement_target(recent)
    labelled = recent.loc[target.notna(), MODEL_FEATURES + ["Year"]].copy()
    y = target.loc[target.notna()].astype(int)
    if y.nunique() != 2:
        raise ValueError("The engagement target must contain both binary classes.")

    labelled_years = sorted(labelled["Year"].unique().tolist())
    LOGGER.info(
        "Training engagement model for '%s' on %s labelled responses from year(s): %s",
        target_name,
        len(labelled),
        ", ".join(map(str, labelled_years)),
    )

    features, groups = encode_model_features(labelled[MODEL_FEATURES])
    model = RandomForestClassifier(
        n_estimators=100,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        class_weight="balanced",
    )
    model.fit(features, y)

    encoded_importance = pd.Series(model.feature_importances_, index=features.columns)
    grouped_importance = pd.Series(
        {
            feature: float(encoded_importance.reindex(columns, fill_value=0).sum())
            for feature, columns in groups.items()
        },
        name="importance",
    )
    total = grouped_importance.sum()
    if total > 0:
        grouped_importance /= total
    return grouped_importance.sort_values()


def plot_feature_importance(
    importances: pd.Series,
    output_path: Path,
) -> None:
    """Plot grouped random-forest feature importances."""
    labels = [FEATURE_LABELS.get(feature, feature) for feature in importances.index]

    fig, axis = plt.subplots(figsize=(13, 8))
    bars = axis.barh(
        labels,
        importances.values,
        color=PRIMARY_COLOR,
        edgecolor="white",
    )
    axis.bar_label(
        bars,
        labels=[f"{value:.3f}" for value in importances.values],
        padding=5,
        fontsize=11,
    )
    upper = max(float(importances.max()) * 1.18, 0.1)
    axis.set_xlim(0, upper)
    axis.set_xlabel("Aggregated random-forest importance", fontsize=13)
    axis.set_ylabel("Predictor", fontsize=13)
    axis.tick_params(axis="both", labelsize=11)
    axis.set_title(
        "Professional experience, compensation, and education predict engagement",
        fontsize=17,
        pad=18,
        weight="semibold",
    )
    axis.spines[["top", "right", "left"]].set_visible(False)
    axis.grid(axis="y", visible=False)
    fig.tight_layout()
    fig.savefig(output_path, dpi=EXPORT_DPI, bbox_inches="tight")
    plt.close(fig)
