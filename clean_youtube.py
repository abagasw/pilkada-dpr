#!/usr/bin/env python3
"""
Clean YouTube data from raw/youtube
- Handle full data with nested structure
- Handle videos list
- Remove duplicates
- Validate required fields
- Save to CSV
"""

import pandas as pd
import json
from pathlib import Path

print("="*70)
print("CLEANING YOUTUBE DATA")
print("="*70)

# Setup directories
youtube_dir = Path('raw/youtube')
output_dir = Path('data/youtube')
output_dir.mkdir(parents=True, exist_ok=True)

all_videos = []
total_loaded = 0

# Process youtube_pilkada_full_20260108_234758.json
print("\nProcessing youtube_pilkada_full_20260108_234758.json...")
try:
    with open(youtube_dir / 'youtube_pilkada_full_20260108_234758.json', 'r', encoding='utf-8') as f:
        full_data = json.load(f)
    
    # Extract videos from results_by_keyword
    if 'results_by_keyword' in full_data and isinstance(full_data['results_by_keyword'], list):
        for keyword_item in full_data['results_by_keyword']:
            if 'videos' in keyword_item and isinstance(keyword_item['videos'], list):
                for video in keyword_item['videos']:
                    if isinstance(video, dict):
                        video['keyword'] = keyword_item.get('keyword', 'unknown')
                        all_videos.append(video)
                        total_loaded += 1
    
    print(f"  Loaded {total_loaded} videos from full file")
except Exception as e:
    print(f"  Error: {str(e)}")

# Process youtube_pilkada_videos_20260108_234758.json
print("Processing youtube_pilkada_videos_20260108_234758.json...")
try:
    with open(youtube_dir / 'youtube_pilkada_videos_20260108_234758.json', 'r', encoding='utf-8') as f:
        videos_data = json.load(f)
    
    if isinstance(videos_data, list):
        for video in videos_data:
            if isinstance(video, dict):
                all_videos.append(video)
                total_loaded += 1
    
    print(f"  Loaded {len(videos_data)} videos from videos file")
except Exception as e:
    print(f"  Error: {str(e)}")

print(f"\nTotal videos before cleaning: {total_loaded}")

# Convert to DataFrame
if all_videos:
    df = pd.DataFrame(all_videos)
    print(f"DataFrame shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    
    # Check duplicates
    print(f"\nChecking for duplicates...")
    
    # By video_id
    if 'video_id' in df.columns:
        dupes_vid = df.duplicated(subset=['video_id'], keep=False).sum()
        print(f"  Duplicates by video_id: {dupes_vid}")
    
    # By title
    if 'title' in df.columns:
        dupes_title = df.duplicated(subset=['title'], keep=False).sum()
        print(f"  Duplicates by title: {dupes_title}")
    
    # Clean data
    print(f"\nCleaning data...")
    
    # Remove missing video_id
    before = len(df)
    if 'video_id' in df.columns:
        df = df.dropna(subset=['video_id'])
        print(f"  Removed {before - len(df)} rows with missing video_id")
    
    # Remove missing title
    before = len(df)
    if 'title' in df.columns:
        df = df.dropna(subset=['title'])
        print(f"  Removed {before - len(df)} rows with missing title")
    
    # Remove duplicate video_id
    before = len(df)
    if 'video_id' in df.columns:
        df = df.drop_duplicates(subset=['video_id'], keep='first')
        print(f"  Removed {before - len(df)} duplicate videos by video_id")
    
    # Remove duplicate title
    before = len(df)
    if 'title' in df.columns:
        df = df.drop_duplicates(subset=['title'], keep='first')
        print(f"  Removed {before - len(df)} duplicate videos by title")
    
    df = df.reset_index(drop=True)
    
    # Fill missing keyword if exists
    if 'keyword' in df.columns:
        df['keyword'] = df['keyword'].fillna('general')
    
    print(f"\nFinal cleaned data shape: {df.shape}")
    
    # Save to CSV
    output_file = output_dir / 'youtube_videos_clean.csv'
    df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"\nSaved to: {output_file}")
    
    # Show sample
    print(f"\nSample videos:")
    if 'title' in df.columns:
        for idx, row in df.head(3).iterrows():
            title = row['title'][:60] + "..." if len(str(row['title'])) > 60 else row['title']
            print(f"  {idx+1}. {title}")
            if 'channel_title' in df.columns and pd.notna(row['channel_title']):
                print(f"     Channel: {row['channel_title']}")
    
    print("\n" + "="*70)
    print("YOUTUBE DATA CLEANING COMPLETE!")
    print(f"Original: {total_loaded} videos")
    print(f"Cleaned: {len(df)} videos")
    print(f"Removed: {total_loaded - len(df)} duplicates/invalid ({((total_loaded - len(df))/total_loaded*100):.1f}%)")
    print("="*70)
    
else:
    print("ERROR: No videos loaded!")
