# Supabase Database Schema

**Project**: "Advanced Fantasy Insights" (region: us-east-1, project ID in `.env` files)

## Table Groups (~90 tables in `public` schema)

| Prefix | Count | Description |
|---|---|---|
| `nflreadr_nfl_*` | ~20 | Core NFL data: players, rosters, stats, schedules, injuries, snap counts, combine, contracts, depth charts, trades |
| `nflreadr_nfl_advstats_*` | 8 | Advanced stats by position (rec/pass/rush/def) x (season/week) |
| `nflreadr_dictionary_*` | ~15 | Data dictionaries for all nflreadr tables |
| `nflreadr_nfl_nextgen_stats_*` | 3 | NextGen Stats (passing, receiving, rushing) |
| `nfldata_*` | ~15 | Games, predictions, standings, teams, logos, draft picks/values, rosters |
| `dynastyprocess_*` | 4 | Fantasy valuations, FPECR rankings, player IDs |
| `vw_advanced_*` | 8 | Pre-computed analytics views (receiving/passing/rushing/defense x season/weekly) |
| `vw_dictionary_combined` | 1 | Combined data dictionary view |
| `vw_nfl_players_with_dynasty_ids` | 1 | Player IDs joined with dynasty process IDs |
| `vw_seasonal_offensive_player_data` | 1 | Seasonal offensive stats view |

## App-Specific Tables

- `chat_sessions` — Chat persistence (AI SDK messages as JSONB)
- `platform_users` — App user accounts
- `user_preferences` — Cross-session user memory (Sleeper username, leagues, roster notes)
- `player_insights`, `player_metrics_weekly`, `player_projection` — Derived analytics
