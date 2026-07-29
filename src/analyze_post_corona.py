import pandas as pd
import matplotlib.pyplot as plt

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

PARTICIPATION_ORDER = [
    'Never participated',
    'Once per month or less',
    'Few times per month',
    'Weekly',
    'Daily',
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
    'Never participated': '#4C78A8',
    'Once per month or less': '#F58518',
    'Few times per month': '#54A24B',
    'Weekly': '#E45756',
    'Daily': '#B279A2',
}


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

        mask_2020 = df['Year'] == '2020'
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
        df[col_name] = df[col_name].astype(str).str.strip()
        df[col_name] = df[col_name].replace(participation_map)
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
    
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.bar(shares.index, shares.values)
            ax.set_ylim(0.0, 1.0)
            ax.set_yticks([i / 10 for i in range(11)])
            ax.set_ylabel('Share of answers')
            ax.set_xlabel(f'{column_name}')
            ax.set_title(f'{column_name} answer distribution')
            plt.xticks(rotation=30, ha='right')
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

    def plot_fulltime_participation(self, employment_status: str):
        """
        Bar plot of Participates_in_questions frequency for respondents
        in employment status x. Ignores NaN. Y-axis is share of that subgroup.
        """
        employed = self.df[self.df['Employment_Status'] == employment_status]
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
        ax.set_ylabel(f'Share of {employment_status} respondents')
        ax.set_xlabel('Participation frequency in Q&A')
        ax.set_title(f'Q&A participation among {employment_status}')
        plt.tight_layout()
        plt.show()
        return shares

    def plot_age_participation_stacked(self):
        """
        Stacked bar chart: for each age group, share of participation frequencies.
        Each stack segment is participation / age-group total.
        """
        filtered = self.df[
            self.df['Age'].isin(AGE_BINS_ORDER)
            & self.df['Participates_in_questions'].isin(PARTICIPATION_ORDER)
        ].copy()
        filtered['Age_short'] = filtered['Age'].map(AGE_SHORT_LABELS)

        shares = (
            pd.crosstab(filtered['Age_short'], filtered['Participates_in_questions'], normalize='index')
            .reindex(index=AGE_SHORT_ORDER, columns=PARTICIPATION_ORDER, fill_value=0.0)
        )

        fig, ax = plt.subplots(figsize=(11, 6))
        bottom = pd.Series(0.0, index=shares.index)
        x = range(len(shares.index))

        for participation in PARTICIPATION_ORDER:
            values = shares[participation]
            ax.bar(
                x,
                values,
                bottom=bottom,
                label=participation,
                color=PARTICIPATION_COLORS[participation],
            )
            bottom = bottom + values

        ax.set_xticks(list(x))
        ax.set_xticklabels(shares.index)
        ax.set_ylim(0.0, 1.0)
        ax.set_yticks([i / 10 for i in range(11)])
        ax.set_ylabel('Share within age group')
        ax.set_xlabel('Age group')
        ax.set_title('Q&A participation by age group')
        ax.legend(title='Participation', bbox_to_anchor=(1.02, 1), loc='upper left')
        plt.tight_layout()
        plt.show()
        return shares

    def compare_answer_with_column(self, columnA: str, answerA: str, columnB: str):
        """condenses dataset to those who gave a specific answer in columnA, and then 
        removes all columns except columnB. Its usage is to see correlation between
        columns"""
        only_answer = self.df[self.df[columnA] == answerA]
        corr_vec = only_answer[only_answer[columnB].notna()]
        return corr_vec

    def plot_compare_answer_with_column(self, columnA: str, answerA: str, columnB: str):
        """
        Filter by `columnA == answerA`, then plot the percentage distribution
        of non-null answers in `columnB`.
        """
        corr_df = self.compare_answer_with_column(columnA, answerA, columnB)
        counts = corr_df[columnB].value_counts()
        shares = counts / len(corr_df)

        fig, ax = plt.subplots(figsize=(11, 5))
        ax.bar(range(len(shares)), shares.values)
        ax.set_xticks(range(len(shares)))
        ax.set_xticklabels(shares.index, rotation=45, ha='right')
        ax.set_ylim(0.0, 1.0)
        ax.set_yticks([i / 10 for i in range(11)])
        ax.set_ylabel('Percentage of filtered rows')
        ax.set_xlabel(columnB)
        ax.set_title(f'{columnB} distribution for {columnA} = {answerA}')
        plt.tight_layout()
        plt.show()
        return shares

    def plot_stacked_by_columns(self, columnA: str, columnB: str, orderA=None, orderB=None):
        """
        Create a stacked bar plot where x-axis is `columnB`, each bar sums to 1,
        and the stacks are the different answers in `columnA`.
        If provided, `orderA` controls stack order and `orderB` controls x-axis order.
        """
        filtered = self.df[
            self.df[columnA].notna()
            & self.df[columnB].notna()
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

        fig, ax = plt.subplots(figsize=(12, 6))
        bottom = pd.Series(0.0, index=shares.index)
        x = range(len(shares.index))
        cmap = plt.get_cmap('tab20')

        for idx, answer in enumerate(shares.columns):
            values = shares[answer]
            ax.bar(
                x,
                values,
                bottom=bottom,
                label=answer,
                color=cmap(idx % cmap.N),
            )
            bottom = bottom + values

        ax.set_xticks(list(x))
        ax.set_xticklabels(shares.index, rotation=45, ha='right')
        ax.set_ylim(0.0, 1.0)
        ax.set_yticks([i / 10 for i in range(11)])
        ax.set_ylabel('Percentage')
        ax.set_xlabel(columnB)
        ax.set_title(f'{columnA} distribution within {columnB}')
        ax.legend(title=columnA, bbox_to_anchor=(1.02, 1), loc='upper left')
        plt.tight_layout()
        plt.show()
        return shares
