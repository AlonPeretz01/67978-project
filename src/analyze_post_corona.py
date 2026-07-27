import os
import pandas as pd
import matplotlib.pyplot as plt

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
            return 'Prefer not to say'
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
    df['Age'] = df['Age'].fillna('Prefer not to say')
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


def drop_all_nan_rows(df, min_nan=5):
    """Count and remove rows with at least `min_nan` NaN columns. Returns (cleaned_df, count)."""
    mask = df.isna().sum(axis=1) >= min_nan
    count = int(mask.sum())
    return df.loc[~mask].copy(), count


def unite_employement(df):
    """
    Normalize Employment_Status labels:
    - merge 'Employed full-time' and 'Employed, full-time'
    - map 'Student, part-time' / 'Student part-time' to 'Student'
    """
    df = df.copy()
    employment_map = {
        'Employed, full-time': 'Employed full-time',
        'Student, part-time': 'Student',
        'Student, full-time': 'Student',
        'Not employed, and not looking for work': 'Not employed, but looking for work',
        'NaN': 'I prefer not to say',
    }
    df['Employment_Status'] = df['Employment_Status'].replace(employment_map)
    return df


def fill_student_unemployed_compensation(df):
    """
    Replace NaN Yearly_Compensation with 0 for respondents whose
    Employment_Status is 'Student' or 'Not employed, but looking for work'.
    """
    df = df.copy()
    mask = (
        df['Employment_Status'].isin([
            'Student',
            'Not employed, but looking for work',
        ])
        & df['Yearly_Compensation'].isna()
    )
    df.loc[mask, 'Yearly_Compensation'] = 0
    return df

def change_education_level_names(df):
    """ Reduces the length of answers in the education level column"""
    df = df.copy()
    col_name = "Education_Level"
    # Dictionary mapping old long answers to new short names
    edu_map = {
        "Bachelor’s degree (B.A., B.S., B.Eng., etc.)": "B.S.",
        "Master’s degree (M.A., M.S., M.Eng., MBA, etc.)": "M.S.",
        "Secondary school (e.g. American high school, German Realschule or Gymnasium, etc.)": "High School",
        "Other doctoral degree (Ph.D., Ed.D., etc.)": "Ph.D.",
        "Associate degree (A.A., A.S., etc.)": "Associate degree",
        "Some college/university study without earning a degree": "didnt finish college",
        'Primary/elementary school': "Primary school",
        'Professional degree (JD, MD, etc.)': "Professional degree",
        'I never completed any formal education': "Never completed",
    }

    # Replace values inside the specific column
    df[col_name] = df[col_name].replace(edu_map)

    return df

def change_participation_names(df):
    """Changing names of answers in the participation column"""
    # df = df.copy()
    col_name = "Participates_in_questions"
    # Dictionary mapping old long answers to new short names
    edu_map = {
        "I have never participated in Q&A on Stack Overflow": "Never participated",
        "Less than once per month or monthly": "Once per month or less",
        "A few times per month or weekly": "Few times per month",
        "A few times per week": "Weekly",
        "Daily or almost daily": "Daily",
        "Multiple times per day": "Daily",
    }
    df[col_name] = df[col_name].astype(str).str.strip()
    # Replace values inside the specific column
    df[col_name] = df[col_name].replace(edu_map)
    
    return df

def count_rows_with_any_nan(df):
    """Count how many rows contain at least one NaN/NA value."""
    return int(df.isna().any(axis=1).sum())


def rows_with_missing_yearly_compensation(df):
    """Return two subsets: Yearly_Compensation is NaN, and Yearly_Compensation is not NaN."""
    missing = df[df['Yearly_Compensation'].isna()].copy()
    present = df[df['Yearly_Compensation'].notna()].copy()
    return missing, present


def compare_answer_counts(missing_df, present_df):
    """
    Compare answer shares (as fractions of each group) between the
    missing- and present-compensation groups for every column except
    Yearly_Compensation.
    """
    missing_counts = count_answers(missing_df)
    present_counts = count_answers(present_df)
    comparisons = {}

    columns = [
        col for col in missing_df.columns
        if col != 'Yearly_Compensation'
    ]

    for col in columns:
        missing_share = missing_counts[col] / len(missing_df)
        present_share = present_counts[col] / len(present_df)
        comparison = pd.DataFrame({
            'missing_comp': missing_share,
            'present_comp': present_share,
        }).fillna(0.0)
        comparison['difference'] = comparison['missing_comp'] - comparison['present_comp']
        comparisons[col] = comparison.sort_values('difference', key=abs, ascending=False)

    return comparisons


COMMUNITY_ORDER = [
    'No, not at all',
    'No, not really',
    'Neutral',
    'Yes, somewhat',
    'Yes, definitely',
]


def plot_part_of_community(df):
    """
    Bar plot of Part_of_community answer shares for the ordered scale
    from 'No, not at all' to 'Yes, definitely'. Other answers are ignored.
    """
    filtered = df[df['Part_of_community'].isin(COMMUNITY_ORDER)]
    shares = (
        filtered['Part_of_community']
        .value_counts()
        .reindex(COMMUNITY_ORDER, fill_value=0)
        / len(filtered)
    )

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(shares.index, shares.values)
    ax.set_ylim(0.0, 1.0)
    ax.set_yticks([i / 10 for i in range(11)])
    ax.set_ylabel('Share of answers')
    ax.set_xlabel('Part of community')
    ax.set_title('Part_of_community answer distribution')
    plt.xticks(rotation=30, ha='right')
    plt.tight_layout()
    plt.show()
    return shares


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


def plot_education_level(df):
    """
    Bar plot of Education_Level answer shares. Ignores NaN and 'Something else'.
    """
    filtered = df[
        df['Education_Level'].notna()
        & ~df['Education_Level'].isin(EDUCATION_IGNORE)
    ]
    # Keep a stable order: known progression first, then any unexpected labels
    present = filtered['Education_Level'].value_counts()
    ordered = [level for level in EDUCATION_ORDER if level in present.index]
    extras = [level for level in present.index if level not in EDUCATION_ORDER]
    shares = present.reindex(ordered + extras, fill_value=0) / len(filtered)

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(range(len(shares)), shares.values)
    ax.set_xticks(range(len(shares)))
    ax.set_xticklabels(shares.index, rotation=45, ha='right')
    ax.set_ylim(0.0, 0.8)
    ax.set_yticks([i / 10 for i in range(9)])
    ax.set_ylabel('Share of answers')
    ax.set_xlabel('Education level')
    ax.set_title('Education_Level answer distribution')
    plt.tight_layout()
    plt.show()
    return shares


PARTICIPATION_ORDER = [
    'I have never participated in Q&A on Stack Overflow',
    'Less than once per month or monthly',
    'A few times per month or weekly',
    'A few times per week',
    'Daily or almost daily',
    'Multiple times per day',
]


def plot_fulltime_participation(df):
    """
    Bar plot of Participates_in_questions frequency for respondents
    employed full-time. Ignores NaN. Y-axis is share of that subgroup.
    """
    employed = df[df['Employment_Status'] == 'Employed full-time']
    filtered = employed[employed['Participates_in_questions'].notna()]
    shares = (
        filtered['Participates_in_questions']
        .value_counts()
        .reindex(PARTICIPATION_ORDER, fill_value=0)
        / len(filtered)
    )

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.bar(range(len(shares)), shares.values)
    ax.set_xticks(range(len(shares)))
    ax.set_xticklabels(shares.index, rotation=35, ha='right')
    ax.set_ylim(0.0, 1.0)
    ax.set_yticks([i / 10 for i in range(11)])
    ax.set_ylabel('Share of employed full-time respondents')
    ax.set_xlabel('Participation frequency in Q&A')
    ax.set_title('Q&A participation among full-time employees')
    plt.tight_layout()
    plt.show()
    return shares


if __name__ == '__main__':
    df = combine_post_corona_datasets()
    df, all_nan_count = drop_all_nan_rows(df)
    print(f"Rows with at least 5 NaN columns (dropped): {all_nan_count}")
    df = age_union(df)
    df = unite_employement(df)
    df = fill_student_unemployed_compensation(df)
    df = change_education_level_names(df)
    df = change_participation_names(df)
    # plot_part_of_community(df)
    # plot_education_level(df)
    plot_fulltime_participation(df)
