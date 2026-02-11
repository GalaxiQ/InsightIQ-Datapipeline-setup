
WITH metrics AS (
    SELECT * FROM {{ ref('int_daily_post_metrics') }}
),

growth AS (
    SELECT * FROM {{ ref('int_follower_growth') }}
),

mentions AS (
    SELECT * FROM {{ ref('int_daily_mentions') }}
)

SELECT
    COALESCE(m.date, g.date, mn.date) AS date,
    COALESCE(m.brand, g.brand, mn.brand) AS brand,
    COALESCE(m.platform, g.platform, mn.platform) AS platform,
    
    COALESCE(m.impressions, 0) AS impressions,
    COALESCE(m.reach, 0) AS reach,
    COALESCE(g.follower_growth_rate, 0) AS follower_growth_rate,
    COALESCE(mn.brand_mentions, 0) AS brand_mention_volume,
    
    CASE 
        WHEN mn.total_mentions > 0 
        THEN (mn.brand_mentions::float / mn.total_mentions)
        ELSE 0 
    END AS share_of_voice

FROM metrics m
FULL OUTER JOIN growth g 
    ON m.date = g.date AND m.brand = g.brand AND m.platform = g.platform
FULL OUTER JOIN mentions mn 
    ON m.date = mn.date AND m.brand = mn.brand AND m.platform = mn.platform
