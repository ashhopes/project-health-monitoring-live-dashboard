import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
import plotly.graph_objects as go
import time

# --- Page setup ---
st.set_page_config(page_title="Live Health Monitoring System with LoRa", layout="wide")

# --- Custom Elegant Theme (Maroon + Beige + Gold + Background Image + Card Style) ---
st.markdown(
    """
    <style>
    .stApp {
        background-image: url("umpsa.png");
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }
    .stApp::before {
        content: "";
        position: fixed;
        top: 0; left: 0;
        width: 100%; height: 100%;
        background-color: rgba(255, 255, 255, 0.7); /* overlay supaya teks jelas */
        z-index: -1;
    }
    .stSidebar { background-color: #f7ede2; }
    h1, h2, h3 { color: #800000; font-family: 'Helvetica Neue', sans-serif; font-weight: 600; }
    .stDataFrame { background-color: #ffffff; border-radius: 8px; padding: 10px; border: 1px solid #bfa76f; }
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

        # --- Tabs untuk 3 layout ---
        tab1, tab2, tab3 = st.tabs(["📈 Live Data", "👤 Subject/Testor Info", "🤖 Predictions"])

        # --- Layout 1: Live Data ---
        with tab1:
            st.markdown("<div class='section-wrapper'>", unsafe_allow_html=True)
            st.subheader("📈 Section 1: Live Sensor Data")
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
            fig.update_layout(title="Live Health Metrics", xaxis_title="Time", yaxis_title="Values",
                              plot_bgcolor="#fdf6ec", paper_bgcolor="#fdf6ec")
            st.plotly_chart(fig, use_container_width=True)

            with st.expander("🗃️ Show Latest Sensor Data"):
                st.dataframe(df, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # --- Layout 2: Subject/Testor Info ---
        with tab2:
            st.subheader("👤 Section 2: Subject Info")
            subjects = [
                {"name": "Noryusnita", "age": 48, "gender": "Female", "weight": 67.8, "height": 159, "bmi": 28.5, "id": "U1", "com_port": "COM8"},
                {"name": "Arif", "age": 50, "gender": "Male", "weight": 89, "height": 176, "bmi": 27.0, "id": "U2", "com_port": "COM9"},
                {"name": "Ayreen", "age": 25, "gender": "Female", "weight": 55, "height": 160, "bmi": 21.5, "id": "U3", "com_port": "COM10"},
                {"name": "Kayatri", "age": 29, "gender": "Female", "weight": 70, "height": 170, "bmi": 24.2, "id": "U4", "com_port": "COM12"},
            ]
            for subj in subjects:
                st.markdown("<div class='subject-box'>", unsafe_allow_html=True)
                st.markdown(f"### 🧑 {subj['name']} (ID: {subj['id']}, Port: {subj['com_port']})")
                st.write(
                    f"Age: {subj['age']} | Gender: {subj['gender']} | "
                    f"Weight: {subj['weight']} kg | Height: {subj['height']} cm | BMI: {subj['bmi']}"
                )

                subj_df = df[df['id_user'] == subj['id']].head(100)
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
                fig.update_layout(title=f"Health Trends for {subj['name']}")
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