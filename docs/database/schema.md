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
| `vw_advanced_*` | 8 | Pre-computed analytics views (receiving/passing/rushing/defense x season/weekly) with positional percentile ranks |
| `vw_dictionary_combined` | 1 | Combined data dictionary view |
| `vw_nfl_players_with_dynasty_ids` | 1 | Player IDs joined with dynasty process IDs |
| `vw_seasonal_offensive_player_data` | 1 | Seasonal offensive stats view |

## App-Specific Tables

### `chat_sessions`

Stores AI chat conversation sessions with messages in JSONB format (Vercel AI SDK UIMessage format).

**Columns:**

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | NO | `gen_random_uuid()` | Primary key, unique session identifier |
| `user_id` | UUID | NO | - | Foreign key to `auth.users(id)`, owner of the session (ON DELETE CASCADE) |
| `title` | TEXT | NO | - | Chat session title (derived from first user message) |
| `messages` | JSONB | NO | `'[]'::jsonb` | Array of chat messages in Vercel AI SDK UIMessage format |
| `created_at` | TIMESTAMPTZ | NO | `NOW()` | Timestamp when session was created |
| `updated_at` | TIMESTAMPTZ | NO | `NOW()` | Timestamp when session was last updated (auto-updated via trigger) |

**Indexes:**
- `idx_chat_sessions_user_id` on `user_id` (for filtering sessions by user)
- `idx_chat_sessions_created_at` on `created_at DESC` (for sorting sessions chronologically)

**RLS Policies:**
- Users can view/insert/update/delete only their own chat sessions (scoped by `auth.uid() = user_id`)

**JSONB Message Structure (AI SDK UIMessage format):**

Each message in the `messages` array follows the Vercel AI SDK v6 UIMessage format:

```json
{
  "id": "msg-uuid",
  "role": "user" | "assistant" | "system" | "tool",
  "parts": [
    { "type": "text", "text": "message content" },
    { "type": "tool-call", "toolCallId": "call-123", "toolName": "get_player_stats", "args": {...} },
    { "type": "tool-result", "toolCallId": "call-123", "toolName": "get_player_stats", "result": {...} }
  ],
  "createdAt": "2025-01-15T10:30:00Z"
}
```

**Triggers:**
- `set_updated_at` — Auto-updates `updated_at` timestamp on row update via `handle_updated_at()` function

**Example Query:**

```sql
-- Fetch all sessions for a user, sorted by most recent
SELECT id, title, created_at
FROM chat_sessions
WHERE user_id = '550e8400-e29b-41d4-a716-446655440000'
ORDER BY created_at DESC;

-- Get a single session with all messages
SELECT *
FROM chat_sessions
WHERE id = 'session-uuid'
  AND user_id = '550e8400-e29b-41d4-a716-446655440000';
```

---

### `user_preferences`

Stores user preferences for cross-session memory including connected Sleeper leagues, favorite players, and analysis style.

**Columns:**

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | NO | `gen_random_uuid()` | Primary key, unique preference record identifier |
| `user_id` | UUID | NO | - | Foreign key to `auth.users(id)`, owner of preferences (ON DELETE CASCADE) |
| `connected_leagues` | JSONB | NO | `'[]'::jsonb` | Array of connected Sleeper leagues with metadata |
| `primary_league_id` | TEXT | YES | `NULL` | ID of user's primary/most frequently referenced league |
| `favorite_players` | TEXT[] | NO | `'{}'` | Array of favorite player names or Sleeper IDs |
| `roster_notes` | JSONB | NO | `'{}'::jsonb` | Roster composition, strengths, and needs per league |
| `analysis_style` | TEXT | NO | `'balanced'` | Preferred analysis style: `data-heavy`, `narrative`, `concise`, `balanced` |
| `preference_tags` | TEXT[] | NO | `'{}'` | Array of preference tags: `dynasty-focused`, `redraft`, `best-ball`, `dfs`, etc. |
| `custom_preferences` | JSONB | NO | `'{}'::jsonb` | Flexible key-value store for any other preferences |
| `created_at` | TIMESTAMPTZ | NO | `NOW()` | Timestamp when preference record was created |
| `updated_at` | TIMESTAMPTZ | NO | `NOW()` | Timestamp when preference record was last updated (auto-updated via trigger) |

**Indexes:**
- `idx_user_preferences_user_id` (UNIQUE) on `user_id` (one preference record per user)

**RLS Policies:**
- Users can view/insert/update/delete only their own preferences (scoped by `auth.uid() = user_id`)

**JSONB Structure for `connected_leagues`:**

```json
[
  {
    "league_id": "123456789",
    "name": "Dynasty League 2024",
    "scoring_format": "PPR",
    "season": 2024,
    "is_primary": true
  }
]
```

**JSONB Structure for `roster_notes`:**

```json
{
  "123456789": {
    "team_name": "The Dynasty Destroyers",
    "key_players": ["Justin Jefferson", "Bijan Robinson"],
    "strengths": ["WR depth", "Young RB core"],
    "needs": ["TE upgrade", "QB2"]
  }
}
```

**Triggers:**
- `set_updated_at` — Auto-updates `updated_at` timestamp on row update via `handle_updated_at()` function

**Example Query:**

```sql
-- Get user preferences with formatted league info
SELECT
  user_id,
  connected_leagues,
  primary_league_id,
  favorite_players,
  analysis_style
FROM user_preferences
WHERE user_id = '550e8400-e29b-41d4-a716-446655440000';

-- Check if user has connected leagues
SELECT
  user_id,
  jsonb_array_length(connected_leagues) as league_count,
  connected_leagues->0->>'name' as primary_league_name
FROM user_preferences
WHERE user_id = '550e8400-e29b-41d4-a716-446655440000'
  AND jsonb_array_length(connected_leagues) > 0;
```

---

### `user_onboarding`

Stores user onboarding progress and Sleeper league connection details.

**Columns:**

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | NO | `gen_random_uuid()` | Primary key, unique onboarding record identifier |
| `user_id` | UUID | NO | - | Foreign key to `auth.users(id)`, owner of onboarding record (ON DELETE CASCADE) |
| `completed` | BOOLEAN | NO | `false` | Boolean flag indicating if onboarding is complete |
| `sleeper_username` | TEXT | YES | `NULL` | User's Sleeper platform username |
| `selected_league_id` | TEXT | YES | `NULL` | ID of the selected Sleeper league |
| `league_name` | TEXT | YES | `NULL` | Name of the selected Sleeper league |
| `created_at` | TIMESTAMPTZ | NO | `NOW()` | Timestamp when onboarding record was created |
| `updated_at` | TIMESTAMPTZ | NO | `NOW()` | Timestamp when onboarding record was last updated (auto-updated via trigger) |

**Indexes:**
- `idx_user_onboarding_user_id` (UNIQUE) on `user_id` (one onboarding record per user)

**RLS Policies:**
- Users can view/insert/update/delete only their own onboarding data (scoped by `auth.uid() = user_id`)

**Triggers:**
- `set_updated_at` — Auto-updates `updated_at` timestamp on row update via `handle_updated_at()` function

**Example Query:**

```sql
-- Check onboarding status for a user
SELECT completed, sleeper_username, league_name
FROM user_onboarding
WHERE user_id = '550e8400-e29b-41d4-a716-446655440000';
```

---

### `auth.users` (Supabase Auth, read-only reference)

Built-in Supabase Auth table for user accounts. App tables reference this via foreign keys.

**Key Columns:**
- `id` (UUID) — User's unique identifier, referenced by `chat_sessions.user_id`, `user_preferences.user_id`, etc.
- `email` (TEXT) — User's email address
- `created_at` (TIMESTAMPTZ) — Account creation timestamp

**Note:** This table is managed by Supabase Auth. App code should NOT directly insert/update/delete from `auth.users`. Use Supabase Auth APIs instead.

---

### `player_insights`, `player_metrics_weekly`, `player_projection` (Planned)

**Status:** Tables mentioned in roadmap but not yet implemented. Reserved for future derived analytics features.

**Planned Purpose:**
- `player_insights` — AI-generated player analysis and narrative insights
- `player_metrics_weekly` — Weekly aggregated player performance metrics
- `player_projection` — Fantasy point projections for upcoming games

**Note:** Implementation pending. See technical debt documentation for details.

---

## Advanced Analytics Views with Percentile Ranks

The seasonal advanced analytics views (`vw_advanced_receiving_analytics`, `vw_advanced_passing_analytics`, `vw_advanced_rushing_analytics`, `vw_advanced_def_analytics`) include positional percentile rank columns for the most fantasy-relevant metrics.

### Percentile Rank Columns by View

**vw_advanced_receiving_analytics** (partitioned by `ff_position` and `season`):
- `targets_pctile` — Percentile rank for targets (0-100)
- `target_share_pctile` — Percentile rank for target share (0-100)
- `receiving_yards_pctile` — Percentile rank for receiving yards (0-100)
- `fantasy_points_ppr_pctile` — Percentile rank for PPR fantasy points (0-100)
- `catch_percentage_pctile` — Percentile rank for catch percentage (0-100)
- `avg_yac_pctile` — Percentile rank for average yards after catch (0-100)

**vw_advanced_passing_analytics** (partitioned by `ff_position` and `season`):
- `passing_yards_pctile` — Percentile rank for passing yards (0-100)
- `passing_tds_pctile` — Percentile rank for passing touchdowns (0-100)
- `passer_rating_pctile` — Percentile rank for passer rating (0-100)
- `completion_percentage_pctile` — Percentile rank for completion percentage (0-100)
- `epa_total_pctile` — Percentile rank for total EPA (0-100)
- `fantasy_points_ppr_pctile` — Percentile rank for PPR fantasy points (0-100)

**vw_advanced_rushing_analytics** (partitioned by `ff_position` and `season`):
- `carries_pctile` — Percentile rank for carries (0-100)
- `rushing_yards_pctile` — Percentile rank for rushing yards (0-100)
- `rushing_tds_pctile` — Percentile rank for rushing touchdowns (0-100)
- `rushing_epa_pctile` — Percentile rank for rushing EPA (0-100)
- `fantasy_points_ppr_pctile` — Percentile rank for PPR fantasy points (0-100)
- `avg_rush_yards_pctile` — Percentile rank for average yards per carry (0-100)

**vw_advanced_def_analytics** (partitioned by `position` and `season`):
- `sk_pctile` — Percentile rank for sacks (0-100)
- `int_pctile` — Percentile rank for interceptions (0-100)
- `comb_pctile` — Percentile rank for combined tackles (0-100)
- `prss_pctile` — Percentile rank for pressures (0-100)
- `cmp_percent_pctile` — Percentile rank for completion percentage allowed (0-100, lower is better so DESC ordered)

**Implementation Notes:**
- Percentiles are computed using `PERCENT_RANK()` window function at query time
- Values range from 0 (worst) to 100 (best)
- Partitioning by position and season ensures apples-to-apples comparisons
- For defense `cmp_percent_pctile`, lower completion % allowed is better, so it uses DESC ordering

---

## Materialized Views

### `mv_player_id_lookup`

Fast player ID resolution and player info lookups. Replaces expensive real-time queries against `vw_nfl_players_with_dynasty_ids` which times out on name searches and large IN() batches.

**Purpose:** Optimize player name → Sleeper ID resolution and player info retrieval.

**Source Tables:** `nflreadr_nfl_players`, `dynastyprocess_playerids`

**Refresh Schedule:** Daily at 6:00 AM UTC via pg_cron (`refresh-mv-player-id-lookup`)

**Refresh Command:**
```sql
SET statement_timeout = '120s';
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_player_id_lookup;
```

**Columns:**
- `sleeper_id` — Sleeper platform player ID (unique index)
- `display_name` — Player display name (trigram index for ILIKE searches)
- `merge_name` — Standardized player name for matching (trigram index)
- `latest_team` — Most recent NFL team
- `position` — Player position
- `height`, `weight` — Physical measurements
- `gsis_id` — NFL GSIS identifier
- `years_of_experience` — Years in NFL
- `age` — Player age

**Used By:**
- `_resolve_player_ids()` in `tools/fantasy/info.py`
- `get_player_info()` in `tools/player/info.py`
- `get_players_by_sleeper_id()` in `tools/player/info.py`

---

### `mv_player_consistency`

Player consistency metrics showing week-to-week fantasy point variance. Used to identify boom/bust players and assess floor/ceiling profiles.

**Purpose:** Provide pre-computed consistency metrics for player reliability analysis.

**Source Tables:** `vw_advanced_receiving_analytics_weekly`, `vw_advanced_passing_analytics_weekly`, `vw_advanced_rushing_analytics_weekly`

**Refresh Schedule:** Weekly on Tuesday at 7:00 AM UTC via pg_cron (`refresh-mv-player-consistency`)

**Refresh Command:**
```sql
SET statement_timeout = '120s';
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_player_consistency;
```

**Columns:**

| Column | Type | Description |
|--------|------|-------------|
| `season` | INTEGER | NFL season year |
| `player_name` | TEXT | Player's full name (unique index with season) |
| `ff_position` | TEXT | Fantasy position (QB/RB/WR/TE) |
| `ff_team` | TEXT | Team abbreviation |
| `games_played` | INTEGER | Games included in calculation (minimum 4) |
| `avg_fp_ppr` | NUMERIC(10,2) | Average weekly fantasy points (PPR) |
| `fp_stddev_ppr` | NUMERIC(10,2) | Standard deviation of weekly points |
| `fp_floor_p10` | NUMERIC(10,2) | 10th percentile weekly score (floor) |
| `fp_ceiling_p90` | NUMERIC(10,2) | 90th percentile weekly score (ceiling) |
| `fp_median_ppr` | NUMERIC(10,2) | Median weekly fantasy points |
| `boom_games_20plus` | INTEGER | Games scoring 20+ PPR points |
| `bust_games_under_5` | INTEGER | Games scoring fewer than 5 PPR points |
| `consistency_coefficient` | NUMERIC(10,3) | Stddev / mean (lower = more consistent) |

**Indexes:**
- `idx_mv_player_consistency_player_season` (UNIQUE) — Player + season (required for CONCURRENTLY refresh)
- `idx_mv_player_consistency_position_season` — Position + season queries

**Interpretation:**
- **Consistency coefficient:** <0.4 = elite, 0.4-0.6 = good, 0.6-0.8 = average, >0.8 = boom/bust
- **Boom ratio:** boom_games_20plus / games_played shows upside frequency
- **Bust ratio:** bust_games_under_5 / games_played shows downside risk
- Lower coefficient = safer floor, better for cash games
- Higher coefficient = more variance, better for tournaments

**Used By:**
- `get_player_consistency()` in `tools/metrics/info.py`
- `compare_players()` enrichment for player comparison context

**Example Query:**
```sql
-- Find most consistent RBs in 2024 (minimum 8 games)
SELECT player_name, ff_team, games_played,
       avg_fp_ppr, fp_floor_p10, fp_ceiling_p90,
       boom_games_20plus, bust_games_under_5, consistency_coefficient
FROM mv_player_consistency
WHERE season = 2024
  AND ff_position = 'RB'
  AND games_played >= 8
ORDER BY consistency_coefficient ASC
LIMIT 20;

-- Compare boom/bust vs consistent WRs
SELECT player_name,
       ROUND(avg_fp_ppr, 1) as avg_ppg,
       fp_floor_p10 as floor,
       fp_ceiling_p90 as ceiling,
       boom_games_20plus as booms,
       bust_games_under_5 as busts,
       consistency_coefficient as coeff,
       CASE
         WHEN consistency_coefficient < 0.4 THEN 'Elite Consistency'
         WHEN consistency_coefficient < 0.6 THEN 'Good Consistency'
         WHEN consistency_coefficient < 0.8 THEN 'Average Consistency'
         ELSE 'Boom/Bust'
       END as profile
FROM mv_player_consistency
WHERE season = 2024 AND ff_position = 'WR' AND games_played >= 8
ORDER BY avg_fp_ppr DESC
LIMIT 50;
```

---
