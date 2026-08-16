import os
import logging

import pandas as pd

from src.cleaning.clean_data import YEARS, clean_survey_data
# from clean_data import YEARS, clean_survey_data

# Define paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
RAW_DIR = os.path.join(PROJECT_ROOT, 'data', 'raw')
PROCESSED_DIR = os.path.join(PROJECT_ROOT, 'data', 'processed')
LOGGER = logging.getLogger(__name__)

# Core schema - target columns to retain across all years
TARGET_COLUMNS = [
    'Year', # Manually added column to track the timeline
    'Age', 
    'Education_Level', 
    'Years_of_Experience', 
    'Employment_Status', 
    'Yearly_Compensation', 
    'Usage_Frequency', 
    'AI_Tool_Usage',
    'AI_Usage_Status',
    'Has_SO_account',
    'Part_of_community',
    'Participates_in_questions',
    'Visits_SO_freq'
]

# These survey instruments do not provide the same professional-experience
# measure used elsewhere.  Preserve that provenance in the master dataset.
EXPERIENCE_PROXY_YEARS = {'2015', '2016', '2025'}

# Harmonization Dictionary (Schema mapping for all years)
schema_mapping = {
    '2011': {
        'How old are you?': 'Age',
        'How many years of IT/Programming experience do you have?': 'Years_of_Experience',
        'Which of the following best describes your occupation?': 'Employment_Status',
        'Including bonus, what is your annual compensation in USD?': 'Yearly_Compensation',
    },
    '2012': {
        'How many years of IT/Programming experience do you have?': 'Years_of_Experience',
        'Which of the following best describes your occupation?': 'Employment_Status',
        'Including bonus, what is your annual compensation in USD?': 'Yearly_Compensation',
    },
    '2013': {
        'How many years of IT/Programming experience do you have?': 'Years_of_Experience',
        'Which of the following best describes your occupation?': 'Employment_Status',
        'Including bonus, what is your annual compensation in USD?': 'Yearly_Compensation',
    },
    '2014': {
        'How many years of IT/Programming experience do you have?': 'Years_of_Experience',
        'Which of the following best describes your occupation?': 'Employment_Status',
        'Including bonus, what is your annual compensation in USD?': 'Yearly_Compensation',
    },
    '2015': {
        'Age': 'Age',
        'Years IT / Programming Experience': 'Years_of_Experience',
        'Occupation': 'Employment_Status',
        'Employment Status': 'Employment_Status',
        'Compensation': 'Yearly_Compensation',
        'Compensation: midpoint': 'Yearly_Compensation',
    },
    '2016': {
        'age_midpoint': 'Age',
        'occupation': 'Employment_Status',
        'education': 'Education_Level',
        'experience_range': 'Years_of_Experience',
        'salary_midpoint': 'Yearly_Compensation',
    },
    '2017': {
        'EmploymentStatus': 'Employment_Status',
        'FormalEducation': 'Education_Level',
        'YearsCodedJob': 'Years_of_Experience',
        'Salary': 'Yearly_Compensation',
        'StackOverflowVisit': 'Usage_Frequency',
        'StackOverflowCommunity': 'Part_of_community',
    },
    '2018': {
        'Age': 'Age',
        'Employment': 'Employment_Status',
        'FormalEducation': 'Education_Level',
        'YearsCodingProf': 'Years_of_Experience',
        'ConvertedSalary': 'Yearly_Compensation',
        'StackOverflowVisit': 'Usage_Frequency',
        'StackOverflowParticipation': 'Participates_in_questions',
        'StackOverflowConsiderMember': 'Part_of_community',
    },
    '2019': {
        'Age': 'Age',
        'Employment': 'Employment_Status',
        'EdLevel': 'Education_Level',
        'YearsCodePro': 'Years_of_Experience',
        'ConvertedComp': 'Yearly_Compensation',
        'SOPartFreq': 'Participates_in_questions',
        'SOComm': 'Part_of_community',
        'SOVisitFreq': 'Visits_SO_freq'
    },
    '2020': {
        'Age': 'Age',
        'Employment': 'Employment_Status',
        'EdLevel': 'Education_Level',
        'YearsCodePro': 'Years_of_Experience',
        'ConvertedComp': 'Yearly_Compensation',
        'SOAccount': 'Has_SO_account',
        'SOPartFreq': 'Participates_in_questions',
        'SOComm': 'Part_of_community',
        'SOVisitFreq': 'Visits_SO_freq'
    },
    '2021': {
        'Age': 'Age',
        'Employment': 'Employment_Status',
        'EdLevel': 'Education_Level',
        'YearsCodePro': 'Years_of_Experience',
        'ConvertedCompYearly': 'Yearly_Compensation',
        'SOAccount': 'Has_SO_account',
        'SOPartFreq': 'Participates_in_questions',
        'SOComm': 'Part_of_community',
        'SOVisitFreq': 'Visits_SO_freq'
    },
    '2022': {
        'Age': 'Age',
        'Employment': 'Employment_Status',
        'EdLevel': 'Education_Level',
        'YearsCodePro': 'Years_of_Experience',
        'ConvertedCompYearly': 'Yearly_Compensation',
        'SOAccount': 'Has_SO_account',
        'SOPartFreq': 'Participates_in_questions',
        'SOComm': 'Part_of_community',
        'SOVisitFreq': 'Visits_SO_freq'
    },
    '2023': {
        'Age': 'Age',
        'Employment': 'Employment_Status',
        'EdLevel': 'Education_Level',
        'YearsCodePro': 'Years_of_Experience',
        'ConvertedCompYearly': 'Yearly_Compensation',
        'AISelect': 'AI_Usage_Status',
        'AIToolCurrently Using': 'AI_Tool_Usage',
        'SOPartFreq': 'Participates_in_questions',
        'SOComm': 'Part_of_community',
        'SOVisitFreq': 'Visits_SO_freq'
    },
    '2024': {
        'Age': 'Age',
        'Employment': 'Employment_Status',
        'EdLevel': 'Education_Level',
        'YearsCodePro': 'Years_of_Experience',
        'ConvertedCompYearly': 'Yearly_Compensation',
        'AISelect': 'AI_Usage_Status',
        'AIToolCurrently Using': 'AI_Tool_Usage',
        'SOPartFreq': 'Participates_in_questions',
        'SOComm': 'Part_of_community',
        'SOVisitFreq': 'Visits_SO_freq'
    },
    '2025': {
        'Age': 'Age',
        'Employment': 'Employment_Status',
        'EdLevel': 'Education_Level',
        # 2025 does not publish YearsCodePro; YearsCode is total coding
        # experience and is retained only as an explicitly tagged proxy.
        'YearsCode': 'Years_of_Experience',
        'ConvertedCompYearly': 'Yearly_Compensation',
        'AISelect': 'AI_Usage_Status',
        'SOAccount': 'Has_SO_account',
        'SOPartFreq': 'Participates_in_questions',
        'SOComm': 'Part_of_community',
        'SOVisitFreq': 'Visits_SO_freq'
    }
}

def harmonize_schema(df, year):
    """
    Maps DataFrame columns based on the survey year and retains only the core columns.
    """
    year = str(year)
    mapping = schema_mapping.get(year, {})
    harmonized = pd.DataFrame(index=df.index)
    harmonized['Year'] = year

    expected_targets = set(mapping.values())

    for target in TARGET_COLUMNS[1:]:
        source_columns = [
            source for source, mapped_target in mapping.items()
            if mapped_target == target and source in df.columns
        ]
        if target in df.columns and target not in source_columns:
            source_columns.insert(0, target)

        if len(source_columns) == 1:
            harmonized[target] = df[source_columns[0]]
        elif len(source_columns) > 1:
            harmonized[target] = df[source_columns].bfill(axis=1).iloc[:, 0]
        else:
            harmonized[target] = pd.NA

        if year in {'2015', '2016'} and target == 'Years_of_Experience' and source_columns:
            LOGGER.info(
                "Harmonized %s professional experience from observed raw column(s): %s",
                year,
                ', '.join(source_columns),
            )

    collapsed_targets = [
        target for target in expected_targets
        if target in harmonized.columns and harmonized[target].notna().sum() == 0
    ]
    if expected_targets and len(collapsed_targets) > len(expected_targets) / 2:
        raise ValueError(
            f"{year}: {len(collapsed_targets)} of {len(expected_targets)} columns "
            f"schema_mapping expects for this year are entirely null "
            f"({', '.join(sorted(collapsed_targets))}). A single sparse column is "
            f"expected sometimes, but this many failing at once means the cleaned "
            f"input likely lost its expected raw columns (e.g. a misread header "
            f"renaming them all to 'Unnamed: N') before harmonization ran."
        )

    experience_is_proxy = (
        year in EXPERIENCE_PROXY_YEARS
        and harmonized['Years_of_Experience'].notna()
    )
    harmonized['experience_is_proxy'] = experience_is_proxy
    return harmonized.reindex(columns=[*TARGET_COLUMNS, 'experience_is_proxy'])

def run_harmonization_pipeline():
    if not os.path.exists(PROCESSED_DIR):
        os.makedirs(PROCESSED_DIR)
        
    harmonized_dfs = []
    
    print("Starting Data Harmonization Process...")
    
    cleaned_paths = clean_survey_data()

    for year in YEARS:
        year = str(year)
        file_path = cleaned_paths.get(year)
        if file_path is None:
            print(f"Skipping harmonization for {year}: no cleaned CSV was generated.")
            continue

        print(f"Harmonizing {year}...")
        print(f"Reading file: {file_path}")
        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension in {'.xls', '.xlsx', '.xlsm', '.xlsb', '.ods'}:
            df = pd.read_excel(file_path)
        else:
            try:
                df = pd.read_csv(file_path, low_memory=False)
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, low_memory=False, encoding='latin1')

        harmonized_df = harmonize_schema(df, str(year))
        harmonized_dfs.append(harmonized_df)

        print(f"  -> Extracted {harmonized_df.shape[1]} core columns.")

      # Display the first 3 rows of the last harmonized DataFrame for verification
    # Concatenate all DataFrames into a single central dataset
    if harmonized_dfs:
        year_2019 = harmonized_dfs[YEARS.index(2019)]
        print("\nConcatenating all years into a single dataset...")
        final_dataset = pd.concat(harmonized_dfs, ignore_index=True)
        
        # Save the final output
        out_path = os.path.join(PROCESSED_DIR, 'harmonized_stack_overflow_2011_2025.csv')
        final_dataset.to_csv(out_path, index=False)
        
        print(f"\nSuccess! Final dataset saved to: {out_path}")
        print(f"Total rows: {final_dataset.shape[0]}, Total columns: {final_dataset.shape[1]}")
    else:
        print("No raw survey CSV files were found to harmonize.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_harmonization_pipeline()
    