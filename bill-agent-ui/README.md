# BiLL-2 Agent UI

A modern chat interface for BiLL-2 Evo, an AI-powered fantasy football analytics platform. Built with Next.js 15, Tailwind CSS, TypeScript, and Vercel AI SDK 6.

## Features

- 💬 **Modern Chat Interface**: Clean design with real-time streaming support
- 🧩 **Tool Calls Support**: Visualizes AI agent tool calls and their results
- 🏈 **Fantasy Football Analytics**: Access to ~40 MCP tools for NFL stats, Sleeper league management, and dynasty rankings
- 🤖 **Single Agent Architecture**: Provider-agnostic AI agent (Claude, GPT, Gemini) with MCP tool integration
- 📊 **Advanced NFL Stats**: Query 90+ Supabase tables with advanced receiving, passing, rushing, and defensive metrics
- 🎨 **Customizable UI**: Built with Tailwind CSS and shadcn/ui components
- 🔐 **Authentication**: Supabase auth with session management

## Architecture

BiLL-2 Agent UI contains both the frontend chat interface and the AI backend:

- **Frontend**: Next.js 15 App Router with React 18 and TypeScript
- **AI Backend**: `/api/chat` route using Vercel AI SDK 6 with `ToolLoopAgent`
- **MCP Integration**: Connects to fantasy-tools-mcp server for NFL data and Sleeper API access
- **Database**: Supabase (PostgreSQL) with 90+ NFL data tables
- **State Management**: Zustand for client state, Supabase for chat persistence

## Getting Started

### Prerequisites

1. **fantasy-tools-mcp server** must be running (see monorepo root for setup)
2. **Supabase project** with NFL data tables configured
3. **API keys** for AI providers (Anthropic, OpenAI, or Google)

### Installation

1. Install dependencies:

```bash
pnpm install
```

2. Set up environment variables:

Copy `.env.example` to `.env` and configure:

```bash
# AI Provider API Keys
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here  # optional

# AI Model Configuration
AI_MODEL_ID=claude-sonnet-4-20250514

# MCP Server
MCP_SERVER_URL=http://localhost:8000/mcp/

# Supabase
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

3. Start the development server:

```bash
pnpm dev
```

4. Open [http://localhost:3000](http://localhost:3000) with your browser.

## MCP Server Connection

The UI connects to the fantasy-tools-mcp server at `http://localhost:8000/mcp/` by default. Make sure the MCP server is running before starting the UI:

```bash
cd ../fantasy-tools-mcp
python main.py
```

## Available Scripts

- `pnpm dev` - Start development server
- `pnpm build` - Build for production
- `pnpm start` - Start production server
- `pnpm lint` - Run ESLint
- `pnpm format` - Format code with Prettier
- `pnpm validate` - Run lint, format check, and type check

## Tech Stack

- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript 5
- **AI SDK**: Vercel AI SDK 6 (`ai`, `@ai-sdk/anthropic`, `@ai-sdk/mcp`)
- **UI Components**: shadcn/ui, Radix UI
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **Database**: Supabase (PostgreSQL)
- **Authentication**: Supabase Auth
- **Package Manager**: pnpm

## Key Files

- `src/app/api/chat/route.ts` - AI backend with ToolLoopAgent + MCP client
- `src/app/` - Next.js App Router pages
- `src/components/playground/` - Chat UI components
- `src/store.ts` - Zustand state store
- `src/lib/supabase/` - Supabase client utilities
- `middleware.ts` - Auth session refresh middleware

## License

This project is part of the BiLL-2 Evo monorepo.
