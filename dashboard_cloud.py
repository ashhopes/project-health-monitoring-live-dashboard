import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import numpy as np
from datetime import datetime
import pytz
from collections import deque

# --- Page setup ---
st.set_page_config(page_title="Live Health Monitoring System with LoRa", layout="wide")
st.set_page_config(
    page_title="STEMCUBE REAL-TIME MONITOR",
    page_icon="🏥",
    layout="wide"
)

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
    .send-data-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
# --- MUJI + OLIVE MARROON THEME ---
st.markdown(f"""
<style>
    /* MUJI + OLIVE MARROON COLOR PALETTE */
    :root {{
        --muji-maroon: #8B4513;
        --olive-green: #556B2F;
        --champagne: #F7E7CE;
        --soft-beige: #F5F5DC;
        --dark-chocolate: #3C2F2F;
        --cream: #FFFDD0;
        --warm-brown: #A0522D;
        --earth-green: #6B8E23;
    }}
    
    .stApp {{
        background: linear-gradient(135deg, var(--soft-beige) 0%, var(--cream) 100%);
        font-family: 'Segoe UI', 'Arial', sans-serif;
    }}
    
    .main-header {{
        background: linear-gradient(135deg, var(--muji-maroon) 0%, var(--olive-green) 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .metric-card {
        border-radius: 15px;
        margin-bottom: 25px;
        box-shadow: 0 6px 20px rgba(139, 69, 19, 0.3);
        text-align: center;
        position: relative;
    }}
    
    .metric-card {{
        background: linear-gradient(135deg, white 0%, var(--champagne) 100%);
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(85, 107, 47, 0.15);
        border-left: 4px solid var(--olive-green);
        margin-bottom: 15px;
        transition: all 0.3s ease;
    }}
    
    .metric-card:hover {{
        transform: translateY(-3px);
        box-shadow: 0 6px 16px rgba(85, 107, 47, 0.2);
    }}
    
    .graph-container {{
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(139, 69, 19, 0.15);
        border-top: 4px solid var(--muji-maroon);
        margin-bottom: 20px;
    }}
    
    .sidebar-section {{
        background: linear-gradient(135deg, var(--champagne) 0%, white 100%);
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(139, 69, 19, 0.15);
        margin-bottom: 20px;
        border: 2px solid var(--soft-beige);
    }}
    
    .metric-value {{
        font-size: 32px;
        font-weight: 700;
        color: var(--dark-chocolate);
        margin: 5px 0;
    }}
    
    .metric-label {{
        font-size: 13px;
        color: var(--olive-green);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    
    .user-selector {{
        background: linear-gradient(135deg, var(--champagne) 0%, white 100%);
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
        margin: 5px;
        border-radius: 12px;
        margin-bottom: 20px;
        border: 2px solid var(--muji-maroon);
    }}
    
    .status-normal {{
        background: linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%);
        color: white;
        padding: 6px 14px;
        border-radius: 18px;
        font-weight: 600;
        display: inline-block;
        font-size: 13px;
    }}
    
    .status-warning {{
        background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%);
        color: white;
        padding: 6px 14px;
        border-radius: 18px;
        font-weight: 600;
        display: inline-block;
        font-size: 13px;
    }}
    
    .status-critical {{
        background: linear-gradient(135deg, #F44336 0%, #D32F2F 100%);
        color: white;
        padding: 6px 14px;
        border-radius: 18px;
        font-weight: 600;
        display: inline-block;
        font-size: 13px;
    }}
</style>
""", unsafe_allow_html=True)

# ================ INITIALIZE DATA BUFFERS ================
def init_session_state():
    """Initialize all session state variables"""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        current_time = datetime.now()
        
        # All sensor data buffers
        st.session_state.hr_data = deque([75, 76, 74, 77, 75, 76, 78, 76, 75, 74], maxlen=50)
        st.session_state.spo2_data = deque([98, 97, 98, 96, 97, 98, 97, 98, 99, 98], maxlen=50)
        st.session_state.temp_data = deque([36.5, 36.6, 36.5, 36.7, 36.6, 36.5, 36.6, 36.7, 36.5, 36.6], maxlen=50)
        st.session_state.humidity_data = deque([45.0, 46.0, 44.5, 47.0, 45.5, 46.0, 45.0, 47.0, 46.0, 45.5], maxlen=50)
        
        # Movement sensors (accelerometer)
        st.session_state.ax_data = deque([0.1, 0.2, -0.1, 0.3, 0.0, -0.2, 0.1, 0.4, -0.1, 0.2], maxlen=50)
        st.session_state.ay_data = deque([0.0, 0.1, 0.2, -0.1, 0.3, 0.1, -0.2, 0.0, 0.1, 0.2], maxlen=50)
        st.session_state.az_data = deque([9.8, 9.7, 9.8, 9.6, 9.8, 9.7, 9.9, 9.8, 9.7, 9.8], maxlen=50)
        
        # Gyroscope sensors
        st.session_state.gx_data = deque([1.2, 1.5, -1.0, 2.0, 0.8, -1.5, 1.0, 2.5, -0.5, 1.8], maxlen=50)
        st.session_state.gy_data = deque([-0.5, 0.2, 0.8, -0.3, 1.0, 0.5, -0.8, 0.0, 0.3, 0.7], maxlen=50)
        st.session_state.gz_data = deque([0.1, 0.3, -0.2, 0.5, 0.0, -0.4, 0.2, 0.6, -0.1, 0.4], maxlen=50)
        
        st.session_state.timestamps = deque([current_time - timedelta(seconds=i) for i in range(10)][::-1], maxlen=50)
        
        # User selection
        st.session_state.selected_user = "STEMCUBE_001"
        
        # Store complete records
        st.session_state.all_data = deque([
            {
                'timestamp': current_time - timedelta(seconds=i),
                'user': 'STEMCUBE_001',
                'hr': 75 + np.random.randint(-3, 3),
                'spo2': 97 + np.random.randint(-1, 2),
                'temp': 36.5 + np.random.uniform(-0.2, 0.2),
                'humidity': 45 + np.random.uniform(-2, 2),
                'ax': np.random.uniform(-0.5, 0.5),
                'ay': np.random.uniform(-0.5, 0.5),
                'az': 9.8 + np.random.uniform(-0.1, 0.1),
                'gx': np.random.uniform(-3, 3),
                'gy': np.random.uniform(-3, 3),
                'gz': np.random.uniform(-1, 1),
                'activity': ['RESTING', 'WALKING', 'RUNNING'][i % 3]
            }
            for i in range(10)
        ], maxlen=50)

# ================ DISPLAY HEADER ================
def display_header():
    """Display header with Malaysia time"""
    malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
    current_time_malaysia = datetime.now(malaysia_tz)
    
    st.markdown(f"""
    <div class="main-header">
        <div style="margin-left: 80px;">
            <h1 style="margin: 0; font-size: 2.2rem; font-weight: 700;">🏥 STEMCUBE REAL-TIME MONITOR</h1>
            <p style="margin: 8px 0 0 0; font-size: 1.1rem; opacity: 0.95;">
                📍 Universiti Malaysia Pahang • 🎓 Final Year Project 2025
            </p>
            <p style="margin: 5px 0 0 0; font-size: 0.95rem; opacity: 0.85;">
                🇲🇾 Malaysia Time: <strong>{current_time_malaysia.strftime('%I:%M:%S %p')}</strong> • 
                📅 Date: {current_time_malaysia.strftime('%d %B %Y')}
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ================ DEMO DATA GENERATOR ================
def get_demo_data():
    """Generate demo data for testing - ALL SENSORS"""
    current_time = datetime.now()
    
    # Simulate different activities
    activity_choice = np.random.choice(['RESTING', 'WALKING', 'RUNNING'], p=[0.5, 0.3, 0.2])
    
    # Health sensors (MAX30102)
    if activity_choice == 'RESTING':
        hr = np.random.randint(60, 80)
        spo2 = np.random.randint(96, 100)
        ax, ay, az = np.random.uniform(-0.2, 0.2, 3)
        gx, gy, gz = np.random.uniform(-5, 5, 3)
    elif activity_choice == 'WALKING':
        hr = np.random.randint(75, 95)
        spo2 = np.random.randint(94, 98)
        ax, ay, az = np.random.uniform(-1.0, 1.0, 3)
        gx, gy, gz = np.random.uniform(-15, 15, 3)
    else:  # RUNNING
        hr = np.random.randint(90, 110)
        spo2 = np.random.randint(92, 97)
        ax, ay, az = np.random.uniform(-2.0, 2.0, 3)
        gx, gy, gz = np.random.uniform(-30, 30, 3)
    
    # BME280 sensors
    temp = np.random.uniform(36.2, 36.8)
    humidity = np.random.uniform(40, 50)
    
    return {
        'timestamp': current_time,
        'user': st.session_state.selected_user,
        'hr': int(hr),
        'spo2': int(spo2),
        'temp': round(temp, 1),
        'humidity': round(humidity, 1),
        'ax': round(ax, 3),
        'ay': round(ay, 3),
        'az': round(az, 3),
        'gx': round(gx, 2),
        'gy': round(gy, 2),
        'gz': round(gz, 2),
        'activity': activity_choice,
        'is_real': False
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Header ---
st.markdown("<h1 style='text-align: center; color:#4B0082;'>🏥 Live Health Monitoring System with LoRa</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Real-time monitoring of vital signs and motion data using LoRa sensors</p>", unsafe_allow_html=True)
st.markdown("---")

# ================== NEW: DATA SENDING FUNCTIONALITY ==================

# --- Sidebar controls ---
with st.sidebar:
    st.header("⚙️ Controls")
# ================ UPDATE DATA BUFFERS ================
def update_data_buffers(data):
    """Update all data buffers"""
    st.session_state.timestamps.append(data['timestamp'])
    
    # Mode selection
    mode = st.radio("Operation Mode:", ["Live Monitoring", "Send Data"])
    # Health sensors
    st.session_state.hr_data.append(data['hr'])
    st.session_state.spo2_data.append(data['spo2'])
    st.session_state.temp_data.append(data['temp'])
    st.session_state.humidity_data.append(data['humidity'])
    
    refresh_rate = st.slider("Auto-refresh every (seconds)", 0, 120, 30)
    n_samples = st.slider("Number of samples to display", 50, 500, 100)
    st.sidebar.info("Project by mOONbLOOM26 🌙")
    # Movement sensors
    st.session_state.ax_data.append(data['ax'])
    st.session_state.ay_data.append(data['ay'])
    st.session_state.az_data.append(data['az'])
    
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
    # Gyroscope sensors
    st.session_state.gx_data.append(data['gx'])
    st.session_state.gy_data.append(data['gy'])
    st.session_state.gz_data.append(data['gz'])
    
    # Store complete record
    st.session_state.all_data.append(data)

# ================ GRAPH FUNCTIONS ================
def create_multi_sensor_graph(title, sensors_data, colors, labels):
    """Create graph with multiple sensor lines"""
    if len(st.session_state.timestamps) == 0:
        return None
    
    n_points = min(20, len(st.session_state.timestamps))
    
    fig = go.Figure()
    
    for i, (data, color, label) in enumerate(zip(sensors_data, colors, labels)):
        fig.add_trace(go.Scatter(
            x=list(st.session_state.timestamps)[-n_points:],
            y=list(data)[-n_points:],
            mode='lines',
            name=label,
            line=dict(color=color, width=2),
            yaxis=f'y{i+1}' if i > 0 else 'y'
        ))
    
    # Update layout with multiple y-axes
    fig.update_layout(
        title={'text': title, 'font': {'size': 16, 'color': '#3C2F2F'}},
        height=300,
        margin=dict(l=50, r=50, t=50, b=50),
        xaxis_title="Time",
        plot_bgcolor='rgba(255, 253, 208, 0.1)',
        paper_bgcolor='white',
        font=dict(family='Arial', size=12),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    # Add secondary y-axes if needed
    if len(sensors_data) > 1:
        for i in range(1, len(sensors_data)):
            fig.update_layout({
                f'yaxis{i+1}': dict(
                    title=labels[i],
                    titlefont=dict(color=colors[i]),
                    tickfont=dict(color=colors[i]),
                    overlaying='y',
                    side='right' if i % 2 == 0 else 'left',
                    position=0.15 if i == 1 else 0.85
                )
            })
    
    return fig

# ================== NEW: SEND DATA TAB ==================
if mode == "Send Data":
    st.markdown("<div class='send-data-box'>", unsafe_allow_html=True)
    st.markdown("### 📤 Send Data to BigQuery")
    st.markdown("Generate and send simulated health data to the database")
# ================ TAB 1: HEALTH VITALS ================
def tab_health_vitals(current_data):
    """Tab 1: Health Vitals - ALL SENSORS"""
    
    # User selector in tab
    st.markdown("<div class='user-selector'>", unsafe_allow_html=True)
    col_user = st.columns([1, 2])
    with col_user[0]:
        st.markdown("### 👤 User Selection")
    with col_user[1]:
        # Radio buttons for user selection
        user_choice = st.radio(
            "Select User:",
            ["STEMCUBE_001", "STEMCUBE_002", "STEMCUBE_003"],
            horizontal=True,
            index=0
        )
        st.session_state.selected_user = user_choice
    
    # Update current data with selected user
    current_data['user'] = st.session_state.selected_user
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    # Activity display
    col_activity = st.columns([1, 2, 1])
    with col_activity[1]:
        activity = current_data['activity']
        emoji = "😴" if activity == 'RESTING' else "🚶" if activity == 'WALKING' else "🏃"
        activity_color = '#8B4513' if activity == 'RESTING' else '#556B2F' if activity == 'WALKING' else '#D4A76A'
        
        st.markdown(f"""
        <div style="text-align: center; padding: 15px; border-radius: 12px; 
                    background: linear-gradient(135deg, {activity_color}20 0%, white 100%);
                    border: 2px solid {activity_color}40;">
            <div style="font-size: 48px; margin: 10px 0;">{emoji}</div>
            <h2 style="color: {activity_color}; margin: 5px 0;">{activity}</h2>
            <p style="color: #666; font-size: 14px;">Detected by Master Cube</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Current Metrics - 2 rows
    st.markdown("### 📊 Current Sensor Readings")
    
    # Row 1: Health Sensors
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        subject_id = st.selectbox("Select Subject:", ["user_001", "user_002", "user_003"])
        activity = st.selectbox("Activity:", ["RESTING", "WALKING", "RUNNING"])
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        hr = current_data['hr']
        status_class = "status-normal" if 60 <= hr <= 100 else "status-warning" if 50 <= hr <= 110 else "status-critical"
        status = "NORMAL" if 60 <= hr <= 100 else "WARNING" if 50 <= hr <= 110 else "ALERT"
        
        if st.button("🎲 Generate Random Data", use_container_width=True):
            # Generate realistic data based on activity
            if activity == "RESTING":
                hr = np.random.randint(60, 80)
                spo2 = np.random.randint(96, 100)
                temp = np.random.uniform(36.2, 36.7)
                ax, ay, az = np.random.uniform(-0.2, 0.2, 3)
            elif activity == "WALKING":
                hr = np.random.randint(75, 95)
                spo2 = np.random.randint(94, 98)
                temp = np.random.uniform(36.5, 37.0)
                ax, ay, az = np.random.uniform(-1.0, 1.0, 3)
            else:  # RUNNING
                hr = np.random.randint(90, 110)
                spo2 = np.random.randint(92, 97)
                temp = np.random.uniform(36.8, 37.5)
                ax, ay, az = np.random.uniform(-2.0, 2.0, 3)
            
            # Generate gyroscope data
            gx, gy, gz = np.random.uniform(-50, 50, 3)
            
            st.session_state.generated_data = {
                'id_user': subject_id,
                'temp': round(temp, 1),
                'spo2': spo2,
                'hr': hr,
                'ax': round(ax, 3),
                'ay': round(ay, 3),
                'az': round(az, 3),
                'gx': round(gx, 2),
                'gy': round(gy, 2),
                'gz': round(gz, 2)
            }
        st.markdown(f"""
        <div style="text-align: center;">
            <div class="metric-label">HEART RATE</div>
            <div class="metric-value" style="color: {'#4CAF50' if 60 <= hr <= 100 else '#FF9800' if 50 <= hr <= 110 else '#F44336'};">{hr}</div>
            <div style="font-size: 14px; color: #666; margin: 5px 0;">BPM (MAX30102)</div>
            <div class="{status_class}">{status}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        if 'generated_data' in st.session_state:
            st.markdown("### Generated Data")
            data = st.session_state.generated_data
            
            # Display metrics in cards
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.markdown(f"<div class='metric-card'><h3>{data['hr']}</h3><p>Heart Rate</p></div>", unsafe_allow_html=True)
            with col_b:
                st.markdown(f"<div class='metric-card'><h3>{data['spo2']}%</h3><p>SpO₂</p></div>", unsafe_allow_html=True)
            with col_c:
                st.markdown(f"<div class='metric-card'><h3>{data['temp']}°C</h3><p>Temperature</p></div>", unsafe_allow_html=True)
            
            # Display all data
            st.json(data)
            
            if st.button("📤 Send to BigQuery", type="primary", use_container_width=True):
                try:
                    # Insert data into BigQuery
                    rows_to_insert = [{
                        'id_user': data['id_user'],
                        'timestamp': datetime.now(pytz.timezone('Asia/Kuala_Lumpur')).strftime('%Y-%m-%d %H:%M:%S'),
                        'temp': data['temp'],
                        'spo2': data['spo2'],
                        'hr': data['hr'],
                        'ax': data['ax'],
                        'ay': data['ay'],
                        'az': data['az'],
                        'gx': data['gx'],
                        'gy': data['gy'],
                        'gz': data['gz'],
                        'activity': activity
                    }]
                    
                    errors = client.insert_rows_json(table_id, rows_to_insert)
                    
                    if errors == []:
                        st.success(f"✅ Data sent successfully for {subject_id}!")
                        st.balloons()
                        del st.session_state.generated_data
                    else:
                        st.error(f"❌ Error sending data: {errors}")
                except Exception as e:
                    st.error(f"❌ Database error: {str(e)}")
    
    # Manual data entry option
    st.markdown("---")
    st.markdown("### ✏️ Manual Data Entry")
    
    with st.form("manual_data_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            manual_hr = st.number_input("Heart Rate (BPM)", 40, 200, 75)
            manual_temp = st.number_input("Temperature (°C)", 35.0, 42.0, 36.6)
        with col2:
            manual_spo2 = st.number_input("SpO₂ (%)", 80, 100, 98)
            manual_ax = st.number_input("Accel X", -5.0, 5.0, 0.1)
        with col3:
            manual_ay = st.number_input("Accel Y", -5.0, 5.0, 0.2)
            manual_az = st.number_input("Accel Z", -5.0, 5.0, 0.3)
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        spo2 = current_data['spo2']
        status_class = "status-normal" if spo2 >= 95 else "status-warning" if spo2 >= 90 else "status-critical"
        status = "NORMAL" if spo2 >= 95 else "LOW" if spo2 >= 90 else "CRITICAL"
        
        manual_gx = st.number_input("Gyro X", -100.0, 100.0, 10.0)
        manual_gy = st.number_input("Gyro Y", -100.0, 100.0, 5.0)
        manual_gz = st.number_input("Gyro Z", -100.0, 100.0, 15.0)
        st.markdown(f"""
        <div style="text-align: center;">
            <div class="metric-label">BLOOD OXYGEN</div>
            <div class="metric-value" style="color: {'#4CAF50' if spo2 >= 95 else '#FF9800' if spo2 >= 90 else '#F44336'};">{spo2}%</div>
            <div style="font-size: 14px; color: #666; margin: 5px 0;">SpO₂ (MAX30102)</div>
            <div class="{status_class}">{status}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col3:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        temp = current_data['temp']
        status_class = "status-normal" if temp <= 37.5 else "status-warning" if temp <= 38.5 else "status-critical"
        status = "NORMAL" if temp <= 37.5 else "ELEVATED" if temp <= 38.5 else "FEVER"
        
        if st.form_submit_button("📤 Send Manual Data"):
            try:
                rows_to_insert = [{
                    'id_user': subject_id,
                    'timestamp': datetime.now(pytz.timezone('Asia/Kuala_Lumpur')).strftime('%Y-%m-%d %H:%M:%S'),
                    'temp': manual_temp,
                    'spo2': manual_spo2,
                    'hr': manual_hr,
                    'ax': manual_ax,
                    'ay': manual_ay,
                    'az': manual_az,
                    'gx': manual_gx,
                    'gy': manual_gy,
                    'gz': manual_gz,
                    'activity': activity
                }]
                
                errors = client.insert_rows_json(table_id, rows_to_insert)
                
                if errors == []:
                    st.success("✅ Manual data sent successfully!")
                else:
                    st.error(f"❌ Error: {errors}")
            except Exception as e:
                st.error(f"❌ Database error: {str(e)}")

else:  # ================== LIVE MONITORING MODE ==================
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
                col1.markdown(f"*Average HR:* <span style='color:#c0392b;'><b>{df['hr'].mean():.1f} BPM</b></span>", unsafe_allow_html=True)
                col2.markdown(f"*minSpO₂:* <span style='color:#27ae60;'><b>{df['spo2'].min():.1f} %</b></span>", unsafe_allow_html=True)
                col3.markdown(f"*Average Temp:* <span style='color:#e67e22;'><b>{df['temp'].mean():.1f} °C</b></span>", unsafe_allow_html=True)
                col4.markdown(f"*maxTemp:* <span style='color:#e74c3c;'><b>{df['temp'].max():.1f} °C</b></span>", unsafe_allow_html=True)
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
        st.markdown(f"""
        <div style="text-align: center;">
            <div class="metric-label">BODY TEMP</div>
            <div class="metric-value" style="color: {'#4CAF50' if temp <= 37.5 else '#FF9800' if temp <= 38.5 else '#F44336'};">{temp}°C</div>
            <div style="font-size: 14px; color: #666; margin: 5px 0;">(MAX30102)</div>
            <div class="{status_class}">{status}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col4:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        humidity = current_data['humidity']
        
        st.markdown(f"""
        <div style="text-align: center;">
            <div class="metric-label">HUMIDITY</div>
            <div class="metric-value" style="color: #3498db;">{humidity}%</div>
            <div style="font-size: 14px; color: #666; margin: 5px 0;">Environment (BME280)</div>
            <div style="margin-top: 10px;">
                <div style="background: #F5F5DC; height: 8px; border-radius: 4px; overflow: hidden;">
                    <div style="background: linear-gradient(90deg, #3498db, #2980b9); 
                                width: {min(100, humidity)}%; height: 100%;"></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Row 2: Movement Sensors
    col5, col6, col7, col8 = st.columns(4)
    
    with col5:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        ax = current_data['ax']
        st.markdown(f"""
        <div style="text-align: center;">
            <div class="metric-label">ACCELEROMETER X</div>
            <div class="metric-value" style="color: #8B4513;">{ax}</div>
            <div style="font-size: 14px; color: #666; margin: 5px 0;">(g) Movement</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col6:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        ay = current_data['ay']
        st.markdown(f"""
        <div style="text-align: center;">
            <div class="metric-label">ACCELEROMETER Y</div>
            <div class="metric-value" style="color: #556B2F;">{ay}</div>
            <div style="font-size: 14px; color: #666; margin: 5px 0;">(g) Movement</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col7:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        az = current_data['az']
        st.markdown(f"""
        <div style="text-align: center;">
            <div class="metric-label">ACCELEROMETER Z</div>
            <div class="metric-value" style="color: #A0522D;">{az}</div>
            <div style="font-size: 14px; color: #666; margin: 5px 0;">(g) Gravity</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col8:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        movement = np.sqrt(current_data['ax']**2 + current_data['ay']**2 + current_data['az']**2)
        st.markdown(f"""
        <div style="text-align: center;">
            <div class="metric-label">TOTAL MOVEMENT</div>
            <div class="metric-value" style="color: #D4A76A;">{movement:.2f}</div>
            <div style="font-size: 14px; color: #666; margin: 5px 0;">Vector Magnitude</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Real-time Graphs
    st.markdown("### 📈 Real-time Sensor Monitoring")
    
    # Graph 1: Health Sensors
    st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
    st.markdown("#### ❤️ Health Sensors (MAX30102)")
    
    health_fig = create_multi_sensor_graph(
        "Heart Rate & SpO₂",
        [st.session_state.hr_data, st.session_state.spo2_data],
        ['#8B4513', '#556B2F'],
        ['Heart Rate (BPM)', 'SpO₂ (%)']
    )
    if health_fig:
        st.plotly_chart(health_fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Graph 2: Accelerometer
    st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
    st.markdown("#### 📍 Accelerometer (AX, AY, AZ)")
    
    accel_fig = create_multi_sensor_graph(
        "Accelerometer Data",
        [st.session_state.ax_data, st.session_state.ay_data, st.session_state.az_data],
        ['#8B4513', '#556B2F', '#A0522D'],
        ['AX (g)', 'AY (g)', 'AZ (g)']
    )
    if accel_fig:
        st.plotly_chart(accel_fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Graph 3: Gyroscope
    st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
    st.markdown("#### 🌀 Gyroscope (GX, GY, GZ)")
    
    gyro_fig = create_multi_sensor_graph(
        "Gyroscope Data",
        [st.session_state.gx_data, st.session_state.gy_data, st.session_state.gz_data],
        ['#8B4513', '#556B2F', '#A0522D'],
        ['GX (deg/s)', 'GY (deg/s)', 'GZ (deg/s)']
    )
    if gyro_fig:
        st.plotly_chart(gyro_fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

                    sub_pred = pred_df[pred_df['id_user'] == sid]
                    if sub_pred.empty:
                        st.warning(f"No predictions found for Subject {sid}")
                    else:
                        # Show prediction table
                        st.dataframe(sub_pred, use_container_width=True)
# ================ TAB 2: DATA LOG ================
def tab_data_log():
    """Tab 2: Data Log - Live Data Table"""
    
    st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
    st.markdown("### 📋 Live Data Log")
    
    if len(st.session_state.all_data) > 0:
        all_data_list = list(st.session_state.all_data)
        n_items = min(10, len(all_data_list))
        
        table_data = []
        for i in range(1, n_items + 1):
            record = all_data_list[-i]
            table_data.append({
                'Time': record['timestamp'].strftime('%H:%M:%S'),
                'User': record['user'],
                'HR': record['hr'],
                'SpO₂': f"{record['spo2']}%",
                'Temp': f"{record['temp']}°C",
                'Humidity': f"{record['humidity']}%",
                'AX': f"{record['ax']:.3f}",
                'AY': f"{record['ay']:.3f}",
                'AZ': f"{record['az']:.3f}",
                'GX': f"{record['gx']:.2f}",
                'GY': f"{record['gy']:.2f}",
                'GZ': f"{record['gz']:.2f}",
                'Activity': record['activity'],
                'Source': '📡 REAL' if record.get('is_real', False) else '💻 DEMO'
            })
        
        table_data.reverse()
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, height=400)
    else:
        st.info("No data available yet")
    
    st.markdown("</div>", unsafe_allow_html=True)

                        # Show bar chart of cluster counts
                        cluster_counts = sub_pred.groupby("predicted_cluster").size()
                        st.bar_chart(cluster_counts)
# ================ MAIN DASHBOARD ================
def main():
    """Main dashboard function"""
    
    # Initialize session state
    init_session_state()
    
    # Display header
    display_header()
    
    # Sidebar
    with st.sidebar:
        st.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
        st.markdown("### ⚙️ Control Panel")
        
        auto_refresh = st.toggle("🔄 Auto Refresh", value=True)
        refresh_rate = st.slider("Refresh Rate (seconds)", 1, 10, 2)
        
        if st.button("🔄 Manual Refresh", use_container_width=True):
            st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
        st.markdown("### 📊 Current Readings")
        
        current_data = get_demo_data()
        
        col_sb1, col_sb2 = st.columns(2)
        with col_sb1:
            st.metric("❤️ HR", f"{current_data['hr']} BPM")
            st.metric("🌡️ Temp", f"{current_data['temp']:.1f}°C")
            st.metric("📍 AX", f"{current_data['ax']:.3f}")
        with col_sb2:
            st.metric("🩸 SpO₂", f"{current_data['spo2']}%")
            st.metric("🏃 Activity", current_data['activity'])
            st.metric("🌀 GX", f"{current_data['gx']:.2f}")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
        st.markdown("### 🔌 System Info")
        
        st.write(f"**User:** {st.session_state.selected_user}")
        st.write(f"**Samples:** {len(st.session_state.all_data)}")
        st.write(f"**Last Update:** {datetime.now().strftime('%H:%M:%S')}")
        st.write("**Status:** 💻 Demo Mode Active")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Update data buffers
    update_data_buffers(current_data)
    
    # TABS - 2 TABS ONLY
    tab1, tab2 = st.tabs(["🩺 Sensor Dashboard", "📋 Data Log"])
    
    with tab1:
        tab_health_vitals(current_data)
    
    with tab2:
        tab_data_log()
    
    # Auto-refresh
    if auto_refresh:
        time.sleep(refresh_rate)
        st.rerun()

                    st.markdown("</div>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"❌ Error fetching data: {e}")
# ================ RUN DASHBOARD ================
if __name__ == "__main__":
    main()