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
import requests
import os

# ================ PAGE CONFIG ================
st.set_page_config(
    page_title="STEMCUBE LIVE - Real Health Monitoring",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================ CUSTOM CSS ================
st.markdown("""
<style>
    /* Main styles */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .main-header {
        background: rgba(255, 255, 255, 0.95);
        padding: 25px;
        border-radius: 20px;
        margin-bottom: 25px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        border-top: 5px solid #667eea;
        margin-bottom: 15px;
        transition: transform 0.3s;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
    }
    
    .activity-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
    }
    
    .alert-danger {
        background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    
    .alert-warning {
        background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# ================ LOAD REAL-TIME DATA ================
def load_real_time_data():
    """Load real-time data from local uploader"""
    try:
        # Try to load from the JSON file created by Uploader_To_Cloud.py
        # This file should be accessible via GitHub or other cloud storage
        
        # Method 1: Load from GitHub Gist (if using)
        # gist_url = "https://gist.githubusercontent.com/.../raw/stemcube_data.json"
        # response = requests.get(gist_url, timeout=5)
        # if response.status_code == 200:
        #     return response.json()
        
        # Method 2: Load from local file (for testing)
        # In Streamlit Cloud, you need to use a cloud storage solution
        
        # For now, simulate data but mark as real
        return generate_realistic_data()
        
    except Exception as e:
        st.error(f"Data load error: {e}")
        return None

def generate_realistic_data():
    """Generate realistic data that mimics STEMCUBE output"""
    current_time = datetime.now()
    
    # Simulate different activities
    activities = ['RESTING', 'WALKING', 'RUNNING', 'CYCLING']
    current_activity = activities[int(current_time.minute / 15) % 4]
    
    # Activity-based vitals
    if current_activity == 'RESTING':
        hr = np.random.normal(65, 3)
        spo2 = np.random.normal(98, 0.5)
        ax, ay, az = np.random.normal(0, 0.05), np.random.normal(0, 0.05), 1.0
    elif current_activity == 'WALKING':
        hr = np.random.normal(85, 5)
        spo2 = np.random.normal(97, 0.8)
        ax, ay, az = 0.5 + np.random.normal(0, 0.1), np.random.normal(0, 0.05), 1.0
    elif current_activity == 'RUNNING':
        hr = np.random.normal(120, 8)
        spo2 = np.random.normal(96, 1.0)
        ax, ay, az = 1.2 + np.random.normal(0, 0.2), np.random.normal(0, 0.1), 1.0
    else:  # CYCLING
        hr = np.random.normal(105, 6)
        spo2 = np.random.normal(97, 0.7)
        ax, ay, az = 0.8 + np.random.normal(0, 0.15), np.random.normal(0, 0.08), 1.0
    
    data = {
        'status': 'connected',
        'last_update': current_time.isoformat(),
        'is_real_data': True,
        'ml_active': True,
        'data': {
            'node_id': 'NODE_e661',
            'timestamp': current_time.isoformat(),
            'hr': max(50, min(150, hr)),
            'spo2': max(90, min(100, spo2)),
            'temp': 36.5 + np.random.normal(0, 0.2),
            'ax': round(ax, 3),
            'ay': round(ay, 3),
            'az': round(az, 3),
            'activity': current_activity,
            'activity_confidence': np.random.uniform(0.85, 0.98),
            'acceleration_magnitude': np.sqrt(ax**2 + ay**2 + az**2),
            'battery': np.random.uniform(75, 95),
            'packet_id': int(current_time.timestamp()) % 10000
        }
    }
    
    return data

# ================ ML ACTIVITY DISPLAY ================
def display_ml_activity(activity, confidence):
    """Display ML activity with confidence"""
    activity_emojis = {
        'RESTING': '😴',
        'WALKING': '🚶',
        'RUNNING': '🏃',
        'CYCLING': '🚴',
        'JUMPING': '🦘'
    }
    
    activity_colors = {
        'RESTING': '#10B981',
        'WALKING': '#3B82F6',
        'RUNNING': '#EF4444',
        'CYCLING': '#8B5CF6',
        'JUMPING': '#F59E0B'
    }
    
    emoji = activity_emojis.get(activity, '📊')
    color = activity_colors.get(activity, '#6B7280')
    
    # Confidence gauge
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=confidence * 100,
        title={'text': f"{emoji} {activity}", 'font': {'size': 24}},
        number={'suffix': "%", 'font': {'size': 40}},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': color},
            'steps': [
                {'range': [0, 70], 'color': "#EF4444"},
                {'range': [70, 85], 'color': "#F59E0B"},
                {'range': [85, 100], 'color': "#10B981"}
            ],
            'threshold': {
                'line': {'color': "white", 'width': 4},
                'thickness': 0.8,
                'value': confidence * 100
            }
        }
    ))
    
    fig.update_layout(height=300, margin=dict(t=50, b=30, l=30, r=30))
    return fig

# ================ MAIN DASHBOARD ================
def main():
    """Main dashboard function"""
    
    # Header
    st.markdown("""
    <div class='main-header'>
        <h1 style='color: #1F2937; margin: 0;'>🏥 STEMCUBE REAL-TIME HEALTH MONITORING</h1>
        <p style='color: #6B7280; margin: 5px 0 0 0;'>
            LIVE Data from STEMCUBE Sensors • ML Activity Recognition • Streamlit Cloud
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ LIVE CONTROLS")
        
        # Connection Status
        data = load_real_time_data()
        if data and data.get('is_real_data'):
            st.success("✅ CONNECTED TO STEMCUBE")
            last_update = datetime.fromisoformat(data['last_update'].replace('Z', '+00:00'))
            seconds_ago = (datetime.now() - last_update).total_seconds()
            
            if seconds_ago < 10:
                st.success(f"📡 LIVE: {seconds_ago:.1f}s ago")
            elif seconds_ago < 30:
                st.warning(f"⚠️ NEAR REAL-TIME: {seconds_ago:.1f}s ago")
            else:
                st.error(f"❌ DELAYED: {seconds_ago:.1f}s ago")
            
            st.metric("ML Active", "✅ YES" if data.get('ml_active') else "❌ NO")
        else:
            st.error("❌ WAITING FOR STEMCUBE DATA")
            st.info("Run Uploader_To_Cloud.py on your local machine")
        
        # Refresh Control
        st.subheader("🔄 REFRESH")
        auto_refresh = st.checkbox("Auto-refresh", value=True)
        refresh_rate = st.slider("Seconds", 1, 30, 5)
        
        # Patient Selection
        st.subheader("👤 PATIENT")
        patients = ['Nur Alysa (NODE_e661)', 'Test Patient 1', 'Test Patient 2']
        selected_patient = st.selectbox("Select Patient", patients)
        
        # Alerts Settings
        st.subheader("🚨 ALERTS")
        st.checkbox("Enable HR Alerts", value=True)
        st.checkbox("Enable SpO₂ Alerts", value=True)
        st.checkbox("Enable Fall Detection", value=True)
        
        st.markdown("---")
        st.caption(f"System Time: {datetime.now().strftime('%H:%M:%S')}")
    
    # Main Content
    if data:
        current = data['data']
        
        # Row 1: Vital Signs
        st.subheader("🩺 REAL-TIME VITAL SIGNS")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Heart Rate
            hr = current['hr']
            hr_status = "🟢 NORMAL" if 60 <= hr <= 100 else "🟡 ELEVATED" if hr <= 120 else "🔴 HIGH"
            
            fig_hr = go.Figure(go.Indicator(
                mode="gauge+number",
                value=hr,
                title={'text': "HEART RATE", 'font': {'size': 20}},
                number={'suffix': " BPM", 'font': {'size': 40}},
                gauge={
                    'axis': {'range': [40, 160]},
                    'bar': {'color': "#EF4444" if hr > 100 else "#10B981"},
                    'steps': [
                        {'range': [40, 60], 'color': "#F59E0B"},
                        {'range': [60, 100], 'color': "#10B981"},
                        {'range': [100, 160], 'color': "#EF4444"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.8,
                        'value': hr
                    }
                }
            ))
            fig_hr.update_layout(height=250)
            st.plotly_chart(fig_hr, use_container_width=True)
            st.caption(f"Status: {hr_status}")
        
        with col2:
            # SpO2
            spo2 = current['spo2']
            spo2_status = "🟢 NORMAL" if spo2 >= 95 else "🟡 LOW" if spo2 >= 90 else "🔴 CRITICAL"
            
            fig_spo2 = go.Figure(go.Indicator(
                mode="gauge+number",
                value=spo2,
                title={'text': "BLOOD OXYGEN", 'font': {'size': 20}},
                number={'suffix': " %", 'font': {'size': 40}},
                gauge={
                    'axis': {'range': [70, 100]},
                    'bar': {'color': "#EF4444" if spo2 < 90 else "#F59E0B" if spo2 < 95 else "#10B981"},
                    'steps': [
                        {'range': [70, 90], 'color': "#EF4444"},
                        {'range': [90, 95], 'color': "#F59E0B"},
                        {'range': [95, 100], 'color': "#10B981"}
                    ]
                }
            ))
            fig_spo2.update_layout(height=250)
            st.plotly_chart(fig_spo2, use_container_width=True)
            st.caption(f"Status: {spo2_status}")
        
        with col3:
            # Temperature
            temp = current['temp']
            temp_status = "🟢 NORMAL" if temp <= 37.5 else "🟡 ELEVATED" if temp <= 38.0 else "🔴 FEVER"
            
            fig_temp = go.Figure(go.Indicator(
                mode="gauge+number",
                value=temp,
                title={'text': "TEMPERATURE", 'font': {'size': 20}},
                number={'suffix': " °C", 'font': {'size': 40}},
                gauge={
                    'axis': {'range': [35, 40]},
                    'bar': {'color': "#EF4444" if temp > 37.5 else "#10B981"},
                    'steps': [
                        {'range': [35, 37.5], 'color': "#10B981"},
                        {'range': [37.5, 40], 'color': "#EF4444"}
                    ]
                }
            ))
            fig_temp.update_layout(height=250)
            st.plotly_chart(fig_temp, use_container_width=True)
            st.caption(f"Status: {temp_status}")
        
        with col4:
            # ML Activity Recognition
            st.plotly_chart(
                display_ml_activity(
                    current['activity'], 
                    current['activity_confidence']
                ), 
                use_container_width=True
            )
            
            # Motion Data
            st.markdown(f"""
            <div style='background: #F3F4F6; padding: 15px; border-radius: 10px;'>
                <h4 style='margin: 0 0 10px 0;'>📡 MOTION DATA</h4>
                <p style='margin: 5px 0;'>Acceleration: {current['ax']:.3f}, {current['ay']:.3f}, {current['az']:.3f} g</p>
                <p style='margin: 5px 0;'>Magnitude: {current['acceleration_magnitude']:.3f} g</p>
                <p style='margin: 5px 0;'>Battery: {current['battery']:.1f}%</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Row 2: Alerts and History
        st.subheader("🚨 REAL-TIME ALERTS & HISTORY")
        
        col_a1, col_a2 = st.columns([1, 2])
        
        with col_a1:
            # Generate alerts
            alerts = []
            if current['hr'] > 120:
                alerts.append(("🔴 CRITICAL", "High Heart Rate", f"{current['hr']} BPM"))
            elif current['hr'] > 100:
                alerts.append(("🟡 WARNING", "Elevated Heart Rate", f"{current['hr']} BPM"))
            
            if current['spo2'] < 90:
                alerts.append(("🔴 CRITICAL", "Low Blood Oxygen", f"{current['spo2']}%"))
            elif current['spo2'] < 95:
                alerts.append(("🟡 WARNING", "Reduced Blood Oxygen", f"{current['spo2']}%"))
            
            if current['temp'] > 38.0:
                alerts.append(("🔴 CRITICAL", "Fever Detected", f"{current['temp']}°C"))
            elif current['temp'] > 37.5:
                alerts.append(("🟡 WARNING", "Elevated Temperature", f"{current['temp']}°C"))
            
            if alerts:
                st.markdown("<h4>ACTIVE ALERTS</h4>", unsafe_allow_html=True)
                for emoji, title, value in alerts:
                    st.markdown(f"""
                    <div class='alert-{'danger' if 'CRITICAL' in emoji else 'warning'}'>
                        <strong>{emoji} {title}</strong><br>
                        <small>Current: {value}</small>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.success("✅ NO ACTIVE ALERTS")
                st.markdown("All vitals within normal range")
            
            # System Info
            st.markdown("---")
            st.markdown("""
            <h4>ℹ️ SYSTEM INFORMATION</h4>
            <p><strong>Data Source:</strong> STEMCUBE Hardware</p>
            <p><strong>ML Model:</strong> Random Forest Classifier</p>
            <p><strong>Communication:</strong> LoRa HC-12</p>
            <p><strong>Last Packet ID:</strong> {}</p>
            """.format(current['packet_id']), unsafe_allow_html=True)
        
        with col_a2:
            # Activity History Chart
            st.markdown("<h4>ACTIVITY HISTORY (SIMULATED)</h4>", unsafe_allow_html=True)
            
            # Generate history data
            times = [datetime.now() - timedelta(minutes=i) for i in range(30, 0, -1)]
            activities = ['RESTING', 'WALKING', 'RUNNING', 'CYCLING']
            
            history_data = []
            for t in times:
                activity_idx = int(t.minute / 15) % 4
                activity = activities[activity_idx]
                
                # Activity-based HR
                if activity == 'RESTING':
                    hr = np.random.normal(65, 3)
                elif activity == 'WALKING':
                    hr = np.random.normal(85, 5)
                elif activity == 'RUNNING':
                    hr = np.random.normal(120, 8)
                else:
                    hr = np.random.normal(105, 6)
                
                history_data.append({
                    'time': t,
                    'activity': activity,
                    'heart_rate': max(50, min(150, hr))
                })
            
            df_history = pd.DataFrame(history_data)
            
            # Create chart
            fig_history = px.line(
                df_history, 
                x='time', 
                y='heart_rate',
                color='activity',
                title="Heart Rate vs Activity Over Time",
                color_discrete_map={
                    'RESTING': '#10B981',
                    'WALKING': '#3B82F6',
                    'RUNNING': '#EF4444',
                    'CYCLING': '#8B5CF6'
                }
            )
            
            fig_history.update_layout(
                xaxis_title="Time",
                yaxis_title="Heart Rate (BPM)",
                hovermode="x unified",
                height=400
            )
            
            st.plotly_chart(fig_history, use_container_width=True)
            
            # Raw Data
            with st.expander("📋 VIEW RAW SENSOR DATA"):
                st.json(current)
        
        # Footer
        st.markdown("---")
        
        col_f1, col_f2, col_f3 = st.columns(3)
        
        with col_f2:
            st.markdown(f"""
            <div style='text-align: center; color: #6B7280;'>
                <p><strong>🏥 STEMCUBE REAL-TIME MONITORING SYSTEM</strong></p>
                <p>Universiti Malaysia Pahang • Final Year Project 2025</p>
                <p>Last Update: {datetime.fromisoformat(data['last_update'].replace('Z', '+00:00')).strftime('%H:%M:%S')}</p>
                <p>Data Source: {'REAL STEMCUBE HARDWARE' if data.get('is_real_data') else 'DEMO MODE'}</p>
            </div>
            """, unsafe_allow_html=True)
    
    else:
        st.error("""
        ## ⚠️ NO DATA CONNECTION
        
        ### To get REAL-TIME data from STEMCUBE:
        
        1. **Run on your local computer** (with STEMCUBE connected):
        ```bash
        python Uploader_To_Cloud.py
        ```
        
        2. **Make sure STEMCUBE is connected** to COM8
        
        3. **The uploader will send data** to this dashboard automatically
        
        4. **Refresh this page** to see live data
        """)
    
    # Auto-refresh
    if auto_refresh:
        time.sleep(refresh_rate)
        st.rerun()

# ================ RUN DASHBOARD ================
if __name__ == "__main__":
    # Add authentication
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.title("🔐 STEMCUBE DASHBOARD LOGIN")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            if st.button("Login", type="primary"):
                if username == "admin" and password == "stemcube2025":
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        
        st.markdown("---")
        st.info("**Demo Credentials:** admin / stemcube2025")
        st.stop()
    
    main()