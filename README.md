# Fraud Prevention Demo on GCP (SMS Pumping & AIT)

This repository contains the code and configuration for a Fraud Prevention Demo on Google Cloud Platform (GCP), focusing on CPaaS fraud scenarios like SMS Pumping and Artificially Inflated Traffic (AIT). The demo showcases how to use synthetic data generation, advanced analytics with BigQuery (including Continuous Queries and Object Tables), and generative AI with Vertex AI to detect and prevent fraudulent transactions.

## Project Structure

The project is organized into the following phases:

### Phase 1: The Multimodal Data Layer (Structured + Unstructured)

This phase establishes the data foundation handling both structured logs and unstructured data.

*   **Structured Data**: Standard SMS logs (Timestamp, Sender ID, Destination, Cost, IP Address) streamed via Pub/Sub into BigQuery.
*   **Unstructured Data (The Multimodal Twist)**:
    *   **Call/Audio Snippets**: For "Flash Calls", metadata is stored in BQ and audio/signaling logs in Cloud Storage.
    *   **Image Metadata**: For "Smishing", screenshots of fraudulent websites are stored in Cloud Storage.
*   **Integration**: Use BigQuery Object Tables to create a unified view, allowing Gemini models to run directly over images/audio files using SQL to extract "Intent" or "Risk Score".

### Phase 2: Real-Time Detection: Continuous Queries

This phase involves developing the core logic for processing transactions and detecting fraud in real-time.

*   **Continuous Queries (CQ)** act as your "Always-On" radar, processing data as it arrives.
*   **The Logic**: Compare streaming traffic against a "Historical Baseline" table.
*   **The Query Pattern**:
    *   **Windowing**: Calculate the count of messages per destination in a 30-second sliding window.
    *   **Join**: Compare this to the 30-day average for that same destination.
    *   **Threshold**: If $CurrentRate > (HistoricalAverage * 10)$, trigger an event.

### Phase 3: The Agentic Architecture: "The Investigator"

This phase introduces AI agents to handle alerts and investigate potential fraud.

*   **Trigger**: A Continuous Query detects an anomaly and calls a BigQuery Remote Function.
*   **The Agent's Goal**: "Determine if this traffic is legitimate business growth or an AIT attack, and take action."
*   **Autonomous Tools**: The Agent is granted "Tools" (functions) it can call:
    *   `get_customer_history(customer_id)`: Queries historical BQ data.
    *   `analyze_message_content(sample_text)`: Uses Gemini to check if the SMS body looks like a template-based bot attack.
    *   `check_ip_reputation(ip_address)`: Hits an external API to see if the IP is a known proxy.
*   **Decision & Action**: The Agent can autonomously call an API to throttle the traffic or quarantine the messages.

### Phase 4: The End-to-End Demo Flow

| Step | Component | Action |
| :--- | :--- | :--- |
| Ingest | Pub/Sub | Streams live SMS traffic and links to "unstructured" phishing screenshots. |
| Store | BigQuery | Real-time table receives the stream; Object Table manages the screenshots. |
| Detect | Continuous Queries | Constant SQL monitoring: `SELECT * FROM stream WHERE rate > threshold`. |
| Analyze | BQ ML + Gemini | Extracts features from message text and screenshots to confirm "phishing" intent. |
| Act | AI Agent | Receives the alert, "reasons" through the logs, and triggers a mitigation script. |

## How to Run the Streaming Simulation

Follow these steps to run the real-time data generation and ingestion pipeline.

### Step 1: Activate Virtual Environment and Install Dependencies
Ensure you have activated the virtual environment and installed the required Python packages.

```bash
source .venv/bin/activate
python3 -m pip install google-cloud-pubsub google-cloud-bigquery faker
```

### Step 2: Ensure Pub/Sub Resources Exist
Create the Pub/Sub topic and subscription if they do not already exist.

```bash
gcloud pubsub topics create fraud-transactions-topic --project=fraud-prevention-demo
gcloud pubsub subscriptions create fraud-transactions-sub --topic=fraud-transactions-topic --project=fraud-prevention-demo
```

### Step 3: Ensure BigQuery Table Exists
Create the `streaming_transactions` table with the correct schema.

```bash
bq mk --table fraud-prevention-demo:fraud_data.streaming_transactions timestamp:TIMESTAMP,sender_id:STRING,destination:STRING,cost:FLOAT,ip_address:STRING,unstructured_ref:STRING
```

### Step 4: Run the Scripts (Use Separate Terminals)
Run the streamer to generate data and the bridge to load it into BigQuery.

**Terminal 1:**
```bash
python3 data_generator/stream_data.py
```

**Terminal 2:**
```bash
python3 data_generator/pubsub_to_bq.py
```

### Step 5: Verify Data in BigQuery
Check if data is arriving in BigQuery by running:

```bash
bq query --use_legacy_sql=false 'SELECT * FROM `fraud-prevention-demo.fraud_data.streaming_transactions` ORDER BY timestamp DESC LIMIT 10'
```

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.

