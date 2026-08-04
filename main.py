"""Single entry point and orchestration pipeline for the project."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd

from src.analysis.analyze_nulls import summarize_null_percentages
from src.analysis.analyze_post_corona import (
    AGE_BINS_ORDER,
    PARTICIPATION_ORDER,
    plot_age_participation_stacked,
    plot_compare_answer_with_column,
    plot_fulltime_participation,
    plot_stacked_by_columns,
    prepare_post_corona_data,
)
from src.analysis.audit_dataset import audit_dataset
from src.analysis.structural_break import (
    analyze_theoretical_slope_changes,
    format_sensitivity_table,
)
from src.cleaning.clean_data import clean_dataframe
from src.models.community_demographics_ml import (
    build_demographic_summary,
    fit_engagement_model,
    plot_demographic_shift,
    plot_feature_importance,
)
from src.visualization.plot_nulls import plot_null_percentages


PROJECT_ROOT = Path(__file__).resolve().parent
PROCESSED_DATASET = (
    PROJECT_ROOT / "data" / "processed" / "harmonized_stack_overflow_2011_2025.csv"
)
FIGURES_DIRECTORY = PROJECT_ROOT / "outputs" / "figures"


def load_processed_dataset(dataset_path: Path = PROCESSED_DATASET) -> pd.DataFrame:
    """Load the single harmonized dataset used by the project pipeline."""
    if not dataset_path.is_file():
        raise FileNotFoundError(f"Processed dataset not found: {dataset_path}")
    return pd.read_csv(dataset_path, low_memory=False)


def run_pipeline(dataset_path: Path = PROCESSED_DATASET) -> dict[str, Any]:
    """Run cleaning, audit, analysis, modelling, and figure generation once."""
    raw_dataframe = load_processed_dataset(dataset_path)
    cleaned_dataframe = clean_dataframe(raw_dataframe)
    audit_report = audit_dataset(cleaned_dataframe)

    null_summary = summarize_null_percentages(cleaned_dataframe)
    post_corona_dataframe = prepare_post_corona_data(cleaned_dataframe)
    demographic_summary = build_demographic_summary(cleaned_dataframe)
    model_importances = fit_engagement_model(cleaned_dataframe)

    FIGURES_DIRECTORY.mkdir(parents=True, exist_ok=True)
    plot_null_percentages(null_summary, FIGURES_DIRECTORY / "null_distribution_plot.png")
    plot_demographic_shift(
        demographic_summary,
        FIGURES_DIRECTORY / "demographic_shift_2011_2025.png",
    )
    plot_feature_importance(
        model_importances,
        FIGURES_DIRECTORY / "feature_importance_so_engagement.png",
    )
    plot_fulltime_participation(
        post_corona_dataframe,
        FIGURES_DIRECTORY / "post_corona_fulltime_participation.png",
        employment_status="Employed full-time",
    )
    plot_age_participation_stacked(
        post_corona_dataframe,
        FIGURES_DIRECTORY / "post_corona_age_participation.png",
    )
    plot_compare_answer_with_column(
        post_corona_dataframe,
        FIGURES_DIRECTORY / "post_corona_fulltime_participation_distribution.png",
        columnA="Employment_Status",
        answerA="Employed full-time",
        columnB="Participates_in_questions",
    )
    plot_stacked_by_columns(
        post_corona_dataframe,
        FIGURES_DIRECTORY / "post_corona_participation_by_age.png",
        columnA="Participates_in_questions",
        columnB="Age",
        orderA=PARTICIPATION_ORDER,
        orderB=AGE_BINS_ORDER,
    )

    structural_break_input = (
        demographic_summary.reset_index()
        .rename(columns={"Year": "Survey_Year", "early_career_share": "Junior_Proportion"})
        .loc[:, ["Survey_Year", "Junior_Proportion"]]
        .dropna()
    )
    structural_break_results, break_figures = analyze_theoretical_slope_changes(
        structural_break_input,
        metric_columns=["Junior_Proportion"],
        output_directory=FIGURES_DIRECTORY,
    )

    return {
        "audit": audit_report,
        "null_summary": null_summary,
        "post_corona_data": post_corona_dataframe,
        "demographic_summary": demographic_summary,
        "model_importances": model_importances,
        "structural_break_results": structural_break_results,
        "structural_break_figures": break_figures,
    }


def main() -> int:
    """Run the full project pipeline and report the primary outcomes."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        results = run_pipeline()
    except (FileNotFoundError, ValueError, RuntimeError, KeyError) as error:
        logging.error("Pipeline failed: %s", error)
        return 1

    audit_report = results["audit"]
    logging.info(
        "Completed pipeline for %s rows and %s columns.",
        audit_report["rows"],
        audit_report["columns"],
    )
    sensitivity_table = format_sensitivity_table(results["structural_break_results"])
    logging.info(
        "Piecewise-regression sensitivity analysis:\n%s",
        sensitivity_table.to_string(index=False),
    )
    logging.info("Saved figures to %s", FIGURES_DIRECTORY.relative_to(PROJECT_ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
