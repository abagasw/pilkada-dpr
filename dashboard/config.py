import os
from pathlib import Path

# ============================================================================
# PROJECT PATHS
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
DATA_CLEAN_PATH = PROJECT_ROOT / "data" / "data_clean"
DATA_ANALYSIS_PATH = PROJECT_ROOT / "data" / "analysis_results"
MODELS_PATH = PROJECT_ROOT / "models"

# Key data files
UNIFIED_DATA_CSV = DATA_CLEAN_PATH / "df_unified_with_sentiment.csv"

# Notebook-exported dashboard bundle (optional)
DASHBOARD_DATA_PKL = PROJECT_ROOT / "dashboard" / "data" / "dashboard_data.pkl"

# ============================================================================
# COLOR PALETTE
# ============================================================================

COLORS = {
    "positif": "#2ECC71",      # Green
    "negatif": "#E74C3C",      # Red
    "netral": "#95A5A6",       # Gray
    "accent": "#3498DB",       # Blue
    "warning": "#F39C12",      # Orange
    "critical": "#C0392B",     # Dark Red
}

SENTIMENT_COLORS = {
    "Positif": COLORS["positif"],
    "Negatif": COLORS["negatif"],
    "Netral": COLORS["netral"],
}

# ============================================================================
# PLATFORMS
# ============================================================================

PLATFORMS = {
    "tiktok": {"label": "TikTok", "icon": "🎵", "color": "#000000"},
    "facebook": {"label": "Facebook", "icon": "f", "color": "#1877F2"},
    "x": {"label": "X (Twitter)", "icon": "𝕏", "color": "#000000"},
    "instagram": {"label": "Instagram", "icon": "📷", "color": "#E1306C"},
    "youtube": {"label": "YouTube", "icon": "▶️", "color": "#FF0000"},
    "threads": {"label": "Threads", "icon": "@", "color": "#000000"},
    "online": {"label": "Online News", "icon": "📰", "color": "#0066CC"},
}

# ============================================================================
# SENTIMENT KEYWORDS
# ============================================================================

PROTEST_KEYWORDS = {
    "Aksi Protes": ["demo", "demonstrasi", "unjuk rasa", "aksi massa", "turun ke jalan"],
    "Penolakan": ["tolak", "menolak", "ditolak", "tidak setuju", "batalkan"],
    "Ancaman": ["akan turun", "siap turun", "akan demo", "siap demo", "jika disahkan"],
    "Kemarahan": ["marah", "murka", "geram", "berani-beraninya", "keterlaluan"],
    "Kekhawatiran": ["bahaya", "berbahaya", "mengkhawatirkan", "rawan", "chaos"],
    "Kritik Keras": ["gila", "bodoh", "tolol", "dungu", "konyol"],
    "Gerakan Massal": ["gerakan", "rakyat bangkit", "bersatu", "solidaritas"],
    "Anti-Demokrasi": ["kudeta", "otoriter", "diktator", "tiran", "zalim"],
    "Gangguan Keamanan": ["anarkis", "chaos", "riot", "kerusuhan", "bentrok"],
    "Desakan": ["desak", "tuntut", "minta", "harus", "wajib"],
}

# ============================================================================
# POLITICAL FIGURES
# ============================================================================

POLITICAL_FIGURES = {
    "Pro-Policy": {
        "Individuals": [
            "prabowo", "bahlil", "cak imin", "hasyim muzadi", "muhaimin iskandar",
            "mardani", "ardiansyah", "puan maharani", "ahy", "andi surya",
            "sugiono", "bambang soesatyo"
        ],
        "Parties": [
            "gerindra", "golkar", "pkb", "pan", "demokrat",
            "ppp", "pks", "nasdem", "perindo"
        ]
    },
    "Contra-Policy": {
        "Individuals": [
            "megawati", "gus dur", "ridwan kamil", "mahfud", "melki",
            "iyang", "bambang ribowo", "baso sudaryono", "joko widodo",
            "ganjar pranowo"
        ],
        "Parties": [
            "pdip", "gmni", "pdi-p", "buruh", "aktivis",
            "civil society", "ormas", "organisasi"
        ]
    },
    "Neutral": {
        "Institutions": [
            "dpr", "dprd", "kpu", "bawaslu", "mahkamah",
            "media", "pers", "wartawan", "jurnalis"
        ],
    }
}

# ============================================================================
# RISK LEVELS
# ============================================================================

RISK_LEVELS = {
    "LOW": {"label": "🟢 RENDAH", "color": COLORS["positif"], "threshold": 0.3},
    "MEDIUM": {"label": "🟡 SEDANG", "color": COLORS["warning"], "threshold": 0.5},
    "HIGH": {"label": "🟠 TINGGI", "color": COLORS["warning"], "threshold": 0.7},
    "CRITICAL": {"label": "🔴 KRITIS", "color": COLORS["critical"], "threshold": 1.0},
}

# ============================================================================
# CHARTS CONFIGURATION
# ============================================================================

CHART_HEIGHT_SMALL = 400
CHART_HEIGHT_MEDIUM = 500
CHART_HEIGHT_LARGE = 600

HOVER_MODE = "x unified"

# ============================================================================
# ANALYSIS PARAMETERS
# ============================================================================

TOP_N_FIGURES = 10
TOP_N_KEYWORDS = 15
TOP_N_COOCCURRENCE = 10

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# ============================================================================
# CACHE SETTINGS
# ============================================================================

CACHE_TTL = 3600  # 1 hour in seconds
MAX_CACHE_SIZE = 100  # MB
