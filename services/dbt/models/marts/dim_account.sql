SELECT
  raw_json->>'id' AS account_id,
  p->>'id' AS post_id,

  p->>'message' AS message,
  (p->'reactions'->'summary'->>'total_count')::int AS reactions,
  (p->'comments'->'summary'->>'total_count')::int AS comments,
  (p->'shares'->>'count')::int AS shares,

  (p->>'created_time')::timestamp AS created_time,
  ingested_at AS last_updated

FROM {{ source('raw', 'raw_events') }},
jsonb_array_elements(raw_json->'posts'->'data') p
WHERE domain = 'social'
