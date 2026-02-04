# CLAUDE.md - BiLL-2 Evo Monorepo

## Project Overview

BiLL-2 Evo is an AI-powered fantasy football analytics platform. It uses a single AI agent with ~40 MCP tools to provide advanced NFL stats, Sleeper league management, dynasty rankings, and web research — all accessible through a chat UI.

The monorepo contains two active services:

1. **bill-agent-ui** — Next.js 15 chat frontend + AI backend (TypeScript, Vercel AI SDK 6)
2. **fantasy-tools-mcp** — MCP tool server with ~40 fantasy football tools (Python / FastMCP)

Legacy service (archived, not actively used):
3. **bill-agno** — Old Python/Agno agent backend (being replaced by Vercel AI SDK in bill-agent-ui)

## Architecture

```
┌──────────────────────────────┐
│       bill-agent-ui          │
│       (Next.js 15)           │
│                              │
│  /api/chat ←── useChat()     │
│      │         (streaming)   │
│      ▼                       │
│  Vercel AI SDK 6             │
│  ┌────────────────┐          │
│  │ Claude / GPT / │          │
│  │ Gemini (single │          │
│  │ agent + tools) │          │
│  └───────┬────────┘          │
│          │                   │
└──────────┼───────────────────┘
           │ MCP (Streamable HTTP)
           ▼
┌─────────────────────┐
│  fantasy-tools-mcp  │
│  (FastMCP, Python)  │
│  Port 8000          │
│  ~40 tools          │
└─────────┬───────────┘
          │
          ▼
┌─────────────────┐
│    Supabase     │
│  (PostgreSQL)   │
│  ~90 NFL tables │
└─────────────────┘
```

**Data flow:** UI sends chat messages to `/api/chat`. The Vercel AI SDK creates a single Claude agent (or GPT/Gemini — provider-agnostic) that calls fantasy-tools-mcp via MCP protocol to query Supabase for NFL data. Responses stream back to the UI via the `useChat()` hook.

**Key design decisions:**
- **Single agent, not a team** — One inference call per query instead of 3-4. Tool Search dynamically loads only needed tools (85% token reduction).
- **Provider-agnostic** — Swap Claude/GPT/Gemini with one line change via Vercel AI SDK.
- **No separate Python backend** — The AI agent runs in a Next.js API route, eliminating a whole service.

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

### 2. bill-agent-ui (Frontend + AI Backend)
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
| `ANTHROPIC_API_KEY` | Anthropic API key (for Claude models) |
| `OPENAI_API_KEY` | OpenAI API key (optional, for GPT models) |
| `AI_MODEL_ID` | Model to use (default: `claude-sonnet-4-20250514`). Supports any Vercel AI SDK provider model. |
| `MCP_SERVER_URL` | fantasy-tools-mcp URL (default: `http://localhost:8000/mcp/`) |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon (public) key |

### fantasy-tools-mcp/.env
| Variable | Description |
|---|---|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_ANON_KEY` | Supabase anon key |

## Key Source Files

### bill-agent-ui (Next.js 15 / TypeScript / Vercel AI SDK 6)
- `src/app/api/chat/route.ts` — **Core AI backend**. Single API route with ToolLoopAgent + MCP client. Handles streaming, tool calling, and chat persistence.
- `src/app/` — Next.js App Router pages and API routes
- `src/components/playground/` — Chat UI components (ChatArea, Sidebar, Sessions)
- `src/store.ts` — Zustand state store
- `src/lib/supabase/client.ts` — Browser Supabase client
- `src/lib/supabase/server.ts` — Server Supabase client (SSR)
- `middleware.ts` — Next.js middleware (Supabase auth session refresh)

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

### bill-agno (Python / Agno) — ARCHIVED
- `team_playground.py` — Old Agno Playground entry point (4-agent team). Being replaced by AI SDK route.
- `gridiron_toolkit/info.py` — Old GridironTools MCP wrapper. No longer needed.
- `_archive/` — Archived entry point variants (bill_api.py, bill_agui.py, discord_team.py)

## AI Agent Architecture

The system uses a **single AI agent** powered by the Vercel AI SDK 6 `ToolLoopAgent`:

- **Model**: Claude Sonnet 4 (default, configurable via `AI_MODEL_ID` env var)
- **Provider**: Anthropic (swappable to OpenAI, Google, etc. — one line change)
- **Tools**: ~40 MCP tools from fantasy-tools-mcp, loaded via `@ai-sdk/mcp`
- **Tool Search**: Anthropic's Tool Search feature loads only relevant tools per query (85% token reduction)
- **Streaming**: Built-in via `useChat()` hook + `createAgentUIStreamResponse`
- **Memory**: Chat persistence via Supabase (JSONB messages in `chat_sessions` table)

### Why Single Agent (Not Multi-Agent Team)

The previous architecture used a 4-agent team (Web, Analytics, Fantasy, League + Supervisor). This caused:
- 3-4 LLM inference calls per query (3-6s latency)
- 50-70% of context wasted on duplicated instructions and history injection
- 5 separate MCP connections to the same server
- Shared memory with cross-contamination between agents

The single agent approach with Tool Search solves all of these.

## Supabase Database

**Project**: "Advanced Fantasy Insights" (region: us-east-1, project ID in `.env` files)

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
- `chat_sessions` — Chat persistence (AI SDK messages as JSONB)
- `platform_users` — App user accounts
- `player_insights`, `player_metrics_weekly`, `player_projection` — Derived analytics

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

### Python (fantasy-tools-mcp)
- Python 3.10+
- Use `python-dotenv` for env loading at module top: `load_dotenv()`
- Tools registered via FastMCP `@mcp.tool()` decorator in registry files
- Each tool module follows the pattern: `info.py` (business logic) + `registry.py` (MCP registration)
- Use `os.getenv()` for environment variables with sensible defaults
- Async patterns with `asyncio` for MCP tool calls
- Type hints on function signatures

### TypeScript (bill-agent-ui)
- Next.js 15 with App Router (`src/app/`)
- React 18, TypeScript 5, strict mode
- **pnpm** package manager (not npm or yarn)
- Vercel AI SDK 6 for agent orchestration (`ai`, `@ai-sdk/anthropic`, `@ai-sdk/mcp`)
- `useChat()` hook for streaming chat UI
- `ToolLoopAgent` + `createAgentUIStreamResponse` for the agent backend
- Zustand for client state management
- Tailwind CSS + shadcn/ui + Radix UI for components
- Supabase SSR pattern (`@supabase/ssr`) for auth
- Path alias: `@/*` maps to `./src/*`
- Validation: `pnpm run validate` (lint + format + typecheck)

### General
- No secrets in code — always use env vars
- `.env.example` files document required variables
- Each service runs independently and communicates via HTTP/MCP
- Model IDs configurable via `AI_MODEL_ID` env var

## Known Technical Debt
- bill-agno directory still exists (archived) — can be removed once AI SDK migration is complete
- `bill-agent-ui/package-lock.json` coexists with `pnpm-lock.yaml` (should remove package-lock.json)
- MCP tool responses return too much data (need `columns` parameter, lower default limits)
- No automated test suite for MCP tools or UI components
- No CI/CD pipeline at monorepo level (bill-agent-ui has a standalone validate workflow)
- No Docker containerization
