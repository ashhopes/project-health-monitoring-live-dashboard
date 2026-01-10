# dashboard_cloud.py - UPDATED FOR STREAMLIT CLOUD
"""
Live Health Monitoring Dashboard with LoRa
Streamlit Cloud Version - Real-time STEMCUBE Integration
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
import requests
from google.cloud import bigquery
from google.oauth2 import service_account
import base64

# ================ PAGE CONFIG ================
st.set_page_config(
    page_title="STEMCUBE Health Monitoring",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================ CUSTOM CSS ================
st.markdown("""
<style>
    /* Main container */
    .main {
        padding: 0rem 1rem;
    }
    
    /* Metrics styling */
    [data-testid="metric-container"] {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #764ba2;
    }
    
    /* Connection status badges */
    .connected {
        background-color: #d4edda;
        color: #155724;
        padding: 8px 15px;
        border-radius: 20px;
        font-weight: bold;
    }
    
    .disconnected {
        background-color: #f8d7da;
        color: #721c24;
        padding: 8px 15px;
        border-radius: 20px;
        font-weight: bold;
    }
    
    /* Card styling */
    .card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f8f9fa;
        border-radius: 10px 10px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #667eea;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# ================ INITIALIZE SESSION STATE ================
if 'stemcube_data' not in st.session_state:
    st.session_state.stemcube_data = []
if 'last_update' not in st.session_state:
    st.session_state.last_update = None
if 'connected' not in st.session_state:
    st.session_state.connected = False
if 'bigquery_data' not in st.session_state:
    st.session_state.bigquery_data = []
if 'data_source' not in st.session_state:
    st.session_state.data_source = "Simulated"

# ================ BIGQUERY CONNECTION ================
@st.cache_resource
def init_bigquery():
    """Initialize BigQuery connection from Streamlit secrets"""
    try:
        # Get credentials from Streamlit secrets
        service_account_info = st.secrets["gcp_service_account"]
        
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info
        )
        
        client = bigquery.Client(
            credentials=credentials,
            project=service_account_info["project_id"]
        )
        
        return client
    except Exception as e:
        st.warning(f"BigQuery connection failed: {e}")
        return None

def get_bigquery_data(node_id="NODE_e661", limit=100):
    """Get latest data from BigQuery"""
    try:
        bq_client = init_bigquery()
        if not bq_client:
            return []
        
        # Query your BigQuery table
        query = f"""
        SELECT 
            id_user as node_id,
            TIMESTAMP(timestamp) as timestamp,
            hr,
            spo2,
            temp,
            ax, ay, az,
            gx, gy, gz,
            activity,
            packet_id
        FROM `{st.secrets["bigquery"]["project_id"]}.{st.secrets["bigquery"]["dataset"]}.{st.secrets["bigquery"]["table"]}`
        WHERE id_user = '{node_id}'
        ORDER BY timestamp DESC
        LIMIT {limit}
        """
        
        query_job = bq_client.query(query)
        results = query_job.result()
        
        data = []
        for row in results:
            data.append(dict(row))
        
        return data
        
    except Exception as e:
        st.error(f"BigQuery query error: {e}")
        return []

# ================ API ENDPOINT FOR RECEIVING DATA ================
def receive_data_from_api():
    """Receive data from your local bridge via API"""
    try:
        # Your local bridge API endpoint (you need to expose this)
        api_url = st.secrets.get("api", {}).get("url", "http://localhost:5000/api/data")
        
        response = requests.get(api_url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            return None
            
    except Exception as e:
        # st.warning(f"API connection failed: {e}")
        return None

# ================ SIMULATED DATA ================
def generate_simulated_data(num_records=100):
    """Generate simulated data for demo"""
    base_time = datetime.now() - timedelta(minutes=num_records)
    
    data = []
    for i in range(num_records):
        timestamp = base_time + timedelta(seconds=i)
        
        # Realistic variations
        hr_base = 72
        hr_variation = np.sin(i/10) * 8 + np.random.normal(0, 2)
        hr = max(60, min(120, hr_base + hr_variation))
        
        spo2 = max(92, min(99, 97 + np.random.normal(0, 1)))
        
        temp_base = 36.5
        temp_variation = np.sin(i/20) * 0.2 + np.random.normal(0, 0.05)
        temp = max(35.5, min(37.5, temp_base + temp_variation))
        
        # Activity simulation
        activity_cycle = i % 40
        if activity_cycle < 30:
            activity = "RESTING"
            ax, ay, az = np.random.normal(0, 0.1, 3)
            az += 1.0  # gravity
        else:
            activity = "WALKING"
            ax = np.sin(i/5) * 0.5 + np.random.normal(0, 0.2)
            ay = np.cos(i/5) * 0.3 + np.random.normal(0, 0.1)
            az = 1.0 + np.random.normal(0, 0.1)
        
        data.append({
            'node_id': 'NODE_e661',
            'timestamp': timestamp,
            'hr': float(hr),
            'spo2': float(spo2),
            'temp': float(temp),
            'ax': float(ax),
            'ay': float(ay),
            'az': float(az),
            'gx': float(np.random.normal(0, 0.5)),
            'gy': float(np.random.normal(0, 0.5)),
            'gz': float(np.random.normal(0, 0.5)),
            'activity': activity,
            'packet_id': i + 1000,
            'battery_level': np.random.uniform(70, 100),
            'data_source': 'Simulated'
        })
    
    return data

# ================ GET DATA FUNCTION ================
def get_data():
    """Get data from available sources (BigQuery > API > Simulated)"""
    # Try BigQuery first
    try:
        bq_data = get_bigquery_data("NODE_e661", 100)
        if bq_data:
            st.session_state.data_source = "BigQuery"
            return bq_data
    except:
        pass
    
    # Try API
    try:
        api_data = receive_data_from_api()
        if api_data:
            st.session_state.data_source = "API"
            return [api_data] if isinstance(api_data, dict) else api_data
    except:
        pass
    
    # Fallback to simulated
    st.session_state.data_source = "Simulated"
    return generate_simulated_data(100)

# ================ HEADER SECTION ================
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.markdown("""
    <div style='background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
                padding: 25px; border-radius: 15px; color: white;'>
        <h1 style='margin: 0;'>🏥 STEMCUBE Health Monitoring</h1>
        <p style='margin: 5px 0 0 0; opacity: 0.9;'>Live data from STEMCUBE sensors via LoRa</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    # Connection status
    if st.session_state.connected:
        st.markdown('<div class="connected">✅ CONNECTED</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="disconnected">⚠️ DISCONNECTED</div>', unsafe_allow_html=True)
    
    # Data source
    st.caption(f"Source: {st.session_state.data_source}")

with col3:
    st.metric("Last Update", 
              st.session_state.last_update.strftime("%H:%M:%S") if st.session_state.last_update else "Never",
              delta="Live" if st.session_state.connected else "Offline")

# ================ SIDEBAR ================
with st.sidebar:
    st.markdown("## ⚙️ Dashboard Controls")
    
    # Node Selection
    st.subheader("📟 Node Selection")
    node_options = ["NODE_e661", "NODE_e662", "user_001", "user_002", "user_003"]
    selected_node = st.selectbox("Select Device", node_options, index=0)
    
    # Data Source Selection
    st.subheader("🔌 Data Source")
    source = st.radio(
        "Choose data source:",
        ["Auto-detect", "BigQuery", "Simulated", "API"],
        horizontal=True
    )
    
    # Display Settings
    st.subheader("📊 Display Settings")
    refresh_rate = st.slider("Refresh interval (seconds)", 1, 60, 5)
    display_samples = st.slider("Samples to display", 50, 500, 100)
    
    # Data Controls
    st.subheader("💾 Data Management")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        if st.button("🔄 Refresh Now", use_container_width=True):
            st.session_state.bigquery_data = get_bigquery_data(selected_node, display_samples)
            st.session_state.last_update = datetime.now()
            st.rerun()
    
    with col_s2:
        if st.button("🗑️ Clear Cache", use_container_width=True):
            st.session_state.stemcube_data = []
            st.session_state.bigquery_data = []
            st.rerun()
    
    # System Info
    st.markdown("---")
    st.markdown("### 📈 System Status")
    
    # Get latest data for status
    all_data = get_data()
    if all_data:
        latest = all_data[-1] if isinstance(all_data, list) else all_data
        
        st.metric("Data Points", len(all_data) if isinstance(all_data, list) else 1)
        st.metric("Battery", f"{latest.get('battery_level', 75):.0f}%")
        
        # Connection quality
        if isinstance(all_data, list) and len(all_data) > 1:
            timestamps = [pd.to_datetime(d.get('timestamp')) for d in all_data if 'timestamp' in d]
            if timestamps:
                intervals = np.diff([ts.timestamp() for ts in timestamps])
                avg_interval = np.mean(intervals) if len(intervals) > 0 else 0
                st.metric("Avg Interval", f"{avg_interval:.1f}s")
    
    st.markdown("---")
    st.caption("Project by NUR ALYSA@TG22051")
    st.caption(f"Last update: {datetime.now().strftime('%H:%M:%S')}")

# ================ MAIN DASHBOARD ================
# Get data based on selected source
if source == "BigQuery":
    data = st.session_state.bigquery_data or get_bigquery_data(selected_node, display_samples)
    st.session_state.data_source = "BigQuery"
elif source == "Simulated":
    data = generate_simulated_data(display_samples)
    st.session_state.data_source = "Simulated"
elif source == "API":
    api_data = receive_data_from_api()
    data = [api_data] if api_data else generate_simulated_data(display_samples)
    st.session_state.data_source = "API" if api_data else "Simulated"
else:  # Auto-detect
    data = get_data()

# Convert to DataFrame
if isinstance(data, list):
    df = pd.DataFrame(data)
elif isinstance(data, dict):
    df = pd.DataFrame([data])
else:
    df = pd.DataFrame()

if not df.empty and 'timestamp' in df.columns:
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp', ascending=True).tail(display_samples)

# Create tabs
tab1, tab2, tab3 = st.tabs(["🩺 Health Vitals", "📈 Trends", "📊 Analytics"])

with tab1:
    if not df.empty:
        latest = df.iloc[-1].to_dict()
        
        # Top metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Heart Rate
            hr = latest.get('hr', 72)
            hr_status = "Normal" if 60 <= hr <= 100 else "High" if hr > 100 else "Low"
            
            st.metric(
                "❤️ Heart Rate",
                f"{hr:.0f} BPM",
                hr_status,
                delta_color="normal" if hr_status == "Normal" else "inverse"
            )
            
            # Heart rate mini chart
            if 'hr' in df.columns:
                fig_hr = go.Figure()
                fig_hr.add_trace(go.Scatter(
                    x=df['timestamp'].tail(20),
                    y=df['hr'].tail(20),
                    mode='lines+markers',
                    line=dict(color='#FF6B6B', width=3),
                    marker=dict(size=4)
                ))
                fig_hr.update_layout(
                    height=150,
                    margin=dict(t=0, b=0, l=0, r=0),
                    showlegend=False,
                    plot_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(showgrid=False, showticklabels=False),
                    yaxis=dict(showgrid=False, showticklabels=False)
                )
                st.plotly_chart(fig_hr, use_container_width=True, config={'displayModeBar': False})
        
        with col2:
            # SpO2 Gauge
            spo2 = latest.get('spo2', 96)
            spo2_color = "#28a745" if spo2 >= 95 else "#ffc107" if spo2 >= 90 else "#dc3545"
            
            fig_spo2 = go.Figure(go.Indicator(
                mode="gauge+number",
                value=spo2,
                title={'text': "🩸 SpO₂ (%)", 'font': {'size': 18}},
                number={'font': {'size': 30, 'color': spo2_color}},
                domain={'x': [0, 1], 'y': [0, 1]},
                gauge={
                    'axis': {'range': [85, 100], 'tickwidth': 1},
                    'bar': {'color': spo2_color, 'thickness': 0.5},
                    'steps': [
                        {'range': [85, 90], 'color': '#dc3545'},
                        {'range': [90, 95], 'color': '#ffc107'},
                        {'range': [95, 100], 'color': '#28a745'}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 95
                    }
                }
            ))
            fig_spo2.update_layout(height=200, margin=dict(t=0, b=0))
            st.plotly_chart(fig_spo2, use_container_width=True, config={'displayModeBar': False})
        
        with col3:
            # Temperature
            temp = latest.get('temp', 36.5)
            temp_status = "Normal" if 36 <= temp <= 37.5 else "Fever" if temp > 37.5 else "Low"
            
            st.metric(
                "🌡️ Temperature",
                f"{temp:.1f} °C",
                temp_status,
                delta_color="normal" if temp_status == "Normal" else "inverse"
            )
            
            # Temperature mini chart
            if 'temp' in df.columns:
                fig_temp = go.Figure()
                fig_temp.add_trace(go.Scatter(
                    x=df['timestamp'].tail(20),
                    y=df['temp'].tail(20),
                    mode='lines+markers',
                    line=dict(color='#FFA726', width=3),
                    marker=dict(size=4)
                ))
                fig_temp.add_hline(y=37.5, line_dash="dash", line_color="red", opacity=0.5)
                fig_temp.update_layout(
                    height=150,
                    margin=dict(t=0, b=0, l=0, r=0),
                    showlegend=False,
                    plot_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(showgrid=False, showticklabels=False),
                    yaxis=dict(showgrid=False, showticklabels=False)
                )
                st.plotly_chart(fig_temp, use_container_width=True, config={'displayModeBar': False})
        
        with col4:
            # Activity
            activity = latest.get('activity', 'UNKNOWN')
            activity_map = {
                'RESTING': {'emoji': '😴', 'color': '#6c757d'},
                'WALKING': {'emoji': '🚶', 'color': '#17a2b8'},
                'ACTIVE': {'emoji': '🏃', 'color': '#28a745'},
                'UNKNOWN': {'emoji': '❓', 'color': '#ffc107'}
            }
            
            activity_info = activity_map.get(activity, activity_map['UNKNOWN'])
            
            st.markdown(f"""
            <div style='text-align: center; padding: 15px; border-radius: 10px; 
                        background: {activity_info['color']}20; border-left: 5px solid {activity_info['color']};'>
                <h3 style='margin-bottom: 10px; color: {activity_info['color']};'>🏃 Activity</h3>
                <div style='font-size: 48px; margin: 10px 0;'>{activity_info['emoji']}</div>
                <h2 style='color: {activity_info['color']};'>{activity}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        # Motion Sensors
        st.subheader("📡 Motion Sensors")
        motion_cols = st.columns(6)
        
        motion_metrics = [
            ('Accel X', 'ax', '#FF6384'),
            ('Accel Y', 'ay', '#36A2EB'),
            ('Accel Z', 'az', '#FFCE56'),
            ('Gyro X', 'gx', '#4BC0C0'),
            ('Gyro Y', 'gy', '#9966FF'),
            ('Gyro Z', 'gz', '#FF9F40')
        ]
        
        for i, (name, key, color) in enumerate(motion_metrics):
            with motion_cols[i]:
                value = latest.get(key, 0)
                st.metric(name, f"{value:.3f}")
        
        # Recent Data Table
        st.subheader("📋 Recent Readings")
        display_df = df[['timestamp', 'hr', 'spo2', 'temp', 'activity']].tail(10).copy()
        if 'timestamp' in display_df.columns:
            display_df['timestamp'] = display_df['timestamp'].dt.strftime("%H:%M:%S")
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
    else:
        st.warning("No data available. Check your data source settings.")

with tab2:
    if not df.empty and len(df) > 1:
        # Create trend charts
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Heart Rate Trend', 'SpO₂ Trend', 'Temperature Trend', 'Motion Activity'),
            vertical_spacing=0.15,
            horizontal_spacing=0.1
        )
        
        # Heart Rate
        if 'hr' in df.columns:
            fig.add_trace(
                go.Scatter(x=df['timestamp'], y=df['hr'], 
                          mode='lines', name='HR', line=dict(color='#FF6B6B', width=3)),
                row=1, col=1
            )
            fig.add_hline(y=100, line_dash="dash", line_color="orange", row=1, col=1)
            fig.add_hline(y=60, line_dash="dash", line_color="orange", row=1, col=1)
        
        # SpO2
        if 'spo2' in df.columns:
            fig.add_trace(
                go.Scatter(x=df['timestamp'], y=df['spo2'],
                          mode='lines', name='SpO₂', line=dict(color='#36A2EB', width=3)),
                row=1, col=2
            )
            fig.add_hline(y=95, line_dash="dash", line_color="red", row=1, col=2)
        
        # Temperature
        if 'temp' in df.columns:
            fig.add_trace(
                go.Scatter(x=df['timestamp'], y=df['temp'],
                          mode='lines', name='Temp', line=dict(color='#FFA726', width=3)),
                row=2, col=1
            )
            fig.add_hline(y=37.5, line_dash="dash", line_color="red", row=2, col=1)
        
        # Motion (calculate magnitude)
        if all(col in df.columns for col in ['ax', 'ay', 'az']):
            df['motion_mag'] = np.sqrt(df['ax']**2 + df['ay']**2 + df['az']**2)
            fig.add_trace(
                go.Scatter(x=df['timestamp'], y=df['motion_mag'],
                          mode='lines', name='Motion', line=dict(color='#4BC0C0', width=3)),
                row=2, col=2
            )
        
        fig.update_layout(
            height=600,
            showlegend=True,
            template="plotly_white",
            hovermode="x unified"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Additional analysis
        st.subheader("📊 Statistical Analysis")
        
        stat_cols = st.columns(4)
        metrics = [
            ('Heart Rate', 'hr', 'BPM'),
            ('SpO₂', 'spo2', '%'),
            ('Temperature', 'temp', '°C'),
            ('Motion', 'motion_mag' if 'motion_mag' in df.columns else 'ax', 'g')
        ]
        
        for col, (name, key, unit) in zip(stat_cols, metrics):
            with col:
                if key in df.columns:
                    data_series = df[key].dropna()
                    if not data_series.empty:
                        st.metric(f"Avg {name}", f"{data_series.mean():.1f}{unit}")
                        st.metric(f"Min {name}", f"{data_series.min():.1f}{unit}")
                        st.metric(f"Max {name}", f"{data_series.max():.1f}{unit}")
    else:
        st.info("Not enough data for trend analysis. Collect more data points.")

with tab3:
    st.header("📊 Data Analytics & Export")
    
    if not df.empty:
        # Data summary
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Data Statistics")
            
            stats_df = pd.DataFrame({
                'Metric': ['Total Records', 'Time Range', 'Heart Rate (Avg)', 'SpO₂ (Avg)', 'Temperature (Avg)'],
                'Value': [
                    len(df),
                    f"{(df['timestamp'].max() - df['timestamp'].min()).total_seconds()/60:.1f} min" if 'timestamp' in df.columns else 'N/A',
                    f"{df['hr'].mean():.1f} BPM" if 'hr' in df.columns else 'N/A',
                    f"{df['spo2'].mean():.1f}%" if 'spo2' in df.columns else 'N/A',
                    f"{df['temp'].mean():.1f}°C" if 'temp' in df.columns else 'N/A'
                ]
            })
            
            st.dataframe(stats_df, use_container_width=True, hide_index=True)
        
        with col2:
            st.subheader("Health Status")
            
            # Health assessment
            if 'hr' in df.columns:
                hr_normal = ((df['hr'] >= 60) & (df['hr'] <= 100)).mean() * 100
                st.progress(hr_normal/100, text=f"Normal HR: {hr_normal:.1f}%")
            
            if 'spo2' in df.columns:
                spo2_normal = (df['spo2'] >= 95).mean() * 100
                st.progress(spo2_normal/100, text=f"Normal SpO₂: {spo2_normal:.1f}%")
            
            if 'temp' in df.columns:
                temp_normal = ((df['temp'] >= 36) & (df['temp'] <= 37.5)).mean() * 100
                st.progress(temp_normal/100, text=f"Normal Temp: {temp_normal:.1f}%")
        
        # Data Export
        st.subheader("📥 Export Data")
        
        col_exp1, col_exp2, col_exp3 = st.columns(3)
        
        with col_exp1:
            # CSV Export
            csv = df.to_csv(index=False)
            st.download_button(
                label="💾 Download CSV",
                data=csv,
                file_name=f"stemcube_{selected_node}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col_exp2:
            # JSON Export
            json_str = df.to_json(orient='records', indent=2)
            st.download_button(
                label="📄 Download JSON",
                data=json_str,
                file_name=f"stemcube_{selected_node}_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json",
                use_container_width=True
            )
        
        with col_exp3:
            # Excel Export
            @st.cache_data
            def convert_to_excel(df):
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='HealthData')
                return output.getvalue()
            
            excel_data = convert_to_excel(df)
            st.download_button(
                label="📊 Download Excel",
                data=excel_data,
                file_name=f"stemcube_{selected_node}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        
        # Raw Data Preview
        with st.expander("🔍 View Raw Data"):
            st.dataframe(df, use_container_width=True)
    
    else:
        st.warning("No data available for analytics.")

# ================ AUTO REFRESH ================
if refresh_rate > 0:
    time.sleep(refresh_rate)
    st.rerun()

# ================ FOOTER ================
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; color: #6c757d; padding: 20px;'>
    <p>STEMCUBE Health Monitoring System • v2.1 • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p>Data Source: {st.session_state.data_source} • Streamlit Cloud</p>
</div>
""", unsafe_allow_html=True)