import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
import plotly.graph_objects as go
import time

# --- Page setup ---
st.set_page_config(page_title="Live Health Monitoring System with LoRa", layout="wide")

# --- Custom Elegant Theme (Maroon + Beige + Gold) ---
st.markdown(
    """
    <style>
    .stApp {
        background-color: #fdf6ec; /* beige hangat */
    }
    .stSidebar {
        background-color: #f7ede2; /* sidebar beige terang */
    }
    h1, h2, h3 {
        color: #800000; /* maroon */
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 600;
    }
    .stDataFrame {
        background-color: #ffffff;
        border-radius: 8px;
        padding: 10px;
        border: 1px solid #bfa76f; /* gold accent */
    }
    .css-1d391kg, .css-1v3fvcr {
        color: #2e2e2e; /* neutral text */
    }
    .stMarkdown hr {
        border-top: 1px solid #bfa76f; /* gold divider */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Header ---
st.markdown("<h1 style='text-align: center;'>🧠 Live Health Monitoring System with LoRa</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Real-time monitoring of vital signs and motion data using LoRa sensors</p>", unsafe_allow_html=True)
st.markdown("---")

# --- Sidebar controls ---
st.sidebar.header("⚙️ Controls")
refresh_rate = st.sidebar.slider("Auto-refresh every (seconds)", 0, 120, 30)
n_samples = st.sidebar.slider("Number of samples to display", 50, 500, 100)
st.sidebar.info("Project by mOONbLOOM26 🌙")

if refresh_rate > 0:
    time.sleep(refresh_rate)

# --- BigQuery Authentication ---
credentials = service_account.Credentials.from_service_account_info(st.secrets["gcp"])
client = bigquery.Client(
    credentials=credentials,
    project=st.secrets["gcp"]["project_id"],
    location="asia-southeast1"
)

# --- Table reference ---
table_id = "monitoring-system-with-lora.sdp2_live_monitoring_system.lora_health_data_clean2"

# --- Fetch latest data ---
@st.cache_data(ttl=30)
def fetch_latest(n=100):
    query = f"""
        SELECT id_user, timestamp, temp, spo2, hr, ax, ay, az, gx, gy, gz
        FROM `{table_id}`
        ORDER BY timestamp DESC
        LIMIT {n}
    """
    return client.query(query).to_dataframe()

try:
    df = fetch_latest(n_samples)
    if df.empty:
        st.info("No data found yet. Upload from your local app first.")
    else:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors="coerce")
        trend_df = df.sort_values("timestamp", ascending=True).set_index("timestamp")

        # --- Section 1: Live Sensor Data ---
        st.subheader("📈 Section 1: Live Sensor Data")
        fig = go.Figure()
        for col, color, label in [
            ("temp", "#d35400", "Temperature (°C)"),
            ("hr", "#c0392b", "Heart Rate (BPM)"),
            ("spo2", "#27ae60", "SpO₂ (%)")
        ]:
            if col in trend_df.columns:
                fig.add_trace(go.Scatter(
                    x=trend_df.index, y=trend_df[col],
                    mode="lines+markers", name=label, line=dict(color=color)
                ))
        fig.update_layout(
            title="Live Health Metrics",
            xaxis_title="Time",
            yaxis_title="Values",
            plot_bgcolor="#fdf6ec",
            paper_bgcolor="#fdf6ec"
        )
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("🗃️ Show Latest 100 Sensor Data"):
            st.dataframe(df, use_container_width=True)

        # --- Section 2: Subject/Testor Info ---
        st.subheader("👤 Section 2: Subject / Testor Info")
        subject_data = pd.DataFrame({
            "Master ID": ["Master1", "Master2", "Master3", "Master4"],
            "Slave Target": ["SlaveA", "SlaveB", "SlaveC", "SlaveD"],
            "Status": ["Active", "Active", "Idle", "Active"]
        })
        with st.expander("📋 Show Subject Table"):
            st.dataframe(subject_data, use_container_width=True)

        # --- Section 3: ML Predictions ---
        st.subheader("🤖 Section 3: ML Predictions (Anomaly Detection)")
        pred_query = f"""
            SELECT timestamp, id_user, temp, spo2, hr, ax, ay, az, gx, gy, gz, predicted_cluster
            FROM ML.PREDICT(MODEL `monitoring-system-with-lora.sdp2_live_monitoring_system.anomaly_model`,
            (
              SELECT temp, spo2, hr, ax, ay, az, gx, gy, gz, timestamp, id_user
              FROM `{table_id}`
              ORDER BY timestamp DESC
              LIMIT 100
            ))
        """
        pred_df = client.query(pred_query).to_dataframe()

        for subject in pred_df['id_user'].unique():
            st.markdown(f"**🔍 Predictions for Subject: {subject}**")
            sub_df = pred_df[pred_df['id_user'] == subject]
            st.dataframe(sub_df, use_container_width=True)
            st.bar_chart(sub_df.groupby("predicted_cluster").size())

except Exception as e:
    st.error(f"BigQuery error: {e}")