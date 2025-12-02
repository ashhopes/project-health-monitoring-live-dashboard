import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
import plotly.graph_objects as go
import time

# ✅ FIXED: Cache BigQuery client - NO MORE SLOW AUTH EVERY RUN
@st.cache_resource
def init_client():
    credentials = service_account.Credentials.from_service_account_info(st.secrets["gcp"])
    return bigquery.Client(
        credentials=credentials,
        project=st.secrets["gcp"]["project_id"],
        location="asia-southeast1"
    )

# ✅ GLOBAL CLIENT - FAST LOADING
client = init_client()

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

# --- Login logic - ULTRA FAST ---
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
                st.rerun()  # ✅ INSTANT redirect
            else:
                st.error("❌ Invalid username or password")

        st.markdown("</div>", unsafe_allow_html=True)
        st.stop()

# --- Run login check FIRST ---
check_login()

# --- Page setup ---
st.set_page_config(page_title="Live Health Monitoring System with LoRa", layout="wide")

# --- Header ---
st.markdown("<h1 style='text-align: center; color:#4B0082;'>🧠 Live Health Monitoring System with LoRa</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Real-time monitoring of vital signs and motion data using LoRa sensors</p>", unsafe_allow_html=True)
st.markdown("---")

# --- NON-BLOCKING REFRESH COUNTER ---
if 'refresh_counter' not in st.session_state:
    st.session_state.refresh_counter = 0

# --- Sidebar controls ---
st.sidebar.header("⚙️ Controls")
refresh_rate = st.sidebar.slider("🔄 Auto-refresh every (seconds)", 10, 120, 30)  # Min 10s
n_samples = st.sidebar.slider("Number of samples to display", 50, 300, 100)  # Reduced max
st.sidebar.info("Project by mOONbLOOM26 🌙")

# ✅ FIXED REFRESH - NO time.sleep BLOCKING!
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = time.time()

if time.time() - st.session_state.last_refresh > refresh_rate:
    st.session_state.last_refresh = time.time()
    st.session_state.refresh_counter += 1
    st.rerun()

st.sidebar.metric("🔄 Refreshes", st.session_state.refresh_counter)

# --- Table reference ---
table_id = "monitoring-system-with-lora.sdp2_live_monitoring_system.lora_health_data_clean2"

# ✅ BETTER CACHING
@st.cache_data(ttl=15)  # 15s for live data
def fetch_latest(n=100):
    query = f"""
        SELECT id_user, timestamp, temp, spo2, hr, ax, ay, az, gx, gy, gz, ir, red
        FROM `{table_id}`
        ORDER BY timestamp DESC
        LIMIT {n}
    """
    return client.query(query).to_dataframe()

@st.cache_data(ttl=60)  # Subjects rarely change
def get_subjects():
    query = """
        SELECT DISTINCT id_user
        FROM `{table_id}`
        WHERE id_user IS NOT NULL
    """.format(table_id=table_id)
    return client.query(query).to_dataframe()['id_user'].tolist()

try:
    with st.spinner('Loading live LoRa data...'):
        df = fetch_latest(n_samples)
    
    if df.empty:
        st.info("📡 No data found yet. Upload from your LoRa sensors first.")
    else:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors="coerce")
        subject_ids = get_subjects()

        # --- Tabs ---
        tab1, tab2, tab3 = st.tabs(["📈 Overview", "👤 Subject Info", "🤖 Predictions"])

        # --- Layout 1: System Overview ---
        with tab1:
            st.markdown("<h2 style='color:#4B0082;'>📈 System Overview</h2>", unsafe_allow_html=True)

            # Section 1: Active Subjects
            st.markdown("<div class='section' style='border-left:6px solid #3498db;'><h3>👥 Active Subjects</h3>", unsafe_allow_html=True)
            active_subjects = df['id_user'].dropna().unique().tolist()
            latest_time = df['timestamp'].max()
            col1, col2 = st.columns([3,1])
            with col1:
                st.markdown(f"<b>📊 Active: <span style='color:#3498db;'>{len(active_subjects)}</span> subjects</b>", unsafe_allow_html=True)
                st.json({i+1: sid for i, sid in enumerate(active_subjects[:5])})  # Show top 5
            with col2:
                st.metric("🕐 Last Update", latest_time.strftime('%H:%M:%S') if pd.notna(latest_time) else 'N/A')
            st.markdown("</div>", unsafe_allow_html=True)

            # Section 2: Alerts - FASTER
            st.markdown("<div class='section' style='border-left:6px solid #e67e22;'><h3>⚠️ Live Alerts</h3>", unsafe_allow_html=True)
            alerts = []
            if 'spo2' in df and (df['spo2'] < 95).any():
                alerts.append("🫁 Low SpO₂ detected")
            if 'hr' in df and (df['hr'] > 120).any():
                alerts.append("❤️ High HR detected")
            if 'temp' in df and (df['temp'] > 38).any():
                alerts.append("🌡️ Fever detected")
            [st.error(alert) for alert in alerts]
            if not alerts:
                st.success("✅ All vitals normal")
            st.markdown("</div>", unsafe_allow_html=True)

            # Section 3: Summary Metrics - NATIVE METRICS FASTER
            st.markdown("<div class='section' style='border-left:6px solid #2ecc71;'><h3>📊 Live Metrics</h3>", unsafe_allow_html=True)
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("❤️ Avg HR", f"{df['hr'].mean():.1f} BPM")
            col2.metric("🫁 Min SpO₂", f"{df['spo2'].min():.1f}%")
            col3.metric("🌡️ Avg Temp", f"{df['temp'].mean():.1f}°C")
            col4.metric("📈 Samples", len(df))
            st.markdown("</div>", unsafe_allow_html=True)

            # Section 4: Health Trends
            st.markdown("<div class='section' style='border-left:6px solid #9b59b6;'><h3>📈 Health Trends</h3>", unsafe_allow_html=True)
            avg_hr = df['hr'].mean()
            avg_spo2 = df['spo2'].mean()
            avg_temp = df['temp'].mean()

            fig = go.Figure(data=[
                go.Bar(name="Heart Rate", x=["HR"], y=[avg_hr], marker_color="#c0392b"),
                go.Bar(name="SpO₂", x=["SpO₂"], y=[avg_spo2], marker_color="#27ae60"),
                go.Bar(name="Temperature", x=["Temp"], y=[avg_temp], marker_color="#e67e22")
            ])
            fig.update_layout(title="Live Health Metrics", height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # --- Layout 2: Subject Info - OPTIMIZED ---
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
                if sid in active_subjects:
                    st.markdown(f"<div class='subject-box'><h4>🧑 {sid}</h4>", unsafe_allow_html=True)
                    subj_df = df[df['id_user'] == sid].tail(30).copy()  # LIMITED data
                    latest = subj_df.iloc[0]

                    bio = biodata.get(sid, {})
                    bmi = round(bio.get("Weight", 0) / ((bio.get("Height", 0) / 100) ** 2), 1)

                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("❤️ HR", f"{latest.get('hr', 0):.0f}")
                        st.metric("🫁 SpO₂", f"{latest.get('spo2', 0):.1f}%")
                    with col2:
                        st.metric("🌡️ Temp", f"{latest.get('temp', 0):.1f}°C")
                        st.metric("📏 BMI", bmi)

                    # PPG - FASTER
                    if 'ir' in subj_df.columns or 'red' in subj_df.columns:
                        subj_plot = subj_df.sort_values("timestamp").tail(50).set_index("timestamp")
                        fig = go.Figure()
                        if 'ir' in subj_plot and subj_plot["ir"].notna().any():
                            fig.add_trace(go.Scatter(x=subj_plot.index, y=subj_plot["ir"], mode="lines", name="IR", line=dict(color="#8e44ad")))
                        if 'red' in subj_plot and subj_plot["red"].notna().any():
                            fig.add_trace(go.Scatter(x=subj_plot.index, y=subj_plot["red"], mode="lines", name="RED", line=dict(color="#e74c3c")))
                        if fig.data:
                            fig.update_layout(title=f"PPG {sid}", height=250)
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("No PPG data available")

                    st.markdown("</div>", unsafe_allow_html=True)

        # --- Tab 3: Predictions - LIGHTER ---
        with tab3:
            st.subheader("🤖 ML Predictions")
            try:
                # LIGHTER query - LIMIT 50
                cluster_df = client.query("""
                    SELECT spo2, hr, predicted_cluster
                    FROM ML.PREDICT(MODEL `monitoring-system-with-lora.sdp2_live_monitoring_system.lora_health_data_model`,
                    (SELECT spo2, hr, ax, ay, az, gx, gy, gz
                     FROM `monitoring-system-with-lora.sdp2_live_monitoring_system.lora_health_data_clean2`
                     ORDER BY timestamp DESC LIMIT 50))
                """).to_dataframe()

                labels = {0: "✅ Normal", 1: "⚡ Active", 2: "🚨 Critical"}
                cluster_df["Status"] = cluster_df["predicted_cluster"].map(labels)
                st.dataframe(cluster_df[["spo2", "hr", "Status"]], use_container_width=True)
                st.bar_chart(cluster_df["Status"].value_counts())
            except Exception as e:
                st.warning(f"ML predictions unavailable: {e}")

except Exception as e:
    st.error(f"Dashboard error: {e}")

# ✅ REFRESH STATUS - BOTTOM RIGHT
st.markdown(f"""
    <div style='position: fixed; bottom: 20px; right: 20px; 
                background: #4B0082; color: white; padding: 10px; 
                border-radius: 10px; font-size: 12px; z-index: 1000;'>
    🔄 Auto-refresh: {refresh_rate}s | Next: {refresh_rate - (time.time() - st.session_state.last_refresh):.0f}s
    </div>
""", unsafe_allow_html=True)
