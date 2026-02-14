# MCP Tools Catalog

The fantasy-tools-mcp server exposes ~40 tools across these categories. This document provides complete parameter reference for all tools.

---

## Player Tools

### `get_player_info_tool`

Fetch basic information for players such as: name, latest team, position, height, weight, birthdate (age) and identifiers.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `player_names` | `list[str]` | Yes | - | List of player names (partial matches supported, case-insensitive) |

**Returns:** List of player info dicts with: name, team, position, height, weight, age, sleeper_id, gsis_id, pfr_id, etc.

**Example:**
```python
get_player_info_tool(player_names=["Justin Jefferson", "Ja'Marr Chase"])
```

---

### `get_players_by_sleeper_id_tool`

Fetch basic information for players by their Sleeper IDs.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `sleeper_ids` | `list[str]` | Yes | - | List of Sleeper player IDs |

**Returns:** List of player info dicts matching the provided Sleeper IDs.

**Example:**
```python
get_players_by_sleeper_id_tool(sleeper_ids=["4017", "6797"])
```

---

### `get_player_profile`

Fetch comprehensive player profile combining basic info and all available stats in a single call. This unified tool reduces the need for 3-4 separate tool calls.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `player_names` | `list[str]` | Yes | - | List of player names (partial matches supported) |
| `season_list` | `list[int] \| None` | No | `None` | Filter by specific seasons (e.g., `[2024, 2025]`) |
| `metrics` | `list[str] \| None` | No | `None` | Specific metrics to include; if None, returns default set |
| `limit` | `int \| None` | No | `25` | Max rows per stats category (receiving/passing/rushing) |

**Returns:** Dict with keys: `playerInfo`, `receivingStats`, `passingStats`, `rushingStats`. Stats categories may be empty for positions that don't record those stats.

**When to use:** Use this when you need a complete player overview instead of calling multiple specialized stats tools separately.

**Example:**
```python
get_player_profile(
    player_names=["Christian McCaffrey"],
    season_list=[2024, 2025],
    limit=50
)
```

---

## Advanced Metrics Tools

These tools query `vw_advanced_*` views for receiving, passing, rushing, and defense analytics.

### Common Parameters (All Advanced Metrics Tools)

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `player_names` | `list[str] \| None` | No | `None` | Player names (partial/fuzzy matching, case-insensitive) |
| `season_list` | `list[int] \| None` | No | `None` | Seasons to filter (e.g., `[2023, 2024, 2025]`) |
| `metrics` | `list[str] \| None` | No | `None` | Specific metrics to return; if None, returns default set. See metric categories in tool descriptions |
| `order_by_metric` | `str \| None` | No | `None` | Metric name to sort by (descending order) |
| `limit` | `int \| None` | No | `100` | Maximum rows to return (implementation may cap this) |
| `positions` | `list[str] \| None` | No | Tool-specific | Filter by positions (defaults vary by tool) |

### Common Parameters (Weekly Stats Tools Only)

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `weekly_list` | `list[int] \| None` | No | `None` | Week numbers to filter (e.g., `[1, 2, 3, 17]`) |

---

### `get_advanced_receiving_stats`

Fetch advanced seasonal receiving stats for WR/TE/RB.

**Default Positions:** `['WR', 'TE', 'RB']`

**Metric Categories:**
- **Volume Metrics:** games, targets, receptions, receiving_yards, receiving_tds, fantasy_points, fantasy_points_ppr, air_yards_share, receiving_air_yards, receiving_first_downs, receiving_2pt_conversions, receiving_yards_after_catch, etc.
- **Efficiency Metrics:** dom, racr, target_share, receiving_epa, catch_percentage, avg_yac, avg_expected_yac, avg_intended_air_yards, avg_yac_above_expectation, drop_percent, etc.
- **Situational Metrics:** avg_cushion, avg_separation, receiving_first_downs, age

**Use `get_metrics_metadata(category="receiving")` for complete metric definitions.**

**Example:**
```python
get_advanced_receiving_stats(
    player_names=["Tyreek Hill", "CeeDee Lamb"],
    season_list=[2024],
    metrics=["targets", "receptions", "receiving_yards", "target_share", "catch_percentage"],
    order_by_metric="receiving_yards",
    limit=50
)
```

---

### `get_advanced_passing_stats`

Fetch advanced seasonal passing stats for QB.

**Default Positions:** `['QB']`

**Metric Categories:**
- **Volume Metrics:** qb_plays, times_hit, times_sacked, times_blitzed, times_hurried, times_pressured, exp_sack, passing_drops
- **Efficiency Metrics:** passer_rating, completion_percentage, avg_air_distance, avg_intended_air_yards, expected_completion_percentage, completion_percentage_above_expectation, qbr_total, epa_total
- **Situational Metrics:** aggressiveness, avg_time_to_throw, passing_bad_throws, passing_bad_throw_pct, times_pressured_pct

**Use `get_metrics_metadata(category="passing")` for complete metric definitions.**

---

### `get_advanced_rushing_stats`

Fetch advanced seasonal rushing stats for RB/QB.

**Default Positions:** `['RB', 'QB']`

**Metric Categories:**
- **Volume Metrics:** games, carries, rushing_yards, rushing_tds, rushing_first_downs, rush_attempts
- **Efficiency Metrics:** rushing_epa, fantasy_points, fantasy_points_ppr, avg_rush_yards, efficiency, expected_rush_yards, rush_pct_over_expected, rush_yards_over_expected, avg_time_to_los
- **Situational Metrics:** rushing_2pt_conversions, rushing_first_downs, rushing_yards_after_catch, brk_tkl

**Use `get_metrics_metadata(category="rushing")` for complete metric definitions.**

---

### `get_advanced_defense_stats`

Fetch advanced seasonal defensive stats for defensive players.

**Default Positions:** `['CB', 'DB', 'DE', 'DL', 'LB', 'S']`

**Metric Categories:**
- **Volume Metrics:** g, gs, sk (sacks), td, int, tgt, prss, bltz, hrry, qbkd, comb (combined tackles), m_tkl (missed tackles)
- **Efficiency Metrics:** cmp_percent, m_tkl_percent, yds_cmp, yds_tgt, rat (passer rating allowed)
- **Situational Metrics:** dadot, age, pos

**Use `get_metrics_metadata(category="defense")` for complete metric definitions.**

---

### `get_advanced_receiving_stats_weekly`

Fetch advanced weekly receiving stats for WR/TE/RB.

**Default Positions:** `['WR', 'TE', 'RB']`

**Additional Parameter:** `weekly_list` (list of week numbers)

**Metric Categories:**
- **Volume Metrics:** passing_drops, receiving_int, receiving_drop, rushing_broken_tackles, receiving_broken_tackles
- **Efficiency Metrics:** receiving_rat, passing_drop_pct, receiving_drop_pct, avg_yac, avg_expected_yac, catch_percentage
- **Situational Metrics:** avg_cushion, avg_separation, player_position, player_display_name, ngr_team

---

### `get_advanced_passing_stats_weekly`

Fetch advanced weekly passing stats for QB.

**Default Positions:** `['QB']`

**Additional Parameter:** `weekly_list` (list of week numbers)

**Metric categories similar to seasonal version but on a per-week basis.**

---

### `get_advanced_rushing_stats_weekly`

Fetch advanced weekly rushing stats for RB/QB.

**Default Positions:** `['RB', 'QB']`

**Additional Parameter:** `weekly_list` (list of week numbers)

**Metric Categories:**
- **Volume Metrics:** rush_attempts, rush_touchdowns
- **Efficiency Metrics:** efficiency, avg_rush_yards, avg_time_to_los, expected_rush_yards, rush_pct_over_expected
- **Situational Metrics:** rushing_broken_tackles, rushing_yards_after_contact, rushing_yards_before_contact

---

### `get_advanced_defense_stats_weekly`

Fetch advanced weekly defensive stats for defensive players.

**Default Positions:** `['CB', 'DB', 'DE', 'DL', 'LB', 'S']`

**Additional Parameter:** `weekly_list` (list of week numbers)

**Metric Categories:**
- **Volume Metrics:** def_tackles_combined, def_sacks, def_ints, def_targets, def_pressures, def_times_blitzed
- **Efficiency Metrics:** def_completion_pct, def_missed_tackles, def_missed_tackle_pct, def_passer_rating_allowed
- **Situational Metrics:** def_adot, def_yards_after_catch, def_receiving_td_allowed, game_id, opponent

---

### `get_metrics_metadata`

Returns metric definitions by category for receiving, passing, rushing, and defense advanced NFL statistics.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `category` | `str \| None` | No | `None` | Category: `receiving`, `passing`, `rushing`, `defense`. If None, returns full catalog |
| `subcategory` | `str \| None` | No | `None` | Subcategory: `basic_info`, `volume_metrics`, `efficiency_metrics`, `situational_metrics`, `weekly` |

**Returns:** Dict of metric definitions with descriptions and units.

**When to use:** Use this tool before querying stats to understand available metrics and their meanings.

**Example:**
```python
# Get all receiving metrics
get_metrics_metadata(category="receiving")

# Get only efficiency metrics for passing
get_metrics_metadata(category="passing", subcategory="efficiency_metrics")
```

---

## Game Stats Tools

### `get_offensive_players_game_stats`

Fetch offensive weekly game stats for NFL players (per-game stats, not season aggregates).

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `player_names` | `list[str] \| None` | No | `None` | Player names (partial/case-insensitive matching) |
| `season_list` | `list[int] \| None` | No | `None` | Seasons to filter |
| `weekly_list` | `list[int] \| None` | No | `None` | Week numbers to filter |
| `metrics` | `list[str] \| None` | No | `None` | Specific metrics; if None, returns default core offensive metrics |
| `order_by_metric` | `str \| None` | No | `None` | Metric to sort by (descending) |
| `limit` | `int \| None` | No | `100` | Max rows to return |
| `positions` | `list[str] \| None` | No | `['QB', 'RB', 'WR', 'TE']` | Offensive positions to include |

**Metric Categories:**
- **Volume:** passing yards, rushing yards, receiving yards, touchdowns, targets, snaps
- **Efficiency:** completion percentage, yards per attempt, yards after catch
- **Situational:** red zone efficiency, third down conversions, game identifiers, opponent

**Use `get_stats_metadata(category="offense")` for field definitions.**

---

### `get_defensive_players_game_stats`

Fetch defensive weekly game stats for NFL players.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `player_names` | `list[str] \| None` | No | `None` | Player names (partial/case-insensitive matching) |
| `season_list` | `list[int] \| None` | No | `None` | Seasons to filter |
| `weekly_list` | `list[int] \| None` | No | `None` | Week numbers to filter |
| `metrics` | `list[str] \| None` | No | `None` | Specific metrics; if None, returns default core defensive metrics |
| `order_by_metric` | `str \| None` | No | `None` | Metric to sort by (descending) |
| `limit` | `int \| None` | No | `100` | Max rows to return |
| `positions` | `list[str] \| None` | No | `['CB', 'DB', 'DE', 'DL', 'LB', 'S']` | Defensive positions to include |

**Metric Categories:**
- **Volume:** tackles, assisted tackles, sacks, interceptions, targets, pressures, pass breakups
- **Efficiency:** completion percentage allowed, yards allowed, passer rating allowed, missed tackle rate
- **Situational:** yards after catch allowed, air yards completed, TDs allowed, game identifiers

**Use `get_stats_metadata(category="defense")` for field definitions.**

---

### `get_stats_metadata`

Return game-stat field definitions for NFL offense/defense.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `category` | `str` | Yes | - | `offense` or `defense` (aliases: `off`, `o`, `def`, `d`) |
| `subcategory` | `str \| None` | No | `None` | Offense: `overall`, `passing`, `rushing`, `receiving`, `pressure_and_sacks`, `special_teams`, `seasonal`. Defense: `overall`, `tackling`, `pressure`, `coverage`, `turnovers`, `penalties` |

**Returns:** Dict of field definitions for the requested category/subcategory.

**Example:**
```python
# Get all offensive stats definitions
get_stats_metadata(category="offense")

# Get only passing stats definitions
get_stats_metadata(category="offense", subcategory="passing")
```

---

## Sleeper API Tools

### `get_sleeper_leagues_by_username`

Fetch Sleeper leagues for a specific user by their username.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `username` | `str` | Yes | - | Sleeper username |
| `verbose` | `bool` | No | `False` | If True, includes `scoring_settings`, `settings`, and `roster_positions`. If False, returns compact league info |

**Returns:** List of league dicts.

**When to use `verbose`:**
- `False` (default): Quick league list, just basic info (league_id, name, season, sport, status)
- `True`: Full details including scoring rules, roster settings, and league configuration

**Example:**
```python
# Quick league list
get_sleeper_leagues_by_username(username="john_doe")

# Full league details
get_sleeper_leagues_by_username(username="john_doe", verbose=True)
```

---

### `get_sleeper_league_rosters`

Get rosters for a given Sleeper league ID.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `league_id` | `str` | Yes | - | Sleeper league ID |
| `summary` | `bool` | No | `False` | If True, returns compact roster info with player names/positions/teams instead of raw player ID arrays. If False, returns full roster data with player IDs |

**Returns:** List of roster dicts.

**When to use `summary`:**
- `False` (default): Raw Sleeper API format with player ID arrays
- `True`: Human-readable format with player names, positions, and teams resolved from database

**Example:**
```python
# Raw roster data with player IDs
get_sleeper_league_rosters(league_id="123456789")

# Summary with player names
get_sleeper_league_rosters(league_id="123456789", summary=True)
```

---

### `get_sleeper_league_users`

Get the users for a given Sleeper league ID.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `league_id` | `str` | Yes | - | Sleeper league ID |

**Returns:** List of user dicts with display names, user IDs, and metadata.

---

### `get_sleeper_league_matchups`

Get matchups for a given Sleeper league ID and week.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `league_id` | `str` | Yes | - | Sleeper league ID |
| `week` | `int` | Yes | - | Week number (1-18 for regular season) |
| `summary` | `bool` | No | `False` | If True, returns compact matchup info with player names/positions/teams. If False, returns raw matchup data with player IDs |

**Returns:** List of matchup dicts.

**When to use `summary`:**
- `False` (default): Raw API format with player ID arrays and points
- `True`: Human-readable with player names resolved and lineup details

---

### `get_sleeper_league_transactions`

Get transactions for a given Sleeper league ID and week.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `league_id` | `str` | Yes | - | Sleeper league ID |
| `week` | `int` | Yes | - | Week number |
| `txn_type` | `str \| None` | No | `None` | Filter by transaction type: `trade`, `waiver`, `free_agent`. If None, returns all types |

**Returns:** List of transaction dicts.

**When to use `txn_type`:**
- `None` (default): All transactions (trades, waivers, free agent moves)
- `"trade"`: Only trades
- `"waiver"`: Only waiver claims
- `"free_agent"`: Only free agent pickups

**Example:**
```python
# All transactions
get_sleeper_league_transactions(league_id="123456789", week=5)

# Only trades
get_sleeper_league_transactions(league_id="123456789", week=5, txn_type="trade")
```

---

### `get_sleeper_trending_players`

Get trending players for the specified sport from Sleeper (adds/drops over time window).

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `sport` | `str` | No | `"nfl"` | Sport type (typically `"nfl"`) |
| `add_drop` | `str` | No | `"add"` | Trend type: `"add"` for most added, `"drop"` for most dropped |
| `hours` | `int` | No | `24` | Lookback period in hours (12, 24, or 48 typical) |
| `limit` | `int` | No | `25` | Number of trending players to return |

**Returns:** List of trending player dicts with counts.

**Example:**
```python
# Top 25 adds in last 24 hours
get_sleeper_trending_players()

# Top 50 drops in last 48 hours
get_sleeper_trending_players(add_drop="drop", hours=48, limit=50)
```

---

### `get_sleeper_user_drafts`

Get all drafts for a Sleeper user.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `username` | `str` | Yes | - | Sleeper username |
| `sport` | `str` | No | `"nfl"` | Sport type |
| `season` | `int` | No | `2025` | Season year |

**Returns:** List of draft dicts.

---

### `get_sleeper_league_by_id`

Get a Sleeper league by its ID.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `league_id` | `str` | Yes | - | Sleeper league ID |
| `summary` | `bool` | No | `False` | If True, returns compact league data without nested settings. If False, includes scoring settings, league settings, and roster positions |

**Returns:** League dict.

**When to use `summary`:**
- `False` (default): Full league details with all settings
- `True`: Compact overview without nested configuration objects

---

### `get_sleeper_draft_by_id`

Get a Sleeper draft by its ID.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `draft_id` | `str` | Yes | - | Sleeper draft ID |

**Returns:** Draft dict with basic info, participants, and draft settings.

---

### `get_sleeper_all_draft_picks_by_id`

Get all draft picks for a given Sleeper draft ID.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `draft_id` | `str` | Yes | - | Sleeper draft ID |

**Returns:** Dict with all draft picks in order.

---

## Ranking Tools

### `get_fantasy_rank_page_types`

Get distinct dynasty rank page types for context.

**Parameters:** None

**Returns:** List of unique `page_type` values from `vw_dynasty_ranks` (e.g., `["dynasty-overall", "dynasty-qb", "superflex-rankings"]`)

**When to use:** Call this first to discover available ranking categories before calling `get_fantasy_ranks`.

---

### `get_fantasy_ranks`

Fetch dynasty ranks from `vw_dynasty_ranks`, filtered by position and/or page_type.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `position` | `str \| None` | No | `None` | Filter by position (e.g., `"QB"`, `"RB"`, `"WR"`, `"TE"`) |
| `page_type` | `str \| None` | No | `None` | Filter by ranking category (use `get_fantasy_rank_page_types` to discover available types) |
| `limit` | `int \| None` | No | `30` | Max rows to return |

**Returns:** List of rank dicts with: player_name, position, rank, value, tier, etc.

**Example:**
```python
# Top 30 overall dynasty rankings
get_fantasy_ranks(limit=30)

# Top 20 dynasty QBs
get_fantasy_ranks(position="QB", limit=20)

# Top 50 superflex rankings
get_fantasy_ranks(page_type="superflex-rankings", limit=50)
```

---

## Dictionary Tools

### `get_dictionary_info`

Fetch rows from the combined dictionary view, optionally filtering by search criteria in the description.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `search_criteria` | `list[str] \| None` | No | `None` | List of search terms to filter descriptions (case-insensitive partial matching) |

**Returns:** List of data field definition dicts.

**When to use:** Use this to understand what columns/fields mean in the underlying nflreadr/nfldata tables.

**Example:**
```python
# Get all field definitions
get_dictionary_info()

# Search for fields related to targets
get_dictionary_info(search_criteria=["target", "reception"])
```

---

## Web Search Tools

### `search_web_tool`

Search the web for current NFL news, injury reports, fantasy analysis, and breaking stories.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | `str` | Yes | - | Search query string |
| `max_results` | `int` | No | `5` | Maximum number of search results to return |

**Returns:** Dict with search results and AI-generated summaries.

**When to use:** Use this for real-time information not available in the database (breaking news, injury updates, recent transactions, expert analysis).

**Example:**
```python
search_web_tool(query="Christian McCaffrey injury update", max_results=3)
```

---

## Parameter Best Practices

### Using `summary` vs `verbose` Parameters

- **`summary`** (league/roster/matchup tools): Controls output detail level
  - `False` = raw API format (player IDs, full objects)
  - `True` = human-readable (resolved player names, simplified structure)

- **`verbose`** (league tools): Controls inclusion of nested settings
  - `False` = basic info only
  - `True` = includes scoring_settings, roster_positions, etc.

**When to use which:**
- Use `summary=True` when presenting data to users or for readability
- Use `summary=False` when you need raw IDs for further API calls
- Use `verbose=True` when you need scoring rules or league configuration details

### Using `metrics` Parameter

The `metrics` parameter lets you request specific stat columns instead of getting a default set:

```python
# Get only specific efficiency metrics
get_advanced_receiving_stats(
    player_names=["Tyreek Hill"],
    metrics=["target_share", "catch_percentage", "avg_yac_above_expectation"]
)
```

**Best practice:** Use `get_metrics_metadata()` first to discover available metrics, then request only what you need.

### Using `txn_type` Parameter

Filter Sleeper transactions by type:

- `None`: All transactions (trades, waivers, free agents)
- `"trade"`: Only trades between teams
- `"waiver"`: Only successful waiver claims
- `"free_agent"`: Only free agent pickups (no waiver)

### Using `limit` Parameter

All query tools support `limit` to control result size:

- **Default values vary by tool** (typically 25-100)
- Implementation may enforce maximum caps
- Use lower limits for faster responses
- Increase limit when you need comprehensive data

**Example:**
```python
# Quick check: top 10 RBs by rushing yards
get_advanced_rushing_stats(
    positions=["RB"],
    season_list=[2024],
    order_by_metric="rushing_yards",
    limit=10
)
```

---

## MCP Resources

The server also exposes metrics definitions as MCP resources with `metrics://` URIs:

- `metrics://catalog` — Complete metrics catalog
- `metrics://receiving` — Receiving metrics only
- `metrics://passing` — Passing metrics only
- `metrics://rushing` — Rushing metrics only
- `metrics://defense` — Defense metrics only

These are static resources that can be accessed via MCP resource protocol.
