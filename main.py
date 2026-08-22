"""Single entry point and orchestration pipeline for the project."""

from __future__ import annotations

import logging
from datetime import datetime
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
from src.analysis.SO_analysis import (
    is_part_of_community,
    visit_over_time,
)
from src.analysis import ai_adoption, ai_nonresponse
from src.analysis.cluster_developers import run_cluster_analysis
from src.analysis.audit_dataset import audit_dataset
from src.cleaning.clean_data import clean_dataframe
from src.cleaning.data_harmonization import run_harmonization_pipeline
from src.models.community_demographics_ml import (
    build_demographic_summary,
    plot_demographic_shift,
)
from src.visualization.plot_nulls import (
    plot_null_distribution_by_year,
    plot_null_percentages,
)
from scripts.audit.generate_ai_analysis import write_ai_analysis
from scripts.audit.generate_audit import write_audit
from scripts.audit.generate_clustering import write_clustering
from scripts.audit.generate_community import write_community_audit
from scripts.audit.generate_followup import (
    write_reconciliation,
    write_rf_eval,
    write_robustness,
)
from scripts.audit.generate_proxy_bias import write_proxy_bias
from scripts.audit.regenerate_and_sweep import write_figure_sweep


PROJECT_ROOT = Path(__file__).resolve().parent
PROCESSED_DATASET = (
    PROJECT_ROOT / "data" / "processed" / "harmonized_stack_overflow_2011_2025.csv"
)
HARMONIZATION_MODULE = PROJECT_ROOT / "src" / "cleaning" / "data_harmonization.py"
CLEAN_DATA_DIRECTORY = PROJECT_ROOT / "data" / "clean"
RAW_DATA_DIRECTORY = PROJECT_ROOT / "data" / "raw"
FIGURES_DIRECTORY = PROJECT_ROOT / "outputs" / "figures"
AUDIT_DIRECTORY = PROJECT_ROOT / "outputs" / "audit"
AI_DIRECTORY = PROJECT_ROOT / "outputs" / "ai"

# Every stage name printed by run_pipeline, in order.  The list drives both
# the STAGE numbering and the "N" in "STAGE xx/N", so adding a stage cannot
# leave the two out of step.
STAGE_NAMES = (
    "load master dataset",
    "clean and audit master data",
    "prepare analysis summaries",
    "write master audit",
    "verify cohort audit values",
    "generate pipeline figures",
    "write community audit",
    "run AI adoption analysis",
    "cluster developers with k-modes",
    "write cohort reconciliation",
    "evaluate reference random forest",
    "write robustness analysis",
    "write proxy-bias audit",
    "write AI analysis audit",
    "write clustering audit",
    "verify figure freshness",
)


def _dataset_is_stale(dataset_path: Path) -> bool:
    """True if the processed dataset is missing or older than its inputs.

    This is the second time a stale, gitignored build artefact under
    data/processed has silently diverged from the code/data that generates
    it (see outputs/audit/CLUSTERING_CHECK.md for the first instance), so
    staleness is checked automatically rather than relying on the file
    merely existing.
    """
    if not dataset_path.is_file():
        return True
    dataset_mtime = dataset_path.stat().st_mtime
    if HARMONIZATION_MODULE.is_file() and HARMONIZATION_MODULE.stat().st_mtime > dataset_mtime:
        return True
    if CLEAN_DATA_DIRECTORY.is_dir():
        for cleaned_file in CLEAN_DATA_DIRECTORY.rglob("*.csv"):
            if cleaned_file.stat().st_mtime > dataset_mtime:
                return True
    return False


def load_processed_dataset(dataset_path: Path = PROCESSED_DATASET) -> pd.DataFrame:
    """Load the harmonized dataset, rebuilding it when missing or stale."""
    if _dataset_is_stale(dataset_path):
        print(
            "Processed dataset missing or stale relative to its inputs; "
            "rebuilding from data/raw.",
            flush=True,
        )
        run_harmonization_pipeline()
    if not dataset_path.is_file():
        raise FileNotFoundError(f"Processed dataset not found: {dataset_path}")
    return pd.read_csv(dataset_path, low_memory=False)


def run_pipeline(dataset_path: Path = PROCESSED_DATASET) -> dict[str, Any]:
    """Regenerate every report-referenced figure and audit artefact once."""
    run_started = datetime.now()
    stage = 0

    def report_stage(name: str) -> None:
        """Print the next stage banner, enforcing the declared stage order."""
        nonlocal stage
        if stage >= len(STAGE_NAMES) or STAGE_NAMES[stage] != name:
            expected = STAGE_NAMES[stage] if stage < len(STAGE_NAMES) else "(no further stages)"
            raise RuntimeError(
                f"Stage {stage + 1} is {name!r} but STAGE_NAMES declares {expected!r}."
            )
        stage += 1
        print(f"STAGE {stage:02d}/{len(STAGE_NAMES)}: {name}", flush=True)

    report_stage("load master dataset")
    raw_dataframe = load_processed_dataset(dataset_path)
    report_stage("clean and audit master data")
    cleaned_dataframe = clean_dataframe(raw_dataframe)
    audit_report = audit_dataset(cleaned_dataframe)

    report_stage("prepare analysis summaries")
    null_summary = summarize_null_percentages(cleaned_dataframe)
    post_corona_dataframe = prepare_post_corona_data(cleaned_dataframe)
    # The cohort figure is an audit of the harmonized master itself.  Do not
    # deduplicate it here: repeated survey responses are analytical rows, and
    # dropping them made its values disagree with AUDIT.md.
    demographic_summary = build_demographic_summary(raw_dataframe)

    FIGURES_DIRECTORY.mkdir(parents=True, exist_ok=True)
    AUDIT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    report_stage("write master audit")
    write_audit(raw_dataframe)
    report_stage("verify cohort audit values")
    audit_text = (AUDIT_DIRECTORY / "AUDIT.md").read_text(encoding="utf-8")
    for year, junior, senior in ((2017, 0.369076, 0.358792), (2018, 0.392047, 0.327715)):
        observed = demographic_summary.loc[year]
        if not (abs(observed["early_career_share"] - junior) < 5e-7 and abs(observed["senior_share"] - senior) < 5e-7):
            raise RuntimeError(f"Current master cohort summary disagrees for {year}.")
        if not any(f"| {year} |" in line and f"{junior:.6f}" in line and f"{senior:.6f}" in line for line in audit_text.splitlines()):
            raise RuntimeError(f"AUDIT.md does not contain the verified {year} cohort row.")
    report_stage("generate pipeline figures")
    plot_null_percentages(null_summary, FIGURES_DIRECTORY / "null_distribution_plot.png")
    plot_null_distribution_by_year(
        cleaned_dataframe,
        FIGURES_DIRECTORY / "null_distribution_boxplot.png",
    )
    plot_demographic_shift(
        demographic_summary,
        FIGURES_DIRECTORY / "demographic_shift_2011_2025.png",
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
    belonging_metrics = is_part_of_community(
        cleaned_dataframe,
        FIGURES_DIRECTORY / "part_of_community_2017_2025.png",
    )
    participation_metrics = visit_over_time(
        cleaned_dataframe,
        FIGURES_DIRECTORY / "visits_so_freq_2017_2025.png",
    )
    report_stage("write community audit")
    write_community_audit(cleaned_dataframe, belonging_metrics, participation_metrics)

    # The AI and clustering analyses each run once here and hand their tables
    # to the matching audit stage below, so the published figures and the
    # audit reports can never come from two different fits.
    report_stage("run AI adoption analysis")
    AI_DIRECTORY.mkdir(parents=True, exist_ok=True)
    ai_adoption_results = ai_adoption.run(RAW_DATA_DIRECTORY, AI_DIRECTORY, FIGURES_DIRECTORY)
    ai_nonresponse_results = ai_nonresponse.run(RAW_DATA_DIRECTORY, AI_DIRECTORY, FIGURES_DIRECTORY)

    report_stage("cluster developers with k-modes")
    clustering_results = run_cluster_analysis(
        raw_dataframe,
        FIGURES_DIRECTORY / "cluster_developers_heatmap.png",
    )

    report_stage("write cohort reconciliation")
    write_reconciliation(raw_dataframe)
    report_stage("evaluate reference random forest")
    write_rf_eval(raw_dataframe)
    report_stage("write robustness analysis")
    write_robustness(raw_dataframe)
    report_stage("write proxy-bias audit")
    write_proxy_bias(raw_dataframe)
    report_stage("write AI analysis audit")
    write_ai_analysis(ai_adoption_results, ai_nonresponse_results, raw_dataframe)
    report_stage("write clustering audit")
    write_clustering(clustering_results)
    report_stage("verify figure freshness")
    write_figure_sweep(run_started)

    if stage != len(STAGE_NAMES):
        raise RuntimeError(
            f"Ran {stage} stages but STAGE_NAMES declares {len(STAGE_NAMES)}."
        )

    return {
        "audit": audit_report,
        "master_rows": len(raw_dataframe),
        "null_summary": null_summary,
        "post_corona_data": post_corona_dataframe,
        "demographic_summary": demographic_summary,
        "clustering": clustering_results,
        "audit_directory": AUDIT_DIRECTORY,
        "stage_count": stage,
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
        "Completed pipeline. Master: %s rows; analysis frame: %s rows; %s columns.",
        f'{results["master_rows"]:,}',
        f'{audit_report["rows"]:,}',
        audit_report["columns"],
    )
    logging.info("Saved figures to %s and audits to %s", FIGURES_DIRECTORY.relative_to(PROJECT_ROOT), AUDIT_DIRECTORY.relative_to(PROJECT_ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
