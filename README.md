# Stack Overflow Annual Developer Survey analysis

This project analyzes the Stack Overflow Annual Developer Survey from 2011 through 2025. It examines whether the composition of survey respondents shifted with the arrival of LLM coding assistants. The pipeline harmonizes the annual responses, audits the resulting master dataset, and generates figures and audit reports.

## Getting the data

The raw survey files are too large for Git and are excluded from this repository. Download each year's public response CSV from the official [Stack Overflow Annual Developer Survey archive](https://survey.stackoverflow.co/), then place or rename it to the canonical path below; the archive URL was verified on 2026-08-04.

```text
data/raw/2011/survey_results_public.csv
data/raw/2012/survey_results_public.csv
data/raw/2013/survey_results_public.csv
data/raw/2014/survey_results_public.csv
data/raw/2015/survey_results_public.csv
data/raw/2016/survey_results_public.csv
data/raw/2017/survey_results_public.csv
data/raw/2018/survey_results_public.csv
data/raw/2019/survey_results_public.csv
data/raw/2020/survey_results_public.csv
data/raw/2021/survey_results_public.csv
data/raw/2022/survey_results_public.csv
data/raw/2023/survey_results_public.csv
data/raw/2024/survey_results_public.csv
data/raw/2025/survey_results_public.csv
```

`src/cleaning/clean_data.py` checks that exact canonical filename first. It can also fall back to the first CSV found recursively in the year's directory, excluding filenames containing `schema`, `crosswalk`, or `question`; use the tree above to avoid relying on that fallback. `scripts/audit/generate_proxy_bias.py` directly requires the canonical filenames for 2019-2024, so those six files must have the names shown.

For a year whose directory contains no eligible CSV, the cleaning stage prints `Skipping <year>: no survey results CSV was found.` A missing or misnamed 2019-2024 canonical file then causes the main command to finish with `ERROR: Pipeline failed: [Errno 2] No such file or directory: '.../data/raw/<year>/survey_results_public.csv'` when it writes `PROXY_BIAS.md`. If no raw files can produce the master dataset, it instead reports `ERROR: Pipeline failed: Processed dataset not found: .../data/processed/harmonized_stack_overflow_2011_2025.csv`.

On a clean machine, `main.py` detects that the master dataset is absent and runs the cleaning and harmonization pipeline from these raw files before generating the analyses. It writes cleaned annual files under `data/clean/<year>/` and the master file `data/processed/harmonized_stack_overflow_2011_2025.csv`.

## Setup

Python 3.10 or later is required: the source uses Python 3.10 union type syntax and `zip(..., strict=True)`. From the repository root, install the verified runtime dependencies with:

```bash
pip install -r requirements.txt
```

## Running

```bash
python main.py
```

With all raw files in place, the full run takes about 11 minutes. It generates these figures in `outputs/figures/`:

- `demographic_shift_2011_2025.png`
- `null_distribution_boxplot.png`
- `null_distribution_plot.png`
- `post_corona_age_participation.png`
- `post_corona_fulltime_participation.png`
- `post_corona_fulltime_participation_distribution.png`
- `post_corona_participation_by_age.png`
- `robustness_junior_series.png`
- `robustness_r_squared_by_break.png`

It writes these reports in `outputs/audit/`:

- `AUDIT.md`
- `COHORT_RECONCILIATION.md`
- `FIGURE_SWEEP.md`
- `PROXY_BIAS.md`
- `RF_EVAL.md`
- `ROBUSTNESS.md`

## Demo app

`app/streamlit_app.py` presents the findings interactively over four tabs: the junior/mid/senior series, the placebo scan over candidate break years, the coverage of the two community questions, and the 2025 K-modes clusters. Charts are Plotly, so filtering a cohort or dragging the break-year slider updates the page in the browser without a server-side redraw.

```bash
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

The app needs no raw data and does not load the harmonized master dataset. It runs entirely from the committed audit files in `outputs/audit/`, plus two committed figures in `outputs/figures/` whose underlying tables are not written to any audit file.

## Repository structure

```text
main.py                                            Pipeline entry point and raw-data bootstrap.
requirements.txt                                   Python dependencies.
data/raw/<year>/survey_results_public.csv          Downloaded annual response CSVs; not tracked by Git.
data/clean/<year>/survey_results_public_<year>_cleaned.csv  Generated cleaned annual CSVs; not tracked by Git.
data/processed/harmonized_stack_overflow_2011_2025.csv      Generated 14-column master dataset; not tracked by Git.
outputs/figures/*.png                              Generated analysis figures; not tracked by Git.
outputs/audit/*.md                                 Generated audit reports; not tracked by Git.
scripts/__init__.py                                Scripts package marker.
scripts/audit/__init__.py                          Audit-scripts package marker.
scripts/audit/generate_audit.py                    Master-data, provenance, model, and composition audit writer.
scripts/audit/generate_followup.py                 Reconciliation, robustness, and RF-evaluation report writers.
scripts/audit/generate_proxy_bias.py               YearsCode versus YearsCodePro proxy-bias audit writer.
scripts/audit/regenerate_and_sweep.py              Figure-freshness audit writer.
src/__init__.py                                    Source package marker.
src/analysis/__init__.py                           Analysis package marker.
src/analysis/analyze_nulls.py                      Missing-data summary helpers.
src/analysis/analyze_post_corona.py                Participation and age figure helpers.
src/analysis/audit_dataset.py                      Master-dataset shape and quality checks.
src/analysis/structural_break.py                   Broken-stick regression helper.
src/cleaning/__init__.py                           Cleaning package marker.
src/cleaning/clean_data.py                         Raw-file discovery and annual cleaning pipeline.
src/cleaning/data_harmonization.py                 Annual schema mapping and master-dataset builder.
src/models/__init__.py                             Models package marker.
src/models/community_demographics_ml.py            Experience parsing, cohort summaries, and demographic figure helper.
src/reference/__init__.py                          Reference-code package marker.
src/reference/engagement_random_forest.py          Retained random-forest evaluation implementation.
src/visualization/__init__.py                      Visualization package marker.
src/visualization/plot_nulls.py                    Missing-data figure helpers.
```

## Data notes

The master dataset is 768,404 rows x 14 columns. The `experience_is_proxy` flag marks 2015, 2016, and 2025, whose experience measures are general rather than professional; these years are excluded from the primary series and all regressions. The 2025 data is used for the AI and geographic-composition analyses.

## Reference code

`src/reference/engagement_random_forest.py` is retained because `outputs/audit/RF_EVAL.md` cites its evaluation numbers; it is not part of the reported analysis.
