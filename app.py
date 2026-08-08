import streamlit as st
import pandas as pd
import altair as alt
import glob
import os
import base64
import requests
from header_photo_data import HEADER_PHOTO_B64
from streamlit_lottie import st_lottie

# ==========================================
# 1. SETTING HALAMAN & INJEKSI CSS PREMIUM
# ==========================================
st.set_page_config(page_title="Dashboard SCO", page_icon="📦", layout="wide")

# ------------------------------------------
# PALET WARNA BRAND (dipakai konsisten di semua chart)
# ------------------------------------------
BRAND_TEAL = "#64ffda"
BRAND_TEAL_DARK = "#0f9b8e"
BRAND_GOLD = "#ffd166"
BRAND_CYAN = "#00b4d8"
BRAND_WHITE = "#ffffff"

# Palet kategorikal (dipakai utk chart per-SCO, per-layanan, dll)
BRAND_CATEGORICAL = [BRAND_TEAL, BRAND_GOLD, BRAND_CYAN, "#0096c7", "#48cae4", "#ffe066", "#80ffdb", "#ade8f4"]

# Palet sequential/gradient (dipakai utk chart yang di-rank by value, ex: Top Customer)
BRAND_SEQUENTIAL = ["#0f9b8e", "#14b8a6", "#2dd4bf", "#5eead4", "#99f6e4", "#64ffda"]
BRAND_SEQUENTIAL_GOLD = ["#7a5c00", "#b8860b", "#daa520", "#e8b923", "#ffd166", "#ffe699"]

def add_custom_css():
    st.markdown("""
    <style>
    /* Injeksi Google Fonts (Plus Jakarta Sans) */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
        color: #ffffff;
    }
    [data-testid="stHeader"] { background: rgba(0,0,0,0); }
    [data-testid="stSidebar"] {
        background: rgba(15, 32, 39, 0.6) !important;
        backdrop-filter: blur(15px);
        -webkit-backdrop-filter: blur(15px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        transition: transform 0.3s ease, box-shadow 0.3s ease, border 0.3s ease;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.5);
        border: 1px solid rgba(100, 255, 218, 0.4);
    }
    [data-testid="stMetricLabel"] { color: #a8b2d1 !important; font-weight: 600; font-size: 1.1rem; }
    [data-testid="stMetricValue"] { color: #64ffda !important; font-weight: 800; }
    [data-testid="stMetricDelta"] svg { fill: #00e676; }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px; background-color: rgba(255, 255, 255, 0.05);
        border-radius: 15px; padding: 10px; box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important; border-radius: 10px !important;
        color: #a8b2d1 !important; padding: 10px 20px; font-weight: 600;
        transition: all 0.3s ease;
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(100, 255, 218, 0.1) !important; color: #64ffda !important;
        border: 1px solid rgba(100, 255, 218, 0.3) !important; box-shadow: 0 0 15px rgba(100, 255, 218, 0.1);
    }
    h1, h2, h3, p, .stMarkdown { color: #ffffff !important; }
    
    .insight-box {
        background: linear-gradient(90deg, rgba(100, 255, 218, 0.15) 0%, rgba(100, 255, 218, 0.0) 100%);
        border-left: 5px solid #64ffda;
        padding: 15px 20px;
        border-radius: 5px 15px 15px 5px;
        margin-bottom: 25px;
        font-size: 1.1rem;
        color: #e6f1ff;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        transition: box-shadow 0.3s ease;
    }
    .insight-box:hover {
        box-shadow: 0 4px 20px rgba(100, 255, 218, 0.25);
    }
    .insight-box.insight-warning {
        background: linear-gradient(90deg, rgba(255, 209, 102, 0.15) 0%, rgba(255, 209, 102, 0.0) 100%);
        border-left: 5px solid #ffd166;
    }

    /* ============ POLISH: Chart container hover glow ============ */
    [data-testid="stVegaLiteChart"], [data-testid="stArrowVegaLiteChart"] {
        border-radius: 15px;
        padding: 10px;
        transition: box-shadow 0.35s ease, transform 0.25s ease, background 0.35s ease;
        border: 1px solid transparent;
    }
    [data-testid="stVegaLiteChart"]:hover, [data-testid="stArrowVegaLiteChart"]:hover {
        box-shadow: 0 8px 30px rgba(100, 255, 218, 0.15);
        border: 1px solid rgba(100, 255, 218, 0.25);
        background: rgba(255, 255, 255, 0.02);
    }
    
    /* pydeck map container glow */
    [data-testid="stDeckGlJsonChart"] {
        border-radius: 15px;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        transition: box-shadow 0.35s ease, border 0.35s ease;
    }
    [data-testid="stDeckGlJsonChart"]:hover {
        box-shadow: 0 12px 40px rgba(100, 255, 218, 0.2);
        border: 1px solid rgba(100, 255, 218, 0.3);
    }

    /* ============ POLISH: Dataframe/table rounded corners ============ */
    [data-testid="stDataFrame"] {
        border-radius: 15px;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.25);
        transition: box-shadow 0.3s ease, border 0.3s ease;
    }
    [data-testid="stDataFrame"]:hover {
        box-shadow: 0 10px 36px rgba(100, 255, 218, 0.15);
        border: 1px solid rgba(100, 255, 218, 0.25);
    }

    /* ============ FOOTER ============ */
    .app-footer {
        text-align: center;
        color: #a8b2d1;
        padding: 28px 0 10px 0;
        font-size: 0.85rem;
        opacity: 0.8;
        border-top: 1px solid rgba(255,255,255,0.08);
        margin-top: 30px;
    }
    .app-footer b { color: #64ffda; }

    /* ============ st.toast styling nudge ============ */
    [data-testid="stToast"] {
        background: rgba(15, 32, 39, 0.95) !important;
        border: 1px solid rgba(100, 255, 218, 0.3) !important;
        border-radius: 12px !important;
    }
    </style>
    """, unsafe_allow_html=True)

add_custom_css()

# ==========================================
# ANIMASI LOTTIE
# ==========================================
@st.cache_data
def load_lottieurl(url: str):
    try:
        r = requests.get(url)
        if r.status_code != 200: return None
        return r.json()
    except:
        return None

lottie_empty = load_lottieurl("https://lottie.host/8c0678a3-2c1b-4171-af63-1463132e01df/p3F2Q1MTh5.json")


# ==========================================
# 2. TEMA ALTAIR GLOBAL (SEAMLESS BACKGROUND)
# ==========================================
def altair_dark_theme():
    return {
        "config": {
            "background": "transparent",
            "view": {"stroke": "transparent"},
            "axis": {
                "labelColor": "#a8b2d1",
                "titleColor": "#a8b2d1",
                "gridColor": "rgba(255,255,255,0.05)",
                "domainColor": "rgba(255,255,255,0.1)",
                "tickColor": "rgba(255,255,255,0.1)"
            },
            "legend": {
                "labelColor": "#a8b2d1",
                "titleColor": "#a8b2d1"
            },
            "title": {"color": "#ffffff"},
            "range": {
                "category": BRAND_CATEGORICAL,
                "heatmap": BRAND_SEQUENTIAL,
                "ramp": BRAND_SEQUENTIAL
            }
        }
    }
alt.themes.register("dark_custom", altair_dark_theme)
alt.themes.enable("dark_custom")

# ==========================================
# NOTIFIKASI TOAST (Hanya muncul sekali saat web di-load)
# ==========================================
if 'welcome_toast' not in st.session_state:
    st.toast('🚀 Selamat datang di Dashboard KP Grand Taruma! Memuat data analitik...', icon='🔥')
    st.session_state['welcome_toast'] = True

# ==========================================
# FUNGSI KELOLA DATA & STANDARISASI
# ==========================================
def clean_destination(dest, kpi_type):
    if pd.isna(dest) or str(dest).strip() == "-" or str(dest).strip() == "":
        return "-"
    dest_str = str(dest).strip().upper()
    
    if kpi_type == "Cashless":
        code = dest_str[:3]
        mapping = {
            'CGK': 'JAKARTA', 'BKI': 'BEKASI', 'BOO': 'BOGOR', 'DPK': 'DEPOK', 'TGR': 'TANGERANG',
            'BDO': 'BANDUNG', 'SMI': 'SUKABUMI', 'SOC': 'SOLO', 'SRG': 'SEMARANG', 'JOG': 'YOGYAKARTA',
            'SUB': 'SURABAYA', 'MLG': 'MALANG', 'DPS': 'BALI', 'KNO': 'MEDAN', 'MES': 'MEDAN',
            'PDG': 'PADANG', 'PKU': 'PEKANBARU', 'PLM': 'PALEMBANG', 'BPN': 'BALIKPAPAN',
            'BJM': 'BANJARMASIN', 'PNK': 'PONTIANAK', 'UPG': 'MAKASSAR', 'MDC': 'MANADO',
            'BTJ': 'BANDA ACEH', 'MGL': 'MAGELANG', 'TKG': 'BANDAR LAMPUNG', 'CBN': 'CIREBON',
            'KDI': 'KENDARI', 'AMQ': 'AMBON', 'DJJ': 'JAYAPURA', 'TRK': 'TARAKAN'
        }
        return mapping.get(code, code)
    else:
        return dest_str.split(',')[0].strip()

# FIX 3: Tambahin parameter get_mtime buat memecahkan masalah cache yang nyangkut
def get_file_mtimes(file_list):
    mtimes = []
    for f in file_list:
        if isinstance(f, str) and os.path.exists(f):
            mtimes.append(os.path.getmtime(f))
        elif hasattr(f, 'size'):
            mtimes.append(f.size)
    return tuple(mtimes)

@st.cache_data
def load_unified_data(file_list, _mtimes):
    all_raw = []
    all_rata2 = []
    load_errors = []  

    for f in file_list:
        fname_for_error = f.name if hasattr(f, 'name') else os.path.basename(str(f))
        try:
            if hasattr(f, 'name'):
                filename = f.name.lower()
                xls_input = f
            else:
                filename = os.path.basename(f).lower()
                xls_input = f
            
            if "cashless" in filename: kpi_type = "Cashless"
            elif "kredit auto" in filename: kpi_type = "Kredit Auto"
            elif "kredit manual" in filename: kpi_type = "Kredit Manual" 
            elif "cash" in filename: kpi_type = "Cash"
            else: kpi_type = "Cash"
                
            xls = pd.ExcelFile(xls_input)
            
            if "Raw Data" in xls.sheet_names:
                df = pd.read_excel(xls, "Raw Data")
                df_std = pd.DataFrame(index=df.index) 
                df_std['KPI'] = kpi_type
                
                # Biar bisa ngetrack bulan data ini aslinya dari mana (untuk Fix Tab 3)
                df_std['Source_File'] = filename
                
                col_sco = 'User id' if 'User id' in df.columns else ('User Id' if 'User Id' in df.columns else None)
                df_std['SCO'] = df[col_sco] if col_sco else "UNKNOWN"
                
                col_date = 'Created date' if 'Created date' in df.columns else 'Date'
                # FIX 2: Tambah dayfirst=True biar format Indo DD/MM/YYYY gak ketuker jadi format Bule
                df_std['Date'] = pd.to_datetime(df[col_date], errors='coerce', dayfirst=True)
                
                col_rev = 'Cnote Amount' if 'Cnote Amount' in df.columns else 'Amount'
                df_std['Revenue'] = pd.to_numeric(df[col_rev], errors='coerce').fillna(0)
                
                df_std['Weight'] = pd.to_numeric(df['Weight'] if 'Weight' in df.columns else 0, errors='coerce').fillna(0)

                # FIX 4: Qty dihapus sesuai instruksi

                if 'Insurance' in df.columns:
                    df_std['Insurance'] = pd.to_numeric(df['Insurance'], errors='coerce').fillna(0)
                else:
                    df_std['Insurance'] = 0.0

                col_srv = 'Service' if 'Service' in df.columns else ('Services' if 'Services' in df.columns else None)
                df_std['Service'] = df[col_srv] if col_srv else "-"
                
                df_std['Customer'] = df['Shipper Name'].fillna("-") if 'Shipper Name' in df.columns else "-"
                
                df_std['Destination'] = df['Destination'].apply(lambda x: clean_destination(x, kpi_type)) if 'Destination' in df.columns else "-"
                
                if kpi_type == "Cashless":
                    col_pay = 'Marketplace_Clean' if 'Marketplace_Clean' in df.columns else ('Marketplace' if 'Marketplace' in df.columns else None)
                    df_std['Payment_Method'] = df[col_pay].fillna("Lainnya") if col_pay else "Lainnya"
                elif kpi_type == "Cash":
                    df_std['Payment_Method'] = df['Payment type'].fillna("Cash") if 'Payment type' in df.columns else "Cash"
                else:
                    df_std['Payment_Method'] = kpi_type
                    
                all_raw.append(df_std)
            
            if kpi_type == "Cash" and "Rata-Rata Hari Masuk" in xls.sheet_names:
                df_r = pd.read_excel(xls, "Rata-Rata Hari Masuk")
                # Tambahin info source file juga buat difilter nanti (Fix Tab 3)
                df_r['Source_File'] = filename 
                all_rata2.append(df_r)

        except Exception as e:
            load_errors.append(f"{fname_for_error}: {e}")

    df_master = pd.concat(all_raw, ignore_index=True) if all_raw else pd.DataFrame()
    df_rata2_master = pd.concat(all_rata2, ignore_index=True) if all_rata2 else pd.DataFrame()

    return df_master, df_rata2_master, load_errors

def format_rupiah(val):
    return f"Rp {val:,.0f}".replace(",", ".")

# ------------------------------------------
# POLISH: helper buat highlight baris juara (rank 1) di tabel ranking
# ------------------------------------------
def style_top_row(df):
    """Kasih highlight emas tipis di baris pertama (baris juara) sebuah tabel ranking."""
    def _highlight(row):
        if row.name == df.index[0]:
            return ['background-color: rgba(255, 209, 102, 0.18); font-weight: 700;'] * len(row)
        return [''] * len(row)
    return df.style.apply(_highlight, axis=1)

# ==========================================
# SIDEBAR KIRI: SISTEM HYBRID & GAMBAR
# ==========================================
with st.sidebar:
    # 1. Gambar Logo Asli aja yang dipake (Animasi rusak dicabut biar bersih)
    st.image("https://cdn-icons-png.flaticon.com/512/3063/3063822.png", width=100)

st.sidebar.header("📁 Data Source (Hybrid)")
st.sidebar.markdown("<p style='font-size:0.9rem; color:#a8b2d1;'>Sistem akan otomatis baca dari server/GitHub. Upload file hanya jika ingin menimpa data sementara.</p>", unsafe_allow_html=True)

uploaded_files = st.sidebar.file_uploader("Upload File Bypass (.xlsx)", type=['xlsx'], accept_multiple_files=True)

if uploaded_files:
    active_files = uploaded_files
else:
    list_local = glob.glob("*.xlsx")
    list_local = [f for f in list_local if not f.startswith("~$")]
    active_files = list_local

if not active_files:
    if lottie_empty: st_lottie(lottie_empty, height=200, key="empty_file")
    st.error("⚠️ Data server kosong dan belum ada file yang di-upload.")
    st.stop()

# Terapin fix cache di pemanggilan data
df_global, _, global_load_errors = load_unified_data(active_files, get_file_mtimes(active_files))

if df_global.empty:
    st.error("Gagal membaca data. Pastikan sheet 'Raw Data' ada di dalam file.")
    st.stop()

if global_load_errors:
    with st.sidebar.expander(f"⚠️ {len(global_load_errors)} file gagal dibaca", expanded=False):
        for err in global_load_errors:
            st.caption(f"❌ {err}")

st.sidebar.markdown("---")
st.sidebar.header("🔍 Filter Analytics")

available_kpis = df_global['KPI'].unique().tolist()
selected_kpi = st.sidebar.selectbox("📊 Pilih Pilar KPI:", options=available_kpis)

list_file_kpi = []
for f in active_files:
    fname = f.name.lower() if hasattr(f, 'name') else os.path.basename(f).lower()
    if selected_kpi == "Cash" and "cashless" not in fname and "kredit" not in fname:
        list_file_kpi.append(f)
    elif selected_kpi == "Cashless" and "cashless" in fname:
        list_file_kpi.append(f)
    elif selected_kpi not in ["Cash", "Cashless"] and selected_kpi.lower() in fname:
        list_file_kpi.append(f)

if not list_file_kpi:
    st.sidebar.warning(f"File untuk KPI {selected_kpi} tidak ditemukan.")
    st.stop()

# Langsung Bypass Filter (Terapin fix cache)
selected_files = list_file_kpi
df_active, df_rata2_active, _ = load_unified_data(selected_files, get_file_mtimes(selected_files))

# --- SABUK PENGAMAN (FIX ERROR) ---
if df_active.empty:
    st.warning("⚠️ Data kosong! Gagal memproses file untuk KPI yang dipilih.")
    st.stop()
# ----------------------------------

df_active = df_active.dropna(subset=['Date', 'SCO'])
df_active['Date_Only'] = df_active['Date'].dt.date

df_kpi_only = df_active[df_active['KPI'] == selected_kpi]

if df_kpi_only.empty:
    st.warning("Data untuk KPI ini kosong pada file yang dipilih.")
    st.stop()

min_date = df_kpi_only['Date_Only'].min()
max_date = df_kpi_only['Date_Only'].max()
date_range = st.sidebar.date_input("📅 Rentang Tanggal", value=(min_date, max_date), min_value=min_date, max_value=max_date)
if len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = end_date = date_range[0]
    
list_sco = df_kpi_only['SCO'].dropna().unique().tolist()
selected_sco = st.sidebar.multiselect("👨‍💼 Pilih SCO (Bisa >1):", options=list_sco, default=[], help="Kosongkan buat nampilin semua")

mask_date = (df_kpi_only['Date_Only'] >= start_date) & (df_kpi_only['Date_Only'] <= end_date)
df_filtered = df_kpi_only[mask_date].copy()
if selected_sco:
    df_filtered = df_filtered[df_filtered['SCO'].isin(selected_sco)]

st.sidebar.markdown("---")
st.sidebar.header("📥 Export Data")
csv_data = df_filtered.to_csv(index=False).encode('utf-8')
st.sidebar.download_button(label=f"Download Rekap {selected_kpi} (CSV)", data=csv_data, file_name=f"Data_Export_{selected_kpi}.csv", mime='text/csv')

# ==========================================
# TAMPILAN DASHBOARD (HERO HEADER BANNER)
# ==========================================
# FIX 5: background-position diubah ke center 20% biar muka & seragam orangnya masuk frame.
st.markdown(f"""
<div style="
    position: relative;
    width: 100%;
    padding: 110px 32px;
    border-radius: 20px;
    margin-bottom: 25px;
    background: linear-gradient(90deg, rgba(15, 32, 39, 0.95) 0%, rgba(15, 32, 39, 0.82) 55%, rgba(15, 32, 39, 0.35) 100%), 
                url('data:image/jpeg;base64,{HEADER_PHOTO_B64}');
    background-size: cover;
    background-position: center 100%;
    border: 1px solid rgba(100, 255, 218, 0.35);
    box-shadow: 0 10px 35px rgba(100, 100, 100, 100);
    overflow: hidden;
">
    <div style="position: relative; z-index: 2; max-width: 75%;">
        <div style="font-size: 2.2rem; font-weight: 800; color: #ffffff; line-height: 1.2; text-shadow: 0 2px 10px rgba(0,0,0,0.85);">
            📊 Dashboard Enterprise KP Grand Taruma
        </div>
        <div style="color: #64ffda; font-size: 1.15rem; font-weight: 700; margin-top: 8px; text-shadow: 0 2px 8px rgba(0,0,0,0.85);">
            By Yusuf Zulkarnaen
        </div>
        <div style="color: #e6f1ff; font-size: 0.95rem; font-weight: 600; margin-top: 14px; opacity: 0.95;">
            Sedang menampilkan analitik untuk pilar: <b style="color: #ffd166; text-transform: uppercase;">{selected_kpi}</b>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

if df_filtered.empty:
    if lottie_empty: st_lottie(lottie_empty, height=250, key="empty_filtered")
    st.warning("⚠️ Data kosong pada rentang waktu atau SCO yang dipilih.")
    st.stop()

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "📈 Dashboard Utama", 
    "🏆 Top Customer", 
    f"👨‍💼 Kinerja SCO", 
    "⏰ Pola Waktu", 
    "💳 Metode Pembayaran & Layanan",
    "📍 Pemetaan Destinasi",
    f"🚀 Tren {selected_kpi}",
    "🌐 Executive Summary"
])

# ==========================================
# TAB 1: DASHBOARD UTAMA
# ==========================================
with tab1:
    total_resi = len(df_filtered)
    total_rev = df_filtered['Revenue'].sum()
    total_berat = df_filtered['Weight'].sum()
    rata_transaksi = total_rev / total_resi if total_resi > 0 else 0
    
    rekap_user = df_filtered.groupby('SCO')['Revenue'].sum().sort_values(ascending=False)
    best_user = rekap_user.index[0] if not rekap_user.empty else "-"
    best_user_rev = rekap_user.iloc[0] if not rekap_user.empty else 0
    
    sco_aktif = df_filtered['SCO'].nunique()
    srv_top = df_filtered['Service'].mode()[0] if not df_filtered['Service'].empty else "-"
    pay_top = df_filtered['Payment_Method'].mode()[0] if not df_filtered['Payment_Method'].empty else "-"
    
    share_best = (best_user_rev / total_rev * 100) if total_rev > 0 else 0
    if share_best >= 40:
        insight_icon = "🔥"
        insight_class = "insight-box"
    else:
        insight_icon = "💡"
        insight_class = "insight-box"

    st.markdown(f"""
    <div class="{insight_class}">
        <b>{insight_icon} Automated Insight:</b> Berdasarkan periode yang dipilih, <b>{best_user}</b> memimpin kontribusi SCO dengan revenue <b>{format_rupiah(best_user_rev)}</b>. 
        Secara keseluruhan, layanan <b>{srv_top}</b> paling sering diandalkan oleh pelanggan.
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📦 TOTAL TRANSAKSI", f"{total_resi} Resi")
    c2.metric("💰 TOTAL REVENUE", format_rupiah(total_rev), delta="Target On Track")
    c3.metric("📈 RATA-RATA / TRANSAKSI", format_rupiah(rata_transaksi))
    c4.metric("⚖️ TOTAL BERAT", f"{total_berat:,.1f} Kg")
    
    st.markdown("<br>", unsafe_allow_html=True)
    c5, c6, c7, c8 = st.columns(4)
    c5.metric("🏆 BEST SCO", f"{best_user}", delta=f"{total_resi} Resi Dikelola")
    c6.metric("👥 SCO AKTIF", f"{sco_aktif} Orang")
    c7.metric("🚚 LAYANAN TERLARIS", srv_top)
    c8.metric("💳 METODE FAVORIT", pay_top)

    total_insurance_val = df_filtered['Insurance'].sum() if 'Insurance' in df_filtered.columns else 0
    ada_asuransi = selected_kpi == "Cash" and total_insurance_val > 0

    if ada_asuransi:
        st.markdown("<br>", unsafe_allow_html=True)
        c9, c10 = st.columns(2)
        resi_berasuransi = (df_filtered['Insurance'] > 0).sum()
        pct_berasuransi = (resi_berasuransi / total_resi * 100) if total_resi > 0 else 0
        c9.metric("🛡️ TRANSAKSI BERASURANSI", f"{pct_berasuransi:,.1f}%", delta=f"{resi_berasuransi} dari {total_resi} Resi")
        c10.metric("💰 TOTAL PREMI ASURANSI", format_rupiah(total_insurance_val))

    st.markdown("---")
    kiri, kanan = st.columns(2)
    with kiri:
        st.subheader(f"📈 Tren Harian ({selected_kpi})")
        harian = df_filtered.groupby('Date_Only', as_index=False).size().rename(columns={'size':'Transaksi'})
        chart_tren = alt.Chart(harian).mark_line(point=True, color=BRAND_TEAL, strokeWidth=3).encode(
            x=alt.X('Date_Only:T', title='Tanggal'), y=alt.Y('Transaksi:Q', title='Jumlah Resi'), tooltip=['Date_Only', 'Transaksi']
        ).properties(height=300)
        st.altair_chart(chart_tren, use_container_width=True)
        
    with kanan:
        st.subheader("🏅 Ranking Revenue SCO")
        rekap_user_df = df_filtered.groupby('SCO', as_index=False).agg({'Revenue':'sum'}).rename(columns={'Revenue':'Pendapatan'}).sort_values(by='Pendapatan', ascending=False)
        chart_sco = alt.Chart(rekap_user_df).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
            x=alt.X('SCO:N', sort='-y', title='Nama SCO'), y=alt.Y('Pendapatan:Q', title='Total Revenue (Rp)'),
            color=alt.Color('SCO:N', scale=alt.Scale(range=BRAND_CATEGORICAL), legend=None), tooltip=['SCO', 'Pendapatan']
        ).properties(height=300)
        st.altair_chart(chart_sco, use_container_width=True)
        
    st.markdown("---")
    bawah1, bawah2 = st.columns(2)
    with bawah1:
        st.subheader(f"💵 Rata-Rata Revenue per Resi (Harian)")
        rata_harian = df_filtered.groupby('Date_Only', as_index=False).agg(Total_Rev=('Revenue', 'sum'), Total_Resi=('Revenue', 'count'))
        rata_harian['Rata-Rata'] = rata_harian['Total_Rev'] / rata_harian['Total_Resi']
        chart_avg = alt.Chart(rata_harian).mark_area(
            opacity=0.3,
            color=alt.Gradient(gradient='linear', stops=[alt.GradientStop(color=BRAND_TEAL, offset=0), alt.GradientStop(color='rgba(0,0,0,0)', offset=1)], x1=1, x2=1, y1=1, y2=0)
        ).encode(
            x=alt.X('Date_Only:T', title='Tanggal'), y=alt.Y('Rata-Rata:Q', title='Rata-Rata Revenue (Rp)'), tooltip=['Date_Only', 'Rata-Rata']
        )
        line_avg = alt.Chart(rata_harian).mark_line(color=BRAND_TEAL, strokeWidth=3).encode(x='Date_Only:T', y='Rata-Rata:Q')
        st.altair_chart((chart_avg + line_avg).properties(height=300), use_container_width=True)

    with bawah2:
        st.subheader("📦 Top 5 Destinasi Pengiriman")
        dest_df_quick = df_filtered[df_filtered['Destination'] != '-'].groupby('Destination', as_index=False).size().rename(columns={'size':'Total Resi'}).sort_values('Total Resi', ascending=False).head(5)
        chart_dest_quick = alt.Chart(dest_df_quick).mark_bar(cornerRadiusTopRight=5, cornerRadiusBottomRight=5, color=BRAND_CYAN).encode(
            x=alt.X('Total Resi:Q', title='Jumlah Transaksi'),
            y=alt.Y('Destination:N', sort='-x', title='Daerah Tujuan'),
            tooltip=['Destination', 'Total Resi']
        ).properties(height=300)
        st.altair_chart(chart_dest_quick, use_container_width=True)

# ==========================================
# TAB 2: TOP CUSTOMER
# ==========================================
with tab2:
    st.header(f"🏆 Analisis Top Customer ({selected_kpi})")
    df_cust = df_filtered[df_filtered['Customer'] != '-']
    if df_cust.empty:
        st.info("Tidak ada data Customer (Shipper Name) di rentang waktu/SCO ini.")
    else:
        cust_rev_rank = df_cust.groupby('Customer')['Revenue'].sum().sort_values(ascending=False)
        n_unique_cust = df_cust['Customer'].nunique()
        top1_cust = cust_rev_rank.index[0]
        top1_cust_rev = cust_rev_rank.iloc[0]
        total_cust_rev = cust_rev_rank.sum()
        share_top1 = (top1_cust_rev / total_cust_rev * 100) if total_cust_rev > 0 else 0

        if share_top1 >= 30:
            st.markdown(f"""
            <div class="insight-box insight-warning">
                <b>⚠️ Automated Insight:</b> Dari <b>{n_unique_cust} customer unik</b>, <b>{top1_cust}</b> menyumbang <b>{share_top1:,.1f}%</b>
                dari total revenue customer (<b>{format_rupiah(top1_cust_rev)}</b>). Konsentrasi sebesar ini berarti revenue cukup bergantung
                pada satu customer besar — perlu strategi retensi khusus supaya order-nya gak hilang.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="insight-box">
                <b>💡 Automated Insight:</b> Dari <b>{n_unique_cust} customer unik</b>, customer teratas <b>{top1_cust}</b> berkontribusi
                <b>{share_top1:,.1f}%</b> dari total revenue customer (<b>{format_rupiah(top1_cust_rev)}</b>). Distribusi revenue relatif
                merata, tidak bergantung pada satu customer saja.
            </div>
            """, unsafe_allow_html=True)

        col_rev, col_con = st.columns(2)
        with col_rev:
            st.subheader("🥇 Top 10 Customer (By Revenue)")
            top_rev = df_cust.groupby('Customer', as_index=False).agg({'Revenue':'sum', 'SCO':'count'}).rename(columns={'Revenue':'Total Belanja', 'SCO':'Total Resi'}).sort_values(by='Total Belanja', ascending=False).head(10)
            chart_rev = alt.Chart(top_rev).mark_bar(cornerRadiusTopRight=5, cornerRadiusBottomRight=5).encode(
                x=alt.X('Total Belanja:Q', title='Total Revenue (Rp)'), y=alt.Y('Customer:N', sort='-x', title='Customer'),
                color=alt.Color('Total Belanja:Q', scale=alt.Scale(range=BRAND_SEQUENTIAL), legend=None), tooltip=['Customer', 'Total Belanja', 'Total Resi']
            ).properties(height=400)
            st.altair_chart(chart_rev, use_container_width=True)
            
            top_rev_tabel = top_rev.copy()
            top_rev_tabel['Total Belanja'] = top_rev_tabel['Total Belanja'].apply(format_rupiah)
            top_rev_tabel.index = range(1, len(top_rev_tabel) + 1)
            st.dataframe(style_top_row(top_rev_tabel), use_container_width=True)

        with col_con:
            st.subheader("🔢 Top 10 Customer (By Connote)")
            top_con = df_cust.groupby('Customer', as_index=False).agg({'SCO':'count', 'Revenue':'sum'}).rename(columns={'SCO':'Total Resi', 'Revenue':'Total Belanja'}).sort_values(by='Total Resi', ascending=False).head(10)
            chart_con = alt.Chart(top_con).mark_bar(cornerRadiusTopRight=5, cornerRadiusBottomRight=5).encode(
                x=alt.X('Total Resi:Q', title='Total Transaksi (Resi)'), y=alt.Y('Customer:N', sort='-x', title='Customer'),
                color=alt.Color('Total Resi:Q', scale=alt.Scale(range=BRAND_SEQUENTIAL_GOLD), legend=None), tooltip=['Customer', 'Total Resi', 'Total Belanja']
            ).properties(height=400)
            st.altair_chart(chart_con, use_container_width=True)
            
            top_con_tabel = top_con.copy()
            top_con_tabel['Total Belanja'] = top_con_tabel['Total Belanja'].apply(format_rupiah)
            top_con_tabel.index = range(1, len(top_con_tabel) + 1)
            st.dataframe(style_top_row(top_con_tabel), use_container_width=True)

# ==========================================
# TAB 3: KINERJA SCO
# ==========================================
with tab3:
    if selected_kpi == "Cash":
        st.header("👨‍💼 Rata-Rata Hari Masuk & Produktivitas SCO")
        if df_rata2_active.empty:
            st.info("Data sheet 'Rata-Rata Hari Masuk' tidak ditemukan di file Cash ini.")
        else:
            # FIX 1: Filter sheet Hari Masuk berdasarkan file sumber (Source_File) yang lagi aktif dilihat di Date Filter
            active_sources = df_filtered['Source_File'].unique().tolist()
            hari_masuk_filtered = df_rata2_active[df_rata2_active['Source_File'].isin(active_sources)].copy()
            
            if 'Hari_Masuk' in hari_masuk_filtered.columns:
                hari_masuk_filtered['Hari_Masuk'] = pd.to_numeric(hari_masuk_filtered['Hari_Masuk'], errors='coerce').fillna(0)
                hari_masuk_df = hari_masuk_filtered.groupby('User id', as_index=False).agg({'Hari_Masuk': 'sum'})
            else:
                hari_masuk_df = pd.DataFrame(columns=['User id', 'Hari_Masuk'])

            df_r_clean = df_filtered.groupby('SCO', as_index=False).agg(
                Total_Connote=('Revenue', 'count'),
                Revenue=('Revenue', 'sum')
            ).rename(columns={'SCO': 'User id'})

            df_r_clean = pd.merge(df_r_clean, hari_masuk_df, on='User id', how='left')
            df_r_clean['Hari_Masuk'] = df_r_clean['Hari_Masuk'].fillna(0)

            df_r_clean['Rata_Transaksi_Per_Hari'] = (df_r_clean['Total_Connote'] / df_r_clean['Hari_Masuk'].replace(0, pd.NA)).fillna(0).round(1)
            df_r_clean['Rata_Pendapatan_Per_Hari'] = (df_r_clean['Revenue'] / df_r_clean['Hari_Masuk'].replace(0, pd.NA)).fillna(0)
            df_r_clean['Rata_Pendapatan_Per_Hari_Num'] = df_r_clean['Rata_Pendapatan_Per_Hari']

            df_r_clean['Revenue'] = df_r_clean['Revenue'].apply(format_rupiah)
            df_r_clean['Rata_Pendapatan_Per_Hari'] = df_r_clean['Rata_Pendapatan_Per_Hari'].apply(format_rupiah)
            df_r_clean['Total_Connote'] = df_r_clean['Total_Connote'].astype(int)
            df_r_clean['Hari_Masuk'] = df_r_clean['Hari_Masuk'].astype(int)
            
            if 'Rata_Pendapatan_Per_Hari_Num' in df_r_clean.columns:
                st.subheader("📊 Rata-Rata Pendapatan Harian")
                df_r_sorted = df_r_clean.sort_values('Rata_Pendapatan_Per_Hari_Num', ascending=False)
                chart_abs = alt.Chart(df_r_sorted).mark_bar(size=50, cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
                    x=alt.X('User id:N', title='SCO', sort='-y'), y=alt.Y('Rata_Pendapatan_Per_Hari_Num:Q', title='Rata-Rata Pendapatan (Rp)'),
                    color=alt.Color('User id:N', scale=alt.Scale(range=BRAND_CATEGORICAL), legend=None), tooltip=['User id', 'Hari_Masuk', 'Rata_Pendapatan_Per_Hari']
                ).properties(height=350)
                st.altair_chart(chart_abs, use_container_width=True)
            
            st.subheader("📋 Tabel Detail Kinerja (CASH)")
            cols = [c for c in df_r_clean.columns if not c.endswith('_Num')]
            df_r_display = df_r_clean[cols].copy()
            df_r_display.index = range(1, len(df_r_display) + 1)
            st.dataframe(style_top_row(df_r_display), use_container_width=True)
            
    else:
        st.header(f"👨‍💼 Rekapitulasi Kinerja SCO ({selected_kpi})")
        rekap_sco = df_filtered.groupby('SCO', as_index=False).agg(Total_Resi=('Revenue', 'count'), Total_Revenue=('Revenue', 'sum')).sort_values('Total_Revenue', ascending=False)
        rekap_sco['Total_Revenue_Num'] = rekap_sco['Total_Revenue']
        st.subheader("📊 Total Pendapatan Tiap SCO")
        chart_noncash = alt.Chart(rekap_sco).mark_bar(size=50, cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
            x=alt.X('SCO:N', title='Nama SCO', sort='-y'), y=alt.Y('Total_Revenue_Num:Q', title='Total Revenue (Rp)'),
            color=alt.Color('SCO:N', scale=alt.Scale(range=BRAND_CATEGORICAL), legend=None), tooltip=['SCO', 'Total_Resi', 'Total_Revenue_Num']
        ).properties(height=350)
        st.altair_chart(chart_noncash, use_container_width=True)
        tabel_sco = rekap_sco.copy()
        tabel_sco['Total_Revenue'] = tabel_sco['Total_Revenue'].apply(format_rupiah)
        tabel_sco = tabel_sco.drop(columns=['Total_Revenue_Num'])
        tabel_sco.index = range(1, len(tabel_sco) + 1)
        st.subheader(f"📋 Tabel Detail Kinerja ({selected_kpi})")
        st.dataframe(style_top_row(tabel_sco), use_container_width=True)

# ==========================================
# TAB 4: POLA HARI & JAM SIBUK
# ==========================================
with tab4:
    st.header(f"⏰ Jam Operasional ({selected_kpi})")

    df_filtered_hari = df_filtered.copy()
    hari_map_ins = {'Monday': 'Senin', 'Tuesday': 'Selasa', 'Wednesday': 'Rabu', 'Thursday': 'Kamis', 'Friday': 'Jumat', 'Saturday': 'Sabtu', 'Sunday': 'Minggu'}
    df_filtered_hari['Hari'] = df_filtered_hari['Date'].dt.day_name().map(hari_map_ins)
    
    hari_count = df_filtered_hari.groupby('Hari').size().sort_values(ascending=False)
    jam_count = df_filtered_hari.groupby(df_filtered_hari['Date'].dt.hour).size().sort_values(ascending=False)
    
    if not hari_count.empty and not jam_count.empty:
        hari_tersibuk = hari_count.index[0]
        jam_tersibuk = jam_count.index[0]
        st.markdown(f"""
        <div class="insight-box">
            <b>💡 Automated Insight:</b> Hari tersibuk adalah <b>{hari_tersibuk}</b> dengan <b>{hari_count.iloc[0]}</b> transaksi,
            sedangkan jam tersibuk ada di sekitar pukul <b>{jam_tersibuk:02d}:00</b> dengan <b>{jam_count.iloc[0]}</b> transaksi.
            Pola ini bisa dipakai buat atur jadwal penjemputan atau shift SCO biar lebih optimal di jam-jam padat.
        </div>
        """, unsafe_allow_html=True)

    a1, a2 = st.columns(2)
    with a1:
        hari_order = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
        pola_df = df_filtered_hari.groupby('Hari', as_index=False).size().rename(columns={'size':'Total Transaksi'})
        chart_pola = alt.Chart(pola_df).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
            x=alt.X('Hari:N', sort=hari_order), y=alt.Y('Total Transaksi:Q'),
            color=alt.condition(alt.datum['Total Transaksi'] == pola_df['Total Transaksi'].max(), alt.value(BRAND_GOLD), alt.value(BRAND_TEAL)),
            tooltip=['Hari', 'Total Transaksi']
        ).properties(height=350)
        st.altair_chart(chart_pola, use_container_width=True)
        
    with a2:
        # Fitur Baru: Filter dinamis per hari untuk ngecek jam sibuk
        pilihan_hari = ["Semua Hari", "Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
        hari_terpilih = st.selectbox("🎯 Cek Jam Sibuk Spesifik di Hari:", pilihan_hari)

        if hari_terpilih == "Semua Hari":
            df_jam = df_filtered_hari.copy()
        else:
            df_jam = df_filtered_hari[df_filtered_hari['Hari'] == hari_terpilih].copy()

        if not df_jam.empty:
            df_jam['Jam'] = df_jam['Date'].dt.hour
            jam_df = df_jam.groupby('Jam', as_index=False).size().rename(columns={'size':'Total Transaksi'})
            jam_df['Jam_Label'] = jam_df['Jam'].apply(lambda x: f"{x:02d}:00")
            
            # Tinggi chart disesuaikan biar sejajar dengan chart sebelahnya setelah ditambah selectbox
            chart_jam = alt.Chart(jam_df).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
                x=alt.X('Jam_Label:N', sort=jam_df['Jam_Label'].tolist(), title='Jam'), y=alt.Y('Total Transaksi:Q'),
                color=alt.condition(alt.datum['Total Transaksi'] == jam_df['Total Transaksi'].max(), alt.value(BRAND_GOLD), alt.value(BRAND_TEAL)),
                tooltip=['Jam_Label', 'Total Transaksi']
            ).properties(height=280) 
            st.altair_chart(chart_jam, use_container_width=True)
        else:
            st.info(f"Belum ada data transaksi di hari {hari_terpilih}.")

# ==========================================
# TAB 5: LAYANAN & PAYMENT
# ==========================================
with tab5:
    st.header(f"💳 Distribusi Layanan & Metode Pembayaran ({selected_kpi})")

    srv_counts = df_filtered['Service'].value_counts()
    pay_counts = df_filtered['Payment_Method'].value_counts()
    if not srv_counts.empty and not pay_counts.empty:
        srv_share = (srv_counts.iloc[0] / srv_counts.sum() * 100)
        pay_share = (pay_counts.iloc[0] / pay_counts.sum() * 100)
        st.markdown(f"""
        <div class="insight-box">
            <b>💡 Automated Insight:</b> Layanan <b>{srv_counts.index[0]}</b> mendominasi <b>{srv_share:,.1f}%</b> dari seluruh transaksi.
            Untuk metode pembayaran, <b>{pay_counts.index[0]}</b> jadi favorit dengan pangsa <b>{pay_share:,.1f}%</b>.
            Kalau salah satu pangsanya di atas 70%, ada baiknya dicek apakah opsi lain kurang dipromosikan ke customer.
        </div>
        """, unsafe_allow_html=True)

    s1, s2 = st.columns(2)
    with s1:
        st.subheader("🚚 Jenis Layanan")
        top_serv = df_filtered['Service'].value_counts().reset_index().rename(columns={'Service':'Jenis Layanan', 'count':'Total Dipakai'})
        chart_serv = alt.Chart(top_serv).mark_arc(innerRadius=60).encode(
            theta=alt.Theta(field="Total Dipakai", type="quantitative"),
            color=alt.Color(field="Jenis Layanan", type="nominal", scale=alt.Scale(range=BRAND_CATEGORICAL)),
            tooltip=['Jenis Layanan', 'Total Dipakai']
        ).properties(height=300)
        st.altair_chart(chart_serv, use_container_width=True)
    with s2:
        st.subheader("💳 Metode Pembayaran")
        top_pay = df_filtered['Payment_Method'].value_counts().reset_index().rename(columns={'Payment_Method':'Metode', 'count':'Total Transaksi'})
        chart_pay = alt.Chart(top_pay).mark_bar(cornerRadiusTopRight=5, cornerRadiusBottomRight=5).encode(
            y=alt.Y('Metode:N', sort='-x', title='Tipe / Marketplace'), x=alt.X('Total Transaksi:Q', title='Penggunaan'),
            color=alt.Color('Metode:N', scale=alt.Scale(range=BRAND_CATEGORICAL), legend=None), tooltip=['Metode', 'Total Transaksi']
        ).properties(height=300)
        st.altair_chart(chart_pay, use_container_width=True)

    if selected_kpi == "Cash" and 'Insurance' in df_filtered.columns and df_filtered['Insurance'].sum() > 0:
        st.markdown("---")
        st.subheader("🛡️ Ringkasan Asuransi Pengiriman")
        total_resi_ins = len(df_filtered)
        resi_berasuransi_ins = (df_filtered['Insurance'] > 0).sum()
        pct_ins = (resi_berasuransi_ins / total_resi_ins * 100) if total_resi_ins > 0 else 0
        total_premi_ins = df_filtered['Insurance'].sum()
        avg_premi_ins = (total_premi_ins / resi_berasuransi_ins) if resi_berasuransi_ins > 0 else 0

        i1, i2, i3 = st.columns(3)
        i1.metric("🛡️ % TRANSAKSI BERASURANSI", f"{pct_ins:,.1f}%", delta=f"{resi_berasuransi_ins} dari {total_resi_ins} Resi")
        i2.metric("💰 TOTAL PREMI ASURANSI", format_rupiah(total_premi_ins))
        i3.metric("📊 RATA-RATA PREMI / RESI BERASURANSI", format_rupiah(avg_premi_ins))

        ins_by_sco = df_filtered[df_filtered['Insurance'] > 0].groupby('SCO', as_index=False).agg(Total_Premi=('Insurance', 'sum'), Jumlah_Resi=('Insurance', 'count')).sort_values('Total_Premi', ascending=False)
        if not ins_by_sco.empty:
            chart_ins = alt.Chart(ins_by_sco).mark_bar(cornerRadiusTopRight=5, cornerRadiusBottomRight=5, color=BRAND_GOLD).encode(
                x=alt.X('Total_Premi:Q', title='Total Premi Asuransi (Rp)'),
                y=alt.Y('SCO:N', sort='-x', title='SCO'),
                tooltip=['SCO', 'Jumlah_Resi', 'Total_Premi']
            ).properties(height=250)
            st.altair_chart(chart_ins, use_container_width=True)

# ==========================================
# TAB 6: PEMETAAN DESTINASI (3D HEAT-PILLAR)
# ==========================================
with tab6:
    st.header(f"📍 Analisis Wilayah Destinasi ({selected_kpi})")
    df_dest = df_filtered[df_filtered['Destination'] != '-']
    if not df_dest.empty:
        dest_df = df_dest.groupby('Destination', as_index=False).agg({'Revenue': 'sum', 'SCO': 'count'}).rename(columns={'SCO': 'Total Resi'}).sort_values('Total Resi', ascending=False)

        top_dest = dest_df.iloc[0]['Destination']
        top_dest_resi = dest_df.iloc[0]['Total Resi']
        top_dest_share = (top_dest_resi / dest_df['Total Resi'].sum() * 100)
        n_dest_unik = dest_df['Destination'].nunique()
        st.markdown(f"""
        <div class="insight-box">
            <b>💡 Automated Insight:</b> Dari <b>{n_dest_unik} wilayah tujuan</b>, <b>{top_dest}</b> jadi destinasi paling ramai dengan
            <b>{top_dest_resi} resi</b> (<b>{top_dest_share:,.1f}%</b> dari total pengiriman). Wilayah ini layak jadi prioritas
            untuk efisiensi rute atau penempatan armada.
        </div>
        """, unsafe_allow_html=True)

        import pydeck as pdk
        CITY_COORDS = {
            'JAKARTA': [-6.2088, 106.8456], 'BEKASI': [-6.2383, 106.9756], 
            'BOGOR': [-6.5971, 106.7932], 'DEPOK': [-6.4025, 106.7942], 
            'TANGERANG': [-6.1702, 106.6403], 'BANDUNG': [-6.9175, 107.6191], 
            'SUKABUMI': [-6.9275, 106.9300], 'TAMBUN SELATAN': [-6.2652, 107.0543],
            'SURABAYA': [-7.2504, 112.7688], 'SEMARANG': [-6.9667, 110.4167],
            'MEDAN': [3.5952, 98.6722], 'BALI': [-8.4095, 115.1889],
            'SOLO': [-7.5666, 110.8266], 'YOGYAKARTA': [-7.7956, 110.3695],
            'MALANG': [-7.9839, 112.6214], 'MAKASSAR': [-5.1477, 119.4327],
            'BANDA ACEH': [5.5483, 95.3238], 'MAGELANG': [-7.4797, 110.2177],
            'CIREBON': [-6.7320, 108.5523], 'KENDARI': [-3.9985, 122.5127],
            'AMBON': [-3.6954, 128.1814], 'JAYAPURA': [-2.5337, 140.7181],
            'TARAKAN': [3.3148, 117.5925], 'BANDAR LAMPUNG': [-5.4500, 105.2667],
            'PALEMBANG': [-2.9909, 104.7566], 'PEKANBARU': [0.5333, 101.4500],
            'PADANG': [-0.9471, 100.3690], 'BANJARMASIN': [-3.3167, 114.5901],
            'BALIKPAPAN': [-1.2379, 116.8529], 'PONTIANAK': [-0.0227, 109.3333],
            'PENJARINGAN': [-6.1283, 106.7865], 'KELAPA DUA': [-6.2372, 106.6143],
            'MEDAN SUNGGAL': [3.5786, 98.6256]
        }
        
        dest_df['lat'] = dest_df['Destination'].apply(lambda x: CITY_COORDS.get(x, [None, None])[0])
        dest_df['lon'] = dest_df['Destination'].apply(lambda x: CITY_COORDS.get(x, [None, None])[1])
        
        map_df = dest_df.dropna(subset=['lat', 'lon']).copy()

        unmapped_df = dest_df[dest_df['lat'].isna()]
        if not unmapped_df.empty:
            unmapped_resi = unmapped_df['Total Resi'].sum()
            st.caption(f"ℹ️ {len(unmapped_df)} wilayah ({unmapped_resi} resi) belum ada di kamus koordinat sistem, jadi belum tampil di peta 3D di bawah — tapi tetap terhitung di tabel & chart lainnya. Contoh: {', '.join(unmapped_df['Destination'].head(5).tolist())}")

        if not map_df.empty:
            st.subheader("🗺️ Peta 3D Persebaran Logistik")
            st.markdown("<p style='color:#a8b2d1; font-size:0.9rem;'>Warna teal ke emas dan tinggi pilar menandakan tingginya jumlah resi. (Bisa di-zoom, geser, klik kanan tahan untuk memutar 3D)</p>", unsafe_allow_html=True)
            
            max_resi = map_df['Total Resi'].max()
            min_resi = map_df['Total Resi'].min()
            
            def get_color(resi):
                if max_resi == min_resi:
                    norm = 0.5
                else:
                    norm = (resi - min_resi) / (max_resi - min_resi)
                start = (15, 155, 142)   # BRAND_TEAL_DARK
                end = (255, 209, 102)    # BRAND_GOLD
                r = int(start[0] + (end[0] - start[0]) * norm)
                g = int(start[1] + (end[1] - start[1]) * norm)
                b = int(start[2] + (end[2] - start[2]) * norm)
                return [r, g, b, 220]
                
            map_df['color'] = map_df['Total Resi'].apply(get_color)
            
            layer = pdk.Layer(
                'ColumnLayer', 
                data=map_df,
                get_position='[lon, lat]',
                get_elevation='Total Resi',
                elevation_scale=1000, 
                radius=10000, 
                get_fill_color='color',
                pickable=True,
                auto_highlight=True,
                extruded=True
            )
            
            view_state = pdk.ViewState(latitude=-6.2, longitude=110.0, zoom=5, pitch=50, bearing=15)
            
            r = pdk.Deck(
                layers=[layer], initial_view_state=view_state,
                tooltip={
                    "html": "<b style='color:#64ffda;'>📍 {Destination}</b><br/>📦 Resi: {Total Resi}<br/>💰 Rev: Rp {Revenue}",
                    "style": {
                        "backgroundColor": "rgba(15, 32, 39, 0.95)",
                        "color": "#e6f1ff",
                        "border": "1px solid rgba(100, 255, 218, 0.4)",
                        "borderRadius": "10px",
                        "padding": "10px 14px",
                        "fontFamily": "'Plus Jakarta Sans', sans-serif",
                        "fontSize": "0.85rem"
                    }
                },
                map_style='dark'
            )
            st.pydeck_chart(r)
        else:
            st.info("💡 Peta logistik belum bisa ditampilkan. Pastikan nama kota sudah ada di kamus sistem.")
            
        st.markdown("---")
        
        st.subheader("📊 Rincian Top Destinasi")
        d1, d2 = st.columns([2, 1])
        top15_df = dest_df.head(15).copy()
        with d1:
            chart_dest = alt.Chart(top15_df).mark_arc(innerRadius=70, cornerRadius=4).encode(
                theta=alt.Theta(field="Total Resi", type="quantitative"),
                color=alt.Color(field="Destination", type="nominal", scale=alt.Scale(range=BRAND_SEQUENTIAL + BRAND_CATEGORICAL), legend=None),
                tooltip=['Destination', 'Total Resi', 'Revenue']
            ).properties(height=400)
            st.altair_chart(chart_dest, use_container_width=True)
        with d2:
            top15_df.index = range(1, len(top15_df) + 1) 
            st.dataframe(style_top_row(top15_df[['Destination', 'Total Resi']]), use_container_width=True)
    else:
        st.info("Data destinasi tidak tersedia di file ini.")

# ==========================================
# TAB 7: TREN LINTAS BULAN
# ==========================================
with tab7:
    st.header(f"🚀 Pertumbuhan Bisnis - {selected_kpi.upper()}")
    st.markdown(f"<p style='color:#a8b2d1 !important;'>Menarik data {selected_kpi} dari seluruh file (tidak terpengaruh rentang tanggal di sidebar).</p>", unsafe_allow_html=True)
    
    if not df_kpi_only.empty:
        df_kpi_only['Sort_Bulan'] = df_kpi_only['Date'].dt.strftime('%Y-%m')
        df_kpi_only['Periode'] = df_kpi_only['Date'].dt.strftime('%b %Y')    
        
        tren_bulan = df_kpi_only.groupby(['Sort_Bulan', 'Periode'], as_index=False).agg({'Revenue': 'sum', 'SCO': 'count'}).rename(columns={'Revenue': 'Total Revenue', 'SCO': 'Total Transaksi'})
        tren_bulan = tren_bulan.sort_values('Sort_Bulan')
        sort_order = tren_bulan['Periode'].tolist()
        
        b1, b2 = st.columns(2)
        with b1:
            base_rev = alt.Chart(tren_bulan).encode(x=alt.X('Periode:N', sort=sort_order, title='Bulan', axis=alt.Axis(labelAngle=0, grid=False)))
            area_rev = base_rev.mark_area(opacity=0.2, color=BRAND_CYAN, interpolate='monotone').encode(y=alt.Y('Total Revenue:Q', title='Pendapatan (Rp)'))
            line_rev = base_rev.mark_line(color=BRAND_CYAN, strokeWidth=4, interpolate='monotone').encode(y='Total Revenue:Q')
            points_rev = base_rev.mark_circle(color=BRAND_WHITE, size=120, opacity=1).encode(y='Total Revenue:Q', tooltip=['Periode', 'Total Revenue'])
            st.altair_chart((area_rev + line_rev + points_rev).properties(height=350), use_container_width=True)
            
        with b2:
            base_trx = alt.Chart(tren_bulan).encode(x=alt.X('Periode:N', sort=sort_order, title='Bulan', axis=alt.Axis(labelAngle=0, grid=False)))
            area_trx = base_trx.mark_area(opacity=0.2, color=BRAND_GOLD, interpolate='monotone').encode(y=alt.Y('Total Transaksi:Q', title='Jumlah Resi'))
            line_trx = base_trx.mark_line(color=BRAND_GOLD, strokeWidth=4, interpolate='monotone').encode(y='Total Transaksi:Q')
            points_trx = base_trx.mark_circle(color=BRAND_WHITE, size=120, opacity=1).encode(y='Total Transaksi:Q', tooltip=['Periode', 'Total Transaksi'])
            st.altair_chart((area_trx + line_trx + points_trx).properties(height=350), use_container_width=True)
            
        st.markdown("---")
        st.subheader("📋 Master Table Tren Bulanan")
        tabel_tren = tren_bulan.copy()
        tabel_tren['Total Revenue'] = tabel_tren['Total Revenue'].apply(format_rupiah)
        tabel_tren.index = range(1, len(tabel_tren) + 1)
        st.dataframe(tabel_tren[['Periode', 'Total Transaksi', 'Total Revenue']], use_container_width=True)

        # ==========================================
        # GROWTH MoM 
        # ==========================================
        st.markdown("---")
        if len(tren_bulan) >= 2:
            periode_now = tren_bulan.iloc[-1]
            periode_prev = tren_bulan.iloc[-2]

            st.subheader(f"📈 Growth Month-over-Month: {periode_prev['Periode']} → {periode_now['Periode']}")

            rev_now, rev_prev = periode_now['Total Revenue'], periode_prev['Total Revenue']
            trx_now, trx_prev = periode_now['Total Transaksi'], periode_prev['Total Transaksi']
            growth_rev_pct = ((rev_now - rev_prev) / rev_prev * 100) if rev_prev > 0 else 0
            growth_trx_pct = ((trx_now - trx_prev) / trx_prev * 100) if trx_prev > 0 else 0

            gm1, gm2 = st.columns(2)
            gm1.metric(f"💰 Revenue {periode_now['Periode']}", format_rupiah(rev_now), delta=f"{growth_rev_pct:+.1f}% vs {periode_prev['Periode']}")
            gm2.metric(f"📦 Transaksi {periode_now['Periode']}", f"{trx_now} Resi", delta=f"{growth_trx_pct:+.1f}% vs {periode_prev['Periode']}")

            # --- Customer Churn & New Customer Analysis ---
            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader("👥 Customer Baru vs Customer Hilang (Churn)")
            st.markdown(f"<p style='color:#a8b2d1; font-size:0.9rem;'>Membandingkan customer unik yang order di <b>{periode_prev['Periode']}</b> vs <b>{periode_now['Periode']}</b>.</p>", unsafe_allow_html=True)

            df_cust_period = df_kpi_only[df_kpi_only['Customer'] != '-']
            cust_prev = set(df_cust_period[df_cust_period['Sort_Bulan'] == periode_prev['Sort_Bulan']]['Customer'].unique())
            cust_now = set(df_cust_period[df_cust_period['Sort_Bulan'] == periode_now['Sort_Bulan']]['Customer'].unique())

            cust_churned = cust_prev - cust_now
            cust_new = cust_now - cust_prev
            cust_retained = cust_prev & cust_now

            cm1, cm2, cm3 = st.columns(3)
            cm1.metric("🆕 CUSTOMER BARU", f"{len(cust_new)} Customer", delta=f"Hanya order di {periode_now['Periode']}")
            cm2.metric("⚠️ CUSTOMER HILANG", f"{len(cust_churned)} Customer", delta=f"Order di {periode_prev['Periode']}, tidak lanjut", delta_color="inverse")
            cm3.metric("♻️ CUSTOMER BERTAHAN", f"{len(cust_retained)} Customer")

            if cust_churned:
                rev_prev_by_cust = df_cust_period[
                    (df_cust_period['Sort_Bulan'] == periode_prev['Sort_Bulan']) & (df_cust_period['Customer'].isin(cust_churned))
                ].groupby('Customer', as_index=False)['Revenue'].sum().rename(columns={'Revenue': f"Revenue {periode_prev['Periode']}"}).sort_values(f"Revenue {periode_prev['Periode']}", ascending=False).head(10)
                rev_prev_by_cust[f"Revenue {periode_prev['Periode']}"] = rev_prev_by_cust[f"Revenue {periode_prev['Periode']}"].apply(format_rupiah)
                rev_prev_by_cust.index = range(1, len(rev_prev_by_cust) + 1)

                top_churn_name = rev_prev_by_cust.iloc[0]['Customer']
                st.markdown(f"""
                <div class="insight-box insight-warning">
                    <b>⚠️ Automated Insight:</b> Ada <b>{len(cust_churned)} customer</b> yang order di {periode_prev['Periode']} tapi tidak lanjut di {periode_now['Periode']}.
                    Yang paling besar kontribusinya sebelumnya adalah <b>{top_churn_name}</b>. Layak di-follow up ulang sebelum makin lama tidak aktif.
                </div>
                """, unsafe_allow_html=True)
                st.markdown("**🔟 Top 10 Customer Hilang (berdasarkan revenue bulan sebelumnya)**")
                st.dataframe(rev_prev_by_cust, use_container_width=True)
        else:
            st.info("Growth MoM & analisis Customer Churn butuh data minimal 2 bulan berbeda. Upload file bulan lain untuk mengaktifkan fitur ini.")

# ==========================================
# TAB 8: EXECUTIVE SUMMARY (Full Width Chart & Table)
# ==========================================
with tab8:
    st.header("🌐 Executive Summary (Master Global)")
    st.markdown("<p style='color:#a8b2d1 !important;'>Tabel ini <b>kebal terhadap filter Sidebar</b>. Menarik SEMUA data dari SEMUA file untuk membandingkan kinerja antar pilar KPI secara menyeluruh.</p>", unsafe_allow_html=True)
    
    tot_rev_global = df_global['Revenue'].sum()
    tot_resi_global = len(df_global)
    rekap_sco_global = df_global.groupby('SCO')['Revenue'].sum()
    best_sco_global = rekap_sco_global.idxmax() if not rekap_sco_global.empty else "-"
    best_sco_rev_global = rekap_sco_global.max() if not rekap_sco_global.empty else 0

    g1, g2, g3 = st.columns(3)
    g1.metric("🌍 TOTAL REVENUE (ALL KPI)", format_rupiah(tot_rev_global))
    g2.metric("📦 TOTAL RESI (ALL KPI)", f"{tot_resi_global} Resi")
    g3.metric("👑 MVP SCO (OVERALL)", best_sco_global, f"{format_rupiah(best_sco_rev_global)} Contributed")

    rekap_kpi_global = df_global.groupby('KPI')['Revenue'].sum().sort_values(ascending=False)
    if len(rekap_kpi_global) > 1:
        top_kpi_name = rekap_kpi_global.index[0]
        top_kpi_share = (rekap_kpi_global.iloc[0] / rekap_kpi_global.sum() * 100)
        st.markdown(f"""
        <div class="insight-box">
            <b>💡 Automated Insight:</b> Pilar <b>{top_kpi_name}</b> menjadi kontributor revenue terbesar secara keseluruhan dengan pangsa
            <b>{top_kpi_share:,.1f}%</b> dari total <b>{format_rupiah(tot_rev_global)}</b>. SCO <b>{best_sco_global}</b> jadi kontributor
            individu tertinggi lintas semua pilar KPI.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    st.subheader("📊 Komposisi Revenue SCO berdasarkan KPI")
    rekap_chart = df_global.groupby(['SCO', 'KPI'], as_index=False)['Revenue'].sum()
    chart_global = alt.Chart(rekap_chart).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
        x=alt.X('SCO:N', sort='-y', title='Nama SCO'),
        y=alt.Y('Revenue:Q', title='Total Revenue (Rp)'),
        color=alt.Color('KPI:N', scale=alt.Scale(range=BRAND_CATEGORICAL), title='Jenis KPI'),
        tooltip=['SCO', 'KPI', 'Revenue']
    ).properties(height=450)
    st.altair_chart(chart_global, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    st.subheader("📋 Master Table Keseluruhan")
    
    pivot_resi = df_global.pivot_table(index='SCO', columns='KPI', values='Revenue', aggfunc='count', fill_value=0)
    pivot_resi['Total Resi Akhir'] = pivot_resi.sum(axis=1)
    
    pivot_rev = df_global.pivot_table(index='SCO', columns='KPI', values='Revenue', aggfunc='sum', fill_value=0)
    pivot_rev['Total Pendapatan Akhir'] = pivot_rev.sum(axis=1)
    
    pivot_resi.columns = [f"📦 Resi {c}" if c != 'Total Resi Akhir' else c for c in pivot_resi.columns]
    pivot_rev.columns = [f"💰 Rev {c}" if c != 'Total Pendapatan Akhir' else c for c in pivot_rev.columns]
    
    global_rekap = pd.concat([pivot_resi, pivot_rev], axis=1).reset_index()
    global_rekap = global_rekap.sort_values('Total Pendapatan Akhir', ascending=False)
    
    rev_cols = [c for c in global_rekap.columns if "Rev" in c or "Pendapatan" in c]
    for c in rev_cols:
        global_rekap[c] = global_rekap[c].apply(format_rupiah)
        
    global_rekap.index = range(1, len(global_rekap) + 1)
    st.dataframe(style_top_row(global_rekap), use_container_width=True)

# ==========================================
# FOOTER
# ==========================================
st.markdown("""
<div class="app-footer">
    📦 <b>Dashboard Enterprise KP Grand Taruma</b> · Dibangun untuk monitoring performa SCO Cash &amp; Cashless<br/>
    Dibuat dengan ❤️ oleh <b>Yusuf Zulkarnaen</b>
</div>
""", unsafe_allow_html=True)
