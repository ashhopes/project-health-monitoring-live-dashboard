import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
import plotly.graph_objects as go
import time

# --- Page setup ---
st.set_page_config(page_title="Live Health Monitoring System with LoRa", layout="wide")

# --- Header ---
st.markdown("<h1 style='text-align: center; color: #2E86C1;'>🧠 Live Health Monitoring System with LoRa</h1>", unsafe_allow_html=True)
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
        df = df.sort_values("timestamp", ascending=False).reset_index(drop=True)

        # --- Tabs for organization ---
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📈 Health Trends", "🎢 Motion Trends", "🤖 Predictions"])

        # --- Tab 1: Overview ---
        with tab1:
            st.subheader("🗃️ Latest Sensor Data")
            st.dataframe(df, use_container_width=True)

            latest = df.iloc[0]
            col1, col2, col3 = st.columns(3)
            with col1:
                st.plotly_chart(go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=latest.get("temp") or 0,
                    title={'text': "Temperature (°C)"},
                    gauge={'axis': {'range': [20, 45]}}
                )), use_container_width=True)
            with col2:
                st.plotly_chart(go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=latest.get("hr") or 0,
                    title={'text': "Heart Rate (BPM)"},
                    gauge={'axis': {'range': [30, 180]}}
                )), use_container_width=True)
            with col3:
                st.plotly_chart(go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=latest.get("spo2") or 0,
                    title={'text': "SpO₂ (%)"},
                    gauge={'axis': {'range': [70, 100]}}
                )), use_container_width=True)

        # --- Tab 2: Health Trends ---
        with tab2:
            st.subheader("📈 Health Metrics (last samples)")
            trend_df = df.sort_values("timestamp", ascending=True).set_index("timestamp")
            trend_df.index = pd.to_datetime(trend_df.index, errors="coerce")

            fig = go.Figure()
            for col, color, label in [
                ("temp", "orange", "Temperature (°C)"),
                ("hr", "red", "Heart Rate (BPM)"),
                ("spo2", "green", "SpO₂ (%)")
            ]:
                if col in trend_df.columns:
                    fig.add_trace(go.Scatter(
                        x=trend_df.index, y=trend_df[col],
                        mode="lines+markers", name=label, line=dict(color=color)
                    ))
            fig.update_layout(
                title="Health Metrics Trends",
                xaxis_title="Timestamp",
                yaxis_title="Values",
                legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)

        # --- Tab 3: Motion Trends ---
        with tab3:
            st.subheader("🎢 Accelerometer & Gyroscope (last samples)")
            motion_fig = go.Figure()
            for col, color, label in [
                ("ax", "blue", "Accel X"),
                ("ay", "purple", "Accel Y"),
                ("az", "cyan", "Accel Z"),
                ("gx", "brown", "Gyro X"),
                ("gy", "magenta", "Gyro Y"),
                ("gz", "gray", "Gyro Z")
            ]:
                if col in trend_df.columns:
                    motion_fig.add_trace(go.Scatter(
                        x=trend_df.index, y=trend_df[col],
                        mode="lines+markers", name=label, line=dict(color=color)
                    ))
            motion_fig.update_layout(
                title="Motion Sensor Trends",
                xaxis_title="Timestamp",
                yaxis_title="Sensor Values",
                legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
                height=500
            )
            st.plotly_chart(motion_fig, use_container_width=True)

        # --- Tab 4: Predictions (BigQuery ML) ---
        with tab4:
            st.subheader("🤖 ML Predictions (Anomaly Detection)")
            pred_query = f"""
                SELECT
                  timestamp,
                  temp,
                  spo2,
                  hr,
                  ax, ay, az, gx, gy, gz,
                  predicted_cluster
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