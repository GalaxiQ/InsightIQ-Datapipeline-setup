{{
    config(
        materialized='incremental',
        unique_key='post_id'
    )
}}

WITH source AS (
    SELECT * FROM {{ source('raw', 'raw_social_posts') }}
    {% if is_incremental() %}
    -- Only process new rows since the last run
    WHERE fetched_at > (SELECT MAX(last_updated) FROM {{ this }})
    {% endif %}
),

deduplicated AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (
            PARTITION BY raw_json->>'post_id' 
            ORDER BY fetched_at DESC
        ) as row_num
    FROM source
)

SELECT
    COALESCE(raw_json->>'post_id', raw_json->>'id') AS post_id,
    platform,
    brand,
    
    -- Account ID extraction
    COALESCE(
        raw_json->'owner'->>'id', 
        raw_json->>'author_id', 
        raw_json->>'author'
    ) AS account_id,

    COALESCE(
        raw_json->>'created_at',
        raw_json->>'timestamp'
    )::timestamp AS created_at,
    COALESCE(
        raw_json->>'created_at',
        raw_json->>'timestamp'
    )::timestamp AS created_time, -- for fct_posts
    
    -- Metrics (default to 0 if null)
    COALESCE((raw_json->'metrics'->>'likes')::int, 0) AS reactions, -- for fct_posts
    COALESCE((raw_json->'metrics'->>'likes')::int, 0) AS likes, -- for intermediate models
    
    COALESCE((raw_json->'metrics'->>'comments')::int, 0) AS comments,
    COALESCE((raw_json->'metrics'->>'shares')::int, 0) AS shares,
    COALESCE((raw_json->'metrics'->>'impressions')::int, 0) AS impressions,
    COALESCE((raw_json->'metrics'->>'reach')::int, 0) AS reach,
    COALESCE((raw_json->'metrics'->>'clicks')::int, 0) AS clicks,
    
    -- Specific Twitter/LinkedIn metrics
    COALESCE((raw_json->'metrics'->>'retweet_count')::int, 0) AS retweet_count,
    
    raw_json->>'text' AS message,
    TRUE AS is_brand_post,
    fetched_at AS last_updated

FROM deduplicated
WHERE row_num = 1
