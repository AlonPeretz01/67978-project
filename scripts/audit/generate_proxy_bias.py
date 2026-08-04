"""Quantify the raw YearsCode versus YearsCodePro measurement difference."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.models.community_demographics_ml import experience_cohort_weights, experience_to_years


def markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    return "\n".join([
        "| " + " | ".join(map(str, headers)) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
        *("| " + " | ".join(map(str, row)) + " |" for row in rows),
    ])


def junior_share(series: pd.Series) -> tuple[int, float]:
    weights = pd.DataFrame(series.map(experience_cohort_weights).tolist(), columns=["junior", "mid", "senior"])
    usable = weights.dropna()
    return len(usable), float(usable["junior"].mean()) if len(usable) else np.nan


def write_proxy_bias(master: pd.DataFrame | None = None) -> Path:
    """Write the raw-instrument proxy-bias report."""
    rows: list[list[object]] = []
    for year in range(2019, 2025):
        path = ROOT / "data" / "raw" / str(year) / "survey_results_public.csv"
        raw = pd.read_csv(path, low_memory=False)
        required = {"YearsCode", "YearsCodePro"}
        if not required.issubset(raw.columns):
            rows.append([year, "NOT AVAILABLE: source column missing", "", "", "", "", "", ""])
            continue
        total = raw["YearsCode"].map(experience_to_years)
        professional = raw["YearsCodePro"].map(experience_to_years)
        paired = total.notna() & professional.notna()
        differences = total.loc[paired] - professional.loc[paired]
        # Use exactly the same paired, parsable respondent set for both cohort
        # shares, so their difference is a measurement comparison rather than
        # a change in denominator.
        cohort_usable = pd.DataFrame({"total": total, "professional": professional}).loc[paired]
        total_n, total_junior = junior_share(cohort_usable["total"])
        professional_n, professional_junior = junior_share(cohort_usable["professional"])
        if total_n != professional_n:
            raise RuntimeError("Paired cohort denominators unexpectedly differ.")
        rows.append([
            year, int(paired.sum()), f"{differences.mean():.6f}", f"{differences.median():.6f}",
            total_n, f"{total_junior:.6f}", f"{professional_junior:.6f}",
            f"{(total_junior - professional_junior) * 100:.6f}",
        ])

    if master is None:
        master = pd.read_csv(ROOT / "data" / "processed" / "harmonized_stack_overflow_2011_2025.csv", low_memory=False)
    _, junior_2024 = junior_share(master.loc[master["Year"].eq(2024), "Years_of_Experience"])
    _, junior_2025 = junior_share(master.loc[master["Year"].eq(2025), "Years_of_Experience"])
    content = "# Proxy-experience measurement bias\n\n"
    content += "This uses the raw 2019–2024 public files, all of which contain both `YearsCode` (total coding experience) and `YearsCodePro` (professional coding experience). For the difference and both junior shares, the denominator is the same paired set of respondents with both values parsable by the project’s existing experience parser. Positive percentage-point shifts mean `YearsCode` produces a larger junior share than `YearsCodePro`.\n\n"
    content += markdown_table([
        "Year", "Paired parsable n", "Mean (YearsCode - YearsCodePro)", "Median difference",
        "Cohort n", "Junior: YearsCode", "Junior: YearsCodePro", "YearsCode - YearsCodePro (pp)",
    ], rows)
    content += f"\n\nThe observed adjacent-year change is 2024 professional-experience junior share {junior_2024:.6f} to 2025 proxy `YearsCode` junior share {junior_2025:.6f}: **{(junior_2025 - junior_2024) * 100:.6f} percentage points**. The table quantifies within-year instrument differences, but the exact fraction of that 2024→2025 change attributable to the instrument is **NOT AVAILABLE: 2025 has no `YearsCodePro`, so its counterfactual professional-experience junior share is unobserved.**\n"
    output = ROOT / "outputs" / "audit" / "PROXY_BIAS.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    return output


def main() -> None:
    print(f"Wrote {write_proxy_bias()}")


if __name__ == "__main__":
    main()
