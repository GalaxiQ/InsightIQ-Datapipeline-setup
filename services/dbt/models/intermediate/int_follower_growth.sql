
WITH snapshot AS (
    SELECT * FROM {{ ref('stg_account_daily_snapshot') }}
),

lagged AS (
    SELECT
        date,
        brand,
        platform,
        follower_count,
        LAG(follower_count) OVER (PARTITION BY brand, platform ORDER BY date) AS previous_follower_count
    FROM snapshot
)

SELECT
    date,
    brand,
    platform,
    follower_count,
    previous_follower_count,
    CASE 
        WHEN previous_follower_count > 0 
        THEN ((follower_count - previous_follower_count)::float / previous_follower_count)
        ELSE 0 
    END AS follower_growth_rate,
    now() AS last_updated
FROM lagged
