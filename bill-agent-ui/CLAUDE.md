# bill-agent-ui

Next.js 15 chat frontend + AI backend for BiLL-2 Evo.

## Must-Know Rules

- **pnpm** package manager — never npm or yarn
- Path alias: `@/*` maps to `./src/*`
- Run `pnpm run validate` before committing (lint + format + typecheck)
- Layer boundaries enforced by ESLint — see `../docs/bill-agent-ui/layers.md`

## Architecture Layers

```
@/app/          → Pages, API routes (can import anything)
@/components/   → React components (can use hooks, lib, types)
@/hooks/        → React hooks (can use lib, types)
@/lib/          → Utilities, services (can use types only)
@/types/        → TypeScript types (no internal imports)
```

Within `@/lib/`, sub-modules are independent:
- `@/lib/ai/` — AI orchestration (do NOT import from `@/lib/supabase/`)
- `@/lib/supabase/` — Database access (do NOT import from `@/lib/ai/`)
- `@/lib/utils/` — Pure utilities (do NOT import from ai or supabase)

The API route (`src/app/api/chat/route.ts`) is the composition root that wires these together.

## Stack

Next.js 15, React 18, TypeScript 5 (strict), Vercel AI SDK 6, Zustand, Tailwind CSS + shadcn/ui, Supabase SSR

## Docs

- `../docs/bill-agent-ui/conventions.md` — Full conventions reference
- `../docs/bill-agent-ui/layers.md` — Import boundary rules
- `../docs/architecture.md` — System-level architecture
