import os
import pandas as pd
import matplotlib.pyplot as plt

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
RAW_DIR = os.path.join(PROJECT_ROOT, 'data', 'raw')

def get_null_dataframe(data_path):
    """Extracts null percentages for all columns across all years into a single DataFrame."""
    records = []
    
    for year in sorted(os.listdir(data_path)):
        if not (year.isdigit() and len(year) == 4):
            continue

        file_path = os.path.join(data_path, str(year), 'survey_results_public.csv')
        if not os.path.isfile(file_path):
            continue

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
    df = get_null_dataframe(RAW_DIR)
    
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
