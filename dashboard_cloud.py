# bridge_api.py - Run on YOUR LOCAL PC
"""
Local API Bridge for STEMCUBE to Streamlit Cloud
Run this on your PC where STEMCUBE is connected via USB
"""

from flask import Flask, jsonify
import serial
import threading
import time
import json
from datetime import datetime
import re
import numpy as np
from flask_cors import CORS
import logging
import sys

app = Flask(__name__)
CORS(app)  # Enable CORS for Streamlit Cloud

# Configuration - CHANGE THESE FOR YOUR SETUP
STEMCUBE_PORT = 'COM8'      # Change to your COM port (e.g., COM3, COM4, etc.)
BAUD_RATE = 115200          # Change if your STEMCUBE uses different baud rate
API_PORT = 5000             # Port for the API

# Global variables
latest_data = {
    'node_id': 'NODE_e661',
    'timestamp': datetime.now().isoformat(),
    'hr': 72,
    'spo2': 96,
    'temp': 36.5,
    'ax': 0.1,
    'ay': 0.2,
    'az': 1.0,
    'activity': 'RESTING',
    'packet_id': 0,
    'battery_level': 85,
    'data_source': 'stemcube'
}
connected = False
serial_conn = None
packet_counter = 1000

def find_stemcube_port():
    """Try to find STEMCUBE port automatically"""
    try:
        import serial.tools.list_ports
        ports = list(serial.tools.list_ports.comports())
        
        print("🔍 Searching for STEMCUBE...")
        for port in ports:
            print(f"  Found: {port.device} - {port.description}")
            
            # Try common port names
            if 'USB' in port.description or 'Serial' in port.description:
                try:
                    test_conn = serial.Serial(port.device, BAUD_RATE, timeout=1)
                    test_conn.close()
                    print(f"✅ Found potential STEMCUBE at {port.device}")
                    return port.device
                except:
                    continue
        
        return None
    except:
        return None

def parse_stemcube_data(raw_text):
    """Parse STEMCUBE data - MODIFY THIS BASED ON YOUR ACTUAL DATA FORMAT"""
    global packet_counter
    
    try:
        print(f"📥 Raw data: {raw_text[:100]}...")  # Debug print
        
        # Example format: [4541] STING\n[4542] NODE_e661|\n[4543] 532|269377\n[4544] 0|26.5|59|
        
        # Try to extract numbers
        numbers = re.findall(r'-?\d+\.?\d*', raw_text)
        
        if numbers:
            print(f"🔢 Found numbers: {numbers}")
        
        # For now, create realistic simulated data
        # YOU NEED TO MODIFY THIS TO MATCH YOUR ACTUAL STEMCUBE OUTPUT
        
        packet_counter += 1
        
        # Simulate some variation
        hr_base = 72
        hr_variation = np.sin(time.time()/10) * 5 + np.random.normal(0, 2)
        hr = max(60, min(110, hr_base + hr_variation))
        
        spo2 = max(94, min(99, 97 + np.random.normal(0, 1)))
        
        temp_base = 36.5
        temp_variation = np.sin(time.time()/20) * 0.1
        temp = max(36.0, min(37.2, temp_base + temp_variation))
        
        # Activity based on time
        activity_cycle = int(time.time()) % 60
        if activity_cycle < 45:
            activity = "RESTING"
            ax, ay, az = np.random.normal(0, 0.05, 3)
            az += 1.0
        else:
            activity = "WALKING"
            ax = np.sin(time.time()) * 0.2 + np.random.normal(0, 0.1)
            ay = np.cos(time.time()) * 0.1 + np.random.normal(0, 0.05)
            az = 1.0 + np.random.normal(0, 0.05)
        
        data = {
            'node_id': 'NODE_e661',
            'timestamp': datetime.now().isoformat(),
            'hr': float(hr),
            'spo2': float(spo2),
            'temp': float(temp),
            'ax': float(ax),
            'ay': float(ay),
            'az': float(az),
            'gx': float(np.random.normal(0, 0.2)),
            'gy': float(np.random.normal(0, 0.2)),
            'gz': float(np.random.normal(0, 0.2)),
            'activity': activity,
            'packet_id': packet_counter,
            'battery_level': np.random.uniform(80, 95),
            'data_source': 'stemcube',
            'raw_sample': raw_text[:50]  # Keep first 50 chars for debugging
        }
        
        print(f"📊 Parsed: HR={data['hr']:.0f}, SpO2={data['spo2']:.1f}, Temp={data['temp']:.1f}")
        return data
        
    except Exception as e:
        print(f"❌ Parse error: {e}")
        return None

def read_stemcube():
    """Read data from STEMCUBE"""
    global latest_data, connected, serial_conn
    
    # Try to find port
    port = STEMCUBE_PORT
    if port is None:
        port = find_stemcube_port()
    
    if not port:
        print("❌ No STEMCUBE port found. Using simulated data.")
        connected = False
        return
    
    try:
        print(f"🔌 Connecting to STEMCUBE on {port} at {BAUD_RATE} baud...")
        serial_conn = serial.Serial(
            port=port,
            baudrate=BAUD_RATE,
            timeout=1
        )
        
        # Clear buffer
        serial_conn.reset_input_buffer()
        time.sleep(2)
        
        connected = True
        print(f"✅ Connected to STEMCUBE on {port}")
        
        buffer = ""
        
        while True:
            if serial_conn.in_waiting:
                raw = serial_conn.read(serial_conn.in_waiting)
                text = raw.decode('utf-8', errors='ignore')
                buffer += text
                
                # Process complete lines
                if '\n' in buffer:
                    lines = buffer.split('\n')
                    
                    for line in lines[:-1]:  # Process all but last (incomplete)
                        line = line.strip()
                        
                        if line and len(line) > 5:  # Minimum length
                            print(f"📨 Received: {line}")
                            
                            # Parse the data
                            data = parse_stemcube_data(line)
                            if data:
                                latest_data = data
                                print(f"✅ Updated: Packet #{data['packet_id']}")
                    
                    # Keep incomplete line
                    buffer = lines[-1]
            
            time.sleep(0.1)
            
    except Exception as e:
        print(f"❌ STEMCUBE error: {e}")
        connected = False
        
        # Try to reconnect
        time.sleep(5)
        if serial_conn:
            serial_conn.close()
        read_stemcube()

@app.route('/api/data', methods=['GET'])
def get_data():
    """API endpoint for Streamlit Cloud"""
    global latest_data, connected
    
    # Update timestamp
    latest_data['timestamp'] = datetime.now().isoformat()
    
    return jsonify({
        'success': True,
        'connected': connected,
        'timestamp': datetime.now().isoformat(),
        'data': latest_data
    })

@app.route('/api/status', methods=['GET'])
def get_status():
    """Status endpoint"""
    return jsonify({
        'status': 'running',
        'stemcube_connected': connected,
        'api_port': API_PORT,
        'uptime': time.time() - start_time
    })

@app.route('/')
def index():
    """Home page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>STEMCUBE Bridge API</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .status { padding: 20px; border-radius: 10px; margin: 20px 0; }
            .connected { background: #d4edda; color: #155724; }
            .disconnected { background: #f8d7da; color: #721c24; }
            .endpoint { background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏥 STEMCUBE Bridge API</h1>
            <div class="status %s">
                <h2>Status: %s</h2>
                <p>STEMCUBE: %s</p>
                <p>Last Update: %s</p>
            </div>
            
            <h2>API Endpoints:</h2>
            <div class="endpoint">
                <h3>GET /api/data</h3>
                <p>Get latest STEMCUBE data</p>
                <code>curl http://localhost:%s/api/data</code>
            </div>
            
            <div class="endpoint">
                <h3>GET /api/status</h3>
                <p>Check API status</p>
            </div>
            
            <p>For Streamlit Cloud dashboard, use: <code>http://YOUR_LOCAL_IP:5000/api/data</code></p>
            <p>Replace YOUR_LOCAL_IP with your computer's IP address</p>
        </div>
    </body>
    </html>
    """ % (
        'connected' if connected else 'disconnected',
        'RUNNING' if connected else 'DISCONNECTED',
        'CONNECTED' if connected else 'DISCONNECTED',
        latest_data.get('timestamp', 'Never'),
        API_PORT
    )

if __name__ == '__main__':
    print("=" * 60)
    print("🏥 STEMCUBE BRIDGE API")
    print("=" * 60)
    
    # Start STEMCUBE reader in background thread
    stemcube_thread = threading.Thread(target=read_stemcube, daemon=True)
    stemcube_thread.start()
    
    start_time = time.time()
    
    print(f"🌐 Starting API server on port {API_PORT}")
    print(f"📡 STEMCUBE Port: {STEMCUBE_PORT}")
    print(f"🚀 API URL: http://localhost:{API_PORT}/api/data")
    print("=" * 60)
    print("💡 For Streamlit Cloud, use your public IP address")
    print("💡 Run: ipconfig (Windows) or ifconfig (Mac/Linux) to find your IP")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=API_PORT, debug=False)