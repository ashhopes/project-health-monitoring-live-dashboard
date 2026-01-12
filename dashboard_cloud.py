import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
from datetime import datetime
from google.cloud import bigquery
import os

# ============================================================================
# 1. SETUP & KONFIGURASI
# ============================================================================

# Tetapan Halaman (Mesti diletakkan paling atas)
st.set_page_config(
    page_title="STEMCUBE Health Dashboard",
    page_icon="🏥",
    layout="wide"
)

# Konfigurasi BigQuery (Pastikan ini sama dengan Apps Script anda)
PROJECT_ID = "monitoring-system-with-lora"
DATASET_ID = "realtime_health_monitoring_system_with_lora"
TABLE_ID = "lora_sensor_logs"

# CSS untuk cantikkan Dashboard
st.markdown("""
<style>
    .metric-card {
        background-color: #1E1E1E;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #333;
        text-align: center;
    }
    .metric-value {
        font-size: 2em;
        font-weight: bold;
        color: #00FF00;
    }
    .metric-label {
        color: #888;
        font-size: 0.9em;
    }
    h1, h2, h3 { color: #FAFAFA; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# 2. FUNGSI MENARIK DATA DARI CLOUD
# ============================================================================

def get_data_from_bigquery():
    """Menarik data terkini dari BigQuery"""
    try:
        # Jika run di Local (Laptop), pastikan fail key.json wujud
        # Jika run di Streamlit Cloud, ia guna 'secrets'
        if os.path.exists('key.json'):
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'key.json'
            
        client = bigquery.Client(project=PROJECT_ID)
        
        # Query: Ambil 100 data terkini
        query = f"""
            SELECT *
            FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
            ORDER BY timestamp DESC
            LIMIT 100
        """
        
        df = client.query(query).to_dataframe()
        return df
        
    except Exception as e:
        st.error(f"❌ Ralat BigQuery: {e}")
        return pd.DataFrame()

# ============================================================================
# 3. FUNGSI PEMBANTU (UTILITIES)
# ============================================================================

def check_bigquery_data():
    """Fungsi untuk semak status sambungan (Fix IndentationError)"""
    try:
        print("🔍 Checking BigQuery connection...")
        df = get_data_from_bigquery()
        if not df.empty:
            print(f"✅ Connection OK! Found {len(df)} rows.")
            print(df.head())
        else:
            print("⚠️ Connection OK but table is empty.")
    except Exception as e:
        print(f"❌ Connection Failed: {e}")

# ============================================================================
# 4. PAPARAN UTAMA DASHBOARD
# ============================================================================

def main():
    # Tajuk Dashboard
    st.title("🏥 Real-Time Health Monitoring System")
    st.caption(f"Connected to: {PROJECT_ID} | Table: {TABLE_ID}")

    # Container untuk Auto-Refresh
    placeholder = st.empty()

    # Loop untuk sentiasa kemaskini data
    while True:
        with placeholder.container():
            # 1. Tarik Data
            df = get_data_from_bigquery()

            if not df.empty:
                # Ambil data paling baru (baris pertama)
                latest = df.iloc[0]
                
                # --- BARIS 1: METRIK UTAMA ---
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Status Activity", latest.get('activity', 'N/A'))
                with col2:
                    st.metric("Heart Rate (BPM)", f"{latest.get('hr', 0):.0f}")
                with col3:
                    st.metric("SpO2 (%)", f"{latest.get('spo2', 0):.1f}%")
                with col4:
                    st.metric("Temperature (°C)", f"{latest.get('temp', 0):.1f}°C")

                # --- BARIS 2: CARTA GRAF ---
                col_left, col_right = st.columns(2)
                
                with col_left:
                    st.subheader("Graf Jantung & SpO2")
                    fig_hr = px.line(df, x='timestamp', y=['hr', 'spo2'], 
                                   title='Health Trends Over Time',
                                   markers=True)
                    st.plotly_chart(fig_hr, use_container_width=True)
                
                with col_right:
                    st.subheader("Graf Pergerakan (Accelerometer)")
                    # Pastikan kolum ax, ay, az wujud
                    if 'ax' in df.columns:
                        fig_acc = px.line(df, x='timestamp', y=['ax', 'ay', 'az'], 
                                        title='Motion Sensor Data')
                        st.plotly_chart(fig_acc, use_container_width=True)
                    else:
                        st.info("Tiada data accelerometer.")

                # --- BARIS 3: JADUAL DATA MENTAH ---
                with st.expander("Lihat Data Mentah (Raw Data)"):
                    st.dataframe(df)
                    
                # Papar masa kemaskini
                st.write(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")

            else:
                st.warning("Menunggu data masuk ke BigQuery... (Sila on-kan sensor)")
        
        # Tunggu 3 saat sebelum refresh semula
        time.sleep(3)

# ============================================================================
# 5. ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Dashboard stopped by user.")