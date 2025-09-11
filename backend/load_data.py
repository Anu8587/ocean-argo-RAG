import pandas as pd
from sqlalchemy import create_engine, text
import json
import numpy as np
import os
import gc

# --- DATABASE CONFIGURATION ---
DB_USER = 'postgres'
DB_PASSWORD = 'anushka'
DB_HOST = 'localhost'
DB_PORT = '5432'
DB_NAME = 'floatchat_db'

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def test_db_connection():
    """Test PostgreSQL connection"""
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            print("Database connection successful!")
        return engine
    except Exception as e:
        print(f"Database connection failed: {e}")
        return None

def load_csv_to_db(csv_path, chunk_size=50000):
    print(f"Step 1: Loading CSV '{csv_path}'...")
    
    # Check if file exists
    if not os.path.exists(csv_path):
        print(f"--- ❌ Error: File '{csv_path}' not found! ---")
        return
    
    # Test DB connection
    engine = test_db_connection()
    if not engine:
        return
    
    stats_log = []
    all_profiles = []
    total_rows_read = 0
    total_unique_pairs = 0
    
    try:
        # Check for QC columns (case-insensitive)
        first_chunk = pd.read_csv(csv_path, skiprows=[1], nrows=1000)
        qc_columns = [col for col in first_chunk.columns if col.lower().endswith('_qc')]
        stats_log.append(f"QC columns detected: {qc_columns}")
        print(f"QC columns in CSV: {qc_columns}")
        
        for chunk_idx, chunk in enumerate(pd.read_csv(csv_path, skiprows=[1], chunksize=chunk_size, low_memory=False)):
            print(f"\nProcessing chunk {chunk_idx + 1} ({len(chunk)} rows)...")
            total_rows_read += len(chunk)
            
            # Log chunk stats
            nan_temp = chunk['temp_adjusted'].isna().sum()
            nan_pres = chunk['pres_adjusted'].isna().sum()
            nan_psal = chunk['psal_adjusted'].isna().sum()
            unique_pairs = len(chunk[['platform_number', 'time']].drop_duplicates())
            total_unique_pairs += unique_pairs
            chunk_stats = (f"Chunk {chunk_idx + 1}: {len(chunk)} rows, "
                         f"NaNs: temp={nan_temp} ({nan_temp/len(chunk)*100:.1f}%), "
                         f"pres={nan_pres} ({nan_pres/len(chunk)*100:.1f}%), "
                         f"psal={nan_psal} ({nan_psal/len(chunk)*100:.1f}%), "
                         f"Unique (platform, time): {unique_pairs}")
            print(chunk_stats)
            stats_log.append(chunk_stats)
            
            # No row-level dropna; rely on array filtering
            chunk_clean = chunk
            print(f"  - Valid rows in chunk: {len(chunk_clean)} (no rows dropped)")
            stats_log.append(f"Chunk {chunk_idx + 1}: Dropped 0, Valid {len(chunk_clean)}")
            
            if len(chunk_clean) == 0:
                stats_log.append(f"Chunk {chunk_idx + 1}: Skipped (no valid rows)")
                continue
            
            # Group into profiles
            print("  - Grouping into profiles...")
            agg_functions = {
                'latitude': 'first',
                'longitude': 'first',
                'pres_adjusted': lambda x: json.dumps([v for v in x if pd.notna(v)]),
                'temp_adjusted': lambda x: json.dumps([v for v in x if pd.notna(v)]),
                'psal_adjusted': lambda x: json.dumps([v for v in x if pd.notna(v)])
            }
            chunk_profiles = chunk_clean.groupby(['platform_number', 'time']).agg(agg_functions).reset_index()
            
            chunk_profiles.rename(columns={
                'platform_number': 'float_id',
                'time': 'profile_date',
                'pres_adjusted': 'pressure_levels',
                'temp_adjusted': 'temperature_values',
                'psal_adjusted': 'salinity_values'
            }, inplace=True)
            
            # Check for empty arrays
            empty_temp = sum(len(json.loads(row['temperature_values'])) == 0 for _, row in chunk_profiles.iterrows())
            empty_pres = sum(len(json.loads(row['pressure_levels'])) == 0 for _, row in chunk_profiles.iterrows())
            empty_psal = sum(len(json.loads(row['salinity_values'])) == 0 for _, row in chunk_profiles.iterrows())
            print(f"  - Profiles in chunk: {len(chunk_profiles)}, Empty temp: {empty_temp}, pres: {empty_pres}, psal: {empty_psal}")
            stats_log.append(f"Chunk {chunk_idx + 1}: {len(chunk_profiles)} profiles, Empty temp: {empty_temp}, pres: {empty_pres}, psal: {empty_psal}")
            
            all_profiles.append(chunk_profiles)
            
            # Clear memory
            del chunk, chunk_clean, chunk_profiles
            gc.collect()
        
        # Combine and insert
        if all_profiles:
            profiles = pd.concat(all_profiles, ignore_index=True)
            final_profiles = len(profiles)
            print(f"\nStep 3: Combined {final_profiles} unique profiles from {total_rows_read} rows.")
            stats_log.append(f"Final: {final_profiles} profiles from {total_rows_read} rows (Total unique pairs: {total_unique_pairs})")
            
            # No array filtering; keep all profiles
            print(f"  - After filtering: {len(profiles)} profiles (no empty array filter)")
            stats_log.append(f"After filtering: {len(profiles)} profiles")
            
            # Print sample profile
            if len(profiles) > 0:
                print("\nSample profile:")
                print(profiles.iloc[0][['float_id', 'profile_date', 'latitude', 'longitude', 
                                      'temperature_values', 'pressure_levels', 'salinity_values']].to_dict())
                stats_log.append(f"Sample profile: {profiles.iloc[0][['float_id', 'profile_date', 'latitude', 'longitude']].to_dict()}")
            
            # Insert to DB
            print("Step 4: Inserting profiles to database...")
            profiles.to_sql('argo_profiles', engine, if_exists='replace', index=False, chunksize=10000)
            
            # Verify DB count
            db_count = pd.read_sql("SELECT COUNT(*) as count FROM argo_profiles", engine)['count'].iloc[0]
            print(f"Final DB row count: {db_count}")
            stats_log.append(f"DB count: {db_count} profiles")
            
            # Add indexes
            print("Step 5: Adding indexes for performance...")
            with engine.connect() as conn:
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_float_id ON argo_profiles(float_id);"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_profile_date ON argo_profiles(profile_date);"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_location ON argo_profiles(latitude, longitude);"))
                conn.commit()
            
            print("\n--- ✅ Success! Loaded profiles into 'argo_profiles' table. ---")
        else:
            print("--- ❌ No valid profiles found! ---")
            stats_log.append("No valid profiles")
    
    except Exception as e:
        print(f"\n--- ❌ Error occurred: {e} ---")
        stats_log.append(f"Error: {str(e)}")
    
    finally:
        # Save stats even if error occurs
        with open('load_stats.txt', 'w') as f:
            f.write("\n".join(stats_log))
        print("Stats saved to 'load_stats.txt'.")

# --- To run this script ---
if __name__ == '__main__':
    csv_file = 'argo_sample_sept2025.csv'  # Update if needed
    load_csv_to_db(csv_file)