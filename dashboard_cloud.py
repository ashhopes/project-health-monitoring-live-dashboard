import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
import time

st.markdown("""
    <style>
    body {
        background-color: #f2f2f2;
        background-image: url("https://images.unsplash.com/photo-1588776814546-ec7d2c7f1b6b"); /* optional muted background */
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }
    .login-box {
        background-color: #e6e6e6;
        border: 1px solid #999999;
        border-radius: 8px;
        padding: 25px;
        width: 350px;
        margin: auto;
        margin-top: 120px;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.1);
    }
    .login-title {
        text-align: center;
        font-size: 22px;
        font-weight: 500;
        color: #333333;
        margin-bottom: 20px;
    }
    .stTextInput > div > input {
        background-color: #f9f9f9;
        color: #333333;
        border: 1px solid #cccccc;
    }
    .stButton button {
        background-color: #cccccc;
        color: #333333;
        border-radius: 4px;
        border: none;
        padding: 6px 16px;
    }
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
    </style>
""", unsafe_allow_html=True)

# --- Login logic ---
def check_login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.markdown("<div class='login-title'>🔐 Login Page</div>", unsafe_allow_html=True)

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if username == "admin" and password == "moon123":   # ✅ your credentials
                st.session_state.logged_in = True
                st.success("✅ Login successful!")
            else:
                st.error("❌ Invalid username or password")

        st.markdown("</div>", unsafe_allow_html=True)
        st.stop()

# --- Run login check ---
check_login()


# --- Page setup ---
st.set_page_config(page_title="Live Health Monitoring System with LoRa", layout="wide")

# --- Header ---
st.markdown("<h1 style='text-align: center; color:#4B0082;'>🧠 Live Health Monitoring System with LoRa</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Real-time monitoring of vital signs and motion data using LoRa sensors</p>", unsafe_allow_html=True)
st.markdown("---")

# --- Sidebar controls ---
st.sidebar.header("⚙️ Controls")
refresh_rate = st.sidebar.slider("Auto-refresh every (seconds)", 0, 120, 30)
n_samples = st.sidebar.slider("Number of samples to display", 50, 500, 100)
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
            st_autorefresh(interval=refresh_rate * 1000, key="tab1_refresh")
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
            st_autorefresh(interval=refresh_rate * 1000, key="tab2_refresh")
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

                    
                    # --- Part 2: PPG Waveform Graph ---
                    subj_df = subj_df.sort_values("timestamp", ascending=True).set_index("timestamp")
                    fig = go.Figure()

                    # Plot IR signal
                    if "ir" in subj_df.columns and subj_df["ir"].notna().any():
                     fig.add_trace(go.Scatter(
                     x=subj_df.index,
                     y=subj_df["ir"],
                     mode="lines",
                    name="IR Signal",
                    line=dict(color="#8e44ad", width=2)
                    ))

                    # Plot RED signal
                    if "red" in subj_df.columns and subj_df["red"].notna().any():
                        fig.add_trace(go.Scatter(
                        x=subj_df.index,
                        y=subj_df["red"],
                        mode="lines",
                        name="RED Signal",
                        line=dict(color="#e74c3c", width=2)
                    ))

                        fig.update_layout(
                        title=f"<b>PPG Waveform for {sid}</b>",
                        xaxis_title="Timestamp",
                        yaxis_title="Signal Value",
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

        # --- Tab 3: Clustering Results ---
        with tab3:
            st_autorefresh(interval=refresh_rate * 1000, key="tab3_refresh")

            st.subheader("🧪 Health Signal Clustering (SpO₂, HR + Movement)")

            try:
                # Prediction query using your BigQuery ML model
                query_cluster = """
                SELECT *
                FROM ML.PREDICT(MODEL `monitoring-system-with-lora.sdp2_live_monitoring_system.lora_health_data_model`,
                  (SELECT spo2, hr, ax, ay, az, gx, gy, gz
                   FROM `monitoring-system-with-lora.sdp2_live_monitoring_system.lora_health_data_clean2`))
                """
                cluster_df = client.query(query_cluster).to_dataframe()

                # Map cluster IDs to health states
                labels = {0: "Normal", 1: "Active", 2: "Critical"}
                cluster_df["health_state"] = cluster_df["predicted_cluster"].map(labels)

                # Show classified results
                st.dataframe(cluster_df[["spo2", "hr", "predicted_cluster", "health_state"]], use_container_width=True)

                # Distribution chart of health states
                st.subheader("📊 Health State Distribution")
                st.bar_chart(cluster_df["health_state"].value_counts())

                # Cluster averages for interpretation
                avg_query = """
                SELECT predicted_cluster,
                       COUNT(*) AS total_records,
                       AVG(spo2) AS avg_spo2,
                       AVG(hr) AS avg_hr,
                       AVG(ax) AS avg_ax,
                       AVG(ay) AS avg_ay,
                       AVG(az) AS avg_az,
                       AVG(gx) AS avg_gx,
                       AVG(gy) AS avg_gy,
                       AVG(gz) AS avg_gz
                FROM ML.PREDICT(MODEL `monitoring-system-with-lora.sdp2_live_monitoring_system.lora_health_data_model`,
                  (SELECT spo2, hr, ax, ay, az, gx, gy, gz
                   FROM `monitoring-system-with-lora.sdp2_live_monitoring_system.lora_health_data_clean2`))
                GROUP BY predicted_cluster
                ORDER BY predicted_cluster
                """
                avg_df = client.query(avg_query).to_dataframe()
                st.subheader("📊 Cluster Averages (Interpretation)")
                st.dataframe(avg_df, use_container_width=True)
            except Exception as e:
                st.error(f"Error fetching clustering results: {e}")

except Exception as e:
    st.error(f"Error loading dashboard data: {e}")
    st.write(f"Details: {str(e)}")