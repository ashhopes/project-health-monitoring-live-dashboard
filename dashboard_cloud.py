import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh  # ✅ Auto-refresh import
import time

st.markdown("""
    <style>
    body {
        background-color: #f2f2f2;
        background-image: url("https://images.unsplash.com/photo-1588776814546-ec7d2c7f1b6b");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }
    .login-box {
        background-color: #e6e6e6;
        border: 1px solid #999999;
        border-radius: 8px;
        padding: 25px;
        width: 350px;
        margin: auto;
        margin-top: 120px;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.1);
    }
    .login-title {
        text-align: center;
        font-size: 22px;
        font-weight: 500;
        color: #333333;
        margin-bottom: 20px;
    }
    .stTextInput > div > input {
        background-color: #f9f9f9;
        color: #333333;
        border: 1px solid #cccccc;
    }
    .stButton button {
        background-color: #cccccc;
        color: #333333;
        border-radius: 4px;
        border: none;
        padding: 6px 16px;
    }
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
""", unsafe_allow_html=True)

# --- Login logic ---
def check_login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.markdown("<div class='login-title'>🔐 Login Page</div>", unsafe_allow_html=True)

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if username == "admin" and password == "moon123":
                st.session_state.logged_in = True
                st.success("✅ Login successful!")
            else:
                st.error("❌ Invalid username or password")

        st.markdown("</div>", unsafe_allow_html=True)
        st.stop()

# --- Run login check ---
check_login()

# --- Page setup ---
st.set_page_config(page_title="Live Health Monitoring System with LoRa", layout="wide")

# --- Header ---
st.markdown("<h1 style='text-align: center; color:#4B0082;'>🧠 Live Health Monitoring System with LoRa</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Real-time monitoring of vital signs and motion data using LoRa sensors</p>", unsafe_allow_html=True)
st.markdown("---")

# --- Sidebar controls ---
st.sidebar.header("⚙️ Controls")
refresh_rate = st.sidebar.slider("🔄 Auto-refresh every (seconds)", 5, 120, 30)  # ✅ Min 5s
n_samples = st.sidebar.slider("Number of samples to display", 50, 500, 100)
st.sidebar.info("Project by mOONbLOOM26 🌙")

# ✅ AUTO-REFRESH IMPLEMENTATION (REPLACE time.sleep)
count = st_autorefresh(interval=refresh_rate*1000, limit=None, key="fancy_refresh")  # Runs every X seconds
st.sidebar.metric("⏱️ Refresh Count", count)  # Shows refresh counter

# --- BigQuery Authentication ---
@st.cache_resource
def init_bigquery():
    credentials = service_account.Credentials.from_service_account_info(st.secrets["gcp"])
    return bigquery.Client(
        credentials=credentials,
        project=st.secrets["gcp"]["project_id"],
        location="asia-southeast1"
    )

client = init_bigquery()

# --- Table reference ---
table_id = "monitoring-system-with-lora.sdp2_live_monitoring_system.lora_health_data_clean2"

# --- Fetch latest data ---
@st.cache_data(ttl=10)  # ✅ Shorter cache for live data
def fetch_latest(n=100):
    query = f"""
        SELECT id_user, timestamp, temp, spo2, hr, ax, ay, az, gx, gy, gz, ir, red
        FROM `{table_id}`
        ORDER BY timestamp DESC
        LIMIT {n}
    """
    return client.query(query).to_dataframe()

try:
    df = fetch_latest(n_samples)
    if df.empty:
        st.info("📡 No data found yet. Upload from your LoRa sensors first.")
        st.stop()
    else:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors="coerce")

        # --- Get active subject IDs dynamically ---
        subject_query = f"""
            SELECT DISTINCT id_user
            FROM `{table_id}`
            WHERE id_user IS NOT NULL
            ORDER BY id_user
        """
        subject_ids = client.query(subject_query).to_dataframe()['id_user'].tolist()

        # --- Tabs ---
        tab1, tab2, tab3 = st.tabs(["📈 Overview", "👤 Subject Info", "🤖 Predictions"])

        # --- Layout 1: System Overview ---
        with tab1:
            st.markdown("<h2 style='color:#4B0082;'>📈 System Overview</h2>", unsafe_allow_html=True)

            # Section 1: Active Subjects & Last Update
            st.markdown("<div class='section' style='border-left:6px solid #3498db;'><h3>👥 Active Subjects</h3>", unsafe_allow_html=True)
            active_subjects = df['id_user'].dropna().unique().tolist()
            latest_time = df['timestamp'].max()
            col1, col2 = st.columns([3,1])
            with col1:
                st.markdown(f"<b>📊 Receiving data from <span style='color:#3498db;'>{len(active_subjects)}</span> subjects:</b>", unsafe_allow_html=True)
                st.json({i+1: sid for i, sid in enumerate(active_subjects)})
            with col2:
                st.markdown(f"**🕐 Last update:** {latest_time.strftime('%H:%M:%S') if pd.notna(latest_time) else 'N/A'}")
            st.markdown("</div>", unsafe_allow_html=True)

            # Section 2: Live Alerts
            st.markdown("<div class='section' style='border-left:6px solid #e67e22;'><h3>⚠️ Live Alerts</h3>", unsafe_allow_html=True)
            alerts = []
            if 'spo2' in df.columns and (df['spo2'] < 95).any():
                low_spo2_users = df[df['spo2'] < 95]['id_user'].unique().tolist()
                alerts.append(f"🫁 SpO₂ < 95%: **{', '.join(low_spo2_users)}**")
            if 'hr' in df.columns and (df['hr'] > 120).any():
                high_hr_users = df[df['hr'] > 120]['id_user'].unique().tolist()
                alerts.append(f"❤️ HR > 120bpm: **{', '.join(high_hr_users)}**")
            if 'temp' in df.columns and (df['temp'] > 38).any():
                fever_users = df[df['temp'] > 38]['id_user'].unique().tolist()
                alerts.append(f"🌡️️ Temp > 38°C: **{', '.join(fever_users)}**")
            
            if alerts:
                for alert in alerts:
                    st.error(alert)
            else:
                st.success("✅ All vitals within normal range")
            st.markdown("</div>", unsafe_allow_html=True)

            # Section 3: Live Metrics
            st.markdown("<div class='section' style='border-left:6px solid #2ecc71;'><h3>📊 Live Metrics</h3>", unsafe_allow_html=True)
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("❤️ Avg HR", f"{df['hr'].mean():.1f} bpm", f"{df['hr'].mean()-df['hr'].shift().mean():+.1f}")
            col2.metric("🫁 Min SpO₂", f"{df['spo2'].min():.1f}%", f"{df['spo2'].min()-df['spo2'].shift().min():+.1f}")
            col3.metric("🌡️ Avg Temp", f"{df['temp'].mean():.1f}°C", f"{df['temp'].mean()-df['temp'].shift().mean():+.1f}")
            col4.metric("📈 Samples", len(df), "1")
            st.markdown("</div>", unsafe_allow_html=True)

        # --- Layout 2: Subject Info ---
        with tab2:
            st.subheader("👤 Subject Details")

            all_subjects = ["user_001", "user_002", "user_003"]
            active_subjects = df['id_user'].dropna().unique().tolist()

            biodata = {
                "user_001": {"Age": 25, "Weight": 60, "Height": 165},
                "user_002": {"Age": 30, "Weight": 70, "Height": 170},
                "user_003": {"Age": 28, "Weight": 55, "Height": 160}
            }

            for sid in all_subjects:
                st.markdown(f"<div class='subject-box'><h4>🧑 {sid}</h4>", unsafe_allow_html=True)
                
                if sid not in active_subjects:
                    st.warning("❌ Offline - No recent data")
                else:
                    subj_df = df[df['id_user'] == sid].copy().tail(50)  # Last 50 samples
                    latest = subj_df.iloc[0]

                    # Biodata & Latest Vitals
                    bio = biodata.get(sid, {})
                    bmi = round(bio.get("Weight", 0) / ((bio.get("Height", 0) / 100) ** 2), 1) if bio.get("Height") else "N/A"
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("❤️ HR", f"{latest.get('hr', 'N/A')}", "📈")
                        st.metric("🫁 SpO₂", f"{latest.get('spo2', 'N/A')}%", "📈")
                        st.metric("🌡️ Temp", f"{latest.get('temp', 'N/A')}°C", "📈")
                    with col2:
                        st.metric("📏 BMI", bmi)
                        st.metric("👤 Age", bio.get("Age", "N/A"))

                    # Live Waveform
                    if 'ir' in subj_df.columns or 'red' in subj_df.columns:
                        subj_df_plot = subj_df.sort_values("timestamp").set_index("timestamp").tail(100)
                        fig = go.Figure()
                        
                        if "ir" in subj_df_plot.columns and subj_df_plot["ir"].notna().any():
                            fig.add_trace(go.Scatter(x=subj_df_plot.index, y=subj_df_plot["ir"],
                                                   mode="lines", name="IR", line=dict(color="#8e44ad")))
                        if "red" in subj_df_plot.columns and subj_df_plot["red"].notna().any():
                            fig.add_trace(go.Scatter(x=subj_df_plot.index, y=subj_df_plot["red"],
                                                   mode="lines", name="RED", line=dict(color="#e74c3c")))
                        
                        fig.update_layout(title=f"📊 Live PPG {sid}", height=300, showlegend=True)
                        st.plotly_chart(fig, use_container_width=True)

                    st.dataframe(subj_df[['timestamp', 'hr', 'spo2', 'temp']].tail(10), use_container_width=True)
                
                st.markdown("</div>", unsafe_allow_html=True)

        # --- Tab 3: ML Predictions ---
        with tab3:
            st.subheader("🤖 Health Predictions")
            
            try:
                query_cluster = """
                SELECT spo2, hr, predicted_cluster
                FROM ML.PREDICT(MODEL `monitoring-system-with-lora.sdp2_live_monitoring_system.lora_health_data_model`,
                    (SELECT * FROM `monitoring-system-with-lora.sdp2_live_monitoring_system.lora_health_data_clean2` 
                     ORDER BY timestamp DESC LIMIT 100))
                ORDER BY predicted_cluster
                """
                cluster_df = client.query(query_cluster).to_dataframe()
                
                labels = {0: "✅ Normal", 1: "⚡ Active", 2: "🚨 Critical"}
                cluster_df["Status"] = cluster_df["predicted_cluster"].map(labels)
                
                st.dataframe(cluster_df, use_container_width=True)
                st.bar_chart(cluster_df["Status"].value_counts())
                
            except Exception as e:
                st.error(f"❌ ML Model error: {e}")

except Exception as e:
    st.error(f"💥 Dashboard error: {e}")
    st.info("🔧 Check BigQuery connection and secrets.toml")
