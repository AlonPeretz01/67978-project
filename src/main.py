import os
import pandas as pd

from cleaning.data_harmonization import harmonize_schema
from analyze_post_corona import Post_Corona

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
RAW_DIR = os.path.join(PROJECT_ROOT, 'data', 'raw')
YEARS = ['2020', '2021', '2022']

PARTICIPATION_ORDER = [
    'nan',
    'Never participated',
    'Once per month or less',
    'Few times per month',
    'Weekly',
    'Daily',
]

COMMUNITY_ORDER = [
    'No, not at all',
    'No, not really',
    'Not sure',
    'Neutral',
    'Yes, somewhat',
    'Yes, definitely',
]

VISITING_ORDER = [
    'nan',
    'Once per month or less',
    'Few times per month',
    'Weekly',
    'Daily',
]

EDUCATION_ORDER = [
    'Never completed',
    'Primary school',
    'High School',
    'didnt finish college',
    'Associate degree',
    'B.S.',
    'M.S.',
    'Professional degree',
    'Ph.D.',
]

EDUCATION_IGNORE = {'Something else'}

def load_and_harmonize_year(year):
    """Load survey_results_public for a year and apply schema harmonization."""
    year = str(year)
    file_path = os.path.join(RAW_DIR, str(year), 'survey_results_public.csv')
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


if __name__ == '__main__':
    df = combine_post_corona_datasets()
    post_corona = Post_Corona(df)
    post_corona.age_union()
    post_corona.drop_all_nan_rows()
    post_corona.change_education_level_names()
    post_corona.change_participation_names()
    post_corona.change_visiting_names()
    post_corona.fill_student_unemployed_compensation()
    # print(final_df['Visits_SO_freq'].value_counts())
    # print("\n")
    # print(final_df['Participates_in_questions'].value_counts())
    post_corona.plot_column('Part_of_community', COMMUNITY_ORDER)
    # post_corona.plot_compare_answer_with_column('Part_of_community', 'Yes, definitely','Participates_in_questions', )
    # post_corona.plot_stacked_by_columns('Part_of_community', 'Visits_SO_freq', 
    #                                     COMMUNITY_ORDER, VISITING_ORDER)
