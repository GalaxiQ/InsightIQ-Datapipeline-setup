
WITH interactions AS (
    SELECT * FROM {{ ref('stg_social_interactions') }}
)

SELECT
    DATE(created_at) AS date,
    brand,
    platform,
    
    COUNT(CASE WHEN brand_mentioned THEN 1 END) AS brand_mentions,
    COUNT(CASE WHEN competitor_mentioned THEN 1 END) AS competitor_mentions,
    
    COUNT(*) AS total_mentions -- Total interactions considered as mentions/activity

FROM interactions
GROUP BY 1, 2, 3
