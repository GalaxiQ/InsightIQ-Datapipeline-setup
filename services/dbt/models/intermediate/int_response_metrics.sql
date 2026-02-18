
WITH interactions AS (
    SELECT * FROM {{ ref('stg_social_interactions') }}
),

daily_comments AS (
    SELECT
        DATE(created_at) AS date,
        brand,
        platform,
        COUNT(*) AS total_user_comments
    FROM interactions
    WHERE NOT is_brand_reply
    GROUP BY 1, 2, 3
),

daily_replies AS (
    SELECT
        DATE(created_at) AS date,
        brand,
        platform,
        COUNT(*) AS brand_replies
    FROM interactions
    WHERE is_brand_reply
    GROUP BY 1, 2, 3
),

response_times AS (
    SELECT
        r.brand,
        r.platform,
        c.created_at AS comment_time,
        EXTRACT(EPOCH FROM (r.created_at - c.created_at))/60 AS response_time_minutes
    FROM interactions r
    JOIN interactions c ON r.parent_interaction_id = c.interaction_id
    WHERE r.is_brand_reply AND NOT c.is_brand_reply
),

daily_avg_response AS (
    SELECT
        DATE(comment_time) AS date,
        brand,
        platform,
        AVG(response_time_minutes) AS avg_response_time_minutes
    FROM response_times
    GROUP BY 1, 2, 3
)

SELECT
    COALESCE(c.date, r.date, a.date) AS date,
    COALESCE(c.brand, r.brand, a.brand) AS brand,
    COALESCE(c.platform, r.platform, a.platform) AS platform,
    
    COALESCE(c.total_user_comments, 0) AS total_user_comments,
    COALESCE(r.brand_replies, 0) AS brand_replies,
    COALESCE(a.avg_response_time_minutes, 0) AS avg_response_time_minutes,
    now() AS last_updated
FROM daily_comments c
FULL OUTER JOIN daily_replies r 
    ON c.date = r.date AND c.brand = r.brand AND c.platform = r.platform
FULL OUTER JOIN daily_avg_response a
    ON c.date = a.date AND c.brand = a.brand AND c.platform = a.platform
