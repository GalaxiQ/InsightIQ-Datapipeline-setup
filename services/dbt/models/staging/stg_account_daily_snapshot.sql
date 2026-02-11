{{
    config(
        materialized='incremental',
        unique_key=['date', 'brand', 'platform']
    )
}}

WITH source AS (
    SELECT * FROM {{ source('raw', 'raw_account_metrics') }}
    {% if is_incremental() %}
    WHERE fetched_at > (SELECT MAX(last_updated) FROM {{ this }})
    {% endif %}
),

deduplicated AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (
            PARTITION BY (raw_json->>'date')::date, brand, platform 
            ORDER BY fetched_at DESC
        ) as row_num
    FROM source
)

SELECT
    (raw_json->>'date')::date AS date,
    platform,
    brand,
    COALESCE(
        (raw_json->>'follower_count')::int,
        (raw_json->>'followers_count')::int
    ) AS follower_count,
    fetched_at AS last_updated

FROM deduplicated
WHERE row_num = 1
