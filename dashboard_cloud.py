import os
import serial
import pandas as pd
import re
from datetime import datetime
from pytz import timezone
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objects as go
import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account

# === Configuration ===
SERIAL_PORT = 'COM8'   # Adjust to your actual port
BAUD_RATE = 9600
MALAYSIA = timezone("Asia/Kuala_Lumpur")

# === BigQuery Configuration ===
# Make sure your .streamlit/secrets.toml contains the JSON you uploaded
credentials = service_account.Credentials.from_service_account_info(st.secrets["gcp"])
client = bigquery.Client(credentials=credentials, project="monitoring-system-with-lora")
table_id = "monitoring-system-with-lora.sensor_data.lora_health_data_clean"

def upload_to_bigquery(entry):
    try:
        df = pd.DataFrame([entry])
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        job = client.load_table_from_dataframe(df, table_id)
        job.result()
        debug_expander.success("✅ Uploaded to BigQuery")
    except Exception as e:
        debug_expander.error(f"❌ Upload failed: {e}")

# === Page setup ===
st.set_page_config(page_title="Health Monitoring Dashboard", layout="wide")

# === Background style ===
st.markdown("""
    <style>
    .stApp {
        background-image: url("md.gif");
        background-attachment: fixed;
        background-size: cover;
        background-position: center;
    }
    </style>
""", unsafe_allow_html=True)

# === Sidebar Debug ===
debug_expander = st.sidebar.expander("Serial Debug", expanded=True)

# === Title ===
st.markdown("""
    <div style="text-align: center;">
        <h2>🧠 Health Monitoring System with LoRa</h2>
        <h4>Real-time Body Sensor Data Visualization</h4>
    </div>
""", unsafe_allow_html=True)

# === Serial Setup ===
if "ser" not in st.session_state:
    try:
        st.session_state.ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.5)
        debug_expander.success(f"✅ Connected to {SERIAL_PORT} @ {BAUD_RATE} baud")
    except Exception as e:
        debug_expander.error(f"❌ Serial port error: {e}")
        st.warning("⚠️ Serial connection not available. No data will be displayed.")
        st.stop()

# === Regex pattern ===
pattern = re.compile(
    r"^T:(?P<temp>[\d\.]+),H:(?P<hum>[\d\.]+),HR:(?P<hr>\d+|--),SpO2:(?P<spo2>\d+|--),"
    r"ax:(?P<ax>-?[\d\.]+),ay:(?P<ay>-?[\d\.]+),az:(?P<az>-?[\d\.]+),"
    r"gx:(?P<gx>-?[\d\.]+),gy:(?P<gy>-?[\d\.]+),gz:(?P<gz>-?[\d\.]+)$"
)

# === Session state ===
if "data" not in st.session_state:
    st.session_state.data = []
if "invalid_lines" not in st.session_state:
    st.session_state.invalid_lines = []

# === Utility functions ===
def safe_float(val): 
    try: return float(val)
    except: return None

def safe_int(val): 
    try: return int(val) if val != "--" else None
    except: return None

def read_serial_lines():
    lines = []
    ser = st.session_state.ser
    try:
        while getattr(ser, "in_waiting", 0) > 0:
            raw = ser.readline().decode('utf-8', errors='replace').strip()
            if raw:
                if raw.lower().startswith("received:"):
                    raw = raw.split(":", 1)[1].strip()
                debug_expander.write(f"Raw -> {raw}")
                lines.append(raw)
    except Exception as e:
        debug_expander.error(f"Serial read error: {e}")
    return lines

def create_gauge(value, title, min_val, max_val, units=""):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value or 0,
        title={'text': f"{title} ({units})"},
        gauge={
            'axis': {'range': [min_val, max_val]},
            'bar': {'color': "darkblue"},
            'steps': [{'range': [min_val, max_val], 'color': '#e9edf2'}]
        }
    ))
    fig.update_layout(height=250, margin=dict(l=10, r=10, t=40, b=10))
    return fig

# === Auto-refresh ===
st_autorefresh(interval=2000, limit=None, key="datarefresh")

# === Read and parse serial lines ===
lines = read_serial_lines()
for line in lines:
    match = pattern.match(line)
    if match:
        gd = match.groupdict()
        timestamp = datetime.now(MALAYSIA).strftime("%Y-%m-%d %H:%M:%S")
        entry = {
            "timestamp": timestamp,
            "temp": safe_float(gd["temp"]),
            "hum": safe_float(gd["hum"]),
            "hr": safe_int(gd["hr"]),
            "spo2": safe_int(gd["spo2"]),
            "ax": safe_float(gd["ax"]),
            "ay": safe_float(gd["ay"]),
            "az": safe_float(gd["az"]),
            "gx": safe_float(gd["gx"]),
            "gy": safe_float(gd["gy"]),
            "gz": safe_float(gd["gz"])
        }
        st.session_state.data.append(entry)
        upload_to_bigquery(entry)
        debug_expander.success(f"Parsed data appended: {entry}")
    else:
        st.session_state.invalid_lines.append({
            "timestamp": datetime.now(MALAYSIA).strftime("%Y-%m-%d %H:%M:%S"),
            "line": line
        })
        debug_expander.warning(f"Ignored invalid line: {line}")

# === Display valid sensor data ===
df = pd.DataFrame(st.session_state.data)
st.markdown("## 🗃️ Logged Sensor Data")
if df.empty:
    st.info("No valid sensor data received yet. Waiting for complete data lines...")
else:
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df.sort_values("timestamp", ascending=False, inplace=True)
    st.dataframe(df.head(100).reset_index(drop=True), use_container_width=True)

# === Display unmatched lines ===
st.markdown("## ⚠️ Unmatched Sensor Lines")
if st.session_state.invalid_lines:
    invalid_df = pd.DataFrame(st.session_state.invalid_lines)
    invalid_df["timestamp"] = pd.to_datetime(invalid_df["timestamp"])
    invalid_df.sort_values("timestamp", ascending=False, inplace=True)
    st.dataframe(invalid_df.head(20).reset_index(drop=True), use_container_width=True)
else:
    st.info("No unmatched lines received yet.")

# === Gauges ===
if not df.empty:
    last = df.iloc[0]
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.plotly_chart(create_gauge(last.get("temp"), "Temperature", 20, 45, "°C"), use_container_width=True)
    with col2:
        st.plotly_chart(create_gauge(last.get("hr"), "Heart Rate", 30, 180, "BPM"), use_container_width=True)
    with col3:
        st.plotly_chart(create_gauge(last.get("spo2"), "SpO2", 70, 100, "%"), use_container_width=True)

# === Trend charts ===
if not df.empty:
    st.markdown("## 📈 Trends (last 100 samples)")
    trend_df = df.head(100).set_index("timestamp")
    try:
        trend_df.index = pd.to_datetime(trend_df.index)
    except:
        pass
    cols = st.columns(3)
    with cols[0]:
        st.line_chart(trend_df[["temp"]])
    with cols[1]:
        st.line_chart(trend_df[["hr"]])
    with cols[2]:
        st.line_chart(trend_df[["spo2"]])