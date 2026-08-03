# Stack Overflow Survey Analysis

This project analyzes Stack Overflow Annual Developer Survey data (2011–2025)
with a script-only data-science pipeline.

## Project layout

```text
.
├── data/
│   ├── raw/                         # Original datasets, grouped by survey year
│   └── processed/                   # Cleaned and harmonized data
│       ├── clean/                   # Per-year cleaned datasets
│       └── harmonized_stack_overflow_2011_2025.csv
├── outputs/
│   └── figures/                     # Pipeline-generated figures
├── src/
│   ├── analysis/                    # Audit, null, post-corona, break analyses
│   ├── cleaning/                    # Data cleaning and schema harmonization
│   ├── models/                      # Demographic and ML modelling
│   └── visualization/               # Figure-generation helpers
├── main.py                          # The only executable project entry point
├── requirements.txt
└── README.md
```

## Run the pipeline

Install dependencies once:

```bash
pip install -r requirements.txt
```

Run all cleaning, audit, analysis, modelling, and visualization steps from the
repository root:

```bash
python main.py
```

`main.py` loads `data/processed/harmonized_stack_overflow_2011_2025.csv` once,
then writes all figures to `outputs/figures/`.
