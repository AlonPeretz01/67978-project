import os
import pandas as pd

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
RAW_DIR = os.path.join(PROJECT_ROOT, 'data', 'raw')
CLEAN_DIR = os.path.join(PROJECT_ROOT, 'data', 'clean')
THRESHOLD = 80.0

def clean_survey_data():
    if not os.path.exists(CLEAN_DIR):
        os.makedirs(CLEAN_DIR)
        
    for year in sorted(os.listdir(RAW_DIR)):
        if not (year.isdigit() and len(year) == 4):
            continue

        file_path = os.path.join(RAW_DIR, str(year), 'survey_results_public.csv')
        if not os.path.isfile(file_path):
            continue

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

        out_dir = os.path.join(CLEAN_DIR, str(year))
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f'survey_results_public_{year}_cleaned.csv')

        df.to_csv(out_path, index=False)
        print(f"Saved {year} | Dropped {len(unnamed_cols)} Unnamed, {len(cols_to_drop)} >{THRESHOLD}% nulls. Remaining: {df.shape[1]} cols")

        print(f"\n--- {year} Matching Columns ---")
        target_keywords = ['age', 'year', 'ed', 'employ', 'comp', 'salary', 'ai', 'stack', 'occup']
        matching_cols = [c for c in df.columns if any(k in c.lower() for k in target_keywords)]
        for col in matching_cols:
            print(f"  - {col}")

if __name__ == "__main__":
    clean_survey_data()
    print("\nData cleaning complete.")
