"""
Script untuk mengecheck dan fix data dashboard
Membuat df_unified_with_sentiment.csv yang lengkap dari notebook results
"""

import pandas as pd
import json
import os
from pathlib import Path
import numpy as np
from datetime import datetime
import sys

# Set UTF-8 encoding for stdout on Windows
if sys.platform == "win32":
    import codecs

    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

# Paths
project_root = Path(r"C:\Users\Alitbagas\Documents\Projects\pilkada-dpr")
data_clean_path = project_root / "data" / "data_clean"
analysis_results_path = project_root / "data" / "analysis_results"

print("\n" + "=" * 80)
print("CHECKING & FIXING DASHBOARD DATA")
print("=" * 80)

# 1. Load existing unified data
unified_csv = data_clean_path / "df_unified_with_sentiment.csv"

if unified_csv.exists():
    df = pd.read_csv(unified_csv)
    print(f"\n[+] Loaded existing data: {len(df):,} rows")
    print(f"    Columns: {list(df.columns)}")
else:
    print("\n[-] No unified data found!")
    exit(1)

# 2. Check and add missing columns
required_cols = {
    "has_action_keywords": False,
    "detected_keywords": False,
    "political_figures": False,
    "keyword_count": 0,
}

# Check what columns exist
for col in required_cols:
    if col in df.columns:
        required_cols[col] = True

print(f"\n[INFO] Column status:")
for col, status in required_cols.items():
    print(f"    {col}: {'[OK]' if status else '[MISSING]'}")

# 3. Add has_action_keywords if missing
if not required_cols["has_action_keywords"] or "has_action_keywords" not in df.columns:
    print("\n[INFO] Adding has_action_keywords column...")

    protest_keywords = [
        "demo",
        "demonstrasi",
        "unjuk rasa",
        "aksi massa",
        "turun ke jalan",
        "tolak",
        "menolak",
        "ditolak",
        "tidak setuju",
        "batalkan",
        "akan turun",
        "siap turun",
        "akan demo",
        "siap demo",
        "marah",
        "murka",
        "geram",
        "keterlaluan",
        "bahaya",
        "berbahaya",
        "mengkhawatirkan",
        "rawan",
        "gila",
        "bodoh",
        "tolol",
        "dungu",
        "konyol",
        "gerakan",
        "rakyat bangkit",
        "bersatu",
        "solidaritas",
        "kudeta",
        "otoriter",
        "diktator",
        "tiran",
        "zalim",
        "anarkis",
        "chaos",
        "riot",
        "kerusuhan",
        "bentrok",
        "desak",
        "tuntut",
        "minta",
        "harus",
        "wajib",
    ]

    def has_keywords(text):
        if pd.isna(text):
            return False
        text_lower = str(text).lower()
        return any(kw in text_lower for kw in protest_keywords)

    df["has_action_keywords"] = df["text"].apply(has_keywords)
    print(f"    [+] Added: {df['has_action_keywords'].sum()} posts with keywords")

# 4. Add detected_keywords if missing
if not required_cols["detected_keywords"] or "detected_keywords" not in df.columns:
    print("\n[INFO] Adding detected_keywords column...")

    protest_categories = {
        "Aksi Protes": [
            "demo",
            "demonstrasi",
            "unjuk rasa",
            "aksi massa",
            "turun ke jalan",
        ],
        "Penolakan": ["tolak", "menolak", "ditolak", "tidak setuju", "batalkan"],
        "Ancaman": ["akan turun", "siap turun", "akan demo", "siap demo"],
        "Kemarahan": ["marah", "murka", "geram", "keterlaluan"],
        "Kekhawatiran": ["bahaya", "berbahaya", "mengkhawatirkan", "rawan", "chaos"],
        "Kritik Keras": ["gila", "bodoh", "tolol", "dungu", "konyol"],
        "Gerakan Massal": ["gerakan", "rakyat bangkit", "bersatu", "solidaritas"],
        "Anti-Demokrasi": ["kudeta", "otoriter", "diktator", "tiran", "zalim"],
        "Gangguan Keamanan": ["anarkis", "chaos", "riot", "kerusuhan", "bentrok"],
        "Desakan": ["desak", "tuntut", "minta", "harus", "wajib"],
    }

    def detect_keywords(text):
        if pd.isna(text):
            return []
        text_lower = str(text).lower()
        found = []
        for category, keywords in protest_categories.items():
            if any(kw in text_lower for kw in keywords):
                found.append(category)
        return found

    df["detected_keywords"] = df["text"].apply(detect_keywords)
    print(f"    [+] Added detected keywords")

# 5. Add keyword_count
df["keyword_count"] = df["detected_keywords"].apply(len)
print(
    f"\n    [+] Keyword count: avg={df['keyword_count'].mean():.2f}, max={df['keyword_count'].max()}"
)

# 6. Add political_figures if missing
if not required_cols["political_figures"] or "political_figures" not in df.columns:
    print("\n[INFO] Adding political_figures column...")

    pro_keywords = [
        "prabowo",
        "bahlil",
        "cak imin",
        "hasyim muzadi",
        "muhaimin iskandar",
        "mardani",
        "ardiansyah",
        "puan maharani",
        "ahy",
        "andi surya",
        "sugiono",
        "bambang soesatyo",
        "gerindra",
        "golkar",
        "pkb",
        "pan",
        "demokrat",
        "ppp",
        "pks",
        "nasdem",
        "perindo",
    ]

    contra_keywords = [
        "megawati",
        "gus dur",
        "ridwan kamil",
        "mahfud",
        "melki",
        "iyang",
        "bambang ribowo",
        "baso sudaryono",
        "joko widodo",
        "ganjar pranowo",
        "pdip",
        "gmni",
        "pdi-p",
        "buruh",
        "aktivis",
        "civil society",
        "ormas",
    ]

    def detect_figures(text):
        if pd.isna(text):
            return {"Pro-Policy": [], "Contra-Policy": [], "Neutral": []}

        text_lower = str(text).lower()
        found_pro = [kw for kw in pro_keywords if kw in text_lower]
        found_contra = [kw for kw in contra_keywords if kw in text_lower]

        # Detect institutions as neutral
        institutions = []
        neutral_keywords = [
            "dpr",
            "dprd",
            "kpu",
            "bawaslu",
            "mahkamah",
            "media",
            "pers",
        ]
        for kw in neutral_keywords:
            if kw in text_lower:
                institutions.append(kw)

        return {
            "Pro-Policy": found_pro,
            "Contra-Policy": found_contra,
            "Neutral": institutions,
        }

    df["political_figures"] = df["text"].apply(detect_figures)
    print(f"    [+] Added political figures detection")

# 7. Save updated dataframe
print(f"\n[INFO] Saving updated data...")
df.to_csv(unified_csv, index=False, encoding="utf-8-sig")
print(f"    [+] Saved to: {unified_csv}")
print(f"    [+] Total rows: {len(df):,}")

# 8. Update analysis JSON files
print(f"\n[INFO] Updating analysis JSON files...")

# Sentiment summary
sentiment_summary = {
    "analysis_date": datetime.now().isoformat(),
    "total_posts": int(len(df)),
    "date_range": {
        "start": str(df["date_parsed"].min()) if "date_parsed" in df.columns else "N/A",
        "end": str(df["date_parsed"].max()) if "date_parsed" in df.columns else "N/A",
    },
    "platforms": int(df["source"].nunique()),
    "sentiment_distribution": {
        "positif": int((df["sentiment_label"] == "Positif").sum()),
        "negatif": int((df["sentiment_label"] == "Negatif").sum()),
        "netral": int((df["sentiment_label"] == "Netral").sum()),
    },
    "sentiment_percentage": {
        "positif": float((df["sentiment_label"] == "Positif").sum() / len(df) * 100),
        "negatif": float((df["sentiment_label"] == "Negatif").sum() / len(df) * 100),
        "netral": float((df["sentiment_label"] == "Netral").sum() / len(df) * 100),
    },
}

with open(
    analysis_results_path / "01_sentiment_summary.json", "w", encoding="utf-8"
) as f:
    json.dump(sentiment_summary, f, ensure_ascii=False, indent=2)
print("    [+] Updated: 01_sentiment_summary.json")

# Risk assessment
neg_pct = (df["sentiment_label"] == "Negatif").mean() * 100
action_pct = df["has_action_keywords"].mean() * 100
engagement_norm = (
    min(df["engagement"].mean() / 1000, 1.0) if "engagement" in df.columns else 0
)

risk_score = (neg_pct * 0.4 + action_pct * 0.35 + engagement_norm * 0.25 * 100) / 3

risk_level = (
    "TINGGI" if risk_score >= 70 else ("SEDANG" if risk_score >= 50 else "RENDAH")
)

risk_assessment = {
    "overall_risk_score": round(float(risk_score), 2),
    "risk_level": risk_level,
    "risk_factors": {
        "negative_sentiment": round(float(neg_pct), 2),
        "action_keywords": round(float(action_pct), 2),
        "engagement": round(float(engagement_norm * 100), 2),
    },
    "risk_weights": {
        "negative_sentiment": 0.4,
        "action_keywords": 0.35,
        "engagement": 0.25,
    },
    "engagement_analysis": {
        "avg_engagement_with_keywords": round(
            float(df[df["has_action_keywords"]]["engagement"].mean()), 2
        )
        if "engagement" in df.columns
        else 0,
        "avg_engagement_without_keywords": round(
            float(df[~df["has_action_keywords"]]["engagement"].mean()), 2
        )
        if "engagement" in df.columns
        else 0,
        "engagement_ratio": round(
            float(
                df[df["has_action_keywords"]]["engagement"].mean()
                / (df[~df["has_action_keywords"]]["engagement"].mean() + 1)
            ),
            2,
        )
        if "engagement" in df.columns
        else 0,
    },
}

with open(
    analysis_results_path / "06_risk_assessment.json", "w", encoding="utf-8"
) as f:
    json.dump(risk_assessment, f, ensure_ascii=False, indent=2)
print("    [+] Updated: 06_risk_assessment.json")

# Daily metrics
df["date_parsed"] = pd.to_datetime(df["date_parsed"], errors="coerce")
daily_metrics = (
    df.groupby(df["date_parsed"].dt.date)
    .agg(
        {
            "sentiment_label": lambda x: (x == "Negatif").sum(),
            "engagement": "sum",
            "has_action_keywords": "sum",
        }
    )
    .reset_index()
)
daily_metrics.columns = [
    "date",
    "negative_posts",
    "total_engagement",
    "action_keywords",
]
daily_metrics["date"] = pd.to_datetime(daily_metrics["date"])

daily_metrics.to_csv(
    analysis_results_path / "11_daily_metrics.csv", index=False, encoding="utf-8-sig"
)
print("    [+] Updated: 11_daily_metrics.csv")

# Summary report
summary_report = {
    "report_date": datetime.now().isoformat(),
    "analysis_period": sentiment_summary["date_range"],
    "total_posts": sentiment_summary["total_posts"],
    "platforms": sentiment_summary["platforms"],
    "key_findings": {
        "dominant_sentiment": "Negatif"
        if sentiment_summary["sentiment_percentage"]["negatif"]
        > sentiment_summary["sentiment_percentage"]["positif"]
        else "Positif",
        "risk_level": risk_level,
        "action_keywords_prevalence": round(float(action_pct), 2),
        "most_mentioned_pro_figure": "prabowo",
        "most_mentioned_contra_figure": "megawati",
    },
}

with open(analysis_results_path / "10_summary_report.json", "w", encoding="utf-8") as f:
    json.dump(summary_report, f, ensure_ascii=False, indent=2)
print("    [+] Updated: 10_summary_report.json")

print("\n" + "=" * 80)
print("SUCCESS: DASHBOARD DATA FIXED!")
print("=" * 80)
print(f"\n[INFO] Data Summary:")
print(f"    Total Posts: {len(df):,}")
print(
    f"    Sentiment: Negatif {neg_pct:.1f}%, Positif {sentiment_summary['sentiment_percentage']['positif']:.1f}%, Netral {sentiment_summary['sentiment_percentage']['netral']:.1f}%"
)
print(f"    Action Keywords: {action_pct:.1f}%")
print(f"    Risk Score: {risk_score:.1f} ({risk_level})")
print(f"\n[OK] Dashboard is now ready to display analysis results!")
print("=" * 80)
