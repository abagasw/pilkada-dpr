"""
Clean dan standardisasi data Threads replies
"""

import pandas as pd
import re
import os
import logging
from datetime import datetime
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ThreadsRepliesCleaner:
    def __init__(self):
        self.original_count = 0
        self.cleaned_count = 0
    
    def clean_text(self, text: str) -> str:
        """Bersihkan text content"""
        if not isinstance(text, str):
            return ''
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove common artifacts
        text = text.replace('\xa0', ' ')
        text = text.replace('\u200b', '')  # Zero-width space
        
        # Remove URLs (optional - comment jika ingin keep URLs)
        # text = re.sub(r'http[s]?://\S+', '', text)
        
        return text.strip()
    
    def parse_timestamp(self, timestamp_str: str) -> Optional[str]:
        """Parse dan standardisasi timestamp"""
        if not timestamp_str:
            return None
        
        try:
            # Format dari API: "2026-01-07T14:47:55.000Z"
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return dt.isoformat()
        except Exception as e:
            logger.warning(f"Error parsing timestamp '{timestamp_str}': {e}")
            return timestamp_str
    
    def extract_username_clean(self, username: str) -> str:
        """Bersihkan username"""
        if not username:
            return ''
        
        # Remove @ if exists
        username = username.replace('@', '').strip()
        
        # Lowercase
        username = username.lower()
        
        return username
    
    def validate_reply(self, row: pd.Series) -> bool:
        """Validasi bahwa row adalah reply yang valid"""
        # Check required fields
        required_fields = ['username', 'text']
        for field in required_fields:
            if field not in row or pd.isna(row[field]) or not str(row[field]).strip():
                return False
        
        # Minimum text length
        if len(str(row['text']).strip()) < 3:
            return False
        
        return True
    
    def clean_data(self, input_file: str, output_file: Optional[str] = None) -> pd.DataFrame:
        """Main cleaning function"""
        
        if not os.path.exists(input_file):
            logger.error(f"File not found: {input_file}")
            return pd.DataFrame()
        
        # Load data
        logger.info(f"Loading data from {input_file}")
        df = pd.read_csv(input_file)
        self.original_count = len(df)
        logger.info(f"Loaded {self.original_count} rows")
        
        # Clean text
        logger.info("Cleaning text...")
        df['text'] = df['text'].apply(self.clean_text)
        
        # Clean username
        logger.info("Cleaning usernames...")
        df['username'] = df['username'].apply(self.extract_username_clean)
        
        # Parse timestamp
        logger.info("Parsing timestamps...")
        df['timestamp'] = df['timestamp'].apply(self.parse_timestamp)
        
        # Standardize engagement metrics
        for col in ['likes', 'comments', 'reposts', 'shares']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        
        # Remove duplicates
        logger.info("Removing duplicates...")
        initial_len = len(df)
        df = df.drop_duplicates(subset=['username', 'text', 'post_url'], keep='first')
        duplicates = initial_len - len(df)
        if duplicates > 0:
            logger.info(f"Removed {duplicates} duplicate rows")
        
        # Validate replies
        logger.info("Validating replies...")
        valid_mask = df.apply(self.validate_reply, axis=1)
        df = df[valid_mask].reset_index(drop=True)
        
        self.cleaned_count = len(df)
        
        # Add metadata
        df['cleaned_at'] = datetime.now().isoformat()
        
        # Reorder columns untuk consistency
        column_order = [
            'username', 'text', 'timestamp', 'post_url', 'post_id',
            'likes', 'comments', 'reposts', 'shares',
            'original_author', 'scraped_at', 'cleaned_at'
        ]
        
        # Keep hanya kolom yang ada
        available_cols = [c for c in column_order if c in df.columns]
        df = df[available_cols]
        
        # Save output
        if output_file:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            df.to_csv(output_file, index=False, encoding='utf-8')
            logger.info(f"Cleaned data saved to {output_file}")
        
        # Log statistics
        logger.info(f"Original rows: {self.original_count}")
        logger.info(f"Cleaned rows: {self.cleaned_count}")
        logger.info(f"Rows removed: {self.original_count - self.cleaned_count}")
        
        return df
    
    def generate_statistics(self, df: pd.DataFrame) -> dict:
        """Generate statistics tentang cleaned data"""
        stats = {
            'total_replies': len(df),
            'unique_users': df['username'].nunique(),
            'avg_engagement': {
                'likes': df['likes'].mean() if 'likes' in df else 0,
                'comments': df['comments'].mean() if 'comments' in df else 0,
                'reposts': df['reposts'].mean() if 'reposts' in df else 0,
                'shares': df['shares'].mean() if 'shares' in df else 0
            },
            'max_engagement': {
                'likes': df['likes'].max() if 'likes' in df else 0,
                'comments': df['comments'].max() if 'comments' in df else 0,
                'reposts': df['reposts'].max() if 'reposts' in df else 0,
                'shares': df['shares'].max() if 'shares' in df else 0
            },
            'avg_text_length': df['text'].str.len().mean(),
            'date_range': {
                'start': df['timestamp'].min() if 'timestamp' in df else None,
                'end': df['timestamp'].max() if 'timestamp' in df else None
            }
        }
        
        return stats

def main():
    """Main execution"""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description='Clean Threads replies data')
    parser.add_argument('--input', default='data/threads_replies/threads_replies_raw.csv',
                       help='Input CSV file')
    parser.add_argument('--output', default='data/threads_replies/threads_replies_clean.csv',
                       help='Output CSV file')
    parser.add_argument('--stats', action='store_true',
                       help='Generate dan print statistics')
    
    args = parser.parse_args()
    
    # Initialize cleaner
    cleaner = ThreadsRepliesCleaner()
    
    # Clean data
    logger.info("Starting cleaning process...")
    df = cleaner.clean_data(args.input, args.output)
    
    if not df.empty:
        # Generate statistics
        if args.stats:
            stats = cleaner.generate_statistics(df)
            logger.info("Statistics:")
            print(json.dumps(stats, indent=2, default=str))
            
            # Save statistics
            stats_file = args.output.replace('.csv', '_stats.json')
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, default=str)
            logger.info(f"Statistics saved to {stats_file}")
    else:
        logger.error("No data to clean")

if __name__ == '__main__':
    main()
