#!/usr/bin/env python3
"""
Clean Google News data from raw/news and save to data/online-news
- Handle both list and dict formats
- Remove duplicates
- Validate required fields
- Save to CSV
"""

import pandas as pd
import json
from pathlib import Path

print("="*70)
print("🧹 CLEANING GOOGLE NEWS DATA")
print("="*70)

# Setup directories
news_dir = Path('raw/news')
output_dir = Path('data/online-news')
output_dir.mkdir(parents=True, exist_ok=True)

# Get all JSON files
json_files = sorted(list(news_dir.glob('*.json')))
print(f"\n📂 Found {len(json_files)} JSON files in {news_dir}\n")

# Load all data
all_articles = []
file_stats = []

for fpath in json_files:
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        articles = []
        
        # Handle list format
        if isinstance(data, list):
            articles = data
        
        # Handle dict format (with 'articles' key)
        elif isinstance(data, dict):
            if 'articles' in data:
                articles = data['articles']
            else:
                # If no 'articles' key, use the entire dict as single article
                articles = [data]
        
        # Add source file column
        for article in articles:
            if isinstance(article, dict):
                article['source_file'] = fpath.name
                all_articles.append(article)
        
        file_stats.append({
            'file': fpath.name,
            'count': len(articles)
        })
        print(f"  ✓ {fpath.name}: {len(articles)} articles")
        
    except Exception as e:
        print(f"  ✗ {fpath.name}: Error - {str(e)}")

print(f"\n📊 Total articles loaded: {len(all_articles)}")

# Convert to DataFrame
if all_articles:
    df = pd.DataFrame(all_articles)
    print(f"\n📋 Original data shape: {df.shape}")
    print(f"   Columns: {list(df.columns)}")
    
    # Check for duplicates before cleaning
    print(f"\n🔍 Checking for duplicates...")
    
    # Check by link (most reliable identifier)
    if 'link' in df.columns:
        dupes_link = df.duplicated(subset=['link'], keep=False).sum()
        print(f"   Duplicates by 'link': {dupes_link}")
    
    # Check by title
    if 'title' in df.columns:
        dupes_title = df.duplicated(subset=['title'], keep=False).sum()
        print(f"   Duplicates by 'title': {dupes_title}")
    
    # Clean data
    print(f"\n🧹 Cleaning data...")
    
    # Remove rows where link is missing (cannot identify duplicates without it)
    before = len(df)
    if 'link' in df.columns:
        df = df.dropna(subset=['link'])
        print(f"   ✓ Removed {before - len(df)} rows with missing 'link'")
    
    # Remove rows where title is missing
    before = len(df)
    if 'title' in df.columns:
        df = df.dropna(subset=['title'])
        print(f"   ✓ Removed {before - len(df)} rows with missing 'title'")
    
    # Remove duplicate links (keeping first occurrence)
    before = len(df)
    if 'link' in df.columns:
        df = df.drop_duplicates(subset=['link'], keep='first')
        print(f"   ✓ Removed {before - len(df)} duplicate articles by link")
    
    # Remove duplicate titles (keeping first occurrence)
    before = len(df)
    if 'title' in df.columns:
        df = df.drop_duplicates(subset=['title'], keep='first')
        print(f"   ✓ Removed {before - len(df)} duplicate articles by title")
    
    # Reset index
    df = df.reset_index(drop=True)
    
    print(f"\n✨ Final cleaned data shape: {df.shape}")
    
    # Save to CSV
    output_file = output_dir / 'online_news_clean.csv'
    df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"\n💾 Saved to: {output_file}")
    
    # Show sample
    print(f"\n📰 Sample of cleaned data:")
    if 'title' in df.columns:
        for idx, row in df.head(3).iterrows():
            print(f"   {idx+1}. {row['title'][:70]}...")
    
    print(f"\n" + "="*70)
    print(f"✅ NEWS DATA CLEANING COMPLETE!")
    print(f"   Original: {len(all_articles)} articles")
    print(f"   Cleaned: {len(df)} articles")
    print(f"   Removed: {len(all_articles) - len(df)} duplicates/invalid ({((len(all_articles) - len(df))/len(all_articles)*100):.1f}%)")
    print("="*70)
    
else:
    print("❌ No articles loaded!")
