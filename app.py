import streamlit as st
import pandas as pd

st.set_page_config(page_title="Dashboard SCO", page_icon="📦", layout="wide")

st.title("📊 Aplikasi Monitor SCO")
st.markdown("Aplikasi internal untuk monitoring transaksi, performa tim, dan pelanggan.")
st.markdown("---")

@st.cache_data
def load_data():
    file_path = "REKAP DATA CASH MEI 2026.xlsx"
    # Kita baca dua sheet sekarang
    df_raw = pd.read_excel(file_path, sheet_name="Raw Data")
    df_rata_rata = pd.read_excel(file_path, sheet_name="Rata-Rata Hari Masuk")
    # Bersihkan nama kolom rata-rata kalau ada spasi/newline
    df_rata_rata.columns = df_rata_rata.columns.str.strip().str.replace('\n', '')
    return df_raw, df_rata_rata

try:
    df, df_rata2 = load_data()
    
    # 5 TABS SEKARANG!
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Dashboard Utama", "👨‍💼 Performa Total SCO", "⏱️ Produktivitas & Absensi", "🏆 Top Customer", "💳 Layanan & Payment"])
    
    # --- TAB 1: DASHBOARD ---
    with tab1:
        st.header("Ringkasan Bulan Ini")
        col1, col2, col3 = st.columns(3)
        col1.metric("📦 Total Transaksi", f"{len(df)} Resi")
        col2.metric("💰 Total Pendapatan", f"Rp {df['Amount'].sum():,.0f}".replace(",", "."))
        col3.metric("⚖️ Total Berat", f"{df['Weight'].sum():,.1f} Kg")
        
        st.markdown("<br>", unsafe_allow_html=True)
        kiri, kanan = st.columns(2)
        with kiri:
            st.subheader("Tren Transaksi Harian")
            df['Tanggal'] = pd.to_datetime(df['Date']).dt.date
            st.bar_chart(df.groupby('Tanggal').size())
        with kanan:
            st.subheader("Top 5 Area Pengiriman")
            st.bar_chart(df['Destination'].value_counts().head(5))

    # --- TAB 2: PERFORMA TOTAL SCO ---
    with tab2:
        st.header("Total Kinerja Kasir (SCO)")
        rekap_user = df.groupby('User id').agg({'User id':'count', 'Amount':'sum'}).rename(columns={'User id':'Total Resi', 'Amount':'Total Pendapatan (Rp)'}).sort_values(by='Total Pendapatan (Rp)', ascending=False)
        rekap_user['Total Pendapatan (Rp)'] = rekap_user['Total Pendapatan (Rp)'].apply(lambda x: f"Rp {x:,.0f}".replace(",", "."))
        st.dataframe(rekap_user, use_container_width=True)

    # --- TAB 3: PRODUKTIVITAS & ABSENSI (BARU!) ---
    with tab3:
        st.header("Rata-Rata Harian & Hari Masuk SCO")
        st.markdown("Diambil dari sheet: **Rata-Rata Hari Masuk**")
        
        # Bikin rapi tabelnya
        df_display = df_rata2.copy()
        
        # Pastiin kolomnya bener (handling beda penamaan)
        revenue_col = 'Revenue' if 'Revenue' in df_display.columns else 'Total_Pendapatan'
        resi_col = 'Total_Connote' if 'Total_Connote' in df_display.columns else 'Total_Transaksi'
        
        if revenue_col in df_display.columns:
            df_display[revenue_col] = pd.to_numeric(df_display[revenue_col], errors='coerce').fillna(0)
            df_display[revenue_col] = df_display[revenue_col].apply(lambda x: f"Rp {x:,.0f}".replace(",", "."))
            
        if 'Rata_Pendapatan_Per_Hari' in df_display.columns:
            df_display['Rata_Pendapatan_Per_Hari'] = pd.to_numeric(df_display['Rata_Pendapatan_Per_Hari'], errors='coerce').fillna(0)
            df_display['Rata_Pendapatan_Per_Hari'] = df_display['Rata_Pendapatan_Per_Hari'].apply(lambda x: f"Rp {x:,.0f}".replace(",", "."))
            
        if 'Rata_Transaksi_Per_Hari' in df_display.columns:
            df_display['Rata_Transaksi_Per_Hari'] = pd.to_numeric(df_display['Rata_Transaksi_Per_Hari'], errors='coerce').fillna(0)
            df_display['Rata_Transaksi_Per_Hari'] = df_display['Rata_Transaksi_Per_Hari'].round(1)

        st.dataframe(df_display, use_container_width=True)

    # --- TAB 4: TOP CUSTOMER ---
    with tab4:
        st.header("Daftar Shipper / Customer Paling Sultan")
        df_cust = df[df['Shipper Name'] != '-']
        top_cust = df_cust.groupby('Shipper Name').agg({'Shipper Name':'count', 'Amount':'sum'}).rename(columns={'Shipper Name':'Jumlah Order', 'Amount':'Total Belanja (Rp)'}).sort_values(by='Total Belanja (Rp)', ascending=False).head(10)
        top_cust['Total Belanja (Rp)'] = top_cust['Total Belanja (Rp)'].apply(lambda x: f"Rp {x:,.0f}".replace(",", "."))
        st.dataframe(top_cust, use_container_width=True)

    # --- TAB 5: PAYMENT & SERVICE ---
    with tab5:
        st.header("Analisis Pembayaran & Layanan")
        k1, k2 = st.columns(2)
        with k1:
            st.subheader("Metode Pembayaran")
            pay = df.groupby('Payment type').size()
            st.bar_chart(pay)
        with k2:
            st.subheader("Layanan yang Paling Laku")
            serv = df.groupby('Services').size()
            st.bar_chart(serv)

except Exception as e:
    st.error(f"Error bro: {e}")
