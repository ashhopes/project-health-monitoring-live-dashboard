Update dashboard_cloud.py
9878d0e
dashboard_cloud.py
@@ -1,7 +1,7 @@
# dashboard_cloud.py - SIMULATED DATA VERSION
# dashboard_cloud.py - UPDATED WITH REAL STEMCUBE DATA
"""
Live Health Monitoring Dashboard with LoRa
Streamlit Cloud Version - No BigQuery Required
Streamlit Cloud Version - Supports STEMCUBE Real Data
"""

# ================ IMPORTS ================


@@ -51,33 +51,72 @@ check_login()

# ================ PAGE SETUP ================
st.set_page_config(
    page_title="Live Health Monitoring System with LoRa", 
    page_title="STEMCUBE Health Monitoring", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================ HEADER ================
st.markdown("<h1 style='text-align: center; color:#4B0082;'>🩺 Live Health Monitoring System with LoRa</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Real-time monitoring of vital signs and motion data using LoRa sensors</p>", unsafe_allow_html=True)
st.markdown("---")
st.markdown("""
<div style='background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
            padding: 25px; border-radius: 15px; color: white; text-align: center; margin-bottom: 25px;'>
    <h1 style='margin: 0;'>🏥 STEMCUBE Real-Time Health Monitoring</h1>
    <p style='margin: 5px 0 0 0;'>Live data from STEMCUBE sensors via LoRa • NODE_e661</p>
</div>
""", unsafe_allow_html=True)

# ================ INITIALIZE SESSION STATE ================
if 'stemcube_data' not in st.session_state:
    st.session_state.stemcube_data = []
if 'last_stemcube_update' not in st.session_state:
    st.session_state.last_stemcube_update = None
if 'stemcube_connected' not in st.session_state:
    st.session_state.stemcube_connected = False

# ================ SIDEBAR CONTROLS ================
st.sidebar.header("⚙️ Controls")