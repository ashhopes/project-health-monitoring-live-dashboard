import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
import plotly.graph_objects as go
import time

# --- Page setup ---
st.set_page_config(page_title="Live Health Monitoring System with LoRa", layout="wide")

# --- Custom Elegant Theme ---
st.markdown(
    """
    <style>
    .stApp {
        background-image: url("http://www.umpsa.edu.my/sites/default/files/slider/ZAF_1540-edit.jpg");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }
    .stApp::before {
        content: "";
        position: fixed;
        top: 0; left: 0;
        width: 100%; height: 100%;
        background-color: rgba(255, 255, 255, 0.7);
        z-index: -1;
    }
    .stSidebar { background-color: #f7ede2; }
    h1, h2, h3 { color: #800000; font-family: 'Helvetica Neue', sans-serif; font-weight: 600; }
    .section-wrapper {
        background-color: #ffffff;
        border: 2px solid #bfa76f;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 30px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    }
    .subject-box {
        background-color: #ffffff;
        border: 2px solid #800000;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 25px;
    }
    .prediction-box {
        background-color: #ffffff;
        border: 2px solid #bfa76f;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 25px;
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
st.sidebar.info("Project by Tg22051-UMPSA🌙")

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

        # --- Get active subject IDs dynamically ---
        subject_query = f"""
            SELECT DISTINCT id_user
            FROM `{table_id}`
            WHERE id_user IS NOT NULL
        """
        subject_ids = client.query(subject_query).to_dataframe()['id_user'].tolist()

        # --- Tabs untuk 3 layout ---
        tab1, tab2, tab3 = st.tabs(["📈 Overview", "👤 Subject Info", "🤖 Predictions"])

        # --- Layout 1: Overview ---
        with tab1:
            st.markdown("<div class='section-wrapper'>", unsafe_allow_html=True)
            st.subheader("📈 Section 1: System Overview")

            # Summary metrics
            col1, col2, col3 = st.columns(3)
            col1.metric("Average HR", f"{df['hr'].mean():.1f} BPM")
            col2.metric("Average SpO₂", f"{df['spo2'].mean():.1f} %")
            col3.metric("Average Temp", f"{df['temp'].mean():.1f} °C")

            # Distribution charts
            st.markdown("### 📊 Distribution of Health Metrics")
            dist_fig = go.Figure()
            dist_fig.add_trace(go.Box(y=df['hr'], name="Heart Rate", marker_color="#c0392b"))
            dist_fig.add_trace(go.Box(y=df['spo2'], name="SpO₂", marker_color="#27ae60"))
            dist_fig.add_trace(go.Box(y=df['temp'], name="Temperature", marker_color="#d35400"))
            dist_fig.update_layout(plot_bgcolor="#fdf6ec", paper_bgcolor="#fdf6ec")
            st.plotly_chart(dist_fig, use_container_width=True)

            # Active subjects
            st.markdown("### 👥 Active Subjects")
            active_subjects = df['id_user'].unique().tolist()
            st.write(f"Currently receiving data from {len(active_subjects)} subjects: {active_subjects}")

            # Alerts
            st.markdown("### ⚠️ Alerts")
            if (df['spo2'] < 95).any():
                st.warning("Some subjects have SpO₂ below 95%")
            if (df['hr'] > 120).any():
                st.error("High heart rate detected (>120 BPM)")
            if (df['temp'] > 38).any():
                st.error("Fever detected (Temp > 38°C)")

            st.markdown("</div>", unsafe_allow_html=True)

        # --- Layout 2: Subject/Testor Info ---
        with tab2:
            st.subheader("👤 Section 2: Subject Info")
            for sid in subject_ids:
                st.markdown("<div class='subject-box'>", unsafe_allow_html=True)
                st.markdown(f"### 🧑 Subject {sid} (ID: {sid})")

                subj_df = df[df['id_user'] == sid].head(100)
                if subj_df.empty:
                    st.warning(f"No data found for Subject {sid}")
                else:
                    subj_df = subj_df.sort_values("timestamp", ascending=True).set_index("timestamp")

                    fig = go.Figure()
                    for col, color, label in [
                        ("temp", "#d35400", "Temperature (°C)"),
                        ("hr", "#c0392b", "Heart Rate (BPM)"),
                        ("spo2", "#27ae60", "SpO₂ (%)")
                    ]:
                        if col in subj_df.columns:
                            fig.add_trace(go.Scatter(
                                x=subj_df.index, y=subj_df[col],
                                mode="lines+markers", name=label, line=dict(color=color)
                            ))
                    fig.update_layout(title=f"Health Trends for Subject {sid}")
                    st.plotly_chart(fig, use_container_width=True)

                    st.dataframe(subj_df, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

        # --- Layout 3: Predictions ---
        with tab3:
            st.subheader("🤖 Section 3: ML Predictions by Subject")
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

            for sid in subject_ids:
                st.markdown("<div class='prediction-box'>", unsafe_allow_html=True)
                st.markdown(f"### 🔍 Predictions for Subject {sid}")
                sub_pred = pred_df[pred_df['id_user'] == sid]
                if sub_pred.empty:
                    st.warning(f"No predictions found for Subject {sid}")
                else:
                    st.dataframe(sub_pred, use_container_width=True)
                    st.bar_chart(sub_pred['predicted_cluster'].value_counts().sort_index())
                st.markdown("</div>", unsafe_allow_html=True)       
except Exception as e:
    st.error(f"BigQuery error: {e}")
