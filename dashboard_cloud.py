import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
import plotly.graph_objects as go
import time

st.markdown("""
    <style>
    .stSidebar { background-color: #f7ede2; }
    .section { background: #fff; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
    .subject-box { background: #ffffff; border: 2px solid #800000; border-radius: 10px; padding: 15px; margin: 10px 0; }
    </style>
""", unsafe_allow_html=True)

# Login (same as before)
def check_login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if not st.session_state.logged_in:
        st.markdown("<h2 style='text-align:center;'>🔐 Login</h2>", unsafe_allow_html=True)
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if username == "admin" and password == "moon123":
                st.session_state.logged_in = True
                st.success("✅ Login successful!")
            else:
                st.error("❌ Invalid credentials")
        st.stop()

check_login()

st.set_page_config(page_title="🧠 LoRa Health Dashboard", layout="wide")

# Header
st.markdown("<h1 style='text-align:center;color:#4B0082;'>🧠 Live Health Monitoring - LoRa</h1>", unsafe_allow_html=True)

# ✅ SIDEBAR CONTROLS WITH NATIVE AUTO-REFRESH
st.sidebar.header("⚙️ Controls")
refresh_rate = st.sidebar.slider("🔄 Auto-refresh every", 5, 60, 30)
n_samples = st.sidebar.slider("📊 Samples", 50, 500, 100)

# ✅ NATIVE STREAMLIT AUTO-REFRESH (WORKS ON STREAMLIT CLOUD)
if refresh_rate > 0:
    st.sidebar.metric("⏱️ Next refresh", f"{refresh_rate}s")
    time.sleep(refresh_rate)
    st.rerun()

# BigQuery setup
@st.cache_resource
def init_client():
    credentials = service_account.Credentials.from_service_account_info(st.secrets["gcp"])
    return bigquery.Client(credentials=credentials, project=st.secrets["gcp"]["project_id"])

client = init_client()
table_id = "monitoring-system-with-lora.sdp2_live_monitoring_system.lora_health_data_clean2"

@st.cache_data(ttl=5)  # 5s cache for live data
def fetch_data(n=100):
    query = f"SELECT * FROM `{table_id}` ORDER BY timestamp DESC LIMIT {n}"
    return client.query(query).to_dataframe()

# Main dashboard
try:
    df = fetch_data(n_samples)
    if df.empty:
        st.info("📡 Waiting for LoRa sensor data...")
        st.stop()
    
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    st.success(f"✅ Live data: {len(df)} samples | Last update: {df['timestamp'].max()}")
    
    # Tabs
    tab1, tab2 = st.tabs(["📈 Overview", "👤 Subjects"])
    
    with tab1:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("❤️ Avg HR", f"{df['hr'].mean():.1f}bpm")
        col2.metric("🫁 Avg SpO₂", f"{df['spo2'].mean():.1f}%")
        col3.metric("🌡️ Avg Temp", f"{df['temp'].mean():.1f}°C")
        col4.metric("👥 Active Users", len(df['id_user'].unique()))
        
        st.markdown("<div class='section'><h3>⚠️ Alerts</h3>", unsafe_allow_html=True)
        alerts = []
        if (df['spo2'] < 95).any(): alerts.append("🫁 Low SpO₂ detected")
        if (df['hr'] > 120).any(): alerts.append("❤️ High HR detected")
        if (df['temp'] > 38).any(): alerts.append("🌡️ Fever detected")
        for alert in alerts: st.error(alert)
        if not alerts: st.success("✅ All vitals normal")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with tab2:
        subjects = df['id_user'].unique()
        for subject in subjects:
            st.markdown(f"<div class='subject-box'><h4>🧑 {subject}</h4>", unsafe_allow_html=True)
            subj_df = df[df['id_user'] == subject].tail(20)
            col1, col2 = st.columns(2)
            latest = subj_df.iloc[0]
            col1.metric("HR", latest['hr'])
            col2.metric("SpO₂", f"{latest['spo2']:.1f}%")
            st.line_chart(subj_df.set_index('timestamp')['hr'])
            st.markdown("</div>", unsafe_allow_html=True)

except Exception as e:
    st.error(f"❌ Error: {e}")
    st.info("🔧 Check `secrets.toml` and BigQuery table")
