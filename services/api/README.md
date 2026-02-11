# InsightIQ API

Multi-tenant ingestion + analytics + serving platform.

## Endpoints

### 1. Register Tenant
Registers a new tenant with their database configuration.

- **URL**: `/tenant/register`
- **Method**: `POST`
- **Payload**:
  ```json
  {
    "org_name": "acme",
    "host": "localhost",
    "port": 5432,
    "db_name": "tenant_db",
    "user": "postgres",
    "password": "password"
  }
  ```
- **Response**:
  ```json
  {
    "tenant_id": "tenant-uuid-..."
  }
  ```

### 2. Bootstrap Schema
Initializes the schema for a specific tenant in their database.

- **URL**: `/schema/bootstrap`
- **Method**: `POST`
- **Headers**:
  - `x-tenant-id`: string (Optional if provided in body)
- **Payload**:
  ```json
  {
    "tenant_id": "tenant-uuid-..."
  }
  ```
- **Response**:
  ```json
  {
    "status": "schema ready",
    "tenant_id": "tenant-uuid-...",
    "schema": "tenant_acme_..."
  }
  ```

### 3. Ingest Data
Ingest raw data for a specific domain (social, web, crm, ads).

- **URL**: `/ingest/{domain}`
  - `domain`: `social` | `web` | `crm` | `ads`
- **Method**: `POST`
- **Headers**:
  - `x-tenant-id`: string (Required)
- **Payload**:
  ```json
  {
    "brand_id": "brand_123",
    "platform": "twitter",
    "payload": { "some": "raw_data" },
    "schema_version": "v1"
  }
  ```
- **Response**:
  ```json
  {
    "status": "ingested"
  }
  ```

### 4. Analyze & Summarize (Social Media)
Generates summaries and embeddings for social media content using LLM.
- **URL**: `/analysis/summarize`
- **Method**: `POST`
- **Headers**:
  - `x-tenant-id`: string (Required)
- **Payload**:
  ```json
  {
    "payload": { ...any json content... }
  }
  ```
- **Response**:
  ```json
  {
    "status": "ok",
    "post_id": "uuid...",
    "created_at": "2024-..."
  }
  ```

### 5. Transform Data (DBT)
Triggers DBT models for a tenant to transform raw data into analytics tables.

- **URL**: `/transform/run`
- **Method**: `POST`
- **Payload**:
  ```json
  {
    "tenant_id": "tenant-uuid-...",
    "full_refresh": false
  }
  ```
- **Response**:
  ```json
  {
    "status": "ok",
    "tenant_id": "tenant-uuid-...",
    "schema": "tenant_acme_...",
    "full_refresh": false,
    "dbt_output_tail": "..."
  }
  ```

### 6. Serving (Fetch Accounts)
Fetch account metrics for a brand.

- **URL**: `/serve/brands/{brand_id}/accounts`
- **Method**: `GET`
- **Headers**:
  - `x-tenant-id`: string (Required)
- **Response**:
  ```json
  [
    {
      "name": "Acme Corp",
      "followers": 1500,
      "rating": 4.5,
      "last_updated": "2023-..."
    }
  ]
  ```
