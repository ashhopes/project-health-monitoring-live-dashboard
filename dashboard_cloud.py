import serial
import pandas as pd
import re
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objects as go
# === Configuration ===
SERIAL_PORT = 'COM5' # Change as needed
BAUD_RATE = 9600
IMAGE_PATH = "human_anatomy_front.png" # Change to your image path or URL
# === Page setup ===
st.set_page_config(page_title="Health Monitoring Dashboard", layout="wide")
# === Centered Title and Subtitle ===
st.markdown(
"""
<div style="text-align: center;">
<h2>🧠 Health Monitoring System with LoRa</h2>
<h4>Real-time Body Sensor Data Visualization</h4>
</div>
""",
unsafe_allow_html=True
)
# === Initialize serial port once ===
if "ser" not in st.session_state:
try:
st.session_state.ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.5)
st.sidebar.success(f"Connected to {SERIAL_PORT}")
except Exception as e:
st.sidebar.error(f"Error opening serial port: {e}")
st.stop()
# === Regex pattern for expected sensor data format ===
pattern = re.compile(
r"^T:(?P<temp>[\d\.]+),H:(?P<hum>[\d\.]+),HR:(?P<hr>\d+|--),SpO2:(?P<spo2>\d+|--),"
r"ax:(?P<ax>-?[\d\.]+),ay:(?P<ay>-?[\d\.]+),az:(?P<az>-?[\d\.]+),"
r"gx:(?P<gx>-?[\d\.]+),gy:(?P<gy>-?[\d\.]+),gz:(?P<gz>-?[\d\.]+)$"
)
if "data" not in st.session_state:
st.session_state.data = []
def safe_float(val):
try:

47

return float(val)
except:
return None
def safe_int(val):
try:
return int(val)
except:
return None
def read_serial_lines():
"""Read all available lines from serial buffer."""
lines = []
ser = st.session_state.ser
while ser.in_waiting:
try:
line = ser.readline().decode('utf-8').strip()
if line:
lines.append(line)
except Exception as e:
st.sidebar.error(f"Serial read error: {e}")
break
return lines
def create_gauge(value, title, min_val, max_val, units, thresholds=None):
if thresholds is None:
thresholds = []
color = 'green'
for threshold_val, threshold_color in thresholds:
if value <= threshold_val:
color = threshold_color
break
fig = go.Figure(go.Indicator(
mode="gauge+number",
value=value,
domain={'x': [0, 1], 'y': [0, 1]},
title={'text': title},
number={'suffix': units},
gauge={
'axis': {'range': [min_val, max_val]},
'bar': {'color': color},
'steps': [{'range': [min_val, max_val], 'color': "#e6e6e6"}],
}
))
fig.update_layout(height=280, margin=dict(t=40, b=0, l=0, r=0))
return fig
# === Auto-refresh every 2 seconds ===
st_autorefresh(interval=2000, limit=None, key="datarefresh")

48

# === Read all available serial lines and parse latest valid ===
lines = read_serial_lines()
for line in lines:
if line.startswith("Received: "):
line = line[len("Received: "):].strip()
match = pattern.match(line)
if match:
now = datetime.now().strftime("%H:%M:%S")
temp = safe_float(match.group("temp"))
hum = safe_float(match.group("hum"))
hr_raw = match.group("hr")
spo2_raw = match.group("spo2")
hr = safe_int(hr_raw) if hr_raw != '--' else None
spo2 = safe_int(spo2_raw) if spo2_raw != '--' else None
ax = safe_float(match.group("ax"))
ay = safe_float(match.group("ay"))
az = safe_float(match.group("az"))
gx = safe_float(match.group("gx"))
gy = safe_float(match.group("gy"))
gz = safe_float(match.group("gz"))
# Validate sensor values
if temp is not None and not (0 <= temp <= 60):
temp = None
if hum is not None and not (0 <= hum <= 100):
hum = None
if hr is not None and not (30 <= hr <= 180):
hr = None
if spo2 is not None and not (50 <= spo2 <= 100):
spo2 = None
st.session_state.data.append({
"Time": now,
"Temperature (°C)": temp,
"Humidity (%)": hum,
"Heart Rate (bpm)": hr,
"SpO2 (%)": spo2,
"ax": ax, "ay": ay, "az": az,
"gx": gx, "gy": gy, "gz": gz,
})
if len(st.session_state.data) > 100:
st.session_state.data = st.session_state.data[-100:]
df = pd.DataFrame(st.session_state.data)
# === Logged data table (full width) ===
st.markdown("## ️ Logged Sensor Data")
if df.empty:

49

st.info("No valid sensor data received yet. Waiting for complete data
lines...")
else:
st.dataframe(df.iloc[::-1].reset_index(drop=True), use_container_width=True,
height=400)
csv = df.to_csv(index=False).encode('utf-8')
st.download_button(
label="Download CSV",
data=csv,
file_name='sensor_data.csv',
mime='text/csv',
)
# === Alerts and gauges with single image beside gauges ===
if not df.empty:
latest = df.iloc[-1]
st.markdown("---")
col_img, col_gauges = st.columns([1, 3])
with col_img:
st.image(IMAGE_PATH, caption="Human Anatomy", use_container_width=True)
with col_gauges:
if latest["Heart Rate (bpm)"] and latest["Heart Rate (bpm)"] > 120:
st.error(f"⚠️ High Heart Rate Alert: {latest['Heart Rate (bpm)']} bpm")
if latest["SpO2 (%)"] and latest["SpO2 (%)"] < 90:
st.error(f"⚠️ Low SpO2 Alert: {latest['SpO2 (%)']}%")
if latest["Temperature (°C)"] and latest["Temperature (°C)"] > 37.5:
st.warning(f"️ High Temperature Warning: {latest['Temperature (°C)']}
°C")
gauge_col1, gauge_col2, gauge_col3 = st.columns(3)
with gauge_col1:
st.plotly_chart(create_gauge(
latest["Temperature (°C)"] or 0,
"Temperature", 0, 60, "°C",
thresholds=[(33, 'red'), (25, 'yellow'), (0, 'green')]
), use_container_width=True)
with gauge_col2:
st.plotly_chart(create_gauge(
latest["SpO2 (%)"] or 0,
"SpO2", 50, 100, "%",
thresholds=[(89, 'red'), (94, 'yellow'), (100, 'green')]
), use_container_width=True)
with gauge_col3:
st.plotly_chart(create_gauge(
latest["Heart Rate (bpm)"] or 0,

50

"Heart Rate", 30, 180, "bpm",
thresholds=[(100, 'green'), (120, 'yellow'), (180, 'red')]
), use_container_width=True)
# === Trend charts ===
if not df.empty:
st.markdown("## 📈 Sensor Trends")
tab1, tab2, tab3 = st.tabs(["Vitals", "Environment", "Motion"])
with tab1:
vitals_df = df.set_index("Time")[["Heart Rate (bpm)", "SpO2 (%)"]].dropna()
if not vitals_df.empty:
st.line_chart(vitals_df)
else:
st.write("No Heart Rate or SpO2 data to display.")
with tab2:
env_df = df.set_index("Time")[["Temperature (°C)", "Humidity
(%)"]].dropna()
if not env_df.empty:
st.line_chart(env_df)
else:
st.write("No Temperature or Humidity data to display.")
with tab3:
accel_df = df.set_index("Time")[["ax", "ay", "az"]].dropna()
gyro_df = df.set_index("Time")[["gx", "gy", "gz"]].dropna()
if not accel_df.empty:
st.subheader("Accelerometer")
st.line_chart(accel_df)
else:
st.write("No Accelerometer data to display.")
if not gyro_df.empty:
st.subheader("Gyroscope")
st.line_chart(gyro_df)
else:
st.write("No Gyroscope data to display.")