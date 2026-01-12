import streamlit as st
import pandas as pd
import plotly.express as px
import time
from datetime import datetime
from google.cloud import bigquery
from google.oauth2 import service_account
import os

# ============================================================================
# 1. SETUP & KONFIGURASI
# ============================================================================

st.set_page_config(
    page_title="STEMCUBE Health Dashboard",
    page_icon="🏥",
    layout="wide"
)

# 👇 SETTING BIGQUERY (Pastikan sama dengan Uploader!)
PROJECT_ID = "monitoring-system-with-lora"
DATASET_ID = "realtime_health_monitoring_system_with_lora"
TABLE_ID = "lora_sensors_logs"  # <-- Table Baru Anda

# ============================================================================
# 2. FUNGSI SAMBUNGAN BIGQUERY
# ============================================================================

def get_data_from_bigquery():
    """Menarik data dari BigQuery"""
    try:
        # Cuba cari fail key.json (utk Local Run)
        credentials = None
        if os.path.exists('key.json'):
            credentials = service_account.Credentials.from_service_account_file('key.json')
        elif os.path.exists('service-account-key.json'):
            credentials = service_account.Credentials.from_service_account_file('service-account-key.json')
        
        # Jika tiada key file, ia akan cuba guna 'st.secrets' (Streamlit Cloud)
        client = bigquery.Client(credentials=credentials, project=PROJECT_ID)
        
        # SQL Query
        query = f"""
            SELECT *
            FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
            ORDER BY timestamp DESC
            LIMIT 100
        """
        
        df = client.query(query).to_dataframe()
        return df
        
    except Exception as e:
        print(f"❌ Error BigQuery: {e}")
        return pd.DataFrame()

# ============================================================================
# 3. PAPARAN UTAMA
# ============================================================================

def main():
    st.title("🏥 Real-Time Health Monitoring")
    st.caption(f"Status: Connected to `{DATASET_ID}.{TABLE_ID}`")
    st.markdown("---")

    placeholder = st.empty()

    while True:
        with placeholder.container():
            df = get_data_from_bigquery()

            if not df.empty:
                latest = df.iloc[0]
                
                # --- A. KAD METRIK ---
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("User ID", str(latest.get('ID_user', 'N/A')))
                col2.metric("Activity", str(latest.get('activity', '-')))
                col3.metric("Heart Rate", f"{latest.get('hr', 0)} BPM")
                col4.metric("Temperature", f"{latest.get('temp', 0)} °C")

                # --- B. GRAF ---
                col_left, col_right = st.columns(2)
                
                with col_left:
                    st.subheader("📈 Jantung & Suhu")
                    if 'timestamp' in df.columns:
                        fig = px.line(df, x='timestamp', y=['hr', 'temp'], markers=True)
                        st.plotly_chart(fig, use_container_width=True)
                
                with col_right:
                    st.subheader("📊 Analisis Aktiviti")
                    if 'activity' in df.columns:
                        act_counts = df['activity'].value_counts().reset_index()
                        act_counts.columns = ['activity', 'count']
                        fig_pie = px.pie(act_counts, values='count', names='activity')
                        st.plotly_chart(fig_pie, use_container_width=True)

                # --- C. DATA VIEW ---
                with st.expander("Lihat Data Penuh"):
                    st.dataframe(df)
                    
                st.success(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")

            else:
                st.warning(f"⚠️ Tiada data dijumpai dalam `{TABLE_ID}`.")
                st.info("Sila jalankan 'cloud_upload_simple.py' di terminal sebelah untuk hantar data.")
                
        time.sleep(3)

if __name__ == "__main__":
    main()