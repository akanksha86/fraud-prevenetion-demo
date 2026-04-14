"""
Synthetic Data Generator for Fraud Prevention Demo (SMS Pumping & AIT).

This script generates realistic SMS traffic data for a CPaaS company (Sinch),
including normal traffic and specific fraud scenarios (SMS Pumping/AIT),
saves it to a CSV file, and loads the CSV into BigQuery.
"""

import csv
from datetime import datetime, timedelta, timezone
import random
import subprocess
from faker import Faker

fake = Faker()

def generate_data(num_records=1000):
    """Generates synthetic SMS log data with a focus on AIT fraud."""
    data = []
    
    # Configuration
    # Fixed pools of destinations to ensure matches between historical and streaming data
    fixed_normal_destinations = [
        '+1111111111', '+1222222222', '+1333333333', '+1444444444',
        '+44111111111', '+44222222222', '+44333333333',
        '+33111111111', '+33222222222',
        '+49111111111', '+49222222222',
        '+81111111111', '+81222222222',
        '+61111111111', '+61222222222'
    ]
    fixed_high_cost_destinations = [
        '+234111111111', '+234222222222',
        '+252111111111', '+252222222222',
        '+263111111111', '+263222222222'
    ]
    
    asset_paths = [
        "gs://fraud-prevention-demo-assets/phishing_bank.png",
        "gs://fraud-prevention-demo-assets/phishing_delivery.png",
        "gs://fraud-prevention-demo-assets/dummy_audio_1.wav",
        "gs://fraud-prevention-demo-assets/dummy_audio_2.wav"
    ]
    
    # Generate normal data
    normal_records = num_records - 100 # Leave room for fraud scenarios
    
    for _ in range(normal_records):
        timestamp = datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30))
        destination = random.choice(fixed_normal_destinations)
        
        # 5% chance of being a high cost destination in normal traffic
        if random.random() < 0.05:
            destination = random.choice(fixed_high_cost_destinations)
            
        data.append({
            'timestamp': timestamp.isoformat(),
            'sender_id': 'SinchMsg' + str(random.randint(100, 999)),
            'destination': destination,
            'cost': round(random.uniform(0.01, 0.05), 4),
            'ip_address': fake.ipv4(),
            'unstructured_ref': random.choice(asset_paths + [None] * 10)
        })
        
    # Fraud Scenario 1: SMS Pumping / AIT
    fraud_start_time = datetime.now(timezone.utc) - timedelta(days=random.randint(1, 5))
    fraud_ip = fake.ipv4()
    fraud_destination = random.choice(fixed_high_cost_destinations)
    
    print(f"Generating fraud scenario: Spike to {fraud_destination} from {fraud_ip}")
    
    for i in range(100):
        timestamp = fraud_start_time + timedelta(seconds=random.randint(1, 60))
        destination = fraud_destination
        
        ref = None
        if random.random() < 0.3:
            ref = asset_paths[0] # Bank phishing
        elif random.random() < 0.6:
            ref = asset_paths[1] # Delivery phishing
        elif random.random() < 0.8:
            ref = asset_paths[2] # Audio 1
        else:
            ref = asset_paths[3] # Audio 2
            
        data.append({
            'timestamp': timestamp.isoformat(),
            'sender_id': 'SinchMsg' + str(random.randint(100, 999)),
            'destination': destination,
            'cost': round(random.uniform(0.10, 0.50), 4),
            'ip_address': fraud_ip,
            'unstructured_ref': ref
        })
        
    data.sort(key=lambda x: x['timestamp'])
    return data

def save_to_csv(data, filename="synthetic_sms_logs.csv"):
    """Saves the generated data to a CSV file."""
    if not data:
        return
        
    fieldnames = data[0].keys()
    
    with open(filename, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)

def load_csv_to_bigquery(csv_file_path, table_id):
    """Loads a CSV file into a BigQuery table using bq CLI."""
    print(f"Loading {csv_file_path} into BigQuery table {table_id}...")
    try:
        parts = table_id.split('.')
        if len(parts) == 3:
            bq_table = f"{parts[0]}:{parts[1]}.{parts[2]}"
            bq_dataset = f"{parts[0]}:{parts[1]}"
        else:
            bq_table = table_id
            bq_dataset = None
            
        if bq_dataset:
            print(f"Ensuring dataset {bq_dataset} exists...")
            create_ds_cmd = f"bq mk --dataset_id={bq_dataset}"
            subprocess.run(create_ds_cmd, shell=True, capture_output=True, text=True)

        cmd = f"bq load --source_format=CSV --skip_leading_rows=1 --autodetect --replace {bq_table} {csv_file_path}"
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        print(f"Successfully loaded CSV to BigQuery.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to load CSV to BigQuery: {e}")
        print(f"Error output: {e.stderr}")

def upload_assets_to_gcs(bucket_name, source_directory, project_id):
    """Uploads all files in a directory to a GCS bucket using gcloud CLI."""
    print(f"Ensuring GCS bucket gs://{bucket_name} exists...")
    try:
        # Try to create bucket, ignore if already exists
        create_cmd = f"gcloud storage buckets create gs://{bucket_name} --project={project_id}"
        subprocess.run(create_cmd, shell=True, capture_output=True, text=True)
    except Exception as e:
        print(f"Note on bucket creation: {e}")

    print(f"Uploading assets from {source_directory} to gs://{bucket_name}...")
    try:
        # Fallback to gsutil as gcloud storage hits SSL/mTLS issues in this environment
        cmd = f"gsutil cp {source_directory}/* gs://{bucket_name}/"
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        print(f"Successfully uploaded assets to gs://{bucket_name}/")
    except subprocess.CalledProcessError as e:
        print(f"Failed to upload assets to GCS: {e}")
        print(f"Error output: {e.stderr}")

if __name__ == "__main__":
    PROJECT_ID = "fraud-prevention-demo"
    BUCKET_NAME = "fraud-prevention-demo-assets"
    TABLE_ID = f"{PROJECT_ID}.fraud_data.historical_transactions"
    
    print("Generating synthetic SMS logs (AIT Context)...")
    data = generate_data(num_records=1000)
    csv_filename = "data_generator/synthetic_sms_logs.csv"
    save_to_csv(data, csv_filename)
    print(f"Done. Generated {len(data)} records in {csv_filename}")
    
    # Load CSV to BigQuery
    load_csv_to_bigquery(csv_filename, TABLE_ID)
    
    # Upload assets to GCS
    upload_assets_to_gcs(BUCKET_NAME, "synthetic_assets", PROJECT_ID)
