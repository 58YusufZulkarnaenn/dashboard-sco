import streamlit as st
import pandas as pd

# Setting tampilan web biar lebar dan profesional
st.set_page_config(page_title="Dashboard SCO", page_icon="📦", layout="wide")

st.title("📊 Aplikasi Monitor SCO (Versi Pro)")
st.markdown("Aplikasi internal untuk monitoring transaksi, performa tim, dan pelanggan.")
st.markdown("---")

@st.cache_data
def load_data():
    file_path = "REKAP DATA CASH MEI 2026.xlsx"
    df = pd.read_excel(file_path, sheet_name="Raw Data")
    return df

try:
    df = load_data()
    
    # BIKIN MENU TABS BIAR KAYAK SHEET EXCEL
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Dashboard Utama", "👨‍💼 Performa Tim SCO", "🏆 Top Customer", "💳 Layanan & Payment"])
    
    # --- ISI TAB 1: DASHBOARD ---
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

    # --- ISI TAB 2: PERFORMA SCO ---
    with tab2:
        st.header("Kinerja Masing-Masing Kasir (SCO)")
        # Ngitung total transaksi dan pendapatan per User ID
        rekap_user = df.groupby('User id').agg({'User id':'count', 'Amount':'sum'}).rename(columns={'User id':'Total Resi', 'Amount':'Pendapatan (Rp)'}).sort_values(by='Pendapatan (Rp)', ascending=False)
        
        # Bikin format Rupiah rapi di tabel
        rekap_user['Pendapatan (Rp)'] = rekap_user['Pendapatan (Rp)'].apply(lambda x: f"Rp {x:,.0f}".replace(",", "."))
        st.dataframe(rekap_user, use_container_width=True)

    # --- ISI TAB 3: TOP CUSTOMER ---
    with tab3:
        st.header("Daftar Shipper / Customer Paling Sultan")
        # Filter yang namanya ada (bukan strip atau kosong)
        df_cust = df[df['Shipper Name'] != '-']
        top_cust = df_cust.groupby('Shipper Name').agg({'Shipper Name':'count', 'Amount':'sum'}).rename(columns={'Shipper Name':'Jumlah Order', 'Amount':'Total Belanja (Rp)'}).sort_values(by='Total Belanja (Rp)', ascending=False).head(10)
        
        top_cust['Total Belanja (Rp)'] = top_cust['Total Belanja (Rp)'].apply(lambda x: f"Rp {x:,.0f}".replace(",", "."))
        st.dataframe(top_cust, use_container_width=True)

    # --- ISI TAB 4: PAYMENT & SERVICE ---
    with tab4:
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
