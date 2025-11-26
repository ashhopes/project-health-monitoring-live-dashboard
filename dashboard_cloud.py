import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
import plotly.graph_objects as go
import time

# --- Page setup ---
st.set_page_config(page_title="Live Environmental Monitoring System with LoRa", layout="wide")

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

    .section {
        background: #fff;
        padding: 20px;
        margin-bottom: 20px;
        border-radius: 8px;
        box-shadow: 0 0 10px rgba(0,0,0,0.1);
        display: block;
    }
    .subject-box {
        background-color: #ffffff;
        border: 2px solid #800000;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 25px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Header ---
st.markdown("<h1 style='text-align: center;'>🌍 Live Environmental Monitoring System with LoRa</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Real-time monitoring of environmental parameters using LoRa sensors</p>", unsafe_allow_html=True)
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
        SELECT id_user, timestamp, temp_m, hum_m, s02, co, o3, pm10, pm25
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

        # --- Tabs ---
        tab1, tab2, tab3 = st.tabs(["📈 Overview", "👤 Subject Info", "🤖 Predictions"])

        # --- Layout 1: System Overview ---
        with tab1:
            st.subheader("📈 Section 1: System Overview")

            # Section 1: Alerts
            st.markdown("<div class='section'><h2>⚠️ Alerts</h2>", unsafe_allow_html=True)
            alerts = []
            if 's02' in df.columns and (df['s02'] > 0.1).any():
                alerts.append("SO₂ levels above threshold")
            if 'co' in df.columns and (df['co'] > 1.0).any():
                alerts.append("CO levels above threshold")
            if 'pm25' in df.columns and (df['pm25'] > 50).any():
                alerts.append("High PM2.5 detected")
            if alerts:
                for msg in alerts:
                    st.warning(msg)
            else:
                st.success("All environmental parameters are within normal range.")
            st.markdown("</div>", unsafe_allow_html=True)

            # Section 2: Summary Metrics
            st.markdown("<div class='section'><h2>📊 Summary Metrics</h2>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            col1.metric("Average SO₂", f"{df['s02'].mean():.2f} ppm")
            col2.metric("Average CO", f"{df['co'].mean():.2f} ppm")
            col3.metric("Average PM2.5", f"{df['pm25'].mean():.2f} µg/m³")
            st.markdown("</div>", unsafe_allow_html=True)

            # Section 3: Trends
            st.markdown("<div class='section'><h2>📈 Environmental Trends</h2>", unsafe_allow_html=True)
            trend_df = df.sort_values("timestamp", ascending=True).set_index("timestamp")
            fig = go.Figure()
            for col, color, label in [
                ("s02", "#27ae60", "SO₂ (ppm)"),
                ("co", "#c0392b", "CO (ppm)"),
                ("pm10", "#2980b9", "PM10 (µg/m³)"),
                ("pm25", "#8e44ad", "PM2.5 (µg/m³)")
            ]:
                if col in trend_df.columns and trend_df[col].notna().any():
                    fig.add_trace(go.Scatter(
                        x=trend_df.index, y=trend_df[col],
                        mode="lines+markers", name=label,
                        line=dict(color=color)
                    ))
            fig.update_layout(
                xaxis_title="Time", yaxis_title="Values",
                plot_bgcolor="#fdf6ec", paper_bgcolor="#fdf6ec",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # Section 4: Active Subjects
            st.markdown("<div class='section'><h2>👥 Active Subjects</h2>", unsafe_allow_html=True)
            active_subjects = df['id_user'].dropna().unique().tolist()
            st.write(f"Currently receiving data from {len(active_subjects)} subjects:")
            st.json({i: sid for i, sid in enumerate(active_subjects)})
            st.markdown("</div>", unsafe_allow_html=True)

        # --- Layout 2: Subject Info ---
        with tab2:
            st.subheader("👤 Section 2: Subject Info")
            for sid in subject_ids:
                st.markdown("<div class='subject-box'>", unsafe_allow_html=True)
                st.markdown(f"### 🧑 Subject {sid} (ID: {sid})")
                subj_df = df[df['id_user'] == sid].copy()
                if subj_df.empty:
                    st.warning(f"No data found for Subject {sid}")
                else:
                    subj_df = subj_df.sort_values("timestamp", ascending=True).set_index("timestamp")

                    fig = go.Figure()
                    for col, color, label in [
                        ("s02", "#27ae60", "SO₂ (ppm)"),
                        ("co", "#c0392b", "CO (ppm)"),
                        ("pm10", "#2980b9", "PM10 (µg/m³)"),
                        ("pm25", "#8e44ad", "PM2.5 (µg/m³)")
                    ]:
                        if col in subj_df.columns and subj_df[col].notna().any():
                            fig.add_trace(go.Scatter(
                                x=subj_df.index, y=subj_df[col],
                                mode="lines+markers", name=label,
                                line=dict(color=color)
                            ))

                    fig.update_layout(
                        title="Environmental Sensor Readings",
                        xaxis_title="Timestamp",
                        yaxis_title="Sensor Values",
                        height=600,
                        plot_bgcolor="#fdf6ec", paper_bgcolor="#fdf6ec"
                    )
                    st.plotly_chart(fig, use_container_width=True)

                st.markdown("</div>", unsafe_allow_html=True)
        # --- Layout 3: Predictions ---
        with tab3:
            st.subheader("🤖 Section 3: Predictions")

            # Kotak section untuk Predictions
            st.markdown("<div class='section'><h2>📡 AI Predictions</h2>", unsafe_allow_html=True)

            # Placeholder untuk model ML
            st.info("Prediction models can be integrated here (e.g., anomaly detection, air quality classification).")

            # Contoh rule-based prediction menggunakan data sebenar
            if 's02' in df.columns and 'co' in df.columns and 'pm25' in df.columns:
                avg_s02 = df['s02'].mean()
                avg_co = df['co'].mean()
                avg_pm25 = df['pm25'].mean()

                if avg_s02 > 0.1 or avg_co > 1.0 or avg_pm25 > 50:
                    st.warning("⚠️ Potential unhealthy air quality detected.")
                else:
                    st.success("✅ Air quality appears normal.")

            st.markdown("</div>", unsafe_allow_html=True)

except Exception as e:
    st.error(f"Error fetching or processing data: {e}")