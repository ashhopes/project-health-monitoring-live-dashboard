# Uploader.py - UPDATED FOR YOUR DATA FORMAT
"""
LoRa Receiver Data Uploader - Fixed for your fragmented data format
"""

import serial
import time
import json
from datetime import datetime
import pandas as pd
import numpy as np
from google.cloud import bigquery
from google.oauth2 import service_account
import threading
import queue
import logging
import re
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('lora_receiver_fixed.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LoRaDataParser:
    def __init__(self):
        self.buffer = ""
        self.current_packet = {}
        self.expected_fields = 0
        self.field_count = 0
        
    def parse_line(self, line):
        """Parse a line of data from LoRa transmitter"""
        line = line.strip()
        
        # Skip empty lines
        if not line:
            return None
        
        logger.debug(f"Raw line: {line}")
        
        # Check if this is a complete data packet
        # Pattern: temperature|humidity|heart_rate|spo2
        if '|' in line:
            parts = line.split('|')
            
            # Try to identify what type of data this is
            if len(parts) >= 4:
                # Check if this looks like vital signs: 26.3|63|72|98
                try:
                    # Check if first part is temperature-like (20-40)
                    temp = float(parts[0])
                    if 20 <= temp <= 40:
                        # Check if other parts are numeric
                        hr = float(parts[2])
                        spo2 = float(parts[3])
                        
                        # This looks like vital signs
                        self.current_packet.update({
                            'temp': temp,
                            'humidity': float(parts[1]) if len(parts) > 1 else 0,
                            'hr': hr,
                            'spo2': spo2
                        })
                        self.field_count += 4
                        logger.info(f"Parsed vitals: Temp={temp}, HR={hr}, SpO2={spo2}")
                except (ValueError, IndexError):
                    pass
            
            # Check if this looks like motion data: -0.34|0.04|0.89|-0.97|-0.31|0.54|8.860|0
            if len(parts) >= 8:
                try:
                    # Check if values are small floats (typical for motion)
                    ax = float(parts[0])
                    ay = float(parts[1])
                    az = float(parts[2])
                    
                    if -5 < ax < 5 and -5 < ay < 5 and -15 < az < 15:  # Typical accelerometer range
                        self.current_packet.update({
                            'ax': ax,
                            'ay': ay,
                            'az': az,
                            'gx': float(parts[3]) if len(parts) > 3 else 0,
                            'gy': float(parts[4]) if len(parts) > 4 else 0,
                            'gz': float(parts[5]) if len(parts) > 5 else 0
                        })
                        self.field_count += 6
                        logger.info(f"Parsed motion: ax={ax}, ay={ay}, az={az}")
                except (ValueError, IndexError):
                    pass
        
        # Check for NODE identifier
        if 'NODE_' in line or 'NOD' in line:
            # Extract node ID
            match = re.search(r'NODE?_([a-zA-Z0-9_]+)', line)
            if match:
                node_id = match.group(1)
                self.current_packet['node_id'] = node_id
                logger.info(f"Found Node: {node_id}")
        
        # Check for RESTING/activity
        if 'RESTING' in line:
            self.current_packet['activity'] = 'RESTING'
            logger.info("Activity: RESTING")
        
        # Check if we have a complete packet
        if self.field_count >= 10:  # We have both vitals and motion
            complete_packet = self.current_packet.copy()
            self.current_packet = {}
            self.field_count = 0
            return complete_packet
        
        return None

class LoRaReceiverUploader:
    def __init__(self):
        self.config = self.load_config()
        self.receiver_port = None
        self.bq_client = None
        self.data_queue = queue.Queue()
        self.running = False
        self.parser = LoRaDataParser()
        
        # Initialize connections
        self.init_receiver()
        self.init_bigquery()
        
    def load_config(self):
        """Load configuration"""
        config = {
            # Receiver Configuration
            'receiver_port': 'COM8',
            'baud_rate': 9600,
            'timeout': 1.0,
            
            # BigQuery Configuration
            'project_id': 'monitoring-system-with-lora',
            'dataset_id': 'sdp2_live_monitoring_system',
            'table_id': 'lora_health_data_clean2',
            
            # Processing Configuration
            'batch_size': 5,
            'upload_interval': 10,
            
            # Node Configuration
            'nodes': {
                'e661': 'user_001',  # From your data: NODE_e661
                'e662': 'user_002'   # Add your second node ID
            }
        }
        
        # Override with environment variables
        config['receiver_port'] = os.getenv('RECEIVER_PORT', config['receiver_port'])
        config['baud_rate'] = int(os.getenv('BAUD_RATE', config['baud_rate']))
        
        return config
    
    def init_receiver(self):
        """Initialize serial connection"""
        try:
            self.receiver_port = serial.Serial(
                port=self.config['receiver_port'],
                baudrate=self.config['baud_rate'],
                timeout=self.config['timeout']
            )
            logger.info(f"✅ Connected to {self.config['receiver_port']} at {self.config['baud_rate']} baud")
        except Exception as e:
            logger.error(f"❌ Failed to connect: {e}")
            self.receiver_port = None
    
    def init_bigquery(self):
        """Initialize BigQuery client"""
        try:
            # Try environment variable first
            credentials_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
            if credentials_json:
                credentials_info = json.loads(credentials_json)
                credentials = service_account.Credentials.from_service_account_info(credentials_info)
            else:
                # Try file
                creds_path = 'service_account.json'
                if os.path.exists(creds_path):
                    credentials = service_account.Credentials.from_service_account_file(creds_path)
                else:
                    logger.error("No credentials found")
                    return
            
            self.bq_client = bigquery.Client(
                credentials=credentials,
                project=self.config['project_id']
            )
            logger.info("✅ BigQuery client initialized")
            
        except Exception as e:
            logger.error(f"❌ BigQuery init failed: {e}")
            self.bq_client = None
    
    def format_data(self, packet):
        """Format parsed packet for BigQuery"""
        try:
            # Get node ID and map to user ID
            node_id = packet.get('node_id', 'e661')
            user_id = self.config['nodes'].get(node_id, f'user_{node_id}')
            
            timestamp = datetime.utcnow().isoformat() + 'Z'
            
            # Create record
            record = {
                'ID_user': user_id,  # Note: Capital ID to match your table
                'timestamp': timestamp,
                'temp': packet.get('temp', 0),
                'humidity': packet.get('humidity', 0),
                'spo2': packet.get('spo2', 0),
                'hr': packet.get('hr', 0),
                'ax': packet.get('ax', 0),
                'ay': packet.get('ay', 0),
                'az': packet.get('az', 0),
                'gx': packet.get('gx', 0),
                'gy': packet.get('gy', 0),
                'gz': packet.get('gz', 0),
                'activity': packet.get('activity', 'UNKNOWN'),
                'node_id': node_id,
                'receiver_port': self.config['receiver_port']
            }
            
            # Calculate acceleration magnitude
            ax = record['ax']
            ay = record['ay']
            az = record['az']
            record['acceleration_magnitude'] = np.sqrt(ax**2 + ay**2 + az**2)
            
            # Add IR and RED if available (you might need to adjust based on your actual data)
            record['ir'] = np.random.randint(50000, 100000)  # Simulated
            record['red'] = np.random.randint(20000, 80000)   # Simulated
            
            logger.info(f"📦 Formatted: {user_id} - HR={record['hr']}, SpO2={record['spo2']}, Temp={record['temp']}")
            return record
            
        except Exception as e:
            logger.error(f"Format error: {e}")
            return None
    
    def read_receiver(self):
        """Read and parse data from receiver"""
        if not self.receiver_port:
            return
        
        logger.info("📡 Listening for data...")
        
        while self.running:
            try:
                if self.receiver_port.in_waiting > 0:
                    # Read line
                    line = self.receiver_port.readline()
                    
                    try:
                        decoded = line.decode('utf-8', errors='ignore').strip()
                        if decoded:
                            # Parse the line
                            packet = self.parser.parse_line(decoded)
                            
                            if packet:
                                # Format and queue the complete packet
                                formatted = self.format_data(packet)
                                if formatted:
                                    self.data_queue.put(formatted)
                                    logger.info("✅ Queued complete packet")
                    
                    except UnicodeDecodeError:
                        # Try other encodings
                        try:
                            decoded = line.decode('ascii', errors='ignore').strip()
                            if decoded:
                                packet = self.parser.parse_line(decoded)
                                if packet:
                                    formatted = self.format_data(packet)
                                    if formatted:
                                        self.data_queue.put(formatted)
                        except:
                            pass
                
                time.sleep(0.01)
                
            except Exception as e:
                logger.error(f"Read error: {e}")
                time.sleep(1)
    
    def upload_batch(self, batch):
        """Upload batch to BigQuery"""
        if not self.bq_client:
            return False
        
        try:
            table_ref = f"{self.config['project_id']}.{self.config['dataset_id']}.{self.config['table_id']}"
            
            df = pd.DataFrame(batch)
            
            # Upload
            job = self.bq_client.load_table_from_dataframe(
                df, table_ref,
                job_config=bigquery.LoadJobConfig(
                    write_disposition=bigquery.WriteDisposition.WRITE_APPEND
                )
            )
            
            job.result()
            
            logger.info(f"✅ Uploaded {len(batch)} records")
            
            # Log summary
            for user_id in df['ID_user'].unique():
                count = (df['ID_user'] == user_id).sum()
                logger.info(f"   - {user_id}: {count} records")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Upload failed: {e}")
            return False
    
    def process_data(self):
        """Process and upload data"""
        logger.info("🔄 Starting processor...")
        
        batch = []
        last_upload = time.time()
        
        while self.running:
            try:
                # Get data from queue
                try:
                    data = self.data_queue.get(timeout=1)
                    batch.append(data)
                    logger.debug(f"Batch size: {len(batch)}")
                except queue.Empty:
                    pass
                
                # Check if we should upload
                current_time = time.time()
                time_since_upload = current_time - last_upload
                
                should_upload = (
                    len(batch) >= self.config['batch_size'] or 
                    (time_since_upload >= self.config['upload_interval'] and batch)
                )
                
                if should_upload and batch:
                    success = self.upload_batch(batch)
                    
                    if success:
                        last_upload = current_time
                        batch = []
                    else:
                        logger.warning("Upload failed, keeping batch")
                        time.sleep(5)
                
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Processor error: {e}")
                time.sleep(1)
    
    def start(self, simulate=False):
        """Start the uploader"""
        self.running = True
        
        logger.info("=" * 60)
        logger.info("🚀 LoRa Health Monitor - Fixed Uploader")
        logger.info("=" * 60)
        logger.info(f"Port: {self.config['receiver_port']}")
        logger.info(f"Baud: {self.config['baud_rate']}")
        logger.info(f"Project: {self.config['project_id']}")
        logger.info(f"Table: {self.config['table_id']}")
        logger.info("=" * 60)
        
        # Start threads
        if not simulate:
            if self.receiver_port:
                receiver_thread = threading.Thread(target=self.read_receiver, daemon=True)
                receiver_thread.start()
                logger.info("✅ Started receiver thread")
            else:
                logger.error("❌ No receiver available")
                return
        
        processor_thread = threading.Thread(target=self.process_data, daemon=True)
        processor_thread.start()
        logger.info("✅ Started processor thread")
        
        # Keep main thread running
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop the uploader"""
        logger.info("🛑 Stopping...")
        self.running = False
        
        if self.receiver_port:
            self.receiver_port.close()
            logger.info("✅ Receiver closed")

def main():
    """Main function"""
    print("=" * 60)
    print("LoRa Health Monitor - Fixed Uploader")
    print("=" * 60)
    print()
    
    import argparse
    parser = argparse.ArgumentParser(description='Upload LoRa data')
    parser.add_argument('--port', help='Receiver port')
    parser.add_argument('--simulate', action='store_true', help='Use simulated data')
    
    args = parser.parse_args()
    
    uploader = LoRaReceiverUploader()
    
    if args.port:
        uploader.config['receiver_port'] = args.port
    
    try:
        uploader.start(simulate=args.simulate)
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
        uploader.stop()
    except Exception as e:
        logger.error(f"Fatal: {e}")
        uploader.stop()

if __name__ == "__main__":
    main()