"""
Simulated Stream Generator for Fraud Prevention Demo (Telco Context).

This script generates simulated real-time transaction data for a Telco company (Sinch)
and publishes it to a Pub/Sub topic.
"""

import time
import uuid
from datetime import datetime
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

def generate_transaction():
    """Generates a single simulated transaction."""
    merchants = ["Sinch SMS", "Sinch Voice", "Sinch API", "Sinch Verification", "Sinch Messaging"]
    
    # Occasionally generate a potential fraud transaction (small amount)
    if random.random() < 0.1:
        amount = round(random.uniform(1.00, 9.99), 2)
    else:
        amount = round(random.uniform(10.00, 200.00), 2)
        
    return {
        'transaction_id': str(uuid.uuid4()),
        'event_timestamp': datetime.utcnow().isoformat() + 'Z',
        'amount': amount,
        'merchant': random.choice(merchants),
        'customer_id': random.randint(1000, 2000),
        'receipt_image_gcs_path': None # Receipts are processed separately in this architecture
    }

def stream_data():
    """Continuously generates and publishes transactions."""
    print(f"Starting to stream transactions to {topic_path}...")
    try:
        while True:
            transaction = generate_transaction()
            message_data = json.dumps(transaction).encode("utf-8")
            
            # Publish the message
            future = publisher.publish(topic_path, message_data)
            print(f"Published message ID: {future.result()} | Amount: ${transaction['amount']}")
            
            # Wait a bit before the next transaction
            time.sleep(random.uniform(0.5, 2.0))
            
    except KeyboardInterrupt:
        print("\nStreaming stopped.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    stream_data()
