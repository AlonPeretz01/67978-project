import os
import re
import pandas as pd

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
RAW_DIR = os.path.join(PROJECT_ROOT, 'data', 'raw')
CLEAN_DIR = os.path.join(PROJECT_ROOT, 'data', 'clean')
THRESHOLD = 80.0

def clean_survey_data():
    if not os.path.exists(CLEAN_DIR):
        os.makedirs(CLEAN_DIR)
        
    for root, dirs, files in os.walk(RAW_DIR):
        for dir_name in dirs:
            match = re.search(r'20[1-2][0-9]', dir_name)
            if not match:
                continue
                
            year = match.group(0)
            year_path = os.path.join(root, dir_name)
            
            csv_files = [f for f in os.listdir(year_path) 
                         if f.endswith('.csv') and 'schema' not in f.lower()]
            
            if csv_files:
                file_path = os.path.join(year_path, csv_files[0])
                print(f"Cleaning {year}...")
                
                try:
                    df = pd.read_csv(file_path, low_memory=False)
                except UnicodeDecodeError:
                    df = pd.read_csv(file_path, low_memory=False, encoding='latin1')
                    
                unnamed_cols = [c for c in df.columns if 'unnamed' in str(c).lower()]
                df.drop(columns=unnamed_cols, inplace=True)
                
                null_pct = (df.isnull().sum() / len(df)) * 100
                cols_to_drop = null_pct[null_pct > THRESHOLD].index
                df.drop(columns=cols_to_drop, inplace=True)
                
                out_dir = os.path.join(CLEAN_DIR, f'stack-overflow-developer-survey-{year}')
                os.makedirs(out_dir, exist_ok=True)
                out_path = os.path.join(out_dir, f'survey_results_public_{year}_cleaned.csv')
                
                df.to_csv(out_path, index=False)
                print(f"Saved {year} | Dropped {len(unnamed_cols)} Unnamed, {len(cols_to_drop)} >{THRESHOLD}% nulls. Remaining: {df.shape[1]} cols")
                
                if year in ['2011', '2012', '2013', '2014', '2015', '2016', '2017', '2018', '2019', '2020', '2021', '2022', '2023', '2024', '2025']:
                    print(f"\n--- {year} Matching Columns ---")
                    target_keywords = ['age', 'year', 'ed', 'employ', 'comp', 'salary', 'ai', 'stack', 'occup']
                    matching_cols = [c for c in df.columns if any(k in c.lower() for k in target_keywords)]
                    for col in matching_cols:
                        print(f"  - {col}")

if __name__ == "__main__":
    clean_survey_data()
    print("\nData cleaning complete.")