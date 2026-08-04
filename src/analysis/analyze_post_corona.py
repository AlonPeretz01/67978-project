import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from matplotlib.ticker import PercentFormatter

AGE_BINS_ORDER = [
    'Under 18 years old',
    '18-24 years old',
    '25-34 years old',
    '35-44 years old',
    '45-54 years old',
    '55-64 years old',
    '65 years or older',
]

COMMUNITY_ORDER = [
    'No, not at all',
    'No, not really',
    'Neutral',
    'Yes, somewhat',
    'Yes, definitely',
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

PRIMARY_COLOR = '#1F4E79'
SECONDARY_COLOR = '#E69F00'
TERTIARY_COLOR = '#009E73'
QUATERNARY_COLOR = '#CC79A7'
QUINARY_COLOR = '#56B4E9'
GRID_COLOR = '#D9D9D9'

PARTICIPATION_ORDER = [
    'Never participated',
    'Once per month or less',
    'Few times per month',
    'Weekly',
    'Daily',
    'No answer',
]

AGE_SHORT_LABELS = {
    'Under 18 years old': '<18',
    '18-24 years old': '18-24',
    '25-34 years old': '25-34',
    '35-44 years old': '35-44',
    '45-54 years old': '45-54',
    '55-64 years old': '55-64',
    '65 years or older': '65+',
}

AGE_SHORT_ORDER = ['<18', '18-24', '25-34', '35-44', '45-54', '55-64', '65+']

PARTICIPATION_COLORS = {
    'Never participated': PRIMARY_COLOR,
    'Once per month or less': SECONDARY_COLOR,
    'Few times per month': TERTIARY_COLOR,
    'Weekly': QUATERNARY_COLOR,
    'Daily': QUINARY_COLOR,
    'No answer': '#999999',
}

CATEGORICAL_COLORS = (
    PRIMARY_COLOR,
    SECONDARY_COLOR,
    TERTIARY_COLOR,
    QUATERNARY_COLOR,
    QUINARY_COLOR,
)


class Post_Corona:
    def __init__(self, df):
        self.df = df

    def age_union(self):
        """
        Align 2020 numeric Age values to the 2021/2022 categorical groups:
        Under 18, 18-24, 25-34, 35-44, 45-54, 55-64, 65+.
        Leaves already-categorical Age values unchanged.
        """
        df = self.df.copy()

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

        mask_2020 = pd.to_numeric(df['Year'], errors='coerce').eq(2020)
        df.loc[mask_2020, 'Age'] = df.loc[mask_2020, 'Age'].map(to_age_group)
        df['Age'] = df['Age'].fillna('Prefer not to say')
        self.df = df
        return self.df

    def count_answers(self, df=None):
        """Count how many respondents gave each answer, per column."""
        df = self.df if df is None else df
        counts = {}

        for col in df.columns:
            col_counts = df[col].value_counts(dropna=False)

            if col == 'Age':
                ordered = [g for g in AGE_BINS_ORDER if g in col_counts.index]
                extras = [i for i in col_counts.index if i not in AGE_BINS_ORDER]
                col_counts = col_counts.reindex(ordered + extras)

            counts[col] = col_counts

        return counts

    def drop_all_nan_rows(self, min_nan=5):
        """Count and remove rows with at least `min_nan` NaN columns. Returns count dropped."""
        mask = self.df.isna().sum(axis=1) >= min_nan
        count = int(mask.sum())
        self.df = self.df.loc[~mask].copy()
        return count

    def unite_employement(self):
        """
        Normalize Employment_Status labels:
        - merge 'Employed full-time' and 'Employed, full-time'
        - map 'Student, part-time' / 'Student part-time' to 'Student'
        """
        df = self.df.copy()
        employment_map = {
            'Employed, full-time': 'Employed full-time',
            'Student, part-time': 'Student',
            'Student, full-time': 'Student',
            'Not employed, and not looking for work': 'Not employed, but looking for work',
            'NaN': 'I prefer not to say',
        }
        df['Employment_Status'] = df['Employment_Status'].replace(employment_map)
        self.df = df
        return self.df

    def fill_student_unemployed_compensation(self):
        """
        Replace NaN Yearly_Compensation with 0 for respondents whose
        Employment_Status is 'Student' or 'Not employed, but looking for work'.
        """
        df = self.df.copy()
        mask = (
            df['Employment_Status'].isin([
                'Student',
                'Not employed, but looking for work',
            ])
            & df['Yearly_Compensation'].isna()
        )
        df.loc[mask, 'Yearly_Compensation'] = 0
        self.df = df
        return self.df

    def change_education_level_names(self):
        """Reduces the length of answers in the education level column."""
        df = self.df.copy()
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
        df['Education_Level'] = df['Education_Level'].replace(edu_map)
        self.df = df
        return self.df

    def change_participation_names(self):
        """Changing names of answers in the participation column."""
        df = self.df.copy()
        col_name = 'Participates_in_questions'
        participation_map = {
            "I have never participated in Q&A on Stack Overflow": "Never participated",
            "Less than once per month or monthly": "Once per month or less",
            "A few times per month or weekly": "Few times per month",
            "A few times per week": "Weekly",
            "Daily or almost daily": "Daily",
            "Multiple times per day": "Daily",
        }
        df[col_name] = df[col_name].astype('string').str.strip()
        df[col_name] = df[col_name].replace(participation_map).fillna('No answer')
        self.df = df
        return self.df

    def change_visiting_names(self):
        df = self.df.copy()
        col_name = 'Visits_SO_freq'
        visiting_map = {
            "I have never visited Stack Overflow (before today)": "Never visited",
            "Less than once per month or monthly": "Once per month or less",
            "A few times per month or weekly": "Few times per month",
            "A few times per week": "Weekly",
            "Daily or almost daily": "Daily",
            "Multiple times per day": "Daily",
        }
        df[col_name] = df[col_name].astype(str).str.strip()
        df[col_name] = df[col_name].replace(visiting_map)
        df = df[df[col_name] != "Never visited"].copy()
        self.df = df
        return self.df

    def count_rows_with_any_nan(self):
        """Count how many rows contain at least one NaN/NA value."""
        return int(self.df.isna().any(axis=1).sum())

    def rows_with_missing_yearly_compensation(self):
        """Return two subsets: Yearly_Compensation is NaN, and Yearly_Compensation is not NaN."""
        missing = self.df[self.df['Yearly_Compensation'].isna()].copy()
        present = self.df[self.df['Yearly_Compensation'].notna()].copy()
        return missing, present

    def compare_answer_counts(self, missing_df, present_df):
        """
        Compare answer shares (as fractions of each group) between the
        missing- and present-compensation groups for every column except
        Yearly_Compensation.
        """
        missing_counts = self.count_answers(missing_df)
        present_counts = self.count_answers(present_df)
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

    # def plot_part_of_community(self):
    #     """
    #     Bar plot of Part_of_community answer shares for the ordered scale
    #     from 'No, not at all' to 'Yes, definitely'. Other answers are ignored.
    #     """
    #     filtered = self.df[self.df['Part_of_community'].isin(COMMUNITY_ORDER)]
    #     shares = (
    #         filtered['Part_of_community']
    #         .value_counts()
    #         .reindex(COMMUNITY_ORDER, fill_value=0)
    #         / len(filtered)
    #     )

    #     fig, ax = plt.subplots(figsize=(10, 5))
    #     ax.bar(shares.index, shares.values)
    #     ax.set_ylim(0.0, 1.0)
    #     ax.set_yticks([i / 10 for i in range(11)])
    #     ax.set_ylabel('Share of answers')
    #     ax.set_xlabel('Part of community')
    #     ax.set_title('Part_of_community answer distribution')
    #     plt.xticks(rotation=30, ha='right')
    #     plt.tight_layout()
    #     plt.show()
    #     return shares

    def plot_column(self, column_name: str, order: list):
            """
            Bar plot of Part_of_community answer shares for the ordered scale
            from 'No, not at all' to 'Yes, definitely'. Other answers are ignored.
            """
            filtered = self.df[self.df[column_name].isin(order)]
            shares = (
                filtered[column_name]
                .value_counts()
                .reindex(order, fill_value=0)
                / len(filtered)
            )
    
            fig, ax = plt.subplots(figsize=(10, 5.5))
            ax.bar(shares.index, shares.values, color=PRIMARY_COLOR)
            ax.set_ylim(0.0, 1.0)
            ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
            ax.set_ylabel('Share of valid responses', fontsize=13)
            ax.set_xlabel(column_name, fontsize=13)
            ax.set_title(f'Distribution of responses: {column_name}', fontsize=17, weight='semibold', pad=14)
            ax.tick_params(axis='both', labelsize=11)
            ax.tick_params(axis='x', rotation=30)
            ax.grid(axis='y', color=GRID_COLOR, linestyle=':', alpha=0.7)
            ax.set_axisbelow(True)
            plt.tight_layout()
            plt.show()
            return shares

    def plot_education_level(self):
        """
        Bar plot of Education_Level answer shares. Ignores NaN and 'Something else'.
        """
        filtered = self.df[
            self.df['Education_Level'].notna()
            & ~self.df['Education_Level'].isin(EDUCATION_IGNORE)
        ]
        present = filtered['Education_Level'].value_counts()
        ordered = [level for level in EDUCATION_ORDER if level in present.index]
        extras = [level for level in present.index if level not in EDUCATION_ORDER]
        shares = present.reindex(ordered + extras, fill_value=0) / len(filtered)

        fig, ax = plt.subplots(figsize=(12, 5.5))
        ax.bar(range(len(shares)), shares.values, color=PRIMARY_COLOR)
        ax.set_xticks(range(len(shares)))
        ax.set_xticklabels(shares.index, rotation=45, ha='right')
        ax.set_ylim(0.0, 0.8)
        ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
        ax.set_ylabel('Share of valid responses', fontsize=13)
        ax.set_xlabel('Education level', fontsize=13)
        ax.set_title('Education attainment among post-corona survey respondents', fontsize=17, weight='semibold', pad=14)
        ax.tick_params(axis='both', labelsize=11)
        ax.grid(axis='y', color=GRID_COLOR, linestyle=':', alpha=0.7)
        ax.set_axisbelow(True)
        plt.tight_layout()
        plt.show()
        return shares


def prepare_post_corona_data(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Return a consistently labelled 2020–2022 analysis subset.

    The function performs the existing post-corona transformations without
    displaying figures or reading files. It is intended for orchestration by
    root ``main.py``.
    """
    required_columns = {
        "Year",
        "Age",
        "Education_Level",
        "Employment_Status",
        "Yearly_Compensation",
        "Participates_in_questions",
        "Visits_SO_freq",
    }
    missing_columns = required_columns.difference(dataframe.columns)
    if missing_columns:
        raise ValueError(
            "Post-corona analysis is missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

    years = pd.to_numeric(dataframe["Year"], errors="coerce")
    subset = dataframe.loc[years.between(2020, 2022)].copy()
    if subset.empty:
        raise ValueError("No rows are available for the 2020–2022 analysis period.")

    analysis = Post_Corona(subset)
    analysis.age_union()
    analysis.unite_employement()
    analysis.change_education_level_names()
    analysis.change_participation_names()
    analysis.change_visiting_names()
    analysis.fill_student_unemployed_compensation()
    return analysis.df

def plot_fulltime_participation(
    df: pd.DataFrame,
    output_path: Path,
    employment_status: str,
) -> pd.Series:
    """
    Bar plot of participation frequency for respondents in an employment group,
    including missing answers as the explicit ``No answer`` category.
    """
    employed = df[df['Employment_Status'] == employment_status]
    filtered = employed[employed['Participates_in_questions'].notna()]
    shares = (
        filtered['Participates_in_questions']
        .value_counts()
        .reindex(PARTICIPATION_ORDER, fill_value=0)
        / len(filtered)
    )

    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.bar(range(len(shares)), shares.values, color=PRIMARY_COLOR)
    ax.set_xticks(range(len(shares)))
    ax.set_xticklabels(shares.index, rotation=35, ha='right')
    ax.set_ylim(0.0, 1.0)
    ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    ax.set_ylabel(f'Share of {employment_status} respondents', fontsize=13)
    ax.set_xlabel('Participation frequency in Q&A', fontsize=13)
    ax.set_title(f'Q&A participation among {employment_status} respondents', fontsize=17, weight='semibold', pad=14)
    ax.tick_params(axis='both', labelsize=11)
    ax.grid(axis='y', color=GRID_COLOR, linestyle=':', alpha=0.7)
    ax.set_axisbelow(True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches='tight')
    plt.close(fig)
    return shares

def plot_age_participation_stacked(
    df: pd.DataFrame,
    output_path: Path,
) -> pd.DataFrame:
    """
    Grouped bar chart: for each age group, share of participation frequencies.
    Each bar is participation / age-group total.
    """
    filtered = df[
        df['Age'].isin(AGE_BINS_ORDER)
        & df['Participates_in_questions'].isin(PARTICIPATION_ORDER)
    ].copy()
    filtered['Age_short'] = filtered['Age'].map(AGE_SHORT_LABELS)

    shares = (
        pd.crosstab(filtered['Age_short'], filtered['Participates_in_questions'], normalize='index')
        .reindex(index=AGE_SHORT_ORDER, columns=PARTICIPATION_ORDER, fill_value=0.0)
    )

    fig, ax = plt.subplots(figsize=(12, 6.5))
    x = list(range(len(shares.index)))
    width = 0.8 / len(PARTICIPATION_ORDER)

    for index, participation in enumerate(PARTICIPATION_ORDER):
        values = shares[participation]
        ax.bar(
            [position + (index - (len(PARTICIPATION_ORDER) - 1) / 2) * width for position in x],
            values,
            label=participation,
            color=PARTICIPATION_COLORS[participation],
            width=width,
        )

    ax.set_xticks(x)
    ax.set_xticklabels(shares.index)
    ax.set_ylim(0.0, 1.0)
    ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    ax.set_ylabel('Share within age group', fontsize=13)
    ax.set_xlabel('Age group', fontsize=13)
    ax.set_title('Q&A participation frequency differs across age groups', fontsize=17, weight='semibold', pad=14)
    ax.tick_params(axis='both', labelsize=11)
    ax.grid(axis='y', color=GRID_COLOR, linestyle=':', alpha=0.7)
    ax.set_axisbelow(True)
    ax.legend(title='Participation', bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=11, title_fontsize=11)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches='tight')
    plt.close(fig)
    return shares

def compare_answer_with_column(
    df: pd.DataFrame,
    columnA: str,
    answerA: str,
    columnB: str,
) -> pd.DataFrame:
    """Return non-null ``columnB`` responses for a selected ``columnA`` answer."""
    only_answer = df[df[columnA] == answerA]
    corr_vec = only_answer[only_answer[columnB].notna()]
    return corr_vec

def plot_compare_answer_with_column(
    df: pd.DataFrame,
    output_path: Path,
    columnA: str,
    answerA: str,
    columnB: str,
) -> pd.Series:
    """
    Filter by `columnA == answerA`, then plot the percentage distribution
    of non-null answers in `columnB`.
    """
    corr_df = compare_answer_with_column(df, columnA, answerA, columnB)
    counts = corr_df[columnB].value_counts()
    shares = counts / len(corr_df)

    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.bar(range(len(shares)), shares.values, color=PRIMARY_COLOR)
    ax.set_xticks(range(len(shares)))
    ax.set_xticklabels(shares.index, rotation=45, ha='right')
    ax.set_ylim(0.0, 1.0)
    ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    ax.set_ylabel('Share of filtered respondents', fontsize=13)
    ax.set_xlabel(columnB, fontsize=13)
    ax.set_title(f'{columnB} responses among respondents with {columnA} = {answerA}', fontsize=17, weight='semibold', pad=14)
    ax.tick_params(axis='both', labelsize=11)
    ax.grid(axis='y', color=GRID_COLOR, linestyle=':', alpha=0.7)
    ax.set_axisbelow(True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches='tight')
    plt.close(fig)
    return shares

def plot_stacked_by_columns(
    df: pd.DataFrame,
    output_path: Path,
    columnA: str,
    columnB: str,
    orderA: list | None = None,
    orderB: list | None = None,
) -> pd.DataFrame:
    """
    Create a grouped bar plot where x-axis is `columnB` and each bar shows
    the share of a `columnA` response within that `columnB` category.
    If provided, `orderA` controls stack order and `orderB` controls x-axis order.
    """
    filtered = df[
        df[columnA].notna()
        & df[columnB].notna()
    ].copy()

    shares = pd.crosstab(
        filtered[columnB],
        filtered[columnA],
        normalize='index',
    )

    if orderB is not None:
        remaining_b = [value for value in shares.index if value not in orderB]
        shares = shares.reindex(list(orderB) + remaining_b, fill_value=0.0)

    if orderA is not None:
        remaining_a = [value for value in shares.columns if value not in orderA]
        shares = shares.reindex(columns=list(orderA) + remaining_a, fill_value=0.0)

    fig, ax = plt.subplots(figsize=(12, 6.5))
    x = list(range(len(shares.index)))
    width = 0.8 / len(shares.columns)

    for idx, answer in enumerate(shares.columns):
        values = shares[answer]
        ax.bar(
            [position + (idx - (len(shares.columns) - 1) / 2) * width for position in x],
            values,
            label=answer,
            color=PARTICIPATION_COLORS.get(answer, CATEGORICAL_COLORS[idx % len(CATEGORICAL_COLORS)]),
            width=width,
        )

    ax.set_xticks(x)
    ax.set_xticklabels(shares.index, rotation=45, ha='right')
    ax.set_ylim(0.0, 1.0)
    ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    ax.set_ylabel(f'Share of {columnB} respondents', fontsize=13)
    ax.set_xlabel(columnB, fontsize=13)
    ax.set_title(f'{columnA} response shares within each {columnB} category', fontsize=17, weight='semibold', pad=14)
    ax.tick_params(axis='both', labelsize=11)
    ax.grid(axis='y', color=GRID_COLOR, linestyle=':', alpha=0.7)
    ax.set_axisbelow(True)
    ax.legend(title=columnA, bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=11, title_fontsize=11)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches='tight')
    plt.close(fig)
    return shares
