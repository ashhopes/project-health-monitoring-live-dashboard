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
    h1, h2, h3 { font-family: 'Helvetica Neue', sans-serif; font-weight: 600; }
    .section {
        background: #fff; padding: 20px; margin-bottom: 20px;
        border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1);
    }
    .subject-box {
        background-color: #ffffff; border: 2px solid #800000;
        border-radius: 10px; padding: 15px; margin-bottom: 25px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Header ---
st.markdown("<h1 style='text-align: center; color:#4B0082;'>🧠 Live Health Monitoring System with LoRa</h1>", unsafe_allow_html=True)
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

        # --- Get active subject IDs dynamically ---
        subject_query = f"""
            SELECT DISTINCT id_user
            FROM `{table_id}`
            WHERE id_user IS NOT NULL
        """
        subject_ids = client.query(subject_query).to_dataframe()['id_user'].tolist()

        # --- Tabs ---
        tab1, tab2, tab3 = st.tabs(["📈 Overview", "👤 Subject Info", "🤖 Predictions"])

        # --- Layout 1: Overview ---
        with tab1:
            st.markdown("<h2 style='color:#4B0082;'>📈 System Overview</h2>", unsafe_allow_html=True)
            # (Overview sections here – same as your previous design)

        # --- Layout 2: Subject Info ---
        with tab2:
            st.subheader("👤 Section 2: Subject Info")

            # Define all subjects (3 COMs)
            all_subjects = ["user_001", "user_002", "user_003"]
            active_subjects = df['id_user'].dropna().unique().tolist()

            # Manual biodata (replace with DB if needed)
            biodata = {
                "user_001": {"Age": 25, "Weight": 60, "Height": 165},
                "user_002": {"Age": 30, "Weight": 70, "Height": 170},
                "user_003": {"Age": 28, "Weight": 55, "Height": 160}
            }

            for sid in all_subjects:
                st.markdown(f"<div class='subject-box'><h3>🧑 Subject {sid}</h3>", unsafe_allow_html=True)

                if sid not in active_subjects:
                    st.markdown("<p style='color:gray;'>❌ Subject not active yet. No data received.</p>", unsafe_allow_html=True)
                else:
                    subj_df = df[df['id_user'] == sid].copy()
                    subj_df = subj_df.sort_values("timestamp", ascending=False)

                    # --- Part 1: Biodata & Latest Vitals ---
                    bio = biodata.get(sid, {})
                    weight = bio.get("Weight", 0)
                    height = bio.get("Height", 0)
                    bmi = round(weight / ((height / 100) ** 2), 1) if weight and height else "N/A"
                    latest = subj_df.iloc[0] if not subj_df.empty else {}

                    st.markdown(f"""
                        <ul>
                            <li><b>Age:</b> {bio.get("Age", "N/A")} years</li>
                            <li><b>Weight:</b> {weight} kg</li>
                            <li><b>Height:</b> {height} cm</li>
                            <li><b>BMI:</b> {bmi}</li>
                            <li><b>SpO₂:</b> <span style='color:#27ae60; font-weight:bold;'>{latest.get('spo2', 'N/A')}</span> %</li>
                            <li><b>HR:</b> <span style='color:#c0392b; font-weight:bold;'>{latest.get('hr', 'N/A')}</span> BPM</li>
                            <li><b>Temp:</b> <span style='color:#e67e22; font-weight:bold;'>{latest.get('temp', 'N/A')}</span> °C</li>
                        </ul>
                    """, unsafe_allow_html=True)

                    # --- Part 2: Graph ---
                    subj_df = subj_df.sort_values("timestamp", ascending=True).set_index("timestamp")
                    fig = go.Figure()
                    for col, color, label in [
                        ("ax", "#2980b9", "Accel X"),
                        ("ay", "#16a085", "Accel Y"),
                        ("az", "#8e44ad", "Accel Z"),
                        ("hr", "#c0392b", "Heart Rate"),
                        ("spo2", "#27ae60", "SpO₂"),
                        ("temp", "#e67e22", "Temperature")
                    ]:
                        if col in subj_df.columns and subj_df[col].notna().any():
                            fig.add_trace(go.Scatter(
                                x=subj_df.index,
                                y=subj_df[col],
                                mode="lines",
                                name=label,
                                line=dict(color=color, width=2)
                            ))
                    fig.update_layout(
                        title=f"<b>Signal Pattern for {sid}</b>",
                        xaxis_title="Timestamp",
                        yaxis_title="Value",
                        plot_bgcolor="#fdf6ec",
                        paper_bgcolor="#fdf6ec",
                        font=dict(size=14),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # --- Part 3: Live Data Table ---
                    st.markdown("<h4>📋 Live Data Table</h4>", unsafe_allow_html=True)
                    st.dataframe(subj_df.reset_index(), use_container_width=True)

                st.markdown("</div>", unsafe_allow_html=True)

       
                # --- Layout 3: Predictions ---
        with tab3:
            st.subheader("🤖 Section 3: ML Predictions by Subject")

            # Query ML predictions from BigQuery
            pred_query = f"""
                SELECT timestamp, id_user, temp, spo2, hr, ax, ay, az, gx, gy, gz, predicted_cluster
                FROM ML.PREDICT(
                    MODEL `monitoring-system-with-lora.sdp2_live_monitoring_system.anomaly_model`,
                    (
                        SELECT temp, spo2, hr, ax, ay, az, gx, gy, gz, timestamp, id_user
                        FROM `{table_id}`
                        ORDER BY timestamp DESC
                        LIMIT 100
                    )
                )
            """
            pred_df = client.query(pred_query).to_dataframe()

            # Loop through subjects
            for sid in subject_ids:
                st.markdown("<div class='prediction-box'>", unsafe_allow_html=True)
                st.markdown(f"### 🔍 Predictions for Subject {sid}")

                sub_pred = pred_df[pred_df['id_user'] == sid]
                if sub_pred.empty:
                    st.warning(f"No predictions found for Subject {sid}")
                else:
                    # Show prediction table
                    st.dataframe(sub_pred, use_container_width=True)

                    # Show bar chart of cluster counts
                    cluster_counts = sub_pred.groupby("predicted_cluster").size()
                    st.bar_chart(cluster_counts)

                st.markdown("</div>", unsafe_allow_html=True)
except Exception as e:
    st.error(f"❌ Error fetching data: {e}")    
           
