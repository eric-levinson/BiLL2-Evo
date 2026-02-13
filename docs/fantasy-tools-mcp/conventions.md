# fantasy-tools-mcp Conventions

## Stack
- Python 3.10+
- FastMCP for MCP server
- Supabase Python client for database access
- aiohttp + asyncio for async HTTP calls
- tenacity for retry logic
- ruff for linting and formatting

## Tool Module Pattern

Every tool category follows a strict two-file pattern:

```
tools/{category}/
  info.py       — Business logic and helper functions
  registry.py   — MCP tool registration via @mcp.tool() decorator
```

Central coordination: `tools/registry.py` imports all sub-module registries.

### Adding a New Tool

1. Create `tools/{category}/info.py` with the business logic function
2. Create `tools/{category}/registry.py` that imports from `info.py` and registers with `@mcp.tool()`
3. Import the new registry in `tools/registry.py`
4. See `adding-tools.md` for a complete template

## Key Source Files
- `main.py` — FastMCP server entry point (port 8000)
- `tools/registry.py` — Central tool registration
- `helpers/query_utils.py` — Shared Supabase query helpers
- `helpers/retry_utils.py` — Retry decorators (sync + async)
- `docs/metrics_catalog.py` — Full metrics definitions
- `docs/game_stats_catalog.py` — Game stats field definitions

## Coding Rules
- Use `python-dotenv` for env loading: `load_dotenv()`
- Use `os.getenv()` with sensible defaults
- Type hints on all function signatures
- Run `ruff check .` before committing
- Use `asyncio.gather` for parallel independent API calls (see `helpers/retry_utils.py`)

## Async Patterns

Multiple independent API calls should run in parallel using `asyncio.gather`:

```python
async def _fetch_parallel():
    result1, result2 = await asyncio.gather(
        api_client._call_async(url1),
        api_client._call_async(url2)
    )
    return result1, result2

results = asyncio.run(_fetch_parallel())
```

Key files: `helpers/retry_utils.py` (async_retry_with_backoff), `tools/fantasy/sleeper_wrapper/base_api.py` (_call_async)
