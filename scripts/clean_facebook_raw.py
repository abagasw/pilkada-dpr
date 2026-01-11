import pandas as pd
import json
import re
from pathlib import Path

# Input and output files
input_file = r'raw\facebook\dataset_facebook-comments-scraper_2026-01-08_20-59-05-481.csv'
output_file = r'data\facebook\facebook_clean.csv'

print("Loading Facebook data...")
df = pd.read_csv(input_file)

print(f"Original shape: {df.shape}")
print(f"Columns: {df.shape[1]}")

# Extract key columns - looking for main comment data
# The file has nested structure, so we'll focus on extracting comments/0 level data
key_columns = []

# Identify columns that contain comment data
for col in df.columns:
    if 'comments/0/' in col:
        key_columns.append(col)

print(f"\nFound {len(key_columns)} comment-related columns")

# Create a clean dataset with main comment data
clean_data = []

for idx, row in df.iterrows():
    try:
        comment_row = {
            'post_url': row.get('facebookUrl', ''),
            'post_title': row.get('postTitle', ''),
            'date': row.get('date', ''),
            'profile_name': row.get('profileName', ''),
            'profile_url': row.get('profileUrl', ''),
            'text': row.get('text', ''),
            'likes_count': row.get('likesCount', 0),
            'comments_count': row.get('commentsCount', 0),
        }
        
        # Try to get first comment data
        if pd.notna(row.get('comments/0/text')):
            comment_row['comment_0_text'] = row.get('comments/0/text', '')
            comment_row['comment_0_author'] = row.get('comments/0/profileName', '')
            comment_row['comment_0_date'] = row.get('comments/0/date', '')
            comment_row['comment_0_likes'] = row.get('comments/0/likesCount', 0)
        
        clean_data.append(comment_row)
    except Exception as e:
        print(f"Error at row {idx}: {str(e)}")
        continue

clean_df = pd.DataFrame(clean_data)

# Remove duplicates
clean_df = clean_df.drop_duplicates(subset=['text', 'profile_name'], keep='first')

# Remove rows with empty text
clean_df = clean_df[clean_df['text'].notna() & (clean_df['text'] != '')]

# Clean text
clean_df['text'] = clean_df['text'].str.strip()
clean_df['post_title'] = clean_df['post_title'].str.strip()

# Remove rows where both post text and comment text are empty
clean_df = clean_df[
    ((clean_df['text'].notna() & (clean_df['text'] != '')) |
     (clean_df['comment_0_text'].notna() & (clean_df['comment_0_text'] != '')))
]

# Save to CSV
output_dir = Path(output_file).parent
output_dir.mkdir(parents=True, exist_ok=True)

clean_df.to_csv(output_file, index=False, encoding='utf-8')

print(f"\n{'='*60}")
print(f"FACEBOOK DATA CLEANING SUMMARY")
print(f"{'='*60}")
print(f"Original rows: {df.shape[0]}")
print(f"Cleaned rows: {clean_df.shape[0]}")
print(f"Rows removed: {df.shape[0] - clean_df.shape[0]}")
print(f"Columns in output: {clean_df.shape[1]}")
print(f"\nColumns: {', '.join(clean_df.columns.tolist())}")
print(f"\n✅ Cleaned data saved to: {Path(output_file).absolute()}")
print(f"File size: {Path(output_file).stat().st_size / (1024*1024):.2f} MB")
print(f"\nData info:")
print(f"- Non-null posts: {clean_df['text'].notna().sum()}")
print(f"- Non-null comments: {clean_df['comment_0_text'].notna().sum()}")
