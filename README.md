# BiLL-2 Evo

AI-powered fantasy football analytics platform with a single AI agent and ~40 MCP tools.

## Services

| Service | Stack | Port | Description |
|---|---|---|---|
| **bill-agent-ui** | Next.js 15 / TypeScript | 3000 | Chat UI frontend + AI backend (Vercel AI SDK 6) |
| **fantasy-tools-mcp** | Python / FastMCP | 8000 | MCP server with ~40 fantasy football tools |

## Architecture

```
bill-agent-ui (3000) -> fantasy-tools-mcp (8000) -> Supabase (PostgreSQL)
                │
         Vercel AI SDK 6
     (Claude agent + MCP tools)
```

## Quick Start

1. Copy `.env.example` to `.env` in each service directory and fill in your keys
2. Start services in order:

```bash
# Terminal 1: MCP server
cd fantasy-tools-mcp && python main.py

# Terminal 2: Frontend + AI Backend
cd bill-agent-ui && pnpm install && pnpm dev
```

3. Open http://localhost:3000

## Documentation

See [CLAUDE.md](./CLAUDE.md) for detailed architecture, file maps, agent design, database schema, and coding conventions.
