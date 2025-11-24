import time
import sqlite3
import csv
from datetime import datetime
from google.cloud import bigquery
from google.oauth2 import service_account

# --- BigQuery Setup ---
credentials = service_account.Credentials.from_service_account_file(
    "monitoring-system-with-lora-05bc326b792a.json"   # local JSON key
)
client = bigquery.Client(
    credentials=credentials,
    project="monitoring-system-with-lora",
    location="asia-southeast1"
)
table_id = "monitoring-system-with-lora.sdp2_live_monitoring_system.lora_health_data_clean2"

# --- Local Database Setup (SQLite) ---
sqlite_file = "local_health_data.db"
conn = sqlite3.connect(sqlite_file)
cursor = conn.cursor()

# Create table if not exists
cursor.execute("""
CREATE TABLE IF NOT EXISTS health_data (
    timestamp TEXT,
    temp REAL,
    hr INTEGER,
    spo2 INTEGER,
    humidity REAL
)
""")
conn.commit()

# --- Local CSV Setup ---
csv_file = "local_health_data.csv"
# Ensure header exists
with open(csv_file, "a", newline="") as f:
    writer = csv.writer(f)
    if f.tell() == 0:  # file is empty
        writer.writerow(["timestamp", "temp", "hr", "spo2", "humidity"])

# --- Function to insert data ---
def insert_sensor_data(temp, hr, spo2, humidity):
    ts = datetime.utcnow().isoformat()

    row = {
        "timestamp": ts,
        "temp": temp,
        "hr": hr,
        "spo2": spo2,
        "humidity": humidity
    }

    # 1. Insert into BigQuery
    errors = client.insert_rows_json(table_id, [row])
    if errors == []:
        print("✅ BigQuery row inserted:", row)
    else:
        print("❌ BigQuery errors:", errors)

    # 2. Insert into SQLite
    cursor.execute("INSERT INTO health_data VALUES (?, ?, ?, ?, ?)",
                   (ts, temp, hr, spo2, humidity))
    conn.commit()
    print("💾 Saved to SQLite")

    # 3. Append to CSV
    with open(csv_file, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([ts, temp, hr, spo2, humidity])
    print("📄 Saved to CSV")

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