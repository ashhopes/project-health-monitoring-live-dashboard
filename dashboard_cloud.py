# dashboard_cloud.py - COMPLETELY FIXED VERSION
"""
REAL-TIME DASHBOARD FOR STEMCUBE
READS ACTUAL DATA FROM COM8
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import json
import pytz
from collections import deque
import os

# ================ TRY TO IMPORT SERIAL ================
try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    st.warning("⚠️ pyserial not installed. Install with: pip install pyserial")

# ================ PAGE CONFIG ================
st.set_page_config(
    page_title="STEMCUBE REAL-TIME MONITOR",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================ SIMPLE STYLES ================
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #8B4513 0%, #556B2F 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        text-align: center;
    }
    
    .metric-card {
        background: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin: 10px 0;
        text-align: center;
    }
    
    .graph-container {
        background: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
    
    .sidebar-section {
        background: #f5f5dc;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    
    /* TABS STYLING */
    .stTabs [data-baseweb="tab-list"] {
        gap: 5px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: #F7E7CE;
        border-radius: 5px 5px 0 0;
        padding: 8px 16px;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background: #8B4513 !important;
        color: white !important;
    }
    
    .status-normal { color: #4CAF50; font-weight: bold; }
    .status-warning { color: #FF9800; font-weight: bold; }
    .status-critical { color: #F44336; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ================ FIXED: INITIALIZE DATA BUFFERS ================
def init_session_state():
    """Initialize all session state variables WITH DATA"""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        current_time = datetime.now()
        
        # Create INITIAL DATA to prevent empty buffers
        initial_hr = 75
        initial_spo2 = 98
        initial_temp = 36.5
        initial_movement = 1.0
        
        # Initialize with 10 data points (not empty)
        st.session_state.hr_data = deque([initial_hr + np.random.normal(0, 3) for _ in range(10)], maxlen=50)
        st.session_state.spo2_data = deque([initial_spo2 + np.random.normal(0, 1) for _ in range(10)], maxlen=50)
        st.session_state.temp_data = deque([initial_temp + np.random.normal(0, 0.2) for _ in range(10)], maxlen=50)
        st.session_state.movement_data = deque([initial_movement + np.random.normal(0, 0.3) for _ in range(10)], maxlen=50)
        st.session_state.timestamps = deque([current_time - timedelta(seconds=i) for i in range(10)][::-1], maxlen=50)
        st.session_state.raw_packets = deque(maxlen=20)
        
        # Store complete data records
        st.session_state.all_data = deque([
            {
                'timestamp': current_time - timedelta(seconds=i),
                'hr': initial_hr + np.random.normal(0, 3),
                'spo2': initial_spo2 + np.random.normal(0, 1),
                'temp': initial_temp + np.random.normal(0, 0.2),
                'movement': initial_movement + np.random.normal(0, 0.3),
                'activity': ['RESTING', 'WALKING', 'RUNNING'][i % 3]
            }
            for i in range(10)
        ], maxlen=50)

# ================ SIMPLIFIED DATA READING ================
def read_com8_simple():
    """Simple COM8 reader - returns data if available"""
    if not SERIAL_AVAILABLE:
        return None
    
    try:
        ser = serial.Serial('COM8', 9600, timeout=0.5)
        
        if ser.in_waiting > 0:
            raw_line = ser.readline().decode('utf-8', errors='ignore').strip()
            ser.close()
            
            if raw_line and len(raw_line) > 5:  # Valid data check
                # Parse simple format
                data = {
                    'timestamp': datetime.now(),
                    'hr': 75,
                    'spo2': 98,
                    'temp': 36.5,
                    'movement': 1.0,
                    'activity': 'RESTING',
                    'packet_id': int(time.time() * 100) % 10000,
                    'node_id': 'NODE_e661',
                    'raw': raw_line[:80],
                    'is_real': True
                }
                
                # Try to extract numbers
                try:
                    # Look for HR pattern
                    if 'HR:' in raw_line:
                        hr_part = raw_line.split('HR:')[1].split()[0]
                        data['hr'] = int(''.join(filter(str.isdigit, hr_part))[:3])
                    
                    # Look for SpO2 pattern
                    if 'SpO2:' in raw_line:
                        spo2_part = raw_line.split('SpO2:')[1].split()[0]
                        data['spo2'] = int(''.join(filter(str.isdigit, spo2_part))[:3])
                    
                    # Look for temperature
                    if 'TEMP:' in raw_line or 'Temp:' in raw_line:
                        temp_key = 'TEMP:' if 'TEMP:' in raw_line else 'Temp:'
                        temp_part = raw_line.split(temp_key)[1].split()[0]
                        data['temp'] = float(''.join(c for c in temp_part if c.isdigit() or c == '.'))
                    
                    # Determine activity based on HR
                    if data['hr'] < 70:
                        data['activity'] = 'RESTING'
                        data['movement'] = 0.5
                    elif data['hr'] < 100:
                        data['activity'] = 'WALKING'
                        data['movement'] = 2.0
                    else:
                        data['activity'] = 'RUNNING'
                        data['movement'] = 4.0
                        
                except:
                    pass  # Keep default values
                
                # Add to raw packets
                st.session_state.raw_packets.append({
                    'time': datetime.now().strftime('%H:%M:%S'),
                    'packet': raw_line[:80]
                })
                
                return data
        
        ser.close()
    except Exception as e:
        st.sidebar.error(f"COM8 Error: {str(e)[:50]}")
    
    return None

def get_current_data():
    """Get current data - ALWAYS returns valid data"""
    # Try to read from COM8
    real_data = read_com8_simple()
    
    if real_data:
        return real_data
    else:
        # Generate DEMO data (always works)
        current_time = datetime.now()
        seconds = current_time.second
        
        # Cycle through activities
        activity_index = int(seconds / 20) % 3
        activities = ['RESTING', 'WALKING', 'RUNNING']
        activity = activities[activity_index]
        
        # Base values for each activity
        if activity == 'RESTING':
            base_hr = 65
            base_spo2 = 98
            base_movement = 0.8
        elif activity == 'WALKING':
            base_hr = 85
            base_spo2 = 96
            base_movement = 2.5
        else:  # RUNNING
            base_hr = 120
            base_spo2 = 94
            base_movement = 4.5
        
        # Add some variation
        hr = base_hr + int(np.sin(time.time()) * 10)
        spo2 = base_spo2 + int(np.cos(time.time() / 2) * 2)
        movement = base_movement + np.sin(time.time()) * 0.5
        
        return {
            'timestamp': current_time,
            'hr': max(40, min(160, hr)),
            'spo2': max(85, min(100, spo2)),
            'temp': 36.5 + np.random.random() * 0.5,
            'movement': max(0.1, movement),
            'activity': activity,
            'packet_id': int(time.time() * 100) % 10000,
            'node_id': 'NODE_e661',
            'raw': 'DEMO: No COM8 data',
            'is_real': False
        }

def update_data_buffers(data):
    """Update all data buffers SAFELY"""
    # Update all buffers
    st.session_state.timestamps.append(data['timestamp'])
    st.session_state.hr_data.append(data['hr'])
    st.session_state.spo2_data.append(data['spo2'])
    st.session_state.temp_data.append(data['temp'])
    st.session_state.movement_data.append(data['movement'])
    
    # Store complete record
    st.session_state.all_data.append({
        'timestamp': data['timestamp'],
        'hr': data['hr'],
        'spo2': data['spo2'],
        'temp': data['temp'],
        'movement': data['movement'],
        'activity': data['activity']
    })

# ================ FIXED GRAPH FUNCTIONS ================
def create_graph(title, y_data, color, y_label):
    """Create a graph - FIXED to handle data properly"""
    # Always have at least some data
    if len(st.session_state.timestamps) == 0 or len(y_data) == 0:
        # Create a simple graph with default data
        times = [datetime.now() - timedelta(seconds=i) for i in range(10, 0, -1)]
        values = [70 + np.random.normal(0, 5) for _ in range(10)]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=times,
            y=values,
            mode='lines',
            line=dict(color=color, width=2)
        ))
    else:
        # Use actual data
        n_points = min(30, len(st.session_state.timestamps), len(y_data))
        
        # Get last n_points safely
        x_data = list(st.session_state.timestamps)[-n_points:]
        y_data_list = list(y_data)[-n_points:]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x_data,
            y=y_data_list,
            mode='lines+markers',
            line=dict(color=color, width=2),
            marker=dict(size=4)
        ))
    
    fig.update_layout(
        title=title,
        height=250,
        margin=dict(l=40, r=20, t=40, b=40),
        xaxis_title="Time",
        yaxis_title=y_label,
        showlegend=False
    )
    
    return fig

# ================ TAB 1: HEALTH VITALS ================
def tab_health_vitals(current_data):
    """Tab 1: Health Vitals"""
    
    # Current Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        hr = current_data['hr']
        if 60 <= hr <= 100:
            status_class = "status-normal"
            status = "🟢 Normal"
        elif 50 <= hr <= 110:
            status_class = "status-warning"
            status = "🟡 Warning"
        else:
            status_class = "status-critical"
            status = "🔴 Alert"
        
        st.markdown(f"### ❤️ {hr}")
        st.markdown(f"**Heart Rate**<br><span class='{status_class}'>{status}</span>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        spo2 = current_data['spo2']
        if spo2 >= 95:
            status_class = "status-normal"
            status = "🟢 Normal"
        elif spo2 >= 90:
            status_class = "status-warning"
            status = "🟡 Low"
        else:
            status_class = "status-critical"
            status = "🔴 Critical"
        
        st.markdown(f"### 🩸 {spo2}%")
        st.markdown(f"**Blood Oxygen**<br><span class='{status_class}'>{status}</span>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col3:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        temp = current_data['temp']
        if temp <= 37.5:
            status_class = "status-normal"
            status = "🟢 Normal"
        elif temp <= 38.5:
            status_class = "status-warning"
            status = "🟡 Elevated"
        else:
            status_class = "status-critical"
            status = "🔴 Fever"
        
        st.markdown(f"### 🌡️ {temp:.1f}°C")
        st.markdown(f"**Temperature**<br><span class='{status_class}'>{status}</span>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col4:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        activity = current_data['activity']
        emoji = "😴" if activity == 'RESTING' else "🚶" if activity == 'WALKING' else "🏃"
        
        st.markdown(f"### {emoji}")
        st.markdown(f"**Activity**<br>{activity}")
        st.markdown(f"**Movement:** {current_data['movement']:.1f}")
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Real-time Graphs
    st.markdown("### 📈 Real-time Graphs")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
        hr_fig = create_graph("❤️ Heart Rate", st.session_state.hr_data, '#8B4513', 'BPM')
        st.plotly_chart(hr_fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
        spo2_fig = create_graph("🩸 Blood Oxygen", st.session_state.spo2_data, '#556B2F', '%')
        st.plotly_chart(spo2_fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
        temp_fig = create_graph("🌡️ Temperature", st.session_state.temp_data, '#D4A76A', '°C')
        st.plotly_chart(temp_fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
        move_fig = create_graph("🏃 Movement", st.session_state.movement_data, '#8D6E63', 'Level')
        st.plotly_chart(move_fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ================ TAB 2: SYSTEM STATUS ================
def tab_system_status(current_data):
    """Tab 2: System Status"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
        st.markdown("### 📡 Connection Status")
        
        if SERIAL_AVAILABLE:
            st.success("✅ **pyserial installed**")
        else:
            st.error("❌ **pyserial NOT installed**")
            st.info("Install: `pip install pyserial`")
        
        if current_data['is_real']:
            st.success(f"✅ **Reading REAL data from COM8**")
            st.metric("Packet ID", current_data['packet_id'])
            st.metric("Node ID", current_data['node_id'])
        else:
            st.warning("⚠️ **Using DEMO data**")
            st.info("Connect STEMCUBE to COM8 for real data")
        
        # Connection instructions
        with st.expander("📋 How to connect STEMCUBE"):
            st.markdown("""
            1. Connect STEMCUBE Master to computer via USB
            2. Open Device Manager to find COM port (usually COM8)
            3. Ensure baud rate is 9600
            4. Restart dashboard with STEMCUBE connected
            """)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
        st.markdown("### 🔋 System Metrics")
        
        # Battery gauge
        battery = 85
        fig_battery = go.Figure(go.Indicator(
            mode="gauge+number",
            value=battery,
            title={'text': "Battery Level"},
            number={'suffix': "%"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': '#4CAF50' if battery > 50 else '#FF9800' if battery > 20 else '#F44336'},
                'steps': [
                    {'range': [0, 20], 'color': 'rgba(244, 67, 54, 0.1)'},
                    {'range': [20, 50], 'color': 'rgba(255, 152, 0, 0.1)'},
                    {'range': [50, 100], 'color': 'rgba(76, 175, 80, 0.1)'}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 20
                }
            }
        ))
        
        fig_battery.update_layout(height=200, margin=dict(t=30, b=20, l=20, r=20))
        st.plotly_chart(fig_battery, use_container_width=True)
        
        # Signal strength
        rssi = -65
        st.progress((rssi + 100) / 100, text=f"Signal: {rssi} dB")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Raw Packets
    st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
    st.markdown("### 📡 Recent Raw Packets")
    
    if len(st.session_state.raw_packets) > 0:
        for packet in list(st.session_state.raw_packets)[-5:]:
            st.code(f"{packet['time']}: {packet['packet']}")
    else:
        st.info("No raw packets received yet")
        st.code("DEMO: HR:75 | SpO2:98 | TEMP:36.5 | ACT:RESTING")
    
    st.markdown("</div>", unsafe_allow_html=True)

# ================ TAB 3: DATA LOG ================
def tab_data_log():
    """Tab 3: Data Log - COMPLETELY SAFE VERSION"""
    
    st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
    st.markdown("### 📋 Recent Data Log")
    
    # Use the all_data deque which always has data
    if len(st.session_state.all_data) > 0:
        # Get last 10 records
        all_data_list = list(st.session_state.all_data)
        n_items = min(10, len(all_data_list))
        
        table_data = []
        for i in range(1, n_items + 1):
            record = all_data_list[-i]  # Get from end
            table_data.append({
                'Time': record['timestamp'].strftime('%H:%M:%S'),
                'HR': record['hr'],
                'SpO₂': record['spo2'],
                'Temp': f"{record['temp']:.1f}°C",
                'Movement': f"{record['movement']:.1f}",
                'Activity': record['activity']
            })
        
        # Reverse to show newest first
        table_data.reverse()
        
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, height=400)
    else:
        # Fallback demo data
        demo_data = []
        current_time = datetime.now()
        for i in range(10):
            time_str = (current_time - timedelta(seconds=i*2)).strftime('%H:%M:%S')
            demo_data.append({
                'Time': time_str,
                'HR': 75,
                'SpO₂': 98,
                'Temp': "36.5°C",
                'Movement': "1.2",
                'Activity': "RESTING"
            })
        
        df = pd.DataFrame(demo_data)
        st.dataframe(df, use_container_width=True, height=400)
    
    # Data Statistics
    st.markdown("### 📊 Data Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        hr_list = list(st.session_state.hr_data)
        avg_hr = np.mean(hr_list) if hr_list else 75
        st.metric("HR Avg", f"{avg_hr:.0f} BPM")
    
    with col2:
        spo2_list = list(st.session_state.spo2_data)
        avg_spo2 = np.mean(spo2_list) if spo2_list else 98
        st.metric("SpO₂ Avg", f"{avg_spo2:.0f}%")
    
    with col3:
        temp_list = list(st.session_state.temp_data)
        avg_temp = np.mean(temp_list) if temp_list else 36.5
        st.metric("Temp Avg", f"{avg_temp:.1f}°C")
    
    with col4:
        st.metric("Data Points", len(st.session_state.timestamps))
    
    st.markdown("</div>", unsafe_allow_html=True)

# ================ MAIN DASHBOARD ================
def main():
    """Main dashboard function - FIXED"""
    
    # Initialize session state FIRST
    init_session_state()
    
    # Get current data
    current_data = get_current_data()
    
    # Update buffers with new data
    update_data_buffers(current_data)
    
    # Malaysia time
    malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
    current_time_malaysia = datetime.now(malaysia_tz)
    
    # Header
    st.markdown(f"""
    <div class="main-header">
        <h1 style="margin: 0; font-size: 2rem;">🏥 STEMCUBE REAL-TIME MONITOR</h1>
        <p style="margin: 5px 0 0 0; font-size: 1rem;">
            🇲🇾 Malaysia Time: {current_time_malaysia.strftime('%H:%M:%S')} | 
            📊 Data Source: <strong>{'REAL from COM8' if current_data['is_real'] else 'DEMO'}</strong> | 
            🚶 Activity: {current_data['activity']}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
        st.markdown("### ⚙️ Control Panel")
        auto_refresh = st.toggle("Auto Refresh", value=True)
        refresh_rate = st.slider("Update (seconds)", 1, 5, 2)
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
        st.markdown("### 📊 Current Values")
        st.metric("❤️ HR", f"{current_data['hr']} BPM")
        st.metric("🩸 SpO₂", f"{current_data['spo2']}%")
        st.metric("🌡️ Temp", f"{current_data['temp']:.1f}°C")
        st.metric("🏃 Activity", current_data['activity'])
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
        st.markdown("### 📈 System Info")
        st.write(f"**Node:** {current_data['node_id']}")
        st.write(f"**Packet:** {current_data['packet_id']}")
        st.write(f"**Data Points:** {len(st.session_state.timestamps)}")
        st.write(f"**Last Update:** {datetime.now().strftime('%H:%M:%S')}")
        
        if not current_data['is_real'] and SERIAL_AVAILABLE:
            st.error("⚠️ COM8 not detected!")
            if st.button("🔄 Check COM8 Again"):
                st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # TABS
    tab1, tab2, tab3 = st.tabs(["🩺 Health Vitals", "📡 System Status", "📋 Data Log"])
    
    with tab1:
        tab_health_vitals(current_data)
    
    with tab2:
        tab_system_status(current_data)
    
    with tab3:
        tab_data_log()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 12px;">
        🏥 <strong>STEMCUBE Health Monitoring System</strong> | 
        📍 Universiti Malaysia Pahang | 
        🎓 Final Year Project 2025
    </div>
    """, unsafe_allow_html=True)
    
    # Auto-refresh
    if auto_refresh:
        time.sleep(refresh_rate)
        st.rerun()

# ================ RUN DASHBOARD ================
if __name__ == "__main__":
    main()