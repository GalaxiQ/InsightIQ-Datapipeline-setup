# InsightsIQ Platform Setup Guide

This guide covers the end-to-end flow for setting up and running the InsightsIQ platform, including the API services and data transformation (dbt) layer.

## Prerequisites

- **Docker & Docker Compose**: For running the database infrastructure.
- **Python 3.10+**: For running the API service.
- **dbt-postgres**: For running data transformations.

## 1. Infrastructure Setup

Start the PostgreSQL database infrastructure.

```bash
cd infra
docker-compose up -d
```

This starts:
- `master_db` (Port 5432): Stores tenant registry.
- `tenant_db` (Port 5433): Stores actual tenant data (in production, this might be multiple instances).

## 2. API Service Setup

The API service handles tenant registration, schema bootstrapping, and data ingestion.

### Install Dependencies
```bash
cd services/api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run the API
```bash
# From services/api directory
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
API docs will be available at: http://localhost:8000/docs

## 3. End-to-End Usage Flow

### A. Register a Tenant
Create a new tenant organization. This registers them in the master DB.

**POST** `/tenant/register`
```json
{
  "org_name": "Nike",
  "host": "tenant_db",
  "port": 5432,
  "db_name": "brand_intelligence",
  "user": "insightiq",
  "password": "insightiq"
}
```
*Note: In this local Docker setup, we use `tenant_db` as the host because the API container (if Dockerized) or dbt sees it by that name. If running API locally, ensure `tenant_db` resolves to localhost or use `localhost`.*

**Response**:
```json
{
  "tenant_id": "c7b3d8e0-5e0b-4b2a-8b1e-0c9d8e7f6a5b"
}
```
**Copy the `tenant_id` from the response. You will use it for all subsequent requests.**

### B. Bootstrap Tenant Schema
Create the raw data tables for the new tenant.

**POST** `/schema/bootstrap`
**Headers**: `x-tenant-id: <YOUR_TENANT_ID>`

**Response**: `{"status": "schema ready"}`

### C. Ingest Data
Push raw social media data into the system.

**POST** `/ingest/social`
**Headers**: `x-tenant-id: <YOUR_TENANT_ID>`
**Body**:
```json
{
  "brand_id": "nike_us",
  "platform": "facebook",
  "schema_version": "v1",
  "payload": {
    "id": "12345",
    "name": "Nike",
    "username": "nike",
    "category": "Apparel",
    "followers_count": 1000000,
    "website": "https://nike.com",
    "posts": {
      "data": [
        {
          "id": "post_1",
          "message": "Just Do It",
          "created_time": "2023-10-27T10:00:00",
          "reactions": {"summary": {"total_count": 500}},
          "comments": {"summary": {"total_count": 50}},
          "shares": {"count": 20}
        }
      ]
    }
  }
}
```

## 4. Running dbt (Data Transformation)

Since the `dbt-worker` service is not currently active, you must trigger transformations manually to move data from `raw_events` to the business tables (`dim_account`, `fct_posts`).

### Install dbt
```bash
pip install dbt-postgres
```

### Configuration
Ensure your `services/dbt/profiles.yml` is correctly configured. 
*Note: If running dbt locally (outside Docker), you may need to change `host: tenant_db` to `host: localhost` in `profiles.yml`.*

### Run Models
Run this command from the `services/dbt` directory:

```bash
dbt build --profiles-dir .
```

This will:
1.  Read `raw_events` logic from `models/staging`.
2.  Populate `dim_account` and `fct_posts` in the `analytics` schema.
3.  Run any defined data tests.

## 5. Fetch Insights

Now that dbt has processed the data, you can query the business layer via the API.

**GET** `/serve/brands/nike_us/accounts`
**Headers**: `x-tenant-id: <YOUR_TENANT_ID>`

**Response**:
```json
[
  {
    "name": "Nike",
    "followers": 1000000,
    "rating": null,
    "last_updated": "..."
  }
]
```
