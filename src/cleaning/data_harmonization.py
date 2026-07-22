import os
import re
import pandas as pd

# Define paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
CLEAN_DIR = os.path.join(PROJECT_ROOT, 'data', 'clean')
PROCESSED_DIR = os.path.join(PROJECT_ROOT, 'data', 'processed')

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
    'AI_Usage_Status'
]

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
        'EmploymentStatus': 'Employment_Status',
        'Involved': 'Employment_Status', 
        'YearsCode': 'Years_of_Experience',
        'Salary': 'Yearly_Compensation',
    },
    '2016': {
        'age_midpoint': 'Age',
        'occupation': 'Employment_Status',
        'education': 'Education_Level',
        'salary_midpoint': 'Yearly_Compensation',
    },
    '2017': {
        'EmploymentStatus': 'Employment_Status',
        'FormalEducation': 'Education_Level',
        'YearsCodedJob': 'Years_of_Experience',
        'Salary': 'Yearly_Compensation',
        'StackOverflowVisit': 'Usage_Frequency',
    },
    '2018': {
        'Age': 'Age',
        'Employment': 'Employment_Status',
        'FormalEducation': 'Education_Level',
        'YearsCodingProf': 'Years_of_Experience',
        'ConvertedSalary': 'Yearly_Compensation',
        'StackOverflowVisit': 'Usage_Frequency',
    },
    '2019': {
        'Age': 'Age',
        'Employment': 'Employment_Status',
        'EdLevel': 'Education_Level',
        'YearsCodePro': 'Years_of_Experience',
        'ConvertedComp': 'Yearly_Compensation',
    },
    '2020': {
        'Age': 'Age',
        'Employment': 'Employment_Status',
        'EdLevel': 'Education_Level',
        'YearsCodePro': 'Years_of_Experience',
        'ConvertedComp': 'Yearly_Compensation',
    },
    '2021': {
        'Age': 'Age',
        'Employment': 'Employment_Status',
        'EdLevel': 'Education_Level',
        'YearsCodePro': 'Years_of_Experience',
        'ConvertedCompYearly': 'Yearly_Compensation',
    },
    '2022': {
        'Age': 'Age',
        'Employment': 'Employment_Status',
        'EdLevel': 'Education_Level',
        'YearsCodePro': 'Years_of_Experience',
        'ConvertedCompYearly': 'Yearly_Compensation',
    },
    '2023': {
        'Age': 'Age',
        'Employment': 'Employment_Status',
        'EdLevel': 'Education_Level',
        'YearsCodePro': 'Years_of_Experience',
        'ConvertedCompYearly': 'Yearly_Compensation',
        'AISelect': 'AI_Usage_Status',
        'AIToolCurrently Using': 'AI_Tool_Usage',
    },
    '2024': {
        'Age': 'Age',
        'Employment': 'Employment_Status',
        'EdLevel': 'Education_Level',
        'YearsCodePro': 'Years_of_Experience',
        'ConvertedCompYearly': 'Yearly_Compensation',
        'AISelect': 'AI_Usage_Status',
        'AIToolCurrently Using': 'AI_Tool_Usage',
    },
    '2025': {
        'Age': 'Age',
        'Employment': 'Employment_Status',
        'EdLevel': 'Education_Level',
        'YearsCodePro': 'Years_of_Experience',
        'ConvertedCompYearly': 'Yearly_Compensation',
        'AISelect': 'AI_Usage_Status',
    }
}

def harmonize_schema(df, year):
    """
    Maps DataFrame columns based on the survey year and retains only the core columns.
    """
    # Rename columns if a mapping exists for the current year
    if year in schema_mapping:
        df = df.rename(columns=schema_mapping[year])
    
    # Add survey year as a column for longitudinal analysis
    df['Year'] = year
    
    # Keep only the core columns that exist in the current DataFrame
    existing_targets = [col for col in TARGET_COLUMNS if col in df.columns]
    
    return df[existing_targets]

def run_harmonization_pipeline():
    if not os.path.exists(PROCESSED_DIR):
        os.makedirs(PROCESSED_DIR)
        
    harmonized_dfs = []
    
    print("Starting Data Harmonization Process...")
    
    # Iterate through all directories and files in the clean data directory
    for root, dirs, files in os.walk(CLEAN_DIR):
        for file in files:
            if file.endswith('.csv'):
                # Extract the year from the file or directory name
                match = re.search(r'20[1-2][0-9]', file)
                if not match:
                    match = re.search(r'20[1-2][0-9]', root)
                    
                if match:
                    year = match.group(0)
                    file_path = os.path.join(root, file)
                    
                    print(f"Harmonizing {year}...")
                    
                    # Read the cleaned CSV file
                    df = pd.read_csv(file_path, low_memory=False)
                    
                    # Apply the harmonization function
                    harmonized_df = harmonize_schema(df, year)
                    harmonized_dfs.append(harmonized_df)
                    
                    print(f"  -> Extracted {harmonized_df.shape[1]} core columns.")

    # Concatenate all DataFrames into a single central dataset
    if harmonized_dfs:
        print("\nConcatenating all years into a single dataset...")
        final_dataset = pd.concat(harmonized_dfs, ignore_index=True)
        
        # Save the final output
        out_path = os.path.join(PROCESSED_DIR, 'harmonized_stack_overflow_2011_2025.csv')
        final_dataset.to_csv(out_path, index=False)
        
        print(f"\nSuccess! Final dataset saved to: {out_path}")
        print(f"Total rows: {final_dataset.shape[0]}, Total columns: {final_dataset.shape[1]}")
    else:
        print("No cleaned CSV files were found to harmonize.")

if __name__ == "__main__":
    run_harmonization_pipeline()