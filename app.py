import streamlit as st
import pandas as pd
import altair as alt
import glob
import os
import pydeck as pdk

# ==========================================
# 1. SETTING HALAMAN & INJEKSI CSS PREMIUM
# ==========================================
st.set_page_config(page_title="Dashboard SCO", page_icon="📦", layout="wide")

def add_custom_css():
    st.markdown("""
    <style>
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
    }
    </style>
    """, unsafe_allow_html=True)

add_custom_css()

# ==========================================
# FUNGSI KELOLA DATA & STANDARISASI
# ==========================================
def clean_destination(dest, kpi_type):
    if pd.isna(dest) or str(dest).strip() == "-" or str(dest).strip() == "":
        return "-"
    dest_str = str(dest).strip().upper()
    
    if kpi_type == "Cashless":
        # Mapping kode Cashless (ex: BOO10028 -> BOGOR)
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
        # Data Cash biasa di split koma (ex: TAMBUN SELATAN,CIKAR -> TAMBUN SELATAN)
        return dest_str.split(',')[0].strip()

@st.cache_data
def load_unified_data(file_list):
    all_raw = []
    all_rata2 = []
    
    for f in file_list:
        try:
            # Handle sifat file (Uploaded vs Local path)
            if hasattr(f, 'name'):
                filename = f.name.lower()
                xls_input = f
            else:
                filename = os.path.basename(f).lower()
                xls_input = f
            
            # Deteksi KPI 
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
                
                col_sco = 'User id' if 'User id' in df.columns else ('User Id' if 'User Id' in df.columns else None)
                df_std['SCO'] = df[col_sco] if col_sco else "UNKNOWN"
                
                col_date = 'Created date' if 'Created date' in df.columns else 'Date'
                df_std['Date'] = pd.to_datetime(df[col_date], errors='coerce')
                
                col_rev = 'Cnote Amount' if 'Cnote Amount' in df.columns else 'Amount'
                df_std['Revenue'] = pd.to_numeric(df[col_rev], errors='coerce').fillna(0)
                
                df_std['Weight'] = pd.to_numeric(df['Weight'] if 'Weight' in df.columns else 0, errors='coerce').fillna(0)
                
                col_srv = 'Service' if 'Service' in df.columns else ('Services' if 'Services' in df.columns else None)
                df_std['Service'] = df[col_srv] if col_srv else "-"
                
                df_std['Customer'] = df['Shipper Name'].fillna("-") if 'Shipper Name' in df.columns else "-"
                
                # Fitur Baru: Clean Destinasi
                df_std['Destination'] = df['Destination'].apply(lambda x: clean_destination(x, kpi_type)) if 'Destination' in df.columns else "-"
                
                if kpi_type == "Cashless":
                    col_pay = 'Marketplace_Clean' if 'Marketplace_Clean' in df.columns else ('Marketplace' if 'Marketplace' in df.columns else None)
                    df_std['Payment_Method'] = df[col_pay].fillna("Lainnya") if col_pay else "Lainnya"
                elif kpi_type == "Cash":
                    df_std['Payment_Method'] = df['Payment type'].fillna("Cash") if 'Payment type' in df.columns else "Cash"
                else:
                    df_std['Payment_Method'] = kpi_type
                    
                all_raw.append(df_std)
            
            # Load Rata-Rata Khusus Cash
            if kpi_type == "Cash" and "Rata-Rata Hari Masuk" in xls.sheet_names:
                df_r = pd.read_excel(xls, "Rata-Rata Hari Masuk")
                all_rata2.append(df_r)
                
        except Exception as e:
            pass
            
    df_master = pd.concat(all_raw, ignore_index=True) if all_raw else pd.DataFrame()
    df_rata2_master = pd.concat(all_rata2, ignore_index=True) if all_rata2 else pd.DataFrame()
    
    return df_master, df_rata2_master

def format_rupiah(val):
    return f"Rp {val:,.0f}".replace(",", ".")

# ==========================================
# SIDEBAR KIRI: SISTEM HYBRID & FILTER
# ==========================================
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3063/3063822.png", width=100)
st.sidebar.header("📁 Data Source (Hybrid)")
st.sidebar.markdown("<p style='font-size:0.9rem; color:#a8b2d1;'>Sistem akan otomatis baca dari server/GitHub. Upload file hanya jika ingin menimpa data sementara.</p>", unsafe_allow_html=True)

uploaded_files = st.sidebar.file_uploader("Upload File Bypass (.xlsx)", type=['xlsx'], accept_multiple_files=True)

# LOGIKA HYBRID
if uploaded_files:
    active_files = uploaded_files
else:
    list_local = glob.glob("*.xlsx")
    list_local = [f for f in list_local if not f.startswith("~$")]
    active_files = list_local

if not active_files:
    st.error("⚠️ Data server kosong dan belum ada file yang di-upload.")
    st.stop()

# 1. LOAD GLOBAL MASTER 
df_global, _ = load_unified_data(active_files)
if df_global.empty:
    st.error("Gagal membaca data. Pastikan sheet 'Raw Data' ada di dalam file.")
    st.stop()

st.sidebar.markdown("---")
st.sidebar.header("🔍 Filter Analytics")

# 2. PILIH KPI
available_kpis = df_global['KPI'].unique().tolist()
selected_kpi = st.sidebar.selectbox("📊 Pilih Pilar KPI:", options=available_kpis)

# 3. FIX BUG: Pemilihan File Ketat
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

# Langsung teruskan file yang udah disaring otomatis tanpa perlu multiselect lagi
selected_files = list_file_kpi


# 4. LOAD ACTIVE MASTER 
df_active, df_rata2_active = load_unified_data(selected_files)

df_active = df_active.dropna(subset=['Date', 'SCO'])
df_active['Date_Only'] = df_active['Date'].dt.date

df_kpi_only = df_active[df_active['KPI'] == selected_kpi]

if df_kpi_only.empty:
    st.warning("Data untuk KPI ini kosong pada file yang dipilih.")
    st.stop()

# 5. RENTANG TANGGAL
min_date = df_kpi_only['Date_Only'].min()
max_date = df_kpi_only['Date_Only'].max()
date_range = st.sidebar.date_input("📅 Rentang Tanggal", value=(min_date, max_date), min_value=min_date, max_value=max_date)
if len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = end_date = date_range[0]
    
# 6. NAMA SCO 
list_sco = df_kpi_only['SCO'].dropna().unique().tolist()
selected_sco = st.sidebar.multiselect("👨‍💼 Pilih SCO (Bisa >1):", options=list_sco, default=[], help="Kosongkan buat nampilin semua")

# ==========================================
# EKSEKUSI FILTER UTAMA (TAB 1-6)
# ==========================================
mask_date = (df_kpi_only['Date_Only'] >= start_date) & (df_kpi_only['Date_Only'] <= end_date)
df_filtered = df_kpi_only[mask_date].copy()
if selected_sco:
    df_filtered = df_filtered[df_filtered['SCO'].isin(selected_sco)]

# DOWNLOAD DATA
st.sidebar.markdown("---")
st.sidebar.header("📥 Export Data")
csv_data = df_filtered.to_csv(index=False).encode('utf-8')
st.sidebar.download_button(label=f"Download Rekap {selected_kpi} (CSV)", data=csv_data, file_name=f"Data_Export_{selected_kpi}.csv", mime='text/csv')

# ==========================================
# TAMPILAN DASHBOARD
# ==========================================
st.title("📊 Dashboard Enterprise KP Grand Taruma")
st.markdown("<p style='color:#a8b2d1 !important; font-size:1.2rem;'>(By Yusuf Zulkarnaen)</p>", unsafe_allow_html=True)
st.markdown(f"Sedang menampilkan analitik untuk pilar: <b style='color:#64ffda;'>{selected_kpi.upper()}</b>", unsafe_allow_html=True)
st.markdown("---")

if df_filtered.empty:
    st.warning("⚠️ Data kosong pada rentang waktu atau SCO yang dipilih.")
    st.stop()

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "📈 Dashboard Utama", 
    "🏆 Top Customer", 
    f"👨‍💼 Kinerja SCO", 
    "⏰ Pola Waktu", 
    "💳 Layanan",
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
    
    st.markdown(f"""
    <div class="insight-box">
        <b>💡 Automated Insight:</b> Berdasarkan periode yang dipilih, <b>{best_user}</b> memimpin kontribusi SCO dengan revenue <b>{format_rupiah(best_user_rev)}</b>. 
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
    
    st.markdown("---")
    kiri, kanan = st.columns(2)
    with kiri:
        st.subheader(f"📈 Tren Harian ({selected_kpi})")
        harian = df_filtered.groupby('Date_Only', as_index=False).size().rename(columns={'size':'Transaksi'})
        chart_tren = alt.Chart(harian).mark_line(point=True, color='#64ffda', strokeWidth=3).encode(
            x=alt.X('Date_Only:T', title='Tanggal'), y=alt.Y('Transaksi:Q', title='Jumlah Resi'), tooltip=['Date_Only', 'Transaksi']
        ).properties(height=300)
        st.altair_chart(chart_tren, use_container_width=True)
        
    with kanan:
        st.subheader("🏅 Ranking Revenue SCO")
        rekap_user_df = df_filtered.groupby('SCO', as_index=False).agg({'Revenue':'sum'}).rename(columns={'Revenue':'Pendapatan'}).sort_values(by='Pendapatan', ascending=False)
        chart_sco = alt.Chart(rekap_user_df).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
            x=alt.X('SCO:N', sort='-y', title='Nama SCO'), y=alt.Y('Pendapatan:Q', title='Total Revenue (Rp)'),
            color=alt.Color('SCO:N', scale=alt.Scale(scheme='teals'), legend=None), tooltip=['SCO', 'Pendapatan']
        ).properties(height=300)
        st.altair_chart(chart_sco, use_container_width=True)
        
    # FITUR BARU: Tambahan diagram di Tab Utama
    st.markdown("---")
    bawah1, bawah2 = st.columns(2)
    with bawah1:
        st.subheader(f"💵 Rata-Rata Revenue per Resi (Harian)")
        rata_harian = df_filtered.groupby('Date_Only', as_index=False).agg(Total_Rev=('Revenue', 'sum'), Total_Resi=('Revenue', 'count'))
        rata_harian['Rata-Rata'] = rata_harian['Total_Rev'] / rata_harian['Total_Resi']
        chart_avg = alt.Chart(rata_harian).mark_area(
            opacity=0.3,
            color=alt.Gradient(gradient='linear', stops=[alt.GradientStop(color='#64ffda', offset=0), alt.GradientStop(color='rgba(0,0,0,0)', offset=1)], x1=1, x2=1, y1=1, y2=0)
        ).encode(
            x=alt.X('Date_Only:T', title='Tanggal'), y=alt.Y('Rata-Rata:Q', title='Rata-Rata Revenue (Rp)'), tooltip=['Date_Only', 'Rata-Rata']
        )
        line_avg = alt.Chart(rata_harian).mark_line(color='#64ffda', strokeWidth=3).encode(x='Date_Only:T', y='Rata-Rata:Q')
        st.altair_chart((chart_avg + line_avg).properties(height=300), use_container_width=True)

    with bawah2:
        st.subheader("📦 Top 5 Destinasi Pengiriman")
        dest_df_quick = df_filtered[df_filtered['Destination'] != '-'].groupby('Destination', as_index=False).size().rename(columns={'size':'Total Resi'}).sort_values('Total Resi', ascending=False).head(5)
        chart_dest_quick = alt.Chart(dest_df_quick).mark_bar(cornerRadiusTopRight=5, cornerRadiusBottomRight=5, color='#00b4d8').encode(
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
        col_rev, col_con = st.columns(2)
        with col_rev:
            st.subheader("🥇 Top 10 Customer (By Revenue)")
            top_rev = df_cust.groupby('Customer', as_index=False).agg({'Revenue':'sum', 'SCO':'count'}).rename(columns={'Revenue':'Total Belanja', 'SCO':'Total Resi'}).sort_values(by='Total Belanja', ascending=False).head(10)
            chart_rev = alt.Chart(top_rev).mark_bar(cornerRadiusTopRight=5, cornerRadiusBottomRight=5).encode(
                x=alt.X('Total Belanja:Q', title='Total Revenue (Rp)'), y=alt.Y('Customer:N', sort='-x', title='Customer'),
                color=alt.Color('Total Belanja:Q', scale=alt.Scale(scheme='blues'), legend=None), tooltip=['Customer', 'Total Belanja', 'Total Resi']
            ).properties(height=400)
            st.altair_chart(chart_rev, use_container_width=True)
            
            top_rev_tabel = top_rev.copy()
            top_rev_tabel['Total Belanja'] = top_rev_tabel['Total Belanja'].apply(format_rupiah)
            top_rev_tabel.index = range(1, len(top_rev_tabel) + 1)
            st.dataframe(top_rev_tabel, use_container_width=True)

        with col_con:
            st.subheader("🔢 Top 10 Customer (By Connote)")
            top_con = df_cust.groupby('Customer', as_index=False).agg({'SCO':'count', 'Revenue':'sum'}).rename(columns={'SCO':'Total Resi', 'Revenue':'Total Belanja'}).sort_values(by='Total Resi', ascending=False).head(10)
            chart_con = alt.Chart(top_con).mark_bar(cornerRadiusTopRight=5, cornerRadiusBottomRight=5).encode(
                x=alt.X('Total Resi:Q', title='Total Transaksi (Resi)'), y=alt.Y('Customer:N', sort='-x', title='Customer'),
                color=alt.Color('Total Resi:Q', scale=alt.Scale(scheme='oranges'), legend=None), tooltip=['Customer', 'Total Resi', 'Total Belanja']
            ).properties(height=400)
            st.altair_chart(chart_con, use_container_width=True)
            
            top_con_tabel = top_con.copy()
            top_con_tabel['Total Belanja'] = top_con_tabel['Total Belanja'].apply(format_rupiah)
            top_con_tabel.index = range(1, len(top_con_tabel) + 1)
            st.dataframe(top_con_tabel, use_container_width=True)

# ==========================================
# TAB 3: KINERJA SCO
# ==========================================
with tab3:
    if selected_kpi == "Cash":
        st.header("👨‍💼 Rata-Rata Hari Masuk & Produktivitas SCO")
        if df_rata2_active.empty:
            st.info("Data sheet 'Rata-Rata Hari Masuk' tidak ditemukan di file Cash ini.")
        else:
            df_r_clean = df_rata2_active.copy()
            if selected_sco:
                df_r_clean = df_r_clean[df_r_clean['User id'].isin(selected_sco)]
            for col in ['Total_Connote', 'Revenue', 'Hari_Masuk']:
                if col in df_r_clean.columns: df_r_clean[col] = pd.to_numeric(df_r_clean[col], errors='coerce').fillna(0)
            agg_rules = {}
            if 'Total_Connote' in df_r_clean.columns: agg_rules['Total_Connote'] = 'sum'
            if 'Revenue' in df_r_clean.columns: agg_rules['Revenue'] = 'sum'
            if 'Hari_Masuk' in df_r_clean.columns: agg_rules['Hari_Masuk'] = 'sum'
            if agg_rules: df_r_clean = df_r_clean.groupby('User id', as_index=False).agg(agg_rules)
            if 'Hari_Masuk' in df_r_clean.columns:
                if 'Total_Connote' in df_r_clean.columns: df_r_clean['Rata_Transaksi_Per_Hari'] = (df_r_clean['Total_Connote'] / df_r_clean['Hari_Masuk']).fillna(0).round(1)
                if 'Revenue' in df_r_clean.columns: df_r_clean['Rata_Pendapatan_Per_Hari'] = (df_r_clean['Revenue'] / df_r_clean['Hari_Masuk']).fillna(0)
            if 'Rata_Pendapatan_Per_Hari' in df_r_clean.columns: df_r_clean['Rata_Pendapatan_Per_Hari_Num'] = df_r_clean['Rata_Pendapatan_Per_Hari']
            
            if 'Revenue' in df_r_clean.columns: df_r_clean['Revenue'] = df_r_clean['Revenue'].apply(format_rupiah)
            if 'Rata_Pendapatan_Per_Hari' in df_r_clean.columns: df_r_clean['Rata_Pendapatan_Per_Hari'] = df_r_clean['Rata_Pendapatan_Per_Hari'].apply(format_rupiah)
            if 'Total_Connote' in df_r_clean.columns: df_r_clean['Total_Connote'] = df_r_clean['Total_Connote'].astype(int)
            if 'Hari_Masuk' in df_r_clean.columns: df_r_clean['Hari_Masuk'] = df_r_clean['Hari_Masuk'].astype(int)
            
            if 'Rata_Pendapatan_Per_Hari_Num' in df_r_clean.columns:
                st.subheader("📊 Rata-Rata Pendapatan Harian")
                chart_abs = alt.Chart(df_r_clean).mark_bar(size=50, cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
                    x=alt.X('User id:N', title='SCO', sort='-y'), y=alt.Y('Rata_Pendapatan_Per_Hari_Num:Q', title='Rata-Rata Pendapatan (Rp)'),
                    color=alt.Color('User id:N', scale=alt.Scale(scheme='set2'), legend=None), tooltip=['User id', 'Hari_Masuk', 'Rata_Pendapatan_Per_Hari']
                ).properties(height=350)
                st.altair_chart(chart_abs, use_container_width=True)
            st.subheader("📋 Tabel Detail Kinerja (CASH)")
            cols = [c for c in df_r_clean.columns if not c.endswith('_Num')]
            st.dataframe(df_r_clean[cols], use_container_width=True)
    else:
        st.header(f"👨‍💼 Rekapitulasi Kinerja SCO ({selected_kpi})")
        rekap_sco = df_filtered.groupby('SCO', as_index=False).agg(Total_Resi=('Revenue', 'count'), Total_Revenue=('Revenue', 'sum')).sort_values('Total_Revenue', ascending=False)
        rekap_sco['Total_Revenue_Num'] = rekap_sco['Total_Revenue']
        st.subheader("📊 Total Pendapatan Tiap SCO")
        chart_noncash = alt.Chart(rekap_sco).mark_bar(size=50, cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
            x=alt.X('SCO:N', title='Nama SCO', sort='-y'), y=alt.Y('Total_Revenue_Num:Q', title='Total Revenue (Rp)'),
            color=alt.Color('SCO:N', scale=alt.Scale(scheme='set2'), legend=None), tooltip=['SCO', 'Total_Resi', 'Total_Revenue_Num']
        ).properties(height=350)
        st.altair_chart(chart_noncash, use_container_width=True)
        tabel_sco = rekap_sco.copy()
        tabel_sco['Total_Revenue'] = tabel_sco['Total_Revenue'].apply(format_rupiah)
        tabel_sco = tabel_sco.drop(columns=['Total_Revenue_Num'])
        tabel_sco.index = range(1, len(tabel_sco) + 1)
        st.subheader(f"📋 Tabel Detail Kinerja ({selected_kpi})")
        st.dataframe(tabel_sco, use_container_width=True)

# ==========================================
# TAB 4: POLA HARI & JAM SIBUK
# ==========================================
with tab4:
    st.header(f"⏰ Jam Operasional ({selected_kpi})")
    a1, a2 = st.columns(2)
    with a1:
        hari_map = {'Monday': 'Senin', 'Tuesday': 'Selasa', 'Wednesday': 'Rabu', 'Thursday': 'Kamis', 'Friday': 'Jumat', 'Saturday': 'Sabtu', 'Sunday': 'Minggu'}
        df_filtered['Hari'] = df_filtered['Date'].dt.day_name().map(hari_map)
        hari_order = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
        pola_df = df_filtered.groupby('Hari', as_index=False).size().rename(columns={'size':'Total Transaksi'})
        chart_pola = alt.Chart(pola_df).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
            x=alt.X('Hari:N', sort=hari_order), y=alt.Y('Total Transaksi:Q'),
            color=alt.condition(alt.datum['Total Transaksi'] == pola_df['Total Transaksi'].max(), alt.value('#ff4b4b'), alt.value('#64ffda')),
            tooltip=['Hari', 'Total Transaksi']
        ).properties(height=350)
        st.altair_chart(chart_pola, use_container_width=True)
    with a2:
        df_filtered['Jam'] = df_filtered['Date'].dt.hour
        jam_df = df_filtered.groupby('Jam', as_index=False).size().rename(columns={'size':'Total Transaksi'})
        jam_df['Jam_Label'] = jam_df['Jam'].apply(lambda x: f"{x:02d}:00")
        chart_jam = alt.Chart(jam_df).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
            x=alt.X('Jam_Label:N', sort=jam_df['Jam_Label'].tolist(), title='Jam'), y=alt.Y('Total Transaksi:Q'),
            color=alt.condition(alt.datum['Total Transaksi'] == jam_df['Total Transaksi'].max(), alt.value('#f5a623'), alt.value('#64ffda')),
            tooltip=['Jam_Label', 'Total Transaksi']
        ).properties(height=350)
        st.altair_chart(chart_jam, use_container_width=True)

# ==========================================
# TAB 5: LAYANAN & PAYMENT
# ==========================================
with tab5:
    st.header(f"💳 Distribusi Layanan ({selected_kpi})")
    s1, s2 = st.columns(2)
    with s1:
        top_serv = df_filtered['Service'].value_counts().reset_index().rename(columns={'Service':'Jenis Layanan', 'count':'Total Dipakai'})
        chart_serv = alt.Chart(top_serv).mark_arc(innerRadius=60).encode(
            theta=alt.Theta(field="Total Dipakai", type="quantitative"),
            color=alt.Color(field="Jenis Layanan", type="nominal", scale=alt.Scale(scheme='category20b')),
            tooltip=['Jenis Layanan', 'Total Dipakai']
        ).properties(height=300)
        st.altair_chart(chart_serv, use_container_width=True)
    with s2:
        top_pay = df_filtered['Payment_Method'].value_counts().reset_index().rename(columns={'Payment_Method':'Metode', 'count':'Total Transaksi'})
        chart_pay = alt.Chart(top_pay).mark_bar(cornerRadiusTopRight=5, cornerRadiusBottomRight=5).encode(
            y=alt.Y('Metode:N', sort='-x', title='Tipe / Marketplace'), x=alt.X('Total Transaksi:Q', title='Penggunaan'),
            color=alt.Color('Metode:N', scale=alt.Scale(scheme='set1'), legend=None), tooltip=['Metode', 'Total Transaksi']
        ).properties(height=300)
        st.altair_chart(chart_pay, use_container_width=True)

# ==========================================
# TAB 6: PEMETAAN DESTINASI
# ==========================================
# ==========================================
# TAB 6: PEMETAAN DESTINASI (WITH 3D MAP)
# ==========================================
# ==========================================
# TAB 6: PEMETAAN DESTINASI (TANPA INSTALL)
# ==========================================
with tab6:
    st.header(f"📍 Analisis Wilayah Destinasi ({selected_kpi})")
    df_dest = df_filtered[df_filtered['Destination'] != '-']
    if not df_dest.empty:
        dest_df = df_dest.groupby('Destination', as_index=False).agg({'Revenue': 'sum', 'SCO': 'count'}).rename(columns={'SCO': 'Total Resi'}).sort_values('Total Resi', ascending=False)
        
        # --- 1. KAMUS KOORDINAT LENGKAP (Gak perlu Geopy) ---
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
        
        # --- 2. SISTEM PETA PREMIUM PYDECK ---
        dest_df['lat'] = dest_df['Destination'].apply(lambda x: CITY_COORDS.get(x, [None, None])[0])
        dest_df['lon'] = dest_df['Destination'].apply(lambda x: CITY_COORDS.get(x, [None, None])[1])
        
        map_df = dest_df.dropna(subset=['lat', 'lon']).copy()
        
        if not map_df.empty:
            st.subheader("🗺️ Peta 3D Persebaran Logistik")
            st.markdown("<p style='color:#a8b2d1; font-size:0.9rem;'>Besar cahaya titik menandakan tingginya jumlah resi. (Bisa di-zoom & di-geser)</p>", unsafe_allow_html=True)
            
            # Bikin radius (ukuran titik) proporsional sama jumlah resi
            map_df['radius'] = map_df['Total Resi'] * 800 
            map_df['radius'] = map_df['radius'].clip(lower=4000, upper=60000) # Biar ga kegedean/kekecilan
            
            layer = pdk.Layer(
                'ScatterplotLayer',
                data=map_df,
                get_position='[lon, lat]',
                get_radius='radius',
                get_fill_color='[100, 255, 218, 140]', # Warna Neon Cyan
                get_line_color='[255, 255, 255]',
                pickable=True,
                auto_highlight=True
            )
            
            # Kamera awal menghadap pulau Jawa
            view_state = pdk.ViewState(latitude=-6.2, longitude=110.0, zoom=5, pitch=45)
            
            r = pdk.Deck(
                layers=[layer], initial_view_state=view_state,
                tooltip={"text": "📍 {Destination}\n📦 Resi: {Total Resi}\n💰 Rev: Rp {Revenue}"},
                map_style='dark' # Ini kunci biar petanya nongol bro!
            )
            st.pydeck_chart(r)
        else:
            st.info("💡 Peta logistik belum bisa ditampilkan. Pastikan nama kota sudah ada di kamus sistem.")
            
        st.markdown("---")
        
        # --- 3. DIAGRAM LAMA TETEP ADA DI BAWAHNYA ---
        st.subheader("📊 Rincian Top Destinasi")
        d1, d2 = st.columns([2, 1])
        top15_df = dest_df.head(15).copy()
        with d1:
            chart_dest = alt.Chart(top15_df).mark_arc(innerRadius=70, cornerRadius=4).encode(
                theta=alt.Theta(field="Total Resi", type="quantitative"),
                color=alt.Color(field="Destination", type="nominal", scale=alt.Scale(scheme='tealblues'), legend=None),
                tooltip=['Destination', 'Total Resi', 'Revenue']
            ).properties(height=400)
            st.altair_chart(chart_dest, use_container_width=True)
        with d2:
            top15_df.index = range(1, len(top15_df) + 1) 
            st.dataframe(top15_df[['Destination', 'Total Resi']], use_container_width=True)
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
            area_rev = base_rev.mark_area(opacity=0.2, color='#00b4d8', interpolate='monotone').encode(y=alt.Y('Total Revenue:Q', title='Pendapatan (Rp)'))
            line_rev = base_rev.mark_line(color='#00d4ff', strokeWidth=4, interpolate='monotone').encode(y='Total Revenue:Q')
            points_rev = base_rev.mark_circle(color='#ffffff', size=120, opacity=1).encode(y='Total Revenue:Q', tooltip=['Periode', 'Total Revenue'])
            st.altair_chart((area_rev + line_rev + points_rev).properties(height=350), use_container_width=True)
            
        with b2:
            base_trx = alt.Chart(tren_bulan).encode(x=alt.X('Periode:N', sort=sort_order, title='Bulan', axis=alt.Axis(labelAngle=0, grid=False)))
            area_trx = base_trx.mark_area(opacity=0.2, color='#ffb703', interpolate='monotone').encode(y=alt.Y('Total Transaksi:Q', title='Jumlah Resi'))
            line_trx = base_trx.mark_line(color='#ffea00', strokeWidth=4, interpolate='monotone').encode(y='Total Transaksi:Q')
            points_trx = base_trx.mark_circle(color='#ffffff', size=120, opacity=1).encode(y='Total Transaksi:Q', tooltip=['Periode', 'Total Transaksi'])
            st.altair_chart((area_trx + line_trx + points_trx).properties(height=350), use_container_width=True)
            
        # FITUR BARU: Master Table di Tab 7
        st.markdown("---")
        st.subheader("📋 Master Table Tren Bulanan")
        tabel_tren = tren_bulan.copy()
        tabel_tren['Total Revenue'] = tabel_tren['Total Revenue'].apply(format_rupiah)
        tabel_tren.index = range(1, len(tabel_tren) + 1)
        st.dataframe(tabel_tren[['Periode', 'Total Transaksi', 'Total Revenue']], use_container_width=True)

# ==========================================
# TAB 8: EXECUTIVE SUMMARY 
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
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    e1, e2 = st.columns([2, 1])
    with e1:
        st.subheader("📊 Komposisi Revenue SCO berdasarkan KPI")
        rekap_chart = df_global.groupby(['SCO', 'KPI'], as_index=False)['Revenue'].sum()
        chart_global = alt.Chart(rekap_chart).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
            x=alt.X('SCO:N', sort='-y', title='Nama SCO'),
            y=alt.Y('Revenue:Q', title='Total Revenue (Rp)'),
            color=alt.Color('KPI:N', scale=alt.Scale(scheme='set2'), title='Jenis KPI'),
            tooltip=['SCO', 'KPI', 'Revenue']
        ).properties(height=400)
        st.altair_chart(chart_global, use_container_width=True)

    with e2:
        st.subheader("📋 Master Table")
        
        # FITUR BARU: Nambahin Total Resi di Master Table Tab 8
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
        st.dataframe(global_rekap, use_container_width=True)
