import streamlit as st
import pandas as pd
from google.cloud import bigquery
import plotly.graph_objects as go
from datetime import datetime

# --- 1. CONFIGURATION ---
PROJECT_ID = "monitoring-system-with-lora"
DATASET_ID = "sdp2_live_monitoring_system"
TABLE_ID = "lora_health_data_clean2"
KEY_FILE = "key.json"

# --- 2. PAGE SETUP ---
st.set_page_config(
    page_title="Health & Movement Tracker",
    page_icon="🏃",
    layout="wide"
)

# --- 3. BIGQUERY CONNECTION ---
@st.cache_resource
def get_bq_client():
    try:
        return bigquery.Client.from_service_account_json(KEY_FILE)
    except Exception as e:
        st.error(f"❌ Connection Error: {e}")
        return None

client = get_bq_client()

# --- 4. DATA FETCHING ---
def load_data():
    if client is None: return pd.DataFrame()
    # Ambil 100 data terbaru dari database
    query = f"""
        SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}` 
        ORDER BY timestamp DESC LIMIT 100
    """
    try:
        return client.query(query).to_dataframe()
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

df = load_data()

# --- 5. MAIN DASHBOARD ---
st.title("🏥 Real-Time Health & Movement Dashboard")

if not df.empty:
    latest = df.iloc[0]
    
    # --- SECTION 1: ACTIVITY RECOGNITION (DARI MASTER) ---
    st.subheader("🏃 Current Activity Status")
    
    # Ambil data activity dari Master (Pastikan column name 'activity' sama dengan di BigQuery)
    current_activity = str(latest.get('activity', 'UNKNOWN')).upper()
    
    # Warna mengikut status
    bg_color = "#2ecc71" if current_activity == "RESTING" else "#f1c40f"
    if "FALL" in current_activity: bg_color = "#e74c3c"

    st.markdown(f"""
        <div style="background-color:{bg_color}; padding:25px; border-radius:15px; text-align:center; border: 2px solid rgba(0,0,0,0.1)">
            <h1 style="color:white; margin:0; font-size: 50px;">{current_activity}</h1>
            <p style="color:white; font-size: 18px;">Last Updated: {latest['timestamp'].strftime('%H:%M:%S')}</p>
        </div>
    """, unsafe_allow_html=True)

    # --- SECTION 2: MOVEMENT TRACKING (ACCELEROMETER) ---
    st.write("---")
    col_graph, col_stats = st.columns([3, 1])

    with col_graph:
        st.subheader("📉 Movement Analysis (Accelerometer)")
        fig_move = go.Figure()
        fig_move.add_trace(go.Scatter(x=df['timestamp'], y=df['ax'], name="AX (X-Axis)", line=dict(color='#e74c3c')))
        fig_move.add_trace(go.Scatter(x=df['timestamp'], y=df['ay'], name="AY (Y-Axis)", line=dict(color='#2ecc71')))
        fig_move.add_trace(go.Scatter(x=df['timestamp'], y=df['az'], name="AZ (Z-Axis)", line=dict(color='#3498db')))

        fig_move.update_layout(
            title=dict(text="G-Force Sensor Data", font=dict(size=14)),
            xaxis=dict(title=dict(text="Time")),
            yaxis=dict(title=dict(text="Acceleration (g)")),
            template="plotly_white",
            height=400,
            hovermode="x unified"
        )
        st.plotly_chart(fig_move, use_container_width=True)

    with col_stats:
        st.subheader("📍 Raw Motion")
        st.write(f"**AX:** `{latest['ax']}`")
        st.write(f"**AY:** `{latest['ay']}`")
        st.write(f"**AZ:** `{latest['az']}`")
        st.info("Data paksi digunakan oleh Master untuk mengenalpasti jatuh atau berjalan.")

    # --- SECTION 3: DATABASE LIST LOG ---
    st.write("---")
    st.subheader("📋 Full Database Log (Historical Records)")
    
    # Filter paparan log
    log_display = df[['timestamp', 'ID_user', 'activity', 'temp', 'hr', 'spo2', 'ax', 'ay', 'az', 'ir']]
    
    st.dataframe(
        log_display, 
        use_container_width=True,
        column_config={
            "timestamp": st.column_config.DatetimeColumn("Timestamp", format="D MMM, h:mm:ss a"),
            "activity": st.column_config.TextColumn("Activity Status"),
            "temp": "Temp (°C)",
            "hr": "HR (BPM)",
            "spo2": "SpO2 (%)"
        }
    )

    # Butang Download
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Database Log (CSV)",
        data=csv,
        file_name=f"health_log_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )

else:
    st.warning("⚠️ Menunggu data dari BigQuery... Sila pastikan Master Transmit dan Laptop Gateway sedang berjalan.")

# Auto-refresh Button
if st.sidebar.button('🔄 Refresh Dashboard'):
    st.rerun()