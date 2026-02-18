/* ============================================================
   EXTENSIONS
   ============================================================ */

CREATE EXTENSION IF NOT EXISTS vector;



/* ============================================================
   RAW DATA CAPTURE TABLES (SOURCE OF TRUTH)
   RULES:
   - Store exact API payload
   - No transformations
   - No KPIs
   - JSONB is canonical
   ============================================================ */


/* ------------------------------------------------------------
   A. BRAND-OWNED SOCIAL POSTS
   ------------------------------------------------------------ */

CREATE TABLE IF NOT EXISTS raw_social_posts (
    id BIGSERIAL PRIMARY KEY,
    platform TEXT NOT NULL,              -- instagram | twitter | linkedin
    brand TEXT NOT NULL,
    fetched_at TIMESTAMP NOT NULL DEFAULT now(),
    raw_json JSONB NOT NULL
);

-- Indexes (retrieval + joins only)
CREATE INDEX IF NOT EXISTS idx_rsp_platform
    ON raw_social_posts(platform);

CREATE INDEX IF NOT EXISTS idx_rsp_brand
    ON raw_social_posts(brand);

CREATE INDEX IF NOT EXISTS idx_rsp_post_id
    ON raw_social_posts ((raw_json->>'post_id'));

CREATE INDEX IF NOT EXISTS idx_rsp_created_time
    ON raw_social_posts ((raw_json->>'created_time'));



/* ------------------------------------------------------------
   B. SOCIAL INTERACTIONS / UGC
   ------------------------------------------------------------ */

CREATE TABLE IF NOT EXISTS raw_social_interactions (
    id BIGSERIAL PRIMARY KEY,
    platform TEXT NOT NULL,
    fetched_at TIMESTAMP NOT NULL DEFAULT now(),
    raw_json JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_rsi_platform
    ON raw_social_interactions(platform);

CREATE INDEX IF NOT EXISTS idx_rsi_post_id
    ON raw_social_interactions ((raw_json->>'post_id'));

CREATE INDEX IF NOT EXISTS idx_rsi_interaction_id
    ON raw_social_interactions ((raw_json->>'interaction_id'));



/* ------------------------------------------------------------
   C. ACCOUNT-LEVEL METRICS
   ------------------------------------------------------------ */

CREATE TABLE IF NOT EXISTS raw_account_metrics (
    id BIGSERIAL PRIMARY KEY,
    platform TEXT NOT NULL,
    brand TEXT NOT NULL,
    fetched_at TIMESTAMP NOT NULL DEFAULT now(),
    raw_json JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ram_platform
    ON raw_account_metrics(platform);

CREATE INDEX IF NOT EXISTS idx_ram_brand
    ON raw_account_metrics(brand);



/* ============================================================
   UNIVERSAL RAW EVENT STORE (NON-SOCIAL ONLY)
   NOTE:
   - Keep for web | crm | ads
   - DO NOT store social here
   ============================================================ */

CREATE TABLE IF NOT EXISTS raw_events (
    event_id BIGSERIAL PRIMARY KEY,
    brand_id TEXT NOT NULL,
    domain TEXT NOT NULL,         -- web | crm | ads
    platform TEXT,
    raw_json JSONB NOT NULL,
    schema_version TEXT DEFAULT 'v1',
    payload_hash TEXT,
    ingested_at TIMESTAMP DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_raw_events_brand
    ON raw_events(brand_id);

CREATE INDEX IF NOT EXISTS idx_raw_events_domain
    ON raw_events(domain);



/* ============================================================
   MODELED / DERIVED TABLES
   (POPULATED FROM RAW TABLES ONLY)
   ============================================================ */


/* ------------------------------------------------------------
   ACCOUNT DIMENSION
   ------------------------------------------------------------ */

CREATE TABLE IF NOT EXISTS dim_account (
    account_id TEXT PRIMARY KEY,
    brand_id TEXT,
    platform TEXT,
    name TEXT,
    username TEXT,
    category TEXT,
    followers INT,
    website TEXT,
    rating FLOAT,
    last_updated TIMESTAMP
);



/* ------------------------------------------------------------
   POSTS FACT TABLE (LATEST STATE)
   ------------------------------------------------------------ */

CREATE TABLE IF NOT EXISTS fct_posts (
    post_id TEXT PRIMARY KEY,
    account_id TEXT,
    message TEXT,
    reactions INT,
    comments INT,
    shares INT,
    created_time TIMESTAMP,
    last_updated TIMESTAMP
);



/* ------------------------------------------------------------
   POST SNAPSHOTS (HISTORICAL METRICS)
   ------------------------------------------------------------ */

CREATE TABLE IF NOT EXISTS post_snapshots (
    post_id TEXT,
    reactions INT,
    comments INT,
    shares INT,
    snapshot_time TIMESTAMP DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_post_snapshots_post_id
    ON post_snapshots(post_id);



/* ============================================================
   ALERTING
   ============================================================ */

-- CREATE TABLE IF NOT EXISTS alert_rules (
--     brand_id TEXT,
--     metric TEXT,
--     threshold FLOAT,
--     direction TEXT,     -- above | below
--     channel TEXT        -- slack | email | webhook
-- );



/* ============================================================
   ML / VECTOR LAYER
   ============================================================ */

CREATE TABLE IF NOT EXISTS post_embeddings (
    post_id TEXT PRIMARY KEY,
    embedding VECTOR(3072),
    payload JSONB,
    created_at TIMESTAMP DEFAULT now()
);



/* ============================================================
   LLM / ANALYSIS OUTPUT
   (DERIVED — NOT RAW)
   ============================================================ */

CREATE TABLE IF NOT EXISTS sentiment_results (
    interaction_id TEXT PRIMARY KEY,
    sentiment TEXT NOT NULL,       -- positive | neutral | negative
    emotion TEXT,                  -- trust | excitement | frustration | etc
    confidence FLOAT,
    model_version TEXT,
    processed_at TIMESTAMP DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_sentiment_results_sentiment
    ON sentiment_results(sentiment);


/* ============================================================
   SUMMARY LOGGING / CHECKPOINTING
   ============================================================ */

CREATE TABLE IF NOT EXISTS summary_checkpoint (
    id SERIAL PRIMARY KEY,
    last_summarized_at TIMESTAMP NOT NULL,
    summary_type TEXT NOT NULL,       -- global_daily | platform_specific
    metadata JSONB
);

CREATE INDEX IF NOT EXISTS idx_summary_checkpoint_time
    ON summary_checkpoint(last_summarized_at);


-- CREATE INDEX IF NOT EXISTS idx_rao_brand
--     ON raw_analysis_output(brand_id);

-- CREATE INDEX IF NOT EXISTS idx_rao_domain
--     ON raw_analysis_output(domain);
