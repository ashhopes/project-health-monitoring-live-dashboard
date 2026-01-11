import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import numpy as np
from collections import deque
import json
import os
import requests  # For API calls if needed

# ========== PAGE CONFIGURATION ==========
st.set_page_config(
    page_title="Real-Time Health Monitoring Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== CUSTOM CSS ==========
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* Header */
    .dashboard-header {
        background: linear-gradient(90deg, #2c3e50 0%, #4ca1af 100%);
        color: white;
        padding: 25px;
        border-radius: 15px;
        margin-bottom: 25px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Cards */
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border-left: 5px solid #3498db;
        margin-bottom: 20px;
    }
    
    .metric-card.critical {
        border-left: 5px solid #e74c3c;
        background: #ffeaea;
    }
    
    .metric-card.warning {
        border-left: 5px solid #f39c12;
        background: #fff4e6;
    }
    
    .metric-card.normal {
        border-left: 5px solid #2ecc71;
        background: #e8f8f1;
    }
    
    /* Values */
    .metric-value {
        font-size: 32px;
        font-weight: bold;
        color: #2c3e50;
    }
    
    .metric-label {
        font-size: 14px;
        color: #7f8c8d;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Status badges */
    .status-badge {
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        display: inline-block;
    }
    
    .status-normal {
        background: #d5f4e6;
        color: #27ae60;
    }
    
    .status-warning {
        background: #fdebd0;
        color: #f39c12;
    }
    
    .status-critical {
        background: #fadbd8;
        color: #e74c3c;
    }
    
    /* Data source indicator */
    .data-source-real {
        background: #d5f4e6;
        color: #27ae60;
        padding: 5px 10px;
        border-radius: 10px;
        font-size: 12px;
        font-weight: bold;
    }
    
    .data-source-sim {
        background: #fdebd0;
        color: #f39c12;
        padding: 5px 10px;
        border-radius: 10px;
        font-size: 12px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ========== DATA LOADING FUNCTIONS ==========
def load_health_data():
    """Load health data - for Streamlit Cloud, we'll use simulated data or API"""
    # On Streamlit Cloud, we can't access local files directly
    # So we'll use simulation mode or fetch from an API
    
    try:
        # OPTION 1: Try to load from a URL (if you have an API)
        # api_url = "https://your-api.com/health-data"
        # response = requests.get(api_url, timeout=5)
        # if response.status_code == 200:
        #     return response.json()
        
        # OPTION 2: Use built-in simulation for Streamlit Cloud
        current_time = datetime.now()
        
        # Generate simulation data for cloud
        simulation_data = generate_simulation_data()
        
        return {
            'status': 'connected',
            'last_update': current_time.isoformat(),
            'is_real_data': False,  # On cloud, it's always simulation
            'data_source': 'STREAMLIT_CLOUD_SIMULATION',
            'parsed_success': True,
            'data': simulation_data
        }
        
    except Exception as e:
        st.error(f"Error loading data: {e}")
        # Fallback to basic simulation
        return {
            'status': 'disconnected',
            'last_update': datetime.now().isoformat(),
            'is_real_data': False,
            'data_source': 'FALLBACK_SIMULATION',
            'parsed_success': False,
            'data': {
                'hr': 72, 'spo2': 98, 'temp': 36.5,
                'activity_level': 'RESTING',
                'movement': 0.0,
                'node_id': 'NODE_e661',
                'timestamp': datetime.now().isoformat(),
                'malaysia_time': datetime.now().strftime('%H:%M:%S'),
                'hr_status': 'NORMAL',
                'spo2_status': 'NORMAL',
                'temp_status': 'NORMAL',
                'activity': 0.0
            }
        }

def generate_simulation_data():
    """Generate realistic simulation data for Streamlit Cloud"""
    current_time = datetime.now()
    
    # Cycle through different activities
    activity_cycle = ['RESTING', 'WALKING', 'RUNNING']
    cycle_index = (int(time.time()) // 10) % 3  # Change every 10 seconds
    
    activity = activity_cycle[cycle_index]
    
    # Base values for each activity
    if activity == 'RESTING':
        hr = 65 + np.random.randint(-5, 6)
        spo2 = 97 + np.random.randint(-1, 2)
        temp = 36.5 + np.random.uniform(-0.2, 0.2)
        movement = np.random.uniform(0.0, 0.3)
        activity_score = np.random.uniform(0.0, 1.0)
    elif activity == 'WALKING':
        hr = 85 + np.random.randint(-10, 11)
        spo2 = 96 + np.random.randint(-2, 1)
        temp = 36.8 + np.random.uniform(-0.3, 0.3)
        movement = np.random.uniform(0.5, 1.5)
        activity_score = np.random.uniform(1.5, 3.0)
    else:  # RUNNING
        hr = 115 + np.random.randint(-15, 16)
        spo2 = 94 + np.random.randint(-3, 1)
        temp = 37.2 + np.random.uniform(-0.4, 0.4)
        movement = np.random.uniform(1.5, 3.0)
        activity_score = np.random.uniform(3.0, 5.0)
    
    # Add status indicators
    hr_status = "NORMAL"
    if hr > 120:
        hr_status = "CRITICAL"
    elif hr > 100:
        hr_status = "WARNING"
        
    spo2_status = "NORMAL"
    if spo2 < 90:
        spo2_status = "CRITICAL"
    elif spo2 < 95:
        spo2_status = "WARNING"
        
    temp_status = "NORMAL"
    if temp > 38.0:
        temp_status = "CRITICAL"
    elif temp > 37.0:
        temp_status = "WARNING"
    
    return {
        'hr': hr,
        'spo2': spo2,
        'temp': temp,
        'activity_level': activity,
        'movement': movement,
        'activity': activity_score,
        'node_id': 'NODE_e661',
        'timestamp': current_time.isoformat(),
        'malaysia_time': current_time.strftime('%H:%M:%S'),
        'hr_status': hr_status,
        'spo2_status': spo2_status,
        'temp_status': temp_status,
        'confidence': np.random.uniform(0.85, 0.99),
        'battery': 85,
        'rssi': -65
    }

# ========== DASHBOARD COMPONENTS ==========
def display_header(health_data):
    """Display dashboard header with data source info"""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        data_source = health_data.get('data_source', 'UNKNOWN')
        is_real = health_data.get('is_real_data', False)
        
        source_badge = "🔴 REAL DATA" if is_real else "🟡 STREAMLIT CLOUD SIMULATION"
        source_color = "#27ae60" if is_real else "#f39c12"
        
        st.markdown(f"""
        <div class="dashboard-header">
            <h1 style="margin:0; font-size: 2.5rem;">🏥 HEALTH MONITORING DASHBOARD</h1>
            <p style="margin:10px 0 0 0; font-size: 1.2rem; opacity: 0.9;">
                Cloud-Based Monitoring System
            </p>
            <div style="margin-top: 15px; display: flex; justify-content: center; align-items: center; gap: 10px;">
                <span style="background: {source_color}; color: white; padding: 5px 15px; border-radius: 20px; font-weight: bold;">
                    {source_badge}
                </span>
                <span style="color: rgba(255,255,255,0.8);">{data_source}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

def display_metrics(current_data, history_df, is_real_data):
    """Display health metrics"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        hr_status = current_data.get('hr_status', 'NORMAL')
        hr_status_class = "critical" if hr_status == "CRITICAL" else "warning" if hr_status == "WARNING" else "normal"
        st.markdown(f"""
        <div class="metric-card {hr_status_class}">
            <div class="metric-label">HEART RATE</div>
            <div class="metric-value">{current_data.get('hr', 72):.0f} BPM</div>
            <div class="status-badge status-{hr_status.lower()}">{hr_status}</div>
            <div style="margin-top: 10px; font-size: 12px; color: #7f8c8d;">
                📊 Avg: {history_df['hr'].mean():.0f} BPM
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        spo2_status = current_data.get('spo2_status', 'NORMAL')
        spo2_status_class = "critical" if spo2_status == "CRITICAL" else "warning" if spo2_status == "WARNING" else "normal"
        st.markdown(f"""
        <div class="metric-card {spo2_status_class}">
            <div class="metric-label">OXYGEN SATURATION</div>
            <div class="metric-value">{current_data.get('spo2', 98):.0f} %</div>
            <div class="status-badge status-{spo2_status.lower()}">{spo2_status}</div>
            <div style="margin-top: 10px; font-size: 12px; color: #7f8c8d;">
                📊 Avg: {history_df['spo2'].mean():.0f} %
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        temp_status = current_data.get('temp_status', 'NORMAL')
        temp_status_class = "critical" if temp_status == "CRITICAL" else "warning" if temp_status == "WARNING" else "normal"
        st.markdown(f"""
        <div class="metric-card {temp_status_class}">
            <div class="metric-label">BODY TEMPERATURE</div>
            <div class="metric-value">{current_data.get('temp', 36.5):.1f} °C</div>
            <div class="status-badge status-{temp_status.lower()}">{temp_status}</div>
            <div style="margin-top: 10px; font-size: 12px; color: #7f8c8d;">
                📊 Avg: {history_df['temp'].mean():.1f} °C
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        activity_level = current_data.get('activity_level', 'RESTING')
        activity_color = "#2ecc71" if activity_level == "RESTING" else "#f39c12" if activity_level == "WALKING" else "#e74c3c"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">ACTIVITY LEVEL</div>
            <div class="metric-value" style="color: {activity_color};">{activity_level}</div>
            <div style="margin-top: 10px; font-size: 14px; color: #7f8c8d;">
                Intensity: {current_data.get('activity', 0.0):.2f}
            </div>
            <div style="font-size: 12px; margin-top: 5px; color: #7f8c8d;">
                Movement: {current_data.get('movement', 0.0):.3f} g
            </div>
            {f'<div style="font-size: 12px; margin-top: 5px; color: #9b59b6;">🎯 ML Confidence: {current_data.get("confidence", 0.95):.2f}</div>' if 'confidence' in current_data else ''}
        </div>
        """, unsafe_allow_html=True)

def display_charts(history_df):
    """Display charts"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Vital Signs Trend")
        
        if len(history_df) > 1:
            fig = go.Figure()
            
            # Heart Rate
            fig.add_trace(go.Scatter(
                x=history_df['timestamp'],
                y=history_df['hr'],
                name='Heart Rate (BPM)',
                line=dict(color='#e74c3c', width=2),
                yaxis='y1'
            ))
            
            # SpO2
            fig.add_trace(go.Scatter(
                x=history_df['timestamp'],
                y=history_df['spo2'],
                name='SpO2 (%)',
                line=dict(color='#3498db', width=2),
                yaxis='y2'
            ))
            
            fig.update_layout(
                yaxis=dict(title='Heart Rate (BPM)', titlefont=dict(color='#e74c3c')),
                yaxis2=dict(title='SpO2 (%)', titlefont=dict(color='#3498db'),
                           overlaying='y', side='right'),
                hovermode='x unified',
                height=300,
                margin=dict(l=20, r=50, t=30, b=20),
                plot_bgcolor='rgba(240, 240, 240, 0.1)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🌡️ Temperature & Activity")
        
        if len(history_df) > 1:
            fig = go.Figure()
            
            # Temperature
            fig.add_trace(go.Scatter(
                x=history_df['timestamp'],
                y=history_df['temp'],
                name='Temperature (°C)',
                line=dict(color='#e67e22', width=2),
                yaxis='y1'
            ))
            
            # Activity
            fig.add_trace(go.Scatter(
                x=history_df['timestamp'],
                y=history_df['activity'],
                name='Activity Level',
                line=dict(color='#9b59b6', width=2),
                yaxis='y2',
                fill='tozeroy',
                fillcolor='rgba(155, 89, 182, 0.1)'
            ))
            
            fig.update_layout(
                yaxis=dict(title='Temperature (°C)', titlefont=dict(color='#e67e22')),
                yaxis2=dict(title='Activity Level', titlefont=dict(color='#9b59b6'),
                           overlaying='y', side='right'),
                hovermode='x unified',
                height=300,
                margin=dict(l=20, r=50, t=30, b=20),
                plot_bgcolor='rgba(240, 240, 240, 0.1)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            
            st.plotly_chart(fig, use_container_width=True)

def display_node_info(health_data, current_data, history_df):
    """Display node information and alerts"""
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("📱 Device Information")
        
        last_update = health_data.get('last_update', datetime.now().isoformat())
        try:
            last_update_time = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
            last_update_str = last_update_time.strftime('%H:%M:%S')
        except:
            last_update_str = "Unknown"
        
        status_color = "#27ae60" if health_data.get('is_real_data', False) else "#f39c12"
        status_text = "● REAL DATA" if health_data.get('is_real_data', False) else "● STREAMLIT CLOUD"
        
        st.markdown(f"""
        <div class="metric-card">
            <div style="display: flex; align-items: center; margin-bottom: 15px;">
                <div style="font-size: 24px; margin-right: 10px;">📱</div>
                <div>
                    <div style="font-weight: bold; font-size: 18px;">{current_data.get('node_id', 'NODE_e661')}</div>
                    <div style="color: #7f8c8d; font-size: 14px;">Virtual Wearable Monitor</div>
                </div>
            </div>
            
            <div style="margin-top: 15px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span>Data Points:</span>
                    <span style="font-weight: bold;">{len(history_df)}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span>Last Update:</span>
                    <span style="font-weight: bold;">{last_update_str}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span>Source:</span>
                    <span style="color: {status_color}; font-weight: bold;">{status_text}</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span>Environment:</span>
                    <span style="color: #3498db; font-weight: bold;">☁️ Streamlit Cloud</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.subheader("⚠️ Alerts & Notifications")
        
        alerts = []
        
        hr_status = current_data.get('hr_status', 'NORMAL')
        if hr_status == "CRITICAL":
            alerts.append(("🚨 Critical Heart Rate", f"Heart rate is critically high at {current_data.get('hr', 72):.0f} BPM", "critical"))
        elif hr_status == "WARNING":
            alerts.append(("⚠️ Elevated Heart Rate", f"Heart rate is elevated at {current_data.get('hr', 72):.0f} BPM", "warning"))
            
        spo2_status = current_data.get('spo2_status', 'NORMAL')
        if spo2_status == "CRITICAL":
            alerts.append(("🚨 Low Oxygen", f"SpO2 is critically low at {current_data.get('spo2', 98):.0f}%", "critical"))
        elif spo2_status == "WARNING":
            alerts.append(("⚠️ Low Oxygen", f"SpO2 is low at {current_data.get('spo2', 98):.0f}%", "warning"))
            
        temp_status = current_data.get('temp_status', 'NORMAL')
        if temp_status == "CRITICAL":
            alerts.append(("🚨 High Temperature", f"Temperature is critically high at {current_data.get('temp', 36.5):.1f}°C", "critical"))
        elif temp_status == "WARNING":
            alerts.append(("⚠️ Elevated Temperature", f"Temperature is elevated at {current_data.get('temp', 36.5):.1f}°C", "warning"))
        
        if alerts:
            for alert_title, alert_msg, alert_type in alerts:
                alert_color = "#e74c3c" if alert_type == "critical" else "#f39c12"
                st.markdown(f"""
                <div style="background: {'#ffeaea' if alert_type == 'critical' else '#fff4e6'}; 
                          padding: 15px; border-radius: 10px; border-left: 5px solid {alert_color};
                          margin-bottom: 10px;">
                    <div style="font-weight: bold; color: {alert_color}; margin-bottom: 5px;">
                        {alert_title}
                    </div>
                    <div style="color: #2c3e50;">
                        {alert_msg}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background: #e8f8f1; padding: 30px; border-radius: 10px; text-align: center; border: 2px dashed #2ecc71;">
                <div style="font-size: 48px; color: #27ae60; margin-bottom: 10px;">✓</div>
                <div style="font-size: 18px; color: #27ae60; font-weight: bold;">All Systems Normal</div>
                <div style="color: #7f8c8d; margin-top: 10px;">No critical alerts detected</div>
            </div>
            """, unsafe_allow_html=True)

# ========== MAIN DASHBOARD ==========
def main():
    # Initialize session state
    if 'history' not in st.session_state:
        st.session_state.history = deque(maxlen=100)  # Store last 100 readings
    
    # Sidebar for configuration
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 30px;">
            <div style="font-size: 24px; font-weight: bold; color: #2c3e50;">⚙️ SETTINGS</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Data source info
        st.subheader("Environment")
        st.info("""
        **Streamlit Cloud Environment**
        
        This dashboard is running on Streamlit Cloud servers.
        For real COM8 data, run locally with Uploader.py.
        """)
        
        st.divider()
        
        # Dashboard settings
        st.subheader("Display Settings")
        update_interval = st.slider("Update Interval (seconds)", 1, 10, 2, 
                                   help="How often to refresh data")
        
        st.divider()
        
        # Manual refresh
        st.subheader("Controls")
        if st.button("🔄 Refresh Now", use_container_width=True):
            st.rerun()
        
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.history.clear()
            st.success("History cleared!")
            st.rerun()
        
        if st.button("🔄 Reset Simulation", use_container_width=True):
            st.session_state.history.clear()
            st.rerun()
        
        st.divider()
        
        # System info
        st.subheader("System Status")
        
        # Load current data to show status
        health_data = load_health_data()
        if health_data:
            current_data = health_data.get('data', {})
            st.metric("Data Points", len(st.session_state.history))
            st.metric("Heart Rate", f"{current_data.get('hr', 0)} BPM")
            st.metric("SpO2", f"{current_data.get('spo2', 0)}%")
        else:
            st.warning("No data available")
    
    # Load health data
    health_data = load_health_data()
    
    if health_data:
        current_data = health_data.get('data', {})
        
        # Convert timestamp string to datetime
        if 'timestamp' in current_data:
            try:
                timestamp_str = current_data['timestamp']
                if timestamp_str.endswith('Z'):
                    timestamp_str = timestamp_str[:-1] + '+00:00'
                current_data['timestamp'] = datetime.fromisoformat(timestamp_str)
            except:
                current_data['timestamp'] = datetime.now()
        else:
            current_data['timestamp'] = datetime.now()
        
        # Add to history
        st.session_state.history.append(current_data)
        
        # Display header with data source info
        display_header(health_data)
        
        # Convert history to DataFrame for charts
        history_df = pd.DataFrame(list(st.session_state.history))
        
        # Convert timestamp strings to datetime
        if 'timestamp' in history_df.columns:
            history_df['timestamp'] = pd.to_datetime(history_df['timestamp'])
        
        # Display metrics
        display_metrics(current_data, history_df, health_data.get('is_real_data', False))
        
        # Display charts
        display_charts(history_df)
        
        # Display node info and alerts
        display_node_info(health_data, current_data, history_df)
        
        # Show info about cloud environment
        st.info("""
        **ℹ️ Streamlit Cloud Information**
        
        This dashboard is running on Streamlit Cloud. For real-time COM8 data from your STEMCUBE:
        1. Run **Uploader.py** on your local computer
        2. Run the **local version** of this dashboard
        3. The cloud version shows simulation data for demonstration
        """)
    
    else:
        st.error("❌ Failed to load health data")
    
    # Auto-refresh
    time.sleep(update_interval)
    st.rerun()

if __name__ == "__main__":
    main()