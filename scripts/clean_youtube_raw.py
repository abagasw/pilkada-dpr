import json
import pandas as pd
from pathlib import Path

# Input and output files
input_file = r'raw\youtube\youtube_pilkada_comments_20260108_234758.json'
output_file = r'data\youtube\youtube_comments_clean.csv'

print("Loading YouTube comments JSON...")
try:
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Loaded {len(data)} comments")
    
    # Convert to DataFrame
    comments_list = []
    
    for comment in data:
        try:
            comment_row = {
                'author': comment.get('author', ''),
                'text': comment.get('text', ''),
                'likes': comment.get('likes', 0),
                'published_at': comment.get('published_at', ''),
                'video_id': comment.get('video_id', ''),
                'video_title': comment.get('video_title', ''),
                'channel_title': comment.get('channel_title', ''),
                'comment_type': comment.get('comment_type', ''),
                'scraped_at': comment.get('metadata', {}).get('scraped_at', ''),
                'language': comment.get('metadata', {}).get('language', ''),
                'keyword': comment.get('keyword', ''),
            }
            comments_list.append(comment_row)
        except Exception as e:
            print(f"Error processing comment: {str(e)}")
            continue
    
    df = pd.DataFrame(comments_list)
    
    print(f"\nOriginal shape: {df.shape}")
    
    # Clean data
    # Remove rows with empty text
    df = df[(df['text'].notna()) & (df['text'] != '')]
    
    # Clean text
    df['text'] = df['text'].str.strip()
    df['author'] = df['author'].fillna('').str.strip()
    df['video_title'] = df['video_title'].fillna('').str.strip()
    df['channel_title'] = df['channel_title'].fillna('').str.strip()
    
    # Remove duplicates
    df = df.drop_duplicates(subset=['text', 'author'], keep='first')
    
    # Convert numeric columns
    df['likes'] = pd.to_numeric(df['likes'], errors='coerce').fillna(0).astype(int)
    
    # Create output directory if it doesn't exist
    output_dir = Path(output_file).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_file, index=False, encoding='utf-8')
    
    print(f"\n{'='*60}")
    print(f"YOUTUBE COMMENTS CLEANING SUMMARY")
    print(f"{'='*60}")
    print(f"Original rows: {len(comments_list)}")
    print(f"Cleaned rows: {len(df)}")
    print(f"Rows removed: {len(comments_list) - len(df)}")
    print(f"Final columns: {len(df.columns)}")
    print(f"\nColumns: {', '.join(df.columns.tolist())}")
    print(f"\n✅ Cleaned data saved to: {Path(output_file).absolute()}")
    print(f"File size: {Path(output_file).stat().st_size / (1024*1024):.2f} MB")
    print(f"\nData info:")
    print(f"- Total comments: {len(df)}")
    print(f"- Unique authors: {df['author'].nunique()}")
    print(f"- Total likes: {df['likes'].sum():,}")
    print(f"- Unique videos: {df['video_id'].nunique()}")
    print(f"- Unique channels: {df['channel_title'].nunique()}")
    print(f"- Languages: {df['language'].nunique()}")
    print(f"- Avg likes per comment: {df['likes'].mean():.2f}")
    
except json.JSONDecodeError as e:
    print(f"Error decoding JSON: {str(e)}")
except Exception as e:
    print(f"Error: {str(e)}")
