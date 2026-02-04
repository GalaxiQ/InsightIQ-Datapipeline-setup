# InsightsIQ Platform (Stateless Edition)

This guide covers the setup and usage of the simplified, stateless InsightsIQ API. This version removes the central tenant registry and allows you to connect to any database dynamically by passing credentials in the request payload.

## Prerequisites

- **Docker & Docker Compose**: For running the database infrastructure.
- **Python 3.10+**: For running the API service.

## 1. API Service Setup

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
API docs: http://localhost:8000/docs

## 3. Usage Flow

### A. Bootstrap Schema
Create the raw data tables in your target database.

**POST** `/schema/bootstrap`
**Body**:
```json
{
  "db_config": {
    "host": "tenant_db",
    "port": 5432,
    "db_name": "brand_intelligence",
    "user": "insightiq",
    "password": "insightiq"
  }
}
```
*Note: We assume the API container sees the DB as `tenant_db`. If running locally, you might need to use `localhost` and the exposed port (5433).*

### B. Ingest Data
Push raw data. Note that you must provide the keys again.

**POST** `/ingest/social`
**Body**:
```json
{
  "db_config": {
    "host": "tenant_db",
    "port": 5432,
    "db_name": "brand_intelligence",
    "user": "insightiq",
    "password": "insightiq"
  },
  "brand_id": "nike_us",
  "platform": "facebook",
  "payload": {
    "id": "12345",
    "name": "Nike",
    "posts": { "data": [] }
  }
}
```

### C. Fetch Insights
Query the business tables.

**POST** `/serve/fetch`
**Body**:
```json
{
  "db_config": {
    "host": "tenant_db",
    "port": 5432,
    "db_name": "brand_intelligence",
    "user": "insightiq",
    "password": "insightiq"
  },
  "brand_id": "nike_us"
}
```

## Security Note

In this stateless pattern, database credentials are sent in the request body. **YOU MUST USE HTTPS** in production to encrpyt this traffic. Do not expose this API directly to the public internet without an API Gateway or specific security measures.
