import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import pytz
from collections import deque

# --- Page setup ---
st.set_page_config(
    page_title="STEMCUBE REAL-TIME MONITOR",
    page_icon="🏥",
    layout="wide"
)

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

# ================ UPDATE DATA BUFFERS ================
def update_data_buffers(data):
    """Update all data buffers"""
    st.session_state.timestamps.append(data['timestamp'])
    
    # Health sensors
    st.session_state.hr_data.append(data['hr'])
    st.session_state.spo2_data.append(data['spo2'])
    st.session_state.temp_data.append(data['temp'])
    st.session_state.humidity_data.append(data['humidity'])
    
    # Movement sensors
    st.session_state.ax_data.append(data['ax'])
    st.session_state.ay_data.append(data['ay'])
    st.session_state.az_data.append(data['az'])
    
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
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        hr = current_data['hr']
        status_class = "status-normal" if 60 <= hr <= 100 else "status-warning" if 50 <= hr <= 110 else "status-critical"
        status = "NORMAL" if 60 <= hr <= 100 else "WARNING" if 50 <= hr <= 110 else "ALERT"
        
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
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        spo2 = current_data['spo2']
        status_class = "status-normal" if spo2 >= 95 else "status-warning" if spo2 >= 90 else "status-critical"
        status = "NORMAL" if spo2 >= 95 else "LOW" if spo2 >= 90 else "CRITICAL"
        
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

# ================ RUN DASHBOARD ================
if __name__ == "__main__":
    main()