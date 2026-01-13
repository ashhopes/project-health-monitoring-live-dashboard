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
# 1. PAGE CONFIGURATION - BEAUTIFUL THEME
# ============================================================================
st.set_page_config(
    page_title="LoRa Health Monitor",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for beautiful styling
st.markdown("""
<style>
    /* Main background gradient */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Card styling */
    .stMetric {
        background: linear-gradient(135deg, #ffffff 0%, #f5f7fa 100%);
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        border: 1px solid rgba(255,255,255,0.2);
    }
    
    /* Metric label styling */
    .stMetric label {
        font-size: 14px !important;
        font-weight: 600 !important;
        color: #667eea !important;
    }
    
    /* Metric value styling */
    .stMetric [data-testid="stMetricValue"] {
        font-size: 32px !important;
        font-weight: 700 !important;
        color: #2d3748 !important;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    /* Headers */
    h1 {
        color: white !important;
        text-align: center;
        font-weight: 800 !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        padding: 20px 0;
    }
    
    h2, h3 {
        color: white !important;
        font-weight: 700 !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(255,255,255,0.1);
        padding: 10px;
        border-radius: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: rgba(255,255,255,0.2);
        border-radius: 8px;
        color: white;
        font-weight: 600;
        padding: 10px 20px;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #ffffff 0%, #f5f7fa 100%);
        color: #667eea !important;
    }
    
    /* Buttons */
    .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 10px 24px;
        font-weight: 600;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.3);
    }
    
    /* Info boxes */
    .stAlert {
        border-radius: 10px;
        border: none;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(255,255,255,0.1);
        border-radius: 10px;
        color: white !important;
        font-weight: 600;
    }
    
    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 6px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 12px;
        margin: 4px;
    }
    
    .status-live {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
    }
    
    .status-warning {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: white;
    }
    
    .status-error {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# 2. CONFIGURATION
# ============================================================================
PROJECT_ID = "monitoring-system-with-lora"
DATASET_ID = "realtime_health_monitoring_system_with_lora"
TABLE_ID = "lora_sensor_logs"

# ============================================================================
# 3. BIGQUERY CONNECTION
# ============================================================================
@st.cache_resource
def get_bigquery_client():
    """Initialize BigQuery client"""
    try:
        if "gcp_service_account" in st.secrets:
            credentials = service_account.Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
        else:
            st.error("❌ No credentials found")
            return None
        
        client = bigquery.Client(
            credentials=credentials,
            project=PROJECT_ID,
            location="asia-southeast1"
        )
        
        return client
    except Exception as e:
        st.error(f"❌ Connection failed: {e}")
        return None

# ============================================================================
# 4. DATA FETCHING
# ============================================================================
def fetch_latest_data(client, hours=1, limit=500):
    """Fetch data from BigQuery"""
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
        
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
            if 'ID_user' in df.columns:
                df.rename(columns={'ID_user': 'id_user'}, inplace=True)
        
        return df
    except Exception as e:
        st.error(f"Query failed: {e}")
        return pd.DataFrame()

# ============================================================================
# 5. BEAUTIFUL METRIC CARDS
# ============================================================================
def create_metric_card(label, value, unit, icon, status="normal"):
    """Create beautiful metric card"""
    status_colors = {
        "normal": "#10b981",
        "warning": "#f59e0b", 
        "danger": "#ef4444"
    }
    
    color = status_colors.get(status, "#10b981")
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #ffffff 0%, #f5f7fa 100%);
        padding: 24px;
        border-radius: 16px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        border-left: 4px solid {color};
        transition: transform 0.3s ease;
    ">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div>
                <p style="color: #667eea; font-size: 14px; font-weight: 600; margin: 0;">
                    {icon} {label}
                </p>
                <h2 style="color: #2d3748; font-size: 36px; font-weight: 800; margin: 8px 0;">
                    {value}<span style="font-size: 18px; color: #718096;"> {unit}</span>
                </h2>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# 6. BEAUTIFUL CHARTS
# ============================================================================
def create_vital_signs_chart(df):
    """Beautiful vital signs chart"""
    fig = go.Figure()
    
    # Heart Rate
    fig.add_trace(go.Scatter(
        x=df['timestamp'], 
        y=df['hr'],
        name='Heart Rate',
        line=dict(color='#ef4444', width=3),
        fill='tozeroy',
        fillcolor='rgba(239, 68, 68, 0.1)',
        mode='lines'
    ))
    
    # SpO2
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['spo2'],
        name='SpO2',
        line=dict(color='#3b82f6', width=3),
        fill='tozeroy',
        fillcolor='rgba(59, 130, 246, 0.1)',
        mode='lines',
        yaxis='y2'
    ))
    
    fig.update_layout(
        title=dict(
            text='📈 Vital Signs Monitor',
            font=dict(size=24, color='white', family='Arial Black')
        ),
        paper_bgcolor='rgba(255,255,255,0.1)',
        plot_bgcolor='rgba(255,255,255,0.05)',
        font=dict(color='white'),
        xaxis=dict(
            title='Time',
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True
        ),
        yaxis=dict(
            title='Heart Rate (BPM)',
            gridcolor='rgba(255,255,255,0.1)',
            side='left',
            range=[40, 120]
        ),
        yaxis2=dict(
            title='SpO2 (%)',
            overlaying='y',
            side='right',
            range=[80, 100]
        ),
        height=450,
        hovermode='x unified',
        legend=dict(
            bgcolor='rgba(255,255,255,0.1)',
            bordercolor='rgba(255,255,255,0.2)',
            borderwidth=1
        )
    )
    
    return fig

def create_activity_gauge(activity):
    """Beautiful activity gauge"""
    activity_colors = {
        "resting": "#10b981",
        "walking": "#3b82f6",
        "jogging": "#f59e0b",
        "running": "#ef4444"
    }
    
    color = activity_colors.get(activity.lower(), "#6366f1")
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=1,
        title={'text': f"🏃 {activity.upper()}", 'font': {'size': 24, 'color': 'white'}},
        gauge={
            'axis': {'range': [None, 1], 'tickwidth': 0, 'tickcolor': "white"},
            'bar': {'color': color},
            'bgcolor': "rgba(255,255,255,0.1)",
            'borderwidth': 2,
            'bordercolor': "white",
            'steps': [
                {'range': [0, 1], 'color': 'rgba(255,255,255,0.05)'}
            ],
        }
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(255,255,255,0.1)',
        height=300,
        font={'color': 'white'}
    )
    
    return fig

def create_3d_motion_chart(df):
    """Beautiful 3D motion visualization"""
    fig = px.scatter_3d(
        df.head(100),
        x='ax', y='ay', z='az',
        color='activity',
        title='🎯 3D Motion Pattern',
        color_discrete_sequence=px.colors.qualitative.Vivid
    )
    
    fig.update_layout(
        paper_bgcolor='rgba(255,255,255,0.1)',
        plot_bgcolor='rgba(255,255,255,0.05)',
        font=dict(color='white'),
        height=500,
        scene=dict(
            xaxis=dict(backgroundcolor='rgba(255,255,255,0.05)', gridcolor='rgba(255,255,255,0.1)'),
            yaxis=dict(backgroundcolor='rgba(255,255,255,0.05)', gridcolor='rgba(255,255,255,0.1)'),
            zaxis=dict(backgroundcolor='rgba(255,255,255,0.05)', gridcolor='rgba(255,255,255,0.1)')
        )
    )
    
    return fig

# ============================================================================
# 7. MAIN DASHBOARD
# ============================================================================
def main():
    # Header with emoji and gradient
    st.markdown("""
    <h1>
        🏥 REAL-TIME HEALTH MONITORING SYSTEM
        <br><span style="font-size: 18px; font-weight: 400;">Powered by LoRa Technology</span>
    </h1>
    """, unsafe_allow_html=True)
    
    # Initialize client
    client = get_bigquery_client()
    if not client:
        return
    
    # ============================================================================
    # SIDEBAR
    # ============================================================================
    with st.sidebar:
        st.markdown("### ⚙️ CONTROL PANEL")
        
        # Time range
        hours = st.select_slider(
            "📅 Time Range",
            options=[1, 3, 6, 12, 24],
            value=1,
            format_func=lambda x: f"{x}h"
        )
        
        st.divider()
        
        # Auto refresh
        auto_refresh = st.toggle("🔄 Auto Refresh", value=True)
        if auto_refresh:
            refresh_rate = st.slider("Refresh Rate (sec)", 5, 60, 10)
        
        st.divider()
        
        # Manual refresh
        if st.button("🔄 REFRESH NOW", use_container_width=True):
            st.rerun()
        
        st.divider()
        
        # Status
        st.markdown("### 📊 SYSTEM STATUS")
        current_time = datetime.now(pytz.UTC)
        st.markdown(f"**Time:** {current_time.strftime('%H:%M:%S UTC')}")
        
    # ============================================================================
    # FETCH DATA
    # ============================================================================
    with st.spinner("⏳ Loading real-time data..."):
        df = fetch_latest_data(client, hours=hours)
    
    if df.empty:
        st.warning("⚠️ No data available")
        st.info("💡 Make sure your LoRa system is transmitting")
        return
    
    latest = df.iloc[0]
    
    # ============================================================================
    # HERO METRICS
    # ============================================================================
    st.markdown("### 📊 LIVE VITALS")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 20px; border-radius: 15px; text-align: center; color: white;">
            <h3 style="margin: 0; font-size: 16px;">👤 USER</h3>
            <h1 style="margin: 10px 0; font-size: 32px;">{latest['id_user']}</h1>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        hr_val = int(latest['hr'])
        hr_status = "normal" if 60 <= hr_val <= 100 else "warning"
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); 
                    padding: 20px; border-radius: 15px; text-align: center; color: white;">
            <h3 style="margin: 0; font-size: 16px;">❤️ HEART RATE</h3>
            <h1 style="margin: 10px 0; font-size: 32px;">{hr_val}</h1>
            <p style="margin: 0; font-size: 14px;">BPM</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        spo2_val = int(latest['spo2'])
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); 
                    padding: 20px; border-radius: 15px; text-align: center; color: white;">
            <h3 style="margin: 0; font-size: 16px;">💨 SPO2</h3>
            <h1 style="margin: 10px 0; font-size: 32px;">{spo2_val}</h1>
            <p style="margin: 0; font-size: 14px;">%</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        temp_val = float(latest['temp'])
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); 
                    padding: 20px; border-radius: 15px; text-align: center; color: white;">
            <h3 style="margin: 0; font-size: 16px;">🌡️ TEMP</h3>
            <h1 style="margin: 10px 0; font-size: 32px;">{temp_val:.1f}</h1>
            <p style="margin: 0; font-size: 14px;">°C</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        activity_val = str(latest['activity'])
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                    padding: 20px; border-radius: 15px; text-align: center; color: white;">
            <h3 style="margin: 0; font-size: 16px;">🏃 ACTIVITY</h3>
            <h1 style="margin: 10px 0; font-size: 24px;">{activity_val.upper()}</h1>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ============================================================================
    # CHARTS
    # ============================================================================
    tab1, tab2, tab3 = st.tabs(["📈 VITAL SIGNS", "🎯 MOTION ANALYSIS", "📊 STATISTICS"])
    
    with tab1:
        st.plotly_chart(create_vital_signs_chart(df), use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            fig_temp = px.area(df, x='timestamp', y='temp', 
                              title='🌡️ Temperature Trend',
                              color_discrete_sequence=['#f59e0b'])
            fig_temp.update_layout(
                paper_bgcolor='rgba(255,255,255,0.1)',
                plot_bgcolor='rgba(255,255,255,0.05)',
                font=dict(color='white')
            )
            st.plotly_chart(fig_temp, use_container_width=True)
        
        with col2:
            fig_hum = px.area(df, x='timestamp', y='humidity',
                             title='💧 Humidity Trend',
                             color_discrete_sequence=['#3b82f6'])
            fig_hum.update_layout(
                paper_bgcolor='rgba(255,255,255,0.1)',
                plot_bgcolor='rgba(255,255,255,0.05)',
                font=dict(color='white')
            )
            st.plotly_chart(fig_hum, use_container_width=True)
    
    with tab2:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.plotly_chart(create_3d_motion_chart(df), use_container_width=True)
        
        with col2:
            st.plotly_chart(create_activity_gauge(activity_val), use_container_width=True)
            
            # Activity breakdown
            activity_counts = df['activity'].value_counts()
            fig_pie = px.pie(
                values=activity_counts.values,
                names=activity_counts.index,
                title='📊 Activity Distribution',
                color_discrete_sequence=px.colors.qualitative.Vivid
            )
            fig_pie.update_layout(
                paper_bgcolor='rgba(255,255,255,0.1)',
                font=dict(color='white')
            )
            st.plotly_chart(fig_pie, use_container_width=True)
    
    with tab3:
        st.markdown("### 📈 STATISTICAL ANALYSIS")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div style="background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px;">
                <h4 style="color: white;">Total Records</h4>
                <h2 style="color: #10b981;">{len(df)}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            avg_hr = df['hr'].mean()
            st.markdown(f"""
            <div style="background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px;">
                <h4 style="color: white;">Avg Heart Rate</h4>
                <h2 style="color: #ef4444;">{avg_hr:.1f} BPM</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            avg_temp = df['temp'].mean()
            st.markdown(f"""
            <div style="background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px;">
                <h4 style="color: white;">Avg Temperature</h4>
                <h2 style="color: #f59e0b;">{avg_temp:.1f}°C</h2>
            </div>
            """, unsafe_allow_html=True)
    
    # ============================================================================
    # STATUS BAR
    # ============================================================================
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="background: rgba(16, 185, 129, 0.2); padding: 15px; 
                    border-radius: 10px; border-left: 4px solid #10b981;">
            <h4 style="color: white; margin: 0;">✅ System Online</h4>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        current_time = datetime.now(pytz.UTC)
        latest_timestamp = df['timestamp'].max()
        if latest_timestamp.tzinfo is None:
            latest_timestamp = latest_timestamp.replace(tzinfo=pytz.UTC)
        time_diff = (current_time - latest_timestamp).total_seconds()
        
        if time_diff < 60:
            st.markdown(f"""
            <div style="background: rgba(16, 185, 129, 0.2); padding: 15px; 
                        border-radius: 10px; border-left: 4px solid #10b981;">
                <h4 style="color: white; margin: 0;">🔴 LIVE: {time_diff:.0f}s ago</h4>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background: rgba(245, 158, 11, 0.2); padding: 15px; 
                        border-radius: 10px; border-left: 4px solid #f59e0b;">
                <h4 style="color: white; margin: 0;">⏱️ Updated: {time_diff/60:.0f}m ago</h4>
            </div>
            """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="background: rgba(59, 130, 246, 0.2); padding: 15px; 
                    border-radius: 10px; border-left: 4px solid #3b82f6;">
            <h4 style="color: white; margin: 0;">👥 Users: {df['id_user'].nunique()}</h4>
        </div>
        """, unsafe_allow_html=True)
    
    # ============================================================================
    # AUTO REFRESH
    # ============================================================================
    if auto_refresh:
        time.sleep(refresh_rate)
        st.rerun()

if __name__ == "__main__":
    main()