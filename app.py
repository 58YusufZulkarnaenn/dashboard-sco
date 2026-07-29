import streamlit as st
import pandas as pd
import altair as alt
import glob
import os

# ==========================================
# 1. SETTING HALAMAN & INJEKSI CSS PREMIUM
# ==========================================
st.set_page_config(page_title="Dashboard SCO", page_icon="📦", layout="wide")

def add_custom_css():
    st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #141e30 0%, #243b55 100%);
        color: #ffffff;
    }
    [data-testid="stHeader"] { background: rgba(0,0,0,0); }
    [data-testid="stSidebar"] {
        background: rgba(20, 30, 48, 0.6) !important;
        backdrop-filter: blur(15px);
        -webkit-backdrop-filter: blur(15px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    [data-testid="stMetricLabel"] { color: #a8b2d1 !important; font-weight: 600; font-size: 1.1rem; }
    [data-testid="stMetricValue"] { color: #64ffda !important; font-weight: 800; }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px; background-color: rgba(255, 255, 255, 0.05);
        border-radius: 15px; padding: 10px; box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important; border-radius: 10px !important;
        color: #a8b2d1 !important; padding: 10px 20px; font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(100, 255, 218, 0.1) !important; color: #64ffda !important;
        border: 1px solid rgba(100, 255, 218, 0.3) !important; box-shadow: 0 0 15px rgba(100, 255, 218, 0.1);
    }
    h1, h2, h3, p, .stMarkdown { color: #ffffff !important; }
    </style>
    """, unsafe_allow_html=True)

add_custom_css()

# ==========================================
# FUNGSI KELOLA DATA & STANDARISASI
# ==========================================
@st.cache_data
def load_unified_data(file_paths):
    all_raw = []
    all_rata2 = []
    
    for f in file_paths:
        try:
            filename = os.path.basename(f).lower()
            
            # Deteksi KPI dari nama file
            if "cashless" in filename: kpi_type = "Cashless"
            elif "kredit auto" in filename: kpi_type = "Kredit Auto"
            elif "kredit manual" in filename: kpi_type = "Kredit Manual"
            else: kpi_type = "Cash" # Default ke Cash
                
            xls = pd.ExcelFile(f)
            
            # 1. LOAD RAW DATA
            if "Raw Data" in xls.sheet_names:
                df = pd.read_excel(xls, "Raw Data")
                
                # BUG FIXED DISINI: Kunci indexnya dulu biar baris data nggak jadi NaN!
                df_std = pd.DataFrame(index=df.index) 
                
                df_std['KPI'] = kpi_type
                
                # Standarisasi Kolom
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
                
                if kpi_type == "Cashless":
                    col_pay = 'Marketplace_Clean' if 'Marketplace_Clean' in df.columns else ('Marketplace' if 'Marketplace' in df.columns else None)
                    df_std['Payment_Method'] = df[col_pay].fillna("Lainnya") if col_pay else "Lainnya"
                elif kpi_type == "Cash":
                    df_std['Payment_Method'] = df['Payment type'].fillna("Cash") if 'Payment type' in df.columns else "Cash"
                else:
                    df_std['Payment_Method'] = kpi_type
                    
                all_raw.append(df_std)
            
            # 2. LOAD RATA-RATA (Khusus Cash)
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
# SIDEBAR KIRI: PENGATURAN
# ==========================================
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3063/3063822.png", width=100)
st.sidebar.header("📅 Pengaturan Data")

list_file_excel = glob.glob("*.xlsx")
list_file_excel = [f for f in list_file_excel if not f.startswith("~$")]

if len(list_file_excel) == 0:
    st.error("Belum ada file Excel yang terdeteksi bro. Upload filenya dulu!")
    st.stop()

# Load Data Master secara global
df_master, df_rata2_master = load_unified_data(tuple(list_file_excel))

if df_master.empty:
    st.error("Gagal membaca data dari file Excel. Pastikan sheet 'Raw Data' ada di dalam file.")
    st.stop()

df_master = df_master.dropna(subset=['Date', 'SCO'])
df_master['Date_Only'] = df_master['Date'].dt.date

st.sidebar.markdown("---")
st.sidebar.header("🔍 Filter Analytics")

# 1. PILIH KPI (Cuma bisa 1)
available_kpis = df_master['KPI'].unique().tolist()
selected_kpi = st.sidebar.selectbox("📊 Pilih Pilar KPI:", options=available_kpis)

# Filter Master Data berdasarkan KPI yang dipilih untuk setting min-max kalender
df_kpi_only = df_master[df_master['KPI'] == selected_kpi]
if df_kpi_only.empty:
    st.warning("Data untuk KPI ini kosong.")
    st.stop()

min_date = df_kpi_only['Date_Only'].min()
max_date = df_kpi_only['Date_Only'].max()

# 2. RENTANG TANGGAL
date_range = st.sidebar.date_input("📅 Rentang Tanggal", value=(min_date, max_date), min_value=min_date, max_value=max_date)
if len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = end_date = date_range[0]
    
# 3. NAMA SCO
list_sco = df_kpi_only['SCO'].dropna().unique().tolist()
selected_sco = st.sidebar.multiselect("👨‍💼 Pilih SCO (Bisa >1):", options=list_sco, default=[], help="Kosongkan buat nampilin semua")

# ==========================================
# EKSEKUSI FILTER UTAMA (TAB 1-5)
# ==========================================
mask_date = (df_kpi_only['Date_Only'] >= start_date) & (df_kpi_only['Date_Only'] <= end_date)
df_filtered = df_kpi_only[mask_date].copy()

if selected_sco:
    df_filtered = df_filtered[df_filtered['SCO'].isin(selected_sco)]

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

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📈 Dashboard Utama", 
    "🏆 Top Customer", 
    f"👨‍💼 Kinerja SCO ({selected_kpi})", 
    "⏰ Pola & Jam Sibuk", 
    "💳 Layanan & Payment",
    f"🚀 Tren {selected_kpi}",
    "🌐 Rekap Global (Semua KPI)"
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
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📦 TOTAL TRANSAKSI", f"{total_resi} Resi")
    c2.metric("💰 TOTAL REVENUE", format_rupiah(total_rev))
    c3.metric("📈 RATA-RATA / TRANSAKSI", format_rupiah(rata_transaksi))
    c4.metric("⚖️ TOTAL BERAT", f"{total_berat:,.1f} Kg")
    
    st.markdown("<br>", unsafe_allow_html=True)
    c5, c6, c7, c8 = st.columns(4)
    c5.metric("🏆 BEST SCO", f"{best_user}", format_rupiah(best_user_rev))
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

# ==========================================
# TAB 2: TOP CUSTOMER
# ==========================================
with tab2:
    st.header(f"🏆 Analisis Top Customer ({selected_kpi})")
    df_cust = df_filtered[(df_filtered['Customer'] != '-') & (df_filtered['Customer'].notna())]
    if df_cust.empty:
        st.info("Tidak ada data nama Customer di periode ini.")
    else:
        col_rev, col_con = st.columns(2)
        with col_rev:
            st.subheader("🥇 Top 10 (Berdasarkan Revenue)")
            top_rev = df_cust.groupby('Customer', as_index=False).agg({'Revenue':'sum', 'SCO':'count'}).rename(columns={'Revenue':'Total Belanja', 'SCO':'Total Resi'}).sort_values(by='Total Belanja', ascending=False).head(10)
            chart_rev = alt.Chart(top_rev).mark_bar(cornerRadiusTopRight=5, cornerRadiusBottomRight=5).encode(
                x=alt.X('Total Belanja:Q', title='Revenue (Rp)'), y=alt.Y('Customer:N', sort='-x', title='Customer'),
                color=alt.Color('Total Belanja:Q', scale=alt.Scale(scheme='blues'), legend=None), tooltip=['Customer', 'Total Belanja', 'Total Resi']
            ).properties(height=400)
            st.altair_chart(chart_rev, use_container_width=True)
            
        with col_con:
            st.subheader("🔢 Top 10 (Berdasarkan Resi)")
            top_con = df_cust.groupby('Customer', as_index=False).agg({'SCO':'count', 'Revenue':'sum'}).rename(columns={'SCO':'Total Resi', 'Revenue':'Total Belanja'}).sort_values(by='Total Resi', ascending=False).head(10)
            chart_con = alt.Chart(top_con).mark_bar(cornerRadiusTopRight=5, cornerRadiusBottomRight=5).encode(
                x=alt.X('Total Resi:Q', title='Transaksi (Resi)'), y=alt.Y('Customer:N', sort='-x', title='Customer'),
                color=alt.Color('Total Resi:Q', scale=alt.Scale(scheme='oranges'), legend=None), tooltip=['Customer', 'Total Resi', 'Total Belanja']
            ).properties(height=400)
            st.altair_chart(chart_con, use_container_width=True)

# ==========================================
# TAB 3: KINERJA SCO (LOGIKA CERDAS)
# ==========================================
with tab3:
    if selected_kpi == "Cash":
        st.header("👨‍💼 Rata-Rata Hari Masuk & Produktivitas SCO")
        if df_rata2_master.empty:
            st.info("Data sheet 'Rata-Rata Hari Masuk' tidak ditemukan di file Cash ini.")
        else:
            # Filter rata-rata sesuai SCO yang dipilih di sidebar
            df_r_clean = df_rata2_master.copy()
            if selected_sco:
                df_r_clean = df_r_clean[df_r_clean['User id'].isin(selected_sco)]
            
            for col in ['Total_Connote', 'Revenue', 'Hari_Masuk']:
                if col in df_r_clean.columns:
                    df_r_clean[col] = pd.to_numeric(df_r_clean[col], errors='coerce').fillna(0)
                    
            # Jumlahkan dulu jika ada lebih dari 1 file cash
            agg_rules = {}
            if 'Total_Connote' in df_r_clean.columns: agg_rules['Total_Connote'] = 'sum'
            if 'Revenue' in df_r_clean.columns: agg_rules['Revenue'] = 'sum'
            if 'Hari_Masuk' in df_r_clean.columns: agg_rules['Hari_Masuk'] = 'sum'
            
            if agg_rules:
                df_r_clean = df_r_clean.groupby('User id', as_index=False).agg(agg_rules)
                
            if 'Hari_Masuk' in df_r_clean.columns:
                if 'Total_Connote' in df_r_clean.columns:
                    df_r_clean['Rata_Transaksi_Per_Hari'] = (df_r_clean['Total_Connote'] / df_r_clean['Hari_Masuk']).fillna(0).round(1)
                if 'Revenue' in df_r_clean.columns:
                    df_r_clean['Rata_Pendapatan_Per_Hari'] = (df_r_clean['Revenue'] / df_r_clean['Hari_Masuk']).fillna(0)
                    
            if 'Rata_Pendapatan_Per_Hari' in df_r_clean.columns:
                df_r_clean['Rata_Pendapatan_Per_Hari_Num'] = df_r_clean['Rata_Pendapatan_Per_Hari']
                
            # Formatting
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
        # TAMPILAN KHUSUS SELAIN CASH (Hanya Total Resi & Total Revenue)
        st.header(f"👨‍💼 Rekapitulasi Kinerja SCO ({selected_kpi})")
        st.markdown("<p style='color:#a8b2d1 !important;'>Catatan: Rata-rata hari masuk tidak dihitung pada KPI ini untuk menjaga keakuratan evaluasi kinerja.</p>", unsafe_allow_html=True)
        
        rekap_sco = df_filtered.groupby('SCO', as_index=False).agg(
            Total_Resi=('Revenue', 'count'), Total_Revenue=('Revenue', 'sum')
        ).sort_values('Total_Revenue', ascending=False)
        
        # Bikin duplikat buat chart
        rekap_sco['Total_Revenue_Num'] = rekap_sco['Total_Revenue']
        
        st.subheader("📊 Total Pendapatan Tiap Kasir")
        chart_noncash = alt.Chart(rekap_sco).mark_bar(size=50, cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
            x=alt.X('SCO:N', title='Kasir (SCO)', sort='-y'), y=alt.Y('Total_Revenue_Num:Q', title='Total Revenue (Rp)'),
            color=alt.Color('SCO:N', scale=alt.Scale(scheme='set2'), legend=None), tooltip=['SCO', 'Total_Resi', 'Total_Revenue_Num']
        ).properties(height=350)
        st.altair_chart(chart_noncash, use_container_width=True)
        
        # Formatting buat ditampilin di tabel
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
# TAB 6: TREN LINTAS BULAN (Sesuai KPI)
# ==========================================
with tab6:
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

# ==========================================
# TAB 7: REKAP GLOBAL SCO (KEBAL FILTER)
# ==========================================
with tab7:
    st.header("🌐 Akumulasi Keseluruhan (Master Summary)")
    st.markdown("<p style='color:#a8b2d1 !important;'>Tabel ini <b>kebal terhadap filter Sidebar</b>. Menarik SEMUA data dari SEMUA file yang di-upload untuk melihat total pencapaian masing-masing SCO di setiap pilar KPI.</p>", unsafe_allow_html=True)
    
    # 1. Pivot Jumlah Resi (Volume)
    pivot_resi = df_master.pivot_table(index='SCO', columns='KPI', values='Revenue', aggfunc='count', fill_value=0)
    pivot_resi['Total Semua Resi'] = pivot_resi.sum(axis=1)
    
    # 2. Pivot Total Pendapatan (Revenue)
    pivot_rev = df_master.pivot_table(index='SCO', columns='KPI', values='Revenue', aggfunc='sum', fill_value=0)
    pivot_rev['Total Pendapatan Akhir'] = pivot_rev.sum(axis=1)
    
    # Prefix nama kolom biar jelas saat digabung
    pivot_resi.columns = [f"📦 Resi {c}" if c != 'Total Semua Resi' else c for c in pivot_resi.columns]
    pivot_rev.columns = [f"💰 Rev {c}" if c != 'Total Pendapatan Akhir' else c for c in pivot_rev.columns]
    
    # 3. Gabungkan kedua Pivot
    global_rekap = pd.concat([pivot_resi, pivot_rev], axis=1).reset_index()
    
    # Sortir berdasarkan yang pendapatannya paling tinggi
    global_rekap = global_rekap.sort_values('Total Pendapatan Akhir', ascending=False)
    
    # 4. Format jadi Rupiah buat kolom Revenue
    rev_cols = [c for c in global_rekap.columns if "Rev" in c or "Pendapatan" in c]
    for c in rev_cols:
        global_rekap[c] = global_rekap[c].apply(format_rupiah)
        
    global_rekap.index = range(1, len(global_rekap) + 1)
    st.dataframe(global_rekap, use_container_width=True)
