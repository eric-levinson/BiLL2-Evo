# bill-agent-ui Conventions

## Stack
- Next.js 15 with App Router (`src/app/`)
- React 18, TypeScript 5, strict mode
- **pnpm** package manager (not npm or yarn)
- Vercel AI SDK 6 for agent orchestration (`ai`, `@ai-sdk/anthropic`, `@ai-sdk/mcp`)
- Zustand for client state management
- Tailwind CSS + shadcn/ui + Radix UI for components
- Supabase SSR pattern (`@supabase/ssr`) for auth

## Key Patterns
- `useChat()` hook for streaming chat UI
- `ToolLoopAgent` + `createAgentUIStreamResponse` for the agent backend
- Path alias: `@/*` maps to `./src/*`
- Validation: `pnpm run validate` (lint + format + typecheck)

## Key Source Files
- `src/app/api/chat/route.ts` — Core AI backend (ToolLoopAgent + MCP client)
- `src/components/playground/` — Chat UI components (ChatArea, Sidebar, Sessions)
- `src/store.ts` — Zustand state store
- `src/lib/ai/` — AI orchestration (model factory, tool filtering, circuit breaker, connection pool)
- `src/lib/supabase/` — Database clients (browser + server)
- `src/lib/utils/` — Message filtering and deduplication
- `middleware.ts` — Supabase auth session refresh

## Coding Rules
- No secrets in code — always use env vars
- Run `pnpm run validate` before committing
- Use `@/` path alias for all internal imports
- See `layers.md` for import boundary rules
