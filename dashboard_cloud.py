# dashboard_cloud.py - NO JSON VERSION
"""
REAL-TIME DASHBOARD FOR STEMCUBE
READS DIRECTLY FROM COM8 - NO JSON FILES
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import pytz
from collections import deque

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

# ================ INITIALIZE DATA BUFFERS ================
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
        
        # Raw packets storage
        st.session_state.raw_packets = deque(maxlen=20)
        
        # Store complete data records
        st.session_state.all_data = deque([
            {
                'timestamp': current_time - timedelta(seconds=i),
                'hr': initial_hr + np.random.normal(0, 3),
                'spo2': initial_spo2 + np.random.normal(0, 1),
                'temp': initial_temp + np.random.normal(0, 0.2),
                'movement': initial_movement + np.random.normal(0, 0.3),
                'activity': ['RESTING', 'WALKING', 'RUNNING'][i % 3],
                'is_real': False
            }
            for i in range(10)
        ], maxlen=50)
        
        # Connection status
        st.session_state.com8_status = "Not Connected"

# ================ SIMPLE COM8 READER ================
def read_com8_direct():
    """Read DIRECTLY from COM8 - SIMPLE VERSION"""
    if not SERIAL_AVAILABLE:
        return None, "Serial not available"
    
    try:
        # Try to open COM8
        ser = serial.Serial(
            port='COM8',
            baudrate=9600,
            timeout=0.5
        )
        
        if ser.in_waiting > 0:
            # Read raw data
            raw_line = ser.readline().decode('utf-8', errors='ignore').strip()
            ser.close()
            
            if raw_line:
                # Parse the data
                data = parse_raw_data(raw_line)
                data['is_real'] = True
                data['raw'] = raw_line[:80]
                
                # Store raw packet
                st.session_state.raw_packets.append({
                    'time': datetime.now().strftime('%H:%M:%S'),
                    'packet': raw_line[:60]
                })
                
                return data, "Connected to COM8"
        
        ser.close()
        return None, "COM8 connected, no data"
        
    except serial.SerialException:
        return None, "COM8 not available"
    except Exception as e:
        return None, f"COM8 error: {str(e)[:50]}"

def parse_raw_data(raw_line):
    """Parse raw data from STEMCUBE"""
    # Default data
    data = {
        'timestamp': datetime.now(),
        'hr': 75,
        'spo2': 98,
        'temp': 36.5,
        'movement': 1.0,
        'activity': 'RESTING',
        'packet_id': int(time.time() * 100) % 10000,
        'node_id': 'NODE_e661'
    }
    
    # Try different parsing methods
    try:
        # METHOD 1: Pipe separated
        if '|' in raw_line:
            parts = raw_line.split('|')
            for part in parts:
                part = part.strip()
                if 'HR:' in part or 'hr:' in part:
                    hr_key = 'HR:' if 'HR:' in part else 'hr:'
                    hr_val = part.split(hr_key)[1].strip()
                    data['hr'] = int(''.join(filter(str.isdigit, hr_val))[:3])
                
                elif 'SpO2:' in part or 'spo2:' in part or 'SPO2:' in part:
                    spo2_key = 'SpO2:' if 'SpO2:' in part else 'spo2:' if 'spo2:' in part else 'SPO2:'
                    spo2_val = part.split(spo2_key)[1].strip()
                    data['spo2'] = int(''.join(filter(str.isdigit, spo2_val))[:3])
                
                elif 'TEMP:' in part or 'temp:' in part or 'Temp:' in part:
                    temp_key = 'TEMP:' if 'TEMP:' in part else 'temp:' if 'temp:' in part else 'Temp:'
                    temp_val = part.split(temp_key)[1].strip()
                    data['temp'] = float(''.join([c for c in temp_val if c.isdigit() or c == '.']))
        
        # METHOD 2: Comma separated with equals
        elif '=' in raw_line and ',' in raw_line:
            pairs = raw_line.split(',')
            for pair in pairs:
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    key = key.strip().upper()
                    value = value.strip()
                    
                    if 'HR' in key:
                        data['hr'] = int(''.join(filter(str.isdigit, value))[:3])
                    elif 'SPO2' in key:
                        data['spo2'] = int(''.join(filter(str.isdigit, value))[:3])
                    elif 'TEMP' in key:
                        data['temp'] = float(''.join([c for c in value if c.isdigit() or c == '.']))
        
        # METHOD 3: Simple numbers
        elif ',' in raw_line and ':' not in raw_line and '=' not in raw_line:
            parts = raw_line.split(',')
            if len(parts) >= 3:
                data['hr'] = int(''.join(filter(str.isdigit, parts[0]))[:3])
                data['spo2'] = int(''.join(filter(str.isdigit, parts[1]))[:3])
                if '.' in parts[2]:
                    data['temp'] = float(''.join([c for c in parts[2] if c.isdigit() or c == '.']))
                else:
                    data['temp'] = float(''.join(filter(str.isdigit, parts[2]))[:4]) / 10
        
        # Determine activity based on HR
        if data['hr'] < 70:
            data['activity'] = 'RESTING'
            data['movement'] = 0.8
        elif data['hr'] < 100:
            data['activity'] = 'WALKING'
            data['movement'] = 2.5
        else:
            data['activity'] = 'RUNNING'
            data['movement'] = 4.5
            
    except Exception as e:
        # Keep default values if parsing fails
        pass
    
    return data

def get_demo_data():
    """Generate demo data"""
    current_time = datetime.now()
    seconds = current_time.second
    
    # Cycle activities every 20 seconds
    activity_idx = int(seconds / 20) % 3
    activities = ['RESTING', 'WALKING', 'RUNNING']
    activity = activities[activity_idx]
    
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
    
    # Add natural variation
    time_factor = time.time()
    hr = base_hr + int(np.sin(time_factor) * 8)
    spo2 = base_spo2 + int(np.cos(time_factor / 2) * 2)
    
    return {
        'timestamp': current_time,
        'hr': max(40, min(160, hr)),
        'spo2': max(85, min(100, spo2)),
        'temp': 36.5 + np.sin(time_factor) * 0.3,
        'movement': base_movement + np.sin(time_factor) * 0.5,
        'activity': activity,
        'packet_id': int(time_factor * 100) % 10000,
        'node_id': 'NODE_e661',
        'is_real': False,
        'raw': 'DEMO DATA - Connect STEMCUBE to COM8'
    }

def update_data_buffers(data):
    """Update all data buffers"""
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
        'activity': data['activity'],
        'is_real': data['is_real']
    })

# ================ GRAPH FUNCTIONS ================
def create_graph(title, y_data, color, y_label):
    """Create a graph"""
    if len(st.session_state.timestamps) == 0:
        return None
    
    n_points = min(30, len(st.session_state.timestamps))
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(st.session_state.timestamps)[-n_points:],
        y=list(y_data)[-n_points:],
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
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        hr = current_data['hr']
        status = "🟢 Normal" if 60 <= hr <= 100 else "🟡 Warning" if 50 <= hr <= 110 else "🔴 Alert"
        st.markdown(f"### ❤️ {hr}")
        st.markdown(f"**Heart Rate**<br>{status}", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        spo2 = current_data['spo2']
        status = "🟢 Normal" if spo2 >= 95 else "🟡 Low" if spo2 >= 90 else "🔴 Critical"
        st.markdown(f"### 🩸 {spo2}%")
        st.markdown(f"**Blood Oxygen**<br>{status}", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col3:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        temp = current_data['temp']
        status = "🟢 Normal" if temp <= 37.5 else "🟡 Elevated" if temp <= 38.5 else "🔴 Fever"
        st.markdown(f"### 🌡️ {temp:.1f}°C")
        st.markdown(f"**Temperature**<br>{status}", unsafe_allow_html=True)
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
        if hr_fig:
            st.plotly_chart(hr_fig, use_container_width=True)
        else:
            st.info("Loading HR graph...")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
        spo2_fig = create_graph("🩸 Blood Oxygen", st.session_state.spo2_data, '#556B2F', '%')
        if spo2_fig:
            st.plotly_chart(spo2_fig, use_container_width=True)
        else:
            st.info("Loading SpO₂ graph...")
        st.markdown("</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
        temp_fig = create_graph("🌡️ Temperature", st.session_state.temp_data, '#D4A76A', '°C')
        if temp_fig:
            st.plotly_chart(temp_fig, use_container_width=True)
        else:
            st.info("Loading temperature graph...")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
        move_fig = create_graph("🏃 Movement", st.session_state.movement_data, '#8D6E63', 'Level')
        if move_fig:
            st.plotly_chart(move_fig, use_container_width=True)
        else:
            st.info("Loading movement graph...")
        st.markdown("</div>", unsafe_allow_html=True)

# ================ TAB 2: SYSTEM STATUS ================
def tab_system_status(current_data, com8_status):
    """Tab 2: System Status"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
        st.markdown("### 📡 Connection Status")
        
        # COM8 Status
        if "Connected" in com8_status:
            st.success(f"✅ **{com8_status}**")
        elif "COM8 not available" in com8_status:
            st.error("❌ **COM8 not available**")
        else:
            st.warning(f"⚠️ **{com8_status}**")
        
        st.metric("Data Source", "REAL" if current_data['is_real'] else "DEMO")
        st.metric("Packet ID", current_data['packet_id'])
        st.metric("Node ID", current_data['node_id'])
        
        # Connection instructions
        with st.expander("🔧 Setup Instructions"):
            st.markdown("""
            1. **Connect STEMCUBE** to USB port
            2. **Check Device Manager** for COM port (usually COM8)
            3. **Ensure baud rate is 9600**
            4. **Restart dashboard** if connected
            
            **Common STEMCUBE formats:**
            - `HR:75|SpO2:98|TEMP:36.5|ACT:RUNNING`
            - `75,98,36.5,RUNNING`
            - `HR=75,SpO2=98,TEMP=36.5`
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
                ]
            }
        ))
        
        fig_battery.update_layout(height=200, margin=dict(t=30, b=20, l=20, r=20))
        st.plotly_chart(fig_battery, use_container_width=True)
        
        # Signal strength
        st.progress(0.85, text="Signal: -65 dB")
        st.progress(0.92, text="Battery: 85%")
        
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
    """Tab 3: Data Log"""
    
    st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
    st.markdown("### 📋 Recent Data Log")
    
    if len(st.session_state.all_data) > 0:
        # Get last 10 records
        all_data_list = list(st.session_state.all_data)
        n_items = min(10, len(all_data_list))
        
        table_data = []
        for i in range(1, n_items + 1):
            record = all_data_list[-i]
            table_data.append({
                'Time': record['timestamp'].strftime('%H:%M:%S'),
                'HR': record['hr'],
                'SpO₂': record['spo2'],
                'Temp': f"{record['temp']:.1f}°C",
                'Movement': f"{record['movement']:.1f}",
                'Activity': record['activity'],
                'Source': 'REAL' if record['is_real'] else 'DEMO'
            })
        
        # Reverse to show newest first
        table_data.reverse()
        
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, height=400)
    else:
        st.info("No data available yet")
    
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
    """Main dashboard function - NO JSON"""
    
    # Initialize session state
    init_session_state()
    
    # Get data from COM8 or demo
    com8_data, com8_status = read_com8_direct()
    
    if com8_data:
        current_data = com8_data
        st.session_state.com8_status = com8_status
    else:
        current_data = get_demo_data()
        st.session_state.com8_status = com8_status
    
    # Update buffers
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
            📊 Data: <strong>{'REAL' if current_data['is_real'] else 'DEMO'}</strong> | 
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
        
        # Refresh button
        if st.button("🔄 Manual Refresh"):
            st.rerun()
            
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
        st.markdown("### 📊 Current Values")
        st.metric("❤️ HR", f"{current_data['hr']} BPM")
        st.metric("🩸 SpO₂", f"{current_data['spo2']}%")
        st.metric("🌡️ Temp", f"{current_data['temp']:.1f}°C")
        st.metric("🏃 Activity", current_data['activity'])
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
        st.markdown("### 🔌 Connection Status")
        
        if current_data['is_real']:
            st.success("✅ **COM8 Connected**")
        else:
            st.warning("⚠️ **Demo Mode**")
            if "COM8 not available" in st.session_state.com8_status:
                st.error("❌ COM8 not found")
            else:
                st.info(st.session_state.com8_status)
        
        st.markdown(f"**Node:** {current_data['node_id']}")
        st.markdown(f"**Packets:** {len(st.session_state.raw_packets)}")
        st.markdown(f"**Last:** {datetime.now().strftime('%H:%M:%S')}")
        st.markdown("</div>", unsafe_allow_html=True)
    
    # TABS
    tab1, tab2, tab3 = st.tabs(["🩺 Health Vitals", "📡 System Status", "📋 Data Log"])
    
    with tab1:
        tab_health_vitals(current_data)
    
    with tab2:
        tab_system_status(current_data, st.session_state.com8_status)
    
    with tab3:
        tab_data_log()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 12px;">
        🏥 <strong>STEMCUBE Health Monitoring System</strong> | 
        📍 Universiti Malaysia Pahang | 
        🎓 Final Year Project 2025 | 
        🔄 <em>Direct COM8 Reading - No JSON Files</em>
    </div>
    """, unsafe_allow_html=True)
    
    # Auto-refresh
    if auto_refresh:
        time.sleep(refresh_rate)
        st.rerun()

# ================ RUN DASHBOARD ================
if __name__ == "__main__":
    main()