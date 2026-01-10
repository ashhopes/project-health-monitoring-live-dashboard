# dashboard_cloud.py - STREAMLIT CLOUD VERSION (FIXED)
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
import os
import sys

# ================ TRY TO IMPORT SERIAL ================
try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    st.warning("⚠️ pyserial not installed. Using demo data.")

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
</style>
""", unsafe_allow_html=True)

# ================ ACTIVITY EMOJIS ================
ACTIVITY_CONFIG = {
    'RESTING': {'emoji': '😴', 'color': '#8B4513', 'description': 'Patient is resting'},
    'WALKING': {'emoji': '🚶', 'color': '#556B2F', 'description': 'Patient is walking'},
    'RUNNING': {'emoji': '🏃', 'color': '#D4A76A', 'description': 'Patient is running'}
}

# ================ GENERATE DEMO DATA ================
def generate_demo_data():
    """Generate demo data for Streamlit Cloud"""
    malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
    current_time = datetime.now(malaysia_tz)
    
    # Cycle through activities
    activities = ['RESTING', 'WALKING', 'RUNNING']
    activity_idx = int(current_time.minute / 20) % 3
    
    data = {
        'status': 'connected',
        'last_update': current_time.isoformat(),
        'is_real_data': False,
        'activity_source': 'DEMO_CLOUD',
        'malaysia_time': current_time.strftime('%H:%M:%S'),
        
        'data': {
            'node_id': 'NODE_CLOUD',
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
            'is_real': False
        }
    }
    
    return data

# ================ DISPLAY ACTIVITY ================
def display_activity_with_emoji(activity):
    """Display activity with animated emoji"""
    config = ACTIVITY_CONFIG.get(activity.upper(), ACTIVITY_CONFIG['RESTING'])
    
    st.markdown(f"""
    <div class="activity-emoji-container">
        <div class="activity-emoji">{config['emoji']}</div>
        <h2 style="color: {config['color']}; margin: 10px 0;">{activity}</h2>
        <p style="color: #666; font-size: 16px;">{config['description']}</p>
    </div>
    """, unsafe_allow_html=True)

# ================ TAB 1: HEALTH VITALS ================
def tab_health_vitals(data):
    """Tab 1: Health Vitals Display"""
    current = data['data']
    
    st.markdown("### 🩺 Health Vitals")
    
    # Activity Display
    display_activity_with_emoji(current.get('activity', 'RESTING'))
    
    # Vital Signs in columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("<div class='vital-card'>", unsafe_allow_html=True)
        hr = current['hr']
        
        # Determine status
        if hr < 60:
            status_class = "status-warning"
            status_text = "LOW"
            color = "#FF9800"
        elif hr <= 100:
            status_class = "status-normal"
            status_text = "NORMAL"
            color = "#4CAF50"
        else:
            status_class = "status-critical"
            status_text = "HIGH"
            color = "#F44336"
        
        st.markdown(f"""
        <div style="text-align: center;">
            <div class="metric-label">HEART RATE</div>
            <div class="metric-value" style="color: {color};">{hr}</div>
            <div>BPM</div>
            <br>
            <div class="{status_class}">{status_text}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='vital-card'>", unsafe_allow_html=True)
        spo2 = current['spo2']
        
        # SpO2 status
        if spo2 >= 95:
            status_class = "status-normal"
            status_text = "NORMAL"
            color = "#4CAF50"
        elif spo2 >= 90:
            status_class = "status-warning"
            status_text = "LOW"
            color = "#FF9800"
        else:
            status_class = "status-critical"
            status_text = "CRITICAL"
            color = "#F44336"
        
        st.markdown(f"""
        <div style="text-align: center;">
            <div class="metric-label">BLOOD OXYGEN</div>
            <div class="metric-value" style="color: {color};">{spo2}</div>
            <div>% SpO₂</div>
            <br>
            <div class="{status_class}">{status_text}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col3:
        st.markdown("<div class='vital-card'>", unsafe_allow_html=True)
        temp = current['temp']
        
        # Temperature status
        if temp <= 37.5:
            status_class = "status-normal"
            status_text = "NORMAL"
            color = "#4CAF50"
        elif temp <= 38.0:
            status_class = "status-warning"
            status_text = "ELEVATED"
            color = "#FF9800"
        else:
            status_class = "status-critical"
            status_text = "FEVER"
            color = "#F44336"
        
        st.markdown(f"""
        <div style="text-align: center;">
            <div class="metric-label">TEMPERATURE</div>
            <div class="metric-value" style="color: {color};">{temp}</div>
            <div>°C</div>
            <br>
            <div class="{status_class}">{status_text}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ================ TAB 2: SYSTEM STATUS ================
def tab_system_status(data):
    """Tab 2: System Status"""
    current = data['data']
    
    st.markdown("### 📡 System Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Battery Status
        st.markdown("<div class='system-card'>", unsafe_allow_html=True)
        st.markdown("#### 🔋 Battery")
        battery = current.get('battery', 85)
        
        fig_battery = go.Figure(go.Indicator(
            mode="gauge+number",
            value=battery,
            title={'text': "Battery Level", 'font': {'size': 14}},
            number={'suffix': "%", 'font': {'size': 28}},
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
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        # Signal Status
        st.markdown("<div class='system-card'>", unsafe_allow_html=True)
        st.markdown("#### 📶 Signal Strength")
        rssi = current.get('rssi', -65)
        
        st.metric("RSSI", f"{rssi} dB")
        st.metric("SNR", f"{current.get('snr', 12)} dB")
        st.metric("Packet Loss", f"{current.get('packet_loss', 2.5)}%")
        st.markdown("</div>", unsafe_allow_html=True)

# ================ TAB 3: ANALYTICS ================
def tab_analytics(data):
    """Tab 3: Analytics & Trends"""
    current = data['data']
    
    st.markdown("### 📊 Analytics")
    
    # Create sample chart
    times = pd.date_range(start='now', periods=30, freq='1min')
    hr_values = [current['hr'] + np.random.normal(0, 5) for _ in range(30)]
    hr_values = [max(40, min(160, hr)) for hr in hr_values]
    
    fig = px.line(
        x=times,
        y=hr_values,
        title="Heart Rate Trend (Last 30 Minutes)",
        labels={'x': 'Time', 'y': 'BPM'}
    )
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)
    
    # Data table
    st.markdown("#### Recent Data")
    table_data = []
    for i in range(10):
        table_data.append({
            'Time': (datetime.now() - timedelta(minutes=i)).strftime('%H:%M'),
            'HR': int(current['hr'] + np.random.normal(0, 3)),
            'SpO₂': int(current['spo2'] + np.random.normal(0, 1)),
            'Temp': f"{current['temp']:.1f}°C",
            'Activity': current['activity']
        })
    
    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True)

# ================ MAIN DASHBOARD ================
def main():
    """Main dashboard function"""
    
    # Malaysia timezone
    malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
    current_time_malaysia = datetime.now(malaysia_tz)
    
    # Header
    st.markdown(f"""
    <div class="main-header">
        <h1 style="margin: 0; font-size: 2.5rem;">🏥 STEMCUBE Health Monitor</h1>
        <p style="margin: 10px 0 0 0; font-size: 1.1rem; opacity: 0.9;">
            Streamlit Cloud Dashboard • Malaysia Time: {current_time_malaysia.strftime('%H:%M:%S')}
        </p>
        <p style="margin: 5px 0 0 0; font-size: 0.9rem; opacity: 0.8;">
            Universiti Malaysia Pahang • Final Year Project 2025
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Show warning if serial not available
    if not SERIAL_AVAILABLE:
        st.warning("""
        ⚠️ **Demo Mode Active**
        - pyserial is not installed on Streamlit Cloud
        - Showing demo data only
        - For real data, run locally with COM8 connected
        """)
    
    # Get data
    data = generate_demo_data()
    
    # Sidebar
    with st.sidebar:
        st.markdown("<div class='sidebar-content'>", unsafe_allow_html=True)
        st.markdown("### ⚙️ Control Panel")
        
        auto_refresh = st.toggle("🔄 Auto Refresh", value=True)
        refresh_rate = st.slider("Refresh Rate (seconds)", 1, 10, 2)
        
        st.markdown("---")
        st.markdown("### 📊 System Info")
        
        if data['is_real_data']:
            st.success("✅ **Connected to STEMCUBE**")
        else:
            st.info("🔄 **Demo Mode**")
        
        st.metric("❤️ HR", f"{data['data']['hr']} BPM")
        st.metric("🩸 SpO₂", f"{data['data']['spo2']}%")
        st.metric("🌡️ Temp", f"{data['data']['temp']}°C")
        st.metric("🚶 Activity", data['data']['activity'])
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["🩺 Health Vitals", "📡 System Status", "📊 Analytics"])
    
    with tab1:
        tab_health_vitals(data)
    
    with tab2:
        tab_system_status(data)
    
    with tab3:
        tab_analytics(data)
    
    # Footer
    st.markdown(f"""
    <div class="dashboard-footer">
        <p style="margin: 0; font-size: 14px;">
            🏥 <strong>STEMCUBE Health Monitoring System</strong> | 
            📍 Universiti Malaysia Pahang | 
            🇲🇾 Malaysia Time: {current_time_malaysia.strftime('%H:%M:%S')}
        </p>
        <p style="margin: 5px 0 0 0; font-size: 12px; opacity: 0.8;">
            Streamlit Cloud Version • Data Source: {data['activity_source']}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Auto-refresh
    if auto_refresh:
        time.sleep(refresh_rate)
        st.rerun()

# ================ RUN DASHBOARD ================
if __name__ == "__main__":
    # NO AUTHENTICATION - Direct access
    main()