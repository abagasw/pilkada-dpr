import pandas as pd
import streamlit as st
from pathlib import Path
import sys
import pickle

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
import config

@st.cache_data(ttl=config.CACHE_TTL)
def load_dashboard_data_pickle():
    """Load the notebook-exported dashboard bundle (dashboard_data.pkl).

    Expected format: dict with keys like 'df_unified', 'daily_sentiment', etc.
    """
    pkl_path = getattr(config, "DASHBOARD_DATA_PKL", None)
    if not pkl_path:
        return None

    try:
        pkl_path = Path(pkl_path)
        if not pkl_path.exists():
            return None

        with open(pkl_path, "rb") as f:
            data = pickle.load(f)

        if not isinstance(data, dict):
            st.warning("⚠️ dashboard_data.pkl loaded but is not a dict.")
            return None

        return data
    except Exception as e:
        st.warning(f"⚠️ Could not load dashboard_data.pkl: {e}")
        return None


def _normalize_sentiment_labels(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or not isinstance(df, pd.DataFrame):
        return df
    if 'sentiment_label' not in df.columns:
        return df

    s = df['sentiment_label'].astype(str).str.strip()
    s_lower = s.str.lower()
    mapped = s_lower.map({
        'positif': 'Positif',
        'positive': 'Positif',
        'negatif': 'Negatif',
        'negative': 'Negatif',
        'netral': 'Netral',
        'neutral': 'Netral',
    }).fillna(s)

    df = df.copy()
    df['sentiment_label'] = mapped
    return df


@st.cache_data(ttl=config.CACHE_TTL)
def load_unified_data():
    """Load unified dataset with sentiment analysis"""
    try:
        # Prefer notebook-exported bundle if available
        bundle = load_dashboard_data_pickle()
        if bundle and isinstance(bundle.get('df_unified'), pd.DataFrame):
            df = bundle['df_unified'].copy()
        else:
            df = pd.read_csv(config.UNIFIED_DATA_CSV)
        
        df = _normalize_sentiment_labels(df)

        # Parse dates
        if 'date_parsed' in df.columns:
            df['date_parsed'] = pd.to_datetime(df['date_parsed'], errors='coerce')
        
        return df
    except FileNotFoundError:
        st.error(f"❌ Data file not found: {config.UNIFIED_DATA_CSV}")
        return None
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        return None


@st.cache_data(ttl=config.CACHE_TTL)
def load_analysis_results():
    """Load pre-computed analysis results"""
    results = {}
    try:
        # Try to load JSON analysis files
        import json

        # Load a curated set of JSON artifacts produced by the notebook.
        analysis_files = [
            "01_sentiment_summary.json",
            "02_sentiment_by_platform.json",
            "03_keywords_analysis.json",
            "04_political_figures.json",
            "05_cooccurrence_analysis.json",
            "06_risk_assessment.json",
            "07_platform_analysis.json",
            "08_recommendations.json",
            "10_summary_report.json",
            "12_ml_model_results.json",
        ]

        for filename in analysis_files:
            filepath = config.DATA_ANALYSIS_PATH / filename
            if not filepath.exists():
                continue

            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Keep both a stable stem key and the original filename key.
            stem = Path(filename).stem
            results[stem] = data
            results[filename] = data
        
        return results
    except Exception as e:
        st.warning(f"⚠️ Some analysis files not found: {str(e)}")
        return results


def filter_data(df, date_range=None, platforms=None, sentiments=None):
    """Filter dataframe by date, platforms, and sentiments"""
    filtered_df = df.copy()
    
    # Filter by date range
    if date_range and 'date_parsed' in filtered_df.columns:
        start = pd.Timestamp(date_range[0])
        end = pd.Timestamp(date_range[1])

        # If end is a date (00:00), include the full end day
        try:
            import datetime as _dt
            if isinstance(date_range[1], _dt.date) and not isinstance(date_range[1], _dt.datetime):
                end = end + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
        except Exception:
            pass

        filtered_df = filtered_df[
            (filtered_df['date_parsed'] >= start) &
            (filtered_df['date_parsed'] <= end)
        ]
    
    # Filter by platforms
    if platforms and 'source' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['source'].isin(platforms)]
    
    # Filter by sentiments
    if sentiments and 'sentiment_label' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['sentiment_label'].isin(sentiments)]
    
    return filtered_df.reset_index(drop=True)


def get_sentiment_stats(df):
    """Get sentiment statistics"""
    if df is None or len(df) == 0:
        return None
    
    stats = {
        'total': len(df),
        'sentiment_counts': df['sentiment_label'].value_counts().to_dict() if 'sentiment_label' in df.columns else {},
        'avg_engagement': df['engagement'].mean() if 'engagement' in df.columns else 0,
        'action_keywords_pct': (df['has_action_keywords'].sum() / len(df) * 100) if 'has_action_keywords' in df.columns else 0,
    }
    
    return stats


def get_platform_breakdown(df):
    """Get breakdown by platform"""
    if df is None or 'source' not in df.columns:
        return None

    if 'sentiment_label' not in df.columns:
        return df['source'].value_counts().to_frame('count')
    
    breakdown = pd.crosstab(
        df['source'],
        df['sentiment_label'],
        margins=True
    )
    
    return breakdown


def calculate_risk_score(df):
    """Calculate risk/escalation score based on multiple factors"""
    if df is None or len(df) == 0:
        return 0.0
    
    weights = {
        'negative_sentiment': 0.4,
        'action_keywords': 0.4,
        'engagement': 0.2,
    }
    
    # Negative sentiment component
    negative_pct = (df['sentiment_label'] == 'Negatif').mean() if 'sentiment_label' in df.columns else 0
    
    # Action keywords component
    action_keywords_pct = (df['has_action_keywords'].sum() / len(df)) if 'has_action_keywords' in df.columns else 0
    
    # Engagement component (normalized)
    if 'engagement' in df.columns:
        avg_engagement = df['engagement'].mean()
        engagement_norm = min(avg_engagement / 1000, 1.0)  # Normalize to 0-1
    else:
        engagement_norm = 0
    
    risk_score = (
        negative_pct * weights['negative_sentiment'] +
        action_keywords_pct * weights['action_keywords'] +
        engagement_norm * weights['engagement']
    )
    
    return min(risk_score, 1.0)


def get_risk_level(risk_score):
    """Get risk level based on score"""
    if risk_score >= config.RISK_LEVELS["CRITICAL"]["threshold"]:
        return config.RISK_LEVELS["CRITICAL"]
    elif risk_score >= config.RISK_LEVELS["HIGH"]["threshold"]:
        return config.RISK_LEVELS["HIGH"]
    elif risk_score >= config.RISK_LEVELS["MEDIUM"]["threshold"]:
        return config.RISK_LEVELS["MEDIUM"]
    else:
        return config.RISK_LEVELS["LOW"]
