# dashboard_cloud.py - STREAMLIT CLOUD VERSION
"""
REAL-TIME DASHBOARD FOR STREAMLIT CLOUD
MUJI MARROON CHAMPAGNE OLIVE THEME
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

# ================ TRY TO IMPORT SERIAL ================
try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

# ================ PAGE CONFIG ================
st.set_page_config(
    page_title="STEMCUBE LIVE - Health Monitor",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================ MUJI MARROON CHAMPAGNE OLIVE THEME ================
st.markdown("""
<style>
    /* MUJI INSPIRED COLOR PALETTE */
    :root {
        --muji-maroon: #8B4513;
        --champagne: #F7E7CE;
        --olive: #556B2F;
        --soft-beige: #F5F5DC;
        --dark-chocolate: #3C2F2F;
        --cream: #FFFDD0;
    }
    
    .stApp {
        background: linear-gradient(135deg, var(--soft-beige) 0%, var(--cream) 100%);
        font-family: 'Arial Rounded MT Bold', 'Arial', sans-serif;
    }
    
    /* HEADER */
    .main-header {
        background: linear-gradient(135deg, var(--muji-maroon) 0%, var(--olive) 100%);
        color: white;
        padding: 25px;
        border-radius: 15px;
        margin-bottom: 25px;
        box-shadow: 0 6px 20px rgba(139, 69, 19, 0.2);
        text-align: center;
    }
    
    /* CARD STYLES */
    .vital-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(85, 107, 47, 0.1);
        border-top: 5px solid var(--olive);
        margin-bottom: 15px;
        transition: all 0.3s ease;
    }
    
    .vital-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 16px rgba(85, 107, 47, 0.15);
    }
    
    .system-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(139, 69, 19, 0.1);
        border-left: 5px solid var(--muji-maroon);
        margin-bottom: 15px;
    }
    
    /* TABS */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: var(--champagne);
        border-radius: 10px 10px 0 0;
        padding: 10px 20px;
        font-weight: 600;
        color: var(--dark-chocolate);
        border: 2px solid var(--champagne);
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--muji-maroon) !important;
        color: white !important;
        border-color: var(--muji-maroon) !important;
    }
    
    /* METRICS */
    .metric-value {
        font-size: 36px;
        font-weight: 700;
        color: var(--dark-chocolate);
        margin: 10px 0;
    }
    
    .metric-label {
        font-size: 14px;
        color: var(--olive);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* STATUS INDICATORS */
    .status-normal {
        background: linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%);
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: 600;
        display: inline-block;
    }
    
    .status-warning {
        background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%);
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: 600;
        display: inline-block;
    }
    
    .status-critical {
        background: linear-gradient(135deg, #F44336 0%, #D32F2F 100%);
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: 600;
        display: inline-block;
    }
    
    /* SIDEBAR */
    .sidebar-content {
        background: linear-gradient(180deg, white 0%, var(--champagne) 100%);
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(139, 69, 19, 0.1);
    }
    
    /* FOOTER */
    .dashboard-footer {
        background: var(--dark-chocolate);
        color: var(--champagne);
        padding: 20px;
        border-radius: 15px;
        margin-top: 30px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ================ INITIALIZE DATA BUFFERS ================
if 'hr_data' not in st.session_state:
    st.session_state.hr_data = deque(maxlen=60)
if 'spo2_data' not in st.session_state:
    st.session_state.spo2_data = deque(maxlen=60)
if 'movement_data' not in st.session_state:
    st.session_state.movement_data = deque(maxlen=60)
if 'timestamps' not in st.session_state:
    st.session_state.timestamps = deque(maxlen=60)
if 'activity_history' not in st.session_state:
    st.session_state.activity_history = deque(maxlen=20)

# ================ SIMPLE DATA GENERATION ================

def get_current_data():
    """Get current data point"""
    current_time = datetime.now()
    malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
    malaysia_time = datetime.now(malaysia_tz)
    
    # Cycle activities every 20 seconds
    activity_idx = int(current_time.second / 20) % 3
    activities = ['RESTING', 'WALKING', 'RUNNING']
    
    # Generate realistic data
    base_hr = [65, 85, 120][activity_idx]
    base_spo2 = [98, 96, 94][activity_idx]
    base_movement = [1.2, 2.5, 5.0][activity_idx]
    
    # Add some variation
    time_var = current_time.second % 30
    hr_variation = np.sin(time_var / 5) * 8
    spo2_variation = np.cos(time_var / 10) * 2
    movement_variation = np.sin(time_var / 3) * 1.0
    
    return {
        'timestamp': current_time,
        'malaysia_time': malaysia_time.strftime('%H:%M:%S'),
        'hr': int(base_hr + hr_variation),
        'spo2': int(base_spo2 + spo2_variation),
        'temp': 36.5 + np.random.random() * 0.3,
        'activity': activities[activity_idx],
        'movement': max(0, base_movement + movement_variation),
        'battery': 85 - (current_time.minute % 60),
        'rssi': -65 - np.random.randint(0, 15),
        'is_real': SERIAL_AVAILABLE
    }

def update_data_buffers():
    """Update data buffers with current reading"""
    data = get_current_data()
    
    # Add to buffers
    st.session_state.timestamps.append(data['timestamp'])
    st.session_state.hr_data.append(data['hr'])
    st.session_state.spo2_data.append(data['spo2'])
    st.session_state.movement_data.append(data['movement'])
    st.session_state.activity_history.append(data['activity'])

# ================ GRAPH FUNCTIONS ================

def create_hr_graph():
    """Create heart rate graph"""
    if len(st.session_state.timestamps) == 0:
        return None
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(st.session_state.timestamps),
        y=list(st.session_state.hr_data),
        mode='lines+markers',
        name='Heart Rate',
        line=dict(color='#8B4513', width=3)
    ))
    
    fig.update_layout(
        title="Heart Rate (Last 60 seconds)",
        height=250,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    return fig

def create_spo2_graph():
    """Create SpO2 graph"""
    if len(st.session_state.timestamps) == 0:
        return None
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(st.session_state.timestamps),
        y=list(st.session_state.spo2_data),
        mode='lines+markers',
        name='SpO₂',
        line=dict(color='#556B2F', width=3)
    ))
    
    fig.update_layout(
        title="Blood Oxygen (Last 60 seconds)",
        height=250,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    return fig

def create_movement_graph():
    """Create movement graph"""
    if len(st.session_state.timestamps) == 0:
        return None
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(st.session_state.timestamps),
        y=list(st.session_state.movement_data),
        mode='lines+markers',
        name='Movement',
        line=dict(color='#D4A76A', width=3),
        fill='tozeroy',
        fillcolor='rgba(212, 167, 106, 0.2)'
    ))
    
    fig.update_layout(
        title="Movement Level (Last 60 seconds)",
        height=250,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    return fig

# ================ MAIN DASHBOARD ================

def main():
    """Main dashboard function"""
    
    # Update data buffers
    update_data_buffers()
    
    # Get current data
    current_data = get_current_data()
    malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
    current_time_malaysia = datetime.now(malaysia_tz)
    
    # Header
    st.markdown(f"""
    <div class="main-header">
        <h1 style="margin: 0; font-size: 2.5rem;">🏥 STEMCUBE Health Monitor</h1>
        <p style="margin: 10px 0 0 0; font-size: 1.1rem; opacity: 0.9;">
            Real-time Patient Monitoring • Malaysia Time: {current_time_malaysia.strftime('%H:%M:%S')}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("<div class='sidebar-content'>", unsafe_allow_html=True)
        
        st.markdown("### ⚙️ Control Panel")
        auto_refresh = st.toggle("🔄 Auto Refresh", value=True)
        refresh_rate = st.slider("Refresh Rate (seconds)", 1, 5, 2)
        
        st.markdown("---")
        st.markdown("### 📊 Connection")
        
        if SERIAL_AVAILABLE:
            st.success("✅ Serial Available")
        else:
            st.warning("⚠️ Demo Mode")
        
        st.markdown(f"**Last Update:** {current_data['malaysia_time']}")
        
        st.markdown("---")
        st.markdown("### 📈 Quick Stats")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("❤️ HR", f"{current_data['hr']} BPM")
        with col2:
            st.metric("🩸 SpO₂", f"{current_data['spo2']}%")
        
        st.metric("🌡️ Temp", f"{current_data['temp']:.1f}°C")
        st.metric("🚶 Activity", current_data['activity'])
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Main content - Current Metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("<div class='vital-card'>", unsafe_allow_html=True)
        hr = current_data['hr']
        
        if hr < 60:
            status = "status-warning"
            status_text = "LOW"
            color = "#FF9800"
        elif hr <= 100:
            status = "status-normal"
            status_text = "NORMAL"
            color = "#4CAF50"
        else:
            status = "status-critical"
            status_text = "HIGH"
            color = "#F44336"
        
        st.markdown(f"""
        <div style="text-align: center;">
            <div class="metric-label">HEART RATE</div>
            <div class="metric-value" style="color: {color};">{hr}</div>
            <div>BPM</div>
            <br>
            <div class="{status}">{status_text}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='vital-card'>", unsafe_allow_html=True)
        spo2 = current_data['spo2']
        
        if spo2 >= 95:
            status = "status-normal"
            status_text = "NORMAL"
            color = "#4CAF50"
        elif spo2 >= 90:
            status = "status-warning"
            status_text = "LOW"
            color = "#FF9800"
        else:
            status = "status-critical"
            status_text = "CRITICAL"
            color = "#F44336"
        
        st.markdown(f"""
        <div style="text-align: center;">
            <div class="metric-label">BLOOD OXYGEN</div>
            <div class="metric-value" style="color: {color};">{spo2}</div>
            <div>% SpO₂</div>
            <br>
            <div class="{status}">{status_text}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col3:
        st.markdown("<div class='vital-card'>", unsafe_allow_html=True)
        activity = current_data['activity']
        movement = current_data['movement']
        
        emoji = "😴" if activity == 'RESTING' else "🚶" if activity == 'WALKING' else "🏃"
        
        st.markdown(f"""
        <div style="text-align: center;">
            <div class="metric-label">ACTIVITY</div>
            <div style="font-size: 48px; margin: 10px 0;">{emoji}</div>
            <div style="font-size: 24px; color: var(--dark-chocolate); margin: 10px 0;">{activity}</div>
            <div>Movement: {movement:.1f}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Real-time Graphs
    st.markdown("### 📈 Real-time Graphs")
    
    col1, col2 = st.columns(2)
    
    with col1:
        hr_fig = create_hr_graph()
        if hr_fig:
            st.plotly_chart(hr_fig, use_container_width=True)
    
    with col2:
        spo2_fig = create_spo2_graph()
        if spo2_fig:
            st.plotly_chart(spo2_fig, use_container_width=True)
    
    # Movement graph full width
    movement_fig = create_movement_graph()
    if movement_fig:
        st.plotly_chart(movement_fig, use_container_width=True)
    
    # Data Table - FIXED THE ERROR HERE
    st.markdown("### 📋 Recent Data")
    
    if len(st.session_state.timestamps) > 0:
        # SAFE ACCESS: Get last 10 items or all if less than 10
        n_items = min(10, len(st.session_state.timestamps))
        
        recent_data = {
            'Time': [t.strftime('%H:%M:%S') for t in list(st.session_state.timestamps)[-n_items:][::-1]],
            'HR': list(st.session_state.hr_data)[-n_items:][::-1],
            'SpO₂': list(st.session_state.spo2_data)[-n_items:][::-1],
            'Movement': [f"{m:.1f}" for m in list(st.session_state.movement_data)[-n_items:][::-1]],
            'Activity': list(st.session_state.activity_history)[-n_items:][::-1]
        }
        
        df = pd.DataFrame(recent_data)
        st.dataframe(df, use_container_width=True, height=300)
    else:
        st.info("Waiting for data...")
    
    # Footer
    data_source = "REAL (Serial Available)" if SERIAL_AVAILABLE else "DEMO"
    st.markdown(f"""
    <div class="dashboard-footer">
        <p style="margin: 0; font-size: 14px;">
            🏥 <strong>STEMCUBE Health Monitoring System</strong> | 
            📍 Universiti Malaysia Pahang | 
            🇲🇾 Malaysia Time: {current_time_malaysia.strftime('%H:%M:%S')}
        </p>
        <p style="margin: 5px 0 0 0; font-size: 12px; opacity: 0.8;">
            Data Source: {data_source} | Points: {len(st.session_state.timestamps)}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Auto-refresh
    if auto_refresh:
        time.sleep(refresh_rate)
        st.rerun()

# ================ RUN DASHBOARD ================
if __name__ == "__main__":
    main()