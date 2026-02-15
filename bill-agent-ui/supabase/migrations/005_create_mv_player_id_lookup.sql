-- Lightweight materialized view for fast player ID resolution.
-- Replaces real-time queries against the expensive vw_nfl_players_with_dynasty_ids
-- view which times out on batches >50 IDs due to two ROW_NUMBER() window functions
-- and a complex LEFT JOIN with string operations.
--
-- Refresh with: REFRESH MATERIALIZED VIEW CONCURRENTLY mv_player_id_lookup;
-- (requires direct DB connection with extended statement_timeout — takes ~80s)

DROP MATERIALIZED VIEW IF EXISTS mv_player_id_lookup;

CREATE MATERIALIZED VIEW mv_player_id_lookup AS
SELECT
    d.sleeper_id,
    px.display_name,
    px.latest_team,
    px.position
FROM (
    SELECT p.*,
           ROW_NUMBER() OVER (
               PARTITION BY p.gsis_id
               ORDER BY
                   CASE WHEN COALESCE(p.ngs_status_short_description, '')::text ~~* 'Active' THEN 1 ELSE 0 END DESC,
                   COALESCE(p.last_season, 0::numeric) DESC
           ) AS rn
    FROM nflreadr_nfl_players p
) px
JOIN (
    SELECT d1.sleeper_id, d1.gsis_id, d1.merge_name, d1.draft_year, d1.draft_pick,
           ROW_NUMBER() OVER (
               PARTITION BY COALESCE(NULLIF(TRIM(d1.gsis_id), '^'), lower(TRIM(d1.merge_name)))
               ORDER BY COALESCE(d1.db_season, 0::numeric) DESC
           ) AS rn
    FROM dynastyprocess_playerids d1
    WHERE (NULLIF(TRIM(d1.gsis_id), '^') IS NOT NULL OR lower(TRIM(d1.merge_name)) IS NOT NULL)
      AND d1.sleeper_id IS NOT NULL
      AND d1.sleeper_id > 0
) d ON d.rn = 1 AND (
    (NULLIF(TRIM(px.gsis_id), '^') IS NOT NULL AND NULLIF(TRIM(d.gsis_id), '^') IS NOT NULL AND px.gsis_id::text = d.gsis_id::text)
    OR (NULLIF(TRIM(d.gsis_id), '^') IS NULL AND lower(TRIM(d.merge_name)) = lower(TRIM(px.display_name))
        AND COALESCE(d.draft_year::integer, 0) = COALESCE(px.draft_year::integer, 0)
        AND COALESCE(d.draft_pick::integer, 0) = COALESCE(px.draft_pick::integer, 0))
)
WHERE px.rn = 1
WITH NO DATA;

-- Unique index on sleeper_id for fast IN() lookups
CREATE UNIQUE INDEX idx_mv_player_id_lookup_sleeper_id
    ON mv_player_id_lookup (sleeper_id);

-- Grant read access through the API
GRANT SELECT ON mv_player_id_lookup TO anon, authenticated, service_role;

-- NOTE: After applying this migration, populate the view via direct DB connection:
--   psql $DATABASE_URL -c "SET statement_timeout = '120s'; REFRESH MATERIALIZED VIEW mv_player_id_lookup;"
