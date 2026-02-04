{{ config(materialized='incremental', unique_key='account_id') }}

SELECT DISTINCT ON (account_id)
  account_id,
  brand_id,
  platform,
  name,
  username,
  category,
  followers,
  website,
  rating,
  last_updated
FROM {{ ref('stg_social_accounts') }}
ORDER BY account_id, last_updated DESC
