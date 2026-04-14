# BigQuery Capabilities for Fraud Detection

This directory contains files related to using BigQuery features for fraud detection, including Multimodal Analysis and Continuous Queries.

## Phase 2: Continuous Queries Setup

Continuous Queries allow you to process data as it arrives in BigQuery. They require specific setup steps.

### Pre-requisites

1.  **BigQuery Reservations (Slots)**: Continuous queries require dedicated slots (Enterprise or Enterprise Plus edition).
2.  **APIs**: Ensure `bigquery.googleapis.com`, `aiplatform.googleapis.com`, and `notebooks.googleapis.com` are enabled.
3.  **Permissions**: You need `BigQuery Resource Admin` to create reservations, and `Vertex AI User` for Colab Enterprise.

### Setup Steps

#### Step 1: Create Reservation and Assignment
Since our dataset is in the `US` multi-region, create the reservation and assignment in `US`. Note that reservation names cannot contain underscores (`_`), use dashes (`-`) instead.

**Create Reservation:**
```bash
bq mk --reservation --project_id=fraud-prevention-demo \
  --slots=100 --edition=ENTERPRISE --location=US continuous-query-res
```

**Assign Reservation:**
```bash
bq mk --reservation_assignment --project_id=fraud-prevention-demo \
  --reservation_id=fraud-prevention-demo:US.continuous-query-res \
  --job_type=CONTINUOUS --assignee_type=PROJECT --assignee_id=fraud-prevention-demo \
  --location=US
```

#### Step 2: Colab Enterprise Notebook
Use a Colab Enterprise BQ notebook to create and manage Continuous Queries.
