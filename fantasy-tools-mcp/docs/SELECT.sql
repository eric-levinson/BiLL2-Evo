-- rush tds over 1
SELECT
  SUM(CASE WHEN rushing_tds < 1.0 THEN 1 ELSE 0 END)            AS below_1_count,
  SUM(CASE WHEN rushing_tds >= 1.0 THEN 1 ELSE 0 END)           AS at_or_above_1_count,
  COUNT(*)                                                         AS total_rows,
  ROUND(100.0 * SUM(CASE WHEN rushing_tds < 1.0 THEN 1 ELSE 0 END) / NULLIF(COUNT(*),0), 2) AS pct_below,
  ROUND(100.0 * SUM(CASE WHEN rushing_tds >= 1.0 THEN 1 ELSE 0 END) / NULLIF(COUNT(*),0), 2) AS pct_at_or_above
FROM nflreadr_nfl_player_stats
WHERE player_display_name ILIKE '%Jonathan Taylor%'
  AND opponent_team ILIKE '%TEN%';

-- rec tds over 1
SELECT
  SUM(CASE WHEN receiving_tds < 1.0 THEN 1 ELSE 0 END)            AS below_1_count,
  SUM(CASE WHEN receiving_tds >= 1.0 THEN 1 ELSE 0 END)           AS at_or_above_1_count,
  COUNT(*)                                                         AS total_rows,
  ROUND(100.0 * SUM(CASE WHEN receiving_tds < 1.0 THEN 1 ELSE 0 END) / NULLIF(COUNT(*),0), 2) AS pct_below,
  ROUND(100.0 * SUM(CASE WHEN receiving_tds >= 1.0 THEN 1 ELSE 0 END) / NULLIF(COUNT(*),0), 2) AS pct_at_or_above
FROM nflreadr_nfl_player_stats
WHERE player_display_name ILIKE '%Marr Chase%'
  AND opponent_team ILIKE '%CLE%';

-- above 1 passing tds
SELECT
  SUM(CASE WHEN passing_tds < 1.0 THEN 1 ELSE 0 END)            AS below_1_count,
  SUM(CASE WHEN passing_tds >= 1.0 THEN 1 ELSE 0 END)           AS at_or_above_1_count,
  COUNT(*)                                                         AS total_rows,
  ROUND(100.0 * SUM(CASE WHEN passing_tds < 1.0 THEN 1 ELSE 0 END) / NULLIF(COUNT(*),0), 2) AS pct_below,
  ROUND(100.0 * SUM(CASE WHEN passing_tds >= 1.0 THEN 1 ELSE 0 END) / NULLIF(COUNT(*),0), 2) AS pct_at_or_above
FROM nflreadr_nfl_player_stats
WHERE player_display_name ILIKE '%Justin Herbert%'
  AND opponent_team ILIKE '%KC%';

--Team Abbreviations
SELECT DISTINCT opponent_team FROM nflreadr_nfl_player_stats

select rush_attempts from vw_advanced_rushing_analytics_weekly 
where merge_name ILIKE '%Pacheco%'
and rush_attempts is not null


select passing_yards from nflreadr_nfl_player_stats
where player_display_name ILIKE '%Justin Herbert%'
and opponent_team ILIKE '%KC%'


WITH base AS (
  SELECT
    season,
    season_type,
    team,
    games,
    def_tackles_for_loss,
    def_tackles_for_loss_yards,
    def_tackles_solo,
    def_fumbles_forced
  FROM public.nflreadr_nfl_team_stats_reg
  WHERE season = :season
    AND season_type = :season_type
)
SELECT
  season,
  season_type,
  team,
  games,
  ROUND(def_tackles_for_loss / NULLIF(games, 0), 2)        AS tfl_per_game,
  ROUND(def_tackles_for_loss_yards / NULLIF(games, 0), 2)  AS tfl_yards_lost_pg,
  ROUND(def_tackles_solo / NULLIF(games, 0), 2)            AS solo_tackles_pg,
  ROUND(COALESCE(def_fumbles_forced, 0) / NULLIF(games,0), 3) AS fumbles_forced_pg
FROM base
ORDER BY tfl_per_game DESC NULLS LAST, tfl_yards_lost_pg DESC NULLS LAST;

-- league-wide run-defense leaderboard (per-game rates)
WITH base AS (
  SELECT
    season, season_type, team, games,
    def_tackles_for_loss, def_tackles_for_loss_yards,
    def_tackles_solo, def_fumbles_forced
  FROM public.nflreadr_nfl_team_stats_reg
  WHERE season = 2025
    AND season_type = 'REG'
)
SELECT
  season, season_type, team, games,
  ROUND(def_tackles_for_loss / NULLIF(games, 0), 2)        AS tfl_per_game,
  ROUND(def_tackles_for_loss_yards / NULLIF(games, 0), 2)  AS tfl_yards_lost_pg,
  ROUND(def_tackles_solo / NULLIF(games, 0), 2)            AS solo_tackles_pg,
  ROUND(COALESCE(def_fumbles_forced, 0) / NULLIF(games,0), 3) AS fumbles_forced_pg
FROM base
ORDER BY tfl_per_game DESC NULLS LAST, tfl_yards_lost_pg DESC NULLS LAST;

SELECT
  season, season_type, team, games,
  ROUND(def_tackles_for_loss / NULLIF(games, 0), 2)       AS tfl_per_game,
  ROUND(def_tackles_for_loss_yards / NULLIF(games, 0), 2) AS tfl_yards_lost_pg
FROM public.nflreadr_nfl_team_stats_reg
WHERE season = 2025
  AND season_type = 'REG'
  AND team = 'TEN';


WITH base AS (
  SELECT
    season, season_type, team, games,
    ROUND(def_tackles_for_loss / NULLIF(games, 0), 3)       AS tfl_per_game,
    ROUND(def_tackles_for_loss_yards / NULLIF(games, 0), 3) AS tfl_yards_lost_pg
  FROM public.nflreadr_nfl_team_stats_reg
  WHERE season = 2025 AND season_type = 'REG'
)
SELECT
  season, season_type, team, tfl_per_game, tfl_yards_lost_pg,
  ROUND((
    (tfl_per_game - MIN(tfl_per_game) OVER ()) /
    NULLIF(MAX(tfl_per_game) OVER () - MIN(tfl_per_game) OVER (), 0)
    +
    (tfl_yards_lost_pg - MIN(tfl_yards_lost_pg) OVER ()) /
    NULLIF(MAX(tfl_yards_lost_pg) OVER () - MIN(tfl_yards_lost_pg) OVER (), 0)
  )/2.0, 3) AS run_defense_proxy_score
FROM base
ORDER BY run_defense_proxy_score DESC NULLS LAST;




WITH base AS (
  SELECT
    season, season_type, team, games,
    def_sacks, def_sack_yards, def_qb_hits,
    def_interceptions, def_pass_defended
  FROM public.nflreadr_nfl_team_stats_reg
  WHERE season = 2025 AND season_type = 'REG'
),
rates AS (
  SELECT
    season, season_type, team, games,
    def_sacks / NULLIF(games,0)         AS sacks_pg,
    def_qb_hits / NULLIF(games,0)       AS qb_hits_pg,
    def_sack_yards / NULLIF(games,0)    AS sack_yds_pg,
    def_interceptions / NULLIF(games,0) AS ints_pg,
    def_pass_defended / NULLIF(games,0) AS pd_pg
  FROM base
),
scaled AS (
  SELECT
    season, season_type, team,

    -- min–max scale each metric to 0..1 (guards div-by-zero with NULLIF)
    (sacks_pg    - MIN(sacks_pg)    OVER ()) / NULLIF(MAX(sacks_pg)    OVER () - MIN(sacks_pg)    OVER (), 0) AS sacks_scaled,
    (qb_hits_pg  - MIN(qb_hits_pg)  OVER ()) / NULLIF(MAX(qb_hits_pg)  OVER () - MIN(qb_hits_pg)  OVER (), 0) AS qb_hits_scaled,
    (sack_yds_pg - MIN(sack_yds_pg) OVER ()) / NULLIF(MAX(sack_yds_pg) OVER () - MIN(sack_yds_pg) OVER (), 0) AS sack_yds_scaled,
    (ints_pg     - MIN(ints_pg)     OVER ()) / NULLIF(MAX(ints_pg)     OVER () - MIN(ints_pg)     OVER (), 0) AS ints_scaled,
    (pd_pg       - MIN(pd_pg)       OVER ()) / NULLIF(MAX(pd_pg)       OVER () - MIN(pd_pg)       OVER (), 0) AS pd_scaled
  FROM rates
)
SELECT
  season, season_type, team,
  ROUND((sacks_scaled + qb_hits_scaled)/2.0, 3) AS pressure_score,
  ROUND((ints_scaled  + pd_scaled     )/2.0, 3) AS ballhawk_score,
  ROUND(sack_yds_scaled, 3)                     AS severity_score,
  ROUND(0.4 * ((sacks_scaled + qb_hits_scaled)/2.0)
      + 0.4 * ((ints_scaled  + pd_scaled)/2.0)
      + 0.2 * sack_yds_scaled, 3)               AS pass_defense_proxy_score
FROM scaled
ORDER BY pass_defense_proxy_score DESC NULLS LAST, pressure_score DESC NULLS LAST;