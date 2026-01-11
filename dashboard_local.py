# dashboard_local.py - FOR LOCAL TESTING WITH UPLOADER.PY
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

# ... [Copy all the display functions from previous dashboard but remove simulation] ...

def load_health_data_local():
    """Load health data from Uploader.py JSON file"""
    json_file = 'health_data_streamlit.json'
    
    if os.path.exists(json_file):
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                return data
        except:
            pass
    
    # If no file or error, return empty
    return {
        'status': 'disconnected',
        'is_real_data': False,
        'data': {
            'hr': 72, 'spo2': 98, 'temp': 36.5,
            'activity_level': 'RESTING',
            'movement': 0.0,
            'node_id': 'NODE_e661',
            'timestamp': datetime.now().isoformat(),
            'hr_status': 'NORMAL',
            'spo2_status': 'NORMAL',
            'temp_status': 'NORMAL'
        }
    }

def main():
    # Initialize session state
    if 'history' not in st.session_state:
        st.session_state.history = deque(maxlen=100)
    
    # Sidebar
    with st.sidebar:
        st.title("⚙️ Local Dashboard")
        st.info("""
        **Local Testing Mode**
        
        This dashboard reads from health_data_streamlit.json
        created by Uploader.py
        """)
        
        # Check if JSON file exists
        if os.path.exists('health_data_streamlit.json'):
            file_time = os.path.getmtime('health_data_streamlit.json')
            file_age = time.time() - file_time
            if file_age < 10:  # Updated in last 10 seconds
                st.success(f"✅ Uploader.py active ({file_age:.1f}s ago)")
            else:
                st.warning(f"⚠️ Uploader.py stale ({file_age:.1f}s ago)")
        else:
            st.error("❌ No data file found")
        
        update_interval = st.slider("Refresh (s)", 1, 10, 2)
    
    # Load data
    health_data = load_health_data_local()
    
    if health_data:
        current_data = health_data.get('data', {})
        
        # Add timestamp
        current_data['timestamp'] = datetime.now()
        
        # Add to history
        st.session_state.history.append(current_data)
        
        # Display dashboard
        st.title("🏥 LOCAL HEALTH MONITORING")
        
        # Show metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Heart Rate", f"{current_data.get('hr', 0)} BPM", 
                     delta=None, delta_color="normal")
        with col2:
            st.metric("SpO2", f"{current_data.get('spo2', 0)}%", 
                     delta=None, delta_color="normal")
        with col3:
            st.metric("Temperature", f"{current_data.get('temp', 0):.1f}°C")
        with col4:
            st.metric("Activity", current_data.get('activity_level', 'RESTING'))
        
        # Show raw data
        with st.expander("📊 Raw Data"):
            st.json(health_data)
        
        # Show history
        if st.session_state.history:
            history_df = pd.DataFrame(list(st.session_state.history))
            st.line_chart(history_df[['hr', 'spo2']])
    
    # Auto-refresh
    time.sleep(update_interval)
    st.rerun()

if __name__ == "__main__":
    main()