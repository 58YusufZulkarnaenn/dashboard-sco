import streamlit as st
import pandas as pd
import numpy as np

# Setting tampilan web biar lebar, biar muat banyak diagram
st.set_page_config(page_title="Dashboard SCO", page_icon="📦", layout="wide")

st.title("📊 Dashboard Performa Pengiriman SCO (Ultimate)")
st.markdown("Rekapitulasi lengkap data operasional, performa tim, dan insight pelanggan.")
st.markdown("---")

@st.cache_data
def load_data():
    file_path = "REKAP DATA CASH MEI 2026.xlsx"
    # Narik semua sheet penting
    xls = pd.ExcelFile(file_path)
    df_raw = pd.read_excel(xls, "Raw Data")
    df_rata2 = pd.read_excel(xls, "Rata-Rata Hari Masuk")
    df_matrix = pd.read_excel(xls, "Matrix Harian User")
    df_riwayat = pd.read_excel(xls, "Riwayat Bulanan", header=None) # Ambil mentah biar strukturnya ga rusak
    return df_raw, df_rata2, df_matrix, df_riwayat

try:
    df, df_rata2, df_matrix, df_riwayat = load_data()
    
    # 5 TABS UTAMA (Semua Sheet Masuk Sini)
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Dashboard Utama", 
        "🏆 Top Customer", 
        "👨‍💼 Matrix & Absensi SCO", 
        "📍 Area, Layanan & Payment", 
        "🗓️ Riwayat Bulanan"
    ])
    
    # ==========================================
    # TAB 1: DASHBOARD UTAMA (Bikin Rame & Padat)
    # ==========================================
    with tab1:
        st.header("Ringkasan Performa Bulan Ini")
        
        # Hitung Insight buat Dashboard
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
        
        # Baris 1: Metrik Utama
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📦 TOTAL TRANSAKSI (Connote)", f"{total_resi} Resi")
        c2.metric("💰 TOTAL REVENUE", f"Rp {total_rev:,.0f}".replace(",", "."))
        c3.metric("📈 RATA-RATA / TRANSAKSI", f"Rp {rata_transaksi:,.0f}".replace(",", "."))
        c4.metric("⚖️ TOTAL BERAT", f"{total_berat:,.1f} Kg")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Baris 2: Insight Spesifik
        c5, c6, c7, c8 = st.columns(4)
        c5.metric("🏆 BEST USER (SCO)", f"{best_user}", f"Rp {best_user_rev:,.0f}".replace(",", "."))
        c6.metric("👥 SCO AKTIF BULAN INI", f"{sco_aktif} Orang")
        c7.metric("🚚 LAYANAN TERLARIS", layanan_top)
        c8.metric("💳 METODE BAYAR FAVORIT", pay_top)
        
        st.markdown("---")
        
        # Baris 3: Diagram & Grafik Rame
        kiri, kanan = st.columns(2)
        with kiri:
            st.subheader("📈 Tren Transaksi & Pendapatan Harian")
            df['Tanggal'] = pd.to_datetime(df['Date']).dt.date
            harian = df.groupby('Tanggal').agg({'Amount':'sum', 'User id':'count'}).rename(columns={'Amount':'Revenue', 'User id':'Transaksi'})
            # Nampilin dual chart (Bar & Line) make line_chart buat gampangnya
            st.line_chart(harian['Transaksi'])
            
        with kanan:
            st.subheader("🏅 Ranking Performa SCO")
            rekap_user_df = df.groupby('User id').agg({'User id':'count', 'Amount':'sum'}).rename(columns={'User id':'Total Transaksi', 'Amount':'Pendapatan'}).sort_values(by='Pendapatan', ascending=False)
            st.bar_chart(rekap_user_df['Pendapatan'])

    # ==========================================
    # TAB 2: TOP CUSTOMER (Connote vs Revenue)
    # ==========================================
    with tab2:
        st.header("🏆 Analisis Top Customer")
        df_cust = df[df['Shipper Name'] != '-']
        
        total_cust_unik = df_cust['Shipper Name'].nunique()
        cust_repeat = df_cust.groupby('Shipper Name').size()
        jumlah_repeat = len(cust_repeat[cust_repeat > 1])
        
        k1, k2 = st.columns(2)
        k1.metric("👤 TOTAL CUSTOMER UNIK", total_cust_unik)
        k2.metric("🔂 CUSTOMER REPEAT (Order > 1x)", f"{jumlah_repeat} dari {total_cust_unik}")
        
        st.markdown("---")
        
        col_rev, col_con = st.columns(2)
        
        # By Revenue
        with col_rev:
            st.subheader("🥇 Top 15 Customer (By Revenue)")
            top_rev = df_cust.groupby('Shipper Name').agg({'Amount':'sum', 'User id':'count'}).rename(columns={'Amount':'Total Belanja (Rp)', 'User id':'Total Resi'}).sort_values(by='Total Belanja (Rp)', ascending=False).head(15)
            # Tampilin Diagram
            st.bar_chart(top_rev['Total Belanja (Rp)'])
            # Tampilin Tabel
            top_rev_tabel = top_rev.copy()
            top_rev_tabel['Total Belanja (Rp)'] = top_rev_tabel['Total Belanja (Rp)'].apply(lambda x: f"Rp {x:,.0f}".replace(",", "."))
            st.dataframe(top_rev_tabel, use_container_width=True)

        # By Connote
        with col_con:
            st.subheader("🔢 Top 15 Customer (By Connote)")
            top_con = df_cust.groupby('Shipper Name').agg({'User id':'count', 'Amount':'sum'}).rename(columns={'User id':'Total Resi', 'Amount':'Total Belanja (Rp)'}).sort_values(by='Total Resi', ascending=False).head(15)
            # Tampilin Diagram
            st.bar_chart(top_con['Total Resi'])
            # Tampilin Tabel
            top_con_tabel = top_con.copy()
            top_con_tabel['Total Belanja (Rp)'] = top_con_tabel['Total Belanja (Rp)'].apply(lambda x: f"Rp {x:,.0f}".replace(",", "."))
            st.dataframe(top_con_tabel, use_container_width=True)

    # ==========================================
    # TAB 3: MATRIX & ABSENSI SCO
    # ==========================================
    with tab3:
        st.header("👨‍💼 Kinerja Harian & Absensi Kasir (SCO)")
        
        st.subheader("Rata-Rata Hari Masuk & Produktivitas")
        # Bersihin kolom Unnamed dari sheet
        df_rata2_clean = df_rata2.loc[:, ~df_rata2.columns.str.contains('^Unnamed')]
        st.dataframe(df_rata2_clean, use_container_width=True)
        
        st.markdown("---")
        st.subheader("Matrix Harian User (Jadwal & Pencapaian)")
        # Bersihin kolom Unnamed (Bulan Aktif, dll) biar tabel matrix rapi
        df_matrix_clean = df_matrix.loc[:, ~df_matrix.columns.str.contains('^Unnamed')]
        st.dataframe(df_matrix_clean, use_container_width=True)

    # ==========================================
    # TAB 4: AREA, LAYANAN & PAYMENT
    # ==========================================
    with tab4:
        st.header("📍 Top Area, Layanan & Metode Pembayaran")
        
        a1, a2 = st.columns(2)
        with a1:
            st.subheader("📍 Top Area / Destinasi")
            top_area = df['Destination'].value_counts().head(10)
            st.bar_chart(top_area)
            st.dataframe(top_area.reset_index().rename(columns={'Destination':'Area', 'count':'Total Pengiriman'}), use_container_width=True)
            
        with a2:
            st.subheader("📦 Komposisi Layanan (Service)")
            top_serv = df['Services'].value_counts()
            st.bar_chart(top_serv)
            st.dataframe(top_serv.reset_index().rename(columns={'Services':'Jenis Layanan', 'count':'Total Dipakai'}), use_container_width=True)
            
            st.subheader("💳 Komposisi Pembayaran")
            top_pay = df['Payment type'].value_counts()
            st.bar_chart(top_pay)

    # ==========================================
    # TAB 5: RIWAYAT BULANAN
    # ==========================================
    with tab5:
        st.header("🗓️ Riwayat Bulanan (Snapshot)")
        st.markdown("Isi asli dari sheet **Riwayat Bulanan** lu. (Format tabel asli)")
        # Karena ini formatnya custom lu bikin sendiri pake judul di tengah-tengah, kita tampilin apa adanya tanpa kolom kosong
        df_riwayat_clean = df_riwayat.dropna(how='all').dropna(axis=1, how='all')
        st.dataframe(df_riwayat_clean, use_container_width=True)

except Exception as e:
    st.error(f"Waduh, ada error nih bro: {e}")
