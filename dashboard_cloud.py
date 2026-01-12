
import serial
import time
from datetime import datetime, timedelta
from google.cloud import bigquery
from google.oauth2 import service_account
import plotly.graph_objects as go
import time
import csv
import os
import json
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
import sys

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
# ============================================================================
# CONFIGURATION - ADJUST THESE!
# ============================================================================

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
# Serial port (change if different)
COM_PORT = "COM8"
BAUD_RATE = 9600

# --- Table reference ---
# BigQuery settings
PROJECT_ID = "monitoring-system-with-lora"
DATASET_ID = "sdp2_live_monitoring_system"
TABLE_ID = "lora_health_data_clean2"
FULL_TABLE_ID = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

# --- Fetch latest data ---
@st.cache_data(ttl=30, show_spinner="Fetching latest sensor data...")
def fetch_latest_data(n_samples=200, user_filter=None, hours_back=6):
# Backup CSV
OUTPUT_CSV = "lora_received_backup.csv"

# ============================================================================
# PARSER FUNCTIONS
# ============================================================================

def parse_pipe_format(raw_packet):
    """
    Fetch latest data from BigQuery with filtering options
    Parse pipe-separated format: |timestamp|hr|spo2|temp|humidity|ax|ay|az|gx|gy|gz|
    Example: |1609462182|92|87|40.7|27.7|0.1|0.2|0.3|0.4|0.5|0.6|
    """
    try:
        # Calculate time filter
        time_threshold = datetime.utcnow() - timedelta(hours=hours_back)
        time_threshold_str = time_threshold.strftime('%Y-%m-%d %H:%M:%S')
        if not raw_packet.startswith('|'):
            return None
        
        # Remove pipes and split
        parts = raw_packet.strip('|').split('|')
        
        if len(parts) < 5:
            print(f"❌ Pipe format too short: {len(parts)} parts")
            return None
        
        # Create data dictionary
        data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'source': 'PIPE_FORMAT',
            'activity': 'unknown',
            'activity_confidence': 0.0,
            'battery_level': 3.7,
        }
        
        # Parse timestamp (first value)
        try:
            timestamp_int = int(float(parts[0]))
            dt = datetime.fromtimestamp(timestamp_int)
            data['timestamp'] = dt.isoformat() + 'Z'
        except:
            pass
        
        # Map values based on position
        # ADJUST THIS MAPPING BASED ON YOUR ACTUAL SENSOR ORDER!
        if len(parts) > 1:
            data['hr'] = safe_int(parts[1], 0)           # Heart rate
        if len(parts) > 2:
            data['spo2'] = safe_int(parts[2], 0)         # SpO2
        if len(parts) > 3:
            data['temp'] = safe_float(parts[3], 0.0)     # Temperature
        if len(parts) > 4:
            data['humidity'] = safe_float(parts[4], 0.0) # Humidity
        if len(parts) > 5:
            data['ax'] = safe_float(parts[5], 0.0)       # Accelerometer X
        if len(parts) > 6:
            data['ay'] = safe_float(parts[6], 0.0)       # Accelerometer Y
        if len(parts) > 7:
            data['az'] = safe_float(parts[7], 0.0)       # Accelerometer Z
        if len(parts) > 8:
            data['gx'] = safe_float(parts[8], 0.0)       # Gyroscope X
        if len(parts) > 9:
            data['gy'] = safe_float(parts[9], 0.0)       # Gyroscope Y
        if len(parts) > 10:
            data['gz'] = safe_float(parts[10], 0.0)      # Gyroscope Z
        
        # Set user ID (you might need to detect this differently)
        data['id_user'] = detect_user_from_data(data)
        
        # Calculate derived values
        if 'ax' in data and 'ay' in data and 'az' in data:
            data['movement_magnitude'] = np.sqrt(data['ax']**2 + data['ay']**2 + data['az']**2)
        
        if 'gx' in data and 'gy' in data and 'gz' in data:
            data['rotation_magnitude'] = np.sqrt(data['gx']**2 + data['gy']**2 + data['gz']**2)
        
        return data
        
        # Build query based on filters
        base_query = f"""
            SELECT 
                id_user,
                timestamp,
                temp,
                spo2,
                hr,
                ax,
                ay,
                az,
                gx,
                gy,
                gz,
                humidity,
                activity,
                source,
                activity_confidence,
                battery_level
            FROM `{FULL_TABLE_ID}`
            WHERE TIMESTAMP(timestamp) >= TIMESTAMP('{time_threshold_str}')
        """
        
        # Add user filter if specified
        if user_filter and user_filter != "All Users":
            base_query += f" AND id_user = '{user_filter}'"
        
        # Add ordering and limit
        base_query += f" ORDER BY timestamp DESC LIMIT {n_samples}"
        
        # Execute query
        query_job = client.query(base_query)
        df = query_job.to_dataframe()
        
        if not df.empty:
            # Clean and process data
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce', utc=True)
            df['timestamp'] = df['timestamp'].dt.tz_convert('Asia/Kuala_Lumpur')
            
            # Convert numeric columns
            numeric_cols = ['temp', 'spo2', 'hr', 'ax', 'ay', 'az', 'gx', 'gy', 'gz', 
                           'humidity', 'activity_confidence', 'battery_level']
            
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Sort by timestamp (ascending for plotting)
            df = df.sort_values('timestamp', ascending=True)
    except Exception as e:
        print(f"❌ Error parsing pipe format: {e}")
        print(f"   Packet: {raw_packet[:50]}...")
        return None

def parse_ml_format(raw_packet):
    """
    Parse ML format: ML|USER:XXX|ACTIVITY:XXX|CONFIDENCE:X.XX|HR:XX|...
    Example: ML|USER:STEMCUBE_001|ACTIVITY:RUNNING|CONFIDENCE:0.95|HR:92|...
    """
    try:
        if not raw_packet.startswith('ML|'):
            return None
        
        # Remove "ML|" and split
        parts = raw_packet[3:].split('|')
        
        data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'source': 'ML_FORMAT',
        }
        
        # Parse key-value pairs
        for part in parts:
            if ':' in part:
                key, value = part.split(':', 1)
                key = key.strip().lower()
                
                # Map to your BigQuery schema
                if key == 'user':
                    data['id_user'] = value
                elif key == 'activity':
                    data['activity'] = value
                elif key == 'confidence':
                    data['activity_confidence'] = safe_float(value, 0.0)
                elif key == 'hr':
                    data['hr'] = safe_int(value, 0)
                elif key == 'spo2':
                    data['spo2'] = safe_int(value, 0)
                elif key == 'temp':
                    data['temp'] = safe_float(value, 0.0)
                elif key in ['humidity', 'hum']:
                    data['humidity'] = safe_float(value, 0.0)
                elif key in ['ax', 'ay', 'az', 'gx', 'gy', 'gz']:
                    data[key] = safe_float(value, 0.0)
                elif key == 'battery':
                    data['battery_level'] = safe_float(value, 3.7)
        
        # Set defaults for missing fields
        if 'id_user' not in data:
            data['id_user'] = 'STEMCUBE_001'
        if 'activity' not in data:
            data['activity'] = 'unknown'
        if 'activity_confidence' not in data:
            data['activity_confidence'] = 0.0
        if 'battery_level' not in data:
            data['battery_level'] = 3.7
        
        return data
        
        return df
    
    except Exception as e:
        st.error(f"Query Error: {str(e)}")
        return pd.DataFrame()
        print(f"❌ Error parsing ML format: {e}")
        return None

def detect_user_from_data(data):
    """Detect user ID from data patterns (customize this!)"""
    # This is a simple example - you might need to detect based on:
    # 1. Specific value ranges
    # 2. Device ID in the data
    # 3. Source field
    
    # Example: If HR is consistently in a certain range, assign user
    hr = data.get('hr', 0)
    if 60 <= hr <= 75:
        return "STEMCUBE_001"
    elif 76 <= hr <= 85:
        return "STEMCUBE_002"
    elif 86 <= hr <= 100:
        return "STEMCUBE_003"
    else:
        return "STEMCUBE_001"  # Default

def safe_int(value, default=0):
    """Convert to int safely"""
    try:
        return int(float(value))
    except:
        return default

def safe_float(value, default=0.0):
    """Convert to float safely"""
    try:
        return float(value)
    except:
        return default

# --- Auto-refresh logic ---
if refresh_rate > 0:
    time.sleep(refresh_rate)
    st.rerun()
# ============================================================================
# BIGQUERY FUNCTIONS
# ============================================================================

# --- Main Dashboard Content ---
try:
    # Fetch data
    df = fetch_latest_data(n_samples, selected_user if selected_user != "All Users" else None, hours_filter)
def init_bigquery_client():
    """Initialize BigQuery client"""
    try:
        # Method 1: Use Streamlit secrets (for cloud deployment)
        import streamlit as st
        credentials_dict = st.secrets["gcp"]
        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict,
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        print("✓ Using Streamlit secrets")
        
    except:
        try:
            # Method 2: Use local service account file
            credentials = service_account.Credentials.from_service_account_file(
                "service-account-key.json",
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            print("✓ Using local service account")
        except:
            # Method 3: Use default credentials
            print("⚠ Using default credentials")
            credentials = None
    
    if df.empty:
        st.warning("""
        ## ⚠️ No Data Available
        
        The dashboard is connected to BigQuery, but no sensor data was found.
        
        **Please ensure:**
        1. Your LoRa receiver (COM8) is running
        2. Data is being uploaded from your batch file
        3. Check if data exists in BigQuery table
        4. Adjust the time filter in the sidebar
        
        **Expected table:** `monitoring-system-with-lora.sdp2_live_monitoring_system.lora_health_data_clean2`
        """)
    return bigquery.Client(
        credentials=credentials,
        project=PROJECT_ID,
        location="asia-southeast1"
    )

def upload_to_bigquery(client, data):
    """Upload parsed data to BigQuery"""
    try:
        # Prepare row matching your table schema
        row = {
            'id_user': data.get('id_user', 'UNKNOWN'),
            'timestamp': data.get('timestamp'),
            'hr': data.get('hr', 0),
            'spo2': data.get('spo2', 0),
            'temp': data.get('temp', 0.0),
            'humidity': data.get('humidity', 0.0),
            'ax': data.get('ax', 0.0),
            'ay': data.get('ay', 0.0),
            'az': data.get('az', 0.0),
            'gx': data.get('gx', 0.0),
            'gy': data.get('gy', 0.0),
            'gz': data.get('gz', 0.0),
            'activity': data.get('activity', 'unknown'),
            'activity_confidence': data.get('activity_confidence', 0.0),
            'movement_magnitude': data.get('movement_magnitude', 0.0),
            'rotation_magnitude': data.get('rotation_magnitude', 0.0),
            'battery_level': data.get('battery_level', 3.7),
            'source': data.get('source', 'LoRa'),
        }
        
        # Insert into BigQuery
        errors = client.insert_rows_json(FULL_TABLE_ID, [row])
        
        if errors:
            print(f"❌ BigQuery upload error: {errors}")
            return False
        else:
            print(f"✅ Uploaded: {row['id_user']} - HR: {row['hr']}, Temp: {row['temp']:.1f}")
            return True
            
    except Exception as e:
        print(f"❌ BigQuery upload failed: {e}")
        return False

def save_to_csv(data, filename):
    """Save data to CSV backup"""
    try:
        file_exists = os.path.exists(filename)
        
        # Show available tables for debugging
        with st.expander("🔍 Debug: Check Available Tables"):
            try:
                tables_query = f"""
                    SELECT table_id 
                    FROM `{PROJECT_ID}.{DATASET_ID}.__TABLES__`
                    ORDER BY table_id
                """
                tables = client.query(tables_query).to_dataframe()
                st.write("Available tables in dataset:", tables)
            except:
                st.write("Could not fetch table list")
        with open(filename, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=data.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(data)
        
        st.stop()
    
    # Update sidebar status
    st.sidebar.metric("Data Points", len(df))
        return True
    except Exception as e:
        print(f"⚠ CSV save error: {e}")
        return False

# ============================================================================
# MAIN RECEIVER LOOP
# ============================================================================

def main():
    """Main receiver and uploader loop"""
    print("=" * 60)
    print("📡 LoRa Receiver & BigQuery Uploader")
    print("=" * 60)
    print(f"Port: {COM_PORT}")
    print(f"BigQuery Table: {FULL_TABLE_ID}")
    print("=" * 60)
    
    # Add derived metrics
    if all(col in df.columns for col in ['ax', 'ay', 'az']):
        df['movement_magnitude'] = np.sqrt(df['ax']**2 + df['ay']**2 + df['az']**2)
    # Initialize BigQuery client
    try:
        bq_client = init_bigquery_client()
        print("✅ Connected to BigQuery")
    except Exception as e:
        print(f"❌ BigQuery connection failed: {e}")
        print("Please check your credentials and network connection")
        return
    
    if all(col in df.columns for col in ['gx', 'gy', 'gz']):
        df['rotation_magnitude'] = np.sqrt(df['gx']**2 + df['gy']**2 + df['gz']**2)
    # Open serial port
    try:
        ser = serial.Serial(
            port=COM_PORT,
            baudrate=BAUD_RATE,
            timeout=2
        )
        print(f"✅ Connected to {COM_PORT}")
    except Exception as e:
        print(f"❌ Serial connection failed: {e}")
        print("\n📝 Troubleshooting:")
        print("1. Check if COM8 is correct")
        print("2. Make sure no other program is using COM8")
        print("3. Verify Master Cube is transmitting")
        print("4. Try different baud rate (9600, 115200, etc.)")
        return
    
    # Get unique users
    unique_users = df['id_user'].dropna().unique().tolist() if 'id_user' in df.columns else []
    # Statistics
    stats = {
        'total': 0,
        'pipe_format': 0,
        'ml_format': 0,
        'uploaded': 0,
        'errors': 0
    }
    
    # --- Tabs ---
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Live Dashboard", "👤 Subjects", "📈 Analytics", "⚙️ System Info"])
    print("\n🔄 Listening for data... (Press Ctrl+C to stop)\n")
    
    # ================ TAB 1: LIVE DASHBOARD ================
    with tab1:
        st.markdown(f"<h2 style='color:#4B0082;'>📊 Live Sensor Dashboard</h2>", unsafe_allow_html=True)
        
        # Dashboard header with stats
        col_header1, col_header2, col_header3, col_header4 = st.columns(4)
        
        with col_header1:
            st.metric("Active Users", len(unique_users))
        
        with col_header2:
            latest_time = df['timestamp'].max() if not df.empty else "N/A"
            if isinstance(latest_time, pd.Timestamp):
                st.metric("Latest Data", latest_time.strftime("%H:%M:%S"))
            else:
                st.metric("Latest Data", "N/A")
        
        with col_header3:
            time_span = (df['timestamp'].max() - df['timestamp'].min()).total_seconds() / 60 if not df.empty else 0
            st.metric("Time Span", f"{time_span:.1f} min")
        
        with col_header4:
            if 'activity' in df.columns:
                activities = df['activity'].dropna().unique()
                st.metric("Activities", len(activities))
        
        st.markdown("---")
        
        # SECTION 1: VITAL SIGNS
        st.markdown("<div class='sensor-group'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:#c0392b;'>❤️ Vital Signs Monitor</h3>", unsafe_allow_html=True)
        
        # Vital metrics in cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_hr = df['hr'].mean() if 'hr' in df.columns else 0
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
        
        with col2:
            avg_spo2 = df['spo2'].mean() if 'spo2' in df.columns else 0
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
        
        with col3:
            avg_temp = df['temp'].mean() if 'temp' in df.columns else 0
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
        
        with col4:
            avg_humidity = df['humidity'].mean() if 'humidity' in df.columns else 0
            st.markdown(f"""
                <div class='metric-card-small'>
                    <h4>💧 Humidity</h4>
                    <h2>{avg_humidity:.0f}%</h2>
                    <p>Ambient Humidity</p>
                </div>
            """, unsafe_allow_html=True)
        
        # Vital signs graph
        if all(col in df.columns for col in ['timestamp', 'hr', 'spo2', 'temp']):
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
            
            # Temperature trace
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
                yaxis3=dict(title="Temp (°C)", titlefont=dict(color='#e67e22'), tickfont=dict(color='#e67e22'),
                           overlaying='y', side='left', position=0.05),
                plot_bgcolor='rgba(253, 246, 236, 0.8)',
                paper_bgcolor='rgba(255, 255, 255, 0.9)',
                height=400,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                hovermode='x unified'
            )
            
            st.plotly_chart(fig_vitals, use_container_width=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # SECTION 2: MOVEMENT DATA
        st.markdown("<div class='sensor-group'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:#2980b9;'>📍 Movement & Motion Data</h3>", unsafe_allow_html=True)
        
        # Movement metrics
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            avg_movement = df['movement_magnitude'].mean() if 'movement_magnitude' in df.columns else 0
            st.markdown(f"""
                <div class='metric-card-small'>
                    <h4>📈 Movement Magnitude</h4>
                    <h2>{avg_movement:.3f}</h2>
                    <p>Total Acceleration</p>
                </div>
            """, unsafe_allow_html=True)
        
        with col6:
            avg_rotation = df['rotation_magnitude'].mean() if 'rotation_magnitude' in df.columns else 0
            st.markdown(f"""
                <div class='metric-card-small'>
                    <h4>🌀 Rotation Magnitude</h4>
                    <h2>{avg_rotation:.2f}</h2>
                    <p>Total Rotation</p>
                </div>
            """, unsafe_allow_html=True)
        
        with col7:
            if 'activity' in df.columns:
                most_common_activity = df['activity'].mode()[0] if not df['activity'].mode().empty else "Unknown"
                st.markdown(f"""
                    <div class='metric-card-small'>
                        <h4>🏃 Common Activity</h4>
                        <h2>{most_common_activity}</h2>
                        <p>Most frequent</p>
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
                st.plotly_chart(fig_accel, use_container_width=True)
        
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
                st.plotly_chart(fig_gyro, use_container_width=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # SECTION 3: REAL-TIME DATA TABLE
        st.markdown("<div class='sensor-group'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:#8e44ad;'>📋 Recent Sensor Readings</h3>", unsafe_allow_html=True)
        
        # Show latest data
        if not df.empty:
            display_cols = ['timestamp', 'id_user', 'hr', 'spo2', 'temp', 'activity', 'movement_magnitude']
            display_cols = [col for col in display_cols if col in df.columns]
            
            # Format timestamp for display
            display_df = df[display_cols].copy()
            if 'timestamp' in display_df.columns:
                display_df['timestamp'] = display_df['timestamp'].dt.strftime('%H:%M:%S')
            
            # Show last 20 records
            st.dataframe(
                display_df.tail(20).sort_values('timestamp', ascending=False),
                use_container_width=True,
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
                if len(user_data) > 5:
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
    try:
        while True:
            try:
                # Check for incoming data
                if ser.in_waiting > 0:
                    # Read raw data
                    raw_data = ser.readline().decode('utf-8', errors='ignore').strip()
                    
                    fig_user.update_layout(
                        title=f"<b>Activity Pattern for {user_id}</b>",
                        xaxis_title="Time",
                        yaxis=dict(title="Heart Rate (BPM)", titlefont=dict(color='#c0392b')),
                        yaxis2=dict(title="Movement", titlefont=dict(color='#2980b9'),
                                   overlaying='y', side='right'),
                        height=300,
                        plot_bgcolor='rgba(253, 246, 236, 0.8)',
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    if not raw_data or len(raw_data) < 3:
                        continue
                    
                    st.plotly_chart(fig_user, use_container_width=True)
                
                # User statistics
                if not user_data.empty:
                    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
                    stats['total'] += 1
                    
                    with col_stat1:
                        avg_hr_user = user_data['hr'].mean() if 'hr' in user_data.columns else 0
                        st.metric("Avg HR", f"{avg_hr_user:.0f} BPM")
                    # Parse based on format
                    parsed_data = None
                    
                    with col_stat2:
                        avg_spo2_user = user_data['spo2'].mean() if 'spo2' in user_data.columns else 0
                        st.metric("Avg SpO₂", f"{avg_spo2_user:.0f}%")
                    if raw_data.startswith('|'):
                        # Pipe format
                        print(f"[{stats['total']}] 📦 Pipe format: {raw_data[:40]}...")
                        parsed_data = parse_pipe_format(raw_data)
                        if parsed_data:
                            stats['pipe_format'] += 1
                    
                    with col_stat3:
                        records_count = len(user_data)
                        st.metric("Records", records_count)
                    elif raw_data.startswith('ML|'):
                        # ML format
                        print(f"[{stats['total']}] 🧠 ML format: {raw_data[:40]}...")
                        parsed_data = parse_ml_format(raw_data)
                        if parsed_data:
                            stats['ml_format'] += 1
                    
                    with col_stat4:
                        if 'activity' in user_data.columns:
                            unique_acts = user_data['activity'].nunique()
                            st.metric("Activities", unique_acts)
                
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
            correlation_cols = [col for col in ['hr', 'spo2', 'temp', 'ax', 'ay', 'az', 'gx', 'gy', 'gz', 
                                               'movement_magnitude', 'rotation_magnitude'] 
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
                
                st.plotly_chart(fig_corr, use_container_width=True)
                
                # Interpretation
                with st.expander("📝 How to interpret correlations"):
                    st.markdown("""
                    - **+1.0**: Perfect positive correlation (when one increases, the other increases)
                    - **-1.0**: Perfect negative correlation (when one increases, the other decreases)
                    - **0.0**: No correlation
                    - **> 0.7**: Strong positive correlation
                    - **< -0.7**: Strong negative correlation
                    """)
            else:
                st.info("Need at least 3 numeric sensors for correlation analysis")
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Statistical summary
            st.markdown("<div class='section'>", unsafe_allow_html=True)
            st.markdown("<h3>📊 Statistical Summary</h3>", unsafe_allow_html=True)
            
            if numeric_cols:
                summary_df = df[numeric_cols].describe().round(3)
                st.dataframe(summary_df, use_container_width=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Activity analysis
            if 'activity' in df.columns and 'activity_confidence' in df.columns:
                st.markdown("<div class='section'>", unsafe_allow_html=True)
                st.markdown("<h3>🏃 Activity Analysis</h3>", unsafe_allow_html=True)
                
                col_act1, col_act2 = st.columns(2)
                
                with col_act1:
                    # Activity distribution
                    activity_counts = df['activity'].value_counts()
                    fig_activity = go.Figure(data=[go.Pie(
                        labels=activity_counts.index,
                        values=activity_counts.values,
                        hole=.3,
                        marker_colors=['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6']
                    )])
                    else:
                        print(f"[{stats['total']}] ❓ Unknown: {raw_data[:30]}...")
                    
                    fig_activity.update_layout(
                        title="<b>Activity Distribution</b>",
                        height=300
                    )
                    # Upload if parsed successfully
                    if parsed_data:
                        if upload_to_bigquery(bq_client, parsed_data):
                            stats['uploaded'] += 1
                        
                        # Save to CSV backup
                        save_to_csv(parsed_data, OUTPUT_CSV)
                    
                    st.plotly_chart(fig_activity, use_container_width=True)
                    # Display stats every 10 packets
                    if stats['total'] % 10 == 0:
                        print(f"\n📊 Stats: Total={stats['total']}, "
                              f"Pipe={stats['pipe_format']}, "
                              f"ML={stats['ml_format']}, "
                              f"Uploaded={stats['uploaded']}")
                
                with col_act2:
                    # Activity confidence
                    if not df.empty:
                        avg_confidence = df.groupby('activity')['activity_confidence'].mean().round(3)
                        st.markdown("**Average Confidence by Activity:**")
                        st.dataframe(avg_confidence, use_container_width=True)
                # Small delay to prevent CPU overload
                time.sleep(0.1)
                
                st.markdown("</div>", unsafe_allow_html=True)
            except KeyboardInterrupt:
                print("\n\n🛑 Stopped by user")
                break
            except Exception as e:
                print(f"⚠ Processing error: {e}")
                stats['errors'] += 1
                time.sleep(1)
    
    # ================ TAB 4: SYSTEM INFO ================
    with tab4:
        st.markdown("<h2 style='color:#4B0082;'>⚙️ System Information</h2>", unsafe_allow_html=True)
        
        col_sys1, col_sys2 = st.columns(2)
        
        with col_sys1:
            st.markdown("<div class='section'>", unsafe_allow_html=True)
            st.markdown("<h3>🔧 System Configuration</h3>", unsafe_allow_html=True)
            
            st.markdown("""
            **Data Source:**
            - BigQuery Project: `monitoring-system-with-lora`
            - Dataset: `sdp2_live_monitoring_system`
            - Table: `lora_health_data_clean2`
            
            **Data Flow:**
            1. LoRa Sensors → COM5/7
            2. Master Cube → ML Processing
            3. LoRa Transmission → COM8
            4. Batch Upload → BigQuery
            5. Streamlit Dashboard → Live Display
            
            **Refresh Rate:** Every {refresh_rate} seconds
            **Data Samples:** {n_samples} records
            **Time Filter:** Last {hours_filter} hours
            """.format(refresh_rate=refresh_rate, n_samples=n_samples, hours_filter=hours_filter))
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col_sys2:
            st.markdown("<div class='section'>", unsafe_allow_html=True)
            st.markdown("<h3>📈 Data Statistics</h3>", unsafe_allow_html=True)
            
            if not df.empty:
                st.metric("Total Records", len(df))
                st.metric("Time Range", f"{(df['timestamp'].max() - df['timestamp'].min()).total_seconds()/60:.1f} min")
                st.metric("Data Rate", f"{len(df)/max(1, (df['timestamp'].max() - df['timestamp'].min()).total_seconds()/60):.1f} rec/min")
                st.metric("Active Users", len(unique_users))
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Data preview
        st.markdown("<div class='section'>", unsafe_allow_html=True)
        st.markdown("<h3>📋 Raw Data Preview</h3>", unsafe_allow_html=True)
        
        if not df.empty:
            st.dataframe(df.head(10), use_container_width=True)
            
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
        print(f"\n❌ Fatal error: {e}")
    finally:
        # Cleanup
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("🔌 Serial port closed")
        
        # Final statistics
        print("\n" + "=" * 60)
        print("📊 FINAL STATISTICS")
        print("=" * 60)
        print(f"Total packets received: {stats['total']}")
        print(f"Pipe format packets: {stats['pipe_format']}")
        print(f"ML format packets: {stats['ml_format']}")
        print(f"Successfully uploaded: {stats['uploaded']}")
        print(f"Errors: {stats['errors']}")
        
        if stats['total'] > 0:
            success_rate = (stats['uploaded'] / stats['total']) * 100
            print(f"Success rate: {success_rate:.1f}%")
        
        print(f"CSV backup: {OUTPUT_CSV}")
        print("=" * 60)

# ============================================================================
# TESTING FUNCTIONS
# ============================================================================

except Exception as e:
    st.error(f"❌ Dashboard Error: {str(e)}")
def test_parsers():
    """Test the parsers with sample data"""
    print("🧪 Testing parsers...\n")
    
    with st.expander("🔍 Error Details"):
        st.code(f"""
        Error Type: {type(e).__name__}
        Error Message: {str(e)}
        
        Current Configuration:
        - Project ID: {PROJECT_ID}
        - Dataset: {DATASET_ID}
        - Table: {TABLE_ID}
        - Selected User: {selected_user}
        - Time Filter: {hours_filter} hours
        - Sample Size: {n_samples}
        """)
    test_samples = [
        # Pipe format (what you're receiving)
        "|1609462182|92|87|40.7|27.7|0.1|0.2|0.3|0.4|0.5|0.6|",
        "|1609462184|88|85|36.5|28.1|-0.1|0.3|-0.2|0.1|0.2|0.3|",
        
        # ML format
        "ML|USER:STEMCUBE_001|ACTIVITY:RUNNING|CONFIDENCE:0.95|HR:92|SPO2:98|TEMP:36.5",
        "ML|USER:STEMCUBE_002|ACTIVITY:WALKING|CONFIDENCE:0.87|HR:88|SPO2:96|TEMP:36.8|HUMIDITY:45.2",
        
        # Invalid formats
        "Hello World",
        "123|456|789",
    ]
    
    st.markdown("""
    ### 🚨 Immediate Actions:
    1. **Check your batch file** is running and uploading data
    2. **Verify BigQuery table** exists and has data
    3. **Check internet connection**
    4. **Try reducing sample size** in sidebar
    5. **Extend time filter** to see older data
    for sample in test_samples:
        print(f"📦 Testing: {sample[:50]}...")
        
        if sample.startswith('|'):
            parsed = parse_pipe_format(sample)
            format_name = "Pipe"
        elif sample.startswith('ML|'):
            parsed = parse_ml_format(sample)
            format_name = "ML"
        else:
            parsed = None
            format_name = "Unknown"
        
        if parsed:
            print(f"  ✅ {format_name} format parsed:")
            print(f"     User: {parsed.get('id_user', 'N/A')}")
            print(f"     HR: {parsed.get('hr', 'N/A')}, Temp: {parsed.get('temp', 'N/A')}")
            if 'movement_magnitude' in parsed:
                print(f"     Movement: {parsed['movement_magnitude']:.3f}")
        else:
            print(f"  ❌ Failed to parse {format_name} format")

# ============================================================================
# QUICK DEBUG FOR DASHBOARD
# ============================================================================

def check_bigquery_data():
    """Quick function to check if data exists in BigQuery"""
    try:
        client = init_bigquery_client()
        
        query = f"""
        SELECT 
            COUNT(*) as total_rows,
            MIN(timestamp) as earliest,
            MAX(timestamp) as latest,
            COUNT(DISTINCT id_user) as unique_users
        FROM `{FULL_TABLE_ID}`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
        """
        
        result = client.query(query).result()
        for row in result:
            print(f"\n📊 BigQuery Data Status:")
            print(f"   Total rows (last 24h): {row.total_rows}")
            print(f"   Time range: {row.earliest} to {row.latest}")
            print(f"   Unique users: {row.unique_users}")
            
            if row.total_rows == 0:
                print("\n⚠️ No data found! Check your uploader.")
            else:
                print("\n✅ Data found! Your dashboard should work.")
    
    ### 📞 Support:
    - Project: STEMCUBE Health Monitoring
    - Developer: mOONbLOOM26
    - Contact: Check your project documentation
    """)
    except Exception as e:
        print(f"❌ Error checking BigQuery: {e}")

# ============================================================================
# ENTRY POINT
# ============================================================================

# --- Footer ---
st.markdown("---")
st.markdown("<div style='text-align: center; color: #666; font-size: 0.9em;'>", unsafe_allow_html=True)
st.markdown("🏥 **STEMCUBE Health Monitoring System** | 📡 **LoRa Technology** | 🎓 **UMP Final Year Project 2024**")
st.markdown("</div>", unsafe_allow_html=True)
if __name__ == "__main__":
    # Command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "test":
            test_parsers()
        elif command == "check":
            check_bigquery_data()
        elif command == "help":
            print("Usage:")
            print("  python lora_uploader_fixed.py          # Run uploader")
            print("  python lora_uploader_fixed.py test     # Test parsers")
            print("  python lora_uploader_fixed.py check    # Check BigQuery data")
        else:
            print(f"Unknown command: {command}")
            print("Use: test, check, or help")
    else:
        # Run the main uploader
        main()