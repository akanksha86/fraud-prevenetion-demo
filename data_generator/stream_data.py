"""
Simulated Stream Generator for Fraud Prevention Demo (SMS Pumping & AIT).

This script generates simulated real-time SMS traffic data for a CPaaS company (Sinch)
and publishes it to a Pub/Sub topic. It simulates both normal traffic and
occasional fraud spikes (AIT).
"""

import time
import uuid
from datetime import datetime, timezone
import random
import json
from faker import Faker
from google.cloud import pubsub_v1

fake = Faker()

# Configuration
PROJECT_ID = "fraud-prevention-demo"
TOPIC_ID = "fraud-transactions-topic"

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

# State for simulating fraud bursts
is_fraud_burst = False
fraud_burst_count = 0
fraud_ip = None
fraud_destination_prefix = None

def generate_transaction():
    """Generates a single simulated transaction (SMS log)."""
    global is_fraud_burst, fraud_burst_count, fraud_ip, fraud_destination_prefix
    
    high_cost_destinations = ['+234', '+252', '+263'] # Nigeria, Somalia, Zimbabwe
    normal_destinations = ['+1', '+44', '+33', '+49', '+81', '+61']
    
    asset_paths = [
        "gs://fraud-prevention-demo-assets/phishing_bank.png",
        "gs://fraud-prevention-demo-assets/phishing_delivery.png",
        "gs://fraud-prevention-demo-assets/dummy_audio_1.wav",
        "gs://fraud-prevention-demo-assets/dummy_audio_2.wav"
    ]
    
    # 5% chance to start a fraud burst if not already in one
    if not is_fraud_burst and random.random() < 0.05:
        is_fraud_burst = True
        fraud_burst_count = random.randint(20, 50) # Number of messages in the burst
        fraud_ip = fake.ipv4()
        fraud_destination_prefix = random.choice(high_cost_destinations)
        print(f"\n[SYSTEM] Starting fraud burst to {fraud_destination_prefix} from {fraud_ip}...")
        
    if is_fraud_burst:
        fraud_burst_count -= 1
        if fraud_burst_count <= 0:
            is_fraud_burst = False
            print("\n[SYSTEM] Ending fraud burst.")
            
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'sender_id': 'SinchMsg' + str(random.randint(100, 999)),
            'destination': fraud_destination_prefix + str(random.randint(100000000, 999999999)),
            'cost': round(random.uniform(0.10, 0.50), 4),
            'ip_address': fraud_ip,
            'unstructured_ref': random.choice(asset_paths) # High chance of linking to asset in fraud
        }
    else:
        destination = random.choice(normal_destinations) + str(random.randint(100000000, 999999999))
        # 2% chance of normal traffic hitting high cost destination
        if random.random() < 0.02:
            destination = random.choice(high_cost_destinations) + str(random.randint(100000000, 999999999))
            
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'sender_id': 'SinchMsg' + str(random.randint(100, 999)),
            'destination': destination,
            'cost': round(random.uniform(0.01, 0.05), 4),
            'ip_address': fake.ipv4(),
            'unstructured_ref': random.choice(asset_paths + [None] * 20) # Low chance in normal traffic
        }

def stream_data():
    """Continuously generates and publishes transactions."""
    print(f"Starting to stream SMS logs to {topic_path}...")
    try:
        while True:
            transaction = generate_transaction()
            message_data = json.dumps(transaction).encode("utf-8")
            
            # Publish the message
            future = publisher.publish(topic_path, message_data)
            
            if is_fraud_burst:
                print(f"🔥 Fraud Alert | Dest: {transaction['destination']} | IP: {transaction['ip_address']}")
            else:
                print(f"Published message ID: {future.result()} | Dest: {transaction['destination']}")
            
            # Wait a bit before the next transaction
            # Faster during fraud burst
            if is_fraud_burst:
                time.sleep(random.uniform(0.1, 0.3))
            else:
                time.sleep(random.uniform(0.5, 2.0))
            
    except KeyboardInterrupt:
        print("\nStreaming stopped.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    stream_data()
