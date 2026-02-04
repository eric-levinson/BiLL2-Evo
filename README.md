# BiLL-2 Evo

AI-powered fantasy football analytics platform with multi-agent orchestration.

## Services

| Service | Stack | Port | Description |
|---|---|---|---|
| **bill-agent-ui** | Next.js 15 / TypeScript | 3000 | Chat UI frontend |
| **bill-agno** | Python / Agno | 7777 | AI agent backend (4 agents + Supervisor) |
| **fantasy-tools-mcp** | Python / FastMCP | 8000 | MCP server with ~40 fantasy football tools |

## Architecture

```
bill-agent-ui (3000) -> bill-agno (7777) -> fantasy-tools-mcp (8000) -> Supabase (PostgreSQL)
```

## Quick Start

1. Copy `.env.example` to `.env` in each service directory and fill in your keys
2. Start services in order:

```bash
# Terminal 1: MCP server
cd fantasy-tools-mcp && python main.py

# Terminal 2: Agent backend
cd bill-agno && python team_playground.py

# Terminal 3: Frontend
cd bill-agent-ui && pnpm install && pnpm dev
```

3. Open http://localhost:3000

## Documentation

See [CLAUDE.md](./CLAUDE.md) for detailed architecture, file maps, agent design, database schema, and coding conventions.
