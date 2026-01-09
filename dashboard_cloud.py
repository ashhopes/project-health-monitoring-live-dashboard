# Uploader.py (Simplified - No dotenv required)
"""
LoRa Receiver Data Uploader for Multi-Node Health Monitoring System
This script reads data from LoRa receiver (COM8) and uploads to BigQuery
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
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('lora_receiver.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LoRaReceiverUploader:
    def __init__(self, config_file=None):
        """Initialize the receiver uploader"""
        self.config = self.load_config(config_file)
        self.receiver_port = None
        self.bq_client = None
        self.data_queue = queue.Queue()
        self.running = False
        
        # Initialize connections
        self.init_receiver()
        self.init_bigquery()
        
    def load_config(self, config_file=None):
        """Load configuration from file or use defaults"""
        config = {
            # Receiver Configuration
            'receiver_port': 'COM8',  # Default receiver port
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
                '001': 'user_001',
                '002': 'user_002'
            }
        }
        
        # Load from config file if provided
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    file_config = json.load(f)
                    config.update(file_config)
            except Exception as e:
                logger.error(f"Error loading config file: {e}")
        
        # Override with environment variables if they exist
        config['receiver_port'] = os.getenv('RECEIVER_PORT', config['receiver_port'])
        config['baud_rate'] = int(os.getenv('BAUD_RATE', config['baud_rate']))
        config['project_id'] = os.getenv('GOOGLE_CLOUD_PROJECT', config['project_id'])
        
        return config
    
    def init_receiver(self):
        """Initialize serial connection to LoRa receiver"""
        try:
            self.receiver_port = serial.Serial(
                port=self.config['receiver_port'],
                baudrate=self.config['baud_rate'],
                timeout=self.config['timeout'],
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            logger.info(f"✅ Receiver connected on {self.config['receiver_port']} at {self.config['baud_rate']} baud")
        except Exception as e:
            logger.error(f"❌ Failed to connect to receiver on {self.config['receiver_port']}: {e}")
            logger.info("Please check:")
            logger.info("1. Is the receiver connected to COM8?")
            logger.info("2. Is the port available?")
            logger.info("3. Do you have the correct drivers installed?")
            self.receiver_port = None
    
    def init_bigquery(self):
        """Initialize BigQuery client"""
        try:
            # Try to load credentials from environment variable
            credentials_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
            
            if credentials_json:
                credentials_info = json.loads(credentials_json)
                credentials = service_account.Credentials.from_service_account_info(credentials_info)
                logger.info("✅ Loaded credentials from environment variable")
            else:
                # Try to load from file
                creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
                if creds_path and os.path.exists(creds_path):
                    credentials = service_account.Credentials.from_service_account_file(creds_path)
                    logger.info(f"✅ Loaded credentials from file: {creds_path}")
                else:
                    # Try default location
                    default_creds = 'service_account.json'
                    if os.path.exists(default_creds):
                        credentials = service_account.Credentials.from_service_account_file(default_creds)
                        logger.info(f"✅ Loaded credentials from default file: {default_creds}")
                    else:
                        logger.error("❌ No credentials found. Please provide Google Cloud credentials.")
                        logger.info("Options:")
                        logger.info("1. Set GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable")
                        logger.info("2. Set GOOGLE_APPLICATION_CREDENTIALS environment variable to service account file path")
                        logger.info("3. Place service_account.json in the same directory")
                        return
            
            self.bq_client = bigquery.Client(
                credentials=credentials,
                project=self.config['project_id']
            )
            logger.info("✅ BigQuery client initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize BigQuery: {e}")
            self.bq_client = None
    
    def parse_lora_data(self, raw_data):
        """
        Parse LoRa data with multiple format support
        Supports: JSON, CSV, Key-Value formats
        """
        try:
            raw_data = raw_data.strip()
            
            # Remove any non-printable characters
            raw_data = ''.join(char for char in raw_data if char.isprintable())
            
            # Debug: log raw data
            logger.debug(f"Raw data: {raw_data}")
            
            # Try JSON format
            if raw_data.startswith('{') and raw_data.endswith('}'):
                try:
                    data = json.loads(raw_data)
                    node_id = data.get('node', data.get('NODE', '001'))
                    return self.format_data(node_id, data)
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON parse error: {e}")
            
            # Try CSV format: NODE001,72,98,36.5,...
            if ',' in raw_data:
                parts = [p.strip() for p in raw_data.split(',')]
                
                # Check if first part contains node info
                node_id = '001'  # default
                if parts[0].upper().startswith('NODE'):
                    node_part = parts[0].upper()
                    node_id = node_part.replace('NODE', '').strip()
                    parts = parts[1:]  # Remove node from data
                
                # Try to parse as numbers
                if len(parts) >= 3:
                    data_dict = {}
                    try:
                        data_dict['hr'] = float(parts[0])
                        data_dict['spo2'] = float(parts[1])
                        data_dict['temp'] = float(parts[2])
                        
                        if len(parts) >= 6:
                            data_dict['ax'] = float(parts[3])
                            data_dict['ay'] = float(parts[4])
                            data_dict['az'] = float(parts[5])
                        
                        if len(parts) >= 9:
                            data_dict['gx'] = float(parts[6])
                            data_dict['gy'] = float(parts[7])
                            data_dict['gz'] = float(parts[8])
                        
                        return self.format_data(node_id, data_dict)
                    except ValueError:
                        pass
            
            # Try key-value format: HR=72,SpO2=98,TEMP=36.5,...
            if '=' in raw_data:
                data_dict = {}
                node_id = '001'
                
                pairs = raw_data.split(',')
                for pair in pairs:
                    if '=' in pair:
                        key, value = pair.split('=', 1)
                        key = key.strip().upper()
                        value = value.strip()
                        
                        if key in ['NODE', 'ID']:
                            node_id = value
                        elif key in ['HR', 'HEARTRATE', 'HEART_RATE']:
                            try:
                                data_dict['hr'] = float(value)
                            except:
                                pass
                        elif key in ['SPO2', 'SPO_2', 'OXYGEN']:
                            try:
                                data_dict['spo2'] = float(value)
                            except:
                                pass
                        elif key in ['TEMP', 'TEMPERATURE']:
                            try:
                                data_dict['temp'] = float(value)
                            except:
                                pass
                        elif key == 'AX':
                            try:
                                data_dict['ax'] = float(value)
                            except:
                                pass
                        elif key == 'AY':
                            try:
                                data_dict['ay'] = float(value)
                            except:
                                pass
                        elif key == 'AZ':
                            try:
                                data_dict['az'] = float(value)
                            except:
                                pass
                
                if data_dict:
                    return self.format_data(node_id, data_dict)
            
            # Try to extract numbers from any format
            numbers = re.findall(r"[-+]?\d*\.\d+|\d+", raw_data)
            if len(numbers) >= 3:
                node_match = re.search(r'node[:\s]*(\d+)', raw_data.lower())
                node_id = node_match.group(1) if node_match else '001'
                
                try:
                    data_dict = {
                        'hr': float(numbers[0]),
                        'spo2': float(numbers[1]),
                        'temp': float(numbers[2]),
                    }
                    
                    if len(numbers) >= 6:
                        data_dict['ax'] = float(numbers[3])
                        data_dict['ay'] = float(numbers[4])
                        data_dict['az'] = float(numbers[5])
                    
                    if len(numbers) >= 9:
                        data_dict['gx'] = float(numbers[6])
                        data_dict['gy'] = float(numbers[7])
                        data_dict['gz'] = float(numbers[8])
                    
                    return self.format_data(node_id, data_dict)
                except (ValueError, IndexError):
                    pass
            
            logger.warning(f"Could not parse data: {raw_data}")
            return None
            
        except Exception as e:
            logger.error(f"Error parsing data: {e}")
            return None
    
    def format_data(self, node_id, sensor_data):
        """Format data with metadata"""
        try:
            # Get user ID from node mapping
            user_id = self.config['nodes'].get(node_id, f'user_{node_id.zfill(3)}')
            
            timestamp = datetime.utcnow().isoformat() + 'Z'
            
            # Create record
            record = {
                'id_user': user_id,
                'timestamp': timestamp,
                'received_at': timestamp,
                'node_id': node_id,
                'receiver_port': self.config['receiver_port']
            }
            
            # Add sensor data
            for key, value in sensor_data.items():
                if key.lower() not in ['node', 'id', 'timestamp']:
                    record[key.lower()] = value
            
            # Add simulated system data (if not in sensor_data)
            if 'packet_rssi' not in record:
                record['packet_rssi'] = np.random.randint(-90, -60)  # Good signal
            
            logger.info(f"📡 Parsed Node {node_id} ({user_id}): HR={record.get('hr', 'N/A')}, SpO2={record.get('spo2', 'N/A')}")
            return record
            
        except Exception as e:
            logger.error(f"Error formatting data: {e}")
            return None
    
    def read_receiver(self):
        """Read data from receiver"""
        if not self.receiver_port:
            logger.error("Receiver not available")
            return
        
        buffer = ""
        logger.info("📡 Listening for LoRa data...")
        
        while self.running:
            try:
                if self.receiver_port.in_waiting > 0:
                    # Read line
                    line = self.receiver_port.readline()
                    
                    try:
                        decoded = line.decode('utf-8', errors='ignore').strip()
                        if decoded:
                            buffer += decoded
                            
                            # Check for complete messages (end with newline)
                            if '\n' in buffer or '\r' in buffer:
                                lines = buffer.splitlines()
                                for line_text in lines:
                                    if line_text.strip():
                                        parsed = self.parse_lora_data(line_text)
                                        if parsed:
                                            self.data_queue.put(parsed)
                                            logger.debug(f"✅ Queued: {parsed['id_user']}")
                                
                                buffer = ""  # Clear buffer
                    
                    except UnicodeDecodeError:
                        # Try other encodings
                        try:
                            decoded = line.decode('ascii', errors='ignore').strip()
                            if decoded:
                                parsed = self.parse_lora_data(decoded)
                                if parsed:
                                    self.data_queue.put(parsed)
                        except:
                            logger.warning("Failed to decode data")
                        buffer = ""
                
                time.sleep(0.01)
                
            except serial.SerialException as e:
                logger.error(f"Serial error: {e}")
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error reading: {e}")
                time.sleep(1)
    
    def upload_batch(self, batch):
        """Upload batch to BigQuery"""
        if not self.bq_client:
            logger.error("BigQuery client not available")
            return False
        
        try:
            table_ref = f"{self.config['project_id']}.{self.config['dataset_id']}.{self.config['table_id']}"
            
            df = pd.DataFrame(batch)
            
            # Upload
            job = self.bq_client.load_table_from_dataframe(
                df, 
                table_ref,
                job_config=bigquery.LoadJobConfig(
                    write_disposition=bigquery.WriteDisposition.WRITE_APPEND
                )
            )
            
            job.result()  # Wait for completion
            
            logger.info(f"✅ Uploaded {len(batch)} records to BigQuery")
            
            # Show summary
            for user_id in df['id_user'].unique():
                count = (df['id_user'] == user_id).sum()
                logger.info(f"   - {user_id}: {count} records")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Upload failed: {e}")
            return False
    
    def process_data(self):
        """Process and upload data in batches"""
        logger.info("🔄 Starting data processor...")
        
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
                    data = None
                
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
                        logger.warning("Upload failed, keeping in batch")
                        time.sleep(5)  # Wait before retry
                
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Processor error: {e}")
                time.sleep(1)
    
    def simulate_data(self):
        """Generate simulated data for testing"""
        logger.info("🧪 Generating simulated data...")
        
        nodes = ['001', '002']
        
        while self.running:
            for node_id in nodes:
                try:
                    # Create realistic sensor data
                    if node_id == '001':
                        hr = np.random.randint(65, 85)
                        spo2 = np.random.randint(97, 100)
                        temp = np.random.uniform(36.2, 36.8)
                    else:
                        hr = np.random.randint(75, 95)
                        spo2 = np.random.randint(95, 99)
                        temp = np.random.uniform(36.5, 37.2)
                    
                    data = {
                        'hr': hr,
                        'spo2': spo2,
                        'temp': temp,
                        'ax': np.random.uniform(-0.5, 0.5),
                        'ay': np.random.uniform(-0.5, 0.5),
                        'az': np.random.uniform(9.7, 10.0),
                        'gx': np.random.uniform(-0.2, 0.2),
                        'gy': np.random.uniform(-0.2, 0.2),
                        'gz': np.random.uniform(-0.2, 0.2)
                    }
                    
                    formatted = self.format_data(node_id, data)
                    if formatted:
                        self.data_queue.put(formatted)
                        logger.info(f"🧪 Simulated Node {node_id}: HR={hr}, SpO2={spo2}")
                    
                except Exception as e:
                    logger.error(f"Simulation error: {e}")
                
                time.sleep(np.random.uniform(2, 4))
    
    def start(self, simulate=False):
        """Start the uploader"""
        self.running = True
        
        # Show configuration
        logger.info("=" * 60)
        logger.info("🚀 LoRa Health Monitoring - Data Uploader")
        logger.info("=" * 60)
        logger.info(f"Receiver Port: {self.config['receiver_port']}")
        logger.info(f"Baud Rate: {self.config['baud_rate']}")
        logger.info(f"Project: {self.config['project_id']}")
        logger.info(f"Table: {self.config['table_id']}")
        logger.info(f"Nodes: {self.config['nodes']}")
        logger.info(f"Mode: {'Simulation' if simulate else 'Live'}")
        logger.info("=" * 60)
        
        # Start threads
        if simulate:
            sim_thread = threading.Thread(target=self.simulate_data, daemon=True)
            sim_thread.start()
            logger.info("✅ Started simulation thread")
        else:
            if self.receiver_port:
                receiver_thread = threading.Thread(target=self.read_receiver, daemon=True)
                receiver_thread.start()
                logger.info("✅ Started receiver thread")
            else:
                logger.error("❌ No receiver available, cannot start in live mode")
                self.running = False
                return
        
        # Start processor thread
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
        logger.info("🛑 Stopping uploader...")
        self.running = False
        
        if self.receiver_port:
            self.receiver_port.close()
            logger.info("✅ Receiver closed")
        
        logger.info("✅ Uploader stopped")

def main():
    """Main function"""
    print("=" * 60)
    print("LoRa Health Monitoring - Data Uploader")
    print("=" * 60)
    print()
    
    import argparse
    parser = argparse.ArgumentParser(description='Upload LoRa data to BigQuery')
    parser.add_argument('--simulate', action='store_true', help='Use simulated data')
    parser.add_argument('--port', help='Receiver port (e.g., COM8)')
    parser.add_argument('--config', help='Configuration file')
    
    args = parser.parse_args()
    
    # Create uploader
    uploader = LoRaReceiverUploader(config_file=args.config)
    
    # Override port if specified
    if args.port:
        uploader.config['receiver_port'] = args.port
    
    try:
        uploader.start(simulate=args.simulate)
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
        uploader.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        uploader.stop()

if __name__ == "__main__":
    main()