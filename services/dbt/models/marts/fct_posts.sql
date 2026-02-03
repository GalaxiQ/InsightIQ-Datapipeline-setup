{{ config(materialized='incremental', unique_key='post_id') }}

SELECT DISTINCT ON (post_id)
  post_id,
  account_id,
  message,
  reactions,
  comments,
  shares,
  created_time,
  last_updated
FROM {{ ref('stg_social_posts') }}
ORDER BY post_id, last_updated DESC
