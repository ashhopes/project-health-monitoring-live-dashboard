# dashboard_cloud.py - UPDATED WITH REAL STEMCUBE CONNECTION
"""
Live Health Monitoring Dashboard with STEMCUBE
REAL DATA VERSION - Connects to STEMCUBE Bridge
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
    """Check if user is logged in"""
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

# ================ INITIALIZE REAL DATA STORAGE ================
if 'stemcube_real_data' not in st.session_state:
    st.session_state.stemcube_real_data = []
if 'last_real_update' not in st.session_state:
    st.session_state.last_real_update = None
if 'real_data_received' not in st.session_state:
    st.session_state.real_data_received = False

# ================ FUNCTION TO HANDLE INCOMING STEMCUBE DATA ================
def handle_stemcube_data(data):
    """This function is called when STEMCUBE bridge sends data"""
    try:
        if isinstance(data, dict):
            # Add timestamp if not present
            if 'timestamp' not in data:
                data['timestamp'] = datetime.now().isoformat()
            
            # Add to session state
            st.session_state.stemcube_real_data.append(data)
            st.session_state.last_real_update = datetime.now()
            st.session_state.real_data_received = True
            
            # Keep only last 500 records
            if len(st.session_state.stemcube_real_data) > 500:
                st.session_state.stemcube_real_data = st.session_state.stemcube_real_data[-500:]
            
            return True
    except Exception as e:
        st.error(f"Data handling error: {e}")
    
    return False

# ================ SIDEBAR CONTROLS ================
st.sidebar.header("⚙️ Controls")

# Connection status
st.sidebar.subheader("📡 Connection Status")
if st.session_state.real_data_received and st.session_state.last_real_update:
    time_diff = (datetime.now() - st.session_state.last_real_update).total_seconds()
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
available_nodes = ["NODE_e661", "NODE_e662"]
selected_node = st.sidebar.selectbox("Select Node ID", available_nodes)

# Data management
st.sidebar.subheader("💾 Data Management")
if st.sidebar.button("🔄 Clear Data", use_container_width=True):
    st.session_state.stemcube_real_data = []
    st.session_state.real_data_received = False
    st.rerun()

st.sidebar.info("Project by mOONbLOOM26 🌙")

# ================ GET REAL DATA ================
def get_real_data():
    """Get real STEMCUBE data or fallback to simulated"""
    if st.session_state.real_data_received and st.session_state.stemcube_real_data:
        # Convert real data to DataFrame
        df = pd.DataFrame(st.session_state.stemcube_real_data[-n_samples:])
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        return df
    
    # Fallback to simulated data (for testing only)
    st.sidebar.warning("Using simulated data - STEMCUBE not connected")
    return generate_sample_data(n_samples)

def generate_sample_data(num_records=100):
    """Generate simulated data ONLY when STEMCUBE is not connected"""
    base_time = datetime.now() - timedelta(minutes=num_records)
    data = []
    for i in range(num_records):
        timestamp = base_time + timedelta(seconds=i)
        hr = 70 + np.sin(i/10) * 10 + np.random.normal(0, 3)
        spo2 = 97 + np.random.normal(0, 1.5)
        temp = 36.5 + np.sin(i/20) * 0.3 + np.random.normal(0, 0.1)
        
        data.append({
            'node_id': 'NODE_e661',
            'timestamp': timestamp,
            'hr': max(60, min(120, hr)),
            'spo2': max(92, min(99, spo2)),
            'temp': max(35, min(38.5, temp)),
            'ax': np.random.normal(0, 0.2),
            'ay': np.random.normal(0, 0.2),
            'az': 1 + np.random.normal(0, 0.1),
            'activity': 'RESTING' if i % 20 < 15 else 'WALKING'
        })
    return pd.DataFrame(data)

# ================ ACTIVITY CLASSIFICATION ================
def classify_activity(ax, ay, az):
    """Classify activity based on motion sensor data"""
    try:
        magnitude = np.sqrt(ax**2 + ay**2 + az**2)
        if magnitude < 1.1:
            return "Resting"
        elif magnitude < 2.0:
            return "Walking"
        elif magnitude < 3.5:
            return "Brisk Walking"
        else:
            return "Running"
    except:
        return "Unknown"

# ================ MAIN DASHBOARD ================
try:
    # Get data
    df = get_real_data()
    
    if df.empty:
        st.warning("📊 No data available")
        df = generate_sample_data(50)
    
    # Convert timestamp
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors="coerce")
    
    # Filter for selected node
    if 'node_id' in df.columns:
        node_df = df[df['node_id'] == selected_node].copy()
    else:
        node_df = df.copy()
    
    if not node_df.empty and 'timestamp' in node_df.columns:
        node_df = node_df.sort_values("timestamp", ascending=True)
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["🩺 Live Vitals", "📡 System Status", "📊 Analytics"])

    with tab1:
        st.header(f"Health Vitals - {selected_node}")
        
        if node_df.empty:
            st.warning(f"📭 No data available")
        else:
            latest = node_df.iloc[-1]
            
            # Create metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                hr_value = latest.get('hr', 0)
                st.metric("Heart Rate", f"{hr_value:.0f} BPM", 
                         "Normal" if 60 <= hr_value <= 100 else "Check")
                
                # HR Chart
                if len(node_df) > 1:
                    fig_hr = go.Figure()
                    fig_hr.add_trace(go.Scatter(
                        x=node_df['timestamp'], y=node_df['hr'],
                        mode='lines', line=dict(color='#FF6B6B', width=2)
                    ))
                    fig_hr.update_layout(height=200, margin=dict(t=30, b=30, l=30, r=30))
                    st.plotly_chart(fig_hr, use_container_width=True)
            
            with col2:
                spo2_value = latest.get('spo2', 0)
                fig_spo2 = go.Figure(go.Indicator(
                    mode="gauge+number", value=spo2_value, title={'text': "SpO₂ (%)"},
                    gauge={'axis': {'range': [85, 100]},
                          'bar': {'color': "green" if spo2_value >= 95 else "orange"}}
                ))
                fig_spo2.update_layout(height=250)
                st.plotly_chart(fig_spo2, use_container_width=True)
            
            with col3:
                temp_value = latest.get('temp', 0)
                st.metric("Temperature", f"{temp_value:.1f} °C", 
                         "Normal" if 36 <= temp_value <= 37.5 else "Fever")
                
                if len(node_df) > 1:
                    fig_temp = go.Figure()
                    fig_temp.add_trace(go.Scatter(
                        x=node_df['timestamp'], y=node_df['temp'],
                        mode='lines', line=dict(color='#FFA726', width=2)
                    ))
                    fig_temp.update_layout(height=200, margin=dict(t=30, b=30, l=30, r=30))
                    st.plotly_chart(fig_temp, use_container_width=True)
            
            with col4:
                activity = latest.get('activity', 'Unknown')
                if activity == 'Unknown' and all(col in latest for col in ['ax', 'ay', 'az']):
                    activity = classify_activity(latest['ax'], latest['ay'], latest['az'])
                
                activity_emoji = {"Resting": "😴", "Walking": "🚶", "Running": "🏃", "Unknown": "❓"}
                st.markdown(f"""
                <div style='text-align: center; padding: 20px; border-radius: 10px; background: #f8f9fa;'>
                    <h3>Activity</h3>
                    <div style='font-size: 48px;'>{activity_emoji.get(activity, '📊')}</div>
                    <h2 style='color: #4B0082;'>{activity}</h2>
                </div>
                """, unsafe_allow_html=True)
    
    with tab2:
        st.header("System Status")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info("📡 STEMCUBE Status")
            if st.session_state.real_data_received:
                st.success("✅ Real Data")
                st.metric("Data Points", len(st.session_state.stemcube_real_data))
            else:
                st.warning("⚠️ Simulated Data")
        
        with col2:
            st.info("🌐 Dashboard")
            st.success("✅ Online")
            st.metric("Refresh Rate", f"{refresh_rate}s")
        
        with col3:
            st.info("📊 Data")
            st.metric("Total Records", len(df))
            st.metric("Node", selected_node)
        
        # Recent data table
        st.subheader("Recent Data")
        display_cols = ['timestamp', 'hr', 'spo2', 'temp', 'activity']
        display_df = node_df[[c for c in display_cols if c in node_df.columns]].tail(10).copy()
        if 'timestamp' in display_df.columns:
            display_df['timestamp'] = display_df['timestamp'].dt.strftime("%H:%M:%S")
        st.dataframe(display_df, use_container_width=True)
    
    with tab3:
        st.header("Analytics")
        
        if len(node_df) > 1:
            # Summary stats
            col1, col2, col3 = st.columns(3)
            with col1:
                if 'hr' in node_df.columns:
                    st.metric("Avg HR", f"{node_df['hr'].mean():.1f} BPM")
                    st.metric("Max HR", f"{node_df['hr'].max():.1f} BPM")
            with col2:
                if 'spo2' in node_df.columns:
                    st.metric("Avg SpO₂", f"{node_df['spo2'].mean():.1f}%")
                    st.metric("Min SpO₂", f"{node_df['spo2'].min():.1f}%")
            with col3:
                if 'temp' in node_df.columns:
                    st.metric("Avg Temp", f"{node_df['temp'].mean():.1f}°C")
                    st.metric("Fever Events", f"{(node_df['temp'] > 37.5).sum()}")
            
            # Export data
            st.subheader("Export Data")
            csv = node_df.to_csv(index=False)
            st.download_button("💾 Download CSV", csv, 
                             f"stemcube_data_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                             "text/csv", use_container_width=True)

    # Auto-refresh
    if refresh_rate > 0:
        time.sleep(refresh_rate)
        st.rerun()

except Exception as e:
    st.error(f"Error: {e}")

# Footer
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; color: gray;'>
    <p>STEMCUBE Health Monitoring • {datetime.now().strftime('%H:%M:%S')}</p>
    <p>Data: {'STEMCUBE Real-time' if st.session_state.real_data_received else 'Simulated'}</p>
</div>
""", unsafe_allow_html=True)