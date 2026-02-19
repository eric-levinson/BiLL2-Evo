from fastmcp import FastMCP
from supabase import Client

from .info import get_sleeper_all_draft_picks_by_id as _get_sleeper_all_draft_picks_by_id
from .info import get_sleeper_draft_by_id as _get_sleeper_draft_by_id
from .info import get_sleeper_league_by_id as _get_sleeper_league_by_id
from .info import get_sleeper_league_matchups as _get_sleeper_league_matchups
from .info import get_sleeper_league_rosters as _get_sleeper_league_rosters
from .info import get_sleeper_league_transactions as _get_sleeper_league_transactions
from .info import get_sleeper_league_users as _get_sleeper_league_users
from .info import get_sleeper_leagues_by_username as _get_sleeper_leagues_by_username
from .info import get_sleeper_trending_players as _get_sleeper_trending_players
from .info import get_sleeper_user_drafts as _get_sleeper_user_drafts

# All BiLL2 tools are read-only queries with no write-back capability
_TOOL_ANNOTATIONS = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": False,
}


def register_tools(mcp: FastMCP, supabase: Client):
    """Register fantasy-related tools with the FastMCP instance."""

    @mcp.tool(
        annotations=_TOOL_ANNOTATIONS,
        description=(
            "Find a user's fantasy football leagues on Sleeper for league context and scoring format discovery. "
            "Returns a filtered list of league objects. If verbose is True, "
            "includes scoring_settings, settings, and roster_positions. Essential for identifying "
            "PPR/Standard/Superflex format before providing trade or start/sit advice."
        ),
    )
    def get_sleeper_leagues_by_username(username: str, verbose: bool = False) -> list[dict]:
        return _get_sleeper_leagues_by_username(username, verbose)

    @mcp.tool(
        annotations=_TOOL_ANNOTATIONS,
        description=(
            "Get rosters for a given Sleeper league ID. Analyze roster construction, identify positional needs, "
            "evaluate trade targets, assess team depth. If summary is True, returns compact "
            "roster info with player names/positions/teams instead of full player ID arrays. "
            "If False (default), returns full roster data. Use for trade partner identification and roster gap analysis."
        ),
    )
    def get_sleeper_league_rosters(league_id: str, summary: bool = False) -> list[dict]:
        return _get_sleeper_league_rosters(league_id, summary, supabase=supabase)

    @mcp.tool(
        annotations=_TOOL_ANNOTATIONS,
        description=(
            "Get the users for a given Sleeper league ID. Useful for league management context, "
            "identifying trade partners, and understanding league composition. "
            "Returns a list of user objects as returned by the Sleeper API."
        ),
    )
    def get_sleeper_league_users(league_id: str) -> list[dict]:
        return _get_sleeper_league_users(league_id)

    @mcp.tool(
        annotations=_TOOL_ANNOTATIONS,
        description=(
            "Get matchups for a given Sleeper league ID and week. Use for weekly matchup analysis, "
            "start/sit context, and head-to-head evaluation. If summary is True, returns "
            "compact matchup info with player names/positions/teams instead of full player ID arrays. "
            "If False (default), returns full matchup data. The caller must provide the target week."
        ),
    )
    def get_sleeper_league_matchups(league_id: str, week: int, summary: bool = False) -> list[dict]:
        return _get_sleeper_league_matchups(league_id, week, summary, supabase=supabase)

    @mcp.tool(
        annotations=_TOOL_ANNOTATIONS,
        description=(
            "Get transactions for a given Sleeper league ID and week. Use for trade history review, "
            "waiver activity tracking, free agent pickups, and league activity monitoring. "
            "Optionally filter by transaction type such as 'trade', 'waiver', "
            "or 'free_agent'. Useful for understanding league trends and identifying savvy managers."
        ),
    )
    def get_sleeper_league_transactions(league_id: str, week: int, txn_type: str | None = None) -> list[dict]:
        return _get_sleeper_league_transactions(league_id, week, txn_type)

    @mcp.tool(
        annotations=_TOOL_ANNOTATIONS,
        description=(
            "Get trending players for the specified sport from Sleeper. Essential for waiver wire recommendations, "
            "pickup targets, and breakout detection. Identifies must-add players based on league-wide adds/drops. "
            "Use add_drop to choose adds or drops, hours to set the lookback "
            "period, and limit for the number of players returned. Perfect for identifying league winners on waivers. "
            "Returns enriched data with player names, positions, and teams."
        ),
    )
    def get_sleeper_trending_players(
        sport: str = "nfl", add_drop: str = "add", hours: int = 24, limit: int = 25
    ) -> list[dict]:
        return _get_sleeper_trending_players(sport, add_drop, hours, limit, supabase=supabase)

    @mcp.tool(
        annotations=_TOOL_ANNOTATIONS,
        description=(
            "Get all drafts for a Sleeper user. Use for draft analysis, reviewing draft strategy, "
            "and identifying leagues where the user participated. "
            "Provide the username and optionally sport and season. "
            "Returns a list of draft objects as returned by the Sleeper API."
        ),
    )
    def get_sleeper_user_drafts(username: str, sport: str = "nfl", season: int = 2025) -> list[dict]:
        return _get_sleeper_user_drafts(username, sport, season)

    @mcp.tool(
        annotations=_TOOL_ANNOTATIONS,
        description=(
            "Get a Sleeper league by its ID. Essential for scoring format discovery (PPR/Standard/Superflex detection) "
            "and league context for start/sit and trade analysis. If summary is True, returns compact "
            "league data without nested settings objects. If False (default), "
            "includes basic info, scoring settings, league settings, and roster positions."
        ),
    )
    def get_sleeper_league_by_id(league_id: str, summary: bool = False) -> dict:
        return _get_sleeper_league_by_id(league_id, summary)

    @mcp.tool(
        annotations=_TOOL_ANNOTATIONS,
        description=(
            "Get a Sleeper draft by its ID. Use for draft analysis and reviewing draft strategy. "
            "Includes basic info, participants, and draft settings."
        ),
    )
    def get_sleeper_draft_by_id(draft_id: str) -> dict:
        return _get_sleeper_draft_by_id(draft_id)

    @mcp.tool(
        annotations=_TOOL_ANNOTATIONS,
        description=(
            "Get all draft picks for a given Sleeper draft ID. Use for comprehensive draft analysis, "
            "identifying reaches and steals, and reviewing draft strategy by round."
        ),
    )
    def get_sleeper_all_draft_picks_by_id(draft_id: str) -> dict:
        return _get_sleeper_all_draft_picks_by_id(draft_id)
