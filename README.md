# Analyzing the impact of LLMs on the usage and community of StackOverflow

**Course:** A Needle in a Data Haystack — Data Science analysis project

**Team members:**
- Ilya Ulik
- Alon Peretz
- Ishay Shaul
- Hadar Wolf

## Project Goal

Since the widespread adoption of large language model (LLM) tools such as ChatGPT and GitHub
Copilot, developers have gained a new channel for getting coding help — one that competes
directly with community Q&A platforms like Stack Overflow. This project analyzes the
**Stack Overflow Annual Developer Survey** (2011–2025) to study how the rise of AI tools has
affected:

- Developer usage patterns of Stack Overflow (question asking/answering behavior, visit
  frequency, perceived value of the platform).
- The Stack Overflow community itself (sentiment toward the site, trust in AI-generated
  answers, demographic and experience-level shifts among active users).
- Trends over time, especially the years surrounding the mainstream emergence of LLM-based
  coding assistants (2022 onward), compared against the pre-LLM baseline.

## Data

The data source is the [Stack Overflow Annual Developer Survey](https://survey.stackoverflow.co/),
which has been published every year since 2011. Each yearly release provides:

- A results CSV file with one row per respondent and columns for each survey question.
- A schema/README file describing the questions and answer codes for that year.

This project uses the survey editions from **2011 through 2025**. Survey structure, question
wording, and available fields vary across years, so part of the project's data processing work
involves reconciling these differences into a consistent, analysis-ready schema.

> **Note:** The raw survey files are large (tens of MB per year) and are **not stored in this
> Git repository**. See [data/README.md](data/README.md) for download instructions.

## Repository Structure

```
.
├── README.md              # This file
├── .gitignore             # Excludes raw data, venv, notebook checkpoints, etc.
├── requirements.txt        # Python dependencies
├── data/                   # Local-only folder for raw/processed survey CSVs (gitignored)
│   ├── raw/                # Untouched yearly survey downloads, one subfolder per year
│   ├── clean/               # Per-year output of the cleaning step
│   └── processed/           # Final harmonized dataset spanning all years
├── notebooks/              # Jupyter notebooks for exploratory analysis and visualizations
└── src/                    # Reusable Python modules
    ├── cleaning/            # Data cleaning & schema harmonization pipeline
    │   ├── clean_data.py         # Per-year cleaning (drops empty/near-empty columns)
    │   └── data_harmonization.py # Maps each year's columns to a common schema and merges them
    ├── audit_dataset.py
    ├── analyze_nulls.py
    └── plot_nulls.py
```

Each subfolder contains its own `README.md` explaining its purpose in more detail.

## Running the Cleaning & Harmonization Pipeline

The pipeline turns the raw, per-year survey downloads in `data/raw/` into a single
longitudinal dataset in `data/processed/`, in two steps:

1. **Clean** each year's raw CSV — drops unnamed/index columns and columns with more than
   80% missing values, writing one cleaned CSV per year to `data/clean/`:
   ```
   python src/cleaning/clean_data.py
   ```
2. **Harmonize** the cleaned per-year files — maps each year's differently-named columns
   (e.g. `ConvertedComp` in 2019 vs. `ConvertedCompYearly` in 2022) onto a shared schema
   (`Age`, `Education_Level`, `Years_of_Experience`, `Employment_Status`,
   `Yearly_Compensation`, `Usage_Frequency`, `AI_Tool_Usage`, `AI_Usage_Status`), then
   concatenates all years into `data/processed/harmonized_stack_overflow_2011_2025.csv`:
   ```
   python src/cleaning/data_harmonization.py
   ```

Both scripts resolve `data/` relative to the repository root, so they can be run from any
working directory. Run them in order — harmonization depends on `clean_data.py`'s output.

## Getting the Data

1. Download each year's survey results from the official archive:
   https://survey.stackoverflow.co/ (look for "previous years' results" / archive links).
2. Place each year's extracted CSV file(s) into the `data/` folder, e.g.:
   ```
   data/raw/2024/survey_results_public.csv
   data/raw/2025/survey_results_public.csv
   ...
   ```
3. Do **not** commit these files — `data/` is excluded via `.gitignore`. Everyone on the team
   should download the data locally following the same folder convention so that paths in
   `src/` and `notebooks/` stay consistent across machines.

