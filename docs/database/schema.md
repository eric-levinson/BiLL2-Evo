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
