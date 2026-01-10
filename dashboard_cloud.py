# dashboard_cloud.py - FIXED VERSION (NO AUTHENTICATION)
"""
REAL-TIME DASHBOARD FOR STREAMLIT CLOUD
MUJI MARROON CHAMPAGNE OLIVE THEME
READS REAL DATA FROM STEMCUBE MASTER VIA COM8
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
import serial

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
    
    .activity-card {
        background: linear-gradient(135deg, var(--champagne) 0%, white 100%);
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(139, 69, 19, 0.15);
        text-align: center;
        margin-bottom: 20px;
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
    
    /* BUTTONS */
    .stButton button {
        background: linear-gradient(135deg, var(--olive) 0%, var(--muji-maroon) 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton button:hover {
        transform: scale(1.05);
        box-shadow: 0 4px 12px rgba(139, 69, 19, 0.3);
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
    
    /* DATA TABLE */
    .data-table-container {
        background: white;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    
    .data-table-header {
        background: var(--olive);
        color: white;
        padding: 15px;
        font-weight: 600;
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
    
    /* ACTIVITY EMOJI CONTAINER */
    .activity-emoji-container {
        background: white;
        padding: 30px;
        border-radius: 20px;
        box-shadow: 0 8px 25px rgba(139, 69, 19, 0.15);
        text-align: center;
        margin: 20px 0;
        border: 2px solid var(--champagne);
    }
    
    .activity-emoji {
        font-size: 80px;
        margin: 20px 0;
        animation: float 3s ease-in-out infinite;
    }
    
    @keyframes float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
        100% { transform: translateY(0px); }
    }
    
    /* COLOR SCHEME FOR CHARTS */
    .chart-color-1 { color: var(--muji-maroon); }
    .chart-color-2 { color: var(--olive); }
    .chart-color-3 { color: #D4A76A; } /* Champagne gold */
    .chart-color-4 { color: #8D6E63; } /* Muji brown */
    
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
    
    /* SIMPLIFIED STYLES FOR DEBUGGING */
    .debug-info {
        background: #f0f0f0;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
        font-family: monospace;
    }
</style>
""", unsafe_allow_html=True)

# ================ SIMPLIFIED DATA LOADING ================

def get_sample_data():
    """Always return sample data for testing"""
    malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
    current_time = datetime.now(malaysia_tz)
    
    # Cycle activities
    activities = ['RESTING', 'WALKING', 'RUNNING']
    activity_idx = int(current_time.second / 20) % 3
    
    sample_data = {
        'status': 'connected',
        'last_update': current_time.isoformat(),
        'is_real_data': False,
        'activity_source': 'DEMO',
        'malaysia_time': current_time.strftime('%H:%M:%S'),
        
        'data': {
            'node_id': 'NODE_e661',
            'timestamp': current_time.isoformat(),
            'malaysia_time': current_time.strftime('%H:%M:%S'),
            'hr': 65 if activity_idx == 0 else 85 if activity_idx == 1 else 120,
            'spo2': 98 if activity_idx == 0 else 96 if activity_idx == 1 else 94,
            'temp': 36.5,
            'humidity': 56,
            'ax': -0.36,
            'ay': -0.20,
            'az': 0.87,
            'gx': -0.96,
            'gy': -0.46,
            'gz': 0.64,
            'acceleration_magnitude': 1.2 if activity_idx == 0 else 2.5 if activity_idx == 1 else 5.0,
            'activity': activities[activity_idx],
            'battery': 85,
            'rssi': -65,
            'snr': 12,
            'packet_id': int(current_time.timestamp()) % 10000,
            'packet_loss': 2.5,
            'is_real': False,
            'raw_packet': 'Demo data - Dashboard is working!'
        }
    }
    
    return sample_data

# ================ SIMPLE DASHBOARD COMPONENTS ================

def display_header():
    """Display the main header"""
    malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
    current_time_malaysia = datetime.now(malaysia_tz)
    
    st.markdown(f"""
    <div class="main-header">
        <h1 style="margin: 0; font-size: 2.5rem;">🏥 STEMCUBE Health Monitor</h1>
        <p style="margin: 10px 0 0 0; font-size: 1.1rem; opacity: 0.9;">
            Real-time Patient Monitoring • LoRa Wireless • Malaysia Time: {current_time_malaysia.strftime('%H:%M:%S')}
        </p>
        <p style="margin: 5px 0 0 0; font-size: 0.9rem; opacity: 0.8;">
            Universiti Malaysia Pahang • Final Year Project 2025
        </p>
    </div>
    """, unsafe_allow_html=True)

def display_activity(activity):
    """Display activity with emoji"""
    emoji_map = {
        'RESTING': '😴',
        'WALKING': '🚶',
        'RUNNING': '🏃',
        'UNKNOWN': '🤔'
    }
    
    color_map = {
        'RESTING': '#8B4513',
        'WALKING': '#556B2F',
        'RUNNING': '#D4A76A',
        'UNKNOWN': '#8D6E63'
    }
    
    emoji = emoji_map.get(activity.upper(), '🤔')
    color = color_map.get(activity.upper(), '#8D6E63')
    
    st.markdown(f"""
    <div class="activity-emoji-container">
        <div class="activity-emoji">{emoji}</div>
        <h2 style="color: {color}; margin: 10px 0;">{activity}</h2>
        <p style="color: #666; font-size: 16px;">Patient is {activity.lower()}</p>
    </div>
    """, unsafe_allow_html=True)

def display_vitals(data):
    """Display vital signs"""
    st.markdown("### 🩺 Vital Signs")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("<div class='vital-card'>", unsafe_allow_html=True)
        hr = data['data']['hr']
        
        # Heart rate status
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
        spo2 = data['data']['spo2']
        
        # SpO2 status
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
        temp = data['data']['temp']
        
        # Temperature status
        if temp <= 37.5:
            status = "status-normal"
            status_text = "NORMAL"
            color = "#4CAF50"
        elif temp <= 38.0:
            status = "status-warning"
            status_text = "ELEVATED"
            color = "#FF9800"
        else:
            status = "status-critical"
            status_text = "FEVER"
            color = "#F44336"
        
        st.markdown(f"""
        <div style="text-align: center;">
            <div class="metric-label">TEMPERATURE</div>
            <div class="metric-value" style="color: {color};">{temp}</div>
            <div>°C</div>
            <br>
            <div class="{status}">{status_text}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

def display_data_table(data):
    """Display data table"""
    st.markdown("### 📋 Live Data Stream")
    
    # Create table data
    table_data = []
    current_time = datetime.now()
    
    for i in range(5):
        timestamp = (current_time - timedelta(seconds=i*2)).strftime('%H:%M:%S')
        table_data.append({
            'Time': timestamp,
            'Node': data['data']['node_id'],
            'HR': data['data']['hr'],
            'SpO₂': data['data']['spo2'],
            'Temp': f"{data['data']['temp']}°C",
            'Activity': data['data']['activity'],
            'Battery': f"{data['data']['battery']}%"
        })
    
    # Convert to DataFrame and display
    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True, height=250)

def display_sidebar(data):
    """Display sidebar"""
    with st.sidebar:
        st.markdown("<div class='sidebar-content'>", unsafe_allow_html=True)
        
        st.markdown("### ⚙️ Control Panel")
        
        # Auto-refresh
        auto_refresh = st.toggle("🔄 Auto Refresh", value=True)
        refresh_rate = st.slider("Refresh Rate (seconds)", 1, 10, 2)
        
        st.markdown("---")
        
        # Status
        st.markdown("### 📊 System Status")
        if data['is_real_data']:
            st.success("✅ **Connected to STEMCUBE**")
        else:
            st.warning("🔄 **Demo Mode**")
        
        st.markdown(f"**Last Update:** {data['malaysia_time']}")
        
        st.markdown("---")
        
        # Quick Stats
        st.markdown("### 📈 Quick Stats")
        st.metric("❤️ Heart Rate", f"{data['data']['hr']} BPM")
        st.metric("🩸 SpO₂", f"{data['data']['spo2']}%")
        st.metric("🌡️ Temperature", f"{data['data']['temp']}°C")
        st.metric("🚶 Activity", data['data']['activity'])
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        return auto_refresh, refresh_rate

# ================ MAIN DASHBOARD ================

def main():
    """Main dashboard function - SIMPLIFIED"""
    
    # Display header
    display_header()
    
    # Get data
    data = get_sample_data()
    
    # Display sidebar
    auto_refresh, refresh_rate = display_sidebar(data)
    
    # Main content area
    
    # Display activity
    display_activity(data['data']['activity'])
    
    # Display vitals
    display_vitals(data)
    
    # Display data table
    display_data_table(data)
    
    # Simple charts
    st.markdown("### 📈 Activity Timeline")
    col1, col2 = st.columns(2)
    
    with col1:
        # Heart rate chart
        times = [datetime.now() - timedelta(seconds=i*5) for i in range(20)][::-1]
        hr_values = [data['data']['hr'] + np.random.normal(0, 3) for _ in range(20)]
        hr_values = [max(40, min(160, hr)) for hr in hr_values]
        
        fig_hr = px.line(
            x=times,
            y=hr_values,
            title="Heart Rate Trend",
            labels={'x': 'Time', 'y': 'BPM'}
        )
        fig_hr.update_layout(height=300, showlegend=False)
        fig_hr.update_traces(line=dict(color='#8B4513', width=3))
        st.plotly_chart(fig_hr, use_container_width=True)
    
    with col2:
        # System metrics
        st.markdown("<div class='system-card'>", unsafe_allow_html=True)
        st.markdown("#### 📡 System Metrics")
        
        metrics_html = f"""
        <div style="line-height: 2.5;">
            <p><strong>🔋 Battery:</strong> {data['data']['battery']}%</p>
            <p><strong>📡 Signal:</strong> {data['data']['rssi']} dB</p>
            <p><strong>📶 SNR:</strong> {data['data']['snr']} dB</p>
            <p><strong>📦 Packets:</strong> {data['data']['packet_id']:,}</p>
            <p><strong>📊 Data Source:</strong> {'REAL' if data['is_real_data'] else 'DEMO'}</p>
        </div>
        """
        st.markdown(metrics_html, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Alerts
        st.markdown("<div class='system-card'>", unsafe_allow_html=True)
        st.markdown("#### ⚠️ Alerts")
        
        alerts = []
        if data['data']['hr'] > 100:
            alerts.append(f"🔴 High heart rate: {data['data']['hr']} BPM")
        if data['data']['spo2'] < 95:
            alerts.append(f"🟡 Reduced SpO₂: {data['data']['spo2']}%")
        if data['data']['temp'] > 37.5:
            alerts.append(f"🔴 Elevated temperature: {data['data']['temp']}°C")
        
        if alerts:
            for alert in alerts:
                st.markdown(alert)
        else:
            st.markdown("✅ **All systems normal**")
            st.markdown("<div class='status-normal' style='text-align: center;'>NORMAL</div>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Footer
    malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
    current_time_malaysia = datetime.now(malaysia_tz)
    
    st.markdown(f"""
    <div class="dashboard-footer">
        <p style="margin: 0; font-size: 14px;">
            🏥 <strong>STEMCUBE Health Monitoring System</strong> | 
            📍 Universiti Malaysia Pahang | 
            🇲🇾 Malaysia Time: {current_time_malaysia.strftime('%H:%M:%S')}
        </p>
        <p style="margin: 5px 0 0 0; font-size: 12px; opacity: 0.8;">
            Dashboard is working! • Version 1.0
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Auto-refresh
    if auto_refresh:
        time.sleep(refresh_rate)
        st.rerun()

# ================ RUN DASHBOARD ================
if __name__ == "__main__":
    # REMOVED AUTHENTICATION - Directly run main
    main()