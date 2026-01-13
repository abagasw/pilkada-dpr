#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check Data Script - Verify dashboard data matches analisa.py output
"""

import sys
import os
from pathlib import Path
import pandas as pd

# Define paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_CLEAN_PATH = PROJECT_ROOT / "data" / "data_clean"
ANALYSIS_RESULTS_PATH = PROJECT_ROOT / "data" / "analysis_results"

print("=" * 70)
print("PILKADA DPRD - DATA CHECK")
print("=" * 70)
print()

# Check unified data file
UNIFIED_FILE = DATA_CLEAN_PATH / "df_unified_with_sentiment.csv"

if not UNIFIED_FILE.exists():
    print("[ERROR] Unified data file not found!")
    print("File: " + str(UNIFIED_FILE))
    print()
    print("Solution: Run analisa.py first")
    sys.exit(1)

print("[OK] Found unified data file")
print("Path: " + str(UNIFIED_FILE))
file_size_mb = UNIFIED_FILE.stat().st_size / 1024 / 1024
print("Size: {:.2f} MB".format(file_size_mb))
print()

# Load data
print("Loading data...")
df = pd.read_csv(UNIFIED_FILE)
print("[OK] Data loaded: {:,} rows, {} columns".format(len(df), len(df.columns)))
print()

# Show columns
print("Columns in dataset:")
for i, col in enumerate(df.columns, 1):
    dtype = df[col].dtype
    non_null = df[col].notna().sum()
    print("  {}. {:<30} ({}) - {:,} values".format(i, col, str(dtype), non_null))
print()

# Check required columns
print("Checking required columns...")
required = ['date_parsed', 'source', 'sentiment_label', 'text']
missing = [c for c in required if c not in df.columns]
if missing:
    print("[WARNING] Missing: " + str(missing))
else:
    print("[OK] All required columns present")
print()

# Statistics
print("Data Statistics:")
print()

# Date range
if 'date_parsed' in df.columns:
    df['date_parsed'] = pd.to_datetime(df['date_parsed'], errors='coerce')
    min_date = df['date_parsed'].min()
    max_date = df['date_parsed'].max()
    print("Date Range: {} to {}".format(min_date, max_date))

# Platforms
if 'source' in df.columns:
    print()
    print("Platforms:")
    for plat, count in df['source'].value_counts().items():
        print("  {}: {:,}".format(plat, count))

# Sentiment
if 'sentiment_label' in df.columns:
    print()
    print("Sentiments:")
    for sent, count in df['sentiment_label'].value_counts().items():
        pct = count / len(df) * 100
        print("  {}: {:,} ({:.1f}%)".format(sent, count, pct))

# Engagement
if 'engagement' in df.columns:
    avg_eng = df['engagement'].mean()
    print()
    print("Average Engagement: {:.0f}".format(avg_eng))

print()
print("=" * 70)
print("[SUCCESS] Data verification complete!")
print("=" * 70)
print()
print("Next: Run streamlit app")
print("Command: streamlit run streamlit_app.py")
print()
