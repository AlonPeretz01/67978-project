"""Longitudinal demographic summaries and publication-ready figures."""

from __future__ import annotations

import logging
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


YEAR_MIN = 2011
YEAR_MAX = 2025
DEMOGRAPHIC_YEAR_MAX = 2025
PROXY_EXPERIENCE_YEARS = {2015, 2016, 2025}
WILSON_Z_95 = 1.959963984540054
PRIMARY_COLOR = "#1F4E79"
SECONDARY_COLOR = "#E69F00"
TERTIARY_COLOR = "#009E73"
NEUTRAL_COLOR = "#4D4D4D"
GRID_COLOR = "#D9D9D9"
EXPORT_DPI = 200
LOGGER = logging.getLogger(__name__)


def experience_interval(value: object) -> tuple[float, float] | None:
    """Return the inclusive bounds for one harmonized experience response."""
    if pd.isna(value):
        return None
    text = str(value).strip().lower().replace("–", "-").replace("—", "-").replace("ג€“", "-").replace("ג€”", "-")
    if not text or text in {"nan", "response", "prefer not to say"}:
        return None
    found = re.search(r"(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)", text)
    if found:
        lower, upper = map(float, found.groups())
        return (lower, upper) if lower <= upper else None
    if re.fullmatch(r"2/5(?:/\d{4})?", text):
        return 2.0, 5.0
    if re.fullmatch(r"6/10(?:/\d{4})?", text):
        return 6.0, 10.0
    number = re.search(r"\d+(?:\.\d+)?", text.replace(",", ""))
    if "less than" in text or text.startswith("<"):
        upper_exclusive = float(number.group()) if number else 1.0
        return 0.0, max(0.0, upper_exclusive - 0.001)
    if not number:
        return None
    parsed = float(number.group())
    if parsed > 1000:
        try:
            date = pd.Timestamp("1899-12-30") + pd.to_timedelta(parsed, unit="D")
        except (OverflowError, ValueError):
            return None
        if (date.month, date.day) == (2, 5):
            return 2.0, 5.0
        if (date.month, date.day) == (6, 10):
            return 6.0, 10.0
        return None
    return (parsed, parsed) if 0 <= parsed <= 60 else None


def experience_to_years(value: object) -> float:
    """Convert an experience label to its numeric midpoint for RF reference use."""
    interval = experience_interval(value)
    return np.nan if interval is None else (interval[0] + interval[1]) / 2.0


def experience_cohort_weights(value: object) -> tuple[float, float, float]:
    """Allocate inclusive integer experience ranges across junior/mid/senior."""
    interval = experience_interval(value)
    if interval is None:
        return np.nan, np.nan, np.nan
    lower, upper = interval
    years = np.arange(np.ceil(lower), np.floor(upper) + 1, dtype=float)
    if years.size == 0:
        years = np.array([(lower + upper) / 2.0])
    return (
        float(np.mean(years <= 3)),
        float(np.mean((years >= 4) & (years <= 7))),
        float(np.mean(years >= 8)),
    )


def _wilson_interval(successes: float, total: int) -> tuple[float, float]:
    if total <= 0:
        return np.nan, np.nan
    share = successes / total
    denominator = 1 + WILSON_Z_95**2 / total
    centre = (share + WILSON_Z_95**2 / (2 * total)) / denominator
    half = WILSON_Z_95 * np.sqrt((share * (1 - share) + WILSON_Z_95**2 / (4 * total)) / total) / denominator
    return float(centre - half), float(centre + half)


def build_demographic_summary(data: pd.DataFrame) -> pd.DataFrame:
    """Calculate annual cohort shares directly from the harmonized master."""
    demographic = data[["Year", "Years_of_Experience"]].copy()
    lookup = {value: experience_cohort_weights(value) for value in demographic["Years_of_Experience"].dropna().unique()}
    weights = pd.DataFrame(demographic["Years_of_Experience"].map(lookup).tolist(), index=demographic.index,
                           columns=["Early_career_weight", "Mid_career_weight", "Senior_weight"])
    demographic = pd.concat([demographic, weights], axis=1).dropna(subset=["Early_career_weight"])
    demographic["experience_is_proxy"] = (data["experience_is_proxy"] if "experience_is_proxy" in data else data["Year"].isin(PROXY_EXPERIENCE_YEARS))
    summary = demographic.groupby("Year").agg(
        early_career_share=("Early_career_weight", "mean"), mid_career_share=("Mid_career_weight", "mean"), senior_share=("Senior_weight", "mean"),
        junior_allocated_count=("Early_career_weight", "sum"), mid_allocated_count=("Mid_career_weight", "sum"), senior_allocated_count=("Senior_weight", "sum"),
        valid_experience_responses=("Years_of_Experience", "size"), proxy_experience_measure=("experience_is_proxy", "any"),
    ).reindex(range(YEAR_MIN, DEMOGRAPHIC_YEAR_MAX + 1))
    summary.index.name = "Year"
    for cohort, counts in (("early_career", "junior_allocated_count"), ("mid_career", "mid_allocated_count"), ("senior", "senior_allocated_count")):
        intervals = summary.apply(lambda row: _wilson_interval(row[counts], int(row["valid_experience_responses"])) if pd.notna(row["valid_experience_responses"]) else (np.nan, np.nan), axis=1)
        summary[f"{cohort}_ci_lower"] = intervals.map(lambda item: item[0])
        summary[f"{cohort}_ci_upper"] = intervals.map(lambda item: item[1])
    fallback_years = [year for year in (2015, 2016) if year in summary.index and pd.isna(summary.loc[year, "early_career_share"])]
    if fallback_years:
        interpolated = summary[["early_career_share"]].interpolate(method="linear", limit_area="inside")
        resolved = [year for year in fallback_years if pd.notna(interpolated.loc[year, "early_career_share"])]
        summary.loc[resolved, "early_career_share"] = interpolated.loc[resolved, "early_career_share"]
        if resolved:
            LOGGER.info("Professional-experience proxies were unavailable for year(s) %s; applied linear interpolation to the aggregated Junior_Proportion series as a fallback.", ", ".join(map(str, resolved)))
    return summary


def plot_demographic_shift(summary: pd.DataFrame, output_path: Path) -> None:
    """Plot professional years as connected series and proxies as hollow points."""
    fig, axis = plt.subplots(figsize=(15, 8.5))
    summary = summary.copy()
    summary["proxy_experience_measure"] = summary.get("proxy_experience_measure", pd.Series(summary.index.isin(PROXY_EXPERIENCE_YEARS), index=summary.index)).fillna(False).astype(bool)
    display = summary.copy()
    display.loc[display["proxy_experience_measure"], ["early_career_share", "mid_career_share", "senior_share"]] = np.nan
    styles = [("early_career", SECONDARY_COLOR, "o", "Early-career / Juniors (0–3 years)", 3.5, 8, 1.0), ("senior", PRIMARY_COLOR, "s", "Seniors / Experienced (8+ years)", 3.5, 8, 1.0), ("mid_career", TERTIARY_COLOR, "D", "Mid-career (4–7 years)", 2.5, 6.5, 0.9)]
    lines, proxy_handle = [], None
    for cohort, color, marker, label, width, size, alpha in styles:
        lines.append(axis.plot(summary.index, display[f"{cohort}_share"] * 100, color=color, marker=marker, linewidth=width, markersize=size, alpha=alpha, label=label)[0])
        valid = summary.dropna(subset=[f"{cohort}_share"])
        axis.errorbar(valid.index, valid[f"{cohort}_share"] * 100, yerr=np.vstack(((valid[f"{cohort}_share"] - valid[f"{cohort}_ci_lower"]) * 100, (valid[f"{cohort}_ci_upper"] - valid[f"{cohort}_share"]) * 100)), fmt="none", ecolor=color, elinewidth=1.2, capsize=3, alpha=0.85)
        proxy = valid.loc[valid["proxy_experience_measure"]]
        if not proxy.empty:
            handle = axis.errorbar(proxy.index, proxy[f"{cohort}_share"] * 100, yerr=np.vstack(((proxy[f"{cohort}_share"] - proxy[f"{cohort}_ci_lower"]) * 100, (proxy[f"{cohort}_ci_upper"] - proxy[f"{cohort}_share"]) * 100)), color=color, marker=marker, linestyle="none", markerfacecolor="none", markeredgewidth=2, markersize=8, capsize=3, label="proxy experience measure (not comparable)" if proxy_handle is None else "_nolegend_")
            proxy_handle = proxy_handle or handle
    reference = axis.axvline(2022.5, color=NEUTRAL_COLOR, linestyle="--", linewidth=2.5, label="ChatGPT release (Nov 2022), no structural break detected", zorder=0)
    axis.set_title("Early-career share peaked in 2018 and declined from 2019", fontsize=17, pad=18, weight="semibold")
    axis.set_xlabel("Survey year", fontsize=13)
    axis.set_ylabel("Survey respondents (%)", fontsize=13)
    axis.tick_params(axis="both", labelsize=11)
    axis.set_xticks(summary.index)
    axis.set_xlim(YEAR_MIN - 0.35, DEMOGRAPHIC_YEAR_MAX + 0.35)
    axis.set_ylim(0, 100)
    axis.text(2022.62, 0.97, "ChatGPT release (Nov 2022)", transform=axis.get_xaxis_transform(), fontsize=11, ha="left", va="top", color=NEUTRAL_COLOR)
    axis.grid(axis="y", color=GRID_COLOR, linewidth=0.9, alpha=0.8)
    axis.grid(axis="x", visible=False)
    axis.spines[["top", "right"]].set_visible(False)
    axis.legend(handles=[*lines, *([proxy_handle] if proxy_handle else []), reference], loc="upper left", fontsize=11, frameon=False)
    fig.text(0.5, 0.025, "Hollow markers use non-professional experience measures (2015, 2016, 2025) and are not comparable to the connected series.", ha="center", va="bottom", fontsize=10.5, color=NEUTRAL_COLOR, style="italic")
    fig.tight_layout(rect=(0, 0.065, 1, 1))
    fig.savefig(output_path, dpi=EXPORT_DPI, bbox_inches="tight")
    plt.close(fig)
