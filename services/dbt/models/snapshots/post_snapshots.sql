SELECT
  post_id,
  reactions,
  comments,
  shares,
  last_updated AS snapshot_time
FROM {{ ref('stg_social_posts') }}
