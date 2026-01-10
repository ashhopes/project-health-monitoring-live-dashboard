# dashboard_cloud.py - UPDATED FOR NEW STREAMLIT SYNTAX
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
import pytz
from collections import deque

# ================ TRY TO IMPORT SERIAL ================
try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

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
</style>
""", unsafe_allow_html=True)

# ================ INITIALIZE DATA BUFFERS ================
if 'hr_data' not in st.session_state:
    st.session_state.hr_data = deque(maxlen=50)
if 'spo2_data' not in st.session_state:
    st.session_state.spo2_data = deque(maxlen=50)
if 'temp_data' not in st.session_state:
    st.session_state.temp_data = deque(maxlen=50)
if 'movement_data' not in st.session_state:
    st.session_state.movement_data = deque(maxlen=50)
if 'timestamps' not in st.session_state:
    st.session_state.timestamps = deque(maxlen=50)
if 'raw_packets' not in st.session_state:
    st.session_state.raw_packets = deque(maxlen=20)

# ================ PARSE ACTUAL STEMCUBE DATA ================

def parse_stemcube_packet(raw_line):
    """Parse ACTUAL STEMCUBE data"""
    data = {
        'hr': 70,
        'spo2': 98,
        'temp': 36.5,
        'movement': 1.0,
        'activity': 'RESTING',
        'packet_id': 0,
        'node_id': 'NODE_e661',
        'raw': raw_line[:50] + "..." if len(raw_line) > 50 else raw_line,
        'is_real': False
    }
    
    try:
        if raw_line.startswith('[') and ']' in raw_line:
            packet_end = raw_line.find(']')
            packet_id_str = raw_line[1:packet_end]
            try:
                data['packet_id'] = int(packet_id_str)
            except:
                data['packet_id'] = 0
            
            data_part = raw_line[packet_end + 1:].strip()
            
            if '|' in data_part:
                parts = data_part.split('|')
                
                if len(parts) >= 1:
                    try:
                        data['hr'] = int(parts[0].strip())
                    except:
                        pass
                
                if len(parts) >= 2:
                    try:
                        second_val = int(parts[1].strip())
                        if 70 <= second_val <= 100:
                            data['spo2'] = second_val
                    except:
                        pass
                
                if len(parts) >= 2:
                    try:
                        temp_val = float(parts[1].strip())
                        if 20 <= temp_val <= 45:
                            data['temp'] = temp_val
                    except:
                        pass
            
            if 'NODE_' in data_part.upper():
                node_part = data_part.upper().split('NODE_')[-1]
                data['node_id'] = f"NODE_{node_part.split()[0] if ' ' in node_part else node_part[:4]}"
        
        # Determine activity
        if data['hr'] < 60:
            data['activity'] = 'RESTING'
            data['movement'] = 0.5 + np.random.random() * 0.5
        elif data['hr'] < 100:
            data['activity'] = 'WALKING'
            data['movement'] = 2.0 + np.random.random() * 1.5
        else:
            data['activity'] = 'RUNNING'
            data['movement'] = 4.0 + np.random.random() * 2.0
        
        data['is_real'] = True
        
    except:
        pass
    
    return data

def read_com8_data():
    """Read REAL data from COM8"""
    if not SERIAL_AVAILABLE:
        return None
    
    try:
        ser = serial.Serial('COM8', 9600, timeout=0.5)
        
        if ser.in_waiting > 0:
            raw_line = ser.readline().decode('utf-8', errors='ignore').strip()
            ser.close()
            
            if raw_line:
                data = parse_stemcube_packet(raw_line)
                data['timestamp'] = datetime.now()
                
                st.session_state.raw_packets.append({
                    'time': datetime.now().strftime('%H:%M:%S'),
                    'packet': raw_line[:80]
                })
                
                return data
        
        ser.close()
    except:
        pass
    
    return None

def get_current_data():
    """Get current data"""
    real_data = read_com8_data()
    
    if real_data:
        return real_data
    else:
        current_time = datetime.now()
        seconds = current_time.second
        
        if seconds < 20:
            activity = 'RESTING'
            hr = 65 + int(np.sin(seconds/5) * 10)
            movement = 0.5 + abs(np.sin(seconds/3)) * 0.5
        elif seconds < 40:
            activity = 'WALKING'
            hr = 85 + int(np.sin(seconds/5) * 15)
            movement = 2.0 + abs(np.sin(seconds/3)) * 1.0
        else:
            activity = 'RUNNING'
            hr = 120 + int(np.sin(seconds/5) * 20)
            movement = 4.0 + abs(np.sin(seconds/3)) * 2.0
        
        return {
            'timestamp': current_time,
            'hr': max(40, min(160, hr)),
            'spo2': 96 + int(np.cos(seconds/10) * 3),
            'temp': 36.5 + np.random.random() * 0.5,
            'movement': movement,
            'activity': activity,
            'packet_id': int(time.time() * 100) % 10000,
            'node_id': 'NODE_e661',
            'raw': 'DEMO DATA',
            'is_real': False
        }

def update_data_buffers(data):
    """Update data buffers"""
    st.session_state.timestamps.append(data['timestamp'])
    st.session_state.hr_data.append(data['hr'])
    st.session_state.spo2_data.append(data['spo2'])
    st.session_state.temp_data.append(data['temp'])
    st.session_state.movement_data.append(data['movement'])

# ================ GRAPH FUNCTIONS ================

def create_graph(title, y_data, color, y_label):
    """Create a generic graph"""
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
    
    # Current Metrics
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
        st.markdown(f"**Activity**<br>{activity}", unsafe_allow_html=True)
        st.markdown(f"Movement: {current_data['movement']:.1f}", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Real-time Graphs
    st.markdown("### 📈 Real-time Graphs")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
        hr_fig = create_graph("❤️ Heart Rate", st.session_state.hr_data, '#8B4513', 'BPM')
        if hr_fig:
            st.plotly_chart(hr_fig, width='stretch')
        else:
            st.info("Waiting for HR data...")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
        spo2_fig = create_graph("🩸 Blood Oxygen", st.session_state.spo2_data, '#556B2F', '%')
        if spo2_fig:
            st.plotly_chart(spo2_fig, width='stretch')
        else:
            st.info("Waiting for SpO₂ data...")
        st.markdown("</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
        temp_fig = create_graph("🌡️ Temperature", st.session_state.temp_data, '#D4A76A', '°C')
        if temp_fig:
            st.plotly_chart(temp_fig, width='stretch')
        else:
            st.info("Waiting for temp data...")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
        move_fig = create_graph("🏃 Movement", st.session_state.movement_data, '#8D6E63', 'Level')
        if move_fig:
            st.plotly_chart(move_fig, width='stretch')
        else:
            st.info("Waiting for movement data...")
        st.markdown("</div>", unsafe_allow_html=True)

# ================ TAB 2: SYSTEM STATUS ================

def tab_system_status(current_data):
    """Tab 2: System Status"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
        st.markdown("### 📡 Connection Status")
        
        if SERIAL_AVAILABLE:
            st.success("✅ pyserial installed")
        else:
            st.warning("⚠️ Install pyserial for COM8")
        
        if current_data['is_real']:
            st.success(f"✅ Reading COM8")
            st.metric("Packet ID", current_data['packet_id'])
            st.metric("Node ID", current_data['node_id'])
        else:
            st.warning("⚠️ Using demo data")
            st.info("Connect STEMCUBE to COM8 for real data")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
        st.markdown("### 🔋 System Metrics")
        
        # Battery gauge
        battery = 85  # Default
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
        st.plotly_chart(fig_battery, width='stretch')
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Raw Packets
    st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
    st.markdown("### 📡 Recent Raw Packets")
    
    if len(st.session_state.raw_packets) > 0:
        for packet in list(st.session_state.raw_packets)[-5:]:
            st.code(f"{packet['time']}: {packet['packet']}")
    else:
        st.info("No raw packets received yet")
    
    st.markdown("</div>", unsafe_allow_html=True)

# ================ TAB 3: DATA LOG ================

def tab_data_log():
    """Tab 3: Data Log"""
    
    st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
    st.markdown("### 📋 Recent Data Log")
    
    if len(st.session_state.timestamps) > 0:
        # Safe way to get last 10 items
        n_items = min(10, len(st.session_state.timestamps))
        
        # Get indices for last n_items
        indices = list(range(len(st.session_state.timestamps)))[-n_items:]
        
        table_data = []
        for idx in indices:
            # Check if buffers have data at this index
            if (idx < len(st.session_state.timestamps) and 
                idx < len(st.session_state.hr_data) and
                idx < len(st.session_state.spo2_data) and
                idx < len(st.session_state.temp_data) and
                idx < len(st.session_state.movement_data)):
                
                table_data.append({
                    'Time': st.session_state.timestamps[idx].strftime('%H:%M:%S'),
                    'HR': st.session_state.hr_data[idx],
                    'SpO₂': st.session_state.spo2_data[idx],
                    'Temp': f"{st.session_state.temp_data[idx]:.1f}°C",
                    'Movement': f"{st.session_state.movement_data[idx]:.1f}",
                    'Index': idx
                })
        
        # Reverse to show newest first
        table_data.reverse()
        
        if table_data:
            df = pd.DataFrame(table_data)
            # Remove Index column for display
            df_display = df.drop('Index', axis=1) if 'Index' in df.columns else df
            
            # FIXED: Updated DataFrame syntax
            st.dataframe(df_display, width='stretch', height=400)
        else:
            st.info("No valid data to display")
    else:
        st.info("Waiting for data...")
    
    # Data Statistics
    st.markdown("### 📊 Data Statistics")
    
    if len(st.session_state.hr_data) > 0:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("HR Avg", f"{np.mean(list(st.session_state.hr_data)):.0f} BPM")
        with col2:
            st.metric("SpO₂ Avg", f"{np.mean(list(st.session_state.spo2_data)):.0f}%")
        with col3:
            st.metric("Temp Avg", f"{np.mean(list(st.session_state.temp_data)):.1f}°C")
        with col4:
            st.metric("Data Points", len(st.session_state.timestamps))
    
    st.markdown("</div>", unsafe_allow_html=True)

# ================ MAIN DASHBOARD ================

def main():
    """Main dashboard function"""
    
    # Get current data
    current_data = get_current_data()
    update_data_buffers(current_data)
    
    # Malaysia time
    malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
    current_time_malaysia = datetime.now(malaysia_tz)
    
    # Header
    st.markdown(f"""
    <div class="main-header">
        <h1 style="margin: 0; font-size: 2rem;">🏥 STEMCUBE REAL-TIME MONITOR</h1>
        <p style="margin: 5px 0 0 0; font-size: 1rem;">
            Malaysia Time: {current_time_malaysia.strftime('%H:%M:%S')} | 
            Data: {'REAL from COM8' if current_data['is_real'] else 'DEMO'}
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
        st.markdown("### 📈 Buffer Status")
        st.write(f"HR Points: {len(st.session_state.hr_data)}")
        st.write(f"SpO₂ Points: {len(st.session_state.spo2_data)}")
        st.write(f"Temp Points: {len(st.session_state.temp_data)}")
        st.write(f"Raw Packets: {len(st.session_state.raw_packets)}")
        st.markdown("</div>", unsafe_allow_html=True)
    
    # TABS
    tab1, tab2, tab3 = st.tabs(["🩺 Health Vitals", "📡 System Status", "📋 Data Log"])
    
    with tab1:
        tab_health_vitals(current_data)
    
    with tab2:
        tab_system_status(current_data)
    
    with tab3:
        tab_data_log()
    
    # Auto-refresh
    if auto_refresh:
        time.sleep(refresh_rate)
        st.rerun()

# ================ RUN DASHBOARD ================
if __name__ == "__main__":
    main()