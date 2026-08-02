import os
import pandas as pd

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
RAW_DIR = os.path.join(PROJECT_ROOT, 'data', 'raw')

def analyze_nulls_per_year(data_path):
    """Scans data directory and calculates null percentages per column."""
    null_summary = {}
    
    for year in sorted(os.listdir(data_path)):
        if not (year.isdigit() and len(year) == 4):
            continue

        file_path = os.path.join(data_path, str(year), 'survey_results_public.csv')
        if not os.path.isfile(file_path):
            continue

        print(f"Loading data for {year}...")

        try:
            df = pd.read_csv(file_path, low_memory=False)
        except UnicodeDecodeError:
            print(f"Encoding error for {year}, retrying with latin1...")
            df = pd.read_csv(file_path, low_memory=False, encoding='latin1')
        except Exception as e:
            print(f"Unexpected error for {year}: {e}")
            continue

        total_rows = len(df)
        null_percentages = (df.isnull().sum() / total_rows) * 100
        null_summary[year] = null_percentages[null_percentages > 0].sort_values(ascending=False)
                    
    return null_summary

if __name__ == "__main__":
    print("Starting data analysis pipeline...")
    results = analyze_nulls_per_year(RAW_DIR)
    
    for year, nulls in results.items():
        print(f"\n--- Top Null Percentages for {year} ---")
        print(nulls.head(10)) 
        
    print("\nAnalysis complete! Ready for EDA.")
    
