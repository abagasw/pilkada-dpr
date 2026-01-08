#!/usr/bin/env python3
"""
Clean Threads replies data
- Load JSON files dari data/threads_comments/
- Normalize dan clean data
- Handle duplikasi dan missing values
- Save ke CSV untuk analysis
"""

import pandas as pd
import json
import re
from pathlib import Path
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

print("="*70)
print("CLEANING THREADS REPLIES DATA")
print("="*70)

# Setup directories
comments_dir = Path('data/threads_comments')
output_dir = Path('data/threads_comments')
output_dir.mkdir(parents=True, exist_ok=True)

# Load semua JSON files
json_files = sorted(list(comments_dir.glob('*.json')))
print(f"\nFound {len(json_files)} JSON files in {comments_dir}\n")

all_replies = []
total_loaded = 0
total_cleaned = 0

for json_file in json_files:
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        post_id = data.get('post_id')
        url = data.get('url')
        replies = data.get('replies', [])
        
        # Process each reply
        for reply_data in replies:
            reply = {
                'post_id': post_id,
                'post_url': url,
                'author': reply_data.get('author', '').strip() if isinstance(reply_data.get('author'), str) else '',
                'text': reply_data.get('text', '').strip() if isinstance(reply_data.get('text'), str) else '',
                'timestamp': reply_data.get('timestamp'),
                'likes': reply_data.get('likes', 0),
                'source_file': json_file.name
            }
            
            # Basic validation
            if reply['text']:  # Only add jika ada text
                all_replies.append(reply)
                total_cleaned += 1
        
        total_loaded += len(replies)
        
    except Exception as e:
        logger.error(f"Error loading {json_file}: {e}")

# Create DataFrame
df = pd.DataFrame(all_replies)

print(f"\nData loaded:")
print(f"  Total replies: {total_loaded}")
print(f"  Replies after cleaning: {total_cleaned}")
print(f"  Duplicate entries removed: {total_loaded - total_cleaned}")

# Remove exact duplicates
df = df.drop_duplicates(subset=['post_id', 'author', 'text'], keep='first')
print(f"  After removing duplicates: {len(df)}")

# Handle missing values
df['author'] = df['author'].fillna('Unknown')
df['text'] = df['text'].fillna('')
df['likes'] = df['likes'].fillna(0).astype(int)

# Clean text
def clean_text(text):
    """Clean reply text"""
    if not isinstance(text, str):
        return ''
    # Remove extra whitespace
    text = ' '.join(text.split())
    # Remove URLs
    text = re.sub(r'http\S+', '', text)
    # Remove special characters but keep Indonesian characters
    text = re.sub(r'[^\w\s\.\,\!\?\-\'\"\@\#\&\(\)\:\;\/áéíóúàèìòùäëïöüâêîôûãõñç]', '', text)
    return text.strip()

df['text_clean'] = df['text'].apply(clean_text)

# Remove replies yang text-nya terlalu pendek setelah cleaning
df = df[df['text_clean'].str.len() > 5]
print(f"  After removing short replies: {len(df)}")

# Add metadata
df['cleaned_at'] = datetime.now().isoformat()
df['text_length'] = df['text_clean'].str.len()
df['word_count'] = df['text_clean'].str.split().str.len()

# Reorder columns
columns_order = [
    'post_id', 'post_url', 'author', 'text', 'text_clean', 'text_length', 'word_count',
    'likes', 'timestamp', 'source_file', 'cleaned_at'
]
df = df[columns_order]

# Sort by post_id and likes (descending)
df = df.sort_values(['post_id', 'likes'], ascending=[True, False]).reset_index(drop=True)

# Save to CSV
output_file = output_dir / 'threads_replies_clean.csv'
df.to_csv(output_file, index=False, encoding='utf-8')
print(f"\n✓ Cleaned data saved to: {output_file}")

# Save summary statistics
summary_stats = {
    'total_replies': len(df),
    'unique_posts': df['post_id'].nunique(),
    'unique_authors': df['author'].nunique(),
    'avg_likes': df['likes'].mean(),
    'avg_text_length': df['text_length'].mean(),
    'avg_word_count': df['word_count'].mean(),
    'max_likes': df['likes'].max(),
    'min_likes': df['likes'].min(),
    'top_authors': df['author'].value_counts().head(10).to_dict(),
    'cleaned_at': datetime.now().isoformat()
}

summary_file = output_dir / 'threads_replies_summary.json'
with open(summary_file, 'w', encoding='utf-8') as f:
    json.dump(summary_stats, f, ensure_ascii=False, indent=2)

print(f"✓ Summary statistics saved to: {summary_file}")

print("\n" + "="*70)
print("CLEANING SUMMARY")
print("="*70)
print(f"\nFinal dataset statistics:")
print(f"  Total replies: {len(df)}")
print(f"  Unique posts: {df['post_id'].nunique()}")
print(f"  Unique authors: {df['author'].nunique()}")
print(f"  Average likes per reply: {df['likes'].mean():.2f}")
print(f"  Average text length: {df['text_length'].mean():.0f} characters")
print(f"  Average word count: {df['word_count'].mean():.0f} words")

print(f"\nTop 5 authors:")
for idx, (author, count) in enumerate(df['author'].value_counts().head(5).items(), 1):
    print(f"  {idx}. {author} ({count} replies)")

print(f"\nTop 5 most-liked replies:")
top_replies = df.nlargest(5, 'likes')[['author', 'text_clean', 'likes']]
for idx, row in top_replies.iterrows():
    print(f"  {row['likes']} likes: {row['author']} - {row['text_clean'][:50]}...")
