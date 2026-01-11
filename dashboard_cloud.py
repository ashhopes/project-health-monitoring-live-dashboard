import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
import plotly.graph_objects as go
import time
import numpy as np
from datetime import datetime, timedelta
import pytz

# --- Page setup ---
st.set_page_config(
    page_title="Live Health Monitoring System with LoRa", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom Elegant Theme ---
st.markdown(
    """
    <style>
    .stApp {
        background-image: url("http://www.umpsa.edu.my/sites/default/files/slider/ZAF_1540-edit.jpg");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }
    .stApp::before {
        content: "";
        position: fixed;
        top: 0; left: 0;
        width: 100%; height: 100%;
        background-color: rgba(255, 255, 255, 0.7);
        z-index: -1;
    }
    .stSidebar { 
        background-color: #f7ede2; 
        padding: 20px !important;
    }
    h1, h2, h3 { 
        font-family: 'Helvetica Neue', sans-serif; 
        font-weight: 600; 
        color: #4B0082;
    }
    .section {
        background: rgba(255, 255, 255, 0.95); 
        padding: 20px; 
        margin-bottom: 20px;
        border-radius: 12px; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
    }
    .subject-box {
        background-color: #ffffff; 
        border: 3px solid #800000;
        border-radius: 12px; 
        padding: 20px; 
        margin-bottom: 25px;
        box-shadow: 0 2px 10px rgba(128, 0, 0, 0.1);
    }
    .sensor-group {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 20px;
        border-radius: 12px;
        border-left: 6px solid #800000;
        margin-bottom: 25px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    .metric-card-small {
        background: white;
        padding: 15px;
        border-radius: 10px;
        border: 2px solid #dee2e6;
        text-align: center;
        margin: 5px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        transition: transform 0.2s;
    }
    .metric-card-small:hover {
        transform: translateY(-3px);
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }
    .user-selector {
        background: white;
        padding: 15px;
        border-radius: 10px;
        border: 2px solid #800000;
        margin-bottom: 20px;
        box-shadow: 0 2px 8px rgba(128, 0, 0, 0.1);
    }
    .stAlert {
        border-radius: 10px;
    }
    .status-good { color: #27ae60; font-weight: bold; }
    .status-warning { color: #f39c12; font-weight: bold; }
    .status-danger { color: #e74c3c; font-weight: bold; }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Header ---
st.markdown("<h1 style='text-align: center; color:#4B0082; margin-bottom: 10px;'>🏥 Live Health Monitoring System with LoRa</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 18px; color:#555; margin-bottom: 30px;'>Real-time monitoring of vital signs and motion data using LoRa transmission</p>", unsafe_allow_html=True)
st.markdown("---")

# --- Sidebar controls ---
with st.sidebar:
    st.markdown("### ⚙️ Dashboard Controls")
    
    # Auto-refresh
    refresh_rate = st.slider(
        "Auto-refresh every (seconds)", 
        0, 120, 30,
        help="Set to 0 to disable auto-refresh"
    )
    
    # Data samples
    n_samples = st.slider(
        "Number of samples to display", 
        50, 1000, 200,
        help="Number of latest records to show"
    )
    
    # Time filter
    hours_filter = st.slider(
        "Show data from last (hours)",
        1, 24, 6,
        help="Filter data by time range"
    )
    
    st.markdown("---")
    
    # User selection
    st.markdown("### 👤 Select User")
    selected_user = st.radio(
        "Active User:",
        ["All Users", "STEMCUBE_001", "STEMCUBE_002", "STEMCUBE_003"],
        index=0,
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # System status
    st.markdown("### 📡 System Status")
    col_status1, col_status2 = st.columns(2)
    
    with col_status1:
        st.metric("Last Update", datetime.now().strftime("%H:%M:%S"))
    
    with col_status2:
        st.metric("Data Points", "Loading...")
    
    st.markdown("---")
    st.markdown("**Project by mOONbLOOM26** 🌙")
    st.caption("UMP Final Year Project 2024")

# --- BigQuery Authentication ---
try:
    # FIX: Using the correct secrets key name "gcp"
    credentials_dict = st.secrets["gcp"]
    
    # Convert to proper service account format
    credentials = service_account.Credentials.from_service_account_info(
        credentials_dict,
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    
    # Initialize BigQuery client
    client = bigquery.Client(
        credentials=credentials,
        project=credentials_dict["project_id"],
        location="asia-southeast1"
    )
    
    st.sidebar.success("✅ Connected to BigQuery")
    
except Exception as e:
    st.error(f"❌ BigQuery Authentication Failed: {str(e)}")
    st.markdown("""
    ### 🔧 Troubleshooting:
    1. Check if your service account has access to BigQuery
    2. Verify the table exists: `lora_health_data_clean2`
    3. Ensure internet connection is available
    """)
    st.stop()

# --- Table reference ---
PROJECT_ID = "monitoring-system-with-lora"
DATASET_ID = "sdp2_live_monitoring_system"
TABLE_ID = "lora_health_data_clean2"
FULL_TABLE_ID = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

# --- First, let's check what columns exist in the table ---
@st.cache_data(ttl=300)
def get_table_schema():
    """Get the actual schema/columns from the BigQuery table"""
    try:
        # Query to get column names
        schema_query = f"""
        SELECT column_name, data_type
        FROM `{PROJECT_ID}.{DATASET_ID}.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = '{TABLE_ID}'
        ORDER BY ordinal_position
        """
        
        schema_df = client.query(schema_query).to_dataframe()
        return schema_df['column_name'].tolist()
    except Exception as e:
        st.warning(f"Could not fetch schema: {e}")
        # Return minimal required columns based on your uploader script
        return ['id_user', 'timestamp', 'temp', 'spo2', 'hr', 'ax', 'ay', 'az', 'gx', 'gy', 'gz']

# Get actual columns
table_columns = get_table_schema()
st.sidebar.info(f"📊 Table has {len(table_columns)} columns")

# --- Fetch latest data with dynamic column selection ---
@st.cache_data(ttl=30, show_spinner="Fetching latest sensor data...")
def fetch_latest_data(n_samples=200, user_filter=None, hours_back=6):
    """
    Fetch latest data from BigQuery with dynamic column selection
    """
    try:
        # Calculate time filter
        time_threshold = datetime.utcnow() - timedelta(hours=hours_back)
        time_threshold_str = time_threshold.strftime('%Y-%m-%d %H:%M:%S')
        
        # Define columns that might exist (check against actual schema)
        possible_columns = [
            'id_user', 'timestamp', 'temp', 'spo2', 'hr', 
            'ax', 'ay', 'az', 'gx', 'gy', 'gz',
            'humidity', 'activity', 'source', 
            'activity_confidence', 'battery_level',
            'movement_magnitude', 'rotation_magnitude',
            'activity_intensity', 'hum'
        ]
        
        # Filter to only include columns that exist in the table
        available_columns = [col for col in possible_columns if col in table_columns]
        
        if not available_columns:
            st.error("No valid columns found in the table!")
            return pd.DataFrame()
        
        # Build SELECT clause with available columns
        select_clause = ", ".join(available_columns)
        
        # Build WHERE clause
        where_clauses = [f"TIMESTAMP(timestamp) >= TIMESTAMP('{time_threshold_str}')"]
        
        if user_filter and user_filter != "All Users":
            where_clauses.append(f"id_user = '{user_filter}'")
        
        where_clause = " AND ".join(where_clauses)
        
        # Build full query
        query = f"""
            SELECT {select_clause}
            FROM `{FULL_TABLE_ID}`
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT {n_samples}
        """
        
        # Execute query
        query_job = client.query(query)
        df = query_job.to_dataframe()
        
        if not df.empty:
            # Clean and process data
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce', utc=True)
                df['timestamp'] = df['timestamp'].dt.tz_convert('Asia/Kuala_Lumpur')
            
            # Sort by timestamp (ascending for plotting)
            if 'timestamp' in df.columns:
                df = df.sort_values('timestamp', ascending=True)
        
        return df
    
    except Exception as e:
        st.error(f"Query Error: {str(e)}")
        
        # Debug: Show the actual query that failed
        with st.expander("🔍 Debug Query Details"):
            st.code(f"""
            Error: {str(e)}
            
            Table: {FULL_TABLE_ID}
            Available columns: {table_columns}
            Selected user: {user_filter}
            Time filter: {hours_back} hours
            """)
        
        return pd.DataFrame()

# --- Auto-refresh logic ---
if refresh_rate > 0:
    time.sleep(refresh_rate)
    st.rerun()

# --- Main Dashboard Content ---
try:
    # Fetch data
    df = fetch_latest_data(n_samples, selected_user if selected_user != "All Users" else None, hours_filter)
    
    if df.empty:
        st.warning("""
        ## ⚠️ No Data Available
        
        The dashboard is connected to BigQuery, but no sensor data was found.
        
        **Please ensure:**
        1. Your LoRa receiver (COM8) is running locally
        2. Data is being uploaded from your batch file
        3. Check if data exists in BigQuery table
        4. Adjust the time filter in the sidebar
        
        **Expected table:** `monitoring-system-with-lora.sdp2_live_monitoring_system.lora_health_data_clean2`
        
        **Available columns:** """ + ", ".join(table_columns))
        
        # Show table preview for debugging
        with st.expander("🔍 Debug: Show Table Preview"):
            try:
                preview_query = f"SELECT * FROM `{FULL_TABLE_ID}` LIMIT 5"
                preview_df = client.query(preview_query).to_dataframe()
                st.write("First 5 rows:", preview_df)
                st.write("Columns:", preview_df.columns.tolist())
            except Exception as e:
                st.write(f"Could not preview table: {e}")
        
        st.stop()
    
    # Update sidebar status
    st.sidebar.metric("Data Points", len(df))
    
    # Add derived metrics if base columns exist
    if all(col in df.columns for col in ['ax', 'ay', 'az']):
        df['movement_magnitude'] = np.sqrt(df['ax']**2 + df['ay']**2 + df['az']**2)
    
    if all(col in df.columns for col in ['gx', 'gy', 'gz']):
        df['rotation_magnitude'] = np.sqrt(df['gx']**2 + df['gy']**2 + df['gz']**2)
    
    # Handle alternative column names
    if 'hum' in df.columns and 'humidity' not in df.columns:
        df['humidity'] = df['hum']
    
    # Get unique users
    unique_users = df['id_user'].dropna().unique().tolist() if 'id_user' in df.columns else []
    
    # --- Tabs ---
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Live Dashboard", "👤 Subjects", "📈 Analytics", "⚙️ System Info"])
    
    # ================ TAB 1: LIVE DASHBOARD ================
    with tab1:
        st.markdown(f"<h2 style='color:#4B0082;'>📊 Live Sensor Dashboard</h2>", unsafe_allow_html=True)
        
        # Dashboard header with stats
        col_header1, col_header2, col_header3, col_header4 = st.columns(4)
        
        with col_header1:
            st.metric("Active Users", len(unique_users))
        
        with col_header2:
            if 'timestamp' in df.columns and not df.empty:
                latest_time = df['timestamp'].max()
                if isinstance(latest_time, pd.Timestamp):
                    st.metric("Latest Data", latest_time.strftime("%H:%M:%S"))
                else:
                    st.metric("Latest Data", "N/A")
            else:
                st.metric("Latest Data", "N/A")
        
        with col_header3:
            if 'timestamp' in df.columns and len(df) > 1:
                time_span = (df['timestamp'].max() - df['timestamp'].min()).total_seconds() / 60
                st.metric("Time Span", f"{time_span:.1f} min")
            else:
                st.metric("Time Span", "N/A")
        
        with col_header4:
            if 'activity' in df.columns:
                activities = df['activity'].dropna().unique()
                st.metric("Activities", len(activities))
            elif 'activity_intensity' in df.columns:
                activities = df['activity_intensity'].dropna().unique()
                st.metric("Activities", len(activities))
            else:
                st.metric("Activities", "N/A")
        
        st.markdown("---")
        
        # SECTION 1: VITAL SIGNS
        st.markdown("<div class='sensor-group'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:#c0392b;'>❤️ Vital Signs Monitor</h3>", unsafe_allow_html=True)
        
        # Vital metrics in cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if 'hr' in df.columns:
                avg_hr = df['hr'].mean()
                if avg_hr == 0:
                    hr_status = "⚪"
                elif 60 <= avg_hr <= 100:
                    hr_status = "🟢"
                elif 50 <= avg_hr <= 110:
                    hr_status = "🟡"
                else:
                    hr_status = "🔴"
                st.markdown(f"""
                    <div class='metric-card-small'>
                        <h4>{hr_status} Heart Rate</h4>
                        <h2>{avg_hr:.0f}</h2>
                        <p>BPM • Normal: 60-100</p>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class='metric-card-small'>
                        <h4>⚪ Heart Rate</h4>
                        <h2>N/A</h2>
                        <p>Data not available</p>
                    </div>
                """, unsafe_allow_html=True)
        
        with col2:
            if 'spo2' in df.columns:
                avg_spo2 = df['spo2'].mean()
                if avg_spo2 == 0:
                    spo2_status = "⚪"
                elif avg_spo2 >= 95:
                    spo2_status = "🟢"
                elif avg_spo2 >= 90:
                    spo2_status = "🟡"
                else:
                    spo2_status = "🔴"
                st.markdown(f"""
                    <div class='metric-card-small'>
                        <h4>{spo2_status} Oxygen Saturation</h4>
                        <h2>{avg_spo2:.0f}%</h2>
                        <p>SpO₂ • Normal: ≥95%</p>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class='metric-card-small'>
                        <h4>⚪ Oxygen Saturation</h4>
                        <h2>N/A</h2>
                        <p>Data not available</p>
                    </div>
                """, unsafe_allow_html=True)
        
        with col3:
            if 'temp' in df.columns:
                avg_temp = df['temp'].mean()
                if avg_temp == 0:
                    temp_status = "⚪"
                elif 36.0 <= avg_temp <= 37.5:
                    temp_status = "🟢"
                elif 35.5 <= avg_temp <= 38.0:
                    temp_status = "🟡"
                else:
                    temp_status = "🔴"
                st.markdown(f"""
                    <div class='metric-card-small'>
                        <h4>{temp_status} Body Temperature</h4>
                        <h2>{avg_temp:.1f}°C</h2>
                        <p>Temp • Normal: 36.5-37.5°C</p>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class='metric-card-small'>
                        <h4>⚪ Body Temperature</h4>
                        <h2>N/A</h2>
                        <p>Data not available</p>
                    </div>
                """, unsafe_allow_html=True)
        
        with col4:
            if 'humidity' in df.columns:
                avg_humidity = df['humidity'].mean()
                st.markdown(f"""
                    <div class='metric-card-small'>
                        <h4>💧 Humidity</h4>
                        <h2>{avg_humidity:.0f}%</h2>
                        <p>Ambient Humidity</p>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class='metric-card-small'>
                        <h4>💧 Humidity</h4>
                        <h2>N/A</h2>
                        <p>Data not available</p>
                    </div>
                """, unsafe_allow_html=True)
        
        # Vital signs graph
        if all(col in df.columns for col in ['timestamp', 'hr', 'spo2']):
            fig_vitals = go.Figure()
            
            # Heart rate trace
            fig_vitals.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df['hr'],
                mode='lines',
                name='Heart Rate',
                line=dict(color='#c0392b', width=3),
                yaxis='y'
            ))
            
            # SpO2 trace
            fig_vitals.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df['spo2'],
                mode='lines',
                name='SpO₂',
                line=dict(color='#27ae60', width=3),
                yaxis='y2'
            ))
            
            # Add temperature if available
            if 'temp' in df.columns:
                fig_vitals.add_trace(go.Scatter(
                    x=df['timestamp'],
                    y=df['temp'],
                    mode='lines',
                    name='Temperature',
                    line=dict(color='#e67e22', width=3),
                    yaxis='y3'
                ))
            
            fig_vitals.update_layout(
                title="<b>Vital Signs Trend</b>",
                xaxis_title="Time",
                yaxis=dict(title="Heart Rate (BPM)", titlefont=dict(color='#c0392b'), tickfont=dict(color='#c0392b')),
                yaxis2=dict(title="SpO₂ (%)", titlefont=dict(color='#27ae60'), tickfont=dict(color='#27ae60'),
                           overlaying='y', side='right'),
                plot_bgcolor='rgba(253, 246, 236, 0.8)',
                paper_bgcolor='rgba(255, 255, 255, 0.9)',
                height=400,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                hovermode='x unified'
            )
            
            if 'temp' in df.columns:
                fig_vitals.update_layout(
                    yaxis3=dict(title="Temp (°C)", titlefont=dict(color='#e67e22'), tickfont=dict(color='#e67e22'),
                               overlaying='y', side='left', position=0.05)
                )
            
            # FIX: Replace use_container_width with width='stretch'
            st.plotly_chart(fig_vitals, width='stretch')
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # SECTION 2: MOVEMENT DATA
        st.markdown("<div class='sensor-group'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:#2980b9;'>📍 Movement & Motion Data</h3>", unsafe_allow_html=True)
        
        # Movement metrics
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            if 'movement_magnitude' in df.columns:
                avg_movement = df['movement_magnitude'].mean()
                st.markdown(f"""
                    <div class='metric-card-small'>
                        <h4>📈 Movement Magnitude</h4>
                        <h2>{avg_movement:.3f}</h2>
                        <p>Total Acceleration</p>
                    </div>
                """, unsafe_allow_html=True)
            elif all(col in df.columns for col in ['ax', 'ay', 'az']):
                avg_movement = np.sqrt(df['ax']**2 + df['ay']**2 + df['az']**2).mean()
                st.markdown(f"""
                    <div class='metric-card-small'>
                        <h4>📈 Movement Magnitude</h4>
                        <h2>{avg_movement:.3f}</h2>
                        <p>Total Acceleration</p>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class='metric-card-small'>
                        <h4>📈 Movement</h4>
                        <h2>N/A</h2>
                        <p>Data not available</p>
                    </div>
                """, unsafe_allow_html=True)
        
        with col6:
            if 'rotation_magnitude' in df.columns:
                avg_rotation = df['rotation_magnitude'].mean()
                st.markdown(f"""
                    <div class='metric-card-small'>
                        <h4>🌀 Rotation Magnitude</h4>
                        <h2>{avg_rotation:.2f}</h2>
                        <p>Total Rotation</p>
                    </div>
                """, unsafe_allow_html=True)
            elif all(col in df.columns for col in ['gx', 'gy', 'gz']):
                avg_rotation = np.sqrt(df['gx']**2 + df['gy']**2 + df['gz']**2).mean()
                st.markdown(f"""
                    <div class='metric-card-small'>
                        <h4>🌀 Rotation Magnitude</h4>
                        <h2>{avg_rotation:.2f}</h2>
                        <p>Total Rotation</p>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class='metric-card-small'>
                        <h4>🌀 Rotation</h4>
                        <h2>N/A</h2>
                        <p>Data not available</p>
                    </div>
                """, unsafe_allow_html=True)
        
        with col7:
            if 'activity' in df.columns:
                most_common_activity = df['activity'].mode()[0] if not df['activity'].mode().empty else "Unknown"
                st.markdown(f"""
                    <div class='metric-card-small'>
                        <h4>🏃 Activity</h4>
                        <h2>{most_common_activity}</h2>
                        <p>Most frequent</p>
                    </div>
                """, unsafe_allow_html=True)
            elif 'activity_intensity' in df.columns:
                most_common_activity = df['activity_intensity'].mode()[0] if not df['activity_intensity'].mode().empty else "Unknown"
                st.markdown(f"""
                    <div class='metric-card-small'>
                        <h4>🏃 Activity Intensity</h4>
                        <h2>{most_common_activity}</h2>
                        <p>Most frequent</p>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class='metric-card-small'>
                        <h4>🏃 Activity</h4>
                        <h2>N/A</h2>
                        <p>Data not available</p>
                    </div>
                """, unsafe_allow_html=True)
        
        with col8:
            if 'battery_level' in df.columns:
                avg_battery = df['battery_level'].mean()
                battery_status = "🟢" if avg_battery >= 3.6 else "🟡" if avg_battery >= 3.3 else "🔴"
                st.markdown(f"""
                    <div class='metric-card-small'>
                        <h4>{battery_status} Battery</h4>
                        <h2>{avg_battery:.2f}V</h2>
                        <p>Device Power</p>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class='metric-card-small'>
                        <h4>🔋 Battery</h4>
                        <h2>N/A</h2>
                        <p>Data not available</p>
                    </div>
                """, unsafe_allow_html=True)
        
        # Movement graphs
        col_graph1, col_graph2 = st.columns(2)
        
        with col_graph1:
            if all(col in df.columns for col in ['timestamp', 'ax', 'ay', 'az']):
                fig_accel = go.Figure()
                
                colors_accel = ['#2980b9', '#16a085', '#8e44ad']
                for i, col in enumerate(['ax', 'ay', 'az']):
                    fig_accel.add_trace(go.Scatter(
                        x=df['timestamp'],
                        y=df[col],
                        mode='lines',
                        name=col.upper(),
                        line=dict(color=colors_accel[i], width=2)
                    ))
                
                fig_accel.update_layout(
                    title="<b>Accelerometer Data</b>",
                    xaxis_title="Time",
                    yaxis_title="Acceleration (g)",
                    height=300,
                    plot_bgcolor='rgba(253, 246, 236, 0.8)',
                    paper_bgcolor='rgba(255, 255, 255, 0.9)',
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                # FIX: Replace use_container_width with width='stretch'
                st.plotly_chart(fig_accel, width='stretch')
            else:
                st.info("Accelerometer data not available")
        
        with col_graph2:
            if all(col in df.columns for col in ['timestamp', 'gx', 'gy', 'gz']):
                fig_gyro = go.Figure()
                
                colors_gyro = ['#e74c3c', '#f39c12', '#9b59b6']
                for i, col in enumerate(['gx', 'gy', 'gz']):
                    fig_gyro.add_trace(go.Scatter(
                        x=df['timestamp'],
                        y=df[col],
                        mode='lines',
                        name=col.upper(),
                        line=dict(color=colors_gyro[i], width=2)
                    ))
                
                fig_gyro.update_layout(
                    title="<b>Gyroscope Data</b>",
                    xaxis_title="Time",
                    yaxis_title="Rotation (°/s)",
                    height=300,
                    plot_bgcolor='rgba(253, 246, 236, 0.8)',
                    paper_bgcolor='rgba(255, 255, 255, 0.9)',
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                # FIX: Replace use_container_width with width='stretch'
                st.plotly_chart(fig_gyro, width='stretch')
            else:
                st.info("Gyroscope data not available")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # SECTION 3: REAL-TIME DATA TABLE
        st.markdown("<div class='sensor-group'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:#8e44ad;'>📋 Recent Sensor Readings</h3>", unsafe_allow_html=True)
        
        # Show latest data
        if not df.empty:
            # Define which columns to show
            display_cols = ['timestamp', 'id_user']
            
            # Add available sensor columns
            sensor_cols = ['hr', 'spo2', 'temp', 'ax', 'ay', 'az', 'gx', 'gy', 'gz']
            display_cols.extend([col for col in sensor_cols if col in df.columns])
            
            # Add activity if available
            if 'activity' in df.columns:
                display_cols.append('activity')
            elif 'activity_intensity' in df.columns:
                display_cols.append('activity_intensity')
            
            # Format timestamp for display
            display_df = df[display_cols].copy()
            if 'timestamp' in display_df.columns:
                display_df['timestamp'] = display_df['timestamp'].dt.strftime('%H:%M:%S')
            
            # Show last 20 records
            # FIX: Replace use_container_width with width='stretch'
            st.dataframe(
                display_df.tail(20).sort_values('timestamp', ascending=False),
                width='stretch',
                height=400
            )
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # ================ TAB 2: SUBJECTS INFO ================
    with tab2:
        st.markdown("<h2 style='color:#4B0082;'>👤 Subject Information</h2>", unsafe_allow_html=True)
        
        if not unique_users:
            st.info("No user data available. Make sure your data includes 'id_user' field.")
        else:
            # Subject biodata (you can expand this with a database)
            biodata = {
                "STEMCUBE_001": {
                    "name": "User 001",
                    "age": 25,
                    "gender": "Male",
                    "weight": 68,
                    "height": 175,
                    "bmi": 22.2,
                    "condition": "Healthy"
                },
                "STEMCUBE_002": {
                    "name": "User 002", 
                    "age": 30,
                    "gender": "Female",
                    "weight": 55,
                    "height": 162,
                    "bmi": 21.0,
                    "condition": "Healthy"
                },
                "STEMCUBE_003": {
                    "name": "User 003",
                    "age": 28,
                    "gender": "Male",
                    "weight": 75,
                    "height": 180,
                    "bmi": 23.1,
                    "condition": "Healthy"
                }
            }
            
            for user_id in unique_users:
                st.markdown(f"<div class='subject-box'>", unsafe_allow_html=True)
                
                # Get user data
                user_data = df[df['id_user'] == user_id].copy()
                bio = biodata.get(user_id, {})
                
                # User header
                col_user1, col_user2 = st.columns([2, 1])
                
                with col_user1:
                    st.markdown(f"### 🧑 {user_id}")
                    if bio:
                        st.markdown(f"""
                            **Basic Info**: {bio.get('name', 'N/A')} • {bio.get('age', 'N/A')} yrs • {bio.get('gender', 'N/A')}
                            <br>**Physical**: {bio.get('weight', 'N/A')} kg • {bio.get('height', 'N/A')} cm • BMI: {bio.get('bmi', 'N/A')}
                            <br>**Condition**: {bio.get('condition', 'N/A')}
                        """, unsafe_allow_html=True)
                
                with col_user2:
                    if not user_data.empty:
                        latest = user_data.iloc[-1]
                        st.markdown(f"""
                            <div style='text-align: center; padding: 10px; background: #f8f9fa; border-radius: 8px;'>
                                <h4>Latest Reading</h4>
                                <p>HR: <span class='status-good'>{latest.get('hr', 'N/A')}</span> BPM</p>
                                <p>SpO₂: <span class='status-good'>{latest.get('spo2', 'N/A')}</span>%</p>
                                <p>Temp: <span class='status-good'>{latest.get('temp', 'N/A')}</span>°C</p>
                            </div>
                        """, unsafe_allow_html=True)
                
                # User-specific graphs
                if len(user_data) > 5 and 'timestamp' in user_data.columns:
                    fig_user = go.Figure()
                    
                    # Add vital signs
                    if 'hr' in user_data.columns:
                        fig_user.add_trace(go.Scatter(
                            x=user_data['timestamp'],
                            y=user_data['hr'],
                            mode='lines',
                            name='Heart Rate',
                            line=dict(color='#c0392b', width=2)
                        ))
                    
                    if 'movement_magnitude' in user_data.columns:
                        fig_user.add_trace(go.Scatter(
                            x=user_data['timestamp'],
                            y=user_data['movement_magnitude'],
                            mode='lines',
                            name='Movement',
                            line=dict(color='#2980b9', width=2),
                            yaxis='y2'
                        ))
                    
                    fig_user.update_layout(
                        title=f"<b>Activity Pattern for {user_id}</b>",
                        xaxis_title="Time",
                        height=300,
                        plot_bgcolor='rgba(253, 246, 236, 0.8)',
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    
                    if 'hr' in user_data.columns:
                        fig_user.update_layout(
                            yaxis=dict(title="Heart Rate (BPM)", titlefont=dict(color='#c0392b'))
                        )
                    
                    if 'movement_magnitude' in user_data.columns:
                        fig_user.update_layout(
                            yaxis2=dict(title="Movement", titlefont=dict(color='#2980b9'),
                                       overlaying='y', side='right')
                        )
                    
                    # FIX: Replace use_container_width with width='stretch'
                    st.plotly_chart(fig_user, width='stretch')
                
                # User statistics
                if not user_data.empty:
                    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
                    
                    with col_stat1:
                        if 'hr' in user_data.columns:
                            avg_hr_user = user_data['hr'].mean()
                            st.metric("Avg HR", f"{avg_hr_user:.0f} BPM")
                        else:
                            st.metric("Avg HR", "N/A")
                    
                    with col_stat2:
                        if 'spo2' in user_data.columns:
                            avg_spo2_user = user_data['spo2'].mean()
                            st.metric("Avg SpO₂", f"{avg_spo2_user:.0f}%")
                        else:
                            st.metric("Avg SpO₂", "N/A")
                    
                    with col_stat3:
                        records_count = len(user_data)
                        st.metric("Records", records_count)
                    
                    with col_stat4:
                        if 'activity' in user_data.columns:
                            unique_acts = user_data['activity'].nunique()
                            st.metric("Activities", unique_acts)
                        else:
                            st.metric("Activities", "N/A")
                
                st.markdown("</div>", unsafe_allow_html=True)
    
    # ================ TAB 3: ANALYTICS ================
    with tab3:
        st.markdown("<h2 style='color:#4B0082;'>📈 Advanced Analytics</h2>", unsafe_allow_html=True)
        
        if len(df) < 10:
            st.warning("Need more data points for analytics (minimum 10 records)")
        else:
            # Correlation matrix
            st.markdown("<div class='section'>", unsafe_allow_html=True)
            st.markdown("<h3>🔗 Sensor Correlations</h3>", unsafe_allow_html=True)
            
            # Select numeric columns for correlation
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            
            # Filter to columns that likely have meaningful correlations
            correlation_cols = [col for col in ['hr', 'spo2', 'temp', 'ax', 'ay', 'az', 'gx', 'gy', 'gz', 
                                               'movement_magnitude', 'rotation_magnitude', 'humidity'] 
                               if col in numeric_cols and col in df.columns]
            
            if len(correlation_cols) > 2:
                corr_matrix = df[correlation_cols].corr()
                
                fig_corr = go.Figure(data=go.Heatmap(
                    z=corr_matrix.values,
                    x=corr_matrix.columns,
                    y=corr_matrix.columns,
                    colorscale='RdBu',
                    zmin=-1,
                    zmax=1,
                    text=corr_matrix.round(2).values,
                    texttemplate='%{text}',
                    textfont={"size": 10},
                    hoverongaps=False
                ))
                
                fig_corr.update_layout(
                    title="<b>Sensor Correlation Matrix</b>",
                    height=500,
                    xaxis_title="Sensors",
                    yaxis_title="Sensors",
                    plot_bgcolor='rgba(253, 246, 236, 0.8)',
                    paper_bgcolor='rgba(255, 255, 255, 0.9)'
                )
                
                # FIX: Replace use_container_width with width='stretch'
                st.plotly_chart(fig_corr, width='stretch')
            else:
                st.info("Need at least 3 numeric sensors for correlation analysis")
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Statistical summary
            st.markdown("<div class='section'>", unsafe_allow_html=True)
            st.markdown("<h3>📊 Statistical Summary</h3>", unsafe_allow_html=True)
            
            if numeric_cols:
                # Filter to meaningful columns
                summary_cols = [col for col in numeric_cols if col in ['hr', 'spo2', 'temp', 'ax', 'ay', 'az', 
                                                                      'gx', 'gy', 'gz', 'humidity', 
                                                                      'movement_magnitude', 'rotation_magnitude']]
                
                if summary_cols:
                    summary_df = df[summary_cols].describe().round(3)
                    # FIX: Replace use_container_width with width='stretch'
                    st.dataframe(summary_df, width='stretch')
                else:
                    st.info("No standard sensor columns available for statistics")
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Distribution plots
            st.markdown("<div class='section'>", unsafe_allow_html=True)
            st.markdown("<h3>📉 Sensor Distributions</h3>", unsafe_allow_html=True)
            
            if not df.empty:
                # Select key sensors for distribution
                dist_cols = [col for col in ['hr', 'ax', 'gx', 'temp', 'spo2'] if col in df.columns]
                
                if dist_cols:
                    cols_per_row = min(3, len(dist_cols))
                    cols = st.columns(cols_per_row)
                    
                    for idx, sensor in enumerate(dist_cols):
                        if idx < len(cols):
                            with cols[idx]:
                                # Determine color based on sensor type
                                if sensor == 'hr':
                                    color = '#c0392b'
                                elif sensor in ['ax', 'ay', 'az']:
                                    color = '#2980b9'
                                elif sensor in ['gx', 'gy', 'gz']:
                                    color = '#8e44ad'
                                elif sensor == 'temp':
                                    color = '#e67e22'
                                else:
                                    color = '#27ae60'
                                
                                fig_dist = go.Figure(data=[
                                    go.Histogram(
                                        x=df[sensor].dropna(), 
                                        nbinsx=20, 
                                        marker_color=color,
                                        opacity=0.7
                                    )
                                ])
                                
                                fig_dist.update_layout(
                                    height=250, 
                                    title=f"{sensor.upper()} Distribution",
                                    plot_bgcolor='rgba(253, 246, 236, 0.8)',
                                    paper_bgcolor='rgba(255, 255, 255, 0.9)',
                                    showlegend=False
                                )
                                # FIX: Replace use_container_width with width='stretch'
                                st.plotly_chart(fig_dist, width='stretch')
                else:
                    st.info("No sensor data available for distribution plots")
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    # ================ TAB 4: SYSTEM INFO ================
    with tab4:
        st.markdown("<h2 style='color:#4B0082;'>⚙️ System Information</h2>", unsafe_allow_html=True)
        
        col_sys1, col_sys2 = st.columns(2)
        
        with col_sys1:
            st.markdown("<div class='section'>", unsafe_allow_html=True)
            st.markdown("<h3>🔧 System Configuration</h3>", unsafe_allow_html=True)
            
            st.markdown(f"""
            **Data Source:**
            - BigQuery Project: `{PROJECT_ID}`
            - Dataset: `{DATASET_ID}`
            - Table: `{TABLE_ID}`
            
            **Data Flow:**
            1. LoRa Sensors → COM5/7
            2. Master Cube → ML Processing
            3. LoRa Transmission → COM8
            4. Batch Upload → BigQuery
            5. Streamlit Dashboard → Live Display
            
            **Dashboard Settings:**
            - Refresh Rate: Every {refresh_rate} seconds
            - Data Samples: {n_samples} records
            - Time Filter: Last {hours_filter} hours
            - Selected User: {selected_user}
            
            **Available Columns:** {len(table_columns)}
            """)
            
            with st.expander("View all columns"):
                st.write(", ".join(table_columns))
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col_sys2:
            st.markdown("<div class='section'>", unsafe_allow_html=True)
            st.markdown("<h3>📈 Data Statistics</h3>", unsafe_allow_html=True)
            
            if not df.empty and 'timestamp' in df.columns:
                st.metric("Total Records", len(df))
                time_diff = (df['timestamp'].max() - df['timestamp'].min()).total_seconds()/60
                st.metric("Time Range", f"{time_diff:.1f} min")
                
                if time_diff > 0:
                    data_rate = len(df) / time_diff
                    st.metric("Data Rate", f"{data_rate:.1f} rec/min")
                else:
                    st.metric("Data Rate", "N/A")
                
                st.metric("Active Users", len(unique_users))
            else:
                st.info("No timestamp data available")
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Data preview
        st.markdown("<div class='section'>", unsafe_allow_html=True)
        st.markdown("<h3>📋 Raw Data Preview</h3>", unsafe_allow_html=True)
        
        if not df.empty:
            # FIX: Replace use_container_width with width='stretch'
            st.dataframe(df.head(10), width='stretch')
            
            # Data download option
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download Current Data (CSV)",
                data=csv,
                file_name=f"lora_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Connection status
        st.markdown("<div class='section'>", unsafe_allow_html=True)
        st.markdown("<h3>🌐 Connection Status</h3>", unsafe_allow_html=True)
        
        col_conn1, col_conn2, col_conn3 = st.columns(3)
        
        with col_conn1:
            st.success("✅ BigQuery Connected")
            st.caption(f"Project: {PROJECT_ID}")
        
        with col_conn2:
            if len(df) > 0:
                st.success("✅ Data Streaming")
                st.caption(f"{len(df)} records loaded")
            else:
                st.warning("⚠️ No Data")
        
        with col_conn3:
            if refresh_rate > 0:
                st.info("🔄 Auto-refresh Active")
                st.caption(f"Every {refresh_rate} seconds")
            else:
                st.info("⏸️ Manual Refresh")
                st.caption("Refresh via sidebar")
        
        st.markdown("</div>", unsafe_allow_html=True)

except Exception as e:
    st.error(f"❌ Dashboard Error: {str(e)}")
    
    with st.expander("🔍 Error Details"):
        st.code(f"""
        Error Type: {type(e).__name__}
        Error Message: {str(e)}
        
        Current Configuration:
        - Project ID: {PROJECT_ID}
        - Dataset: {DATASET_ID}
        - Table: {TABLE_ID}
        - Table Columns: {table_columns}
        - Selected User: {selected_user}
        - Time Filter: {hours_filter} hours
        - Sample Size: {n_samples}
        """)
    
    st.markdown("""
    ### 🚨 Immediate Actions:
    1. **Check your batch file** is running and uploading data
    2. **Verify BigQuery table** has the expected columns
    3. **Adjust time filter** to see older data
    4. **Try selecting "All Users"** in sidebar
    5. **Check your uploader script** for column names
    """)

# --- Footer ---
st.markdown("---")
st.markdown("<div style='text-align: center; color: #666; font-size: 0.9em;'>", unsafe_allow_html=True)
st.markdown("🏥 **STEMCUBE Health Monitoring System** | 📡 **LoRa Technology** | 🎓 **UMP Final Year Project 2024**")
st.markdown("</div>", unsafe_allow_html=True)