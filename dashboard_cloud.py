import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
import plotly.graph_objects as go

# --- Page setup ---
st.set_page_config(page_title="Health Monitoring Dashboard", layout="wide")

# --- Secrets Test ---
st.title("Secrets Test")
try:
    st.write("Project ID:", st.secrets["gcp"]["project_id"])
    st.write("Client Email:", st.secrets["gcp"]["client_email"])
    st.success("✅ Secrets loaded successfully!")
except Exception as e:
    st.error(f"Secrets error: {e}")

# --- Dashboard Title ---
st.title("🧠 Health Monitoring System with LoRa")

# --- BigQuery Authentication ---
credentials = service_account.Credentials.from_service_account_info(st.secrets["gcp"])
client = bigquery.Client(
    credentials=credentials,
    project=st.secrets["gcp"]["project_id"],
    location="asia-southeast1"   # ✅ Malaysia/Singapore region
)

# --- Table reference ---
table_id = "monitoring-system-with-lora.sdp2_live_monitoring_system.lora_health_data_clean2"

# --- Fetch latest data ---
@st.cache_data(ttl=30)
def fetch_latest(n=100):
    query = f"SELECT * FROM `{table_id}` ORDER BY timestamp DESC LIMIT {n}"
    return client.query(query).to_dataframe()

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

        # Gauges (use the first row since it's the newest)
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

        # Trend chart (chronological order for time series)
        st.subheader("📈 Trends (last 100 samples)")
        trend_df = df.sort_values("timestamp", ascending=True).set_index("timestamp")
        try:
            trend_df.index = pd.to_datetime(trend_df.index)
        except Exception:
            pass

        fig = go.Figure()
        for col, color, label in [
            ("temp", "orange", "Temperature (°C)"),
            ("hum", "blue", "Humidity (%)"),
            ("hr", "red", "Heart Rate (BPM)"),
            ("spo2", "green", "SpO₂ (%)")
        ]:
            if col in trend_df.columns:
                fig.add_trace(go.Scatter(
                    x=trend_df.index, y=trend_df[col],
                    mode="lines+markers", name=label, line=dict(color=color)
                ))
        fig.update_layout(
            title="Sensor Trends (last 100 samples)",
            xaxis_title="Timestamp",
            yaxis_title="Values",
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"BigQuery error: {e}")