
WITH interactions AS (
    SELECT * FROM {{ ref('stg_social_interactions') }}
),

sentiment AS (
    SELECT * FROM {{ source('raw', 'sentiment_results') }}
),

joined AS (
    SELECT
        i.created_at,
        i.brand,
        i.platform,
        s.sentiment,
        s.emotion,
        s.confidence
    FROM interactions i
    JOIN sentiment s ON i.interaction_id = s.interaction_id
),

aggregated AS (
    SELECT
        DATE(created_at) AS date,
        brand,
        platform,
        
        COUNT(*) AS total_sentiment_records,
        SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) AS positive_count,
        SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) AS negative_count,
        SUM(CASE WHEN emotion = 'trust' THEN 1 ELSE 0 END) AS trust_count,
        SUM(CASE WHEN emotion = 'excitement' THEN 1 ELSE 0 END) AS excitement_count,
        
        -- Score: (Pos - Neg) / Total (Normalized -1 to 1)
        SUM(CASE 
            WHEN sentiment = 'positive' THEN 1 
            WHEN sentiment = 'negative' THEN -1 
            ELSE 0 
        END) AS sentiment_sum

    FROM joined
    GROUP BY 1, 2, 3
)

SELECT
    date,
    brand,
    platform,
    
    CASE 
        WHEN total_sentiment_records > 0 
        THEN (sentiment_sum::float / total_sentiment_records)
        ELSE 0 
    END AS sentiment_score,
    
    CASE 
        WHEN total_sentiment_records > 0 
        THEN (positive_count::float / total_sentiment_records)
        ELSE 0 
    END AS positive_ratio,
    
    CASE 
        WHEN total_sentiment_records > 0 
        THEN (negative_count::float / total_sentiment_records)
        ELSE 0 
    END AS negative_ratio,
    
    CASE 
        WHEN total_sentiment_records > 0 
        THEN (trust_count::float / total_sentiment_records)
        ELSE 0 
    END AS trust_emotion_ratio,
    
    CASE 
        WHEN total_sentiment_records > 0 
        THEN (excitement_count::float / total_sentiment_records)
        ELSE 0 
    END AS excitement_ratio

FROM aggregated
