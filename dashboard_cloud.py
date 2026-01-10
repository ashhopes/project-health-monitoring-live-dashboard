# dashboard_cloud.py - UPDATED WITH REAL STEMCUBE DATA INTEGRATION
"""
Live Health Monitoring Dashboard with LoRa
Streamlit Cloud Version - Reads real STEMCUBE data from JSON file
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
import os
from datetime import datetime, timedelta
import time
import threading

# ================ FILE-BASED DATA READER ================

def read_stemcube_data():
    """Read real STEMCUBE data from JSON file"""
    data_file = "stemcube_live_data.json"
    history_file = "stemcube_history.jsonl"
    
    # Create sample data file if doesn't exist
    if not os.path.exists(data_file):
        sample_data = {
            "connected": False,
            "last_update": datetime.now().isoformat(),
            "node_id": "NODE_e661",
            "vitals": {
                "hr": 72,
                "spo2": 96,
                "temp": 36.5,
                "activity": "RESTING"
            },
            "data": {
                "id_user": "NODE_e661",
                "node_id": "NODE_e661",
                "hr": 72,
                "spo2": 96,
                "temp": 36.5,
                "ax": 0.1,
                "ay": 0.2,
                "az": 1.0,
                "activity": "RESTING"
            }
        }
        with open(data_file, 'w') as f:
            json.dump(sample_data, f)
    
    try:
        # Read current data
        with open(data_file, 'r') as f:
            live_data = json.load(f)
        
        # Read history
        history_data = []
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                for line in f:
                    try:
                        history_data.append(json.loads(line.strip()))
                    except:
                        continue
        
        return live_data, history_data
        
    except Exception as e:
        print(f"Error reading data: {e}")
        return None, []

def update_session_state():
    """Update session state with real data"""
    live_data, history_data = read_stemcube_data()
    
    if live_data:
        # Update connection status
        st.session_state.stemcube_connected = live_data.get("connected", False)
        st.session_state.last_stemcube_update = datetime.fromisoformat(
            live_data.get("last_update", datetime.now().isoformat())
        )
        
        # Update current data
        if live_data.get("data"):
            current_data = live_data["data"]
            
            # Add timestamp if not present
            if 'timestamp' not in current_data:
                current_data['timestamp'] = datetime.now().isoformat()
            
            # Add to history (keep only last 1000 entries)
            if 'stemcube_data' not in st.session_state:
                st.session_state.stemcube_data = []
            
            # Add if not duplicate
            if (not st.session_state.stemcube_data or 
                st.session_state.stemcube_data[-1].get('packet_id', 0) != current_data.get('packet_id', 0)):
                
                st.session_state.stemcube_data.append(current_data)
                
                # Keep only last 1000 entries
                if len(st.session_state.stemcube_data) > 1000:
                    st.session_state.stemcube_data = st.session_state.stemcube_data[-1000:]

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

# ================ UPDATE WITH REAL DATA ================
update_session_state()

# ================ SIDEBAR CONTROLS ================
st.sidebar.header("⚙️ Controls")

# Connection status
st.sidebar.subheader("📡 Connection Status")
if st.session_state.stemcube_connected and st.session_state.last_stemcube_update:
    time_diff = (datetime.now() - st.session_state.last_stemcube_update).total_seconds()
    
    if time_diff < 10:
        st.sidebar.success("✅ STEMCUBE Connected")
        st.sidebar.metric("Last Update", f"{time_diff:.1f}s ago")
        
        # Show real data preview
        if st.session_state.stemcube_data:
            latest = st.session_state.stemcube_data[-1]
            st.sidebar.info(f"📊 **Live Data:**")
            st.sidebar.write(f"❤️ HR: {latest.get('hr', 'N/A')} BPM")
            st.sidebar.write(f"🩸 SpO₂: {latest.get('spo2', 'N/A')}%")
            st.sidebar.write(f"🌡️ Temp: {latest.get('temp', 'N/A')}°C")
            
    else:
        st.sidebar.warning("⚠️ STEMCUBE Disconnected")
        st.sidebar.metric("Last Update", f"{time_diff:.0f}s ago")
else:
    st.sidebar.error("❌ Waiting for STEMCUBE")
    st.sidebar.info("Run Uploader.py to connect")

# Display settings
st.sidebar.subheader("📊 Display Settings")
refresh_rate = st.sidebar.slider("Auto-refresh every (seconds)", 1, 120, 5)
n_samples = st.sidebar.slider("Number of samples to display", 50, 500, 100)

# Node selection
st.sidebar.subheader("📟 Node Selection")
available_nodes = ["NODE_e661", "NODE_e662", "user_001", "user_002"]
selected_node = st.sidebar.selectbox("Select Node ID", available_nodes)

# Data management
st.sidebar.subheader("💾 Data Management")
col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("🔄 Refresh Now", use_container_width=True):
        update_session_state()
        st.rerun()
with col2:
    if st.button("🗑️ Clear Data", use_container_width=True):
        st.session_state.stemcube_data = []
        st.session_state.stemcube_connected = False
        st.rerun()

st.sidebar.info("Project by mOONbLOOM26 🌙")

# ================ GENERATE SAMPLE DATA (FALLBACK) ================
def generate_sample_data(num_records=100):
    """Generate simulated sensor data if no real data"""
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
            'node_id': selected_node,
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

# ================ GET DATA FUNCTION ================
def get_dashboard_data():
    """Get data for dashboard - real data prioritized"""
    # Use real data if available
    if st.session_state.stemcube_data:
        # Convert to DataFrame
        real_data = st.session_state.stemcube_data[-n_samples:]
        df = pd.DataFrame(real_data)
        
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        
        # Filter by selected node
        if 'node_id' in df.columns:
            df = df[df['node_id'] == selected_node]
        
        if not df.empty:
            return df
    
    # Fallback to simulated data
    st.info("📊 Using simulated data - waiting for STEMCUBE connection...")
    return generate_sample_data(n_samples)

# ================ ACTIVITY CLASSIFICATION ================
def classify_activity(ax, ay, az):
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

# ================ MAIN DASHBOARD ================
try:
    # Get data
    df = get_dashboard_data()
    
    # Ensure timestamp column
    if 'timestamp' not in df.columns:
        df['timestamp'] = pd.date_range(start=datetime.now()-timedelta(minutes=len(df)), 
                                       periods=len(df), freq='s')
    
    # Sort by timestamp
    df = df.sort_values('timestamp', ascending=True)
    
    # Get latest data point
    latest = df.iloc[-1].to_dict() if not df.empty else {}
    
    # ============ CREATE TABS ============
    tab1, tab2, tab3 = st.tabs(["🩺 Health Vitals", "📡 System Status", "📊 Analytics"])
    
    # ============ TAB 1: HEALTH VITALS ============
    with tab1:
        st.header(f"Health Vitals - {selected_node}")
        
        # Row 1: Current vitals
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Heart Rate
            hr_value = latest.get('hr', 72)
            hr_trend = ""
            if len(df) > 1 and 'hr' in df.columns:
                hr_trend = f"{df['hr'].iloc[-1] - df['hr'].iloc[-2]:+.1f}"
            
            st.metric(
                label="❤️ Heart Rate",
                value=f"{hr_value:.0f} BPM",
                delta=hr_trend,
                delta_color="normal"
            )
            
            # Heart rate chart
            if len(df) > 1 and 'hr' in df.columns:
                fig_hr = go.Figure()
                fig_hr.add_trace(go.Scatter(
                    x=df['timestamp'],
                    y=df['hr'],
                    mode='lines',
                    line=dict(color='#FF6B6B', width=3)
                ))
                fig_hr.update_layout(
                    title="Heart Rate Trend",
                    height=200,
                    margin=dict(t=30, b=30, l=30, r=30),
                    showlegend=False,
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_hr, use_container_width=True, config={'displayModeBar': False})
        
        with col2:
            # SpO2 Gauge
            spo2_value = latest.get('spo2', 96)
            spo2_color = "green" if spo2_value >= 95 else "red" if spo2_value < 90 else "orange"
            
            fig_spo2 = go.Figure(go.Indicator(
                mode="gauge+number",
                value=spo2_value,
                title={'text': "🩸 SpO₂ (%)"},
                domain={'x': [0, 1], 'y': [0, 1]},
                gauge={
                    'axis': {'range': [85, 100]},
                    'bar': {'color': spo2_color},
                    'steps': [
                        {'range': [85, 90], 'color': "red"},
                        {'range': [90, 95], 'color': "orange"},
                        {'range': [95, 100], 'color': "green"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 95
                    }
                }
            ))
            fig_spo2.update_layout(height=250)
            st.plotly_chart(fig_spo2, use_container_width=True, config={'displayModeBar': False})
        
        with col3:
            # Temperature
            temp_value = latest.get('temp', 36.5)
            temp_status = "🟢 Normal" if 36 <= temp_value <= 37.5 else "🟡 Mild" if 37.6 <= temp_value <= 38 else "🔴 Fever"
            
            st.metric(
                label="🌡️ Temperature",
                value=f"{temp_value:.1f} °C",
                delta=temp_status
            )
            
            # Temperature chart
            if len(df) > 1 and 'temp' in df.columns:
                fig_temp = go.Figure()
                fig_temp.add_trace(go.Scatter(
                    x=df['timestamp'],
                    y=df['temp'],
                    mode='lines',
                    line=dict(color='#FFA726', width=3)
                ))
                fig_temp.add_hline(y=37.5, line_dash="dash", line_color="red", 
                                 annotation_text="Fever Threshold")
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
                activity = classify_activity(latest.get('ax', 0), latest.get('ay', 0), latest.get('az', 0))
            
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
            <div style='text-align: center; padding: 20px; border-radius: 10px; 
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        color: white;'>
                <h3 style='margin-bottom: 10px;'>🏃 Activity</h3>
                <div style='font-size: 48px; margin: 10px 0;'>{activity_emoji.get(activity, '📊')}</div>
                <h2 style='color: white;'>{activity}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        # Motion Data
        if 'ax' in latest:
            st.subheader("📡 Motion Sensor Data")
            mcol1, mcol2, mcol3 = st.columns(3)
            with mcol1:
                st.metric("Accel X", f"{latest.get('ax', 0):.3f} g")
            with mcol2:
                st.metric("Accel Y", f"{latest.get('ay', 0):.3f} g")
            with mcol3:
                st.metric("Accel Z", f"{latest.get('az', 0):.3f} g")
    
    # ============ TAB 2: SYSTEM STATUS ============
    with tab2:
        st.header(f"System Status - {selected_node}")
        
        # System metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info("📡 STEMCUBE Status")
            if st.session_state.stemcube_connected:
                st.success("✅ Connected to Real Data")
                st.metric("Data Points", len(st.session_state.stemcube_data))
                
                # Show data source
                if st.session_state.stemcube_data:
                    source = st.session_state.stemcube_data[-1].get('sensor_type', 'STEMCUBE')
                    st.metric("Data Source", source)
            else:
                st.warning("⚠️ Using Simulated Data")
                st.metric("Data Points", len(df))
            
            # Signal strength
            st.progress(0.85)
            st.metric("Signal Strength", "-75 dBm")
        
        with col2:
            st.info("🌐 Dashboard Status")
            st.success("✅ Streamlit Active")
            
            # Update frequency
            if len(df) > 1 and 'timestamp' in df.columns:
                time_diffs = pd.Series(df['timestamp']).diff().dropna()
                avg_interval = time_diffs.mean().total_seconds() if not time_diffs.empty else 0
                st.metric("Update Interval", f"{avg_interval:.1f}s")
            
            st.metric("Display Samples", n_samples)
        
        with col3:
            st.info("🔋 Device Status")
            
            # Battery level
            battery = latest.get('battery_level', 72)
            st.progress(battery/100)
            st.metric("Battery Level", f"{battery:.0f}%")
            
            # Packet info
            if 'packet_id' in latest:
                st.metric("Packet ID", latest['packet_id'])
        
        # Recent data table
        st.subheader("📨 Recent Data Points")
        display_cols = ['timestamp']
        for col in ['hr', 'spo2', 'temp', 'activity', 'packet_id']:
            if col in df.columns:
                display_cols.append(col)
        
        display_df = df[display_cols].tail(10).copy()
        if 'timestamp' in display_df.columns:
            display_df['timestamp'] = display_df['timestamp'].dt.strftime("%H:%M:%S")
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # ============ TAB 3: ANALYTICS ============
    with tab3:
        st.header(f"Analytics - {selected_node}")
        
        # Summary statistics
        st.subheader("📊 Summary Statistics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if 'hr' in df.columns:
                hr_data = df['hr'].dropna()
                if not hr_data.empty:
                    st.metric("Avg Heart Rate", f"{hr_data.mean():.1f} BPM")
                    st.metric("Max Heart Rate", f"{hr_data.max():.1f} BPM")
                    st.metric("Min Heart Rate", f"{hr_data.min():.1f} BPM")
                    
                    # Heart rate zones
                    normal_hr = ((hr_data >= 60) & (hr_data <= 100)).sum()
                    st.metric("Normal HR", f"{normal_hr}")
        
        with col2:
            if 'spo2' in df.columns:
                spo2_data = df['spo2'].dropna()
                if not spo2_data.empty:
                    st.metric("Avg SpO₂", f"{spo2_data.mean():.1f}%")
                    st.metric("Min SpO₂", f"{spo2_data.min():.1f}%")
                    
                    low_spo2 = (spo2_data < 95).sum()
                    st.metric("Low SpO₂ Events", low_spo2)
                    
                    # SpO2 quality
                    if spo2_data.mean() >= 95:
                        st.success("✅ Good Oxygenation")
                    elif spo2_data.mean() >= 90:
                        st.warning("⚠️ Moderate Oxygenation")
                    else:
                        st.error("❌ Poor Oxygenation")
        
        with col3:
            if 'temp' in df.columns:
                temp_data = df['temp'].dropna()
                if not temp_data.empty:
                    st.metric("Avg Temperature", f"{temp_data.mean():.1f}°C")
                    st.metric("Max Temperature", f"{temp_data.max():.1f}°C")
                    
                    fever_events = (temp_data > 37.5).sum()
                    st.metric("Fever Events", fever_events)
                    
                    # Temperature status
                    avg_temp = temp_data.mean()
                    if 36 <= avg_temp <= 37.5:
                        st.success("✅ Normal Temperature")
                    elif 37.6 <= avg_temp <= 38:
                        st.warning("⚠️ Mild Fever")
                    else:
                        st.error("❌ High Fever")
        
        # Trends chart
        st.subheader("📈 Vital Signs Trends")
        
        if len(df) > 1:
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Heart Rate (BPM)', 'SpO₂ (%)', 'Temperature (°C)', 'Motion'),
                vertical_spacing=0.15,
                horizontal_spacing=0.1
            )
            
            # Heart Rate
            if 'hr' in df.columns:
                fig.add_trace(
                    go.Scatter(x=df['timestamp'], y=df['hr'], 
                              mode='lines', name='HR', line=dict(color='red', width=2)),
                    row=1, col=1
                )
                fig.add_hline(y=100, line_dash="dash", line_color="orange", row=1, col=1)
                fig.add_hline(y=60, line_dash="dash", line_color="orange", row=1, col=1)
            
            # SpO2
            if 'spo2' in df.columns:
                fig.add_trace(
                    go.Scatter(x=df['timestamp'], y=df['spo2'],
                              mode='lines', name='SpO₂', line=dict(color='blue', width=2)),
                    row=1, col=2
                )
                fig.add_hline(y=95, line_dash="dash", line_color="red", row=1, col=2)
            
            # Temperature
            if 'temp' in df.columns:
                fig.add_trace(
                    go.Scatter(x=df['timestamp'], y=df['temp'],
                              mode='lines', name='Temp', line=dict(color='orange', width=2)),
                    row=2, col=1
                )
                fig.add_hline(y=37.5, line_dash="dash", line_color="red", row=2, col=1)
            
            # Motion (calculate if needed)
            if all(col in df.columns for col in ['ax', 'ay', 'az']):
                df['motion'] = (df['ax']**2 + df['ay']**2 + df['az']**2) ** 0.5
                fig.add_trace(
                    go.Scatter(x=df['timestamp'], y=df['motion'],
                              mode='lines', name='Motion', line=dict(color='green', width=2)),
                    row=2, col=2
                )
            
            fig.update_layout(height=600, showlegend=True, template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
        
        # Data export
        st.subheader("📥 Export Data")
        col_exp1, col_exp2 = st.columns(2)
        
        with col_exp1:
            csv = df.to_csv(index=False)
            st.download_button(
                label="💾 Download CSV",
                data=csv,
                file_name=f"stemcube_{selected_node}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col_exp2:
            json_data = df.to_json(orient='records', indent=2)
            st.download_button(
                label="📄 Download JSON",
                data=json_data,
                file_name=f"stemcube_{selected_node}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )

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
<div style='text-align: center; color: gray; padding: 20px;'>
    <p>🏥 STEMCUBE Health Monitoring System v2.0</p>
    <p>Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p>Data Source: {'REAL STEMCUBE' if st.session_state.stemcube_connected else 'SIMULATED'}</p>
    <p>Project by mOONbLOOM26 🌙 • Streamlit Cloud</p>
</div>
""", unsafe_allow_html=True)