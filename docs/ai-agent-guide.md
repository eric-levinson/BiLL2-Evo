# AI Agent Behavior and Prompt Engineering Guide

This guide explains how BiLL's AI agent works, how to craft effective prompts, and how the system personalizes responses using user preferences.

## Agent System Prompt Structure

The AI agent's behavior is defined in `bill-agent-ui/src/lib/ai/prompts/billSystemPrompt.ts`. The system prompt has three main sections:

### 1. Identity and Context
- Agent identity: "BiLL, an advanced fantasy football analyst powered by AI"
- Current date injection (dynamically generated)
- Season context: The 2025 NFL season is complete, 2026 has not started

### 2. User Context Injection
User preferences and cross-session memory are injected via the `userContext` parameter. This allows the agent to remember:
- Sleeper username and primary league ID
- Connected leagues (multiple fantasy leagues)
- Analysis style preferences (concise vs. detailed)
- Favorite players and teams
- Roster notes and custom reminders

When users mention their Sleeper username or primary league, the agent automatically saves it using `update_sleeper_connection`. Other preferences are saved with `update_user_preference`, `add_connected_league`, or `update_roster_notes`.

**Key Benefit**: Users don't need to repeat their league settings or preferences across sessions. The agent recalls context from previous conversations.

### 3. Behavioral Directives
Guidelines for tool usage, data handling, and response formatting.

## Agent Capabilities

The agent has access to:
- Comprehensive NFL player stats (seasonal and weekly advanced metrics)
- Real-time Sleeper league data (rosters, matchups, transactions, trending players)
- Dynasty and redraft rankings
- Game-level offensive and defensive statistics
- Player information and metrics metadata
- User preference management (cross-session memory)
- Sleeper account connection management

## Tool Usage Guidelines

The system prompt includes 10 core tool usage rules:

1. **Never assume data doesn't exist** — Query tools first; training data may be outdated
2. **Start with `get_player_info_tool`** — Get accurate player IDs and current team info
3. **Use advanced stats tools** — Receiving/passing/rushing/defense tools for deeper insights
4. **Use Sleeper API tools** — For league-specific questions (rosters, matchups)
5. **Fetch latest rankings** — Use `get_fantasy_ranks` for dynasty/redraft valuations
6. **Back up recommendations** — Provide data-driven insights with specific metrics
7. **Check metrics metadata** — Use `get_metrics_metadata` to understand available fields
8. **Fall back to weekly stats** — If seasonal data is missing, check weekly stats tools
9. **Limit tool calls to 4 per question** — Avoid endless retries; tell users what's available
10. **Save user preferences** — Use `update_sleeper_connection` for Sleeper username/league, and preference tools for other settings

## Tool Search Filtering

The AI backend (`src/app/api/chat/route.ts`) uses a dynamic tool filtering system that adapts to user queries:

- **Player stats queries**: Load player, metrics, ranks tools
- **League/roster queries**: Load fantasy, league, Sleeper tools
- **Start/sit analysis**: Load advanced stats tools + league scoring settings
- **Rankings/valuations**: Load ranks and dictionary tools
- **News/injuries**: Load websearch tools

The system uses a `ToolSearchFilter` that maps query patterns to relevant tool categories, reducing latency and improving context efficiency by only loading tools that are likely to be used.

## Multi-Step Query Handling

The agent can chain up to 4 tool calls per question to answer complex queries:

**Example: "Should I trade Justin Jefferson for Travis Kelce?"**

1. Call `get_player_info_tool` for both players (verify IDs, teams)
2. Call `get_advanced_receiving_stats` for both players (seasonal metrics)
3. Call `get_fantasy_ranks` for dynasty trade values
4. Synthesize response with trade recommendation

**Tool Chaining Rules**:
- Maximum 4 tool calls per question
- If data isn't found after a few attempts, explain what's available instead of retrying
- Prefer seasonal stats over weekly unless user specifies a time range
- Always verify player names and team affiliations before making claims

## Crafting Effective Prompts

### Trade Analysis
**Good prompt**: "Should I trade Justin Jefferson for CeeDee Lamb in a PPR dynasty league?"

**Why it works**:
- Specifies both players
- Includes league format (PPR, dynasty)
- Clear decision point

**Agent workflow**:
1. Fetch player info and stats for both players
2. Fetch dynasty trade values
3. Compare metrics weighted for PPR scoring
4. Consider dynasty value (age, contract, long-term outlook)

### Start/Sit Decisions
**Good prompt**: "Should I start Jayden Daniels or Jared Goff this week?"

**Why it works**:
- Specifies decision point ("this week")
- Names both players clearly

**Agent workflow** (see Start/Sit Analysis Protocol below):
1. Check if user has a primary league set
2. Fetch league scoring settings
3. Determine scoring format (PPR, Superflex, Standard)
4. Fetch advanced passing stats for both QBs
5. Optionally fetch matchup data if "this week" is specified
6. Provide format-aware recommendation with reasoning

### Waiver Wire / Free Agency
**Good prompt**: "Who are the best waiver wire WRs available in my league right now?"

**Why it works**:
- Specifies position (WR)
- Implies user has a connected league ("my league")

**Agent workflow**:
1. Check user context for primary league ID
2. Call `get_sleeper_league_by_id` to get rosters
3. Call `get_sleeper_free_agents` to find unowned players
4. Fetch recent stats for available players
5. Rank by recent performance and opportunity metrics

## Start/Sit Analysis Protocol

When users ask start/sit questions, the agent follows a structured protocol to provide league-contextualized recommendations:

### Step 1: Check for Primary League
The agent checks the `userContext` section for a saved primary league ID. If found, it automatically fetches that league's scoring settings.

### Step 2: Fetch Scoring Settings
If a primary league exists, the agent calls `get_sleeper_league_by_id(league_id, verbose=False)` to retrieve scoring settings. If no primary league is set, it asks the user which league or scoring format to use.

### Step 3: Determine Scoring Format
The agent analyzes the `scoring_settings` object to classify the league:
- **Full PPR**: `rec = 1.0`
- **Half PPR**: `rec = 0.5`
- **Standard**: `rec = 0` or `rec` field not present
- **Superflex**: Check `roster_positions` array for `'SUPER_FLEX'` entry

### Step 4: Weight Metrics by Format
Different scoring formats prioritize different metrics:

**PPR Leagues**:
- Emphasize targets, receptions, target share
- Reception-based volume metrics matter most
- Pass-catching RBs and slot WRs gain value

**Standard Leagues**:
- Emphasize yards and TDs over reception volume
- Big-play ability (yards per carry, yards per reception) matters more
- Touchdown-dependent players gain relative value

**Superflex Leagues**:
- Elevate QB value significantly when comparing QB vs. non-QB in flex spots
- QB scarcity drives premium valuation

### Step 5: Fetch Advanced Stats
Call the appropriate advanced stats tools:
- `get_advanced_receiving_stats` for WRs/TEs
- `get_advanced_passing_stats` for QBs
- `get_advanced_rushing_stats` for RBs
- `get_advanced_defense_stats` for DST

### Step 6: Matchup Context (Optional)
If the user mentions "this week", the agent may call `get_sleeper_league_matchups` to get current week data and identify opponents. This provides additional context about game environment and defensive matchups.

### Step 7: Provide Format-Aware Recommendation
The agent's recommendation must explicitly cite:
1. The league's scoring format (PPR/Half-PPR/Standard/Superflex)
2. Key metrics that matter most for that specific format
3. Matchup considerations if applicable (opponent defense strength, game environment)

### Step 8: Explain Reasoning Transparency
The agent explains WHY the scoring format matters for this specific decision. This makes the format-aware reasoning transparent so users understand how league settings influence the recommendation.

**Example Response Structure**:
> "In your **half-PPR league**, I'd start **Player A** over Player B. Here's why:
>
> **Player A**: 6.2 targets/game, 72% catch rate, 15% target share
> **Player B**: 4.8 targets/game, 65% catch rate, 11% target share
>
> In half-PPR, each reception is worth 0.5 points, so Player A's higher target volume (+1.4 targets/game) translates to approximately **0.7 extra PPR points per game**. Combined with his better catch rate, Player A has a higher floor in this format.
>
> If this were a standard league, Player B's higher yards-per-reception (14.2 vs. 12.1) would make the decision closer, but in half-PPR, reception volume wins out."

## Clarifying Questions

The agent asks clarifying questions when:
- A start/sit question is asked but no primary league is set (needs scoring format)
- Player names are ambiguous ("Jefferson" could be Justin Jefferson or Van Jefferson)
- Time range is unclear ("last season" when multiple seasons are available)
- Trade context is missing (dynasty vs. redraft changes valuation)

**Design principle**: Minimize clarifying questions by leveraging user context. If the user has a primary league saved, the agent uses it automatically rather than asking every time.

## User Preferences (Cross-Session Memory)

User preferences are stored in the `user_preferences` table in Supabase and injected into every conversation via the `userContext` parameter in `getBillSystemPrompt()`.

### Preference Types

1. **Sleeper Connection**
   - `sleeper_username`: User's Sleeper account name
   - `primary_league_id`: Default league for contextualized analysis

2. **Connected Leagues**
   - Multiple league IDs with custom labels ("Main Dynasty", "Redraft League", etc.)

3. **Analysis Preferences**
   - `analysis_style`: "concise" or "detailed"
   - Custom settings for chart vs. table preferences

4. **Roster Notes**
   - Per-player or per-league notes (e.g., "Shopping Player X for RB depth")

### How Preferences are Injected

The `userContext` string is generated from the database and passed to `getBillSystemPrompt()`. It contains formatted text like:

```
Your user's Sleeper username: john_doe
Your user's primary league ID: 123456789
Connected leagues: Main Dynasty (123456789), Redraft League (987654321)
Analysis style: concise
```

The agent reads this context and personalizes responses without requiring users to re-state preferences.

## Data Visualization

The agent can render interactive charts using fenced code blocks with the language identifier `chart`:

```chart
{
  "type": "bar",
  "data": [
    {"player": "Player A", "points": 24.5},
    {"player": "Player B", "points": 18.3}
  ],
  "config": {
    "xKey": "player",
    "yKeys": ["points"],
    "title": "Week 12 Fantasy Points",
    "xAxisLabel": "Player",
    "yAxisLabel": "Points"
  }
}
```

### When to Use Charts vs. Tables

**Use charts when**:
- Comparing 3-20 data points
- Showing rankings or relative performance
- Visualizing trends over time (line charts)

**Use tables when**:
- Exact values matter more than visual comparison
- 20+ rows of data
- Precision is critical (e.g., trade value differentials)

## Response Tone and Style

The agent is:
- **Conversational but analytical**: Friendly tone with data-driven insights
- **Specific**: Cites exact metrics when making recommendations
- **Context-aware**: References user preferences and league settings
- **Trend-conscious**: Considers both current performance and historical trends
- **Dynasty-aware**: For dynasty leagues, factors in player age and long-term value

## Security and Safety

**What this guide does NOT cover**:
- Prompt injection vulnerabilities or exploits
- System-level access or internal tool implementation
- Jailbreak techniques or adversarial prompting
- Direct access to database queries or API keys

**Audience**: This guide is for end users and developers building on top of the BiLL platform, not for adversarial use cases.

## Key Files Reference

- `bill-agent-ui/src/lib/ai/prompts/billSystemPrompt.ts` — System prompt generation
- `bill-agent-ui/src/app/api/chat/route.ts` — AI backend + tool filtering
- `bill-agent-ui/src/lib/ai/tool-search-filter.ts` — Dynamic tool loading
- `bill-agent-ui/src/lib/supabase/user-preferences.ts` — User preference persistence
- `docs/fantasy-tools-mcp/tools-catalog.md` — Complete MCP tool reference

## Further Reading

- [Architecture Overview](architecture.md) — System design and data flow
- [MCP Tools Catalog](fantasy-tools-mcp/tools-catalog.md) — All available tools
- [Frontend Conventions](bill-agent-ui/conventions.md) — UI/UX patterns
