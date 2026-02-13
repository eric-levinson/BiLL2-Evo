# CLAUDE.md - BiLL-2 Evo Monorepo

## Project Overview

BiLL-2 Evo is an AI-powered fantasy football analytics platform. Single AI agent with ~40 MCP tools for NFL stats, Sleeper league management, dynasty rankings, and web research — all through a chat UI.

## Services

| Service | Stack | Port | Description |
|---------|-------|------|-------------|
| `bill-agent-ui/` | Next.js 15, TypeScript, Vercel AI SDK 6 | 3000 | Chat frontend + AI backend |
| `fantasy-tools-mcp/` | Python 3.10+, FastMCP | 8000 | MCP tool server (~40 tools) |
| `_archived-services/bill-agno/` | Python, Agno | — | Legacy agent backend (archived) |

## Quick Start

```bash
# 1. MCP server
cd fantasy-tools-mcp && python main.py

# 2. Frontend + AI backend
cd bill-agent-ui && pnpm install && pnpm dev
```

See `docs/getting-started.md` for full setup (venv, env vars, etc.)

## Documentation Map

| Doc | When to read |
|-----|-------------|
| `docs/architecture.md` | Understanding system design, data flow, or design decisions |
| `docs/getting-started.md` | Setting up the project, env vars, running services |
| `docs/bill-agent-ui/conventions.md` | Working on the Next.js frontend or AI backend |
| `docs/bill-agent-ui/layers.md` | Understanding or modifying import boundaries |
| `docs/fantasy-tools-mcp/conventions.md` | Working on Python MCP tools |
| `docs/fantasy-tools-mcp/tools-catalog.md` | Understanding available MCP tools |
| `docs/fantasy-tools-mcp/adding-tools.md` | Adding a new MCP tool (template included) |
| `docs/database/schema.md` | Understanding Supabase tables and views |
| `docs/technical-debt.md` | Known issues and improvement opportunities |

## Critical Invariants

These rules must never be violated:

1. **pnpm only** — Use `pnpm`, never npm or yarn, in `bill-agent-ui/`
2. **No secrets in code** — All credentials via env vars, never committed
3. **Python 3.10+** — Required for `fantasy-tools-mcp/`
4. **Tool module pattern** — Every MCP tool uses `info.py` (logic) + `registry.py` (MCP registration)
5. **Validate before committing** — Run `pnpm run validate` in `bill-agent-ui/`, `ruff check .` in `fantasy-tools-mcp/`
6. **Layer boundaries** — `@/lib/` cannot import from `@/hooks/`, `@/components/`, or `@/app/`. See `docs/bill-agent-ui/layers.md`

## Key Files

### bill-agent-ui
- `src/app/api/chat/route.ts` — Core AI backend (ToolLoopAgent + MCP connection pool)
- `src/lib/ai/` — AI orchestration (model factory, tool filtering, circuit breaker, connection pool)
- `src/lib/supabase/` — Database clients and session/preference persistence
- `src/components/playground/` — Chat UI components

### fantasy-tools-mcp
- `main.py` — FastMCP server entry point
- `tools/registry.py` — Central tool registration
- `helpers/query_utils.py` — Shared Supabase query helpers
- `helpers/retry_utils.py` — Retry decorators (sync + async)
