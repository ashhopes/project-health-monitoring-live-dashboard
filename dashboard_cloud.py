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
import pytz
import base64

# ================ PAGE CONFIG ================
st.set_page_config(
    page_title="STEMCUBE LIVE - Real Health Monitoring",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================ SET BACKGROUND IMAGE ================
def set_background(image_url):
    """Set background image from URL"""
    try:
        # Use the Malaysia medical background image
        st.markdown(f"""
        <style>
        .stApp {{
            background-image: url("{image_url}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        
        /* Semi-transparent overlay for better readability */
        .main-container {{
            background-color: rgba(255, 255, 255, 0.92);
            border-radius: 20px;
            padding: 25px;
            margin: 20px 0;
            box-shadow: 0 10px 30px rgba(0,0,0,0.15);
        }}
        
        .metric-card {{
            background: rgba(255, 255, 255, 0.95);
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            border-top: 5px solid #667eea;
            margin-bottom: 15px;
            transition: transform 0.3s;
        }}
        
        .metric-card:hover {{
            transform: translateY(-5px);
        }}
        
        .alert-danger {{
            background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%);
            color: white;
            padding: 15px;
            border-radius: 10px;
            margin: 10px 0;
        }}
        
        .alert-warning {{
            background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%);
            color: white;
            padding: 15px;
            border-radius: 10px;
            margin: 10px 0;
        }}
        
        .sensor-badge {{
            display: inline-block;
            padding: 3px 10px;
            border-radius: 15px;
            font-size: 12px;
            font-weight: bold;
            margin: 2px;
        }}
        
        .max30102 {{ background: #EF4444; color: white; }}
        .bme280 {{ background: #10B981; color: white; }}
        .mpu6050 {{ background: #3B82F6; color: white; }}
        .master {{ background: #8B5CF6; color: white; }}
        
        .activity-badge {{
            display: inline-block;
            padding: 8px 15px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: bold;
            margin: 5px;
        }}
        
        .resting {{ background: #10B981; color: white; }}
        .walking {{ background: #3B82F6; color: white; }}
        .running {{ background: #EF4444; color: white; }}
        .cycling {{ background: #8B5CF6; color: white; }}
        .sitting {{ background: #F59E0B; color: white; }}
        .standing {{ background: #8B5CF6; color: white; }}
        .unknown {{ background: #6B7280; color: white; }}
        </style>
        """, unsafe_allow_html=True)
    except:
        pass

# Set your background image
BACKGROUND_IMAGE = "https://th.bing.com/th/id/OIP.HVGBvjgRp5eQOBPiWETH8gHaEK?w=275&h=180&c=7&r=0&o=7&dpr=1.3&pid=1.7&rm=3"
set_background(BACKGROUND_IMAGE)

# ================ LOAD REAL-TIME DATA ================
def load_real_time_data():
    """Load real-time data from JSON file"""
    try:
        # Malaysia timezone
        malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
        
        # Try to load from the JSON file created by Uploader.py
        try:
            with open('stemcube_cloud_data.json', 'r') as f:
                data = json.load(f)
            
            # Add Malaysia time
            if 'last_update' in data:
                try:
                    if 'T' in data['last_update']:
                        # Convert to Malaysia time if needed
                        pass
                except:
                    data['last_update'] = datetime.now(malaysia_tz).isoformat()
            
            return data
            
        except FileNotFoundError:
            # If no file exists, generate demo data
            return generate_demo_data(malaysia_tz)
        
    except Exception as e:
        st.error(f"Data load error: {e}")
        return None

def generate_demo_data(timezone):
    """Generate demo data for testing"""
    current_time = datetime.now(timezone)
    
    data = {
        'status': 'connected',
        'last_update': current_time.isoformat(),
        'is_real_data': False,
        'activity_source': 'STEMCUBE_MASTER',
        'sensors': {
            'MAX30102': 'Active',
            'BME280': 'Active', 
            'MPU6050': 'Active'
        },
        'data': {
            'node_id': 'NODE_e661',
            'timestamp': current_time.isoformat(),
            'malaysia_time': current_time.strftime('%H:%M:%S'),
            
            # MAX30102 Data
            'hr': 72,
            'hr_valid': True,
            'spo2': 97,
            'spo2_valid': True,
            
            # BME280 Data
            'temp': 26.5,
            'humidity': 65,
            'pressure': 1013,
            
            # MPU6050 Data
            'ax': 0.12,
            'ay': -0.08,
            'az': 1.02,
            'gx': 0.0,
            'gy': 0.0,
            'gz': 0.0,
            'acceleration_magnitude': 1.03,
            
            # STEMCUBE Master Activity
            'activity': 'RESTING',
            'activity_source': 'STEMCUBE_MASTER',
            
            # System
            'battery': 85,
            'packet_id': int(current_time.timestamp()) % 10000,
            'rssi': -65,
            'snr': 12
        }
    }
    
    return data

# ================ DISPLAY FUNCTIONS ================
def display_sensor_info():
    """Display sensor status"""
    st.markdown("""
    <div class='main-container'>
        <h4 style='margin: 0 0 10px 0;'>📡 ACTIVE SENSORS</h4>
        <span class='sensor-badge max30102'>MAX30102 - Heart Rate & SpO₂</span>
        <span class='sensor-badge bme280'>BME280 - Temperature & Humidity</span>
        <span class='sensor-badge mpu6050'>MPU6050 - Motion Sensor</span>
        <span class='sensor-badge master'>STEMCUBE MASTER - Activity Control</span>
        <p style='margin: 10px 0 0 0; font-size: 14px; color: #6B7280;'>
        <strong>Note:</strong> Activity classification done by STEMCUBE Master
        </p>
    </div>
    """, unsafe_allow_html=True)

def display_activity_badge(activity):
    """Display activity as a colored badge"""
    activity = activity.upper() if activity else "UNKNOWN"
    activity_class = activity.lower()
    
    activity_emojis = {
        'RESTING': '😴',
        'WALKING': '🚶',
        'RUNNING': '🏃',
        'CYCLING': '🚴',
        'SITTING': '💺',
        'STANDING': '🧍',
        'UNKNOWN': '❓'
    }
    
    emoji = activity_emojis.get(activity, '❓')
    
    return f"""
    <div class='activity-badge {activity_class}'>
        {emoji} {activity}
    </div>
    """

# ================ MAIN DASHBOARD ================
def main():
    """Main dashboard function - DISPLAY ONLY"""
    
    # Malaysia timezone
    malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
    current_time_malaysia = datetime.now(malaysia_tz)
    
    # Header with background image
    st.markdown(f"""
    <div class='main-container'>
        <h1 style='color: #1F2937; margin: 0;'>🏥 STEMCUBE REAL-TIME HEALTH MONITORING</h1>
        <p style='color: #6B7280; margin: 5px 0 0 0;'>
            Displaying LIVE data from STEMCUBE Master • Sensors: MAX30102 • BME280 • MPU6050
        </p>
        <p style='color: #667eea; margin: 5px 0 0 0;'>
            🇲🇾 Malaysia Time: {current_time_malaysia.strftime('%H:%M:%S')} (UTC+8) • 
            Streamlit Cloud
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Display sensor info
    display_sensor_info()
    
    # Sidebar
    with st.sidebar:
        st.markdown("<div class='main-container'>", unsafe_allow_html=True)
        st.header("⚙️ DASHBOARD CONTROLS")
        
        # Connection Status
        data = load_real_time_data()
        if data:
            if data.get('is_real_data'):
                st.success("✅ CONNECTED TO STEMCUBE")
                try:
                    last_update_str = data['last_update']
                    if 'T' in last_update_str:
                        last_update = datetime.fromisoformat(last_update_str.replace('Z', '+00:00'))
                        last_update_malaysia = last_update.astimezone(malaysia_tz)
                        seconds_ago = (current_time_malaysia - last_update_malaysia).total_seconds()
                        
                        if seconds_ago < 5:
                            st.success(f"📡 LIVE: {seconds_ago:.1f}s ago")
                        elif seconds_ago < 15:
                            st.warning(f"⚠️ NEAR REAL-TIME: {seconds_ago:.1f}s ago")
                        else:
                            st.error(f"❌ DELAYED: {seconds_ago:.1f}s ago")
                    else:
                        st.info("⏳ Processing timestamp...")
                except:
                    st.info("⏳ Processing...")
            else:
                st.warning("🔄 DEMO MODE")
                st.info("Run Uploader.py with real STEMCUBE")
            
            # Activity Source
            activity_source = data.get('activity_source', 'STEMCUBE_MASTER')
            st.metric("Activity Source", activity_source)
            
        else:
            st.error("❌ NO DATA")
            st.info("Start Uploader.py to send data")
        
        # Refresh Control
        st.subheader("🔄 REFRESH")
        auto_refresh = st.checkbox("Auto-refresh", value=True)
        refresh_rate = st.slider("Seconds", 1, 30, 5)
        
        # Patient Selection
        st.subheader("👤 PATIENT")
        patients = ['Nur Alysa (NODE_e661)', 'Test Patient 1', 'Test Patient 2']
        selected_patient = st.selectbox("Select Patient", patients)
        
        # Alert Settings
        st.subheader("🚨 ALERT SETTINGS")
        st.checkbox("Heart Rate Alerts", value=True)
        st.checkbox("Blood Oxygen Alerts", value=True)
        st.checkbox("Temperature Alerts", value=True)
        
        st.markdown("---")
        st.caption(f"🇲🇾 {current_time_malaysia.strftime('%H:%M:%S')}")
        st.caption("Universiti Malaysia Pahang")
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Main Content Area
    if data:
        current = data['data']
        
        # Row 1: Vital Signs
        st.markdown("<div class='main-container'>", unsafe_allow_html=True)
        st.subheader("❤️ VITAL SIGNS")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Heart Rate (MAX30102)
            hr = current.get('hr', 72)
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
                    ]
                }
            ))
            fig_hr.update_layout(height=250, paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_hr, use_container_width=True)
            st.caption(f"Status: {hr_status} • MAX30102")
        
        with col2:
            # SpO2 (MAX30102)
            spo2 = current.get('spo2', 97)
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
            fig_spo2.update_layout(height=250, paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_spo2, use_container_width=True)
            st.caption(f"Status: {spo2_status} • MAX30102")
        
        with col3:
            # Environmental Temperature (BME280)
            temp_env = current.get('temp', 26.5)
            if temp_env < 18:
                temp_status = "🟢 COOL"
            elif temp_env < 28:
                temp_status = "🟢 COMFORTABLE"
            elif temp_env < 32:
                temp_status = "🟡 WARM"
            else:
                temp_status = "🔴 HOT"
            
            fig_temp = go.Figure(go.Indicator(
                mode="gauge+number",
                value=temp_env,
                title={'text': "ENVIRONMENT", 'font': {'size': 20}},
                number={'suffix': " °C", 'font': {'size': 40}},
                gauge={
                    'axis': {'range': [10, 40]},
                    'bar': {'color': "#EF4444" if temp_env > 30 else "#10B981"},
                    'steps': [
                        {'range': [10, 18], 'color': "#3B82F6"},
                        {'range': [18, 28], 'color': "#10B981"},
                        {'range': [28, 32], 'color': "#F59E0B"},
                        {'range': [32, 40], 'color': "#EF4444"}
                    ]
                }
            ))
            fig_temp.update_layout(height=250, paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_temp, use_container_width=True)
            st.caption(f"Status: {temp_status} • BME280")
        
        with col4:
            # Activity from STEMCUBE Master
            activity = current.get('activity', 'RESTING')
            st.markdown("<h4 style='text-align: center;'>ACTIVITY</h4>", unsafe_allow_html=True)
            st.markdown(f"""
            <div style='text-align: center; margin: 20px 0;'>
                {display_activity_badge(activity)}
            </div>
            """, unsafe_allow_html=True)
            st.caption(f"Source: STEMCUBE MASTER")
            
            # Sensor Values
            st.markdown("""
            <div style='background: rgba(243, 244, 246, 0.8); padding: 15px; border-radius: 10px; margin-top: 10px;'>
                <h4 style='margin: 0 0 10px 0;'>📊 SENSOR READINGS</h4>
                <p style='margin: 5px 0;'>💧 Humidity: <strong>{humidity}%</strong> (BME280)</p>
                <p style='margin: 5px 0;'>📏 Pressure: <strong>{pressure} hPa</strong></p>
                <p style='margin: 5px 0;'>🔋 Battery: <strong>{battery}%</strong></p>
                <p style='margin: 5px 0;'>📡 Signal: <strong>{rssi} dB</strong></p>
            </div>
            """.format(
                humidity=current.get('humidity', 65),
                pressure=current.get('pressure', 1013),
                battery=current.get('battery', 85),
                rssi=current.get('rssi', -65)
            ), unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Row 2: Alerts and Motion Data
        st.markdown("<div class='main-container'>", unsafe_allow_html=True)
        st.subheader("🚨 ALERTS & MOTION DATA")
        
        col_a1, col_a2 = st.columns([1, 2])
        
        with col_a1:
            # Generate alerts
            alerts = []
            
            # MAX30102 Alerts
            hr = current.get('hr', 72)
            if hr > 120:
                alerts.append(("🔴 CRITICAL", "High Heart Rate", f"{hr} BPM", "MAX30102"))
            elif hr > 100:
                alerts.append(("🟡 WARNING", "Elevated Heart Rate", f"{hr} BPM", "MAX30102"))
            elif hr < 50:
                alerts.append(("🔴 CRITICAL", "Low Heart Rate", f"{hr} BPM", "MAX30102"))
            
            spo2 = current.get('spo2', 97)
            if spo2 < 90:
                alerts.append(("🔴 CRITICAL", "Low Blood Oxygen", f"{spo2}%", "MAX30102"))
            elif spo2 < 95:
                alerts.append(("🟡 WARNING", "Reduced Blood Oxygen", f"{spo2}%", "MAX30102"))
            
            # BME280 Alerts
            temp_env = current.get('temp', 26.5)
            if temp_env > 35:
                alerts.append(("🔴 CRITICAL", "Hot Environment", f"{temp_env}°C", "BME280"))
            elif temp_env > 30:
                alerts.append(("🟡 WARNING", "Warm Environment", f"{temp_env}°C", "BME280"))
            
            humidity = current.get('humidity', 65)
            if humidity > 80:
                alerts.append(("🟡 WARNING", "High Humidity", f"{humidity}%", "BME280"))
            
            if alerts:
                st.markdown("<h4>ACTIVE ALERTS</h4>", unsafe_allow_html=True)
                for emoji, title, value, sensor in alerts:
                    st.markdown(f"""
                    <div class='alert-{'danger' if 'CRITICAL' in emoji else 'warning'}'>
                        <strong>{emoji} {title}</strong><br>
                        <small>{value} • {sensor}</small>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.success("✅ NO ACTIVE ALERTS")
                st.markdown("All readings within normal range")
            
            # Motion Data (MPU6050)
            st.markdown("---")
            st.markdown("""
            <h4>🎯 MOTION SENSOR (MPU6050)</h4>
            <p><strong>Acceleration (g):</strong></p>
            <p style='margin: 5px 0;'>X: {ax:.3f}</p>
            <p style='margin: 5px 0;'>Y: {ay:.3f}</p>
            <p style='margin: 5px 0;'>Z: {az:.3f}</p>
            <p><strong>Magnitude:</strong> {mag:.3f} g</p>
            <p><strong>Gyroscope (°/s):</strong></p>
            <p style='margin: 5px 0;'>X: {gx:.1f}</p>
            <p style='margin: 5px 0;'>Y: {gy:.1f}</p>
            <p style='margin: 5px 0;'>Z: {gz:.1f}</p>
            """.format(
                ax=current.get('ax', 0.12),
                ay=current.get('ay', -0.08),
                az=current.get('az', 1.02),
                gx=current.get('gx', 0.0),
                gy=current.get('gy', 0.0),
                gz=current.get('gz', 0.0),
                mag=current.get('acceleration_magnitude', 1.03)
            ), unsafe_allow_html=True)
        
        with col_a2:
            # Activity Timeline
            st.markdown("<h4>ACTIVITY TIMELINE (LAST 30 MINUTES)</h4>", unsafe_allow_html=True)
            
            # Generate simulated timeline
            times = [current_time_malaysia - timedelta(minutes=i) for i in range(30, 0, -1)]
            activities = ['RESTING', 'WALKING', 'SITTING', 'STANDING', 'WALKING', 'RESTING']
            
            timeline_data = []
            for i, t in enumerate(times):
                activity_idx = i % len(activities)
                activity = activities[activity_idx]
                
                # Simulate HR based on activity
                if activity == 'RESTING':
                    hr = 70 + np.random.normal(0, 3)
                elif activity == 'WALKING':
                    hr = 90 + np.random.normal(0, 5)
                elif activity == 'SITTING':
                    hr = 75 + np.random.normal(0, 3)
                elif activity == 'STANDING':
                    hr = 80 + np.random.normal(0, 4)
                else:
                    hr = 85 + np.random.normal(0, 5)
                
                timeline_data.append({
                    'time': t,
                    'activity': activity,
                    'heart_rate': max(50, min(150, hr))
                })
            
            df_timeline = pd.DataFrame(timeline_data)
            
            # Create chart
            fig_timeline = px.line(
                df_timeline, 
                x='time', 
                y='heart_rate',
                color='activity',
                title="Heart Rate vs Activity (Simulated)",
                color_discrete_map={
                    'RESTING': '#10B981',
                    'WALKING': '#3B82F6',
                    'RUNNING': '#EF4444',
                    'CYCLING': '#8B5CF6',
                    'SITTING': '#F59E0B',
                    'STANDING': '#8B5CF6'
                }
            )
            
            fig_timeline.update_layout(
                xaxis_title="Malaysia Time",
                yaxis_title="Heart Rate (BPM)",
                hovermode="x unified",
                height=400,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            
            st.plotly_chart(fig_timeline, use_container_width=True)
            
            # Raw Data
            with st.expander("📋 VIEW RAW SENSOR DATA"):
                st.json(current)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Footer
        st.markdown("<div class='main-container'>", unsafe_allow_html=True)
        col_f1, col_f2, col_f3 = st.columns(3)
        
        with col_f2:
            try:
                last_update = datetime.fromisoformat(data['last_update'].replace('Z', '+00:00')).astimezone(malaysia_tz)
                last_update_str = last_update.strftime('%H:%M:%S')
            except:
                last_update_str = current.get('malaysia_time', 'Unknown')
            
            st.markdown(f"""
            <div style='text-align: center; color: #6B7280;'>
                <p><strong>🏥 STEMCUBE REAL-TIME MONITORING SYSTEM</strong></p>
                <p>Universiti Malaysia Pahang • Final Year Project 2025</p>
                <p>🇲🇾 Malaysia Time: {current_time_malaysia.strftime('%H:%M:%S')} (UTC+8)</p>
                <p>Last Update: {last_update_str} • Node: {current.get('node_id', 'NODE_e661')}</p>
                <p>Data Source: {'REAL STEMCUBE HARDWARE' if data.get('is_real_data') else 'DEMO MODE'}</p>
                <p>Sensors: MAX30102 • BME280 • MPU6050 • Activity by STEMCUBE Master</p>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    else:
        st.markdown("<div class='main-container'>", unsafe_allow_html=True)
        st.error("""
        ## ⚠️ NO DATA CONNECTION
        
        ### To get REAL-TIME data from STEMCUBE:
        
        1. **Run on your local computer** (with STEMCUBE connected):
        ```bash
        python Uploader.py
        ```
        
        2. **Make sure STEMCUBE Master is running** on COM5/COM7
        
        3. **Slave receiver** should be on COM8
        
        4. **Refresh this page** to see live data
        
        ### Current Malaysia Time: {}
        """.format(current_time_malaysia.strftime('%H:%M:%S')))
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Auto-refresh
    if auto_refresh:
        time.sleep(refresh_rate)
        st.rerun()

# ================ RUN DASHBOARD ================
if __name__ == "__main__":
    # Simple authentication
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        st.markdown("<div class='main-container'>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.title("🔐 STEMCUBE DASHBOARD")
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
        st.markdown("</div>", unsafe_allow_html=True)
        st.stop()
    
    main()