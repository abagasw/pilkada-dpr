import pandas as pd
from pathlib import Path

# Input and output files
input_file = r'raw\instagram\instagram_comments.csv'
output_file = r'data\instagram\instagram_comments_clean.csv'

print("Loading Instagram comments data...")
df = pd.read_csv(input_file)

print(f"Original shape: {df.shape}")

# Remove rows with errors (like "no_items" or "Empty or private data")
initial_rows = len(df)
df = df[df['error'].isna() | (df['error'] == '')]

# Remove rows with no actual comment text
df = df[(df['text'].notna() & (df['text'] != ''))]

# Remove rows where both text and replies are empty
df = df[~((df['text'].isna() | (df['text'] == '')) & 
          (df['replies/0/text'].isna() | (df['replies/0/text'] == '')))]

print(f"Rows with errors removed: {initial_rows - len(df)}")

# Select and rename key columns
selected_columns = {
    'postUrl': 'post_url',
    'ownerUsername': 'owner_username',
    'owner/username': 'author_username',
    'owner/full_name': 'author_full_name',
    'owner/is_verified': 'author_is_verified',
    'owner/profile_pic_url': 'author_profile_pic',
    'text': 'comment_text',
    'timestamp': 'comment_date',
    'likesCount': 'likes_count',
    'repliesCount': 'replies_count',
    'commentUrl': 'comment_url',
}

# Create clean dataframe with available columns
clean_df = pd.DataFrame()

for col_name, new_col_name in selected_columns.items():
    if col_name in df.columns:
        clean_df[new_col_name] = df[col_name]
    else:
        clean_df[new_col_name] = None

# Clean text data
clean_df['comment_text'] = clean_df['comment_text'].str.strip()
clean_df['author_full_name'] = clean_df['author_full_name'].str.strip()

# Convert data types
clean_df['likes_count'] = pd.to_numeric(clean_df['likes_count'], errors='coerce').fillna(0).astype(int)
clean_df['replies_count'] = pd.to_numeric(clean_df['replies_count'], errors='coerce').fillna(0).astype(int)

# Remove duplicates
clean_df = clean_df.drop_duplicates(subset=['comment_text', 'author_username'], keep='first')

# Remove rows where comment text is empty
clean_df = clean_df[(clean_df['comment_text'].notna()) & (clean_df['comment_text'] != '')]

# Sort by date
if 'comment_date' in clean_df.columns:
    clean_df = clean_df.sort_values('comment_date', ascending=False, na_position='last')

# Save to CSV
output_dir = Path(output_file).parent
output_dir.mkdir(parents=True, exist_ok=True)

clean_df.to_csv(output_file, index=False, encoding='utf-8')

print(f"\n{'='*60}")
print(f"INSTAGRAM COMMENTS CLEANING SUMMARY")
print(f"{'='*60}")
print(f"Original rows: {initial_rows}")
print(f"Cleaned rows: {len(clean_df)}")
print(f"Rows removed: {initial_rows - len(clean_df)}")
print(f"Final columns: {len(clean_df.columns)}")
print(f"\nColumns: {', '.join(clean_df.columns.tolist())}")
print(f"\n✅ Cleaned data saved to: {Path(output_file).absolute()}")
print(f"File size: {Path(output_file).stat().st_size / (1024*1024):.2f} MB")
print(f"\nData info:")
print(f"- Non-null comments: {clean_df['comment_text'].notna().sum()}")
print(f"- Unique authors: {clean_df['author_username'].nunique()}")
print(f"- Total likes: {clean_df['likes_count'].sum():,}")
print(f"- Total replies: {clean_df['replies_count'].sum():,}")
