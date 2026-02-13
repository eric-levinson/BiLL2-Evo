# fantasy-tools-mcp

Python FastMCP server with ~40 fantasy football tools for BiLL-2 Evo.

## Must-Know Rules

- Python 3.10+ required
- Tool module pattern: `info.py` (business logic) + `registry.py` (MCP registration)
- Run `ruff check .` before committing
- Use `os.getenv()` with sensible defaults, never hardcode credentials

## Adding a New Tool

See `../docs/fantasy-tools-mcp/adding-tools.md` for a complete template.

Quick summary:
1. Create `tools/{category}/info.py` with business logic
2. Create `tools/{category}/registry.py` with `@mcp.tool()` registration
3. Import new registry in `tools/registry.py`

## Key Files

- `main.py` — FastMCP server entry point (port 8000)
- `tools/registry.py` — Central tool registration
- `helpers/query_utils.py` — Shared Supabase query helpers
- `helpers/retry_utils.py` — Retry decorators (sync + async with backoff)
- `docs/metrics_catalog.py` — Metrics definitions
- `docs/game_stats_catalog.py` — Game stats definitions

## Docs

- `../docs/fantasy-tools-mcp/conventions.md` — Full conventions reference
- `../docs/fantasy-tools-mcp/tools-catalog.md` — All MCP tools listed
- `../docs/fantasy-tools-mcp/adding-tools.md` — New tool template
- `../docs/architecture.md` — System-level architecture
