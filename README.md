# Fraud Prevention Demo on GCP

This repository contains the code and configuration for a Fraud Prevention Demo on Google Cloud Platform (GCP). The demo showcases how to use synthetic data generation, advanced analytics with BigQuery, and generative AI with Vertex AI to detect and prevent fraudulent transactions.

## Project Structure

The project is organized into the following phases:

### Phase 1: Synthetic Data Generation & Data Foundation

This phase focuses on creating a realistic dataset to simulate transaction traffic and establishing the data foundation in BigQuery.

*   **Synthetic Data Generation**: A Python script (`data_generator/generate_data.py`) generates realistic transaction records, including both normal transactions and specific fraud scenarios (e.g., high-frequency small transactions, high-value first-time purchases).
*   **Sample Receipts**: Sample receipt images are stored in `sample_receipts/` and uploaded to a Cloud Storage bucket (`gs://fraud-prevention-demo-receipts`).
*   **BigQuery Setup**: Data is loaded into a BigQuery dataset named `fraud_data` with tables for `raw_transactions` and `processed_receipts`.

### Phase 2: Core Logic Implementation

This phase involves developing the core logic for processing transactions and detecting fraud.

*   **Ingestion**: Simulated streaming ingestion or batch load of transaction data.
*   **Receipt Processing**: A Cloud Function processes receipt images using Vertex AI Gemini to extract relevant information.
*   **Fraud Detection**: SQL queries in BigQuery identify potentially fraudulent patterns.

### Phase 3: AI Agents

This phase introduces AI agents to handle alerts and investigate potential fraud.

*   **Agent Triggers**: Alerts are published to a Pub/Sub topic (e.g., `fraud-alert`).
*   **Decisioning Agent**: A Cloud Function acts as the main decision-making agent.
*   **Sub-Agents**: Specialized agents for tasks like Google Search, deeper investigation, and ticketing.

### Phase 4: Action & Integration

This phase covers taking action based on the agent's decisions.

*   **ServiceNow Integration**: A Cloud Function creates tickets in ServiceNow for investigation, using credentials stored securely in Secret Manager.

### Phase 5: Deployment & Workshop Prep

This phase includes tools for deploying the infrastructure and preparing for workshops.

*   **Infrastructure as Code**: (Optional but Recommended) Terraform scripts to manage GCP resources.
*   **Deployment Scripts**: Shell scripts to deploy Cloud Functions and other components.

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.
