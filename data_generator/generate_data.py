"""
Synthetic Data Generator for Fraud Prevention Demo (Telco Context).

This script generates realistic transaction data for a Telco company (Sinch),
including normal transactions and specific fraud scenarios, and saves it to a CSV file.
It also populates the receipt image GCS paths with sample receipts.
"""

import csv
import uuid
from datetime import datetime, timedelta
import random
from faker import Faker

fake = Faker()

def generate_data(num_records=1000):
    """Generates synthetic transaction data with a Telco (Sinch) context."""
    data = []
    
    # Generate normal data
    normal_records = num_records - 30 - 2 # Leave room for fraud scenarios
    
    merchants = ["Sinch SMS", "Sinch Voice", "Sinch API", "Sinch Verification", "Sinch Messaging"]
    receipt_paths = [
        "gs://fraud-prevention-demo-receipts/receipt_1.png",
        "gs://fraud-prevention-demo-receipts/receipt_2.png",
        "gs://fraud-prevention-demo-receipts/receipt_3.png"
    ]
    
    for _ in range(normal_records):
        event_timestamp = datetime.utcnow() - timedelta(days=random.randint(1, 30))
        data.append({
            'transaction_id': str(uuid.uuid4()),
            'event_timestamp': event_timestamp.isoformat() + 'Z',
            'amount': round(random.uniform(5.00, 200.00), 2), # Typical top-up or small bill
            'merchant': random.choice(merchants),
            'customer_id': random.randint(1000, 2000),
            'receipt_image_gcs_path': random.choice(receipt_paths + [None]) # 25% chance of None if we assume 3 paths + None
        })
        
    # Fraud Scenario 1: 5 customers making 6 transactions of less than $10 within 1 hour.
    # Total 30 records. (Simulating rapid small top-ups or micro-usage)
    fraud_customers_s1 = [fake.unique.random_int(min=1000, max=2000) for _ in range(5)]
    for customer_id in fraud_customers_s1:
        start_time = datetime.utcnow() - timedelta(days=random.randint(1, 30))
        for i in range(6):
            event_timestamp = start_time + timedelta(minutes=i * 5)
            data.append({
                'transaction_id': str(uuid.uuid4()),
                'event_timestamp': event_timestamp.isoformat() + 'Z',
                'amount': round(random.uniform(1.00, 9.99), 2),
                'merchant': random.choice(merchants),
                'customer_id': customer_id,
                'receipt_image_gcs_path': random.choice(receipt_paths + [None])
            })
            
    # Fraud Scenario 2: 2 new customers making a first-time purchase over $2000.
    # Total 2 records. (Simulating large bulk purchase or enterprise fraud)
    fraud_customers_s2 = [fake.unique.random_int(min=2001, max=3000) for _ in range(2)]
    for customer_id in fraud_customers_s2:
        event_timestamp = datetime.utcnow() - timedelta(days=random.randint(1, 30))
        data.append({
            'transaction_id': str(uuid.uuid4()),
            'event_timestamp': event_timestamp.isoformat() + 'Z',
            'amount': round(random.uniform(2000.01, 5000.00), 2),
            'merchant': "Sinch Enterprise Bulk",
            'customer_id': customer_id,
            'receipt_image_gcs_path': random.choice(receipt_paths + [None])
        })
        
    # Shuffle to mix normal and fraud data
    random.shuffle(data)
    return data

def save_to_csv(data, filename="synthetic_transactions.csv"):
    """Saves the generated data to a CSV file."""
    if not data:
        return
        
    fieldnames = data[0].keys()
    
    with open(filename, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)

if __name__ == "__main__":
    print("Generating synthetic data (Telco Context with Receipts)...")
    data = generate_data(num_records=1000)
    save_to_csv(data, "data_generator/synthetic_transactions.csv")
    print(f"Done. Generated {len(data)} records in data_generator/synthetic_transactions.csv")
