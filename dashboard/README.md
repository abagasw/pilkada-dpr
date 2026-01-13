# Pilkada DPRD Dashboard

Dashboard interaktif untuk analisis sentimen publik dan prediksi risiko terkait DPRD.

## Installation

```bash
pip install -r requirements.txt
```

## Running the Dashboard

```bash
streamlit run streamlit_app.py
```

### Using notebook exports

If `data/dashboard_data.pkl` exists (exported from `pilkada_dpr_analysis.ipynb`), the dashboard will automatically prefer it as the data source. Otherwise it falls back to `data/data_clean/df_unified_with_sentiment.csv`.

## Features

- Real-time sentiment analysis across multiple platforms
- Risk assessment and prediction
- Platform-specific insights
- Interactive visualizations
- Strategic recommendations

## Data Sources

- TikTok
- Facebook
- Instagram
- X (Twitter)
- YouTube
- Online News

Total posts analyzed: 29,848
Date range: 2025-01-01 to 2026-01-10

---

Generated: January 13, 2026
