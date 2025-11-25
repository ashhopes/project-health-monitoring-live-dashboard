import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
import plotly.graph_objects as go
import time

# --- Page setup ---
st.set_page_config(page_title="Live Health Monitoring System with LoRa", layout="wide")

# --- Custom Muji Style (Maroon + Beige) ---
st.markdown(
    """
    <style>
    .stApp {
        background-color: #f9f5f0; /* beige background */
    }
    .stSidebar {
        background-color: #f2e9e4; /* lighter beige for sidebar */
    }
    h1, h2, h3 {
        color: #800000; /* maroon headings */
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 600;
    }
    .stDataFrame {
        background-color: #ffffff;
        border-radius: 8px;
        padding: 10px;
    }
    .css-1d391kg, .css-1v3fvcr {
        color: #333333; /* neutral text */
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

# --- BigQuery Authentication (using secrets.toml) ---
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
        # --- Tabs untuk 3 layout ---
        tab1, tab2, tab3 = st.tabs(["📈 Live Data", "👤 Subject/Testor", "🤖 Predictions"])

        # --- Layout 1: Live Data ---
        with tab1:
            st.subheader("📈 Sensor Trends (Line Chart)")
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors="coerce")
            trend_df = df.sort_values("timestamp", ascending=True).set_index("timestamp")

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
                plot_bgcolor="#f9f5f0",
                paper_bgcolor="#f9f5f0"
            )
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("🗃️ Latest Sensor Data")
            st.dataframe(df, use_container_width=True)

        # --- Layout 2: Subject/Testor ---
        with tab2:
            st.subheader("👤 Subject / Testor Information")
            st.write("This section displays details about the test subjects being monitored.")
            subject_data = pd.DataFrame({
                "Master ID": ["Master1", "Master2", "Master3", "Master4"],
                "Slave Target": ["SlaveA", "SlaveB", "SlaveC", "SlaveD"],
                "Status": ["Active", "Active", "Idle", "Active"]
            })
            st.dataframe(subject_data, use_container_width=True)

        # --- Layout 3: Predictions ---
        with tab3:
            st.subheader("🤖 ML Predictions (Anomaly Detection)")
            pred_query = f"""
                SELECT timestamp, temp, spo2, hr, ax, ay, az, gx, gy, gz, predicted_cluster
                FROM ML.PREDICT(MODEL `monitoring-system-with-lora.sdp2_live_monitoring_system.anomaly_model`,
                (
                  SELECT temp, spo2, hr, ax, ay, az, gx, gy, gz, timestamp
                  FROM `{table_id}`
                  ORDER BY timestamp DESC
                  LIMIT 50
                ))
            """
            pred_df = client.query(pred_query).to_dataframe()
            st.dataframe(pred_df, use_container_width=True)
            st.markdown("Cluster meaning: One cluster = normal, other cluster = potential anomaly.")
            st.bar_chart(pred_df.groupby("predicted_cluster").size())

except Exception as e:
    st.error(f"BigQuery error: {e}")