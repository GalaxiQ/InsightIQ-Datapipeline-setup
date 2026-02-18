
WITH posts AS (
    SELECT * FROM {{ ref('stg_social_posts') }}
)

SELECT
    DATE(created_at) AS date,
    brand,
    platform,
    
    SUM(impressions) AS impressions,
    SUM(reach) AS reach,
    
    SUM(likes + comments + shares) AS total_engagements,
    
    SUM(shares) AS shares,
    SUM(clicks) AS clicks,
    
    COUNT(post_id) AS post_count,
    now() AS last_updated
FROM posts
GROUP BY 1, 2, 3
