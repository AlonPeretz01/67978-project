"""Audit tables behind every AI adoption figure and every Section 5 number."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.analysis.ai_adoption import AGE_ORDER, COHORT_ORDER, YEAR_CONFIG


OUTPUT_PATH = ROOT / "outputs" / "audit" / "AI_ANALYSIS.md"


def markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    return "\n".join([
        "| " + " | ".join(map(str, headers)) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
        *("| " + " | ".join(map(str, row)) + " |" for row in rows),
    ])


def _pct(value: object) -> str:
    if value is None or pd.isna(value):
        return "NOT AVAILABLE: no valid responses"
    return f"{float(value) * 100:.2f}%"


def _ci(low: object, high: object) -> str:
    if pd.isna(low) or pd.isna(high):
        return "NOT AVAILABLE: no valid responses"
    return f"[{float(low) * 100:.2f}%, {float(high) * 100:.2f}%]"


def community_overlap(master: pd.DataFrame, years: list[int]) -> pd.DataFrame:
    """Rows answering the AI question that also answered `Part_of_community`.

    Section 5 reads the AI result against the community-sentiment result, so
    the size of the set carrying both answers bounds any joint claim.
    """
    rows = []
    year_series = pd.to_numeric(master["Year"], errors="coerce")
    for year in years:
        subset = master[year_series == year]
        if subset.empty:
            rows.append([year, 0, 0, 0, 0, "NOT AVAILABLE: year absent from master"])
            continue
        ai_answered = subset["AI_Usage_Status"].notna()
        community_answered = subset["Part_of_community"].notna()
        both = int((ai_answered & community_answered).sum())
        rows.append([
            year,
            len(subset),
            int(ai_answered.sum()),
            int(community_answered.sum()),
            both,
            f"{both / len(subset) * 100:.2f}%",
        ])
    return pd.DataFrame(
        rows,
        columns=["Year", "rows", "AI_Usage_Status non-null", "Part_of_community non-null", "both non-null", "both as share of year"],
    )


def write_ai_analysis(
    adoption: dict,
    nonresponse: dict,
    master: pd.DataFrame,
    output_path: Path = OUTPUT_PATH,
) -> Path:
    """Write the tables behind the five AI figures.

    Takes the results of the AI analysis stage rather than recomputing them,
    so the report and the figures are guaranteed to come from one pass over
    the raw files.
    """
    summary = adoption["summary"]
    seniority = adoption["seniority"]
    by_age = adoption["age"]
    composition = adoption["composition"]
    bounds = nonresponse["bounds"]
    rr_age = nonresponse["by_age"]
    rr_seniority = nonresponse["by_sen"]
    years = sorted(int(year) for year in summary["Year"])

    content = "# AI adoption analysis — audit tables\n\n"
    content += (
        "Every number quoted in Section 5 of the report is reproduced here from "
        "the same pass over the raw survey files that drew the figures. "
        "Adopter is defined as an `AISelect` answer whose text starts with "
        "\"Yes\", which harmonizes the 2025 daily/weekly/monthly split against the "
        "single \"Yes\" used in 2023 and 2024; §1 lists every raw answer so that "
        "rule is checkable. All intervals are Wilson score 95% intervals.\n\n"
    )

    content += "## 0. Source columns per year\n\n"
    content += (
        "The AI questions are not identical across years, so each year is read "
        "from its own raw column names.\n\n"
    )
    content += markdown_table(
        ["Year", "Raw file", "AI_Usage_Status source", "AI_Tool_Usage source", "Experience source", "Experience is proxy"],
        [
            [
                year,
                f"`data/raw/{year}/survey_results_public.csv`",
                f"`{YEAR_CONFIG[year]['ai_status']}`",
                f"`{YEAR_CONFIG[year]['ai_tool']}`" if YEAR_CONFIG[year]["ai_tool"] else "NOT AVAILABLE: restructured in 2025, no comparable column",
                f"`{YEAR_CONFIG[year]['experience']}`",
                "YES" if YEAR_CONFIG[year]["experience_is_proxy"] else "no",
            ]
            for year in years
        ],
    )

    content += "\n\n## 1. Raw value inventory\n\n"
    content += (
        "Every distinct raw answer with its count, per year. `(null)` is listed "
        "explicitly so each year's counts sum to that year's respondent total.\n\n"
    )
    status_inventory = adoption["status_inventory"]
    content += "### 1.1 `AI_Usage_Status` — every raw answer\n\n"
    content += markdown_table(
        ["Year", "Raw value", "Count", "Share of year"],
        [
            [int(r.Year), f"`{r.raw_value}`", f"{int(r['count']):,}", f"{r.share_of_year * 100:.2f}%"]
            for _, r in status_inventory.iterrows()
        ],
    )
    status_totals = status_inventory.groupby("Year")["count"].sum()
    content += "\n\nCounts sum to the respondent total in every year: " + "; ".join(
        f"{int(year)}: {int(total):,}" for year, total in status_totals.items()
    ) + ".\n\n"

    tool_inventory = adoption["tool_inventory"]
    tool_options = adoption["tool_option_inventory"]
    combination_counts = (
        tool_inventory[tool_inventory["raw_value"] != "(null)"].groupby("Year").size()
    )
    content += "### 1.2 `AI_Tool_Usage` — per-option counts\n\n"
    content += (
        "`AI_Tool_Usage` is a multi-select: each raw answer is a "
        "semicolon-joined list of options, which yields "
        + "; ".join(f"{int(year)}: {int(n):,}" for year, n in combination_counts.items())
        + " distinct answer combinations. The per-option counts below are the "
        "readable form; **every distinct raw combination is listed in full in "
        "Appendix A**. Options do not sum to the respondent total, because one "
        "respondent may select several.\n\n"
    )
    if tool_options.empty:
        content += "NOT AVAILABLE: no year in scope carries `AI_Tool_Usage`.\n\n"
    else:
        content += markdown_table(
            ["Year", "Option", "Respondents selecting it", "Share of answerers"],
            [
                [int(r.Year), r.option, f"{int(r['count']):,}", _pct(r.share_of_answered)]
                for _, r in tool_options.iterrows()
            ],
        )
        content += "\n\n"
    absent = [year for year in years if YEAR_CONFIG[year]["ai_tool"] is None]
    if absent:
        content += (
            "`AI_Tool_Usage` is **NOT AVAILABLE** for "
            + ", ".join(str(year) for year in absent)
            + ": the question was restructured into task-level "
            "\"partially/mostly AI\" columns with no 1:1 equivalent, so it is "
            "treated as absent rather than mapped to an approximation.\n\n"
        )

    content += "## 2. Coverage and overall adoption per year\n\n"
    content += markdown_table(
        ["Year", "Respondents", "AI_Usage_Status non-null", "Coverage", "AI_Tool_Usage non-null", "Coverage", "Adopters", "Adoption rate", "95% CI"],
        [
            [
                int(r.Year),
                f"{int(r.n_total):,}",
                f"{int(r.status_nonnull):,}",
                _pct(r.status_coverage),
                f"{int(r.tool_nonnull):,}",
                _pct(r.tool_coverage),
                f"{int(r.adopters_yes):,}",
                _pct(r.adoption_rate),
                _ci(r.adoption_ci_low, r.adoption_ci_high),
            ]
            for _, r in summary.iterrows()
        ],
    )

    content += "\n\n## 3. Cross-tabulation: adoption by professional seniority\n\n"
    content += "Behind `outputs/figures/ai_adoption_by_seniority.png`.\n\n"
    content += markdown_table(
        ["Year", "Seniority", "Valid n", "Adopters", "Adoption rate", "95% CI", "Experience is proxy"],
        [
            [
                int(r.Year),
                r.Seniority,
                f"{int(r.n_valid):,}",
                f"{int(r.adopters):,}",
                _pct(r.adoption_rate),
                _ci(r.ci_low, r.ci_high),
                "YES" if r.experience_is_proxy else "no",
            ]
            for _, r in seniority.iterrows()
        ],
    )

    content += "\n\n## 4. Cross-tabulation: adoption by age band\n\n"
    content += "Behind `outputs/figures/ai_adoption_by_age.png`.\n\n"
    content += markdown_table(
        ["Year", "Age band", "Valid n", "Adopters", "Adoption rate", "95% CI"],
        [
            [
                int(r.Year),
                r.Age,
                f"{int(r.n_valid):,}",
                f"{int(r.adopters):,}",
                _pct(r.adoption_rate),
                _ci(r.ci_low, r.ci_high),
            ]
            for _, r in by_age.iterrows()
        ],
    )

    content += "\n\n## 5. AISelect status composition\n\n"
    content += (
        "Behind `outputs/figures/ai_status_composition.png`. Shares are of "
        "non-null responses, so each row sums to 100%.\n\n"
    )
    content += markdown_table(
        ["Year", *composition.columns],
        [[int(year), *(_pct(v) for v in row.values)] for year, row in composition.iterrows()],
    )

    content += "\n\n## 6. Who answered the AI question (non-response)\n\n"
    content += (
        "Behind `outputs/figures/ai_response_rate_by_seniority.png` and "
        "`outputs/figures/ai_response_rate_by_age.png`. Coverage of `AISelect` "
        "falls sharply by 2025, so adoption measured among answerers is only "
        "unbiased if non-responders resemble responders.\n\n"
    )
    content += "### 6.1 Manski bounds on overall adoption\n\n"
    content += (
        "`lower` assumes every non-responder is a non-adopter, `upper` assumes "
        "every non-responder is an adopter. The true value must lie inside the "
        "band; its width is the maximum amount missingness could move the "
        "headline number.\n\n"
    )
    content += markdown_table(
        ["Year", "Respondents", "Answered", "Coverage", "Observed adoption", "Lower bound", "Upper bound", "Band width"],
        [
            [
                int(r.Year),
                f"{int(r.n_total):,}",
                f"{int(r.answered):,}",
                _pct(r.coverage),
                _pct(r.observed_adoption),
                _pct(r.lower_bound),
                _pct(r.upper_bound),
                _pct(r.bound_width),
            ]
            for _, r in bounds.iterrows()
        ],
    )

    for title, frame, order in (
        ("6.2 Response rate by seniority", rr_seniority, COHORT_ORDER),
        ("6.3 Response rate by age band", rr_age, AGE_ORDER),
    ):
        content += f"\n\n### {title}\n\n"
        content += markdown_table(
            ["Year", "Category", "Respondents", "Answered", "Response rate"],
            [
                [int(r.Year), r.category, f"{int(r.n):,}", f"{int(r.answered):,}", _pct(r.response_rate)]
                for _, r in frame.set_index("category").loc[order].reset_index().iterrows()
            ],
        )

    content += "\n\n## 7. Overlap with the community question\n\n"
    content += (
        "Section 5 reads the AI result alongside the community-sentiment result. "
        "Both answers exist only on the intersection below, which bounds any "
        "joint claim about the two. Counts come from the harmonized master.\n\n"
    )
    overlap = community_overlap(master, years)
    content += markdown_table(
        list(overlap.columns),
        [
            [
                int(r.Year),
                f"{int(r['rows']):,}",
                f"{int(r['AI_Usage_Status non-null']):,}",
                f"{int(r['Part_of_community non-null']):,}",
                f"{int(r['both non-null']):,}",
                r["both as share of year"],
            ]
            for _, r in overlap.iterrows()
        ],
    )
    content += "\n\n"

    content += "## Appendix A. `AI_Tool_Usage` — every raw answer combination\n\n"
    content += (
        "The complete inventory promised in §1.2, one row per distinct raw "
        "answer, so any per-option count above can be re-derived. `(null)` is "
        "listed explicitly, so counts sum to the respondent total in every "
        "year.\n\n"
    )
    content += markdown_table(
        ["Year", "Raw value", "Count", "Share of year"],
        [
            [int(r.Year), f"`{r.raw_value}`", f"{int(r['count']):,}", f"{r.share_of_year * 100:.2f}%"]
            for _, r in tool_inventory.iterrows()
        ],
    )
    tool_totals = tool_inventory.groupby("Year")["count"].sum()
    content += "\n\nCounts sum to the respondent total in every year: " + "; ".join(
        f"{int(year)}: {int(total):,}" for year, total in tool_totals.items()
    ) + ".\n"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    return output_path


def main() -> None:
    from src.analysis import ai_adoption, ai_nonresponse

    raw_dir = ai_adoption.default_raw_dir(ROOT)
    ai_dir = ROOT / "outputs" / "ai"
    fig_dir = ROOT / "outputs" / "figures"
    master = pd.read_csv(
        ROOT / "data" / "processed" / "harmonized_stack_overflow_2011_2025.csv",
        low_memory=False,
    )
    adoption = ai_adoption.run(raw_dir, ai_dir, fig_dir)
    nonresponse = ai_nonresponse.run(raw_dir, ai_dir, fig_dir)
    print(f"Wrote {write_ai_analysis(adoption, nonresponse, master)}")


if __name__ == "__main__":
    main()
