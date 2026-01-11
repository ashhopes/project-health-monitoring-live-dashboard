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
    .send-data-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .metric-card {
        background: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
        margin: 5px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Header ---
st.markdown("<h1 style='text-align: center; color:#4B0082;'>🏥 Live Health Monitoring System with LoRa</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Real-time monitoring of vital signs and motion data using LoRa sensors</p>", unsafe_allow_html=True)
st.markdown("---")

# ================== NEW: DATA SENDING FUNCTIONALITY ==================

# --- Sidebar controls ---
with st.sidebar:
    st.header("⚙️ Controls")
    
    # Mode selection
    mode = st.radio("Operation Mode:", ["Live Monitoring", "Send Data"])
    
    refresh_rate = st.slider("Auto-refresh every (seconds)", 0, 120, 30)
    n_samples = st.slider("Number of samples to display", 50, 500, 100)
    st.sidebar.info("Project by mOONbLOOM26 🌙")
    
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

# ================== NEW: SEND DATA TAB ==================
if mode == "Send Data":
    st.markdown("<div class='send-data-box'>", unsafe_allow_html=True)
    st.markdown("### 📤 Send Data to BigQuery")
    st.markdown("Generate and send simulated health data to the database")
    st.markdown("</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        subject_id = st.selectbox("Select Subject:", ["user_001", "user_002", "user_003"])
        activity = st.selectbox("Activity:", ["RESTING", "WALKING", "RUNNING"])
        
        if st.button("🎲 Generate Random Data", use_container_width=True):
            # Generate realistic data based on activity
            if activity == "RESTING":
                hr = np.random.randint(60, 80)
                spo2 = np.random.randint(96, 100)
                temp = np.random.uniform(36.2, 36.7)
                ax, ay, az = np.random.uniform(-0.2, 0.2, 3)
            elif activity == "WALKING":
                hr = np.random.randint(75, 95)
                spo2 = np.random.randint(94, 98)
                temp = np.random.uniform(36.5, 37.0)
                ax, ay, az = np.random.uniform(-1.0, 1.0, 3)
            else:  # RUNNING
                hr = np.random.randint(90, 110)
                spo2 = np.random.randint(92, 97)
                temp = np.random.uniform(36.8, 37.5)
                ax, ay, az = np.random.uniform(-2.0, 2.0, 3)
            
            # Generate gyroscope data
            gx, gy, gz = np.random.uniform(-50, 50, 3)
            
            st.session_state.generated_data = {
                'id_user': subject_id,
                'temp': round(temp, 1),
                'spo2': spo2,
                'hr': hr,
                'ax': round(ax, 3),
                'ay': round(ay, 3),
                'az': round(az, 3),
                'gx': round(gx, 2),
                'gy': round(gy, 2),
                'gz': round(gz, 2)
            }
    
    with col2:
        if 'generated_data' in st.session_state:
            st.markdown("### Generated Data")
            data = st.session_state.generated_data
            
            # Display metrics in cards
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.markdown(f"<div class='metric-card'><h3>{data['hr']}</h3><p>Heart Rate</p></div>", unsafe_allow_html=True)
            with col_b:
                st.markdown(f"<div class='metric-card'><h3>{data['spo2']}%</h3><p>SpO₂</p></div>", unsafe_allow_html=True)
            with col_c:
                st.markdown(f"<div class='metric-card'><h3>{data['temp']}°C</h3><p>Temperature</p></div>", unsafe_allow_html=True)
            
            # Display all data
            st.json(data)
            
            if st.button("📤 Send to BigQuery", type="primary", use_container_width=True):
                try:
                    # Insert data into BigQuery
                    rows_to_insert = [{
                        'id_user': data['id_user'],
                        'timestamp': datetime.now(pytz.timezone('Asia/Kuala_Lumpur')).strftime('%Y-%m-%d %H:%M:%S'),
                        'temp': data['temp'],
                        'spo2': data['spo2'],
                        'hr': data['hr'],
                        'ax': data['ax'],
                        'ay': data['ay'],
                        'az': data['az'],
                        'gx': data['gx'],
                        'gy': data['gy'],
                        'gz': data['gz'],
                        'activity': activity
                    }]
                    
                    errors = client.insert_rows_json(table_id, rows_to_insert)
                    
                    if errors == []:
                        st.success(f"✅ Data sent successfully for {subject_id}!")
                        st.balloons()
                        del st.session_state.generated_data
                    else:
                        st.error(f"❌ Error sending data: {errors}")
                except Exception as e:
                    st.error(f"❌ Database error: {str(e)}")
    
    # Manual data entry option
    st.markdown("---")
    st.markdown("### ✏️ Manual Data Entry")
    
    with st.form("manual_data_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            manual_hr = st.number_input("Heart Rate (BPM)", 40, 200, 75)
            manual_temp = st.number_input("Temperature (°C)", 35.0, 42.0, 36.6)
        with col2:
            manual_spo2 = st.number_input("SpO₂ (%)", 80, 100, 98)
            manual_ax = st.number_input("Accel X", -5.0, 5.0, 0.1)
        with col3:
            manual_ay = st.number_input("Accel Y", -5.0, 5.0, 0.2)
            manual_az = st.number_input("Accel Z", -5.0, 5.0, 0.3)
        
        manual_gx = st.number_input("Gyro X", -100.0, 100.0, 10.0)
        manual_gy = st.number_input("Gyro Y", -100.0, 100.0, 5.0)
        manual_gz = st.number_input("Gyro Z", -100.0, 100.0, 15.0)
        
        if st.form_submit_button("📤 Send Manual Data"):
            try:
                rows_to_insert = [{
                    'id_user': subject_id,
                    'timestamp': datetime.now(pytz.timezone('Asia/Kuala_Lumpur')).strftime('%Y-%m-%d %H:%M:%S'),
                    'temp': manual_temp,
                    'spo2': manual_spo2,
                    'hr': manual_hr,
                    'ax': manual_ax,
                    'ay': manual_ay,
                    'az': manual_az,
                    'gx': manual_gx,
                    'gy': manual_gy,
                    'gz': manual_gz,
                    'activity': activity
                }]
                
                errors = client.insert_rows_json(table_id, rows_to_insert)
                
                if errors == []:
                    st.success("✅ Manual data sent successfully!")
                else:
                    st.error(f"❌ Error: {errors}")
            except Exception as e:
                st.error(f"❌ Database error: {str(e)}")

else:  # ================== LIVE MONITORING MODE ==================
    # --- Fetch latest data ---
    @st.cache_data(ttl=30)
    def fetch_latest(n=100):
        query = f"""
            SELECT id_user, timestamp, temp, spo2, hr, ax, ay, az, gx, gy, gz
            FROM `{table_id}`
            ORDER BY timestamp DESC
            LIMIT {n}
        """
        return client.query(query).to_dataframe()

    try:
        df = fetch_latest(n_samples)
        if df.empty:
            st.info("No data found yet. Upload from your local app first.")
        else:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors="coerce")

            # --- Get active subject IDs dynamically ---
            subject_query = f"""
                SELECT DISTINCT id_user
                FROM `{table_id}`
                WHERE id_user IS NOT NULL
            """
            subject_ids = client.query(subject_query).to_dataframe()['id_user'].tolist()

            # --- Tabs ---
            tab1, tab2, tab3 = st.tabs(["📈 Overview", "👤 Subject Info", "🤖 Predictions"])

            # --- Layout 1: System Overview ---
            with tab1:
                st.markdown("<h2 style='color:#4B0082;'>📈 System Overview</h2>", unsafe_allow_html=True)

                # Section 1: Active Subjects
                st.markdown("<div class='section' style='border-left:6px solid #3498db;'><h3>👥Section 1: Active Subjects</h3>", unsafe_allow_html=True)
                active_subjects = df['id_user'].dropna().unique().tolist()
                active_subjects = df['id_user'].dropna().unique().tolist()
                st.markdown(f"<b>Currently receiving data from <span style='color:#3498db;'>{len(active_subjects)}</span> subjects:</b>", unsafe_allow_html=True)
                st.json({i: sid for i, sid in enumerate(active_subjects)})
                st.markdown("</div>", unsafe_allow_html=True)

                # Section 2: Alerts
                st.markdown("<div class='section' style='border-left:6px solid #e67e22;'><h3>Section 2:⚠️ Alert Notification</h3>", unsafe_allow_html=True)
                alerts = []
                if 'spo2' in df.columns and (df['spo2'] < 95).any():
                    low_spo2_users = df[df['spo2'] < 95]['id_user'].unique().tolist()
                    alerts.append(f"SpO₂ below 95%: <b><span style='color:red;'>{', '.join(low_spo2_users)}</span></b>")
                if 'hr' in df.columns and (df['hr'] > 120).any():
                    high_hr_users = df[df['hr'] > 120]['id_user'].unique().tolist()
                    alerts.append(f"HR > 120 BPM: <b><span style='color:red;'>{', '.join(high_hr_users)}</span></b>")
                if 'temp' in df.columns and (df['temp'] > 38).any():
                    fever_users = df[df['temp'] > 38]['id_user'].unique().tolist()
                    alerts.append(f"Temp > 38°C: <b><span style='color:red;'>{', '.join(fever_users)}</span></b>")
                if alerts:
                    st.markdown("<ul>" + "".join([f"<li>{msg}</li>" for msg in alerts]) + "</ul>", unsafe_allow_html=True)
                else:
                    st.markdown("<p style='color:green;'><b>✅ All vitals are within normal range.</b></p>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

                # Section 3: Summary Metrics
                st.markdown("<div class='section' style='border-left:6px solid #2ecc71;'><h3>Section 3: 📊 Summary Metrics</h3>", unsafe_allow_html=True)
                col1, col2, col3, col4 = st.columns(4)
                col1.markdown(f"*Average HR:* <span style='color:#c0392b;'><b>{df['hr'].mean():.1f} BPM</b></span>", unsafe_allow_html=True)
                col2.markdown(f"*minSpO₂:* <span style='color:#27ae60;'><b>{df['spo2'].min():.1f} %</b></span>", unsafe_allow_html=True)
                col3.markdown(f"*Average Temp:* <span style='color:#e67e22;'><b>{df['temp'].mean():.1f} °C</b></span>", unsafe_allow_html=True)
                col4.markdown(f"*maxTemp:* <span style='color:#e74c3c;'><b>{df['temp'].max():.1f} °C</b></span>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

                # Section 4: Health Trend Comparison
                st.markdown("<div class='section' style='border-left:6px solid #9b59b6;'><h3>Section 4: 📈 Health Trend Comparison</h3>", unsafe_allow_html=True)
                avg_hr = df['hr'].mean()
                avg_spo2 = df['spo2'].mean()
                avg_temp = df['temp'].mean()

                fig = go.Figure(data=[
                    go.Bar(name="Heart Rate (BPM)", x=["HR"], y=[avg_hr], marker_color="#c0392b"),
                    go.Bar(name="SpO₂ (%)", x=["SpO₂"], y=[avg_spo2], marker_color="#27ae60"),
                    go.Bar(name="Temperature (°C)", x=["Temp"], y=[avg_temp], marker_color="#e67e22")
                ])
                fig.update_layout(
                    title="<b>Average Health Metrics</b>",
                    yaxis_title="Value",
                    plot_bgcolor="#fdf6ec",
                    paper_bgcolor="#fdf6ec",
                    height=500,
                    font=dict(size=14)
                )
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            # --- Layout 2: Subject Info ---
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

            # --- Layout 3: Predictions ---
            with tab3:
                st.subheader("🤖 Section 3: ML Predictions by Subject")

                # Query ML predictions from BigQuery
                pred_query = f"""
                    SELECT timestamp, id_user, temp, spo2, hr, ax, ay, az, gx, gy, gz, predicted_cluster
                    FROM ML.PREDICT(
                        MODEL `monitoring-system-with-lora.sdp2_live_monitoring_system.anomaly_model`,
                        (
                            SELECT temp, spo2, hr, ax, ay, az, gx, gy, gz, timestamp, id_user
                            FROM `{table_id}`
                            ORDER BY timestamp DESC
                            LIMIT 100
                        )
                    )
                """
                pred_df = client.query(pred_query).to_dataframe()

                # Loop through subjects
                for sid in subject_ids:
                    st.markdown("<div class='prediction-box'>", unsafe_allow_html=True)
                    st.markdown(f"### 🔍 Predictions for Subject {sid}")

                    sub_pred = pred_df[pred_df['id_user'] == sid]
                    if sub_pred.empty:
                        st.warning(f"No predictions found for Subject {sid}")
                    else:
                        # Show prediction table
                        st.dataframe(sub_pred, use_container_width=True)

                        # Show bar chart of cluster counts
                        cluster_counts = sub_pred.groupby("predicted_cluster").size()
                        st.bar_chart(cluster_counts)

                    st.markdown("</div>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"❌ Error fetching data: {e}")