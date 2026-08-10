import os
import logging
import pandas as pd

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
RAW_DIR = os.path.join(PROJECT_ROOT, 'data', 'raw')
CLEAN_DIR = os.path.join(PROJECT_ROOT, 'data', 'clean')
THRESHOLD = 80.0
YEARS = range(2011, 2026)
MULTIROW_HEADER_YEARS = {2015: 1}
LOGGER = logging.getLogger(__name__)


def find_raw_survey_file(year, raw_dir=RAW_DIR):
    """Return the canonical survey CSV, with support for legacy archive names."""
    year_dir = os.path.join(raw_dir, str(year))
    canonical_path = os.path.join(year_dir, 'survey_results_public.csv')
    if os.path.isfile(canonical_path):
        return canonical_path

    if not os.path.isdir(year_dir):
        return None

    candidates = []
    for root, _, files in os.walk(year_dir):
        for filename in files:
            lower_name = filename.lower()
            if not lower_name.endswith('.csv'):
                continue
            if any(term in lower_name for term in ('schema', 'crosswalk', 'question')):
                continue
            candidates.append(os.path.join(root, filename))

    return sorted(candidates)[0] if candidates else None


def clean_dataframe(
    dataframe: pd.DataFrame,
    *,
    missing_column_threshold: float | None = None,
) -> pd.DataFrame:
    """Return a copy with unnamed and optional sparse columns removed.

    Args:
        dataframe: Input dataset to clean.
        missing_column_threshold: Optional percentage above which columns are
            removed. ``None`` preserves sparse analytical columns.
    """
    if dataframe.empty:
        raise ValueError("Cannot clean an empty DataFrame.")
    if missing_column_threshold is not None and not 0 <= missing_column_threshold <= 100:
        raise ValueError("missing_column_threshold must be between 0 and 100.")

    cleaned = dataframe.copy()
    unnamed_columns = [
        column for column in cleaned.columns if "unnamed" in str(column).lower()
    ]
    cleaned = cleaned.drop(columns=unnamed_columns)

    if missing_column_threshold is not None:
        missing_percentages = cleaned.isna().mean().mul(100)
        sparse_columns = missing_percentages[
            missing_percentages > missing_column_threshold
        ].index
        cleaned = cleaned.drop(columns=sparse_columns)

    return cleaned


def clean_survey_data():
    if not os.path.exists(CLEAN_DIR):
        os.makedirs(CLEAN_DIR)
        
    cleaned_paths = {}

    for year in YEARS:
        file_path = find_raw_survey_file(year)
        if file_path is None:
            print(f"Skipping {year}: no survey results CSV was found.")
            continue

        print(f"Cleaning {year}...")

        read_options = {"low_memory": False}
        if year in MULTIROW_HEADER_YEARS:
            read_options["header"] = MULTIROW_HEADER_YEARS[year]
            LOGGER.info(
                "Reading %s survey with row %s as its schema header.",
                year,
                MULTIROW_HEADER_YEARS[year] + 1,
            )
        # try:
        #     df = pd.read_csv(file_path, **read_options)
        # except UnicodeDecodeError:
        #     df = pd.read_csv(file_path, encoding="latin1", **read_options)
        # file_extension = os.path.splitext(file_path)[1].lower()
        # if file_extension in {'.xls', '.xlsx', '.xlsm', '.xlsb', '.ods'}:
        #     df = pd.read_excel(file_path)
        # else:
        print(f"Reading file: {file_path}")
        try:
            df = pd.read_csv(file_path, low_memory=False)
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, low_memory=False, encoding='latin1')

        original_columns = df.columns
        df = clean_dataframe(df, missing_column_threshold=THRESHOLD)
        dropped_columns = set(original_columns).difference(df.columns)

        out_dir = os.path.join(CLEAN_DIR, str(year))
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f'survey_results_public_{year}_cleaned.csv')

        df.to_csv(out_path, index=False)
        cleaned_paths[str(year)] = out_path
        print(
            f"Saved {year} | Dropped {len(dropped_columns)} columns. "
            f"Remaining: {df.shape[1]} cols"
        )

        print(f"\n--- {year} Matching Columns ---")
        target_keywords = ['age', 'year', 'ed', 'employ', 'comp', 'salary', 'ai', 'stack', 'occup']
        matching_cols = [c for c in df.columns if any(k in c.lower() for k in target_keywords)]
        for col in matching_cols:
            print(f"  - {col}")

    return cleaned_paths
