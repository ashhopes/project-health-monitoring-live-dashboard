import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from google.cloud import bigquery
from google.oauth2 import service_account
import os

# ============================================================================
# 1. SETUP & KONFIGURASI
# ============================================================================
st.set_page_config(
    page_title="Realtime Health Monitoring System with LoRa",
    page_icon="🏥",
    layout="wide"
)

PROJECT_ID = "monitoring-system-with-lora"
DATASET_ID = "realtime_health_monitoring_system_with_lora"
TABLE_ID = "lora_sensor_logs"

# ============================================================================
# 2. FUNGSI SAMBUNGAN BIGQUERY
# ============================================================================
def get_data_from_bigquery():
    try:
        credentials = None
        if os.path.exists('key.json'):
            credentials = service_account.Credentials.from_service_account_file('key.json')
        elif os.path.exists('service-account-key.json'):
            credentials = service_account.Credentials.from_service_account_file('service-account-key.json')

        client = bigquery.Client(credentials=credentials, project=PROJECT_ID)

        query = f"""
            SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
            ORDER BY timestamp DESC
            LIMIT 100
        """
        df = client.query(query).to_dataframe()

        # Tukar timestamp ke format datetime (jika perlu)
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', errors='coerce')

        return df

    except Exception as e:
        st.error(f"❌ Error BigQuery: {e}")
        return pd.DataFrame()

# ============================================================================
# 3. PAPARAN UTAMA
# ============================================================================
def main():
    st.title("🏥 Real-Time Health Monitoring")
    st.caption(f"Status: Connected to `{DATASET_ID}.{TABLE_ID}`")
    st.markdown("---")

    # Auto refresh setiap 5 saat
    st_autorefresh = st.experimental_rerun if hasattr(st, 'experimental_rerun') else None
    refresh_interval = st.experimental_data_editor if hasattr(st, 'experimental_data_editor') else None

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
            fig = px.line(df, x='timestamp', y=['hr', 'temp'], markers=True)
            st.plotly_chart(fig, use_container_width=True)

        with col_right:
            st.subheader("📊 Analisis Aktiviti")
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
        st.info("Sila jalankan 'cloud_upload_simple.py' untuk hantar data.")

    # Refresh setiap 5 saat (Streamlit Cloud friendly)
    st.experimental_rerun()

if __name__ == "__main__":
    main()