# fantasy-tools-mcp

MCP tool server for BiLL-2 Evo, providing ~40 fantasy football tools via FastMCP.

## Overview

This service exposes NFL statistics, fantasy football data, dynasty rankings, and league management tools through the Model Context Protocol (MCP). The AI agent in `bill-agent-ui` connects to this server to answer fantasy football questions with real-time data.

- **Framework**: FastMCP
- **Language**: Python 3.10+
- **Port**: 8000 (HTTP transport)
- **Tools**: ~40 MCP tools across 7 categories
- **Database**: Supabase (PostgreSQL)

## Setup

### Prerequisites

- Python 3.10 or higher
- Supabase account (or access to existing project)

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file with credentials
cp .env.example .env
# Edit .env and add your SUPABASE_URL and SUPABASE_ANON_KEY
```

### Environment Variables

Required in `.env`:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
```

## Running the Server

```bash
python main.py
```

Server runs on `http://0.0.0.0:8000`

## Tool Categories

### Player Tools (`tools/player/`)
Search and retrieve NFL player information, rosters, and profiles.

### Metrics Tools (`tools/metrics/`)
Advanced NFL statistics across passing, rushing, receiving, and defense. Includes seasonal and weekly granularity for volume, efficiency, and situational metrics.

### Ranks Tools (`tools/ranks/`)
Dynasty rankings, trade values, and player valuations for long-term fantasy formats.

### Fantasy Tools (`tools/fantasy/`)
Sleeper league data, rosters, matchups, transactions, and league settings.

### League Tools (`tools/league/`)
League-specific queries, standings, and member information.

### Dictionary Tools (`tools/dictionary/`)
NFL terminology, scoring systems, and fantasy football concept definitions.

### WebSearch Tools (`tools/websearch/`)
External web search for injury reports, news, and real-time updates.

## Tool Module Pattern

Every tool category follows a strict two-file pattern:

```
tools/{category}/
  info.py       — Business logic and helper functions
  registry.py   — MCP tool registration via @mcp.tool() decorator
```

Central coordination happens in `tools/registry.py`, which imports all sub-module registries.

## Adding a New Tool

See [docs/fantasy-tools-mcp/adding-tools.md](../docs/fantasy-tools-mcp/adding-tools.md) for a complete step-by-step guide with code templates.

Quick summary:
1. Create `tools/{category}/info.py` with business logic
2. Create `tools/{category}/registry.py` with `@mcp.tool()` decorator
3. Import the new registry in `tools/registry.py`
4. Run `ruff check .` to validate

## Key Files

- `main.py` — FastMCP server entry point
- `tools/registry.py` — Central tool registration
- `helpers/query_utils.py` — Shared Supabase query helpers
- `helpers/retry_utils.py` — Retry decorators (sync + async)
- `docs/metrics_catalog.py` — Full metrics definitions
- `docs/game_stats_catalog.py` — Game stats field definitions

## Documentation

- [Conventions](../docs/fantasy-tools-mcp/conventions.md) — Coding standards, async patterns, stack details
- [Tools Catalog](../docs/fantasy-tools-mcp/tools-catalog.md) — Complete tool reference with parameters
- [Adding Tools](../docs/fantasy-tools-mcp/adding-tools.md) — New tool template and registration guide
- [Architecture](../docs/architecture.md) — System-level design and data flow

## Development

### Linting and Formatting

```bash
# Check code quality
ruff check .

# Auto-format code
ruff format .
```

### Testing

Run validation before committing:

```bash
ruff check . && ruff format --check .
```

## License

Part of BiLL-2 Evo monorepo.
