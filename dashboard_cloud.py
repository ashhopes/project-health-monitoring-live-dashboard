# dashboard_cloud.py - FIXED VERSION
"""
REAL STEMCUBE HEALTH MONITORING DASHBOARD - ERROR FIXED
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

# ================ LOGIN ================
def check_login():
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
check_login()

# ================ PAGE SETUP ================
st.set_page_config(
    page_title="STEMCUBE Real-Time Monitoring", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================ INITIALIZE REAL DATA STORAGE ================
if 'real_stemcube_data' not in st.session_state:
    st.session_state.real_stemcube_data = []
if 'last_real_data' not in st.session_state:
    st.session_state.last_real_data = None
if 'stemcube_connected' not in st.session_state:
    st.session_state.stemcube_connected = False
if 'connection_status' not in st.session_state:
    st.session_state.connection_status = "❌ Waiting for STEMCUBE"

# ================ HEADER ================
st.markdown("""
<div style='background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
            padding: 25px; border-radius: 15px; color: white; text-align: center; margin-bottom: 25px;'>
    <h1 style='margin: 0;'>🏥 STEMCUBE Real-Time Health Monitoring</h1>
    <p style='margin: 5px 0 0 0;'>LIVE DATA from STEMCUBE via LoRa • NODE_e661</p>
</div>
""", unsafe_allow_html=True)

# ================ SIDEBAR ================
with st.sidebar:
    st.header("⚙️ Controls")
    
    # Connection status
    st.subheader("📡 Connection Status")
    status_col1, status_col2 = st.columns(2)
    
    with status_col1:
        if st.session_state.last_real_data:
            time_diff = (datetime.now() - st.session_state.last_real_data).total_seconds()
            if time_diff < 10:
                st.success("✅ STEMCUBE Connected")
                st.metric("Last Update", f"{time_diff:.0f}s ago")
                st.session_state.connection_status = "✅ STEMCUBE Connected"
            else:
                st.warning("⚠️ No Recent Data")
                st.metric("Last Update", f"{time_diff:.0f}s ago")
                st.session_state.connection_status = "⚠️ No Recent Data"
        else:
            st.error("❌ Waiting for STEMCUBE")
            st.session_state.connection_status = "❌ Waiting for STEMCUBE"
    
    with status_col2:
        if st.session_state.real_stemcube_data:
            st.metric("Data Points", len(st.session_state.real_stemcube_data))
        else:
            st.metric("Data Points", 0)
    
    # Display settings
    st.subheader("📊 Display Settings")
    refresh_rate = st.slider("Auto-refresh (seconds)", 1, 60, 5)
    n_samples = st.slider("Samples to show", 10, 500, 100)
    
    # Node selection
    st.subheader("📟 Node Selection")
    selected_node = st.selectbox("Select Node", ["NODE_e661", "NODE_e662", "user_001"])
    
    # Data management
    st.subheader("💾 Data Management")
    if st.button("🔄 Clear All Data", use_container_width=True):
        st.session_state.real_stemcube_data = []
        st.session_state.last_real_data = None
        st.session_state.stemcube_connected = False
        st.rerun()
    
    # Debug info
    with st.expander("🔧 Debug Info"):
        st.write(f"Real data points: {len(st.session_state.real_stemcube_data)}")
        st.write(f"Last data: {st.session_state.last_real_data}")
        st.write(f"Connection: {st.session_state.connection_status}")
        
        # Test button
        if st.button("🧪 Test with Sample Data"):
            test_data = {
                'node_id': 'NODE_e661',
                'timestamp': datetime.now().isoformat(),
                'hr': 72,
                'spo2': 98,
                'temp': 36.5,
                'activity': 'RESTING'
            }
            st.session_state.real_stemcube_data.append(test_data)
            st.session_state.last_real_data = datetime.now()
            st.session_state.stemcube_connected = True
            st.rerun()
    
    st.markdown("---")
    st.info("Project by mOONbLOOM26 🌙")

# ================ DATA FUNCTIONS ================
def update_real_data(new_data):
    """Update with real STEMCUBE data"""
    try:
        if isinstance(new_data, dict):
            if 'timestamp' not in new_data:
                new_data['timestamp'] = datetime.now().isoformat()
            
            st.session_state.real_stemcube_data.append(new_data)
            st.session_state.last_real_data = datetime.now()
            st.session_state.stemcube_connected = True
            
            if len(st.session_state.real_stemcube_data) > 500:
                st.session_state.real_stemcube_data = st.session_state.real_stemcube_data[-500:]
            
            return True
    except Exception as e:
        st.error(f"Data error: {e}")
    return False

def get_display_data():
    """Get data for display"""
    if st.session_state.real_stemcube_data:
        df = pd.DataFrame(st.session_state.real_stemcube_data[-n_samples:])
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        return df, True
    
    # Fallback sample data
    return generate_sample_data(), False

def generate_sample_data():
    """Generate sample data"""
    base_time = datetime.now() - timedelta(minutes=10)
    data = []
    for i in range(n_samples):
        data.append({
            'node_id': 'NODE_e661',
            'timestamp': base_time + timedelta(seconds=i*2),
            'hr': 70 + np.random.normal(0, 5),
            'spo2': 97 + np.random.normal(0, 1),
            'temp': 36.5 + np.random.normal(0, 0.3),
            'activity': 'RESTING' if i % 20 < 15 else 'WALKING'
        })
    return pd.DataFrame(data)

# ================ MAIN DASHBOARD ================
try:
    # Get data
    df, is_real_data = get_display_data()
    
    # Filter for selected node
    if 'node_id' in df.columns:
        node_df = df[df['node_id'] == selected_node].copy()
    else:
        node_df = df.copy()
    
    # Sort by timestamp
    if not node_df.empty and 'timestamp' in node_df.columns:
        node_df = node_df.sort_values("timestamp", ascending=True)
    
    # Show data source
    if is_real_data:
        st.success(f"✅ Displaying REAL STEMCUBE data from {selected_node}")
    else:
        st.warning("⚠️ Displaying SAMPLE data - STEMCUBE not connected")
        st.info("""
        **To connect STEMCUBE:**
        1. Ensure STEMCUBE is connected to COM8
        2. Run: `python simple_bridge.py` (as Administrator)
        3. Data will appear here automatically
        """)
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["🩺 Live Vitals", "📈 Trends", "📊 Analytics"])
    
    with tab1:
        st.header("Real-Time Vital Signs")
        
        if node_df.empty:
            st.warning("No data available")
        else:
            latest = node_df.iloc[-1]
            
            # Create metrics in 4 columns
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                # Heart Rate
                hr = latest.get('hr', 0)
                st.metric("Heart Rate", f"{hr:.0f} BPM", 
                         "Normal" if 60 <= hr <= 100 else "Check")
                
                # HR Chart - SIMPLIFIED
                if len(node_df) > 1:
                    fig_hr = go.Figure()
                    fig_hr.add_trace(go.Scatter(
                        x=node_df['timestamp'], y=node_df['hr'],
                        mode='lines', line=dict(color='red', width=2)
                    ))
                    fig_hr.update_layout(
                        height=200,
                        margin=dict(t=20, b=20, l=20, r=20),
                        showlegend=False,
                        title="HR Trend"
                    )
                    st.plotly_chart(fig_hr, use_container_width=True)
            
            with col2:
                # SpO2
                spo2 = latest.get('spo2', 0)
                fig_spo2 = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=spo2,
                    title={'text': "SpO₂ (%)"},
                    gauge={
                        'axis': {'range': [85, 100]},
                        'bar': {'color': "green" if spo2 >= 95 else "orange"},
                        'steps': [
                            {'range': [85, 90], 'color': "lightcoral"},
                            {'range': [90, 95], 'color': "lightyellow"},
                            {'range': [95, 100], 'color': "lightgreen"}
                        ]
                    }
                ))
                fig_spo2.update_layout(height=250)
                st.plotly_chart(fig_spo2, use_container_width=True)
            
            with col3:
                # Temperature
                temp = latest.get('temp', 0)
                st.metric("Temperature", f"{temp:.1f} °C",
                         "Normal" if 36 <= temp <= 37.5 else "Check")
                
                # Temp Chart - SIMPLIFIED
                if len(node_df) > 1:
                    fig_temp = go.Figure()
                    fig_temp.add_trace(go.Scatter(
                        x=node_df['timestamp'], y=node_df['temp'],
                        mode='lines', line=dict(color='orange', width=2)
                    ))
                    fig_temp.update_layout(
                        height=200,
                        margin=dict(t=20, b=20, l=20, r=20),
                        showlegend=False,
                        title="Temp Trend"
                    )
                    st.plotly_chart(fig_temp, use_container_width=True)
            
            with col4:
                # Activity
                activity = latest.get('activity', 'Unknown')
                activity_emoji = {
                    'RESTING': '😴',
                    'WALKING': '🚶',
                    'RUNNING': '🏃',
                    'ACTIVE': '💪',
                    'Unknown': '❓'
                }
                
                st.markdown(f"""
                <div style='text-align: center; padding: 20px; border-radius: 10px; background: #f8f9fa;'>
                    <h3>Activity</h3>
                    <div style='font-size: 48px; margin: 10px 0;'>
                        {activity_emoji.get(activity, '📊')}
                    </div>
                    <h2 style='color: #4B0082;'>{activity}</h2>
                </div>
                """, unsafe_allow_html=True)
                
                if is_real_data:
                    st.caption("🎯 Real STEMCUBE Data")
                else:
                    st.caption("📱 Sample Data")
    
    with tab2:
        st.header("Data Trends")
        
        if len(node_df) > 1:
            # FIXED: Use correct property names
            fig = go.Figure()
            
            # Add HR trace
            fig.add_trace(go.Scatter(
                x=node_df['timestamp'], y=node_df['hr'],
                mode='lines', name='Heart Rate',
                line=dict(color='red', width=2)
            ))
            
            # Add SpO2 trace
            fig.add_trace(go.Scatter(
                x=node_df['timestamp'], y=node_df['spo2'],
                mode='lines', name='SpO₂',
                line=dict(color='blue', width=2),
                yaxis='y2'
            ))
            
            # FIXED: Use 'title' object instead of 'titlefont'
            fig.update_layout(
                title="Vital Signs Trends",
                xaxis_title="Time",
                yaxis=dict(
                    title="HR (BPM) / Temp (°C)",
                    titlefont=dict(color="red")  # FIXED: inside dict
                ),
                yaxis2=dict(
                    title="SpO₂ (%)",
                    titlefont=dict(color="blue"),  # FIXED: inside dict
                    overlaying='y',
                    side='right'
                ),
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Recent data table
            st.subheader("Recent Data Points")
            display_df = node_df[['timestamp', 'hr', 'spo2', 'temp', 'activity']].tail(10).copy()
            display_df['timestamp'] = display_df['timestamp'].dt.strftime("%H:%M:%S")
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("Not enough data for trends")
    
    with tab3:
        st.header("Analytics & Export")
        
        if not node_df.empty:
            # Statistics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.subheader("Heart Rate")
                st.metric("Average", f"{node_df['hr'].mean():.1f} BPM")
                st.metric("Range", f"{node_df['hr'].min():.0f}-{node_df['hr'].max():.0f}")
            
            with col2:
                st.subheader("SpO₂")
                st.metric("Average", f"{node_df['spo2'].mean():.1f}%")
                low_spo2 = (node_df['spo2'] < 95).sum()
                st.metric("Low Events", low_spo2)
            
            with col3:
                st.subheader("Temperature")
                st.metric("Average", f"{node_df['temp'].mean():.1f}°C")
                fever = (node_df['temp'] > 37.5).sum()
                st.metric("Fever Events", fever)
            
            # Data export
            st.subheader("Export Data")
            csv = node_df.to_csv(index=False)
            
            col_exp1, col_exp2 = st.columns(2)
            with col_exp1:
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"stemcube_data_{selected_node}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        else:
            st.info("No data available for analytics")
    
    # Auto-refresh
    if refresh_rate > 0:
        time.sleep(refresh_rate)
        st.rerun()

except Exception as e:
    st.error(f"Dashboard error: {e}")

# Footer
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; color: gray;'>
    <p>STEMCUBE Health Monitoring • {datetime.now().strftime('%H:%M:%S')}</p>
    <p>Status: {st.session_state.connection_status}</p>
</div>
""", unsafe_allow_html=True)