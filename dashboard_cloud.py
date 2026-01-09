# dashboard_cloud.py - COMPLETE FIXED VERSION
"""
Live Health Monitoring Dashboard with LoRa
Streamlit Cloud Version
"""

# ================ IMPORTS ================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from google.cloud import bigquery
from google.oauth2 import service_account
import google.auth
from io import BytesIO
import json
import os

# ================ LOGIN FUNCTION ================
def check_login():
    """Check if user is logged in, show login form if not"""
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
        
        st.markdown("</div>", unsafe_allow_html=True)
        st.stop()

# ================ RUN LOGIN CHECK ================
check_login()

# ================ PAGE SETUP ================
st.set_page_config(
    page_title="Live Health Monitoring System with LoRa", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================ HEADER ================
st.markdown("<h1 style='text-align: center; color:#4B0082;'>🩺 Live Health Monitoring System with LoRa</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Real-time monitoring of vital signs and motion data using LoRa sensors</p>", unsafe_allow_html=True)
st.markdown("---")

# ================ SIDEBAR CONTROLS ================
st.sidebar.header("⚙️ Controls")
refresh_rate = st.sidebar.slider("Auto-refresh every (seconds)", 0, 120, 30)
n_samples = st.sidebar.slider("Number of samples to display", 50, 500, 100)
st.sidebar.info("Project by mOONbLOOM26 🌙")

# ================ BIGQUERY AUTHENTICATION ================
try:
    # Option 1: Using Streamlit secrets (for Streamlit Cloud)
    if "gcp" in st.secrets:
        credentials = service_account.Credentials.from_service_account_info(
            dict(st.secrets["gcp"])
        )
        project_id = st.secrets["gcp"]["project_id"]
    
    # Option 2: Using environment variable
    else:
        # Check for environment variable
        creds_json = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
        if creds_json:
            creds_info = json.loads(creds_json)
            credentials = service_account.Credentials.from_service_account_info(creds_info)
            project_id = creds_info.get("project_id", "monitoring-system-with-lora")
        else:
            # Option 3: Default credentials
            credentials, project = google.auth.default()
            project_id = project or "monitoring-system-with-lora"
    
    # Initialize BigQuery client
    client = bigquery.Client(
        credentials=credentials,
        project=project_id,
        location="asia-southeast1"
    )
    
    st.sidebar.success("✅ Connected to BigQuery")
    
except Exception as e:
    st.error(f"❌ BigQuery authentication failed: {e}")
    st.info("""
    **Authentication Setup:**
    1. For Streamlit Cloud: Add service account JSON to Secrets
    2. For local: Set GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable
    """)
    st.stop()

# ================ TABLE REFERENCE ================
table_id = "monitoring-system-with-lora.sdp2_live_monitoring_system.lora_health_data_clean2"

# ================ FETCH LATEST DATA ================
@st.cache_data(ttl=30)
def fetch_latest(n=100):
    """Fetch latest data from BigQuery"""
    try:
        query = f"""
            SELECT ID_user as id_user, timestamp, temp, spo2, hr, ax, ay, az, gx, gy, gz, ir, red, humidity
            FROM `{table_id}`
            ORDER BY timestamp DESC
            LIMIT {n}
        """
        df = client.query(query).to_dataframe()
        return df
    except Exception as e:
        st.error(f"Query error: {e}")
        # Try simpler query
        try:
            simple_query = f"""
                SELECT ID_user as id_user, timestamp, temp, spo2, hr
                FROM `{table_id}`
                ORDER BY timestamp DESC
                LIMIT {n}
            """
            return client.query(simple_query).to_dataframe()
        except:
            return pd.DataFrame()

# ================ ACTIVITY CLASSIFICATION ================
def classify_activity(ax, ay, az, gx, gy, gz):
    """Classify activity based on motion sensor data"""
    try:
        # Handle NaN values
        ax = float(ax) if pd.notna(ax) else 0
        ay = float(ay) if pd.notna(ay) else 0
        az = float(az) if pd.notna(az) else 0
        
        magnitude = np.sqrt(ax**2 + ay**2 + az**2)
        
        if magnitude < 1.1:
            return "Resting/Sleeping"
        elif magnitude < 2.0:
            return "Light Activity"
        elif magnitude < 3.5:
            return "Walking"
        elif magnitude < 5.0:
            return "Brisk Walking"
        else:
            return "Running/Vigorous"
    except:
        return "Unknown"

# ================ GET AVAILABLE NODES ================
@st.cache_data(ttl=300)
def get_available_nodes():
    """Get distinct node IDs from the table"""
    try:
        query = f"""
            SELECT DISTINCT ID_user as id_user
            FROM `{table_id}`
            WHERE ID_user IS NOT NULL
            ORDER BY ID_user
            LIMIT 10
        """
        result = client.query(query).to_dataframe()
        
        if result.empty:
            return ["user_001", "user_002"]
        
        return result['id_user'].tolist()
    except Exception as e:
        return ["user_001", "user_002"]

# ================ MAIN DASHBOARD LOGIC ================
try:
    df = fetch_latest(n_samples)
    
    if df.empty:
        st.info("📊 No data found yet. Please start the uploader script to send data.")
        st.markdown("""
        **To get started:**
        1. Run `python uploader.py` on your local machine
        2. Ensure sensors are connected and transmitting
        3. Data should appear here shortly
        """)
        
    else:
        # Debug info
        st.sidebar.write(f"✅ Loaded {len(df)} records")
        
        # Convert timestamp
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors="coerce")
        
        # Get available nodes
        available_nodes = get_available_nodes()
        
        # Sidebar node selection
        st.sidebar.header("📟 Node Selection")
        selected_node = st.sidebar.selectbox(
            "Select Node ID",
            available_nodes,
            help="Choose which sensor node to monitor"
        )
        
        # Filter data for selected node
        if 'id_user' in df.columns:
            node_df = df[df['id_user'] == selected_node].copy()
        else:
            st.warning("No user ID column found in data")
            node_df = df.copy()
        
        if not node_df.empty and 'timestamp' in node_df.columns:
            node_df = node_df.sort_values("timestamp", ascending=True)
        
        # ============ CREATE TABS ============
        tab1, tab2, tab3 = st.tabs(["🩺 Health Vitals", "📡 System & LoRa Status", "📊 Analytics & Trends"])

        # ============ TAB 1: HEALTH VITALS ============
        with tab1:
            st.header(f"Health Vitals - Node: {selected_node}")
            
            if node_df.empty:
                st.warning(f"📭 No data available for node {selected_node}")
                st.info(f"Try selecting a different node from the sidebar. Available nodes: {', '.join(available_nodes)}")
            else:
                # Get latest values
                latest = node_df.iloc[-1]
                
                # Row 1: Current vitals with metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    # Heart Rate
                    hr_value = latest.get('hr', 0)
                    hr_trend = ""
                    if len(node_df) > 1 and 'hr' in node_df.columns:
                        hr_trend = "↑" if node_df['hr'].iloc[-1] > node_df['hr'].iloc[-2] else "↓"
                    
                    st.metric(
                        label="Heart Rate",
                        value=f"{hr_value:.0f} BPM",
                        delta=hr_trend
                    )
                    
                    # Heart rate line chart
                    if len(node_df) > 1 and 'hr' in node_df.columns:
                        fig_hr = go.Figure()
                        fig_hr.add_trace(go.Scatter(
                            x=node_df['timestamp'],
                            y=node_df['hr'],
                            mode='lines',
                            name='Heart Rate',
                            line=dict(color='#FF6B6B', width=3)
                        ))
                        fig_hr.update_layout(
                            title="Heart Rate Trend",
                            height=200,
                            margin=dict(t=30, b=30, l=30, r=30),
                            showlegend=False,
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)'
                        )
                        st.plotly_chart(fig_hr, use_container_width=True, config={'displayModeBar': False})
                
                with col2:
                    # SpO2 Gauge
                    spo2_value = latest.get('spo2', 0)
                    spo2_color = "green" if spo2_value >= 95 else "red" if spo2_value < 90 else "orange"
                    
                    fig_spo2 = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=spo2_value,
                        title={'text': "SpO₂ (%)"},
                        domain={'x': [0, 1], 'y': [0, 1]},
                        gauge={
                            'axis': {'range': [85, 100]},
                            'bar': {'color': spo2_color},
                            'steps': [
                                {'range': [85, 90], 'color': "red"},
                                {'range': [90, 95], 'color': "orange"},
                                {'range': [95, 100], 'color': "green"}
                            ],
                            'threshold': {
                                'line': {'color': "black", 'width': 4},
                                'thickness': 0.75,
                                'value': spo2_value
                            }
                        }
                    ))
                    fig_spo2.update_layout(height=250)
                    st.plotly_chart(fig_spo2, use_container_width=True, config={'displayModeBar': False})
                
                with col3:
                    # Temperature
                    temp_value = latest.get('temp', 0)
                    temp_status = "🟢 Normal" if 36 <= temp_value <= 37.5 else "🟡 Mild" if 37.6 <= temp_value <= 38 else "🔴 Fever"
                    st.metric(
                        label="Body Temperature",
                        value=f"{temp_value:.1f} °C",
                        delta=temp_status
                    )
                    
                    # Temperature trend
                    if len(node_df) > 1 and 'temp' in node_df.columns:
                        fig_temp = go.Figure()
                        fig_temp.add_trace(go.Scatter(
                            x=node_df['timestamp'],
                            y=node_df['temp'],
                            mode='lines',
                            name='Temperature',
                            line=dict(color='#FFA726', width=3)
                        ))
                        # Add fever threshold line
                        fig_temp.add_hline(y=38, line_dash="dash", line_color="red", 
                                         annotation_text="Fever Threshold", 
                                         annotation_position="bottom right")
                        fig_temp.update_layout(
                            title="Temperature Trend",
                            height=200,
                            margin=dict(t=30, b=30, l=30, r=30),
                            showlegend=False,
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)'
                        )
                        st.plotly_chart(fig_temp, use_container_width=True, config={'displayModeBar': False})
                
                with col4:
                    # Activity Classification
                    activity = "Unknown"
                    if all(col in latest for col in ['ax', 'ay', 'az', 'gx', 'gy', 'gz']):
                        activity = classify_activity(
                            latest.get('ax', 0), latest.get('ay', 0), latest.get('az', 0),
                            latest.get('gx', 0), latest.get('gy', 0), latest.get('gz', 0)
                        )
                    
                    # Activity indicator with emoji
                    activity_emoji = {
                        "Resting/Sleeping": "😴",
                        "Light Activity": "🚶‍♂️",
                        "Walking": "🚶‍♂️",
                        "Brisk Walking": "🏃‍♂️",
                        "Running/Vigorous": "🏃‍♂️💨",
                        "Unknown": "❓"
                    }
                    
                    st.markdown(f"""
                    <div style='text-align: center; padding: 20px; border-radius: 10px; background: #f8f9fa;'>
                        <h3 style='margin-bottom: 10px;'>Activity Level</h3>
                        <div style='font-size: 48px; margin: 10px 0;'>{activity_emoji.get(activity, '📊')}</div>
                        <h2 style='color: #4B0082;'>{activity}</h2>
                    </div>
                    """, unsafe_allow_html=True)

        # ============ TAB 2: SYSTEM & LORA STATUS ============
        with tab2:
            st.header(f"System Status - Node: {selected_node}")
            
            if node_df.empty:
                st.warning(f"📭 No system data available for node {selected_node}")
            else:
                latest = node_df.iloc[-1]
                
                # Row 1: Key system metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.info("📡 LoRa Signal Data")
                    st.write("Signal metrics will appear here when available")
                    st.progress(0.75)
                    st.metric("RSSI", "-95 dBm", "Simulated")
                
                with col2:
                    st.info("📦 Packet Delivery")
                    st.write("Packet metrics will appear here when available")
                    st.progress(0.92)
                    st.metric("Delivery Rate", "92%", "Simulated")
                
                with col3:
                    st.info("🔋 Battery Status")
                    st.write("Battery data will appear here when available")
                    st.progress(0.65)
                    st.metric("Battery", "65%", "Simulated")
                    
                    # Latency calculation
                    if len(node_df) > 1 and 'timestamp' in node_df.columns:
                        timestamps = node_df['timestamp'].tail(10)
                        time_diffs = timestamps.diff().dropna()
                        avg_latency = time_diffs.mean().total_seconds() if not time_diffs.empty else 0
                        st.metric(
                            label="Update Interval",
                            value=f"{avg_latency:.1f} sec",
                            delta="Average"
                        )
                
                # Row 2: System Information
                st.subheader("📋 System Information")
                
                sys_info_col1, sys_info_col2 = st.columns(2)
                
                with sys_info_col1:
                    timestamp_str = latest['timestamp'].strftime("%Y-%m-%d %H:%M:%S") if 'timestamp' in latest else "N/A"
                    st.markdown(f"""
                    ### Node Details
                    - **Node ID:** {selected_node}
                    - **Last Update:** {timestamp_str}
                    - **Data Points:** {len(node_df)}
                    - **Sample Rate:** 1 Hz
                    - **Transmission Power:** 14 dBm
                    - **Frequency Band:** 915 MHz
                    """)
                
                with sys_info_col2:
                    st.markdown("""
                    ### Connection Status
                    - **Gateway Distance:** ~100m (estimated)
                    - **Modulation:** LoRa (SF7, BW125)
                    - **Encryption:** AES-128
                    - **Data Format:** JSON
                    - **Cloud Platform:** Google Cloud
                    - **Storage:** BigQuery
                    """)
                
                # Row 3: Recent Data Points
                st.subheader("📨 Recent Data Points")
                
                # Show available columns
                display_cols = ['timestamp']
                if 'hr' in node_df.columns:
                    display_cols.append('hr')
                if 'spo2' in node_df.columns:
                    display_cols.append('spo2')
                if 'temp' in node_df.columns:
                    display_cols.append('temp')
                if 'humidity' in node_df.columns:
                    display_cols.append('humidity')
                
                log_df = node_df[display_cols].tail(10).copy()
                
                # Format timestamp for display
                if 'timestamp' in log_df.columns:
                    log_df['timestamp'] = log_df['timestamp'].dt.strftime("%H:%M:%S")
                
                st.dataframe(log_df, use_container_width=True)

        # ============ TAB 3: ANALYTICS & TRENDS ============
        with tab3:
            st.header(f"Analytics & Trends - Node: {selected_node}")
            
            if node_df.empty:
                st.warning(f"📭 No analytics data available for node {selected_node}")
            else:
                # Create a clean dataframe for analytics
                analytics_df = node_df.copy()
                
                # Fill NaN values with safe defaults
                numeric_cols = ['hr', 'spo2', 'temp', 'ax', 'ay', 'az', 'gx', 'gy', 'gz']
                for col in numeric_cols:
                    if col in analytics_df.columns:
                        if col == 'hr':
                            analytics_df[col] = analytics_df[col].fillna(72)
                        elif col == 'spo2':
                            analytics_df[col] = analytics_df[col].fillna(98)
                        elif col == 'temp':
                            analytics_df[col] = analytics_df[col].fillna(36.5)
                        else:
                            analytics_df[col] = analytics_df[col].fillna(0)
                
                # Row 1: Summary Metrics
                st.subheader("📊 Summary Statistics")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if 'hr' in analytics_df.columns:
                        hr_clean = analytics_df['hr'].dropna()
                        if not hr_clean.empty:
                            st.metric("Average HR", f"{hr_clean.mean():.1f} BPM")
                            st.metric("Max HR", f"{hr_clean.max():.1f} BPM")
                            st.metric("Min HR", f"{hr_clean.min():.1f} BPM")
                
                with col2:
                    if 'spo2' in analytics_df.columns:
                        spo2_clean = analytics_df['spo2'].dropna()
                        if not spo2_clean.empty:
                            st.metric("Average SpO₂", f"{spo2_clean.mean():.1f}%")
                            st.metric("Min SpO₂", f"{spo2_clean.min():.1f}%")
                            # Safe calculation
                            if not spo2_clean.empty:
                                low_spo2_count = (spo2_clean < 95).sum()
                                st.metric("Low SpO₂ Events", f"{low_spo2_count}")
                
                with col3:
                    if 'temp' in analytics_df.columns:
                        temp_clean = analytics_df['temp'].dropna()
                        if not temp_clean.empty:
                            st.metric("Average Temp", f"{temp_clean.mean():.1f}°C")
                            st.metric("Max Temp", f"{temp_clean.max():.1f}°C")
                            # Safe calculation
                            if not temp_clean.empty:
                                fever_count = (temp_clean > 38).sum()
                                st.metric("Fever Events", f"{fever_count}")
                
                # Row 2: Activity Analysis
                st.subheader("🏃 Activity Analysis")
                
                # Check if motion data is available
                motion_cols = ['ax', 'ay', 'az', 'gx', 'gy', 'gz']
                has_motion_data = all(col in analytics_df.columns for col in motion_cols)
                
                if has_motion_data:
                    try:
                        # Calculate activity
                        analytics_df['activity'] = analytics_df.apply(
                            lambda row: classify_activity(
                                row['ax'], row['ay'], row['az'],
                                row['gx'], row['gy'], row['gz']
                            ), axis=1
                        )
                        
                        # Activity distribution
                        activity_counts = analytics_df['activity'].value_counts()
                        
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            # Simple bar chart instead of stacked area
                            fig_activity = go.Figure(data=[
                                go.Bar(
                                    x=activity_counts.index,
                                    y=activity_counts.values,
                                    marker_color=['#FF9999', '#66B3FF', '#99FF99', '#FFCC99', '#FFD700', '#CCCCCC']
                                )
                            ])
                            fig_activity.update_layout(
                                title="Activity Distribution",
                                xaxis_title="Activity",
                                yaxis_title="Count",
                                height=400
                            )
                            st.plotly_chart(fig_activity, use_container_width=True)
                        
                        with col2:
                            st.write("**Activity Breakdown:**")
                            for activity, count in activity_counts.items():
                                st.write(f"- {activity}: {count}")
                    except Exception as e:
                        st.info("Activity analysis not available")
                else:
                    st.info("Motion data not available for activity analysis")
                
                # Row 3: Data Export
                st.subheader("📥 Export Data")
                
                export_col1, export_col2, export_col3 = st.columns(3)
                
                with export_col1:
                    if st.button("📋 Copy Data", use_container_width=True):
                        st.session_state.clipboard = node_df.to_string()
                        st.success("Data copied!")
                
                with export_col2:
                    # Convert to CSV
                    csv = node_df.to_csv(index=False)
                    st.download_button(
                        label="💾 Download CSV",
                        data=csv,
                        file_name=f"health_data_{selected_node}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                with export_col3:
                    # Simple Excel export
                    try:
                        excel_buffer = BytesIO()
                        node_df.to_excel(excel_buffer, index=False, sheet_name='Health Data')
                        st.download_button(
                            label="📊 Download Excel",
                            data=excel_buffer.getvalue(),
                            file_name=f"health_data_{selected_node}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                    except:
                        st.info("Excel export requires openpyxl")

except Exception as e:
    st.error(f"Error loading dashboard data: {e}")
    
    with st.expander("Debug Information"):
        st.write(f"Error details: {str(e)}")
        st.write(f"Error type: {type(e).__name__}")S