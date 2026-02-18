# InsightIQ API Documentation

Multi-tenant ingestion, analytics, and serving platform for brand intelligence.

## Production Readiness Features
- **CORS Support**: Configured for cross-origin requests.
- **Global Error Handling**: Centralized exception management with JSON responses.
- **Structured Logging**: Consistent log formatting across all services.
- **Database Connection Pooling**: Optimized for high-concurrency remote PostgreSQL access.
- **Stateless Architecture**: Tenant configuration is resolved dynamically via schema isolation.

## API Endpoints

### 1. Health Check
Checks if the API service is running.

- **URL**: `/health`
- **Method**: `GET`
- **Response**: `200 OK`
  ```json
  { "status": "ok" }
  ```

### 2. Bootstrap Schema
Initializes the SQL schema for a specific tenant. It verifies if the schema exists on the remote database before applying migrations.

- **URL**: `/schema/bootstrap`
- **Method**: `POST`
- **Payload**:
  ```json
  {
    "tenant_id": "org_423b3ac30b46426db809c4196f7d358a"
  }
  ```
- **Alternate Headers**: `x-tenant-id: org_...` (can be used instead of body)
- **Response**: `200 OK`
  ```json
  {
    "status": "schema ready",
    "tenant_id": "org_...",
    "schema": "org_..."
  }
  ```

### 3. Ingest Data
Ingests raw event data into the tenant-specific `raw_events` table.

- **URL**: `/ingest/{domain}`
  - `domain`: `social` | `web` | `crm` | `ads`
- **Method**: `POST`
- **Headers**:
  - `x-tenant-id`: string (Required)
- **Payload**:
  ```json
  {
    "brand_id": "InsightIQ_Demo",
    "platform": "instagram",
    "payload": { "post_id": "123", "text": "Example content", "metrics": { "likes": 50 } },
    "schema_version": "v1"
  }
  ```
- **Response**: `200 OK`
  ```json
  { "status": "ingested" }
  ```

### 4. Analyze & Summarize
Triggers LLM-based sentiment analysis and summarization for social media content. Stores results in `post_embeddings` and `sentiment_results`.

- **URL**: `/analysis/summarize`
- **Method**: `POST`
- **Headers**:
  - `x-tenant-id`: string (Required)
- **Payload**:
  ```json
  {
    "payload": { "any": "json_content_to_analyze" }
  }
  ```
- **Response**: `200 OK`
  ```json
  {
    "status": "ok",
    "post_id": "uuid-...",
    "created_at": "2024-02-18T..."
  }
  ```

### 5. Transform Data (DBT)
Triggers the DBT build process to transform raw data into optimized analytics marts for a specific tenant.

- **URL**: `/transform/run`
- **Method**: `POST`
- **Payload**:
  ```json
  {
    "tenant_id": "org_...",
    "full_refresh": false
  }
  ```
- **Response**: `200 OK`
  ```json
  {
    "status": "ok",
    "tenant_id": "org_...",
    "schema": "org_...",
    "full_refresh": false,
    "dbt_output_tail": "...dbt build log..."
  }
  ```

### 6. Serving (Fetch Brand Accounts)
Fetches aggregated account metrics for a specific brand from the `dim_account` table.

- **URL**: `/serve/brands/{brand_id}/accounts`
- **Method**: `GET`
- **Headers**:
  - `x-tenant-id`: string (Required)
- **Response**: `200 OK`
  ```json
  [
    {
      "name": "InsightIQ_Demo Instagram Account",
      "followers": 1500,
      "rating": 4.5,
      "last_updated": "2024-02-18T..."
    }
  ]
  ```

## Configuration
The API relies on environment variables or a `.env` file:
- `MASTER_DB_URL`: Connection string for the remote PostgreSQL.
- `AZURE_OPENAI_API_KEY`: Key for Azure OpenAI services.
- `AZURE_OPENAI_ENDPOINT`: Endpoint for Azure OpenAI.
- `DBT_BIN`: Path to the dbt executable.
- `DBT_PROJECT_DIR`: Path to the dbt project directory.
