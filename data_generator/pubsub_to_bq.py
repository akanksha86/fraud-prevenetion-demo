"""
Pub/Sub to BigQuery Bridge (Streaming Inserts).

This script pulls messages from a Pub/Sub subscription and writes them to a
BigQuery table using the standard streaming inserts API.
"""

import os
import json
from google.cloud import pubsub_v1
from google.cloud import bigquery

# Configuration
PROJECT_ID = "fraud-prevention-demo"
SUBSCRIPTION_ID = "fraud-transactions-sub"
DATASET_ID = "fraud_data"
TABLE_ID = "streaming_transactions"

subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)

bq_client = bigquery.Client(project=PROJECT_ID)
table_ref = bq_client.dataset(DATASET_ID).table(TABLE_ID)

def callback(message):
    """Callback function to process received messages."""
    print(f"Received message: {message.data.decode('utf-8')}")
    try:
        data = json.loads(message.data.decode('utf-8'))
        
        # Insert into BigQuery
        errors = bq_client.insert_rows_json(table_ref, [data])
        
        if errors == []:
            print("New rows have been added.")
            message.ack()
        else:
            print(f"Encountered errors while inserting rows: {errors}")
            # Nack so it can be retried if needed
            message.nack()
            
    except Exception as e:
        print(f"Error processing message: {e}")
        message.nack()

def receive_messages():
    """Listens for messages on the subscription."""
    print(f"Listening for messages on {subscription_path}...")
    streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
    
    try:
        # Keep the main thread alive
        streaming_pull_future.result()
    except KeyboardInterrupt:
        streaming_pull_future.cancel()
        print("\nStopped listening.")
    except Exception as e:
        print(f"Listening failed: {e}")
        streaming_pull_future.cancel()

if __name__ == "__main__":
    receive_messages()
