-- Materialized view for player weekly fantasy point consistency metrics.
-- Computes avg, stddev, floor (P10), ceiling (P90), boom/bust counts, and
-- consistency coefficient (stddev/mean) from weekly advanced stats views.
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
WITH weekly_receiving AS (
    SELECT
        season,
        player_name,
        ff_position,
        ff_team,
        week,
        COALESCE(
            fantasy_points_ppr,
            (receptions * 1.0) +
            (receiving_yards / 10.0) +
            (receiving_tds * 6.0)
        ) AS fantasy_points_ppr
    FROM vw_advanced_receiving_analytics_weekly
    WHERE week <= 18
      AND player_name IS NOT NULL
),
weekly_passing AS (
    SELECT
        season,
        player_name,
        position AS ff_position,
        team AS ff_team,
        week,
        COALESCE(
            fantasy_points,
            (passing_yards / 25.0) +
            (passing_tds * 4.0) -
            (COALESCE(interceptions, 0) * 2.0)
        ) AS fantasy_points_ppr
    FROM vw_advanced_passing_analytics_weekly
    WHERE week <= 18
      AND player_name IS NOT NULL
),
weekly_rushing AS (
    SELECT
        season,
        player_name,
        position AS ff_position,
        team AS ff_team,
        week,
        COALESCE(
            fantasy_points_ppr,
            (rushing_yards / 10.0) +
            (rushing_tds * 6.0) +
            (COALESCE(receptions, 0) * 1.0) +
            (COALESCE(receiving_yards, 0) / 10.0) +
            (COALESCE(receiving_tds, 0) * 6.0)
        ) AS fantasy_points_ppr
    FROM vw_advanced_rushing_analytics_weekly
    WHERE week <= 18
      AND player_name IS NOT NULL
),
combined_weekly AS (
    SELECT * FROM weekly_receiving
    UNION ALL
    SELECT * FROM weekly_passing
    UNION ALL
    SELECT * FROM weekly_rushing
),
aggregated AS (
    SELECT
        season,
        player_name,
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
    FROM combined_weekly
    GROUP BY season, player_name, ff_position, ff_team
    HAVING COUNT(DISTINCT week) >= 4  -- Minimum 4 games for meaningful consistency metrics
)
SELECT
    season,
    player_name,
    ff_position,
    ff_team,
    games_played,
    ROUND(avg_fp::numeric, 2) AS avg_fp_ppr,
    ROUND(stddev_fp::numeric, 2) AS fp_stddev_ppr,
    ROUND(floor_p10::numeric, 2) AS fp_floor_p10,
    ROUND(ceiling_p90::numeric, 2) AS fp_ceiling_p90,
    ROUND(median_fp::numeric, 2) AS fp_median_ppr,
    boom_games_20plus,
    bust_games_under_5,
    -- Consistency coefficient: stddev / mean (lower = more consistent)
    CASE
        WHEN avg_fp > 0 THEN
            ROUND((stddev_fp / avg_fp)::numeric, 3)
        ELSE NULL
    END AS consistency_coefficient
FROM aggregated
WITH NO DATA;

-- Unique index required for REFRESH MATERIALIZED VIEW CONCURRENTLY
CREATE UNIQUE INDEX idx_mv_player_consistency_player_season
    ON mv_player_consistency (player_name, season);

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
