def load_real_time_data():
    """Load real-time data from JSON file"""
    try:
        with open('stemcube_cloud_data.json', 'r') as f:
            data = json.load(f)
        
        # DEBUG: Print what data we're actually getting
        print(f"DEBUG: Loaded data - Is real: {data.get('is_real_data')}")
        print(f"DEBUG: Activity: {data['data'].get('activity')}")
        print(f"DEBUG: Raw packet: {data['data'].get('raw_packet', 'N/A')[:50]}...")
        
        # Add Malaysia time
        malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
        data['malaysia_time'] = datetime.now(malaysia_tz).strftime('%H:%M:%S')
        
        return data
        
    except FileNotFoundError:
        return generate_stemcube_demo_data()
    except Exception as e:
        st.error(f"Data error: {e}")
        return None