{{ config(materialized='incremental', unique_key='account_id') }}

SELECT
  raw_json->>'id' AS account_id,
  brand_id,
  platform,

  raw_json->>'name' AS name,
  raw_json->>'username' AS username,
  raw_json->>'category' AS category,
  (raw_json->>'followers_count')::int AS followers,
  raw_json->>'website' AS website,
  (raw_json->>'overall_star_rating')::float AS rating,

  ingested_at AS last_updated
FROM {{ source('raw', 'raw_events') }}
WHERE domain = 'social'

{% if is_incremental() %}
AND ingested_at > (SELECT max(last_updated) FROM {{ this }})
{% endif %}
