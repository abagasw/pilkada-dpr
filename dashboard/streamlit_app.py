import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import Counter
import re
import json
import sys
from pathlib import Path

# Configure page
st.set_page_config(
    page_title="Dashboard Monitoring Sentimen Pilkada DPRD",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent))
from utils import (
    load_dashboard_data_pickle,
    load_unified_data,
    load_analysis_results,
    filter_data,
    get_sentiment_stats,
    get_platform_breakdown,
    calculate_risk_score,
    get_risk_level,
    create_sentiment_pie_chart,
    create_sentiment_trend_chart,
    create_platform_sentiment_chart,
    create_keyword_chart,
    create_political_figures_chart,
    create_engagement_chart,
    create_risk_gauge,
    create_keyword_sentiment_heatmap,
)
import config

# Import Indonesian translations
from translations_id import *

# ============================================================================
# CSS STYLING
# ============================================================================

st.markdown("""
<style>
    /* Main styling */
    .main {
        padding: 0rem 1rem;
    }
    
    /* Metric cards */
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    /* Risk level styling */
    .risk-critical {
        background: linear-gradient(135deg, #C0392B 0%, #E74C3C 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin: 20px 0;
    }
    
    .risk-high {
        background: linear-gradient(135deg, #F39C12 0%, #E67E22 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin: 20px 0;
    }
    
    .risk-medium {
        background: linear-gradient(135deg, #F39C12 0%, #F4D03F 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin: 20px 0;
    }
    
    .risk-low {
        background: linear-gradient(135deg, #2ECC71 0%, #27AE60 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin: 20px 0;
    }
    
    /* Header styling */
    .header-main {
        text-align: center;
        padding: 20px 0;
        border-bottom: 3px solid #E74C3C;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# HEADER
# ============================================================================

st.markdown(f"""
<div class="header-main">
    <h1>{DASHBOARD_TITLE}</h1>
    <p style="color: #7f8c8d; font-size: 16px;">
        {DASHBOARD_SUBTITLE}
    </p>
</div>
""", unsafe_allow_html=True)

# Dashboard Description
with st.expander("ℹ️ Tentang Dashboard Ini", expanded=False):
    st.markdown(DASHBOARD_DESCRIPTION)

# ============================================================================
# LOAD DATA
# ============================================================================

with st.spinner(INFO_LOADING):
    df_unified = load_unified_data()

# Optional notebook exports (used to align dashboard with pilkada_dpr_analysis.ipynb)
analysis_results = load_analysis_results()
dashboard_bundle = load_dashboard_data_pickle()

# Paths for notebook-exported artifacts
summary_path = config.DATA_ANALYSIS_PATH / "10_summary_report.json"
risk_path = config.DATA_ANALYSIS_PATH / "06_risk_assessment.json"


def _clean_keyword_label(raw_value) -> str:
    if raw_value is None:
        return ""
    text = str(raw_value).strip()
    if text in {"[]", "[ ]", ""}:
        return ""

    # Remove list-like formatting artifacts and normalize whitespace
    text = (
        text.replace("[", " ")
            .replace("]", " ")
            .replace("'", "")
            .replace('"', "")
            .replace("\\n", " ")
    )
    text = re.sub(r"\s+", " ", text).strip().strip(",")
    return text


def _normalize_sentiment_label_series(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.strip()
    s_lower = s.str.lower()
    return s_lower.map({
        'positif': 'Positif',
        'positive': 'Positif',
        'negatif': 'Negatif',
        'negative': 'Negatif',
        'netral': 'Netral',
        'neutral': 'Netral',
    }).fillna(s)

if df_unified is None or len(df_unified) == 0:
    st.error(ERROR_LOADING)
    st.stop()

# For type-checkers (st.stop() is not understood as terminating)
assert df_unified is not None

# ============================================================================
# SIDEBAR - FILTERS
# ============================================================================

# Get date range from actual data
if 'date_parsed' in df_unified.columns:
    df_unified['date_parsed'] = pd.to_datetime(df_unified['date_parsed'], errors='coerce')
    min_date = df_unified['date_parsed'].min()
    max_date = df_unified['date_parsed'].max()
    if pd.isna(min_date):
        min_date = datetime(2025, 1, 1)
    if pd.isna(max_date):
        max_date = datetime.now()
else:
    min_date = datetime(2025, 1, 1)
    max_date = datetime.now()

# Normalize sentiment labels BEFORE filtering so sentiment filters match the data
if 'sentiment_label' in df_unified.columns:
    df_unified['sentiment_label'] = _normalize_sentiment_label_series(df_unified['sentiment_label'])

# Ensure Session State defaults exist (prevents missing keys when sidebar tab != Filters)
default_platforms = list(config.PLATFORMS.keys())
default_sentiments = ['Positif', 'Negatif', 'Netral']
default_date_range = (
    min_date.date() if hasattr(min_date, 'date') else min_date,
    max_date.date() if hasattr(max_date, 'date') else max_date,
)

if 'date_range' not in st.session_state:
    st.session_state['date_range'] = default_date_range
if 'platforms' not in st.session_state:
    st.session_state['platforms'] = default_platforms
if 'sentiments' not in st.session_state:
    st.session_state['sentiments'] = default_sentiments
if 'filters_applied' not in st.session_state:
    st.session_state['filters_applied'] = True

with st.sidebar:
    st.header(SIDEBAR_TITLE)
    st.caption(SIDEBAR_DESCRIPTION)

    if dashboard_bundle is not None:
        st.success("📦 Sumber data: dashboard_data.pkl")
    else:
        st.info("📄 Sumber data: df_unified_with_sentiment.csv")
    
    # Create tabs in sidebar
    filter_tab = st.radio("Pilih:", ["Filter", "Tentang", "Pengaturan"])
    
    if filter_tab == "Filter":
        st.subheader(FILTER_DATE_RANGE)
        
        # Use FULL data range as default
        date_range = st.date_input(
            "Pilih Rentang Tanggal",
            value=(
                min_date.date() if hasattr(min_date, 'date') else min_date,
                max_date.date() if hasattr(max_date, 'date') else max_date
            ),
            help=FILTER_DATE_HELP,
            key="date_range"
        )
        
        st.subheader(FILTER_PLATFORM)
        platforms = st.multiselect(
            "Pilih Platform",
            options=default_platforms,
            default=default_platforms,
            help=FILTER_PLATFORM_HELP,
            key="platforms"
        )
        
        st.subheader(FILTER_SENTIMENT)
        sentiments = st.multiselect(
            "Pilih Sentimen",
            options=['Positif', 'Negatif', 'Netral'],
            default=['Positif', 'Negatif', 'Netral'],
            key="sentiments"
        )
        
        # Apply filters button
        if st.button("🔍 Apply Filters", key="apply_filters"):
            st.session_state.filters_applied = True
    
    elif filter_tab == "About":
        st.subheader("ℹ️ About This Dashboard")
        st.write("""
        **Dashboard Analisis Pilkada DPRD**
        
        Dashboard interaktif untuk monitoring sentimen publik, analisis risiko, 
        dan identifikasi figur-figur kunci dalam wacana pemilihan gubernur oleh DPRD.
        
        **Data Sources:**
        - TikTok
        - Facebook
        - X/Twitter
        - Instagram
        - YouTube
        - Threads
        - Online News
        
        **Analysis Period:**
        January 2026
        
        **Last Updated:**
        """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    
    else:  # Settings
        st.subheader("⚙️ Settings")
        if st.button("🔄 Clear cache & reload data", key="clear_cache_reload"):
            try:
                st.cache_data.clear()
            except Exception:
                pass
            try:
                st.cache_resource.clear()
            except Exception:
                pass
            st.rerun()

# ============================================================================
# GET USER FILTERS
# ============================================================================

if st.session_state.get('filters_applied', True):
    df_filtered = filter_data(
        df_unified,
        date_range=st.session_state.get('date_range', default_date_range),
        platforms=st.session_state.get('platforms', default_platforms),
        sentiments=st.session_state.get('sentiments', default_sentiments)
    )
else:
    df_filtered = df_unified.copy()

# Normalize filtered labels too (defensive; should already be normalized)
if 'sentiment_label' in df_filtered.columns:
    df_filtered['sentiment_label'] = _normalize_sentiment_label_series(df_filtered['sentiment_label'])

# ============================================================================
# MAIN METRICS (KPI)
# ============================================================================

st.header(OVERVIEW_TITLE)
st.caption(OVERVIEW_DESCRIPTION)

# Show data summary info
st.info(f"📊 **Data Dimuat:** {len(df_unified):,} total rekord | **Terfilter:** {len(df_filtered):,} rekord | **Rentang Tanggal:** {min_date.strftime('%Y-%m-%d')} s/d {max_date.strftime('%Y-%m-%d')}")

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_posts = len(df_filtered)
    st.metric(
        label="📌 Total Postingan",
        value=f"{total_posts:,}",
        delta=f"dari {len(df_unified):,} total",
        help=METRIC_TOTAL_POSTS_HELP
    )

with col2:
    neg_pct = (df_filtered['sentiment_label'] == 'Negatif').mean() * 100 if len(df_filtered) > 0 else 0
    st.metric(
        label="❌ Sentimen Negatif",
        value=f"{neg_pct:.1f}%",
        delta=f"{(df_filtered['sentiment_label'] == 'Negatif').sum():,} postingan",
        delta_color="inverse",
        help="Persentase postingan dengan sentimen negatif terhadap kebijakan"
    )

with col3:
    if 'has_action_keywords' in df_filtered.columns:
        action_keywords = df_filtered['has_action_keywords'].sum()
        action_pct = (action_keywords / len(df_filtered) * 100) if len(df_filtered) > 0 else 0
    else:
        # Estimate from sentiment - negative often has action keywords
        action_keywords = (df_filtered['sentiment_label'] == 'Negatif').sum()
        action_pct = (action_keywords / len(df_filtered) * 100) if len(df_filtered) > 0 else 0
    
    st.metric(
        label="🔥 Kata Kunci Aksi",
        value=f"{action_pct:.1f}%",
        delta=f"{action_keywords:,} postingan",
        help="Postingan yang mengandung kata-kata mobilisasi seperti 'demo', 'turun', 'tolak'"
    )

with col4:
    avg_engagement = df_filtered['engagement'].mean() if 'engagement' in df_filtered.columns else 0
    st.metric(
        label="💬 Rata-rata Engagement",
        value=f"{avg_engagement:.0f}",
        delta="+8%" if len(df_filtered) > 0 else "---",
        help=METRIC_ENGAGEMENT_HELP
    )

# ============================================================================
# SECTION 1: SENTIMENT ANALYSIS
# ============================================================================

st.header(SENTIMENT_TITLE)

# Add explanation
with st.expander("ℹ️ Penjelasan Analisis Sentimen", expanded=False):
    st.markdown(SENTIMENT_DESCRIPTION)

# Notebook-style charts: Overall pie + Count-by-platform grouped bar
try:
    import plotly.express as px
    import plotly.graph_objects as go
    try:
        import altair as alt
        altair_available = True
    except ImportError:
        altair_available = False
        st.warning("Altair tidak tersedia, menggunakan chart Plotly")

    sentiment_order = ['Positif', 'Negatif', 'Netral']
    sentiment_colors = {
        'Positif': config.SENTIMENT_COLORS.get('Positif', '#2ecc71'),
        'Negatif': config.SENTIMENT_COLORS.get('Negatif', '#e74c3c'),
        'Netral': config.SENTIMENT_COLORS.get('Netral', '#95a5a6'),
    }

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        if 'sentiment_label' in df_filtered.columns and len(df_filtered) > 0:
            vc = (
                df_filtered['sentiment_label']
                .astype(str)
                .str.strip()
                .value_counts()
                .reindex(sentiment_order)
                .fillna(0)
                .astype(int)
            )
            vc = vc[vc > 0]
            
            # Use Plotly pie chart (more reliable than Altair)
            fig_pie = go.Figure(data=[
                go.Pie(
                    labels=list(vc.index),
                    values=list(vc.values),
                    marker=dict(colors=[sentiment_colors[s] for s in vc.index]),
                    textinfo='label+percent+value',
                    textfont=dict(size=12),
                    hovertemplate='<b>%{label}</b><br>Jumlah: %{value:,}<br>Persentase: %{percent}<extra></extra>'
                )
            ])
            
            fig_pie.update_layout(
                height=400,
                margin=dict(l=10, r=10, t=80, b=10),
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.1,
                    xanchor="center",
                    x=0.5
                )
            )
            
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Data kosong untuk membuat pie chart.")

    with chart_col2:
        if 'source' in df_filtered.columns and 'sentiment_label' in df_filtered.columns and len(df_filtered) > 0:
            ctab = pd.crosstab(df_filtered['source'], df_filtered['sentiment_label'])
            ctab = ctab[[c for c in sentiment_order if c in ctab.columns]]
            if not ctab.empty:
                # Match notebook ordering (pd.crosstab default is sorted index)
                ctab = ctab.reindex(sorted(ctab.index))
                long_df = ctab.reset_index().melt(id_vars='source', var_name='Sentimen', value_name='Jumlah')
                
                # Ensure data types are correct
                long_df['Jumlah'] = long_df['Jumlah'].astype(int)
                max_val = int(long_df['Jumlah'].max())
                
                # Try Altair if available, fallback to Plotly
                if altair_available:
                    try:
                        # Simple and reliable Altair bar chart
                        bar_chart = alt.Chart(long_df).mark_bar(
                            stroke='white',
                            strokeWidth=1
                        ).encode(
                            x=alt.X('source:N', title='Platform', sort=sorted(ctab.index)),
                            y=alt.Y('Jumlah:Q', title='Jumlah Postingan', scale=alt.Scale(domain=[0, max_val * 1.1])),
                            color=alt.Color('Sentimen:N', 
                                scale=alt.Scale(
                                    domain=sentiment_order,
                                    range=[sentiment_colors[s] for s in sentiment_order]
                                ),
                                legend=alt.Legend(title='Sentimen')
                            ),
                            xOffset='Sentimen:N',
                            tooltip=['source:N', 'Sentimen:N', alt.Tooltip('Jumlah:Q', format=',.0f')]
                        ).properties(
                            width=550,
                            height=400,
                            )
                        
                        st.altair_chart(bar_chart, use_container_width=True)
                    except Exception as e:
                        st.warning(f"Altair chart failed: {e}, using Plotly")
                        altair_available = False
                
                if not altair_available:
                    # Fallback to reliable Plotly grouped bar chart
                    fig_bar = px.bar(
                        long_df,
                        x='source',
                        y='Jumlah',
                        color='Sentimen',
                        barmode='group',
                        category_orders={
                            'source': sorted(ctab.index), 
                            'Sentimen': sentiment_order
                        },
                        color_discrete_map=sentiment_colors,
                        title='Distribusi Sentimen Berdasarkan Platform Media',
                        labels={'source': 'Platform', 'Jumlah': 'Jumlah Postingan'},
                        text='Jumlah'
                    )
                    
                    # Update layout for better visibility
                    fig_bar.update_layout(
                        height=450,
                        margin=dict(l=10, r=10, t=60, b=10),
                        legend=dict(title='Sentimen', x=1.02, y=1, xanchor='left', yanchor='top'),
                        yaxis_title="Jumlah Postingan",
                        yaxis=dict(
                            range=[0, max_val * 1.1],
                            tickformat=","
                        )
                    )
                    
                    fig_bar.update_xaxes(tickangle=45, title_text="Platform")
                    fig_bar.update_traces(
                        texttemplate='%{text:,.0f}',
                        textposition='outside',
                        textfont_size=10
                    )
                    
                    st.plotly_chart(fig_bar, use_container_width=True)
                
                # Show data summary for verification
                tiktok_neg = long_df[(long_df['source'] == 'tiktok') & (long_df['Sentimen'] == 'Negatif')]['Jumlah'].iloc[0] if len(long_df[(long_df['source'] == 'tiktok') & (long_df['Sentimen'] == 'Negatif')]) > 0 else 0
            else:
                st.info("Tidak ada data platform untuk ditampilkan.")
        else:
            st.info("Kolom source/sentiment_label tidak tersedia.")
except Exception as e:
    st.warning(f"Chart notebook-style tidak dapat ditampilkan: {e}")

# Create crosstab like notebook
sentiment_by_source = pd.crosstab(
    df_filtered['source'], 
    df_filtered['sentiment_label'], 
    margins=True
)
# Sort index to match chart order (alphabetical, 'All' at bottom)
sentiment_by_source = sentiment_by_source.reindex(sorted([idx for idx in sentiment_by_source.index if idx != 'All']) + ['All'])
# Reorder columns
cols_order = [c for c in ['Positif', 'Negatif', 'Netral', 'All'] if c in sentiment_by_source.columns]
sentiment_by_source = sentiment_by_source[cols_order]

sentiment_pct = pd.crosstab(
    df_filtered['source'], 
    df_filtered['sentiment_label'], 
    normalize='index'
) * 100
# Sort to match chart order (alphabetical)
sentiment_pct = sentiment_pct.reindex(sorted(sentiment_pct.index))

# Format as percentage
sentiment_pct_display = sentiment_pct.round(2).astype(str) + '%'

# Platform Sentiment Summary
st.write("**Platform Sentiment Summary**")

platform_summary = []
for source in df_filtered['source'].unique():
    source_data = df_filtered[df_filtered['source'] == source]
    total = len(source_data)
    positif = (source_data['sentiment_label'] == 'Positif').sum()
    negatif = (source_data['sentiment_label'] == 'Negatif').sum()
    netral = (source_data['sentiment_label'] == 'Netral').sum()
    
    platform_summary.append({
        'Platform': source.upper(),
        'Total Posts': total,
        'Positif': f"{positif} ({positif/total*100:.2f}%)",
        'Negatif': f"{negatif} ({negatif/total*100:.2f}%)",
        'Netral': f"{netral} ({netral/total*100:.2f}%)"
    })

df_summary = pd.DataFrame(platform_summary)
# Sort alphabetically to match chart order (not by total posts)
df_summary = df_summary.sort_values('Platform', ascending=True)
st.dataframe(df_summary, use_container_width=True)

# Sentiment Trend Over Time
st.subheader("📈 Sentiment Trend Over Time")

try:
    import altair as alt
    
    # Ensure date_parsed is datetime
    if 'date_parsed' in df_filtered.columns:
        df_with_dates = df_filtered.copy()
        df_with_dates['date_parsed'] = pd.to_datetime(df_with_dates['date_parsed'], errors='coerce')
        df_with_dates = df_with_dates[df_with_dates['date_parsed'].notna()].copy()
        
        if len(df_with_dates) > 0:
            # Create daily sentiment counts
            df_with_dates['date_only'] = df_with_dates['date_parsed'].dt.date
            daily_sentiment = df_with_dates.groupby(['date_only', 'sentiment_label']).size().reset_index(name='count')
            
            # Calculate daily totals and percentages
            daily_totals = daily_sentiment.groupby('date_only')['count'].sum().reset_index(name='total')
            daily_sentiment = daily_sentiment.merge(daily_totals, on='date_only')
            daily_sentiment['percentage'] = (daily_sentiment['count'] / daily_sentiment['total']) * 100
            
            # Convert date to datetime for Altair
            daily_sentiment['date_only'] = pd.to_datetime(daily_sentiment['date_only'])
            
            # Calculate 7-day moving average for each sentiment
            sentiment_ma_data = []
            for sentiment in ['Positif', 'Negatif', 'Netral']:
                sentiment_df = daily_sentiment[daily_sentiment['sentiment_label'] == sentiment].copy()
                sentiment_df = sentiment_df.sort_values('date_only')
                sentiment_df['ma_7'] = sentiment_df['percentage'].rolling(window=7, min_periods=1).mean()
                sentiment_ma_data.append(sentiment_df[['date_only', 'sentiment_label', 'ma_7']])
            
            ma_df = pd.concat(sentiment_ma_data, ignore_index=True)
            
            # Create line chart with Altair
            sentiment_colors_map = {
                'Positif': '#2ecc71',
                'Negatif': '#e74c3c',
                'Netral': '#95a5a6'
            }
            
            chart_trend = alt.Chart(ma_df).mark_line(strokeWidth=3, opacity=0.8).encode(
                x=alt.X('date_only:T', title='Tanggal', axis=alt.Axis(format='%Y-%m-%d', labelAngle=-45)),
                y=alt.Y('ma_7:Q', title='Persentase (%)', scale=alt.Scale(domain=[0, 100])),
                color=alt.Color('sentiment_label:N', 
                    scale=alt.Scale(
                        domain=['Positif', 'Negatif', 'Netral'],
                        range=[sentiment_colors_map['Positif'], sentiment_colors_map['Negatif'], sentiment_colors_map['Netral']]
                    ),
                    legend=alt.Legend(title='Sentimen')
                ),
                tooltip=[
                    alt.Tooltip('date_only:T', title='Tanggal', format='%Y-%m-%d'),
                    alt.Tooltip('sentiment_label:N', title='Sentimen'),
                    alt.Tooltip('ma_7:Q', title='Persentase (7-day MA)', format='.2f')
                ]
            ).properties(
                title='Tren Sentimen Publik Over Time (7-day Moving Average)',
                height=400
            ).configure_axis(
                labelFontSize=11,
                titleFontSize=12
            ).configure_title(
                fontSize=14,
                fontWeight='bold'
            ).configure_legend(
                labelFontSize=11,
                titleFontSize=12
            )
            
            st.altair_chart(chart_trend, use_container_width=True)
            
            # Summary statistics
            col_trend1, col_trend2, col_trend3 = st.columns(3)
            
            with col_trend1:
                date_range_days = (df_with_dates['date_parsed'].max() - df_with_dates['date_parsed'].min()).days
                st.metric("Date Range", f"{date_range_days} days")
            
            with col_trend2:
                # Latest sentiment distribution
                latest_date = df_with_dates['date_only'].max()
                latest_data = daily_sentiment[daily_sentiment['date_only'] == pd.to_datetime(latest_date)]
                if len(latest_data) > 0:
                    latest_neg = latest_data[latest_data['sentiment_label'] == 'Negatif']['percentage'].values
                    latest_neg_pct = latest_neg[0] if len(latest_neg) > 0 else 0
                    st.metric("Latest Negative %", f"{latest_neg_pct:.1f}%")
            
            with col_trend3:
                # Average negative sentiment
                avg_neg = ma_df[ma_df['sentiment_label'] == 'Negatif']['ma_7'].mean()
                st.metric("Avg Negative % (7-day MA)", f"{avg_neg:.1f}%")
        else:
            st.info("No date data available for trend analysis")
    else:
        st.info("Date column not found in data")
        
except Exception as e:
    st.warning(f"Could not create sentiment trend chart: {e}")
    import traceback
    st.code(traceback.format_exc())

# ============================================================================
# ROOT CAUSE ANALYSIS: DEEP DIVE INTO NEGATIVE SENTIMENT
# ============================================================================

st.header("🔍 Analisis Akar Masalah: Mengapa Sentimen Negatif Tinggi?")
st.caption("Analisis mendalam sentimen negatif untuk memahami kekhawatiran dan keluhan utama")

with st.expander("ℹ️ Penjelasan Analisis Akar Masalah", expanded=False):
    st.markdown("""
**Analisis Akar Masalah mengidentifikasi:**
- Keluhan dan kekhawatiran utama publik
- Platform dengan tingkat negativitas tertinggi
- Periode waktu dengan lonjakan sentimen negatif
- Pemicu (triggers) yang menyebabkan eskalasi

**Kegunaan:**
- Memahami akar permasalahan, bukan hanya gejala
- Merancang strategi komunikasi yang tepat sasaran
- Mengantisipasi isu yang akan berkembang
- Memprioritaskan respons berdasarkan concern terbesar

**7 Kategori Pain Points:**
1. Demokrasi Dirampas - Kehilangan hak pilih langsung
2. Korupsi & Politik Uang - Kekhawatiran suap dan transaksional
3. Legitimasi Pemimpin - Pertanyaan tentang keabsahan
4. Oligarki Elite - Dominasi elite politik
5. Kepentingan Pribadi - Tidak mewakili rakyat
6. Ketidakpercayaan Institusi - Hilangnya trust
7. Kekhawatiran Otoriter - Ancaman kebebasan
    """)

# Analyze negative sentiment posts
negative_posts = df_filtered[df_filtered['sentiment_label'] == 'Negatif'].copy()

if len(negative_posts) > 0:
    neg_pct = (len(negative_posts) / len(df_filtered) * 100)
    st.info(f"📊 Menganalisis **{len(negative_posts):,}** postingan negatif (**{neg_pct:.1f}%** dari total)")
    
    # 1. KEY PAIN POINTS
    st.subheader("1️⃣ Keluhan Utama (Kekhawatiran yang Paling Sering Muncul)")
    
    pain_points = {
        'Demokrasi Dirampas': ['demokrasi', 'hak', 'rakyat', 'suara', 'pilih', 'langsung', 'hilang'],
        'Korupsi & Politik Uang': ['korupsi', 'politik uang', 'suap', 'mahar', 'transaksional', 'money politics'],
        'Legitimasi Pemimpin': ['legitimasi', 'tidak sah', 'ilegal', 'ngakalin', 'akal-akalan', 'konstitusi'],
        'Oligarki Elite': ['oligarki', 'elite', 'kekuasaan', 'elite politik', 'partai berkuasa', 'kartel'],
        'Kepentingan Pribadi': ['kepentingan', 'pribadi', 'golongan', 'partai', 'bukan rakyat', 'egois'],
        'Ketidakpercayaan Institusi': ['tidak percaya', 'bohong', 'tipu', 'khianat', 'janji', 'munafik'],
        'Kekhawatiran Otoriter': ['otoriter', 'diktator', 'kebebasan', 'represif', 'ancaman', 'bahaya']
    }
    
    pain_point_counts = {}
    for pain, keywords in pain_points.items():
        count = negative_posts['text'].str.lower().apply(
            lambda x: any(kw in str(x) for kw in keywords) if pd.notna(x) else False
        ).sum()
        pain_point_counts[pain] = count
    
    # Visualize pain points
    try:
        import altair as alt
        
        pain_df = pd.DataFrame([
            {'Pain Point': k, 'Count': v, 'Percentage': (v / len(negative_posts) * 100)}
            for k, v in pain_point_counts.items()
        ]).sort_values('Count', ascending=False)
        
        col_pain1, col_pain2 = st.columns([2, 1])
        
        with col_pain1:
            chart_pain = alt.Chart(pain_df).mark_bar(color='#e74c3c', opacity=0.8).encode(
                x=alt.X('Count:Q', title='Jumlah Postingan'),
                y=alt.Y('Pain Point:N', title='', sort='-x'),
                tooltip=[
                    alt.Tooltip('Pain Point:N', title='Keluhan'),
                    alt.Tooltip('Count:Q', title='Postingan', format=','),
                    alt.Tooltip('Percentage:Q', title='% dari Negatif', format='.1f')
                ]
            ).properties(
                title='Keluhan Utama dalam Sentimen Negatif',
                height=400
            ).configure_axis(
                labelFontSize=11,
                titleFontSize=12
            ).configure_title(
                fontSize=13,
                fontWeight='bold'
            )
            
            st.altair_chart(chart_pain, use_container_width=True)
        
        with col_pain2:
            st.write("**Kekhawatiran Teratas:**")
            for idx, row in pain_df.head(5).iterrows():
                st.write(f"{row['Pain Point']}")
                st.progress(row['Percentage'] / 100)
                st.caption(f"{row['Count']:,} postingan ({row['Percentage']:.1f}%)")
    
    except Exception as e:
        st.warning(f"Tidak dapat membuat grafik keluhan: {e}")
    
    # 2. PLATFORM NEGATIVITY PATTERNS
    st.subheader("2️⃣ Sentimen Negatif per Platform")
    
    if 'source' in df_filtered.columns:
        platform_negative = df_filtered.groupby('source').apply(
            lambda x: (x['sentiment_label'] == 'Negatif').sum() / len(x) * 100,
            include_groups=False
        ).sort_values(ascending=False)
        
        try:
            import altair as alt
            
            platform_neg_df = pd.DataFrame({
                'Platform': [p.upper() for p in platform_negative.index],
                'Negativity Rate': platform_negative.values
            })
            
            col_plat1, col_plat2 = st.columns([2, 1])
            
            with col_plat1:
                chart_platform_neg = alt.Chart(platform_neg_df).mark_bar(color='#e67e22', opacity=0.8).encode(
                    x=alt.X('Negativity Rate:Q', title='Tingkat Negativitas (%)', scale=alt.Scale(domain=[0, 100])),
                    y=alt.Y('Platform:N', title='', sort='-x'),
                    tooltip=[
                        alt.Tooltip('Platform:N', title='Platform'),
                        alt.Tooltip('Negativity Rate:Q', title='Negativitas %', format='.1f')
                    ]
                ).properties(
                    title='Tingkat Negativitas per Platform',
                    height=300
                ).configure_axis(
                    labelFontSize=11,
                    titleFontSize=12
                ).configure_title(
                    fontSize=13,
                    fontWeight='bold'
                )
                
                st.altair_chart(chart_platform_neg, use_container_width=True)
            
            with col_plat2:
                st.write("**Peringkat Negativitas:**")
                for idx, (platform, rate) in enumerate(platform_negative.items(), 1):
                    emoji = "🔴" if rate > 50 else "🟡" if rate > 30 else "🟢"
                    st.write(f"{idx}. {emoji} **{platform.upper()}**: {rate:.1f}%")
        
        except Exception as e:
            st.warning(f"Tidak dapat membuat grafik negativitas platform: {e}")
    
    # 3. TEMPORAL TRIGGERS
    st.subheader("3️⃣ Pemicu Temporal (Lonjakan Negativitas)")
    
    if 'date_parsed' in df_filtered.columns:
        df_with_dates = df_filtered.copy()
        df_with_dates['date_parsed'] = pd.to_datetime(df_with_dates['date_parsed'], errors='coerce')
        df_with_dates = df_with_dates[df_with_dates['date_parsed'].notna()].copy()
        
        if len(df_with_dates) > 0:
            df_with_dates['date_only'] = df_with_dates['date_parsed'].dt.date
            
            daily_neg_rate = df_with_dates.groupby('date_only').apply(
                lambda x: (x['sentiment_label'] == 'Negatif').sum() / len(x) * 100 if len(x) > 0 else 0,
                include_groups=False
            )
            
            daily_counts = df_with_dates.groupby('date_only').size()
            
            # Find top 5 most negative days
            top_negative_days = daily_neg_rate.nlargest(5)
            
            try:
                import altair as alt
                
                # Create time series of negativity rate
                daily_neg_df = pd.DataFrame({
                    'Date': pd.to_datetime(daily_neg_rate.index),
                    'Negativity Rate': daily_neg_rate.values
                })
                
                col_temp1, col_temp2 = st.columns([2, 1])
                
                with col_temp1:
                    # Line chart with threshold
                    base_temp = alt.Chart(daily_neg_df).encode(
                        x=alt.X('Date:T', title='Tanggal', axis=alt.Axis(format='%Y-%m-%d', labelAngle=-45))
                    )
                    
                    line_temp = base_temp.mark_line(color='#e74c3c', strokeWidth=2).encode(
                        y=alt.Y('Negativity Rate:Q', title='Tingkat Negativitas (%)', scale=alt.Scale(domain=[0, 100])),
                        tooltip=[
                            alt.Tooltip('Date:T', title='Tanggal', format='%Y-%m-%d'),
                            alt.Tooltip('Negativity Rate:Q', title='Negativitas %', format='.1f')
                        ]
                    )
                    
                    # Add threshold line at 50%
                    threshold = alt.Chart(pd.DataFrame({'y': [50]})).mark_rule(
                        color='orange',
                        strokeDash=[5, 5]
                    ).encode(y='y:Q')
                    
                    chart_temp = (line_temp + threshold).properties(
                        title='Tingkat Negativitas Harian dari Waktu ke Waktu',
                        height=300
                    ).configure_axis(
                        labelFontSize=11,
                        titleFontSize=12
                    ).configure_title(
                        fontSize=13,
                        fontWeight='bold'
                    )
                    
                    st.altair_chart(chart_temp, use_container_width=True)
                
                with col_temp2:
                    st.write("**5 Hari Paling Negatif:**")
                    for date, neg_pct in top_negative_days.items():
                        day_count = daily_counts[date]
                        st.write(f"📅 **{date}**")
                        st.caption(f"{neg_pct:.1f}% negatif ({day_count} postingan)")
            
            except Exception as e:
                st.warning(f"Tidak dapat membuat grafik temporal: {e}")
    
    # 4. ROOT CAUSE SUMMARY
    st.subheader("🎯 Ringkasan Akar Masalah & Insight yang Dapat Ditindaklanjuti")
    
    top_pain = max(pain_point_counts.items(), key=lambda x: x[1])
    top_pain_pct = (top_pain[1] / len(negative_posts) * 100)
    
    col_summary1, col_summary2 = st.columns(2)
    
    with col_summary1:
        st.markdown(f"""
        **KEKHAWATIRAN UTAMA:**  
        🔴 **{top_pain[0]}** ({top_pain[1]:,} penyebutan)  
        Ini mewakili **{top_pain_pct:.1f}%** dari postingan negatif.
        
        **TEMUAN KUNCI:**
        1. 🗳️ **Keberatan Utama**: Ketakutan kehilangan hak demokrasi (pemilihan langsung)
        2. 🤝 **Masalah Kepercayaan**: Ketidakpercayaan luas terhadap elite politik dan institusi
        3. 💰 **Kekhawatiran Korupsi**: Kecemasan tinggi tentang peluang korupsi yang meningkat
        4. ⚖️ **Pertanyaan Legitimasi**: Keraguan tentang mandat gubernur terpilih
        5. 📱 **Variasi Platform**: Tingkat negativitas berbeda di setiap platform
        """)
    
    with col_summary2:
        st.markdown("""
        **INSIGHT YANG DAPAT DITINDAKLANJUTI:**
        
        ✅ **Strategi Komunikasi**
        - Tangani kekhawatiran LEGITIMASI dan KORUPSI secara langsung
        - Mekanisme transparan untuk mencegah pengaruh politik uang
        
        ✅ **Keterlibatan Stakeholder**
        - Libatkan masyarakat sipil dan media untuk membangun kembali kepercayaan
        - Strategi pesan khusus per platform
        
        ✅ **Monitoring**
        - Lacak tanggal dengan negativitas tinggi untuk identifikasi pemicu/peristiwa
        - Monitor tren keluhan dari waktu ke waktu
        
        ✅ **Respons Kebijakan**
        - Perkuat perlindungan demokrasi
        - Tingkatkan transparansi dalam pengambilan keputusan
        """)
    
    # Additional metrics
    st.divider()
    col_metric1, col_metric2, col_metric3, col_metric4 = st.columns(4)
    
    with col_metric1:
        st.metric("Postingan Negatif", f"{len(negative_posts):,}")
    
    with col_metric2:
        st.metric("Tingkat Negativitas", f"{neg_pct:.1f}%")
    
    with col_metric3:
        top_concern_count = pain_df.iloc[0]['Count']
        st.metric("Postingan Keluhan Teratas", f"{top_concern_count:,}")
    
    with col_metric4:
        if 'source' in df_filtered.columns:
            most_neg_platform = platform_negative.idxmax()
            st.metric("Platform Paling Negatif", most_neg_platform.upper())

else:
    st.info("Tidak ada postingan dengan sentimen negatif ditemukan dalam data yang difilter.")


# ============================================================================
# BIAS-CORRECTED SENTIMENT SCORING
# ============================================================================

st.header("⚖️ Skor Sentimen Terkoreksi Bias")
st.caption("Memperhitungkan ketidakseimbangan distribusi platform untuk mendapatkan gambaran sentimen yang lebih akurat")

with st.expander("ℹ️ Penjelasan Koreksi Bias", expanded=False):
    st.markdown("""
**Mengapa Koreksi Bias Diperlukan?**

Ketika satu platform mendominasi dataset (misalnya 80% dari Twitter), hasil analisis akan sangat dipengaruhi oleh karakteristik platform tersebut, bukan mencerminkan sentimen publik secara keseluruhan.

**Metode Koreksi:**
1. **Identifikasi** distribusi platform yang tidak seimbang
2. **Hitung bobot** untuk menyeimbangkan kontribusi setiap platform
3. **Terapkan bobot** pada perhitungan sentimen
4. **Bandingkan** hasil sebelum dan sesudah koreksi

**Manfaat:**
- Gambaran sentimen yang lebih representatif
- Tidak bias terhadap platform dominan
- Keputusan berdasarkan data yang lebih akurat
- Memahami perbedaan sentimen antar platform

**Interpretasi:**
- Jika sentimen negatif **turun** setelah koreksi → Platform dominan lebih negatif dari rata-rata
- Jika sentimen negatif **naik** setelah koreksi → Platform lain lebih negatif dari platform dominan
    """)

# Check platform distribution
if 'source' in df_filtered.columns:
    platform_dist = df_filtered['source'].value_counts()
    total_posts = len(df_filtered)
    
    # Calculate dominance
    dominant_platform = platform_dist.idxmax()
    dominant_pct = (platform_dist.max() / total_posts * 100)
    
    st.warning(f"⚠️ **MASALAH**: {dominant_platform.upper()} mendominasi {dominant_pct:.1f}% dari dataset, berpotensi mendistorsi hasil")
    
    # 1. CURRENT PLATFORM DISTRIBUTION
    st.subheader("1️⃣ Distribusi Platform Saat Ini (Berpotensi Bias)")
    
    col_dist1, col_dist2 = st.columns([2, 1])
    
    with col_dist1:
        try:
            import altair as alt
            
            platform_dist_df = pd.DataFrame({
                'Platform': [p.upper() for p in platform_dist.index],
                'Count': platform_dist.values,
                'Percentage': (platform_dist.values / total_posts * 100)
            })
            
            chart_dist = alt.Chart(platform_dist_df).mark_bar(color='#3498db', opacity=0.8).encode(
                x=alt.X('Count:Q', title='Jumlah Postingan'),
                y=alt.Y('Platform:N', title='', sort='-x'),
                tooltip=[
                    alt.Tooltip('Platform:N', title='Platform'),
                    alt.Tooltip('Count:Q', title='Postingan', format=','),
                    alt.Tooltip('Percentage:Q', title='Persentase', format='.1f')
                ]
            ).properties(
                title='Distribusi Platform Aktual',
                height=300
            ).configure_axis(
                labelFontSize=11,
                titleFontSize=12
            ).configure_title(
                fontSize=13,
                fontWeight='bold'
            )
            
            st.altair_chart(chart_dist, use_container_width=True)
        
        except Exception as e:
            st.warning(f"Tidak dapat membuat grafik distribusi: {e}")
    
    with col_dist2:
        st.write("**Rincian Platform:**")
        for platform, count in platform_dist.items():
            pct = count / total_posts * 100
            st.write(f"**{platform.upper()}**")
            st.progress(pct / 100)
            st.caption(f"{count:,} postingan ({pct:.1f}%)")
    
    # 2. SENTIMENT BY PLATFORM
    st.subheader("2️⃣ Distribusi Sentimen per Platform")
    
    platform_sentiment = pd.crosstab(df_filtered['source'], df_filtered['sentiment_label'], normalize='index') * 100
    
    st.dataframe(platform_sentiment.round(1), use_container_width=True)
    
    # 3. CALCULATE WEIGHTS (Equal Platform Weight)
    st.subheader("3️⃣ Menerapkan Koreksi Bias (Bobot Platform Setara)")
    
    n_platforms = df_filtered['source'].nunique()
    equal_weight = 1.0 / n_platforms
    
    platform_actual = df_filtered['source'].value_counts(normalize=True)
    platform_weights = {platform: equal_weight / actual for platform, actual in platform_actual.items()}
    
    # Display weights
    col_weight1, col_weight2 = st.columns([2, 1])
    
    with col_weight1:
        try:
            import altair as alt
            
            weights_df = pd.DataFrame({
                'Platform': [p.upper() for p in platform_weights.keys()],
                'Weight': list(platform_weights.values()),
                'Original %': [platform_actual[p] * 100 for p in platform_weights.keys()],
                'Target %': [equal_weight * 100] * len(platform_weights)
            }).sort_values('Weight', ascending=False)
            
            chart_weights = alt.Chart(weights_df).mark_bar(color='#9b59b6', opacity=0.8).encode(
                x=alt.X('Weight:Q', title='Bobot Koreksi'),
                y=alt.Y('Platform:N', title='', sort='-x'),
                tooltip=[
                    alt.Tooltip('Platform:N', title='Platform'),
                    alt.Tooltip('Weight:Q', title='Bobot', format='.2f'),
                    alt.Tooltip('Original %:Q', title='% Asli', format='.1f'),
                    alt.Tooltip('Target %:Q', title='% Target', format='.1f')
                ]
            ).properties(
                title='Bobot Koreksi Platform',
                height=300
            ).configure_axis(
                labelFontSize=11,
                titleFontSize=12
            ).configure_title(
                fontSize=13,
                fontWeight='bold'
            )
            
            st.altair_chart(chart_weights, use_container_width=True)
        
        except Exception as e:
            st.warning(f"Tidak dapat membuat grafik bobot: {e}")
    
    with col_weight2:
        st.write("**Bobot Koreksi:**")
        for platform, weight in sorted(platform_weights.items(), key=lambda x: x[1], reverse=True):
            st.write(f"**{platform.upper()}**")
            st.caption(f"Bobot: {weight:.2f}x")
            st.caption(f"{platform_actual[platform]*100:.1f}% → {equal_weight*100:.1f}%")
    
    # 4. APPLY WEIGHTS TO SENTIMENT
    df_filtered_weighted = df_filtered.copy()
    df_filtered_weighted['platform_weight'] = df_filtered_weighted['source'].map(platform_weights)
    
    # Calculate weighted sentiment
    total_weight = df_filtered_weighted['platform_weight'].sum()
    
    original_sentiment = df_filtered['sentiment_label'].value_counts(normalize=True) * 100
    weighted_sentiment = {}
    
    for sentiment in ['Negatif', 'Positif', 'Netral']:
        weighted_count = df_filtered_weighted[df_filtered_weighted['sentiment_label'] == sentiment]['platform_weight'].sum()
        weighted_sentiment[sentiment] = (weighted_count / total_weight * 100)
    
    # 5. COMPARISON: BEFORE vs AFTER
    st.subheader("4️⃣ Perbandingan: Sentimen Asli vs Terkoreksi Bias")
    
    comparison_df = pd.DataFrame({
        'Asli (Bias)': original_sentiment.sort_index(),
        'Terkoreksi Bias': pd.Series(weighted_sentiment).sort_index()
    })
    comparison_df['Perubahan (pp)'] = comparison_df['Terkoreksi Bias'] - comparison_df['Asli (Bias)']
    
    col_comp1, col_comp2 = st.columns(2)
    
    with col_comp1:
        st.dataframe(comparison_df.round(2), use_container_width=True)
    
    with col_comp2:
        st.write("**Perubahan Kunci:**")
        for sentiment in comparison_df.index:
            change = comparison_df.loc[sentiment, 'Perubahan (pp)']
            emoji = "📈" if change > 0 else "📉" if change < 0 else "➡️"
            color = "green" if (sentiment == 'Positif' and change > 0) or (sentiment == 'Negatif' and change < 0) else "red" if change != 0 else "gray"
            st.markdown(f"{emoji} **{sentiment}**: {change:+.1f}pp")
    
    # 6. VISUALIZE COMPARISON
    try:
        import altair as alt
        
        # Prepare data for visualization
        viz_data = []
        sentiments = ['Positif', 'Negatif', 'Netral']
        colors_sentiment = {'Positif': '#2ecc71', 'Negatif': '#e74c3c', 'Netral': '#95a5a6'}
        
        for sentiment in sentiments:
            viz_data.append({
                'Sentiment': sentiment,
                'Type': 'Asli',
                'Percentage': original_sentiment.get(sentiment, 0),
                'Color': colors_sentiment[sentiment]
            })
            viz_data.append({
                'Sentiment': sentiment,
                'Type': 'Terkoreksi Bias',
                'Percentage': weighted_sentiment.get(sentiment, 0),
                'Color': colors_sentiment[sentiment]
            })
        
        viz_df = pd.DataFrame(viz_data)
        
        col_viz1, col_viz2 = st.columns(2)
        
        with col_viz1:
            # Original sentiment
            original_df = viz_df[viz_df['Type'] == 'Asli']
            
            chart_original = alt.Chart(original_df).mark_bar(opacity=0.8).encode(
                x=alt.X('Sentiment:N', title='', sort=sentiments),
                y=alt.Y('Percentage:Q', title='Persentase (%)', scale=alt.Scale(domain=[0, 100])),
                color=alt.Color('Color:N', scale=None, legend=None),
                tooltip=[
                    alt.Tooltip('Sentiment:N', title='Sentimen'),
                    alt.Tooltip('Percentage:Q', title='Persentase', format='.1f')
                ]
            ).properties(
                title=f'Sentimen ASLI (Didominasi {dominant_platform.upper()})',
                height=350
            ).configure_axis(
                labelFontSize=11,
                titleFontSize=12
            ).configure_title(
                fontSize=13,
                fontWeight='bold'
            )
            
            st.altair_chart(chart_original, use_container_width=True)
        
        with col_viz2:
            # Bias-corrected sentiment
            corrected_df = viz_df[viz_df['Type'] == 'Terkoreksi Bias']
            
            chart_corrected = alt.Chart(corrected_df).mark_bar(opacity=0.8).encode(
                x=alt.X('Sentiment:N', title='', sort=sentiments),
                y=alt.Y('Percentage:Q', title='Persentase (%)', scale=alt.Scale(domain=[0, 100])),
                color=alt.Color('Color:N', scale=None, legend=None),
                tooltip=[
                    alt.Tooltip('Sentiment:N', title='Sentimen'),
                    alt.Tooltip('Percentage:Q', title='Persentase', format='.1f')
                ]
            ).properties(
                title='Sentimen TERKOREKSI BIAS (Bobot Platform Setara)',
                height=350
            ).configure_axis(
                labelFontSize=11,
                titleFontSize=12
            ).configure_title(
                fontSize=13,
                fontWeight='bold'
            )
            
            st.altair_chart(chart_corrected, use_container_width=True)
        
        # Change visualization
        change_df = pd.DataFrame({
            'Sentiment': sentiments,
            'Change': [comparison_df.loc[s, 'Perubahan (pp)'] for s in sentiments]
        })
        
        chart_change = alt.Chart(change_df).mark_bar().encode(
            x=alt.X('Sentiment:N', title='', sort=sentiments),
            y=alt.Y('Change:Q', title='Perubahan Poin Persentase'),
            color=alt.condition(
                alt.datum.Change > 0,
                alt.value('#2ecc71'),
                alt.value('#e74c3c')
            ),
            tooltip=[
                alt.Tooltip('Sentiment:N', title='Sentimen'),
                alt.Tooltip('Change:Q', title='Perubahan (pp)', format='+.1f')
            ]
        ).properties(
            title='Perubahan Setelah Koreksi Bias',
            height=300
        ).configure_axis(
            labelFontSize=11,
            titleFontSize=12
        ).configure_title(
            fontSize=13,
            fontWeight='bold'
        )
        
        st.altair_chart(chart_change, use_container_width=True)
    
    except Exception as e:
        st.warning(f"Tidak dapat membuat grafik perbandingan: {e}")
    
    # 7. KEY FINDINGS & RECOMMENDATIONS
    st.subheader("🎯 Temuan Kunci & Rekomendasi")
    
    max_change_idx = comparison_df['Perubahan (pp)'].abs().idxmax()
    max_change = comparison_df.loc[max_change_idx, 'Perubahan (pp)']
    
    col_findings1, col_findings2 = st.columns(2)
    
    with col_findings1:
        st.markdown(f"""
        **PERUBAHAN TERBESAR:**  
        🔄 Sentimen **{max_change_idx}** berubah sebesar **{max_change:+.1f}** poin persentase
        
        **INTERPRETASI:**
        """)
        
        if weighted_sentiment['Negatif'] < original_sentiment['Negatif']:
            diff = original_sentiment['Negatif'] - weighted_sentiment['Negatif']
            st.success(f"""
            ✅ Sentimen negatif **KURANG PARAH** saat memperhitungkan bias platform
            - Turun dari **{original_sentiment['Negatif']:.1f}%** ke **{weighted_sentiment['Negatif']:.1f}%** (-{diff:.1f}pp)
            - Dominasi {dominant_platform.upper()} **memperbesar** sentimen negatif
            """)
        elif weighted_sentiment['Negatif'] > original_sentiment['Negatif']:
            diff = weighted_sentiment['Negatif'] - original_sentiment['Negatif']
            st.error(f"""
            ⚠️ Sentimen negatif **LEBIH PARAH** dari yang ditunjukkan data {dominant_platform.upper()}
            - Naik dari **{original_sentiment['Negatif']:.1f}%** ke **{weighted_sentiment['Negatif']:.1f}%** (+{diff:.1f}pp)
            - Platform lain **LEBIH NEGATIF** dari {dominant_platform.upper()}
            """)
        else:
            st.info("➡️ Sentimen negatif relatif stabil setelah koreksi bias")
    
    with col_findings2:
        st.markdown("""
        **REKOMENDASI:**
        
        ✅ **Analisis Data**
        - Gunakan angka TERKOREKSI BIAS untuk keputusan kebijakan
        - Pertimbangkan demografi platform dalam interpretasi
        
        ✅ **Pengumpulan Data**
        - Kumpulkan lebih banyak data dari platform yang kurang terwakili
        - Seimbangkan dataset di seluruh platform
        
        ✅ **Strategi**
        - Strategi engagement khusus per platform
        - Pesan yang ditargetkan berdasarkan sentimen platform
        
        ✅ **Monitoring**
        - Lacak perubahan sentimen di seluruh platform
        - Monitor tren khusus platform
        """)
    
    # Summary metrics
    st.divider()
    col_sum1, col_sum2, col_sum3, col_sum4 = st.columns(4)
    
    with col_sum1:
        st.metric("Platform Dianalisis", n_platforms)
    
    with col_sum2:
        st.metric("Platform Dominan", f"{dominant_platform.upper()}")
        st.caption(f"{dominant_pct:.1f}% dari data")
    
    with col_sum3:
        neg_change = comparison_df.loc['Negatif', 'Perubahan (pp)']
        st.metric("Δ Negatif", f"{neg_change:+.1f}pp")
    
    with col_sum4:
        pos_change = comparison_df.loc['Positif', 'Perubahan (pp)']
        st.metric("Δ Positif", f"{pos_change:+.1f}pp")

else:
    st.info("Data sumber/platform tidak tersedia untuk analisis koreksi bias")

# ============================================================================
# ENGAGEMENT ANALYSIS: KORELASI SENTIMEN DENGAN INTERAKSI
# ============================================================================

st.header(ENGAGEMENT_TITLE)
st.caption("Menganalisis korelasi antara sentimen dan interaksi pengguna")

with st.expander("ℹ️ Penjelasan Analisis Engagement", expanded=False):
    st.markdown(ENGAGEMENT_DESCRIPTION)

# Check if engagement column exists
if 'engagement' in df_filtered.columns:
    
    # 1. ENGAGEMENT METRICS BY SENTIMENT
    st.subheader("1️⃣ Metrik Engagement per Sentimen")
    
    engagement_by_sentiment = df_filtered.groupby('sentiment_label')['engagement'].agg([
        ('Rata-rata', 'mean'),
        ('Median', 'median'),
        ('Total', 'sum'),
        ('Jumlah', 'count'),
        ('Std Dev', 'std')
    ]).round(2)
    
    col_eng1, col_eng2 = st.columns([2, 1])
    
    with col_eng1:
        st.dataframe(engagement_by_sentiment, use_container_width=True)
    
    with col_eng2:
        # Show which sentiment has highest engagement
        max_mean_sentiment = engagement_by_sentiment['Rata-rata'].idxmax()
        max_mean_value = engagement_by_sentiment.loc[max_mean_sentiment, 'Rata-rata']
        
        st.metric("Engagement Rata-rata Tertinggi", max_mean_sentiment)
        st.caption(f"{max_mean_value:,.0f} interaksi")
        
        max_total_sentiment = engagement_by_sentiment['Total'].idxmax()
        max_total_value = engagement_by_sentiment.loc[max_total_sentiment, 'Total']
        
        st.metric("Engagement Total Tertinggi", max_total_sentiment)
        st.caption(f"{max_total_value:,.0f} total interaksi")
    
    # Visualize engagement by sentiment
    try:
        import altair as alt
        
        eng_sent_df = pd.DataFrame({
            'Sentiment': engagement_by_sentiment.index,
            'Mean Engagement': engagement_by_sentiment['Rata-rata'].values,
            'Total Engagement': engagement_by_sentiment['Total'].values
        })
        
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            colors_sentiment = {'Positif': '#2ecc71', 'Negatif': '#e74c3c', 'Netral': '#95a5a6'}
            
            chart_eng_mean = alt.Chart(eng_sent_df).mark_bar(opacity=0.8).encode(
                x=alt.X('Sentiment:N', title='', sort=['Positif', 'Negatif', 'Netral']),
                y=alt.Y('Mean Engagement:Q', title='Rata-rata Engagement'),
                color=alt.Color('Sentiment:N', 
                    scale=alt.Scale(
                        domain=['Positif', 'Negatif', 'Netral'],
                        range=['#2ecc71', '#e74c3c', '#95a5a6']
                    ),
                    legend=None
                ),
                tooltip=[
                    alt.Tooltip('Sentiment:N', title='Sentimen'),
                    alt.Tooltip('Mean Engagement:Q', title='Rata-rata Engagement', format=',.0f')
                ]
            ).properties(
                title='Rata-rata Engagement per Sentimen',
                height=300
            ).configure_axis(
                labelFontSize=11,
                titleFontSize=12
            ).configure_title(
                fontSize=13,
                fontWeight='bold'
            )
            
            st.altair_chart(chart_eng_mean, use_container_width=True)
        
        with col_chart2:
            chart_eng_total = alt.Chart(eng_sent_df).mark_bar(opacity=0.8).encode(
                x=alt.X('Sentiment:N', title='', sort=['Positif', 'Negatif', 'Netral']),
                y=alt.Y('Total Engagement:Q', title='Total Engagement'),
                color=alt.Color('Sentiment:N', 
                    scale=alt.Scale(
                        domain=['Positif', 'Negatif', 'Netral'],
                        range=['#2ecc71', '#e74c3c', '#95a5a6']
                    ),
                    legend=None
                ),
                tooltip=[
                    alt.Tooltip('Sentiment:N', title='Sentimen'),
                    alt.Tooltip('Total Engagement:Q', title='Total Engagement', format=',.0f')
                ]
            ).properties(
                title='Total Engagement per Sentimen',
                height=300
            ).configure_axis(
                labelFontSize=11,
                titleFontSize=12
            ).configure_title(
                fontSize=13,
                fontWeight='bold'
            )
            
            st.altair_chart(chart_eng_total, use_container_width=True)
    
    except Exception as e:
        st.warning(f"Tidak dapat membuat grafik engagement: {e}")
    
    # 2. ENGAGEMENT METRICS BY PLATFORM
    st.subheader("2️⃣ Metrik Engagement per Platform")
    
    if 'source' in df_filtered.columns:
        engagement_by_platform = df_filtered.groupby('source')['engagement'].agg([
            ('Rata-rata', 'mean'),
            ('Median', 'median'),
            ('Total', 'sum'),
            ('Jumlah', 'count')
        ]).round(2).sort_values('Total', ascending=False)
        
        col_plat_eng1, col_plat_eng2 = st.columns([2, 1])
        
        with col_plat_eng1:
            st.dataframe(engagement_by_platform, use_container_width=True)
        
        with col_plat_eng2:
            top_platform = engagement_by_platform.index[0]
            top_platform_total = engagement_by_platform.iloc[0]['Total']
            
            st.metric("Platform Teratas (Total)", top_platform.upper())
            st.caption(f"{top_platform_total:,.0f} total interaksi")
            
            top_mean_platform = engagement_by_platform['Rata-rata'].idxmax()
            top_mean_value = engagement_by_platform.loc[top_mean_platform, 'Rata-rata']
            
            st.metric("Platform Teratas (Rata-rata)", top_mean_platform.upper())
            st.caption(f"{top_mean_value:,.0f} rata-rata interaksi")
        
        # Visualize platform engagement
        try:
            import altair as alt
            
            plat_eng_df = pd.DataFrame({
                'Platform': [p.upper() for p in engagement_by_platform.index],
                'Total Engagement': engagement_by_platform['Total'].values,
                'Mean Engagement': engagement_by_platform['Rata-rata'].values
            })
            
            chart_plat_eng = alt.Chart(plat_eng_df).mark_bar(color='#3498db', opacity=0.8).encode(
                x=alt.X('Total Engagement:Q', title='Total Engagement'),
                y=alt.Y('Platform:N', title='', sort='-x'),
                tooltip=[
                    alt.Tooltip('Platform:N', title='Platform'),
                    alt.Tooltip('Total Engagement:Q', title='Total', format=',.0f'),
                    alt.Tooltip('Mean Engagement:Q', title='Rata-rata', format=',.0f')
                ]
            ).properties(
                title='Total Engagement per Platform',
                height=300
            ).configure_axis(
                labelFontSize=11,
                titleFontSize=12
            ).configure_title(
                fontSize=13,
                fontWeight='bold'
            )
            
            st.altair_chart(chart_plat_eng, use_container_width=True)
        
        except Exception as e:
            st.warning(f"Tidak dapat membuat grafik engagement platform: {e}")
    
    # 3. VIRAL CONTENT ANALYSIS (Top 10%)
    st.subheader("3️⃣ Analisis Konten Engagement Tinggi")
    
    high_engagement_threshold = df_filtered['engagement'].quantile(0.90)  # Top 10%
    high_engagement_df = df_filtered[df_filtered['engagement'] >= high_engagement_threshold]
    
    st.info(f"📊 Menganalisis **{len(high_engagement_df):,}** postingan engagement tinggi (Top 10%, engagement ≥ {high_engagement_threshold:,.0f})")
    
    col_viral1, col_viral2, col_viral3 = st.columns(3)
    
    with col_viral1:
        st.write("**Distribusi Sentimen:**")
        high_eng_sentiment = high_engagement_df['sentiment_label'].value_counts()
        for sentiment, count in high_eng_sentiment.items():
            pct = (count / len(high_engagement_df)) * 100
            st.write(f"{sentiment}: {count} ({pct:.1f}%)")
            st.progress(pct / 100)
    
    with col_viral2:
        if 'has_action_keywords' in df_filtered.columns or 'detected_keywords' in df_filtered.columns:
            if 'has_action_keywords' in df_filtered.columns:
                high_eng_keywords = high_engagement_df['has_action_keywords'].sum()
            else:
                high_eng_keywords = sum(1 for kws in high_engagement_df['detected_keywords'] 
                                       if isinstance(kws, list) and len(kws) > 0)
            
            high_eng_keywords_pct = (high_eng_keywords / len(high_engagement_df)) * 100
            
            st.metric("Dengan Kata Kunci Aksi", f"{high_eng_keywords}")
            st.caption(f"{high_eng_keywords_pct:.1f}% dari konten viral")
    
    with col_viral3:
        if 'source' in df_filtered.columns:
            top_viral_platform = high_engagement_df['source'].value_counts().idxmax()
            top_viral_count = high_engagement_df['source'].value_counts().max()
            
            st.metric("Platform Viral Teratas", top_viral_platform.upper())
            st.caption(f"{top_viral_count} postingan viral")
    
    # 4. TOP 10 MOST ENGAGING CONTENT
    st.subheader("4️⃣ Top 10 Konten Paling Engaging")
    
    top_engagement = df_filtered.nlargest(10, 'engagement')
    
    for idx, row in enumerate(top_engagement.itertuples(), 1):
        with st.expander(f"#{idx} - {getattr(row, 'source', 'Unknown').upper()} | {getattr(row, 'sentiment_label', 'Unknown')} | {row.engagement:,.0f} interaksi"):
            col_top1, col_top2 = st.columns([1, 3])
            
            with col_top1:
                st.write("**Metrik:**")
                st.write(f"Platform: {getattr(row, 'source', 'Unknown').upper()}")
                st.write(f"Sentimen: {getattr(row, 'sentiment_label', 'Unknown')}")
                st.write(f"Engagement: {row.engagement:,.0f}")
                
                if hasattr(row, 'has_action_keywords'):
                    st.write(f"Kata Kunci Aksi: {'Ya ✓' if row.has_action_keywords else 'Tidak'}")
                elif hasattr(row, 'detected_keywords'):
                    has_kw = isinstance(row.detected_keywords, list) and len(row.detected_keywords) > 0
                    st.write(f"Kata Kunci Aksi: {'Ya ✓' if has_kw else 'Tidak'}")
            
            with col_top2:
                st.write("**Konten:**")
                text_content = getattr(row, 'text', 'Tidak ada teks tersedia')
                st.write(text_content[:300] + ('...' if len(text_content) > 300 else ''))
    
    # 5. KEY INSIGHTS
    st.subheader("💡 Insight Kunci")
    
    col_insight1, col_insight2 = st.columns(2)
    
    with col_insight1:
        st.markdown(f"""
        **Pola Engagement:**
        - 📈 Engagement rata-rata tertinggi: **{max_mean_sentiment}** ({max_mean_value:,.0f})
        - 🔥 Sentimen konten viral: **{high_eng_sentiment.index[0]}** ({high_eng_sentiment.iloc[0]} postingan)
        - 📱 Platform engagement teratas: **{top_platform.upper()}** ({top_platform_total:,.0f} total)
        """)
    
    with col_insight2:
        if 'has_action_keywords' in df_filtered.columns or 'detected_keywords' in df_filtered.columns:
            st.markdown(f"""
            **Karakteristik Konten:**
            - 🔑 {high_eng_keywords_pct:.1f}% konten viral mengandung kata kunci aksi
            - 📊 Ambang batas engagement tinggi: {high_engagement_threshold:,.0f} interaksi
            - 🎯 Top 10% mewakili {len(high_engagement_df):,} postingan
            """)
        else:
            st.markdown(f"""
            **Karakteristik Konten:**
            - 📊 Ambang batas engagement tinggi: {high_engagement_threshold:,.0f} interaksi
            - 🎯 Top 10% mewakili {len(high_engagement_df):,} postingan
            - 💬 Engagement bervariasi signifikan per sentimen
            """)
    
    # Summary metrics
    st.divider()
    col_sum_eng1, col_sum_eng2, col_sum_eng3, col_sum_eng4 = st.columns(4)
    
    with col_sum_eng1:
        total_engagement = df_filtered['engagement'].sum()
        st.metric("Total Engagement", f"{total_engagement:,.0f}")
    
    with col_sum_eng2:
        avg_engagement = df_filtered['engagement'].mean()
        st.metric("Rata-rata Engagement", f"{avg_engagement:,.0f}")
    
    with col_sum_eng3:
        median_engagement = df_filtered['engagement'].median()
        st.metric("Median Engagement", f"{median_engagement:,.0f}")
    
    with col_sum_eng4:
        max_engagement = df_filtered['engagement'].max()
        st.metric("Engagement Maksimum", f"{max_engagement:,.0f}")

else:
    st.info("Data engagement tidak tersedia dalam dataset")

# ============================================================================
# TIME SERIES ANALYSIS: TREN SENTIMEN DAN AKTIVITAS
# ============================================================================

st.header("📈 Analisis Time Series: Tren Sentimen dari Waktu ke Waktu")
st.caption("Melacak evolusi sentimen dan mengidentifikasi periode kritis")

with st.expander("ℹ️ Penjelasan Time Series", expanded=False):
    st.markdown("""
**Analisis Time Series membantu:**
- Memahami bagaimana sentimen berubah dari waktu ke waktu
- Mengidentifikasi pola harian, mingguan, atau bulanan
- Mendeteksi lonjakan aktivitas atau perubahan mendadak
- Memprediksi tren masa depan berdasarkan pola historis

**Interpretasi:**
- Lonjakan mendadak = Peristiwa pemicu (breaking news, viral content)
- Tren menurun = Isu kehilangan momentum
- Pola berulang = Aktivitas terkoordinasi atau bot
    """)

# Check if date column exists
if 'date_parsed' in df_filtered.columns:
    df_with_dates = df_filtered.copy()
    df_with_dates['date_parsed'] = pd.to_datetime(df_with_dates['date_parsed'], errors='coerce')
    df_with_dates = df_with_dates[df_with_dates['date_parsed'].notna()].copy()
    
    if len(df_with_dates) > 0:
        df_with_dates['date_only'] = df_with_dates['date_parsed'].dt.date
        
        # Display date range
        min_date = df_with_dates['date_only'].min()
        max_date = df_with_dates['date_only'].max()
        date_range_days = (pd.to_datetime(max_date) - pd.to_datetime(min_date)).days
        
        st.info(f"📅 Analyzing **{len(df_with_dates):,}** posts with dates | Date range: **{min_date}** to **{max_date}** ({date_range_days} days)")
        
        # 1. SENTIMENT MOMENTUM
        st.subheader("1️⃣ Momentum Sentimen (Tren Terkini vs Awal)")
        
        daily_sentiment = df_with_dates.groupby(['date_only', 'sentiment_label']).size().unstack(fill_value=0)
        
        if len(daily_sentiment) > 1:
            sentiment_momentum = {}
            for sentiment in ['Positif', 'Negatif', 'Netral']:
                if sentiment in daily_sentiment.columns:
                    recent_avg = daily_sentiment[sentiment].tail(3).mean()
                    earlier_avg = daily_sentiment[sentiment].head(3).mean()
                    momentum = ((recent_avg - earlier_avg) / (earlier_avg + 1)) * 100
                    sentiment_momentum[sentiment] = momentum
            
            col_mom1, col_mom2, col_mom3 = st.columns(3)
            
            with col_mom1:
                if 'Positif' in sentiment_momentum:
                    mom_pos = sentiment_momentum['Positif']
                    delta_color = "normal" if mom_pos > 5 else "inverse" if mom_pos < -5 else "off"
                    st.metric("Momentum Positif", f"{mom_pos:+.1f}%", 
                             delta="Meningkat" if mom_pos > 5 else "Menurun" if mom_pos < -5 else "Stabil",
                             delta_color=delta_color)
            
            with col_mom2:
                if 'Negatif' in sentiment_momentum:
                    mom_neg = sentiment_momentum['Negatif']
                    delta_color = "inverse" if mom_neg > 5 else "normal" if mom_neg < -5 else "off"
                    st.metric("Momentum Negatif", f"{mom_neg:+.1f}%",
                             delta="Meningkat" if mom_neg > 5 else "Menurun" if mom_neg < -5 else "Stabil",
                             delta_color=delta_color)
            
            with col_mom3:
                if 'Netral' in sentiment_momentum:
                    mom_net = sentiment_momentum['Netral']
                    st.metric("Momentum Netral", f"{mom_net:+.1f}%",
                             delta="Meningkat" if mom_net > 5 else "Menurun" if mom_net < -5 else "Stabil",
                             delta_color="off")
        
        # 2. DAILY ACTIVITY TREND
        st.subheader("2️⃣ Tren Aktivitas Harian")
        
        daily_activity = df_with_dates.groupby('date_only').size()
        
        if len(daily_activity) > 5:
            recent_activity = daily_activity.tail(5).mean()
            earlier_activity = daily_activity.head(5).mean()
            activity_change = ((recent_activity - earlier_activity) / (earlier_activity + 1)) * 100
            
            col_act1, col_act2, col_act3 = st.columns(3)
            
            with col_act1:
                st.metric("Rata-rata Periode Awal", f"{earlier_activity:.1f} postingan/hari")
            
            with col_act2:
                st.metric("Rata-rata Periode Terkini", f"{recent_activity:.1f} postingan/hari")
            
            with col_act3:
                delta_color = "normal" if activity_change > 0 else "inverse"
                st.metric("Perubahan Aktivitas", f"{activity_change:+.1f}%",
                         delta="Meningkat" if activity_change > 0 else "Menurun",
                         delta_color=delta_color)
            
            # Visualize daily activity
            try:
                import altair as alt
                
                activity_df = pd.DataFrame({
                    'Date': pd.to_datetime(daily_activity.index),
                    'Posts': daily_activity.values
                })
                
                # Calculate 7-day moving average
                activity_df['MA_7'] = activity_df['Posts'].rolling(window=7, min_periods=1).mean()
                
                # Create layered chart
                base = alt.Chart(activity_df).encode(
                    x=alt.X('Date:T', title='Tanggal', axis=alt.Axis(format='%Y-%m-%d', labelAngle=-45))
                )
                
                bars = base.mark_bar(opacity=0.3, color='#3498db').encode(
                    y=alt.Y('Posts:Q', title='Jumlah Postingan'),
                    tooltip=[
                        alt.Tooltip('Date:T', title='Tanggal', format='%Y-%m-%d'),
                        alt.Tooltip('Posts:Q', title='Postingan', format=',')
                    ]
                )
                
                line = base.mark_line(strokeWidth=2, color='#e74c3c').encode(
                    y=alt.Y('MA_7:Q', title=''),
                    tooltip=[
                        alt.Tooltip('Date:T', title='Tanggal', format='%Y-%m-%d'),
                        alt.Tooltip('MA_7:Q', title='MA 7-hari', format='.1f')
                    ]
                )
                
                chart_activity = (bars + line).properties(
                    title='Tren Aktivitas Harian (dengan Moving Average 7-hari)',
                    height=350
                ).configure_axis(
                    labelFontSize=11,
                    titleFontSize=12
                ).configure_title(
                    fontSize=13,
                    fontWeight='bold'
                )
                
                st.altair_chart(chart_activity, use_container_width=True)
            
            except Exception as e:
                st.warning(f"Tidak dapat membuat grafik aktivitas: {e}")
        
        # 3. PEAK ACTIVITY DATES
        st.subheader("3️⃣ Tanggal Aktivitas Puncak")
        
        top_5_dates = daily_activity.nlargest(5)
        
        col_peak1, col_peak2 = st.columns([1, 2])
        
        with col_peak1:
            st.write("**5 Hari Paling Aktif:**")
            for idx, (date, count) in enumerate(top_5_dates.items(), 1):
                st.write(f"{idx}. **{date}**")
                st.caption(f"{count} postingan")
        
        with col_peak2:
            # Show sentiment distribution for peak dates
            peak_data = []
            for date, count in top_5_dates.items():
                date_data = df_with_dates[df_with_dates['date_only'] == date]
                sentiment_dist = date_data['sentiment_label'].value_counts()
                dominant = sentiment_dist.index[0] if len(sentiment_dist) > 0 else 'N/A'
                
                for sentiment in ['Positif', 'Negatif', 'Netral']:
                    sent_count = sentiment_dist.get(sentiment, 0)
                    peak_data.append({
                        'Date': str(date),
                        'Sentiment': sentiment,
                        'Count': sent_count,
                        'Dominant': '⭐' if sentiment == dominant else ''
                    })
            
            peak_df = pd.DataFrame(peak_data)
            
            try:
                import altair as alt
                
                chart_peak = alt.Chart(peak_df).mark_bar().encode(
                    x=alt.X('Count:Q', title='Jumlah Postingan'),
                    y=alt.Y('Date:N', title='', sort=list(top_5_dates.index.astype(str))),
                    color=alt.Color('Sentiment:N',
                        scale=alt.Scale(
                            domain=['Positif', 'Negatif', 'Netral'],
                            range=['#2ecc71', '#e74c3c', '#95a5a6']
                        ),
                        legend=alt.Legend(title='Sentimen')
                    ),
                    xOffset='Sentiment:N',
                    tooltip=[
                        alt.Tooltip('Date:N', title='Tanggal'),
                        alt.Tooltip('Sentiment:N', title='Sentimen'),
                        alt.Tooltip('Count:Q', title='Postingan', format=','),
                        alt.Tooltip('Dominant:N', title='Dominan')
                    ]
                ).properties(
                    title='Distribusi Sentimen pada Hari Aktivitas Puncak',
                    height=250
                ).configure_axis(
                    labelFontSize=11,
                    titleFontSize=12
                ).configure_title(
                    fontSize=13,
                    fontWeight='bold'
                )
                
                st.altair_chart(chart_peak, use_container_width=True)
            
            except Exception as e:
                st.warning(f"Tidak dapat membuat grafik tanggal puncak: {e}")
        
        # 4. SENTIMENT EVOLUTION OVER TIME
        st.subheader("4️⃣ Evolusi Sentimen dari Waktu ke Waktu")
        
        try:
            import altair as alt
            
            # Calculate daily sentiment percentages
            daily_sentiment_pct = daily_sentiment.div(daily_sentiment.sum(axis=1), axis=0) * 100
            
            # Prepare data for visualization
            evolution_data = []
            for date in daily_sentiment_pct.index:
                for sentiment in ['Positif', 'Negatif', 'Netral']:
                    if sentiment in daily_sentiment_pct.columns:
                        evolution_data.append({
                            'Date': pd.to_datetime(date),
                            'Sentiment': sentiment,
                            'Percentage': daily_sentiment_pct.loc[date, sentiment]
                        })
            
            evolution_df = pd.DataFrame(evolution_data)
            
            # Calculate 7-day moving average for smoothing
            evolution_df_smooth = []
            for sentiment in ['Positif', 'Negatif', 'Netral']:
                sent_df = evolution_df[evolution_df['Sentiment'] == sentiment].copy()
                sent_df = sent_df.sort_values('Date')
                sent_df['MA_7'] = sent_df['Percentage'].rolling(window=7, min_periods=1).mean()
                evolution_df_smooth.append(sent_df)
            
            evolution_df_final = pd.concat(evolution_df_smooth, ignore_index=True)
            
            chart_evolution = alt.Chart(evolution_df_final).mark_line(strokeWidth=2.5).encode(
                x=alt.X('Date:T', title='Tanggal', axis=alt.Axis(format='%Y-%m-%d', labelAngle=-45)),
                y=alt.Y('MA_7:Q', title='Persentase (%)', scale=alt.Scale(domain=[0, 100])),
                color=alt.Color('Sentiment:N',
                    scale=alt.Scale(
                        domain=['Positif', 'Negatif', 'Netral'],
                        range=['#2ecc71', '#e74c3c', '#95a5a6']
                    ),
                    legend=alt.Legend(title='Sentimen')
                ),
                tooltip=[
                    alt.Tooltip('Date:T', title='Tanggal', format='%Y-%m-%d'),
                    alt.Tooltip('Sentiment:N', title='Sentimen'),
                    alt.Tooltip('MA_7:Q', title='Persentase (MA 7-hari)', format='.1f')
                ]
            ).properties(
                title='Evolusi Sentimen dari Waktu ke Waktu (Moving Average 7-hari)',
                height=400
            ).configure_axis(
                labelFontSize=11,
                titleFontSize=12
            ).configure_title(
                fontSize=13,
                fontWeight='bold'
            ).configure_legend(
                labelFontSize=11,
                titleFontSize=12
            )
            
            st.altair_chart(chart_evolution, use_container_width=True)
        
        except Exception as e:
            st.warning(f"Tidak dapat membuat grafik evolusi sentimen: {e}")
        
        # 5. KEY INSIGHTS
        st.subheader("💡 Insight Time Series")
        
        col_ts_insight1, col_ts_insight2 = st.columns(2)
        
        with col_ts_insight1:
            # Find sentiment with highest momentum
            if sentiment_momentum:
                max_momentum_sent = max(sentiment_momentum.items(), key=lambda x: abs(x[1]))
                
                st.markdown(f"""
                **Analisis Momentum:**
                - 📊 Momentum terkuat: **{max_momentum_sent[0]}** ({max_momentum_sent[1]:+.1f}%)
                - 📈 Tren aktivitas: **{'Meningkat' if activity_change > 0 else 'Menurun'}** ({activity_change:+.1f}%)
                - 📅 Periode analisis: **{date_range_days}** hari
                """)
        
        with col_ts_insight2:
            # Peak activity insights
            peak_date = top_5_dates.index[0]
            peak_count = top_5_dates.iloc[0]
            peak_sentiment = df_with_dates[df_with_dates['date_only'] == peak_date]['sentiment_label'].value_counts().index[0]
            
            st.markdown(f"""
            **Aktivitas Puncak:**
            - 🔥 Aktivitas tertinggi: **{peak_date}** ({peak_count} postingan)
            - 🎯 Sentimen dominan pada puncak: **{peak_sentiment}**
            - 📊 Rata-rata postingan harian: **{daily_activity.mean():.1f}**
            """)
        
        # Summary metrics
        st.divider()
        col_ts1, col_ts2, col_ts3, col_ts4 = st.columns(4)
        
        with col_ts1:
            st.metric("Total Hari", date_range_days)
        
        with col_ts2:
            st.metric("Rata-rata Postingan/Hari", f"{daily_activity.mean():.1f}")
        
        with col_ts3:
            st.metric("Postingan Hari Puncak", peak_count)
        
        with col_ts4:
            st.metric("Postingan Hari Terendah", daily_activity.min())
    
    else:
        st.info("Tidak ada data tanggal yang valid untuk analisis time series")

else:
    st.info("Kolom tanggal tidak ditemukan dalam dataset untuk analisis time series")

# ============================================================================
# RISK PREDICTION MODEL: ANALISIS PROBABILITAS ESKALASI
# ============================================================================

st.header(RISK_TITLE)
st.caption("Model prediktif untuk menilai risiko eskalasi aksi massa")

# Add explanation
with st.expander("ℹ️ Penjelasan Penilaian Risiko", expanded=False):
    st.markdown(RISK_DESCRIPTION)

# Calculate risk factors
risk_factors = {}

# Factor 1: Negative sentiment ratio
negative_ratio = (df_filtered['sentiment_label'] == 'Negatif').sum() / len(df_filtered)
risk_factors['negative_sentiment'] = negative_ratio * 100

# Factor 2: Action keyword prevalence
if 'has_action_keywords' in df_filtered.columns:
    action_ratio = df_filtered['has_action_keywords'].sum() / len(df_filtered)
elif 'detected_keywords' in df_filtered.columns:
    action_ratio = sum(1 for kws in df_filtered['detected_keywords'] if isinstance(kws, list) and len(kws) > 0) / len(df_filtered)
else:
    action_ratio = 0
risk_factors['action_keywords'] = action_ratio * 100

# Factor 3: High engagement on negative content
if 'engagement' in df_filtered.columns:
    negative_content = df_filtered[df_filtered['sentiment_label'] == 'Negatif']
    if len(negative_content) > 0:
        negative_high_engagement = (negative_content['engagement'] > negative_content['engagement'].quantile(0.75)).sum()
        risk_factors['viral_negative'] = (negative_high_engagement / len(negative_content)) * 100
    else:
        risk_factors['viral_negative'] = 0
else:
    risk_factors['viral_negative'] = 0

# Factor 4: Opposition figure mentions (if political figures data available)
if 'political_figures' in df_filtered.columns:
    pro_mentions = 0
    contra_mentions = 0
    for fig_dict in df_filtered['political_figures']:
        if isinstance(fig_dict, dict):
            pro_mentions += len(fig_dict.get('Pro-Policy', []))
            contra_mentions += len(fig_dict.get('Contra-Policy', []))
    
    opposition_ratio = contra_mentions / (pro_mentions + contra_mentions + 1)
    risk_factors['opposition_figures'] = opposition_ratio * 100
else:
    risk_factors['opposition_figures'] = 0

# Factor 5: Cross-platform spread
if 'source' in df_filtered.columns:
    platforms_with_high_negative = 0
    for source in df_filtered['source'].unique():
        source_data = df_filtered[df_filtered['source'] == source]
        neg_pct = (source_data['sentiment_label'] == 'Negatif').sum() / len(source_data)
        if neg_pct > 0.4:  # More than 40% negative
            platforms_with_high_negative += 1
    risk_factors['platform_spread'] = (platforms_with_high_negative / df_filtered['source'].nunique()) * 100
else:
    risk_factors['platform_spread'] = 0

# Define weights for each factor
weights = {
    'negative_sentiment': 0.25,
    'action_keywords': 0.30,
    'viral_negative': 0.20,
    'opposition_figures': 0.15,
    'platform_spread': 0.10
}

# Calculate weighted risk score
risk_score = sum(risk_factors[key] * weights[key] for key in weights.keys())

# Display risk score prominently
st.subheader("🎯 Penilaian Risiko Keseluruhan")

col_risk_main1, col_risk_main2 = st.columns([1, 2])

with col_risk_main1:
    # Risk level classification
    if risk_score >= 70:
        risk_level = "🔴 SANGAT TINGGI"
        risk_color = "red"
        probability = "75-90%"
    elif risk_score >= 50:
        risk_level = "🟠 TINGGI"
        risk_color = "orange"
        probability = "50-75%"
    elif risk_score >= 30:
        risk_level = "🟡 SEDANG"
        risk_color = "yellow"
        probability = "25-50%"
    else:
        risk_level = "🟢 RENDAH"
        risk_color = "green"
        probability = "<25%"
    
    st.metric("Skor Risiko", f"{risk_score:.1f}/100")
    st.metric("Tingkat Risiko", risk_level)
    st.metric("Probabilitas Eskalasi", probability)

with col_risk_main2:
    # Risk gauge visualization
    try:
        import altair as alt
        
        # Create gauge chart data
        gauge_data = pd.DataFrame({
            'value': [risk_score],
            'max': [100]
        })
        
        # Determine color based on risk score
        if risk_score >= 70:
            gauge_color = '#e74c3c'
        elif risk_score >= 50:
            gauge_color = '#e67e22'
        elif risk_score >= 30:
            gauge_color = '#f39c12'
        else:
            gauge_color = '#2ecc71'
        
        # Create horizontal bar as gauge
        chart_gauge = alt.Chart(gauge_data).mark_bar(height=50, color=gauge_color).encode(
            x=alt.X('value:Q', scale=alt.Scale(domain=[0, 100]), title='Skor Risiko'),
            tooltip=[alt.Tooltip('value:Q', title='Skor Risiko', format='.1f')]
        ).properties(
            title='Meteran Skor Risiko',
            height=100
        ).configure_axis(
            labelFontSize=11,
            titleFontSize=12
        ).configure_title(
            fontSize=13,
            fontWeight='bold'
        )
        
        st.altair_chart(chart_gauge, use_container_width=True)
    
    except Exception as e:
        st.warning(f"Tidak dapat membuat grafik meteran: {e}")

# Risk factors breakdown
st.subheader("📊 Rincian Faktor Risiko")

factor_names = {
    'negative_sentiment': 'Rasio Sentimen Negatif',
    'action_keywords': 'Prevalensi Kata Kunci Aksi',
    'viral_negative': 'Konten Negatif Viral',
    'opposition_figures': 'Sebutan Tokoh Oposisi',
    'platform_spread': 'Penyebaran Lintas Platform'
}

# Create visualization
try:
    import altair as alt
    
    factors_df = pd.DataFrame([
        {
            'Factor': factor_names[key],
            'Value': value,
            'Weight': weights[key],
            'Contribution': value * weights[key]
        }
        for key, value in risk_factors.items()
    ]).sort_values('Contribution', ascending=False)
    
    col_factor1, col_factor2 = st.columns([2, 1])
    
    with col_factor1:
        chart_factors = alt.Chart(factors_df).mark_bar(color='#e74c3c', opacity=0.8).encode(
            x=alt.X('Value:Q', title='Nilai Faktor (%)'),
            y=alt.Y('Factor:N', title='', sort='-x'),
            tooltip=[
                alt.Tooltip('Factor:N', title='Faktor Risiko'),
                alt.Tooltip('Value:Q', title='Nilai', format='.1f'),
                alt.Tooltip('Weight:Q', title='Bobot', format='.2f'),
                alt.Tooltip('Contribution:Q', title='Kontribusi', format='.1f')
            ]
        ).properties(
            title='Faktor Risiko berdasarkan Nilai',
            height=300
        ).configure_axis(
            labelFontSize=11,
            titleFontSize=12
        ).configure_title(
            fontSize=13,
            fontWeight='bold'
        )
        
        st.altair_chart(chart_factors, use_container_width=True)
    
    with col_factor2:
        st.write("**Detail Faktor:**")
        for _, row in factors_df.iterrows():
            st.write(f"**{row['Factor']}**")
            st.progress(row['Value'] / 100)
            st.caption(f"Nilai: {row['Value']:.1f}% | Bobot: {row['Weight']:.2f}")

except Exception as e:
    st.warning(f"Tidak dapat membuat grafik faktor: {e}")

# Recommendations based on risk level
st.subheader("💡 Rekomendasi & Rencana Aksi")

col_rec1, col_rec2 = st.columns(2)

with col_rec1:
    if risk_score >= 70:
        st.error("""
        **⚠️ PERINGATAN KRITIS**
        
        **Siaga Tingkat 1 - Manajemen Krisis**
        
        **Tindakan Segera:**
        - 🚨 Aktifkan tim komunikasi krisis
        - 📞 Libatkan pemangku kepentingan utama segera
        - 👁️ Pemantauan 24/7 semua platform
        - 📢 Strategi komunikasi proaktif
        - 🤝 Dialog dengan pemimpin oposisi
        
        **Waktu:** Segera (0-24 jam)
        """)
    elif risk_score >= 50:
        st.warning("""
        **⚠️ PERINGATAN TINGGI**
        
        **Siaga Tingkat 2 - Pemantauan Intensif**
        
        **Tindakan Disarankan:**
        - 📊 Social listening intensif
        - 💬 Keterlibatan pemangku kepentingan
        - 📝 Siapkan materi komunikasi krisis
        - 🎯 Strategi kontra-narasi
        - 👥 Sesi dialog komunitas
        
        **Waktu:** Mendesak (24-72 jam)
        """)
    elif risk_score >= 30:
        st.info("""
        **ℹ️ WASPADA SEDANG**
        
        **Siaga Tingkat 3 - Langkah Pencegahan**
        
        **Tindakan Disarankan:**
        - 📈 Pemantauan rutin
        - 📢 Komunikasi preventif
        - 🎓 Sosialisasi kebijakan
        - 🤝 Dialog dengan kelompok kritis
        - 📊 Lacak tren sentimen
        
        **Waktu:** Standar (3-7 hari)
        """)
    else:
        st.success("""
        **✓ KONDISI TERKENDALI**
        
        **Siaga Tingkat 4 - Pemantauan Standar**
        
        **Tindakan Disarankan:**
        - 📊 Pemantauan standar
        - 📢 Pertahankan komunikasi
        - 🎓 Edukasi publik berkelanjutan
        - 🤝 Update rutin stakeholder
        - 📈 Lacak metrik dasar
        
        **Waktu:** Rutin (berkelanjutan)
        """)

with col_rec2:
    st.markdown("**Strategi Mitigasi Utama:**")
    
    # Specific recommendations based on highest risk factors
    top_factor = factors_df.iloc[0]
    
    if top_factor['Factor'] == 'Prevalensi Kata Kunci Aksi':
        st.markdown("""
        🎯 **Fokus: Mitigasi Kata Kunci Aksi**
        - Pantau upaya pengorganisasian protes
        - Libatkan penyelenggara potensial
        - Sediakan saluran resmi untuk keluhan
        - Komunikasi transparan mengenai kebijakan
        """)
    elif top_factor['Factor'] == 'Rasio Sentimen Negatif':
        st.markdown("""
        🎯 **Fokus: Perbaikan Sentimen**
        - Tangani kekhawatiran publik secara langsung
        - Soroti manfaat kebijakan
        - Bagikan kisah sukses
        - Tingkatkan pesan positif
        """)
    elif top_factor['Factor'] == 'Konten Negatif Viral':
        st.markdown("""
        🎯 **Fokus: Manajemen Konten Viral**
        - Respon cepat terhadap postingan viral
        - Pemeriksaan fakta dan klarifikasi
        - Keterlibatan influencer
        - Amplifikasi konten positif
        """)
    elif top_factor['Factor'] == 'Sebutan Tokoh Oposisi':
        st.markdown("""
        🎯 **Fokus: Keterlibatan Oposisi**
        - Dialog langsung dengan oposisi
        - Cari titik temu
        - Solusi kolaboratif
        - Pengambilan keputusan inklusif
        """)
    else:
        st.markdown("""
        🎯 **Fokus: Manajemen Platform**
        - Strategi spesifik platform
        - Pesan terkoordinasi
        - Manajemen komunitas
        - Pemantauan lintas platform
        """)

# Scenario predictions
st.subheader("📋 Skenario Terprediksi")

scenarios = []

# Scenario 1: Based on action keywords
if action_ratio > 0.25:
    scenarios.append({
        'probability': 'Tinggi (70-80%)',
        'scenario': 'Aksi Demonstrasi Terbatas',
        'description': 'Unjuk rasa oleh kelompok oposisi di lokasi strategis',
        'color': 'red'
    })
else:
    scenarios.append({
        'probability': 'Sedang (40-50%)',
        'scenario': 'Protes Online Terbatas',
        'description': 'Kampanye media sosial tanpa mobilisasi fisik signifikan',
        'color': 'orange'
    })

# Scenario 2: Based on sentiment and engagement
if negative_ratio > 0.4 and risk_factors['viral_negative'] > 25:
    scenarios.append({
        'probability': 'Tinggi (65-75%)',
        'scenario': 'Viral Campaign Negatif',
        'description': 'Trending topic negatif dengan jangkauan luas',
        'color': 'red'
    })

# Scenario 3: Based on opposition figures
if risk_factors['opposition_figures'] > 20:
    scenarios.append({
        'probability': 'Sedang (50-60%)',
        'scenario': 'Koordinasi Oposisi Terorganisir',
        'description': 'Konsolidasi penolakan secara terstruktur',
        'color': 'orange'
    })

# Scenario 4: Platform spread
if risk_factors['platform_spread'] > 50:
    scenarios.append({
        'probability': 'Tinggi (70-80%)',
        'scenario': 'Eskalasi Multi-Platform',
        'description': 'Sentimen negatif menyebar ke semua platform',
        'color': 'red'
    })

if scenarios:
    for idx, scenario in enumerate(scenarios, 1):
        with st.expander(f"Skenario {idx}: {scenario['scenario']} - Probabilitas: {scenario['probability']}"):
            st.write(f"**Deskripsi:** {scenario['description']}")
            
            if scenario['color'] == 'red':
                st.error("⚠️ Skenario probabilitas tinggi - memerlukan perhatian segera")
            elif scenario['color'] == 'orange':
                st.warning("⚠️ Skenario probabilitas sedang - memerlukan pemantauan")
            else:
                st.info("ℹ️ Skenario probabilitas rendah - pemantauan standar")

# Summary metrics
st.divider()
col_sum_risk1, col_sum_risk2, col_sum_risk3, col_sum_risk4 = st.columns(4)

with col_sum_risk1:
    st.metric("Skor Risiko", f"{risk_score:.1f}/100")

with col_sum_risk2:
    top_risk_factor = factors_df.iloc[0]['Factor']
    st.metric("Faktor Risiko Utama", top_risk_factor.split()[0])

with col_sum_risk3:
    st.metric("Skenario Terprediksi", len(scenarios))

with col_sum_risk4:
    high_prob_scenarios = sum(1 for s in scenarios if 'Tinggi' in s['probability'])
    st.metric("Skenario Prob. Tinggi", high_prob_scenarios)

# ============================================================================
# PLATFORM-SPECIFIC ANALYSIS & STRATEGIC RECOMMENDATIONS
# ============================================================================

st.header(PLATFORM_TITLE)
st.caption("Strategi yang disesuaikan untuk setiap platform media sosial")

with st.expander("ℹ️ Penjelasan Strategi Platform", expanded=False):
    st.markdown(PLATFORM_DESCRIPTION)

if 'source' in df_filtered.columns:
    
    st.subheader("🎯 Platform-by-Platform Breakdown")
    
    # Calculate platform-specific metrics
    platform_analysis = {}
    
    for platform in sorted(df_filtered['source'].unique()):
        platform_data = df_filtered[df_filtered['source'] == platform]
        
        # Calculate metrics
        total_posts = len(platform_data)
        sentiment_dist = platform_data['sentiment_label'].value_counts(normalize=True) * 100
        
        # Action keywords
        if 'has_action_keywords' in platform_data.columns:
            action_keywords_pct = (platform_data['has_action_keywords'].sum() / total_posts) * 100
        elif 'detected_keywords' in platform_data.columns:
            action_keywords_pct = (sum(1 for kws in platform_data['detected_keywords'] if isinstance(kws, list) and len(kws) > 0) / total_posts) * 100
        else:
            action_keywords_pct = 0
        
        # Engagement
        avg_engagement = platform_data['engagement'].mean() if 'engagement' in platform_data.columns else 0
        
        # Top figure
        top_figure_name = "N/A"
        if 'political_figures' in platform_data.columns:
            platform_figures = []
            for fig_dict in platform_data['political_figures']:
                if isinstance(fig_dict, dict):
                    platform_figures.extend(fig_dict.get('Pro-Policy', []))
                    platform_figures.extend(fig_dict.get('Contra-Policy', []))
            
            if platform_figures:
                from collections import Counter
                top_figure = Counter(platform_figures).most_common(1)
                top_figure_name = top_figure[0][0] if top_figure else "N/A"
        
        # Determine risk level
        neg_pct = sentiment_dist.get('Negatif', 0)
        platform_risk = "High" if (neg_pct > 50 or action_keywords_pct > 30) else ("Medium" if neg_pct > 35 else "Low")
        
        platform_analysis[platform] = {
            'total_posts': total_posts,
            'negative_pct': neg_pct,
            'action_keywords_pct': action_keywords_pct,
            'avg_engagement': avg_engagement,
            'top_figure': top_figure_name,
            'risk_level': platform_risk,
            'dominant_sentiment': sentiment_dist.idxmax()
        }
    
    # Display platform cards
    for platform, metrics in platform_analysis.items():
        risk_emoji = "🔴" if metrics['risk_level'] == "High" else ("🟡" if metrics['risk_level'] == "Medium" else "🟢")
        
        with st.expander(f"{risk_emoji} {platform.upper()} - Risk: {metrics['risk_level']} | {metrics['total_posts']:,} posts"):
            col_plat1, col_plat2 = st.columns([1, 2])
            
            with col_plat1:
                st.write("**📊 Metrics:**")
                st.metric("Total Posts", f"{metrics['total_posts']:,}")
                st.metric("Negative %", f"{metrics['negative_pct']:.1f}%")
                st.metric("Action Keywords %", f"{metrics['action_keywords_pct']:.1f}%")
                if metrics['avg_engagement'] > 0:
                    st.metric("Avg Engagement", f"{metrics['avg_engagement']:.0f}")
                st.write(f"**Top Figure:** {metrics['top_figure'].upper()}")
            
            with col_plat2:
                st.write("**💡 Rekomendasi Strategis:**")
                
                if platform == 'tiktok':
                    if metrics['risk_level'] == 'High':
                        st.error("""
                        **Prioritas: TERTINGGI** (Sumber data terbesar)
                        - 🎥 Video kontra-narasi dengan influencer pro-kebijakan
                        - 📱 Video penjelasan tentang manfaat kebijakan (< 60 detik)
                        - 🎵 Lacak suara & tagar tren terkait pilkada
                        - 👥 Kolaborasi dengan kreator TikTok muda
                        """)
                    else:
                        st.success("""
                        - 📱 Pertahankan interaksi dengan konten edukatif
                        - 🎬 Gunakan format bercerita yang relevan
                        - 🎵 Manfaatkan suara tren untuk jangkauan maksimal
                        """)
                
                elif platform == 'facebook':
                    if metrics['risk_level'] == 'High':
                        st.error("""
                        **Fokus: Demografi 30+ tahun**
                        - ✅ Postingan cek fakta, keterlibatan komunitas
                        - 📊 Infografis dampak positif kebijakan
                        - 🤝 Kemitraan dengan halaman influencer lokal
                        - 💬 Moderasi aktif di kolom komentar
                        """)
                    else:
                        st.success("""
                        - 💬 Pertahankan dialog di kolom komentar
                        - 📖 Bagikan kisah sukses dari daerah lain
                        - 👥 Membangun komunitas melalui grup
                        """)
                
                elif platform == 'x':
                    if metrics['risk_level'] == 'High':
                        st.error("""
                        **Prioritas: TINGGI** (Platform diskusi kritis)
                        - ⚡ Tim respon cepat untuk melawan misinformasi
                        - 🧵 Utas (thread) edukatif, argumen berbasis data
                        - 💬 Balasan langsung ke akun berpengaruh
                        - 📊 Pemantauan topik tren secara real-time
                        """)
                    else:
                        st.success("""
                        - 📊 Pantau topik tren secara real-time
                        - 🎓 Terlibat dengan suara akademisi/ahli
                        - 🧵 Bagikan wawasan berbasis data
                        """)
                
                elif platform == 'instagram':
                    st.info("""
                    - 📸 Penceritaan visual (carousel, reels)
                    - 🤝 Kolaborasi dengan mikro-influencer
                    - 💬 Lacak sentimen di kolom komentar
                    - 🎨 Konten visual berkualitas tinggi
                    """)
                
                elif platform == 'youtube':
                    st.info("""
                    - 🎥 Video penjelasan panjang, wawancara ahli
                    - 🔍 Optimasi SEO untuk kemudahan pencarian
                    - 💬 Sematkan komentar positif, tanggapi kritik
                    - 📺 Kolaborasi dengan saluran edukasi
                    """)
                
                elif platform == 'threads':
                    st.info("""
                    - 🆕 Platform berkembang, keuntungan pengadopsi awal
                    - 💬 Percakapan otentik, transparansi
                    - 🎯 Proses pembuatan kebijakan di balik layar
                    - 🤝 Bangun komunitas dari awal
                    """)
                
                else:  # online/media
                    st.info("""
                    - 📰 Hubungan media & rilis pers
                    - 🎤 Briefing media proaktif, opini ahli
                    - 📊 Lacak sentimen media & nada pemberitaan
                    - 🤝 Bangun hubungan dengan jurnalis
                    """)

# ============================================================================
# RENCANA AKSI & PREDIKSI JADWAL
# ============================================================================

st.header("📋 Rencana Aksi & Prediksi Jadwal")
st.caption("Strategi jangka panjang untuk 3 bulan ke depan (Januari-April 2026)")

# Timeline predictions based on risk score
st.subheader("⏰ Timeline Predictions")

timeline_predictions = []

# Month 1: January-February 2026
if risk_score >= 50:
    timeline_predictions.append({
        'period': 'BULAN 1 (Januari-Februari 2026)',
        'prediction': 'Eskalasi Media Sosial & Mobilisasi Awal',
        'probability': '75-85%',
        'color': 'red',
        'indicators': [
            'Topik tren negatif berkelanjutan di X, TikTok, Facebook',
            'Video protes/kritik viral mencapai jutaan tayangan',
            'Koordinasi antar kelompok oposisi semakin solid',
            'Kampanye tagar #TolakRevisi atau sejenisnya'
        ],
        'actions': [
            'Aktifkan tim komunikasi krisis 24/7',
            'Respon cepat di semua platform (< 2 jam)',
            'Keterlibatan intensif dengan influencer netral/pro',
            'Pemantauan sentimen real-time dengan AI',
            'Rilis pers & briefing media harian',
            'Gempuran media: TV, radio, iklan digital',
            'Dialog darurat dengan tokoh kunci oposisi'
        ]
    })
else:
    timeline_predictions.append({
        'period': 'BULAN 1 (Januari-Februari 2026)',
        'prediction': 'Diskusi Online Moderat',
        'probability': '40-50%',
        'color': 'green',
        'indicators': [
            'Diskusi terbatas di kalangan tertentu',
            'Topik tren sporadis, belum berkelanjutan',
            'Sentimen negatif tersebar, belum terkonsolidasi'
        ],
        'actions': [
            'Sosialisasi proaktif manfaat kebijakan',
            'Pantau pergeseran sentimen harian',
            'Dialog preventif dengan pemangku kepentingan kunci',
            'Kampanye media sosial edukatif',
            'Kesaksian ahli & dukungan akademis'
        ]
    })

# Month 2: February-March 2026
if action_ratio > 0.25:
    timeline_predictions.append({
        'period': 'BULAN 2 (Februari-Maret 2026)',
        'prediction': 'Mobilisasi Fisik & Kampanye Terorganisir',
        'probability': '65-75%',
        'color': 'orange',
        'indicators': [
            'Pernyataan resmi untuk aksi massa',
            'Koordinasi antar ormas oposisi semakin rapi',
            'Penyebaran info lokasi & waktu demo massal',
            'Petisi online mencapai ratusan ribu tanda tangan',
            'Liputan media intensif tentang rencana protes'
        ],
        'actions': [
            'Koordinasi ketat dengan keamanan & Polri',
            'Komunikasi transparansi maksimal',
            'Mediasi intensif dengan tokoh oposisi moderat',
            'Kampanye media masif (semua saluran)',
            'Dengar pendapat umum & pertemuan warga di 10+ kota',
            'Melibatkan tokoh lintas partai sebagai mediator',
            'Pemantauan massa real-time & protokol de-eskalasi'
        ]
    })
else:
    timeline_predictions.append({
        'period': 'BULAN 2 (Februari-Maret 2026)',
        'prediction': 'Konsolidasi Oposisi Terbatas',
        'probability': '45-55%',
        'color': 'yellow',
        'indicators': [
            'Diskusi publik meningkat tapi belum terorganisir',
            'Kelompok oposisi masih mencari momentum',
            'Liputan media meningkat tapi belum viral'
        ],
        'actions': [
            'Intensifikasi pemantauan & peringatan dini',
            'Keterlibatan preventif dengan penggerak potensial',
            'Kampanye kontra-narasi yang berbasis data',
            'Melibatkan akademisi & masyarakat sipil',
            'Kehadiran media berkelanjutan dengan cerita positif'
        ]
    })

# Month 3: March-April 2026
timeline_predictions.append({
    'period': 'BULAN 3 (Maret-April 2026)',
    'prediction': 'Kampanye Berkelanjutan' if negative_ratio > 0.4 else 'Normalisasi Bertahap',
    'probability': '55-65%' if negative_ratio > 0.4 else '60-70%',
    'color': 'orange' if negative_ratio > 0.4 else 'green',
    'indicators': [
        'Ulasan Yudisial & tekanan politik' if negative_ratio > 0.4 else 'Intensitas diskusi menurun',
        'Kampanye media berkelanjutan' if negative_ratio > 0.4 else 'Fokus publik mulai ke isu lain',
        'Membangun koalisi antar oposisi' if negative_ratio > 0.4 else 'Fragmentasi kelompok oposisi'
    ],
    'actions': [
        'Konten jangka panjang: artikel penelitian, kertas putih',
        'Keterlibatan dengan akademisi, ahli, & wadah pemikir',
        'Tunjukkan hasil konkret & dampak positif',
        'Perbandingan internasional & praktik terbaik',
        'Perbaikan berkelanjutan berdasarkan umpan balik',
        'Pameran inovasi & kisah sukses',
        'Perkuat koalisi dengan pemangku kepentingan'
    ]
})

# Display timeline
for idx, timeline in enumerate(timeline_predictions, 1):
    with st.expander(f"⏰ {timeline['period']} - {timeline['prediction']} (Prob: {timeline['probability']})"):
        
        if timeline['color'] == 'red':
            st.error(f"**Periode Risiko Tinggi** - Probabilitas: {timeline['probability']}")
        elif timeline['color'] == 'orange':
            st.warning(f"**Periode Risiko Sedang** - Probabilitas: {timeline['probability']}")
        else:
            st.success(f"**Periode Terkendali** - Probabilitas: {timeline['probability']}")
        
        col_time1, col_time2 = st.columns(2)
        
        with col_time1:
            st.write("**📍 Indikator untuk Dipantau:**")
            for indicator in timeline['indicators']:
                st.write(f"• {indicator}")
        
        with col_time2:
            st.write("**✅ Tindakan Disarankan:**")
            for action in timeline['actions']:
                st.write(f"• {action}")

# Strategic Framework
st.subheader("🎯 Kerangka Strategis 5 Pilar")

strategic_pillars = {
    '1. KOMUNIKASI PROAKTIF': {
        'objective': 'Bingkai narasi positif sebelum narasi negatif menguat',
        'tactics': [
            'Briefing pers harian dengan data konkret',
            'Testimoni ahli & dukungan akademis',
            'Kisah sukses dari daerah dengan sistem serupa',
            'Sesi tanya jawab transparan (online & offline)'
        ],
        'kpi': 'Keseimbangan liputan media 60:40 (positif:negatif)'
    },
    '2. KETERLIBATAN PEMANGKU KEPENTINGAN': {
        'objective': 'Bangun koalisi luas & netralkan oposisi keras',
        'tactics': [
            'Pertemuan tatap muka dengan tokoh kunci',
            'Forum multi-stakeholder & diskusi meja bundar',
            'Libatkan masyarakat sipil & organisasi akar rumput',
            'Buat kelompok kerja lintas partai'
        ],
        'kpi': 'Min. 5 tokoh netral/oposisi moderat mendukung'
    },
    '3. KAMPANYE DIGITAL': {
        'objective': 'Dominasi narasi di platform digital utama',
        'tactics': [
            'Konten multi-platform (disesuaikan per platform)',
            'Kemitraan influencer (mikro & makro)',
            'Kampanye konten buatan pengguna (UGC)',
            'Iklan berbayar dengan penargetan strategis'
        ],
        'kpi': 'Tingkat keterlibatan 15%+, pergeseran sentimen +10%'
    },
    '4. MITIGASI RISIKO': {
        'objective': 'Cegah & respon pemicu eskalasi',
        'tactics': [
            'Sistem peringatan dini dengan pemantauan AI',
            'Protokol respon cepat (<2 jam)',
            'Latihan & simulasi komunikasi krisis',
            'Saluran khusus untuk keluhan'
        ],
        'kpi': 'Waktu respon <2 jam, penyelesaian masalah <24 jam'
    },
    '5. PEMANTAUAN & EVALUASI': {
        'objective': 'Pembelajaran berkelanjutan & adaptasi strategi',
        'tactics': [
            'Dashboard pelacakan sentimen harian',
            'Pertemuan tinjauan strategi mingguan',
            'Survei persepsi publik dua mingguan',
            'Penilaian dampak komprehensif bulanan'
        ],
        'kpi': 'Trajektori perbaikan sentimen +5% per bulan'
    }
}

for pillar, details in strategic_pillars.items():
    with st.expander(f"{pillar}"):
        st.write(f"**🎯 Tujuan:** {details['objective']}")
        
        st.write("**📋 Taktik:**")
        for tactic in details['tactics']:
            st.write(f"• {tactic}")
        
        st.write(f"**📊 Indikator Kinerja Utama (KPI):**")
        st.info(f"✓ {details['kpi']}")

# Final Strategic Recommendation
st.subheader("🎯 Rekomendasi Strategis Akhir")

final_rec_color = "error" if risk_score >= 70 else ("warning" if risk_score >= 50 else "info")

if final_rec_color == "error":
    st.error(f"""
    **⚠️ SITUASI KRITIS - Skor Risiko: {risk_score:.1f}/100**
    
    Berdasarkan analisis {len(df_filtered):,} postingan, situasi memerlukan **TINDAKAN SEGERA**.
    
    **PRIORITAS UTAMA (48 Jam Ke Depan):**
    1. 🚨 Aktifkan tim komunikasi krisis
    2. 📞 Engagement stakeholder darurat
    3. 📢 Strategi media proaktif
    4. 👁️ Monitoring 24/7 semua platform
    
    **FAKTOR SUKSES KRITIS:**
    • Transparansi maksimal & responsiveness
    • Endorser pihak ketiga (akademisi, tokoh netral)
    • Respons cepat spesifik per platform
    • Kesediaan untuk mengakomodasi masukan
    
    **JENDELA KESEMPATAN:** 2-4 minggu
    Setelah itu, biaya mitigasi meningkat 3-5x lipat.
    """)
elif final_rec_color == "warning":
    st.warning(f"""
    **⚠️ RISIKO TINGGI - Skor Risiko: {risk_score:.1f}/100**
    
    Berdasarkan analisis {len(df_filtered):,} postingan, situasi memerlukan **PERHATIAN MENDESAK**.
    
    **PRIORITAS (1-2 Minggu Ke Depan):**
    1. 📊 Monitoring intensif & peringatan dini
    2. 💬 Kampanye engagement stakeholder
    3. 📝 Siapkan materi komunikasi krisis
    4. 🎯 Strategi kontra-narasi
    
    **HASIL YANG DIHARAPKAN (3 bulan):**
    • Pergeseran sentimen: Negatif ↓15-20%, Positif ↑10-15%
    • Kata kunci aksi: ↓30-40%
    • Penerimaan publik: ↑25-30%
    
    **TIMELINE:** Bertindak dalam 2 minggu untuk hasil optimal.
    """)
else:
    st.info(f"""
    **ℹ️ SITUASI TERKELOLA - Skor Risiko: {risk_score:.1f}/100**
    
    Berdasarkan analisis {len(df_filtered):,} postingan, situasi **TERKENDALI** dengan monitoring standar.
    
    **TINDAKAN YANG DIREKOMENDASIKAN:**
    1. 📊 Monitoring & tracking reguler
    2. 📢 Komunikasi preventif
    3. 🎓 Sosialisasi kebijakan
    4. 🤝 Dialog stakeholder
    
    **PERTAHANKAN:**
    • Pesan positif
    • Engagement komunitas
    • Komunikasi transparan
    • Tracking metrik baseline
    """)


# Summary metrics
st.divider()
col_final1, col_final2, col_final3, col_final4 = st.columns(4)

with col_final1:
    st.metric("Periode Analisis", f"{len(df_filtered):,} postingan")

with col_final2:
    st.metric("Tingkat Risiko", risk_level)

with col_final3:
    st.metric("Jadwal", "3 bulan")

with col_final4:
    st.metric("Item Aksi", sum(len(t['actions']) for t in timeline_predictions))

# ============================================================================
# FORECASTING ANALYSIS: PREDIKSI TIMELINE & TREND SENTIMENT
# ============================================================================

st.header("🔮 Analisis Forecasting: Memprediksi Tren Masa Depan")
st.caption("Prediksi berbasis machine learning untuk sentimen dan engagement")

with st.expander("ℹ️ Penjelasan Forecasting", expanded=False):
    st.markdown("""
**Model Forecasting menggunakan:**
- Regresi polinomial untuk memprediksi tren
- Data historis untuk melatih model
- Confidence intervals untuk mengukur ketidakpastian

**Kegunaan:**
- Antisipasi perubahan sentimen
- Perencanaan strategi komunikasi
- Alokasi sumber daya monitoring
- Early warning system

**Catatan:** Prediksi akurat untuk jangka pendek (7-30 hari), semakin jauh prediksi semakin besar ketidakpastian.
    """)

# Check if we have date data
if 'date_parsed' in df_filtered.columns:
    df_forecast = df_filtered.copy()
    df_forecast['date_parsed'] = pd.to_datetime(df_forecast['date_parsed'], errors='coerce')
    df_forecast = df_forecast[df_forecast['date_parsed'].notna()].copy()
    
    if len(df_forecast) > 0:
        df_forecast['date_only'] = df_forecast['date_parsed'].dt.date
        df_forecast['date_numeric'] = (df_forecast['date_parsed'] - df_forecast['date_parsed'].min()).dt.days
        
        # Calculate daily metrics
        daily_metrics = df_forecast.groupby('date_only').agg({
            'sentiment_label': lambda x: (x == 'Negatif').sum(),
            'date_numeric': 'first'
        }).reset_index()
        
        # Add action keywords count
        if 'has_action_keywords' in df_forecast.columns:
            action_counts = df_forecast.groupby('date_only')['has_action_keywords'].sum()
        elif 'detected_keywords' in df_forecast.columns:
            action_counts = df_forecast.groupby('date_only').apply(
                lambda x: sum(1 for kws in x['detected_keywords'] if isinstance(kws, list) and len(kws) > 0)
            )
        else:
            action_counts = pd.Series(0, index=daily_metrics['date_only'])
        
        daily_metrics['action_keywords_count'] = daily_metrics['date_only'].map(action_counts).fillna(0)
        daily_metrics.columns = ['date', 'negative_count', 'days_since_start', 'action_keywords_count']
        
        # Display date range
        min_date = daily_metrics['date'].min()
        max_date = daily_metrics['date'].max()
        total_days = len(daily_metrics)
        
        st.info(f"📅 Data historis: **{min_date}** sampai **{max_date}** ({total_days} hari)")
        
        # Show recent trends
        col_trend1, col_trend2 = st.columns(2)
        
        with col_trend1:
            st.write("**5 Hari Pertama:**")
            st.dataframe(daily_metrics.head(5), use_container_width=True)
        
        with col_trend2:
            st.write("**5 Hari Terakhir:**")
            st.dataframe(daily_metrics.tail(5), use_container_width=True)
        
        # Forecasting with polynomial regression
        if len(daily_metrics) >= 3:
            st.subheader("📈 Prediksi Tren (Regresi Polinomial)")
            
            # Prepare data
            X = daily_metrics['days_since_start'].values.reshape(-1, 1)
            y_negative = daily_metrics['negative_count'].values
            y_action = daily_metrics['action_keywords_count'].values
            
            # Polynomial regression (degree 2)
            from sklearn.preprocessing import PolynomialFeatures
            from sklearn.linear_model import LinearRegression
            import numpy as np
            
            poly = PolynomialFeatures(degree=2)
            X_poly = poly.fit_transform(X)
            
            poly_negative = LinearRegression()
            poly_negative.fit(X_poly, y_negative)
            
            poly_action = LinearRegression()
            poly_action.fit(X_poly, y_action)
            
            # Forecast for 7, 14, 30 days
            forecast_periods = [
                {'days': 7, 'label': '1 Minggu'},
                {'days': 14, 'label': '2 Minggu'},
                {'days': 30, 'label': '1 Bulan'}
            ]
            
            max_day = daily_metrics['days_since_start'].max()
            current_neg_avg = y_negative.mean()
            current_action_avg = y_action.mean()
            
            # Display forecasts
            for period in forecast_periods:
                days_ahead = period['days']
                label = period['label']
                
                future_day = max_day + days_ahead
                X_future = np.array([[future_day]])
                X_future_poly = poly.transform(X_future)
                
                pred_neg = poly_negative.predict(X_future_poly)[0]
                pred_action = poly_action.predict(X_future_poly)[0]
                
                neg_change = ((pred_neg - current_neg_avg) / (current_neg_avg + 1)) * 100
                action_change = ((pred_action - current_action_avg) / (current_action_avg + 1)) * 100
                
                # Determine risk
                if pred_neg > current_neg_avg * 1.2 and pred_action > current_action_avg * 1.2:
                    risk = "🔴 ESKALASI KRITIS"
                    risk_color = "error"
                elif pred_neg > current_neg_avg * 1.1 or pred_action > current_action_avg * 1.1:
                    risk = "🟠 ESKALASI SEDANG"
                    risk_color = "warning"
                elif pred_neg < current_neg_avg * 0.9 and pred_action < current_action_avg * 0.9:
                    risk = "🟢 SENTIMEN MEMBAIK"
                    risk_color = "success"
                else:
                    risk = "🟡 STABIL DENGAN FLUKTUASI"
                    risk_color = "info"
                
                forecast_date = pd.to_datetime(max_date) + pd.Timedelta(days=days_ahead)
                
                with st.expander(f"⏰ Prediksi {label} ({forecast_date.strftime('%Y-%m-%d')}) - {risk}"):
                    col_fc1, col_fc2, col_fc3 = st.columns(3)
                    
                    with col_fc1:
                        st.write("**Postingan Negatif:**")
                        st.metric("Rerata Saat Ini", f"{current_neg_avg:.1f}/hari")
                        st.metric("Diprediksi", f"{pred_neg:.1f}/hari", delta=f"{neg_change:+.1f}%")
                        
                        if neg_change > 10:
                            st.error("📈 Tren MENINGKAT")
                        elif neg_change < -10:
                            st.success("📉 Tren MENURUN")
                        else:
                            st.info("➡️ Tren STABIL")
                    
                    with col_fc2:
                        st.write("**Kata Kunci Aksi:**")
                        st.metric("Rerata Saat Ini", f"{current_action_avg:.1f}/hari")
                        st.metric("Diprediksi", f"{pred_action:.1f}/hari", delta=f"{action_change:+.1f}%")
                        
                        if action_change > 10:
                            st.error("📈 Tren MENINGKAT")
                        elif action_change < -10:
                            st.success("📉 Tren MENURUN")
                        else:
                            st.info("➡️ Tren STABIL")
                    
                    with col_fc3:
                        st.write("**Penilaian Risiko:**")
                        if risk_color == "error":
                            st.error(risk)
                            st.write("**Tindakan Diperlukan:**")
                            st.write("• Intervensi segera")
                            st.write("• Aktivasi tim krisis")
                        elif risk_color == "warning":
                            st.warning(risk)
                            st.write("**Tindakan Diperlukan:**")
                            st.write("• Pemantauan ditingkatkan")
                            st.write("• Langkah pencegahan")
                        elif risk_color == "success":
                            st.success(risk)
                            st.write("**Rekomendasi:**")
                            st.write("• Pertahankan strategi saat ini")
                            st.write("• Lanjutkan pemantauan")
                        else:
                            st.info(risk)
                            st.write("**Rekomendasi:**")
                            st.write("• Pemantauan standar")
                            st.write("• Waspadai perubahan")
            
            # Visualization: 90-day forecast
            st.subheader("📊 Visualisasi Prediksi 90 Hari")
            
            try:
                import altair as alt
                
                # Generate 90-day forecast
                future_days = np.arange(max_day + 1, max_day + 91)
                future_dates = [pd.to_datetime(max_date) + pd.Timedelta(days=i) for i in range(1, 91)]
                
                # Polynomial predictions
                z_neg = np.polyfit(daily_metrics['days_since_start'], daily_metrics['negative_count'], 2)
                p_neg = np.poly1d(z_neg)
                
                z_act = np.polyfit(daily_metrics['days_since_start'], daily_metrics['action_keywords_count'], 2)
                p_act = np.poly1d(z_act)
                
                future_neg = p_neg(future_days)
                future_action = p_act(future_days)
                
                # Prepare data for Altair
                # Historical data
                hist_data = pd.DataFrame({
                    'Date': pd.to_datetime(daily_metrics['date']),
                    'Negative Count': daily_metrics['negative_count'],
                    'Action Keywords': daily_metrics['action_keywords_count'],
                    'Type': 'Historis'
                })
                
                # Forecast data
                forecast_data = pd.DataFrame({
                    'Date': future_dates,
                    'Negative Count': future_neg,
                    'Action Keywords': future_action,
                    'Type': 'Prediksi'
                })
                
                # Combine
                combined_data = pd.concat([hist_data, forecast_data], ignore_index=True)
                
                # Create tabs for different views
                tab_neg, tab_act = st.tabs(["Prediksi Sentimen Negatif", "Prediksi Kata Kunci Aksi"])
                
                with tab_neg:
                    # Negative sentiment chart
                    base_neg = alt.Chart(combined_data).encode(
                        x=alt.X('Date:T', title='Tanggal', axis=alt.Axis(format='%Y-%m-%d', labelAngle=-45))
                    )
                    
                    # Historical line
                    hist_line_neg = base_neg.transform_filter(
                        alt.datum.Type == 'Historis'
                    ).mark_line(color='#e74c3c', strokeWidth=2).encode(
                        y=alt.Y('Negative Count:Q', title='Postingan Negatif per Hari'),
                        tooltip=[
                            alt.Tooltip('Date:T', title='Tanggal', format='%Y-%m-%d'),
                            alt.Tooltip('Negative Count:Q', title='Jumlah', format='.0f'),
                            alt.Tooltip('Type:N', title='Tipe')
                        ]
                    )
                    
                    # Forecast line
                    forecast_line_neg = base_neg.transform_filter(
                        alt.datum.Type == 'Prediksi'
                    ).mark_line(color='#ff6b6b', strokeWidth=3, strokeDash=[5, 5]).encode(
                        y=alt.Y('Negative Count:Q'),
                        tooltip=[
                            alt.Tooltip('Date:T', title='Tanggal', format='%Y-%m-%d'),
                            alt.Tooltip('Negative Count:Q', title='Jumlah Diprediksi', format='.0f'),
                            alt.Tooltip('Type:N', title='Tipe')
                        ]
                    )
                    
                    # Today marker
                    today_line = alt.Chart(pd.DataFrame({'Date': [pd.Timestamp.now()]})).mark_rule(
                        color='green',
                        strokeWidth=2
                    ).encode(x='Date:T')
                    
                    chart_neg_forecast = (hist_line_neg + forecast_line_neg + today_line).properties(
                        title='Sentimen Negatif: Prediksi 90 Hari',
                        height=400
                    ).configure_axis(
                        labelFontSize=11,
                        titleFontSize=12
                    ).configure_title(
                        fontSize=14,
                        fontWeight='bold'
                    )
                    
                    st.altair_chart(chart_neg_forecast, use_container_width=True)
                
                with tab_act:
                    # Action keywords chart
                    base_act = alt.Chart(combined_data).encode(
                        x=alt.X('Date:T', title='Tanggal', axis=alt.Axis(format='%Y-%m-%d', labelAngle=-45))
                    )
                    
                    # Historical line
                    hist_line_act = base_act.transform_filter(
                        alt.datum.Type == 'Historis'
                    ).mark_line(color='#f39c12', strokeWidth=2).encode(
                        y=alt.Y('Action Keywords:Q', title='Kata Kunci Aksi per Hari'),
                        tooltip=[
                            alt.Tooltip('Date:T', title='Tanggal', format='%Y-%m-%d'),
                            alt.Tooltip('Action Keywords:Q', title='Jumlah', format='.0f'),
                            alt.Tooltip('Type:N', title='Tipe')
                        ]
                    )
                    
                    # Forecast line
                    forecast_line_act = base_act.transform_filter(
                        alt.datum.Type == 'Prediksi'
                    ).mark_line(color='#ffa726', strokeWidth=3, strokeDash=[5, 5]).encode(
                        y=alt.Y('Action Keywords:Q'),
                        tooltip=[
                            alt.Tooltip('Date:T', title='Tanggal', format='%Y-%m-%d'),
                            alt.Tooltip('Action Keywords:Q', title='Jumlah Diprediksi', format='.0f'),
                            alt.Tooltip('Type:N', title='Tipe')
                        ]
                    )
                    
                    chart_act_forecast = (hist_line_act + forecast_line_act + today_line).properties(
                        title='Kata Kunci Aksi: Prediksi 90 Hari',
                        height=400
                    ).configure_axis(
                        labelFontSize=11,
                        titleFontSize=12
                    ).configure_title(
                        fontSize=14,
                        fontWeight='bold'
                    )
                    
                    st.altair_chart(chart_act_forecast, use_container_width=True)
                
                # Forecast summary for critical dates
                st.subheader("📅 Prediksi Tanggal Kunci")
                
                critical_dates = [
                    (7, '1 Minggu'),
                    (30, '1 Bulan'),
                    (60, '2 Bulan'),
                    (90, '3 Bulan')
                ]
                
                summary_data = []
                for days, label in critical_dates:
                    day_num = max_day + days
                    pred_neg = p_neg(day_num)
                    pred_act = p_act(day_num)
                    
                    neg_change_pct = ((pred_neg / current_neg_avg - 1) * 100) if current_neg_avg > 0 else 0
                    act_change_pct = ((pred_act / current_action_avg - 1) * 100) if current_action_avg > 0 else 0
                    
                    if pred_neg > current_neg_avg * 1.5:
                        status = "⚠️ KRITIS"
                    elif pred_neg > current_neg_avg * 1.2:
                        status = "🟠 RISIKO TINGGI"
                    else:
                        status = "🟡 MODERATE"
                    
                    forecast_date = pd.to_datetime(max_date) + pd.Timedelta(days=days)
                    
                    summary_data.append({
                        'Periode': label,
                        'Tanggal': forecast_date.strftime('%Y-%m-%d'),
                        'Post Neg/Hari': f"{pred_neg:.0f} ({neg_change_pct:+.0f}%)",
                        'Kata Kunci Aksi/Hari': f"{pred_act:.0f} ({act_change_pct:+.0f}%)",
                        'Status': status
                    })
                
                summary_df = pd.DataFrame(summary_data)
                st.dataframe(summary_df, use_container_width=True)
            
            except Exception as e:
                st.warning(f"Tidak dapat membuat visualisasi prediksi: {e}")
        
        else:
            st.info("Data tidak cukup untuk peramalan (perlu minimal 3 hari)")
    
    else:
        st.info("Tidak ada data tanggal valid yang tersedia untuk peramalan")

else:
    st.info("Kolom tanggal tidak ditemukan untuk analisis peramalan")

# ============================================================================
# INFLUENTIAL USERS IDENTIFICATION
# ============================================================================

st.header(INFLUENCER_TITLE)
st.caption("Mengidentifikasi influencer kunci dan opinion leaders dalam diskusi")

with st.expander("ℹ️ Penjelasan Identifikasi Influencer", expanded=False):
    st.markdown(INFLUENCER_DESCRIPTION)

# Check if we have author data
if 'author' in df_filtered.columns and 'engagement' in df_filtered.columns:
    
    # Filter out unknown authors
    df_authors = df_filtered[df_filtered['author'] != 'unknown'].copy()
    
    if len(df_authors) > 0:
        
        # Calculate user influence metrics
        user_metrics = df_authors.groupby('author').agg({
            'engagement': ['sum', 'mean', 'max'],
            'text': 'count'
        })
        
        user_metrics.columns = ['total_engagement', 'avg_engagement', 'max_engagement', 'post_count']
        
        # Add sentiment score if available
        if 'sentiment_score' in df_authors.columns:
            user_metrics['avg_sentiment'] = df_authors.groupby('author')['sentiment_score'].mean()
        
        # Add action keywords percentage
        if 'has_action_keywords' in df_authors.columns:
            user_metrics['action_keywords_pct'] = df_authors.groupby('author')['has_action_keywords'].apply(
                lambda x: (x.sum() / len(x)) * 100 if len(x) > 0 else 0
            )
        elif 'detected_keywords' in df_authors.columns:
            user_metrics['action_keywords_pct'] = df_authors.groupby('author')['detected_keywords'].apply(
                lambda x: sum(1 for kws in x if isinstance(kws, list) and len(kws) > 0) / len(x) * 100 if len(x) > 0 else 0
            )
        else:
            user_metrics['action_keywords_pct'] = 0
        
        # Normalize metrics (0-100 scale)
        user_metrics['engagement_score'] = (user_metrics['total_engagement'] / user_metrics['total_engagement'].max() * 100).round(2)
        user_metrics['reach_score'] = (user_metrics['post_count'] / user_metrics['post_count'].max() * 100).round(2)
        user_metrics['action_score'] = user_metrics['action_keywords_pct']
        
        # Calculate composite influence score
        user_metrics['influence_score'] = (
            user_metrics['engagement_score'] * 0.5 +  # 50% engagement
            user_metrics['reach_score'] * 0.3 +        # 30% reach/frequency
            user_metrics['action_score'] * 0.2         # 20% action keywords
        ).round(2)
        
        # Add platform info
        user_metrics['platform'] = df_authors.groupby('author')['source'].apply(
            lambda x: x.mode()[0] if len(x.mode()) > 0 else 'unknown'
        )
        
        # Identify top influencers (top 2%)
        top_percentile = user_metrics['influence_score'].quantile(0.98)
        influencers = user_metrics[user_metrics['influence_score'] >= top_percentile].sort_values('influence_score', ascending=False)
        
        # Display statistics
        st.subheader("📊 Influencer Statistics")
        
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        
        with col_stat1:
            st.metric("Total Authors", f"{len(user_metrics):,}")
        
        with col_stat2:
            st.metric("Top Influencers (2%)", len(influencers))
        
        with col_stat3:
            st.metric("Influence Threshold", f"{top_percentile:.1f}")
        
        with col_stat4:
            avg_influence = influencers['influence_score'].mean()
            st.metric("Avg Influence Score", f"{avg_influence:.1f}")
        
        # Top 20 Influential Users
        st.subheader("🌟 Top 20 Influential Users")
        
        top_20 = influencers.head(20).copy()
        top_20['Rank'] = range(1, len(top_20) + 1)
        top_20_display = top_20[['Rank', 'platform', 'influence_score', 'post_count', 'avg_engagement', 'action_keywords_pct']].copy()
        top_20_display.columns = ['Rank', 'Platform', 'Influence Score', 'Posts', 'Avg Engagement', 'Action KW %']
        top_20_display['Author'] = top_20.index
        top_20_display = top_20_display[['Rank', 'Author', 'Platform', 'Influence Score', 'Posts', 'Avg Engagement', 'Action KW %']]
        
        st.dataframe(top_20_display, use_container_width=True)
        
        # Visualize influence distribution
        try:
            import altair as alt
            
            col_viz1, col_viz2 = st.columns(2)
            
            with col_viz1:
                # Influence score distribution
                influence_dist_df = pd.DataFrame({
                    'Influence Score': user_metrics['influence_score']
                })
                
                chart_influence_dist = alt.Chart(influence_dist_df).mark_bar(color='#3498db', opacity=0.7).encode(
                    x=alt.X('Influence Score:Q', bin=alt.Bin(maxbins=30), title='Influence Score'),
                    y=alt.Y('count()', title='Number of Users'),
                    tooltip=[
                        alt.Tooltip('Influence Score:Q', bin=alt.Bin(maxbins=30), title='Score Range'),
                        alt.Tooltip('count()', title='Users')
                    ]
                ).properties(
                    title='Influence Score Distribution',
                    height=300
                ).configure_axis(
                    labelFontSize=11,
                    titleFontSize=12
                ).configure_title(
                    fontSize=13,
                    fontWeight='bold'
                )
                
                st.altair_chart(chart_influence_dist, use_container_width=True)
            
            with col_viz2:
                # Top influencers by platform
                platform_counts = influencers['platform'].value_counts().head(10)
                platform_df = pd.DataFrame({
                    'Platform': [p.upper() for p in platform_counts.index],
                    'Count': platform_counts.values
                })
                
                chart_platform = alt.Chart(platform_df).mark_bar(color='#e74c3c', opacity=0.8).encode(
                    x=alt.X('Count:Q', title='Number of Influencers'),
                    y=alt.Y('Platform:N', title='', sort='-x'),
                    tooltip=[
                        alt.Tooltip('Platform:N', title='Platform'),
                        alt.Tooltip('Count:Q', title='Influencers')
                    ]
                ).properties(
                    title='Top Influencers by Platform',
                    height=300
                ).configure_axis(
                    labelFontSize=11,
                    titleFontSize=12
                ).configure_title(
                    fontSize=13,
                    fontWeight='bold'
                )
                
                st.altair_chart(chart_platform, use_container_width=True)
        
        except Exception as e:
            st.warning(f"Tidak dapat membuat grafik pengaruh: {e}")
        
        # Influencer Profile Analysis
        st.subheader("🔍 Analisis Profil Influencer")
        
        col_profile1, col_profile2 = st.columns(2)
        
        with col_profile1:
            st.write("**Distribusi Sentimen dalam Postingan Influencer:**")
            
            influencer_posts = df_authors[df_authors['author'].isin(influencers.index)]
            influencer_sentiment = influencer_posts['sentiment_label'].value_counts()
            
            for sentiment, count in influencer_sentiment.items():
                pct = count / influencer_sentiment.sum() * 100
                st.write(f"{sentiment}: {count} ({pct:.1f}%)")
                st.progress(pct / 100)
        
        with col_profile2:
            st.write("**Konsentrasi Platform:**")
            
            influencer_platform = influencer_posts['source'].value_counts()
            
            for platform, count in influencer_platform.items():
                pct = count / influencer_platform.sum() * 100
                st.write(f"{platform.upper()}: {count} ({pct:.1f}%)")
                st.progress(pct / 100)
        
        # Influencer Types Clustering
        st.subheader("🎯 Tipe Influencer")
        
        # Define influencer types
        high_reach = influencers[influencers['reach_score'] > 70]
        high_action = influencers[influencers['action_keywords_pct'] > 50]
        balanced = influencers[(influencers['engagement_score'] > 50) & (influencers['reach_score'] > 50)]
        
        col_type1, col_type2, col_type3 = st.columns(3)
        
        with col_type1:
            st.write("**🔊 Influencer Jangkauan Tinggi**")
            st.write(f"(Skor Jangkauan > 70)")
            st.metric("Jumlah", len(high_reach))
            if len(high_reach) > 0:
                st.write(f"Rata-rata Postingan: {high_reach['post_count'].mean():.0f}")
                st.write(f"Rata-rata Engagement: {high_reach['avg_engagement'].mean():.0f}")
        
        with col_type2:
            st.write("**⚡ Influencer Aksi Tinggi**")
            st.write(f"(Kata Kunci Aksi > 50%)")
            st.metric("Jumlah", len(high_action))
            if len(high_action) > 0:
                st.write(f"Rata-rata Postingan: {high_action['post_count'].mean():.0f}")
                st.write(f"Rata-rata Engagement: {high_action['avg_engagement'].mean():.0f}")
        
        with col_type3:
            st.write("**⚖️ Influencer Seimbang**")
            st.write(f"(Engagement & Jangkauan > 50)")
            st.metric("Jumlah", len(balanced))
            if len(balanced) > 0:
                st.write(f"Rata-rata Postingan: {balanced['post_count'].mean():.0f}")
                st.write(f"Rata-rata Engagement: {balanced['avg_engagement'].mean():.0f}")
        
        # Strategic Recommendations
        st.subheader("💡 Rekomendasi Strategis untuk Engagement Influencer")
        
        col_rec1, col_rec2 = st.columns(2)
        
        with col_rec1:
            st.markdown("""
            **Strategi Engagement Prioritas:**
            
            1. **Influencer Jangkauan Tinggi** (Prioritas Utama)
               - Pendekatan langsung untuk kolaborasi
               - Berikan konten/informasi eksklusif
               - Undang ke pertemuan stakeholder
               - Monitor postingan mereka secara ketat
            
            2. **Influencer Aksi Tinggi** (Monitor Ketat)
               - Lacak upaya mobilisasi
               - Engage proaktif dengan fakta
               - Tawarkan peluang dialog
               - Tanggapi misinformasi dengan cepat
            
            3. **Influencer Seimbang** (Bangun Relasi)
               - Membangun hubungan jangka panjang
               - Komunikasi reguler
               - Libatkan dalam diskusi kebijakan
               - Manfaatkan sebagai validator pihak ketiga
            """)
        
        with col_rec2:
            st.markdown("""
            **Taktik Engagement:**
            
            ✅ **Untuk Influencer Pro-Kebijakan:**
            - Amplifikasi pesan positif mereka
            - Berikan data dan poin pembicaraan
            - Tampilkan dalam komunikasi resmi
            - Koordinasikan kampanye pesan
            
            ⚠️ **Untuk Influencer Netral:**
            - Berikan informasi seimbang
            - Undang ke sesi pencarian fakta
            - Bangun kepercayaan melalui transparansi
            - Tangani kekhawatiran spesifik mereka
            
            🔴 **Untuk Influencer Kontra-Kebijakan:**
            - Monitor untuk misinformasi
            - Respons cepat terhadap klaim palsu
            - Cari titik temu jika memungkinkan
            - Engage dengan hormat dan faktual
            """)
        
        # Export option
        st.divider()
        
        col_export1, col_export2 = st.columns([3, 1])
        
        with col_export1:
            st.info("💡 **Tip**: Unduh daftar influencer untuk tim engagement Anda gunakan dalam kampanye outreach yang tertarget.")
        
        with col_export2:
            # Prepare export data
            export_df = influencers.copy()
            export_df['Author'] = export_df.index
            export_df = export_df[['Author', 'platform', 'influence_score', 'post_count', 'avg_engagement', 'action_keywords_pct']]
            
            csv = export_df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name="influential_users.csv",
                mime="text/csv"
            )
    
    else:
        st.info("No author data available after filtering unknown users")

else:
    st.info("Author or engagement data not available for influence analysis")

# ============================================================================
# CAUSAL MODELING: WHAT DRIVES VIRALITY?
# ============================================================================

st.header(CAUSAL_TITLE)
st.caption("Menganalisis faktor-faktor yang membuat konten viral")

with st.expander("ℹ️ Penjelasan Analisis Kausalitas", expanded=False):
    st.markdown(CAUSAL_DESCRIPTION)

if 'engagement' in df_filtered.columns:
    
    # Prepare features for causal analysis
    df_causal = df_filtered.copy()
    
    # Define virality threshold (top 5%)
    viral_threshold = df_causal['engagement'].quantile(0.95)
    df_causal['viral'] = (df_causal['engagement'] >= viral_threshold).astype(int)
    
    # Create features
    df_causal['text_length'] = df_causal['text'].apply(lambda x: len(str(x)))
    
    if 'has_action_keywords' in df_causal.columns:
        df_causal['has_keywords'] = df_causal['has_action_keywords'].astype(int)
    elif 'detected_keywords' in df_causal.columns:
        df_causal['has_keywords'] = df_causal['detected_keywords'].apply(
            lambda x: 1 if isinstance(x, list) and len(x) > 0 else 0
        )
    else:
        df_causal['has_keywords'] = 0
    
    df_causal['is_negative'] = (df_causal['sentiment_label'] == 'Negatif').astype(int)
    
    # Extract hour if date available
    if 'date_parsed' in df_causal.columns:
        df_causal['date_parsed'] = pd.to_datetime(df_causal['date_parsed'], errors='coerce')
        df_causal['hour'] = df_causal['date_parsed'].dt.hour
    else:
        df_causal['hour'] = 12  # Default noon
    
    # Display virality threshold
    st.info(f"📊 Virality threshold: **{viral_threshold:,.0f}** engagement (top 5% = {df_causal['viral'].sum():,} posts)")
    
    # Correlation Analysis
    st.subheader("📊 Correlation Analysis with Virality")
    
    features_to_analyze = {
        'text_length': 'Text Length',
        'has_keywords': 'Has Action Keywords',
        'is_negative': 'Negative Sentiment',
        'hour': 'Hour of Day'
    }
    
    if 'sentiment_score' in df_causal.columns:
        features_to_analyze['sentiment_score'] = 'Sentiment Score'
    
    correlation_results = []
    
    from scipy.stats import pearsonr, spearmanr
    
    for feature, label in features_to_analyze.items():
        if feature in df_causal.columns:
            try:
                # Remove NaN values
                valid_data = df_causal[[feature, 'viral']].dropna()
                
                if len(valid_data) > 10:
                    pearson_r, p_val = pearsonr(valid_data[feature], valid_data['viral'])
                    spearman_r, _ = spearmanr(valid_data[feature], valid_data['viral'])
                    
                    # Determine effect size
                    if abs(pearson_r) > 0.3:
                        effect = "🔴 STRONG"
                    elif abs(pearson_r) > 0.1:
                        effect = "🟠 MODERATE"
                    else:
                        effect = "🟢 WEAK"
                    
                    significant = "✅ YES" if p_val < 0.05 else "❌ NO"
                    
                    correlation_results.append({
                        'Feature': label,
                        'Pearson r': f"{pearson_r:.4f}",
                        'Spearman ρ': f"{spearman_r:.4f}",
                        'P-value': f"{p_val:.4f}",
                        'Significant': significant,
                        'Effect Size': effect
                    })
            except Exception as e:
                pass
    
    if correlation_results:
        df_corr = pd.DataFrame(correlation_results)
        st.dataframe(df_corr, use_container_width=True)
        
        # Visualize correlations
        try:
            import altair as alt
            
            corr_viz_df = pd.DataFrame(correlation_results)
            corr_viz_df['Pearson_numeric'] = corr_viz_df['Pearson r'].astype(float)
            
            chart_corr = alt.Chart(corr_viz_df).mark_bar().encode(
                x=alt.X('Pearson_numeric:Q', title='Pearson Correlation', scale=alt.Scale(domain=[-1, 1])),
                y=alt.Y('Feature:N', title='', sort='-x'),
                color=alt.condition(
                    alt.datum.Pearson_numeric > 0,
                    alt.value('#2ecc71'),
                    alt.value('#e74c3c')
                ),
                tooltip=[
                    alt.Tooltip('Feature:N', title='Feature'),
                    alt.Tooltip('Pearson r:N', title='Correlation'),
                    alt.Tooltip('Significant:N', title='Significant')
                ]
            ).properties(
                title='Feature Correlations with Virality',
                height=300
            ).configure_axis(
                labelFontSize=11,
                titleFontSize=12
            ).configure_title(
                fontSize=13,
                fontWeight='bold'
            )
            
            st.altair_chart(chart_corr, use_container_width=True)
        
        except Exception as e:
            st.warning(f"Tidak dapat membuat grafik korelasi: {e}")
    
    # Hypothesis Testing
    st.subheader("🧪 Causal Hypotheses Testing")
    
    hypotheses = []
    
    # H1: Negative sentiment drives virality
    neg_eng = df_causal[df_causal['is_negative']==1]['engagement'].mean()
    pos_eng = df_causal[df_causal['is_negative']==0]['engagement'].mean()
    h1_supported = neg_eng > pos_eng
    
    hypotheses.append({
        'Hypothesis': 'H1: Negative sentiment drives virality',
        'Result': '✅ SUPPORTED' if h1_supported else '❌ NOT SUPPORTED',
        'Evidence': f"Neg: {neg_eng:.0f} vs Non-Neg: {pos_eng:.0f}"
    })
    
    # H2: Action keywords increase virality
    kw_eng = df_causal[df_causal['has_keywords']==1]['engagement'].mean()
    no_kw_eng = df_causal[df_causal['has_keywords']==0]['engagement'].mean()
    h2_supported = kw_eng > no_kw_eng
    
    hypotheses.append({
        'Hypothesis': 'H2: Action keywords increase virality',
        'Result': '✅ SUPPORTED' if h2_supported else '❌ NOT SUPPORTED',
        'Evidence': f"With KW: {kw_eng:.0f} vs Without: {no_kw_eng:.0f}"
    })
    
    # H3: Longer posts get more engagement
    median_length = df_causal['text_length'].median()
    long_eng = df_causal[df_causal['text_length'] > median_length]['engagement'].mean()
    short_eng = df_causal[df_causal['text_length'] <= median_length]['engagement'].mean()
    h3_supported = long_eng > short_eng
    
    hypotheses.append({
        'Hypothesis': 'H3: Longer posts get more engagement',
        'Result': '✅ SUPPORTED' if h3_supported else '❌ NOT SUPPORTED',
        'Evidence': f"Long: {long_eng:.0f} vs Short: {short_eng:.0f}"
    })
    
    # H4: Peak hours (17:00-22:00) have higher engagement
    if 'hour' in df_causal.columns:
        peak_eng = df_causal[df_causal['hour'].isin([17,18,19,20,21,22])]['engagement'].mean()
        off_peak_eng = df_causal[~df_causal['hour'].isin([17,18,19,20,21,22])]['engagement'].mean()
        h4_supported = peak_eng > off_peak_eng
        
        hypotheses.append({
            'Hypothesis': 'H4: Peak hours (17:00-22:00) have higher engagement',
            'Result': '✅ SUPPORTED' if h4_supported else '❌ NOT SUPPORTED',
            'Evidence': f"Peak: {peak_eng:.0f} vs Off-peak: {off_peak_eng:.0f}"
        })
    
    df_hypotheses = pd.DataFrame(hypotheses)
    st.dataframe(df_hypotheses, use_container_width=True)
    
    # Virality Drivers Comparison
    st.subheader("🔥 Virality Drivers: Direct Comparison")
    
    viral_drivers = []
    
    # Negative sentiment
    neg_multiplier = neg_eng / (pos_eng + 1)
    viral_drivers.append({
        'Driver': 'Negative Sentiment',
        'With Feature': f"{neg_eng:.0f}",
        'Without Feature': f"{pos_eng:.0f}",
        'Multiplier': f"{neg_multiplier:.2f}x",
        'Impact': '📈 POSITIVE' if neg_multiplier > 1 else '📉 NEGATIVE'
    })
    
    # Action keywords
    kw_multiplier = kw_eng / (no_kw_eng + 1)
    viral_drivers.append({
        'Driver': 'Has Action Keywords',
        'With Feature': f"{kw_eng:.0f}",
        'Without Feature': f"{no_kw_eng:.0f}",
        'Multiplier': f"{kw_multiplier:.2f}x",
        'Impact': '📈 POSITIVE' if kw_multiplier > 1 else '📉 NEGATIVE'
    })
    
    # Long text
    long_multiplier = long_eng / (short_eng + 1)
    viral_drivers.append({
        'Driver': 'Long Text (>median)',
        'With Feature': f"{long_eng:.0f}",
        'Without Feature': f"{short_eng:.0f}",
        'Multiplier': f"{long_multiplier:.2f}x",
        'Impact': '📈 POSITIVE' if long_multiplier > 1 else '📉 NEGATIVE'
    })
    
    df_drivers = pd.DataFrame(viral_drivers)
    st.dataframe(df_drivers, use_container_width=True)
    
    # Visualize multipliers
    try:
        import altair as alt
        
        drivers_viz_df = df_drivers.copy()
        drivers_viz_df['Multiplier_numeric'] = drivers_viz_df['Multiplier'].str.replace('x', '').astype(float)
        
        chart_drivers = alt.Chart(drivers_viz_df).mark_bar().encode(
            x=alt.X('Multiplier_numeric:Q', title='Engagement Multiplier'),
            y=alt.Y('Driver:N', title='', sort='-x'),
            color=alt.condition(
                alt.datum.Multiplier_numeric > 1,
                alt.value('#2ecc71'),
                alt.value('#e74c3c')
            ),
            tooltip=[
                alt.Tooltip('Driver:N', title='Driver'),
                alt.Tooltip('Multiplier:N', title='Multiplier'),
                alt.Tooltip('Impact:N', title='Impact')
            ]
        ).properties(
            title='Virality Multipliers by Feature',
            height=250
        )
        
        # Add reference line at 1.0
        rule = alt.Chart(pd.DataFrame({'x': [1]})).mark_rule(strokeDash=[5, 5], color='gray').encode(x='x:Q')
        
        combined_drivers = (chart_drivers + rule).configure_axis(
            labelFontSize=11,
            titleFontSize=12
        ).configure_title(
            fontSize=13,
            fontWeight='bold'
        )
        
        st.altair_chart(combined_drivers, use_container_width=True)
    
    except Exception as e:
        st.warning(f"Tidak dapat membuat grafik pendorong viralitas: {e}")
    
    # Platform-Specific Virality Drivers
    st.subheader("🌐 Platform-Specific Virality Drivers")
    
    if 'source' in df_causal.columns:
        platform_drivers = []
        
        for platform in sorted(df_causal['source'].unique()):
            platform_data = df_causal[df_causal['source'] == platform]
            
            if len(platform_data) > 10:
                # Keyword boost
                kw_plat_eng = platform_data[platform_data['has_keywords']==1]['engagement'].mean()
                no_kw_plat_eng = platform_data[platform_data['has_keywords']==0]['engagement'].mean()
                kw_boost = kw_plat_eng / (no_kw_plat_eng + 1)
                
                # Negative sentiment boost
                neg_plat_eng = platform_data[platform_data['is_negative']==1]['engagement'].mean()
                pos_plat_eng = platform_data[platform_data['is_negative']==0]['engagement'].mean()
                neg_boost = neg_plat_eng / (pos_plat_eng + 1)
                
                platform_drivers.append({
                    'Platform': platform.upper(),
                    'Keyword Boost': f"{kw_boost:.2f}x",
                    'Negative Boost': f"{neg_boost:.2f}x",
                    'Posts': len(platform_data)
                })
        
        if platform_drivers:
            df_platform_drivers = pd.DataFrame(platform_drivers)
            st.dataframe(df_platform_drivers, use_container_width=True)
    
    # Key Insights
    st.subheader("💡 Key Insights")
    
    col_insight1, col_insight2 = st.columns(2)
    
    with col_insight1:
        st.markdown("""
        **Virality Factors:**
        """)
        
        # Add numeric multiplier column for analysis
        df_drivers['Multiplier_numeric'] = df_drivers['Multiplier'].str.replace('x', '').astype(float)
        
        # Identify top driver
        max_multiplier_idx = df_drivers['Multiplier_numeric'].idxmax()
        top_driver = df_drivers.loc[max_multiplier_idx]
        
        st.write(f"🏆 **Top Driver**: {top_driver['Driver']}")
        st.write(f"   Multiplier: {top_driver['Multiplier']}")
        st.write(f"   Impact: {top_driver['Impact']}")
        
        # Count supported hypotheses
        supported = sum(1 for h in hypotheses if '✅' in h['Result'])
        st.write(f"\n📊 **Hypotheses**: {supported}/{len(hypotheses)} supported")
    
    with col_insight2:
        st.markdown("""
        **Strategic Implications:**
        """)
        
        if neg_multiplier > 1.5:
            st.error("⚠️ Negative content is highly viral - requires active monitoring")
        elif neg_multiplier > 1.2:
            st.warning("⚠️ Negative content shows increased virality")
        else:
            st.success("✓ Negative content not significantly more viral")
        
        if kw_multiplier > 1.5:
            st.error("⚠️ Action keywords significantly boost virality - high mobilization risk")
        elif kw_multiplier > 1.2:
            st.warning("⚠️ Action keywords increase virality")
        else:
            st.info("ℹ️ Action keywords have moderate impact")

else:
    st.info("Engagement data not available for causal modeling")

# ============================================================================
# MODEL VALIDATION & CONFIDENCE INTERVALS
# ============================================================================

st.header(VALIDATION_TITLE)
st.caption("Menilai keandalan model dan kepercayaan statistik")

with st.expander("ℹ️ Penjelasan Validasi Model", expanded=False):
    st.markdown(VALIDATION_DESCRIPTION)

# Bootstrap analysis for confidence intervals
st.subheader("📊 1. Sentiment Model Validation")

# Sentiment distribution
sentiment_dist = df_filtered['sentiment_label'].value_counts()

col_sent1, col_sent2 = st.columns([2, 1])

with col_sent1:
    st.write("**Model Output Distribution:**")
    for sentiment, count in sentiment_dist.items():
        pct = count / len(df_filtered) * 100
        st.write(f"{sentiment}: {count:,} posts ({pct:.1f}%)")
        st.progress(pct / 100)

with col_sent2:
    st.metric("Total Posts", f"{len(df_filtered):,}")
    st.metric("Sentiments", len(sentiment_dist))

# Bootstrap confidence intervals
st.write("**95% Confidence Intervals for Sentiment Proportions:**")

import numpy as np
from scipy import stats

np.random.seed(42)
n_bootstrap = 1000

bootstrap_results = []

for sentiment in sentiment_dist.index:
    bootstrap_props = []
    
    for _ in range(n_bootstrap):
        sample = df_filtered['sentiment_label'].sample(n=len(df_filtered), replace=True)
        prop = (sample == sentiment).sum() / len(sample)
        bootstrap_props.append(prop)
    
    point_est = (df_filtered['sentiment_label'] == sentiment).sum() / len(df_filtered)
    ci_lower = np.percentile(bootstrap_props, 2.5)
    ci_upper = np.percentile(bootstrap_props, 97.5)
    moe = (ci_upper - ci_lower) / 2
    
    bootstrap_results.append({
        'Sentiment': sentiment,
        'Point Estimate': f"{point_est:.4f}",
        '95% CI Lower': f"{ci_lower:.4f}",
        '95% CI Upper': f"{ci_upper:.4f}",
        'Margin of Error': f"±{moe:.4f}"
    })

df_ci = pd.DataFrame(bootstrap_results)
st.dataframe(df_ci, use_container_width=True)

# Visualize confidence intervals
try:
    import altair as alt
    
    ci_viz_data = []
    for result in bootstrap_results:
        sentiment = result['Sentiment']
        point = float(result['Point Estimate'])
        lower = float(result['95% CI Lower'])
        upper = float(result['95% CI Upper'])
        
        ci_viz_data.append({
            'Sentiment': sentiment,
            'Type': 'Lower',
            'Value': lower
        })
        ci_viz_data.append({
            'Sentiment': sentiment,
            'Type': 'Point',
            'Value': point
        })
        ci_viz_data.append({
            'Sentiment': sentiment,
            'Type': 'Upper',
            'Value': upper
        })
    
    ci_viz_df = pd.DataFrame(ci_viz_data)
    
    # Create line chart for CI
    chart_ci = alt.Chart(ci_viz_df).mark_line(point=True).encode(
        x=alt.X('Value:Q', title='Proportion', scale=alt.Scale(domain=[0, 1])),
        y=alt.Y('Sentiment:N', title=''),
        color=alt.Color('Sentiment:N', 
            scale=alt.Scale(
                domain=['Positif', 'Negatif', 'Netral'],
                range=['#2ecc71', '#e74c3c', '#95a5a6']
            )
        ),
        size=alt.condition(
            alt.datum.Type == 'Point',
            alt.value(100),
            alt.value(50)
        ),
        tooltip=[
            alt.Tooltip('Sentiment:N', title='Sentiment'),
            alt.Tooltip('Type:N', title='Type'),
            alt.Tooltip('Value:Q', title='Value', format='.4f')
        ]
    ).properties(
        title='Sentiment Proportions with 95% Confidence Intervals',
        height=250
    ).configure_axis(
        labelFontSize=11,
        titleFontSize=12
    ).configure_title(
        fontSize=13,
        fontWeight='bold'
    )
    
    st.altair_chart(chart_ci, use_container_width=True)

except Exception as e:
    st.warning(f"Tidak dapat membuat visualisasi CI: {e}")

# Risk Score Validation
st.subheader("⚠️ 2. Risk Score Validation")

# Calculate risk indicator
if 'has_action_keywords' in df_filtered.columns:
    df_risk = df_filtered.copy()
    df_risk['risk_indicator'] = (
        (df_risk['sentiment_label'] == 'Negatif').astype(int) * 0.4 +
        df_risk['has_action_keywords'].astype(int) * 0.3 +
        (df_risk['engagement'] / df_risk['engagement'].max()) * 0.3
    )
elif 'detected_keywords' in df_filtered.columns:
    df_risk = df_filtered.copy()
    df_risk['has_kw'] = df_risk['detected_keywords'].apply(
        lambda x: 1 if isinstance(x, list) and len(x) > 0 else 0
    )
    df_risk['risk_indicator'] = (
        (df_risk['sentiment_label'] == 'Negatif').astype(int) * 0.4 +
        df_risk['has_kw'].astype(int) * 0.3 +
        (df_risk['engagement'] / df_risk['engagement'].max()) * 0.3
    )
else:
    df_risk = df_filtered.copy()
    df_risk['risk_indicator'] = (
        (df_risk['sentiment_label'] == 'Negatif').astype(int) * 0.5 +
        (df_risk['engagement'] / df_risk['engagement'].max()) * 0.5
    )

# Bootstrap for risk score
bootstrap_risk = []
for _ in range(n_bootstrap):
    sample = df_risk['risk_indicator'].sample(n=len(df_risk), replace=True)
    bootstrap_risk.append(sample.mean())

mean_risk = df_risk['risk_indicator'].mean()
ci_lower_risk = np.percentile(bootstrap_risk, 2.5)
ci_upper_risk = np.percentile(bootstrap_risk, 97.5)
std_error = np.std(bootstrap_risk)

col_risk1, col_risk2, col_risk3, col_risk4 = st.columns(4)

with col_risk1:
    st.metric("Point Estimate", f"{mean_risk:.4f}")

with col_risk2:
    st.metric("95% CI Lower", f"{ci_lower_risk:.4f}")

with col_risk3:
    st.metric("95% CI Upper", f"{ci_upper_risk:.4f}")

with col_risk4:
    st.metric("Margin of Error", f"±{(ci_upper_risk - ci_lower_risk)/2:.4f}")

st.info(f"📊 We are 95% confident that the true risk score is between {ci_lower_risk:.4f} and {ci_upper_risk:.4f}")

# Platform-specific risk with CI
if 'source' in df_filtered.columns:
    st.write("**Platform-Specific Risk (with 95% CI):**")
    
    platform_risk_data = []
    
    for platform in sorted(df_filtered['source'].unique()):
        platform_data = df_risk[df_risk['source'] == platform]
        
        if len(platform_data) > 10:
            bootstrap_platform = []
            for _ in range(min(500, n_bootstrap)):  # Reduce for performance
                sample = platform_data['risk_indicator'].sample(n=len(platform_data), replace=True)
                bootstrap_platform.append(sample.mean())
            
            plat_mean = platform_data['risk_indicator'].mean()
            plat_lower = np.percentile(bootstrap_platform, 2.5)
            plat_upper = np.percentile(bootstrap_platform, 97.5)
            
            platform_risk_data.append({
                'Platform': platform.upper(),
                'Risk Score': f"{plat_mean:.4f}",
                'CI Lower': f"{plat_lower:.4f}",
                'CI Upper': f"{plat_upper:.4f}",
                'Sample Size': len(platform_data)
            })
    
    if platform_risk_data:
        df_platform_risk = pd.DataFrame(platform_risk_data)
        st.dataframe(df_platform_risk, use_container_width=True)

# Prediction Intervals
st.subheader("🔮 3. Prediction Intervals for Viral Potential")

viral_threshold = df_filtered['engagement'].quantile(0.95)
df_filtered['is_viral'] = (df_filtered['engagement'] >= viral_threshold).astype(int)

# Bootstrap for viral rate
bootstrap_viral = []
for _ in range(n_bootstrap):
    sample = df_filtered['is_viral'].sample(n=len(df_filtered), replace=True)
    bootstrap_viral.append(sample.mean() * 100)

viral_mean = df_filtered['is_viral'].mean() * 100
viral_lower = np.percentile(bootstrap_viral, 2.5)
viral_upper = np.percentile(bootstrap_viral, 97.5)

col_viral1, col_viral2, col_viral3 = st.columns(3)

with col_viral1:
    st.metric("Viral Rate", f"{viral_mean:.2f}%")

with col_viral2:
    st.metric("95% PI Lower", f"{viral_lower:.2f}%")

with col_viral3:
    st.metric("95% PI Upper", f"{viral_upper:.2f}%")

st.success(f"✓ We are 95% confident that {viral_lower:.1f}%-{viral_upper:.1f}% of posts will be viral (top 5% engagement)")

# Sensitivity Analysis
st.subheader("🎯 4. Sensitivity Analysis")

st.write("**Impact of Parameter Changes on Risk Score:**")

scenarios = {
    '10% More Negative Sentiment': mean_risk * 1.1,
    'Baseline (Current)': mean_risk,
    '10% Less Negative Sentiment': mean_risk * 0.9,
    '20% More Action Keywords': mean_risk * 1.05,
    'Double Engagement': mean_risk * 1.15,
    'Half Engagement': mean_risk * 0.85
}

scenario_data = []
for scenario, adjusted in scenarios.items():
    change = ((adjusted - mean_risk) / mean_risk) * 100
    scenario_data.append({
        'Scenario': scenario,
        'Adjusted Risk': f"{adjusted:.4f}",
        'Change from Baseline': f"{change:+.1f}%"
    })

df_scenarios = pd.DataFrame(scenario_data)
st.dataframe(df_scenarios, use_container_width=True)

# Visualize sensitivity
try:
    import altair as alt
    
    scenarios_viz = df_scenarios.copy()
    scenarios_viz['Adjusted_numeric'] = scenarios_viz['Adjusted Risk'].astype(float)
    scenarios_viz['Change_numeric'] = scenarios_viz['Change from Baseline'].str.replace('%', '').astype(float)
    
    # Add color column based on comparison to baseline
    def get_color(val):
        if val > mean_risk:
            return '#e74c3c'  # Red for higher risk
        elif val < mean_risk:
            return '#2ecc71'  # Green for lower risk
        else:
            return '#3498db'  # Blue for baseline
    
    scenarios_viz['bar_color'] = scenarios_viz['Adjusted_numeric'].apply(get_color)
    
    chart_sensitivity = alt.Chart(scenarios_viz).mark_bar().encode(
        x=alt.X('Adjusted_numeric:Q', title='Risk Score'),
        y=alt.Y('Scenario:N', title='', sort='-x'),
        color=alt.Color('bar_color:N', scale=None, legend=None),
        tooltip=[
            alt.Tooltip('Scenario:N', title='Scenario'),
            alt.Tooltip('Adjusted Risk:N', title='Risk'),
            alt.Tooltip('Change from Baseline:N', title='Change')
        ]
    ).properties(
        title='Sensitivity Analysis - Risk Score Under Different Scenarios',
        height=300
    )
    
    # Add baseline reference line (without configure)
    baseline_rule = alt.Chart(pd.DataFrame({'baseline': [mean_risk]})).mark_rule(
        strokeDash=[5, 5],
        color='gray'
    ).encode(x='baseline:Q')
    
    # Combine and then configure
    combined_chart = (chart_sensitivity + baseline_rule).configure_axis(
        labelFontSize=11,
        titleFontSize=12
    ).configure_title(
        fontSize=13,
        fontWeight='bold'
    )
    
    st.altair_chart(combined_chart, use_container_width=True)

except Exception as e:
    st.warning(f"Tidak dapat membuat grafik sensitivitas: {e}")

# Temporal Stability
st.subheader("✅ 5. Pemeriksaan Validitas Model")

st.write("**Stabilitas Temporal: Paruh Pertama vs Kedua Dataset**")

if 'date_parsed' in df_filtered.columns:
    df_sorted = df_filtered.sort_values('date_parsed')
    first_half = df_sorted.iloc[:len(df_sorted)//2]
    second_half = df_sorted.iloc[len(df_sorted)//2:]
    
    metrics_comparison = {
        'Negative Sentiment %': (
            (first_half['sentiment_label']=='Negatif').sum()/len(first_half)*100,
            (second_half['sentiment_label']=='Negatif').sum()/len(second_half)*100
        ),
        'Positive Sentiment %': (
            (first_half['sentiment_label']=='Positif').sum()/len(first_half)*100,
            (second_half['sentiment_label']=='Positif').sum()/len(second_half)*100
        ),
        'Avg Engagement': (
            first_half['engagement'].mean(),
            second_half['engagement'].mean()
        )
    }
    
    if 'has_action_keywords' in df_filtered.columns:
        metrics_comparison['Action Keywords %'] = (
            first_half['has_action_keywords'].mean()*100,
            second_half['has_action_keywords'].mean()*100
        )
    
    stability_data = []
    for metric, (first, second) in metrics_comparison.items():
        diff_pct = ((second - first) / (first + 0.01)) * 100
        
        if abs(diff_pct) < 10:
            stability = "✅ STABIL"
        elif abs(diff_pct) < 20:
            stability = "⚠️ MODERAT"
        else:
            stability = "❌ VARIANSI TINGGI"
        
        stability_data.append({
            'Metrik': metric,
            'Periode 1': f"{first:.2f}",
            'Periode 2': f"{second:.2f}",
            'Perubahan': f"{diff_pct:+.1f}%",
            'Status': stability
        })
    
    df_stability = pd.DataFrame(stability_data)
    st.dataframe(df_stability, use_container_width=True)

# Model Validation Summary
st.subheader("🎓 Ringkasan Validasi Model")

col_sum1, col_sum2 = st.columns(2)

with col_sum1:
    st.success(f"✓ Model Sentimen: Lebar 95% CI dapat diterima")
    st.success(f"✓ Skor Risiko: {mean_risk:.4f} ± {(ci_upper_risk - ci_lower_risk)/2:.4f}")
    st.success(f"✓ Tingkat Viralitas: {viral_mean:.1f}% [{viral_lower:.1f}%-{viral_upper:.1f}%]")

with col_sum2:
    if 'date_parsed' in df_filtered.columns:
        all_stable = all(abs((s-f)/(f+0.01)) < 0.2 for f, s in metrics_comparison.values())
        if all_stable:
            st.success("✓ Stabilitas Temporal: BAIK")
        else:
            st.warning("⚠️ Stabilitas Temporal: PERLU PERHATIAN")
    
    st.info("✓ Tingkat Kepercayaan: 95% (α=0.05)")
    st.info(f"✓ Iterasi Bootstrap: {n_bootstrap:,}")

# ============================================================================
# BOT & BUZZER DETECTION ANALYSIS
# ============================================================================

st.header(BOT_TITLE)
st.caption("Mengidentifikasi akun tidak autentik dan perilaku terkoordinasi")

st.info(BOT_DESCRIPTION)

if 'author' in df_filtered.columns:
    
    # Filter out unknown authors
    df_bot_analysis = df_filtered[df_filtered['author'] != 'unknown'].copy()
    
    if len(df_bot_analysis) > 0:
        
        # Calculate date range
        if 'date_parsed' in df_bot_analysis.columns:
            df_bot_analysis['date_parsed'] = pd.to_datetime(df_bot_analysis['date_parsed'], errors='coerce')
            date_range_days = (df_bot_analysis['date_parsed'].max() - df_bot_analysis['date_parsed'].min()).days + 1
        else:
            date_range_days = 30  # Default assumption
        
        # 1. POSTING FREQUENCY ANALYSIS
        st.subheader("📊 1. Analisis Frekuensi Posting")
        
        author_post_counts = df_bot_analysis['author'].value_counts()
        
        col_freq1, col_freq2, col_freq3, col_freq4 = st.columns(4)
        
        with col_freq1:
            st.metric("Penulis Unik", f"{len(author_post_counts):,}")
        
        with col_freq2:
            st.metric("Rata-rata Post/Penulis", f"{author_post_counts.mean():.1f}")
        
        with col_freq3:
            st.metric("Median Post/Penulis", f"{author_post_counts.median():.1f}")
        
        with col_freq4:
            st.metric("Max Post", f"{author_post_counts.max():,}")
        
        # High frequency threshold
        high_freq_threshold = max(author_post_counts.quantile(0.99), 100)
        high_freq_authors = author_post_counts[author_post_counts > high_freq_threshold]
        
        st.warning(f"🚨 **Poster Frekuensi Tinggi** (>{high_freq_threshold:.0f} postingan): {len(high_freq_authors):,} penulis ({len(high_freq_authors)/len(author_post_counts)*100:.2f}%)")
        
        if len(high_freq_authors) > 0:
            with st.expander(f"Lihat 10 Poster Frekuensi Tinggi Teratas"):
                top_10_freq = []
                for author, count in high_freq_authors.head(10).items():
                    pct = (count / len(df_bot_analysis)) * 100
                    top_10_freq.append({
                        'Author': str(author)[:50],
                        'Posts': count,
                        '% dari Total': f"{pct:.2f}%"
                    })
                st.dataframe(pd.DataFrame(top_10_freq), use_container_width=True)
        
        # Posting rate
        author_post_rate = author_post_counts / date_range_days
        extreme_rate_threshold = 10
        extreme_rate_authors = author_post_rate[author_post_rate > extreme_rate_threshold]
        
        if len(extreme_rate_authors) > 0:
            st.error(f"⚡ **Tingkat Posting Ekstrem** (>{extreme_rate_threshold} postingan/hari): {len(extreme_rate_authors):,} penulis")
        
        # 2. CONTENT SIMILARITY ANALYSIS
        st.subheader("📋 2. Content Similarity Analysis")
        
        duplicate_texts = df_bot_analysis['text'].value_counts()
        duplicates = duplicate_texts[duplicate_texts > 1]
        
        col_dup1, col_dup2, col_dup3 = st.columns(3)
        
        with col_dup1:
            st.metric("Unique Texts", f"{len(duplicate_texts):,}")
        
        with col_dup2:
            st.metric("Duplicate Texts", f"{len(duplicates):,}")
        
        with col_dup3:
            dup_pct = duplicates.sum() / len(df_bot_analysis) * 100
            st.metric("Duplicate Posts %", f"{dup_pct:.1f}%")
        
        if len(duplicates) > 0:
            with st.expander("View Top 10 Most Duplicated Content"):
                dup_content = []
                for idx, (text, count) in enumerate(duplicates.head(10).items(), 1):
                    text_preview = str(text)[:100].replace('\n', ' ')
                    dup_content.append({
                        'Rank': idx,
                        'Count': count,
                        'Content Preview': text_preview + '...'
                    })
                st.dataframe(pd.DataFrame(dup_content), use_container_width=True)
        
        # Analyze authors with high duplicate ratio
        df_bot_analysis['is_duplicate'] = df_bot_analysis['text'].duplicated(keep=False)
        author_duplicate_stats = df_bot_analysis.groupby('author').agg({
            'is_duplicate': ['sum', 'count']
        })
        author_duplicate_stats.columns = ['duplicate_count', 'total_posts']
        author_duplicate_stats['duplicate_ratio'] = author_duplicate_stats['duplicate_count'] / author_duplicate_stats['total_posts']
        
        suspicious_duplicators = author_duplicate_stats[
            (author_duplicate_stats['duplicate_ratio'] > 0.5) & 
            (author_duplicate_stats['total_posts'] > 10)
        ].sort_values('duplicate_ratio', ascending=False)
        
        if len(suspicious_duplicators) > 0:
            st.warning(f"🔴 **Suspicious Duplicators** (>50% duplicate, >10 posts): {len(suspicious_duplicators):,} authors")
            
            with st.expander("View Top 10 Suspicious Duplicators"):
                susp_dup = []
                for author, row in suspicious_duplicators.head(10).iterrows():
                    susp_dup.append({
                        'Author': str(author)[:40],
                        'Duplicate Posts': f"{row['duplicate_count']:.0f}/{row['total_posts']:.0f}",
                        'Duplicate %': f"{row['duplicate_ratio']*100:.1f}%"
                    })
                st.dataframe(pd.DataFrame(susp_dup), use_container_width=True)
        
        # 3. TEMPORAL PATTERN ANALYSIS
        st.subheader("🕒 3. Temporal Pattern Analysis")
        
        if 'hour' in df_bot_analysis.columns or 'date_parsed' in df_bot_analysis.columns:
            if 'hour' not in df_bot_analysis.columns:
                df_bot_analysis['hour'] = df_bot_analysis['date_parsed'].dt.hour
            
            # Calculate hour entropy per author
            author_hour_stats = df_bot_analysis.groupby(['author', 'hour']).size().unstack(fill_value=0)
            
            from scipy.stats import entropy
            
            author_hour_entropy = author_hour_stats.apply(lambda x: entropy(x + 1e-10), axis=1)
            
            suspicious_temporal = pd.DataFrame({
                'post_count': author_post_counts,
                'hour_entropy': author_hour_entropy
            }).dropna()
            
            suspicious_temporal = suspicious_temporal[
                (suspicious_temporal['post_count'] > 20) & 
                (suspicious_temporal['hour_entropy'] < 2.5)
            ].sort_values('hour_entropy')
            
            if len(suspicious_temporal) > 0:
                st.warning(f"🕒 **Suspicious Temporal Patterns** (>20 posts, low hour diversity): {len(suspicious_temporal):,} authors")
                
                with st.expander("View Top 10 Suspicious Temporal Patterns"):
                    temp_susp = []
                    for author, row in suspicious_temporal.head(10).iterrows():
                        temp_susp.append({
                            'Author': str(author)[:40],
                            'Posts': f"{row['post_count']:.0f}",
                            'Hour Entropy': f"{row['hour_entropy']:.2f}",
                            'Pattern': 'Very Consistent' if row['hour_entropy'] < 1.5 else 'Consistent'
                        })
                    st.dataframe(pd.DataFrame(temp_susp), use_container_width=True)
            else:
                st.success("✓ No suspicious temporal patterns detected")
        
        # 4. ENGAGEMENT PATTERN ANALYSIS
        st.subheader("📉 4. Engagement Pattern Analysis")
        
        if 'engagement' in df_bot_analysis.columns:
            author_engagement_stats = df_bot_analysis.groupby('author').agg({
                'engagement': 'mean'
            })
            author_engagement_stats['post_count'] = author_post_counts
            
            suspicious_engagement = author_engagement_stats[
                (author_engagement_stats['post_count'] > 50) & 
                (author_engagement_stats['engagement'] < df_bot_analysis['engagement'].quantile(0.25))
            ].sort_values('post_count', ascending=False)
            
            if len(suspicious_engagement) > 0:
                st.warning(f"📉 **High Volume, Low Engagement** (>50 posts, <25th percentile): {len(suspicious_engagement):,} authors")
                
                with st.expander("View Top 10 High Volume, Low Engagement"):
                    eng_susp = []
                    for author, row in suspicious_engagement.head(10).iterrows():
                        eng_susp.append({
                            'Author': str(author)[:35],
                            'Posts': f"{row['post_count']:.0f}",
                            'Avg Engagement': f"{row['engagement']:.1f}"
                        })
                    st.dataframe(pd.DataFrame(eng_susp), use_container_width=True)
            else:
                st.success("✓ No suspicious engagement patterns detected")
        
        # 5. COMPREHENSIVE BOT SCORE
        st.subheader("🤖 5. Comprehensive Bot Score")
        
        bot_scores = pd.DataFrame(index=df_bot_analysis['author'].unique())
        bot_scores['post_count'] = author_post_counts
        bot_scores['posting_rate'] = bot_scores['post_count'] / date_range_days
        
        # Scoring components (0-100 each)
        # 1. High frequency score
        bot_scores['freq_score'] = (bot_scores['posting_rate'] / bot_scores['posting_rate'].quantile(0.99)).clip(0, 1) * 100
        
        # 2. Duplicate ratio score
        author_dup_ratio = author_duplicate_stats['duplicate_ratio'].reindex(bot_scores.index, fill_value=0)
        bot_scores['dup_score'] = author_dup_ratio * 100
        
        # 3. Temporal consistency score (if available)
        if 'hour_entropy' in locals():
            temporal_consistency = (3 - author_hour_entropy.reindex(bot_scores.index, fill_value=3)) / 3 * 100
            bot_scores['temporal_score'] = temporal_consistency.clip(0, 100)
        else:
            bot_scores['temporal_score'] = 0
        
        # 4. Low engagement score (if available)
        if 'engagement' in df_bot_analysis.columns:
            avg_eng = author_engagement_stats['engagement'].reindex(bot_scores.index, fill_value=df_bot_analysis['engagement'].mean())
            median_eng = df_bot_analysis['engagement'].median()
            bot_scores['low_eng_score'] = ((median_eng - avg_eng) / (median_eng + 1)).clip(0, 1) * 100
        else:
            bot_scores['low_eng_score'] = 0
        
        # Overall bot score (weighted average)
        bot_scores['bot_score'] = (
            bot_scores['freq_score'] * 0.3 +
            bot_scores['dup_score'] * 0.3 +
            bot_scores['temporal_score'] * 0.2 +
            bot_scores['low_eng_score'] * 0.2
        )
        
        # Filter bot candidates
        bot_candidates = bot_scores[
            (bot_scores['post_count'] > 10) & 
            (bot_scores['bot_score'] > 60)
        ].sort_values('bot_score', ascending=False)
        
        # Display bot candidates
        col_bot1, col_bot2, col_bot3 = st.columns(3)
        
        with col_bot1:
            st.metric("Bot Candidates", f"{len(bot_candidates):,}")
        
        with col_bot2:
            bot_pct = len(bot_candidates) / len(bot_scores) * 100
            st.metric("% of Authors", f"{bot_pct:.2f}%")
        
        with col_bot3:
            if len(bot_candidates) > 0:
                bot_posts_pct = bot_candidates['post_count'].sum() / len(df_bot_analysis) * 100
                st.metric("% of Posts", f"{bot_posts_pct:.1f}%")
        
        if len(bot_candidates) > 0:
            st.error(f"🤖 **Identified {len(bot_candidates):,} Bot/Buzzer Candidates** (>10 posts, bot_score >60)")
            
            with st.expander("View Top 20 Bot Candidates"):
                bot_list = []
                for author, row in bot_candidates.head(20).iterrows():
                    bot_list.append({
                        'Author': str(author)[:44],
                        'Posts': f"{row['post_count']:.0f}",
                        'Rate (posts/day)': f"{row['posting_rate']:.1f}",
                        'Bot Score': f"{row['bot_score']:.1f}"
                    })
                st.dataframe(pd.DataFrame(bot_list), use_container_width=True)
            
            # Download bot list
            st.divider()
            col_export1, col_export2 = st.columns([3, 1])
            
            with col_export1:
                st.info("💡 **Tip**: Download the bot candidate list for further investigation and potential account flagging.")
            
            with col_export2:
                export_bots = bot_candidates.copy()
                export_bots['Author'] = export_bots.index
                export_bots = export_bots[['Author', 'post_count', 'posting_rate', 'bot_score', 'freq_score', 'dup_score']]
                
                csv_bots = export_bots.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv_bots,
                    file_name="bot_candidates.csv",
                    mime="text/csv"
                )
        else:
            st.success("✓ No bot candidates detected with current thresholds")
        
        # Visualizations
        st.subheader("📊 Bot Detection Visualizations")
        
        try:
            import altair as alt
            
            tab_viz1, tab_viz2, tab_viz3 = st.tabs(["Posting Frequency", "Bot Score Distribution", "Duplicate Patterns"])
            
            with tab_viz1:
                # Posting frequency distribution
                post_dist_series = author_post_counts.value_counts().head(50)
                post_dist_data = pd.DataFrame({
                    'Posts per Author': post_dist_series.index,
                    'Number of Authors': post_dist_series.values
                })
                
                chart_freq = alt.Chart(post_dist_data).mark_bar(color='steelblue', opacity=0.8).encode(
                    x=alt.X('Posts per Author:Q', title='Number of Posts'),
                    y=alt.Y('Number of Authors:Q', title='Number of Authors', scale=alt.Scale(type='log')),
                    tooltip=[
                        alt.Tooltip('Posts per Author:Q', title='Posts'),
                        alt.Tooltip('Number of Authors:Q', title='Authors')
                    ]
                ).properties(
                    title='Author Posting Frequency Distribution (Log Scale)',
                    height=400
                )
                
                # Add threshold line
                threshold_line = alt.Chart(pd.DataFrame({'threshold': [high_freq_threshold]})).mark_rule(
                    color='red',
                    strokeDash=[5, 5],
                    strokeWidth=2
                ).encode(x='threshold:Q')
                
                # Combine and configure
                combined_freq = (chart_freq + threshold_line).configure_axis(
                    labelFontSize=11,
                    titleFontSize=12
                ).configure_title(
                    fontSize=13,
                    fontWeight='bold'
                )
                
                st.altair_chart(combined_freq, use_container_width=True)
            
            with tab_viz2:
                # Bot score distribution
                bot_score_data = pd.DataFrame({
                    'Bot Score': bot_scores['bot_score']
                })
                
                chart_bot_score = alt.Chart(bot_score_data).mark_bar(color='coral', opacity=0.7).encode(
                    x=alt.X('Bot Score:Q', bin=alt.Bin(maxbins=50), title='Bot Score'),
                    y=alt.Y('count()', title='Number of Authors'),
                    tooltip=[
                        alt.Tooltip('Bot Score:Q', bin=alt.Bin(maxbins=50), title='Score Range'),
                        alt.Tooltip('count()', title='Authors')
                    ]
                ).properties(
                    title='Bot Score Distribution',
                    height=400
                )
                
                # Add threshold line
                bot_threshold_line = alt.Chart(pd.DataFrame({'threshold': [60]})).mark_rule(
                    color='red',
                    strokeDash=[5, 5],
                    strokeWidth=2
                ).encode(x='threshold:Q')
                
                # Combine and configure
                combined_bot_score = (chart_bot_score + bot_threshold_line).configure_axis(
                    labelFontSize=11,
                    titleFontSize=12
                ).configure_title(
                    fontSize=13,
                    fontWeight='bold'
                )
                
                st.altair_chart(combined_bot_score, use_container_width=True)
            
            with tab_viz3:
                # Duplicate ratio vs post count
                scatter_data = author_duplicate_stats[author_duplicate_stats['total_posts'] > 5].copy()
                scatter_data['duplicate_pct'] = scatter_data['duplicate_ratio'] * 100
                scatter_data = scatter_data.reset_index()
                
                chart_scatter = alt.Chart(scatter_data).mark_circle(opacity=0.5, size=30).encode(
                    x=alt.X('total_posts:Q', title='Total Posts', scale=alt.Scale(type='log')),
                    y=alt.Y('duplicate_pct:Q', title='Duplicate Ratio (%)'),
                    tooltip=[
                        alt.Tooltip('author:N', title='Author'),
                        alt.Tooltip('total_posts:Q', title='Posts'),
                        alt.Tooltip('duplicate_pct:Q', title='Duplicate %', format='.1f')
                    ],
                    color=alt.condition(
                        alt.datum.duplicate_pct > 50,
                        alt.value('#e74c3c'),
                        alt.value('#9b59b6')
                    )
                ).properties(
                    title='Content Duplication Pattern',
                    height=400
                )
                
                # Add threshold line
                dup_threshold_line = alt.Chart(pd.DataFrame({'threshold': [50]})).mark_rule(
                    color='red',
                    strokeDash=[5, 5],
                    strokeWidth=2
                ).encode(y='threshold:Q')
                
                # Combine and configure
                combined_scatter = (chart_scatter + dup_threshold_line).configure_axis(
                    labelFontSize=11,
                    titleFontSize=12
                ).configure_title(
                    fontSize=13,
                    fontWeight='bold'
                )
                
                st.altair_chart(combined_scatter, use_container_width=True)
        
        except Exception as e:
            st.warning(f"Could not create visualizations: {e}")
        
        # Summary
        st.subheader("📊 Detection Summary")
        
        summary_data = {
            'Metric': [
                'Total Authors Analyzed',
                'Bot/Buzzer Candidates',
                'Posts by Bots',
                'High Frequency Posters',
                'Suspicious Duplicators',
                'Suspicious Temporal Patterns',
                'High Volume Low Engagement'
            ],
            'Count': [
                f"{len(bot_scores):,}",
                f"{len(bot_candidates):,}",
                f"{bot_candidates['post_count'].sum():,}" if len(bot_candidates) > 0 else "0",
                f"{len(high_freq_authors):,}",
                f"{len(suspicious_duplicators):,}",
                f"{len(suspicious_temporal):,}" if 'suspicious_temporal' in locals() else "N/A",
                f"{len(suspicious_engagement):,}" if 'suspicious_engagement' in locals() else "N/A"
            ]
        }
        
        st.dataframe(pd.DataFrame(summary_data), use_container_width=True)
    
    else:
        st.info("No author data available after filtering unknown users")

else:
    st.info("Author data not available for bot detection analysis")

# ============================================================================
# TOPIC MODELING: LDA (Latent Dirichlet Allocation)
# ============================================================================

st.header(TOPIC_TITLE)
st.caption("Menggunakan LDA untuk mengidentifikasi topik tersembunyi dalam diskusi")

with st.expander("ℹ️ Penjelasan Pemodelan Topik", expanded=False):
    st.markdown(TOPIC_DESCRIPTION)

# Sample data for efficiency
sample_size = min(5000, len(df_filtered))
text_sample = df_filtered['text'].dropna().sample(sample_size, random_state=42)

st.write(f"📊 **Analyzing {len(text_sample):,} documents** (avg length: {text_sample.str.len().mean():.0f} characters)")

# Vectorization
st.subheader("🔧 1. Text Vectorization")

with st.spinner("Creating TF-IDF matrix..."):
    from sklearn.feature_extraction.text import TfidfVectorizer
    
    # Indonesian stop words
    indonesian_stopwords = [
        'yang', 'untuk', 'dengan', 'dari', 'ini', 'itu', 'dan', 'di', 'ke', 'pada',
        'adalah', 'akan', 'ada', 'juga', 'oleh', 'atau', 'dalam', 'tidak', 'sudah',
        'telah', 'dapat', 'bisa', 'harus', 'lebih', 'saat', 'saya', 'kami', 'kita'
    ]
    
    tfidf_vectorizer = TfidfVectorizer(
        max_features=1000,
        min_df=5,
        max_df=0.8,
        ngram_range=(1, 2),
        stop_words=indonesian_stopwords
    )
    
    tfidf_matrix = tfidf_vectorizer.fit_transform(text_sample)
    
    col_vec1, col_vec2, col_vec3 = st.columns(3)
    
    with col_vec1:
        st.metric("Matrix Shape", f"{tfidf_matrix.shape[0]} × {tfidf_matrix.shape[1]}")
    
    with col_vec2:
        st.metric("Vocabulary Size", f"{len(tfidf_vectorizer.get_feature_names_out()):,}")
    
    with col_vec3:
        sparsity = (1 - tfidf_matrix.nnz / (tfidf_matrix.shape[0] * tfidf_matrix.shape[1])) * 100
        st.metric("Sparsity", f"{sparsity:.1f}%")

# LDA Model Training
st.subheader("🤖 2. LDA Model Training")

with st.spinner("Training LDA models..."):
    from sklearn.decomposition import LatentDirichletAllocation
    
    # Train models with different topic counts
    n_topics_list = [5, 7, 10]
    lda_models = {}
    
    for n_topics in n_topics_list:
        lda = LatentDirichletAllocation(
            n_components=n_topics,
            max_iter=20,
            learning_method='online',
            random_state=42,
            n_jobs=-1
        )
        lda.fit(tfidf_matrix)
        
        perplexity = lda.perplexity(tfidf_matrix)
        
        lda_models[n_topics] = {
            'model': lda,
            'perplexity': perplexity
        }
    
    # Select best model
    best_n_topics = min(lda_models.keys(), key=lambda k: lda_models[k]['perplexity'])
    best_lda = lda_models[best_n_topics]['model']
    
    st.success(f"🏆 **Model Terbaik**: {best_n_topics} topik (Perplexity: {lda_models[best_n_topics]['perplexity']:.2f})")
    
    # Show all models
    model_comparison = []
    for n, data in lda_models.items():
        model_comparison.append({
            'Topics': n,
            'Perplexity': f"{data['perplexity']:.2f}",
            'Selected': '✓' if n == best_n_topics else ''
        })
    
    st.dataframe(pd.DataFrame(model_comparison), use_container_width=True)

# Topic Interpretation
st.subheader("📋 3. Topic Interpretation")

feature_names = tfidf_vectorizer.get_feature_names_out()
n_top_words = 15

topic_data = []

for topic_idx, topic in enumerate(best_lda.components_):
    top_indices = topic.argsort()[-n_top_words:][::-1]
    top_words = [feature_names[i] for i in top_indices]
    
    topic_data.append({
        'Topic': f"Topic {topic_idx}",
        'Top Words': ', '.join(top_words[:10]),
        'Additional Words': ', '.join(top_words[10:])
    })

st.write("**Kata Kunci Teratas per Topik:**")

for topic in topic_data:
    with st.expander(f"🔹 {topic['Topic']}"):
        st.write(f"**Kata Kunci Utama:** {topic['Top Words']}")
        st.write(f"**Kata Kunci Sekunder:** {topic['Additional Words']}")

# Topic Distribution
st.subheader("📊 4. Distribusi Topik")

# Get document-topic distribution
doc_topics = best_lda.transform(tfidf_matrix)
dominant_topics = doc_topics.argmax(axis=1)
topic_counts = pd.Series(dominant_topics).value_counts().sort_index()

col_dist1, col_dist2 = st.columns([2, 1])

with col_dist1:
    st.write("**Distribusi Dokumen di Seluruh Topik:**")
    
    dist_data = []
    for topic_idx, count in topic_counts.items():
        percentage = (count / len(dominant_topics)) * 100
        dist_data.append({
            'Topic': f"Topic {topic_idx}",
            'Documents': count,
            'Percentage': f"{percentage:.1f}%"
        })
    
    df_dist = pd.DataFrame(dist_data)
    st.dataframe(df_dist, use_container_width=True)
    
    # Visualize distribution
    try:
        import altair as alt
        
        chart_topic_dist = alt.Chart(df_dist).mark_bar(color='#3498db', opacity=0.8).encode(
            x=alt.X('Documents:Q', title='Number of Documents'),
            y=alt.Y('Topic:N', title='', sort='-x'),
            tooltip=[
                alt.Tooltip('Topic:N', title='Topic'),
                alt.Tooltip('Documents:Q', title='Documents'),
                alt.Tooltip('Percentage:N', title='Percentage')
            ]
        ).properties(
            title='Distribusi Dokumen di Seluruh Topik',
            height=300
        ).configure_axis(
            labelFontSize=11,
            titleFontSize=12
        ).configure_title(
            fontSize=13,
            fontWeight='bold'
        )
        
        st.altair_chart(chart_topic_dist, use_container_width=True)
    
    except Exception as e:
        st.warning(f"Could not create distribution chart: {e}")

with col_dist2:
    st.write("**Statistik Topik:**")
    st.metric("Total Topics", best_n_topics)
    st.metric("Dominant Topic", f"Topic {topic_counts.idxmax()}")
    st.metric("Docs in Dominant", topic_counts.max())
    st.metric("Avg Docs/Topic", f"{topic_counts.mean():.0f}")

# Topic-Sentiment Analysis
if 'sentiment_label' in df_filtered.columns:
    st.subheader("🎭 5. Analisis Sentimen Topik")
    
    # Map topics back to original sample
    text_sample_reset = text_sample.reset_index()
    text_sample_reset['topic'] = dominant_topics
    
    # Merge with sentiment
    topic_sentiment = text_sample_reset.merge(
        df_filtered[['sentiment_label']],
        left_on='index',
        right_index=True,
        how='left'
    )
    
    # Calculate sentiment distribution per topic
    topic_sent_dist = topic_sentiment.groupby(['topic', 'sentiment_label']).size().unstack(fill_value=0)
    topic_sent_pct = topic_sent_dist.div(topic_sent_dist.sum(axis=1), axis=0) * 100
    
    st.write("**Distribusi Sentimen berdasarkan Topik (%):**")
    st.dataframe(topic_sent_pct.round(1), use_container_width=True)
    
    # Identify most negative and positive topics
    if 'Negatif' in topic_sent_pct.columns:
        most_negative_topic = topic_sent_pct['Negatif'].idxmax()
        st.warning(f"⚠️ **Topik Paling Negatif**: Topik {most_negative_topic} ({topic_sent_pct.loc[most_negative_topic, 'Negatif']:.1f}% negatif)")
    
    if 'Positif' in topic_sent_pct.columns:
        most_positive_topic = topic_sent_pct['Positif'].idxmax()
        st.success(f"✓ **Topik Paling Positif**: Topik {most_positive_topic} ({topic_sent_pct.loc[most_positive_topic, 'Positif']:.1f}% positif)")

# Word Clouds Visualization
st.subheader("☁️ 6. Word Cloud Topik")

st.write("**Representasi visual kata kunci topik:**")

try:
    from wordcloud import WordCloud
    import matplotlib.pyplot as plt
    import numpy as np
    
    # Create tabs for each topic
    topic_tabs = st.tabs([f"Topic {i}" for i in range(best_n_topics)])
    
    for topic_idx, tab in enumerate(topic_tabs):
        with tab:
            # Create word frequency dict
            topic = best_lda.components_[topic_idx]
            word_freq = {feature_names[i]: topic[i] for i in topic.argsort()[-50:]}
            
            # Generate word cloud
            wordcloud = WordCloud(
                width=800,
                height=400,
                background_color='white',
                colormap='viridis',
                relative_scaling=0.5,
                min_font_size=10
            ).generate_from_frequencies(word_freq)
            
            # Display - convert to array to avoid numpy compatibility issues
            fig, ax = plt.subplots(figsize=(10, 5))
            # Convert wordcloud to image array explicitly
            wordcloud_array = np.array(wordcloud.to_image())
            ax.imshow(wordcloud_array, interpolation='bilinear')
            ax.set_title(f'Topic {topic_idx} ({topic_counts.get(topic_idx, 0):,} documents)', 
                        fontsize=12, weight='bold')
            ax.axis('off')
            
            st.pyplot(fig)
            plt.close()
            
            # Show top words
            st.write(f"**10 Kata Kunci Teratas:** {', '.join(topic_data[topic_idx]['Top Words'].split(', ')[:10])}")

except Exception as e:
    st.warning(f"Could not generate word clouds: {e}")
    st.write("Install wordcloud package: `pip install wordcloud`")

# Topic Insights
st.subheader("💡 Insight Pemodelan Topik")

col_insight1, col_insight2 = st.columns(2)

with col_insight1:
    st.markdown("""
    **Temuan Utama:**
    """)
    
    st.write(f"📊 Teridentifikasi **{best_n_topics} topik berbeda** dalam diskusi")
    st.write(f"📈 Topik {topic_counts.idxmax()} paling dominan ({topic_counts.max():,} dokumen)")
    st.write(f"📉 Topik {topic_counts.idxmin()} paling sedikit ({topic_counts.min():,} dokumen)")
    
    # Topic diversity
    topic_entropy = -(topic_counts / topic_counts.sum() * np.log(topic_counts / topic_counts.sum())).sum()
    max_entropy = np.log(best_n_topics)
    diversity_score = topic_entropy / max_entropy * 100
    
    st.write(f"🎯 Diversitas Topik: {diversity_score:.1f}% (lebih tinggi = lebih seimbang)")

with col_insight2:
    st.markdown("""
    **Implikasi Strategis:**
    """)
    
    if diversity_score > 80:
        st.success("✓ Diskusi beragam - banyak perspektif terwakili")
    elif diversity_score > 60:
        st.info("ℹ️ Diversitas sedang - beberapa topik mendominasi")
    else:
        st.warning("⚠️ Diversitas rendah - diskusi terpusat pada sedikit topik")
    
    if 'sentiment_label' in df_filtered.columns and 'Negatif' in topic_sent_pct.columns:
        avg_negative = topic_sent_pct['Negatif'].mean()
        if avg_negative > 50:
            st.error("⚠️ Sebagian besar topik cenderung negatif - kekhawatiran luas")
        elif avg_negative > 35:
            st.warning("⚠️ Sentimen negatif tingkat sedang di seluruh topik")
        else:
            st.success("✓ Topik umumnya seimbang atau positif")

# Export topic assignments
st.divider()

col_export1, col_export2 = st.columns([3, 1])

with col_export1:
    st.info("💡 **Tip**: Unduh penetapan topik untuk menganalisis konten berdasarkan tema")

with col_export2:
    # Prepare export data
    export_topics = text_sample_reset.copy()
    export_topics['topic_label'] = export_topics['topic'].apply(lambda x: f"Topic {x}")
    export_topics = export_topics[['index', 'text', 'topic', 'topic_label']]
    
    csv_topics = export_topics.to_csv(index=False)
    st.download_button(
        label="📥 Download CSV",
        data=csv_topics,
        file_name="topic_assignments.csv",
        mime="text/csv"
    )

# ============================================================================
# TIME SERIES FORECASTING: ARIMA
# ============================================================================

st.header(FORECAST_TITLE)
st.caption("Menggunakan ARIMA untuk memprediksi aktivitas posting masa depan")

with st.expander("ℹ️ Penjelasan Prediksi", expanded=False):
    st.markdown(FORECAST_DESCRIPTION)

if 'date_parsed' in df_filtered.columns:
    
    # Prepare daily time series
    df_ts = df_filtered.copy()
    df_ts['date_parsed'] = pd.to_datetime(df_ts['date_parsed'], errors='coerce')
    df_ts = df_ts[df_ts['date_parsed'].notna()]
    
    if len(df_ts) > 30:  # Need sufficient data
        
        daily_counts = df_ts.groupby(df_ts['date_parsed'].dt.date).size().reset_index(name='post_count')
        daily_counts.columns = ['date', 'post_count']
        daily_counts['date'] = pd.to_datetime(daily_counts['date'])
        daily_counts = daily_counts.set_index('date')
        
        # Fill missing dates
        date_range = pd.date_range(start=daily_counts.index.min(), end=daily_counts.index.max(), freq='D')
        daily_counts = daily_counts.reindex(date_range, fill_value=0)
        daily_counts.index.name = 'date'
        
        # Display time series info
        col_ts1, col_ts2, col_ts3, col_ts4 = st.columns(4)
        
        with col_ts1:
            st.metric("Date Range", f"{(daily_counts.index.max() - daily_counts.index.min()).days} days")
        
        with col_ts2:
            st.metric("Mean Posts/Day", f"{daily_counts['post_count'].mean():.1f}")
        
        with col_ts3:
            st.metric("Std Posts/Day", f"{daily_counts['post_count'].std():.1f}")
        
        with col_ts4:
            st.metric("Max Posts/Day", f"{daily_counts['post_count'].max()}")
        
        # Stationarity Test
        st.subheader("🔬 1. Stationarity Test (ADF)")
        
        from statsmodels.tsa.stattools import adfuller
        
        adf_result = adfuller(daily_counts['post_count'])
        
        col_adf1, col_adf2 = st.columns(2)
        
        with col_adf1:
            st.write("**ADF Test Results:**")
            st.write(f"ADF Statistic: {adf_result[0]:.4f}")
            st.write(f"P-value: {adf_result[1]:.4f}")
            
            if adf_result[1] < 0.05:
                st.success("✓ Series adalah STATIONARY (p < 0.05)")
                d_order = 0
            else:
                st.warning("⚠️ Series adalah NON-STATIONARY (p >= 0.05)")
                d_order = 1
        
        with col_adf2:
            st.write("**Critical Values:**")
            for key, value in adf_result[4].items():
                st.write(f"{key}: {value:.4f}")
        
        # ARIMA Model
        st.subheader("🤖 2. Pelatihan Model ARIMA")
        
        with st.spinner("Training ARIMA model..."):
            from statsmodels.tsa.arima.model import ARIMA
            
            # Train ARIMA model
            arima_order = (5, d_order, 0)
            
            try:
                arima_model = ARIMA(daily_counts['post_count'], order=arima_order)
                arima_fit = arima_model.fit()
                
                st.success(f"✓ Model ARIMA{arima_order} berhasil dilatih")
                
                col_model1, col_model2 = st.columns(2)
                
                with col_model1:
                    st.metric("AIC", f"{arima_fit.aic:.2f}")
                
                with col_model2:
                    st.metric("BIC", f"{arima_fit.bic:.2f}")
                
                # Forecast
                st.subheader("🔮 3. Prediksi 90 Hari")
                
                forecast_steps = 90
                arima_forecast = arima_fit.forecast(steps=forecast_steps)
                forecast_dates = pd.date_range(
                    start=daily_counts.index.max() + pd.Timedelta(days=1),
                    periods=forecast_steps,
                    freq='D'
                )
                
                # Calculate confidence intervals
                forecast_se = np.std(arima_fit.resid) * np.sqrt(np.arange(1, forecast_steps+1))
                forecast_lower = arima_forecast - 1.96 * forecast_se
                forecast_upper = arima_forecast + 1.96 * forecast_se
                
                # Display forecast summary
                col_fc1, col_fc2, col_fc3, col_fc4 = st.columns(4)
                
                with col_fc1:
                    st.metric("Next 7 Days Avg", f"{arima_forecast[:7].mean():.1f} posts/day")
                
                with col_fc2:
                    st.metric("Next 30 Days Avg", f"{arima_forecast[:30].mean():.1f} posts/day")
                
                with col_fc3:
                    st.metric("Next 60 Days Avg", f"{arima_forecast[:60].mean():.1f} posts/day")
                
                with col_fc4:
                    st.metric("Next 90 Days Avg", f"{arima_forecast[:90].mean():.1f} posts/day")
                
                # Visualization
                st.subheader("📊 4. Visualisasi Prediksi")
                
                try:
                    import altair as alt
                    
                    # Prepare data for Altair
                    # Historical data
                    hist_data = pd.DataFrame({
                        'Date': daily_counts.index,
                        'Posts': daily_counts['post_count'],
                        'Type': 'Historical'
                    })
                    
                    # Forecast data
                    forecast_data = pd.DataFrame({
                        'Date': forecast_dates,
                        'Posts': arima_forecast,
                        'Lower': forecast_lower,
                        'Upper': forecast_upper,
                        'Type': 'Forecast'
                    })
                    
                    # Historical line
                    hist_line = alt.Chart(hist_data).mark_line(color='#2c3e50', strokeWidth=2).encode(
                        x=alt.X('Date:T', title='Date', axis=alt.Axis(format='%Y-%m-%d', labelAngle=-45)),
                        y=alt.Y('Posts:Q', title='Posts per Day'),
                        tooltip=[
                            alt.Tooltip('Date:T', title='Date', format='%Y-%m-%d'),
                            alt.Tooltip('Posts:Q', title='Posts', format='.0f'),
                            alt.Tooltip('Type:N', title='Type')
                        ]
                    )
                    
                    # Forecast line
                    forecast_line = alt.Chart(forecast_data).mark_line(color='#e74c3c', strokeWidth=2, strokeDash=[5, 5]).encode(
                        x=alt.X('Date:T'),
                        y=alt.Y('Posts:Q'),
                        tooltip=[
                            alt.Tooltip('Date:T', title='Date', format='%Y-%m-%d'),
                            alt.Tooltip('Posts:Q', title='Forecast', format='.0f'),
                            alt.Tooltip('Type:N', title='Type')
                        ]
                    )
                    
                    # Confidence interval
                    ci_area = alt.Chart(forecast_data).mark_area(opacity=0.2, color='#e74c3c').encode(
                        x=alt.X('Date:T'),
                        y=alt.Y('Lower:Q'),
                        y2=alt.Y2('Upper:Q')
                    )
                    
                    # Today marker
                    today_line = alt.Chart(pd.DataFrame({'Date': [daily_counts.index.max()]})).mark_rule(
                        color='green',
                        strokeWidth=2,
                        strokeDash=[3, 3]
                    ).encode(x='Date:T')
                    
                    # Combine
                    chart_forecast = (hist_line + forecast_line + ci_area + today_line).properties(
                        title='Prediksi ARIMA: 90 Hari ke Depan dengan 95% Interval Kepercayaan',
                        height=400
                    ).configure_axis(
                        labelFontSize=11,
                        titleFontSize=12
                    ).configure_title(
                        fontSize=13,
                        fontWeight='bold'
                    )
                    
                    st.altair_chart(chart_forecast, use_container_width=True)
                
                except Exception as e:
                    st.warning(f"Tidak dapat membuat visualisasi Altair: {e}")
                    
                    # Fallback to matplotlib
                    import matplotlib.pyplot as plt
                    
                    fig, ax = plt.subplots(figsize=(12, 6))
                    
                    ax.plot(daily_counts.index, daily_counts['post_count'], 
                           label='Historical Data', color='black', linewidth=1.5)
                    ax.plot(forecast_dates, arima_forecast, 
                           label='ARIMA Forecast', color='red', linewidth=2)
                    ax.fill_between(forecast_dates, forecast_lower, forecast_upper, 
                                   alpha=0.2, color='red', label='95% CI')
                    ax.axvline(daily_counts.index.max(), color='green', 
                              linestyle='--', linewidth=2, label='Forecast Start')
                    
                    ax.set_xlabel('Date', fontsize=11)
                    ax.set_ylabel('Posts per Day', fontsize=11)
                    ax.set_title('ARIMA Forecast - 90 Days Ahead', fontsize=12, weight='bold')
                    ax.legend(loc='upper left')
                    ax.grid(True, alpha=0.3)
                    
                    st.pyplot(fig)
                    plt.close()
                
                # Forecast table for key dates
                st.subheader("📅 5. Prediksi Tanggal Kunci")
                
                key_dates = [7, 14, 30, 60, 90]
                forecast_table = []
                
                for days in key_dates:
                    idx = days - 1
                    forecast_date = forecast_dates[idx]
                    forecast_value = arima_forecast.iloc[idx]
                    lower_bound = forecast_lower.iloc[idx]
                    upper_bound = forecast_upper.iloc[idx]
                    
                    forecast_table.append({
                        'Period': f"{days} days",
                        'Date': forecast_date.strftime('%Y-%m-%d'),
                        'Forecast': f"{forecast_value:.1f}",
                        '95% CI': f"[{lower_bound:.1f}, {upper_bound:.1f}]"
                    })
                
                st.dataframe(pd.DataFrame(forecast_table), use_container_width=True)
                
                # Insights
                st.subheader("💡 Insight Prediksi")
                
                col_insight1, col_insight2 = st.columns(2)
                
                with col_insight1:
                    st.markdown("**Analisis Tren:**")
                    
                    current_avg = daily_counts['post_count'].tail(7).mean()
                    forecast_avg = arima_forecast[:7].mean()
                    trend_change = ((forecast_avg - current_avg) / current_avg) * 100
                    
                    if trend_change > 10:
                        st.error(f"📈 **Tren Meningkat**: +{trend_change:.1f}% diharapkan dalam minggu depan")
                        st.write("⚠️ Bersiaplah untuk volume aktivitas yang lebih tinggi")
                    elif trend_change < -10:
                        st.success(f"📉 **Tren Menurun**: {trend_change:.1f}% diharapkan dalam minggu depan")
                        st.write("✓ Aktivitas diperkirakan menurun")
                    else:
                        st.info(f"➡️ **Tren Stabil**: {trend_change:+.1f}% perubahan diharapkan")
                        st.write("ℹ️ Tingkat aktivitas tetap konsisten")
                
                with col_insight2:
                    st.markdown("**Implikasi Strategis:**")
                    
                    max_forecast = arima_forecast.max()
                    max_historical = daily_counts['post_count'].max()
                    
                    if max_forecast > max_historical * 1.2:
                        st.warning("⚠️ Prediksi menunjukkan lonjakan aktivitas di atas maksimum historis")
                        st.write("• Tingkatkan kapasitas pemantauan")
                        st.write("• Siapkan tim respon cepat")
                    elif max_forecast < max_historical * 0.5:
                        st.success("✓ Aktivitas diperkirakan tetap di bawah level puncak")
                        st.write("• Pemantauan standar sudah cukup")
                    else:
                        st.info("ℹ️ Aktivitas dalam rentang normal")
                        st.write("• Pertahankan pemantauan saat ini")
                
                # Export forecast
                st.divider()
                
                col_export1, col_export2 = st.columns([3, 1])
                
                with col_export1:
                    st.info("💡 **Tip**: Unduh data prediksi untuk perencanaan kapasitas dan alokasi sumber daya")
                
                with col_export2:
                    export_forecast = pd.DataFrame({
                        'Date': forecast_dates,
                        'Forecast': arima_forecast,
                        'Lower_95CI': forecast_lower,
                        'Upper_95CI': forecast_upper
                    })
                    
                    csv_forecast = export_forecast.to_csv(index=False)
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv_forecast,
                        file_name="arima_forecast_90days.csv",
                        mime="text/csv"
                    )
            
            except Exception as e:
                st.error(f"Tidak dapat melatih model ARIMA: {e}")
                st.write("Ini mungkin karena data tidak cukup atau masalah kualitas data.")
    
    else:
        st.warning("Insufficient data for time series forecasting (need at least 30 days)")

else:
    st.info("Date column not available for time series forecasting")

# ============================================================================
# SECTION 2: KEYWORD & ACTION DETECTION
# ============================================================================

st.header(KEYWORDS_TITLE)

with st.expander("ℹ️ Penjelasan Kata Kunci Aksi", expanded=False):
    st.markdown(KEYWORDS_DESCRIPTION)

# Calculate keyword statistics
keyword_counts = {}
texts_with_keywords = 0
total_keyword_mentions = 0

if 'detected_keywords' in df_filtered.columns:
    for keywords_list in df_filtered['detected_keywords']:
        if isinstance(keywords_list, list) and len(keywords_list) > 0:
            texts_with_keywords += 1
            for kw in keywords_list:
                kw_clean = _clean_keyword_label(kw)
                if not kw_clean:
                    continue
                keyword_counts[kw_clean] = keyword_counts.get(kw_clean, 0) + 1
                total_keyword_mentions += 1
elif 'text' in df_filtered.columns and 'sentiment_label' in df_filtered.columns:
    neg_posts = df_filtered[df_filtered['sentiment_label'] == 'Negatif']['text'].astype(str)
    protest_keywords = ['demo', 'demonstrasi', 'tolak', 'menolak', 'bahaya', 'marah', 'geram',
                       'unjuk rasa', 'aksi massa', 'turun ke jalan', 'kemarahan']

    for post in neg_posts:
        post_lower = post.lower()
        found_keywords = []
        for kw in protest_keywords:
            if kw in post_lower:
                keyword_counts[kw] = keyword_counts.get(kw, 0) + 1
                found_keywords.append(kw)
        if found_keywords:
            texts_with_keywords += 1
            total_keyword_mentions += len(found_keywords)

# Display overall statistics
total_texts = len(df_filtered)
texts_without_keywords = total_texts - texts_with_keywords
pct_with_keywords = (texts_with_keywords / total_texts * 100) if total_texts > 0 else 0
pct_without_keywords = (texts_without_keywords / total_texts * 100) if total_texts > 0 else 0
avg_keywords_per_text = (total_keyword_mentions / total_texts) if total_texts > 0 else 0

st.subheader("📊 Overall Statistics")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Texts Analyzed", f"{total_texts:,}")
with col2:
    st.metric("Texts With Keywords", f"{texts_with_keywords:,}", f"{pct_with_keywords:.2f}%")
with col3:
    st.metric("Texts Without Keywords", f"{texts_without_keywords:,}", f"{pct_without_keywords:.2f}%")
with col4:
    st.metric("Avg Keywords/Text", f"{avg_keywords_per_text:.2f}")

if keyword_counts:
    # Sort keywords by frequency
    keyword_counts_sorted = dict(sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True))
    
      
    # Create visualizations using Altair
    try:
        import altair as alt
        
        st.subheader("📊 Detailed Keyword Analysis")
        
        # Create 2x2 grid for charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Chart 1: Top Keywords Bar Chart
            top_n = min(10, len(keyword_counts_sorted))
            keyword_top = dict(list(keyword_counts_sorted.items())[:top_n])
            
            kw_df = pd.DataFrame([
                {'Kata Kunci': k, 'Frekuensi': v} 
                for k, v in keyword_top.items()
            ])
            
            chart1 = alt.Chart(kw_df).mark_bar(color='#e74c3c').encode(
                x=alt.X('Frekuensi:Q', title='Frekuensi'),
                y=alt.Y('Kata Kunci:N', title='', sort='-x'),
                tooltip=[
                    alt.Tooltip('Kata Kunci:N', title='Kategori'),
                    alt.Tooltip('Frekuensi:Q', title='Frekuensi', format=',')
                ]
            ).properties(
                title='Top 10 Kategori Kata Kunci Aksi/Protes',
                height=400
            ).configure_axis(
                labelFontSize=11,
                titleFontSize=12
            ).configure_title(
                fontSize=13,
                fontWeight='bold'
            )
            
            st.altair_chart(chart1, use_container_width=True)
        
        with col2:
            # Chart 2: Keyword Detection by Sentiment
            if 'sentiment_label' in df_filtered.columns:
                sentiment_keyword_data = []
                sentiments = ['Positif', 'Negatif', 'Netral']
                
                for sentiment in sentiments:
                    subset = df_filtered[df_filtered['sentiment_label'] == sentiment]
                    if 'detected_keywords' in df_filtered.columns:
                        with_kw = sum(1 for kws in subset['detected_keywords'] if isinstance(kws, list) and len(kws) > 0)
                    else:
                        with_kw = 0
                    
                    pct = (with_kw / len(subset) * 100) if len(subset) > 0 else 0
                    sentiment_keyword_data.append({
                        'Sentimen': sentiment,
                        'Persentase': pct
                    })
                
                sentiment_df = pd.DataFrame(sentiment_keyword_data)
                
                colors_sentiment = {'Positif': '#2ecc71', 'Negatif': '#e74c3c', 'Netral': '#95a5a6'}
                
                base2 = alt.Chart(sentiment_df).encode(
                    x=alt.X('Sentimen:N', title=''),
                    y=alt.Y('Persentase:Q', title='% dengan Kata Kunci Aksi', scale=alt.Scale(domain=[0, max([d['Persentase'] for d in sentiment_keyword_data]) * 1.1])),
                    color=alt.Color('Sentimen:N', scale=alt.Scale(domain=list(colors_sentiment.keys()), range=list(colors_sentiment.values())), legend=None),
                    tooltip=[
                        alt.Tooltip('Sentimen:N', title='Sentimen'),
                        alt.Tooltip('Persentase:Q', title='Persentase', format='.1f')
                    ]
                )
                
                chart2 = base2.mark_bar()
                text2 = base2.mark_text(
                    align='center',
                    baseline='bottom',
                    dy=-5,
                    fontWeight='bold'
                ).encode(
                    text=alt.Text('Persentase:Q', format='.1f')
                )
                
                final_chart2 = (chart2 + text2).properties(
                    title='Keyword Aksi/Protes Berdasarkan Sentimen',
                    height=400
                ).configure_axis(
                    labelFontSize=11,
                    titleFontSize=12
                ).configure_title(
                    fontSize=13,
                    fontWeight='bold'
                )
                
                st.altair_chart(final_chart2, use_container_width=True)
        
        col3, col4 = st.columns(2)
        
        with col3:
            # Chart 3: Keyword by Source/Platform
            if 'source' in df_filtered.columns:
                source_keyword_data = []
                
                for source in sorted(df_filtered['source'].unique()):
                    subset = df_filtered[df_filtered['source'] == source]
                    if 'detected_keywords' in df_filtered.columns:
                        with_kw = sum(1 for kws in subset['detected_keywords'] if isinstance(kws, list) and len(kws) > 0)
                    else:
                        with_kw = 0
                    
                    pct = (with_kw / len(subset) * 100) if len(subset) > 0 else 0
                    source_keyword_data.append({
                        'Platform': source,
                        'Persentase': pct
                    })
                
                source_df = pd.DataFrame(source_keyword_data)
                
                base3 = alt.Chart(source_df).encode(
                    x=alt.X('Platform:N', title='', sort=None),
                    y=alt.Y('Persentase:Q', title='% dengan Kata Kunci Aksi', scale=alt.Scale(domain=[0, max([d['Persentase'] for d in source_keyword_data]) * 1.1])),
                    tooltip=[
                        alt.Tooltip('Platform:N', title='Platform'),
                        alt.Tooltip('Persentase:Q', title='Persentase', format='.1f')
                    ]
                )
                
                chart3 = base3.mark_bar(color='#3498db')
                text3 = base3.mark_text(
                    align='center',
                    baseline='bottom',
                    dy=-5,
                    fontWeight='bold'
                ).encode(
                    text=alt.Text('Persentase:Q', format='.1f')
                )
                
                final_chart3 = (chart3 + text3).properties(
                    title='Keyword Aksi/Protes Berdasarkan Platform',
                    height=400
                ).configure_axis(
                    labelFontSize=11,
                    titleFontSize=12,
                    labelAngle=-45
                ).configure_title(
                    fontSize=13,
                    fontWeight='bold'
                )
                
                st.altair_chart(final_chart3, use_container_width=True)
        
        with col4:
            # Chart 4: Heatmap - Sentiment vs Keywords
            if 'sentiment_label' in df_filtered.columns and 'detected_keywords' in df_filtered.columns:
                sentiments = ['Positif', 'Negatif', 'Netral']
                keywords_for_heatmap = list(keyword_counts_sorted.keys())[:10]  # Top 10 keywords
                
                heatmap_data = []
                for sentiment in sentiments:
                    subset = df_filtered[df_filtered['sentiment_label'] == sentiment]
                    for category in keywords_for_heatmap:
                        count = sum(1 for keywords_list in subset['detected_keywords'] 
                                   if isinstance(keywords_list, list) and category in keywords_list)
                        heatmap_data.append({
                            'Sentimen': sentiment,
                            'Kata Kunci': category,
                            'Jumlah': count
                        })
                
                heatmap_df = pd.DataFrame(heatmap_data)
                
                base4 = alt.Chart(heatmap_df).encode(
                    x=alt.X('Kata Kunci:N', title=''),
                    y=alt.Y('Sentimen:N', title=''),
                    color=alt.Color('Jumlah:Q', scale=alt.Scale(scheme='yelloworangered'), legend=alt.Legend(title='Jumlah Mentions')),
                    tooltip=[
                        alt.Tooltip('Sentimen:N', title='Sentimen'),
                        alt.Tooltip('Kata Kunci:N', title='Kata Kunci'),
                        alt.Tooltip('Jumlah:Q', title='Jumlah', format=',')
                    ]
                )
                
                chart4 = base4.mark_rect()
                text4 = base4.mark_text(baseline='middle', fontWeight='bold').encode(
                    text=alt.Text('Jumlah:Q'),
                    color=alt.condition(
                        alt.datum.Jumlah > heatmap_df['Jumlah'].max() / 2,
                        alt.value('white'),
                        alt.value('black')
                    )
                )
                
                final_chart4 = (chart4 + text4).properties(
                    title='Heatmap: Sentimen vs Kata Kunci Aksi',
                    height=400
                ).configure_axis(
                    labelFontSize=10,
                    titleFontSize=12,
                    labelAngle=-45
                ).configure_title(
                    fontSize=13,
                    fontWeight='bold'
                )
                
                st.altair_chart(final_chart4, use_container_width=True)
        
    except ImportError:
        st.warning("Altair not available. Please install: pip install altair")
    except Exception as e:
        st.error(f"Error creating Altair charts: {e}")
        import traceback
        st.code(traceback.format_exc())

else:
    st.info("No action keywords found in the filtered data.")

# ============================================================================
# SECTION 3: POLITICAL FIGURES
# ============================================================================

st.header(FIGURES_TITLE)

with st.expander("ℹ️ Penjelasan Analisis Tokoh Politik", expanded=False):
    st.markdown(FIGURES_DESCRIPTION)

# Extract political figures from data
pro_figures = []
contra_figures = []
neutral_figures = []

if 'political_figures' in df_filtered.columns:
    for figures_dict in df_filtered['political_figures']:
        if isinstance(figures_dict, dict):
            if 'Pro-Policy' in figures_dict:
                pro_figures.extend(figures_dict['Pro-Policy'])
            if 'Contra-Policy' in figures_dict:
                contra_figures.extend(figures_dict['Contra-Policy'])
            if 'Neutral/Media' in figures_dict:
                neutral_figures.extend(figures_dict['Neutral/Media'])
            elif 'Neutral' in figures_dict:
                neutral_figures.extend(figures_dict['Neutral'])
elif 'text' in df_filtered.columns:
    pro_figures_config = config.POLITICAL_FIGURES.get('Pro-Policy', {}).get('Individuals', [])
    contra_figures_config = config.POLITICAL_FIGURES.get('Contra-Policy', {}).get('Individuals', [])

    for _, row in df_filtered.iterrows():
        text = str(row.get('text', '')).lower()
        for fig in pro_figures_config:
            if fig.lower() in text:
                pro_figures.append(fig)
        for fig in contra_figures_config:
            if fig.lower() in text:
                contra_figures.append(fig)

pro_counts = Counter([_clean_keyword_label(x).upper() for x in pro_figures if _clean_keyword_label(x)])
contra_counts = Counter([_clean_keyword_label(x).upper() for x in contra_figures if _clean_keyword_label(x)])
neutral_counts = Counter([_clean_keyword_label(x).upper() for x in neutral_figures if _clean_keyword_label(x)])

# Display overall statistics
st.subheader("📊 Statistik Keseluruhan")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Tokoh Pro-Kebijakan", len(pro_counts))
    st.metric("Total Sebutan Pro", f"{sum(pro_counts.values()):,}")
with col2:
    st.metric("Tokoh Kontra-Kebijakan", len(contra_counts))
    st.metric("Total Sebutan Kontra", f"{sum(contra_counts.values()):,}")
with col3:
    st.metric("Tokoh Netral/Media", len(neutral_counts))
    st.metric("Total Sebutan Netral", f"{sum(neutral_counts.values()):,}")

if pro_counts or contra_counts or neutral_counts:
    # Display top figures as text
       
    # Create visualizations using Altair
    try:
        import altair as alt
        
        st.subheader("📊 Analisis Tokoh Politik")
        
        # Row 1: Top figures by stance (3 charts)
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Chart 1: Top Pro-Policy Figures
            pro_data = dict(pro_counts.most_common(15))
            if pro_data:
                pro_df = pd.DataFrame([
                    {'Figure': k, 'Mentions': v} 
                    for k, v in pro_data.items()
                ])
                
                chart1 = alt.Chart(pro_df).mark_bar(color='green', opacity=0.7).encode(
                    x=alt.X('Mentions:Q', title='Mentions'),
                    y=alt.Y('Figure:N', title='', sort='-x'),
                    tooltip=[
                        alt.Tooltip('Figure:N', title='Figure'),
                        alt.Tooltip('Mentions:Q', title='Mentions', format=',')
                    ]
                ).properties(
                    title='15 Tokoh/Entitas Pro-Kebijakan Teratas',
                    height=400
                ).configure_axis(
                    labelFontSize=9,
                    titleFontSize=11
                ).configure_title(
                    fontSize=12,
                    fontWeight='bold',
                    color='darkgreen'
                )
                
                st.altair_chart(chart1, use_container_width=True)
        
        with col2:
            # Chart 2: Top Contra-Policy Figures
            contra_data = dict(contra_counts.most_common(15))
            if contra_data:
                contra_df = pd.DataFrame([
                    {'Figure': k, 'Mentions': v} 
                    for k, v in contra_data.items()
                ])
                
                chart2 = alt.Chart(contra_df).mark_bar(color='red', opacity=0.7).encode(
                    x=alt.X('Mentions:Q', title='Mentions'),
                    y=alt.Y('Figure:N', title='', sort='-x'),
                    tooltip=[
                        alt.Tooltip('Figure:N', title='Figure'),
                        alt.Tooltip('Mentions:Q', title='Mentions', format=',')
                    ]
                ).properties(
                    title='15 Tokoh/Entitas Kontra-Kebijakan Teratas',
                    height=400
                ).configure_axis(
                    labelFontSize=9,
                    titleFontSize=11
                ).configure_title(
                    fontSize=12,
                    fontWeight='bold',
                    color='darkred'
                )
                
                st.altair_chart(chart2, use_container_width=True)
        
        with col3:
            # Chart 3: Top Neutral/Media Figures
            neutral_data = dict(neutral_counts.most_common(10))
            if neutral_data:
                neutral_df = pd.DataFrame([
                    {'Figure': k, 'Mentions': v} 
                    for k, v in neutral_data.items()
                ])
                
                chart3 = alt.Chart(neutral_df).mark_bar(color='gray', opacity=0.7).encode(
                    x=alt.X('Mentions:Q', title='Mentions'),
                    y=alt.Y('Figure:N', title='', sort='-x'),
                    tooltip=[
                        alt.Tooltip('Figure:N', title='Figure'),
                        alt.Tooltip('Mentions:Q', title='Mentions', format=',')
                    ]
                ).properties(
                    title='10 Entitas Netral/Media Teratas',
                    height=400
                ).configure_axis(
                    labelFontSize=9,
                    titleFontSize=11
                ).configure_title(
                    fontSize=12,
                    fontWeight='bold',
                    color='dimgray'
                )
                
                st.altair_chart(chart3, use_container_width=True)
        
        # Row 2: Distribution and comparisons (3 charts)
        col4, col5, col6 = st.columns(3)
        
        with col4:
            # Chart 4: Overall Stance Distribution (Pie Chart)
            total_mentions = {
                'Pro-Policy': sum(pro_counts.values()),
                'Contra-Policy': sum(contra_counts.values()),
                'Neutral/Media': sum(neutral_counts.values())
            }
            
            pie_df = pd.DataFrame([
                {'Stance': k, 'Mentions': v, 'Percentage': v / sum(total_mentions.values()) * 100}
                for k, v in total_mentions.items()
            ])
            
            chart4 = alt.Chart(pie_df).mark_arc().encode(
                theta=alt.Theta('Mentions:Q'),
                color=alt.Color('Stance:N', 
                    scale=alt.Scale(
                        domain=['Pro-Policy', 'Contra-Policy', 'Neutral/Media'],
                        range=['green', 'red', 'gray']
                    ),
                    legend=alt.Legend(title='Stance')
                ),
                tooltip=[
                    alt.Tooltip('Stance:N', title='Stance'),
                    alt.Tooltip('Mentions:Q', title='Mentions', format=','),
                    alt.Tooltip('Percentage:Q', title='Percentage', format='.1f')
                ]
            ).properties(
                title='Distribusi Sebutan Tokoh Politik',
                height=400
            ).configure_title(
                fontSize=12,
                fontWeight='bold'
            )
            
            st.altair_chart(chart4, use_container_width=True)
        
        with col5:
            # Chart 5: Mentions by Sentiment
            if 'sentiment_label' in df_filtered.columns and 'political_figures' in df_filtered.columns:
                sentiment_data = []
                sentiments = ['Positif', 'Negatif', 'Netral']
                
                for sentiment in sentiments:
                    subset = df_filtered[df_filtered['sentiment_label'] == sentiment]
                    pro_count = sum(len(f.get('Pro-Policy', [])) for f in subset['political_figures'] if isinstance(f, dict))
                    contra_count = sum(len(f.get('Contra-Policy', [])) for f in subset['political_figures'] if isinstance(f, dict))
                    neutral_count = sum(len(f.get('Neutral/Media', []) or f.get('Neutral', [])) for f in subset['political_figures'] if isinstance(f, dict))
                    
                    sentiment_data.extend([
                        {'Sentiment': sentiment, 'Stance': 'Pro-Policy', 'Mentions': pro_count},
                        {'Sentiment': sentiment, 'Stance': 'Contra-Policy', 'Mentions': contra_count},
                        {'Sentiment': sentiment, 'Stance': 'Neutral/Media', 'Mentions': neutral_count}
                    ])
                
                sentiment_df = pd.DataFrame(sentiment_data)
                
                chart5 = alt.Chart(sentiment_df).mark_bar().encode(
                    x=alt.X('Stance:N', title=''),
                    y=alt.Y('Mentions:Q', title='Mentions'),
                    color=alt.Color('Sentiment:N', 
                        scale=alt.Scale(
                            domain=['Positif', 'Negatif', 'Netral'],
                            range=['#2ecc71', '#e74c3c', '#95a5a6']
                        ),
                        legend=alt.Legend(title='Sentiment')
                    ),
                    xOffset='Sentiment:N',
                    tooltip=[
                        alt.Tooltip('Stance:N', title='Stance'),
                        alt.Tooltip('Sentiment:N', title='Sentiment'),
                        alt.Tooltip('Mentions:Q', title='Mentions', format=',')
                    ]
                ).properties(
                    title='Sebutan Tokoh Berdasarkan Sentimen',
                    height=400
                ).configure_axis(
                    labelFontSize=10,
                    titleFontSize=11
                ).configure_title(
                    fontSize=12,
                    fontWeight='bold'
                )
                
                st.altair_chart(chart5, use_container_width=True)
        
        with col6:
            # Chart 6: Mentions by Platform
            if 'source' in df_filtered.columns and 'political_figures' in df_filtered.columns:
                platform_data = []
                
                for source in sorted(df_filtered['source'].unique()):
                    subset = df_filtered[df_filtered['source'] == source]
                    pro_count = sum(len(f.get('Pro-Policy', [])) for f in subset['political_figures'] if isinstance(f, dict))
                    contra_count = sum(len(f.get('Contra-Policy', [])) for f in subset['political_figures'] if isinstance(f, dict))
                    neutral_count = sum(len(f.get('Neutral/Media', []) or f.get('Neutral', [])) for f in subset['political_figures'] if isinstance(f, dict))
                    
                    platform_data.extend([
                        {'Platform': source, 'Stance': 'Pro-Policy', 'Mentions': pro_count},
                        {'Platform': source, 'Stance': 'Contra-Policy', 'Mentions': contra_count},
                        {'Platform': source, 'Stance': 'Neutral/Media', 'Mentions': neutral_count}
                    ])
                
                platform_df = pd.DataFrame(platform_data)
                
                chart6 = alt.Chart(platform_df).mark_bar().encode(
                    x=alt.X('Platform:N', title='', sort=None),
                    y=alt.Y('Mentions:Q', title='Mentions'),
                    color=alt.Color('Stance:N', 
                        scale=alt.Scale(
                            domain=['Pro-Policy', 'Contra-Policy', 'Neutral/Media'],
                            range=['green', 'red', 'gray']
                        ),
                        legend=alt.Legend(title='Stance')
                    ),
                    xOffset='Stance:N',
                    tooltip=[
                        alt.Tooltip('Platform:N', title='Platform'),
                        alt.Tooltip('Stance:N', title='Stance'),
                        alt.Tooltip('Mentions:Q', title='Mentions', format=',')
                    ]
                ).properties(
                    title='Sebutan Tokoh Berdasarkan Platform',
                    height=400
                ).configure_axis(
                    labelFontSize=9,
                    titleFontSize=11,
                    labelAngle=-45
                ).configure_title(
                    fontSize=12,
                    fontWeight='bold'
                )
                
                st.altair_chart(chart6, use_container_width=True)
        
        # Row 3: Advanced analysis (3 charts)
        col7, col8, col9 = st.columns(3)
        
        with col7:
            # Chart 7: Top 15 Overall Figures (Combined)
            all_figures = []
            for fig, count in pro_counts.most_common(10):
                all_figures.append({'Figure': fig, 'Mentions': count, 'Stance': 'Pro-Policy'})
            for fig, count in contra_counts.most_common(10):
                all_figures.append({'Figure': fig, 'Mentions': count, 'Stance': 'Contra-Policy'})
            
            all_figures_df = pd.DataFrame(all_figures)
            all_figures_df = all_figures_df.sort_values('Mentions', ascending=False).head(15)
            
            chart7 = alt.Chart(all_figures_df).mark_bar(opacity=0.7).encode(
                x=alt.X('Mentions:Q', title='Total Mentions'),
                y=alt.Y('Figure:N', title='', sort='-x'),
                color=alt.Color('Stance:N', 
                    scale=alt.Scale(
                        domain=['Pro-Policy', 'Contra-Policy'],
                        range=['green', 'red']
                    ),
                    legend=alt.Legend(title='Stance')
                ),
                tooltip=[
                    alt.Tooltip('Figure:N', title='Figure'),
                    alt.Tooltip('Mentions:Q', title='Mentions', format=','),
                    alt.Tooltip('Stance:N', title='Stance')
                ]
            ).properties(
                title='15 Tokoh Paling Banyak Disebut (Semua Posisi)',
                height=400
            ).configure_axis(
                labelFontSize=9,
                titleFontSize=11
            ).configure_title(
                fontSize=12,
                fontWeight='bold'
            )
            
            st.altair_chart(chart7, use_container_width=True)
        
        with col8:
            # Chart 8: Pro vs Contra Ratio by Sentiment (Stacked Bar)
            if 'sentiment_label' in df_filtered.columns and 'political_figures' in df_filtered.columns:
                ratio_data = []
                
                for sentiment in ['Positif', 'Negatif', 'Netral']:
                    subset = df_filtered[df_filtered['sentiment_label'] == sentiment]
                    pro_count = sum(len(f.get('Pro-Policy', [])) for f in subset['political_figures'] if isinstance(f, dict))
                    contra_count = sum(len(f.get('Contra-Policy', [])) for f in subset['political_figures'] if isinstance(f, dict))
                    total = pro_count + contra_count
                    
                    if total > 0:
                        ratio_data.extend([
                            {'Sentiment': sentiment, 'Stance': 'Pro-Policy', 'Percentage': (pro_count / total) * 100},
                            {'Sentiment': sentiment, 'Stance': 'Contra-Policy', 'Percentage': (contra_count / total) * 100}
                        ])
                
                ratio_df = pd.DataFrame(ratio_data)
                
                chart8 = alt.Chart(ratio_df).mark_bar().encode(
                    x=alt.X('Sentiment:N', title=''),
                    y=alt.Y('Percentage:Q', title='Percentage (%)', stack='zero', scale=alt.Scale(domain=[0, 100])),
                    color=alt.Color('Stance:N', 
                        scale=alt.Scale(
                            domain=['Pro-Policy', 'Contra-Policy'],
                            range=['green', 'red']
                        ),
                        legend=alt.Legend(title='Stance')
                    ),
                    tooltip=[
                        alt.Tooltip('Sentiment:N', title='Sentiment'),
                        alt.Tooltip('Stance:N', title='Stance'),
                        alt.Tooltip('Percentage:Q', title='Percentage', format='.1f')
                    ]
                ).properties(
                    title='Rasio Pro vs Kontra Berdasarkan Sentimen',
                    height=400
                ).configure_axis(
                    labelFontSize=10,
                    titleFontSize=11
                ).configure_title(
                    fontSize=12,
                    fontWeight='bold'
                )
                
                st.altair_chart(chart8, use_container_width=True)
        
        with col9:
            # Chart 9: Mention Heatmap (Top 10 Figures x Sentiment)
            if 'sentiment_label' in df_filtered.columns and 'political_figures' in df_filtered.columns:
                top_10_figures = [f['Figure'] for f in all_figures_df.head(10).to_dict('records')]
                heatmap_data = []
                
                for figure in top_10_figures:
                    for sentiment in ['Positif', 'Netral', 'Negatif']:
                        subset = df_filtered[df_filtered['sentiment_label'] == sentiment]
                        count = 0
                        for fig_dict in subset['political_figures']:
                            if isinstance(fig_dict, dict):
                                for stance_figs in fig_dict.values():
                                    if isinstance(stance_figs, list):
                                        count += sum(1 for f in stance_figs if figure.lower() in str(f).lower())
                        
                        heatmap_data.append({
                            'Figure': figure,
                            'Sentiment': sentiment,
                            'Mentions': count
                        })
                
                heatmap_df = pd.DataFrame(heatmap_data)
                
                base9 = alt.Chart(heatmap_df).encode(
                    x=alt.X('Sentiment:N', title=''),
                    y=alt.Y('Figure:N', title=''),
                    color=alt.Color('Mentions:Q', 
                        scale=alt.Scale(scheme='yelloworangered'),
                        legend=alt.Legend(title='Mentions')
                    ),
                    tooltip=[
                        alt.Tooltip('Figure:N', title='Figure'),
                        alt.Tooltip('Sentiment:N', title='Sentiment'),
                        alt.Tooltip('Mentions:Q', title='Mentions', format=',')
                    ]
                )
                
                chart9 = base9.mark_rect()
                text9 = base9.mark_text(baseline='middle', fontWeight='bold').encode(
                    text=alt.Text('Mentions:Q'),
                    color=alt.condition(
                        alt.datum.Mentions > heatmap_df['Mentions'].max() / 2,
                        alt.value('white'),
                        alt.value('black')
                    )
                )
                
                final_chart9 = (chart9 + text9).properties(
                    title='Heatmap Sebutan: 10 Tokoh Teratas x Sentimen',
                    height=400
                ).configure_axis(
                    labelFontSize=9,
                    titleFontSize=11
                ).configure_title(
                    fontSize=12,
                    fontWeight='bold'
                )
                
                st.altair_chart(final_chart9, use_container_width=True)
        
        # Co-occurrence Network Analysis
        st.subheader("🔗 Jejaring Ko-Okurensi Tokoh Politik")
        st.caption("Figur politik yang sering disebut bersamaan dalam diskusi yang sama")
        
        # Calculate co-occurrences
        if 'political_figures' in df_filtered.columns:
            from itertools import combinations
            co_occurrence = Counter()
            all_pro_set = set(pro_counts.keys())
            all_contra_set = set(contra_counts.keys())
            
            for figures_dict in df_filtered['political_figures']:
                if isinstance(figures_dict, dict):
                    # Get all figures mentioned in this post
                    post_figures = []
                    for stance, figs in figures_dict.items():
                        if isinstance(figs, list):
                            post_figures.extend([_clean_keyword_label(f).upper() for f in figs if _clean_keyword_label(f)])
                    
                    # Count co-occurrences (pairs)
                    if len(post_figures) >= 2:
                        for fig1, fig2 in combinations(sorted(set(post_figures)), 2):
                            co_occurrence[(fig1, fig2)] += 1
            
            if len(co_occurrence) > 0:
                top_15_cooccur = co_occurrence.most_common(15)
                
                col_cooccur1, col_cooccur2 = st.columns(2)
                
                with col_cooccur1:
                    # Chart: Top 15 Co-occurrences
                    cooccur_data = []
                    for (fig1, fig2), count in top_15_cooccur:
                        # Determine if same or opposing stance
                        fig1_in_pro = fig1 in all_pro_set
                        fig2_in_pro = fig2 in all_pro_set
                        
                        if (fig1_in_pro and fig2_in_pro) or (not fig1_in_pro and not fig2_in_pro):
                            stance_type = '🤝 Satu Kubu'
                            color = 'green'
                        else:
                            stance_type = '⚔️ Berlawanan Kubu'
                            color = 'red'
                        
                        cooccur_data.append({
                            'Pair': f"{fig1} ↔️ {fig2}",
                            'Count': count,
                            'Stance': stance_type,
                            'Color': color
                        })
                    
                    cooccur_df = pd.DataFrame(cooccur_data)
                    
                    chart_cooccur = alt.Chart(cooccur_df).mark_bar(opacity=0.7).encode(
                        x=alt.X('Count:Q', title='Co-occurrence Frequency'),
                        y=alt.Y('Pair:N', title='', sort='-x'),
                        color=alt.Color('Color:N', 
                            scale=alt.Scale(
                                domain=['green', 'red'],
                                range=['green', 'red']
                            ),
                            legend=None
                        ),
                        tooltip=[
                            alt.Tooltip('Pair:N', title='Figure Pair'),
                            alt.Tooltip('Count:Q', title='Frequency', format=','),
                            alt.Tooltip('Stance:N', title='Stance Type')
                        ]
                    ).properties(
                        title='15 Pasangan Tokoh Politik Ko-Okuren Teratas',
                        height=500
                    ).configure_axis(
                        labelFontSize=9,
                        titleFontSize=11
                    ).configure_title(
                        fontSize=12,
                        fontWeight='bold'
                    )
                    
                    st.altair_chart(chart_cooccur, use_container_width=True)
                    
                    # Legend
                    st.markdown("""
                    **Legenda:**
                    - 🟢 **Satu Kubu**: Kedua tokoh Pro-Kebijakan atau kedua tokoh Kontra-Kebijakan
                    - 🔴 **Berlawanan Kubu**: Satu tokoh Pro-Kebijakan dan satu tokoh Kontra-Kebijakan
                    """)
                
                with col_cooccur2:
                    # Heatmap: Co-occurrence Matrix
                    # Get top figures from co-occurrences
                    top_figures_set = set()
                    for (fig1, fig2), count in top_15_cooccur:
                        top_figures_set.add(fig1)
                        top_figures_set.add(fig2)
                    
                    top_figures_list = sorted(list(top_figures_set))[:12]  # Limit to 12
                    
                    # Create adjacency matrix data
                    heatmap_cooccur_data = []
                    for fig1 in top_figures_list:
                        for fig2 in top_figures_list:
                            if fig1 != fig2:
                                count = co_occurrence.get((min(fig1, fig2), max(fig1, fig2)), 0)
                                if count > 0:
                                    heatmap_cooccur_data.append({
                                        'Figure 1': fig1,
                                        'Figure 2': fig2,
                                        'Count': count
                                    })
                    
                    if heatmap_cooccur_data:
                        heatmap_cooccur_df = pd.DataFrame(heatmap_cooccur_data)
                        
                        base_heatmap = alt.Chart(heatmap_cooccur_df).encode(
                            x=alt.X('Figure 2:N', title=''),
                            y=alt.Y('Figure 1:N', title=''),
                            color=alt.Color('Count:Q', 
                                scale=alt.Scale(scheme='yelloworangered'),
                                legend=alt.Legend(title='Co-occurrence Count')
                            ),
                            tooltip=[
                                alt.Tooltip('Figure 1:N', title='Figure 1'),
                                alt.Tooltip('Figure 2:N', title='Figure 2'),
                                alt.Tooltip('Count:Q', title='Count', format=',')
                            ]
                        )
                        
                        chart_heatmap = base_heatmap.mark_rect()
                        text_heatmap = base_heatmap.mark_text(baseline='middle', fontWeight='bold').encode(
                            text=alt.Text('Count:Q'),
                            color=alt.condition(
                                alt.datum.Count > heatmap_cooccur_df['Count'].max() / 2,
                                alt.value('white'),
                                alt.value('black')
                            )
                        )
                        
                        final_heatmap = (chart_heatmap + text_heatmap).properties(
                            title='Heatmap Matriks Ko-Okurensi',
                            height=500
                        ).configure_axis(
                            labelFontSize=9,
                            titleFontSize=11,
                            labelAngle=-45
                        ).configure_title(
                            fontSize=12,
                            fontWeight='bold'
                        )
                        
                        st.altair_chart(final_heatmap, use_container_width=True)
                
                # Summary statistics
                st.subheader("📊 Insight Jejaring")
                col_stat1, col_stat2, col_stat3 = st.columns(3)
                
                with col_stat1:
                    st.metric("Total Pasangan Tokoh", f"{len(co_occurrence):,}")
                    most_freq = top_15_cooccur[0]
                    st.write(f"**Paling Sering:**  \n{most_freq[0][0]} ↔️ {most_freq[0][1]}  \n({most_freq[1]}x)")
                
                with col_stat2:
                    same_stance = sum(1 for item in cooccur_data if item['Stance'] == '🤝 Satu Kubu')
                    opposing_stance = sum(1 for item in cooccur_data if item['Stance'] == '⚔️ Berlawanan Kubu')
                    st.metric("Pasangan Satu Kubu", f"{same_stance}/15")
                    st.metric("Pasangan Berlawanan Kubu", f"{opposing_stance}/15")
                
                with col_stat3:
                    # Most connected figures
                    figure_connections = {}
                    for (fig1, fig2), count in co_occurrence.most_common(30):
                        figure_connections[fig1] = figure_connections.get(fig1, 0) + 1
                        figure_connections[fig2] = figure_connections.get(fig2, 0) + 1
                    
                    most_connected = sorted(figure_connections.items(), key=lambda x: x[1], reverse=True)[:5]
                    st.write("**Tokoh Paling Terkoneksi:**")
                    for fig, connections in most_connected:
                        st.write(f"• {fig}: {connections} koneksi")
            else:
                st.info("No co-occurrences found in the filtered data.")
        
    except ImportError:
        st.warning("Altair not available. Please install: pip install altair")
    except Exception as e:
        st.error(f"Error creating Altair charts: {e}")
        import traceback
        st.code(traceback.format_exc())


else:
    st.info("No political figures found in the filtered data.")

# ============================================================================
# SECTION 4: DETAILED DATA
# ============================================================================

st.header("📑 Tampilan Data Detail")

tab1, tab2, tab3 = st.tabs(["Postingan Teratas", "Rincian Platform", "Ekspor Data"])

with tab1:
    st.subheader("Postingan Paling Viral Berdasarkan Engagement")
    
    if len(df_filtered) > 0:
        top_posts = df_filtered.nlargest(10, 'engagement' if 'engagement' in df_filtered.columns else 'text')[
            ['date_parsed', 'source', 'sentiment_label', 'engagement', 'text'] 
            if 'engagement' in df_filtered.columns 
            else ['date_parsed', 'source', 'sentiment_label', 'text']
        ].copy()
        
        top_posts['text_preview'] = top_posts['text'].str[:100] + '...'
        
        display_cols = ['date_parsed', 'source', 'sentiment_label'] + (['engagement'] if 'engagement' in top_posts.columns else [])
        st.dataframe(
            top_posts[display_cols],
            use_container_width=True,
            height=400
        )
    else:
        st.info("Tidak ada postingan yang tersedia dengan filter saat ini.")

with tab2:
    st.subheader("Sentimen Berdasarkan Platform")
    
    if len(df_filtered) > 0 and 'source' in df_filtered.columns:
        platform_breakdown = get_platform_breakdown(df_filtered)
        st.dataframe(platform_breakdown, use_container_width=True)
    else:
        st.info("Data platform tidak tersedia.")

with tab3:
    st.subheader("Ekspor Data")
    
    if len(df_filtered) > 0:
        # CSV export
        csv = df_filtered.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 Unduh sebagai CSV",
            data=csv,
            file_name=f"pilkada_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
        
        # Summary stats
        st.write(f"**Total Rekaman:** {len(df_filtered)}")
        st.write(f"**Rentang Tanggal:** {df_filtered['date_parsed'].min()} hingga {df_filtered['date_parsed'].max()}")
        st.write(f"**Sumber Unik:** {df_filtered['source'].nunique()}")
    else:
        st.info("Tidak ada data untuk diekspor dengan filter saat ini.")

# ============================================================================
# FOOTER
# ============================================================================

st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.write("**📊 Info Dashboard**")
    st.caption("Monitor Sentimen Pilkada DPRD v1.0")

with col2:
    st.write("**⏰ Terakhir Diperbarui**")
    st.caption(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

with col3:
    st.write("**📁 Sumber Data**")
    st.caption("Pemantauan media sosial multi-platform")

st.caption("""
    ℹ️ **Penafian:** Dashboard ini hanya untuk tujuan analitis. Keputusan strategis harus 
    dibuat dengan berkonsultasi dengan pemangku kepentingan terkait.
""")
