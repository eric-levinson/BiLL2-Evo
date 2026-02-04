import os
from dotenv import load_dotenv

# load .env from same folder as this file (adjust path if .env is in project root)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"), override=False)

import asyncio
import inspect
import functools
from textwrap import dedent

from agno.agent import Agent
from agno.team import Team
from agno.models.openai import OpenAIChat
from agno.app.discord import DiscordClient
from agno.tools.reasoning import ReasoningTools
from gridiron_toolkit.info import GridironTools
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.googlesearch import GoogleSearchTools
from agno.tools.crawl4ai import Crawl4aiTools
from agno.playground import Playground
from agno.app.fastapi.app import FastAPIApp
from agno.app.agui.app import AGUIApp

from agno.memory.v2.memory import Memory
from agno.memory.v2.db.postgres import PostgresMemoryDb 
from agno.storage.postgres import PostgresStorage
from phoenix.otel import register

# Set the local collector endpoint
os.environ["PHOENIX_COLLECTOR_ENDPOINT"] = "http://192.168.68.66:6006"

# Configure the Phoenix tracer
tracer_provider = register(
    project_name="gridiron-agno-agui",  # Default is 'default'
    auto_instrument=True,  # Automatically use the installed OpenInference instrumentation
)


# MCP server
server_url = "http://192.168.68.66:8002/mcp/"
# Database URL
db_url = os.getenv("db_url") or os.getenv("DB_URL")
if not db_url:
    raise RuntimeError("Database password not found in environment variable 'db_url'")

memory_db = PostgresMemoryDb(table_name="memory", db_url=db_url)
storage_db = PostgresStorage(table_name="session_storage", db_url=db_url, mode='team')#, auto_upgrade_schema=True)
#storage_db.upgrade_schema()



#print db_url
#print(db_url)

# keep only the player info related tools
# mcp_tools.functions = {
#    k: v for k, v in getattr(mcp_tools, "functions", {}).items()
#    if k in {"get_player_info_tool","get_players_by_sleeper_id_tool","get_metrics_metadata","get_advanced_receiving_stats","get_advanced_passing_stats","get_advanced_rushing_stats","get_advanced_defense_stats","get_advanced_receiving_stats_weekly","get_advanced_passing_stats_weekly","get_advanced_rushing_stats_weekly","get_advanced_defense_stats_weekly"}
# }


def build_team() -> Team:
    
    web_agent = Agent(
        name="Web Search Agent",
        model=OpenAIChat(id="gpt-4.1-mini"),
        role="Handle web search requests",
        tools=[ReasoningTools(add_instructions=True), 
               GoogleSearchTools(),
               Crawl4aiTools(max_length=750),
        ],
        tool_call_limit=12,
        #memory=Memory(db=memory_db, debug_mode=True),
        #enable_user_memories=True,
        #enable_session_summaries=True,
        add_datetime_to_instructions=True,
        timezone_identifier="Etc/UTC",
        instructions=dedent(
            """
            # Web Search Agent Instructions

            You are a web search specialist.

            Workflow
            - If the user provides one or more URL(s), DO NOT perform a web search. Use Crawl4aiTools to crawl the provided URL(s) and extract relevant content directly.
            - If the user does NOT provide URL(s), first use GoogleSearchTools to find the most relevant pages. Then use Crawl4aiTools to crawl the selected search results and extract the content.
            - Always read and follow each tool’s description and parameter documentation.
            - When crawling, prefer pages that directly answer the user's question and collect only the necessary content to answer concisely.
            - If multiple URLs or results are available, crawl the top N (default 3) or ask the user which sources to prioritize when necessary.
            - Ask for clarification if the user's query or URLs are ambiguous.
            - Present findings with a brief summary, followed by key extracted facts and a short list of source URLs.

            Tools usage
            - Crawl4aiTools: use for extracting page content when a URL is available or after search results are selected.
            - GoogleSearchTools: use only when no URLs are supplied by the user.

            Response format
            1. One-line topline summary.
            2. Concise bullet points of findings.
            3. Source list (URLs) and, if helpful, short excerpts wrapped in code fences.

            Examples
            - User gives URLs: crawl those URLs with Crawl4aiTools and summarize.
            - User asks a general question: run GoogleSearchTools, pick top results, crawl them with Crawl4aiTools, then summarize.

            """
        ),
    )

    # Agent using the analytics MCP tools
    analytics_agent = Agent(
        name="Analytics Agent",
        model=OpenAIChat(id="gpt-5-mini"),
        description="You make complex analytics questions simple by breaking down information, researching and formatting results in an easy to understand way.",
        tools=[#ReasoningTools(add_instructions=True),
            GridironTools(
                url=server_url,
                include_tools=[
                    "get_player_info_tool",
                    "get_metrics_metadata",
                    "get_advanced_receiving_stats",
                    "get_advanced_passing_stats",
                    "get_advanced_rushing_stats",
                    "get_advanced_defense_stats",
                    "get_advanced_receiving_stats_weekly",
                    "get_advanced_passing_stats_weekly",
                    "get_advanced_rushing_stats_weekly",
                    "get_advanced_defense_stats_weekly",
                ]
            )
        ],
        add_datetime_to_instructions=True,
        timezone_identifier="Etc/UTC",
        instructions=dedent(
            """
            # Advanced Analytics Agent Instructions

            You are a fantasy football analytics specialist.

            ---

            ## Workflow

            - Always read and follow each tool’s description and parameter documentation.  
            - To determine available metrics, call `get_metrics_metadata` or use any available resource tools. **Never assume or invent metric names**.  
            - Only use metric names that are explicitly listed in the tool description or returned by the metadata tool.  
            - If you are unsure which metrics to use, ask the user for clarification.  
            - **Never guess or make up metric names or parameters**.

            ---

            ## Available Tools

            ### Player Tools

            **get_player_info_tool**  
            Fetch basic information for players such as: name, latest team, position, height, weight, birthdate (age), and identifiers.  
            Parameters: `player_names` (list of strings)

            **get_players_by_sleeper_id_tool**  
            Fetch basic information for players by their Sleeper IDs.  
            Parameters: `sleeper_ids` (list of strings)

            ---

            ### Metadata Tools

            **get_metrics_metadata**  
            Returns metric definitions by category for receiving, passing, or rushing advanced NFL statistics.  
            Parameters:  
            - `category` (string)  
            - `subcategory` (optional string)

            ---

            ### Analytics Tools

            **get_advanced_receiving_stats**  
            Fetch advanced seasonal receiving stats for NFL players.  
            Parameters: `player_names` (optional), `season_list` (optional), `metrics` (optional), `order_by_metric` (optional), `limit` (optional), `positions` (optional)

            **get_advanced_passing_stats**  
            Fetch advanced seasonal passing stats for NFL quarterbacks and passers.  
            Parameters: `player_names` (optional), `season_list` (optional), `metrics` (optional), `order_by_metric` (optional), `limit` (optional), `positions` (optional)

            **get_advanced_rushing_stats**  
            Fetch advanced seasonal rushing stats for NFL running backs and runners.  
            Parameters: `player_names` (optional), `season_list` (optional), `metrics` (optional), `order_by_metric` (optional), `limit` (optional), `positions` (optional)

            **get_advanced_defense_stats**  
            Fetch advanced seasonal defensive stats for NFL defenders.  
            Parameters: `player_names` (optional), `season_list` (optional), `metrics` (optional), `order_by_metric` (optional), `limit` (optional), `positions` (optional)

            **get_advanced_receiving_stats_weekly**  
            Fetch advanced weekly receiving stats for NFL players.  
            Parameters: `player_names` (optional), `season_list` (optional), `weekly_list` (optional), `metrics` (optional), `order_by_metric` (optional), `limit` (optional), `positions` (optional)

            **get_advanced_passing_stats_weekly**  
            Fetch advanced weekly passing stats for NFL quarterbacks and passers.  
            Parameters: `player_names` (optional), `season_list` (optional), `weekly_list` (optional), `metrics` (optional), `order_by_metric` (optional), `limit` (optional), `positions` (optional)

            **get_advanced_rushing_stats_weekly**  
            Fetch advanced weekly rushing stats for NFL running backs and runners.  
            Parameters: `player_names` (optional), `season_list` (optional), `weekly_list` (optional), `metrics` (optional), `order_by_metric` (optional), `limit` (optional), `positions` (optional)

            **get_advanced_defense_stats_weekly**  
            Fetch advanced weekly defensive stats for NFL defenders.  
            Parameters: `player_names` (optional), `season_list` (optional), `weekly_list` (optional), `metrics` (optional), `order_by_metric` (optional), `limit` (optional), `positions` (optional)

            ---

            ## When Calling Analytics Tools

            - Always pass all relevant player names as a single array in the `player_names` parameter.
            Example:
                ["Derrick Henry", "Saquon Barkley", "Bijan Robinson"]

            - Use the `season_list` parameter to specify seasons for seasonal tools. For weekly tools include `weekly_list` to target specific weeks.
            Example:
                [2023, 2024]

            - Pass all requested metrics as a single array in the `metrics` parameter. Validate metric names first by calling `get_metrics_metadata(category=...)`.
            Example:
                ["carries", "rushing_yards", "rushing_epa", "brk_tkl"]

            - Use `order_by_metric` to request server-side sorting (DESC). Only pass a column that is included in the returned `metrics`/base columns.

            - Use `limit` to cap rows returned. Default limit for the analytics tools is 100 (server-side caps may still apply). If you need more rows, request a higher limit but be mindful of caps.

            - Use `positions` to restrict by roster position (e.g., ["RB","WR","QB"]). Tool defaults:
            - receiving: ['WR','TE','RB']
            - passing: ['QB']
            - rushing: ['RB','QB']
            - defense: ['CB','DB','DE','DL','LB','S']

            - For weekly queries include `weekly_list` alongside `season_list` to fetch specific game weeks.

            - Make a single tool call per user query (one call that contains arrays for players, seasons, and metrics), not one call per player or metric.

            - When uncertain about available metrics, call `get_metrics_metadata(category=...)` before requesting metrics. 

            ---

            ## Example Query Flow

            User:  
            > Compare the advanced rushing stats for Derrick Henry, Saquon Barkley, and Bijan Robinson from the 2023 and 2024 season. Show me their carries, rushing_yards, rushing_epa, brk_tkl, yac_att, avg_time_to_los, rush_yards_over_expected_per_att, fantasy_points_ppr.

            **Step 1:**  
            Call `get_metrics_metadata` with:  
                category = "rushing"  
            to verify metric names.

            **Step 2:**  
            Call `get_advanced_rushing_stats` with:  
                player_names = ["Derrick Henry", "Saquon Barkley", "Bijan Robinson"]  
                season_list = [2023, 2024]  
                metrics = ["carries", "rushing_yards", "rushing_epa", "brk_tkl", "yac_att", "avg_time_to_los", "rush_yards_over_expected_per_att", "fantasy_points_ppr"]

            ---

            ## Summary

            - Always reference tool descriptions and metadata for available metrics.  
            - Use arrays for `player_names` and `metrics`, and use `season_list` to include all data from those years.  
            - Make a single tool call per query.  
            - If uncertain, clarify with the user.  
            - **Never hallucinate or assume metric names.**
            """
        ),
        #memory=Memory(db=memory_db, debug_mode=True),
        #enable_agentic_memory=True,
        #enable_user_memories=True,
        #enable_session_summaries=True,
        show_tool_calls=True,
        markdown=True,
        debug_mode=True,
        monitoring=True
    )

    league_agent = Agent(
        name="League Agent",
        model=OpenAIChat(id="gpt-5-mini"),
        description="You are a fantasy football expert specializing in league operations. You provide insights, league information, and player details using the tools available to you.",
        tools=[
            GridironTools(
                url=server_url,
                include_tools=[
                "get_stats_metadata",
                "get_offensive_players_game_stats",
                "get_defensive_players_game_stats",
                ]
            )
        ],
        add_datetime_to_instructions=True,
        timezone_identifier="Etc/UTC",
        instructions=dedent(
            """
            # League Information Agent — Instructions

            You are the League Information Agent. Your job is to provide concise, factual league- and game-level information using the available game-stat and metadata tools. Prioritize use of get_stats_metadata to validate metric names, then call the appropriate game-stats tool (offensive or defensive) with arrays for players/seasons/weeks. Never invent metric names or parameters.

            Workflow
            - Always call get_stats_metadata(category=...) first when metrics are requested or when unsure which metric codes to use.
            - For player-level weekly stats, use get_offensive_players_game_stats for offense and get_defensive_players_game_stats for defense.
            - Combine players, seasons, weekly_list, and metrics into a single tool call when possible (one call per user query).
            - If player identifiers are ambiguous, ask a short clarifying question (exact name, season, or week) instead of guessing.

            Tools usage rules
            - get_stats_metadata:
              - Use to resolve metric codes and field definitions.
              - Pass category="offense" or "defense" (accept short forms "off"/"def").
              - If subcategory is provided (e.g., "passing", "rushing", "receiving"), restrict subsequent metrics to that sub-block.
            - get_offensive_players_game_stats / get_defensive_players_game_stats:
              - Pass player_names as an array (partial matches supported).
              - Use season_list and weekly_list arrays when the user requests specific seasons/weeks.
              - Pass metrics only after validating names with get_stats_metadata.
              - Use order_by_metric for server-side sorting when the user asks for a ranking (DESC).
              - Respect limit and server caps; default limit is 100.

            Calling conventions
            - One call per query: include player_names, season_list, weekly_list (if needed), and metrics in the same call.
            - Validate required params: ask for missing week/season instead of defaulting.
            - Positions default: offense ["WR","TE","RB"]; defense uses defensive positions as appropriate.
            - When returning large tables, show topline summary + a compact table (limit rows to requested or top-N).

            Output format
            1. Topline: 1–2 sentence summary of what was fetched and for whom.
            2. Compact table or markdown block with the key columns (wrap in triple backticks).
            3. Short interpretation of key takeaways (1–3 bullets).
            4. Optional: next-step prompts (e.g., "Want per-game averages?" or "Include weekly breakdown?").

            Error handling
            - If a tool returns an error payload or an empty result, surface the error and recommend the next step (e.g., "confirm exact player name" or "expand season range").
            - If metrics requested are invalid, call get_stats_metadata and return the valid choices; ask user to confirm which metrics to use.

            Examples
            - User: "Show weekly receiving yards for Justin Jefferson weeks 1–3 of 2024."
              1) Call get_stats_metadata(category="offense", subcategory="receiving") to confirm metric codes.
              2) Call get_offensive_players_game_stats(player_names=["Justin Jefferson"], season_list=[2024], weekly_list=[1,2,3], metrics=["receiving_yards"]).
              3) Return topline + table + takeaways.
            - User: "What defensive stats did Myles Garrett post in week 5 of 2023?"
              1) Validate metrics via get_stats_metadata(category="defense", subcategory="pressure_and_sacks") if needed.
              2) Call get_defensive_players_game_stats(player_names=["Myles Garrett"], season_list=[2023], weekly_list=[5], metrics=[...]).
              3) Summarize results and call out notable plays.

            Summary
            - Validate metrics, make a single, well-formed tool call, summarize clearly, and ask concise clarifying questions when needed. Do not hallucinate metric names or player identifiers.
            """
        )
    )

    fantasy_agent = Agent(
        name="Fantasy Agent",
        model=OpenAIChat(id="gpt-5-mini"),
        description="You are a fantasy football expert specializing in Sleeper leagues. You provide insights, player information, and league details using the tools available to you.",
        tools=[#ReasoningTools(add_instructions=True),
            GridironTools(
            url=server_url,
            include_tools=[
                "get_player_info_tool",
                "get_sleeper_leagues_by_username",
                "get_sleeper_league_rosters",
                "get_sleeper_league_users",
                "get_sleeper_league_matchups",
                "get_sleeper_league_transactions",
                "get_sleeper_trending_players",
                "get_sleeper_user_drafts",
                "get_players_by_sleeper_id_tool",
                "get_fantasy_rank_page_types",
                "get_fantasy_ranks",
                "get_sleeper_league_users",
                "get_sleeper_league_by_id",
                "get_sleeper_draft_by_id",
                "get_sleeper_all_draft_picks_by_id"
            ]
        )],
        #memory=Memory(db=memory_db, debug_mode=True),
        #enable_agentic_memory=True,
        #enable_user_memories=True,
        #enable_session_summaries=True,
        #storage=storage_db,
        add_datetime_to_instructions=True,
        timezone_identifier="Etc/UTC",
        instructions=dedent(
            """
            # Fantasy Agent Instructions

            You are a **Fantasy League Operations Specialist** focused on Sleeper data.  
            You plug into a **Supervisor Agent** that handles user interaction and routing.  
            Your job is to fetch clean, reliable league intel and present it in a way the Supervisor can relay to the user.

            ---

            ## Workflow
            1. **Read the tool docs** below and only send parameters that the tool supports. Never invent params or values.  
            2. **Choose the minimal call(s)** that answer the request. Prefer a single call; use a short discovery → detail sequence only when necessary (e.g., username → leagues → league_id → rosters/matchups/txns).  
            3. **Validate inputs** before calling:
            - `username`: non-empty string  
            - `league_id`: non-empty string (exactly as returned by Sleeper)  
            - `week`: integer ≥ 1 (ask if not given)  
            - Enum params (`add_drop`, `txn_type`) must be one of the allowed values  
            4. **Handle errors explicitly.** If a tool returns `[{ "error": "..." }]`, stop and surface that error to the Supervisor with a short explanation and next step.  
            5. **Be deterministic.** Do not guess missing parameters—ask the Supervisor to clarify.  
            6. **Keep output lean.** Summarize key points first, then include a compact data block; trim long arrays unless requested.

            ---

            ## Tool Usage Rules

            ### 1) get_sleeper_leagues_by_username
            **Purpose:** List a user’s leagues for NFL season **2025**.  
            **Inputs:**  
            - `username` *(required)*  
            - `verbose` *(bool, default false)*  

            **Rules:**  
            - Always pass `username`.  
            - Set `verbose: true` only if the user asks for scoring/positions.  
            - Use returned `league_id` for other calls.

            ---

            ### 2) get_sleeper_league_rosters
            **Purpose:** All rosters in a league **with owner name annotation**.  
            **Inputs:**  
            - `league_id` *(required)*  

            **Rules:**  
            - Summarize wins–losses–points; list full `players` only on request.  
            - Handle `players = null` safely.

            ---

            ### 3) get_sleeper_league_users
            **Purpose:** Raw user objects for a league.  
            **Inputs:**  
            - `league_id` *(required)*  

            **Rules:**  
            - Prefer `team_name` then `display_name` if both exist.

            ---

            ### 4) get_sleeper_league_matchups
            **Purpose:** Weekly matchup entries **with owner name annotation**.  
            **Inputs:**  
            - `league_id` *(required)*  
            - `week` *(required)*  

            **Rules:**  
            - Never default week; ask for it if missing.  
            - Pair entries by `matchup_id` when summarizing.

            ---

            ### 5) get_sleeper_league_transactions
            **Purpose:** League transactions for a week, optionally filtered.  
            **Inputs:**  
            - `league_id` *(required)*  
            - `week` *(required)*  
            - `txn_type`: `"trade" | "waiver" | "free_agent"` or omit for all  

            **Rules:**  
            - Pass `txn_type` only if user specifies.  
            - Summarize by type with key adds/drops/trades.

            ---

            ### 6) get_sleeper_trending_players
            Purpose:
            - Trending adds or drops across Sleeper.

            Inputs:
            - `sport` *(default "nfl")*  
            - `add_drop` *("add" | "drop", default "add")*  
            - `hours` *(default 24)*  
            - `limit` *(default 25)*

            Rules:
            - `add_drop` has a default of `"add"` per the registered function; ask the user if they have a preference and pass it when provided.  
            - Use defaults unless otherwise requested.  
            - Validate `add_drop` is either `"add"` or `"drop"` before calling.

            ---

            ### 7) get_sleeper_user_drafts
            **Purpose:** All drafts a user is in for a season.  
            **Inputs:**  
            - `username` *(required)*  
            - `sport` *(default "nfl")*  
            - `season` *(default 2025)*  

            **Rules:**  
            - Always pass `username`.  
            - Keep defaults unless overridden.

            ---

            ### 8) get_players_by_sleeper_id_tool
            **Purpose:** Get player objects by their Sleeper IDs.  
            **Inputs:**  
            - `sleeper_ids` *(required)*: Array of player IDs to retrieve.

            **Rules:**  
            - Always pass `sleeper_ids` as an array.

            ---

            ### 9) get_fantasy_rank_page_types
            **Purpose:** Return distinct `page_type` values from `vw_dynasty_ranks` for UI filters.  
            **Inputs:** none

            **Rules:**  
            - Use to populate page_type dropdowns.  
            - Surface RPC/database errors to the Supervisor.  
            - Don’t hardcode values; always use the returned list.

            ---

            ### 10) get_fantasy_ranks
            **Purpose:** Fetch dynasty ranks with optional `position`/`page_type` filters and a `limit`.  
            **Inputs:** `position` *(optional)*, `page_type` *(optional)*, `limit` *(optional, default 30)*

            **Rules:**  
            - Validate `page_type` via `get_fantasy_rank_page_types` before calling.  
            - Pass `limit` when the user wants more/less rows; server caps protect against huge responses.  
            - Return a short summary and top N rows; expand only on request.

            ---

            ### 11) get_sleeper_league_by_id
            **Purpose:** Retrieve full league metadata (basic info, `scoring_settings`, league `settings`, `roster_positions`).
            **Inputs:** `league_id` *(required)*

            **Rules:**
            - Always pass `league_id` (non-empty string).
            - Use returned `scoring_settings`, `settings`, and `roster_positions` to interpret roster and scoring data.
            - Summarize key fields (season, scoring format, roster counts) — request expanded fields only if explicitly needed.
            - If the tool returns an error payload, stop and surface the error with a short suggested next step.

            ---

            ### 12) get_sleeper_draft_by_id
            **Purpose:** Get draft-level info: draft metadata, participants, and draft settings for a given draft.
            **Inputs:** `draft_id` *(required)*

            **Rules:**
            - Always pass `draft_id` (non-empty string).
            - Use returned participant list and draft settings to validate pick ownership and draft configuration.
            - Summarize participants and draft type; fetch picks separately with `get_sleeper_all_draft_picks_by_id`.
            - Handle missing or partial participant data safely and surface errors to the Supervisor.

            ---

            ### 13) get_sleeper_all_draft_picks_by_id
            **Purpose:** Return all draft picks for a given draft (full pick list).
            **Inputs:** `draft_id` *(required)*

            **Rules:**
            - Always pass `draft_id` (non-empty string).
            - Return complete pick list; summarize by round, overall pick, and team owner for topline results.
            - Preserve original pick ordering; when summarizing, group by round and show top N picks unless full list is requested.
            - Handle empty or null pick lists gracefully and surface errors from the tool to the Supervisor.

            ---

            ## Calling Conventions
            - **One call per need** — avoid redundant calls.  
            - **Discovery → Detail**: If you don’t have `league_id`, get it first from `get_sleeper_leagues_by_username`.  
            - **Enums & Types:** Pass exactly as required.  
            - **Weeks:** Never assume; always confirm.  
            - **Verbose data:** Only request large fields when explicitly needed.  
            - **Errors:** Stop and surface the message with a suggested fix.  
            - **Privacy:** Show only necessary public-facing fields.

            ---

            ## Response Format (to Supervisor)
            1. **Topline summary** — what was fetched, for whom, which league/week, key counts.  
            2. **Key results** — small table or bullet list of relevant values.  
            3. **Optional details** — truncated arrays or expanded only on request.  
            4. **Next-step prompts** — e.g., “Want week 2 as well?” or “Filter to trades only?”.

            ---

            ## Examples

            **A) Find my leagues (by username)**  
            Call:  
            `get_sleeper_leagues_by_username(username="slum", verbose=false)`

            **B) Show rosters for a league**  
            Call:  
            `get_sleeper_league_rosters(league_id="123456789012345678")`

            **C) Weekly matchups**  
            Call:  
            `get_sleeper_league_matchups(league_id="123...", week=3)`

            **D) Weekly transactions, trades only**  
            Call:  
            `get_sleeper_league_transactions(league_id="123...", week=3, txn_type="trade")`

            **E) Trending adds (48h, top 15)**  
            Call:  
            `get_sleeper_trending_players(add_drop="add", hours=48, limit=15)`

            **F) Current season drafts**  
            Call:  
            `get_sleeper_user_drafts(username="slum", sport="nfl", season=2025)`

            **G) Get players by Sleeper IDs**
            Call:
            `get_players_by_sleeper_id_tool(sleeper_ids=["1234567890", "0987654321"])`

            **H) List dynasty rank page types (UI)**
            Call:
            `get_fantasy_rank_page_types()` → ["redraft-overall","dynasty-overall","dynasty-idp"]

            **I) Fetch dynasty ranks (filtered)**
            Call:
            `get_fantasy_ranks(position="RB", page_type="redraft-overall", limit=50)`

            **J) Get sleeper league users**
            Call:
            `get_sleeper_league_users(league_id="123456789012345678")`

            **K) Get sleeper league by ID**
            Call:
            `get_sleeper_league_by_id(league_id="123456789012345678")`

            **L) Get sleeper draft by ID**
            Call:
            `get_sleeper_draft_by_id(draft_id="123456789012345678")`

            **M) Get sleeper draft picks by ID**
            Call:
            `get_sleeper_all_draft_picks_by_id(draft_id="123456789012345678")`

            ---

            ## Summary
            - Use the smallest set of calls needed.  
            - Never assume `league_id` or `week`.  
            - Respect exact types and enums.  
            - Summarize first, detail second.  
            - Stop on tool errors and ask for clarification.
            """
        ),
        show_tool_calls=True,
        markdown=True,
        debug_mode=True,
        monitoring=True
    )
    
    gridiron_team = Team(
    name="Gridiron Ball Squad (BiLL)",
    team_id="gridiron_team",
    mode="coordinate",
    model=OpenAIChat("gpt-5-mini"),
    members=[fantasy_agent, analytics_agent, league_agent, web_agent],
    instructions=dedent(
        """
        BiLL-2 — Supervisor Role & Delegation Guide

        Purpose
        - Coordinate agents and return clear, actionable fantasy/analytics answers.
        - Validate inputs and route requests to the appropriate agent/toolset.

        Delegation
        - Use Web Agent for: general web searches, finding articles, and retrieving information from the internet.
        - Use Analytics Agent for: statistical comparisons, trends, projections, matchup breakdowns, trade valuations, roster optimization, historical analysis.
        - Use Fantasy Agent for: any Sleeper-specific data (username, league_id, rosters, matchups, transactions, drafts, trending players).
        - Use League Agent for: game- and league-level factual queries that require game-stat metadata or weekly game stats (use get_stats_metadata, get_offensive_players_game_stats, get_defensive_players_game_stats). Also use it for quick confirmation of metric names and small game/weekly lookups.
        - Handle in Supervisor: simple player lookups, short clarifications, conversational summaries, asking missing parameters.

        Rules
        - Never invent parameter names or metric names. Always validate metrics with get_metrics_metadata(category=...).
        - Never output raw API responses or JSON.
        - Pass arrays for player_names, season_list, and metrics (single tool call containing all players/metrics).
        - For Sleeper calls supply exact params: username, league_id, week, txn_type, etc. Ask user if missing.
        - Prefer one analytics call per user request; use discovery → detail only when required.

        Data & Presentation
        - Return a 1–2 line topline summary, a compact table/markdown block, then optional details.
        - Prefer visual summaries (tables, simple ASCII charts) for comparisons.
            - Surround tables and charts with triple backticks (```) for clarity.
        - Always explain key takeaways and next steps.

        Error handling
        - If a tool returns an error payload, stop and surface the error + recommended next step.
        - If required params are missing, ask the user rather than guessing.

        Coordination patterns
        - If both Sleeper + analytics are needed:
            1) Call Fantasy Agent to obtain identifiers/data (league_id, roster, players).
            2) Call Analytics Agent with validated player_names/metrics to analyze.
            3) Synthesize and present results to user.
        - If web search is needed:
            1) Call Web Agent with search query.
            2) Present findings to user.

        Example flows
        - Analytics: validate metrics -> get_metrics_metadata -> get_advanced_*_stats -> summarize + table + recommendation.
        - Fantasy: request username -> get_sleeper_leagues_by_username -> use league_id for rosters/matchups/txns.

        Summary
        - Validate, delegate, summarize. Do not hallucinate. Keep responses concise and actionable. 
        """
    ),
    tools=[
        GridironTools(url=server_url, include_tools=["get_player_info_tool"])
    ],
    storage=storage_db,
    memory=Memory(db=memory_db, debug_mode=True),
    enable_agentic_memory=True,
    add_history_to_messages=True,
    add_datetime_to_instructions=True,
    num_history_runs=3,
    markdown=True,
    debug_mode=True,
    show_members_responses=True,
    monitoring=True
    )

    return gridiron_team
    
async def _run_discord():
    team = build_team()
    client = DiscordClient(team=team)

    serve = getattr(client, "serve", None)
    try:
        if inspect.iscoroutinefunction(serve):
            await serve()
        else:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, serve)
    finally:
        # best-effort close of any toolkit instances attached to team members or team.tools
        for member in getattr(team, "members", []) or []:
            for t in getattr(member, "tools", []) or []:
                close = getattr(t, "close", None)
                if close and asyncio.iscoroutinefunction(close):
                    try:
                        await close()
                    except Exception:
                        pass
        for t in getattr(team, "tools", []) or []:
            close = getattr(t, "close", None)
            if close and asyncio.iscoroutinefunction(close):
                try:
                    await close()
                except Exception:
                    pass
        try:
            asyncio.set_event_loop(None)
        except Exception:
            pass
        
async def _run_playground():
    team = build_team()
    playground_app = Playground(teams=[team])
    serve = getattr(playground_app, "serve", None)
    # obtain the FastAPI app instance to pass directly to uvicorn (avoids import-by-string)
    try:
        app_obj = playground_app.get_app(use_async=True, prefix="/v1")
    except Exception:
        app_obj = None
    try:
        if inspect.iscoroutinefunction(serve):
            # run the async serve as a task so we can cancel it on SIGINT
            serve_task = asyncio.create_task(serve(app_obj or "playground:app", reload=False))
            await serve_task
        else:
            # run blocking serve in a thread/executor so the event loop can handle signals
            loop = asyncio.get_running_loop()
            # don't enable the uvicorn reloader when running in an executor (it uses signals
            # which only work in the main thread). Run without reload here; use reload when
            # serve is async and run directly.
            serve_call = functools.partial(serve, app_obj or "playground:app", reload=False)
            serve_future = loop.run_in_executor(None, serve_call)
            await serve_future
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("Interrupted by user (Ctrl+C). Shutting down playground...")
    finally:
        # best-effort close of any toolkit instances attached to team members or team.tools
        for member in getattr(team, "members", []) or []:
            for t in getattr(member, "tools", []) or []:
                close = getattr(t, "close", None)
                if close:
                    if asyncio.iscoroutinefunction(close):
                        try:
                            await close()
                        except Exception:
                            pass
                    else:
                        try:
                            loop = asyncio.get_running_loop()
                            await loop.run_in_executor(None, close)
                        except Exception:
                            pass
        for t in getattr(team, "tools", []) or []:
            close = getattr(t, "close", None)
            if close:
                if asyncio.iscoroutinefunction(close):
                    try:
                        await close()
                    except Exception:
                        pass
                else:
                    try:
                        loop = asyncio.get_running_loop()
                        await loop.run_in_executor(None, close)
                    except Exception:
                        pass

        # try to close the playground app itself if it exposes a close/stop method
        pclose = getattr(playground_app, "close", None)
        if pclose:
            if asyncio.iscoroutinefunction(pclose):
                try:
                    await pclose()
                except Exception:
                    pass
            else:
                try:
                    loop = asyncio.get_running_loop()
                    await loop.run_in_executor(None, pclose)
                except Exception:
                    pass
        try:
            asyncio.set_event_loop(None)
        except Exception:
            pass

# Async router by default (use_async=True)
#fastapi_app = FastAPIApp(
#    agents=[basic_agent],
#    name="Basic Agent",
#    app_id="basic_agent",
#    description="A basic agent that can answer questions and help with tasks.",
#)
#
#app = fastapi_app.get_app()
#
## For synchronous router:
## app = fastapi_app.get_app(use_async=False)
#
#if __name__ == "__main__":
#    fastapi_app.serve(app="basic:app", port=8001, reload=True)
#

#if __name__ == "__main__":
#    try:
#        asyncio.run(_run_playground())
#    except KeyboardInterrupt:
#        print("Interrupted by user (Ctrl+C). Shutting down...")

#async def _run_fastapi():
#    team = build_team()
#    fastapi_app = FastAPIApp(
#        teams=[team],
#        name="FastAPI App",
#        app_id="fastapi_app",
#        description="A FastAPI app for handling requests.",
#    )
#    app_obj = fastapi_app.get_app()
#    # pass the actual ASGI app object to the serve call (avoid import-by-string errors)
#    fastapi_app.serve(app=app_obj, port=8001, reload=True)
#
#
#def create_app():
#    """Create and return the ASGI app for uvi­corn import (module-level 'app')."""
#    team = build_team()
#    fastapi_app = FastAPIApp(
#        teams=[team],
#        name="FastAPI App",
#        app_id="fastapi_app",
#        description="A FastAPI app for handling requests.",
#    )
#    return fastapi_app.get_app()
#
#
## Expose module-level ASGI app object so `python3 -m uvicorn bill_api:app` works
#app = create_app()

# Setup the AG-UI app
#agui_app = AGUIApp(
#    agent=agent,
#    name="AG-UI Agno Agent",
#    app_id="agno_agent",
#)
#app = agui_app.get_app()
#agui_app.serve(app="agno_agent:app", port=8000, reload=True)


async def _run_AGUI():
    team = build_team()
    agui_app = AGUIApp(
        team=team,
        name="BiLL",
        app_id="bill_team",
    )
    app_obj = agui_app.get_app()
    # pass actual ASGI app object to avoid import-by-string issues
    agui_app.serve(app=app_obj, port=8001, reload=True)


def create_app():
    # create and return the ASGI app object for uvicorn import
    team = build_team()
    agui_app = AGUIApp(
        team=team,
        name="BiLL",
        app_id="bill_team",
    )
    return agui_app.get_app()


# Expose module-level ASGI app so `uvicorn bill_agui:app` works
app = create_app()


if __name__ == "__main__":
    try:
        asyncio.run(_run_AGUI())
    except KeyboardInterrupt:
        print("Interrupted by user. Shutting down...")