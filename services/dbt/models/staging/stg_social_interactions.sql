{{
    config(
        materialized='incremental',
        unique_key='interaction_id'
    )
}}

WITH source AS (
    SELECT * FROM {{ source('raw', 'raw_social_interactions') }}
    {% if is_incremental() %}
    WHERE fetched_at > (SELECT MAX(last_updated) FROM {{ this }})
    {% endif %}
),

deduplicated AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (
            PARTITION BY raw_json->>'interaction_id' 
            ORDER BY fetched_at DESC
        ) as row_num
    FROM source
)

SELECT
    COALESCE(raw_json->>'interaction_id', raw_json->>'id') AS interaction_id,
    COALESCE(
        raw_json->>'post_id', 
        raw_json->>'conversation_id', 
        raw_json->>'object'
    ) AS post_id,
    platform,
    
    -- "brand" is optional in interactions, extraction fallback
    COALESCE(raw_json->>'brand', 'unknown') AS brand,
    
    COALESCE(raw_json->>'user_id', raw_json->>'author_id', raw_json->>'actor') AS user_id,
    COALESCE(raw_json->>'text', raw_json->>'message') AS text,
    (raw_json->>'created_at')::timestamp AS created_at,
    
    -- Booleans (defaulting to null if missing is safer for staging)
    (raw_json->>'is_brand_reply')::boolean AS is_brand_reply,
    COALESCE(raw_json->>'parent_interaction_id', raw_json->>'in_reply_to_user_id') AS parent_interaction_id,
    
    (raw_json->>'brand_mentioned')::boolean AS brand_mentioned,
    (raw_json->>'competitor_mentioned')::boolean AS competitor_mentioned,
    (raw_json->>'in_reply_to_brand_post')::boolean AS in_reply_to_brand_post,
    
    (raw_json->>'user_follower_count')::int AS user_follower_count,
    fetched_at AS last_updated

FROM deduplicated
WHERE row_num = 1
