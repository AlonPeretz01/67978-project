# src/

Clean, reusable Python modules for the project: data loading, cleaning, schema
reconciliation across survey years, and processing pipelines.

Code here should be stable and importable from notebooks (e.g. `from src.data_loader import
load_survey_year`), unlike the exploratory code in `notebooks/`.

## cleaning/

The data cleaning and schema harmonization pipeline (`clean_data.py` and
`data_harmonization.py`). See the root [README.md](../README.md#running-the-cleaning--harmonization-pipeline)
for how to run it.
