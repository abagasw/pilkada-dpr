import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from collections import Counter
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import config


def create_sentiment_pie_chart(df):
    """Create pie chart for sentiment distribution"""
    if df is None or 'sentiment_label' not in df.columns:
        return None

    # Normalize labels defensively (handles trailing spaces / casing differences)
    s = df['sentiment_label'].astype(str).str.strip()
    s_lower = s.str.lower()
    s = s_lower.map({
        'positif': 'Positif',
        'negatif': 'Negatif',
        'netral': 'Netral',
    }).fillna(s)

    sentiment_counts = s.value_counts()

    # Ensure consistent order (and stable colors)
    order = ['Negatif', 'Netral', 'Positif']
    ordered_counts = {k: int(sentiment_counts.get(k, 0)) for k in order if int(sentiment_counts.get(k, 0)) > 0}
    if not ordered_counts:
        ordered_counts = {k: int(v) for k, v in sentiment_counts.items()}
    
    labels = list(ordered_counts.keys())
    values = [int(v) for v in ordered_counts.values()]
    colors_list = [config.SENTIMENT_COLORS.get(label, config.COLORS["netral"]) for label in labels]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker=dict(colors=colors_list),
        textposition='inside',
        textinfo='label+percent',
        hovertemplate='<b>%{label}</b><br>Jumlah: %{value}<br>Persentase: %{percent}<extra></extra>'
    )])
    
    fig.update_layout(
        title="📊 Distribusi Sentimen Publik",
        height=config.CHART_HEIGHT_MEDIUM,
        showlegend=True,
        hovermode='closest',
    )
    
    return fig


def create_sentiment_trend_chart(df):
    """Create line chart for sentiment trend over time"""
    if df is None or 'date_parsed' not in df.columns or 'sentiment_label' not in df.columns:
        return None
    
    # Filter out null dates
    df_with_dates = df[df['date_parsed'].notna()].copy()
    
    if len(df_with_dates) == 0:
        return None
    
    # Group by date and sentiment
    df_with_dates['date'] = df_with_dates['date_parsed'].dt.date
    daily_sentiment = df_with_dates.groupby(['date', 'sentiment_label']).size().unstack(fill_value=0)
    
    fig = go.Figure()
    
    sentiments_order = ['Positif', 'Negatif', 'Netral']
    for sentiment in sentiments_order:
        if sentiment in daily_sentiment.columns:
            fig.add_trace(go.Scatter(
                x=daily_sentiment.index,
                y=daily_sentiment[sentiment],
                name=sentiment,
                mode='lines+markers',
                line=dict(color=config.SENTIMENT_COLORS[sentiment], width=3),
                marker=dict(size=6),
                hovertemplate=f'<b>{sentiment}</b><br>Tanggal: %{{x}}<br>Jumlah: %{{y}}<extra></extra>'
            ))
    
    fig.update_layout(
        title="📈 Tren Sentimen Dari Waktu ke Waktu",
        xaxis_title="Tanggal",
        yaxis_title="Jumlah Postingan",
        hovermode=config.HOVER_MODE,
        height=config.CHART_HEIGHT_MEDIUM,
        legend=dict(x=1.02, y=1, xanchor='left', yanchor='top'),
    )
    
    return fig


def create_platform_sentiment_chart(df):
    """Create bar chart for sentiment by platform (notebook-aligned).

    The notebook visual shows absolute counts per platform (grouped bars).
    """
    if df is None or 'source' not in df.columns or 'sentiment_label' not in df.columns:
        return None

    sentiment_order = ['Positif', 'Negatif', 'Netral']
    counts = pd.crosstab(df['source'], df['sentiment_label'])
    counts = counts[[c for c in sentiment_order if c in counts.columns]]

    if counts.empty:
        return None

    # Match notebook ordering (pd.crosstab default is sorted index)
    counts = counts.reindex(sorted(counts.index))

    long_df = counts.reset_index().melt(
        id_vars='source',
        var_name='Sentimen',
        value_name='Jumlah'
    )

    fig = px.bar(
        long_df,
        x='source',
        y='Jumlah',
        color='Sentimen',
        barmode='group',
        category_orders={
            'Sentimen': sentiment_order,
            'source': list(counts.index),
        },
        color_discrete_map=config.SENTIMENT_COLORS,
        title="Distribusi Sentimen Berdasarkan Platform Media",
        labels={'source': 'Platform', 'Jumlah': 'Jumlah Postingan'},
    )
    
    fig.update_layout(
        height=config.CHART_HEIGHT_MEDIUM,
        hovermode=config.HOVER_MODE,
        legend=dict(title='Sentimen', x=1.02, y=1, xanchor='left', yanchor='top'),
    )

    fig.update_xaxes(tickangle=45)
    
    return fig


def create_keyword_chart(keyword_counts_dict, top_n=config.TOP_N_KEYWORDS):
    """Create bar chart for top keywords"""
    if not keyword_counts_dict or len(keyword_counts_dict) == 0:
        return None
    
    # Sort and get top N
    sorted_keywords = dict(sorted(
        keyword_counts_dict.items(),
        key=lambda x: x[1],
        reverse=True
    )[:top_n])
    
    fig = px.bar(
        x=list(sorted_keywords.values()),
        y=list(sorted_keywords.keys()),
        orientation='h',
        color=list(sorted_keywords.values()),
        color_continuous_scale='Reds',
        title=f"🔥 Top {top_n} Kata Kunci Aksi/Protes",
        labels={'x': 'Frekuensi', 'y': 'Kata Kunci'},
    )
    
    fig.update_layout(
        height=config.CHART_HEIGHT_LARGE,
        showlegend=False,
        hovermode=config.HOVER_MODE,
    )
    
    return fig


def create_political_figures_chart(pro_figures, contra_figures, top_n=10):
    """Create comparison chart for political figures"""
    # Prepare data
    pro_names = list(dict(pro_figures.most_common(top_n)).keys())
    pro_counts = list(dict(pro_figures.most_common(top_n)).values())
    
    contra_names = list(dict(contra_figures.most_common(top_n)).keys())
    contra_counts = list(dict(contra_figures.most_common(top_n)).values())
    
    fig = go.Figure()
    
    # Pro-policy
    fig.add_trace(go.Bar(
        y=pro_names,
        x=pro_counts,
        name='Pro-Kebijakan',
        orientation='h',
        marker=dict(color=config.COLORS["positif"]),
        hovertemplate='<b>%{y}</b><br>Mentions: %{x}<extra></extra>'
    ))
    
    # Contra-policy
    fig.add_trace(go.Bar(
        y=contra_names,
        x=[-c for c in contra_counts],  # Negative for left side
        name='Kontra-Kebijakan',
        orientation='h',
        marker=dict(color=config.COLORS["negatif"]),
        hovertemplate='<b>%{y}</b><br>Mentions: %{x}<extra></extra>'
    ))
    
    fig.update_layout(
        title=f"🎯 Top {top_n} Figur Politik - Pro vs Kontra",
        xaxis_title="Jumlah Mentions",
        yaxis_title="Figur Politik",
        barmode='relative',
        height=config.CHART_HEIGHT_LARGE,
        hovermode=config.HOVER_MODE,
        xaxis=dict(
            tickformat='d',
            tickvals=[-1000, -500, 0, 500, 1000],
            ticktext=['1000', '500', '0', '500', '1000']
        )
    )
    
    return fig


def create_engagement_chart(df):
    """Create engagement metrics visualization"""
    if df is None or 'engagement' not in df.columns:
        return None
    
    # Group by sentiment and calculate engagement stats
    engagement_by_sentiment = df.groupby('sentiment_label')['engagement'].agg([
        ('avg', 'mean'),
        ('max', 'max'),
        ('count', 'count')
    ]).reset_index()
    
    fig = px.bar(
        engagement_by_sentiment,
        x='sentiment_label',
        y='avg',
        color='sentiment_label',
        color_discrete_map=config.SENTIMENT_COLORS,
        title="💬 Rata-rata Engagement Berdasarkan Sentimen",
        labels={'sentiment_label': 'Sentimen', 'avg': 'Rata-rata Engagement'},
    )
    
    fig.update_layout(
        height=config.CHART_HEIGHT_MEDIUM,
        showlegend=False,
        hovermode=config.HOVER_MODE,
    )
    
    # Add count annotation
    for idx, row in engagement_by_sentiment.iterrows():
        fig.add_annotation(
            x=row['sentiment_label'],
            y=row['avg'],
            text=f"n={int(row['count'])}",
            showarrow=False,
            yshift=10
        )
    
    return fig


def create_risk_gauge(risk_score):
    """Create gauge chart for risk level"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=risk_score * 100,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Risk Score"},
        delta={'reference': 50, 'suffix': " points"},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': config.COLORS["critical"]},
            'steps': [
                {'range': [0, 30], 'color': config.COLORS["positif"]},
                {'range': [30, 50], 'color': config.COLORS["warning"]},
                {'range': [50, 70], 'color': "#F39C12"},
                {'range': [70, 100], 'color': config.COLORS["critical"]}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': risk_score * 100
            }
        }
    ))
    
    fig.update_layout(height=400)
    return fig


def create_keyword_sentiment_heatmap(df, keyword_dict, top_n=10):
    """Create heatmap of keywords vs sentiment"""
    if df is None or 'detected_keywords' not in df.columns:
        return None
    
    # Extract all keywords
    all_keywords = []
    keyword_sentiment_data = {s: {} for s in ['Positif', 'Negatif', 'Netral']}
    
    for idx, keywords_list in enumerate(df['detected_keywords']):
        sentiment = df.iloc[idx]['sentiment_label'] if 'sentiment_label' in df.columns else 'Unknown'
        if isinstance(keywords_list, list):
            for kw in keywords_list:
                all_keywords.append(kw)
                if kw not in keyword_sentiment_data[sentiment]:
                    keyword_sentiment_data[sentiment][kw] = 0
                keyword_sentiment_data[sentiment][kw] += 1
    
    # Get top keywords
    top_keywords = dict(Counter(all_keywords).most_common(top_n))
    
    # Create heatmap data
    heatmap_data = []
    for sentiment in ['Positif', 'Negatif', 'Netral']:
        row = [keyword_sentiment_data[sentiment].get(kw, 0) for kw in top_keywords.keys()]
        heatmap_data.append(row)
    
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data,
        x=list(top_keywords.keys()),
        y=['Positif', 'Negatif', 'Netral'],
        colorscale='Reds',
        hovertemplate='<b>%{y}</b> - <b>%{x}</b><br>Jumlah: %{z}<extra></extra>'
    ))
    
    fig.update_layout(
        title=f"🔥 Heatmap: Top {top_n} Keyword vs Sentimen",
        xaxis_title="Kata Kunci",
        yaxis_title="Sentimen",
        height=config.CHART_HEIGHT_MEDIUM,
    )
    
    return fig
