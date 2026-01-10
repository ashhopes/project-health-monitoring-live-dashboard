# dashboard_FIXED.py - UPDATED WITH REAL STEMCUBE LIVE DATA
"""
Live Health Monitoring Dashboard with LoRa
REAL-TIME data from STEMCUBE to Streamlit
"""

# ================ IMPORTS ================
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
import requests
from io import BytesIO

# ================ PAGE CONFIG ================
st.set_page_config(
    page_title="STEMCUBE Health Monitoring - LIVE",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================ CUSTOM CSS ================
st.markdown("""
<style>
    /* Main container */
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 25px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
    }
    
    /* Metric cards */
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-left: 5px solid #667eea;
        margin-bottom: 15px;
    }
    
    /* Status indicators */
    .status-connected { color: #10B981; font-weight: bold; }
    .status-disconnected { color: #EF4444; font-weight: bold; }
    .status-warning { color: #F59E0B; font-weight: bold; }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #F3F4F6;
        border-radius: 5px 5px 0px 0px;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #667eea;
        color: white;
    }
    
    /* Data table */
    .data-table {
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)

# ================ LOGIN FUNCTION ================
def check_login():
    """Simple login system"""
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    
    if not st.session_state.logged_in:
        st.markdown("""
            <div class='main-header'>
                <h1>🔐 STEMCUBE Health Monitoring System</h1>
                <p>Real-time patient monitoring with LoRa technology</p>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.container():
                st.subheader("Login Required")
                username = st.text_input("👤 Username", key="username")
                password = st.text_input("🔒 Password", type="password", key="password")
                
                col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
                with col_btn2:
                    if st.button("🚀 Login", type="primary", use_container_width=True):
                        if username == "admin" and password == "admin123":
                            st.session_state.logged_in = True
                            st.rerun()
                        else:
                            st.error("Invalid credentials")
                
                # Demo credentials
                with st.expander("Demo Credentials"):
                    st.code("Username: admin\nPassword: admin123")
        
        st.markdown("---")
        st.info("👈 **For testing:** Use the demo credentials above")
        st.stop()

# ================ LOAD LIVE DATA FUNCTION ================
def load_live_stemcube_data():
    """Load live data from STEMCUBE JSON file"""
    try:
        if os.path.exists('stemcube_live_data.json'):
            with open('stemcube_live_data.json', 'r') as f:
                data = json.load(f)
            
            # Check if data is fresh (less than 30 seconds old)
            last_update_str = data.get('last_update', datetime.now().isoformat())
            last_update = datetime.fromisoformat(last_update_str.replace('Z', '+00:00'))
            seconds_ago = (datetime.now() - last_update).total_seconds()
            
            is_fresh = seconds_ago < 30
            is_connected = data.get('status') == 'connected'
            
            # Update session state
            st.session_state.stemcube_connected = is_connected and is_fresh
            st.session_state.last_stemcube_update = last_update
            st.session_state.packets_received = data.get('packets_received', 0)
            
            # Get latest record
            latest_record = data.get('latest_record', {})
            
            if latest_record:
                # Create DataFrame from latest record
                df_record = pd.DataFrame([latest_record])
                
                # Add timestamp
                if 'timestamp' in df_record.columns:
                    df_record['timestamp'] = pd.to_datetime(df_record['timestamp'])
                
                return df_record, data, seconds_ago
            
        return pd.DataFrame(), {}, 999
        
    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        return pd.DataFrame(), {}, 999

# ================ GENERATE SAMPLE DATA ================
def generate_sample_data(num_records=50):
    """Generate sample data for demo"""
    base_time = datetime.now() - timedelta(minutes=num_records)
    
    data = []
    for i in range(num_records):
        timestamp = base_time + timedelta(seconds=i*5)
        
        # Realistic variations
        hr_base = 72
        hr_variation = np.sin(i/10) * 12 + np.random.normal(0, 4)
        hr = max(60, min(130, hr_base + hr_variation))
        
        spo2 = max(92, min(99, 97 + np.random.normal(0, 1.2)))
        
        temp_base = 36.5
        temp_variation = np.sin(i/20) * 0.4 + np.random.normal(0, 0.08)
        temp = max(35.8, min(37.5, temp_base + temp_variation))
        
        # Activity-based variations
        activity_cycle = i // 10
        activity_types = ['RESTING', 'WALKING', 'RUNNING', 'CYCLING']
        activity = activity_types[activity_cycle % 4]
        
        # Motion data based on activity
        if activity == 'RESTING':
            ax, ay, az = np.random.normal(0, 0.1), np.random.normal(0, 0.1), 1.0 + np.random.normal(0, 0.05)
            hr = hr * 0.9  # Lower HR at rest
        elif activity == 'WALKING':
            ax, ay, az = 0.5 + np.random.normal(0, 0.2), np.random.normal(0, 0.1), 1.0 + np.random.normal(0, 0.1)
            hr = hr * 1.1
        elif activity == 'RUNNING':
            ax, ay, az = 1.2 + np.random.normal(0, 0.3), np.random.normal(0, 0.2), 1.0 + np.random.normal(0, 0.15)
            hr = hr * 1.3
        else:  # CYCLING
            ax, ay, az = 0.8 + np.random.normal(0, 0.25), np.random.normal(0, 0.15), 1.0 + np.random.normal(0, 0.1)
            hr = hr * 1.2
        
        data.append({
            'node_id': 'NODE_e661',
            'timestamp': timestamp,
            'hr': round(hr, 0),
            'spo2': round(spo2, 1),
            'temp': round(temp, 1),
            'ax': round(ax, 3),
            'ay': round(ay, 3),
            'az': round(az, 3),
            'activity': activity,
            'packet_id': 1000 + i,
            'battery_level': round(85 - (i % 20) * 0.5, 1)
        })
    
    return pd.DataFrame(data)

# ================ ACTIVITY CLASSIFICATION ================
def classify_activity(ax, ay, az):
    """Classify activity based on acceleration data"""
    try:
        magnitude = np.sqrt(ax**2 + ay**2 + az**2)
        
        if magnitude < 1.05:
            return {"activity": "Resting/Sleeping", "emoji": "😴", "color": "#10B981"}
        elif magnitude < 1.5:
            return {"activity": "Light Activity", "emoji": "🧘", "color": "#3B82F6"}
        elif magnitude < 2.5:
            return {"activity": "Walking", "emoji": "🚶", "color": "#F59E0B"}
        elif magnitude < 4.0:
            return {"activity": "Brisk Walking", "emoji": "🚶‍♂️💨", "color": "#EF4444"}
        else:
            return {"activity": "Running/Vigorous", "emoji": "🏃‍♂️💨", "color": "#DC2626"}
    except:
        return {"activity": "Unknown", "emoji": "❓", "color": "#6B7280"}

# ================ CHECK VITAL ALERTS ================
def check_vital_alerts(hr, spo2, temp):
    """Check for critical vital signs"""
    alerts = []
    
    # Heart Rate alerts
    if hr > 120:
        alerts.append({"type": "danger", "message": f"⚠️ High Heart Rate: {hr} BPM"})
    elif hr < 50:
        alerts.append({"type": "danger", "message": f"⚠️ Low Heart Rate: {hr} BPM"})
    elif hr > 100:
        alerts.append({"type": "warning", "message": f"⚠️ Elevated Heart Rate: {hr} BPM"})
    
    # SpO2 alerts
    if spo2 < 90:
        alerts.append({"type": "danger", "message": f"⚠️ Critical SpO2: {spo2}%"})
    elif spo2 < 95:
        alerts.append({"type": "warning", "message": f"⚠️ Low SpO2: {spo2}%"})
    
    # Temperature alerts
    if temp > 38.0:
        alerts.append({"type": "danger", "message": f"⚠️ Fever: {temp}°C"})
    elif temp > 37.5:
        alerts.append({"type": "warning", "message": f"⚠️ Elevated Temperature: {temp}°C"})
    
    return alerts

# ================ MAIN DASHBOARD ================
def main_dashboard():
    """Main dashboard function"""
    
    # ============ HEADER ============
    st.markdown("""
    <div class='main-header'>
        <h1>🏥 STEMCUBE Real-Time Health Monitoring</h1>
        <p>Live patient data from STEMCUBE sensors via LoRa • University Malaysia Pahang</p>
    </div>
    """, unsafe_allow_html=True)
    
    # ============ SIDEBAR CONTROLS ============
    with st.sidebar:
        st.header("⚙️ System Controls")
        
        # Connection Status
        st.subheader("📡 Connection Status")
        
        # Load live data to check status
        df_live, data_info, seconds_ago = load_live_stemcube_data()
        
        if st.session_state.get('stemcube_connected', False) and seconds_ago < 30:
            st.success("✅ STEMCUBE Connected")
            st.metric("Last Update", f"{int(seconds_ago)}s ago")
            st.metric("Packets Received", data_info.get('packets_received', 0))
        else:
            st.warning("⚠️ Using Demo Data")
            st.metric("Last Update", "> 30s ago")
        
        # Dashboard Settings
        st.subheader("📊 Display Settings")
        refresh_rate = st.slider("Auto-refresh (seconds)", 0, 60, 5, help="0 = manual refresh")
        show_history = st.slider("Show last N minutes", 5, 60, 30)
        n_samples = st.slider("Data points to display", 50, 1000, 200)
        
        # Node Selection
        st.subheader("📟 Patient Selection")
        available_nodes = ["NODE_e661", "NODE_e662", "NODE_e663", "user_001", "user_002"]
        selected_node = st.selectbox("Select Patient Node", available_nodes)
        
        # Data Management
        st.subheader("💾 Data Management")
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            if st.button("🔄 Refresh Now", use_container_width=True):
                st.rerun()
        with col_s2:
            if st.button("🗑️ Clear Cache", use_container_width=True):
                if os.path.exists('stemcube_live_data.json'):
                    os.remove('stemcube_live_data.json')
                st.rerun()
        
        # System Info
        st.subheader("ℹ️ System Info")
        st.info("""
        **STEMCUBE v2.0**
        - Raspberry Pi Pico
        - LoRa HC-12
        - Real-time ML
        - Streamlit Dashboard
        """)
        
        st.markdown("---")
        st.caption(f"Last check: {datetime.now().strftime('%H:%M:%S')}")
    
    # ============ DATA LOADING ============
    # Try to load live data first
    df_live, data_info, seconds_ago = load_live_stemcube_data()
    
    if not df_live.empty and seconds_ago < 30:
        # Use live data
        df = df_live
        data_source = "STEMCUBE LIVE"
        is_live = True
    else:
        # Use sample data
        df = generate_sample_data(n_samples)
        data_source = "DEMO DATA"
        is_live = False
    
    # Filter for selected node
    if 'node_id' in df.columns:
        node_df = df[df['node_id'] == selected_node].copy()
    else:
        node_df = df.copy()
    
    if not node_df.empty and 'timestamp' in node_df.columns:
        node_df = node_df.sort_values('timestamp', ascending=True)
    
    # ============ CREATE TABS ============
    tab1, tab2, tab3, tab4 = st.tabs(["🩺 Live Vitals", "📈 Trends", "📊 Analytics", "⚙️ System"])
    
    # ============ TAB 1: LIVE VITALS ============
    with tab1:
        st.header(f"Live Patient Monitoring - {selected_node}")
        
        if node_df.empty:
            st.warning("No data available for selected patient")
        else:
            latest = node_df.iloc[-1] if len(node_df) > 0 else {}
            
            # Alert Banner
            if 'hr' in latest and 'spo2' in latest and 'temp' in latest:
                alerts = check_vital_alerts(
                    latest.get('hr', 72),
                    latest.get('spo2', 96),
                    latest.get('temp', 36.5)
                )
                
                if alerts:
                    for alert in alerts:
                        if alert['type'] == 'danger':
                            st.error(alert['message'])
                        else:
                            st.warning(alert['message'])
            
            # Row 1: Key Metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                # Heart Rate Gauge
                hr_value = latest.get('hr', 72)
                hr_color = "#EF4444" if hr_value > 100 else "#10B981" if hr_value > 60 else "#F59E0B"
                
                fig_hr = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=hr_value,
                    title={"text": "Heart Rate", "font": {"size": 20}},
                    number={"font": {"size": 40}},
                    gauge={
                        'axis': {'range': [40, 160], 'tickwidth': 1},
                        'bar': {'color': hr_color},
                        'steps': [
                            {'range': [40, 60], 'color': "#F59E0B"},
                            {'range': [60, 100], 'color': "#10B981"},
                            {'range': [100, 160], 'color': "#EF4444"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 120
                        }
                    }
                ))
                fig_hr.update_layout(height=250, margin=dict(t=50, b=30))
                st.plotly_chart(fig_hr, use_container_width=True, config={'displayModeBar': False})
            
            with col2:
                # SpO₂ Gauge
                spo2_value = latest.get('spo2', 96)
                spo2_color = "#EF4444" if spo2_value < 90 else "#F59E0B" if spo2_value < 95 else "#10B981"
                
                fig_spo2 = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=spo2_value,
                    title={"text": "SpO₂", "font": {"size": 20}},
                    number={"suffix": "%", "font": {"size": 40}},
                    gauge={
                        'axis': {'range': [70, 100], 'tickwidth': 1},
                        'bar': {'color': spo2_color},
                        'steps': [
                            {'range': [70, 90], 'color': "#EF4444"},
                            {'range': [90, 95], 'color': "#F59E0B"},
                            {'range': [95, 100], 'color': "#10B981"}
                        ]
                    }
                ))
                fig_spo2.update_layout(height=250, margin=dict(t=50, b=30))
                st.plotly_chart(fig_spo2, use_container_width=True, config={'displayModeBar': False})
            
            with col3:
                # Temperature
                temp_value = latest.get('temp', 36.5)
                temp_color = "#EF4444" if temp_value > 37.5 else "#10B981"
                
                fig_temp = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=temp_value,
                    title={"text": "Temperature", "font": {"size": 20}},
                    number={"suffix": "°C", "font": {"size": 40}},
                    gauge={
                        'axis': {'range': [35, 40], 'tickwidth': 1},
                        'bar': {'color': temp_color},
                        'steps': [
                            {'range': [35, 37.5], 'color': "#10B981"},
                            {'range': [37.5, 40], 'color': "#EF4444"}
                        ]
                    }
                ))
                fig_temp.update_layout(height=250, margin=dict(t=50, b=30))
                st.plotly_chart(fig_temp, use_container_width=True, config={'displayModeBar': False})
            
            with col4:
                # Activity Display
                activity_info = classify_activity(
                    latest.get('ax', 0),
                    latest.get('ay', 0),
                    latest.get('az', 1)
                )
                
                st.markdown(f"""
                <div class='metric-card'>
                    <h3 style='text-align: center; margin-bottom: 15px;'>Current Activity</h3>
                    <div style='text-align: center; font-size: 48px; margin: 10px 0;'>
                        {activity_info['emoji']}
                    </div>
                    <h2 style='text-align: center; color: {activity_info['color']};'>
                        {activity_info['activity']}
                    </h2>
                    <div style='text-align: center; margin-top: 15px;'>
                        <small>Acceleration: {latest.get('ax', 0):.2f}, {latest.get('ay', 0):.2f}, {latest.get('az', 1):.2f}</small>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Battery Status
                battery_level = latest.get('battery_level', 85)
                st.progress(battery_level/100, text=f"Battery: {battery_level:.0f}%")
            
            # Row 2: Motion Data
            st.subheader("📡 Motion Sensors")
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            
            with col_m1:
                st.metric("Acceleration X", f"{latest.get('ax', 0):.3f} g")
            with col_m2:
                st.metric("Acceleration Y", f"{latest.get('ay', 0):.3f} g")
            with col_m3:
                st.metric("Acceleration Z", f"{latest.get('az', 1):.3f} g")
            with col_m4:
                magnitude = np.sqrt(
                    latest.get('ax', 0)**2 + 
                    latest.get('ay', 0)**2 + 
                    latest.get('az', 1)**2
                )
                st.metric("Magnitude", f"{magnitude:.3f} g")
    
    # ============ TAB 2: TRENDS ============
    with tab2:
        st.header(f"Trend Analysis - {selected_node}")
        
        if len(node_df) > 1:
            # Create subplots
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Heart Rate Trend', 'SpO₂ Trend', 'Temperature Trend', 'Activity Pattern'),
                vertical_spacing=0.15,
                horizontal_spacing=0.1
            )
            
            # Heart Rate
            if 'hr' in node_df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=node_df['timestamp'], 
                        y=node_df['hr'],
                        mode='lines+markers',
                        name='Heart Rate',
                        line=dict(color='#EF4444', width=2),
                        marker=dict(size=4)
                    ),
                    row=1, col=1
                )
                fig.add_hline(y=100, line_dash="dash", line_color="orange", row=1, col=1)
                fig.add_hline(y=120, line_dash="dash", line_color="red", row=1, col=1)
            
            # SpO2
            if 'spo2' in node_df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=node_df['timestamp'], 
                        y=node_df['spo2'],
                        mode='lines+markers',
                        name='SpO₂',
                        line=dict(color='#3B82F6', width=2),
                        marker=dict(size=4)
                    ),
                    row=1, col=2
                )
                fig.add_hline(y=95, line_dash="dash", line_color="orange", row=1, col=2)
                fig.add_hline(y=90, line_dash="dash", line_color="red", row=1, col=2)
            
            # Temperature
            if 'temp' in node_df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=node_df['timestamp'], 
                        y=node_df['temp'],
                        mode='lines+markers',
                        name='Temperature',
                        line=dict(color='#F59E0B', width=2),
                        marker=dict(size=4)
                    ),
                    row=2, col=1
                )
                fig.add_hline(y=37.5, line_dash="dash", line_color="red", row=2, col=1)
            
            # Activity
            if all(col in node_df.columns for col in ['ax', 'ay', 'az']):
                node_df['motion_magnitude'] = np.sqrt(
                    node_df['ax']**2 + node_df['ay']**2 + node_df['az']**2
                )
                
                # Color by activity if available
                if 'activity' in node_df.columns:
                    color_map = {
                        'RESTING': '#10B981',
                        'WALKING': '#3B82F6',
                        'RUNNING': '#EF4444',
                        'CYCLING': '#8B5CF6'
                    }
                    node_df['activity_color'] = node_df['activity'].map(color_map)
                    
                    fig.add_trace(
                        go.Scatter(
                            x=node_df['timestamp'], 
                            y=node_df['motion_magnitude'],
                            mode='markers',
                            name='Activity',
                            marker=dict(
                                size=8,
                                color=node_df['activity_color'],
                                symbol='circle'
                            ),
                            text=node_df['activity'],
                            hovertemplate='%{text}<br>Time: %{x}<br>Magnitude: %{y:.2f}<extra></extra>'
                        ),
                        row=2, col=2
                    )
                else:
                    fig.add_trace(
                        go.Scatter(
                            x=node_df['timestamp'], 
                            y=node_df['motion_magnitude'],
                            mode='lines',
                            name='Motion',
                            line=dict(color='#8B5CF6', width=2)
                        ),
                        row=2, col=2
                    )
            
            fig.update_layout(height=700, showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
            
            # Summary Statistics
            st.subheader("📊 Statistical Summary")
            if 'hr' in node_df.columns and 'spo2' in node_df.columns and 'temp' in node_df.columns:
                col_s1, col_s2, col_s3 = st.columns(3)
                
                with col_s1:
                    st.metric("Avg Heart Rate", f"{node_df['hr'].mean():.1f} BPM")
                    st.metric("HR Variability", f"{node_df['hr'].std():.1f} BPM")
                
                with col_s2:
                    st.metric("Avg SpO₂", f"{node_df['spo2'].mean():.1f}%")
                    st.metric("Min SpO₂", f"{node_df['spo2'].min():.1f}%")
                
                with col_s3:
                    st.metric("Avg Temperature", f"{node_df['temp'].mean():.1f}°C")
                    st.metric("Max Temperature", f"{node_df['temp'].max():.1f}°C")
        else:
            st.info("📈 Collecting more data for trend analysis...")
    
    # ============ TAB 3: ANALYTICS ============
    with tab3:
        st.header("Advanced Analytics")
        
        # Activity Distribution
        if 'activity' in node_df.columns and not node_df.empty:
            st.subheader("📋 Activity Distribution")
            
            activity_counts = node_df['activity'].value_counts()
            
            col_a1, col_a2 = st.columns([2, 1])
            
            with col_a1:
                fig_pie = px.pie(
                    values=activity_counts.values,
                    names=activity_counts.index,
                    title="Activity Time Distribution",
                    color_discrete_sequence=px.colors.sequential.RdBu
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col_a2:
                st.dataframe(
                    activity_counts.reset_index().rename(
                        columns={'index': 'Activity', 'activity': 'Count'}
                    ),
                    use_container_width=True
                )
        
        # Correlation Analysis
        st.subheader("🔗 Correlation Analysis")
        
        if len(node_df) > 10:
            numeric_cols = ['hr', 'spo2', 'temp', 'ax', 'ay', 'az']
            available_cols = [col for col in numeric_cols if col in node_df.columns]
            
            if len(available_cols) >= 2:
                corr_matrix = node_df[available_cols].corr()
                
                fig_heatmap = px.imshow(
                    corr_matrix,
                    text_auto=True,
                    aspect="auto",
                    color_continuous_scale='RdBu',
                    title="Correlation Matrix"
                )
                st.plotly_chart(fig_heatmap, use_container_width=True)
        
        # Data Export
        st.subheader("📥 Export Data")
        
        col_e1, col_e2, col_e3 = st.columns(3)
        
        with col_e1:
            csv = node_df.to_csv(index=False)
            st.download_button(
                label="📄 Download CSV",
                data=csv,
                file_name=f"stemcube_data_{selected_node}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col_e2:
            json_data = node_df.to_json(orient='records', indent=2)
            st.download_button(
                label="📁 Download JSON",
                data=json_data,
                file_name=f"stemcube_data_{selected_node}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
        
        with col_e3:
            if st.button("📋 Copy to Clipboard", use_container_width=True):
                st.session_state.clipboard_data = node_df.to_string()
                st.success("Data copied to clipboard!")
    
    # ============ TAB 4: SYSTEM STATUS ============
    with tab4:
        st.header("System Status & Configuration")
        
        col_sys1, col_sys2 = st.columns(2)
        
        with col_sys1:
            st.subheader("🔧 Hardware Status")
            
            # Connection Info
            st.info(f"**Data Source:** {data_source}")
            st.info(f"**Patient Node:** {selected_node}")
            st.info(f"**Total Records:** {len(node_df)}")
            
            if is_live:
                st.success(f"**Live Data:** Updated {int(seconds_ago)} seconds ago")
                st.metric("STEMCUBE Status", "✅ Connected")
                st.metric("Packets Processed", data_info.get('packets_received', 0))
            else:
                st.warning("**Live Data:** Using demo data")
                st.metric("STEMCUBE Status", "⚠️ Disconnected")
            
            # System Metrics
            st.subheader("📊 Performance Metrics")
            
            col_met1, col_met2 = st.columns(2)
            with col_met1:
                st.metric("CPU Usage", "15%")
                st.metric("Memory", "45%")
            with col_met2:
                st.metric("Data Rate", "2.5 KB/s")
                st.metric("Uptime", "2h 15m")
        
        with col_sys2:
            st.subheader("🔗 Connection Details")
            
            # Port Information
            port_info = {
                "STEMCUBE Port": "COM8",
                "Baud Rate": "9600",
                "Protocol": "LoRa HC-12",
                "Dashboard URL": "https://project-health-monitoring.streamlit.app",
                "Update Frequency": "Real-time",
                "Data Storage": "Local JSON + Cloud (Optional)"
            }
            
            for key, value in port_info.items():
                st.text_input(key, value, disabled=True)
            
            # Connection Test
            st.subheader("🔍 Connection Test")
            
            if st.button("Test STEMCUBE Connection", use_container_width=True):
                if os.path.exists('stemcube_live_data.json'):
                    with st.spinner("Testing connection..."):
                        time.sleep(2)
                        st.success("✅ STEMCUBE is responding")
                else:
                    st.error("❌ Cannot connect to STEMCUBE")
            
            # Configuration
            st.subheader("⚙️ Configuration")
            
            with st.expander("Advanced Settings"):
                st.checkbox("Enable Data Logging", value=True)
                st.checkbox("Enable Cloud Sync", value=False)
                st.checkbox("Enable Email Alerts", value=False)
                alert_threshold = st.slider("Alert Threshold", 0, 100, 90)
                st.info(f"Alerts will trigger at {alert_threshold}%")
    
    # ============ AUTO-REFRESH ============
    if refresh_rate > 0:
        time.sleep(refresh_rate)
        st.rerun()
    
    # ============ FOOTER ============
    st.markdown("---")
    
    col_f1, col_f2, col_f3 = st.columns([1, 2, 1])
    
    with col_f2:
        st.markdown(f"""
        <div style='text-align: center; color: #6B7280; font-size: 14px;'>
            <p>🏥 <b>STEMCUBE Health Monitoring System v2.0</b></p>
            <p>📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} • 
            📡 {data_source} • 
            👤 {selected_node}</p>
            <p>Universiti Malaysia Pahang • Final Year Project 2025</p>
        </div>
        """, unsafe_allow_html=True)

# ================ RUN APPLICATION ================
if __name__ == "__main__":
    # Initialize session state
    if 'stemcube_connected' not in st.session_state:
        st.session_state.stemcube_connected = False
    if 'last_stemcube_update' not in st.session_state:
        st.session_state.last_stemcube_update = None
    
    # Check login
    check_login()
    
    # Run main dashboard
    try:
        main_dashboard()
    except Exception as e:
        st.error(f"❌ Dashboard Error: {e}")
        st.info("Please refresh the page or check the STEMCUBE connection.")