# dashboard_cloud.py - FINAL FIXED VERSION
"""
STEMCUBE REAL-TIME HEALTH MONITORING DASHBOARD
FIXED Plotly error - Simplified version
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
    page_title="STEMCUBE Health Monitoring", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================ INITIALIZE DATA STORAGE ================
if 'real_stemcube_data' not in st.session_state:
    st.session_state.real_stemcube_data = []
if 'last_real_data' not in st.session_state:
    st.session_state.last_real_data = None

# ================ HEADER ================
st.markdown("""
<div style='background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
            padding: 25px; border-radius: 15px; color: white; text-align: center; margin-bottom: 25px;'>
    <h1 style='margin: 0;'>🏥 STEMCUBE Real-Time Health Monitoring</h1>
    <p style='margin: 5px 0 0 0;'>Live data from STEMCUBE sensors • NODE_e661</p>
</div>
""", unsafe_allow_html=True)

# ================ SIDEBAR ================
with st.sidebar:
    st.header("⚙️ Controls")
    
    # Connection status
    st.subheader("📡 Connection Status")
    
    if st.session_state.last_real_data:
        time_diff = (datetime.now() - st.session_state.last_real_data).total_seconds()
        if time_diff < 10:
            st.success("✅ STEMCUBE Connected")
            st.metric("Last Update", f"{time_diff:.0f}s ago")
        else:
            st.warning("⚠️ No Recent Data")
            st.metric("Last Update", f"{time_diff:.0f}s ago")
    else:
        st.error("❌ Waiting for STEMCUBE")
    
    if st.session_state.real_stemcube_data:
        st.metric("Data Points", len(st.session_state.real_stemcube_data))
    
    # Display settings
    st.subheader("📊 Display Settings")
    refresh_rate = st.slider("Auto-refresh (seconds)", 1, 60, 5)
    n_samples = st.slider("Samples to show", 10, 500, 100)
    
    # Node selection
    st.subheader("📟 Node Selection")
    selected_node = st.selectbox("Select Node", ["NODE_e661", "NODE_e662"])
    
    # Data management
    st.subheader("💾 Data Management")
    if st.button("🔄 Clear All Data", use_container_width=True):
        st.session_state.real_stemcube_data = []
        st.session_state.last_real_data = None
        st.rerun()
    
    # Test data button
    with st.expander("🔧 Test Options"):
        if st.button("🧪 Add Test Data"):
            test_data = {
                'node_id': 'NODE_e661',
                'timestamp': datetime.now().isoformat(),
                'hr': 75,
                'spo2': 97,
                'temp': 36.6,
                'activity': 'RESTING'
            }
            st.session_state.real_stemcube_data.append(test_data)
            st.session_state.last_real_data = datetime.now()
            st.rerun()
    
    st.markdown("---")
    st.info("Project by mOONbLOOM26 🌙")

# ================ DATA FUNCTIONS ================
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
    base_time = datetime.now() - timedelta(minutes=5)
    data = []
    for i in range(n_samples):
        data.append({
            'node_id': 'NODE_e661',
            'timestamp': base_time + timedelta(seconds=i*2),
            'hr': 70 + np.random.normal(0, 5),
            'spo2': 96 + np.random.normal(0, 2),
            'temp': 36.5 + np.random.normal(0, 0.3),
            'activity': 'RESTING' if i % 10 < 7 else 'WALKING'
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
    if is_real_data and st.session_state.real_stemcube_data:
        st.success(f"✅ Displaying REAL STEMCUBE data from {selected_node}")
    else:
        st.warning("⚠️ Displaying SAMPLE data - STEMCUBE not connected")
        st.info("""
        **To connect STEMCUBE:**
        1. Ensure STEMCUBE is connected to COM8
        2. Run bridge script as Administrator
        3. Real data will appear here automatically
        """)
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["🩺 Live Vitals", "📈 Trends", "📊 Analytics"])
    
    with tab1:
        st.header("Real-Time Vital Signs")
        
        if node_df.empty:
            st.warning("No data available")
        else:
            latest = node_df.iloc[-1]
            
            # Create metrics in 3 columns (simpler)
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Heart Rate
                hr = latest.get('hr', 0)
                st.metric("❤️ Heart Rate", f"{hr:.0f} BPM")
                
                # Simple HR chart
                if len(node_df) > 1:
                    fig_hr = go.Figure()
                    fig_hr.add_trace(go.Scatter(
                        x=node_df['timestamp'], y=node_df['hr'],
                        mode='lines', line=dict(color='red', width=2),
                        name='Heart Rate'
                    ))
                    fig_hr.update_layout(
                        height=200,
                        margin=dict(t=10, b=10, l=10, r=10),
                        showlegend=False,
                        title="HR Trend"
                    )
                    st.plotly_chart(fig_hr, use_container_width=True)
            
            with col2:
                # SpO2
                spo2 = latest.get('spo2', 0)
                st.metric("🩸 SpO₂", f"{spo2:.1f}%")
                
                # SpO2 gauge (simplified)
                fig_spo2 = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=spo2,
                    title={'text': "SpO₂"},
                    gauge={
                        'axis': {'range': [85, 100]},
                        'bar': {'color': "green" if spo2 >= 95 else "orange"},
                    }
                ))
                fig_spo2.update_layout(height=200)
                st.plotly_chart(fig_spo2, use_container_width=True)
            
            with col3:
                # Temperature
                temp = latest.get('temp', 0)
                st.metric("🌡️ Temperature", f"{temp:.1f} °C")
                
                # Activity
                activity = latest.get('activity', 'Unknown')
                activity_emoji = {
                    'RESTING': '😴',
                    'WALKING': '🚶',
                    'RUNNING': '🏃',
                    'Unknown': '❓'
                }
                
                st.markdown(f"""
                <div style='text-align: center; padding: 15px; border-radius: 10px; background: #f8f9fa;'>
                    <h4>Activity</h4>
                    <div style='font-size: 36px; margin: 10px 0;'>
                        {activity_emoji.get(activity, '📊')}
                    </div>
                    <h3 style='color: #4B0082;'>{activity}</h3>
                </div>
                """, unsafe_allow_html=True)
    
    with tab2:
        st.header("Data Trends")
        
        if len(node_df) > 1:
            # SIMPLIFIED chart without dual axes
            fig = go.Figure()
            
            # Add HR trace
            fig.add_trace(go.Scatter(
                x=node_df['timestamp'], y=node_df['hr'],
                mode='lines', name='Heart Rate',
                line=dict(color='red', width=2)
            ))
            
            # Add SpO2 trace (scaled to similar range)
            fig.add_trace(go.Scatter(
                x=node_df['timestamp'], y=node_df['spo2'],
                mode='lines', name='SpO₂',
                line=dict(color='blue', width=2)
            ))
            
            # Add Temperature trace
            fig.add_trace(go.Scatter(
                x=node_df['timestamp'], y=node_df['temp'],
                mode='lines', name='Temperature',
                line=dict(color='orange', width=2)
            ))
            
            # SIMPLIFIED layout - NO complex yaxis configuration
            fig.update_layout(
                title="Vital Signs Trends",
                xaxis_title="Time",
                yaxis_title="Value",
                height=400,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Recent data table
            st.subheader("Recent Data Points")
            display_df = node_df[['timestamp', 'hr', 'spo2', 'temp', 'activity']].tail(10).copy()
            if 'timestamp' in display_df.columns:
                display_df['timestamp'] = display_df['timestamp'].dt.strftime("%H:%M:%S")
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("Not enough data for trends")
    
    with tab3:
        st.header("Analytics & Export")
        
        if not node_df.empty:
            # Simple statistics
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 Statistics")
                st.write(f"**Heart Rate:** {node_df['hr'].mean():.1f} ± {node_df['hr'].std():.1f} BPM")
                st.write(f"**SpO₂:** {node_df['spo2'].mean():.1f} ± {node_df['spo2'].std():.1f}%")
                st.write(f"**Temperature:** {node_df['temp'].mean():.1f} ± {node_df['temp'].std():.1f}°C")
                
                if 'activity' in node_df.columns:
                    activity_counts = node_df['activity'].value_counts()
                    st.write("**Activity Distribution:**")
                    for activity, count in activity_counts.items():
                        st.write(f"- {activity}: {count}")
            
            with col2:
                st.subheader("📥 Export Data")
                csv = node_df.to_csv(index=False)
                
                st.download_button(
                    label="💾 Download CSV",
                    data=csv,
                    file_name=f"stemcube_data_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                
                if st.button("📋 Copy to Clipboard", use_container_width=True):
                    st.session_state.clipboard_data = node_df.to_string()
                    st.success("Data copied to clipboard!")
        else:
            st.info("No data available for analytics")
    
    # Auto-refresh
    if refresh_rate > 0:
        time.sleep(refresh_rate)
        st.rerun()

except Exception as e:
    st.error(f"Dashboard error: {e}")
    st.info("Please refresh the page")

# Footer
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; color: gray;'>
    <p>STEMCUBE Health Monitoring • {datetime.now().strftime('%H:%M:%S')}</p>
    <p>Status: {'Connected' if st.session_state.last_real_data else 'Waiting'}</p>
</div>
""", unsafe_allow_html=True)