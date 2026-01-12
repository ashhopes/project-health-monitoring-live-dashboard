@ -1,185 +1,1166 @@
# dashboard_cloud.py - FILE READER VERSION
# dashboard_cloud.py - UPDATED FOR REAL STEMCUBE DATA
"""
REAL-TIME DASHBOARD FOR STEMCUBE - READ FROM FILE
REAL-TIME DASHBOARD FOR STEMCUBE
CONNECTED TO REAL STEMCUBE DATA FROM COM8
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import pytz
from collections import deque
import base64
import math

# ================ FILE READER (NO SERIAL NEEDED) ================
def read_from_file():
    """Read STEMCUBE data from file instead of COM8"""
    try:
        with open('stemcube_data.txt', 'r') as f:
            lines = f.readlines()
            if lines:
                # Get last line
                raw_line = lines[-1].strip()
                return parse_real_stemcube_data(raw_line), "✅ Reading from file"
    except:
        pass
    
    # Create sample data if file doesn't exist
    sample_data = "|1768143201|95|81|45.7|26.7|0.199|0.062|1.028|9.3|-1.8|4.3|walking|"
    return parse_real_stemcube_data(sample_data), "✅ Using sample data"
# ================ TRY TO IMPORT SERIAL ================
try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

# ================ PARSER FUNCTION ================
def parse_real_stemcube_data(raw_line):
    """Parse STEMCUBE data format"""
    """Parse the ACTUAL STEMCUBE format: |timestamp|SpO2|HR|humidity|temperature|ax|ay|az|gx|gy|gz|activity|"""
    
    # Default values
    data = {
        'node_id': 'STEMCUBE_MASTER',
        'hr': 72,
        'spo2': 98,
        'temp': 36.5,
        'activity_level': 'RESTING',
        'movement': 0.0,
        'humidity': 50.0,
        'confidence': 0.95,
        'is_real': True,
        'raw_packet': raw_line,
        'parsed_success': False
    }
    
    try:
        print(f"📥 REAL STEMCUBE DATA: {raw_line[:80]}")
        
        # Remove leading/trailing pipes and split
        cleaned = raw_line.strip('|')
        parts = cleaned.split('|')
        
        # Expected: 12 parts
        # Index: 0=timestamp, 1=SpO2, 2=HR, 3=humidity, 4=temp, 5=ax, 6=ay, 7=az, 
        #         8=gx, 9=gy, 10=gz, 11=activity
        
        if len(parts) >= 12:
            # Parse data
            # Parse SpO2 (index 1)
            try:
                spo2_val = float(parts[1])
                if 70 <= spo2_val <= 100:
                    data['spo2'] = int(spo2_val)
            except:
                pass
            
            # Parse HR (index 2)
            try:
                hr_val = float(parts[2])
                if 40 <= hr_val <= 200:
                    data['hr'] = int(hr_val)
            except:
                pass
            
            # Parse Temperature (index 4)
            try:
                temp_val = float(parts[4])
                if 20 <= temp_val <= 45:
                    data['temp'] = round(temp_val, 1)
            except:
                pass
            
            # Parse Humidity (index 3)
            try:
                hum_val = float(parts[3])
                data['humidity'] = hum_val
            except:
                pass
            
            # Parse Activity (index 11)
            try:
                activity_str = parts[11].strip().lower()
                if 'walking' in activity_str:
                    data['activity_level'] = 'WALKING'
                    data['movement'] = 2.5
                elif 'running' in activity_str:
                    data['activity_level'] = 'RUNNING'
                    data['movement'] = 4.0
                elif 'standing' in activity_str:
                    data['activity_level'] = 'STANDING'
                    data['movement'] = 1.0
                else:
                    data['activity_level'] = 'RESTING'
                    data['movement'] = 0.0
            except:
                pass
            
            # Calculate movement from gyroscope data
            try:
                gx = float(parts[8])
                gy = float(parts[9])
                gz = float(parts[10])
                movement = math.sqrt(gx*gx + gy*gy + gz*gz)
                data['movement'] = round(movement, 2)
            except:
                pass
            
            data['parsed_success'] = True
            print(f"✅ PARSED: HR={data['hr']}, SpO2={data['spo2']}, Temp={data['temp']}, Activity={data['activity_level']}")
            
    except Exception as e:
        print(f"Parse error: {e}")
        print(f"⚠️ Parse error: {e}")
    
    return data

# ================ PAGE CONFIG ================
st.set_page_config(
    page_title="STEMCUBE REAL-TIME MONITOR",
    page_icon="🏥",
    layout="wide"
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================ SIMPLIFIED THEME ================
st.markdown("""
# ================ UMP LOGO BASE64 ================
UMP_LOGO_BASE64 = """
iVBORw0KGgoAAAANSUhEUgAAAfQAAABmCAYAAAD3mVZSAAAACXBIWXMAAAsTAAALEwEAmpwYAAAA
AXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAZdSURBVHgB7d1BbhtHEIDRGRp5/4uyJ5ByYBwY
wIF9YIC4h6QL2ySbe2d2B1jfRwEESfL/j1/f/vgJAPDavr1/AAD4IkEHAEkEHQCkEXQAkEbQAUAa
QQcAaQQdAKQRdACQRtABQBpBBwBpBB0ApBF0AJBG0AFAGkE3wOsX3j/xAsA6V2y/Owg6AHh9j85S
0AFAu6uzFHQA0GrGLAUdALSZNUtBBwAtZs9S0AHAy1bmKOgA4KWr8xN0APCy1fkJOgB4ycoMBR0A
vGRljoIOAF6yOkdBBwDjrc5R0AHAaKtzFHQA0GLGPAUdAIw2Y56CDgDGmjVPQQcAI82cq6ADgHFm
zlXQAcAos2cr6ABgjNnzFXQAMMLq+Qo6AFhu9YwFHQAsN3vGgg4Alpo9Z0EHAEvNnrOgA4BlVsxZ
0AHAEitmLegAYL4VsxZ0ADDXilkLOgCYa9W8BR0AzLNq3oIOAOZZNW9BBwDzrJq3oAOAeVbNW9AB
wByr5i3oAGCeVfMWdAAwx6p5CzoAmGflzAUdAMyxcuaCDgDmWDlzQQcAc6ycuaADgBlWz13QAcD1
Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVW
z13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbP
XdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d
0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13Q
AcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdAB
wPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA
9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1
Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVW
z13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbP
XdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d
0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13Q
AcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdAB
wPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA
9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1
Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVW
z13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbP
XdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d
0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13Q
AcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdAB
wPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA
9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1
Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVW
z13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbP
XdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d
0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13Q
AcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdAB
wPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA
9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1
Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVW
z13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbP
XdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d
0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13Q
AcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdAB
wPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA
9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1
Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVW
z13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbP
XdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d
0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13Q
AcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdAB
wPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA
9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1
Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVW
z13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbP
XdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d
0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13Q
AcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdAB
wPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA
9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1
Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVW
z13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbP
XdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d
0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13Q
AcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdAB
wPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA
9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1
Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVW
z13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbP
XdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d
0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13Q
AcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdAB
wPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA
9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1
Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVW
z13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbP
XdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d
0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13Q
AcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdAB
wPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA
9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1
Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVW
z13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbP
XdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d
0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13Q
AcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdAB
wPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA
9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1
Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVW
z13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbP
XdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d
0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13Q
AcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdAB
wPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA
9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1
Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVW
z13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbP
XdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d
0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13Q
AcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdAB
wPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA
9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1
Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVW
z13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbP
XdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d
0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13Q
AcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdAB
wPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA
9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1
Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVW
z13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbP
XdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d
0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13Q
AcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdAB
wPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA
9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1
Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVW
z13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbP
XdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d
0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13Q
AcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdAB
wPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA
9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1
Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVW
z13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbP
XdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d
0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13Q
AcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdAB
wPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA
9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1
Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVW
z13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbP
XdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d
0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13Q
AcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdAB
wPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA
9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1
Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVW
z13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbP
XdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d
0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13Q
AcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdAB
wPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA
9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1
Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVW
z13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbP
XdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d
0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13Q
AcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdAB
wPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA9VbPXdABwPVWz13QAcD1Vs9d0AHA
9VbPXdABwPVWz13QAcD1Vs9d0AGA9//4HZRlAQAt9zY4AAAAAElFTkSuQmCC
"""

# ================ MUJI + OLIVE MARROON THEME ================
st.markdown(f"""
<style>
    .main-header {
        background: linear-gradient(135deg, #8B4513 0%, #556B2F 100%);
    /* MUJI + OLIVE MARROON COLOR PALETTE */
    :root {{
        --muji-maroon: #8B4513;
        --olive-green: #556B2F;
        --champagne: #F7E7CE;
        --soft-beige: #F5F5DC;
        --dark-chocolate: #3C2F2F;
        --cream: #FFFDD0;
        --warm-brown: #A0522D;
        --earth-green: #6B8E23;
    }}
    
    /* MAIN BACKGROUND */
    .stApp {{
        background: linear-gradient(135deg, var(--soft-beige) 0%, var(--cream) 100%);
        font-family: 'Segoe UI', 'Arial', sans-serif;
    }}
    
    /* HEADER WITH LOGO */
    .main-header {{
        background: linear-gradient(135deg, var(--muji-maroon) 0%, var(--olive-green) 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 25px;
        box-shadow: 0 6px 20px rgba(139, 69, 19, 0.3);
        text-align: center;
    }
        position: relative;
    }}
    
    .logo-container {{
        position: absolute;
        left: 30px;
        top: 50%;
        transform: translateY(-50%);
    }}
    
    .logo-img {{
        height: 60px;
        width: auto;
        filter: brightness(0) invert(1);
    }}
    
    /* CARD STYLES */
    .metric-card {{
        background: linear-gradient(135deg, white 0%, var(--champagne) 100%);
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(85, 107, 47, 0.15);
        border-left: 4px solid var(--olive-green);
        margin-bottom: 15px;
        transition: all 0.3s ease;
    }}
    
    .metric-card:hover {{
        transform: translateY(-3px);
        box-shadow: 0 6px 16px rgba(85, 107, 47, 0.2);
    }}
    
    .graph-container {{
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(139, 69, 19, 0.15);
        border-top: 4px solid var(--muji-maroon);
        margin-bottom: 20px;
    }}
    
    /* SIDEBAR */
    .sidebar-section {{
        background: linear-gradient(135deg, var(--champagne) 0%, white 100%);
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(139, 69, 19, 0.15);
        margin-bottom: 20px;
        border: 2px solid var(--soft-beige);
    }}
    
    /* TABS */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 5px;
        background: var(--soft-beige);
        padding: 5px;
        border-radius: 10px;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background: var(--champagne);
        border-radius: 8px 8px 0 0;
        padding: 12px 24px;
        font-weight: 600;
        color: var(--dark-chocolate);
        border: 2px solid transparent;
        transition: all 0.3s;
    }}
    
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(135deg, var(--muji-maroon) 0%, var(--olive-green) 100%) !important;
        color: white !important;
        border-color: var(--muji-maroon) !important;
    }}
    
    /* BUTTONS */
    .stButton button {{
        background: linear-gradient(135deg, var(--olive-green) 0%, var(--muji-maroon) 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
        transition: all 0.3s;
    }}
    
    .stButton button:hover {{
        transform: scale(1.05);
        box-shadow: 0 4px 12px rgba(139, 69, 19, 0.3);
    }}
    
    /* METRICS */
    .metric-value {{
        font-size: 32px;
        font-weight: 700;
        color: var(--dark-chocolate);
        margin: 5px 0;
    }}
    
    .metric-label {{
        font-size: 13px;
        color: var(--olive-green);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    
    /* STATUS INDICATORS */
    .status-normal {{
        background: linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%);
        color: white;
        padding: 6px 14px;
        border-radius: 18px;
        font-weight: 600;
        display: inline-block;
        font-size: 13px;
    }}
    
    .status-warning {{
        background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%);
        color: white;
        padding: 6px 14px;
        border-radius: 18px;
        font-weight: 600;
        display: inline-block;
        font-size: 13px;
    }}
    
    .status-critical {{
        background: linear-gradient(135deg, #F44336 0%, #D32F2F 100%);
        color: white;
        padding: 6px 14px;
        border-radius: 18px;
        font-weight: 600;
        display: inline-block;
        font-size: 13px;
    }}
    
    /* DATA TABLE */
    .dataframe {{
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }}
    
    .dataframe th {{
        background: var(--olive-green) !important;
        color: white !important;
        font-weight: 600 !important;
    }}
    
    /* FOOTER */
    .dashboard-footer {{
        background: linear-gradient(135deg, var(--dark-chocolate) 0%, #2C1810 100%);
        color: var(--champagne);
        padding: 20px;
        border-radius: 12px;
        margin-top: 30px;
        text-align: center;
        font-size: 14px;
    }}
    
    /* ACTIVITY EMOJI */
    .activity-emoji {{
        font-size: 48px;
        margin: 10px 0;
        animation: pulse 2s ease-in-out infinite;
    }}
    
    @keyframes pulse {{
        0% {{ transform: scale(1); }}
        50% {{ transform: scale(1.1); }}
        100% {{ transform: scale(1); }}
    }}
</style>
""", unsafe_allow_html=True)

# ================ INITIALIZE ================
if 'hr_data' not in st.session_state:
    st.session_state.hr_data = deque(maxlen=50)
    st.session_state.spo2_data = deque(maxlen=50)
    st.session_state.temp_data = deque(maxlen=50)
    st.session_state.movement_data = deque(maxlen=50)
    st.session_state.timestamps = deque(maxlen=50)
# ================ INITIALIZE DATA BUFFERS ================
def init_session_state():
    """Initialize all session state variables WITH DATA"""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        current_time = datetime.now()
        
        # Create INITIAL DATA
        initial_hr = 75
        initial_spo2 = 98
        initial_temp = 36.5
        initial_movement = 1.0
        
        # Initialize with 10 data points
        st.session_state.hr_data = deque([initial_hr + np.random.normal(0, 3) for _ in range(10)], maxlen=50)
        st.session_state.spo2_data = deque([initial_spo2 + np.random.normal(0, 1) for _ in range(10)], maxlen=50)
        st.session_state.temp_data = deque([initial_temp + np.random.normal(0, 0.2) for _ in range(10)], maxlen=50)
        st.session_state.movement_data = deque([initial_movement + np.random.normal(0, 0.3) for _ in range(10)], maxlen=50)
        st.session_state.timestamps = deque([current_time - timedelta(seconds=i) for i in range(10)][::-1], maxlen=50)
        
        # Raw packets storage
        st.session_state.raw_packets = deque(maxlen=20)
        
        # Store complete data records
        st.session_state.all_data = deque([
            {
                'timestamp': current_time - timedelta(seconds=i),
                'hr': initial_hr + np.random.normal(0, 3),
                'spo2': initial_spo2 + np.random.normal(0, 1),
                'temp': initial_temp + np.random.normal(0, 0.2),
                'movement': initial_movement + np.random.normal(0, 0.3),
                'activity': ['RESTING', 'WALKING', 'RUNNING'][i % 3],
                'is_real': False
            }
            for i in range(10)
        ], maxlen=50)
        
        # Connection status
        st.session_state.com8_status = "Checking..."

# ================ MAIN DASHBOARD ================
def main():
    # Header
    st.markdown("""
# ================ READ REAL STEMCUBE DATA ================
def read_com8_direct():
    """Read REAL STEMCUBE data from COM8"""
    if not SERIAL_AVAILABLE:
        return None, "Serial library not installed"
    
    try:
        ser = serial.Serial('COM8', 9600, timeout=0.5)
        
        if ser.in_waiting > 0:
            raw_line = ser.readline().decode('utf-8', errors='ignore').strip()
            ser.close()
            
            if raw_line and raw_line.startswith('|'):
                print(f"📥 RAW FROM STEMCUBE: {raw_line[:80]}")
                
                # Parse using the REAL STEMCUBE parser
                parsed = parse_real_stemcube_data(raw_line)
                
                if parsed['parsed_success']:
                    data = {
                        'timestamp': datetime.now(),
                        'hr': parsed['hr'],
                        'spo2': parsed['spo2'],
                        'temp': parsed['temp'],
                        'movement': parsed['movement'],
                        'activity': parsed['activity_level'],
                        'packet_id': int(time.time() * 100) % 10000,
                        'node_id': parsed['node_id'],
                        'is_real': True,
                        'raw': raw_line[:60],
                        'humidity': parsed.get('humidity', 0.0)
                    }
                    
                    # Add status indicators
                    data['hr_status'] = "NORMAL"
                    if data['hr'] > 120:
                        data['hr_status'] = "CRITICAL"
                    elif data['hr'] > 100:
                        data['hr_status'] = "WARNING"
                        
                    data['spo2_status'] = "NORMAL"
                    if data['spo2'] < 90:
                        data['spo2_status'] = "CRITICAL"
                    elif data['spo2'] < 95:
                        data['spo2_status'] = "WARNING"
                        
                    data['temp_status'] = "NORMAL"
                    if data['temp'] > 38.0:
                        data['temp_status'] = "CRITICAL"
                    elif data['temp'] > 37.0:
                        data['temp_status'] = "WARNING"
                    
                    # Store raw packet
                    st.session_state.raw_packets.append({
                        'time': datetime.now().strftime('%H:%M:%S'),
                        'packet': raw_line[:80]
                    })
                    
                    print(f"✅ PARSED: HR={data['hr']}, SpO2={data['spo2']}, Temp={data['temp']}, Activity={data['activity']}")
                    return data, "✅ Connected to STEMCUBE"
                else:
                    return None, "✅ Connected (Parsing failed)"
        
        ser.close()
        return None, "⏳ Waiting for STEMCUBE data..."
        
    except serial.SerialException:
        return None, "❌ COM8 not available"
    except Exception as e:
        print(f"COM8 Error: {e}")
        return None, f"⚠️ COM8 error"

# ================ DISPLAY HEADER WITH LOGO ================
def display_header():
    """Display header with UMP logo"""
    malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
    current_time_malaysia = datetime.now(malaysia_tz)
    
    st.markdown(f"""
    <div class="main-header">
        <h1>🏥 STEMCUBE REAL-TIME MONITOR</h1>
        <p>📍 Universiti Malaysia Pahang • 🎓 Final Year Project 2025</p>
        <div class="logo-container">
            <img src="data:image/png;base64,{UMP_LOGO_BASE64}" class="logo-img">
        </div>
        <div style="margin-left: 80px;">
            <h1 style="margin: 0; font-size: 2.2rem; font-weight: 700;">🏥 STEMCUBE REAL-TIME MONITOR</h1>
            <p style="margin: 8px 0 0 0; font-size: 1.1rem; opacity: 0.95;">
                📍 Universiti Malaysia Pahang • 🎓 Final Year Project 2025
            </p>
            <p style="margin: 5px 0 0 0; font-size: 0.95rem; opacity: 0.85;">
                🇲🇾 Malaysia Time: <strong>{current_time_malaysia.strftime('%I:%M:%S %p')}</strong> • 
                📅 Date: {current_time_malaysia.strftime('%d %B %Y')}
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ================ DEMO DATA ================
def get_demo_data():
    """Generate demo data"""
    current_time = datetime.now()
    
    # Read data
    parsed_data, status = read_from_file()
    base_hr = 68 + np.random.normal(0, 4)
    base_spo2 = 97 + np.random.normal(0, 1)
    base_temp = 36.5 + np.random.normal(0, 0.2)
    
    if parsed_data['parsed_success']:
        # Add to buffers
        current_time = datetime.now()
        st.session_state.timestamps.append(current_time)
        st.session_state.hr_data.append(parsed_data['hr'])
        st.session_state.spo2_data.append(parsed_data['spo2'])
        st.session_state.temp_data.append(parsed_data['temp'])
        st.session_state.movement_data.append(parsed_data['movement'])
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("❤️ Heart Rate", f"{parsed_data['hr']} BPM")
        
        with col2:
            st.metric("🩸 SpO₂", f"{parsed_data['spo2']}%")
        
        with col3:
            st.metric("🌡️ Temperature", f"{parsed_data['temp']}°C")
        
        with col4:
            st.metric("🏃 Activity", parsed_data['activity_level'])
        
        # Status
        st.success(f"**{status}**")
        
        # Simple graph
        if len(st.session_state.timestamps) > 1:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=list(st.session_state.timestamps),
                y=list(st.session_state.hr_data),
                mode='lines+markers',
                name='Heart Rate'
            ))
            fig.update_layout(title="Heart Rate Trend", height=300)
            st.plotly_chart(fig, use_container_width=True)
        
        # Auto-refresh
        time.sleep(2)
        st.rerun()
    activities = ['RESTING', 'RESTING', 'RESTING', 'WALKING']
    activity = np.random.choice(activities)
    
    if activity == 'RESTING':
        movement = 0.5 + np.random.random() * 0.5
        base_hr = max(60, min(75, base_hr))
    else:
        st.error("❌ Could not parse data")
        movement = 1.5 + np.random.random() * 1.0
        base_hr = max(75, min(90, base_hr))
    
    return {
        'timestamp': current_time,
        'hr': int(max(55, min(90, base_hr))),
        'spo2': int(max(95, min(100, base_spo2))),
        'temp': round(max(36.0, min(37.0, base_temp)), 1),
        'movement': round(movement, 1),
        'activity': activity,
        'packet_id': int(time.time() * 100) % 10000,
        'node_id': 'STEMCUBE_MASTER',
        'is_real': False,
        'raw': 'DEMO: Simulated data'
    }

# ================ UPDATE DATA BUFFERS ================
def update_data_buffers(data):
    """Update all data buffers"""
    st.session_state.timestamps.append(data['timestamp'])
    st.session_state.hr_data.append(data['hr'])
    st.session_state.spo2_data.append(data['spo2'])
    st.session_state.temp_data.append(data['temp'])
    st.session_state.movement_data.append(data['movement'])
    
    # Store complete record
    record = {
        'timestamp': data['timestamp'],
        'hr': data['hr'],
        'spo2': data['spo2'],
        'temp': data['temp'],
        'movement': data['movement'],
        'activity': data['activity'],
        'is_real': data['is_real']
    }
    
    st.session_state.all_data.append(record)

# ================ GRAPH FUNCTIONS ================
def create_graph(title, y_data, color, y_label):
    """Create a graph with MUJI colors"""
    if len(st.session_state.timestamps) == 0:
        return None
    
    n_points = min(30, len(st.session_state.timestamps))
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(st.session_state.timestamps)[-n_points:],
        y=list(y_data)[-n_points:],
        mode='lines+markers',
        line=dict(color=color, width=3),
        marker=dict(size=5, color=color),
        fill='tozeroy',
        fillcolor=f'rgba{tuple(int(color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4)) + (0.1,)}'
    ))
    
    fig.update_layout(
        title={
            'text': title,
            'font': {'size': 16, 'color': '#3C2F2F', 'family': 'Arial'}
        },
        height=280,
        margin=dict(l=50, r=20, t=50, b=50),
        xaxis_title="Time",
        yaxis_title=y_label,
        plot_bgcolor='rgba(255, 253, 208, 0.1)',
        paper_bgcolor='white',
        font=dict(family='Arial', size=12),
        showlegend=False
    )
    
    return fig

# ================ TAB 1: HEALTH VITALS ================
def tab_health_vitals(current_data):
    """Tab 1: Health Vitals"""
    
    # Activity display with emoji
    col_activity = st.columns([1, 2, 1])
    with col_activity[1]:
        activity = current_data['activity']
        emoji = "😴" if activity == 'RESTING' else "🚶" if activity == 'WALKING' else "🏃"
        activity_color = '#8B4513' if activity == 'RESTING' else '#556B2F' if activity == 'WALKING' else '#D4A76A'
        
        st.markdown(f"""
        <div style="text-align: center; padding: 15px; border-radius: 12px; 
                    background: linear-gradient(135deg, {activity_color}20 0%, white 100%);
                    border: 2px solid {activity_color}40;">
            <div class="activity-emoji">{emoji}</div>
            <h2 style="color: {activity_color}; margin: 5px 0;">{activity}</h2>
            <p style="color: #666; font-size: 14px;">Patient Activity Status</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Current Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        hr = current_data['hr']
        if 60 <= hr <= 100:
            status_class = "status-normal"
            status = "NORMAL"
        elif 50 <= hr <= 110:
            status_class = "status-warning"
            status = "WARNING"
        else:
            status_class = "status-critical"
            status = "ALERT"
        
        st.markdown(f"""
        <div style="text-align: center;">
            <div class="metric-label">HEART RATE</div>
            <div class="metric-value" style="color: {'#4CAF50' if 60 <= hr <= 100 else '#FF9800' if 50 <= hr <= 110 else '#F44336'};">{hr}</div>
            <div style="font-size: 14px; color: #666; margin: 5px 0;">BPM</div>
            <div class="{status_class}">{status}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        spo2 = current_data['spo2']
        if spo2 >= 95:
            status_class = "status-normal"
            status = "NORMAL"
        elif spo2 >= 90:
            status_class = "status-warning"
            status = "LOW"
        else:
            status_class = "status-critical"
            status = "CRITICAL"
        
        st.markdown(f"""
        <div style="text-align: center;">
            <div class="metric-label">BLOOD OXYGEN</div>
            <div class="metric-value" style="color: {'#4CAF50' if spo2 >= 95 else '#FF9800' if spo2 >= 90 else '#F44336'};">{spo2}%</div>
            <div style="font-size: 14px; color: #666; margin: 5px 0;">SpO₂</div>
            <div class="{status_class}">{status}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col3:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        temp = current_data['temp']
        if temp <= 37.5:
            status_class = "status-normal"
            status = "NORMAL"
        elif temp <= 38.5:
            status_class = "status-warning"
            status = "ELEVATED"
        else:
            status_class = "status-critical"
            status = "FEVER"
        
        st.markdown(f"""
        <div style="text-align: center;">
            <div class="metric-label">TEMPERATURE</div>
            <div class="metric-value" style="color: {'#4CAF50' if temp <= 37.5 else '#FF9800' if temp <= 38.5 else '#F44336'};">{temp}°C</div>
            <div style="font-size: 14px; color: #666; margin: 5px 0;">Body Temp</div>
            <div class="{status_class}">{status}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col4:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        movement = current_data['movement']
        
        st.markdown(f"""
        <div style="text-align: center;">
            <div class="metric-label">MOVEMENT</div>
            <div class="metric-value" style="color: #8D6E63;">{movement}</div>
            <div style="font-size: 14px; color: #666; margin: 5px 0;">Activity Level</div>
            <div style="margin-top: 10px;">
                <div style="background: #F5F5DC; height: 8px; border-radius: 4px; overflow: hidden;">
                    <div style="background: linear-gradient(90deg, #556B2F, #8B4513); 
                                width: {min(100, movement * 20)}%; height: 100%;"></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Real-time Graphs
    st.markdown("### 📈 Real-time Monitoring")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
        hr_fig = create_graph("❤️ Heart Rate Trend", st.session_state.hr_data, '#8B4513', 'BPM')
        if hr_fig:
            st.plotly_chart(hr_fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
        spo2_fig = create_graph("🩸 Blood Oxygen Trend", st.session_state.spo2_data, '#556B2F', 'SpO₂ %')
        if spo2_fig:
            st.plotly_chart(spo2_fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
        temp_fig = create_graph("🌡️ Temperature Trend", st.session_state.temp_data, '#D4A76A', '°C')
        if temp_fig:
            st.plotly_chart(temp_fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
        move_fig = create_graph("🏃 Movement Activity", st.session_state.movement_data, '#8D6E63', 'Activity Level')
        if move_fig:
            st.plotly_chart(move_fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ================ TAB 2: SYSTEM STATUS ================
def tab_system_status(current_data, com8_status):
    """Tab 2: System Status"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
        st.markdown("### 📡 Connection Status")
        
        # Connection status
        if "✅ Connected" in com8_status:
            st.success(f"**{com8_status}**")
        elif "❌" in com8_status:
            st.error(f"**{com8_status}**")
        elif "⚠️" in com8_status:
            st.warning(f"**{com8_status}**")
        else:
            st.info(f"**{com8_status}**")
        
        # Data source
        st.markdown("---")
        if current_data['is_real']:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #4CAF5020 0%, #4CAF5010 100%); 
                        padding: 15px; border-radius: 10px; border-left: 4px solid #4CAF50;">
                <h4 style="color: #2E7D32; margin: 0 0 10px 0;">🌐 REAL DATA MODE</h4>
                <p style="color: #666; margin: 0; font-size: 14px;">
                    Receiving live data from STEMCUBE via COM8
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #FF980020 0%, #FF980010 100%); 
                        padding: 15px; border-radius: 10px; border-left: 4px solid #FF9800;">
                <h4 style="color: #F57C00; margin: 0 0 10px 0;">💻 DEMO DATA MODE</h4>
                <p style="color: #666; margin: 0; font-size: 14px;">
                    Showing simulated data. Connect STEMCUBE for real-time monitoring.
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.metric("🔢 Packet ID", current_data['packet_id'])
        st.metric("📟 Node ID", current_data['node_id'])
        st.metric("⏰ Last Update", datetime.now().strftime('%H:%M:%S'))
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
        st.markdown("### 🔋 System Health")
        
        # Battery gauge
        battery = 85
        fig_battery = go.Figure(go.Indicator(
            mode="gauge+number",
            value=battery,
            title={'text': "Battery Level", 'font': {'size': 16, 'color': '#3C2F2F'}},
            number={'suffix': "%", 'font': {'size': 28, 'color': '#8B4513'}},
            gauge={
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': '#3C2F2F'},
                'bar': {'color': '#556B2F'},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "#F7E7CE",
                'steps': [
                    {'range': [0, 20], 'color': 'rgba(244, 67, 54, 0.1)'},
                    {'range': [20, 50], 'color': 'rgba(255, 152, 0, 0.1)'},
                    {'range': [50, 100], 'color': 'rgba(85, 107, 47, 0.1)'}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 20
                }
            }
        ))
        
        fig_battery.update_layout(
            height=250,
            margin=dict(t=50, b=20, l=20, r=20),
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Arial', size=12)
        )
        st.plotly_chart(fig_battery, use_container_width=True)
        
        # System metrics
        col_metric1, col_metric2 = st.columns(2)
        with col_metric1:
            st.metric("📶 Signal", "-65 dB")
        with col_metric2:
            st.metric("📡 SNR", "12 dB")
        
        # Progress bars
        st.progress(0.85, text="Battery: 85%")
        st.progress(0.92, text="Signal Quality: 92%")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Raw Packets
    st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
    st.markdown("### 📡 Recent Data Packets")
    
    if len(st.session_state.raw_packets) > 0:
        for packet in list(st.session_state.raw_packets)[-5:]:
            st.code(f"{packet['time']}: {packet['packet']}")
    else:
        st.info("Waiting for data packets...")
        st.markdown("""
        **Expected STEMCUBE Format:**
        ```
        |timestamp|SpO2|HR|humidity|temperature|ax|ay|az|gx|gy|gz|activity|
        ```
        """)
    
    st.markdown("</div>", unsafe_allow_html=True)

# ================ TAB 3: DATA LOG ================
def tab_data_log():
    """Tab 3: Data Log"""
    
    st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
    st.markdown("### 📋 Recent Data Log")
    
    if len(st.session_state.all_data) > 0:
        # Get last 10 records
        all_data_list = list(st.session_state.all_data)
        n_items = min(10, len(all_data_list))
        
        table_data = []
        for i in range(1, n_items + 1):
            record = all_data_list[-i]
            table_data.append({
                'Time': record['timestamp'].strftime('%H:%M:%S'),
                'HR': record['hr'],
                'SpO₂': record['spo2'],
                'Temp': f"{record['temp']:.1f}°C",
                'Movement': f"{record['movement']:.1f}",
                'Activity': record['activity'],
                'Source': '📡 REAL' if record['is_real'] else '💻 DEMO'
            })
        
        # Reverse to show newest first
        table_data.reverse()
        
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, height=400)
    else:
        st.info("No data available yet")
    
    # Data Statistics
    st.markdown("### 📊 Data Statistics")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        hr_list = list(st.session_state.hr_data)
        avg_hr = np.mean(hr_list) if hr_list else 75
        st.metric("HR Avg", f"{avg_hr:.0f} BPM", delta="Normal" if 60 <= avg_hr <= 100 else "Check")
    
    with col2:
        spo2_list = list(st.session_state.spo2_data)
        avg_spo2 = np.mean(spo2_list) if spo2_list else 98
        st.metric("SpO₂ Avg", f"{avg_spo2:.0f}%", delta="Good" if avg_spo2 >= 95 else "Low")
    
    with col3:
        temp_list = list(st.session_state.temp_data)
        avg_temp = np.mean(temp_list) if temp_list else 36.5
        st.metric("Temp Avg", f"{avg_temp:.1f}°C", delta="Normal" if avg_temp <= 37.5 else "High")
    
    with col4:
        move_list = list(st.session_state.movement_data)
        avg_move = np.mean(move_list) if move_list else 1.0
        st.metric("Activity Avg", f"{avg_move:.1f}")
    
    with col5:
        st.metric("Data Points", len(st.session_state.timestamps))
    
    st.markdown("</div>", unsafe_allow_html=True)

# ================ MAIN DASHBOARD ================
def main():
    """Main dashboard function"""
    
    # Initialize session state
    init_session_state()
    
    # Display header with logo
    display_header()
    
    # Get data from COM8 or demo
    com8_data, com8_status = read_com8_direct()
    
    if com8_data:
        current_data = com8_data
        st.session_state.com8_status = com8_status
    else:
        current_data = get_demo_data()
        st.session_state.com8_status = com8_status
    
    # Update buffers
    update_data_buffers(current_data)
    
    # Sidebar
    with st.sidebar:
        st.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
        st.markdown("### ⚙️ Control Panel")
        
        auto_refresh = st.toggle("🔄 Auto Refresh", value=True, help="Automatically refresh data")
        refresh_rate = st.slider("Refresh Rate (seconds)", 1, 10, 2, help="How often to update the data")
        
        if st.button("🔄 Manual Refresh", use_container_width=True):
            st.rerun()
            
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
        st.markdown("### 📊 Current Readings")
        
        col_sb1, col_sb2 = st.columns(2)
        with col_sb1:
            st.metric("❤️ HR", f"{current_data['hr']} BPM")
            st.metric("🌡️ Temp", f"{current_data['temp']:.1f}°C")
        with col_sb2:
            st.metric("🩸 SpO₂", f"{current_data['spo2']}%")
            st.metric("🏃 Activity", current_data['activity'])
        
        # Activity indicator
        activity_color = '#8B4513' if current_data['activity'] == 'RESTING' else '#556B2F' if current_data['activity'] == 'WALKING' else '#D4A76A'
        st.markdown(f"""
        <div style="background: {activity_color}20; padding: 10px; border-radius: 8px; 
                    border-left: 4px solid {activity_color}; margin-top: 10px;">
            <p style="margin: 0; font-size: 13px; color: {activity_color};">
                <strong>Current Status:</strong> Patient is {current_data['activity'].lower()}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
        st.markdown("### 🔌 System Info")
        
        st.write(f"**Data Source:** {'📡 REAL' if current_data['is_real'] else '💻 DEMO'}")
        st.write(f"**Node:** {current_data['node_id']}")
        st.write(f"**Packets:** {len(st.session_state.raw_packets)}")
        st.write(f"**Last Update:** {datetime.now().strftime('%H:%M:%S')}")
        
        # Connection status
        if current_data['is_real']:
            st.success("✅ Connected to STEMCUBE")
        else:
            st.warning("⚠️ Demo Mode Active")
            if st.button("🔍 Check COM8", use_container_width=True):
                st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # TABS
    tab1, tab2, tab3 = st.tabs(["🩺 Health Vitals", "📡 System Status", "📋 Data Log"])
    
    with tab1:
        tab_health_vitals(current_data)
    
    with tab2:
        tab_system_status(current_data, st.session_state.com8_status)
    
    with tab3:
        tab_data_log()
    
    # Footer
    malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
    current_time_malaysia = datetime.now(malaysia_tz)
    
    st.markdown("""
    <div class="dashboard-footer">
        <p style="margin: 0; font-size: 14px;">
            🏥 <strong>STEMCUBE Health Monitoring System</strong> | 
            📍 Universiti Malaysia Pahang • Faculty of Electrical & Electronics Engineering |
            🎓 Final Year Project 2025
        </p>
        <p style="margin: 5px 0 0 0; font-size: 12px; opacity: 0.8;">
            🇲🇾 Malaysia Time: {current_time} • 🔄 Auto-refresh every {refresh_rate}s • 
            🎨 MUJI + Olive Maroon Theme
        </p>
    </div>
    """.format(
        current_time=current_time_malaysia.strftime('%I:%M:%S %p'),
        refresh_rate=refresh_rate
    ), unsafe_allow_html=True)
    
    # Auto-refresh
    if auto_refresh:
        time.sleep(refresh_rate)
        st.rerun()

# ================ RUN DASHBOARD ================
if __name__ == "__main__":
    main()
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