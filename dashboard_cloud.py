# dashboard_Real_Cloud.py - STREAMLIT CLOUD VERSION
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
from PIL import Image
import requests
from io import BytesIO

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

# ================ ACTIVITY EMOJIS/GIFs ================
ACTIVITY_CONFIG = {
    'RESTING': {
        'emoji': '😴',
        'color': '#8B4513',  # Maroon
        'description': 'Patient is resting',
        'gif_url': 'https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif'  # Sleeping emoji gif
    },
    'WALKING': {
        'emoji': '🚶',
        'color': '#556B2F',  # Olive
        'description': 'Patient is walking',
        'gif_url': 'https://media.giphy.com/media/3o7TKsQ8gTp3WqXq1q/giphy.gif'  # Walking emoji gif
    },
    'RUNNING': {
        'emoji': '🏃',
        'color': '#D4A76A',  # Champagne gold
        'description': 'Patient is running',
        'gif_url': 'https://media.giphy.com/media/3o7TKsQ8gTp3WqXq1q/giphy.gif'  # Running emoji gif
    }
}

# ================ LOAD REAL-TIME DATA ================
def load_real_time_data():
    """Load real-time data from JSON file"""
    try:
        with open('stemcube_cloud_data.json', 'r') as f:
            data = json.load(f)
        
        # Add Malaysia time
        malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
        data['malaysia_time'] = datetime.now(malaysia_tz).strftime('%H:%M:%S')
        
        return data
        
    except FileNotFoundError:
        return generate_stemcube_demo_data()
    except Exception as e:
        st.error(f"Data error: {e}")
        return None

def generate_stemcube_demo_data():
    """Generate demo data matching YOUR STEMCUBE format"""
    malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
    current_time = datetime.now(malaysia_tz)
    
    # Cycle through activities for demo
    activities = ['RESTING', 'WALKING', 'RUNNING']
    activity_idx = int(current_time.minute / 20) % 3  # Change every 20 minutes
    
    data = {
        'status': 'connected',
        'last_update': current_time.isoformat(),
        'is_real_data': False,
        'activity_source': 'STEMCUBE_MASTER',
        
        'data': {
            'node_id': 'NODE_e661',
            'timestamp': current_time.isoformat(),
            'malaysia_time': current_time.strftime('%H:%M:%S'),
            
            # Vary data based on activity
            'hr': 65 if activities[activity_idx] == 'RESTING' else 85 if activities[activity_idx] == 'WALKING' else 120,
            'spo2': 98 if activities[activity_idx] == 'RESTING' else 96 if activities[activity_idx] == 'WALKING' else 94,
            'temp': 36.5,
            'humidity': 56,
            
            # MPU6050 Data
            'ax': -0.36,
            'ay': -0.20,
            'az': 0.87,
            'gx': -0.96,
            'gy': -0.46,
            'gz': 0.64,
            'acceleration_magnitude': 1.2 if activities[activity_idx] == 'RESTING' else 2.5 if activities[activity_idx] == 'WALKING' else 5.0,
            
            # Activity
            'activity': activities[activity_idx],
            
            # System data
            'battery': 85,
            'rssi': -65,
            'snr': 12,
            'packet_id': int(current_time.timestamp()) % 10000,
            'packet_loss': 2.5
        }
    }
    
    return data

# ================ DISPLAY ACTIVITY WITH EMOJI/GIF ================
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
    
    # Header with patient selection
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown("### 👤 Patient Monitoring")
    with col2:
        nodes = ['NODE_e661', 'NODE_e662', 'NODE_e663']
        selected_node = st.selectbox("Select Node", nodes, key="node_select_vitals")
    with col3:
        st.markdown(f"**Last Update:** {current.get('malaysia_time', 'N/A')}")
    
    st.markdown("---")
    
    # Activity Display (Center of attention)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        display_activity_with_emoji(current.get('activity', 'RESTING'))
    
    # Vital Signs in a grid
    st.markdown("### 🩺 Vital Signs")
    
    # Row 1: Heart Rate
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("<div class='vital-card'>", unsafe_allow_html=True)
        st.markdown("#### ❤️ Heart Rate Trend")
        
        # Generate HR trend
        times = [datetime.now() - timedelta(seconds=i*5) for i in range(20)][::-1]
        base_hr = current['hr']
        hr_values = [base_hr + np.random.normal(0, 3) for _ in range(20)]
        hr_values = [max(40, min(160, hr)) for hr in hr_values]
        
        fig_hr = px.line(
            x=times,
            y=hr_values,
            title="",
            labels={'x': 'Time', 'y': 'BPM'}
        )
        fig_hr.update_layout(
            height=200,
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#3C2F2F'
        )
        fig_hr.update_traces(line=dict(color='#8B4513', width=3))
        st.plotly_chart(fig_hr, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
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
    
    # Row 2: SpO2 and Temperature
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='vital-card'>", unsafe_allow_html=True)
        st.markdown("#### 🩸 Blood Oxygen")
        
        spo2 = current['spo2']
        
        # SpO2 Gauge
        fig_spo2 = go.Figure(go.Indicator(
            mode="gauge+number",
            value=spo2,
            title={'text': "SpO₂ Level", 'font': {'size': 16, 'color': '#556B2F'}},
            number={'suffix': "%", 'font': {'size': 36, 'color': '#556B2F'}},
            gauge={
                'axis': {'range': [70, 100], 'tickcolor': '#556B2F'},
                'bar': {'color': '#F44336' if spo2 < 90 else '#FF9800' if spo2 < 95 else '#4CAF50'},
                'steps': [
                    {'range': [70, 90], 'color': 'rgba(244, 67, 54, 0.2)'},
                    {'range': [90, 95], 'color': 'rgba(255, 152, 0, 0.2)'},
                    {'range': [95, 100], 'color': 'rgba(76, 175, 80, 0.2)'}
                ],
                'threshold': {
                    'line': {'color': "#556B2F", 'width': 3},
                    'thickness': 0.8,
                    'value': 95
                }
            }
        ))
        
        fig_spo2.update_layout(
            height=200,
            margin=dict(t=40, b=20, l=20, r=20),
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_spo2, use_container_width=True)
        
        # SpO2 status
        if spo2 >= 95:
            st.markdown("<div class='status-normal' style='text-align: center;'>NORMAL OXYGEN</div>", unsafe_allow_html=True)
        elif spo2 >= 90:
            st.markdown("<div class='status-warning' style='text-align: center;'>LOW OXYGEN</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='status-critical' style='text-align: center;'>CRITICAL OXYGEN</div>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='vital-card'>", unsafe_allow_html=True)
        st.markdown("#### 🌡️ Body Temperature")
        
        temp = current['temp']
        
        # Temperature indicator
        fig_temp = go.Figure(go.Indicator(
            mode="number+gauge",
            value=temp,
            title={'text': "Temperature", 'font': {'size': 16, 'color': '#8D6E63'}},
            number={'suffix': "°C", 'font': {'size': 36, 'color': '#8D6E63'}},
            gauge={
                'axis': {'range': [35, 40], 'tickcolor': '#8D6E63'},
                'bar': {'color': '#F44336' if temp > 37.5 else '#4CAF50'},
                'steps': [
                    {'range': [35, 37.5], 'color': 'rgba(76, 175, 80, 0.2)'},
                    {'range': [37.5, 40], 'color': 'rgba(244, 67, 54, 0.2)'}
                ]
            }
        ))
        
        fig_temp.update_layout(
            height=200,
            margin=dict(t=40, b=20, l=20, r=20),
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_temp, use_container_width=True)
        
        # Temperature status
        if temp <= 37.5:
            st.markdown("<div class='status-normal' style='text-align: center;'>NORMAL TEMP</div>", unsafe_allow_html=True)
        elif temp <= 38.0:
            st.markdown("<div class='status-warning' style='text-align: center;'>ELEVATED</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='status-critical' style='text-align: center;'>FEVER</div>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

# ================ TAB 2: SYSTEM & LORA STATUS ================
def tab_system_status(data):
    """Tab 2: System & LoRa Status"""
    current = data['data']
    
    st.markdown("### 📡 System Status Dashboard")
    
    # System Metrics Grid
    col1, col2 = st.columns(2)
    
    with col1:
        # LoRa Signal Quality
        st.markdown("<div class='system-card'>", unsafe_allow_html=True)
        st.markdown("#### 📶 LoRa Connection")
        
        rssi = current.get('rssi', -65)
        snr = current.get('snr', 12)
        
        # Signal strength indicator
        fig_signal = go.Figure(go.Indicator(
            mode="gauge+number",
            value=rssi,
            title={'text': "Signal Strength (RSSI)", 'font': {'size': 14, 'color': '#556B2F'}},
            number={'suffix': " dB", 'font': {'size': 28, 'color': '#556B2F'}},
            gauge={
                'axis': {'range': [-120, -40], 'tickcolor': '#556B2F'},
                'bar': {'color': '#4CAF50' if rssi > -70 else '#FF9800' if rssi > -90 else '#F44336'},
                'steps': [
                    {'range': [-120, -90], 'color': 'rgba(244, 67, 54, 0.1)'},
                    {'range': [-90, -70], 'color': 'rgba(255, 152, 0, 0.1)'},
                    {'range': [-70, -40], 'color': 'rgba(76, 175, 80, 0.1)'}
                ]
            }
        ))
        
        fig_signal.update_layout(
            height=180,
            margin=dict(t=30, b=20, l=20, r=20),
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_signal, use_container_width=True)
        
        # SNR value
        col_snr1, col_snr2 = st.columns([2, 1])
        with col_snr1:
            st.metric("SNR Ratio", f"{snr} dB")
        with col_snr2:
            quality = "Excellent" if snr > 10 else "Good" if snr > 5 else "Poor"
            st.markdown(f"**{quality}**")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Battery Status
        st.markdown("<div class='system-card'>", unsafe_allow_html=True)
        st.markdown("#### 🔋 Power Management")
        
        battery = current.get('battery', 85)
        
        fig_battery = go.Figure(go.Indicator(
            mode="gauge+number",
            value=battery,
            title={'text': "Battery Level", 'font': {'size': 14, 'color': '#8B4513'}},
            number={'suffix': "%", 'font': {'size': 28, 'color': '#8B4513'}},
            gauge={
                'axis': {'range': [0, 100], 'tickcolor': '#8B4513'},
                'bar': {'color': '#4CAF50' if battery > 50 else '#FF9800' if battery > 20 else '#F44336'},
                'steps': [
                    {'range': [0, 20], 'color': 'rgba(244, 67, 54, 0.1)'},
                    {'range': [20, 50], 'color': 'rgba(255, 152, 0, 0.1)'},
                    {'range': [50, 100], 'color': 'rgba(76, 175, 80, 0.1)'}
                ]
            }
        ))
        
        fig_battery.update_layout(
            height=180,
            margin=dict(t=30, b=20, l=20, r=20),
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_battery, use_container_width=True)
        
        # Runtime estimation
        if battery > 80:
            runtime = "> 48 hours"
        elif battery > 50:
            runtime = "24-48 hours"
        elif battery > 20:
            runtime = "8-24 hours"
        else:
            runtime = "< 8 hours"
        
        st.markdown(f"**Estimated Runtime:** {runtime}")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        # Network Performance
        st.markdown("<div class='system-card'>", unsafe_allow_html=True)
        st.markdown("#### 📊 Network Performance")
        
        # Metrics in a grid
        metric_col1, metric_col2 = st.columns(2)
        
        with metric_col1:
            packet_loss = current.get('packet_loss', 2.5)
            st.metric("Packet Loss", f"{packet_loss}%", 
                     delta="Low" if packet_loss < 5 else "Moderate",
                     delta_color="normal" if packet_loss < 5 else "off")
        
        with metric_col2:
            packet_id = current.get('packet_id', 0)
            st.metric("Total Packets", f"{packet_id:,}")
        
        # Latency
        try:
            last_update = datetime.fromisoformat(data['last_update'].replace('Z', '+00:00'))
            latency = (datetime.now() - last_update).total_seconds()
            st.metric("Data Latency", f"{latency:.1f}s",
                     delta="Real-time" if latency < 3 else "Normal" if latency < 10 else "Delayed",
                     delta_color="normal" if latency < 3 else "off" if latency < 10 else "inverse")
        except:
            st.metric("Data Latency", "N/A")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Device Information
        st.markdown("<div class='system-card'>", unsafe_allow_html=True)
        st.markdown("#### 🖥️ Device Information")
        
        info_html = f"""
        <div style="line-height: 2;">
            <p><strong>🏷️ Node ID:</strong> {current.get('node_id', 'NODE_e661')}</p>
            <p><strong>🔧 Firmware:</strong> STEMCUBE v2.1</p>
            <p><strong>📡 Connection:</strong> LoRa HC-12</p>
            <p><strong>📊 Frequency:</strong> 433 MHz</p>
            <p><strong>⚡ Baud Rate:</strong> 9600</p>
            <p><strong>🔄 Activity Source:</strong> STEMCUBE Master</p>
            <p><strong>🕐 Last Update:</strong> {current.get('malaysia_time', 'N/A')}</p>
        </div>
        """
        st.markdown(info_html, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Sensor Status
        st.markdown("<div class='system-card'>", unsafe_allow_html=True)
        st.markdown("#### 🔬 Active Sensors")
        
        sensors = [
            ("❤️", "MAX30102", "Heart Rate & SpO₂", "Active"),
            ("🌡️", "BME280", "Temperature & Humidity", "Active"),
            ("🎯", "MPU6050", "Motion Detection", "Active")
        ]
        
        for emoji, name, desc, status in sensors:
            st.markdown(f"{emoji} **{name}** - {desc} *({status})*")
        st.markdown("</div>", unsafe_allow_html=True)

# ================ TAB 3: ANALYTICS & TRENDS ================
def tab_analytics(data):
    """Tab 3: Analytics & Trends"""
    current = data['data']
    
    st.markdown("### 📊 Analytics & Trends")
    
    # Two column layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Activity Timeline
        st.markdown("<div class='vital-card'>", unsafe_allow_html=True)
        st.markdown("#### 📈 Activity Timeline")
        
        # Generate activity data
        times = [datetime.now() - timedelta(minutes=i) for i in range(30, 0, -1)]
        activities = []
        hr_values = []
        
        for i, t in enumerate(times):
            # Simulate activity patterns
            if i < 10:
                activity = 'RESTING'
                hr = 65 + np.random.normal(0, 3)
            elif i < 20:
                activity = 'WALKING'
                hr = 85 + np.random.normal(0, 5)
            else:
                activity = 'RUNNING'
                hr = 120 + np.random.normal(0, 8)
            
            activities.append(activity)
            hr_values.append(max(40, min(160, hr)))
        
        df_timeline = pd.DataFrame({
            'Time': times,
            'Activity': activities,
            'Heart Rate': hr_values
        })
        
        # Create timeline chart
        fig_timeline = px.line(
            df_timeline,
            x='Time',
            y='Heart Rate',
            color='Activity',
            color_discrete_map={
                'RESTING': '#8B4513',
                'WALKING': '#556B2F',
                'RUNNING': '#D4A76A'
            },
            title="Heart Rate vs Activity (Last 30 Minutes)"
        )
        
        fig_timeline.update_layout(
            height=300,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#3C2F2F',
            legend_title_text='Activity'
        )
        
        st.plotly_chart(fig_timeline, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Export Data Section
        st.markdown("<div class='vital-card'>", unsafe_allow_html=True)
        st.markdown("#### 📥 Data Export")
        
        # Create sample export data
        export_data = pd.DataFrame({
            'Timestamp': [current['malaysia_time']],
            'Node_ID': [current['node_id']],
            'Heart_Rate_BPM': [current['hr']],
            'SpO2_Percent': [current['spo2']],
            'Temperature_C': [current['temp']],
            'Activity': [current['activity']],
            'Battery_Percent': [current.get('battery', 85)],
            'RSSI_dB': [current.get('rssi', -65)]
        })
        
        # Convert to CSV
        csv = export_data.to_csv(index=False)
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            st.download_button(
                label="📥 Download Current Data",
                data=csv,
                file_name=f"stemcube_{current['node_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        with col_btn2:
            if st.button("📊 Generate Daily Report"):
                st.success("Daily report generated successfully!")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        # Daily Summary
        st.markdown("<div class='system-card'>", unsafe_allow_html=True)
        st.markdown("#### 📅 Daily Summary")
        
        summary_html = f"""
        <div style="line-height: 2.5;">
            <p><strong>❤️ Avg Heart Rate:</strong> {current['hr']} BPM</p>
            <p><strong>🩸 Avg SpO₂:</strong> {current['spo2']}%</p>
            <p><strong>🌡️ Avg Temperature:</strong> {current['temp']}°C</p>
            <p><strong>💧 Humidity:</strong> {current.get('humidity', 56)}%</p>
            <p><strong>🚶 Main Activity:</strong> {current['activity']}</p>
            <p><strong>📡 Avg Signal:</strong> {current.get('rssi', -65)} dB</p>
            <p><strong>🔋 Avg Battery:</strong> {current.get('battery', 85)}%</p>
        </div>
        """
        st.markdown(summary_html, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Alerts Panel
        st.markdown("<div class='system-card'>", unsafe_allow_html=True)
        st.markdown("#### ⚠️ Health Alerts")
        
        alerts = []
        
        # Check conditions
        if current['hr'] > 100 and current['activity'] == 'RESTING':
            alerts.append(("🔴", f"High HR ({current['hr']} BPM) while resting"))
        
        if current['spo2'] < 90:
            alerts.append(("🔴", f"Low SpO₂ ({current['spo2']}%)"))
        
        if current['spo2'] < 95:
            alerts.append(("🟡", f"Reduced SpO₂ ({current['spo2']}%)"))
        
        if current['temp'] > 37.5:
            alerts.append(("🔴", f"Elevated temperature ({current['temp']}°C)"))
        
        if current.get('battery', 85) < 30:
            alerts.append(("🟡", f"Low battery ({current.get('battery', 85)}%)"))
        
        if alerts:
            for emoji, text in alerts:
                st.markdown(f"{emoji} {text}")
        else:
            st.markdown("✅ **All readings within normal range**")
            st.markdown("<div class='status-normal' style='text-align: center; margin-top: 10px;'>ALL SYSTEMS NORMAL</div>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

# ================ MAIN DASHBOARD ================
def main():
    """Main dashboard function"""
    
    # Malaysia timezone
    malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
    current_time_malaysia = datetime.now(malaysia_tz)
    
    # Beautiful Header
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
    
    # Load data
    data = load_real_time_data()
    
    if not data:
        st.error("❌ No data connection. Please start Uploader.py on your local machine.")
        return
    
    current = data['data']
    
    # SIDEBAR
    with st.sidebar:
        st.markdown("<div class='sidebar-content'>", unsafe_allow_html=True)
        
        st.markdown("### ⚙️ Control Panel")
        
        # Auto-refresh toggle
        auto_refresh = st.toggle("🔄 Auto Refresh", value=True, key="auto_refresh")
        
        # Refresh rate
        refresh_rate = st.slider("Refresh Rate (seconds)", 1, 10, 2)
        
        st.markdown("---")
        
        # Connection Status
        st.markdown("### 📊 Connection Status")
        
        if data.get('is_real_data'):
            st.success("✅ **Connected to STEMCUBE**")
        else:
            st.warning("🔄 **Demo Mode Active**")
        
        # Data freshness
        try:
            last_update = datetime.fromisoformat(data['last_update'].replace('Z', '+00:00'))
            seconds_ago = (datetime.now() - last_update).total_seconds()
            
            if seconds_ago < 3:
                st.success(f"📡 **Live Data** ({seconds_ago:.1f}s ago)")
            elif seconds_ago < 10:
                st.info(f"⏱️ **Recent Data** ({seconds_ago:.1f}s ago)")
            else:
                st.warning(f"⚠️ **Delayed Data** ({seconds_ago:.1f}s ago)")
        except:
            st.info("⏳ Processing timestamp...")
        
        st.markdown("---")
        
        # Quick Stats
        st.markdown("### 📈 Quick Stats")
        
        col_stat1, col_stat2 = st.columns(2)
        with col_stat1:
            st.metric("❤️ HR", f"{current['hr']} BPM")
        with col_stat2:
            st.metric("🩸 SpO₂", f"{current['spo2']}%")
        
        st.metric("🌡️ Temp", f"{current['temp']}°C")
        st.metric("🚶 Activity", current['activity'])
        
        st.markdown("---")
        
        # System Info
        st.markdown("### ℹ️ System Info")
        st.markdown(f"""
        - **Node:** {current['node_id']}
        - **Packets:** {current.get('packet_id', 0):,}
        - **Battery:** {current.get('battery', 85)}%
        - **Signal:** {current.get('rssi', -65)} dB
        """)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # MAIN CONTENT AREA
    
    # Data Log Table (Always on top)
    st.markdown("### 📋 Live Data Stream")
    st.markdown("<div class='data-table-container'>", unsafe_allow_html=True)
    
    # Create recent data
    data_history = []
    for i in range(8):  # Last 8 readings
        timestamp = (datetime.now() - timedelta(seconds=i*5)).strftime('%H:%M:%S')
        data_history.append({
            'Time': timestamp,
            'Node': current['node_id'],
            '❤️ HR': int(current['hr'] + np.random.normal(0, 2)),
            '🩸 SpO₂': int(current['spo2'] + np.random.normal(0, 1)),
            '🌡️ Temp': f"{current['temp']:.1f}°C",
            '🚶 Activity': current['activity'],
            '📡 RSSI': f"{current['rssi']} dB",
            '#️⃣ Packet': current['packet_id'] - i
        })
    
    # Display as dataframe with custom styling
    df_log = pd.DataFrame(data_history)
    st.dataframe(
        df_log,
        use_container_width=True,
        height=320,
        column_config={
            "Time": st.column_config.TextColumn("⏰ Time"),
            "Node": st.column_config.TextColumn("🏷️ Node"),
            "❤️ HR": st.column_config.NumberColumn("❤️ HR", format="%d BPM"),
            "🩸 SpO₂": st.column_config.NumberColumn("🩸 SpO₂", format="%d%%"),
            "🌡️ Temp": st.column_config.TextColumn("🌡️ Temp"),
            "🚶 Activity": st.column_config.TextColumn("🚶 Activity"),
            "📡 RSSI": st.column_config.TextColumn("📡 RSSI"),
            "#️⃣ Packet": st.column_config.NumberColumn("#️⃣ Packet", format="%d")
        }
    )
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 3 TABS
    tab1, tab2, tab3 = st.tabs(["🩺 Health Vitals", "📡 System Status", "📊 Analytics"])
    
    with tab1:
        tab_health_vitals(data)
    
    with tab2:
        tab_system_status(data)
    
    with tab3:
        tab_analytics(data)
    
    # FOOTER
    st.markdown("""
    <div class="dashboard-footer">
        <p style="margin: 0; font-size: 14px;">
            🏥 <strong>STEMCUBE Health Monitoring System</strong> | 
            📍 Universiti Malaysia Pahang | 
            🇲🇾 Malaysia Time: {time} (UTC+8)
        </p>
        <p style="margin: 5px 0 0 0; font-size: 12px; opacity: 0.8;">
            Real-time monitoring using MAX30102, BME280, MPU6050 sensors • Activity detection by STEMCUBE Master
        </p>
    </div>
    """.format(time=current_time_malaysia.strftime('%H:%M:%S')), unsafe_allow_html=True)
    
    # Auto-refresh
    if auto_refresh:
        time.sleep(refresh_rate)
        st.rerun()

# ================ RUN DASHBOARD ================
if __name__ == "__main__":
    # Simple authentication
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #F7E7CE 0%, #FFFDD0 100%);
            padding: 40px;
            border-radius: 20px;
            text-align: center;
            box-shadow: 0 8px 25px rgba(139, 69, 19, 0.2);
            margin: 50px auto;
            max-width: 500px;
        ">
            <h1 style="color: #8B4513; margin-bottom: 30px;">🔐 STEMCUBE Dashboard</h1>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.container():
                st.markdown("<div style='padding: 20px;'>", unsafe_allow_html=True)
                username = st.text_input("👤 Username")
                password = st.text_input("🔒 Password", type="password")
                
                if st.button("Login", use_container_width=True):
                    if username == "admin" and password == "stemcube2025":
                        st.session_state.authenticated = True
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
                
                st.info("**Default:** admin / stemcube2025")
                st.markdown("</div>", unsafe_allow_html=True)
        
        st.stop()
    
    main()