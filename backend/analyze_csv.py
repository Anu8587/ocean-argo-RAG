import pandas as pd
import numpy as np

# Path to your large CSV
csv_path = 'argo_sample_sept2025.csv'  # Update if different

print("Analyzing CSV...")

# Read in chunks to handle large file
chunk_size = 100000  # Adjust if needed
total_rows = 0
nan_counts = {'temp_adjusted': 0, 'pres_adjusted': 0, 'psal_adjusted': 0}
unique_profiles_before_clean = set()

for chunk in pd.read_csv(csv_path, skiprows=[1], chunksize=chunk_size):
    total_rows += len(chunk)
    
    # Count NaNs in this chunk
    nan_counts['temp_adjusted'] += chunk['temp_adjusted'].isna().sum()
    nan_counts['pres_adjusted'] += chunk['pres_adjusted'].isna().sum()
    nan_counts['psal_adjusted'] += chunk['psal_adjusted'].isna().sum()
    
    # Estimate unique profiles (before any cleaning)
    chunk_profiles = chunk[['platform_number', 'time']].drop_duplicates()
    unique_profiles_before_clean.update(chunk_profiles['platform_number'].astype(str) + '_' + chunk_profiles['time'].astype(str))

print(f"\n--- CSV Analysis Results ---")
print(f"Total rows in CSV: {total_rows}")
print(f"NaNs in temp_adjusted: {nan_counts['temp_adjusted']} ({nan_counts['temp_adjusted']/total_rows*100:.1f}%)")
print(f"NaNs in pres_adjusted: {nan_counts['pres_adjusted']} ({nan_counts['pres_adjusted']/total_rows*100:.1f}%)")
print(f"NaNs in psal_adjusted: {nan_counts['psal_adjusted']} ({nan_counts['psal_adjusted']/total_rows*100:.1f}%)")
print(f"Estimated unique profiles before cleaning: {len(unique_profiles_before_clean)}")

# Quick sample of first 10 rows
df_sample = pd.read_csv(csv_path, skiprows=[1], nrows=10)
print("\nSample data:")
print(df_sample.head())