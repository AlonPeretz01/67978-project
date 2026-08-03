# Data Directory

> **Version-control note:** All data files in this directory are ignored by
> Git via `.gitignore` and are not uploaded to the repository.

This directory stores the local Stack Overflow Developer Survey datasets used
by the analysis, covering survey years 2011–2025.

## Current structure

```text
data/
├── raw/                                  # Original survey releases
│   ├── 2011/ … 2015/                     # One historical survey CSV each
│   ├── 2016/2016 Stack Overflow Survey Results/
│   └── 2017/ … 2025/                     # Public-result CSVs and schema files
├── clean/                                # Per-year cleaned survey CSVs
│   └── 2011/ … 2025/
└── processed/
    └── harmonized_stack_overflow_2011_2025.csv
```

## Raw survey response CSVs

| Survey year | Existing response CSV location |
| --- | --- |
| 2011 | `raw/2011/2011 Stack Overflow Survey Results.csv` |
| 2012 | `raw/2012/2012 Stack Overflow Survey Results.csv` |
| 2013 | `raw/2013/2013 Stack Overflow Survey Responses.csv` |
| 2014 | `raw/2014/2014 Stack Overflow Survey Responses.csv` |
| 2015 | `raw/2015/2015 Stack Overflow Developer Survey Responses.csv` |
| 2016 | `raw/2016/2016 Stack Overflow Survey Results/2016 Stack Overflow Survey Responses.csv` |
| 2017–2023 | `raw/<year>/survey_results_public.csv` |
| 2024 | `raw/2024/survey_results_public.csv` (plus `kaggle_extra/` survey CSVs) |
| 2025 | `raw/2025/survey_results_public.csv` |

The 2017–2025 raw-year folders also contain the matching survey schema CSV
where supplied by Stack Overflow, alongside survey documentation files.

## Derived datasets

- `clean/<year>/survey_results_public_<year>_cleaned.csv`: cleaned annual
  survey data for every year from 2011 through 2025.
- `processed/harmonized_stack_overflow_2011_2025.csv`: the combined,
  harmonized dataset used by the root project pipeline.
