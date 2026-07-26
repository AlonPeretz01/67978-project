import os
import pandas as pd

from cleaning.data_harmonization import harmonize_schema

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PROJECT_DATA_DIR = os.path.join(PROJECT_ROOT, 'project_data')
YEARS = ['2020', '2021', '2022']


def load_and_harmonize_year(year):
    """Load survey_results_public for a year and apply schema harmonization."""
    file_path = os.path.join(PROJECT_DATA_DIR, year, 'survey_results_public.csv')
    print(f"Loading {year} from {file_path}...")

    try:
        df = pd.read_csv(file_path, low_memory=False)
    except UnicodeDecodeError:
        print(f"Encoding error for {year}, retrying with latin1...")
        df = pd.read_csv(file_path, low_memory=False, encoding='latin1')

    # print(f"Columns for {year}:")
    # print(list(df.columns))

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


if __name__ == '__main__':
    # df = combine_post_corona_datasets()
    # print("\nRows per year:")
    # print(df['Year'].value_counts().sort_index())
    # print("\nColumns:", list(df.columns))
    # print("\nSample:")
    # print(df.head(3))
    df = load_and_harmonize_year('2020')

