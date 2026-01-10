# dashboard_cloud.py - OLIVECLOUD E-MART INSPIRED DESIGN
"""
STEMCUBE HEALTH MONITOR - OliveCloud E-mart Inspired Design
Clean, Modern, Card-based Interface
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
    page_title="STEMCUBE Health Monitor",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"  # Cleaner without sidebar
)

# ================ OLIVECLOUD E-MART INSPIRED STYLES ================
st.markdown("""
<style>
    /* OLIVECLOUD COLOR THEME */
    :root {
        --olive-primary: #556B2F;
        --olive-secondary: #8B4513;
        --olive-light: #F5F5DC;
        --olive-cream: #FFFDD0;
        --olive-dark: #2F4F4F;
        --olive-accent: #D4A76A;
        --card-shadow: 0 4px 12px rgba(85, 107, 47, 0.1);
        --card-radius: 12px;
    }
    
    /* MAIN CONTAINER */
    .stApp {
        background: linear-gradient(135deg, #FFFFFF 0%, var(--olive-cream) 100%);
        font-family: 'Segoe UI', 'Arial', sans-serif;
    }
    
    /* HEADER - Clean E-mart style */
    .header-container {
        background: white;
        padding: 25px 40px;
        border-radius: 0 0 var(--card-radius) var(--card-radius);
        box-shadow: var(--card-shadow);
        margin-bottom: 30px;
        border-bottom: 4px solid var(--olive-primary);
    }
    
    .header-title {
        color: var(--olive-dark);
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0;
        background: linear-gradient(135deg, var(--olive-primary), var(--olive-secondary));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .header-subtitle {
        color: #666;
        font-size: 1rem;
        margin: 8px 0 0 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    /* CARD STYLES - E-mart card design */
    .emart-card {
        background: white;
        padding: 25px;
        border-radius: var(--card-radius);
        box-shadow: var(--card-shadow);
        border: 1px solid rgba(85, 107, 47, 0.1);
        margin-bottom: 20px;
        transition: all 0.3s ease;
    }
    
    .emart-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(85, 107, 47, 0.15);
    }
    
    .card-header {
        color: var(--olive-primary);
        font-size: 1.3rem;
        font-weight: 600;
        margin-bottom: 20px;
        padding-bottom: 10px;
        border-bottom: 2px solid var(--olive-light);
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    /* METRIC CARDS - Clean, minimal */
    .metric-container {
        background: white;
        padding: 20px;
        border-radius: var(--card-radius);
        box-shadow: var(--card-shadow);
        text-align: center;
        border-top: 4px solid var(--olive-primary);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: var(--olive-dark);
        margin: 10px 0;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: var(--olive-primary);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-unit {
        font-size: 0.9rem;
        color: #666;
        margin-top: 5px;
    }
    
    /* STATUS BADGES - E-mart style tags */
    .status-badge {
        display: inline-block;
        padding: 6px 16px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 5px;
    }
    
    .status-normal {
        background: linear-gradient(135deg, #E8F5E9, #C8E6C9);
        color: #2E7D32;
        border: 1px solid #A5D6A7;
    }
    
    .status-warning {
        background: linear-gradient(135deg, #FFF3E0, #FFE0B2);
        color: #EF6C00;
        border: 1px solid #FFCC80;
    }
    
    .status-critical {
        background: linear-gradient(135deg, #FFEBEE, #FFCDD2);
        color: #C62828;
        border: 1px solid #EF9A9A;
    }
    
    /* DATA TABLE - Clean design */
    .data-table {
        background: white;
        border-radius: var(--card-radius);
        overflow: hidden;
        box-shadow: var(--card-shadow);
    }
    
    .data-table thead {
        background: var(--olive-primary);
        color: white;
    }
    
    /* BUTTONS - E-mart style */
    .emart-button {
        background: linear-gradient(135deg, var(--olive-primary), var(--olive-secondary));
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s;
        width: 100%;
    }
    
    .emart-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(85, 107, 47, 0.2);
    }
    
    /* GRAPH CONTAINERS */
    .graph-card {
        background: white;
        padding: 20px;
        border-radius: var(--card-radius);
        box-shadow: var(--card-shadow);
        margin-bottom: 20px;
    }
    
    /* INFO BOXES - Like E-mart delivery info */
    .info-box {
        background: linear-gradient(135deg, #F9FBE7, #F0F4C3);
        padding: 20px;
        border-radius: var(--card-radius);
        border-left: 4px solid var(--olive-accent);
        margin-bottom: 20px;
    }
    
    /* FOOTER - Clean footer */
    .footer {
        background: var(--olive-dark);
        color: white;
        padding: 20px;
        border-radius: var(--card-radius) var(--card-radius) 0 0;
        margin-top: 40px;
        text-align: center;
        font-size: 0.9rem;
    }
    
    /* CUSTOM SCROLLBAR */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--olive-light);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--olive-primary);
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# ================ INITIALIZE DATA ================
def init_session_state():
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        current_time = datetime.now()
        
        # Initialize data buffers
        st.session_state.hr_data = deque([72, 71, 73, 70, 72, 74, 73, 71, 70, 72], maxlen=50)
        st.session_state.spo2_data = deque([98, 97, 98, 99, 98, 97, 98, 99, 98, 97], maxlen=50)
        st.session_state.temp_data = deque([36.5, 36.6, 36.5, 36.4, 36.5, 36.6, 36.5, 36.4, 36.5, 36.6], maxlen=50)
        st.session_state.timestamps = deque([current_time - timedelta(seconds=i) for i in range(10)][::-1], maxlen=50)
        
        # Patient info
        st.session_state.patient_data = {
            'name': 'AHMAD BIN ISMAIL',
            'age': 35,
            'id': 'PID-2025-001',
            'room': 'WARD A-12',
            'admission': '2025-01-10'
        }

# ================ HEADER ================
def display_header():
    malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
    current_time = datetime.now(malaysia_tz)
    
    st.markdown(f"""
    <div class="header-container">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h1 class="header-title">🏥 STEMCUBE Health Monitor</h1>
                <div class="header-subtitle">
                    <span>📍 Universiti Malaysia Pahang</span>
                    <span>•</span>
                    <span>📅 {current_time.strftime('%d %B %Y')}</span>
                    <span>•</span>
                    <span>🕒 {current_time.strftime('%I:%M:%S %p')}</span>
                </div>
            </div>
            <div style="text-align: right;">
                <div style="background: linear-gradient(135deg, var(--olive-light), white); 
                            padding: 10px 20px; border-radius: 8px; border: 1px solid rgba(85, 107, 47, 0.2);">
                    <div style="font-size: 0.9rem; color: var(--olive-primary);">Status</div>
                    <div style="font-size: 1.1rem; font-weight: 600; color: var(--olive-secondary);">
                        <span style="color: #4CAF50;">●</span> Live Monitoring
                    </div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ================ PATIENT INFO CARD ================
def display_patient_info():
    st.markdown("""
    <div class="emart-card">
        <div class="card-header">👤 Patient Information</div>
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px;">
    """, unsafe_allow_html=True)
    
    cols = st.columns(4)
    with cols[0]:
        st.markdown(f"""
        <div style="text-align: center; padding: 15px; background: #F9FBE7; border-radius: 8px;">
            <div style="font-size: 0.9rem; color: #666;">Patient Name</div>
            <div style="font-size: 1.2rem; font-weight: 600; color: var(--olive-dark); margin-top: 5px;">
                {st.session_state.patient_data['name']}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[1]:
        st.markdown(f"""
        <div style="text-align: center; padding: 15px; background: #E8F5E9; border-radius: 8px;">
            <div style="font-size: 0.9rem; color: #666;">Age</div>
            <div style="font-size: 1.2rem; font-weight: 600; color: var(--olive-dark); margin-top: 5px;">
                {st.session_state.patient_data['age']} years
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[2]:
        st.markdown(f"""
        <div style="text-align: center; padding: 15px; background: #E3F2FD; border-radius: 8px;">
            <div style="font-size: 0.9rem; color: #666;">Patient ID</div>
            <div style="font-size: 1.2rem; font-weight: 600; color: var(--olive-dark); margin-top: 5px;">
                {st.session_state.patient_data['id']}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[3]:
        st.markdown(f"""
        <div style="text-align: center; padding: 15px; background: #FFF3E0; border-radius: 8px;">
            <div style="font-size: 0.9rem; color: #666;">Room Number</div>
            <div style="font-size: 1.2rem; font-weight: 600; color: var(--olive-dark); margin-top: 5px;">
                {st.session_state.patient_data['room']}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div></div>", unsafe_allow_html=True)

# ================ VITAL SIGNS METRICS ================
def display_vital_signs():
    st.markdown("""
    <div class="emart-card">
        <div class="card-header">📊 Vital Signs Monitor</div>
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px;">
    """, unsafe_allow_html=True)
    
    # Generate current values
    current_time = datetime.now()
    seconds = current_time.second
    
    # Heart Rate
    hr = 72 + int(np.sin(seconds/5) * 10)
    hr_status = "status-normal" if 60 <= hr <= 100 else "status-warning" if 50 <= hr <= 110 else "status-critical"
    hr_status_text = "Normal" if 60 <= hr <= 100 else "Warning" if 50 <= hr <= 110 else "Critical"
    
    # SpO2
    spo2 = 98 + int(np.cos(seconds/10) * 2)
    spo2_status = "status-normal" if spo2 >= 95 else "status-warning" if spo2 >= 90 else "status-critical"
    spo2_status_text = "Normal" if spo2 >= 95 else "Low" if spo2 >= 90 else "Critical"
    
    # Temperature
    temp = 36.5 + np.sin(seconds/7) * 0.3
    temp_status = "status-normal" if temp <= 37.5 else "status-warning" if temp <= 38.5 else "status-critical"
    temp_status_text = "Normal" if temp <= 37.5 else "Elevated" if temp <= 38.5 else "Fever"
    
    # Activity
    activity_idx = int(seconds / 20) % 3
    activities = ['RESTING', 'WALKING', 'RUNNING']
    activity = activities[activity_idx]
    activity_emoji = "😴" if activity == 'RESTING' else "🚶" if activity == 'WALKING' else "🏃"
    
    cols = st.columns(4)
    
    with cols[0]:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">HEART RATE</div>
            <div class="metric-value" style="color: {'#4CAF50' if 60 <= hr <= 100 else '#FF9800' if 50 <= hr <= 110 else '#F44336'};">{hr}</div>
            <div class="metric-unit">BPM</div>
            <div class="{hr_status} status-badge" style="margin-top: 10px;">{hr_status_text}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[1]:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">BLOOD OXYGEN</div>
            <div class="metric-value" style="color: {'#4CAF50' if spo2 >= 95 else '#FF9800' if spo2 >= 90 else '#F44336'};">{spo2}%</div>
            <div class="metric-unit">SpO₂</div>
            <div class="{spo2_status} status-badge" style="margin-top: 10px;">{spo2_status_text}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[2]:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">TEMPERATURE</div>
            <div class="metric-value" style="color: {'#4CAF50' if temp <= 37.5 else '#FF9800' if temp <= 38.5 else '#F44336'};">{temp:.1f}</div>
            <div class="metric-unit">°C</div>
            <div class="{temp_status} status-badge" style="margin-top: 10px;">{temp_status_text}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[3]:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">PATIENT ACTIVITY</div>
            <div style="font-size: 2.5rem; margin: 15px 0;">{activity_emoji}</div>
            <div style="font-size: 1.2rem; font-weight: 600; color: var(--olive-dark);">{activity}</div>
            <div style="background: {'#E8F5E9' if activity == 'RESTING' else '#FFF3E0' if activity == 'WALKING' else '#FFEBEE'}; 
                        color: {'#2E7D32' if activity == 'RESTING' else '#EF6C00' if activity == 'WALKING' else '#C62828'};
                        padding: 6px 16px; border-radius: 20px; font-size: 0.9rem; font-weight: 600; margin-top: 10px;">
                {activity}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div></div>", unsafe_allow_html=True)

# ================ REAL-TIME GRAPHS ================
def display_graphs():
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='graph-card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-header'>📈 Heart Rate Trend</div>", unsafe_allow_html=True)
        
        # Generate heart rate data
        times = [datetime.now() - timedelta(seconds=i*5) for i in range(20)][::-1]
        hr_values = [72 + np.random.normal(0, 3) for _ in range(20)]
        hr_values = [max(60, min(90, hr)) for hr in hr_values]
        
        fig_hr = px.line(
            x=times,
            y=hr_values,
            labels={'x': 'Time', 'y': 'BPM'}
        )
        
        fig_hr.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=20, b=40),
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(size=12),
            showlegend=False
        )
        
        fig_hr.update_traces(
            line=dict(color='#556B2F', width=3),
            fill='tozeroy',
            fillcolor='rgba(85, 107, 47, 0.1)'
        )
        
        st.plotly_chart(fig_hr, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='graph-card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-header'>📊 Oxygen Level Trend</div>", unsafe_allow_html=True)
        
        # Generate SpO2 data
        spo2_values = [98 + np.random.normal(0, 1) for _ in range(20)]
        spo2_values = [max(95, min(100, spo2)) for spo2 in spo2_values]
        
        fig_spo2 = px.line(
            x=times,
            y=spo2_values,
            labels={'x': 'Time', 'y': 'SpO₂ %'}
        )
        
        fig_spo2.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=20, b=40),
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(size=12),
            showlegend=False
        )
        
        fig_spo2.update_traces(
            line=dict(color='#8B4513', width=3),
            fill='tozeroy',
            fillcolor='rgba(139, 69, 19, 0.1)'
        )
        
        st.plotly_chart(fig_spo2, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ================ SYSTEM STATUS ================
def display_system_status():
    st.markdown("<div class='emart-card'>", unsafe_allow_html=True)
    st.markdown("<div class='card-header'>⚙️ System Status</div>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div style="text-align: center; padding: 20px; background: #F5F5DC; border-radius: 8px;">
            <div style="font-size: 2rem; margin-bottom: 10px;">📡</div>
            <div style="font-size: 0.9rem; color: #666;">Connection</div>
            <div style="font-size: 1.2rem; font-weight: 600; color: #4CAF50; margin-top: 5px;">Connected</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 20px; background: #F5F5DC; border-radius: 8px;">
            <div style="font-size: 2rem; margin-bottom: 10px;">🔋</div>
            <div style="font-size: 0.9rem; color: #666;">Battery</div>
            <div style="font-size: 1.2rem; font-weight: 600; color: #556B2F; margin-top: 5px;">85%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="text-align: center; padding: 20px; background: #F5F5DC; border-radius: 8px;">
            <div style="font-size: 2rem; margin-bottom: 10px;">📶</div>
            <div style="font-size: 0.9rem; color: #666;">Signal</div>
            <div style="font-size: 1.2rem; font-weight: 600; color: #8B4513; margin-top: 5px;">-65 dB</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div style="text-align: center; padding: 20px; background: #F5F5DC; border-radius: 8px;">
            <div style="font-size: 2rem; margin-bottom: 10px;">🔄</div>
            <div style="font-size: 0.9rem; color: #666;">Last Update</div>
            <div style="font-size: 1.1rem; font-weight: 600; color: #2F4F4F; margin-top: 5px;">
                """ + datetime.now().strftime('%H:%M:%S') + """
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

# ================ DATA TABLE ================
def display_data_table():
    st.markdown("<div class='emart-card'>", unsafe_allow_html=True)
    st.markdown("<div class='card-header'>📋 Recent Readings</div>", unsafe_allow_html=True)
    
    # Create sample data
    current_time = datetime.now()
    table_data = []
    
    for i in range(8):
        time_str = (current_time - timedelta(minutes=i*5)).strftime('%H:%M')
        hr = 72 + np.random.randint(-5, 6)
        spo2 = 98 + np.random.randint(-2, 3)
        temp = 36.5 + np.random.uniform(-0.3, 0.3)
        activity = ['RESTING', 'WALKING', 'RUNNING'][i % 3]
        
        table_data.append({
            'Time': time_str,
            'Heart Rate': f"{hr} BPM",
            'SpO₂': f"{spo2}%",
            'Temp': f"{temp:.1f}°C",
            'Activity': activity,
            'Status': 'Normal' if hr <= 100 and spo2 >= 95 else 'Check'
        })
    
    df = pd.DataFrame(table_data)
    
    # Apply custom styling
    def color_status(val):
        color = '#4CAF50' if val == 'Normal' else '#FF9800'
        return f'color: {color}; font-weight: 600;'
    
    styled_df = df.style.applymap(color_status, subset=['Status'])
    
    # Display table
    st.dataframe(
        styled_df,
        use_container_width=True,
        height=350,
        hide_index=True
    )
    
    st.markdown("</div>", unsafe_allow_html=True)

# ================ ALERTS & NOTIFICATIONS ================
def display_alerts():
    st.markdown("<div class='info-box'>", unsafe_allow_html=True)
    st.markdown("<div style='font-size: 1.2rem; font-weight: 600; color: var(--olive-primary); margin-bottom: 15px;'>📢 System Alerts</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style="padding: 15px; background: white; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #4CAF50;">
            <div style="font-weight: 600; color: #2E7D32;">✅ All Systems Normal</div>
            <div style="font-size: 0.9rem; color: #666; margin-top: 5px;">Vital signs within normal range</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="padding: 15px; background: white; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #2196F3;">
            <div style="font-weight: 600; color: #1565C0;">🔵 Connection Active</div>
            <div style="font-size: 0.9rem; color: #666; margin-top: 5px;">LoRa link established</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

# ================ CONTROL PANEL ================
def display_controls():
    st.markdown("<div class='emart-card'>", unsafe_allow_html=True)
    st.markdown("<div class='card-header'>🎛️ Control Panel</div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()
    
    with col2:
        auto_refresh = st.checkbox("Auto Refresh (5s)", value=True)
    
    with col3:
        if st.button("📥 Export Report", use_container_width=True):
            st.success("Report exported successfully!")
    
    # Additional controls
    st.markdown("---")
    col4, col5, col6 = st.columns(3)
    
    with col4:
        st.selectbox("Update Frequency", ["1 second", "5 seconds", "10 seconds", "30 seconds"])
    
    with col5:
        st.selectbox("Data Source", ["Live Sensor", "Demo Mode", "Historical Data"])
    
    with col6:
        st.selectbox("Alert Level", ["Normal", "High", "Critical"])
    
    st.markdown("</div>", unsafe_allow_html=True)

# ================ FOOTER ================
def display_footer():
    malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
    current_time = datetime.now(malaysia_tz)
    
    st.markdown(f"""
    <div class="footer">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div style="text-align: left;">
                <div style="font-weight: 600; margin-bottom: 5px;">🏥 STEMCUBE Health Monitoring System</div>
                <div style="font-size: 0.8rem; opacity: 0.8;">Universiti Malaysia Pahang • Final Year Project 2025</div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 0.9rem;">🕒 Last Updated: {current_time.strftime('%I:%M:%S %p')}</div>
                <div style="font-size: 0.8rem; opacity: 0.8;">Design Inspired by OliveCloud E-mart</div>
            </div>
        </div>
        <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(255, 255, 255, 0.1); font-size: 0.8rem; opacity: 0.7;">
            For emergency contact: +60 12-345 6789 • Monitoring 24/7
        </div>
    </div>
    """, unsafe_allow_html=True)

# ================ MAIN DASHBOARD ================
def main():
    # Initialize
    init_session_state()
    
    # Display all components
    display_header()
    
    # Row 1: Patient Info
    display_patient_info()
    
    # Row 2: Vital Signs
    display_vital_signs()
    
    # Row 3: Graphs
    display_graphs()
    
    # Row 4: System Status & Controls
    col1, col2 = st.columns([2, 1])
    
    with col1:
        display_system_status()
        display_data_table()
    
    with col2:
        display_alerts()
        display_controls()
    
    # Footer
    display_footer()
    
    # Auto-refresh
    if st.session_state.get('auto_refresh', True):
        time.sleep(5)
        st.rerun()

# ================ RUN ================
if __name__ == "__main__":
    main()