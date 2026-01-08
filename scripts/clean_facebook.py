#!/usr/bin/env python3
"""
Clean Facebook data from raw/facebook
- Handle list format with posts
- Remove duplicates by postId
- Validate required fields
- Save to CSV
"""

import pandas as pd
import json
from pathlib import Path

print("="*70)
print("CLEANING FACEBOOK DATA")
print("="*70)

# Setup directories
facebook_dir = Path('raw/facebook')
output_dir = Path('data/facebook')
output_dir.mkdir(parents=True, exist_ok=True)

all_posts = []
file_stats = []

# Get all JSON files
json_files = sorted(list(facebook_dir.glob('*.json')))
print(f"\nFound {len(json_files)} JSON files in {facebook_dir}\n")

total_loaded = 0

for fpath in json_files:
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        posts = []
        
        # Handle list format
        if isinstance(data, list):
            posts = data
        # Handle dict format with nested data
        elif isinstance(data, dict):
            if 'data' in data and isinstance(data['data'], list):
                posts = data['data']
            elif 'posts' in data and isinstance(data['posts'], list):
                posts = data['posts']
        
        # Add posts to collection
        for post in posts:
            if isinstance(post, dict):
                all_posts.append(post)
                total_loaded += 1
        
        file_stats.append({
            'file': fpath.name,
            'count': len(posts)
        })
        print(f"  OK {fpath.name}: {len(posts)} posts")
        
    except Exception as e:
        print(f"  ERROR {fpath.name}: {str(e)}")

print(f"\nTotal posts before cleaning: {total_loaded}")

# Convert to DataFrame
if all_posts:
    df = pd.DataFrame(all_posts)
    print(f"\nDataFrame shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    
    # Check duplicates
    print(f"\nChecking for duplicates...")
    
    # Identify unique ID column
    id_col = None
    for col in ['postFacebookId', 'postId', 'id', 'post_id']:
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
    
    # Remove rows with missing post identifier
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
    
    # Remove duplicate posts by ID
    if id_col:
        before = len(df)
        df = df.drop_duplicates(subset=[id_col], keep='first')
        removed = before - len(df)
        if removed > 0:
            print(f"  Removed {removed} duplicate posts by '{id_col}'")
    
    # Remove duplicate posts by URL
    if 'url' in df.columns:
        before = len(df)
        df = df.drop_duplicates(subset=['url'], keep='first')
        removed = before - len(df)
        if removed > 0:
            print(f"  Removed {removed} duplicate posts by 'url'")
    
    # Reset index
    df = df.reset_index(drop=True)
    
    print(f"\nFinal cleaned data shape: {df.shape}")
    
    # Save to CSV
    output_file = output_dir / 'facebook_posts_clean.csv'
    df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"\nSaved to: {output_file}")
    
    # Show sample
    print(f"\nSample posts:")
    if 'pageName' in df.columns and 'text' in df.columns:
        for idx, row in df.head(3).iterrows():
            page = row['pageName'] if pd.notna(row['pageName']) else 'Unknown'
            text = row['text'][:60] + "..." if len(str(row['text'])) > 60 else row['text']
            print(f"  {idx+1}. [{page}] {text}")
    
    print("\n" + "="*70)
    print("FACEBOOK DATA CLEANING COMPLETE!")
    print(f"Original: {total_loaded} posts")
    print(f"Cleaned: {len(df)} posts")
    print(f"Removed: {total_loaded - len(df)} duplicates/invalid ({((total_loaded - len(df))/total_loaded*100):.1f}%)")
    print("="*70)
    
else:
    print("ERROR: No posts loaded!")
