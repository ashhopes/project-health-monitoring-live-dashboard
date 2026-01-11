import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
import plotly.graph_objects as go
import time
import numpy as np
from datetime import datetime
import pytz

# --- Page setup ---
st.set_page_config(page_title="Live Health Monitoring System with LoRa", layout="wide")

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
    .stSidebar { background-color: #f7ede2; }
    h1, h2, h3 { font-family: 'Helvetica Neue', sans-serif; font-weight: 600; }
    .section {
        background: #fff; padding: 20px; margin-bottom: 20px;
        border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1);
    }
    .subject-box {
        background-color: #ffffff; border: 2px solid #800000;
        border-radius: 10px; padding: 15px; margin-bottom: 25px;
    }
    .sensor-group {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #800000;
        margin-bottom: 20px;
    }
    .metric-card-small {
        background: white;
        padding: 10px;
        border-radius: 8px;
        border: 1px solid #dee2e6;
        text-align: center;
        margin: 5px;
    }
    .user-selector {
        background: white;
        padding: 10px;
        border-radius: 8px;
        border: 2px solid #800000;
        margin-bottom: 15px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Header ---
st.markdown("<h1 style='text-align: center; color:#4B0082;'>🏥 Live Health Monitoring System with LoRa</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Real-time monitoring of vital signs and motion data using LoRa sensors</p>", unsafe_allow_html=True)
st.markdown("---")

# --- Sidebar controls ---
st.sidebar.header("⚙️ Controls")
refresh_rate = st.sidebar.slider("Auto-refresh every (seconds)", 0, 120, 30)
n_samples = st.sidebar.slider("Number of samples to display", 50, 500, 100)
st.sidebar.info("Project by mOONbLOOM26 🌙")

# Add user selection in sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### 👤 Select User")
selected_user = st.sidebar.radio(
    "Active User:",
    ["All Users", "user_001", "user_002", "user_003"],
    index=0
)

if refresh_rate > 0:
    time.sleep(refresh_rate)

# --- BigQuery Authentication ---
credentials = service_account.Credentials.from_service_account_info(st.secrets["gcp"])
client = bigquery.Client(
    credentials=credentials,
    project=st.secrets["gcp"]["project_id"],
    location="asia-southeast1"
)

# --- Table reference ---
table_id = "monitoring-system-with-lora.sdp2_live_monitoring_system.lora_health_data_clean2"

# --- Fetch latest data ---
@st.cache_data(ttl=30)
def fetch_latest(n=100, user_filter=None):
    if user_filter and user_filter != "All Users":
        query = f"""
            SELECT id_user, timestamp, temp, spo2, hr, ax, ay, az, gx, gy, gz
            FROM `{table_id}`
            WHERE id_user = '{user_filter}'
            ORDER BY timestamp DESC
            LIMIT {n}
        """
    else:
        query = f"""
            SELECT id_user, timestamp, temp, spo2, hr, ax, ay, az, gx, gy, gz
            FROM `{table_id}`
            ORDER BY timestamp DESC
            LIMIT {n}
        """
    return client.query(query).to_dataframe()

try:
    df = fetch_latest(n_samples, selected_user)
    if df.empty:
        st.info("No data found yet. Upload from your local app first.")
    else:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors="coerce")
        
        # Add derived metrics
        df['movement_magnitude'] = np.sqrt(df['ax']**2 + df['ay']**2 + df['az']**2)
        df['rotation_magnitude'] = np.sqrt(df['gx']**2 + df['gy']**2 + df['gz']**2)
        
        # --- Get active subject IDs dynamically ---
        subject_query = f"""
            SELECT DISTINCT id_user
            FROM `{table_id}`
            WHERE id_user IS NOT NULL
        """
        subject_ids = client.query(subject_query).to_dataframe()['id_user'].tolist()

        # --- Tabs ---
        tab1, tab2, tab3 = st.tabs(["📊 Sensor Dashboard", "👤 Subject Info", "📈 Analytics"])

        # ================ TAB 1: SENSOR DASHBOARD ================
        with tab1:
            st.markdown("<h2 style='color:#4B0082;'>📊 Sensor Dashboard</h2>", unsafe_allow_html=True)
            
            # User selection display
            st.markdown(f"<div class='user-selector'>", unsafe_allow_html=True)
            st.markdown(f"**Currently viewing:** <span style='color:#800000; font-weight:bold;'>{selected_user}</span>")
            st.markdown(f"**Total records:** {len(df)} samples")
            st.markdown(f"**Time range:** {df['timestamp'].min().strftime('%H:%M')} to {df['timestamp'].max().strftime('%H:%M')}")
            st.markdown("</div>", unsafe_allow_html=True)
            
            # SECTION 1: MAX30102 SENSORS (Health)
            st.markdown("<div class='sensor-group'>", unsafe_allow_html=True)
            st.markdown("<h3 style='color:#c0392b;'>❤️ MAX30102 Health Sensors</h3>", unsafe_allow_html=True)
            
            # Health metrics in cards
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                avg_hr = df['hr'].mean()
                hr_status = "🟢" if 60 <= avg_hr <= 100 else "🟡" if 50 <= avg_hr <= 110 else "🔴"
                st.markdown(f"<div class='metric-card-small'><h4>{hr_status} HR</h4><h3>{avg_hr:.1f}</h3><p>BPM</p></div>", unsafe_allow_html=True)
            
            with col2:
                avg_spo2 = df['spo2'].mean()
                spo2_status = "🟢" if avg_spo2 >= 95 else "🟡" if avg_spo2 >= 90 else "🔴"
                st.markdown(f"<div class='metric-card-small'><h4>{spo2_status} SpO₂</h4><h3>{avg_spo2:.1f}%</h3><p>Oxygen</p></div>", unsafe_allow_html=True)
            
            with col3:
                avg_temp = df['temp'].mean()
                temp_status = "🟢" if avg_temp <= 37.5 else "🟡" if avg_temp <= 38.5 else "🔴"
                st.markdown(f"<div class='metric-card-small'><h4>{temp_status} Temp</h4><h3>{avg_temp:.1f}°C</h3><p>Body</p></div>", unsafe_allow_html=True)
            
            with col4:
                hr_range = df['hr'].max() - df['hr'].min()
                st.markdown(f"<div class='metric-card-small'><h4>📈 HR Range</h4><h3>{hr_range:.0f}</h3><p>BPM Variance</p></div>", unsafe_allow_html=True)
            
            # Health sensors graph
            latest_health = df.sort_values("timestamp", ascending=False).head(50).sort_values("timestamp", ascending=True)
            fig_health = go.Figure()
            
            fig_health.add_trace(go.Scatter(
                x=latest_health['timestamp'],
                y=latest_health['hr'],
                mode='lines',
                name='Heart Rate',
                line=dict(color='#c0392b', width=3),
                yaxis='y'
            ))
            
            fig_health.add_trace(go.Scatter(
                x=latest_health['timestamp'],
                y=latest_health['spo2'],
                mode='lines',
                name='SpO₂',
                line=dict(color='#27ae60', width=3),
                yaxis='y2'
            ))
            
            fig_health.update_layout(
                title="<b>Heart Rate & SpO₂ Trend</b>",
                xaxis_title="Time",
                yaxis=dict(title="Heart Rate (BPM)", titlefont=dict(color='#c0392b'), tickfont=dict(color='#c0392b')),
                yaxis2=dict(title="SpO₂ (%)", titlefont=dict(color='#27ae60'), tickfont=dict(color='#27ae60'),
                           overlaying='y', side='right'),
                plot_bgcolor='#fdf6ec',
                paper_bgcolor='#fdf6ec',
                height=300,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_health, use_container_width=True)
            
            st.markdown("</div>", unsafe_allow_html=True)  # Close sensor group
            
            # SECTION 2: ACCELEROMETER (Movement)
            st.markdown("<div class='sensor-group'>", unsafe_allow_html=True)
            st.markdown("<h3 style='color:#2980b9;'>📍 Accelerometer (Movement)</h3>", unsafe_allow_html=True)
            
            # Accelerometer metrics
            col5, col6, col7, col8 = st.columns(4)
            
            with col5:
                avg_ax = df['ax'].mean()
                st.markdown(f"<div class='metric-card-small'><h4>AX</h4><h3>{avg_ax:.3f}</h3><p>g-force</p></div>", unsafe_allow_html=True)
            
            with col6:
                avg_ay = df['ay'].mean()
                st.markdown(f"<div class='metric-card-small'><h4>AY</h4><h3>{avg_ay:.3f}</h3><p>g-force</p></div>", unsafe_allow_html=True)
            
            with col7:
                avg_az = df['az'].mean()
                st.markdown(f"<div class='metric-card-small'><h4>AZ</h4><h3>{avg_az:.3f}</h3><p>g-force</p></div>", unsafe_allow_html=True)
            
            with col8:
                avg_movement = df['movement_magnitude'].mean()
                st.markdown(f"<div class='metric-card-small'><h4>Total Move</h4><h3>{avg_movement:.3f}</h3><p>Magnitude</p></div>", unsafe_allow_html=True)
            
            # Accelerometer graph
            latest_move = df.sort_values("timestamp", ascending=False).head(50).sort_values("timestamp", ascending=True)
            fig_move = go.Figure()
            
            colors_accel = ['#2980b9', '#16a085', '#8e44ad']
            for i, col in enumerate(['ax', 'ay', 'az']):
                fig_move.add_trace(go.Scatter(
                    x=latest_move['timestamp'],
                    y=latest_move[col],
                    mode='lines',
                    name=col.upper(),
                    line=dict(color=colors_accel[i], width=2)
                ))
            
            fig_move.update_layout(
                title="<b>Accelerometer Data (AX, AY, AZ)</b>",
                xaxis_title="Time",
                yaxis_title="g-force",
                plot_bgcolor='#fdf6ec',
                paper_bgcolor='#fdf6ec',
                height=300,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_move, use_container_width=True)
            
            st.markdown("</div>", unsafe_allow_html=True)  # Close sensor group
            
            # SECTION 3: GYROSCOPE (Rotation)
            st.markdown("<div class='sensor-group'>", unsafe_allow_html=True)
            st.markdown("<h3 style='color:#8e44ad;'>🌀 Gyroscope (Rotation)</h3>", unsafe_allow_html=True)
            
            # Gyroscope metrics
            col9, col10, col11, col12 = st.columns(4)
            
            with col9:
                avg_gx = df['gx'].mean()
                st.markdown(f"<div class='metric-card-small'><h4>GX</h4><h3>{avg_gx:.2f}</h3><p>deg/s</p></div>", unsafe_allow_html=True)
            
            with col10:
                avg_gy = df['gy'].mean()
                st.markdown(f"<div class='metric-card-small'><h4>GY</h4><h3>{avg_gy:.2f}</h3><p>deg/s</p></div>", unsafe_allow_html=True)
            
            with col11:
                avg_gz = df['gz'].mean()
                st.markdown(f"<div class='metric-card-small'><h4>GZ</h4><h3>{avg_gz:.2f}</h3><p>deg/s</p></div>", unsafe_allow_html=True)
            
            with col12:
                avg_rotation = df['rotation_magnitude'].mean()
                st.markdown(f"<div class='metric-card-small'><h4>Total Rotation</h4><h3>{avg_rotation:.2f}</h3><p>Magnitude</p></div>", unsafe_allow_html=True)
            
            # Gyroscope graph
            latest_gyro = df.sort_values("timestamp", ascending=False).head(50).sort_values("timestamp", ascending=True)
            fig_gyro = go.Figure()
            
            colors_gyro = ['#e74c3c', '#f39c12', '#9b59b6']
            for i, col in enumerate(['gx', 'gy', 'gz']):
                fig_gyro.add_trace(go.Scatter(
                    x=latest_gyro['timestamp'],
                    y=latest_gyro[col],
                    mode='lines',
                    name=col.upper(),
                    line=dict(color=colors_gyro[i], width=2)
                ))
            
            fig_gyro.update_layout(
                title="<b>Gyroscope Data (GX, GY, GZ)</b>",
                xaxis_title="Time",
                yaxis_title="deg/s",
                plot_bgcolor='#fdf6ec',
                paper_bgcolor='#fdf6ec',
                height=300,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_gyro, use_container_width=True)
            
            st.markdown("</div>", unsafe_allow_html=True)  # Close sensor group

        # ================ TAB 2: SUBJECT INFO (KEEP YOUR ORIGINAL) ================
        with tab2:
            st.subheader("👤 Section 2: Subject Info")

            # Define all subjects (3 COMs)
            all_subjects = ["user_001", "user_002", "user_003"]
            active_subjects = df['id_user'].dropna().unique().tolist()

            # Manual biodata (replace with DB if needed)
            biodata = {
                "user_001": {"Age": 25, "Weight": 60, "Height": 165},
                "user_002": {"Age": 30, "Weight": 70, "Height": 170},
                "user_003": {"Age": 28, "Weight": 55, "Height": 160}
            }

            for sid in all_subjects:
                st.markdown(f"<div class='subject-box'><h3>🧑 Subject {sid}</h3>", unsafe_allow_html=True)

                if sid not in active_subjects:
                    st.markdown("<p style='color:gray;'>❌ Subject not active yet. No data received.</p>", unsafe_allow_html=True)
                else:
                    subj_df = df[df['id_user'] == sid].copy()
                    subj_df = subj_df.sort_values("timestamp", ascending=False)

                    # --- Part 1: Biodata & Latest Vitals ---
                    bio = biodata.get(sid, {})
                    weight = bio.get("Weight", 0)
                    height = bio.get("Height", 0)
                    bmi = round(weight / ((height / 100) ** 2), 1) if weight and height else "N/A"
                    latest = subj_df.iloc[0] if not subj_df.empty else {}

                    st.markdown(f"""
                        <ul>
                            <li><b>Age:</b> {bio.get("Age", "N/A")} years</li>
                            <li><b>Weight:</b> {weight} kg</li>
                            <li><b>Height:</b> {height} cm</li>
                            <li><b>BMI:</b> {bmi}</li>
                            <li><b>SpO₂:</b> <span style='color:#27ae60; font-weight:bold;'>{latest.get('spo2', 'N/A')}</span> %</li>
                            <li><b>HR:</b> <span style='color:#c0392b; font-weight:bold;'>{latest.get('hr', 'N/A')}</span> BPM</li>
                            <li><b>Temp:</b> <span style='color:#e67e22; font-weight:bold;'>{latest.get('temp', 'N/A')}</span> °C</li>
                        </ul>
                    """, unsafe_allow_html=True)

                    # --- Part 2: Graph ---
                    subj_df = subj_df.sort_values("timestamp", ascending=True).set_index("timestamp")
                    fig = go.Figure()
                    for col, color, label in [
                        ("ax", "#2980b9", "Accel X"),
                        ("ay", "#16a085", "Accel Y"),
                        ("az", "#8e44ad", "Accel Z"),
                        ("hr", "#c0392b", "Heart Rate"),
                        ("spo2", "#27ae60", "SpO₂"),
                        ("temp", "#e67e22", "Temperature")
                    ]:
                        if col in subj_df.columns and subj_df[col].notna().any():
                            fig.add_trace(go.Scatter(
                                x=subj_df.index,
                                y=subj_df[col],
                                mode="lines",
                                name=label,
                                line=dict(color=color, width=2)
                            ))
                    fig.update_layout(
                        title=f"<b>Signal Pattern for {sid}</b>",
                        xaxis_title="Timestamp",
                        yaxis_title="Value",
                        plot_bgcolor="#fdf6ec",
                        paper_bgcolor="#fdf6ec",
                        font=dict(size=14),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # --- Part 3: Live Data Table ---
                    st.markdown("<h4>📋 Live Data Table</h4>", unsafe_allow_html=True)
                    st.dataframe(subj_df.reset_index(), use_container_width=True)

                st.markdown("</div>", unsafe_allow_html=True)

        # ================ TAB 3: ANALYTICS (UPDATED FOR ALL SENSORS) ================
        with tab3:
            st.markdown("<h2 style='color:#4B0082;'>📈 Sensor Analytics</h2>", unsafe_allow_html=True)
            
            # Sensor correlation heatmap
            st.markdown("<div class='section' style='border-left:6px solid #9b59b6;'><h3>Section 1: 🔗 Sensor Correlations</h3>", unsafe_allow_html=True)
            
            # Calculate correlations between sensors
            corr_cols = ['hr', 'spo2', 'temp', 'ax', 'ay', 'az', 'gx', 'gy', 'gz']
            corr_df = df[corr_cols].corr()
            
            fig_corr = go.Figure(data=go.Heatmap(
                z=corr_df.values,
                x=corr_df.columns,
                y=corr_df.columns,
                colorscale='RdBu',
                zmid=0,
                text=corr_df.round(2).values,
                texttemplate='%{text}',
                textfont={"size": 10}
            ))
            
            fig_corr.update_layout(
                title="<b>Sensor Correlation Matrix</b>",
                height=500,
                xaxis_title="Sensors",
                yaxis_title="Sensors",
                plot_bgcolor='#fdf6ec',
                paper_bgcolor='#fdf6ec'
            )
            st.plotly_chart(fig_corr, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Sensor statistics
            st.markdown("<div class='section' style='border-left:6px solid #2ecc71;'><h3>Section 2: 📊 Sensor Statistics</h3>", unsafe_allow_html=True)
            
            # Create summary statistics table
            stats_data = []
            sensor_groups = {
                "MAX30102": ['hr', 'spo2', 'temp'],
                "Accelerometer": ['ax', 'ay', 'az'],
                "Gyroscope": ['gx', 'gy', 'gz']
            }
            
            for group_name, sensors in sensor_groups.items():
                for sensor in sensors:
                    if sensor in df.columns:
                        stats_data.append({
                            'Sensor Group': group_name,
                            'Sensor': sensor.upper(),
                            'Mean': df[sensor].mean(),
                            'Std Dev': df[sensor].std(),
                            'Min': df[sensor].min(),
                            'Max': df[sensor].max()
                        })
            
            stats_df = pd.DataFrame(stats_data)
            st.dataframe(stats_df.round(3), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Distribution plots
            st.markdown("<div class='section' style='border-left:6px solid #3498db;'><h3>Section 3: 📉 Sensor Distributions</h3>", unsafe_allow_html=True)
            
            col_dist1, col_dist2, col_dist3 = st.columns(3)
            
            with col_dist1:
                st.markdown("**MAX30102 Distributions**")
                fig_hr = go.Figure(data=[go.Histogram(x=df['hr'], nbinsx=20, marker_color='#c0392b')])
                fig_hr.update_layout(height=250, title="Heart Rate", plot_bgcolor='#fdf6ec', paper_bgcolor='#fdf6ec')
                st.plotly_chart(fig_hr, use_container_width=True)
            
            with col_dist2:
                st.markdown("**Accelerometer Distributions**")
                fig_ax = go.Figure(data=[go.Histogram(x=df['ax'], nbinsx=20, marker_color='#2980b9')])
                fig_ax.update_layout(height=250, title="Accel X", plot_bgcolor='#fdf6ec', paper_bgcolor='#fdf6ec')
                st.plotly_chart(fig_ax, use_container_width=True)
            
            with col_dist3:
                st.markdown("**Gyroscope Distributions**")
                fig_gx = go.Figure(data=[go.Histogram(x=df['gx'], nbinsx=20, marker_color='#8e44ad')])
                fig_gx.update_layout(height=250, title="Gyro X", plot_bgcolor='#fdf6ec', paper_bgcolor='#fdf6ec')
                st.plotly_chart(fig_gx, use_container_width=True)
            
            st.markdown("</div>", unsafe_allow_html=True)

except Exception as e:
    st.error(f"❌ Error fetching data: {e}")