import streamlit as st
import pandas as pd
import plotly.express as px

# Konfigurasi Halaman Dasar
st.set_page_config(page_title="Smart Grid NTL Dashboard", layout="wide")
st.title("⚡ Smart Grid: Non-Technical Loss (NTL) Analytics Dashboard")
st.markdown("Dashboard ini menyajikan *business insights* berdasarkan pemodelan Machine Learning (Isolation Forest) dan Graph Analytics (NetworkX).")

# 1. LOAD DATA & CLEANING
@st.cache_data
def load_data():
    df = pd.read_csv("dashboard_data.csv")
    # Konversi format waktu
    df['tstp'] = pd.to_datetime(df['tstp'])
    return df

df = load_data()

# 2. INSIGHT 1: ESTIMASI KEBOCORAN PENDAPATAN (REVENUE LOSS)
st.header("1. Estimasi Kerugian Bisnis & Metrik Anomali")

# Menghitung agregasi
total_samples = len(df)
anomalies_df = df[df['is_anomaly'] == 1]
total_anomalies = len(anomalies_df)
anomaly_rate = (total_anomalies / total_samples) * 100

# Asumsi Tarif Listrik di London (misal £0.20 per kWh)
kwh_lost = anomalies_df['energy_kwh'].sum()
est_revenue_loss = kwh_lost * 0.20 

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Sampel Data", f"{total_samples:,}")
col2.metric("Titik Terdeteksi Anomali", f"{total_anomalies:,}")
col3.metric("Tingkat Anomali (%)", f"{anomaly_rate:.1f} %")
col4.metric("Est. Kerugian (Asumsi £0.20/kWh)", f"£ {est_revenue_loss:,.2f}")

st.info("💡 **Business Insight:** Angka kerugian di atas mengkuantifikasi nilai risiko finansial akibat pencurian/kerusakan meteran, memberikan justifikasi ROI yang jelas bagi operasional tim audit lapangan.")

st.divider()

# 3. INSIGHT 2: PROFIL WAKTU TEMPORAL
st.header("2. Profil Waktu Terjadinya Penyimpangan Beban")
st.markdown("Visualisasi ini memetakan di jam berapa anomali kelistrikan paling sering terjadi, membantu operasional menjadwalkan inspeksi.")

# Agregasi jumlah anomali berdasarkan jam
anomaly_by_hour = anomalies_df.groupby('hour').size().reset_index(name='Jumlah Anomali')
fig_time = px.bar(anomaly_by_hour, x='hour', y='Jumlah Anomali', 
                  title='Distribusi Anomali Berdasarkan Jam (0 - 23)',
                  labels={'hour': 'Jam (Format 24 Jam)', 'Jumlah Anomali': 'Frekuensi Deteksi'},
                  color='Jumlah Anomali', color_continuous_scale='Reds')

# REVISI: Menggunakan width='stretch' sesuai panduan terbaru Streamlit
st.plotly_chart(fig_time, width='stretch')

st.divider()

# 4. INSIGHT 3: PRIORITAS AUDIT LAPANGAN (NETWORKX SPATIAL CLUSTER)
st.header("3. Prioritas Audit Spasial (Berdasarkan Topologi Jaringan)")
st.markdown("Tabel dan grafik ini **hanya** menampilkan meteran yang masuk ke dalam pemetaan sampel *NetworkX* (tidak bernilai NaN). Menghubungkan titik sentralitas tinggi dengan deteksi anomali untuk investigasi yang tertarget.")

# Filter Data yang memiliki nilai degree_centrality (Menjaga Integritas Data)
graph_df = df.dropna(subset=['degree_centrality']).copy()
anomalous_graph_nodes = graph_df[graph_df['is_anomaly'] == 1].sort_values(by='degree_centrality', ascending=False)

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Daftar Prioritas Investigasi Meteran")
    st.markdown("ID Meteran dengan nilai *Degree Centrality* tinggi berpotensi menjadi pusat pencurian terorganisir di klaster tersebut.")
    st.dataframe(anomalous_graph_nodes[['LCLid', 'tstp', 'energy_kwh', 'degree_centrality']], hide_index=True)

with col_b:
    st.subheader("Korelasi Sentralitas vs Konsumsi (Klaster Anomali)")
    fig_scatter = px.scatter(anomalous_graph_nodes, x='degree_centrality', y='energy_kwh', 
                             hover_data=['LCLid', 'tstp'],
                             color='energy_kwh', color_continuous_scale='Turbo',
                             title="Titik Audit Berisiko Tinggi")
    
    st.plotly_chart(fig_scatter, width='stretch')