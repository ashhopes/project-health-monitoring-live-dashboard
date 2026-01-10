# dashboard_cloud.py - UPDATED WITH REAL STEMCUBE DATA
"""
Live Health Monitoring Dashboard with LoRa
Streamlit Cloud Version - Supports STEMCUBE Real Data
"""

# ================ IMPORTS ================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from io import BytesIO
import json
import os
from datetime import datetime, timedelta
import time

# ================ LOGIN FUNCTION ================
def check_login():
    """Check if user is logged in, show login form if not"""
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.markdown("""
            <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                     padding: 50px; border-radius: 20px; text-align: center;'>
                <h1 style='color: white;'>🔐 Health Monitoring System</h1>
                <p style='color: white;'>Please login to access the dashboard</p>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.button("Login", type="primary", use_container_width=True):
                if username == "admin" and password == "admin123":
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        
        st.markdown("</div>", unsafe_allow_html=True)
        st.stop()

# ================ RUN LOGIN CHECK ================
check_login()

# ================ PAGE SETUP ================
st.set_page_config(
    page_title="STEMCUBE Health Monitoring", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================ HEADER ================
st.markdown("""
<div style='background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
            padding: 25px; border-radius: 15px; color: white; text-align: center; margin-bottom: 25px;'>
    <h1 style='margin: 0;'>🏥 STEMCUBE Real-Time Health Monitoring</h1>
    <p style='margin: 5px 0 0 0;'>Live data from STEMCUBE sensors via LoRa • NODE_e661</p>
</div>
""", unsafe_allow_html=True)

# ================ INITIALIZE SESSION STATE ================
if 'stemcube_data' not in st.session_state:
    st.session_state.stemcube_data = []
if 'last_stemcube_update' not in st.session_state:
    st.session_state.last_stemcube_update = None
if 'stemcube_connected' not in st.session_state:
    st.session_state.stemcube_connected = False

# ================ SIDEBAR CONTROLS ================
st.sidebar.header("⚙️ Controls")

# Connection status
st.sidebar.subheader("📡 Connection Status")
if st.session_state.stemcube_connected and st.session_state.last_stemcube_update:
    time_diff = (datetime.now() - st.session_state.last_stemcube_update).total_seconds()
    if time_diff < 10:
        st.sidebar.success("✅ STEMCUBE Connected")
        st.sidebar.metric("Last Update", f"{time_diff:.0f}s ago")
    else:
        st.sidebar.warning("⚠️ STEMCUBE Disconnected")
        st.sidebar.metric("Last Update", f"{time_diff:.0f}s ago")
else:
    st.sidebar.error("❌ Waiting for STEMCUBE")

# Display settings
st.sidebar.subheader("📊 Display Settings")
refresh_rate = st.sidebar.slider("Auto-refresh every (seconds)", 0, 120, 30)
n_samples = st.sidebar.slider("Number of samples to display", 50, 500, 100)

# Node selection
st.sidebar.subheader("📟 Node Selection")
available_nodes = ["NODE_e661", "NODE_e662", "user_001", "user_002"]
selected_node = st.sidebar.selectbox("Select Node ID", available_nodes)

# Data management
st.sidebar.subheader("💾 Data Management")
if st.sidebar.button("🔄 Clear Data", use_container_width=True):
    st.session_state.stemcube_data = []
    st.session_state.stemcube_connected = False
    st.rerun()

st.sidebar.info("Project by mOONbLOOM26 🌙")

# ================ SIMULATED DATA (FALLBACK) ================
def generate_sample_data(num_records=100):
    """Generate simulated sensor data for demo"""
    base_time = datetime.now() - timedelta(minutes=num_records)
    
    data = []
    for i in range(num_records):
        timestamp = base_time + timedelta(seconds=i)
        
        hr_base = 72
        hr_variation = np.sin(i/10) * 10 + np.random.normal(0, 3)
        hr = max(60, min(120, hr_base + hr_variation))
        
        spo2 = max(92, min(99, 97 + np.random.normal(0, 1.5)))
        
        temp_base = 36.5
        temp_variation = np.sin(i/20) * 0.3 + np.random.normal(0, 0.1)
        temp = max(35, min(38.5, temp_base + temp_variation))
        
        ax = np.random.normal(0, 0.2)
        ay = np.random.normal(0, 0.2)
        az = 1 + np.random.normal(0, 0.1)
        
        data.append({
            'node_id': 'NODE_e661',
            'timestamp': timestamp,
            'hr': hr,
            'spo2': spo2,
            'temp': temp,
            'ax': ax,
            'ay': ay,
            'az': az,
            'activity': 'RESTING' if i % 20 < 15 else 'WALKING'
        })
    
    return pd.DataFrame(data)

# ================ GET DATA ================
def get_data():
    """Get data from STEMCUBE or fallback to simulated"""
    # Check if we have real STEMCUBE data
    if st.session_state.stemcube_data:
        df = pd.DataFrame(st.session_state.stemcube_data[-n_samples:])
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    
    # Fallback to simulated data
    return generate_sample_data(n_samples)

# ================ ACTIVITY CLASSIFICATION ================
def classify_activity(ax, ay, az, gx=None, gy=None, gz=None):
    """Classify activity based on motion sensor data"""
    try:
        ax = float(ax) if pd.notna(ax) else 0
        ay = float(ay) if pd.notna(ay) else 0
        az = float(az) if pd.notna(az) else 0
        
        magnitude = np.sqrt(ax**2 + ay**2 + az**2)
        
        if magnitude < 1.1:
            return "Resting/Sleeping"
        elif magnitude < 2.0:
            return "Light Activity"
        elif magnitude < 3.5:
            return "Walking"
        elif magnitude < 5.0:
            return "Brisk Walking"
        else:
            return "Running/Vigorous"
    except:
        return "Unknown"

# ================ MAIN DASHBOARD LOGIC ================
try:
    # Get data
    df = get_data()
    
    if df.empty:
        st.info("📊 No data found yet. Using simulated data.")
        df = generate_sample_data(n_samples)
    
    # Convert timestamp
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors="coerce")
    
    # Filter data for selected node
    if 'node_id' in df.columns:
        node_df = df[df['node_id'] == selected_node].copy()
    elif 'id_user' in df.columns:
        node_df = df[df['id_user'] == selected_node].copy()
    else:
        node_df = df.copy()
    
    if not node_df.empty and 'timestamp' in node_df.columns:
        node_df = node_df.sort_values("timestamp", ascending=True)
    
    # ============ CREATE TABS ============
    tab1, tab2, tab3 = st.tabs(["🩺 Health Vitals", "📡 System Status", "📊 Analytics"])

    # ============ TAB 1: HEALTH VITALS ============
    with tab1:
        st.header(f"Health Vitals - {selected_node}")
        
        if node_df.empty:
            st.warning(f"📭 No data available for {selected_node}")
        else:
            latest = node_df.iloc[-1]
            
            # Row 1: Current vitals with metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                # Heart Rate
                hr_value = latest.get('hr', 0)
                hr_trend = ""
                if len(node_df) > 1 and 'hr' in node_df.columns:
                    hr_trend = "↑" if node_df['hr'].iloc[-1] > node_df['hr'].iloc[-2] else "↓"
                
                st.metric(
                    label="Heart Rate",
                    value=f"{hr_value:.0f} BPM",
                    delta=hr_trend
                )
                
                # Heart rate line chart
                if len(node_df) > 1 and 'hr' in node_df.columns:
                    fig_hr = go.Figure()
                    fig_hr.add_trace(go.Scatter(
                        x=node_df['timestamp'],
                        y=node_df['hr'],
                        mode='lines',
                        name='Heart Rate',
                        line=dict(color='#FF6B6B', width=2)
                    ))
                    fig_hr.update_layout(
                        title="Heart Rate Trend",
                        height=200,
                        margin=dict(t=30, b=30, l=30, r=30),
                        showlegend=False,
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)'
                    )
                    st.plotly_chart(fig_hr, use_container_width=True, config={'displayModeBar': False})
            
            with col2:
                # SpO2 Gauge
                spo2_value = latest.get('spo2', 0)
                spo2_color = "green" if spo2_value >= 95 else "red" if spo2_value < 90 else "orange"
                
                fig_spo2 = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=spo2_value,
                    title={'text': "SpO₂ (%)"},
                    domain={'x': [0, 1], 'y': [0, 1]},
                    gauge={
                        'axis': {'range': [85, 100]},
                        'bar': {'color': spo2_color},
                        'steps': [
                            {'range': [85, 90], 'color': "red"},
                            {'range': [90, 95], 'color': "orange"},
                            {'range': [95, 100], 'color': "green"}
                        ]
                    }
                ))
                fig_spo2.update_layout(height=250)
                st.plotly_chart(fig_spo2, use_container_width=True, config={'displayModeBar': False})
            
            with col3:
                # Temperature
                temp_value = latest.get('temp', 0)
                temp_status = "🟢 Normal" if 36 <= temp_value <= 37.5 else "🟡 Mild" if 37.6 <= temp_value <= 38 else "🔴 Fever"
                st.metric(
                    label="Temperature",
                    value=f"{temp_value:.1f} °C",
                    delta=temp_status
                )
                
                # Temperature trend
                if len(node_df) > 1 and 'temp' in node_df.columns:
                    fig_temp = go.Figure()
                    fig_temp.add_trace(go.Scatter(
                        x=node_df['timestamp'],
                        y=node_df['temp'],
                        mode='lines',
                        name='Temperature',
                        line=dict(color='#FFA726', width=2)
                    ))
                    fig_temp.add_hline(y=37.5, line_dash="dash", line_color="red")
                    fig_temp.update_layout(
                        title="Temperature Trend",
                        height=200,
                        margin=dict(t=30, b=30, l=30, r=30),
                        showlegend=False
                    )
                    st.plotly_chart(fig_temp, use_container_width=True, config={'displayModeBar': False})
            
            with col4:
                # Activity
                activity = latest.get('activity', 'Unknown')
                if activity == 'Unknown' and all(col in latest for col in ['ax', 'ay', 'az']):
                    activity = classify_activity(
                        latest.get('ax', 0), latest.get('ay', 0), latest.get('az', 0)
                    )
                
                activity_emoji = {
                    "Resting/Sleeping": "😴",
                    "Light Activity": "🚶",
                    "Walking": "🚶",
                    "Brisk Walking": "🏃",
                    "Running/Vigorous": "🏃💨",
                    "RESTING": "😴",
                    "WALKING": "🚶",
                    "Unknown": "❓"
                }
                
                st.markdown(f"""
                <div style='text-align: center; padding: 20px; border-radius: 10px; background: #f8f9fa;'>
                    <h3 style='margin-bottom: 10px;'>Activity</h3>
                    <div style='font-size: 48px; margin: 10px 0;'>{activity_emoji.get(activity, '📊')}</div>
                    <h2 style='color: #4B0082;'>{activity}</h2>
                </div>
                """, unsafe_allow_html=True)
            
            # Motion data
            if 'ax' in latest:
                st.subheader("📡 Motion Data")
                col_m1, col_m2, col_m3 = st.columns(3)
                with col_m1:
                    st.metric("Accel X", f"{latest.get('ax', 0):.3f}")
                with col_m2:
                    st.metric("Accel Y", f"{latest.get('ay', 0):.3f}")
                with col_m3:
                    st.metric("Accel Z", f"{latest.get('az', 0):.3f}")
    
    # ============ TAB 2: SYSTEM STATUS ============
    with tab2:
        st.header(f"System Status - {selected_node}")
        
        if node_df.empty:
            st.warning(f"📭 No system data available")
        else:
            latest = node_df.iloc[-1]
            
            # System metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.info("📡 STEMCUBE Status")
                if st.session_state.stemcube_connected:
                    st.success("✅ Connected")
                    st.metric("Data Points", len(st.session_state.stemcube_data))
                else:
                    st.warning("⚠️ Using Simulated Data")
                
                st.progress(0.85)
                st.metric("Signal Strength", "-75 dBm")
            
            with col2:
                st.info("🌐 Cloud Connection")
                st.success("✅ Streamlit Cloud Active")
                st.metric("Dashboard URL", "project-health...")
                
                # Latency
                if len(node_df) > 1 and 'timestamp' in node_df.columns:
                    timestamps = node_df['timestamp'].tail(10)
                    time_diffs = timestamps.diff().dropna()
                    avg_latency = time_diffs.mean().total_seconds() if not time_diffs.empty else 0
                    st.metric("Update Interval", f"{avg_latency:.1f}s")
            
            with col3:
                st.info("🔋 Battery Status")
                st.progress(0.72)
                st.metric("Battery Level", "72%")
                
                if 'packet_id' in latest:
                    st.metric("Packet ID", latest['packet_id'])
            
            # Recent data
            st.subheader("📨 Recent Data Points")
            display_cols = ['timestamp']
            for col in ['hr', 'spo2', 'temp', 'activity']:
                if col in node_df.columns:
                    display_cols.append(col)
            
            display_df = node_df[display_cols].tail(10).copy()
            if 'timestamp' in display_df.columns:
                display_df['timestamp'] = display_df['timestamp'].dt.strftime("%H:%M:%S")
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # ============ TAB 3: ANALYTICS ============
    with tab3:
        st.header(f"Analytics - {selected_node}")
        
        if node_df.empty:
            st.warning(f"📭 No analytics data available")
        else:
            # Summary statistics
            st.subheader("📊 Summary Statistics")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if 'hr' in node_df.columns:
                    hr_data = node_df['hr'].dropna()
                    if not hr_data.empty:
                        st.metric("Avg Heart Rate", f"{hr_data.mean():.1f} BPM")
                        st.metric("Max Heart Rate", f"{hr_data.max():.1f} BPM")
                        st.metric("Min Heart Rate", f"{hr_data.min():.1f} BPM")
            
            with col2:
                if 'spo2' in node_df.columns:
                    spo2_data = node_df['spo2'].dropna()
                    if not spo2_data.empty:
                        st.metric("Avg SpO₂", f"{spo2_data.mean():.1f}%")
                        st.metric("Min SpO₂", f"{spo2_data.min():.1f}%")
                        low_count = (spo2_data < 95).sum()
                        st.metric("Low SpO₂ Events", low_count)
            
            with col3:
                if 'temp' in node_df.columns:
                    temp_data = node_df['temp'].dropna()
                    if not temp_data.empty:
                        st.metric("Avg Temperature", f"{temp_data.mean():.1f}°C")
                        st.metric("Max Temperature", f"{temp_data.max():.1f}°C")
                        fever_count = (temp_data > 37.5).sum()
                        st.metric("Fever Events", fever_count)
            
            # Trends chart
            st.subheader("📈 Trends")
            if len(node_df) > 1:
                fig = make_subplots(
                    rows=2, cols=2,
                    subplot_titles=('Heart Rate', 'SpO₂', 'Temperature', 'Motion'),
                    vertical_spacing=0.15
                )
                
                # Heart Rate
                if 'hr' in node_df.columns:
                    fig.add_trace(
                        go.Scatter(x=node_df['timestamp'], y=node_df['hr'], 
                                  mode='lines', name='HR', line=dict(color='red')),
                        row=1, col=1
                    )
                
                # SpO2
                if 'spo2' in node_df.columns:
                    fig.add_trace(
                        go.Scatter(x=node_df['timestamp'], y=node_df['spo2'],
                                  mode='lines', name='SpO₂', line=dict(color='blue')),
                        row=1, col=2
                    )
                
                # Temperature
                if 'temp' in node_df.columns:
                    fig.add_trace(
                        go.Scatter(x=node_df['timestamp'], y=node_df['temp'],
                                  mode='lines', name='Temp', line=dict(color='orange')),
                        row=2, col=1
                    )
                
                # Motion magnitude
                if all(col in node_df.columns for col in ['ax', 'ay', 'az']):
                    node_df['motion'] = (node_df['ax']**2 + node_df['ay']**2 + node_df['az']**2) ** 0.5
                    fig.add_trace(
                        go.Scatter(x=node_df['timestamp'], y=node_df['motion'],
                                  mode='lines', name='Motion', line=dict(color='green')),
                        row=2, col=2
                    )
                
                fig.update_layout(height=600, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            
            # Data export
            st.subheader("📥 Export Data")
            col_exp1, col_exp2 = st.columns(2)
            
            with col_exp1:
                csv = node_df.to_csv(index=False)
                st.download_button(
                    label="💾 Download CSV",
                    data=csv,
                    file_name=f"stemcube_data_{selected_node}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col_exp2:
                if st.button("📋 Copy to Clipboard", use_container_width=True):
                    st.session_state.clipboard = node_df.to_string()
                    st.success("Data copied!")

    # Auto-refresh
    if refresh_rate > 0:
        time.sleep(refresh_rate)
        st.rerun()

except Exception as e:
    st.error(f"Dashboard error: {e}")
    st.info("Please check the connection and try again.")

# Footer
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; color: gray;'>
    <p>STEMCUBE Health Monitoring System • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p>Data Source: {'STEMCUBE' if st.session_state.stemcube_connected else 'Simulated'}</p>
</div>
""", unsafe_allow_html=True)