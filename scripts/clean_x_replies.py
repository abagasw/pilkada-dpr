import pandas as pd
import os
from pathlib import Path

# Directory containing all reply CSV files
input_dir = r'raw\x\replies'
output_file = r'data\x\x_replies_clean.csv'

# Get all CSV files from the replies directory
csv_files = [f for f in os.listdir(input_dir) if f.endswith('.csv')]
print(f"Found {len(csv_files)} CSV files in {input_dir}\n")

# Read and combine all CSV files
dataframes = []
total_rows = 0

for file in csv_files:
    file_path = os.path.join(input_dir, file)
    try:
        df = pd.read_csv(file_path)
        total_rows += len(df)
        dataframes.append(df)
        print(f"✅ Loaded {file} - {len(df)} rows")
    except Exception as e:
        print(f"❌ Error loading {file}: {str(e)}")

# Combine all dataframes
print(f"\nCombining {len(dataframes)} files with {total_rows} total rows...")
combined_df = pd.concat(dataframes, ignore_index=True)

print(f"Combined shape: {combined_df.shape}")

# Create clean dataframe with key columns
clean_data = []

for idx, row in combined_df.iterrows():
    # Prefer raw_data/text over reply_text
    text = row.get('raw_data/text') or row.get('reply_text')
    author = row.get('raw_data/user_legacy/screen_name') or row.get('reply_author')
    author_name = row.get('raw_data/user_legacy/name') or row.get('reply_author_name')
    
    if pd.notna(text) and text != '':
        clean_row = {
            'tweet_id': row.get('raw_data/tweet_id', ''),
            'text': str(text).strip(),
            'author': str(author).strip() if author else '',
            'author_name': str(author_name).strip() if author_name else '',
            'created_at': row.get('raw_data/created_at') or row.get('created_at', ''),
            'likes': pd.to_numeric(row.get('raw_data/favorite_count', 0), errors='coerce') or pd.to_numeric(row.get('like_count', 0), errors='coerce'),
            'replies': pd.to_numeric(row.get('raw_data/reply_count', 0), errors='coerce') or pd.to_numeric(row.get('reply_count', 0), errors='coerce'),
            'retweets': pd.to_numeric(row.get('raw_data/retweet_count', 0), errors='coerce') or pd.to_numeric(row.get('retweet_count', 0), errors='coerce'),
            'verified': row.get('raw_data/user_legacy/verified') or row.get('verified', ''),
            'followers': pd.to_numeric(row.get('raw_data/user_legacy/followers_count', 0), errors='coerce'),
            'lang': row.get('lang', ''),
            'in_reply_to_tweet_id': row.get('in_reply_to_tweet_id') or row.get('raw_data/in_reply_to_status_id_str', ''),
        }
        clean_data.append(clean_row)

clean_df = pd.DataFrame(clean_data)

# Remove duplicates
clean_df = clean_df.drop_duplicates(subset=['text', 'author'], keep='first')

# Convert numeric columns
clean_df['likes'] = pd.to_numeric(clean_df['likes'], errors='coerce').fillna(0).astype(int)
clean_df['replies'] = pd.to_numeric(clean_df['replies'], errors='coerce').fillna(0).astype(int)
clean_df['retweets'] = pd.to_numeric(clean_df['retweets'], errors='coerce').fillna(0).astype(int)
clean_df['followers'] = pd.to_numeric(clean_df['followers'], errors='coerce').fillna(0).astype(int)

# Create output directory if it doesn't exist
output_dir = Path(output_file).parent
output_dir.mkdir(parents=True, exist_ok=True)

# Save to CSV
clean_df.to_csv(output_file, index=False, encoding='utf-8')

print(f"\n{'='*60}")
print(f"X REPLIES CLEANING SUMMARY")
print(f"{'='*60}")
print(f"Total rows (combined): {len(combined_df)}")
print(f"Cleaned rows: {len(clean_df)}")
print(f"Rows removed: {len(combined_df) - len(clean_df)}")
print(f"Final columns: {len(clean_df.columns)}")
print(f"\nColumns: {', '.join(clean_df.columns.tolist())}")
print(f"\n✅ Cleaned data saved to: {Path(output_file).absolute()}")
print(f"File size: {Path(output_file).stat().st_size / (1024*1024):.2f} MB")
print(f"\nData info:")
print(f"- Total replies: {len(clean_df)}")
print(f"- Unique authors: {clean_df['author'].nunique()}")
print(f"- Total likes: {clean_df['likes'].sum():,}")
print(f"- Total retweets: {clean_df['retweets'].sum():,}")
print(f"- Verified users: {(clean_df['verified'] == True).sum()}")
print(f"- Average followers: {clean_df['followers'].mean():.0f}")
