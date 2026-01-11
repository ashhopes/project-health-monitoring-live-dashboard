import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import numpy as np
from collections import deque
import serial
import threading
import queue
import re

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
</style>
""", unsafe_allow_html=True)

# ========== DATA PARSING FUNCTIONS ==========
def parse_health_data(data_string):
    """Parse health data from string format"""
    try:
        # Parse format: HR:58|SpO2:71|TEMP:9.1|ACT:8.826|MOV:-0.087|NODE:NODE_e661
        data = {}
        
        # Extract using regex
        hr_match = re.search(r'HR:([\d\.]+)', data_string)
        spo2_match = re.search(r'SpO2:([\d\.]+)', data_string)
        temp_match = re.search(r'TEMP:([\d\.]+)', data_string)
        act_match = re.search(r'ACT:([\d\.]+)', data_string)
        mov_match = re.search(r'MOV:([-\d\.]+)', data_string)
        node_match = re.search(r'NODE:(\w+)', data_string)
        
        if hr_match:
            data['hr'] = float(hr_match.group(1))
            data['hr'] = max(30, min(data['hr'], 200))  # Clamp to reasonable range
        else:
            data['hr'] = 72.0
            
        if spo2_match:
            data['spo2'] = float(spo2_match.group(1))
            data['spo2'] = max(70, min(data['spo2'], 100))
        else:
            data['spo2'] = 98.0
            
        if temp_match:
            data['temp'] = float(temp_match.group(1))
            data['temp'] = max(0, min(data['temp'], 50))
        else:
            data['temp'] = 25.0
            
        if act_match:
            data['activity'] = float(act_match.group(1))
        else:
            data['activity'] = 0.0
            
        if mov_match:
            data['movement'] = float(mov_match.group(1))
        else:
            data['movement'] = 0.0
            
        if node_match:
            data['node_id'] = node_match.group(1)
        else:
            data['node_id'] = "UNKNOWN"
            
        data['timestamp'] = datetime.now()
        
        # Determine activity level
        if data['activity'] < 1.0:
            data['activity_level'] = "RESTING"
        elif data['activity'] < 2.0:
            data['activity_level'] = "WALKING"
        else:
            data['activity_level'] = "RUNNING"
            
        # Determine status
        data['hr_status'] = "NORMAL"
        if data['hr'] > 120:
            data['hr_status'] = "CRITICAL"
        elif data['hr'] > 100:
            data['hr_status'] = "WARNING"
            
        data['spo2_status'] = "NORMAL"
        if data['spo2'] < 90:
            data['spo2_status'] = "CRITICAL"
        elif data['spo2'] < 95:
            data['spo2_status'] = "WARNING"
            
        data['temp_status'] = "NORMAL"
        if data['temp'] > 38.0:
            data['temp_status'] = "CRITICAL"
        elif data['temp'] > 37.0:
            data['temp_status'] = "WARNING"
            
        return data
        
    except Exception as e:
        print(f"Error parsing data: {e}")
        return None

# ========== SERIAL READER ==========
class SerialReader:
    def __init__(self, port='COM8', baudrate=9600):
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.data_queue = queue.Queue()
        self.running = False
        self.thread = None
        
    def start(self):
        """Start serial reading thread"""
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1
            )
            self.running = True
            self.thread = threading.Thread(target=self._read_serial)
            self.thread.daemon = True
            self.thread.start()
            st.success(f"Connected to {self.port} at {self.baudrate} baud")
            return True
        except Exception as e:
            st.error(f"Failed to connect to {self.port}: {e}")
            return False
    
    def _read_serial(self):
        """Read data from serial port"""
        while self.running:
            try:
                if self.serial_conn and self.serial_conn.in_waiting > 0:
                    line = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                    if line and "NODE:" in line:
                        self.data_queue.put(line)
            except Exception as e:
                print(f"Serial read error: {e}")
                time.sleep(0.1)
    
    def get_data(self):
        """Get data from queue"""
        if not self.data_queue.empty():
            return self.data_queue.get()
        return None
    
    def stop(self):
        """Stop serial reading"""
        self.running = False
        if self.serial_conn:
            self.serial_conn.close()

# ========== DASHBOARD COMPONENTS ==========
def display_header():
    """Display dashboard header"""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class="dashboard-header">
            <h1 style="margin:0; font-size: 2.5rem;">🏥 REAL-TIME HEALTH MONITORING</h1>
            <p style="margin:10px 0 0 0; font-size: 1.2rem; opacity: 0.9;">
                Wireless Multi-Node Patient Monitoring System
            </p>
        </div>
        """, unsafe_allow_html=True)

def display_metrics(current_data, history_df):
    """Display health metrics"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        hr_status_class = "critical" if current_data['hr_status'] == "CRITICAL" else "warning" if current_data['hr_status'] == "WARNING" else "normal"
        st.markdown(f"""
        <div class="metric-card {hr_status_class}">
            <div class="metric-label">HEART RATE</div>
            <div class="metric-value">{current_data['hr']:.0f} BPM</div>
            <div class="status-badge status-{current_data['hr_status'].lower()}">{current_data['hr_status']}</div>
            <div style="margin-top: 10px; font-size: 12px;">
                📊 Avg: {history_df['hr'].mean():.0f} BPM
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        spo2_status_class = "critical" if current_data['spo2_status'] == "CRITICAL" else "warning" if current_data['spo2_status'] == "WARNING" else "normal"
        st.markdown(f"""
        <div class="metric-card {spo2_status_class}">
            <div class="metric-label">OXYGEN SATURATION</div>
            <div class="metric-value">{current_data['spo2']:.0f} %</div>
            <div class="status-badge status-{current_data['spo2_status'].lower()}">{current_data['spo2_status']}</div>
            <div style="margin-top: 10px; font-size: 12px;">
                📊 Avg: {history_df['spo2'].mean():.0f} %
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        temp_status_class = "critical" if current_data['temp_status'] == "CRITICAL" else "warning" if current_data['temp_status'] == "WARNING" else "normal"
        st.markdown(f"""
        <div class="metric-card {temp_status_class}">
            <div class="metric-label">BODY TEMPERATURE</div>
            <div class="metric-value">{current_data['temp']:.1f} °C</div>
            <div class="status-badge status-{current_data['temp_status'].lower()}">{current_data['temp_status']}</div>
            <div style="margin-top: 10px; font-size: 12px;">
                📊 Avg: {history_df['temp'].mean():.1f} °C
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        activity_color = "#2ecc71" if current_data['activity_level'] == "RESTING" else "#f39c12" if current_data['activity_level'] == "WALKING" else "#e74c3c"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">ACTIVITY LEVEL</div>
            <div class="metric-value" style="color: {activity_color};">{current_data['activity_level']}</div>
            <div style="margin-top: 10px; font-size: 14px; color: #7f8c8d;">
                Intensity: {current_data['activity']:.2f}
            </div>
            <div style="font-size: 12px; margin-top: 5px;">
                Movement: {current_data['movement']:.3f} g
            </div>
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

def display_node_info(current_data, history_df):
    """Display node information and alerts"""
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("📱 Device Information")
        
        st.markdown(f"""
        <div class="metric-card">
            <div style="display: flex; align-items: center; margin-bottom: 15px;">
                <div style="font-size: 24px; margin-right: 10px;">📱</div>
                <div>
                    <div style="font-weight: bold; font-size: 18px;">{current_data['node_id']}</div>
                    <div style="color: #7f8c8d; font-size: 14px;">Wearable Health Monitor</div>
                </div>
            </div>
            
            <div style="margin-top: 15px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span>Data Points:</span>
                    <span style="font-weight: bold;">{len(history_df)}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span>Last Update:</span>
                    <span style="font-weight: bold;">{current_data['timestamp'].strftime('%H:%M:%S')}</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span>Connection:</span>
                    <span style="color: #27ae60; font-weight: bold;">● LIVE</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.subheader("⚠️ Alerts & Notifications")
        
        alerts = []
        
        if current_data['hr_status'] == "CRITICAL":
            alerts.append(("🚨 Critical Heart Rate", f"Heart rate is critically high at {current_data['hr']:.0f} BPM", "critical"))
        elif current_data['hr_status'] == "WARNING":
            alerts.append(("⚠️ Elevated Heart Rate", f"Heart rate is elevated at {current_data['hr']:.0f} BPM", "warning"))
            
        if current_data['spo2_status'] == "CRITICAL":
            alerts.append(("🚨 Low Oxygen", f"SpO2 is critically low at {current_data['spo2']:.0f}%", "critical"))
        elif current_data['spo2_status'] == "WARNING":
            alerts.append(("⚠️ Low Oxygen", f"SpO2 is low at {current_data['spo2']:.0f}%", "warning"))
            
        if current_data['temp_status'] == "CRITICAL":
            alerts.append(("🚨 High Temperature", f"Temperature is critically high at {current_data['temp']:.1f}°C", "critical"))
        elif current_data['temp_status'] == "WARNING":
            alerts.append(("⚠️ Elevated Temperature", f"Temperature is elevated at {current_data['temp']:.1f}°C", "warning"))
        
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
    if 'serial_reader' not in st.session_state:
        st.session_state.serial_reader = None
    if 'current_data' not in st.session_state:
        st.session_state.current_data = {
            'hr': 72.0, 'spo2': 98.0, 'temp': 25.0,
            'activity': 0.0, 'movement': 0.0,
            'node_id': 'NODE_e661',
            'timestamp': datetime.now(),
            'hr_status': 'NORMAL',
            'spo2_status': 'NORMAL',
            'temp_status': 'NORMAL',
            'activity_level': 'RESTING'
        }
    
    # Display header
    display_header()
    
    # Sidebar for configuration
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 30px;">
            <div style="font-size: 24px; font-weight: bold; color: #2c3e50;">⚙️ SETTINGS</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Serial port configuration
        st.subheader("Serial Connection")
        port = st.selectbox("COM Port", ["COM8", "COM3", "COM4", "COM5", "COM6", "COM7"])
        baudrate = st.selectbox("Baud Rate", [9600, 115200, 57600, 38400, 19200])
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔗 Connect", use_container_width=True):
                if st.session_state.serial_reader:
                    st.session_state.serial_reader.stop()
                st.session_state.serial_reader = SerialReader(port=port, baudrate=baudrate)
                if st.session_state.serial_reader.start():
                    st.rerun()
        
        with col2:
            if st.button("🔴 Disconnect", use_container_width=True):
                if st.session_state.serial_reader:
                    st.session_state.serial_reader.stop()
                    st.session_state.serial_reader = None
                    st.success("Disconnected")
                    st.rerun()
        
        st.divider()
        
        # Dashboard settings
        st.subheader("Display Settings")
        history_length = st.slider("History Length (seconds)", 30, 300, 60)
        update_interval = st.slider("Update Interval (ms)", 100, 2000, 500)
        
        st.divider()
        
        # Simulated data option
        st.subheader("Test Mode")
        use_simulated = st.checkbox("Use Simulated Data", value=False)
        
        if use_simulated:
            st.info("Using simulated data for testing")
        
        st.divider()
        
        # System info
        st.subheader("System Status")
        st.metric("Data Points", len(st.session_state.history))
        if st.session_state.serial_reader and st.session_state.serial_reader.running:
            st.success("Connected to serial")
        else:
            st.warning("Not connected to serial")
    
    # Main content area
    if use_simulated:
        # Generate simulated data
        import random
        simulated_data = {
            'hr': 70 + random.randint(-10, 20),
            'spo2': 97 + random.randint(-2, 2),
            'temp': 36.5 + random.uniform(-0.5, 0.5),
            'activity': random.uniform(0, 3),
            'movement': random.uniform(-0.5, 0.5),
            'node_id': 'NODE_e661',
            'timestamp': datetime.now()
        }
        parsed_data = parse_health_data(
            f"HR:{simulated_data['hr']}|SpO2:{simulated_data['spo2']}|TEMP:{simulated_data['temp']}|"
            f"ACT:{simulated_data['activity']}|MOV:{simulated_data['movement']}|NODE:{simulated_data['node_id']}"
        )
        if parsed_data:
            st.session_state.current_data = parsed_data
            st.session_state.history.append(parsed_data)
    
    elif st.session_state.serial_reader and st.session_state.serial_reader.running:
        # Read real data from serial
        raw_data = st.session_state.serial_reader.get_data()
        if raw_data:
            parsed_data = parse_health_data(raw_data)
            if parsed_data:
                st.session_state.current_data = parsed_data
                st.session_state.history.append(parsed_data)
    
    # Convert history to DataFrame for charts
    history_df = pd.DataFrame(list(st.session_state.history))
    
    # Display metrics
    display_metrics(st.session_state.current_data, history_df)
    
    # Display charts
    display_charts(history_df)
    
    # Display node info and alerts
    display_node_info(st.session_state.current_data, history_df)
    
    # Auto-refresh
    time.sleep(update_interval / 1000.0)
    st.rerun()

if __name__ == "__main__":
    main()