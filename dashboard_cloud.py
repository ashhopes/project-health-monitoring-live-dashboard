import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from google.cloud import bigquery
from google.oauth2 import service_account
from datetime import datetime, timedelta
import time
import pytz
import base64
from pathlib import Path

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
# 2. LOAD UMPSA BACKGROUND IMAGE
# ============================================================================
def get_base64_image(image_path):
    """Convert image to base64 for CSS background"""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        # Try alternative paths
        for path in ["umpsa.png", "./umpsa.png", "../umpsa.png"]:
            try:
                with open(path, "rb") as img_file:
                    return base64.b64encode(img_file.read()).decode()
            except:
                continue
        return None

# Load UMPSA wallpaper
umpsa_bg = get_base64_image("umpsa.png")

# MUJI-style CSS with UMPSA wallpaper
if umpsa_bg:
    background_style = f"""
    background-image: linear-gradient(rgba(255, 255, 255, 0.85), rgba(255, 255, 255, 0.85)), 
                      url('data:image/png;base64,{umpsa_bg}');
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
    background-repeat: no-repeat;
    """
else:
    background_style = """
    background: linear-gradient(135deg, #f5f5f5 0%, #ffffff 100%);
    """

st.markdown(f"""
<style>
    /* ============================================
       MUJI PHILOSOPHY: 無印良品
       - Natural, Simple, Essential
       - Minimal colors, maximum function
    ============================================ */
    
    /* Main background with UMPSA wallpaper */
    .main {{
        {background_style}
    }}
    
    /* Clean white cards with subtle shadows */
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
    
    /* Typography - Clean and readable (MUJI style) */
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
    
    /* Headers - Minimal Japanese typography influence */
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
    
    /* Info boxes - Clean and subtle */
    .stAlert {{
        border-radius: 4px;
        border: 1px solid rgba(0,0,0,0.08);
        background: rgba(250, 250, 250, 0.9);
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
# 4. BIGQUERY CONNECTION
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
            st.error("No credentials found")
            return None
        
        client = bigquery.Client(
            credentials=credentials,
            project=PROJECT_ID,
            location="asia-southeast1"
        )
        
        return client
    except Exception as e:
        st.error(f"Connection failed: {e}")
        return None

# ============================================================================
# 5. DATA FETCHING
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
# 6. MINIMAL CHARTS - MUJI STYLE
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
        title=dict(
            text=title, 
            font=dict(size=14, color='#2c2c2c', family='Arial'),
            x=0
        ),
        paper_bgcolor='rgba(255,255,255,0.9)',
        plot_bgcolor='rgba(255,255,255,0.5)',
        font=dict(color='#666666', size=11),
        xaxis=dict(
            gridcolor='rgba(0,0,0,0.05)',
            showgrid=True,
            zeroline=False
        ),
        yaxis=dict(
            gridcolor='rgba(0,0,0,0.05)',
            showgrid=True,
            zeroline=False
        ),
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
        marker=dict(
            color='#2c2c2c',
            line=dict(color='#2c2c2c', width=1)
        )
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
# 7. MAIN DASHBOARD - MUJI MINIMALIST
# ============================================================================
def main():
    # Header with UMPSA branding - Minimal style
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("""
        <div style="padding: 15px 0;">
            <h1 style="margin: 0; font-weight: 300; color: #2c2c2c;">Health Monitoring System</h1>
            <p style="color: #999999; font-size: 13px; margin-top: 4px; letter-spacing: 0.5px;">
                Real-time LoRa-based Vital Signs Monitor
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="text-align: right; padding: 15px 0;">
            <p style="color: #999999; font-size: 11px; margin: 0; letter-spacing: 0.5px;">DEVELOPED BY</p>
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
    # SIDEBAR - MINIMAL CONTROLS
    # ============================================================================
    with st.sidebar:
        st.markdown("### Settings")
        st.markdown("<br>", unsafe_allow_html=True)
        
        hours = st.select_slider(
            "Time Range",
            options=[1, 3, 6, 12, 24],
            value=1,
            format_func=lambda x: f"{x} hour{'s' if x > 1 else ''}"
        )
        
        st.markdown("---")
        
        auto_refresh = st.checkbox("Auto Refresh", value=True)
        if auto_refresh:
            refresh_rate = st.slider("Refresh Rate (seconds)", 5, 60, 10)
        
        st.markdown("---")
        
        if st.button("Refresh Now", use_container_width=True):
            st.rerun()
        
        st.markdown("---")
        
        current_time = datetime.now(pytz.UTC)
        st.caption(f"Updated: {current_time.strftime('%H:%M:%S UTC')}")
    
    # ============================================================================
    # FETCH DATA
    # ============================================================================
    with st.spinner("Loading..."):
        df = fetch_latest_data(client, hours=hours)
    
    if df.empty:
        st.warning("No data available")
        return
    
    latest = df.iloc[0]
    
    # ============================================================================
    # METRICS - MINIMAL CARDS (MUJI STYLE)
    # ============================================================================
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.95); backdrop-filter: blur(10px); 
                    padding: 20px; border-radius: 8px; 
                    box-shadow: 0 2px 8px rgba(0,0,0,0.06); border: 1px solid rgba(0,0,0,0.05);">
            <p style="color: #999; font-size: 11px; margin: 0; text-transform: uppercase; 
                      letter-spacing: 1px; font-weight: 500;">USER ID</p>
            <h2 style="color: #2c2c2c; font-size: 24px; margin: 6px 0 0 0; font-weight: 300;">
                {latest['id_user']}
            </h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        hr_val = int(latest['hr'])
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.95); backdrop-filter: blur(10px); 
                    padding: 20px; border-radius: 8px; 
                    box-shadow: 0 2px 8px rgba(0,0,0,0.06); border: 1px solid rgba(0,0,0,0.05);">
            <p style="color: #999; font-size: 11px; margin: 0; text-transform: uppercase; 
                      letter-spacing: 1px; font-weight: 500;">HEART RATE</p>
            <h2 style="color: #2c2c2c; font-size: 28px; margin: 6px 0 0 0; font-weight: 300;">
                {hr_val}<span style="font-size: 12px; color: #bbb;"> BPM</span>
            </h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        spo2_val = int(latest['spo2'])
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.95); backdrop-filter: blur(10px); 
                    padding: 20px; border-radius: 8px; 
                    box-shadow: 0 2px 8px rgba(0,0,0,0.06); border: 1px solid rgba(0,0,0,0.05);">
            <p style="color: #999; font-size: 11px; margin: 0; text-transform: uppercase; 
                      letter-spacing: 1px; font-weight: 500;">SPO2</p>
            <h2 style="color: #2c2c2c; font-size: 28px; margin: 6px 0 0 0; font-weight: 300;">
                {spo2_val}<span style="font-size: 12px; color: #bbb;"> %</span>
            </h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        temp_val = float(latest['temp'])
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.95); backdrop-filter: blur(10px); 
                    padding: 20px; border-radius: 8px; 
                    box-shadow: 0 2px 8px rgba(0,0,0,0.06); border: 1px solid rgba(0,0,0,0.05);">
            <p style="color: #999; font-size: 11px; margin: 0; text-transform: uppercase; 
                      letter-spacing: 1px; font-weight: 500;">TEMPERATURE</p>
            <h2 style="color: #2c2c2c; font-size: 28px; margin: 6px 0 0 0; font-weight: 300;">
                {temp_val:.1f}<span style="font-size: 12px; color: #bbb;"> °C</span>
            </h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        activity_val = str(latest['activity'])
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.95); backdrop-filter: blur(10px); 
                    padding: 20px; border-radius: 8px; 
                    box-shadow: 0 2px 8px rgba(0,0,0,0.06); border: 1px solid rgba(0,0,0,0.05);">
            <p style="color: #999; font-size: 11px; margin: 0; text-transform: uppercase; 
                      letter-spacing: 1px; font-weight: 500;">ACTIVITY</p>
            <h2 style="color: #2c2c2c; font-size: 20px; margin: 6px 0 0 0; font-weight: 400;">
                {activity_val.title()}
            </h2>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ============================================================================
    # CHARTS - MINIMAL TABS
    # ============================================================================
    tab1, tab2, tab3 = st.tabs(["VITAL SIGNS", "MOTION DATA", "STATISTICS"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            fig_hr = create_minimal_line_chart(df, 'hr', 'Heart Rate (BPM)', '#2c2c2c')
            st.plotly_chart(fig_hr, use_container_width=True)
        
        with col2:
            fig_spo2 = create_minimal_line_chart(df, 'spo2', 'SpO2 (%)', '#2c2c2c')
            st.plotly_chart(fig_spo2, use_container_width=True)
        
        col3, col4 = st.columns(2)
        
        with col3:
            fig_temp = create_minimal_line_chart(df, 'temp', 'Temperature (°C)', '#2c2c2c')
            st.plotly_chart(fig_temp, use_container_width=True)
        
        with col4:
            fig_hum = create_minimal_line_chart(df, 'humidity', 'Humidity (%)', '#2c2c2c')
            st.plotly_chart(fig_hum, use_container_width=True)
    
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            fig_accel = create_minimal_line_chart(df, 'ax', 'Accelerometer X', '#2c2c2c')
            st.plotly_chart(fig_accel, use_container_width=True)
        
        with col2:
            st.plotly_chart(create_minimal_bar_chart(df), use_container_width=True)
    
    with tab3:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div style="background: rgba(250,250,250,0.9); padding: 20px; border-radius: 8px; 
                        border: 1px solid rgba(0,0,0,0.05);">
                <p style="color: #999; font-size: 11px; margin: 0; letter-spacing: 0.5px;">Total Records</p>
                <h2 style="color: #2c2c2c; margin: 8px 0 0 0; font-weight: 300;">{len(df)}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            avg_hr = df['hr'].mean()
            st.markdown(f"""
            <div style="background: rgba(250,250,250,0.9); padding: 20px; border-radius: 8px; 
                        border: 1px solid rgba(0,0,0,0.05);">
                <p style="color: #999; font-size: 11px; margin: 0; letter-spacing: 0.5px;">Average HR</p>
                <h2 style="color: #2c2c2c; margin: 8px 0 0 0; font-weight: 300;">{avg_hr:.1f} BPM</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            avg_temp = df['temp'].mean()
            st.markdown(f"""
            <div style="background: rgba(250,250,250,0.9); padding: 20px; border-radius: 8px; 
                        border: 1px solid rgba(0,0,0,0.05);">
                <p style="color: #999; font-size: 11px; margin: 0; letter-spacing: 0.5px;">Average Temp</p>
                <h2 style="color: #2c2c2c; margin: 8px 0 0 0; font-weight: 300;">{avg_temp:.1f}°C</h2>
            </div>
            """, unsafe_allow_html=True)
    
    # ============================================================================
    # FOOTER - CLEAN STATUS
    # ============================================================================
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="background: rgba(250,250,250,0.9); padding: 14px; border-radius: 4px; 
                    border: 1px solid rgba(0,0,0,0.05);">
            <p style="color: #2c2c2c; margin: 0; font-size: 12px;">● System Online</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        current_time = datetime.now(pytz.UTC)
        latest_timestamp = df['timestamp'].max()
        if latest_timestamp.tzinfo is None:
            latest_timestamp = latest_timestamp.replace(tzinfo=pytz.UTC)
        time_diff = (current_time - latest_timestamp).total_seconds()
        
        status_text = f"Live: {time_diff:.0f}s ago" if time_diff < 60 else f"Updated: {time_diff/60:.0f}m ago"
        
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
            <p style="color: #2c2c2c; margin: 0; font-size: 12px;">Users: {df['id_user'].nunique()}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Auto refresh
    if auto_refresh:
        time.sleep(refresh_rate)
        st.rerun()

if __name__ == "__main__":
    main()