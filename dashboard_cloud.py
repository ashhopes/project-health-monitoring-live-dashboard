import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime

# ============================================================================
# 1. SETUP & KONFIGURASI
# ============================================================================
st.set_page_config(
    page_title="Realtime health monitoring system with LoRa",
    page_icon="🏥",
    layout="wide"
)

API_URL = "https://rhealthmonitoringsystem.infinityfreeapp.com/api.php"

# ============================================================================
# 2. FUNGSI AMBIL DATA DARI API
# ============================================================================
def get_data_from_api():
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(API_URL, headers=headers, timeout=15)
        st.write("🔍 Status code:", response.status_code)
        st.write("🔍 Raw response:", response.text[:200])

        if response.status_code == 200:
            try:
                df = pd.DataFrame(response.json())
                if 'timestamp' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', errors='coerce')
                return df
            except Exception as json_error:
                st.error(f"❌ Gagal parse JSON: {json_error}")
                return pd.DataFrame()
        else:
            st.error(f"❌ API status: {response.status_code}")
            return pd.DataFrame()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Sambungan API gagal: {e}")
        return pd.DataFrame()

# ============================================================================
# 3. PAPARAN UTAMA
# ============================================================================
def main():
    st.title("🏥 Real-Time Health Monitoring")
    st.caption(f"Connected to: `{API_URL}`")
    st.markdown("---")

    # Setup session state untuk refresh selamat
    if "refresh" not in st.session_state:
        st.session_state.refresh = False

    if st.button("🔄 Refresh Data"):
        st.session_state.refresh = True

    if st.session_state.refresh:
        st.session_state.refresh = False
        st.experimental_rerun()

    df = get_data_from_api()

    if df.empty:
        st.warning("⚠️ Tiada data dijumpai dari API.")
        st.stop()

    # Penapisan pengguna
    user_ids = df['user_id'].unique()
    selected_user = st.selectbox("🧑‍⚕️ Pilih Pengguna", user_ids)
    df = df[df['user_id'] == selected_user]

    latest = df.iloc[0]

    # --- A. KAD METRIK ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("User ID", str(latest.get('user_id', 'N/A')))
    col2.metric("Activity", str(latest.get('activity', '-')))
    col3.metric("Heart Rate", f"{latest.get('hr', 0)} BPM")
    col4.metric("Temperature", f"{latest.get('temp', 0)} °C")

    # --- B. GRAF ---
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("📈 Jantung & Suhu")
        fig = px.line(df, x='timestamp', y=['hr', 'temp'], markers=True)
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("📊 Analisis Aktiviti")
        act_counts = df['activity'].value_counts().reset_index()
        act_counts.columns = ['activity', 'count']
        fig_pie = px.pie(act_counts, values='count', names='activity')
        st.plotly_chart(fig_pie, use_container_width=True)

    # --- C. DATA VIEW ---
    with st.expander("Lihat Data Penuh"):
        st.dataframe(df)

    st.success(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    main()