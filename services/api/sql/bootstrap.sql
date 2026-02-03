-- RAW EVENT STORE (Universal)
CREATE TABLE IF NOT EXISTS raw_events (
    event_id BIGSERIAL PRIMARY KEY,
    brand_id TEXT NOT NULL,
    domain TEXT NOT NULL,         -- social | web | crm | ads
    platform TEXT,
    raw_json JSONB NOT NULL,
    schema_version TEXT DEFAULT 'v1',
    payload_hash TEXT,
    ingested_at TIMESTAMP DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_raw_brand ON raw_events(brand_id);
CREATE INDEX IF NOT EXISTS idx_raw_domain ON raw_events(domain);
CREATE INDEX IF NOT EXISTS idx_raw_post_id
ON raw_events ((raw_json->>'id'));

-- ACCOUNT STATE
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

-- POST STATE
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

-- POST SNAPSHOTS (History)
CREATE TABLE IF NOT EXISTS post_snapshots (
    post_id TEXT,
    reactions INT,
    comments INT,
    shares INT,
    snapshot_time TIMESTAMP DEFAULT now()
);

-- ALERT RULES
CREATE TABLE IF NOT EXISTS alert_rules (
    brand_id TEXT,
    metric TEXT,
    threshold FLOAT,
    direction TEXT,
    channel TEXT
);

-- VECTOR SUPPORT
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS post_embeddings (
    post_id TEXT PRIMARY KEY,
    embedding VECTOR(1536),
    payload JSONB,
    created_at TIMESTAMP DEFAULT now()
);
