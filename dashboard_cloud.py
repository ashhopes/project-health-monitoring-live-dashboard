# dashboard_cloud_final.py
"""
🏥 STEMCUBE REAL-TIME MONITORING DASHBOARD
🚀 READY FOR STREAMLIT CLOUD DEPLOYMENT
✅ Google Sheets Integrated | ✅ UMP Theme | ✅ Live Data
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
import base64
import math
import gspread
from google.oauth2.service_account import Credentials

# ================ GOOGLE SHEETS CONFIGURATION ================
# 🔗 PASTE YOUR GOOGLE SHEETS LINK HERE:
GOOGLE_SHEETS_URL = "https://docs.google.com/spreadsheets/d/1F3exCRakTPG-Jsbfk4KG0T2cUDeyvoTfp36G-i9kcEk/edit"

# ================ GOOGLE SHEETS FUNCTIONS ================
@st.cache_resource
def init_google_sheets():
    """Initialize connection to Google Sheets"""
    try:
        # Convert public Google Sheets URL to CSV
        csv_url = GOOGLE_SHEETS_URL.replace('/edit#gid=', '/export?format=csv&gid=')
        return {'type': 'public', 'csv_url': csv_url}
    except Exception as e:
        st.error(f"Error configuring Google Sheets: {e}")
        return None

def save_to_google_sheets_simple(data):
    """Simple method to save data (for Streamlit Cloud)"""
    try:
        # Save to session state (works on Streamlit Cloud)
        if 'google_sheets_data' not in st.session_state:
            st.session_state.google_sheets_data = []
        
        record = {
            'Timestamp': data['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
            'SpO2': int(data['spo2']),
            'Heart_Rate': int(data['hr']),
            'Temperature': float(data['temp']),
            'Movement': float(data['movement']),
            'Activity': data['activity'],
            'Data_Source': 'REAL' if data.get('is_real', False) else 'DEMO',
            'Node_ID': data.get('node_id', 'STEMCUBE_001')
        }
        
        st.session_state.google_sheets_data.append(record)
        
        # Keep only last 100 records
        if len(st.session_state.google_sheets_data) > 100:
            st.session_state.google_sheets_data = st.session_state.google_sheets_data[-100:]
        
        return True, "✅ Data saved locally"
    except Exception as e:
        return False, f"❌ Error: {str(e)}"

def load_from_google_sheets():
    """Load data from Google Sheets"""
    try:
        gsheet_conn = init_google_sheets()
        if gsheet_conn and gsheet_conn['type'] == 'public':
            df = pd.read_csv(gsheet_conn['csv_url'])
            return df
        return pd.DataFrame()
    except:
        # Fallback to session state data
        if 'google_sheets_data' in st.session_state:
            return pd.DataFrame(st.session_state.google_sheets_data)
        return pd.DataFrame()

# ================ UMP LOGO BASE64 ================
UMP_LOGO_BASE64 = """
iVBORw0KGgoAAAANSUhEUgAAAfQAAABmCAYAAAD3mVZSAAAACXBIWXMAAAsTAAALEwEAmpwYAAAA
AXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAZdSURBVHgB7d1BbhtHEIDRGRp5/4uyJ5ByYBwY
wIF9YIC4h6QL2ySbe2d2B1jfRwEESfL/j1/f/vgJAPDavr1/AAD4IkEHAEkEHQCkEXQAkEbQAUAa
QQcAaQQdAKQRdACQRtABQBpBBwBpBB0ApBF0AJBG0AFAGkE3wOsX3j/xAsA6V2y/Owg6AHh9j85S
0AFAu6uzFHQA0GrGLAUdALSZNUtBBwAtZs9S0AFAy1bmKOgA4KWr8xN0APCy1fkJOgB4ycoMBR0A
vGRljoIOAF6yOkdBBwAjrc5R0AHAaKtzFHQA0GLGPAUdAIw2Y56CDgDGmjVPQQcAI82cq6ADgHFm
zlXQAcAos2cr6ABgjNnzFXQAMMLq+Qo6AFhu9YwFHQAsN3vGgg4Alpo9Z0EHAEvNnrOgA4BlVsxZ
0AHAEitmLegAYL4VsxZ0ADDXilkLOgCYa9W8BR0AzLNq3oIOAOZZNW9BBwDzrJq3oAOAeVbNW9AB
wByr5i3oAGCeVfMWdAAwx6p5CzoAmGflzAUdAMyxcuaCDgDmWDlzQQcAc6ycuaADgBlWz13QAcD1
Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVW
z13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbP
XdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d
0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13Q
AcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdAB
wPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA
9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1
Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVW
z13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbP
XdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d
0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13Q
AcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdAB
wPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA
9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AGA9//4HZRlAQAt9zY4AAAA
AElFTkSuQmCC
"""

# ================ PAGE CONFIG ================
st.set_page_config(
    page_title="STEMCUBE REAL-TIME MONITOR",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================ MUJI + OLIVE MARROON THEME ================
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
    
    .dashboard-footer {{
        background: linear-gradient(135deg, var(--dark-chocolate) 0%, #2C1810 100%);
        color: var(--champagne);
        padding: 20px;
        border-radius: 12px;
        margin-top: 30px;
        text-align: center;
        font-size: 14px;
    }}
</style>
""", unsafe_allow_html=True)

# ================ INITIALIZE DATA ================
def init_session_state():
    """Initialize all session state variables"""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        current_time = datetime.now()
        
        # Create INITIAL DATA
        st.session_state.hr_data = deque([75, 76, 74, 77, 75, 76, 78, 76, 75, 74], maxlen=50)
        st.session_state.spo2_data = deque([98, 97, 98, 96, 97, 98, 97, 98, 99, 98], maxlen=50)
        st.session_state.temp_data = deque([36.5, 36.6, 36.5, 36.7, 36.6, 36.5, 36.6, 36.7, 36.5, 36.6], maxlen=50)
        st.session_state.movement_data = deque([1.0, 1.2, 0.8, 2.5, 1.5, 0.7, 3.2, 1.8, 0.9, 1.1], maxlen=50)
        st.session_state.timestamps = deque([current_time - timedelta(seconds=i) for i in range(10)][::-1], maxlen=50)
        
        # Google Sheets data
        st.session_state.google_sheets_data = []
        st.session_state.google_sheets_status = "Ready to connect"
        
        # Store complete records
        st.session_state.all_data = deque([
            {
                'timestamp': current_time - timedelta(seconds=i),
                'hr': 75 + np.random.randint(-3, 3),
                'spo2': 97 + np.random.randint(-1, 2),
                'temp': 36.5 + np.random.uniform(-0.2, 0.2),
                'movement': 1.0 + np.random.uniform(0, 0.5),
                'activity': ['RESTING', 'WALKING', 'RUNNING'][i % 3],
                'is_real': False
            }
            for i in range(10)
        ], maxlen=50)

# ================ DISPLAY HEADER ================
def display_header():
    """Display header with UMP logo"""
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
    """Generate demo data for testing"""
    current_time = datetime.now()
    
    # Simulate different activities
    activity_choice = np.random.choice(['RESTING', 'WALKING', 'RUNNING'], p=[0.5, 0.3, 0.2])
    
    if activity_choice == 'RESTING':
        hr = np.random.randint(60, 80)
        spo2 = np.random.randint(96, 100)
        temp = np.random.uniform(36.2, 36.7)
        movement = np.random.uniform(0.5, 1.5)
    elif activity_choice == 'WALKING':
        hr = np.random.randint(75, 95)
        spo2 = np.random.randint(94, 98)
        temp = np.random.uniform(36.5, 37.0)
        movement = np.random.uniform(1.5, 3.0)
    else:  # RUNNING
        hr = np.random.randint(90, 110)
        spo2 = np.random.randint(92, 97)
        temp = np.random.uniform(36.8, 37.5)
        movement = np.random.uniform(2.5, 4.5)
    
    return {
        'timestamp': current_time,
        'hr': int(hr),
        'spo2': int(spo2),
        'temp': round(temp, 1),
        'movement': round(movement, 1),
        'activity': activity_choice,
        'packet_id': int(time.time() * 100) % 10000,
        'node_id': 'STEMCUBE_MASTER',
        'is_real': False,
        'raw': f'DEMO|{current_time.strftime("%H:%M:%S")}|{activity_choice}'
    }

# ================ UPDATE DATA ================
def update_data_buffers(data):
    """Update all data buffers"""
    st.session_state.timestamps.append(data['timestamp'])
    st.session_state.hr_data.append(data['hr'])
    st.session_state.spo2_data.append(data['spo2'])
    st.session_state.temp_data.append(data['temp'])
    st.session_state.movement_data.append(data['movement'])
    
    # Store complete record
    record = {
        'timestamp': data['timestamp'],
        'hr': data['hr'],
        'spo2': data['spo2'],
        'temp': data['temp'],
        'movement': data['movement'],
        'activity': data['activity'],
        'is_real': data['is_real']
    }
    
    st.session_state.all_data.append(record)
    
    # Save to Google Sheets
    success, message = save_to_google_sheets_simple(data)
    st.session_state.google_sheets_status = message

# ================ GRAPH FUNCTIONS ================
def create_graph(title, y_data, color, y_label):
    """Create a graph with MUJI colors"""
    if len(st.session_state.timestamps) == 0:
        return None
    
    n_points = min(20, len(st.session_state.timestamps))
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(st.session_state.timestamps)[-n_points:],
        y=list(y_data)[-n_points:],
        mode='lines+markers',
        line=dict(color=color, width=3),
        marker=dict(size=5, color=color),
        fill='tozeroy',
        fillcolor=f'rgba{tuple(int(color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4)) + (0.1,)}'
    ))
    
    fig.update_layout(
        title={'text': title, 'font': {'size': 16, 'color': '#3C2F2F'}},
        height=250,
        margin=dict(l=50, r=20, t=50, b=50),
        xaxis_title="Time",
        yaxis_title=y_label,
        plot_bgcolor='rgba(255, 253, 208, 0.1)',
        paper_bgcolor='white',
        font=dict(family='Arial', size=12),
        showlegend=False
    )
    
    return fig

# ================ TAB 1: HEALTH VITALS ================
def tab_health_vitals(current_data):
    """Tab 1: Health Vitals"""
    
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
            <p style="color: #666; font-size: 14px;">Patient Activity Status</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Current Metrics
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
            <div style="font-size: 14px; color: #666; margin: 5px 0;">BPM</div>
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
            <div style="font-size: 14px; color: #666; margin: 5px 0;">SpO₂</div>
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
            <div class="metric-label">TEMPERATURE</div>
            <div class="metric-value" style="color: {'#4CAF50' if temp <= 37.5 else '#FF9800' if temp <= 38.5 else '#F44336'};">{temp}°C</div>
            <div style="font-size: 14px; color: #666; margin: 5px 0;">Body Temp</div>
            <div class="{status_class}">{status}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col4:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        movement = current_data['movement']
        
        st.markdown(f"""
        <div style="text-align: center;">
            <div class="metric-label">MOVEMENT</div>
            <div class="metric-value" style="color: #8D6E63;">{movement}</div>
            <div style="font-size: 14px; color: #666; margin: 5px 0;">Activity Level</div>
            <div style="margin-top: 10px;">
                <div style="background: #F5F5DC; height: 8px; border-radius: 4px; overflow: hidden;">
                    <div style="background: linear-gradient(90deg, #556B2F, #8B4513); 
                                width: {min(100, movement * 20)}%; height: 100%;"></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Real-time Graphs
    st.markdown("### 📈 Real-time Monitoring")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
        hr_fig = create_graph("❤️ Heart Rate Trend", st.session_state.hr_data, '#8B4513', 'BPM')
        if hr_fig:
            st.plotly_chart(hr_fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
        spo2_fig = create_graph("🩸 Blood Oxygen Trend", st.session_state.spo2_data, '#556B2F', 'SpO₂ %')
        if spo2_fig:
            st.plotly_chart(spo2_fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ================ TAB 2: SYSTEM STATUS ================
def tab_system_status(current_data):
    """Tab 2: System Status"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
        st.markdown("### 📡 System Status")
        
        # Google Sheets Status
        st.write(f"**Google Sheets Status:** {st.session_state.google_sheets_status}")
        
        if current_data['is_real']:
            st.success("✅ Connected to STEMCUBE Device")
        else:
            st.info("💻 Demo Mode Active")
        
        st.markdown("---")
        st.metric("🔢 Packet ID", current_data['packet_id'])
        st.metric("📟 Node ID", current_data['node_id'])
        st.metric("⏰ Last Update", datetime.now().strftime('%H:%M:%S'))
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
        st.markdown("### 🔋 System Health")
        
        # Battery gauge
        battery = 85
        fig_battery = go.Figure(go.Indicator(
            mode="gauge+number",
            value=battery,
            title={'text': "Battery Level", 'font': {'size': 16, 'color': '#3C2F2F'}},
            number={'suffix': "%", 'font': {'size': 28, 'color': '#8B4513'}},
            gauge={
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': '#3C2F2F'},
                'bar': {'color': '#556B2F'},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "#F7E7CE",
                'steps': [
                    {'range': [0, 20], 'color': 'rgba(244, 67, 54, 0.1)'},
                    {'range': [20, 50], 'color': 'rgba(255, 152, 0, 0.1)'},
                    {'range': [50, 100], 'color': 'rgba(85, 107, 47, 0.1)'}
                ]
            }
        ))
        
        fig_battery.update_layout(height=250, margin=dict(t=50, b=20, l=20, r=20))
        st.plotly_chart(fig_battery, use_container_width=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

# ================ TAB 3: DATA LOG ================
def tab_data_log():
    """Tab 3: Data Log"""
    
    st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
    st.markdown("### 📋 Recent Data Log")
    
    if len(st.session_state.all_data) > 0:
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
                'Source': '📡 REAL' if record['is_real'] else '💻 DEMO'
            })
        
        table_data.reverse()
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, height=400)
    else:
        st.info("No data available yet")
    
    st.markdown("</div>", unsafe_allow_html=True)

# ================ TAB 4: GOOGLE SHEETS DATA ================
def tab_google_sheets():
    """Tab 4: Google Sheets Data"""
    
    st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
    st.markdown("### 📊 Google Sheets Data")
    
    # Connection status
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Refresh Google Sheets", use_container_width=True):
            st.rerun()
    
    with col2:
        # Show Google Sheets URL
        st.info(f"**Connected to:** {GOOGLE_SHEETS_URL[:50]}...")
    
    st.markdown("---")
    
    # Load and display data
    df = load_from_google_sheets()
    
    if not df.empty:
        st.success(f"✅ Loaded {len(df)} records from Google Sheets")
        
        # Show data table
        st.dataframe(df.tail(10), use_container_width=True, height=300)
        
        # Statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if 'SpO2' in df.columns:
                st.metric("Avg SpO2", f"{df['SpO2'].mean():.1f}%")
        
        with col2:
            if 'Heart_Rate' in df.columns:
                st.metric("Avg HR", f"{df['Heart_Rate'].mean():.1f} BPM")
        
        with col3:
            if 'Temperature' in df.columns:
                st.metric("Avg Temp", f"{df['Temperature'].mean():.1f}°C")
        
        with col4:
            st.metric("Total Records", len(df))
        
        # Download button
        csv = df.to_csv(index=False)
        st.download_button(
            "📥 Download All Data (CSV)",
            csv,
            f"stemcube_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "text/csv"
        )
    else:
        st.info("📝 No data found in Google Sheets or not connected yet.")
        st.markdown("""
        **To add data to Google Sheets:**
        1. Go to your Google Sheets
        2. Add data with columns: Timestamp, SpO2, Heart_Rate, Temperature, Activity
        3. Click "Refresh Google Sheets" above
        """)
    
    st.markdown("</div>", unsafe_allow_html=True)

# ================ MAIN DASHBOARD ================
def main():
    """Main dashboard function"""
    
    # Initialize session state
    init_session_state()
    
    # Display header
    display_header()
    
    # Get demo data
    current_data = get_demo_data()
    
    # Update buffers
    update_data_buffers(current_data)
    
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
        
        col_sb1, col_sb2 = st.columns(2)
        with col_sb1:
            st.metric("❤️ HR", f"{current_data['hr']} BPM")
            st.metric("🌡️ Temp", f"{current_data['temp']:.1f}°C")
        with col_sb2:
            st.metric("🩸 SpO₂", f"{current_data['spo2']}%")
            st.metric("🏃 Activity", current_data['activity'])
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
        st.markdown("### 🔌 System Info")
        
        st.write(f"**Node:** {current_data['node_id']}")
        st.write(f"**Packets:** {len(st.session_state.all_data)}")
        st.write(f"**Last Update:** {datetime.now().strftime('%H:%M:%S')}")
        
        if current_data['is_real']:
            st.success("✅ Connected to STEMCUBE")
        else:
            st.warning("⚠️ Demo Mode Active")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # TABS - 4 TABS INCLUDING GOOGLE SHEETS
    tab1, tab2, tab3, tab4 = st.tabs([
        "🩺 Health Vitals", 
        "📡 System Status", 
        "📋 Data Log",
        "📊 Google Sheets"
    ])
    
    with tab1:
        tab_health_vitals(current_data)
    
    with tab2:
        tab_system_status(current_data)
    
    with tab3:
        tab_data_log()
    
    with tab4:
        tab_google_sheets()
    
    # Footer
    malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
    current_time_malaysia = datetime.now(malaysia_tz)
    
    st.markdown(f"""
    <div class="dashboard-footer">
        <p style="margin: 0; font-size: 14px;">
            🏥 <strong>STEMCUBE Health Monitoring System</strong> | 
            📍 Universiti Malaysia Pahang • Faculty of Electrical & Electronics Engineering |
            🎓 Final Year Project 2025 | 📊 Google Sheets Integrated
        </p>
        <p style="margin: 5px 0 0 0; font-size: 12px; opacity: 0.8;">
            🇲🇾 Malaysia Time: {current_time_malaysia.strftime('%I:%M:%S %p')} • 
            🔄 Auto-refresh every {refresh_rate}s • 
            🎨 MUJI + Olive Maroon Theme
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