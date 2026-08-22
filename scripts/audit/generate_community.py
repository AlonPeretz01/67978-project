"""Write the audit tables behind the community and participation figures."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts.audit.generate_audit import markdown_table, proportion, wilson_interval
from src.analysis.SO_analysis import VISIT_INCLUDED, VISIT_YEAR_RANGE, YEAR_RANGE


OUTPUT_PATH = Path(__file__).resolve().parents[2] / "outputs" / "audit" / "COMMUNITY.md"


def _figure_responses(data: pd.DataFrame, column: str, years: list[int]) -> pd.DataFrame:
    """Apply the response inclusion rule used by the existing figure functions."""
    subset = data.copy()
    subset["Year"] = pd.to_numeric(subset["Year"], errors="coerce")
    subset = subset.loc[subset["Year"].isin(years)].copy()
    subset["_answer"] = subset[column].astype("string").str.strip()
    return subset


def _metric_row(metrics: pd.DataFrame, year: int) -> pd.Series:
    """Return one returned figure-metric row, retaining its exact shares."""
    return metrics.loc[metrics["Year"].eq(year)].iloc[0]


def _count_from_figure_share(metric_row: pd.Series, share_column: str) -> int:
    """Recover the integer boolean count represented by a figure's mean share."""
    return int(round(float(metric_row[share_column]) * int(metric_row["n_responses"])))


def _belonging_tables(data: pd.DataFrame, metrics: pd.DataFrame) -> tuple[str, str]:
    answers = _figure_responses(data, "Part_of_community", YEAR_RANGE)
    summary_rows: list[list[object]] = []
    mapping_rows: list[list[object]] = []

    for year in YEAR_RANGE:
        annual = answers.loc[answers["Year"].eq(year)]
        answered = annual.loc[annual["_answer"].notna() & annual["_answer"].ne("")]
        metric = _metric_row(metrics, year)
        n_answered = int(metric["n_responses"])
        if n_answered != len(answered):
            raise RuntimeError(f"Belonging audit response count disagrees with the {year} figure.")

        yes = answered["_answer"].str.contains(r"yes|(?<!dis)agree", case=False, na=False, regex=True)
        no = answered["_answer"].str.contains(r"no|disagree", case=False, na=False, regex=True)
        yes_count = _count_from_figure_share(metric, "yes_share")
        no_count = _count_from_figure_share(metric, "no_share")
        if yes_count != int(yes.sum()) or no_count != int(no.sum()):
            raise RuntimeError(f"Belonging audit categories disagree with the {year} figure.")
        excluded_count = int((~yes & ~no).sum())
        yes_ci = wilson_interval(yes_count, n_answered)
        no_ci = wilson_interval(no_count, n_answered)
        excluded_ci = wilson_interval(excluded_count, n_answered)
        n_total = len(annual)

        summary_rows.append([
            year, n_answered, n_total, proportion(1 - n_answered / n_total),
            yes_count, proportion(float(metric["yes_share"])), f"[{proportion(yes_ci[0])}, {proportion(yes_ci[1])}]",
            no_count, proportion(float(metric["no_share"])), f"[{proportion(no_ci[0])}, {proportion(no_ci[1])}]",
            excluded_count, proportion(excluded_count / n_answered), f"[{proportion(excluded_ci[0])}, {proportion(excluded_ci[1])}]",
        ])

        for answer, count in answered["_answer"].value_counts().sort_index().items():
            answer_yes = bool(pd.Series([answer], dtype="string").str.contains(r"yes|(?<!dis)agree", case=False, na=False, regex=True).iloc[0])
            answer_no = bool(pd.Series([answer], dtype="string").str.contains(r"no|disagree", case=False, na=False, regex=True).iloc[0])
            if answer_yes and answer_no:
                mapped = "yes/agree and no/disagree (counted in both figure lines)"
            elif answer_yes:
                mapped = "yes/agree"
            elif answer_no:
                mapped = "no/disagree"
            else:
                mapped = "excluded (neither yes/agree nor no/disagree)"
            mapping_rows.append([year, answer, int(count), mapped])
        nonresponse = n_total - n_answered
        if nonresponse:
            mapping_rows.append([year, "<NULL or blank>", nonresponse, "non-response (excluded before figure calculation)"])

    summary = markdown_table(
        ["Year", "n answered", "n total", "non-response rate", "yes/agree count", "yes/agree share", "yes/agree Wilson 95% CI", "no/disagree count", "no/disagree share", "no/disagree Wilson 95% CI", "excluded count", "excluded share", "excluded Wilson 95% CI"],
        summary_rows,
    )
    mappings = markdown_table(["Year", "Raw response category", "Count", "Mapped figure value"], mapping_rows)
    return summary, mappings


def _participation_tables(data: pd.DataFrame, metrics: pd.DataFrame) -> tuple[str, str]:
    answers = _figure_responses(data, "Participates_in_questions", VISIT_YEAR_RANGE)
    summary_rows: list[list[object]] = []
    mapping_rows: list[list[object]] = []

    for year in VISIT_YEAR_RANGE:
        annual = answers.loc[answers["Year"].eq(year)]
        answered = annual.loc[annual["_answer"].notna() & annual["_answer"].ne("")]
        metric = _metric_row(metrics, year)
        n_answered = int(metric["n_responses"])
        if n_answered != len(answered):
            raise RuntimeError(f"Participation audit response count disagrees with the {year} figure.")

        frequent_count = _count_from_figure_share(metric, "frequent_visit_share")
        if frequent_count != int(answered["_answer"].isin(VISIT_INCLUDED).sum()):
            raise RuntimeError(f"Participation audit categories disagree with the {year} figure.")
        frequent_ci = wilson_interval(frequent_count, n_answered)
        n_total = len(annual)
        summary_rows.append([
            year, n_answered, n_total, proportion(1 - n_answered / n_total),
            frequent_count, proportion(float(metric["frequent_visit_share"])),
            f"[{proportion(frequent_ci[0])}, {proportion(frequent_ci[1])}]",
        ])

        for answer, count in answered["_answer"].value_counts().sort_index().items():
            mapped = "frequent (at least a few times per month)" if answer in VISIT_INCLUDED else "infrequent"
            mapping_rows.append([year, answer, int(count), mapped])
        nonresponse = n_total - n_answered
        if nonresponse:
            mapping_rows.append([year, "<NULL or blank>", nonresponse, "non-response (excluded before figure calculation)"])

    summary = markdown_table(
        ["Year", "n answered", "n total", "non-response rate", "frequent count", "frequent share", "frequent Wilson 95% CI"],
        summary_rows,
    )
    mappings = markdown_table(["Year", "Raw response category", "Count", "Mapped figure value"], mapping_rows)
    return summary, mappings


def write_community_audit(
    data: pd.DataFrame,
    belonging_metrics: pd.DataFrame,
    participation_metrics: pd.DataFrame,
    output_path: Path = OUTPUT_PATH,
) -> None:
    """Persist the already-computed figure shares with coverage and provenance."""
    belonging, belonging_mapping = _belonging_tables(data, belonging_metrics)
    participation, participation_mapping = _participation_tables(data, participation_metrics)
    content = (
        "# Community and participation figure audit\n\n"
        "The share columns below are the exact metric tables returned by the two existing figure functions. "
        "Wilson 95% confidence intervals use `wilson_interval` from `scripts.audit.generate_audit`. "
        "Response categories are shown after the whitespace trim used by the figures.\n\n"
        "## Belonging, 2017-2025\n\n" + belonging + "\n\n"
        "## Participation at least a few times per month, 2019-2025\n\n" + participation + "\n\n"
        "## Belonging raw-category mapping\n\n" + belonging_mapping + "\n\n"
        "## Participation raw-category mapping\n\n" + participation_mapping + "\n"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
