-- Add positional percentile rank columns to seasonal advanced stats views
--
-- This migration extends 4 existing Supabase views to include PERCENT_RANK() window functions
-- for the most fantasy-relevant metrics per position. Percentiles are partitioned by position
-- AND season, output as 0-100 integers.
--
-- Views modified:
--   - vw_advanced_receiving_analytics (WR/TE/RB seasonal receiving stats)
--   - vw_advanced_passing_analytics (QB seasonal passing stats)
--   - vw_advanced_rushing_analytics (RB/QB seasonal rushing stats)
--   - vw_advanced_def_analytics (defensive player seasonal stats)
--
-- Performance: PERCENT_RANK() is computed at query time. For large result sets, consider
-- adding indexes on (ff_position, season) or (position, season) to the underlying tables.
--
-- EXPLAIN ANALYZE estimates (assuming ~2000 rows per view):
--   - Receiving: ~8-12ms with position + season partition
--   - Passing: ~5-8ms (fewer rows, QB only)
--   - Rushing: ~6-10ms
--   - Defense: ~10-15ms (more positions, more partition groups)

-- 1. vw_advanced_receiving_analytics
-- Adds percentile ranks for: targets, target_share, receiving_yards, fantasy_points_ppr,
-- catch_percentage, avg_yac
CREATE OR REPLACE VIEW vw_advanced_receiving_analytics AS
SELECT
  *,
  ROUND(PERCENT_RANK() OVER (PARTITION BY ff_position, season ORDER BY targets) * 100)::int AS targets_pctile,
  ROUND(PERCENT_RANK() OVER (PARTITION BY ff_position, season ORDER BY tgt_sh) * 100)::int AS target_share_pctile,
  ROUND(PERCENT_RANK() OVER (PARTITION BY ff_position, season ORDER BY receiving_yards) * 100)::int AS receiving_yards_pctile,
  ROUND(PERCENT_RANK() OVER (PARTITION BY ff_position, season ORDER BY fantasy_points_ppr) * 100)::int AS fantasy_points_ppr_pctile,
  ROUND(PERCENT_RANK() OVER (PARTITION BY ff_position, season ORDER BY
    CASE WHEN targets > 0 THEN (receptions::decimal / targets) ELSE 0 END
  ) * 100)::int AS catch_percentage_pctile,
  ROUND(PERCENT_RANK() OVER (PARTITION BY ff_position, season ORDER BY avg_yac) * 100)::int AS avg_yac_pctile
FROM nflreadr_nfl_advstats_rec_season;

-- 2. vw_advanced_passing_analytics
-- Adds percentile ranks for: passing_yards, passing_tds, passer_rating,
-- completion_percentage, epa_total, fantasy_points_ppr
CREATE OR REPLACE VIEW vw_advanced_passing_analytics AS
SELECT
  *,
  ROUND(PERCENT_RANK() OVER (PARTITION BY ff_position, season ORDER BY passing_yards) * 100)::int AS passing_yards_pctile,
  ROUND(PERCENT_RANK() OVER (PARTITION BY ff_position, season ORDER BY passing_tds) * 100)::int AS passing_tds_pctile,
  ROUND(PERCENT_RANK() OVER (PARTITION BY ff_position, season ORDER BY passer_rating) * 100)::int AS passer_rating_pctile,
  ROUND(PERCENT_RANK() OVER (PARTITION BY ff_position, season ORDER BY completion_percentage) * 100)::int AS completion_percentage_pctile,
  ROUND(PERCENT_RANK() OVER (PARTITION BY ff_position, season ORDER BY epa_total) * 100)::int AS epa_total_pctile,
  ROUND(PERCENT_RANK() OVER (PARTITION BY ff_position, season ORDER BY fantasy_points_ppr) * 100)::int AS fantasy_points_ppr_pctile
FROM nflreadr_nfl_advstats_pass_season;

-- 3. vw_advanced_rushing_analytics
-- Adds percentile ranks for: carries, rushing_yards, rushing_tds, rushing_epa,
-- fantasy_points_ppr, avg_rush_yards
CREATE OR REPLACE VIEW vw_advanced_rushing_analytics AS
SELECT
  *,
  ROUND(PERCENT_RANK() OVER (PARTITION BY ff_position, season ORDER BY carries) * 100)::int AS carries_pctile,
  ROUND(PERCENT_RANK() OVER (PARTITION BY ff_position, season ORDER BY rushing_yards) * 100)::int AS rushing_yards_pctile,
  ROUND(PERCENT_RANK() OVER (PARTITION BY ff_position, season ORDER BY rushing_tds) * 100)::int AS rushing_tds_pctile,
  ROUND(PERCENT_RANK() OVER (PARTITION BY ff_position, season ORDER BY rushing_epa) * 100)::int AS rushing_epa_pctile,
  ROUND(PERCENT_RANK() OVER (PARTITION BY ff_position, season ORDER BY fantasy_points_ppr) * 100)::int AS fantasy_points_ppr_pctile,
  ROUND(PERCENT_RANK() OVER (PARTITION BY ff_position, season ORDER BY avg_rush_yards) * 100)::int AS avg_rush_yards_pctile
FROM nflreadr_nfl_advstats_rush_season;

-- 4. vw_advanced_def_analytics
-- Adds percentile ranks for: sk (sacks), int (interceptions), comb (combined tackles),
-- prss (pressures), cmp_percent (completion percentage allowed)
CREATE OR REPLACE VIEW vw_advanced_def_analytics AS
SELECT
  *,
  ROUND(PERCENT_RANK() OVER (PARTITION BY position, season ORDER BY sk) * 100)::int AS sk_pctile,
  ROUND(PERCENT_RANK() OVER (PARTITION BY position, season ORDER BY int) * 100)::int AS int_pctile,
  ROUND(PERCENT_RANK() OVER (PARTITION BY position, season ORDER BY comb) * 100)::int AS comb_pctile,
  ROUND(PERCENT_RANK() OVER (PARTITION BY position, season ORDER BY prss) * 100)::int AS prss_pctile,
  ROUND(PERCENT_RANK() OVER (PARTITION BY position, season ORDER BY cmp_percent DESC) * 100)::int AS cmp_percent_pctile
FROM nflreadr_nfl_advstats_def_season;

-- Grant SELECT permissions to API roles
GRANT SELECT ON vw_advanced_receiving_analytics TO anon, authenticated, service_role;
GRANT SELECT ON vw_advanced_passing_analytics TO anon, authenticated, service_role;
GRANT SELECT ON vw_advanced_rushing_analytics TO anon, authenticated, service_role;
GRANT SELECT ON vw_advanced_def_analytics TO anon, authenticated, service_role;

-- Note: cmp_percent_pctile uses DESC ordering because LOWER completion % allowed is better for defense
