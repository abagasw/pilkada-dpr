import pandas as pd
import json
import os
import time
from datetime import datetime
from apify_client import ApifyClient
from pathlib import Path

# Initialize the ApifyClient with your API token
API_TOKEN = "apify_api_yJ2npBdWFUAdbW1YtKgHEGzgpwgjEj347U30"  # Replace with your actual API token
client = ApifyClient(API_TOKEN)

# Configuration
CSV_INPUT_PATH = "data/threads/threads_data_clean.csv"
OUTPUT_DIR = "data/threads_replies"
ACTOR_ID = "BLCIl3gRrBQEx6DFs"
MAX_REPLIES = 100
DELAY_BETWEEN_REQUESTS = 2  # seconds, to avoid rate limiting
START_FROM_ROW = 14  # Skip first 14 rows (already scraped), start from row 15

# Create output directory if it doesn't exist
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

def scrape_threads_replies():
    """
    Main function to scrape threads replies from multiple posts
    """
    # Read the CSV file
    try:
        df = pd.read_csv(CSV_INPUT_PATH)
        print(f"✓ Loaded {len(df)} posts from {CSV_INPUT_PATH}")
    except FileNotFoundError:
        print(f"✗ File not found: {CSV_INPUT_PATH}")
        return
    except Exception as e:
        print(f"✗ Error reading CSV: {e}")
        return

    # Extract URLs
    urls = df['url'].dropna().unique()
    print(f"✓ Found {len(urls)} unique post URLs")
    print(f"✓ Starting from row {START_FROM_ROW + 1} (skipping first {START_FROM_ROW} rows)")

    # Skip already scraped rows
    urls = urls[START_FROM_ROW:]
    print(f"✓ Processing {len(urls)} remaining URLs")

    # Prepare storage for results
    all_replies = []
    successful_posts = 0
    failed_posts = 0
    skipped_posts = 0

    # Iterate through each URL
    for idx, post_url in enumerate(urls, START_FROM_ROW + 1):
        print(f"\n[{idx}/{len(urls)}] Processing: {post_url}")
        
        try:
            # Prepare the Actor input
            run_input = {
                "post_url": post_url,
                "max_replies": MAX_REPLIES,
            }

            # Run the Actor and wait for it to finish
            print(f"  → Calling Actor...")
            run = client.actor(ACTOR_ID).call(run_input=run_input)
            
            # Fetch and process Actor results
            dataset_id = run.get("defaultDatasetId")
            if not dataset_id:
                print(f"  ✗ No dataset returned from Actor")
                failed_posts += 1
                continue

            replies_count = 0
            for item in client.dataset(dataset_id).iterate_items():
                # Add the post_url to each reply for reference
                item['post_url'] = post_url
                item['scraped_at'] = datetime.now().isoformat()
                all_replies.append(item)
                replies_count += 1

            print(f"  ✓ Scraped {replies_count} replies")
            successful_posts += 1

        except Exception as e:
            print(f"  ✗ Error scraping {post_url}: {str(e)}")
            failed_posts += 1

        # Delay between requests to avoid rate limiting
        if idx < len(urls):
            print(f"  → Waiting {DELAY_BETWEEN_REQUESTS}s before next request...")
            time.sleep(DELAY_BETWEEN_REQUESTS)

    # Save results
    print("\n" + "="*60)
    print("SCRAPING COMPLETE")
    print("="*60)
    print(f"Successfully scraped: {successful_posts} posts")
    print(f"Failed: {failed_posts} posts")
    print(f"Total replies collected: {len(all_replies)}")

    if all_replies:
        # Save to CSV (append to existing file if it exists)
        existing_files = [f for f in os.listdir(OUTPUT_DIR) if f.startswith('threads_replies_') and f.endswith('.csv')]
        if existing_files:
            # Append to the most recent file
            existing_files.sort()
            latest_file = os.path.join(OUTPUT_DIR, existing_files[-1])
            existing_df = pd.read_csv(latest_file)
            replies_df = pd.DataFrame(all_replies)
            combined_df = pd.concat([existing_df, replies_df], ignore_index=True)
            combined_df.to_csv(latest_file, index=False, encoding='utf-8')
            print(f"✓ Appended {len(replies_df)} replies to: {latest_file}")
        else:
            # Create new file
            output_csv = os.path.join(OUTPUT_DIR, f"threads_replies_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
            replies_df = pd.DataFrame(all_replies)
            replies_df.to_csv(output_csv, index=False, encoding='utf-8')
            print(f"✓ Saved replies to CSV: {output_csv}")

        # Save to JSON for backup
        output_json = os.path.join(OUTPUT_DIR, f"threads_replies_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(all_replies, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved replies to JSON: {output_json}")

        # Print summary statistics
        print(f"\nReply counts by post:")
        reply_counts = replies_df['post_url'].value_counts()
        for post_url, count in reply_counts.head(10).items():
            print(f"  - {post_url}: {count} replies")

    else:
        print("✗ No replies were collected")

def main():
    """
    Entry point
    """
    print("="*60)
    print("THREADS REPLIES SCRAPER - APIFY CLIENT")
    print("="*60)
    print(f"Starting at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Check if API token is set
    if API_TOKEN == "<YOUR_API_TOKEN>":
        print("✗ ERROR: API_TOKEN not configured!")
        print("  Please replace '<YOUR_API_TOKEN>' with your actual Apify API token")
        return

    # Run the scraper
    scrape_threads_replies()

    print(f"\nEnded at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
