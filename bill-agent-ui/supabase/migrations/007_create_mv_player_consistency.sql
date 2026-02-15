-- Materialized view for player weekly fantasy point consistency metrics.
-- Computes avg, stddev, floor (P10), ceiling (P90), boom/bust counts, and
-- consistency coefficient (stddev/mean) from weekly player stats.
--
-- Sources from nflreadr_nfl_player_stats_week which has pre-computed
-- fantasy_points_ppr plus all counting stats for all positions in one table.
-- Joins to nflreadr_nfl_ff_playerids (via LATERAL LIMIT 1 to avoid fanout
-- from duplicate gsis_id entries) to add merge_name for fuzzy name matching.
--
-- Used by:
--   get_player_consistency() in tools/metrics/info.py (consistency analysis)
--   compare_players() enrichment (player comparison with consistency context)
--
-- Refresh with: REFRESH MATERIALIZED VIEW CONCURRENTLY mv_player_consistency;
-- (requires direct DB connection with extended statement_timeout — takes ~30-60s)
-- Scheduled via pg_cron: weekly on Tuesday at 7 AM UTC (after weekly data loads)

DROP MATERIALIZED VIEW IF EXISTS mv_player_consistency;

CREATE MATERIALIZED VIEW mv_player_consistency AS
WITH weekly_stats AS (
    SELECT
        psw.season,
        psw.player_name,
        psw.player_id,
        psw.position AS ff_position,
        psw.team AS ff_team,
        psw.week,
        psw.fantasy_points_ppr
    FROM nflreadr_nfl_player_stats_week psw
    WHERE psw.season_type = 'REG'
      AND psw.week <= 18
      AND psw.player_name IS NOT NULL
      AND psw.position IN ('QB', 'RB', 'WR', 'TE')
      AND psw.fantasy_points_ppr IS NOT NULL
),
aggregated AS (
    SELECT
        season,
        player_name,
        (ARRAY_AGG(DISTINCT player_id))[1] AS player_id,
        ff_position,
        ff_team,
        COUNT(DISTINCT week) AS games_played,
        AVG(fantasy_points_ppr) AS avg_fp,
        STDDEV_POP(fantasy_points_ppr) AS stddev_fp,
        PERCENTILE_CONT(0.10) WITHIN GROUP (ORDER BY fantasy_points_ppr) AS floor_p10,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY fantasy_points_ppr) AS median_fp,
        PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY fantasy_points_ppr) AS ceiling_p90,
        COUNT(*) FILTER (WHERE fantasy_points_ppr >= 20) AS boom_games_20plus,
        COUNT(*) FILTER (WHERE fantasy_points_ppr < 5) AS bust_games_under_5
    FROM weekly_stats
    GROUP BY season, player_name, ff_position, ff_team
    HAVING COUNT(DISTINCT week) >= 4  -- Minimum 4 games for meaningful consistency metrics
)
SELECT
    agg.season,
    agg.player_name,
    pid.merge_name,
    agg.ff_position,
    agg.ff_team,
    agg.games_played,
    ROUND(agg.avg_fp::numeric, 2) AS avg_fp_ppr,
    ROUND(agg.stddev_fp::numeric, 2) AS fp_stddev_ppr,
    ROUND(agg.floor_p10::numeric, 2) AS fp_floor_p10,
    ROUND(agg.ceiling_p90::numeric, 2) AS fp_ceiling_p90,
    ROUND(agg.median_fp::numeric, 2) AS fp_median_ppr,
    agg.boom_games_20plus,
    agg.bust_games_under_5,
    -- Consistency coefficient: stddev / mean (lower = more consistent)
    CASE
        WHEN agg.avg_fp > 0 THEN
            ROUND((agg.stddev_fp / agg.avg_fp)::numeric, 3)
        ELSE NULL
    END AS consistency_coefficient
FROM aggregated agg
LEFT JOIN LATERAL (
    SELECT p.merge_name
    FROM nflreadr_nfl_ff_playerids p
    WHERE p.gsis_id::text = agg.player_id::text
    LIMIT 1
) pid ON true
WITH NO DATA;

-- Unique index required for REFRESH MATERIALIZED VIEW CONCURRENTLY
-- Includes ff_position + ff_team because traded players or same-name players
-- (e.g., A.Mitchell on different teams) produce multiple rows per (player_name, season)
CREATE UNIQUE INDEX idx_mv_player_consistency_player_season
    ON mv_player_consistency (player_name, season, ff_position, ff_team);

-- Index for position + season queries
CREATE INDEX idx_mv_player_consistency_position_season
    ON mv_player_consistency (ff_position, season);

-- Grant read access through the API
GRANT SELECT ON mv_player_consistency TO anon, authenticated, service_role;

-- NOTE: After applying this migration, populate the view via direct DB connection:
--   psql $DATABASE_URL -c "SET statement_timeout = '120s'; REFRESH MATERIALIZED VIEW mv_player_consistency;"
--
-- pg_cron job refreshes weekly on Tuesday at 7 AM UTC (after weekly data loads):
--   SELECT cron.schedule('refresh-mv-player-consistency', '0 7 * * 2',
--     $$SET statement_timeout = '120s'; REFRESH MATERIALIZED VIEW CONCURRENTLY mv_player_consistency;$$);
