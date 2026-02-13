# MCP Tools Catalog

The fantasy-tools-mcp server exposes ~40 tools across these categories:

## Player Tools
- `get_player_info_tool` — Lookup player by name (returns name, team, position, height, weight, age, IDs)
- `get_players_by_sleeper_id_tool` — Lookup players by Sleeper IDs

## Advanced Stats Tools (query `vw_advanced_*` views)
- `get_advanced_receiving_stats` / `_weekly` — Receiving analytics
- `get_advanced_passing_stats` / `_weekly` — Passing analytics
- `get_advanced_rushing_stats` / `_weekly` — Rushing analytics
- `get_advanced_defense_stats` / `_weekly` — Defensive analytics
- `get_metrics_metadata` — Returns metric definitions by category

## Game Stats Tools
- `get_offensive_players_game_stats` — Per-game offensive stats
- `get_defensive_players_game_stats` — Per-game defensive stats
- `get_stats_metadata` — Game stats field definitions

## Sleeper API Tools
- `get_sleeper_leagues_by_username` — List user's leagues
- `get_sleeper_league_rosters` — Rosters with owner annotations
- `get_sleeper_league_users` — League members
- `get_sleeper_league_matchups` — Weekly matchups
- `get_sleeper_league_transactions` — Trades, waivers, free agent moves
- `get_sleeper_trending_players` — Trending adds/drops
- `get_sleeper_user_drafts` — User's drafts
- `get_sleeper_league_by_id` — Full league metadata
- `get_sleeper_draft_by_id` — Draft metadata
- `get_sleeper_all_draft_picks_by_id` — All picks in a draft

## Ranking Tools
- `get_fantasy_rank_page_types` — Available ranking categories
- `get_fantasy_ranks` — Dynasty/redraft rankings with filters

## Dictionary Tools
- `get_dictionary_info` — Data field definitions

## MCP Resources (served as `metrics://` URIs)
- `metrics://catalog` — Complete metrics catalog
- `metrics://receiving`, `metrics://passing`, `metrics://rushing`, `metrics://defense`
