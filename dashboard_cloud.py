# dashboard_cloud.py - STREAMLIT CLOUD VERSION
"""
Live Health Monitoring Dashboard with LoRa
Streamlit Cloud Version - Direct STEMCUBE Connection
NO Flask needed here - Flask only in local bridge
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time
import requests
import json
import os

# ================ PAGE CONFIG ================
st.set_page_config(
    page_title="STEMCUBE Health Monitoring",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================ CUSTOM CSS ================
st.markdown("""
<style>
    /* Main container */
    .main {
        padding: 0rem 1rem;
    }
    
    /* Metrics styling */
    [data-testid="metric-container"] {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #764ba2;
    }
    
    /* Status badges */
    .status-connected {
        background-color: #d4edda;
        color: #155724;
        padding: 10px 20px;
        border-radius: 25px;
        font-weight: bold;
        text-align: center;
        font-size: 16px;
    }
    
    .status-disconnected {
        background-color: #f8d7da;
        color: #721c24;
        padding: 10px 20px;
        border-radius: 25px;
        font-weight: bold;
        text-align: center;
        font-size: 16px;
    }
    
    .status-simulated {
        background-color: #fff3cd;
        color: #856404;
        padding: 10px 20px;
        border-radius: 25px;
        font-weight: bold;
        text-align: center;
        font-size: 16px;
    }
    
    /* Card styling */
    .vital-card {
        background: white;
        padding: 15px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 15px;
        border-left: 5px solid;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f8f9fa;
        border-radius: 10px 10px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #667eea;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# ================ INITIALIZE SESSION STATE ================
# Initialize all session state variables
if 'stemcube_data' not in st.session_state:
    st.session_state.stemcube_data = []
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()
if 'connection_status' not in st.session_state:
    st.session_state.connection_status = "simulated"
if 'data_source' not in st.session_state:
    st.session_state.data_source = "simulated"
if 'api_url' not in st.session_state:
    st.session_state.api_url = ""
if 'refresh_counter' not in st.session_state:
    st.session_state.refresh_counter = 0

# ================ SIMULATED DATA GENERATOR ================
def generate_simulated_data(num_records=1):
    """Generate realistic simulated data"""
    data_list = []
    
    for i in range(num_records):
        # Base values with realistic variations
        time_offset = st.session_state.refresh_counter * 3  # 3 seconds per refresh
        
        # Heart Rate with natural variation
        hr_base = 72
        hr_variation = np.sin(time_offset/10) * 6 + np.random.normal(0, 1.5)
        hr = max(60, min(110, hr_base + hr_variation))
        
        # SpO2 with slight variations
        spo2 = max(94, min(99, 97 + np.random.normal(0, 0.5)))
        
        # Temperature with daily rhythm
        temp_base = 36.5
        temp_variation = np.sin(time_offset/30) * 0.1 + np.random.normal(0, 0.03)
        temp = max(36.0, min(37.2, temp_base + temp_variation))
        
        # Activity simulation
        activity_cycle = time_offset % 60
        if activity_cycle < 40:
            activity = "RESTING"
            ax, ay, az = np.random.normal(0, 0.05, 3)
            az += 1.0  # gravity
        elif activity_cycle < 55:
            activity = "WALKING"
            ax = np.sin(time_offset/3) * 0.2 + np.random.normal(0, 0.1)
            ay = np.cos(time_offset/3) * 0.1 + np.random.normal(0, 0.05)
            az = 1.0 + np.random.normal(0, 0.05)
        else:
            activity = "ACTIVE"
            ax = np.sin(time_offset/2) * 0.3 + np.random.normal(0, 0.15)
            ay = np.cos(time_offset/2) * 0.2 + np.random.normal(0, 0.1)
            az = 1.0 + np.random.normal(0, 0.08)
        
        data = {
            'node_id': 'NODE_e661',
            'timestamp': datetime.now().isoformat(),
            'hr': float(hr),
            'spo2': float(spo2),
            'temp': float(temp),
            'ax': float(ax),
            'ay': float(ay),
            'az': float(az),
            'gx': float(np.random.normal(0, 0.2)),
            'gy': float(np.random.normal(0, 0.2)),
            'gz': float(np.random.normal(0, 0.2)),
            'activity': activity,
            'packet_id': 1000 + st.session_state.refresh_counter,
            'battery_level': np.random.uniform(75, 95),
            'data_source': 'simulated'
        }
        data_list.append(data)
    
    return data_list

# ================ GET DATA FROM LOCAL BRIDGE ================
def get_data_from_bridge(api_url=""):
    """Get data from local bridge API"""
    if not api_url:
        return None
    
    try:
        response = requests.get(api_url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'success' in data and data['success']:
                bridge_data = data.get('data', {})
                
                # Add timestamp if not present
                if 'timestamp' not in bridge_data:
                    bridge_data['timestamp'] = datetime.now().isoformat()
                
                # Add data source
                bridge_data['data_source'] = 'stemcube'
                
                return bridge_data
                
        return None
        
    except Exception as e:
        # Silent fail - return None
        return None

# ================ HEADER SECTION ================
st.markdown("""
<div style='background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
            padding: 25px; border-radius: 15px; color: white; margin-bottom: 20px;'>
    <h1 style='margin: 0;'>🏥 STEMCUBE Real-Time Health Monitoring</h1>
    <p style='margin: 5px 0 0 0; opacity: 0.9;'>Live data from STEMCUBE sensors via LoRa</p>
</div>
""", unsafe_allow_html=True)

# Status row
col_status1, col_status2, col_status3 = st.columns([1, 1, 1])

with col_status1:
    # Connection status display
    if st.session_state.connection_status == "connected":
        st.markdown('<div class="status-connected">✅ CONNECTED TO STEMCUBE</div>', unsafe_allow_html=True)
    elif st.session_state.connection_status == "simulated":
        st.markdown('<div class="status-simulated">📡 USING SIMULATED DATA</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-disconnected">⚠️ DISCONNECTED</div>', unsafe_allow_html=True)

with col_status2:
    # Data source info
    source_text = "STEMCUBE" if st.session_state.connection_status == "connected" else "Simulated"
    delta_text = "Live" if st.session_state.connection_status == "connected" else "Demo"
    
    st.metric(
        "Data Source",
        source_text,
        delta_text
    )

with col_status3:
    # Last update
    time_diff = (datetime.now() - st.session_state.last_update).total_seconds()
    if time_diff < 10:
        st.metric("Last Update", f"{time_diff:.1f}s ago", delta="Receiving")
    else:
        st.metric("Last Update", f"{time_diff:.0f}s ago", delta="Idle", delta_color="off")

# ================ SIDEBAR ================
with st.sidebar:
    st.markdown("## ⚙️ Dashboard Controls")
    
    # Connection Settings
    st.subheader("🔌 Connection Settings")
    
    connection_mode = st.radio(
        "Select Mode:",
        ["📡 Simulated Data", "🔗 Local Bridge API"],
        index=0,
        key="connection_mode"
    )
    
    if connection_mode == "🔗 Local Bridge API":
        api_url = st.text_input(
            "Bridge API URL:",
            value=st.session_state.api_url,
            placeholder="http://localhost:5000/api/data",
            key="api_url_input"
        )
        
        # Help text
        st.caption("💡 Run bridge_api.py on your PC first")
        st.caption("🌐 Use ngrok for internet access")
        
        col_test1, col_test2 = st.columns(2)
        with col_test1:
            if st.button("🔗 Test Connection", use_container_width=True, key="test_conn"):
                with st.spinner("Testing..."):
                    test_data = get_data_from_bridge(api_url)
                    if test_data:
                        st.success("✅ Connected!")
                        st.session_state.api_url = api_url
                        st.session_state.connection_status = "connected"
                    else:
                        st.error("❌ Connection failed")
                        st.session_state.connection_status = "disconnected"
        
        with col_test2:
            if st.button("🔄 Use Simulated", use_container_width=True, key="use_sim"):
                st.session_state.connection_status = "simulated"
                st.success("Switched to simulated data")
    
    # Device Selection
    st.subheader("📟 Device Selection")
    selected_node = st.selectbox(
        "Select Device:",
        ["NODE_e661", "NODE_e662", "user_001", "user_002"],
        index=0,
        key="device_select"
    )
    
    # Display Settings
    st.subheader("📊 Display Settings")
    refresh_rate = st.slider("Refresh interval (seconds)", 1, 10, 3, key="refresh_slider")
    display_samples = st.slider("Samples to display", 10, 100, 30, key="samples_slider")
    
    # Data Controls
    st.subheader("💾 Data Management")
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🔄 Refresh Now", use_container_width=True, type="primary", key="refresh_btn"):
            st.session_state.last_update = datetime.now()
            st.session_state.refresh_counter += 1
            st.rerun()
    
    with col_btn2:
        if st.button("🗑️ Clear Data", use_container_width=True, key="clear_btn"):
            st.session_state.stemcube_data = []
            st.session_state.refresh_counter = 0
            st.success("Data cleared!")
            st.rerun()
    
    # Manual Data Entry
    with st.expander("🧪 Manual Data Entry", expanded=False):
        st.caption("Add test data manually")
        
        col_man1, col_man2, col_man3 = st.columns(3)
        with col_man1:
            manual_hr = st.number_input("HR (BPM)", 60, 120, 72, key="manual_hr")
        with col_man2:
            manual_spo2 = st.number_input("SpO₂ (%)", 90, 100, 96, key="manual_spo2")
        with col_man3:
            manual_temp = st.number_input("Temp (°C)", 35.0, 39.0, 36.5, 0.1, key="manual_temp")
        
        manual_activity = st.selectbox("Activity", ["RESTING", "WALKING", "ACTIVE"], key="manual_act")
        
        if st.button("➕ Add Manual Data", use_container_width=True, key="add_manual"):
            manual_data = {
                'node_id': selected_node,
                'timestamp': datetime.now().isoformat(),
                'hr': manual_hr,
                'spo2': manual_spo2,
                'temp': manual_temp,
                'activity': manual_activity,
                'ax': 0.1,
                'ay': 0.2,
                'az': 1.0,
                'data_source': 'manual'
            }
            
            if len(st.session_state.stemcube_data) >= display_samples:
                st.session_state.stemcube_data = st.session_state.stemcube_data[-(display_samples-1):]
            
            st.session_state.stemcube_data.append(manual_data)
            st.session_state.last_update = datetime.now()
            st.session_state.data_source = "manual"
            st.success(f"Added manual data: HR={manual_hr}, SpO₂={manual_spo2}")
            st.rerun()
    
    # System Info
    st.markdown("---")
    st.markdown("### 📈 System Info")
    
    if st.session_state.stemcube_data:
        data_count = len(st.session_state.stemcube_data)
        st.metric("Data Points", data_count)
        
        if data_count > 0:
            latest = st.session_state.stemcube_data[-1]
            st.metric("Latest HR", f"{latest.get('hr', 0):.0f} BPM")
            st.metric("Battery", f"{latest.get('battery_level', 75):.0f}%")
    
    st.markdown("---")
    st.caption("🌙 Project by mOONbLOOM26")
    st.caption(f"Updated: {datetime.now().strftime('%H:%M:%S')}")

# ================ GET CURRENT DATA ================
current_data = None

# Update refresh counter
st.session_state.refresh_counter += 1

if connection_mode == "🔗 Local Bridge API" and st.session_state.api_url:
    # Try to get data from bridge
    with st.spinner("Fetching data from STEMCUBE..."):
        current_data = get_data_from_bridge(st.session_state.api_url)
    
    if current_data:
        st.session_state.connection_status = "connected"
        st.session_state.data_source = "stemcube"
        
        # Add to history if not duplicate
        current_packet_id = current_data.get('packet_id')
        if current_packet_id:
            existing_ids = [d.get('packet_id') for d in st.session_state.stemcube_data]
            if current_packet_id not in existing_ids:
                st.session_state.stemcube_data.append(current_data)
        else:
            # Add by timestamp
            current_time = current_data.get('timestamp', datetime.now().isoformat())
            if len(st.session_state.stemcube_data) == 0 or \
               st.session_state.stemcube_data[-1].get('timestamp') != current_time:
                st.session_state.stemcube_data.append(current_data)
        
        st.session_state.last_update = datetime.now()
        
    else:
        # Fallback to simulated
        st.session_state.connection_status = "disconnected"
        current_data = generate_simulated_data(1)[0]
        current_data['data_source'] = 'simulated_fallback'
        
else:
    # Use simulated data
    st.session_state.connection_status = "simulated"
    current_data = generate_simulated_data(1)[0]
    st.session_state.data_source = "simulated"
    
    # Add to history for simulation
    if len(st.session_state.stemcube_data) >= display_samples:
        st.session_state.stemcube_data = st.session_state.stemcube_data[-(display_samples-1):]
    
    st.session_state.stemcube_data.append(current_data)
    st.session_state.last_update = datetime.now()

# ================ PREPARE DATA FOR DISPLAY ================
# Get history data
if st.session_state.stemcube_data:
    # Convert to DataFrame
    df = pd.DataFrame(st.session_state.stemcube_data[-display_samples:])
    
    # Ensure timestamp is datetime
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df = df.sort_values('timestamp', ascending=True)
    
    # Get latest data point
    latest = df.iloc[-1].to_dict() if not df.empty else {}
else:
    df = pd.DataFrame()
    latest = {}

# ================ MAIN DASHBOARD TABS ================
tab1, tab2, tab3 = st.tabs(["🩺 Live Vitals", "📈 Trends", "📊 Export & Logs"])

with tab1:
    # Top row: Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Heart Rate Card
        hr = latest.get('hr', 72)
        hr_status = "Normal" if 60 <= hr <= 100 else "High" if hr > 100 else "Low"
        hr_color = "#28a745" if hr_status == "Normal" else "#dc3545"
        
        st.markdown(f"""
        <div class="vital-card" style="border-left-color: {hr_color};">
            <div style="text-align: center;">
                <h3 style="color: {hr_color}; margin-bottom: 10px;">❤️ Heart Rate</h3>
                <h1 style="color: {hr_color}; margin: 0;">{hr:.0f} BPM</h1>
                <p style="color: #6c757d; margin-top: 5px;">{hr_status}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # HR mini chart
        if 'hr' in df.columns and len(df) > 1:
            fig_hr = go.Figure()
            fig_hr.add_trace(go.Scatter(
                x=df['timestamp'].tail(15),
                y=df['hr'].tail(15),
                mode='lines',
                line=dict(color=hr_color, width=3)
            ))
            fig_hr.update_layout(
                height=120,
                margin=dict(t=0, b=0, l=0, r=0),
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=False, showticklabels=False),
                yaxis=dict(showgrid=False, showticklabels=False)
            )
            st.plotly_chart(fig_hr, use_container_width=True, config={'displayModeBar': False})
    
    with col2:
        # SpO2 Gauge
        spo2 = latest.get('spo2', 96)
        spo2_status = "Normal" if spo2 >= 95 else "Low" if spo2 >= 90 else "Critical"
        spo2_color = "#28a745" if spo2 >= 95 else "#ffc107" if spo2 >= 90 else "#dc3545"
        
        # Create gauge chart
        fig_spo2 = go.Figure(go.Indicator(
            mode="gauge+number",
            value=spo2,
            title={'text': "🩸 SpO₂ (%)", 'font': {'size': 16}},
            number={'font': {'size': 28, 'color': spo2_color}},
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={
                'axis': {'range': [85, 100], 'tickwidth': 1},
                'bar': {'color': spo2_color, 'thickness': 0.6},
                'steps': [
                    {'range': [85, 90], 'color': 'rgba(220, 53, 69, 0.1)'},
                    {'range': [90, 95], 'color': 'rgba(255, 193, 7, 0.1)'},
                    {'range': [95, 100], 'color': 'rgba(40, 167, 69, 0.1)'}
                ],
                'threshold': {
                    'line': {'color': spo2_color, 'width': 4},
                    'thickness': 0.8,
                    'value': spo2
                }
            }
        ))
        fig_spo2.update_layout(
            height=220, 
            margin=dict(t=20, b=20, l=20, r=20)
        )
        st.plotly_chart(fig_spo2, use_container_width=True, config={'displayModeBar': False})
    
    with col3:
        # Temperature Card
        temp = latest.get('temp', 36.5)
        temp_status = "Normal" if 36 <= temp <= 37.5 else "Fever" if temp > 37.5 else "Low"
        temp_color = "#28a745" if temp_status == "Normal" else "#dc3545"
        
        st.markdown(f"""
        <div class="vital-card" style="border-left-color: {temp_color};">
            <div style="text-align: center;">
                <h3 style="color: {temp_color}; margin-bottom: 10px;">🌡️ Temperature</h3>
                <h1 style="color: {temp_color}; margin: 0;">{temp:.1f} °C</h1>
                <p style="color: #6c757d; margin-top: 5px;">{temp_status}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Temp mini chart
        if 'temp' in df.columns and len(df) > 1:
            fig_temp = go.Figure()
            fig_temp.add_trace(go.Scatter(
                x=df['timestamp'].tail(15),
                y=df['temp'].tail(15),
                mode='lines',
                line=dict(color=temp_color, width=3)
            ))
            fig_temp.add_hline(y=37.5, line_dash="dash", line_color="#dc3545", opacity=0.3)
            fig_temp.update_layout(
                height=120,
                margin=dict(t=0, b=0, l=0, r=0),
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=False, showticklabels=False),
                yaxis=dict(showgrid=False, showticklabels=False)
            )
            st.plotly_chart(fig_temp, use_container_width=True, config={'displayModeBar': False})
    
    with col4:
        # Activity Card
        activity = latest.get('activity', 'UNKNOWN')
        activity_info = {
            'RESTING': {'emoji': '😴', 'color': '#6c757d', 'desc': 'At Rest'},
            'WALKING': {'emoji': '🚶', 'color': '#17a2b8', 'desc': 'Walking'},
            'ACTIVE': {'emoji': '🏃', 'color': '#28a745', 'desc': 'Active'},
            'MANUAL': {'emoji': '✍️', 'color': '#ffc107', 'desc': 'Manual Entry'},
            'UNKNOWN': {'emoji': '❓', 'color': '#dc3545', 'desc': 'Unknown'}
        }.get(activity, {'emoji': '❓', 'color': '#dc3545', 'desc': 'Unknown'})
        
        st.markdown(f"""
        <div class="vital-card" style="border-left-color: {activity_info['color']};">
            <div style="text-align: center;">
                <h3 style="color: {activity_info['color']}; margin-bottom: 10px;">Activity Status</h3>
                <div style="font-size: 48px; margin: 5px 0;">{activity_info['emoji']}</div>
                <h2 style="color: {activity_info['color']}; margin: 5px 0;">{activity}</h2>
                <p style="color: #6c757d; margin: 0;">{activity_info['desc']}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Motion Sensors Section
    st.subheader("📡 Motion Sensors")
    motion_cols = st.columns(6)
    
    motion_data = [
        ('Accel X', 'ax', '#FF6384'),
        ('Accel Y', 'ay', '#36A2EB'),
        ('Accel Z', 'az', '#FFCE56'),
        ('Gyro X', 'gx', '#4BC0C0'),
        ('Gyro Y', 'gy', '#9966FF'),
        ('Gyro Z', 'gz', '#FF9F40')
    ]
    
    for i, (name, key, color) in enumerate(motion_data):
        with motion_cols[i]:
            value = latest.get(key, 0)
            st.metric(name, f"{value:.3f}", delta_color="off")
    
    # Recent Data Table
    st.subheader("📋 Recent Readings")
    if not df.empty:
        display_cols = ['timestamp', 'hr', 'spo2', 'temp', 'activity', 'data_source']
        available_cols = [col for col in display_cols if col in df.columns]
        
        display_df = df[available_cols].tail(8).copy()
        
        if 'timestamp' in display_df.columns:
            display_df['timestamp'] = display_df['timestamp'].dt.strftime("%H:%M:%S")
        
        # Style the dataframe
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "hr": st.column_config.NumberColumn("HR", format="%d BPM"),
                "spo2": st.column_config.NumberColumn("SpO₂", format="%d%%"),
                "temp": st.column_config.NumberColumn("Temp", format="%.1f °C"),
                "data_source": st.column_config.TextColumn("Source")
            }
        )
    else:
        st.info("No data available yet. Start collecting data!")

with tab2:
    st.subheader("📈 Vital Signs Trends")
    
    if not df.empty and len(df) > 1:
        # Create trend charts
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Heart Rate Trend', 'SpO₂ Trend', 'Temperature Trend', 'Motion Trend'),
            vertical_spacing=0.15,
            horizontal_spacing=0.1
        )
        
        # Heart Rate
        if 'hr' in df.columns:
            fig.add_trace(
                go.Scatter(x=df['timestamp'], y=df['hr'], 
                          mode='lines', name='HR', line=dict(color='#FF6B6B', width=3)),
                row=1, col=1
            )
            fig.add_hline(y=100, line_dash="dash", line_color="orange", opacity=0.5, row=1, col=1)
            fig.add_hline(y=60, line_dash="dash", line_color="orange", opacity=0.5, row=1, col=1)
            fig.add_hrect(y0=60, y1=100, fillcolor="green", opacity=0.1, row=1, col=1)
        
        # SpO2
        if 'spo2' in df.columns:
            fig.add_trace(
                go.Scatter(x=df['timestamp'], y=df['spo2'],
                          mode='lines', name='SpO₂', line=dict(color='#36A2EB', width=3)),
                row=1, col=2
            )
            fig.add_hline(y=95, line_dash="dash", line_color="red", opacity=0.5, row=1, col=2)
            fig.add_hrect(y0=95, y1=100, fillcolor="green", opacity=0.1, row=1, col=2)
        
        # Temperature
        if 'temp' in df.columns:
            fig.add_trace(
                go.Scatter(x=df['timestamp'], y=df['temp'],
                          mode='lines', name='Temp', line=dict(color='#FFA726', width=3)),
                row=2, col=1
            )
            fig.add_hline(y=37.5, line_dash="dash", line_color="red", opacity=0.5, row=2, col=1)
            fig.add_hrect(y0=36, y1=37.5, fillcolor="green", opacity=0.1, row=2, col=1)
        
        # Motion magnitude
        if all(col in df.columns for col in ['ax', 'ay', 'az']):
            df['motion_mag'] = np.sqrt(df['ax']**2 + df['ay']**2 + df['az']**2)
            fig.add_trace(
                go.Scatter(x=df['timestamp'], y=df['motion_mag'],
                          mode='lines', name='Motion', line=dict(color='#4BC0C0', width=3)),
                row=2, col=2
            )
        
        fig.update_layout(
            height=500, 
            showlegend=True,
            template="plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Statistics Cards
        st.subheader("📊 Statistics Summary")
        stat_cols = st.columns(4)
        
        stats_data = []
        if 'hr' in df.columns:
            hr_data = df['hr'].dropna()
            if not hr_data.empty:
                stats_data.append(("Heart Rate", f"{hr_data.mean():.1f} BPM", f"{hr_data.min():.0f}-{hr_data.max():.0f}"))
        
        if 'spo2' in df.columns:
            spo2_data = df['spo2'].dropna()
            if not spo2_data.empty:
                stats_data.append(("SpO₂", f"{spo2_data.mean():.1f}%", f"{spo2_data.min():.0f}-{spo2_data.max():.0f}"))
        
        if 'temp' in df.columns:
            temp_data = df['temp'].dropna()
            if not temp_data.empty:
                stats_data.append(("Temperature", f"{temp_data.mean():.1f}°C", f"{temp_data.min():.1f}-{temp_data.max():.1f}"))
        
        stats_data.append(("Data Points", str(len(df)), f"{display_samples} max"))
        
        for col, (title, value, range_text) in zip(stat_cols, stats_data):
            with col:
                st.metric(title, value)
                st.caption(f"Range: {range_text}")
    
    else:
        st.info("Collect more data to see trends! Currently have {} data points.".format(len(df)))

with tab3:
    st.subheader("📥 Data Export & System Logs")
    
    if not df.empty:
        # Data Summary
        col_sum1, col_sum2, col_sum3 = st.columns(3)
        
        with col_sum1:
            st.metric("Total Records", len(df))
            time_range_min = (df['timestamp'].max() - df['timestamp'].min()).total_seconds() / 60
            st.caption(f"Time range: {time_range_min:.1f} minutes")
        
        with col_sum2:
            data_sources = df['data_source'].unique() if 'data_source' in df.columns else ['unknown']
            st.metric("Data Sources", len(data_sources))
            st.caption(", ".join(data_sources))
        
        with col_sum3:
            st.metric("Current Status", st.session_state.connection_status.upper())
            st.caption(f"Last update: {st.session_state.last_update.strftime('%H:%M:%S')}")
        
        # Export Options
        st.subheader("Export Data")
        
        col_exp1, col_exp2 = st.columns(2)
        
        with col_exp1:
            # CSV Export
            csv_data = df.to_csv(index=False)
            st.download_button(
                label="📄 Download CSV",
                data=csv_data,
                file_name=f"stemcube_data_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True,
                type="primary"
            )
        
        with col_exp2:
            # JSON Export
            json_data = df.to_json(orient='records', indent=2, date_format='iso')
            st.download_button(
                label="📊 Download JSON",
                data=json_data,
                file_name=f"stemcube_data_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json",
                use_container_width=True
            )
        
        # Data Preview
        with st.expander("🔍 View All Data", expanded=False):
            st.dataframe(df, use_container_width=True)
        
        # Connection Logs
        st.subheader("🔌 Connection Logs")
        
        log_data = []
        if st.session_state.stemcube_data:
            for i, data in enumerate(st.session_state.stemcube_data[-10:]):
                timestamp = data.get('timestamp', 'Unknown')
                if isinstance(timestamp, str):
                    try:
                        ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        time_str = ts.strftime("%H:%M:%S")
                    except:
                        time_str = timestamp
                else:
                    time_str = str(timestamp)
                
                log_data.append({
                    "Time": time_str,
                    "HR": data.get('hr', 'N/A'),
                    "SpO₂": data.get('spo2', 'N/A'),
                    "Source": data.get('data_source', 'N/A'),
                    "Activity": data.get('activity', 'N/A')
                })
        
        if log_data:
            log_df = pd.DataFrame(log_data)
            st.table(log_df)
        else:
            st.info("No connection logs available")
    
    else:
        st.warning("No data available for export")
    
    # System Info
    st.markdown("---")
    st.markdown("### ℹ️ System Information")
    
    info_cols = st.columns(2)
    with info_cols[0]:
        st.write("**Dashboard Info:**")
        st.write(f"- Version: 2.0")
        st.write(f"- Streamlit Cloud: Yes")
        st.write(f"- Auto-refresh: {refresh_rate}s")
        st.write(f"- Max samples: {display_samples}")
    
    with info_cols[1]:
        st.write("**Current Session:**")
        st.write(f"- Data points: {len(st.session_state.stemcube_data)}")
        st.write(f"- Connection: {st.session_state.connection_status}")
        st.write(f"- Source: {st.session_state.data_source}")
        st.write(f"- Refresh count: {st.session_state.refresh_counter}")

# ================ AUTO REFRESH ================
if refresh_rate > 0:
    time.sleep(refresh_rate)
    st.rerun()

# ================ FOOTER ================
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; color: #6c757d; padding: 20px;'>
    <p>🏥 STEMCUBE Real-Time Health Monitoring System • v2.0</p>
    <p>Status: <strong>{st.session_state.connection_status.upper()}</strong> • 
       Source: <strong>{st.session_state.data_source.upper()}</strong> • 
       Auto-refresh: <strong>{refresh_rate}s</strong></p>
    <p>Last Update: {st.session_state.last_update.strftime('%H:%M:%S')} • 
       Data Points: {len(st.session_state.stemcube_data)}</p>
    <p>🌙 Project by mOONbLOOM26 • Streamlit Cloud Deployment</p>
</div>
""", unsafe_allow_html=True)# ================ IMPORTS ================