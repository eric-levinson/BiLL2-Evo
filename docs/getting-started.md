# Getting Started

## Prerequisites

- Node.js 18+, pnpm
- Python 3.10+
- Supabase project (see `database/schema.md`)

## Environment Variables

Each service needs a `.env` file. See `.env.example` in each directory. Never commit `.env` files.

### bill-agent-ui/.env
| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Anthropic API key (for Claude models) |
| `OPENAI_API_KEY` | OpenAI API key (optional, for GPT models) |
| `AI_MODEL_ID` | Model to use (default: `claude-sonnet-4-20250514`) |
| `MCP_SERVER_URL` | fantasy-tools-mcp URL (default: `http://localhost:8000/mcp/`) |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon (public) key |

### fantasy-tools-mcp/.env
| Variable | Description |
|---|---|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_ANON_KEY` | Supabase anon key |

## Running the Services

Start in this order:

### 1. fantasy-tools-mcp (MCP server)
```bash
cd fantasy-tools-mcp
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
python main.py                # Starts on port 8000
```

### 2. bill-agent-ui (Frontend + AI Backend)
```bash
cd bill-agent-ui
pnpm install
pnpm dev                      # Starts on port 3000
```

## Validation

```bash
# TypeScript (bill-agent-ui)
cd bill-agent-ui && pnpm run validate   # lint + format + typecheck

# Python (fantasy-tools-mcp)
cd fantasy-tools-mcp && ruff check . && ruff format --check .

# Or run both from monorepo root:
./validate.sh
```
