from fastmcp import FastMCP
from supabase import Client
from .info import get_sleeper_leagues_by_username as _get_sleeper_leagues_by_username
from .info import get_sleeper_league_rosters as _get_sleeper_league_rosters
from .info import get_sleeper_league_users as _get_sleeper_league_users
from .info import get_sleeper_league_matchups as _get_sleeper_league_matchups
from .info import get_sleeper_league_transactions as _get_sleeper_league_transactions
from .info import get_sleeper_trending_players as _get_sleeper_trending_players
from .info import get_sleeper_user_drafts as _get_sleeper_user_drafts
from .info import get_sleeper_league_by_id as _get_sleeper_league_by_id
from .info import get_sleeper_draft_by_id as _get_sleeper_draft_by_id
from .info import get_sleeper_all_draft_picks_by_id as _get_sleeper_all_draft_picks_by_id


def register_tools(mcp: FastMCP, supabase: Client):
    """Register fantasy-related tools with the FastMCP instance."""

    @mcp.tool(
        description=(
            "Fetch sleeper leagues for a specific user by their username. "
            "Returns a filtered list of league objects. If verbose is True, "
            "includes scoring_settings, settings, and roster_positions."
        )
    )
    def get_sleeper_leagues_by_username(username: str, verbose: bool = False) -> list[dict]:
        return _get_sleeper_leagues_by_username(username, verbose)

    @mcp.tool(
        description=(
            "Get the raw league data for a given Sleeper league ID. "
            "Returns the league object as returned by the Sleeper API."
        )
    )
    def get_sleeper_league_rosters(league_id: str) -> list[dict]:
        return _get_sleeper_league_rosters(league_id)

    @mcp.tool(
        description=(
            "Get the users for a given Sleeper league ID. "
            "Returns a list of user objects as returned by the Sleeper API."
        )
    )
    def get_sleeper_league_users(league_id: str) -> list[dict]:
        return _get_sleeper_league_users(league_id)

    @mcp.tool(
        description=(
            "Get the raw matchup data for a given Sleeper league ID and week. "
            "The caller must provide the target week."
        )
    )
    def get_sleeper_league_matchups(league_id: str, week: int) -> list[dict]:
        return _get_sleeper_league_matchups(league_id, week)

    @mcp.tool(
        description=(
            "Get transactions for a given Sleeper league ID and week. "
            "Optionally filter by transaction type such as 'trade', 'waiver', "
            "or 'free_agent'."
        )
    )
    def get_sleeper_league_transactions(
        league_id: str, week: int, txn_type: str | None = None
    ) -> list[dict]:
        return _get_sleeper_league_transactions(league_id, week, txn_type)

    @mcp.tool(
        description=(
            "Get trending players for the specified sport from Sleeper. "
            "Use add_drop to choose adds or drops, hours to set the lookback "
            "period, and limit for the number of players returned."
        )
    )
    def get_sleeper_trending_players(
        sport: str = "nfl", add_drop: str = "add", hours: int = 24, limit: int = 25
    ) -> list[dict]:
        return _get_sleeper_trending_players(sport, add_drop, hours, limit)

    @mcp.tool(
        description=(
            "Get all drafts for a Sleeper user. "
            "Provide the username and optionally sport and season. "
            "Returns a list of draft objects as returned by the Sleeper API."
        )
    )
    def get_sleeper_user_drafts(
        username: str, sport: str = "nfl", season: int = 2025
    ) -> list[dict]:
        return _get_sleeper_user_drafts(username, sport, season)

    @mcp.tool(
        description=(
            "Get a Sleeper league by its ID. If summary is True, returns compact "
            "league data without nested settings objects. If False (default), "
            "includes basic info, scoring settings, league settings, and roster positions."
        )
    )
    def get_sleeper_league_by_id(league_id: str, summary: bool = False) -> dict:
        return _get_sleeper_league_by_id(league_id, summary)
    
    @mcp.tool(
        description=(
            "Get a Sleeper draft by its ID. Includes basic info, participants, and draft settings."
        )
    )
    def get_sleeper_draft_by_id(draft_id: str ) -> dict:
        return _get_sleeper_draft_by_id(draft_id)

    @mcp.tool(
        description=(
            "Get all draft picks for a given Sleeper draft ID."
        )
    )
    def get_sleeper_all_draft_picks_by_id(draft_id: str) -> dict:
        return _get_sleeper_all_draft_picks_by_id(draft_id)
