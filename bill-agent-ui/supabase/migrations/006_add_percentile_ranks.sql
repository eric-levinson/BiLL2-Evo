-- Add positional percentile rank columns to seasonal advanced stats.
--
-- PERCENT_RANK() window functions are partitioned by position + season, output as 0-100 integers.
--
-- For passing, rushing, and defense: percentiles are added directly to the existing views
-- via CREATE OR REPLACE VIEW (appending new columns preserves the existing column contract).
--
-- For receiving: the view has a LATERAL subquery join that makes inline PERCENT_RANK() too
-- expensive for Supabase's statement timeout. Receiving percentiles are pre-computed in a
-- separate materialized view (mv_receiving_percentile_ranks) instead.
--
-- Views modified (inline PERCENT_RANK):
--   - vw_advanced_passing_analytics (QB seasonal passing stats)
--   - vw_advanced_rushing_analytics (RB/QB seasonal rushing stats)
--   - vw_advanced_def_analytics (defensive player seasonal stats)
--
-- Materialized view created:
--   - mv_receiving_percentile_ranks (WR/TE/RB seasonal receiving percentiles)
--
-- Refresh with: REFRESH MATERIALIZED VIEW mv_receiving_percentile_ranks;

-- ────────────────────────────────────────────────────────────────────────
-- 1. vw_advanced_passing_analytics
-- Adds: passing_yards_pctile, passing_tds_pctile, passer_rating_pctile,
--       completion_percentage_pctile, epa_total_pctile, fantasy_points_ppr_pctile
-- ────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW vw_advanced_passing_analytics AS
SELECT
  sub.*,
  ROUND(PERCENT_RANK() OVER (PARTITION BY sub.ff_position, sub.season ORDER BY sub.passing_yards) * 100)::int AS passing_yards_pctile,
  ROUND(PERCENT_RANK() OVER (PARTITION BY sub.ff_position, sub.season ORDER BY sub.passing_tds) * 100)::int AS passing_tds_pctile,
  ROUND(PERCENT_RANK() OVER (PARTITION BY sub.ff_position, sub.season ORDER BY sub.passer_rating) * 100)::int AS passer_rating_pctile,
  ROUND(PERCENT_RANK() OVER (PARTITION BY sub.ff_position, sub.season ORDER BY sub.completion_percentage) * 100)::int AS completion_percentage_pctile,
  ROUND(PERCENT_RANK() OVER (PARTITION BY sub.ff_position, sub.season ORDER BY sub.epa_total) * 100)::int AS epa_total_pctile,
  ROUND(PERCENT_RANK() OVER (PARTITION BY sub.ff_position, sub.season ORDER BY sub.fantasy_points_ppr) * 100)::int AS fantasy_points_ppr_pctile
FROM (
  SELECT sa.season,
    sa.player_id AS gsis_id,
    pid.name AS player_name,
    pid.team AS ff_team,
    pid."position" AS ff_position,
    sa.pacr,
    sa.games,
    sa.sacks_suffered,
    sa.dakota,
    sa.ppr_sh,
    sa.carries,
    sa.attempts,
    sa.sack_yards_lost,
    sa.completions,
    sa.passing_epa,
    sa.passing_tds,
    sa.rushing_epa,
    sa.rushing_tds,
    sa.sack_fumbles,
    sa.passing_interceptions,
    sa.passing_yards,
    sa.rushing_yards,
    sa.fantasy_points,
    sa.rushing_fumbles,
    sa.passing_air_yards,
    sa.sack_fumbles_lost,
    sa.fantasy_points_ppr,
    sa.passing_first_downs,
    sa.rushing_first_downs,
    sa.rushing_fumbles_lost,
    sa.passing_2pt_conversions,
    sa.rushing_2pt_conversions,
    sa.passing_yards_after_catch,
    sa.passing_cpoe,
    qbr.rank AS qbr_rank,
    qbr.qbr_raw,
    qbr.exp_sack,
    qbr.qb_plays,
    qbr.epa_total,
    qbr.qbr_total,
    ngp.passer_rating,
    ngp.aggressiveness,
    ngp.avg_air_distance,
    ngp.max_air_distance,
    ngp.avg_time_to_throw,
    ngp.completion_percentage,
    ngp.avg_intended_air_yards,
    ngp.avg_air_yards_to_sticks,
    ngp.avg_completed_air_yards,
    ngp.avg_air_yards_differential,
    ngp.max_completed_air_distance,
    ngp.expected_completion_percentage,
    ngp.completion_percentage_above_expectation,
    adv.spikes,
    adv.drop_pct,
    adv.rpo_plays,
    adv.rpo_yards,
    adv.times_hit,
    adv.bad_throws,
    adv.on_tgt_pct,
    adv.throwaways,
    adv.pa_pass_att,
    adv.pocket_time,
    adv.batted_balls,
    adv.pressure_pct,
    adv.rpo_pass_att,
    adv.rpo_rush_att,
    adv.bad_throw_pct,
    adv.on_tgt_throws,
    adv.pa_pass_yards,
    adv.times_blitzed,
    adv.times_hurried,
    adv.rpo_pass_yards,
    adv.rpo_rush_yards,
    adv.times_pressured,
    pid.height,
    pid.weight,
    pid.merge_name
  FROM nfldata_seasonal_analytics sa
    LEFT JOIN nflreadr_nfl_ff_playerids pid ON sa.player_id::text = pid.gsis_id::text AND pid."position"::text = 'QB'::text
    LEFT JOIN nflreadr_nfl_nextgen_stats_passing ngp ON ngp.player_gsis_id::text = sa.player_id::text AND ngp.season = sa.season AND ngp.week = 0::numeric
    LEFT JOIN nflreadr_nfl_advstats_pass_season adv ON adv.pfr_id::text = pid.pfr_id::text AND adv.season = sa.season
    LEFT JOIN nflreadr_nfl_espn_qbr_season qbr ON qbr.player_id = pid.espn_id AND qbr.season = sa.season AND qbr.season_type::text = 'Regular'::text
  WHERE sa.season >= 2015::numeric AND sa.season_type::text = 'REG'::text
) sub;

-- ────────────────────────────────────────────────────────────────────────
-- 2. vw_advanced_rushing_analytics
-- Adds: carries_pctile, rushing_yards_pctile, rushing_tds_pctile,
--       rushing_epa_pctile, fantasy_points_ppr_pctile, avg_rush_yards_pctile
-- ────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW vw_advanced_rushing_analytics AS
SELECT
  sub.*,
  ROUND(PERCENT_RANK() OVER (PARTITION BY sub.ff_position, sub.season ORDER BY sub.carries) * 100)::int AS carries_pctile,
  ROUND(PERCENT_RANK() OVER (PARTITION BY sub.ff_position, sub.season ORDER BY sub.rushing_yards) * 100)::int AS rushing_yards_pctile,
  ROUND(PERCENT_RANK() OVER (PARTITION BY sub.ff_position, sub.season ORDER BY sub.rushing_tds) * 100)::int AS rushing_tds_pctile,
  ROUND(PERCENT_RANK() OVER (PARTITION BY sub.ff_position, sub.season ORDER BY sub.rushing_epa) * 100)::int AS rushing_epa_pctile,
  ROUND(PERCENT_RANK() OVER (PARTITION BY sub.ff_position, sub.season ORDER BY sub.fantasy_points_ppr) * 100)::int AS fantasy_points_ppr_pctile,
  ROUND(PERCENT_RANK() OVER (PARTITION BY sub.ff_position, sub.season ORDER BY sub.avg_rush_yards) * 100)::int AS avg_rush_yards_pctile
FROM (
  SELECT sa.season,
    sa.player_id AS gsis_id,
    pid.name AS player_name,
    pid.team AS ff_team,
    pid."position" AS ff_position,
    sa.dom,
    sa.games,
    sa.ry_sh,
    sa.w8dom,
    sa.ppr_sh,
    sa.tgt_sh,
    sa.yac_sh,
    sa.yptmpa,
    sa.carries,
    sa.targets,
    sa.receptions,
    sa.rushing_epa,
    sa.rushing_tds,
    sa.target_share,
    sa.receiving_epa,
    sa.receiving_tds,
    sa.rushing_yards,
    sa.fantasy_points,
    sa.receiving_yards,
    sa.rushing_fumbles,
    sa.fantasy_points_ppr,
    sa.rushing_first_downs,
    sa.rushing_fumbles_lost,
    sa.receiving_yards_after_catch,
    adv.gs,
    adv.td,
    adv.age,
    adv.att,
    adv.x1d,
    adv.yac,
    adv.ybc,
    adv.yds,
    adv.att_br,
    adv.brk_tkl,
    adv.yac_att,
    adv.ybc_att,
    ngp.efficiency,
    ngp.rush_attempts,
    ngp.avg_rush_yards,
    ngp.avg_time_to_los,
    ngp.rush_touchdowns,
    ngp.expected_rush_yards,
    ngp.rush_pct_over_expected,
    ngp.rush_yards_over_expected,
    ngp.rush_yards_over_expected_per_att,
    ngp.percent_attempts_gte_eight_defenders,
    pid.height,
    pid.weight,
    pid.merge_name
  FROM nfldata_seasonal_analytics sa
    LEFT JOIN nflreadr_nfl_ff_playerids pid ON sa.player_id::text = pid.gsis_id::text
    LEFT JOIN nflreadr_nfl_nextgen_stats_rushing ngp ON ngp.player_gsis_id::text = sa.player_id::text AND ngp.season = sa.season AND ngp.week = 0::numeric
    LEFT JOIN nflreadr_nfl_advstats_rush_season adv ON adv.pfr_id::text = pid.pfr_id::text AND adv.season = sa.season
  WHERE sa.season >= 2015::numeric AND sa.season_type::text = 'REG'::text
) sub;

-- ────────────────────────────────────────────────────────────────────────
-- 3. vw_advanced_def_analytics
-- Adds: sk_pctile, int_pctile, comb_pctile, prss_pctile, cmp_percent_pctile
-- Note: cmp_percent_pctile uses DESC because LOWER completion % allowed is better
-- ────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW vw_advanced_def_analytics AS
SELECT
  sub.*,
  ROUND(PERCENT_RANK() OVER (PARTITION BY sub."position", sub.season ORDER BY sub.sk) * 100)::int AS sk_pctile,
  ROUND(PERCENT_RANK() OVER (PARTITION BY sub."position", sub.season ORDER BY sub."int") * 100)::int AS int_pctile,
  ROUND(PERCENT_RANK() OVER (PARTITION BY sub."position", sub.season ORDER BY sub.comb) * 100)::int AS comb_pctile,
  ROUND(PERCENT_RANK() OVER (PARTITION BY sub."position", sub.season ORDER BY sub.prss) * 100)::int AS prss_pctile,
  ROUND(PERCENT_RANK() OVER (PARTITION BY sub."position", sub.season ORDER BY sub.cmp_percent DESC) * 100)::int AS cmp_percent_pctile
FROM (
  SELECT pid.gsis_id,
    pid.name AS player_name,
    pid.team,
    pid."position",
    pid.height,
    pid.weight,
    pid.merge_name,
    adv.age,
    adv.season,
    adv.g,
    adv.gs,
    adv.sk,
    adv.td,
    adv.air,
    adv.cmp,
    adv."int",
    adv.pos,
    adv.rat,
    adv.tgt,
    adv.yac,
    adv.yds,
    adv.bltz,
    adv.comb,
    adv.hrry,
    adv.prss,
    adv.qbkd,
    adv.dadot,
    adv.m_tkl,
    adv.loaded,
    adv.pfr_id,
    adv.yds_cmp,
    adv.yds_tgt,
    adv.cmp_percent,
    adv.m_tkl_percent
  FROM nflreadr_nfl_advstats_def_season adv
    LEFT JOIN nflreadr_nfl_ff_playerids pid ON adv.pfr_id::text = pid.pfr_id::text
  WHERE adv.season >= 2015::numeric
) sub;

-- ────────────────────────────────────────────────────────────────────────
-- 4. mv_receiving_percentile_ranks (materialized view)
-- Pre-computes receiving percentiles at refresh time so queries stay fast.
-- The receiving view (vw_advanced_receiving_analytics) is NOT modified because
-- its LATERAL subquery join + PERCENT_RANK() exceeds Supabase statement timeout.
--
-- Adds: targets_pctile, target_share_pctile, receiving_yards_pctile,
--       fantasy_points_ppr_pctile, catch_percentage_pctile, avg_yac_pctile
--
-- Refresh with: REFRESH MATERIALIZED VIEW mv_receiving_percentile_ranks;
-- ────────────────────────────────────────────────────────────────────────
DROP MATERIALIZED VIEW IF EXISTS mv_receiving_percentile_ranks;

CREATE MATERIALIZED VIEW mv_receiving_percentile_ranks AS
SELECT
    sub.gsis_id,
    sub.player_name,
    sub.merge_name,
    sub.ff_position,
    sub.season,
    sub.targets,
    sub.tgt_sh,
    sub.receiving_yards,
    sub.fantasy_points_ppr,
    sub.receptions,
    sub.avg_yac,
    ROUND(PERCENT_RANK() OVER (PARTITION BY sub.ff_position, sub.season ORDER BY sub.targets) * 100)::int AS targets_pctile,
    ROUND(PERCENT_RANK() OVER (PARTITION BY sub.ff_position, sub.season ORDER BY sub.tgt_sh) * 100)::int AS target_share_pctile,
    ROUND(PERCENT_RANK() OVER (PARTITION BY sub.ff_position, sub.season ORDER BY sub.receiving_yards) * 100)::int AS receiving_yards_pctile,
    ROUND(PERCENT_RANK() OVER (PARTITION BY sub.ff_position, sub.season ORDER BY sub.fantasy_points_ppr) * 100)::int AS fantasy_points_ppr_pctile,
    ROUND(PERCENT_RANK() OVER (PARTITION BY sub.ff_position, sub.season ORDER BY
        CASE WHEN sub.targets > 0 THEN (sub.receptions::decimal / sub.targets) ELSE 0 END
    ) * 100)::int AS catch_percentage_pctile,
    ROUND(PERCENT_RANK() OVER (PARTITION BY sub.ff_position, sub.season ORDER BY sub.avg_yac) * 100)::int AS avg_yac_pctile
FROM (
    SELECT sa.season,
        sa.player_id AS gsis_id,
        pid.name AS player_name,
        pid."position" AS ff_position,
        pid.merge_name,
        sa.targets,
        sa.tgt_sh,
        sa.receptions,
        sa.receiving_yards,
        sa.fantasy_points_ppr,
        ngr.avg_yac
    FROM nfldata_seasonal_analytics sa
        LEFT JOIN LATERAL (
            SELECT p.name, p."position", p.merge_name
            FROM nflreadr_nfl_ff_playerids p
            WHERE p.gsis_id::text = sa.player_id::text
            LIMIT 1
        ) pid ON true
        LEFT JOIN nflreadr_nfl_nextgen_stats_receiving ngr ON ngr.player_gsis_id::text = sa.player_id::text AND ngr.season = sa.season AND ngr.week = 0::numeric
    WHERE sa.season >= 2015::numeric AND sa.season_type::text = 'REG'::text
        AND pid."position" IN ('WR', 'TE', 'RB')
) sub;

-- Indexes for query performance (no unique index needed — base table has
-- duplicate player_id per season for traded players)
CREATE INDEX idx_mv_receiving_pctile_merge_name
    ON mv_receiving_percentile_ranks (merge_name);

CREATE INDEX idx_mv_receiving_pctile_position_season
    ON mv_receiving_percentile_ranks (ff_position, season);

CREATE INDEX idx_mv_receiving_pctile_gsis_season
    ON mv_receiving_percentile_ranks (gsis_id, season);

-- Grant read access through the API
GRANT SELECT ON vw_advanced_passing_analytics TO anon, authenticated, service_role;
GRANT SELECT ON vw_advanced_rushing_analytics TO anon, authenticated, service_role;
GRANT SELECT ON vw_advanced_def_analytics TO anon, authenticated, service_role;
GRANT SELECT ON mv_receiving_percentile_ranks TO anon, authenticated, service_role;
