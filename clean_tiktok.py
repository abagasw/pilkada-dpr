#!/usr/bin/env python3
"""
Clean TikTok data from raw/tiktok
- Handle list format with TikTok videos
- Remove duplicates by video ID
- Validate required fields
- Save to CSV
"""

import pandas as pd
import json
from pathlib import Path

print("="*70)
print("CLEANING TIKTOK DATA")
print("="*70)

# Setup directories
tiktok_dir = Path('raw/tiktok')
output_dir = Path('data/tiktok')
output_dir.mkdir(parents=True, exist_ok=True)

all_videos = []

# Get all JSON files
json_files = sorted(list(tiktok_dir.glob('*.json')))
print(f"\nFound {len(json_files)} JSON files in {tiktok_dir}\n")

total_loaded = 0

for fpath in json_files:
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        videos = []
        
        # Handle list format
        if isinstance(data, list):
            videos = data
        # Handle dict format with nested data
        elif isinstance(data, dict):
            if 'data' in data and isinstance(data['data'], list):
                videos = data['data']
            elif 'videos' in data and isinstance(data['videos'], list):
                videos = data['videos']
        
        # Add videos to collection
        for video in videos:
            if isinstance(video, dict):
                all_videos.append(video)
                total_loaded += 1
        
        print(f"  OK {fpath.name}: {len(videos)} videos")
        
    except Exception as e:
        print(f"  ERROR {fpath.name}: {str(e)}")

print(f"\nTotal videos before cleaning: {total_loaded}")

# Convert to DataFrame
if all_videos:
    df = pd.DataFrame(all_videos)
    print(f"\nDataFrame shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    
    # Check duplicates
    print(f"\nChecking for duplicates...")
    
    # Identify unique ID column
    id_col = None
    for col in ['id']:
        if col in df.columns:
            id_col = col
            break
    
    if id_col:
        dupes_id = df.duplicated(subset=[id_col], keep=False).sum()
        print(f"  Duplicates by '{id_col}': {dupes_id}")
    
    # Clean data
    print(f"\nCleaning data...")
    
    # Remove rows with missing video ID
    if id_col:
        before = len(df)
        df = df.dropna(subset=[id_col])
        removed = before - len(df)
        if removed > 0:
            print(f"  Removed {removed} rows with missing '{id_col}'")
    
    # Remove rows with missing text/content
    if 'text' in df.columns:
        before = len(df)
        df = df.dropna(subset=['text'])
        removed = before - len(df)
        if removed > 0:
            print(f"  Removed {removed} rows with missing 'text'")
    
    # Remove duplicate videos by ID
    if id_col:
        before = len(df)
        df = df.drop_duplicates(subset=[id_col], keep='first')
        removed = before - len(df)
        if removed > 0:
            print(f"  Removed {removed} duplicate videos by '{id_col}'")
    
    # Reset index
    df = df.reset_index(drop=True)
    
    print(f"\nFinal cleaned data shape: {df.shape}")
    
    # Save to CSV
    output_file = output_dir / 'tiktok_videos_clean.csv'
    df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"\nSaved to: {output_file}")
    
    # Show sample
    print(f"\nSample videos:")
    if 'text' in df.columns and 'authorMeta' in df.columns:
        for idx, row in df.head(3).iterrows():
            text = row['text'][:60] + "..." if len(str(row['text'])) > 60 else row['text']
            author = 'Unknown'
            if pd.notna(row['authorMeta']) and isinstance(row['authorMeta'], dict):
                author = row['authorMeta'].get('name', 'Unknown')
            print(f"  {idx+1}. [{author}] {text}")
    
    print("\n" + "="*70)
    print("TIKTOK DATA CLEANING COMPLETE!")
    print(f"Original: {total_loaded} videos")
    print(f"Cleaned: {len(df)} videos")
    print(f"Removed: {total_loaded - len(df)} duplicates/invalid ({((total_loaded - len(df))/total_loaded*100):.1f}%)")
    print("="*70)
    
else:
    print("ERROR: No videos loaded!")
