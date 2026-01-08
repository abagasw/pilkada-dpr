#!/usr/bin/env python3
"""
Clean X/Twitter data from raw/x
- Handle list format with tweets
- Remove duplicates by tweet ID
- Validate required fields
- Save to CSV
"""

import pandas as pd
import json
from pathlib import Path

print("="*70)
print("CLEANING X/TWITTER DATA")
print("="*70)

# Setup directories
x_dir = Path('raw/x')
output_dir = Path('data/x')
output_dir.mkdir(parents=True, exist_ok=True)

all_tweets = []

# Get all JSON files
json_files = sorted(list(x_dir.glob('*.json')))
print(f"\nFound {len(json_files)} JSON files in {x_dir}\n")

total_loaded = 0

for fpath in json_files:
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        tweets = []
        
        # Handle list format
        if isinstance(data, list):
            tweets = data
        # Handle dict format with nested data
        elif isinstance(data, dict):
            if 'data' in data and isinstance(data['data'], list):
                tweets = data['data']
            elif 'tweets' in data and isinstance(data['tweets'], list):
                tweets = data['tweets']
        
        # Add tweets to collection
        for tweet in tweets:
            if isinstance(tweet, dict):
                all_tweets.append(tweet)
                total_loaded += 1
        
        print(f"  OK {fpath.name}: {len(tweets)} tweets")
        
    except Exception as e:
        print(f"  ERROR {fpath.name}: {str(e)}")

print(f"\nTotal tweets before cleaning: {total_loaded}")

# Convert to DataFrame
if all_tweets:
    df = pd.DataFrame(all_tweets)
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
    
    if 'url' in df.columns:
        dupes_url = df.duplicated(subset=['url'], keep=False).sum()
        print(f"  Duplicates by 'url': {dupes_url}")
    
    # Clean data
    print(f"\nCleaning data...")
    
    # Remove rows with missing tweet ID
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
    
    # Remove duplicate tweets by ID
    if id_col:
        before = len(df)
        df = df.drop_duplicates(subset=[id_col], keep='first')
        removed = before - len(df)
        if removed > 0:
            print(f"  Removed {removed} duplicate tweets by '{id_col}'")
    
    # Remove duplicate tweets by URL
    if 'url' in df.columns:
        before = len(df)
        df = df.drop_duplicates(subset=['url'], keep='first')
        removed = before - len(df)
        if removed > 0:
            print(f"  Removed {removed} duplicate tweets by 'url'")
    
    # Reset index
    df = df.reset_index(drop=True)
    
    print(f"\nFinal cleaned data shape: {df.shape}")
    
    # Save to CSV
    output_file = output_dir / 'x_tweets_clean.csv'
    df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"\nSaved to: {output_file}")
    
    # Show sample
    print(f"\nSample tweets:")
    if 'text' in df.columns and 'author' in df.columns:
        for idx, row in df.head(3).iterrows():
            text = row['text'][:60] + "..." if len(str(row['text'])) > 60 else row['text']
            author = 'Unknown'
            if pd.notna(row['author']) and isinstance(row['author'], dict):
                author = row['author'].get('name', 'Unknown')
            print(f"  {idx+1}. [@{author}] {text}")
    
    print("\n" + "="*70)
    print("X/TWITTER DATA CLEANING COMPLETE!")
    print(f"Original: {total_loaded} tweets")
    print(f"Cleaned: {len(df)} tweets")
    print(f"Removed: {total_loaded - len(df)} duplicates/invalid ({((total_loaded - len(df))/total_loaded*100):.1f}%)")
    print("="*70)
    
else:
    print("ERROR: No tweets loaded!")
