"""
☁️ CLOUD UPLOADER WITH ML RESULTS
Uploads ML-processed data to BigQuery and Streamlit
"""

import pandas as pd
from datetime import datetime, timedelta
import time
import os
from google.cloud import bigquery
from google.oauth2 import service_account

class CloudUploader:
    def __init__(self):
        self.ml_results_file = "ml_results.csv"
        self.uploaded_log = "uploaded_log.txt"
        self.project_id = "monitoring-system-with-lora"
        self.dataset_id = "sdp2_live_monitoring_system"
        self.table_id = "lora_health_data_clean2"
        self.full_table_id = f"{self.project_id}.{self.dataset_id}.{self.table_id}"
        
        # Initialize BigQuery client
        self.client = self.setup_bigquery()
    
    def setup_bigquery(self):
        """Setup BigQuery connection"""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                'service-account-key.json',
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            
            client = bigquery.Client(
                credentials=credentials,
                project=self.project_id,
                location="asia-southeast1"
            )
            
            print("✅ BigQuery client initialized")
            return client
        except Exception as e:
            print(f"❌ BigQuery setup error: {e}")
            return None
    
    def load_uploaded_ids(self):
        """Load already uploaded record IDs"""
        if not os.path.exists(self.uploaded_log):
            return set()
        
        with open(self.uploaded_log, 'r') as f:
            return set(line.strip() for line in f)
    
    def save_uploaded_id(self, record_id):
        """Save uploaded record ID to log"""
        with open(self.uploaded_log, 'a') as f:
            f.write(f"{record_id}\n")
    
    def generate_record_id(self, row):
        """Generate unique ID for record"""
        timestamp = row.get('ml_timestamp', row.get('timestamp', ''))
        device = row.get('device_id', 'unknown')
        return f"{device}_{timestamp}"
    
    def prepare_bigquery_row(self, row):
        """Prepare row for BigQuery insertion"""
        return {
            'id_user': row.get('device_id', 'UNKNOWN'),
            'timestamp': row.get('ml_timestamp', row.get('timestamp', datetime.now().isoformat())),
            'temp': float(row.get('temp', 0.0)),
            'spo2': int(row.get('spo2', 0)),
            'hr': int(row.get('hr', 0)),
            'ax': float(row.get('ax', 0.0)),
            'ay': float(row.get('ay', 0.0)),
            'az': float(row.get('az', 0.0)),
            'gx': float(row.get('gx', 0.0)),
            'gy': float(row.get('gy', 0.0)),
            'gz': float(row.get('gz', 0.0)),
            'humidity': float(row.get('humidity', 0.0)),
            'activity': row.get('ml_activity', row.get('activity', 'UNKNOWN')),
            'activity_confidence': float(row.get('ml_confidence', 0.0)),
            'source': 'LoRa_ML_System',
            'processing_stage': 'ml_processed'
        }
    
    def upload_to_bigquery(self, rows):
        """Upload rows to BigQuery"""
        if not self.client or not rows:
            return False
        
        try:
            errors = self.client.insert_rows_json(self.full_table_id, rows)
            
            if errors == []:
                print(f"✅ Uploaded {len(rows)} records to BigQuery")
                return True
            else:
                print(f"❌ BigQuery errors: {errors}")
                return False
        except Exception as e:
            print(f"❌ Upload error: {e}")
            return False
    
    def check_new_data(self):
        """Check for new ML results to upload"""
        if not os.path.exists(self.ml_results_file):
            print("ℹ️ No ML results file found")
            return []
        
        try:
            # Load ML results
            df = pd.read_csv(self.ml_results_file)
            
            if df.empty:
                return []
            
            # Load already uploaded IDs
            uploaded_ids = self.load_uploaded_ids()
            
            # Find new records
            new_rows = []
            for _, row in df.iterrows():
                record_id = self.generate_record_id(row)
                
                if record_id not in uploaded_ids:
                    new_rows.append(row)
                    self.save_uploaded_id(record_id)
            
            return new_rows
        
        except Exception as e:
            print(f"❌ Data check error: {e}")
            return []
    
    def run(self):
        """Main upload loop"""
        print("\n☁️ Cloud Uploader Started")
        print("=========================")
        print(f"Source: {self.ml_results_file}")
        print(f"Target: {self.full_table_id}")
        print("\nPress Ctrl+C to stop\n")
        
        upload_count = 0
        
        try:
            while True:
                # Check for new data
                new_data = self.check_new_data()
                
                if new_data:
                    print(f"📦 Found {len(new_data)} new records")
                    
                    # Prepare rows for BigQuery
                    rows_to_upload = []
                    for row in new_data:
                        rows_to_upload.append(self.prepare_bigquery_row(row))
                    
                    # Upload to BigQuery
                    if rows_to_upload:
                        success = self.upload_to_bigquery(rows_to_upload)
                        if success:
                            upload_count += len(rows_to_upload)
                    
                    # Display summary
                    for row in rows_to_upload[:3]:  # Show first 3
                        print(f"   👤 {row['id_user']}: {row['activity']} "
                              f"(HR:{row['hr']}, Temp:{row['temp']:.1f})")
                    
                    if len(rows_to_upload) > 3:
                        print(f"   ... and {len(rows_to_upload)-3} more")
                
                # Wait before next check
                time.sleep(5)
                
                # Periodic status
                if upload_count > 0 and upload_count % 10 == 0:
                    print(f"\n📊 Total uploaded: {upload_count} records")
                
        except KeyboardInterrupt:
            print(f"\n🛑 Uploader stopped. Total uploaded: {upload_count} records")
        except Exception as e:
            print(f"❌ Uploader error: {e}")

if __name__ == "__main__":
    uploader = CloudUploader()
    uploader.run()