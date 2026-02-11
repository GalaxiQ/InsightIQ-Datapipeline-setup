
WITH metrics AS (
    SELECT * FROM {{ ref('int_daily_post_metrics') }}
)

SELECT
    date,
    brand,
    platform,
    
    CASE 
        WHEN impressions > 0 
        THEN (total_engagements::float / impressions)
        ELSE 0 
    END AS engagement_rate,
    
    CASE 
        WHEN post_count > 0 
        THEN (total_engagements::float / post_count)
        ELSE 0 
    END AS content_interaction_rate,
    
    CASE 
        WHEN impressions > 0 
        THEN (shares::float / impressions)
        ELSE 0 
    END AS virality_rate,
    
    CASE 
        WHEN impressions > 0 
        THEN (clicks::float / impressions)
        ELSE 0 
    END AS ctr

FROM metrics
