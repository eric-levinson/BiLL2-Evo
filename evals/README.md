# BiLL2 Model Evaluation Framework

Structured eval harness for benchmarking LLM providers against real BiLL2 fantasy football prompts. Built on [Promptfoo](https://github.com/promptfoo/promptfoo).

## Quick Start

```bash
# From bill-agent-ui (where promptfoo is installed)
cd BiLL2-OG-Monorepo/bill-agent-ui

# Validate config without calling APIs
npx promptfoo eval -c ../evals/promptfooconfig.yaml --dry-run

# Run Google + OpenAI only (recommended — avoids Anthropic rate limits)
npx promptfoo eval -c ../evals/promptfooconfig-no-anthropic.yaml

# Run full evaluation (all 7 models x 30 prompts = 210 test cases)
npx promptfoo eval -c ../evals/promptfooconfig.yaml

# View results in browser
npx promptfoo view
```

## Prerequisites

API keys must be set in `bill-agent-ui/.env`:

```
ANTHROPIC_API_KEY=sk-ant-...   # Optional for no-anthropic config
OPENAI_API_KEY=sk-...
GOOGLE_GENERATIVE_AI_API_KEY=AI...
```

The eval framework calls model APIs directly (no running app server needed).

## Models Evaluated

| Provider  | Model                          | Label             | Config          |
|-----------|--------------------------------|-------------------|-----------------|
| Anthropic | claude-sonnet-4-5-20250929     | Claude Sonnet 4.5 | Full only       |
| Anthropic | claude-haiku-4-5-20251001      | Claude Haiku 4.5  | Full only       |
| Anthropic | claude-opus-4-5-20251101       | Claude Opus 4.5   | Full only       |
| Google    | gemini-3-flash-preview         | Gemini 3 Flash    | Both configs    |
| Google    | gemini-3-pro-preview           | Gemini 3 Pro      | Both configs    |
| OpenAI    | gpt-5-mini                     | GPT-5 Mini        | Both configs    |
| OpenAI    | gpt-5.1                        | GPT-5.1           | Both configs    |

## Cost Expectations

| Config               | Models | Test Cases | Estimated Cost |
|----------------------|--------|------------|---------------|
| No-Anthropic (recommended) | 4 | 120 | ~$1-2 per run |
| Full (all 7 models)  | 7      | 210        | ~$3-5 per run  |

Mock data adds ~2-3k tokens per multi-turn test. Total token usage per run: ~960k tokens (4-model) to ~1.7M tokens (7-model).

## Test Categories (30 prompts)

### Tool Selection (10 prompts) — Single-turn
Tests that models select the correct MCP tools based on user intent. Validates enriched tool descriptions and BM25 synonym routing.

- Player lookup → `get_player_info_tool`
- Player comparison → `compare_players`
- Trending adds → `get_sleeper_trending_players`
- Trade evaluation → `get_trade_context`
- Dynasty rankings → `get_fantasy_ranks`
- Consistency query → `get_player_consistency`
- Sell high intent → trade tools via synonym routing

**Scorer:** `scorers/tool-accuracy.js` — parses `[TOOL_CALLS]` output, compares against expected tools.

### Response Quality (7 prompts) — Multi-turn with mock data
Tests analysis depth, output template compliance, fantasy knowledge usage, and scoring format awareness. Each test injects mock tool output so models receive data and can demonstrate analysis capabilities.

- Dynasty trade analysis (PPR, Superflex, TEP formats) + mock comparison/profile data
- Start/sit recommendations + mock receiving stats
- Player profiles + mock profile data
- Waiver wire recommendations + mock trending data

**Scorer:** `llm-rubric` with domain-specific criteria, judged by GPT-5.1.

### Step Efficiency (5 prompts) — Single-turn
Tests that composite tools (`get_trade_context`, `compare_players`) reduce step count vs multi-tool workflows.

- Simple lookup: 1-2 steps
- Player comparison: 1-3 steps (compare_players)
- Trade evaluation: 1-4 steps (get_trade_context)
- Complex multi-player trade: 1-6 steps

**Scorer:** `scorers/step-efficiency.js` — counts tool calls, validates against expected range.

### Chart Generation (4 prompts) — Multi-turn with mock data
Tests valid chart JSON output, proper type selection, and scale separation. Each test injects mock statistical data so models have real numbers to chart.

- Bar chart for category comparison + mock dynasty rankings
- Scale separation (yards vs targets) + mock receiving stats
- Line chart for time series + mock player profile
- Rankings visualization + mock dynasty data

**Scorer:** `scorers/chart-validity.js` — validates JSON structure, required fields, and scale compatibility.

### Instruction Following (4 prompts) — Multi-turn with mock data
Tests compliance with system prompt protocols, output templates, and user preferences. Each test injects mock context so models can demonstrate template compliance.

- Dynasty trade protocol adherence + mock trade context
- Start/sit template usage + mock receiving stats
- Conciseness when requested + mock trending data
- Consistency metrics usage + mock consistency data

**Scorer:** `llm-rubric` + `icontains` assertions.

## Multi-Turn Mock Data

BiLL2 is a multi-turn agentic system where the AI calls tools and receives data before responding. To simulate this realistically, tests in Response Quality, Chart Generation, and Instruction Following categories use **mock tool output** injected as multi-turn conversation history.

### How It Works

1. Test defines a `tool_results` var pointing to a mock data JSON file
2. The provider reads `context.vars.tool_results` and parses the JSON
3. Messages are built with proper tool_use/tool_result pairs per API:
   - **Anthropic:** `tool_use` (assistant) + `tool_result` (user) blocks
   - **OpenAI:** `tool_calls` (assistant) + `tool` role messages
   - **Google:** `functionCall` (model) + `functionResponse` (user) parts
4. Model receives the data as if tools were actually called, then generates analysis

### Mock Data Files

Stored in `datasets/mock-data/` as JSON arrays of tool call/result pairs:

```json
[{
  "tool_name": "get_trade_context",
  "tool_input": { "give_player_names": ["CeeDee Lamb"], "receive_player_names": ["Bijan Robinson"] },
  "tool_output": { ... realistic response data ... }
}]
```

| File | Tool Simulated | Used By |
|------|---------------|---------|
| `player-profile-mahomes.json` | `get_player_profile` | Response Quality, Chart Gen |
| `player-comparison-rb.json` | `compare_players` | Response Quality |
| `trade-context-dynasty.json` | `get_trade_context` | Instruction Following |
| `advanced-receiving-stats.json` | `get_advanced_receiving_stats` | Response Quality, Chart Gen, Instruction Following |
| `trending-players.json` | `get_sleeper_trending_players` | Response Quality, Instruction Following |
| `consistency-metrics.json` | `get_player_consistency` | Response Quality, Instruction Following |
| `fantasy-ranks-rb.json` | `get_fantasy_ranks` | Response Quality, Chart Gen |

## Architecture

```
evals/
  promptfooconfig.yaml              # Full config: 7 providers, 5 test suites
  promptfooconfig-no-anthropic.yaml # Google + OpenAI only (recommended for dev)
  providers/
    bill2-chat.js            # Custom provider — multi-turn + single-turn support
  prompts/
    system.txt               # BiLL2 system prompt (static copy for eval)
  tools/
    definitions.json         # 18 MCP tool definitions in neutral format
  datasets/
    tool-selection.yaml      # 10 tool routing tests (single-turn)
    response-quality.yaml    # 7 analysis quality tests (multi-turn)
    step-efficiency.yaml     # 5 step count tests (single-turn)
    chart-generation.yaml    # 4 chart validity tests (multi-turn)
    instruction-following.yaml  # 4 protocol compliance tests (multi-turn)
    mock-data/               # Reusable mock tool responses (JSON)
  scorers/
    tool-accuracy.js         # Custom: tool selection grading
    step-efficiency.js       # Custom: step count grading
    chart-validity.js        # Custom: chart JSON validation
  results/
    latest.json              # Most recent eval output
```

## Custom Provider

The `bill2-chat.js` provider:

1. Loads API keys from `bill-agent-ui/.env`
2. Loads system prompt from `prompts/system.txt`
3. Loads 18 MCP tool definitions from `tools/definitions.json`
4. Checks for `tool_results` in test vars for multi-turn message building
5. Calls model APIs directly via HTTP (Anthropic, OpenAI, Google)
6. Builds proper multi-turn messages per API format (tool_use/tool_result pairs)
7. Returns structured output with `[TOOL_CALLS]` and `[RESPONSE]` sections

No running app server, MCP server, or Supabase needed for evals.

## Rate Limit Handling

The provider includes hardened rate limit handling:

- **Exponential backoff:** 10s → 20s → 40s → 60s → 60s (capped)
- **Retry-After header:** Respected when present (overrides backoff)
- **Provider identification:** Log messages include provider name (e.g., `[Anthropic/claude-sonnet-4-5]`)
- **Max retries:** 5 attempts before failing the individual test case (not the whole eval)
- **Per-provider delays:** Anthropic providers have `delay: 10000` (10s between requests)

## Running Subsets

```bash
# Run only tool selection tests
npx promptfoo eval -c ../evals/promptfooconfig-no-anthropic.yaml --filter-description "tool"

# Run only against Google models
npx promptfoo eval -c ../evals/promptfooconfig-no-anthropic.yaml -p "Gemini"

# Run with specific test file
npx promptfoo eval -c ../evals/promptfooconfig-no-anthropic.yaml --tests ../evals/datasets/response-quality.yaml
```

## Interpreting Results

After running `npx promptfoo view`:

- **Tool Selection Accuracy**: % of prompts where the correct tool was selected
- **Response Quality**: 0-5 LLM rubric scores for analysis depth (should be >0 now with mock data)
- **Step Efficiency**: % of prompts within expected step count range
- **Chart Validity**: % of prompts with valid, well-structured chart JSON
- **Instruction Following**: % compliance with system prompt protocols

Look for:
- Models that consistently select wrong tools (poor tool description understanding)
- Models that waste steps on simple queries (not using composite tools)
- Models that mix chart scales (ignoring visualization guidelines)
- Models that skip confidence levels or output templates
- Response Quality/Chart/Instruction scores of 0% indicate mock data isn't reaching the model

## Keeping Prompts in Sync

The system prompt (`prompts/system.txt`) is a static copy of `billSystemPrompt.ts`. When the system prompt changes, update this file to match. Key sections:

- `<identity>` — Agent identity
- `<capabilities>` — What tools are available
- `<guidelines>` — Tool usage rules
- `<protocols>` — Start/sit, dynasty trade, waiver wire workflows
- `<fantasy_knowledge>` — Age curves, scoring format adjustments, positional scarcity
- `<output_templates>` — Response structure templates
- `<visualization>` — Chart JSON format and scale separation rules
