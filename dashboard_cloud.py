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
    try:
        response = requests.get(API_URL, timeout=15)
        if response.status_code == 200:
            df = pd.DataFrame(response.json())
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', errors='coerce')
            return df
        else:
            st.error(f"❌ Error API: Status {response.status_code}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Error API: {e}")
        return pd.DataFrame()

# ============================================================================
# 3. PAPARAN UTAMA
# ============================================================================
def main():
    st.title("🏥 Real-Time Health Monitoring")
    st.caption(f"Connected to: `{API_URL}`")
    st.markdown("---")

    # Butang manual refresh
    if st.button("🔄 Refresh Data"):
        st.experimental_rerun()

    df = get_data_from_api()

    if not df.empty:
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
    else:
        st.warning("⚠️ Tiada data dijumpai dari API.")
        st.info("Pastikan `api.php` berfungsi dan ada data dalam table `sensor_logs`.")

if __name__ == "__main__":
    main()