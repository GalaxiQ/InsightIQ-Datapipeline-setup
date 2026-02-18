
WITH response_metrics AS (
    SELECT * FROM {{ ref('int_response_metrics') }}
),

-- Re-using sentiment/interaction join logic for advocacy (simplified)
interactions AS (
    SELECT * FROM {{ ref('stg_social_interactions') }}
),

sentiment AS (
    SELECT * FROM {{ source('raw', 'sentiment_results') }}
),

advocacy_data AS (
    SELECT
        DATE(i.created_at) AS date,
        i.brand,
        i.platform,
        COUNT(*) AS total_ugc,
        SUM(CASE WHEN s.sentiment = 'positive' THEN 1 ELSE 0 END) AS positive_ugc
    FROM interactions i
    JOIN sentiment s ON i.interaction_id = s.interaction_id
    WHERE NOT i.is_brand_reply -- Only count user generated content
    GROUP BY 1, 2, 3
)

SELECT
    COALESCE(r.date, a.date) AS date,
    COALESCE(r.brand, a.brand) AS brand,
    COALESCE(r.platform, a.platform) AS platform,
    
    CASE 
        WHEN r.total_user_comments > 0 
        THEN (r.brand_replies::float / r.total_user_comments)
        ELSE 0 
    END AS response_rate,
    
    r.avg_response_time_minutes AS avg_response_time,
    
    CASE 
        WHEN a.total_ugc > 0 
        THEN (a.positive_ugc::float / a.total_ugc)
        ELSE 0 
    END AS advocacy_rate,
    
    0.0 AS repeat_advocate_ratio, -- Placeholder complexity
    now() AS last_updated

FROM response_metrics r
FULL OUTER JOIN advocacy_data a 
    ON r.date = a.date AND r.brand = a.brand AND r.platform = a.platform
