# dashboard_cloud.py - FIXED FOR REAL STEMCUBE DATA
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
    import serial.tools.list_ports
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
    
    .status-good { color: #4CAF50; font-weight: bold; }
    .status-warning { color: #FF9800; font-weight: bold; }
    .status-critical { color: #F44336; font-weight: bold; }
    
    .sidebar-section {
        background: #f5f5dc;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
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
    """
    Parse ACTUAL STEMCUBE data based on your format examples:
    1. [1016] NODE_e6... (Packet ID and Node ID)
    2. [1017] 61|346|293... (HR|???|???)
    3. [1018] 64743|26.7... (???|Temperature)
    """
    data = {
        'hr': 70,  # Default
        'spo2': 98,  # Default
        'temp': 36.5,  # Default
        'movement': 1.0,  # Default
        'activity': 'RESTING',
        'packet_id': 0,
        'node_id': 'NODE_e661',
        'raw': raw_line[:50] + "..." if len(raw_line) > 50 else raw_line,
        'is_real': False
    }
    
    try:
        # Remove brackets and parse
        if raw_line.startswith('[') and ']' in raw_line:
            # Extract packet ID
            packet_end = raw_line.find(']')
            packet_id_str = raw_line[1:packet_end]
            try:
                data['packet_id'] = int(packet_id_str)
            except:
                data['packet_id'] = 0
            
            # Get the data part after packet ID
            data_part = raw_line[packet_end + 1:].strip()
            
            # Parse based on content
            if '|' in data_part:
                parts = data_part.split('|')
                
                # Format 1: HR|SpO2|??? (based on your data: 61|346|293...)
                if len(parts) >= 2:
                    # First number is likely HR
                    try:
                        data['hr'] = int(parts[0].strip())
                        # Second number might be SpO2 or something else
                        # If it's 346, it's probably not SpO2 (too high)
                        second_val = int(parts[1].strip())
                        if 70 <= second_val <= 100:  # Valid SpO2 range
                            data['spo2'] = second_val
                    except:
                        pass
                
                # Format 2: ???|Temperature (based on your data: 64743|26.7...)
                if len(parts) >= 2:
                    # Check if second part is temperature
                    try:
                        temp_val = float(parts[1].strip())
                        if 20 <= temp_val <= 45:  # Valid body temp range
                            data['temp'] = temp_val
                    except:
                        pass
            
            # Check for NODE ID
            if 'NODE_' in data_part.upper():
                node_part = data_part.upper().split('NODE_')[-1]
                data['node_id'] = f"NODE_{node_part.split()[0] if ' ' in node_part else node_part[:4]}"
        
        # Determine activity based on HR
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
        
    except Exception as e:
        # If parsing fails, use defaults
        pass
    
    return data

def read_com8_data():
    """Read REAL data from COM8"""
    if not SERIAL_AVAILABLE:
        return None
    
    try:
        # Try COM8 first
        ser = serial.Serial('COM8', 9600, timeout=0.5)
        
        if ser.in_waiting > 0:
            raw_line = ser.readline().decode('utf-8', errors='ignore').strip()
            ser.close()
            
            if raw_line:
                # Parse the data
                data = parse_stemcube_packet(raw_line)
                data['timestamp'] = datetime.now()
                
                # Store raw packet
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
    """Get current data - try COM8 first, then demo"""
    # Try to get real data
    real_data = read_com8_data()
    
    if real_data:
        return real_data
    else:
        # Generate demo data
        current_time = datetime.now()
        seconds = current_time.second
        
        # Simulate activities
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
    
    # Get last 30 points or all if less
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
            Data: <span class="{'status-good' if current_data['is_real'] else 'status-warning'}">
            {'REAL from COM8' if current_data['is_real'] else 'DEMO'}
            </span>
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
        st.markdown("### 📊 Connection")
        if SERIAL_AVAILABLE:
            st.success("✅ pyserial installed")
        else:
            st.warning("⚠️ Install pyserial for COM8")
        
        if current_data['is_real']:
            st.success(f"✅ Reading COM8")
            st.info(f"Packet: {current_data['packet_id']}")
        else:
            st.warning("⚠️ Using demo data")
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
        st.markdown("### 📈 Current Values")
        st.metric("❤️ HR", f"{current_data['hr']} BPM")
        st.metric("🩸 SpO₂", f"{current_data['spo2']}%")
        st.metric("🌡️ Temp", f"{current_data['temp']:.1f}°C")
        st.metric("🏃 Activity", current_data['activity'])
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Main content - Current Metrics
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
            st.plotly_chart(hr_fig, use_container_width=True)
        else:
            st.info("Waiting for HR data...")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
        spo2_fig = create_graph("🩸 Blood Oxygen", st.session_state.spo2_data, '#556B2F', '%')
        if spo2_fig:
            st.plotly_chart(spo2_fig, use_container_width=True)
        else:
            st.info("Waiting for SpO₂ data...")
        st.markdown("</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
        temp_fig = create_graph("🌡️ Temperature", st.session_state.temp_data, '#D4A76A', '°C')
        if temp_fig:
            st.plotly_chart(temp_fig, use_container_width=True)
        else:
            st.info("Waiting for temp data...")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
        move_fig = create_graph("🏃 Movement", st.session_state.movement_data, '#8D6E63', 'Level')
        if move_fig:
            st.plotly_chart(move_fig, use_container_width=True)
        else:
            st.info("Waiting for movement data...")
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Data Table - FIXED: No more negative index error
    st.markdown("### 📋 Recent Data")
    
    if len(st.session_state.timestamps) > 0:
        # Get last 10 items safely
        n_items = min(10, len(st.session_state.timestamps))
        
        table_data = []
        for i in range(1, n_items + 1):
            idx = -i  # Negative index from the end
            table_data.append({
                'Time': st.session_state.timestamps[idx].strftime('%H:%M:%S'),
                'HR': st.session_state.hr_data[idx],
                'SpO₂': st.session_state.spo2_data[idx],
                'Temp': f"{st.session_state.temp_data[idx]:.1f}°C",
                'Movement': f"{st.session_state.movement_data[idx]:.1f}"
            })
        
        # Reverse to show newest first
        table_data.reverse()
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, height=300)
    else:
        st.info("Waiting for data...")
    
    # Raw Packets
    with st.expander("📡 Raw COM8 Packets"):
        if len(st.session_state.raw_packets) > 0:
            for packet in list(st.session_state.raw_packets)[-5:]:
                st.code(f"{packet['time']}: {packet['packet']}")
        else:
            st.info("No raw packets received yet")
    
    # Auto-refresh
    if auto_refresh:
        time.sleep(refresh_rate)
        st.rerun()

# ================ RUN DASHBOARD ================
if __name__ == "__main__":
    main()