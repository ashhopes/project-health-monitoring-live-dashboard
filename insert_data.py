import time
from google.cloud import bigquery
from google.oauth2 import service_account
from datetime import datetime

# --- Load credentials (local JSON file for Slave STEMCube) ---
# Replace with the path to your downloaded service account key
credentials = service_account.Credentials.from_service_account_file(
    "monitoring-system-with-lora-05bc326b792a.json"
)

client = bigquery.Client(
    credentials=credentials,
    project="monitoring-system-with-lora",
    location="asia-southeast1"   # ✅ Malaysia/Singapore region
)

# --- Table reference ---
table_id = "monitoring-system-with-lora.sdp2_live_monitoring_system.lora_health_data_clean2"

# --- Function to insert one row ---
def insert_sensor_data(temp, hr, spo2, humidity):
    row = {
        "timestamp": datetime.utcnow().isoformat(),  # current UTC time
        "temp": temp,
        "hr": hr,
        "spo2": spo2,
        "humidity": humidity
    }
    errors = client.insert_rows_json(table_id, [row])
    if errors == []:
        print("✅ Row inserted:", row)
    else:
        print("❌ Errors:", errors)

# --- Example loop (replace with LoRa receive logic) ---
if __name__ == "__main__":
    while True:
        # Simulated sensor values (replace with LoRa data parsing)
        temp = 36.5
        hr = 78
        spo2 = 97
        humidity = 55

        insert_sensor_data(temp, hr, spo2, humidity)

        # Wait before next upload
        time.sleep(10)