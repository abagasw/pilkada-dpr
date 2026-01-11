import pandas as pd
import os
from pathlib import Path

# Directory containing all the CSV files
csv_dir = r'data\tiktok_comments_csv'
output_file = r'data\tiktok_comments_combined.csv'

# Get all CSV files
csv_files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]
print(f"Found {len(csv_files)} CSV files to combine\n")

# Read and combine all CSV files
dataframes = []
for i, file in enumerate(csv_files, 1):
    file_path = os.path.join(csv_dir, file)
    try:
        df = pd.read_csv(file_path)
        dataframes.append(df)
        if i % 100 == 0:
            print(f"Loaded {i}/{len(csv_files)} files...")
    except Exception as e:
        print(f"❌ Error loading {file}: {str(e)}")

# Combine all dataframes
print("\nCombining all dataframes...")
combined_df = pd.concat(dataframes, ignore_index=True)

# Save to single CSV file
print(f"Saving combined data to {output_file}...")
combined_df.to_csv(output_file, index=False, encoding='utf-8')

# Print summary
print(f"\n{'='*60}")
print(f"MERGE SUMMARY")
print(f"{'='*60}")
print(f"Total files combined: {len(csv_files)}")
print(f"Total rows: {len(combined_df):,}")
print(f"Total columns: {len(combined_df.columns)}")
print(f"\nColumns: {', '.join(combined_df.columns.tolist())}")
print(f"\n✅ Combined CSV saved to: {os.path.abspath(output_file)}")
print(f"File size: {os.path.getsize(output_file) / (1024*1024):.2f} MB")
