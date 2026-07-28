import streamlit as st
import pandas as pd

# Setting tampilan web biar lebar dan profesional
st.set_page_config(page_title="Dashboard SCO", page_icon="📦", layout="wide")

st.title("📊 Dashboard Performa Pengiriman SCO")
st.markdown("Aplikasi internal untuk monitoring transaksi dan pendapatan.")
st.markdown("---")

# Fungsi untuk baca file Excel lu yang baru
@st.cache_data
def load_data():
    # NAMA FILE UDAH GUA GANTI SESUAI YANG BARU YAH BRO
    file_path = "REKAP DATA CASH MEI 2026.xlsx"
    df = pd.read_excel(file_path, sheet_name="Raw Data")
    return df

try:
    df = load_data()
    
    # Hitung metrik buat Dashboard atas
    total_transaksi = len(df)
    total_pendapatan = df["Amount"].sum()
    total_berat = df["Weight"].sum()
    
    # Bikin 3 Kotak Metrik yang rapi
    col1, col2, col3 = st.columns(3)
    col1.metric("📦 Total Transaksi", f"{total_transaksi} Resi")
    
    rupiah = f"Rp {total_pendapatan:,.0f}".replace(",", ".")
    col2.metric("💰 Total Pendapatan", rupiah)
    
    col3.metric("⚖️ Total Berat", f"{total_berat} Kg")
    
    st.markdown("---")
    
    # Bikin kolom kiri-kanan buat layout grafik
    kiri, kanan = st.columns(2)
    
    with kiri:
        st.subheader("📈 Tren Transaksi Harian")
        # Ekstrak tanggal biar grafiknya rapi
        df['Tanggal'] = pd.to_datetime(df['Date']).dt.date
        harian = df.groupby('Tanggal').size().reset_index(name='Transaksi')
        st.bar_chart(harian.set_index('Tanggal'))
        
    with kanan:
        st.subheader("🏆 Area Pengiriman Terbanyak")
        area = df['Destination'].value_counts().head(5)
        st.bar_chart(area)

    st.markdown("---")
    st.subheader("📋 10 Transaksi Terbaru")
    # Tampilin tabel data mentah tapi rapi
    st.dataframe(df[['User id', 'Date', 'Services', 'Destination', 'Amount']].tail(10), use_container_width=True)

except Exception as e:
    st.error(f"Waduh, ada error nih bro: {e}. Pastiin nama file Excel-nya bener-bener sama persis huruf besar kecilnya!")
