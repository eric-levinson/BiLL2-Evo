# CLAUDE.md - BiLL-2 Evo Monorepo

## Project Overview

BiLL-2 Evo is an AI-powered fantasy football analytics platform. It uses a multi-agent AI system to provide advanced NFL stats, Sleeper league management, dynasty rankings, and web research — all accessible through a chat UI or Discord bot.

The monorepo contains three services:

1. **bill-agent-ui** — Next.js 15 chat frontend (TypeScript)
2. **bill-agno** — AI agent orchestration backend (Python / Agno framework)
3. **fantasy-tools-mcp** — MCP tool server with ~40 fantasy football tools (Python / FastMCP)

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│  bill-agent-ui  │────>│    bill-agno      │────>│  fantasy-tools-mcp  │
│  (Next.js)      │     │  (Agno/FastAPI)   │     │  (FastMCP)          │
│  Port 3000      │     │  Port 7777        │     │  Port 8000          │
└─────────────────┘     └────────┬─────────-┘     └──────────┬──────────┘
                                 │                            │
                                 │    ┌───────────────┐       │
                                 └───>│   Supabase     │<─────┘
                                      │  (PostgreSQL)  │
                                      └───────────────┘
```

**Data flow:** UI sends chat messages to bill-agno via API proxy. bill-agno's Supervisor agent delegates to specialized agents (Web, Analytics, Fantasy, League). Those agents call fantasy-tools-mcp via MCP protocol to query Supabase for NFL data.

## Running the Services

Start in this order:

### 1. fantasy-tools-mcp (MCP server)
```bash
cd fantasy-tools-mcp
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
python main.py                # Starts on port 8000
```

### 2. bill-agno (Agent backend)
```bash
cd bill-agno
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
pip install agno openai phoenix[otel] python-dotenv httpx crawl4ai google-search-results duckduckgo-search newspaper4k
python team_playground.py     # Starts Agno Playground on port 7777
```

### 3. bill-agent-ui (Frontend)
```bash
cd bill-agent-ui
pnpm install
pnpm dev                      # Starts on port 3000
```

## Environment Variables

Each service needs a `.env` file. See `.env.example` in each directory. Never commit `.env` files.

### bill-agent-ui/.env
| Variable | Description |
|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon (public) key |
| `PLAYGROUND_API_URL` | bill-agno backend URL (default: `http://localhost:7777`) |

### bill-agno/.env
| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | OpenAI API key |
| `db_url` | Supabase PostgreSQL connection string (used for agent memory + storage) |
| `MCP_SERVER_URL` | fantasy-tools-mcp URL (default: `http://localhost:8000/mcp/`) |
| `PHOENIX_COLLECTOR_ENDPOINT` | Phoenix OTEL tracing endpoint (default: `http://localhost:6006`) |
| `GOOGLE_API_KEY` | Google Search API key (for Web Agent) |
| `DISCORD_BOT_TOKEN` | Discord bot token (only needed for Discord bot mode) |
| `AGNO_API_KEY` | Agno platform key (optional, for monitoring) |
| `USE_AI_SUMMARIZER` | Enable AI summarization of crawled pages (`TRUE`/`FALSE`) |
| `SUMMARIZER_MODEL_ID` | Model for summarization (default: `gpt-5-nano`) |

### fantasy-tools-mcp/.env
| Variable | Description |
|---|---|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_ANON_KEY` | Supabase anon key |

## Key Source Files

### bill-agent-ui (Next.js 15 / TypeScript)
- `src/app/` — Next.js App Router pages and API routes
- `src/components/playground/` — Chat UI components (ChatArea, Sidebar, Sessions)
- `src/api/playground.ts` — API client for Agno Playground backend
- `src/api/routes.ts` — API route definitions
- `src/store.ts` — Zustand state store
- `src/lib/supabase/client.ts` — Browser Supabase client
- `src/lib/supabase/server.ts` — Server Supabase client (SSR)
- `src/hooks/useAIStreamHandler.tsx` — Core streaming response handler
- `middleware.ts` — Next.js middleware (Supabase auth session refresh)

### bill-agno (Python / Agno)
- `team_playground.py` — **Primary entry point**. Defines the 4-agent team and runs the Agno Playground server
- `gridiron_toolkit/info.py` — `GridironTools` class: custom Agno Toolkit wrapping remote MCP tools via MCPTools
- `gridiron_toolkit/__init__.py` — Package init
- `helpers/crawl_helpers.py` — `SummarizingCrawl4aiTools` wrapper (summarizes web crawl results before passing to agent)
- `tests/` — Test files for crawl helpers
- `_archive/` — Archived entry point variants (bill_api.py, bill_agui.py, discord_team.py)

### fantasy-tools-mcp (Python / FastMCP)
- `main.py` — FastMCP server entry point (port 8000)
- `tools/registry.py` — Central tool registration (calls all sub-module registries)
- `tools/player/info.py` — Player lookup tools (by name, by Sleeper ID)
- `tools/metrics/info.py` — Advanced stats tools (receiving, passing, rushing, defense — season + weekly)
- `tools/metrics/registry.py` — Metrics tool + resource registration
- `tools/fantasy/info.py` — Sleeper API tools (leagues, rosters, matchups, transactions, drafts, trending)
- `tools/fantasy/registry.py` — Fantasy tool registration
- `tools/league/info.py` — Game-level stats tools (offensive/defensive player game stats)
- `tools/league/registry.py` — League tool registration
- `tools/ranks/info.py` — Fantasy ranking tools
- `tools/dictionary/info.py` — Data dictionary tools
- `tools/fantasy/sleeper_wrapper/` — Sleeper API client library
- `docs/metrics_catalog.py` — Full metrics definitions
- `docs/game_stats_catalog.py` — Game stats field definitions
- `docs/agent-prompts.md` — Reference agent prompts

## Agent Architecture (bill-agno)

The system uses Agno's Team in "coordinate" mode. A Supervisor agent receives user messages and delegates to specialized agents:

| Agent | Model | Role | Tools |
|---|---|---|---|
| **Supervisor** | gpt-5-mini | Routes requests, synthesizes results | `get_player_info_tool` via GridironTools |
| **Web Search Agent** | gpt-5-mini | Google Search + web crawling | GoogleSearchTools, SummarizingCrawl4aiTools |
| **Analytics Agent** | gpt-4.1-mini | Advanced NFL stats (season + weekly) | GridironTools (10 stats tools + metadata) |
| **Fantasy Agent** | gpt-4.1-mini | Sleeper league data | GridironTools (14 Sleeper + ranking tools) |
| **League Agent** | gpt-4.1-mini | Game-level stats | GridironTools (3 game stats tools) |

All agents connect to fantasy-tools-mcp via `GridironTools`, which wraps Agno's `MCPTools` to call the remote MCP server.

The Supervisor team has:
- **Memory**: PostgresMemoryDb (persisted agent memory across sessions)
- **Storage**: PostgresStorage (session state persistence)
- **History**: Last 3 runs injected into context

## Supabase Database

**Project**: "Advanced Fantasy Insights" (ID: `leghrjgcasbtrbnhhuuz`, region: us-east-1)

### Table Groups (~90 tables in `public` schema)

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

### App-Specific Tables
- `leagues`, `matchups`, `rosters`, `users` — Sleeper league data cache
- `platform_users` — App user accounts
- `player_insights`, `player_metrics_weekly`, `player_projection` — Derived analytics
- `memory` — Agent memory (Agno PostgresMemoryDb)
- `session_storage` — Session state (Agno PostgresStorage)

## MCP Tools Reference

The fantasy-tools-mcp server exposes these tool categories:

### Player Tools
- `get_player_info_tool` — Lookup player by name (returns name, team, position, height, weight, age, IDs)
- `get_players_by_sleeper_id_tool` — Lookup players by Sleeper IDs

### Advanced Stats Tools (query `vw_advanced_*` views)
- `get_advanced_receiving_stats` / `_weekly` — Receiving analytics
- `get_advanced_passing_stats` / `_weekly` — Passing analytics
- `get_advanced_rushing_stats` / `_weekly` — Rushing analytics
- `get_advanced_defense_stats` / `_weekly` — Defensive analytics
- `get_metrics_metadata` — Returns metric definitions by category

### Game Stats Tools
- `get_offensive_players_game_stats` — Per-game offensive stats
- `get_defensive_players_game_stats` — Per-game defensive stats
- `get_stats_metadata` — Game stats field definitions

### Sleeper API Tools
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

### Ranking Tools
- `get_fantasy_rank_page_types` — Available ranking categories
- `get_fantasy_ranks` — Dynasty/redraft rankings with filters

### Dictionary Tools
- `get_dictionary_info` — Data field definitions

### MCP Resources (served as `metrics://` URIs)
- `metrics://catalog` — Complete metrics catalog
- `metrics://receiving`, `metrics://passing`, `metrics://rushing`, `metrics://defense`

## Coding Conventions

### Python (bill-agno, fantasy-tools-mcp)
- Python 3.10+
- Use `python-dotenv` for env loading at module top: `load_dotenv()`
- Agno framework patterns: `Agent`, `Team`, `Toolkit`, `Memory`
- Tools registered via FastMCP `@mcp.tool()` decorator in registry files
- Each tool module follows the pattern: `info.py` (business logic) + `registry.py` (MCP registration)
- Use `os.getenv()` for environment variables with sensible defaults
- Async patterns with `asyncio` for MCP tool calls
- Type hints on function signatures

### TypeScript (bill-agent-ui)
- Next.js 15 with App Router (`src/app/`)
- React 18, TypeScript 5, strict mode
- **pnpm** package manager (not npm or yarn)
- Zustand for client state management
- Tailwind CSS + shadcn/ui + Radix UI for components
- Supabase SSR pattern (`@supabase/ssr`) for auth
- API proxy pattern: UI -> Next.js API route -> bill-agno backend
- Path alias: `@/*` maps to `./src/*`
- Validation: `pnpm run validate` (lint + format + typecheck)

### General
- No secrets in code — always use env vars
- `.env.example` files document required variables
- Each service runs independently and communicates via HTTP

## Known Technical Debt
- `_archive/` contains 3 entry point variants (bill_api.py, bill_agui.py, discord_team.py) that duplicate `build_team()` from team_playground.py — should be refactored to share a common team builder
- Agent model versions (gpt-4.1-mini, gpt-5-mini, gpt-5-nano) should be configurable via env vars
- No requirements.txt or pyproject.toml for bill-agno (dependencies installed manually)
- No Docker containerization
- No CI/CD pipeline at monorepo level (bill-agent-ui has a standalone validate workflow)
- `bill-agent-ui/package-lock.json` coexists with `pnpm-lock.yaml` (should remove package-lock.json)
