"""Generate a read-only, reproducible audit of the project data and analyses.

Run from the repository root with ``python -m scripts.audit.generate_audit``.  The
script reads the existing processed and cleaned files and writes AUDIT.md; it
does not alter the project pipeline or any source data.
"""

from __future__ import annotations

import inspect
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.analysis import structural_break  # noqa: E402
from src.cleaning.data_harmonization import TARGET_COLUMNS, schema_mapping  # noqa: E402
from src.models import community_demographics_ml as demographics  # noqa: E402
from src.reference import engagement_random_forest as rf  # noqa: E402


MASTER_PATH = ROOT / "data" / "processed" / "harmonized_stack_overflow_2011_2025.csv"
CLEAN_DIRECTORY = ROOT / "data" / "clean"
OUTPUT_PATH = ROOT / "outputs" / "audit" / "AUDIT.md"
YEARS = list(range(2011, 2026))
Z_95 = 1.959963984540054

# UN M49 Western Europe. The classification is stated here because the project
# has no country-region lookup or definition of "Western Europe".
WESTERN_EUROPE = {
    "austria", "belgium", "france", "germany", "liechtenstein", "luxembourg",
    "monaco", "netherlands", "switzerland",
}
NORTH_AMERICA = {"united states", "united states of america", "usa", "canada"}


def markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    """Render a small Markdown table without external formatting dependencies."""
    def cell(value: object) -> str:
        return str(value).replace("|", "\\|").replace("\n", " ")

    lines = ["| " + " | ".join(map(cell, headers)) + " |"]
    lines.append("| " + " | ".join("---" for _ in headers) + " |")
    lines.extend("| " + " | ".join(map(cell, row)) + " |" for row in rows)
    return "\n".join(lines)


def proportion(value: float) -> str:
    return "NOT AVAILABLE" if pd.isna(value) else f"{value:.6f}"


def wilson_interval(successes: float, total: int) -> tuple[float, float]:
    """Wilson 95% interval, accepting fractional cohort allocations."""
    if total <= 0 or not np.isfinite(successes):
        return np.nan, np.nan
    p = successes / total
    denominator = 1 + Z_95**2 / total
    centre = (p + Z_95**2 / (2 * total)) / denominator
    half_width = Z_95 * math.sqrt((p * (1 - p) + Z_95**2 / (4 * total)) / total) / denominator
    return centre - half_width, centre + half_width


def source_columns_used(year: int, target: str, columns: pd.Index) -> list[str]:
    """Replicate harmonize_schema's source-column selection exactly."""
    mapping = schema_mapping.get(str(year), {})
    found = [source for source, mapped in mapping.items() if mapped == target and source in columns]
    if target in columns and target not in found:
        found.insert(0, target)
    return found


def clean_year(year: int) -> tuple[pd.DataFrame | None, str | None]:
    paths = sorted((CLEAN_DIRECTORY / str(year)).glob("*.csv"))
    if not paths:
        return None, f"NOT AVAILABLE: cleaned file for {year} was not found"
    try:
        return pd.read_csv(paths[0], low_memory=False), None
    except UnicodeDecodeError:
        return pd.read_csv(paths[0], low_memory=False, encoding="latin1"), None


def value_counts_markdown(series: pd.Series) -> str:
    counts = series.value_counts(dropna=False)
    rows = [["<NULL>" if pd.isna(key) else repr(key), int(value)] for key, value in counts.items()]
    return markdown_table(["Raw source value", "Count"], rows)


def cohort_section(master: pd.DataFrame, flags: list[str]) -> str:
    rows: list[list[object]] = []
    junior_exceeds: list[int] = []
    for year in YEARS:
        annual = master.loc[master["Year"] == year, "Years_of_Experience"]
        n_total = len(annual)
        weights = annual.map(demographics.experience_cohort_weights)
        usable = weights.map(
            lambda result: isinstance(result, tuple) and all(pd.notna(value) for value in result)
        ).to_numpy()
        valid = weights[usable]
        n_valid = len(valid)
        if n_valid:
            allocation = np.asarray(valid.tolist(), dtype=float).sum(axis=0)
            shares = allocation / n_valid
            intervals = [wilson_interval(count, n_valid) for count in allocation]
            exceeds = bool(shares[0] > shares[2])
            if exceeds:
                junior_exceeds.append(year)
            summed = float(sum(shares))
            if not np.isclose(summed, 1.0, atol=1e-6):
                flags.append(f"{year}: cohort proportions sum to {summed:.12f}, not 1.0.")
            output = [
                year, n_total, n_valid,
                f"{allocation[0]:.6f}", proportion(shares[0]), f"[{proportion(intervals[0][0])}, {proportion(intervals[0][1])}]",
                f"{allocation[1]:.6f}", proportion(shares[1]), f"[{proportion(intervals[1][0])}, {proportion(intervals[1][1])}]",
                f"{allocation[2]:.6f}", proportion(shares[2]), f"[{proportion(intervals[2][0])}, {proportion(intervals[2][1])}]",
                "YES" if exceeds else "NO",
            ]
        else:
            output = [year, n_total, 0] + ["NOT AVAILABLE"] * 9 + ["NOT AVAILABLE"]
        rows.append(output)

    headers = [
        "Year", "n_total", "n_with_valid_experience",
        "junior count", "junior proportion", "junior Wilson 95% CI",
        "mid count", "mid proportion", "mid Wilson 95% CI",
        "senior count", "senior proportion", "senior Wilson 95% CI",
        "junior > senior?",
    ]
    source = inspect.getsource(demographics.experience_cohort_weights).rstrip()
    years_text = ", ".join(map(str, junior_exceeds)) if junior_exceeds else "NONE"
    return (
        "## EXPERIENCE COHORTS\n\n"
        "Counts may be fractional because the existing cohort function allocates ranges across integer years. "
        "`n_with_valid_experience` means parsable by that function, which can be lower than non-null source values. "
        "Wilson intervals use the fractional allocated count and the number of parsable responses.\n\n"
        "```python\n" + source + "\n```\n\n" + markdown_table(headers, rows)
        + f"\n\nYears where junior_proportion > senior_proportion: **{years_text}**\n"
    )


def provenance_section(master: pd.DataFrame) -> str:
    parts = ["## 2015 / 2016 PROVENANCE\n"]
    for year in (2015, 2016):
        cleaned, error = clean_year(year)
        parts.append(f"### {year}\n")
        if error or cleaned is None:
            parts.append((error or "NOT AVAILABLE") + "\n")
            continue
        sources = source_columns_used(year, "Years_of_Experience", cleaned.columns)
        parts.append(f"Exact source column(s) used: `{', '.join(sources) if sources else 'NONE'}`.\n\n")
        parts.append("Exact configured mapping dict:\n\n```python\n" + repr(schema_mapping[str(year)]) + "\n```\n\n")
        parts.append(f"Non-null `Years_of_Experience` values in master: **{int(master.loc[master['Year'] == year, 'Years_of_Experience'].notna().sum())}**.\n\n")
        if sources:
            parts.append("Raw distribution in the cleaned source file actually used by harmonization:\n\n")
            parts.append(value_counts_markdown(cleaned[sources[0]]) + "\n\n")
        else:
            parts.append("NOT AVAILABLE: configured source column was absent from the cleaned input.\n\n")
    return "".join(parts)


def model_section(master: pd.DataFrame, flags: list[str]) -> str:
    recent = master.loc[master["Year"].between(rf.RECENT_YEAR_MIN, demographics.YEAR_MAX)].copy()
    try:
        target, target_name = rf.engagement_target(recent)
    except ValueError as error:
        return "## RANDOM FOREST MODEL\n\nNOT AVAILABLE: " + str(error) + "\n"

    labelled = recent.loc[target.notna(), rf.MODEL_FEATURES + ["Year"]].copy()
    y = target.loc[target.notna()].astype(int)
    features, groups = rf.encode_model_features(labelled[rf.MODEL_FEATURES])
    model = rf.RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1, class_weight="balanced")
    model.fit(features, y)
    encoded_importances = pd.Series(model.feature_importances_, index=features.columns)
    grouped = pd.Series({name: float(encoded_importances[columns].sum()) for name, columns in groups.items()})
    total = float(grouped.sum())
    if not np.isclose(total, 1.0, atol=1e-12):
        flags.append(f"Random-forest impurity importances sum to {total:.12f}, not 1.0.")
    class_rows = [[int(cls), int((y == cls).sum()), proportion(float((y == cls).mean()))] for cls in sorted(y.unique())]
    feature_rows = [[column, str(features[column].dtype)] for column in features.columns]
    importance_rows = [[name, f"{value:.6f}"] for name, value in grouped.items()]
    return (
        "## RANDOM FOREST MODEL\n\n"
        f"Exact target variable: **{target_name}**; source harmonized column selected by `engagement_target`: "
        "`Part_of_community` (the visit column is evaluated only as a fallback). "
        "It appears with mapped binary values in years: " + ", ".join(map(str, sorted(recent.loc[target.notna(), "Year"].unique()))) + ".\n\n"
        "Binarization source code:\n\n```python\n" + inspect.getsource(rf.engagement_target).rstrip() + "\n```\n\n"
        "Class balance:\n\n" + markdown_table(["Class", "Count", "Proportion"], class_rows) + "\n\n"
        f"Final labelled n used to fit the retained full reference model: **{len(labelled)}**. The separate reproducible stratified 70/30 held-out evaluation, including test metrics and permutation importance, is in `RF_EVAL.md`.\n\n"
        "Features actually fed to the estimator after the existing imputation/one-hot encoding:\n\n"
        + markdown_table(["Encoded feature", "dtype"], feature_rows) + "\n\n"
        "Estimator get_params():\n\n```python\n" + repr(model.get_params()) + "\n```\n\n"
        "Impurity-based `feature_importances_`, aggregated to the original source features as in the project code (sum = "
        f"{total:.6f}):\n\n" + markdown_table(["Source feature", "Importance"], importance_rows) + "\n"
    )


def regression_section(master: pd.DataFrame) -> str:
    summary = demographics.build_demographic_summary(master)
    regression_input = (summary.reset_index().rename(columns={"Year": "Survey_Year", "early_career_share": "Junior_Proportion"})
                        .loc[:, ["Survey_Year", "Junior_Proportion"]].dropna())
    rows: list[list[object]] = []
    for sample_name, sample in (("Full Dataset", regression_input), ("2014+ Truncated Sample", regression_input.query("Survey_Year >= 2014"))):
        for knot in structural_break.THEORETICAL_INTERVENTION_YEARS:
            fit = structural_break._fit_broken_stick(sample, "Survey_Year", "Junior_Proportion", knot)
            intervals = fit.conf_int()
            for parameter in fit.params.index:
                rows.append([sample_name, knot, len(sample), len(fit.params), parameter,
                             f"{fit.params[parameter]:.6f}", f"{fit.bse[parameter]:.6f}",
                             f"[{intervals.loc[parameter, 0]:.6f}, {intervals.loc[parameter, 1]:.6f}]",
                             f"{fit.pvalues[parameter]:.6g}", f"{fit.rsquared:.6f}"])
    return (
        "## PIECEWISE / STRUCTURAL BREAK REGRESSION\n\n"
        "Exact fitting-function source:\n\n```python\n" + inspect.getsource(structural_break._fit_broken_stick).rstrip() + "\n```\n\n"
        "Input is annual `Junior_Proportion` for years " + ", ".join(map(str, regression_input["Survey_Year"].astype(int)))
        + f" (n = {len(regression_input)}). Each fit has 3 estimated parameters: `const`, `time`, and `slope_change`.\n\n"
        + markdown_table(["Sample", "Break year", "n", "Parameters", "Coefficient", "Estimate", "SE", "95% CI", "p-value", "R-squared"], rows)
        + "\n\nThe reported `slope_change` p-value tests the coefficient on `max(0, year − break_year)`: a difference between post-break and pre-break slopes. "
        "The specification is continuous and has no level-shift term, so it tests neither a level shift nor a joint level-and-slope break. "
        "`slope variance 0.0011`: **NOT AVAILABLE: no statistic with that name or value is calculated in the repository.** It must not be treated as a model result without identifying its source.\n"
    )


def country_section(flags: list[str]) -> str:
    parts = ["## COUNTRY COMPOSITION\n\nCountry is not retained in the 13-column master dataset; these figures are computed from each cleaned annual input, which is the closest available respondent-level source. Percentages use all rows in that annual cleaned file as the denominator. Western Europe is operationalized as UN M49 Western Europe (Austria, Belgium, France, Germany, Liechtenstein, Luxembourg, Monaco, Netherlands, Switzerland).\n\n"]
    regional_rows: list[list[object]] = []
    for year in YEARS:
        data, error = clean_year(year)
        if error or data is None:
            regional_rows.append([year, "NOT AVAILABLE", "NOT AVAILABLE"])
            continue
        candidates = [column for column in data.columns if "country" in str(column).lower()]
        if not candidates:
            regional_rows.append([year, "NOT AVAILABLE", "NOT AVAILABLE"])
            continue
        column = candidates[0]
        total = len(data)
        counts = data[column].value_counts(dropna=True).head(10)
        parts.append(f"### {year} (source column: `{column}`; n = {total})\n\n")
        parts.append(markdown_table(["Country", "Respondents", "Proportion"], [[country, int(count), proportion(count / total)] for country, count in counts.items()]) + "\n\n")
        normalised = data[column].astype("string").str.strip().str.lower()
        regional_count = int(normalised.isin(WESTERN_EUROPE | NORTH_AMERICA).sum())
        regional_rows.append([year, regional_count, proportion(regional_count / total)])
    parts.append("US + Canada + Western Europe:\n\n")
    parts.append(markdown_table(["Year", "Respondents", "Proportion"], regional_rows) + "\n")
    return "".join(parts)


def survey_2025_section(master: pd.DataFrame) -> str:
    present = bool((master["Year"] == 2025).any())
    if not present:
        return "## 2025 SURVEY\n\nIs the 2025 file loaded into the master dataset? **NO**.\n"
    data, error = clean_year(2025)
    non_null = [column for column in TARGET_COLUMNS if master.loc[master["Year"] == 2025, column].notna().any()]
    expected = [
        source for source, target in schema_mapping["2025"].items()
        if target == "Years_of_Experience"
    ]
    source_info = ", ".join(expected) or "NONE"
    actual = "NOT AVAILABLE" if error or data is None else ", ".join([column for column in data.columns if "yearscode" in str(column).lower() or "experience" in str(column).lower()]) or "NONE"
    return (
        "## 2025 SURVEY\n\nIs the 2025 file loaded into the master dataset? **YES**.\n\n"
        "Core variables with at least one non-null 2025 value: " + ", ".join(f"`{column}`" for column in non_null) + ".\n\n"
        f"`Years_of_Experience` is sourced from configured column(s) `{source_info}`; the cleaned 2025 input contains experience-like column(s) `{actual}`. "
        "`YearsCodePro` is genuinely absent from raw 2025, so the available `YearsCode` is used as a tagged proxy (`experience_is_proxy=True`) rather than treated as professional experience.\n"
    )


def write_audit(master: pd.DataFrame) -> Path:
    """Write AUDIT.md from the already loaded harmonized master dataset."""
    master["Year"] = pd.to_numeric(master["Year"], errors="coerce")
    flags: list[str] = []
    expected_columns = [*TARGET_COLUMNS, "experience_is_proxy"]
    if list(master.columns) != expected_columns:
        flags.append("Master dataset column order/names differ from the configured core schema plus experience_is_proxy provenance flag.")
    year_rows = [[year, int((master["Year"] == year).sum())] for year in YEARS]
    present_years = sorted(master["Year"].dropna().astype(int).unique())
    report = [
        "# Stack Overflow Survey Audit\n",
        "Generated directly from the existing harmonized master dataset and existing source code. `NOT AVAILABLE` means the current repository does not define or retain the requested quantity.\n",
        "## MASTER DATASET\n\n",
        f"Total rows: **{len(master)}**  \nTotal columns: **{master.shape[1]}**\n\n",
        "Exact column names:\n\n```text\n" + "\n".join(master.columns) + "\n```\n\n",
        "Per-year row count:\n\n" + markdown_table(["Year", "n"], year_rows) + "\n\n",
        "Years present at all: **" + ", ".join(map(str, present_years)) + "**.\n\n",
        "## FACT CHECK\n\n",
        "Per-year non-null count for every current master column (the first 13 are the original core variables; `experience_is_proxy` is the required provenance flag):\n\n",
        markdown_table(["Year", *master.columns], [[year, *[int(master.loc[master["Year"] == year, column].notna().sum()) for column in master.columns]] for year in YEARS]) + "\n\n",
        cohort_section(master, flags), "\n", provenance_section(master), "\n", model_section(master, flags), "\n",
        regression_section(master), "\n", country_section(flags), "\n", survey_2025_section(master), "\n",
        "## DISCREPANCY FLAGS\n\n",
        ("\n".join(f"- {flag}" for flag in flags) if flags else "- NONE: no internally inconsistent computed values were detected.") + "\n",
    ]
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text("".join(report), encoding="utf-8")
    return OUTPUT_PATH


def main() -> None:
    if not MASTER_PATH.is_file():
        raise FileNotFoundError(f"Master dataset not found: {MASTER_PATH}")
    print(f"Wrote {write_audit(pd.read_csv(MASTER_PATH, low_memory=False))}")


if __name__ == "__main__":
    main()
