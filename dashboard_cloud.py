@ -4,25 +4,31 @@ from google.cloud import bigquery
from google.oauth2 import service_account
import plotly.graph_objects as go

import streamlit as st
# --- Page setup ---
st.set_page_config(page_title="Health Monitoring Dashboard", layout="wide")

# --- Secrets Test ---
st.title("Secrets Test")

# Show project_id from secrets
try:
    st.write("Project ID:", st.secrets["gcp"]["project_id"])
    st.write("Client Email:", st.secrets["gcp"]["client_email"])
    st.success("✅ Secrets loaded successfully!")
except Exception as e:
    st.error(f"Secrets error: {e}")
# --- Page setup ---
st.set_page_config(page_title="Health Monitoring Dashboard", layout="wide")

# --- Dashboard Title ---
st.title("🧠 Health Monitoring System with LoRa")

# --- BigQuery Authentication ---
credentials = service_account.Credentials.from_service_account_info(st.secrets["gcp"])
client = bigquery.Client(credentials=credentials, project=st.secrets["gcp"]["project_id"])
table_id = "monitoring-system-with-lora.sdp2_live_monitoring.lora_health_data_clean2"
client = bigquery.Client(
    credentials=credentials,
    project=st.secrets["gcp"]["project_id"],
    location="asia-southeast1"   # ✅ Malaysia/Singapore region
)

# --- Table reference ---
table_id = "monitoring-system-with-lora.sdp2_live_monitoring_system.lora_health_data_clean2"

# --- Fetch latest data ---
@st.cache_data(ttl=30)
@ -35,41 +41,44 @@ try:
    if df.empty:
        st.info("No data found yet. Upload from your local app first.")
    else:
        # Ensure newest rows are at the top
        df = df.sort_values("timestamp", ascending=False).reset_index(drop=True)

        # Show table
        st.subheader("🗃️ Latest sensor data")
        st.subheader("🗃️ Latest sensor data (newest first)")
        st.dataframe(df, use_container_width=True)

        # Gauges (last row)
        last = df.iloc[-1]
        # Gauges (use the first row since it's the newest)
        latest = df.iloc[0]
        col1, col2, col3 = st.columns(3)
        with col1:
            st.plotly_chart(go.Figure(go.Indicator(
                mode="gauge+number",
                value=last.get("temp") or 0,
                value=latest.get("temp") or 0,
                title={'text': "Temperature (°C)"},
                gauge={'axis': {'range': [20, 45]}}
            )), use_container_width=True)
        with col2:
            st.plotly_chart(go.Figure(go.Indicator(
                mode="gauge+number",
                value=last.get("hr") or 0,
                value=latest.get("hr") or 0,
                title={'text': "Heart Rate (BPM)"},
                gauge={'axis': {'range': [30, 180]}}
            )), use_container_width=True)
        with col3:
            st.plotly_chart(go.Figure(go.Indicator(
                mode="gauge+number",
                value=last.get("spo2") or 0,
                value=latest.get("spo2") or 0,
                title={'text': "SpO₂ (%)"},
                gauge={'axis': {'range': [70, 100]}}
            )), use_container_width=True)

        # Trend chart
        # Trend chart (chronological order for time series)
        st.subheader("📈 Trends (last 100 samples)")
        trend_df = df.tail(100).set_index("timestamp")
        trend_df = df.sort_values("timestamp", ascending=True).set_index("timestamp")
        try:
            trend_df.index = pd.to_datetime(trend_df.index)
        except:
        except Exception:
            pass

        fig = go.Figure()
