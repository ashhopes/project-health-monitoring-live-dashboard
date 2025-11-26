import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time

# --- Page setup ---
st.set_page_config(page_title="Live Sensor Monitoring System with LoRa", layout="wide")

# --- Custom Theme ---
st.markdown("""
<style>
.stApp { background-color: #fdf6ec; }
.section {
    background: #fff; padding: 20px; margin-bottom: 20px;
    border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1);
}
.subject-box {
    background-color: #ffffff; border: 2px solid #800000;
    border-radius: 10px; padding: 15px; margin-bottom: 25px;
}
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown("<h1 style='text-align: center;'>📡 Live Sensor Monitoring System with LoRa</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Real-time monitoring of motion and gas sensors using LoRa</p>", unsafe_allow_html=True)
st.markdown("---")

# --- Sidebar ---
st.sidebar.header("⚙️ Controls")
refresh_rate = st.sidebar.slider("Auto-refresh every (seconds)", 0, 120, 30)
n_samples = st.sidebar.slider("Number of samples to display", 50, 500, 100)
st.sidebar.info("Project by mOONbLOOM26 🌙")

if refresh_rate > 0:
    time.sleep(refresh_rate)

# --- BigQuery Setup ---
credentials = service_account.Credentials.from_service_account_info(st.secrets["gcp"])
client = bigquery.Client(credentials=credentials, project=st.secrets["gcp"]["project_id"], location="asia-southeast1")

table_id = "monitoring-system-with-lora.sdp2_live_monitoring_system.lora_health_data_clean2"

@st.cache_data(ttl=30)
def fetch_latest(n=100):
    query = f"""
        SELECT id_user, timestamp, temp, hum, so2, ln, ax, ay, az, gx, gy, gz
        FROM `{table_id}`
        ORDER BY timestamp DESC
        LIMIT {n}
    """
    return client.query(query).to_dataframe()

try:
    df = fetch_latest(n_samples)
    if df.empty:
        st.info("No data found yet.")
    else:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors="coerce")

        subject_ids = df['id_user'].dropna().unique().tolist()
        tab1, tab2, tab3 = st.tabs(["📈 Overview", "👤 Subject Info", "🤖 Predictions"])

        # --- Tab 1: Overview ---
        with tab1:
            st.subheader("📈 System Overview")

            st.markdown("<div class='section'><h2>⚠️ Alerts</h2>", unsafe_allow_html=True)
            alerts = []
            if (df['so2'] > 0.1).any():
                alerts.append("SO₂ levels above threshold")
            if (df['ln'] > 1.0).any():
                alerts.append("LN signal spike detected")
            if (df[['ax','ay','az']].abs().max().max() > 5):
                alerts.append("High movement detected")
            if alerts:
                for msg in alerts:
                    st.warning(msg)
            else:
                st.success("All sensor readings are within normal range.")
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div class='section'><h2>📊 Summary Metrics</h2>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            col1.metric("Avg SO₂", f"{df['so2'].mean():.2f}")
            col2.metric("Avg LN", f"{df['ln'].mean():.2f}")
            col3.metric("Max Acceleration", f"{df[['ax','ay','az']].abs().max().max():.2f}")
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div class='section'><h2>📈 Sensor Trends</h2>", unsafe_allow_html=True)
            trend_df = df.sort_values("timestamp").set_index("timestamp")
            fig = go.Figure()
            for col, color, label in [
                ("so2", "#27ae60", "SO₂"),
                ("ln", "#c0392b", "LN"),
                ("ax", "#2980b9", "Acc X"),
                ("ay", "#8e44ad", "Acc Y"),
                ("az", "#f39c12", "Acc Z")
            ]:
                if col in trend_df.columns:
                    fig.add_trace(go.Scatter(x=trend_df.index, y=trend_df[col], mode="lines", name=label, line=dict(color=color)))
            fig.update_layout(height=500, xaxis_title="Time", yaxis_title="Sensor Value")
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div class='section'><h2>👥 Active Subjects</h2>", unsafe_allow_html=True)
            st.write(f"Active subjects: {len(subject_ids)}")
            st.json({i: sid for i, sid in enumerate(subject_ids)})
            st.markdown("</div>", unsafe_allow_html=True)

        # --- Tab 2: Subject Info ---
        with tab2:
            st.subheader("👤 Subject Info")
            for sid in subject_ids:
                st.markdown("<div class='subject-box'>", unsafe_allow_html=True)
                st.markdown(f"### 🧑 Subject {sid}")
                subj_df = df[df['id_user'] == sid].sort_values("timestamp").set_index("timestamp")

                fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                                    subplot_titles=("SO₂ & LN", "Accelerometer", "Gyroscope"))

                for col, color in zip(['so2','ln'], ['red','blue']):
                    if col in subj_df.columns:
                        fig.add_trace(go.Scatter(x=subj_df.index, y=subj_df[col], mode="lines", name=col.upper(), line=dict(color=color)), row=1, col=1)

                for axis, color in zip(['ax','ay','az'], ['green','orange','purple']):
                    if axis in subj_df.columns:
                        fig.add_trace(go.Scatter(x=subj_df.index, y=subj_df[axis], mode="lines", name=f"Acc {axis.upper()}", line=dict(color=color)), row=2, col=1)

                for axis, color in zip(['gx','gy','gz'], ['blue','brown','gray']):
                    if axis in subj_df.columns:
                        fig.add_trace(go.Scatter(x=subj_df.index, y=subj_df[axis], mode="lines", name=f"Gyro {axis.upper()}", line=dict(color=color)), row=3, col=1)

                fig.update_layout(height=900, xaxis_title="Timestamp", title=f"Subject {sid} Sensor Readings")
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

        # --- Tab 3: Predictions ---
        with tab3:
            st.subheader("🤖 Predictions")
            st.markdown("<div class='section'><h2>📡 AI Predictions</h2>", unsafe_allow_html=True)
            if df['so2'].mean() > 0.1 or df['ln'].mean() > 1.0 or df[['ax','ay','az']].abs().max().max() > 5:
                st.warning("⚠️ Potential abnormal condition detected.")
            else:
                st.success("✅ No abnormal predictions detected.")
            st.markdown("</div>", unsafe_allow_html=True)

except Exception as e:
    st.error(f"Error fetching or processing data: {e}")