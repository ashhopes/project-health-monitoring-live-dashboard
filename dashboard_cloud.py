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

        # --- Layout 1: System Overview ---
        with tab1:
            st.markdown("<h2 style='color:#4B0082;'>📈 System Overview</h2>", unsafe_allow_html=True)

            # Section 1: Active Subjects
            st.markdown("<div class='section' style='border-left:6px solid #3498db;'><h3>👥Section 1: Active Subjects</h3>", unsafe_allow_html=True)
            active_subjects = df['id_user'].dropna().unique().tolist()
            active_subjects = df['id_user'].dropna().unique().tolist()
            st.markdown(f"<b>Currently receiving data from <span style='color:#3498db;'>{len(active_subjects)}</span> subjects:</b>", unsafe_allow_html=True)
            st.json({i: sid for i, sid in enumerate(active_subjects)})
            st.markdown("</div>", unsafe_allow_html=True)

            # Section 2: Alerts
            st.markdown("<div class='section' style='border-left:6px solid #e67e22;'><h3>Section 2:⚠️ Alert Notification</h3>", unsafe_allow_html=True)
            alerts = []
            if 'spo2' in df.columns and (df['spo2'] < 95).any():
                low_spo2_users = df[df['spo2'] < 95]['id_user'].unique().tolist()
                alerts.append(f"SpO₂ below 95%: <b><span style='color:red;'>{', '.join(low_spo2_users)}</span></b>")
            if 'hr' in df.columns and (df['hr'] > 120).any():
                high_hr_users = df[df['hr'] > 120]['id_user'].unique().tolist()
                alerts.append(f"HR > 120 BPM: <b><span style='color:red;'>{', '.join(high_hr_users)}</span></b>")
            if 'temp' in df.columns and (df['temp'] > 38).any():
                fever_users = df[df['temp'] > 38]['id_user'].unique().tolist()
                alerts.append(f"Temp > 38°C: <b><span style='color:red;'>{', '.join(fever_users)}</span></b>")
            if alerts:
                st.markdown("<ul>" + "".join([f"<li>{msg}</li>" for msg in alerts]) + "</ul>", unsafe_allow_html=True)
            else:
                st.markdown("<p style='color:green;'><b>✅ All vitals are within normal range.</b></p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # Section 3: Summary Metrics
            st.markdown("<div class='section' style='border-left:6px solid #2ecc71;'><h3>Section 3: 📊 Summary Metrics</h3>", unsafe_allow_html=True)
            col1, col2, col3, col4 = st.columns(4)
            col1.markdown(f"**Average HR:** <span style='color:#c0392b;'><b>{df['hr'].mean():.1f} BPM</b></span>", unsafe_allow_html=True)
            col2.markdown(f"**minSpO₂:** <span style='color:#27ae60;'><b>{df['spo2'].min():.1f} %</b></span>", unsafe_allow_html=True)
            col3.markdown(f"**Average Temp:** <span style='color:#e67e22;'><b>{df['temp'].mean():.1f} °C</b></span>", unsafe_allow_html=True)
            col4.markdown(f"**maxTemp:** <span style='color:#e74c3c;'><b>{df['temp'].max():.1f} °C</b></span>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # Section 4: Health Trend Comparison
            st.markdown("<div class='section' style='border-left:6px solid #9b59b6;'><h3>Section 4: 📈 Health Trend Comparison</h3>", unsafe_allow_html=True)
            avg_hr = df['hr'].mean()
            avg_spo2 = df['spo2'].mean()
            avg_temp = df['temp'].mean()

            fig = go.Figure(data=[
                go.Bar(name="Heart Rate (BPM)", x=["HR"], y=[avg_hr], marker_color="#c0392b"),
                go.Bar(name="SpO₂ (%)", x=["SpO₂"], y=[avg_spo2], marker_color="#27ae60"),
                go.Bar(name="Temperature (°C)", x=["Temp"], y=[avg_temp], marker_color="#e67e22")
            ])
            fig.update_layout(
                title="<b>Average Health Metrics</b>",
                yaxis_title="Value",
                plot_bgcolor="#fdf6ec",
                paper_bgcolor="#fdf6ec",
                height=500,
                font=dict(size=14)
            )
            st.plotly_chart(fig, use_container_width=True)
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
                        ("temp", "#d35400", "Temperature (°C)"),
                        ("hr", "#c0392b", "Heart Rate (BPM)"),
                        ("spo2", "#27ae60", "SpO₂ (%)")
                    ]:
                        if col in subj_df.columns and subj_df[col].notna().any():
                            fig.add_trace(go.Scatter(
                                x=subj_df.index, y=subj_df[col],
                                mode="lines+markers", name=label, line=dict(color=color)
                            ))
                    fig.update_layout(title=f"Health Trends for Subject {sid}")
                    st.plotly_chart(fig, use_container_width=True)
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
           
