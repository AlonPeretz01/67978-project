import pandas as pd

file_path = 'data/processed/harmonized_stack_overflow_2011_2025.csv'
df = pd.read_csv(file_path, low_memory=False)

print("=== 1. Dataset Shape ===")
print(f"Total Rows: {df.shape[0]:,}")
print(f"Total Columns: {df.shape[1]}")
print(f"Columns: {list(df.columns)}\n")

print("=== 2. Rows per Year ===")
if 'Year' in df.columns:
    print(df['Year'].value_counts().sort_index())
else:
    print("Checking index or available data distribution...")
print()

print("=== 3. Missing Values Percentage per Column ===")
missing = (df.isnull().sum() / len(df)) * 100
print(missing.round(2))
print()

print("=== 4. Sample Data (First 3 rows) ===")
print(df.head(3))