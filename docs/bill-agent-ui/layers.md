# bill-agent-ui Architectural Layers

## Layer Hierarchy

Code can only depend "downward" through these layers:

```
@/app/          (pages, API routes — top level, can import anything)
   ↓
@/components/   (React components — can use hooks, lib, types)
   ↓
@/hooks/        (React hooks — can use lib, types)
   ↓
@/lib/          (utilities, services — can use types)
   ↓
@/types/        (TypeScript types — no internal imports)
```

## Import Rules (enforced by ESLint)

| Module | Can import from | Cannot import from |
|--------|----------------|-------------------|
| `@/types/` | nothing internal | `@/lib/`, `@/hooks/`, `@/components/`, `@/app/` |
| `@/lib/` | `@/types/` | `@/hooks/`, `@/components/`, `@/app/` |
| `@/hooks/` | `@/types/`, `@/lib/` | `@/components/`, `@/app/` |
| `@/components/` | `@/types/`, `@/lib/`, `@/hooks/` | `@/app/` |
| `@/app/` | everything | (no restrictions) |

## Sub-module Boundaries within `@/lib/`

| Module | Purpose | Independence |
|--------|---------|-------------|
| `@/lib/ai/` | AI orchestration, model factory, tool filtering | Should NOT import from `@/lib/supabase/` |
| `@/lib/supabase/` | Database access, sessions, preferences | Should NOT import from `@/lib/ai/` |
| `@/lib/utils/` | Pure utility functions | Should NOT import from `@/lib/ai/` or `@/lib/supabase/` |

The API route (`src/app/api/chat/route.ts`) is the composition root that wires these independent modules together.
