import os
import pandas as pd

from cleaning.data_harmonization import harmonize_schema

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PROJECT_DATA_DIR = os.path.join(PROJECT_ROOT, 'project_data')
YEARS = ['2020', '2021', '2022']

AGE_BINS_ORDER = [
    'Under 18 years old',
    '18-24 years old',
    '25-34 years old',
    '35-44 years old',
    '45-54 years old',
    '55-64 years old',
    '65 years or older',
]


def load_and_harmonize_year(year):
    """Load survey_results_public for a year and apply schema harmonization."""
    file_path = os.path.join(PROJECT_DATA_DIR, year, 'survey_results_public.csv')
    print(f"Loading {year} from {file_path}...")

    try:
        df = pd.read_csv(file_path, low_memory=False)
    except UnicodeDecodeError:
        print(f"Encoding error for {year}, retrying with latin1...")
        df = pd.read_csv(file_path, low_memory=False, encoding='latin1')

    harmonized_df = harmonize_schema(df, year)
    print(f"  -> {harmonized_df.shape[0]:,} rows, {harmonized_df.shape[1]} columns")
    return harmonized_df


def combine_post_corona_datasets():
    """Combine harmonized 2020–2022 survey datasets into one DataFrame."""
    harmonized_dfs = [load_and_harmonize_year(year) for year in YEARS]

    print("\nConcatenating 2020–2022 into a single dataset...")
    combined = pd.concat(harmonized_dfs, ignore_index=True)
    print(f"Combined dataset: {combined.shape[0]:,} rows, {combined.shape[1]} columns")
    return combined


def age_union(df):
    """
    Align 2020 numeric Age values to the 2021/2022 categorical groups:
    Under 18, 18-24, 25-34, 35-44, 45-54, 55-64, 65+.
    Leaves already-categorical Age values unchanged.
    """
    df = df.copy()

    def to_age_group(value):
        if pd.isna(value):
            return value
        if value in AGE_BINS_ORDER:
            return value
        try:
            age = float(value)
        except (TypeError, ValueError):
            return value

        if age < 18:
            return 'Under 18 years old'
        if age <= 24:
            return '18-24 years old'
        if age <= 34:
            return '25-34 years old'
        if age <= 44:
            return '35-44 years old'
        if age <= 54:
            return '45-54 years old'
        if age <= 64:
            return '55-64 years old'
        return '65 years or older'

    mask_2020 = df['Year'] == '2020'
    df.loc[mask_2020, 'Age'] = df.loc[mask_2020, 'Age'].map(to_age_group)
    return df


def count_answers(df):
    """Count how many respondents gave each answer, per column."""
    counts = {}

    for col in df.columns:
        col_counts = df[col].value_counts(dropna=False)

        if col == 'Age':
            ordered = [g for g in AGE_BINS_ORDER if g in col_counts.index]
            extras = [i for i in col_counts.index if i not in AGE_BINS_ORDER]
            col_counts = col_counts.reindex(ordered + extras)

        counts[col] = col_counts

    return counts


if __name__ == '__main__':
    df = combine_post_corona_datasets()
    df = age_union(df)
    answer_counts = count_answers(df)

    for col, counts in answer_counts.items():
        print(f"\n=== {col} ===")
        print(counts)

