import os
import re
import pandas as pd
import matplotlib.pyplot as plt

DATA_DIR = 'data/raw'

def get_null_dataframe(data_path):
    """Extracts null percentages for all columns across all years into a single DataFrame."""
    records = []
    
    for root, dirs, files in os.walk(data_path):
        for dir_name in dirs:
            match = re.search(r'20[1-2][0-9]', dir_name)
            if not match:
                continue
                
            year = match.group(0)
            year_path = os.path.join(root, dir_name)
            
            csv_files = [f for f in os.listdir(year_path) 
                         if f.endswith('.csv') 
                         and 'schema' not in f.lower() 
                         and 'crosswalk' not in f.lower()
                         and 'questions' not in f.lower()]
            
            if csv_files:
                file_path = os.path.join(year_path, csv_files[0])
                print(f"Processing {year}...")
                
                try:
                    df = pd.read_csv(file_path, low_memory=False)
                except UnicodeDecodeError:
                    df = pd.read_csv(file_path, low_memory=False, encoding='latin1')
                except Exception:
                    continue
                    
                null_pct = (df.isnull().sum() / len(df)) * 100
                for col_name, pct in null_pct.items():
                    records.append({'Year': int(year), 'Column': col_name, 'Null_Percentage': pct})
                    
    return pd.DataFrame(records)

if __name__ == "__main__":
    print("Gathering data for visualization...")
    df = get_null_dataframe(DATA_DIR)
    
    print("Generating plot...")
    df.sort_values('Year', inplace=True)
    
    # Create the Boxplot
    plt.figure(figsize=(14, 7))
    df.boxplot(column='Null_Percentage', by='Year', grid=True)
    
    plt.title('Distribution of Null Percentages per Column (2011-2025)')
    plt.suptitle('') 
    plt.xlabel('Survey Year')
    plt.ylabel('Percentage of Missing Values (%)')
    
    # Add a reference line at 80% to help visually decide on a threshold
    plt.axhline(y=80, color='r', linestyle='--', alpha=0.7, label='80% Threshold Reference')
    plt.legend()
    
    output_path = 'null_distribution_plot.png'
    plt.tight_layout()
    plt.savefig(output_path)
    
    print(f"Plot saved successfully to {output_path}")
    plt.show()