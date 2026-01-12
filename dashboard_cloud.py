import streamlit as st
import pandas as pd
import plotly.express as px
import time
from datetime import datetime
from google.cloud import bigquery
from google.oauth2 import service_account
import os

# ============================================================================
# 1. SETUP & KONFIGURASI (KEMASKINI TERBARU)
# ============================================================================

st.set_page_config(
    page_title="STEMCUBE Health Dashboard",
    page_icon="🏥",
    layout="wide"
)

# 👇 INI BAHAGIAN PENTING YANG TELAH DIKEMASKINI 👇
PROJECT_ID = "monitoring-system-with-lora"
DATASET_ID = "realtime_health_monitoring_system_with_lora"
TABLE_ID = "lora_sensor_logs" 

# Nota: Pastikan ejaan 'sensors' (ada 's') atau 'sensor' (tiada 's')
# sama sebiji dengan nama dalam BigQuery Console anda.

# ============================================================================
# 2. FUNGSI SAMBUNGAN BIGQUERY
# ============================================================================

def get_data_from_bigquery():
    """Menarik data dari BigQuery menggunakan key.json"""
    try:
        # 1. Cuba cari fail key.json (utk Local Run)
        credentials = None
        if os.path.exists('key.json'):
            credentials = service_account.Credentials.from_service_account_file('key.json')
        elif os.path.exists('service-account-key.json'):
            credentials = service_account.Credentials.from_service_account_file('service-account-key.json')
            
        # 2. Bina Client
        # Jika tiada key.json, ia akan cuba guna st.secrets (utk Cloud Run)
        client = bigquery.Client(credentials=credentials, project=PROJECT_ID)
        
        # 3. SQL Query
        query = f"""
            SELECT *
            FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
            ORDER BY timestamp DESC
            LIMIT 100
        """
        
        # 4. Tarik Data
        df = client.query(query).to_dataframe()
        return df
        
    except Exception as e:
        # Jangan crash, cuma print error di terminal
        print(f"❌ Error BigQuery: {e}")
        return pd.DataFrame()

# ============================================================================
# 3. PAPARAN UTAMA DASHBOARD
# ============================================================================

def main():
    # Header
    st.title("🏥 Real-Time Health Monitoring")
    st.caption(f"Status: Connected to `{DATASET_ID}.{TABLE_ID}`")
    st.markdown("---")

    # Ruang kosong untuk auto-refresh
    placeholder = st.empty()

    while True:
        with placeholder.container():
            # A. Tarik Data Baru
            df = get_data_from_bigquery()

            if not df.empty:
                # Ambil data paling terkini (baris pertama)
                latest = df.iloc[0]
                
                # B. Papar Metrik (Kotak-kotak Data)
                col1, col2, col3, col4 = st.columns(4)
                
                # Guna .get() supaya tak error kalau kolum hilang
                col1.metric("User ID", str(latest.get('ID_user', 'N/A')))
                col2.metric("Activity", str(latest.get('activity', '-')))
                
                # Format nombor perpuluhan
                hr = latest.get('hr', 0)
                temp = latest.get('temp', 0)
                spo2 = latest.get('spo2', 0)
                
                col3.metric("Heart Rate", f"{hr} BPM")
                col4.metric("Temperature", f"{temp} °C")

                # C. Papar Graf
                col_left, col_right = st.columns(2)
                
                with col_left:
                    st.subheader("📈 Jantung & Suhu")
                    if 'timestamp' in df.columns:
                        # Graf Garisan
                        fig = px.line(df, x='timestamp', y=['hr', 'temp'], markers=True)
                        st.plotly_chart(fig, use_container_width=True)
                
                with col_right:
                    st.subheader("📊 Analisis Aktiviti")
                    if 'activity' in df.columns:
                        # Carta Pie
                        act_counts = df['activity'].value_counts().reset_index()
                        act_counts.columns = ['activity', 'count']
                        fig_pie = px.pie(act_counts, values='count', names='activity')
                        st.plotly_chart(fig_pie, use_container_width=True)

                # D. Papar Jadual Penuh
                with st.expander("Lihat Data Penuh (Table View)"):
                    st.dataframe(df)
                    
                st.success(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")

            else:
                # Paparan jika data KOSONG atau ERROR
                st.warning(f"⚠️ Data tidak dijumpai dalam `{TABLE_ID}`.")
                st.error(f"""
                Kemungkinan punca:
                1. Ejaan Table ID salah? (Anda tulis: {TABLE_ID})
                2. Dataset ID salah? (Anda tulis: {DATASET_ID})
                3. Belum jalankan `cloud_upload_simple.py`?
                """)
                
                # Butang Retry Manual
                if st.button("Cuba Refresh Sekarang"):
                    st.rerun()
        
        # Tunggu 3 saat sebelum ulang
        time.sleep(3)

if __name__ == "__main__":
    main()