# --- Login logic ---
def check_login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.markdown("""
            <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                     padding: 50px; border-radius: 20px; text-align: center;'>
                <h1 style='color: white;'>🔐 Health Monitoring System</h1>
                <p style='color: white;'>Please login to access the dashboard</p>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.button("Login", type="primary", use_container_width=True):
                if username == "admin" and password == "admin123":
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        
        st.markdown("</div>", unsafe_allow_html=True)
        st.stop()

# --- Run login check ---
check_login()

# --- Page setup ---
st.set_page_config(
    page_title="Live Health Monitoring System with LoRa", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Header ---
st.markdown("<h1 style='text-align: center; color:#4B0082;'>🩺 Live Health Monitoring System with LoRa</h1>", unsafe_allow_html=True)
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
        SELECT id_user, timestamp, temp, spo2, hr, ax, ay, az, gx, gy, gz,
               packet_rssi, packet_snr, battery_level, packet_counter, packet_loss
        FROM `{table_id}`
        ORDER BY timestamp DESC
        LIMIT {n}
    """
    return client.query(query).to_dataframe()

# --- Activity classification function ---
def classify_activity(ax, ay, az, gx, gy, gz):
    # Simple activity classification based on accelerometer magnitude
    magnitude = np.sqrt(ax**2 + ay**2 + az**2)
    
    if magnitude < 1.1:
        return "Resting/Sleeping"
    elif magnitude < 2.0:
        return "Light Activity"
    elif magnitude < 3.5:
        return "Walking"
    elif magnitude < 5.0:
        return "Brisk Walking"
    else:
        return "Running/Vigorous"

# --- Get all available node IDs ---
@st.cache_data(ttl=300)
def get_available_nodes():
    query = f"""
        SELECT DISTINCT id_user
        FROM `{table_id}`
        WHERE id_user IS NOT NULL
        ORDER BY id_user
    """
    result = client.query(query).to_dataframe()
    return result['id_user'].tolist()

try:
    df = fetch_latest(n_samples)
    if df.empty:
        st.info("No data found yet. Upload from your local app first.")
    else:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors="coerce")
        
        # Get available nodes
        available_nodes = get_available_nodes()
        
        # Sidebar node selection
        st.sidebar.header("📟 Node Selection")
        selected_node = st.sidebar.selectbox(
            "Select Node ID",
            available_nodes,
            help="Choose which sensor node to monitor"
        )
        
        # Filter data for selected node
        node_df = df[df['id_user'] == selected_node].copy()
        node_df = node_df.sort_values("timestamp", ascending=True)
        
        # --- Tabs ---
        tab1, tab2, tab3 = st.tabs(["🩺 Health Vitals", "📡 System & LoRa Status", "📊 Analytics & Trends"])

        # --- TAB 1: Health Vitals ---
        with tab1:
            st.header(f"Health Vitals - Node: {selected_node}")
            
            if node_df.empty:
                st.warning(f"No data available for node {selected_node}")
            else:
                # Get latest values
                latest = node_df.iloc[-1]
                
                # Row 1: Current vitals with metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    # Heart Rate
                    hr_value = latest.get('hr', 0)
                    st.metric(
                        label="Heart Rate",
                        value=f"{hr_value:.0f} BPM",
                        delta=f"Trend: {'↑' if len(node_df) > 1 and node_df['hr'].iloc[-1] > node_df['hr'].iloc[-2] else '↓'}"
                    )
                    # Heart rate line chart
                    if len(node_df) > 1:
                        fig_hr = go.Figure()
                        fig_hr.add_trace(go.Scatter(
                            x=node_df['timestamp'],
                            y=node_df['hr'],
                            mode='lines',
                            name='Heart Rate',
                            line=dict(color='#FF6B6B', width=3)
                        ))
                        fig_hr.update_layout(
                            title="Heart Rate Trend",
                            height=200,
                            margin=dict(t=30, b=30, l=30, r=30),
                            showlegend=False,
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)'
                        )
                        st.plotly_chart(fig_hr, use_container_width=True, config={'displayModeBar': False})
                
                with col2:
                    # SpO2 Gauge
                    spo2_value = latest.get('spo2', 0)
                    spo2_color = "green" if spo2_value >= 95 else "red" if spo2_value < 90 else "orange"
                    
                    fig_spo2 = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=spo2_value,
                        title={'text': "SpO₂ (%)"},
                        domain={'x': [0, 1], 'y': [0, 1]},
                        gauge={
                            'axis': {'range': [85, 100]},
                            'bar': {'color': spo2_color},
                            'steps': [
                                {'range': [85, 90], 'color': "red"},
                                {'range': [90, 95], 'color': "orange"},
                                {'range': [95, 100], 'color': "green"}
                            ],
                            'threshold': {
                                'line': {'color': "black", 'width': 4},
                                'thickness': 0.75,
                                'value': spo2_value
                            }
                        }
                    ))
                    fig_spo2.update_layout(height=250)
                    st.plotly_chart(fig_spo2, use_container_width=True, config={'displayModeBar': False})
                
                with col3:
                    # Temperature
                    temp_value = latest.get('temp', 0)
                    temp_status = "🟢 Normal" if 36 <= temp_value <= 37.5 else "🟡 Mild" if 37.6 <= temp_value <= 38 else "🔴 Fever"
                    st.metric(
                        label="Body Temperature",
                        value=f"{temp_value:.1f} °C",
                        delta=temp_status
                    )
                    # Temperature trend
                    if len(node_df) > 1:
                        fig_temp = go.Figure()
                        fig_temp.add_trace(go.Scatter(
                            x=node_df['timestamp'],
                            y=node_df['temp'],
                            mode='lines',
                            name='Temperature',
                            line=dict(color='#FFA726', width=3)
                        ))
                        # Add fever threshold line
                        fig_temp.add_hline(y=38, line_dash="dash", line_color="red", 
                                         annotation_text="Fever Threshold", 
                                         annotation_position="bottom right")
                        fig_temp.update_layout(
                            title="Temperature Trend",
                            height=200,
                            margin=dict(t=30, b=30, l=30, r=30),
                            showlegend=False,
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)'
                        )
                        st.plotly_chart(fig_temp, use_container_width=True, config={'displayModeBar': False})
                
                with col4:
                    # Activity Classification
                    # Calculate activity from latest motion data
                    ax, ay, az = latest.get('ax', 0), latest.get('ay', 0), latest.get('az', 0)
                    gx, gy, gz = latest.get('gx', 0), latest.get('gy', 0), latest.get('gz', 0)
                    activity = classify_activity(ax, ay, az, gx, gy, gz)
                    
                    # Activity indicator with emoji
                    activity_emoji = {
                        "Resting/Sleeping": "😴",
                        "Light Activity": "🚶‍♂️",
                        "Walking": "🚶‍♂️",
                        "Brisk Walking": "🏃‍♂️",
                        "Running/Vigorous": "🏃‍♂️💨"
                    }
                    
                    st.markdown(f"""
                    <div style='text-align: center; padding: 20px; border-radius: 10px; background: #f8f9fa;'>
                        <h3 style='margin-bottom: 10px;'>Activity Level</h3>
                        <div style='font-size: 48px; margin: 10px 0;'>{activity_emoji.get(activity, '📊')}</div>
                        <h2 style='color: #4B0082;'>{activity}</h2>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Activity history (last 10 classifications)
                    if len(node_df) > 1:
                        activity_history = []
                        for i, row in node_df.tail(10).iterrows():
                            act = classify_activity(row.get('ax', 0), row.get('ay', 0), 
                                                   row.get('az', 0), row.get('gx', 0), 
                                                   row.get('gy', 0), row.get('gz', 0))
                            activity_history.append(act)
                        
                        st.markdown("**Recent Activity:**")
                        st.write(", ".join(activity_history[-5:]))
                
                # Row 2: Detailed vitals charts
                st.subheader("📈 Detailed Vitals Timeline")
                
                # Create combined plot
                fig_combined = make_subplots(
                    rows=3, cols=1,
                    subplot_titles=("Heart Rate (BPM)", "SpO₂ (%)", "Temperature (°C)"),
                    vertical_spacing=0.1,
                    shared_xaxes=True
                )
                
                # Add traces
                fig_combined.add_trace(
                    go.Scatter(x=node_df['timestamp'], y=node_df['hr'], 
                              mode='lines', name='HR', line=dict(color='#FF6B6B')),
                    row=1, col=1
                )
                
                fig_combined.add_trace(
                    go.Scatter(x=node_df['timestamp'], y=node_df['spo2'], 
                              mode='lines', name='SpO2', line=dict(color='#4ECDC4')),
                    row=2, col=1
                )
                
                fig_combined.add_trace(
                    go.Scatter(x=node_df['timestamp'], y=node_df['temp'], 
                              mode='lines', name='Temp', line=dict(color='#FFA726')),
                    row=3, col=1
                )
                
                # Add threshold lines
                fig_combined.add_hline(y=120, row=1, col=1, line_dash="dash", 
                                      line_color="red", annotation_text="High HR")
                fig_combined.add_hline(y=95, row=2, col=1, line_dash="dash", 
                                      line_color="red", annotation_text="Low SpO2")
                fig_combined.add_hline(y=38, row=3, col=1, line_dash="dash", 
                                      line_color="red", annotation_text="Fever")
                
                fig_combined.update_layout(
                    height=600,
                    showlegend=True,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                
                st.plotly_chart(fig_combined, use_container_width=True)

        # --- TAB 2: System & LoRa Status ---
        with tab2:
            st.header(f"System Status - Node: {selected_node}")
            
            if node_df.empty:
                st.warning(f"No system data available for node {selected_node}")
            else:
                latest = node_df.iloc[-1]
                
                # Row 1: Key system metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    # LoRa Signal Strength
                    rssi = latest.get('packet_rssi', -120)
                    snr = latest.get('packet_snr', 0)
                    
                    st.markdown(f"""
                    <div style='text-align: center; padding: 20px; border-radius: 10px; background: #f8f9fa;'>
                        <h3>📶 LoRa Signal</h3>
                        <h1 style='color: {'green' if rssi > -100 else 'orange' if rssi > -120 else 'red'};'>
                            {rssi} dBm
                        </h1>
                        <p>SNR: {snr} dB</p>
                        <p>{'Excellent' if rssi > -90 else 'Good' if rssi > -100 else 'Fair' if rssi > -120 else 'Poor'}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # RSSI history chart
                    if len(node_df) > 1 and 'packet_rssi' in node_df.columns:
                        fig_rssi = go.Figure()
                        fig_rssi.add_trace(go.Scatter(
                            x=node_df['timestamp'],
                            y=node_df['packet_rssi'],
                            mode='lines+markers',
                            name='RSSI',
                            line=dict(color='#3498db', width=2)
                        ))
                        fig_rssi.add_hline(y=-100, line_dash="dash", line_color="orange")
                        fig_rssi.add_hline(y=-120, line_dash="dash", line_color="red")
                        fig_rssi.update_layout(
                            title="Signal Strength History",
                            height=200,
                            yaxis_title="RSSI (dBm)",
                            plot_bgcolor='rgba(0,0,0,0)'
                        )
                        st.plotly_chart(fig_rssi, use_container_width=True)
                
                with col2:
                    # Packet Delivery
                    packet_counter = latest.get('packet_counter', 0)
                    packet_loss = latest.get('packet_loss', 0)
                    delivery_rate = ((packet_counter - packet_loss) / packet_counter * 100) if packet_counter > 0 else 100
                    
                    fig_delivery = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=delivery_rate,
                        title={'text': "Packet Delivery Rate"},
                        domain={'x': [0, 1], 'y': [0, 1]},
                        gauge={
                            'axis': {'range': [0, 100]},
                            'bar': {'color': "green" if delivery_rate > 95 else "orange" if delivery_rate > 80 else "red"},
                            'steps': [
                                {'range': [0, 80], 'color': "red"},
                                {'range': [80, 95], 'color': "orange"},
                                {'range': [95, 100], 'color': "green"}
                            ]
                        }
                    ))
                    fig_delivery.update_layout(height=250)
                    st.plotly_chart(fig_delivery, use_container_width=True)
                    
                    st.metric(
                        label="Packets",
                        value=f"Sent: {packet_counter}",
                        delta=f"Lost: {packet_loss}"
                    )
                
                with col3:
                    # Battery & Latency
                    battery = latest.get('battery_level', 100)
                    
                    fig_battery = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=battery,
                        title={'text': "Battery Level"},
                        domain={'x': [0, 1], 'y': [0, 1]},
                        gauge={
                            'axis': {'range': [0, 100]},
                            'bar': {'color': "green" if battery > 50 else "orange" if battery > 20 else "red"},
                            'steps': [
                                {'range': [0, 20], 'color': "red"},
                                {'range': [20, 50], 'color': "orange"},
                                {'range': [50, 100], 'color': "green"}
                            ]
                        }
                    ))
                    fig_battery.update_layout(height=250)
                    st.plotly_chart(fig_battery, use_container_width=True)
                    
                    # Latency calculation
                    if len(node_df) > 1:
                        timestamps = node_df['timestamp'].tail(10)
                        time_diffs = timestamps.diff().dropna()
                        avg_latency = time_diffs.mean().total_seconds() if not time_diffs.empty else 0
                        st.metric(
                            label="Update Interval",
                            value=f"{avg_latency:.1f} sec",
                            delta="Average"
                        )
                
                # Row 2: System Information
                st.subheader("📋 System Information")
                
                sys_info_col1, sys_info_col2 = st.columns(2)
                
                with sys_info_col1:
                    st.markdown("""
                    ### Node Details
                    - **Node ID:** {node_id}
                    - **Last Update:** {last_update}
                    - **Data Points:** {data_points}
                    - **Sample Rate:** 1 Hz
                    - **Transmission Power:** 14 dBm
                    - **Frequency Band:** 915 MHz
                    """.format(
                        node_id=selected_node,
                        last_update=latest['timestamp'].strftime("%Y-%m-%d %H:%M:%S") if 'timestamp' in latest else "N/A",
                        data_points=len(node_df)
                    ))
                
                with sys_info_col2:
                    st.markdown("""
                    ### Connection Status
                    - **Gateway Distance:** ~100m (estimated)
                    - **Modulation:** LoRa (SF7, BW125)
                    - **Encryption:** AES-128
                    - **Data Format:** JSON
                    - **Cloud Platform:** Google Cloud
                    - **Storage:** BigQuery
                    """)
                
                # Row 3: Recent Transmission Log
                st.subheader("📨 Recent Transmission Log")
                
                log_df = node_df[['timestamp', 'packet_rssi', 'packet_snr', 'battery_level']].tail(10)
                st.dataframe(
                    log_df.style.format({
                        'packet_rssi': '{:.0f} dBm',
                        'packet_snr': '{:.1f} dB',
                        'battery_level': '{:.1f}%'
                    }),
                    use_container_width=True
                )

        # --- TAB 3: Analytics & Trends ---
        with tab3:
            st.header(f"Analytics & Trends - Node: {selected_node}")
            
            if node_df.empty:
                st.warning(f"No analytics data available for node {selected_node}")
            else:
                # Row 1: Activity Timeline
                st.subheader("🏃 Activity Timeline")
                
                # Calculate activity for each timestamp
                node_df['activity'] = node_df.apply(
                    lambda row: classify_activity(
                        row.get('ax', 0), row.get('ay', 0), row.get('az', 0),
                        row.get('gx', 0), row.get('gy', 0), row.get('gz', 0)
                    ), axis=1
                )
                
                # Activity distribution
                activity_counts = node_df['activity'].value_counts()
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Stacked area chart for activity over time
                    activity_categories = ["Resting/Sleeping", "Light Activity", "Walking", "Brisk Walking", "Running/Vigorous"]
                    
                    fig_activity = go.Figure()
                    
                    # Create binary columns for each activity
                    for activity in activity_categories:
                        mask = node_df['activity'] == activity
                        fig_activity.add_trace(go.Scatter(
                            x=node_df['timestamp'],
                            y=mask.astype(int),
                            mode='lines',
                            name=activity,
                            stackgroup='one',
                            line=dict(width=0.5)
                        ))
                    
                    fig_activity.update_layout(
                        title="Activity Distribution Over Time",
                        yaxis_title="Activity State",
                        xaxis_title="Time",
                        height=400,
                        plot_bgcolor='rgba(0,0,0,0)'
                    )
                    st.plotly_chart(fig_activity, use_container_width=True)
                
                with col2:
                    # Activity pie chart
                    fig_pie = go.Figure(data=[go.Pie(
                        labels=activity_counts.index,
                        values=activity_counts.values,
                        hole=.3,
                        marker_colors=['#FF9999', '#66B3FF', '#99FF99', '#FFCC99', '#FFD700']
                    )])
                    fig_pie.update_layout(
                        title="Activity Distribution",
                        height=400
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                # Row 2: Daily Summary
                st.subheader("📅 Daily Summary")
                
                # Group by date (if data spans multiple days)
                node_df['date'] = node_df['timestamp'].dt.date
                
                if len(node_df['date'].unique()) > 1:
                    daily_summary = node_df.groupby('date').agg({
                        'hr': ['mean', 'max', 'min'],
                        'spo2': ['mean', 'min'],
                        'temp': ['mean', 'max']
                    }).round(1)
                    
                    daily_summary.columns = ['_'.join(col).strip() for col in daily_summary.columns.values]
                    daily_summary = daily_summary.reset_index()
                    
                    st.dataframe(daily_summary, use_container_width=True)
                else:
                    # Single day summary
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Average HR", f"{node_df['hr'].mean():.1f} BPM")
                        st.metric("Max HR", f"{node_df['hr'].max():.1f} BPM")
                        st.metric("Min HR", f"{node_df['hr'].min():.1f} BPM")
                    
                    with col2:
                        st.metric("Average SpO₂", f"{node_df['spo2'].mean():.1f}%")
                        st.metric("Min SpO₂", f"{node_df['spo2'].min():.1f}%")
                        st.metric("Time <95%", f"{(node_df['spo2'] < 95).sum()} samples")
                    
                    with col3:
                        st.metric("Average Temp", f"{node_df['temp'].mean():.1f}°C")
                        st.metric("Max Temp", f"{node_df['temp'].max():.1f}°C")
                        st.metric("Fever Events", f"{(node_df['temp'] > 38).sum()} samples")
                
                # Row 3: Alerts & Thresholds
                st.subheader("🚨 Alert Summary")
                
                # Calculate alerts
                alerts_data = []
                
                # High HR alerts
                high_hr_mask = node_df['hr'] > 120
                if high_hr_mask.any():
                    high_hr_times = node_df[high_hr_mask]['timestamp'].dt.strftime('%H:%M:%S').tolist()
                    alerts_data.append({
                        'Type': 'High Heart Rate',
                        'Count': high_hr_mask.sum(),
                        'Details': f"HR > 120 BPM at: {', '.join(high_hr_times[-3:])}",
                        'Severity': 'High'
                    })
                
                # Low SpO2 alerts
                low_spo2_mask = node_df['spo2'] < 95
                if low_spo2_mask.any():
                    low_spo2_times = node_df[low_spo2_mask]['timestamp'].dt.strftime('%H:%M:%S').tolist()
                    alerts_data.append({
                        'Type': 'Low SpO₂',
                        'Count': low_spo2_mask.sum(),
                        'Details': f"SpO₂ < 95% at: {', '.join(low_spo2_times[-3:])}",
                        'Severity': 'Medium'
                    })
                
                # Fever alerts
                fever_mask = node_df['temp'] > 38
                if fever_mask.any():
                    fever_times = node_df[fever_mask]['timestamp'].dt.strftime('%H:%M:%S').tolist()
                    alerts_data.append({
                        'Type': 'Fever',
                        'Count': fever_mask.sum(),
                        'Details': f"Temp > 38°C at: {', '.join(fever_times[-3:])}",
                        'Severity': 'High'
                    })
                
                if alerts_data:
                    alerts_df = pd.DataFrame(alerts_data)
                    st.dataframe(alerts_df, use_container_width=True)
                    
                    # Alert timeline
                    fig_alerts = go.Figure()
                    
                    if high_hr_mask.any():
                        fig_alerts.add_trace(go.Scatter(
                            x=node_df['timestamp'][high_hr_mask],
                            y=[1] * high_hr_mask.sum(),
                            mode='markers',
                            name='High HR',
                            marker=dict(color='red', size=10, symbol='triangle-up')
                        ))
                    
                    if low_spo2_mask.any():
                        fig_alerts.add_trace(go.Scatter(
                            x=node_df['timestamp'][low_spo2_mask],
                            y=[2] * low_spo2_mask.sum(),
                            mode='markers',
                            name='Low SpO₂',
                            marker=dict(color='orange', size=10, symbol='square')
                        ))
                    
                    if fever_mask.any():
                        fig_alerts.add_trace(go.Scatter(
                            x=node_df['timestamp'][fever_mask],
                            y=[3] * fever_mask.sum(),
                            mode='markers',
                            name='Fever',
                            marker=dict(color='purple', size=10, symbol='x')
                        ))
                    
                    fig_alerts.update_layout(
                        title="Alert Timeline",
                        yaxis=dict(
                            tickmode='array',
                            tickvals=[1, 2, 3],
                            ticktext=['High HR', 'Low SpO₂', 'Fever'],
                            range=[0.5, 3.5]
                        ),
                        height=300,
                        plot_bgcolor='rgba(0,0,0,0)'
                    )
                    st.plotly_chart(fig_alerts, use_container_width=True)
                else:
                    st.success("✅ No alerts detected in the current data")
                
                # Row 4: Export & Download
                st.subheader("📥 Export Data")
                
                export_col1, export_col2, export_col3 = st.columns(3)
                
                with export_col1:
                    if st.button("📋 Copy Current Data", use_container_width=True):
                        st.session_state.clipboard = node_df.to_string()
                        st.success("Data copied to clipboard!")
                
                with export_col2:
                    # Convert to CSV
                    csv = node_df.to_csv(index=False)
                    st.download_button(
                        label="💾 Download CSV",
                        data=csv,
                        file_name=f"health_data_{selected_node}_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                with export_col3:
                    # Convert to Excel
                    excel_buffer = BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                        node_df.to_excel(writer, index=False, sheet_name='Health Data')
                        # Add summary sheet
                        summary = pd.DataFrame({
                            'Metric': ['Average HR', 'Average SpO2', 'Average Temp', 'Total Alerts'],
                            'Value': [
                                f"{node_df['hr'].mean():.1f} BPM",
                                f"{node_df['spo2'].mean():.1f}%",
                                f"{node_df['temp'].mean():.1f}°C",
                                len(alerts_data)
                            ]
                        })
                        summary.to_excel(writer, index=False, sheet_name='Summary')
                    
                    st.download_button(
                        label="📊 Download Excel Report",
                        data=excel_buffer.getvalue(),
                        file_name=f"health_report_{selected_node}_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                
                # Feature Importance (if you have ML model)
                st.subheader("🤖 Feature Importance")
                
                # Mock feature importance (replace with actual ML model output)
                feature_importance = {
                    'Heart Rate': 0.35,
                    'SpO₂': 0.25,
                    'Acceleration X': 0.12,
                    'Acceleration Y': 0.10,
                    'Acceleration Z': 0.08,
                    'Gyro X': 0.05,
                    'Gyro Y': 0.03,
                    'Gyro Z': 0.02
                }
                
                importance_df = pd.DataFrame(
                    list(feature_importance.items()),
                    columns=['Feature', 'Importance']
                ).sort_values('Importance', ascending=False)
                
                fig_importance = go.Figure(go.Bar(
                    x=importance_df['Importance'],
                    y=importance_df['Feature'],
                    orientation='h',
                    marker_color='#4B0082'
                ))
                
                fig_importance.update_layout(
                    title="Sensor Feature Importance for Activity Classification",
                    height=400,
                    xaxis_title="Importance Score",
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                
                st.plotly_chart(fig_importance, use_container_width=True)

except Exception as e:
    st.error(f"Error loading dashboard data: {e}")
    st.write(f"Details: {str(e)}")