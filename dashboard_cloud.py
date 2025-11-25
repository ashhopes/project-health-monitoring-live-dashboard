import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
import plotly.graph_objects as go
import os
import time

# --- Page setup ---
st.set_page_config(page_title="Health Monitoring Dashboard", layout="wide")
st.title("🧠 Health Monitoring System with LoRa")

# --- Unified BigQuery Authentication ---
def get_bigquery_client():
    if "gcp" in st.secrets:  # Cloud mode
        credentials = service_account.Credentials.from_service_account_info(st.secrets["gcp"])
        project_id = st.secrets["gcp"]["project_id"]
        return bigquery.Client(credentials=credentials, project=project_id, location="asia-southeast1")
    elif os.path.exists("monitoring-system-with-lora.json"):  # Local mode
        credentials = service_account.Credentials.from_service_account_file("monitoring-system-with-lora.json")
        return bigquery.Client(credentials=credentials, project="monitoring-system-with-lora", location="asia-southeast1")
    else:
        raise RuntimeError("❌ No credentials found. Please set Streamlit secrets or provide JSON file.")

client = get_bigquery_client()

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

# --- Auto-refresh toggle ---
refresh_rate = st.sidebar.slider("⏱️ Auto-refresh every (seconds)", 0, 120, 30)
if refresh_rate > 0:
    time.sleep(refresh_rate)

try:
    df = fetch_latest()
    if df.empty:
        st.info("No data found yet. Upload from your local app first.")
    else:
        # Ensure newest rows are at the top
        df = df.sort_values("timestamp", ascending=False).reset_index(drop=True)

        # Show table
        st.subheader("🗃️ Latest sensor data (newest first)")
        st.dataframe(df, use_container_width=True)

        # Gauges (newest row)
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

        # Trend chart (health metrics)
        st.subheader("📈 Health Trends (last 100 samples)")
        trend_df = df.sort_values("timestamp", ascending=True).set_index("timestamp")
        try:
            trend_df.index = pd.to_datetime(trend_df.index)
        except Exception:
            pass

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

        # Motion charts (accelerometer + gyroscope)
        st.subheader("🎢 Motion Data Trends (last 100 samples)")

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
            title="Accelerometer & Gyroscope Trends",
            xaxis_title="Timestamp",
            yaxis_title="Sensor Values",
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
            height=500
        )
        st.plotly_chart(motion_fig, use_container_width=True)

except Exception as e:
    st.error(f"BigQuery error: {e}")