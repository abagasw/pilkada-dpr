import json
import pandas as pd
import os
from pathlib import Path

# Base directory containing all video folders
base_dir = r'data\tiktok_comments'
output_dir = r'data\tiktok_comments_csv'

# Create output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

# Track conversion progress
converted_count = 0
failed_count = 0
failed_videos = []

# Get all video ID folders
video_folders = [f for f in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, f))]
print(f"Found {len(video_folders)} video folders to process\n")

for video_id in video_folders:
    video_path = os.path.join(base_dir, video_id)
    json_file = os.path.join(video_path, 'comments_full.json')
    
    if not os.path.exists(json_file):
        print(f"❌ Skipped {video_id} - comments_full.json not found")
        failed_count += 1
        failed_videos.append(video_id)
        continue
    
    try:
        # Read JSON file
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract comments data
        comments_data = []
        for comment in data.get('comments', []):
            comments_data.append({
                "video_id": video_id,
                "comment_id": comment.get('cid'),
                "username": comment.get('username'),
                "nickname": comment.get('nickname'),
                "comment": comment.get('comment'),
                "create_time": comment.get('create_time'),
                "likes": comment.get('likes'),
                "total_reply": comment.get('total_reply'),
                "avatar": comment.get('avatar')
            })
        
        # Save to CSV
        if comments_data:
            csv_file = os.path.join(output_dir, f'{video_id}_comments.csv')
            df = pd.DataFrame(comments_data)
            df.to_csv(csv_file, index=False, encoding='utf-8')
            print(f"✅ Converted {video_id} - {len(comments_data)} comments saved")
            converted_count += 1
        else:
            print(f"⚠️  {video_id} - No comments found in JSON")
            
    except Exception as e:
        print(f"❌ Error processing {video_id}: {str(e)}")
        failed_count += 1
        failed_videos.append(video_id)

# Print summary
print(f"\n{'='*60}")
print(f"CONVERSION SUMMARY")
print(f"{'='*60}")
print(f"✅ Successfully converted: {converted_count}")
print(f"❌ Failed or skipped: {failed_count}")
print(f"📁 Output directory: {os.path.abspath(output_dir)}")

if failed_videos:
    print(f"\nFailed videos:")
    for vid in failed_videos[:10]:  # Show first 10
        print(f"  - {vid}")
    if len(failed_videos) > 10:
        print(f"  ... and {len(failed_videos) - 10} more")
