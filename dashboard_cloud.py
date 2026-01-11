"""
📡 LoRa Receiver & BigQuery Uploader - FIXED VERSION
Receives data from Master Cube (ML format or pipe format) and uploads to BigQuery
"""

import serial
import time
from datetime import datetime, timedelta
from google.cloud import bigquery
from google.oauth2 import service_account
import csv
import os
import json
import numpy as np
import sys

# ============================================================================
# CONFIGURATION - ADJUST THESE!
# ============================================================================

# Serial port (change if different)
COM_PORT = "COM8"
BAUD_RATE = 9600

# BigQuery settings
PROJECT_ID = "monitoring-system-with-lora"
DATASET_ID = "sdp2_live_monitoring_system"
TABLE_ID = "lora_health_data_clean2"
FULL_TABLE_ID = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

# Backup CSV
OUTPUT_CSV = "lora_received_backup.csv"

# ============================================================================
# PARSER FUNCTIONS
# ============================================================================

def parse_pipe_format(raw_packet):
    """
    Parse pipe-separated format: |timestamp|hr|spo2|temp|humidity|ax|ay|az|gx|gy|gz|
    Example: |1609462182|92|87|40.7|27.7|0.1|0.2|0.3|0.4|0.5|0.6|
    """
    try:
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
        
    except Exception as e:
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

# ============================================================================
# BIGQUERY FUNCTIONS
# ============================================================================

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
        
        with open(filename, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=data.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(data)
        
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
    
    # Initialize BigQuery client
    try:
        bq_client = init_bigquery_client()
        print("✅ Connected to BigQuery")
    except Exception as e:
        print(f"❌ BigQuery connection failed: {e}")
        print("Please check your credentials and network connection")
        return
    
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
    
    # Statistics
    stats = {
        'total': 0,
        'pipe_format': 0,
        'ml_format': 0,
        'uploaded': 0,
        'errors': 0
    }
    
    print("\n🔄 Listening for data... (Press Ctrl+C to stop)\n")
    
    try:
        while True:
            try:
                # Check for incoming data
                if ser.in_waiting > 0:
                    # Read raw data
                    raw_data = ser.readline().decode('utf-8', errors='ignore').strip()
                    
                    if not raw_data or len(raw_data) < 3:
                        continue
                    
                    stats['total'] += 1
                    
                    # Parse based on format
                    parsed_data = None
                    
                    if raw_data.startswith('|'):
                        # Pipe format
                        print(f"[{stats['total']}] 📦 Pipe format: {raw_data[:40]}...")
                        parsed_data = parse_pipe_format(raw_data)
                        if parsed_data:
                            stats['pipe_format'] += 1
                    
                    elif raw_data.startswith('ML|'):
                        # ML format
                        print(f"[{stats['total']}] 🧠 ML format: {raw_data[:40]}...")
                        parsed_data = parse_ml_format(raw_data)
                        if parsed_data:
                            stats['ml_format'] += 1
                    
                    else:
                        print(f"[{stats['total']}] ❓ Unknown: {raw_data[:30]}...")
                    
                    # Upload if parsed successfully
                    if parsed_data:
                        if upload_to_bigquery(bq_client, parsed_data):
                            stats['uploaded'] += 1
                        
                        # Save to CSV backup
                        save_to_csv(parsed_data, OUTPUT_CSV)
                    
                    # Display stats every 10 packets
                    if stats['total'] % 10 == 0:
                        print(f"\n📊 Stats: Total={stats['total']}, "
                              f"Pipe={stats['pipe_format']}, "
                              f"ML={stats['ml_format']}, "
                              f"Uploaded={stats['uploaded']}")
                
                # Small delay to prevent CPU overload
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                print("\n\n🛑 Stopped by user")
                break
            except Exception as e:
                print(f"⚠ Processing error: {e}")
                stats['errors'] += 1
                time.sleep(1)
    
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

def test_parsers():
    """Test the parsers with sample data"""
    print("🧪 Testing parsers...\n")
    
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
    
    except Exception as e:
        print(f"❌ Error checking BigQuery: {e}")

# ============================================================================
# ENTRY POINT
# ============================================================================

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