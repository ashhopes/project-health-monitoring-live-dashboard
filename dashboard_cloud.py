import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from google.cloud import bigquery
from google.oauth2 import service_account
from datetime import datetime, timedelta
import time
import pytz

# ============================================================================
# 1. CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="Real-time Health Monitoring with LoRa",
    page_icon="🏥",
    layout="wide"
)

# ✅ CORRECTED TO MATCH YOUR ACTUAL BIGQUERY STRUCTURE
PROJECT_ID = "monitoring-system-with-lora"
DATASET_ID = "realtime_health_monitoring_system_with_lora"
TABLE_ID = "lora_sensor_logs"

# ============================================================================
# 2. BIGQUERY CONNECTION
# ============================================================================
@st.cache_resource
def get_bigquery_client():
    """Initialize BigQuery client with service account from Streamlit secrets"""
    try:
        if "gcp_service_account" in st.secrets:
            st.sidebar.success("🔑 Using: Streamlit secrets")
            credentials = service_account.Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
        else:
            st.error("❌ No credentials found in Streamlit secrets!")
            return None
        
        client = bigquery.Client(
            credentials=credentials,
            project=PROJECT_ID,
            location="asia-southeast1"
        )
        
        # Test connection
        test_query = f"SELECT COUNT(*) as count FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}` LIMIT 1"
        client.query(test_query).result()
        st.sidebar.success(f"✅ Connected to {DATASET_ID}.{TABLE_ID}")
        
        return client
    except Exception as e:
        st.error(f"❌ BigQuery connection failed: {e}")
        return None

# ============================================================================
# 3. DATA FETCHING FUNCTIONS
# ============================================================================
def fetch_latest_data(client, hours=1, limit=500):
    """Fetch latest data from BigQuery with proper timestamp handling"""
    query = f"""
    SELECT 
        ID_user,
        timestamp,
        temp,
        spo2,
        hr,
        ax, ay, az,
        gx, gy, gz,
        humidity,
        activity
    FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
    WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {hours} HOUR)
    ORDER BY timestamp DESC
    LIMIT {limit}
    """
    
    try:
        df = client.query(query).to_dataframe()
        
        if not df.empty and 'timestamp' in df.columns:
            # Convert timestamp to pandas datetime (UTC aware)
            df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
            
            # Rename ID_user to id_user for consistency
            if 'ID_user' in df.columns:
                df.rename(columns={'ID_user': 'id_user'}, inplace=True)
            
            # Add missing activity_confidence column (default to 1.0)
            if 'activity_confidence' not in df.columns:
                df['activity_confidence'] = 1.0
        
        return df
    except Exception as e:
        st.error(f"❌ Query failed: {e}")
        return pd.DataFrame()

def get_user_list(client):
    """Get list of unique users"""
    query = f"""
    SELECT DISTINCT ID_user
    FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
    WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
    ORDER BY ID_user
    """
    try:
        df = client.query(query).to_dataframe()
        return df['ID_user'].tolist()
    except:
        return []

# ============================================================================
# 4. VISUALIZATION FUNCTIONS
# ============================================================================
def create_vital_signs_chart(df):
    """Create combined chart for HR, SpO2, and Temp"""
    fig = go.Figure()
    
    # Heart Rate
    fig.add_trace(go.Scatter(
        x=df['timestamp'], y=df['hr'],
        name='Heart Rate (BPM)',
        line=dict(color='red', width=2),
        mode='lines+markers'
    ))
    
    # SpO2
    fig.add_trace(go.Scatter(
        x=df['timestamp'], y=df['spo2'],
        name='SpO2 (%)',
        line=dict(color='blue', width=2),
        mode='lines+markers',
        yaxis='y2'
    ))
    
    fig.update_layout(
        title='Vital Signs Over Time',
        xaxis_title='Time',
        yaxis=dict(title='Heart Rate (BPM)', side='left', color='red'),
        yaxis2=dict(title='SpO2 (%)', overlaying='y', side='right', color='blue'),
        height=400,
        hovermode='x unified'
    )
    
    return fig

def create_movement_chart(df):
    """Create 3D visualization of accelerometer data"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['ax'], name='Accel X', line=dict(color='red')))
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['ay'], name='Accel Y', line=dict(color='green')))
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['az'], name='Accel Z', line=dict(color='blue')))
    
    fig.update_layout(
        title='Accelerometer Data (MPU6050)',
        xaxis_title='Time',
        yaxis_title='Acceleration (g)',
        height=400,
        hovermode='x unified'
    )
    
    return fig

def create_activity_distribution(df):
    """Create pie chart for activity distribution"""
    activity_counts = df['activity'].value_counts().reset_index()
    activity_counts.columns = ['activity', 'count']
    
    fig = px.pie(
        activity_counts,
        values='count',
        names='activity',
        title='Activity Distribution',
        hole=0.3
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    
    return fig

# ============================================================================
# 5. MAIN DASHBOARD
# ============================================================================
def main():
    st.title("🏥 Real-time Health Monitoring System with LoRa")
    st.caption("📡 Data from Pico → LoRa → BigQuery → Streamlit")
    
    # Initialize BigQuery client
    client = get_bigquery_client()
    
    if not client:
        st.error("❌ Cannot connect to BigQuery. Check your secrets configuration!")
        return
    
    # ============================================================================
    # SIDEBAR CONTROLS
    # ============================================================================
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Time range selector
        hours = st.selectbox(
            "📅 Time Range",
            options=[1, 6, 12, 24, 48],
            index=0,
            format_func=lambda x: f"Last {x} hour{'s' if x > 1 else ''}"
        )
        
        # Auto-refresh
        st.divider()
        auto_refresh = st.checkbox("🔄 Auto-refresh", value=True)
        refresh_interval = st.slider("Refresh interval (seconds)", 5, 60, 10)
        
        # Manual refresh button
        if st.button("🔄 Refresh Now", use_container_width=True):
            st.rerun()
        
        # User filter
        st.divider()
        users = get_user_list(client)
        if users:
            selected_user = st.selectbox("👤 Select User", ["All Users"] + users)
        else:
            selected_user = "All Users"
        
        st.divider()
        current_time = datetime.now(pytz.UTC)
        st.caption(f"🕐 Last updated: {current_time.strftime('%H:%M:%S UTC')}")
    
    # ============================================================================
    # FETCH DATA
    # ============================================================================
    with st.spinner("📊 Loading data from BigQuery..."):
        df = fetch_latest_data(client, hours=hours, limit=500)
    
    if df.empty:
        st.warning("⚠️ No data found in the selected time range.")
        st.info(f"""
        **Troubleshooting:**
        1. Check if data exists in BigQuery
        2. Verify your upload script is running
        3. Try increasing time range to 24 hours
        """)
        return
    
    # Filter by user if selected
    if selected_user != "All Users":
        df = df[df['id_user'] == selected_user]
        if df.empty:
            st.warning(f"⚠️ No data found for user: {selected_user}")
            return
    
    # ============================================================================
    # METRICS CARDS
    # ============================================================================
    latest = df.iloc[0]  # Most recent reading
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("👤 User ID", latest['id_user'])
    
    with col2:
        hr_value = int(latest['hr'])
        hr_status = "🟢" if 60 <= hr_value <= 100 else "🔴"
        st.metric("❤️ Heart Rate", f"{hr_value} BPM", help=f"{hr_status} Normal: 60-100 BPM")
    
    with col3:
        spo2_value = int(latest['spo2'])
        spo2_status = "🟢" if spo2_value >= 95 else "🔴"
        st.metric("💨 SpO2", f"{spo2_value}%", help=f"{spo2_status} Normal: ≥95%")
    
    with col4:
        temp_value = float(latest['temp'])
        temp_status = "🟢" if 36.1 <= temp_value <= 37.2 else "🔴"
        st.metric("🌡️ Temperature", f"{temp_value:.1f}°C", help=f"{temp_status} Normal: 36.1-37.2°C")
    
    with col5:
        activity = str(latest['activity'])
        st.metric("🏃 Activity", activity)
    
    st.divider()
    
    # ============================================================================
    # CHARTS
    # ============================================================================
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Vital Signs",
        "🏃 Movement",
        "🌡️ Environment",
        "📊 Activity Analysis"
    ])
    
    with tab1:
        st.plotly_chart(create_vital_signs_chart(df), use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            fig_hr = px.line(df, x='timestamp', y='hr', title='Heart Rate Trend')
            st.plotly_chart(fig_hr, use_container_width=True)
        
        with col2:
            fig_temp = px.line(df, x='timestamp', y='temp', title='Temperature Trend')
            st.plotly_chart(fig_temp, use_container_width=True)
    
    with tab2:
        st.plotly_chart(create_movement_chart(df), use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            fig_gx = px.line(df, x='timestamp', y=['gx', 'gy', 'gz'], title='Gyroscope Data')
            st.plotly_chart(fig_gx, use_container_width=True)
        
        with col2:
            recent_df = df.head(50)
            fig_3d = px.scatter_3d(recent_df, x='ax', y='ay', z='az',
                                   color='activity', title='3D Movement Pattern')
            st.plotly_chart(fig_3d, use_container_width=True)
    
    with tab3:
        col1, col2 = st.columns(2)
        
        with col1:
            fig_hum = px.line(df, x='timestamp', y='humidity', title='Humidity Over Time')
            st.plotly_chart(fig_hum, use_container_width=True)
        
        with col2:
            fig_env = go.Figure()
            fig_env.add_trace(go.Scatter(x=df['timestamp'], y=df['temp'],
                                        name='Temperature', yaxis='y'))
            fig_env.add_trace(go.Scatter(x=df['timestamp'], y=df['humidity'],
                                        name='Humidity', yaxis='y2'))
            fig_env.update_layout(
                title='Temperature & Humidity',
                yaxis=dict(title='Temp (°C)'),
                yaxis2=dict(title='Humidity (%)', overlaying='y', side='right')
            )
            st.plotly_chart(fig_env, use_container_width=True)
    
    with tab4:
        col1, col2 = st.columns(2)
        
        with col1:
            st.plotly_chart(create_activity_distribution(df), use_container_width=True)
        
        with col2:
            fig_timeline = px.scatter(df, x='timestamp', y='activity',
                                     color='activity', title='Activity Timeline', height=400)
            st.plotly_chart(fig_timeline, use_container_width=True)
        
        st.subheader("📊 Activity Statistics")
        activity_stats = df.groupby('activity').agg({
            'hr': 'mean',
            'temp': 'mean',
        }).round(2)
        activity_stats.columns = ['Avg HR', 'Avg Temp']
        st.dataframe(activity_stats, use_container_width=True)
    
    # ============================================================================
    # RAW DATA TABLE
    # ============================================================================
    with st.expander("📋 View Raw Data"):
        st.dataframe(
            df[['timestamp', 'id_user', 'activity', 'hr', 'spo2', 'temp', 
                'humidity', 'ax', 'ay', 'az']].head(100),
            use_container_width=True,
            hide_index=True
        )
        
        st.download_button(
            label="📥 Download CSV",
            data=df.to_csv(index=False).encode('utf-8'),
            file_name=f"health_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    # ============================================================================
    # SYSTEM STATUS - FIXED TIMESTAMP COMPARISON
    # ============================================================================
    st.divider()
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info(f"📊 Total Records: {len(df)}")
    
    with col2:
        if not df.empty:
            # FIXED: Proper timezone-aware comparison
            current_time = datetime.now(pytz.UTC)
            latest_timestamp = df['timestamp'].max()
            
            # Ensure both are timezone-aware
            if latest_timestamp.tzinfo is None:
                latest_timestamp = latest_timestamp.replace(tzinfo=pytz.UTC)
            
            time_diff = (current_time - latest_timestamp).total_seconds()
            
            if time_diff < 60:
                st.success(f"✅ Live: {time_diff:.0f}s ago")
            else:
                st.warning(f"⚠️ Last update: {time_diff/60:.0f}m ago")
    
    with col3:
        st.info(f"👥 Active Users: {df['id_user'].nunique()}")
    
    # ============================================================================
    # AUTO-REFRESH
    # ============================================================================
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()

if __name__ == "__main__":
    main()