import streamlit as st
import pandas as pd
import altair as alt
import glob

# Setting tampilan web
st.set_page_config(page_title="Dashboard SCO", page_icon="📦", layout="wide")

# ==========================================
# SIDEBAR KIRI: MESIN WAKTU (PILIH BULAN)
# ==========================================
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3063/3063822.png", width=100)
st.sidebar.header("📅 Pengaturan Waktu")
st.sidebar.markdown("Pilih periode data yang mau ditampilkan.")

list_file_excel = glob.glob("*.xlsx")
list_file_excel = [f for f in list_file_excel if not f.startswith("~$")]

if len(list_file_excel) == 0:
    st.error("Waduh, belum ada file Excel yang terdeteksi nih bro. Upload dulu ke GitHub ya!")
    st.stop()

selected_file = st.sidebar.selectbox("📂 Pilih File Periode:", list_file_excel)
st.sidebar.markdown("---")
st.sidebar.success(f"Sedang menampilkan detail dari:\n**{selected_file}**")

# ==========================================
# HEADER UTAMA
# ==========================================
st.title("📊 Dashboard Performa Pengiriman KP Grand Taruma")
st.markdown("(By Yusuf Zulkarnaen)")
st.markdown("Rekapitulasi lengkap data operasional, performa tim, dan insight pelanggan.")
st.markdown("---")

# Fungsi baca 1 file (Buat Tab 1-5)
@st.cache_data
def load_data(file_path):
    xls = pd.ExcelFile(file_path)
    df_raw = pd.read_excel(xls, "Raw Data")
    df_rata2 = pd.read_excel(xls, "Rata-Rata Hari Masuk")
    return df_raw, df_rata2

# Fungsi baca SEMUA file (Khusus buat Tab Tren Lintas Bulan)
@st.cache_data
def load_all_data(file_list):
    all_data = []
    for f in file_list:
        try:
            df = pd.read_excel(f, sheet_name="Raw Data")
            all_data.append(df)
        except Exception as e:
            pass
    if all_data:
        df_gabung = pd.concat(all_data, ignore_index=True)
        return df_gabung
    return pd.DataFrame()

def format_rupiah(val):
    return f"Rp {val:,.0f}".replace(",", ".")

try:
    df, df_rata2 = load_data(selected_file)
    df_all = load_all_data(list_file_excel) # Tarik semua data diem-diem
    
    # ADA 6 TAB SEKARANG!
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📈 Dashboard Utama", 
        "🏆 Top Customer", 
        "👨‍💼 Kinerja SCO", 
        "⏰ Pola & Jam Sibuk", 
        "💳 Layanan & Payment",
        "🚀 Tren Lintas Bulan"
    ])
    
    # ==========================================
    # TAB 1: DASHBOARD UTAMA
    # ==========================================
    with tab1:
        st.header("Ringkasan Performa Bulan Ini")
        
        total_resi = len(df)
        total_rev = df['Amount'].sum()
        total_berat = df['Weight'].sum()
        rata_transaksi = total_rev / total_resi if total_resi > 0 else 0
        
        rekap_user = df.groupby('User id')['Amount'].sum().sort_values(ascending=False)
        best_user = rekap_user.index[0] if not rekap_user.empty else "-"
        best_user_rev = rekap_user.iloc[0] if not rekap_user.empty else 0
        
        sco_aktif = df['User id'].nunique()
        layanan_top = df['Services'].mode()[0] if not df['Services'].empty else "-"
        pay_top = df['Payment type'].mode()[0] if not df['Payment type'].empty else "-"
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📦 TOTAL TRANSAKSI", f"{total_resi} Resi")
        c2.metric("💰 TOTAL REVENUE", format_rupiah(total_rev))
        c3.metric("📈 RATA-RATA / TRANSAKSI", format_rupiah(rata_transaksi))
        c4.metric("⚖️ TOTAL BERAT", f"{total_berat:,.1f} Kg")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        c5, c6, c7, c8 = st.columns(4)
        c5.metric("🏆 BEST USER (SCO)", f"{best_user}", format_rupiah(best_user_rev))
        c6.metric("👥 SCO AKTIF", f"{sco_aktif} Orang")
        c7.metric("🚚 LAYANAN TERLARIS", layanan_top)
        c8.metric("💳 METODE BAYAR FAVORIT", pay_top)
        
        st.markdown("---")
        
        kiri, kanan = st.columns(2)
        with kiri:
            st.subheader("📈 Tren Transaksi Harian (Bulan Ini)")
            df['Tanggal'] = pd.to_datetime(df['Date']).dt.date
            harian = df.groupby('Tanggal', as_index=False).size().rename(columns={'size':'Transaksi'})
            
            chart_tren = alt.Chart(harian).mark_line(point=True, color='#29b5e8', strokeWidth=3).encode(
                x=alt.X('Tanggal:T', title='Tanggal'),
                y=alt.Y('Transaksi:Q', title='Jumlah Resi'),
                tooltip=['Tanggal', 'Transaksi']
            ).properties(height=300)
            st.altair_chart(chart_tren, use_container_width=True)
            
        with kanan:
            st.subheader("🏅 Ranking Performa SCO")
            rekap_user_df = df.groupby('User id', as_index=False).agg({'Amount':'sum'}).rename(columns={'Amount':'Pendapatan'}).sort_values(by='Pendapatan', ascending=False)
            
            chart_sco = alt.Chart(rekap_user_df).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
                x=alt.X('User id:N', sort='-y', title='Nama SCO'),
                y=alt.Y('Pendapatan:Q', title='Total Revenue (Rp)'),
                color=alt.Color('User id:N', scale=alt.Scale(scheme='pastel1'), legend=None),
                tooltip=['User id', 'Pendapatan']
            ).properties(height=300)
            st.altair_chart(chart_sco, use_container_width=True)

    # ==========================================
    # TAB 2: TOP CUSTOMER
    # ==========================================
    with tab2:
        st.header("🏆 Analisis Top Customer")
        df_cust = df[df['Shipper Name'] != '-']
        
        col_rev, col_con = st.columns(2)
        
        with col_rev:
            st.subheader("🥇 Top 10 Customer (By Revenue)")
            top_rev = df_cust.groupby('Shipper Name', as_index=False).agg({'Amount':'sum', 'User id':'count'}).rename(columns={'Amount':'Total Belanja', 'User id':'Total Resi'}).sort_values(by='Total Belanja', ascending=False).head(10)
            
            chart_rev = alt.Chart(top_rev).mark_bar(cornerRadiusTopRight=5, cornerRadiusBottomRight=5).encode(
                x=alt.X('Total Belanja:Q', title='Total Revenue (Rp)'),
                y=alt.Y('Shipper Name:N', sort='-x', title='Customer'),
                color=alt.Color('Total Belanja:Q', scale=alt.Scale(scheme='blues'), legend=None),
                tooltip=['Shipper Name', 'Total Belanja', 'Total Resi']
            ).properties(height=400)
            st.altair_chart(chart_rev, use_container_width=True)
            
            top_rev_tabel = top_rev.copy()
            top_rev_tabel['Total Belanja'] = top_rev_tabel['Total Belanja'].apply(format_rupiah)
            top_rev_tabel.index = range(1, len(top_rev_tabel) + 1)
            st.dataframe(top_rev_tabel, use_container_width=True)

        with col_con:
            st.subheader("🔢 Top 10 Customer (By Connote)")
            top_con = df_cust.groupby('Shipper Name', as_index=False).agg({'User id':'count', 'Amount':'sum'}).rename(columns={'User id':'Total Resi', 'Amount':'Total Belanja'}).sort_values(by='Total Resi', ascending=False).head(10)
            
            chart_con = alt.Chart(top_con).mark_bar(cornerRadiusTopRight=5, cornerRadiusBottomRight=5).encode(
                x=alt.X('Total Resi:Q', title='Total Transaksi (Resi)'),
                y=alt.Y('Shipper Name:N', sort='-x', title='Customer'),
                color=alt.Color('Total Resi:Q', scale=alt.Scale(scheme='oranges'), legend=None),
                tooltip=['Shipper Name', 'Total Resi', 'Total Belanja']
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
        st.header("👨‍💼 Rata-Rata Hari Masuk & Produktivitas SCO")
        
        df_rata2_clean = df_rata2.loc[:, ~df_rata2.columns.str.contains('^Unnamed')].copy()
        
        for col in ['Revenue', 'Rata_Pendapatan_Per_Hari']:
            if col in df_rata2_clean.columns:
                df_rata2_clean[col] = pd.to_numeric(df_rata2_clean[col], errors='coerce').fillna(0)
                df_rata2_clean[f"{col}_Num"] = df_rata2_clean[col] 
                df_rata2_clean[col] = df_rata2_clean[col].apply(format_rupiah)
                
        if 'Rata_Transaksi_Per_Hari' in df_rata2_clean.columns:
            df_rata2_clean['Rata_Transaksi_Per_Hari'] = pd.to_numeric(df_rata2_clean['Rata_Transaksi_Per_Hari'], errors='coerce').fillna(0).round(1)

        if 'Rata_Pendapatan_Per_Hari_Num' in df_rata2_clean.columns:
            st.subheader("📊 Rata-Rata Pendapatan Harian Tiap Kasir")
            chart_absensi = alt.Chart(df_rata2_clean).mark_bar(size=50, cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
                x=alt.X('User id:N', title='Kasir (SCO)', sort='-y'),
                y=alt.Y('Rata_Pendapatan_Per_Hari_Num:Q', title='Rata-Rata Pendapatan (Rp)'),
                color=alt.Color('User id:N', scale=alt.Scale(scheme='set2'), legend=None),
                tooltip=['User id', 'Hari_Masuk', 'Rata_Pendapatan_Per_Hari']
            ).properties(height=350)
            st.altair_chart(chart_absensi, use_container_width=True)
        
        st.markdown("---")
        st.subheader("📋 Tabel Detail Produktivitas")
        cols_to_show = [c for c in df_rata2_clean.columns if not c.endswith('_Num')]
        st.dataframe(df_rata2_clean[cols_to_show], use_container_width=True)

    # ==========================================
    # TAB 4: POLA HARI & JAM SIBUK
    # ==========================================
    with tab4:
        st.header("⏰ Analisis Pola Hari & Jam Sibuk (Rush Hour)")
        
        a1, a2 = st.columns(2)
        
        with a1:
            st.subheader("📅 Pola Sibuk (Berdasarkan Hari)")
            hari_map = {'Monday': 'Senin', 'Tuesday': 'Selasa', 'Wednesday': 'Rabu', 'Thursday': 'Kamis', 'Friday': 'Jumat', 'Saturday': 'Sabtu', 'Sunday': 'Minggu'}
            df['Hari_Inggris'] = pd.to_datetime(df['Date']).dt.day_name()
            df['Hari'] = df['Hari_Inggris'].map(hari_map)
            hari_order = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
            
            pola_df = df.groupby('Hari', as_index=False).size().rename(columns={'size':'Total Transaksi'})
            
            chart_pola = alt.Chart(pola_df).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
                x=alt.X('Hari:N', sort=hari_order, title='Hari Operasional'),
                y=alt.Y('Total Transaksi:Q', title='Jumlah Transaksi'),
                color=alt.condition(
                    alt.datum['Total Transaksi'] == pola_df['Total Transaksi'].max(), 
                    alt.value('#ff4b4b'),
                    alt.value('#ff9f9f')
                ),
                tooltip=['Hari', 'Total Transaksi']
            ).properties(height=350)
            st.altair_chart(chart_pola, use_container_width=True)
            
        with a2:
            st.subheader("⏰ Jam Sibuk (Rush Hour)")
            df['Jam'] = pd.to_datetime(df['Date']).dt.hour
            jam_df = df.groupby('Jam', as_index=False).size().rename(columns={'size':'Total Transaksi'})
            jam_df['Jam_Label'] = jam_df['Jam'].apply(lambda x: f"{x:02d}:00")
            
            chart_jam = alt.Chart(jam_df).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
                x=alt.X('Jam_Label:N', sort=jam_df['Jam_Label'].tolist(), title='Jam Operasional'),
                y=alt.Y('Total Transaksi:Q', title='Jumlah Paket Masuk'),
                color=alt.condition(
                    alt.datum['Total Transaksi'] == jam_df['Total Transaksi'].max(), 
                    alt.value('#f5a623'),
                    alt.value('#fbe1b6')
                ),
                tooltip=['Jam_Label', 'Total Transaksi']
            ).properties(height=350)
            st.altair_chart(chart_jam, use_container_width=True)

    # ==========================================
    # TAB 5: LAYANAN & PAYMENT
    # ==========================================
    with tab5:
        st.header("💳 Komposisi Layanan & Metode Pembayaran")
        
        s1, s2 = st.columns(2)
        with s1:
            st.subheader("📦 Layanan Paling Laku")
            top_serv = df['Services'].value_counts().reset_index().rename(columns={'Services':'Jenis Layanan', 'count':'Total Dipakai'})
            
            chart_serv = alt.Chart(top_serv).mark_arc(innerRadius=70).encode(
                theta=alt.Theta(field="Total Dipakai", type="quantitative"),
                color=alt.Color(field="Jenis Layanan", type="nominal", scale=alt.Scale(scheme='category20b')),
                tooltip=['Jenis Layanan', 'Total Dipakai']
            ).properties(height=350)
            st.altair_chart(chart_serv, use_container_width=True)
            
        with s2:
            st.subheader("💳 Metode Pembayaran")
            top_pay = df['Payment type'].value_counts().reset_index().rename(columns={'Payment type':'Metode', 'count':'Total Transaksi'})
            
            chart_pay = alt.Chart(top_pay).mark_bar(size=70, cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
                x=alt.X('Metode:N', sort='-y', title='Tipe Pembayaran'),
                y=alt.Y('Total Transaksi:Q', title='Jumlah Penggunaan'),
                color=alt.Color('Metode:N', scale=alt.Scale(scheme='set1'), legend=None),
                tooltip=['Metode', 'Total Transaksi']
            ).properties(height=350)
            st.altair_chart(chart_pay, use_container_width=True)

    # ==========================================
    # TAB 6: TREN LINTAS BULAN (BARU!)
    # ==========================================
    with tab6:
        st.header("🚀 Pertumbuhan Bisnis (Akumulasi Seluruh Bulan)")
        st.markdown("Grafik ini menarik data dari **semua file Excel** yang ada di sistem lu buat ngeliat tren jangka panjang.")
        
        if not df_all.empty:
            # Format tanggal jadi Bulan-Tahun (Contoh: 2026-05, 2026-06)
            df_all['Periode'] = pd.to_datetime(df_all['Date']).dt.strftime('%Y-%m')
            
            tren_bulan = df_all.groupby('Periode', as_index=False).agg({
                'Amount': 'sum', 
                'User id': 'count'
            }).rename(columns={'Amount': 'Total Revenue', 'User id': 'Total Transaksi'})
            
            tren_bulan = tren_bulan.sort_values('Periode')
            
            b1, b2 = st.columns(2)
            with b1:
                st.subheader("💰 Tren Pendapatan (Revenue)")
                chart_rev_all = alt.Chart(tren_bulan).mark_line(point=True, color='#28a745', strokeWidth=4).encode(
                    x=alt.X('Periode:N', title='Bulan Tahun'),
                    y=alt.Y('Total Revenue:Q', title='Pendapatan (Rp)'),
                    tooltip=['Periode', 'Total Revenue']
                ).properties(height=350)
                st.altair_chart(chart_rev_all, use_container_width=True)
                
            with b2:
                st.subheader("📦 Tren Volume (Transaksi)")
                chart_trx_all = alt.Chart(tren_bulan).mark_line(point=True, color='#007bff', strokeWidth=4).encode(
                    x=alt.X('Periode:N', title='Bulan Tahun'),
                    y=alt.Y('Total Transaksi:Q', title='Jumlah Resi'),
                    tooltip=['Periode', 'Total Transaksi']
                ).properties(height=350)
                st.altair_chart(chart_trx_all, use_container_width=True)
                
            st.markdown("---")
            st.subheader("📋 Rekap Angka Bulanan")
            tren_tabel = tren_bulan.copy()
            tren_tabel['Total Revenue'] = tren_tabel['Total Revenue'].apply(format_rupiah)
            
            # Bikin urutan ranking 1, 2, 3..
            tren_tabel.index = range(1, len(tren_tabel) + 1)
            st.dataframe(tren_tabel, use_container_width=True)
        else:
            st.info("Wah, data belum cukup buat nampilin tren nih bro.")

except Exception as e:
    st.error(f"Waduh, ada error nih bro: {e}")
