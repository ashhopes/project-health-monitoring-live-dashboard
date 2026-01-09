# dashboard_cloud.py
"""
Live Health Monitoring Dashboard with LoRa
Streamlit Cloud Version - NO SERIAL NEEDED
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
import time
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

# ================ GET AVAILABLE COLUMNS ================
@st.cache_data(ttl=300)
def get_table_columns():
    """Get list of columns in the table"""
    try:
        # Try a simple query first
        sample_query = f"SELECT * FROM `{table_id}` LIMIT 1"
        df = client.query(sample_query).to_dataframe()
        return list(df.columns)
    except Exception as e:
        st.error(f"Error getting columns: {e}")
        # Return the columns we know exist
        return ["ID_user", "timestamp", "temp", "humidity", "spo2", "hr", "ax", "ay", "az", "gx", "gy", "gz", "ir", "red", "T", "H"]

# Get available columns
available_cols = get_table_columns()
st.sidebar.write(f"📊 Found {len(available_cols)} columns")

# ================ FETCH LATEST DATA ================
@st.cache_data(ttl=30)
def fetch_latest(n=100):
    """Fetch latest data from BigQuery"""
    
    # Based on your columns, we need to use "ID_user" not "id_user"
    # Your columns: ["ID_user", "timestamp", "temp", "humidity", "spo2", "hr", "ax", "ay", "az", "gx", "gy", "gz", "ir", "red", "T", "H"]
    
    # Select all relevant columns
    columns_to_select = []
    
    # Essential columns (using exact names from your table)
    if "ID_user" in available_cols:
        columns_to_select.append("ID_user")
    if "timestamp" in available_cols:
        columns_to_select.append("timestamp")
    
    # Vital signs
    for col in ["temp", "spo2", "hr"]:
        if col in available_cols:
            columns_to_select.append(col)
    
    # Motion data
    for col in ["ax", "ay", "az", "gx", "gy", "gz"]:
        if col in available_cols:
            columns_to_select.append(col)
    
    # PPG data
    for col in ["ir", "red", "humidity"]:
        if col in available_cols:
            columns_to_select.append(col)
    
    # Additional columns (T and H might be temperature and humidity duplicates)
    for col in ["T", "H"]:
        if col in available_cols:
            columns_to_select.append(col)
    
    columns_str = ", ".join(columns_to_select)
    
    query = f"""
        SELECT {columns_str}
        FROM `{table_id}`
        ORDER BY timestamp DESC
        LIMIT {n}
    """
    
    try:
        df = client.query(query).to_dataframe()
        
        # Standardize column names (convert "ID_user" to "id_user" for consistency)
        if "ID_user" in df.columns:
            df = df.rename(columns={"ID_user": "id_user"})
        
        return df
    except Exception as e:
        st.error(f"Query error: {e}")
        
        # Try a simpler fallback query
        fallback_query = f"""
            SELECT ID_user as id_user, timestamp, temp, spo2, hr
            FROM `{table_id}`
            ORDER BY timestamp DESC
            LIMIT {n}
        """
        try:
            return client.query(fallback_query).to_dataframe()
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
        # Use the actual column name from your table
        query = f"""
            SELECT DISTINCT ID_user as id_user
            FROM `{table_id}`
            WHERE ID_user IS NOT NULL
            ORDER BY ID_user
        """
        result = client.query(query).to_dataframe()
        
        if result.empty:
            return ["user_001", "user_002"]
        
        return result['id_user'].tolist()
    except Exception as e:
        st.sidebar.error(f"Error getting nodes: {e}")
        # Fallback
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
        # Debug: Show what columns we got
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
        
        # Create tabs
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
                    
                    # Activity history
                    if len(node_df) > 1 and all(col in node_df.columns for col in ['ax', 'ay', 'az', 'gx', 'gy', 'gz']):
                        activity_history = []
                        for i, row in node_df.tail(10).iterrows():
                            act = classify_activity(
                                row.get('ax', 0), row.get('ay', 0), row.get('az', 0),
                                row.get('gx', 0), row.get('gy', 0), row.get('gz', 0)
                            )
                            activity_history.append(act)
                        
                        st.markdown("**Recent Activity:**")
                        st.write(", ".join(activity_history[-5:]))
                
                # Row 2: Detailed vitals charts
                st.subheader("📈 Detailed Vitals Timeline")
                
                # Check which columns are available for plotting
                plot_hr = 'hr' in node_df.columns
                plot_spo2 = 'spo2' in node_df.columns
                plot_temp = 'temp' in node_df.columns
                
                if plot_hr or plot_spo2 or plot_temp:
                    # Create subplots based on available data
                    num_plots = sum([plot_hr, plot_spo2, plot_temp])
                    fig_combined = make_subplots(
                        rows=num_plots, cols=1,
                        subplot_titles=[title for title, has_data in 
                                       [("Heart Rate (BPM)", plot_hr), 
                                        ("SpO₂ (%)", plot_spo2), 
                                        ("Temperature (°C)", plot_temp)] if has_data],
                        vertical_spacing=0.1,
                        shared_xaxes=True
                    )
                    
                    row = 1
                    if plot_hr:
                        fig_combined.add_trace(
                            go.Scatter(x=node_df['timestamp'], y=node_df['hr'], 
                                      mode='lines', name='HR', line=dict(color='#FF6B6B')),
                            row=row, col=1
                        )
                        fig_combined.add_hline(y=120, row=row, col=1, line_dash="dash", 
                                              line_color="red", annotation_text="High HR")
                        row += 1
                    
                    if plot_spo2:
                        fig_combined.add_trace(
                            go.Scatter(x=node_df['timestamp'], y=node_df['spo2'], 
                                      mode='lines', name='SpO2', line=dict(color='#4ECDC4')),
                            row=row, col=1
                        )
                        fig_combined.add_hline(y=95, row=row, col=1, line_dash="dash", 
                                              line_color="red", annotation_text="Low SpO2")
                        row += 1
                    
                    if plot_temp:
                        fig_combined.add_trace(
                            go.Scatter(x=node_df['timestamp'], y=node_df['temp'], 
                                      mode='lines', name='Temp', line=dict(color='#FFA726')),
                            row=row, col=1
                        )
                        fig_combined.add_hline(y=38, row=row, col=1, line_dash="dash", 
                                              line_color="red", annotation_text="Fever")
                    
                    fig_combined.update_layout(
                        height=200 * num_plots,
                        showlegend=True,
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)'
                    )
                    
                    st.plotly_chart(fig_combined, use_container_width=True)
                else:
                    st.info("No vital signs data available for plotting")

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
                # Row 1: Activity Timeline (if motion data available)
                st.subheader("🏃 Activity Analysis")
                
                # Check if motion data is available
                motion_cols = ['ax', 'ay', 'az', 'gx', 'gy', 'gz']
                has_motion_data = all(col in node_df.columns for col in motion_cols)
                
                if has_motion_data:
                    try:
                        # Calculate activity for each timestamp
                        # Handle NaN values in motion data
                        node_df['activity'] = node_df.apply(
                            lambda row: classify_activity(
                                row.get('ax', 0) if pd.notna(row.get('ax')) else 0,
                                row.get('ay', 0) if pd.notna(row.get('ay')) else 0,
                                row.get('az', 0) if pd.notna(row.get('az')) else 0,
                                row.get('gx', 0) if pd.notna(row.get('gx')) else 0,
                                row.get('gy', 0) if pd.notna(row.get('gy')) else 0,
                                row.get('gz', 0) if pd.notna(row.get('gz')) else 0
                            ), axis=1
                        )
                        
                        # Activity distribution - filter out NaN values
                        activity_counts = node_df['activity'].dropna().value_counts()
                        
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            if len(node_df) > 1:
                                # Stacked area chart for activity over time
                                activity_categories = ["Resting/Sleeping", "Light Activity", "Walking", "Brisk Walking", "Running/Vigorous", "Unknown"]
                                
                                fig_activity = go.Figure()
                                
                                for activity in activity_categories:
                                    if activity in node_df['activity'].values:
                                        mask = node_df['activity'] == activity
                                        # Convert boolean mask to int, handling NaN
                                        mask_int = mask.fillna(False).astype(int)
                                        fig_activity.add_trace(go.Scatter(
                                            x=node_df['timestamp'],
                                            y=mask_int,
                                            mode='lines',
                                            name=activity,
                                            stackgroup='one',
                                            line=dict(width=0.5)
                                        ))
                                
                                fig_activity.update_layout(
                                    title="Activity Distribution Over Time",
                                    yaxis_title="Activity State",
                                    xaxis_title="Time",
                                    height=400,
                                    plot_bgcolor='rgba(0,0,0,0)'
                                )
                                st.plotly_chart(fig_activity, use_container_width=True)
                        
                        with col2:
                            # Activity pie chart
                            if not activity_counts.empty:
                                fig_pie = go.Figure(data=[go.Pie(
                                    labels=activity_counts.index,
                                    values=activity_counts.values,
                                    hole=.3,
                                    marker_colors=['#FF9999', '#66B3FF', '#99FF99', '#FFCC99', '#FFD700', '#CCCCCC']
                                )])
                                fig_pie.update_layout(
                                    title="Activity Distribution",
                                    height=400
                                )
                                st.plotly_chart(fig_pie, use_container_width=True)
                    except Exception as e:
                        st.info(f"Could not calculate activity: {e}")
                else:
                    st.info("📊 Motion data not available for activity analysis")
                
                # Row 2: Daily Summary
                st.subheader("📅 Vital Signs Summary")
                
                # Create summary metrics - handle NaN values
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if 'hr' in node_df.columns:
                        # Clean HR data - remove NaN values
                        hr_clean = node_df['hr'].dropna()
                        if not hr_clean.empty:
                            st.metric("Average HR", f"{hr_clean.mean():.1f} BPM")
                            st.metric("Max HR", f"{hr_clean.max():.1f} BPM")
                            st.metric("Min HR", f"{hr_clean.min():.1f} BPM")
                        else:
                            st.info("No valid HR data")
                    else:
                        st.info("Heart Rate data not available")
                
                with col2:
                    if 'spo2' in node_df.columns:
                        # Clean SpO2 data
                        spo2_clean = node_df['spo2'].dropna()
                        if not spo2_clean.empty:
                            st.metric("Average SpO₂", f"{spo2_clean.mean():.1f}%")
                            st.metric("Min SpO₂", f"{spo2_clean.min():.1f}%")
                            # Count low SpO2 events - handle NaN
                            low_spo2_count = spo2_clean[spo2_clean < 95].count()
                            st.metric("Low SpO₂ Events", f"{low_spo2_count}")
                        else:
                            st.info("No valid SpO₂ data")
                    else:
                        st.info("SpO₂ data not available")
                
                with col3:
                    if 'temp' in node_df.columns:
                        # Clean temperature data
                        temp_clean = node_df['temp'].dropna()
                        if not temp_clean.empty:
                            st.metric("Average Temp", f"{temp_clean.mean():.1f}°C")
                            st.metric("Max Temp", f"{temp_clean.max():.1f}°C")
                            # Count fever events - handle NaN
                            fever_count = temp_clean[temp_clean > 38].count()
                            st.metric("Fever Events", f"{fever_count}")
                        else:
                            st.info("No valid temperature data")
                    else:
                        st.info("Temperature data not available")
                
                # Row 3: Alerts & Thresholds - FIXED to handle NaN values
                st.subheader("🚨 Alert Summary")
                
                alerts_data = []
                
                # High HR alerts - handle NaN values
                if 'hr' in node_df.columns:
                    # Clean HR data first
                    hr_clean_series = node_df['hr'].dropna()
                    if not hr_clean_series.empty:
                        high_hr_mask = hr_clean_series > 120
                        if high_hr_mask.any():
                            # Get corresponding timestamps
                            high_hr_indices = hr_clean_series[high_hr_mask].index
                            high_hr_times = node_df.loc[high_hr_indices, 'timestamp'].dt.strftime('%H:%M:%S').tolist()
                            alerts_data.append({
                                'Type': 'High Heart Rate',
                                'Count': int(high_hr_mask.sum()),
                                'Details': f"HR > 120 BPM at: {', '.join(high_hr_times[-3:])}",
                                'Severity': 'High'
                            })
                
                # Low SpO2 alerts - handle NaN values
                if 'spo2' in node_df.columns:
                    # Clean SpO2 data first
                    spo2_clean_series = node_df['spo2'].dropna()
                    if not spo2_clean_series.empty:
                        low_spo2_mask = spo2_clean_series < 95
                        if low_spo2_mask.any():
                            # Get corresponding timestamps
                            low_spo2_indices = spo2_clean_series[low_spo2_mask].index
                            low_spo2_times = node_df.loc[low_spo2_indices, 'timestamp'].dt.strftime('%H:%M:%S').tolist()
                            alerts_data.append({
                                'Type': 'Low SpO₂',
                                'Count': int(low_spo2_mask.sum()),
                                'Details': f"SpO₂ < 95% at: {', '.join(low_spo2_times[-3:])}",
                                'Severity': 'Medium'
                            })
                
                # Fever alerts - handle NaN values
                if 'temp' in node_df.columns:
                    # Clean temperature data first
                    temp_clean_series = node_df['temp'].dropna()
                    if not temp_clean_series.empty:
                        fever_mask = temp_clean_series > 38
                        if fever_mask.any():
                            # Get corresponding timestamps
                            fever_indices = temp_clean_series[fever_mask].index
                            fever_times = node_df.loc[fever_indices, 'timestamp'].dt.strftime('%H:%M:%S').tolist()
                            alerts_data.append({
                                'Type': 'Fever',
                                'Count': int(fever_mask.sum()),
                                'Details': f"Temp > 38°C at: {', '.join(fever_times[-3:])}",
                                'Severity': 'High'
                            })
                
                if alerts_data:
                    alerts_df = pd.DataFrame(alerts_data)
                    st.dataframe(alerts_df, use_container_width=True)
                else:
                    st.success("✅ No alerts detected in the current data")
                
                # Row 4: Export & Download
                st.subheader("📥 Export Data")
                
                export_col1, export_col2, export_col3 = st.columns(3)
                
                with export_col1:
                    if st.button("📋 Copy Current Data", use_container_width=True):
                        st.session_state.clipboard = node_df.to_string()
                        st.success("Data copied to clipboard!")
                
                with export_col2:
                    # Convert to CSV
                    csv = node_df.to_csv(index=False)
                    st.download_button(
                        label="💾 Download CSV",
                        data=csv,
                        file_name=f"health_data_{selected_node}_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                with export_col3:
                    # Convert to Excel
                    excel_buffer = BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                        node_df.to_excel(writer, index=False, sheet_name='Health Data')
                        
                        # Add summary sheet
                        summary_data = []
                        if 'hr' in node_df.columns:
                            summary_data.append(['Average HR', f"{node_df['hr'].dropna().mean():.1f} BPM"])
                            summary_data.append(['Max HR', f"{node_df['hr'].dropna().max():.1f} BPM"])
                            summary_data.append(['Min HR', f"{node_df['hr'].dropna().min():.1f} BPM"])
                        
                        if 'spo2' in node_df.columns:
                            summary_data.append(['Average SpO₂', f"{node_df['spo2'].dropna().mean():.1f}%"])
                            summary_data.append(['Min SpO₂', f"{node_df['spo2'].dropna().min():.1f}%"])
                        
                        if 'temp' in node_df.columns:
                            summary_data.append(['Average Temp', f"{node_df['temp'].dropna().mean():.1f}°C"])
                            summary_data.append(['Max Temp', f"{node_df['temp'].dropna().max():.1f}°C"])
                        
                        summary_data.append(['Total Alerts', len(alerts_data)])
                        summary_data.append(['Data Points', len(node_df)])
                        
                        summary_df = pd.DataFrame(summary_data, columns=['Metric', 'Value'])
                        summary_df.to_excel(writer, index=False, sheet_name='Summary')
                    
                    st.download_button(
                        label="📊 Download Excel Report",
                        data=excel_buffer.getvalue(),
                        file_name=f"health_report_{selected_node}_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )

except Exception as e:
    st.error(f"Error loading dashboard data: {e}")
    st.write(f"Details: {str(e)}")
    
    # Show debug information
    with st.expander("Debug Information"):
        st.write("Available columns:", available_cols)
        st.write("Table ID:", table_id)
        st.write("Error type:", type(e).__name__)