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
# 1. PAGE CONFIGURATION - MUJI MINIMALIST STYLE
# ============================================================================
st.set_page_config(
    page_title="Health Monitor | UMPSA",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# 2. UMPSA BACKGROUND IMAGE FROM URL
# ============================================================================
UMPSA_IMAGE_URL = "http://www.umpsa.edu.my/sites/default/files/slider/ZAF_1540-edit.jpg"

st.markdown(f"""
<style>
    /* MUJI PHILOSOPHY: 無印良品 - Natural, Simple, Essential */
    
    /* Main background with UMPSA image URL */
    .main {{
        background-image: linear-gradient(rgba(255, 255, 255, 0.85), rgba(255, 255, 255, 0.85)), 
                          url('{UMPSA_IMAGE_URL}');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        background-repeat: no-repeat;
    }}
    
    /* Clean white cards with glassmorphism */
    .stMetric {{
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        padding: 24px;
        border-radius: 8px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        border: 1px solid rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }}
    
    .stMetric:hover {{
        box-shadow: 0 4px 16px rgba(0,0,0,0.12);
        transform: translateY(-2px);
    }}
    
    /* Typography - MUJI style */
    .stMetric label {{
        font-size: 12px !important;
        font-weight: 500 !important;
        color: #666666 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    
    .stMetric [data-testid="stMetricValue"] {{
        font-size: 32px !important;
        font-weight: 300 !important;
        color: #2c2c2c !important;
    }}
    
    /* Sidebar - Clean minimal */
    [data-testid="stSidebar"] {{
        background: rgba(250, 250, 250, 0.95);
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(0,0,0,0.08);
    }}
    
    [data-testid="stSidebar"] * {{
        color: #2c2c2c !important;
    }}
    
    /* Headers - Minimal typography */
    h1 {{
        color: #2c2c2c !important;
        font-weight: 300 !important;
        font-size: 36px !important;
        letter-spacing: -0.5px;
        margin-bottom: 8px !important;
        text-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }}
    
    h2, h3 {{
        color: #2c2c2c !important;
        font-weight: 400 !important;
    }}
    
    /* Tabs - Minimal design */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0px;
        background-color: transparent;
        border-bottom: 1px solid rgba(0,0,0,0.1);
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background-color: transparent;
        border: none;
        color: #999999;
        font-weight: 400;
        padding: 12px 24px;
        border-bottom: 2px solid transparent;
        font-size: 13px;
        letter-spacing: 0.5px;
    }}
    
    .stTabs [aria-selected="true"] {{
        background-color: transparent;
        color: #2c2c2c !important;
        border-bottom: 2px solid #2c2c2c;
        font-weight: 500;
    }}
    
    /* Buttons - Minimal MUJI style */
    .stButton button {{
        background: #2c2c2c;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 10px 24px;
        font-weight: 400;
        font-size: 13px;
        letter-spacing: 0.5px;
        transition: all 0.3s ease;
    }}
    
    .stButton button:hover {{
        background: #1a1a1a;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }}
    
    /* Download button */
    .stDownloadButton button {{
        background: #2c2c2c;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 10px 24px;
        font-weight: 400;
        font-size: 13px;
        letter-spacing: 0.5px;
    }}
    
    .stDownloadButton button:hover {{
        background: #1a1a1a;
    }}
    
    /* Alert boxes - Enhanced styling */
    .stAlert {{
        border-radius: 8px;
        border: none;
        backdrop-filter: blur(10px);
        animation: slideDown 0.3s ease;
    }}
    
    @keyframes slideDown {{
        from {{
            opacity: 0;
            transform: translateY(-10px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}
    
    /* Remove excessive padding */
    .block-container {{
        padding-top: 2rem;
        padding-bottom: 1rem;
    }}
    
    /* Clean dividers */
    hr {{
        border: none;
        border-top: 1px solid rgba(0,0,0,0.08);
        margin: 1.5rem 0;
    }}
    
    /* Plotly charts background */
    .js-plotly-plot {{
        background: rgba(255, 255, 255, 0.9) !important;
        backdrop-filter: blur(10px);
        border-radius: 8px;
        padding: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# 3. CONFIGURATION
# ============================================================================
PROJECT_ID = "monitoring-system-with-lora"
DATASET_ID = "realtime_health_monitoring_system_with_lora"
TABLE_ID = "lora_sensor_logs"

# ============================================================================
# 4. HEALTH ALERT SYSTEM
# ============================================================================
def analyze_health_status(latest_data):
    """
    Analyze health status and environmental factors
    Returns: (alert_level, alert_messages, recommendations)
    alert_level: 'critical', 'warning', 'info', or None
    """
    alerts = []
    recommendations = []
    alert_level = None
    
    hr = float(latest_data['hr'])
    spo2 = float(latest_data['spo2'])
    temp = float(latest_data['temp'])
    humidity = float(latest_data['humidity'])
    
    # ===== CRITICAL ALERTS =====
    if hr > 120 or hr < 40:
        alerts.append(f"🚨 CRITICAL: Heart Rate {hr:.0f} BPM is {'too high' if hr > 120 else 'too low'}!")
        recommendations.append("Seek immediate medical attention")
        alert_level = 'critical'
    
    if spo2 < 90:
        alerts.append(f"🚨 CRITICAL: SpO2 {spo2:.0f}% is dangerously low!")
        recommendations.append("Immediate oxygen support may be needed")
        alert_level = 'critical'
    
    # ===== WARNING ALERTS =====
    if hr > 100 and hr <= 120:
        alerts.append(f"⚠️ WARNING: Elevated Heart Rate ({hr:.0f} BPM)")
        recommendations.append("Check for physical activity, stress, or environmental factors")
        if alert_level != 'critical':
            alert_level = 'warning'
    
    if hr < 60 and hr >= 40:
        alerts.append(f"⚠️ WARNING: Low Heart Rate ({hr:.0f} BPM)")
        recommendations.append("Monitor for symptoms of dizziness or fatigue")
        if alert_level != 'critical':
            alert_level = 'warning'
    
    if spo2 < 95 and spo2 >= 90:
        alerts.append(f"⚠️ WARNING: Low SpO2 ({spo2:.0f}%)")
        recommendations.append("Ensure adequate ventilation and monitor breathing")
        if alert_level != 'critical':
            alert_level = 'warning'
    
    # ===== ENVIRONMENTAL FACTORS =====
    # High Temperature Impact
    if temp > 30:
        alerts.append(f"🌡️ High Temperature: {temp:.1f}°C may affect vitals")
        recommendations.append("Consider cooling the environment")
        if alert_level is None:
            alert_level = 'info'
    
    # High Humidity Impact
    if humidity > 70:
        alerts.append(f"💧 High Humidity: {humidity:.1f}% may cause discomfort")
        recommendations.append("Increase ventilation or use dehumidifier")
        
        # Check if humidity is affecting HR/SpO2
        if hr > 90 or spo2 < 97:
            alerts.append("⚡ Humidity may be affecting heart rate and oxygen levels")
            recommendations.append("High humidity reduces breathing efficiency")
        
        if alert_level is None:
            alert_level = 'info'
    
    # Low Humidity Impact
    if humidity < 30:
        alerts.append(f"💧 Low Humidity: {humidity:.1f}% detected")
        recommendations.append("Low humidity can cause respiratory irritation")
        if alert_level is None:
            alert_level = 'info'
    
    # Temperature-Humidity Combination (Heat Index)
    if temp > 28 and humidity > 60:
        alerts.append("🔥 High Heat Index: Temperature + Humidity combination detected")
        recommendations.append("Risk of heat stress - ensure hydration and rest")
        if alert_level == 'info':
            alert_level = 'warning'
    
    # Cold Temperature Impact
    if temp < 18:
        alerts.append(f"❄️ Low Temperature: {temp:.1f}°C may affect circulation")
        recommendations.append("Ensure adequate heating and warm clothing")
        if alert_level is None:
            alert_level = 'info'
    
    return alert_level, alerts, recommendations

# ============================================================================
# 5. BIGQUERY CONNECTION
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
# 6. DATA FETCHING
# ============================================================================
def get_user_list(client):
    """Get list of unique users from database"""
    query = f"""
    SELECT DISTINCT ID_user
    FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
    WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
    ORDER BY ID_user
    """
    try:
        df = client.query(query).to_dataframe()
        if not df.empty:
            return ["All Users"] + df['ID_user'].tolist()
        return ["All Users"]
    except:
        return ["All Users"]

def fetch_latest_data(client, hours=1, selected_user="All Users", limit=500):
    """Fetch data from BigQuery with optional user filter"""
    
    if selected_user == "All Users":
        user_filter = ""
    else:
        user_filter = f"AND ID_user = '{selected_user}'"
    
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
    {user_filter}
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
        st.error(f"❌ Query failed: {e}")
        return pd.DataFrame()

# ============================================================================
# 7. MINIMAL CHARTS
# ============================================================================
def create_minimal_line_chart(df, y_col, title, color='#2c2c2c'):
    """Create minimal line chart - MUJI style"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df[y_col],
        mode='lines',
        line=dict(color=color, width=2),
        fill='tozeroy',
        fillcolor=f'rgba(44, 44, 44, 0.03)'
    ))
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color='#2c2c2c', family='Arial'), x=0),
        paper_bgcolor='rgba(255,255,255,0.9)',
        plot_bgcolor='rgba(255,255,255,0.5)',
        font=dict(color='#666666', size=11),
        xaxis=dict(gridcolor='rgba(0,0,0,0.05)', showgrid=True, zeroline=False),
        yaxis=dict(gridcolor='rgba(0,0,0,0.05)', showgrid=True, zeroline=False),
        height=280,
        margin=dict(l=50, r=30, t=40, b=40),
        hovermode='x unified'
    )
    
    return fig

def create_minimal_bar_chart(df):
    """Create minimal activity distribution"""
    activity_counts = df['activity'].value_counts().reset_index()
    activity_counts.columns = ['activity', 'count']
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=activity_counts['activity'],
        y=activity_counts['count'],
        marker=dict(color='#2c2c2c', line=dict(color='#2c2c2c', width=1))
    ))
    
    fig.update_layout(
        title=dict(text='Activity Distribution', font=dict(size=14, color='#2c2c2c'), x=0),
        paper_bgcolor='rgba(255,255,255,0.9)',
        plot_bgcolor='rgba(255,255,255,0.5)',
        font=dict(color='#666666', size=11),
        xaxis=dict(gridcolor='rgba(0,0,0,0.05)', showgrid=False),
        yaxis=dict(gridcolor='rgba(0,0,0,0.05)', showgrid=True),
        height=280,
        margin=dict(l=50, r=30, t=40, b=40)
    )
    
    return fig

# ============================================================================
# 8. MAIN DASHBOARD
# ============================================================================
def main():
    # Header
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("""
        <div style="padding: 15px 0;">
            <h1 style="margin: 0; font-weight: 300; color: #2c2c2c;">
                🏥 Health Monitoring System
            </h1>
            <p style="color: #999999; font-size: 13px; margin-top: 4px; letter-spacing: 0.5px;">
                📡 Real-time LoRa-based Vital Signs Monitor
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="text-align: right; padding: 15px 0;">
            <p style="color: #999999; font-size: 11px; margin: 0; letter-spacing: 0.5px;">🎓 DEVELOPED BY</p>
            <h3 style="margin: 4px 0; font-weight: 500; color: #2c2c2c;">UMPSA</h3>
            <p style="color: #cccccc; font-size: 10px; margin: 0;">Universiti Malaysia Pahang Al-Sultan Abdullah</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
    
    # Initialize client
    client = get_bigquery_client()
    if not client:
        return
    
    # ============================================================================
    # SIDEBAR
    # ============================================================================
    with st.sidebar:
        st.markdown("### ⚙️ Settings")
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.markdown("**👤 Select User to Monitor:**")
        user_list = get_user_list(client)
        selected_user = st.selectbox("User", options=user_list, index=0, label_visibility="collapsed")
        
        if selected_user == "All Users":
            st.info("👥 Monitoring all users")
        else:
            st.success(f"✅ Monitoring: {selected_user}")
        
        st.markdown("---")
        
        st.markdown("**⏱️ Time Range:**")
        hours = st.select_slider("Time Range", options=[1, 3, 6, 12, 24], value=1,
                                 format_func=lambda x: f"{x} hour{'s' if x > 1 else ''}",
                                 label_visibility="collapsed")
        
        st.markdown("---")
        
        st.markdown("**🔄 Auto Refresh:**")
        auto_refresh = st.checkbox("Enable Auto Refresh", value=True, label_visibility="collapsed")
        if auto_refresh:
            refresh_rate = st.slider("⏲️ Refresh Rate (seconds)", 5, 60, 10)
        
        st.markdown("---")
        
        if st.button("🔄 Refresh Now", use_container_width=True):
            st.rerun()
        
        st.markdown("---")
        
        st.markdown("**ℹ️ System Info:**")
        current_time = datetime.now(pytz.UTC)
        st.caption(f"🕐 Updated: {current_time.strftime('%H:%M:%S UTC')}")
    
    # ============================================================================
    # FETCH DATA
    # ============================================================================
    with st.spinner("⏳ Loading data..."):
        df = fetch_latest_data(client, hours=hours, selected_user=selected_user)
    
    if df.empty:
        st.warning(f"⚠️ No data found for {selected_user} in the last {hours} hour(s)")
        st.info("💡 Try selecting 'All Users' or increasing the time range")
        return
    
    latest = df.iloc[0]
    
    # ============================================================================
    # INTELLIGENT HEALTH ALERTS - TOP OF DASHBOARD
    # ============================================================================
    alert_level, alerts, recommendations = analyze_health_status(latest)
    
    if alert_level == 'critical':
        with st.container():
            st.error("🚨 **CRITICAL HEALTH ALERT**")
            for alert in alerts:
                st.markdown(f"**{alert}**")
            st.markdown("**Recommended Actions:**")
            for rec in recommendations:
                st.markdown(f"• {rec}")
            st.markdown("---")
    
    elif alert_level == 'warning':
        with st.container():
            st.warning("⚠️ **HEALTH WARNING**")
            for alert in alerts:
                st.markdown(f"{alert}")
            if recommendations:
                st.markdown("**Recommendations:**")
                for rec in recommendations:
                    st.markdown(f"• {rec}")
            st.markdown("---")
    
    elif alert_level == 'info':
        with st.container():
            st.info("ℹ️ **ENVIRONMENTAL NOTICE**")
            for alert in alerts:
                st.markdown(f"{alert}")
            if recommendations:
                st.markdown("**Suggestions:**")
                for rec in recommendations:
                    st.markdown(f"• {rec}")
            st.markdown("---")
    
    else:
        # All normal - show success message
        st.success("✅ **All vital signs within normal range** | Environment conditions optimal")
        st.markdown("---")
    
    # ============================================================================
    # CSV DOWNLOAD
    # ============================================================================
    col_left, col_right = st.columns([3, 1])
    
    with col_right:
        csv_data = df.to_csv(index=False).encode('utf-8')
        filename = f"health_data_{selected_user}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name=filename,
            mime="text/csv",
            use_container_width=True
        )
    
    with col_left:
        st.markdown(f"""
        <div style="background: rgba(250,250,250,0.9); padding: 12px; border-radius: 4px; 
                    border: 1px solid rgba(0,0,0,0.05); margin-bottom: 10px;">
            <p style="color: #2c2c2c; margin: 0; font-size: 12px;">
                📊 Showing <strong>{len(df)}</strong> records for <strong>{selected_user}</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # ============================================================================
    # METRICS
    # ============================================================================
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.95); backdrop-filter: blur(10px); 
                    padding: 20px; border-radius: 8px; 
                    box-shadow: 0 2px 8px rgba(0,0,0,0.06); border: 1px solid rgba(0,0,0,0.05);">
            <p style="color: #999; font-size: 11px; margin: 0; text-transform: uppercase; 
                      letter-spacing: 1px; font-weight: 500;">👤 USER ID</p>
            <h2 style="color: #2c2c2c; font-size: 24px; margin: 6px 0 0 0; font-weight: 300;">
                {latest['id_user']}
            </h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        hr_val = int(latest['hr'])
        hr_status = "🟢" if 60 <= hr_val <= 100 else "🔴"
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.95); backdrop-filter: blur(10px); 
                    padding: 20px; border-radius: 8px; 
                    box-shadow: 0 2px 8px rgba(0,0,0,0.06); border: 1px solid rgba(0,0,0,0.05);">
            <p style="color: #999; font-size: 11px; margin: 0; text-transform: uppercase; 
                      letter-spacing: 1px; font-weight: 500;">❤️ HEART RATE {hr_status}</p>
            <h2 style="color: #2c2c2c; font-size: 28px; margin: 6px 0 0 0; font-weight: 300;">
                {hr_val}<span style="font-size: 12px; color: #bbb;"> BPM</span>
            </h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        spo2_val = int(latest['spo2'])
        spo2_status = "🟢" if spo2_val >= 95 else "🔴"
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.95); backdrop-filter: blur(10px); 
                    padding: 20px; border-radius: 8px; 
                    box-shadow: 0 2px 8px rgba(0,0,0,0.06); border: 1px solid rgba(0,0,0,0.05);">
            <p style="color: #999; font-size: 11px; margin: 0; text-transform: uppercase; 
                      letter-spacing: 1px; font-weight: 500;">💨 SPO2 {spo2_status}</p>
            <h2 style="color: #2c2c2c; font-size: 28px; margin: 6px 0 0 0; font-weight: 300;">
                {spo2_val}<span style="font-size: 12px; color: #bbb;"> %</span>
            </h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        temp_val = float(latest['temp'])
        temp_status = "🟢" if 36.1 <= temp_val <= 37.2 else "🟡"
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.95); backdrop-filter: blur(10px); 
                    padding: 20px; border-radius: 8px; 
                    box-shadow: 0 2px 8px rgba(0,0,0,0.06); border: 1px solid rgba(0,0,0,0.05);">
            <p style="color: #999; font-size: 11px; margin: 0; text-transform: uppercase; 
                      letter-spacing: 1px; font-weight: 500;">🌡️ TEMPERATURE {temp_status}</p>
            <h2 style="color: #2c2c2c; font-size: 28px; margin: 6px 0 0 0; font-weight: 300;">
                {temp_val:.1f}<span style="font-size: 12px; color: #bbb;"> °C</span>
            </h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        activity_val = str(latest['activity'])
        activity_icons = {"resting": "🛌", "briskwalk": "🚶", "walking": "🚶", "running": "🏃", "jogging": "🏃"}
        activity_icon = activity_icons.get(activity_val.lower(), "🏃")
        
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.95); backdrop-filter: blur(10px); 
                    padding: 20px; border-radius: 8px; 
                    box-shadow: 0 2px 8px rgba(0,0,0,0.06); border: 1px solid rgba(0,0,0,0.05);">
            <p style="color: #999; font-size: 11px; margin: 0; text-transform: uppercase; 
                      letter-spacing: 1px; font-weight: 500;">🎯 ACTIVITY</p>
            <h2 style="color: #2c2c2c; font-size: 20px; margin: 6px 0 0 0; font-weight: 400;">
                {activity_icon} {activity_val.title()}
            </h2>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ============================================================================
    # CHARTS
    # ============================================================================
    tab1, tab2, tab3 = st.tabs(["📈 VITAL SIGNS", "🎯 MOTION DATA", "📊 STATISTICS"])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(create_minimal_line_chart(df, 'hr', '❤️ Heart Rate (BPM)', '#2c2c2c'), use_container_width=True)
        with col2:
            st.plotly_chart(create_minimal_line_chart(df, 'spo2', '💨 SpO2 (%)', '#2c2c2c'), use_container_width=True)
        
        col3, col4 = st.columns(2)
        with col3:
            st.plotly_chart(create_minimal_line_chart(df, 'temp', '🌡️ Temperature (°C)', '#2c2c2c'), use_container_width=True)
        with col4:
            st.plotly_chart(create_minimal_line_chart(df, 'humidity', '💧 Humidity (%)', '#2c2c2c'), use_container_width=True)
    
    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(create_minimal_line_chart(df, 'ax', '📐 Accelerometer X', '#2c2c2c'), use_container_width=True)
        with col2:
            st.plotly_chart(create_minimal_bar_chart(df), use_container_width=True)
    
    with tab3:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div style="background: rgba(250,250,250,0.9); padding: 20px; border-radius: 8px; 
                        border: 1px solid rgba(0,0,0,0.05);">
                <p style="color: #999; font-size: 11px; margin: 0; letter-spacing: 0.5px;">📊 Total Records</p>
                <h2 style="color: #2c2c2c; margin: 8px 0 0 0; font-weight: 300;">{len(df)}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            avg_hr = df['hr'].mean()
            st.markdown(f"""
            <div style="background: rgba(250,250,250,0.9); padding: 20px; border-radius: 8px; 
                        border: 1px solid rgba(0,0,0,0.05);">
                <p style="color: #999; font-size: 11px; margin: 0; letter-spacing: 0.5px;">❤️ Average HR</p>
                <h2 style="color: #2c2c2c; margin: 8px 0 0 0; font-weight: 300;">{avg_hr:.1f} BPM</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            avg_temp = df['temp'].mean()
            st.markdown(f"""
            <div style="background: rgba(250,250,250,0.9); padding: 20px; border-radius: 8px; 
                        border: 1px solid rgba(0,0,0,0.05);">
                <p style="color: #999; font-size: 11px; margin: 0; letter-spacing: 0.5px;">🌡️ Average Temp</p>
                <h2 style="color: #2c2c2c; margin: 8px 0 0 0; font-weight: 300;">{avg_temp:.1f}°C</h2>
            </div>
            """, unsafe_allow_html=True)
    
    # ============================================================================
    # FOOTER
    # ============================================================================
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="background: rgba(250,250,250,0.9); padding: 14px; border-radius: 4px; 
                    border: 1px solid rgba(0,0,0,0.05);">
            <p style="color: #2c2c2c; margin: 0; font-size: 12px;">✅ System Online</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        current_time = datetime.now(pytz.UTC)
        latest_timestamp = df['timestamp'].max()
        if latest_timestamp.tzinfo is None:
            latest_timestamp = latest_timestamp.replace(tzinfo=pytz.UTC)
        time_diff = (current_time - latest_timestamp).total_seconds()
        
        status_text = f"🔴 Live: {time_diff:.0f}s ago" if time_diff < 60 else f"🟡 Updated: {time_diff/60:.0f}m ago"
        
        st.markdown(f"""
        <div style="background: rgba(250,250,250,0.9); padding: 14px; border-radius: 4px; 
                    border: 1px solid rgba(0,0,0,0.05);">
            <p style="color: #2c2c2c; margin: 0; font-size: 12px;">{status_text}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="background: rgba(250,250,250,0.9); padding: 14px; border-radius: 4px; 
                    border: 1px solid rgba(0,0,0,0.05);">
            <p style="color: #2c2c2c; margin: 0; font-size: 12px;">👥 Users: {df['id_user'].nunique()}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Auto refresh
    if auto_refresh:
        time.sleep(refresh_rate)
        st.rerun()

if __name__ == "__main__":
    main()