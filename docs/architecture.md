# Architecture

## System Diagram

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

## Data Flow

UI sends chat messages to `/api/chat`. The Vercel AI SDK creates a single Claude agent (or GPT/Gemini — provider-agnostic) that calls fantasy-tools-mcp via MCP protocol to query Supabase for NFL data. Responses stream back to the UI via the `useChat()` hook.

## Key Design Decisions

### Single Agent, Not Multi-Agent Team
The previous architecture used a 4-agent team (Web, Analytics, Fantasy, League + Supervisor). This caused:
- 3-4 LLM inference calls per query (3-6s latency)
- 50-70% of context wasted on duplicated instructions and history injection
- 5 separate MCP connections to the same server
- Shared memory with cross-contamination between agents

The single agent approach with Tool Search solves all of these.

### Provider-Agnostic
Swap Claude/GPT/Gemini with one line change via Vercel AI SDK. Model ID configurable via `AI_MODEL_ID` env var.

### No Separate Python Backend
The AI agent runs in a Next.js API route, eliminating a whole service. The Python MCP server only serves tools/data.

## AI Agent Details

- **Model**: Claude Sonnet 4 (default, configurable via `AI_MODEL_ID` env var)
- **Provider**: Anthropic (swappable to OpenAI, Google — one line change)
- **Tools**: ~40 MCP tools from fantasy-tools-mcp, loaded via `@ai-sdk/mcp`
- **Tool Search**: Anthropic's Tool Search loads only relevant tools per query (85% token reduction)
- **Streaming**: Built-in via `useChat()` hook + `createAgentUIStreamResponse`
- **Memory**: Chat persistence via Supabase (JSONB messages in `chat_sessions` table)
- **Resilience**: MCP connection pool + circuit breaker + exponential backoff retry
