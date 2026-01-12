import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pytz

# --- Configuration ---
PROJECT_ID = "monitoring-system-with-lora"
DATASET_ID = "sdp2_live_monitoring_system"
TABLE_ID = "lora_health_data_clean2"

# --- Page Setup ---
st.set_page_config(
    page_title="Live Health Monitoring System",
    layout="wide"
)

# --- BigQuery Connection ---
@st.cache_resource
def get_bq_client():
    try:
        # Pastikan fail key.json ada dalam folder yang sama
        return bigquery.Client.from_service_account_json("key.json")
    except Exception as e:
        st.error(f"Gagal menyambung ke BigQuery: {e}")
        return None

client = get_bq_client()

# --- Sidebar Filters ---
st.sidebar.header("📊 Dashboard Filters")
hours_filter = st.sidebar.slider("Pilih Julat Masa (Jam):", 1, 24, 6)

# --- Data Fetching ---
def load_data():
    if client is None: return pd.DataFrame()
    
    query = f"""
        SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {hours_filter} HOUR)
        ORDER BY timestamp DESC
    """
    return client.query(query).to_dataframe()

df = load_data()

# --- Main Dashboard ---
st.title("🏥 Sistem Pemantauan Kesihatan LoRa (Live)")

if not df.empty:
    # 1. Metrics Row
    latest = df.iloc[0]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Suhu", f"{latest['temp']}°C")
    col2.metric("SpO2", f"{latest['spo2']}%")
    col3.metric("Kadar Jantung", f"{latest['hr']} BPM")
    col4.metric("Kelembapan", f"{latest['humidity']}%")

    # 2. Vital Signs Chart (PUNCA ERROR SEBELUM INI)
    st.subheader("📈 Trend Tanda Vital")
    
    fig = go.Figure()

    # Heart Rate Trace
    fig.add_trace(go.Scatter(
        x=df['timestamp'], y=df['hr'],
        name="Heart Rate", line=dict(color='#c0392b')
    ))

    # SpO2 Trace
    fig.add_trace(go.Scatter(
        x=df['timestamp'], y=df['spo2'],
        name="SpO2", yaxis="y2", line=dict(color='#27ae60')
    ))

    # --- PEMBETULAN STRUKTUR LAYOUT (HILANGKAN ERROR titlefont) ---
    fig.update_layout(
        xaxis=dict(title=dict(text="Masa", font=dict(size=14))),
        yaxis=dict(
            title=dict(
                text="Heart Rate (BPM)",
                font=dict(color="#c0392b", size=14) # Cara betul akses font
            ),
            tickfont=dict(color="#c0392b")
        ),
        yaxis2=dict(
            title=dict(
                text="SpO2 (%)",
                font=dict(color="#27ae60", size=14) # Cara betul akses font
            ),
            tickfont=dict(color="#27ae60"),
            overlaying='y',
            side='right'
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        height=500
    )

    st.plotly_chart(fig, use_container_width=True)

    # 3. Data Table
    st.subheader("📋 Rekod Data Terkini")
    st.dataframe(df.head(20), use_container_width=True)

else:
    st.warning("⚠️ Tiada data ditemui untuk julat masa ini. Pastikan gateway laptop sedang berjalan.")

# --- Auto Refresh ---
st.empty()
if st.sidebar.button('🔄 Refresh Manual'):
    st.rerun()