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
# 1. PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title=" Real-Time Health Monitoring System with LoRa | PS25046",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# 2. COLOR SCHEME - DARK OLIVE & CHAMPAGNE
# ============================================================================
COLORS = {
    'dark_olive': '#556B2F',      # Dark Olive Green
    'olive': '#6B8E23',           # Olive Drab
    'champagne': '#F7E7CE',       # Champagne
    'champagne_dark': '#E8D4B8',  # Darker Champagne
    'olive_light': '#8FBC8F',     # Light Olive
    'text_dark': '#3D3D2B',       # Dark olive text
    'text_light': '#8B8B7A',      # Light olive text
}

# ============================================================================
# 3. UMPSA BACKGROUND WITH NEW COLOR OVERLAY
# ============================================================================
UMPSA_IMAGE_URL = "umpsa.jpg"

st.markdown(f"""
<style>
    /* ============================================
       DARK OLIVE & CHAMPAGNE COLOR SCHEME
       - Sophisticated and Natural
    ============================================ */
    
    .main {{
        background-image: linear-gradient(rgba(247, 231, 206, 0.90), rgba(247, 231, 206, 0.90)), 
                          url('{UMPSA_IMAGE_URL}');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        background-repeat: no-repeat;
    }}
    
    /* Champagne cards with subtle olive accent */
    .stMetric {{
        background: linear-gradient(135deg, rgba(247, 231, 206, 0.98), rgba(232, 212, 184, 0.98));
        backdrop-filter: blur(10px);
        padding: 24px;
        border-radius: 8px;
        box-shadow: 0 2px 12px rgba(85, 107, 47, 0.15);
        border: 1px solid rgba(85, 107, 47, 0.2);
        transition: all 0.3s ease;
    }}
    
    .stMetric:hover {{
        box-shadow: 0 4px 16px rgba(85, 107, 47, 0.25);
        transform: translateY(-2px);
        border: 1px solid rgba(85, 107, 47, 0.3);
    }}
    
    /* Dark Olive Typography */
    .stMetric label {{
        font-size: 12px !important;
        font-weight: 500 !important;
        color: {COLORS['text_light']} !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    
    .stMetric [data-testid="stMetricValue"] {{
        font-size: 32px !important;
        font-weight: 400 !important;
        color: {COLORS['dark_olive']} !important;
    }}
    
    /* Sidebar - Champagne with Olive */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, rgba(247, 231, 206, 0.98), rgba(232, 212, 184, 0.98));
        backdrop-filter: blur(10px);
        border-right: 2px solid rgba(85, 107, 47, 0.2);
    }}
    
    [data-testid="stSidebar"] * {{
        color: {COLORS['dark_olive']} !important;
    }}
    
    /* Headers - Dark Olive */
    h1 {{
        color: {COLORS['dark_olive']} !important;
        font-weight: 400 !important;
        font-size: 36px !important;
        letter-spacing: -0.5px;
        margin-bottom: 8px !important;
        text-shadow: 0 1px 2px rgba(85, 107, 47, 0.1);
    }}
    
    h2, h3 {{
        color: {COLORS['dark_olive']} !important;
        font-weight: 500 !important;
    }}
    
    /* Tabs - Olive accent */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0px;
        background-color: transparent;
        border-bottom: 2px solid rgba(85, 107, 47, 0.2);
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background-color: transparent;
        border: none;
        color: {COLORS['text_light']};
        font-weight: 400;
        padding: 12px 24px;
        border-bottom: 2px solid transparent;
        font-size: 13px;
        letter-spacing: 0.5px;
    }}
    
    .stTabs [aria-selected="true"] {{
        background-color: transparent;
        color: {COLORS['dark_olive']} !important;
        border-bottom: 2px solid {COLORS['dark_olive']};
        font-weight: 600;
    }}
    
    /* Buttons - Dark Olive */
    .stButton button {{
        background: {COLORS['dark_olive']};
        color: {COLORS['champagne']};
        border: none;
        border-radius: 4px;
        padding: 10px 24px;
        font-weight: 500;
        font-size: 13px;
        letter-spacing: 0.5px;
        transition: all 0.3s ease;
    }}
    
    .stButton button:hover {{
        background: {COLORS['olive']};
        box-shadow: 0 2px 8px rgba(85, 107, 47, 0.3);
    }}
    
    /* Download button */
    .stDownloadButton button {{
        background: {COLORS['dark_olive']};
        color: {COLORS['champagne']};
        border: none;
        border-radius: 4px;
        padding: 10px 24px;
        font-weight: 500;
        font-size: 13px;
        letter-spacing: 0.5px;
    }}
    
    .stDownloadButton button:hover {{
        background: {COLORS['olive']};
    }}
    
    /* Alert boxes - Champagne with Olive borders */
    .stAlert {{
        border-radius: 8px;
        border: 2px solid rgba(85, 107, 47, 0.3);
        backdrop-filter: blur(10px);
        animation: slideDown 0.3s ease;
        background: rgba(247, 231, 206, 0.95) !important;
        color: {COLORS['dark_olive']} !important;
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
    
    /* Data table styling - Champagne */
    .stDataFrame {{
        background: rgba(247, 231, 206, 0.98);
        backdrop-filter: blur(10px);
        border-radius: 8px;
        padding: 10px;
        box-shadow: 0 2px 8px rgba(85, 107, 47, 0.1);
        border: 1px solid rgba(85, 107, 47, 0.15);
    }}
    
    .block-container {{
        padding-top: 2rem;
        padding-bottom: 1rem;
    }}
    
    hr {{
        border: none;
        border-top: 2px solid rgba(85, 107, 47, 0.2);
        margin: 1.5rem 0;
    }}
    
    /* Plotly charts - Champagne background */
    .js-plotly-plot {{
        background: rgba(247, 231, 206, 0.95) !important;
        backdrop-filter: blur(10px);
        border-radius: 8px;
        padding: 10px;
        box-shadow: 0 2px 8px rgba(85, 107, 47, 0.1);
        border: 1px solid rgba(85, 107, 47, 0.15);
    }}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# 4. CONFIGURATION
# ============================================================================
PROJECT_ID = "monitoring-system-with-lora"
DATASET_ID = "realtime_health_monitoring_system_with_lora"
TABLE_ID = "lora_sensor_logs"

# ============================================================================
# 5. HEALTH ALERT SYSTEM
# ============================================================================
def analyze_health_status(latest_data):
    """Analyze health status and environmental factors"""
    alerts = []
    recommendations = []
    alert_level = None
    
    hr = float(latest_data['hr'])
    spo2 = float(latest_data['spo2'])
    temp = float(latest_data['temp'])
    humidity = float(latest_data['humidity'])
    
    # CHECK FOR NO FINGER PLACEMENT
    if hr == 0 and spo2 == 0:
        alerts.append("👆 No Finger Detected on Sensor")
        recommendations.append("Place finger on MAX30102 sensor to measure heart rate and SpO2")
        if alert_level is None:
            alert_level = 'info'
    
    # CRITICAL ALERTS (only if measuring)
    if hr > 120 or (hr > 0 and hr < 40):
        alerts.append(f"🚨 CRITICAL: Heart Rate {hr:.0f} BPM is {'too high' if hr > 120 else 'too low'}!")
        recommendations.append("Seek immediate medical attention")
        alert_level = 'critical'
    
    if spo2 > 0 and spo2 < 90:
        alerts.append(f"🚨 CRITICAL: SpO2 {spo2:.0f}% is dangerously low!")
        recommendations.append("Immediate oxygen support may be needed")
        alert_level = 'critical'
    
    # WARNING ALERTS (only if measuring)
    if hr > 100 and hr <= 120:
        alerts.append(f"⚠️ WARNING: Elevated Heart Rate ({hr:.0f} BPM)")
        recommendations.append("Check for physical activity, stress, or environmental factors")
        if alert_level != 'critical':
            alert_level = 'warning'
    
    if hr < 60 and hr > 0 and hr >= 40:
        alerts.append(f"⚠️ WARNING: Low Heart Rate ({hr:.0f} BPM)")
        recommendations.append("Monitor for symptoms of dizziness or fatigue")
        if alert_level != 'critical':
            alert_level = 'warning'
    
    if spo2 > 0 and spo2 < 95 and spo2 >= 90:
        alerts.append(f"⚠️ WARNING: Low SpO2 ({spo2:.0f}%)")
        recommendations.append("Ensure adequate ventilation and monitor breathing")
        if alert_level != 'critical':
            alert_level = 'warning'
    
    # ENVIRONMENTAL FACTORS
    if temp > 30:
        alerts.append(f"🌡️ High Temperature: {temp:.1f}°C may affect vitals")
        recommendations.append("Consider cooling the environment")
        if alert_level is None:
            alert_level = 'info'
    
    if humidity > 70:
        alerts.append(f"💧 High Humidity: {humidity:.1f}% may cause discomfort")
        recommendations.append("Increase ventilation or use dehumidifier")
        
        if hr > 90 or spo2 < 97:
            alerts.append("⚡ Humidity may be affecting heart rate and oxygen levels")
            recommendations.append("High humidity reduces breathing efficiency")
        
        if alert_level is None:
            alert_level = 'info'
    
    if humidity < 30:
        alerts.append(f"💧 Low Humidity: {humidity:.1f}% detected")
        recommendations.append("Low humidity can cause respiratory irritation")
        if alert_level is None:
            alert_level = 'info'
    
    if temp > 28 and humidity > 60:
        alerts.append("🔥 High Heat Index: Temperature + Humidity combination detected")
        recommendations.append("Risk of heat stress - ensure hydration and rest")
        if alert_level == 'info':
            alert_level = 'warning'
    
    if temp < 18:
        alerts.append(f"❄️ Low Temperature: {temp:.1f}°C may affect circulation")
        recommendations.append("Ensure adequate heating and warm clothing")
        if alert_level is None:
            alert_level = 'info'
    
    return alert_level, alerts, recommendations

# ============================================================================
# 6. BIGQUERY CONNECTION
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
# 7. DATA FETCHING
# ============================================================================
def get_user_list(client):
    """Get list of unique users"""
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
    """Fetch data from BigQuery"""
    
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
# 8. CHARTS - DARK OLIVE COLOR SCHEME
# ============================================================================
def create_minimal_line_chart(df, y_col, title, color=COLORS['dark_olive']):
    """Create minimal line chart with dark olive theme"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df[y_col],
        mode='lines',
        line=dict(color=color, width=2),
        fill='tozeroy',
        fillcolor=f'rgba(85, 107, 47, 0.1)'  # Light olive fill
    ))
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color=COLORS['dark_olive'], family='Arial'), x=0),
        paper_bgcolor='rgba(247, 231, 206, 0.95)',
        plot_bgcolor='rgba(247, 231, 206, 0.5)',
        font=dict(color=COLORS['text_light'], size=11),
        xaxis=dict(gridcolor='rgba(85, 107, 47, 0.15)', showgrid=True, zeroline=False),
        yaxis=dict(gridcolor='rgba(85, 107, 47, 0.15)', showgrid=True, zeroline=False),
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
        marker=dict(color=COLORS['dark_olive'], line=dict(color=COLORS['olive'], width=1))
    ))
    
    fig.update_layout(
        title=dict(text='Activity Distribution', font=dict(size=14, color=COLORS['dark_olive']), x=0),
        paper_bgcolor='rgba(247, 231, 206, 0.95)',
        plot_bgcolor='rgba(247, 231, 206, 0.5)',
        font=dict(color=COLORS['text_light'], size=11),
        xaxis=dict(gridcolor='rgba(85, 107, 47, 0.15)', showgrid=False),
        yaxis=dict(gridcolor='rgba(85, 107, 47, 0.15)', showgrid=True),
        height=280,
        margin=dict(l=50, r=30, t=40, b=40)
    )
    
    return fig

# ============================================================================
# 9. MAIN DASHBOARD
# ============================================================================
def main():
    # Header
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"""
        <div style="padding: 15px 0;">
            <h1 style="margin: 0; font-weight: 400; color: {COLORS['dark_olive']};">
                🏥 Health Monitoring System
            </h1>
            <p style="color: {COLORS['text_light']}; font-size: 13px; margin-top: 4px; letter-spacing: 0.5px;">
                📡 Real-time LoRa-based Vital Signs Monitor
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="text-align: right; padding: 15px 0;">
            <p style="color: {COLORS['text_light']}; font-size: 11px; margin: 0; letter-spacing: 0.5px;">🎓 DEVELOPED BY</p>
            <h3 style="margin: 4px 0; font-weight: 600; color: {COLORS['dark_olive']};">UMPSA</h3>
            <p style="color: {COLORS['text_light']}; font-size: 10px; margin: 0;">Universiti Malaysia Pahang Al-Sultan Abdullah</p>
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
        
        st.markdown("**📋 Log Display:**")
        log_limit = st.slider("Number of records to show", 10, 100, 50, step=10)
        
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
        df = fetch_latest_data(client, hours=hours, selected_user=selected_user, limit=500)
    
    if df.empty:
        st.warning(f"⚠️ No data found for {selected_user} in the last {hours} hour(s)")
        st.info("💡 Try selecting 'All Users' or increasing the time range")
        return
    
    latest = df.iloc[0]
    
    # ============================================================================
    # INTELLIGENT HEALTH ALERTS
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
        <div style="background: rgba(247, 231, 206, 0.95); padding: 12px; border-radius: 4px; 
                    border: 1px solid rgba(85, 107, 47, 0.2); margin-bottom: 10px;">
            <p style="color: {COLORS['dark_olive']}; margin: 0; font-size: 12px;">
                📊 Showing <strong>{len(df)}</strong> records for <strong>{selected_user}</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # ============================================================================
    # METRICS - CHAMPAGNE CARDS WITH OLIVE TEXT
    # ============================================================================
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(247, 231, 206, 0.98), rgba(232, 212, 184, 0.98)); 
                    backdrop-filter: blur(10px); padding: 20px; border-radius: 8px; 
                    box-shadow: 0 2px 8px rgba(85, 107, 47, 0.15); border: 1px solid rgba(85, 107, 47, 0.2);">
            <p style="color: {COLORS['text_light']}; font-size: 11px; margin: 0; text-transform: uppercase; 
                      letter-spacing: 1px; font-weight: 500;">👤 USER ID</p>
            <h2 style="color: {COLORS['dark_olive']}; font-size: 24px; margin: 6px 0 0 0; font-weight: 500;">
                {latest['id_user']}
            </h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        hr_val = int(latest['hr'])
        hr_status = "🟢" if 60 <= hr_val <= 100 else "🔴"
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(247, 231, 206, 0.98), rgba(232, 212, 184, 0.98)); 
                    backdrop-filter: blur(10px); padding: 20px; border-radius: 8px; 
                    box-shadow: 0 2px 8px rgba(85, 107, 47, 0.15); border: 1px solid rgba(85, 107, 47, 0.2);">
            <p style="color: {COLORS['text_light']}; font-size: 11px; margin: 0; text-transform: uppercase; 
                      letter-spacing: 1px; font-weight: 500;">❤️ HEART RATE {hr_status}</p>
            <h2 style="color: {COLORS['dark_olive']}; font-size: 28px; margin: 6px 0 0 0; font-weight: 500;">
                {hr_val}<span style="font-size: 12px; color: {COLORS['text_light']};"> BPM</span>
            </h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        spo2_val = int(latest['spo2'])
        spo2_status = "🟢" if spo2_val >= 95 else "🔴"
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(247, 231, 206, 0.98), rgba(232, 212, 184, 0.98)); 
                    backdrop-filter: blur(10px); padding: 20px; border-radius: 8px; 
                    box-shadow: 0 2px 8px rgba(85, 107, 47, 0.15); border: 1px solid rgba(85, 107, 47, 0.2);">
            <p style="color: {COLORS['text_light']}; font-size: 11px; margin: 0; text-transform: uppercase; 
                      letter-spacing: 1px; font-weight: 500;">💨 SPO2 {spo2_status}</p>
            <h2 style="color: {COLORS['dark_olive']}; font-size: 28px; margin: 6px 0 0 0; font-weight: 500;">
                {spo2_val}<span style="font-size: 12px; color: {COLORS['text_light']};"> %</span>
            </h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        temp_val = float(latest['temp'])
        temp_status = "🟢" if 36.1 <= temp_val <= 37.2 else "🟡"
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(247, 231, 206, 0.98), rgba(232, 212, 184, 0.98)); 
                    backdrop-filter: blur(10px); padding: 20px; border-radius: 8px; 
                    box-shadow: 0 2px 8px rgba(85, 107, 47, 0.15); border: 1px solid rgba(85, 107, 47, 0.2);">
            <p style="color: {COLORS['text_light']}; font-size: 11px; margin: 0; text-transform: uppercase; 
                      letter-spacing: 1px; font-weight: 500;">🌡️ TEMPERATURE {temp_status}</p>
            <h2 style="color: {COLORS['dark_olive']}; font-size: 28px; margin: 6px 0 0 0; font-weight: 500;">
                {temp_val:.1f}<span style="font-size: 12px; color: {COLORS['text_light']};"> °C</span>
            </h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        activity_val = str(latest['activity'])
        activity_icons = {"resting": "🛌", "briskwalk": "🚶", "walking": "🚶", "running": "🏃", "jogging": "🏃"}
        activity_icon = activity_icons.get(activity_val.lower(), "🏃")
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(247, 231, 206, 0.98), rgba(232, 212, 184, 0.98)); 
                    backdrop-filter: blur(10px); padding: 20px; border-radius: 8px; 
                    box-shadow: 0 2px 8px rgba(85, 107, 47, 0.15); border: 1px solid rgba(85, 107, 47, 0.2);">
            <p style="color: {COLORS['text_light']}; font-size: 11px; margin: 0; text-transform: uppercase; 
                      letter-spacing: 1px; font-weight: 500;">🎯 ACTIVITY</p>
            <h2 style="color: {COLORS['dark_olive']}; font-size: 20px; margin: 6px 0 0 0; font-weight: 500;">
                {activity_icon} {activity_val.title()}
            </h2>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ============================================================================
    # TABS WITH CHARTS AND LOG TABLE
    # ============================================================================
    tab1, tab2, tab3, tab4 = st.tabs(["📈 VITAL SIGNS", "🎯 MOTION DATA", "📊 STATISTICS", "📋 DATA LOG"])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(create_minimal_line_chart(df, 'hr', '❤️ Heart Rate (BPM)'), use_container_width=True)
        with col2:
            st.plotly_chart(create_minimal_line_chart(df, 'spo2', '💨 SpO2 (%)'), use_container_width=True)
        
        col3, col4 = st.columns(2)
        with col3:
            st.plotly_chart(create_minimal_line_chart(df, 'temp', '🌡️ Temperature (°C)'), use_container_width=True)
        with col4:
            st.plotly_chart(create_minimal_line_chart(df, 'humidity', '💧 Humidity (%)'), use_container_width=True)
    
    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(create_minimal_line_chart(df, 'ax', '📐 Accelerometer X'), use_container_width=True)
        with col2:
            st.plotly_chart(create_minimal_bar_chart(df), use_container_width=True)
    
    with tab3:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div style="background: rgba(247, 231, 206, 0.95); padding: 20px; border-radius: 8px; 
                        border: 1px solid rgba(85, 107, 47, 0.2);">
                <p style="color: {COLORS['text_light']}; font-size: 11px; margin: 0; letter-spacing: 0.5px;">📊 Total Records</p>
                <h2 style="color: {COLORS['dark_olive']}; margin: 8px 0 0 0; font-weight: 500;">{len(df)}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            avg_hr = df['hr'].mean()
            st.markdown(f"""
            <div style="background: rgba(247, 231, 206, 0.95); padding: 20px; border-radius: 8px; 
                        border: 1px solid rgba(85, 107, 47, 0.2);">
                <p style="color: {COLORS['text_light']}; font-size: 11px; margin: 0; letter-spacing: 0.5px;">❤️ Average HR</p>
                <h2 style="color: {COLORS['dark_olive']}; margin: 8px 0 0 0; font-weight: 500;">{avg_hr:.1f} BPM</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            avg_temp = df['temp'].mean()
            st.markdown(f"""
            <div style="background: rgba(247, 231, 206, 0.95); padding: 20px; border-radius: 8px; 
                        border: 1px solid rgba(85, 107, 47, 0.2);">
                <p style="color: {COLORS['text_light']}; font-size: 11px; margin: 0; letter-spacing: 0.5px;">🌡️ Average Temp</p>
                <h2 style="color: {COLORS['dark_olive']}; margin: 8px 0 0 0; font-weight: 500;">{avg_temp:.1f}°C</h2>
            </div>
            """, unsafe_allow_html=True)
    
    with tab4:
        st.markdown("### 📋 Real-time Data Log")
        st.caption(f"Showing latest {log_limit} records")
        
        display_df = df.head(log_limit).copy()
        display_df['timestamp'] = display_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        display_columns = {
            'timestamp': '🕐 Time',
            'id_user': '👤 User',
            'hr': '❤️ HR (BPM)',
            'spo2': '💨 SpO2 (%)',
            'temp': '🌡️ Temp (°C)',
            'humidity': '💧 Humidity (%)',
            'activity': '🎯 Activity',
            'ax': '📐 Accel X',
            'ay': '📐 Accel Y',
            'az': '📐 Accel Z'
        }
        
        display_df = display_df[list(display_columns.keys())].rename(columns=display_columns)
        
        for col in display_df.columns:
            if display_df[col].dtype in ['float64', 'float32']:
                display_df[col] = display_df[col].round(2)
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            height=400
        )
        
        st.markdown("---")
        st.markdown("### 📊 Log Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📋 Records Shown", len(display_df))
        
        with col2:
            time_range = (df['timestamp'].max() - df['timestamp'].min()).total_seconds() / 60
            st.metric("⏱️ Time Span", f"{time_range:.1f} min")
        
        with col3:
            activities = df.head(log_limit)['activity'].nunique()
            st.metric("🎯 Activities", activities)
        
        with col4:
            avg_hr_log = df.head(log_limit)['hr'].mean()
            st.metric("❤️ Avg HR", f"{avg_hr_log:.0f} BPM")
    
    # ============================================================================
    # FOOTER
    # ============================================================================
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div style="background: rgba(247, 231, 206, 0.95); padding: 14px; border-radius: 4px; 
                    border: 1px solid rgba(85, 107, 47, 0.15);">
            <p style="color: {COLORS['dark_olive']}; margin: 0; font-size: 12px;">✅ System Online</p>
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
        <div style="background: rgba(247, 231, 206, 0.95); padding: 14px; border-radius: 4px; 
                    border: 1px solid rgba(85, 107, 47, 0.15);">
            <p style="color: {COLORS['dark_olive']}; margin: 0; font-size: 12px;">{status_text}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="background: rgba(247, 231, 206, 0.95); padding: 14px; border-radius: 4px; 
                    border: 1px solid rgba(85, 107, 47, 0.15);">
            <p style="color: {COLORS['dark_olive']}; margin: 0; font-size: 12px;">👥 Users: {df['id_user'].nunique()}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Auto refresh
    if auto_refresh:
        time.sleep(refresh_rate)
        st.rerun()

if __name__ == "__main__":
    main()