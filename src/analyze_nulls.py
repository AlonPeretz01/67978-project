import os
import re
import pandas as pd

DATA_DIR = 'data/raw'

def analyze_nulls_per_year(data_path):
    """Scans data directory and calculates null percentages per column."""
    null_summary = {}
    
    for root, dirs, files in os.walk(data_path):
        for dir_name in dirs:
            match = re.search(r'20[1-2][0-9]', dir_name)
            if not match:
                continue
                
            year = match.group(0)
            year_path = os.path.join(root, dir_name)
            
            # Filter out schema and metadata files
            csv_files = [f for f in os.listdir(year_path) 
                         if f.endswith('.csv') 
                         and 'schema' not in f.lower() 
                         and 'crosswalk' not in f.lower()
                         and 'questions' not in f.lower()]
            
            if csv_files:
                file_path = os.path.join(year_path, csv_files[0])
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
    results = analyze_nulls_per_year(DATA_DIR)
    
    for year, nulls in results.items():
        print(f"\n--- Top Null Percentages for {year} ---")
        print(nulls.head(10)) 
        
    print("\nAnalysis complete! Ready for EDA.")
    