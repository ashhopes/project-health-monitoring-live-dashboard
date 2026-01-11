# dashboard_cloud.py - FILE READER VERSION
"""
REAL-TIME DASHBOARD FOR STEMCUBE - READ FROM FILE
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import pytz
from collections import deque
import base64
import math

# ================ FILE READER (NO SERIAL NEEDED) ================
def read_from_file():
    """Read STEMCUBE data from file instead of COM8"""
    try:
        with open('stemcube_data.txt', 'r') as f:
            lines = f.readlines()
            if lines:
                # Get last line
                raw_line = lines[-1].strip()
                return parse_real_stemcube_data(raw_line), "✅ Reading from file"
    except:
        pass
    
    # Create sample data if file doesn't exist
    sample_data = "|1768143201|95|81|45.7|26.7|0.199|0.062|1.028|9.3|-1.8|4.3|walking|"
    return parse_real_stemcube_data(sample_data), "✅ Using sample data"

# ================ PARSER FUNCTION ================
def parse_real_stemcube_data(raw_line):
    """Parse STEMCUBE data format"""
    
    data = {
        'node_id': 'STEMCUBE_MASTER',
        'hr': 72,
        'spo2': 98,
        'temp': 36.5,
        'activity_level': 'RESTING',
        'movement': 0.0,
        'is_real': True,
        'parsed_success': False
    }
    
    try:
        cleaned = raw_line.strip('|')
        parts = cleaned.split('|')
        
        if len(parts) >= 12:
            # Parse data
            try:
                spo2_val = float(parts[1])
                if 70 <= spo2_val <= 100:
                    data['spo2'] = int(spo2_val)
            except:
                pass
            
            try:
                hr_val = float(parts[2])
                if 40 <= hr_val <= 200:
                    data['hr'] = int(hr_val)
            except:
                pass
            
            try:
                temp_val = float(parts[4])
                if 20 <= temp_val <= 45:
                    data['temp'] = round(temp_val, 1)
            except:
                pass
            
            try:
                activity_str = parts[11].strip().lower()
                if 'walking' in activity_str:
                    data['activity_level'] = 'WALKING'
                    data['movement'] = 2.5
                elif 'running' in activity_str:
                    data['activity_level'] = 'RUNNING'
                    data['movement'] = 4.0
                else:
                    data['activity_level'] = 'RESTING'
                    data['movement'] = 0.0
            except:
                pass
            
            data['parsed_success'] = True
            
    except Exception as e:
        print(f"Parse error: {e}")
    
    return data

# ================ PAGE CONFIG ================
st.set_page_config(
    page_title="STEMCUBE REAL-TIME MONITOR",
    page_icon="🏥",
    layout="wide"
)

# ================ SIMPLIFIED THEME ================
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #8B4513 0%, #556B2F 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 25px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ================ INITIALIZE ================
if 'hr_data' not in st.session_state:
    st.session_state.hr_data = deque(maxlen=50)
    st.session_state.spo2_data = deque(maxlen=50)
    st.session_state.temp_data = deque(maxlen=50)
    st.session_state.movement_data = deque(maxlen=50)
    st.session_state.timestamps = deque(maxlen=50)

# ================ MAIN DASHBOARD ================
def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🏥 STEMCUBE REAL-TIME MONITOR</h1>
        <p>📍 Universiti Malaysia Pahang • 🎓 Final Year Project 2025</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Read data
    parsed_data, status = read_from_file()
    
    if parsed_data['parsed_success']:
        # Add to buffers
        current_time = datetime.now()
        st.session_state.timestamps.append(current_time)
        st.session_state.hr_data.append(parsed_data['hr'])
        st.session_state.spo2_data.append(parsed_data['spo2'])
        st.session_state.temp_data.append(parsed_data['temp'])
        st.session_state.movement_data.append(parsed_data['movement'])
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("❤️ Heart Rate", f"{parsed_data['hr']} BPM")
        
        with col2:
            st.metric("🩸 SpO₂", f"{parsed_data['spo2']}%")
        
        with col3:
            st.metric("🌡️ Temperature", f"{parsed_data['temp']}°C")
        
        with col4:
            st.metric("🏃 Activity", parsed_data['activity_level'])
        
        # Status
        st.success(f"**{status}**")
        
        # Simple graph
        if len(st.session_state.timestamps) > 1:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=list(st.session_state.timestamps),
                y=list(st.session_state.hr_data),
                mode='lines+markers',
                name='Heart Rate'
            ))
            fig.update_layout(title="Heart Rate Trend", height=300)
            st.plotly_chart(fig, use_container_width=True)
        
        # Auto-refresh
        time.sleep(2)
        st.rerun()
    else:
        st.error("❌ Could not parse data")

if __name__ == "__main__":
    main()