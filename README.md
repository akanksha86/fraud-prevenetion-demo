# Fraud Prevention Demo on GCP (SMS Pumping & AIT)

This repository contains the code and configuration for a Fraud Prevention Demo on Google Cloud Platform (GCP), focusing on CPaaS fraud scenarios like SMS Pumping and Artificially Inflated Traffic (AIT). The demo showcases how to use synthetic data generation, advanced analytics with BigQuery (including Continuous Queries and Object Tables), and generative AI with Vertex AI to detect and prevent fraudulent transactions.

## Current Status: Phase 3 Completed

We have completed the data generation and infrastructure setup (Phase 1), real-time detection with notebook simulation (Phase 2), and the **Agentic Architecture** with ADK and UI (Phase 3).

*   [x] Phase 1: Multimodal Data Layer (Data Generation & Upload)
*   [x] Phase 2: Real-Time Detection (Continuous Queries & Notebook Simulation)
*   [x] Phase 3: Agentic Architecture

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

This phase introduces a multi-agent system to handle alerts and investigate potential fraud autonomously.

*   **Framework**: Built using Google Agent Development Kit (ADK).
*   **Orchestration**: Uses a `SequentialAgent` pipeline.
*   **Sub-Agents**:
    *   **Profiler**: Queries BigQuery for customer history and automatically finds the last known IP and associated asset.
    *   **Inspector**: Queries BigQuery for IP reputation.
    *   **Analyst**: Uses Gemini 2.5 Pro to analyze message text and GCS assets (images/audio) for fraud patterns.
    *   **Decision**: Makes the final decision based on inputs from previous agents.
*   **UI**: A Gradio interface allows human-in-the-loop interaction to trigger investigations and view agent reasoning.

#### Possible Decisions:
*   **ALLOW**: Traffic is deemed legitimate based on historical patterns and low content risk score.
*   **QUARANTINE**: Traffic is flagged as potentially fraudulent (e.g., high risk score from Gemini or suspicious IP history) and should be blocked or reviewed.

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

## How to Run Phase 3: Agentic Architecture

Follow these steps to run the multi-agent ADK server and the Gradio UI.

### Step 1: Activate Virtual Environment
Ensure you have activated the virtual environment in both terminals.

```bash
source .venv/bin/activate
```

### Step 2: Authenticate with Google Cloud
Ensure you are authenticated to access BigQuery and Vertex AI.

```bash
gcloud auth application-default login
```

### Step 3: Run the ADK Backend Server (Terminal 1)
Start the API server on port 8001.

```bash
adk api_server --port 8001 agents
```

### Step 4: Run the Gradio UI (Terminal 2)
Start the frontend interface.

```bash
python3 ui/app.py
```

### Step 5: Verify the Flow
Open the Gradio URL in your browser (usually `http://127.0.0.1:7860`), enter a destination number (e.g., `263222222222`), and click Submit to see the automated investigation!

## How to Run the Demo Notebook

We have created a Jupyter notebook to demonstrate real-time fraud detection and multimodal analysis.

1.  Open `bq_capabilities/continuous_queries.ipynb` in Colab Enterprise or your Jupyter environment.
2.  Follow the instructions in the notebook to:
    *   Monitor the stream and detect fraud spikes in real-time.
    *   Set up Object Tables and Gemini Remote Models.
    *   Run multimodal analysis on flagged transactions.

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.
