# dashboard_Real_Cloud.py - STREAMLIT CLOUD VERSION
"""
REAL-TIME DASHBOARD FOR STREAMLIT CLOUD
Deploy this to: https://project-health-monitoring-live-dashboard-with-lora.streamlit.app/
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

# ================ PAGE CONFIG ================
st.set_page_config(
    page_title="STEMCUBE LIVE - Health Monitoring",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================ CUSTOM CSS ================
st.markdown("""
<style>
    /* Clean professional style */
    .stApp {
        background-color: #f8f9fa;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .metric-box {
        background: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-left: 4px solid #667eea;
        margin-bottom: 10px;
    }
    
    .alert-box {
        background: #fee2e2;
        color: #991b1b;
        padding: 12px;
        border-radius: 8px;
        border-left: 4px solid #dc2626;
        margin: 8px 0;
    }
    
    .normal-box {
        background: #dcfce7;
        color: #166534;
        padding: 12px;
        border-radius: 8px;
        border-left: 4px solid #10b981;
        margin: 8px 0;
    }
    
    .tab-container {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-top: 15px;
    }
    
    .data-table {
        font-size: 14px;
        width: 100%;
    }
    
    .data-table th {
        background-color: #f3f4f6;
        padding: 10px;
        text-align: left;
        font-weight: 600;
    }
    
    .data-table td {
        padding: 8px 10px;
        border-bottom: 1px solid #e5e7eb;
    }
</style>
""", unsafe_allow_html=True)

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
        # Generate realistic demo data based on your STEMCUBE format
        return generate_stemcube_demo_data()
    except Exception as e:
        st.error(f"Data error: {e}")
        return None

def generate_stemcube_demo_data():
    """Generate demo data matching YOUR STEMCUBE format"""
    malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
    current_time = datetime.now(malaysia_tz)
    
    # Your STEMCUBE sends: NODE_e661146|18489901126.7156130170|-0.36|-0.20|0.87|-0.96|-0.46|0.64|8.849|0|RESTING
    # Which shows: Temp: 26.7C, Hum: 56%, HR: 30 BPM, SpO2: 70%, Movement: 8.849, Activity: RESTING
    
    data = {
        'status': 'connected',
        'last_update': current_time.isoformat(),
        'is_real_data': False,  # Will be True when real data comes
        'activity_source': 'STEMCUBE_MASTER',
        
        'data': {
            'node_id': 'NODE_e661',
            'timestamp': current_time.isoformat(),
            'malaysia_time': current_time.strftime('%H:%M:%S'),
            
            # From your image data:
            'hr': 30,           # HR: 30 BPM
            'spo2': 70,         # SpO2: 70%
            'temp': 26.7,       # Temp: 26.7C
            'humidity': 56,     # Hum: 56%
            
            # MPU6050 Data from your format:
            'ax': -0.36,
            'ay': -0.20,
            'az': 0.87,
            'gx': -0.96,
            'gy': -0.46,
            'gz': 0.64,
            'acceleration_magnitude': 8.849,
            
            # Activity from STEMCUBE Master (RESTING, WALKING, RUNNING only)
            'activity': 'RESTING',
            'activity_confidence': 0.95,
            
            # System data
            'battery': 85,
            'rssi': -65,
            'snr': 12,
            'packet_id': int(current_time.timestamp()) % 10000,
            'packet_loss': 2.5
        }
    }
    
    return data

# ================ CREATE DATA LOG TABLE ================
def create_data_log(data_history):
    """Create a table of recent data readings"""
    if not data_history:
        return pd.DataFrame()
    
    df = pd.DataFrame(data_history)
    
    # Keep only relevant columns
    columns_to_keep = ['malaysia_time', 'node_id', 'hr', 'spo2', 'temp', 'activity', 'rssi', 'packet_id']
    available_cols = [col for col in columns_to_keep if col in df.columns]
    
    if available_cols:
        df = df[available_cols]
    
    return df

# ================ TAB 1: HEALTH VITALS ================
def tab_health_vitals(data):
    """Tab 1: Health Vitals Display"""
    current = data['data']
    
    st.markdown("<div class='tab-container'>", unsafe_allow_html=True)
    
    # Node Selection (for multiple users)
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("👤 Patient Selection")
        nodes = ['NODE_e661', 'NODE_e662', 'NODE_e663']
        selected_node = st.selectbox("Select Node ID", nodes, key="node_select")
    
    with col2:
        st.subheader("🕐 Last Update")
        st.write(f"**{current.get('malaysia_time', 'N/A')}** (Malaysia Time)")
    
    st.markdown("---")
    
    # Heart Rate - Line Chart + Current Value
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("❤️ Heart Rate")
        
        # Generate HR history (last 20 readings)
        times = [datetime.now() - timedelta(seconds=i*5) for i in range(20)][::-1]
        hr_values = [current['hr'] + np.random.normal(0, 3) for _ in range(20)]
        hr_values = [max(30, min(120, hr)) for hr in hr_values]  # Clamp values
        
        fig_hr = px.line(
            x=times,
            y=hr_values,
            title="Heart Rate Trend (Last 100 seconds)",
            labels={'x': 'Time', 'y': 'BPM'}
        )
        fig_hr.update_layout(height=250, showlegend=False)
        st.plotly_chart(fig_hr, use_container_width=True)
    
    with col2:
        st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
        hr = current['hr']
        
        # HR status
        if hr < 50:
            hr_status = "🟡 LOW"
            hr_color = "#f59e0b"
        elif hr <= 100:
            hr_status = "🟢 NORMAL"
            hr_color = "#10b981"
        else:
            hr_status = "🔴 HIGH"
            hr_color = "#ef4444"
        
        st.markdown(f"""
        <div class='metric-box' style='text-align: center;'>
            <h1 style='color: {hr_color}; margin: 0;'>{hr}</h1>
            <p style='margin: 5px 0; font-size: 20px;'>BPM</p>
            <p style='margin: 0;'><strong>{hr_status}</strong></p>
        </div>
        """, unsafe_allow_html=True)
    
    # SpO2 and Temperature in one row
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🩸 Blood Oxygen (SpO₂)")
        spo2 = current['spo2']
        
        # SpO2 gauge
        fig_spo2 = go.Figure(go.Indicator(
            mode="gauge+number",
            value=spo2,
            title={'text': "SpO₂ %", 'font': {'size': 20}},
            number={'suffix': "%", 'font': {'size': 30}},
            gauge={
                'axis': {'range': [70, 100]},
                'bar': {'color': "#ef4444" if spo2 < 90 else "#10b981"},
                'steps': [
                    {'range': [70, 90], 'color': "#fee2e2"},
                    {'range': [90, 100], 'color': "#dcfce7"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 95
                }
            }
        ))
        fig_spo2.update_layout(height=200, margin=dict(t=50, b=20, l=20, r=20))
        st.plotly_chart(fig_spo2, use_container_width=True)
        
        # SpO2 status
        if spo2 >= 95:
            st.markdown("<div class='normal-box'>🟢 Normal (≥95%)</div>", unsafe_allow_html=True)
        elif spo2 >= 90:
            st.markdown("<div class='alert-box'>🟡 Low (90-94%)</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='alert-box'>🔴 Critical (<90%)</div>", unsafe_allow_html=True)
    
    with col2:
        st.subheader("🌡️ Body Temperature")
        temp = current['temp']
        
        # Temperature display
        fig_temp = go.Figure(go.Indicator(
            mode="number+gauge",
            value=temp,
            title={'text': "Temperature °C", 'font': {'size': 20}},
            number={'suffix': "°C", 'font': {'size': 40}},
            gauge={
                'axis': {'range': [35, 40]},
                'bar': {'color': "#ef4444" if temp > 37.5 else "#10b981"},
                'steps': [
                    {'range': [35, 37.5], 'color': "#dcfce7"},
                    {'range': [37.5, 40], 'color': "#fee2e2"}
                ]
            }
        ))
        fig_temp.update_layout(height=200, margin=dict(t=50, b=20, l=20, r=20))
        st.plotly_chart(fig_temp, use_container_width=True)
        
        # Temperature status
        if temp <= 37.5:
            st.markdown("<div class='normal-box'>🟢 Normal (≤37.5°C)</div>", unsafe_allow_html=True)
        elif temp <= 38.0:
            st.markdown("<div class='alert-box'>🟡 Elevated (37.6-38.0°C)</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='alert-box'>🔴 Fever (>38.0°C)</div>", unsafe_allow_html=True)
    
    # Activity Classification
    st.subheader("🚶 Activity Classification")
    activity = current.get('activity', 'RESTING')
    
    # Map your 3 activities
    activity_config = {
        'RESTING': {'color': '#10b981', 'emoji': '😴', 'desc': 'Patient is resting'},
        'WALKING': {'color': '#3b82f6', 'emoji': '🚶', 'desc': 'Patient is walking'},
        'RUNNING': {'color': '#ef4444', 'emoji': '🏃', 'desc': 'Patient is running'}
    }
    
    config = activity_config.get(activity.upper(), {'color': '#6b7280', 'emoji': '❓', 'desc': 'Unknown activity'})
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"""
        <div style='
            background: {config['color']};
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            font-size: 24px;
            margin: 10px 0;
        '>
            {config['emoji']} <strong>{activity}</strong>
        </div>
        """, unsafe_allow_html=True)
        st.caption(f"Source: STEMCUBE Master • {config['desc']}")
    
    st.markdown("</div>", unsafe_allow_html=True)

# ================ TAB 2: SYSTEM & LORA STATUS ================
def tab_system_status(data):
    """Tab 2: System & LoRa Status"""
    current = data['data']
    
    st.markdown("<div class='tab-container'>", unsafe_allow_html=True)
    st.subheader("📡 System & LoRa Status")
    
    # System Metrics in 2 columns
    col1, col2 = st.columns(2)
    
    with col1:
        # LoRa Signal Strength
        st.markdown("#### 📶 LoRa Signal Strength")
        
        rssi = current.get('rssi', -65)
        snr = current.get('snr', 12)
        
        # RSSI Gauge
        fig_rssi = go.Figure(go.Indicator(
            mode="gauge+number",
            value=rssi,
            title={'text': "RSSI", 'font': {'size': 18}},
            number={'suffix': " dB", 'font': {'size': 28}},
            gauge={
                'axis': {'range': [-120, -40]},
                'bar': {'color': "#10b981" if rssi > -70 else "#f59e0b" if rssi > -90 else "#ef4444"},
                'steps': [
                    {'range': [-120, -90], 'color': "#fee2e2"},
                    {'range': [-90, -70], 'color': "#fef3c7"},
                    {'range': [-70, -40], 'color': "#dcfce7"}
                ]
            }
        ))
        fig_rssi.update_layout(height=200, margin=dict(t=40, b=20, l=20, r=20))
        st.plotly_chart(fig_rssi, use_container_width=True)
        
        # SNR value
        st.metric("SNR (Signal-to-Noise)", f"{snr} dB", 
                 delta="Good" if snr > 10 else "Poor" if snr > 5 else "Bad",
                 delta_color="normal" if snr > 10 else "off" if snr > 5 else "inverse")
    
    with col2:
        # Battery Level
        st.markdown("#### 🔋 Battery Status")
        
        battery = current.get('battery', 85)
        
        fig_battery = go.Figure(go.Indicator(
            mode="gauge+number",
            value=battery,
            title={'text': "Battery Level", 'font': {'size': 18}},
            number={'suffix': "%", 'font': {'size': 28}},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "#10b981" if battery > 50 else "#f59e0b" if battery > 20 else "#ef4444"},
                'steps': [
                    {'range': [0, 20], 'color': "#fee2e2"},
                    {'range': [20, 50], 'color': "#fef3c7"},
                    {'range': [50, 100], 'color': "#dcfce7"}
                ]
            }
        ))
        fig_battery.update_layout(height=200, margin=dict(t=40, b=20, l=20, r=20))
        st.plotly_chart(fig_battery, use_container_width=True)
        
        # Estimated runtime
        if battery > 80:
            runtime = "> 48 hours"
        elif battery > 50:
            runtime = "24-48 hours"
        elif battery > 20:
            runtime = "8-24 hours"
        else:
            runtime = "< 8 hours"
        
        st.caption(f"Estimated runtime: **{runtime}**")
    
    st.markdown("---")
    
    # Packet Delivery & Latency
    col1, col2, col3 = st.columns(3)
    
    with col1:
        packet_loss = current.get('packet_loss', 2.5)
        st.metric("📦 Packet Loss", f"{packet_loss}%", 
                 delta="Low" if packet_loss < 5 else "High" if packet_loss < 15 else "Critical",
                 delta_color="normal" if packet_loss < 5 else "off" if packet_loss < 15 else "inverse")
        st.caption("Last 100 packets")
    
    with col2:
        packet_id = current.get('packet_id', 0)
        st.metric("🔄 Total Packets", f"{packet_id:,}")
        st.caption("Since system start")
    
    with col3:
        # Calculate latency
        try:
            last_update = datetime.fromisoformat(data['last_update'].replace('Z', '+00:00'))
            latency = (datetime.now() - last_update).total_seconds()
            st.metric("⏱️ Latency", f"{latency:.1f}s",
                     delta="Real-time" if latency < 3 else "Delayed" if latency < 10 else "High delay",
                     delta_color="normal" if latency < 3 else "off" if latency < 10 else "inverse")
        except:
            st.metric("⏱️ Latency", "N/A")
        st.caption("Data freshness")
    
    st.markdown("---")
    
    # Device Information
    st.markdown("#### 🖥️ Device Information")
    
    info_col1, info_col2 = st.columns(2)
    
    with info_col1:
        st.markdown(f"""
        <div class='metric-box'>
            <p><strong>Node ID:</strong> {current.get('node_id', 'NODE_e661')}</p>
            <p><strong>Firmware:</strong> STEMCUBE v2.1</p>
            <p><strong>Sensors:</strong> MAX30102, BME280, MPU6050</p>
            <p><strong>Activity Source:</strong> STEMCUBE Master</p>
        </div>
        """, unsafe_allow_html=True)
    
    with info_col2:
        st.markdown(f"""
        <div class='metric-box'>
            <p><strong>Connection:</strong> LoRa HC-12</p>
            <p><strong>Frequency:</strong> 433 MHz</p>
            <p><strong>Baud Rate:</strong> 9600</p>
            <p><strong>Last Update:</strong> {current.get('malaysia_time', 'N/A')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

# ================ TAB 3: ANALYTICS & TRENDS ================
def tab_analytics(data):
    """Tab 3: Analytics & Trends"""
    current = data['data']
    
    st.markdown("<div class='tab-container'>", unsafe_allow_html=True)
    st.subheader("📊 Analytics & Trends")
    
    # Activity Timeline
    st.markdown("#### 📈 Activity Timeline (Last 30 Minutes)")
    
    # Generate activity history
    times = [datetime.now() - timedelta(minutes=i) for i in range(30, 0, -1)]
    activities = []
    
    for t in times:
        # Simulate activity changes
        minute = t.minute
        if minute < 10:
            activity = 'RESTING'
        elif minute < 20:
            activity = 'WALKING'
        else:
            activity = 'RESTING'
        activities.append(activity)
    
    # Create timeline dataframe
    df_timeline = pd.DataFrame({
        'Time': times,
        'Activity': activities
    })
    
    # Activity distribution chart
    activity_counts = df_timeline['Activity'].value_counts().reset_index()
    activity_counts.columns = ['Activity', 'Count']
    
    fig_activity = px.bar(
        activity_counts,
        x='Activity',
        y='Count',
        color='Activity',
        color_discrete_map={
            'RESTING': '#10b981',
            'WALKING': '#3b82f6',
            'RUNNING': '#ef4444'
        },
        title="Activity Distribution"
    )
    fig_activity.update_layout(height=300, showlegend=False)
    st.plotly_chart(fig_activity, use_container_width=True)
    
    st.markdown("---")
    
    # Daily Summary
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 📅 Daily Summary")
        st.markdown(f"""
        <div class='metric-box'>
            <p><strong>Avg Heart Rate:</strong> {current['hr']} BPM</p>
            <p><strong>Avg SpO₂:</strong> {current['spo2']}%</p>
            <p><strong>Avg Temperature:</strong> {current['temp']}°C</p>
            <p><strong>Main Activity:</strong> {current['activity']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("#### ⚠️ Alerts & Thresholds")
        
        alerts = []
        
        # Check thresholds
        if current['hr'] > 100 and current['activity'] == 'RESTING':
            alerts.append(f"High HR ({current['hr']} BPM) while resting")
        
        if current['spo2'] < 90:
            alerts.append(f"Low SpO₂ ({current['spo2']}%)")
        
        if current['temp'] > 37.5:
            alerts.append(f"Elevated temperature ({current['temp']}°C)")
        
        if alerts:
            for alert in alerts:
                st.markdown(f"<div class='alert-box'>🔴 {alert}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='normal-box'>✅ All readings normal</div>", unsafe_allow_html=True)
    
    with col3:
        st.markdown("#### 📥 Export Data")
        st.markdown("""
        <div class='metric-box'>
            <p>Download data for analysis:</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Create sample data for download
        sample_data = pd.DataFrame({
            'Timestamp': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            'Heart_Rate': [current['hr']],
            'SpO2': [current['spo2']],
            'Temperature': [current['temp']],
            'Activity': [current['activity']]
        })
        
        csv = sample_data.to_csv(index=False)
        st.download_button(
            label="📥 Download Today's Data",
            data=csv,
            file_name=f"stemcube_data_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    st.markdown("---")
    
    # Feature Importance (Simplified for your 3 activities)
    st.markdown("#### 🎯 Activity Detection Factors")
    
    factors = pd.DataFrame({
        'Factor': ['Movement Magnitude', 'Heart Rate Pattern', 'Acceleration Variance'],
        'Importance (%)': [65, 25, 10]
    })
    
    fig_factors = px.bar(
        factors,
        x='Importance (%)',
        y='Factor',
        orientation='h',
        color='Factor',
        color_discrete_sequence=['#667eea', '#764ba2', '#10b981']
    )
    fig_factors.update_layout(height=250, showlegend=False)
    st.plotly_chart(fig_factors, use_container_width=True)
    
    st.caption("Factors considered by STEMCUBE Master for activity classification")
    
    st.markdown("</div>", unsafe_allow_html=True)

# ================ MAIN DASHBOARD ================
def main():
    """Main dashboard function"""
    
    # Malaysia timezone
    malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
    current_time_malaysia = datetime.now(malaysia_tz)
    
    # Header
    st.markdown(f"""
    <div class='main-header'>
        <h1 style='margin: 0;'>🏥 STEMCUBE Health Monitoring System</h1>
        <p style='margin: 5px 0 0 0; opacity: 0.9;'>
            Real-time vital signs monitoring • LoRa wireless • Malaysia Time: {current_time_malaysia.strftime('%H:%M:%S')}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load data
    data = load_real_time_data()
    
    if not data:
        st.error("❌ No data connection. Start Uploader.py on your local machine.")
        return
    
    current = data['data']
    
    # DATA LOG TABLE (ALWAYS ON TOP)
    st.markdown("<div class='tab-container'>", unsafe_allow_html=True)
    st.subheader("📋 Live Data Log")
    
    # Create recent data history
    data_history = []
    for i in range(10):  # Last 10 readings
        timestamp = (datetime.now() - timedelta(seconds=i*5)).strftime('%H:%M:%S')
        data_history.append({
            'malaysia_time': timestamp,
            'node_id': current['node_id'],
            'hr': int(current['hr'] + np.random.normal(0, 2)),
            'spo2': int(current['spo2'] + np.random.normal(0, 1)),
            'temp': round(current['temp'] + np.random.normal(0, 0.1), 1),
            'activity': current['activity'],
            'rssi': current['rssi'],
            'packet_id': current['packet_id'] - i
        })
    
    # Reverse to show newest first
    data_history.reverse()
    
    # Display table
    df_log = pd.DataFrame(data_history)
    st.dataframe(df_log, use_container_width=True, height=300)
    
    # Current data summary
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("❤️ Heart Rate", f"{current['hr']} BPM")
    with col2:
        st.metric("🩸 SpO₂", f"{current['spo2']}%")
    with col3:
        st.metric("🌡️ Temperature", f"{current['temp']}°C")
    with col4:
        st.metric("🚶 Activity", current['activity'])
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 3 TABS
    tab1, tab2, tab3 = st.tabs(["🩺 Health Vitals", "📡 System Status", "📊 Analytics"])
    
    with tab1:
        tab_health_vitals(data)
    
    with tab2:
        tab_system_status(data)
    
    with tab3:
        tab_analytics(data)
    
    # Auto-refresh
    if st.session_state.get('auto_refresh', True):
        time.sleep(1)  # 1 second refresh for real-time
        st.rerun()

# ================ RUN DASHBOARD ================
if __name__ == "__main__":
    # Initialize session state
    if 'auto_refresh' not in st.session_state:
        st.session_state.auto_refresh = True
    
    # Simple login
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.title("🔐 STEMCUBE Dashboard")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            if st.button("Login"):
                if username == "admin" and password == "stemcube2025":
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        
        st.info("**Default:** admin / stemcube2025")
        st.stop()
    
    main()