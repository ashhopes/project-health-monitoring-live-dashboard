import serial
import pandas as pd
import re
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objects as go
import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account

# --- BigQuery Authentication ---
credentials = service_account.Credentials.from_service_account_info(st.secrets["gcp"])
client = bigquery.Client(credentials=credentials, project=st.secrets["gcp"]["project_id"])
table_id = "monitoring-system-with-lora.sdp2_live_monitoring.lora_health_data_clean2"

# --- Serial Configuration ---
SERIAL_PORT = 'COM8'   # Change as needed
BAUD_RATE = 9600

# --- Upload Function ---
def upload_to_bigquery(entry):
    try:
        df = pd.DataFrame([entry])
        job = client.load_table_from_dataframe(df, table_id)
        job.result()
        debug_expander.success("✅ Uploaded to BigQuery (lora_health_data_clean2)")
    except Exception as e:
        debug_expander.error(f"❌ Upload failed: {e}")

# --- Page Setup ---
st.set_page_config(page_title="Health Monitoring Dashboard", layout="wide")

# --- Background Style ---
st.markdown(
    """
    <style>
    .stApp {
        background-image: url("md.gif");
        background-attachment: fixed;
        background-size: cover;
        background-position: center;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Sidebar Debug ---
debug_expander = st.sidebar.expander("Serial Debug", expanded=True)

# --- Title ---
st.markdown(
    """
    <div style="text-align: center;">
        <h2>🧠 Health Monitoring System with LoRa</h2>
        <h4>Real-time Body Sensor Data Visualization</h4>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- Initialize Serial Port ---
if "ser" not in st.session_state:
    try:
        st.session_state.ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.5)
        debug_expander.success(f"Connected to {SERIAL_PORT} @ {BAUD_RATE} baud")
    except Exception as e:
        debug_expander.error(f"Error opening serial port {SERIAL_PORT}: {e}")
        st.stop()

# --- Regex Pattern ---
pattern = re.compile(
    r"^T:(?P<temp>[\d\.]+),H:(?P<hum>[\d\.]+),HR:(?P<hr>\d+|--),SpO2:(?P<spo2>\d+|--),"
    r"ax:(?P<ax>-?[\d\.]+),ay:(?P<ay>-?[\d\.]+),az:(?P<az>-?[\d\.]+),"
    r"gx:(?P<gx>-?[\d\.]+),gy:(?P<gy>-?[\d\.]+),gz:(?P<gz>-?[\d\.]+)$"
)

# --- Session State ---
if "data" not in st.session_state:
    st.session_state.data = []
if "invalid_lines" not in st.session_state:
    st.session_state.invalid_lines = []

# --- Utility Functions ---
def safe_float(val):
    try:
        return float(val)
    except:
        return None

def safe_int(val):
    try:
        return int(val)
    except:
        return None

def read_serial_lines():
    lines = []
    ser = st.session_state.ser
    try:
        while getattr(ser, "in_waiting", 0) and ser.in_waiting > 0:
            raw = ser.readline().decode('utf-8', errors='replace').strip()
            if not raw:
                continue
            if raw.lower().startswith("received:"):
                raw = raw.split(":", 1)[1].strip()
                debug_expander.write(f"Stripped prefix -> {raw}")
            else:
                debug_expander.write(f"Raw -> {raw}")
            lines.append(raw)
    except Exception as e:
        debug_expander.error(f"Serial read error: {e}")
    return lines

# --- Auto-refresh ---
st_autorefresh(interval=2000, limit=None, key="datarefresh")

# --- Read and Parse Serial Lines ---
lines = read_serial_lines()
for line in lines:
    match = pattern.match(line)
    if match:
        gd = match.groupdict()
        entry = {
            "ID_user": "user01",  # Add user ID here
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "temp": safe_float(gd.get("temp")),
            "humidity": safe_float(gd.get("hum")),
            "hr": safe_int(gd.get("hr")) if gd.get("hr") != "--" else None,
            "spo2": safe_int(gd.get("spo2")) if gd.get("spo2") != "--" else None,
            "ax": safe_float(gd.get("ax")),
            "ay": safe_float(gd.get("ay")),
            "az": safe_float(gd.get("az")),
            "gx": safe_float(gd.get("gx")),
            "gy": safe_float(gd.get("gy")),
            "gz": safe_float(gd.get("gz"))
        }
        st.session_state.data.append(entry)
        upload_to_bigquery(entry)
        debug_expander.success(f"Parsed data appended: {entry}")
    else:
        st.session_state.invalid_lines.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "line": line
        })
        debug_expander.warning(f"Ignored invalid line: {line}")

# --- Display Valid Sensor Data ---
df = pd.DataFrame(st.session_state.data)
st.markdown("## 🗃️ Logged Sensor Data")
if df.empty:
    st.info("No valid sensor data received yet. Waiting for complete data lines...")
else:
    st.dataframe(df.tail(100), use_container_width=True)

# --- Display Unmatched Lines ---
st.markdown("## ⚠️ Unmatched Sensor Lines")
if st.session_state.invalid_lines:
    invalid_df = pd.DataFrame(st.session_state.invalid_lines)
    st.dataframe(invalid_df.tail(20), use_container_width=True)
else:
    st.info("No unmatched lines received yet.")

# --- Gauges ---
if not df.empty:
    last = df.iloc[-1]
    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        st.plotly_chart(go.Figure(go.Indicator(
            mode="gauge+number",
            value=last.get("temp") or 0,
            title={'text': "Temperature (°C)"},
            gauge={'axis': {'range': [20, 45]}}
        )), use_container_width=True)
    with col2:
        st.plotly_chart(go.Figure(go.Indicator(
            mode="gauge+number",
            value=last.get("hr") or 0,
            title={'text': "Heart Rate (BPM)"},
            gauge={'axis': {'range': [30, 180]}}
        )), use_container_width=True)
    with col3:
        st.plotly_chart(go.Figure(go.Indicator(
            mode="gauge+number",
            value=last.get("spo2") or 0,
            title={'text': "SpO₂ (%)"},
            gauge={'axis': {'range': [70, 100]}}
        )), use_container_width=True)

# --- Trend Charts ---
if not df.empty:
    st.markdown("## 📈 Trends (last 100 samples)")
    trend_df = df.tail(100).set_index("timestamp")
    try:
        trend_df.index = pd.to_datetime(trend_df.index)
    except:
        pass

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=trend_df.index, y=trend_df["temp"], mode="lines+markers",
                             name="Temperature (°C)", line=dict(color="orange")))
    fig.add_trace(go.Scatter(x=trend_df.index, y=trend_df["humidity"], mode="lines+markers",
                             name="Humidity (%)", line=dict(color="blue")))
    fig.add_trace(go.Scatter(x=trend_df.index, y=trend_df["hr"], mode="lines+markers",
                             name="Heart Rate (BPM)", line=dict(color="red")))
    fig.add_trace(go.Scatter(x=trend_df.index, y=trend_df["spo2"], mode="lines+markers",
                             name="SpO₂ (%)", line=dict(color="green")))

    fig.update_layout(
        title="Sensor Trends (last 100 samples)",
        xaxis_title="Timestamp",
        yaxis_title="Values",
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
        height=500
    )

    st.plotly_chart(fig, use_container_width=True)

    
    
if st.button("Test BigQuery Upload"):
    test_entry = {
        "ID_user": "test_user",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "temp": 36.6,
        "humidity": 50.0,
        "spo2": 97,
        "hr": 75,
        "ax": 0.01,
        "ay": -0.02,
        "az": 0.98,
        "gx": 0.12,
        "gy": -0.05,
        "gz": 0.03
    }
    upload_to_bigquery(test_entry)