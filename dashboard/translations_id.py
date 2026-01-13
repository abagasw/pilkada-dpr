# ============================================================================
# TERJEMAHAN BAHASA INDONESIA & PENJELASAN
# Dashboard Monitoring Sentimen Pilkada DPRD
# ============================================================================

# Judul dan Deskripsi Utama
DASHBOARD_TITLE = "📊 Dashboard Monitoring Sentimen Pilkada DPRD"
DASHBOARD_SUBTITLE = "Analisis Real-time Sentimen Publik terhadap Kebijakan Pilkada DPRD"

# Penjelasan Dashboard
DASHBOARD_DESCRIPTION = """
**Tentang Dashboard Ini:**

Dashboard ini menyediakan analisis komprehensif terhadap sentimen publik di media sosial terkait kebijakan Pilkada DPRD. 
Sistem ini menggunakan teknologi **Machine Learning** dan **Natural Language Processing** untuk:

1. 🎯 **Menganalisis Sentimen** - Mengklasifikasikan opini publik menjadi Positif, Negatif, atau Netral
2. 📊 **Memantau Tren** - Melacak perubahan sentimen dari waktu ke waktu
3. ⚠️ **Deteksi Risiko** - Mengidentifikasi potensi eskalasi aksi massa
4. 🤖 **Identifikasi Bot** - Mendeteksi akun tidak autentik dan buzzer
5. 📈 **Prediksi Aktivitas** - Memperkirakan volume diskusi 90 hari ke depan
6. 💡 **Rekomendasi Strategis** - Memberikan saran tindakan berdasarkan data

**Sumber Data:** Twitter/X, TikTok, Instagram, Facebook, YouTube, Threads, Berita Online
"""

# Sidebar
SIDEBAR_TITLE = "⚙️ Pengaturan Filter"
SIDEBAR_DESCRIPTION = "Sesuaikan parameter analisis sesuai kebutuhan Anda"

FILTER_DATE_RANGE = "📅 Rentang Tanggal"
FILTER_DATE_HELP = "Pilih periode waktu yang ingin dianalisis"

FILTER_PLATFORM = "📱 Platform Media Sosial"
FILTER_PLATFORM_HELP = "Pilih satu atau lebih platform untuk dianalisis"
FILTER_PLATFORM_ALL = "Semua Platform"

FILTER_SENTIMENT = "😊 Filter Sentimen"
FILTER_SENTIMENT_HELP = "Filter berdasarkan kategori sentimen"
FILTER_SENTIMENT_ALL = "Semua Sentimen"

FILTER_KEYWORDS = "🔍 Kata Kunci"
FILTER_KEYWORDS_HELP = "Filter postingan yang mengandung kata kunci tertentu (pisahkan dengan koma)"

FILTER_APPLY = "Terapkan Filter"
FILTER_RESET = "Reset Filter"

# Overview Metrics
OVERVIEW_TITLE = "📊 Ringkasan Utama"
OVERVIEW_DESCRIPTION = "Metrik kunci dari data yang dianalisis"

METRIC_TOTAL_POSTS = "Total Postingan"
METRIC_TOTAL_POSTS_HELP = "Jumlah total postingan yang dianalisis dalam periode terpilih"

METRIC_PLATFORMS = "Platform Aktif"
METRIC_PLATFORMS_HELP = "Jumlah platform media sosial yang memiliki data"

METRIC_DATE_RANGE = "Rentang Data"
METRIC_DATE_RANGE_HELP = "Periode waktu dari data yang tersedia"

METRIC_ENGAGEMENT = "Total Engagement"
METRIC_ENGAGEMENT_HELP = "Total likes, comments, dan shares dari semua postingan"

# Sentiment Analysis
SENTIMENT_TITLE = "🎭 Analisis Sentimen"
SENTIMENT_DESCRIPTION = """
**Penjelasan Analisis Sentimen:**

Sistem menggunakan model **IndoBERT** yang telah dilatih khusus untuk memahami bahasa Indonesia. 
Setiap postingan diklasifikasikan ke dalam 3 kategori:

- **Positif** 😊: Mendukung kebijakan, apresiasi, optimis
- **Negatif** 😠: Menolak kebijakan, kritik, pesimis  
- **Netral** 😐: Informatif, bertanya, tidak berpihak

**Interpretasi:**
- Sentimen negatif >50% → Perlu perhatian khusus
- Sentimen positif >40% → Dukungan cukup baik
- Sentimen netral tinggi → Publik masih mencari informasi
"""

SENTIMENT_DISTRIBUTION = "Distribusi Sentimen"
SENTIMENT_TREND = "Tren Sentimen dari Waktu ke Waktu"
SENTIMENT_BY_PLATFORM = "Sentimen per Platform"

# Risk Assessment
RISK_TITLE = "⚠️ Penilaian Risiko"
RISK_DESCRIPTION = """
**Metodologi Penilaian Risiko:**

Skor risiko dihitung berdasarkan kombinasi faktor:

1. **Sentimen Negatif** (40%) - Proporsi sentimen negatif
2. **Kata Kunci Aksi** (30%) - Frekuensi kata seperti "demo", "turun", "tolak"
3. **Engagement** (30%) - Tingkat interaksi publik

**Tingkat Risiko:**
- 🟢 **RENDAH** (0-40): Situasi normal, monitoring rutin
- 🟡 **SEDANG** (41-60): Perlu perhatian, tingkatkan komunikasi
- 🟠 **TINGGI** (61-80): Siaga, siapkan respons proaktif
- 🔴 **KRITIS** (81-100): Darurat, mobilisasi tim krisis
"""

RISK_SCORE = "Skor Risiko"
RISK_LEVEL = "Tingkat Risiko"
RISK_FACTORS = "Faktor Risiko"
RISK_RECOMMENDATIONS = "Rekomendasi Tindakan"

# Engagement Analysis
ENGAGEMENT_TITLE = "📊 Analisis Engagement"
ENGAGEMENT_DESCRIPTION = """
**Apa itu Engagement?**

Engagement mengukur seberapa aktif publik berinteraksi dengan konten:
- **Likes**: Indikator dukungan/persetujuan
- **Comments**: Tingkat diskusi dan keterlibatan
- **Shares**: Potensi viral dan jangkauan

**Insight:**
- Engagement tinggi + sentimen negatif = Risiko viral
- Engagement rendah = Isu belum menarik perhatian
- Engagement meningkat = Isu sedang trending
"""

# Bot Detection
BOT_TITLE = "🤖 Deteksi Bot & Buzzer"
BOT_DESCRIPTION = """
**Cara Kerja Deteksi Bot:**

Sistem mengidentifikasi akun tidak autentik berdasarkan:

1. **Frekuensi Posting** - Posting terlalu sering (>10/hari)
2. **Konten Duplikat** - Posting berulang >50%
3. **Pola Waktu** - Posting pada jam yang sama terus-menerus
4. **Engagement Rendah** - Banyak posting tapi sedikit interaksi

**Skor Bot:**
- 0-40: Kemungkinan akun asli
- 41-60: Perlu investigasi
- 61-100: Kemungkinan besar bot/buzzer

**Dampak:**
Bot dapat mendistorsi persepsi publik dan menciptakan ilusi dukungan/penolakan massal.
"""

# Topic Modeling
TOPIC_TITLE = "📚 Pemodelan Topik"
TOPIC_DESCRIPTION = """
**Apa itu Topic Modeling?**

Menggunakan algoritma **LDA (Latent Dirichlet Allocation)** untuk menemukan tema tersembunyi dalam diskusi.

**Manfaat:**
- Memahami apa yang dibicarakan publik
- Mengidentifikasi isu-isu spesifik
- Memetakan narasi yang berkembang

**Cara Membaca:**
- Setiap topik berisi kata-kata yang sering muncul bersama
- Ukuran kata di word cloud = tingkat kepentingan
- Distribusi dokumen = seberapa populer topik tersebut
"""

# Forecasting
FORECAST_TITLE = "🔮 Prediksi Aktivitas"
FORECAST_DESCRIPTION = """
**Model Prediksi ARIMA:**

Sistem menggunakan **ARIMA (AutoRegressive Integrated Moving Average)** untuk memprediksi volume posting 90 hari ke depan.

**Komponen:**
- **AR (AutoRegressive)**: Pola dari data historis
- **I (Integrated)**: Penyesuaian tren
- **MA (Moving Average)**: Rata-rata bergerak

**Confidence Interval 95%:**
- Rentang prediksi dengan tingkat kepercayaan 95%
- Semakin jauh prediksi, semakin lebar rentangnya

**Kegunaan:**
- Perencanaan kapasitas monitoring
- Alokasi sumber daya
- Antisipasi lonjakan aktivitas
"""

# Influential Users
INFLUENCER_TITLE = "🌟 Pengguna Berpengaruh"
INFLUENCER_DESCRIPTION = """
**Identifikasi Influencer:**

Skor pengaruh dihitung dari:
- **Engagement** (50%): Total interaksi yang didapat
- **Reach** (30%): Frekuensi posting
- **Action Keywords** (20%): Penggunaan kata-kata mobilisasi

**Tipe Influencer:**
1. **High Reach**: Posting sering, jangkauan luas
2. **High Action**: Sering gunakan kata-kata aksi
3. **Balanced**: Kombinasi reach dan engagement

**Strategi Engagement:**
- Pro-policy: Amplifikasi pesan
- Netral: Berikan informasi berimbang
- Contra-policy: Monitor dan dialog
"""

# Causal Modeling
CAUSAL_TITLE = "🧪 Analisis Kausalitas"
CAUSAL_DESCRIPTION = """
**Apa yang Membuat Konten Viral?**

Analisis korelasi untuk memahami faktor-faktor yang mendorong virality:

**Hipotesis yang Diuji:**
1. Sentimen negatif → Lebih viral?
2. Kata kunci aksi → Meningkatkan engagement?
3. Panjang teks → Pengaruh terhadap interaksi?
4. Waktu posting → Optimal hours?

**Multiplier Effect:**
- >1.5x: Faktor sangat berpengaruh
- 1.2-1.5x: Pengaruh moderat
- <1.2x: Pengaruh minimal

**Aplikasi:**
Memahami mekanisme viral untuk merancang strategi komunikasi yang efektif.
"""

# Model Validation
VALIDATION_TITLE = "🎯 Validasi Model"
VALIDATION_DESCRIPTION = """
**Uji Statistik:**

Memastikan keandalan analisis melalui:

1. **Bootstrap Confidence Intervals** - Estimasi ketidakpastian
2. **Temporal Stability** - Konsistensi model dari waktu ke waktu
3. **Sensitivity Analysis** - Dampak perubahan parameter

**Confidence Level 95%:**
Artinya kita 95% yakin nilai sebenarnya berada dalam rentang yang diberikan.

**Interpretasi:**
- Margin of error kecil = Prediksi lebih akurat
- Temporal stability tinggi = Model robust
- Sensitivity rendah = Model tidak mudah berubah
"""

# Platform Strategy
PLATFORM_TITLE = "📱 Strategi per Platform"
PLATFORM_DESCRIPTION = """
**Karakteristik Platform:**

Setiap platform memiliki dinamika berbeda:

- **Twitter/X**: Cepat, real-time, influencer-driven
- **TikTok**: Visual, viral, generasi muda
- **Instagram**: Visual, lifestyle, engagement tinggi
- **Facebook**: Demografis luas, sharing tinggi
- **YouTube**: Long-form, edukatif, kredibilitas
- **Threads**: Diskusi mendalam, komunitas

**Strategi Disesuaikan:**
Pendekatan komunikasi harus disesuaikan dengan karakteristik masing-masing platform.
"""

# Action Keywords
KEYWORDS_TITLE = "🔥 Kata Kunci Aksi"
KEYWORDS_DESCRIPTION = """
**Deteksi Kata Kunci Mobilisasi:**

Sistem memantau kata-kata yang mengindikasikan potensi aksi massa:

**Kategori:**
- **Aksi Langsung**: demo, turun, mogok, blokir
- **Penolakan**: tolak, lawan, boikot, hentikan
- **Mobilisasi**: rakyat, bersatu, bangkit, perjuangan

**Peringatan:**
- >30% postingan dengan kata kunci = Risiko tinggi
- Trending keywords = Narasi yang berkembang
- Kombinasi keywords = Potensi koordinasi

**Respons:**
Identifikasi dini memungkinkan respons proaktif sebelum eskalasi.
"""

# Political Figures
FIGURES_TITLE = "👥 Tokoh Politik"
FIGURES_DESCRIPTION = """
**Analisis Penyebutan Tokoh:**

Memantau tokoh politik yang paling sering disebut dan sentimen terhadap mereka.

**Insight:**
- Tokoh dengan sentimen negatif tinggi = Perlu perbaikan citra
- Tokoh dengan sentimen positif = Aset komunikasi
- Frekuensi penyebutan = Tingkat relevansi

**Strategi:**
- Leverage tokoh populer untuk kampanye
- Mitigasi sentimen negatif terhadap tokoh kunci
- Identifikasi opinion leaders
"""

# Export & Download
EXPORT_TITLE = "📥 Ekspor Data"
EXPORT_DESCRIPTION = "Unduh hasil analisis untuk laporan atau analisis lanjutan"
EXPORT_BUTTON = "Unduh CSV"

# Footer
FOOTER_TEXT = """
---
**Dashboard Monitoring Sentimen Pilkada DPRD**  
Powered by Machine Learning & Natural Language Processing  
Data diperbarui secara real-time dari berbagai platform media sosial

⚠️ **Disclaimer**: Analisis ini bersifat prediktif dan harus dikombinasikan dengan penilaian ahli untuk pengambilan keputusan.
"""

# Error Messages
ERROR_NO_DATA = "⚠️ Tidak ada data tersedia untuk filter yang dipilih. Silakan sesuaikan parameter filter."
ERROR_LOADING = "❌ Gagal memuat data. Silakan refresh halaman atau hubungi administrator."
ERROR_INSUFFICIENT_DATA = "⚠️ Data tidak cukup untuk analisis ini (minimum 30 hari diperlukan)."

# Success Messages
SUCCESS_FILTER_APPLIED = "✅ Filter berhasil diterapkan!"
SUCCESS_DATA_LOADED = "✅ Data berhasil dimuat!"
SUCCESS_EXPORT = "✅ Data berhasil diekspor!"

# Warning Messages
WARNING_HIGH_RISK = "⚠️ PERINGATAN: Tingkat risiko TINGGI terdeteksi. Segera ambil tindakan!"
WARNING_VIRAL_CONTENT = "⚠️ Konten viral dengan sentimen negatif terdeteksi!"
WARNING_BOT_DETECTED = "⚠️ Aktivitas bot/buzzer terdeteksi dalam jumlah signifikan!"

# Info Messages
INFO_LOADING = "⏳ Memuat data..."
INFO_PROCESSING = "⚙️ Memproses analisis..."
INFO_CALCULATING = "🔢 Menghitung metrik..."
