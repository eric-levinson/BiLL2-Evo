from fastmcp import FastMCP
from supabase import Client

from .comparison_registry import register_comparison_tools
from .info import get_player_info, get_players_by_sleeper_id
from .info import get_player_profile as _get_player_profile


def register_tools(mcp: FastMCP, supabase: Client):
    """
    Register player info tools with the FastMCP instance.
    """
    # Register comparison tools
    register_comparison_tools(mcp, supabase)

    @mcp.tool(
        description=(
            "Look up NFL player information including name, team, position, age, and identifiers. "
            "Essential first step for trade evaluation, start/sit analysis, waiver wire decisions, "
            "and dynasty valuation. Use to verify player identity, confirm team affiliation, and "
            "check age for dynasty value assessment."
        )
    )
    def get_player_info_tool(player_names: list[str]) -> list[dict]:
        return get_player_info(supabase, player_names)

    @mcp.tool(
        description=(
            "Fetch basic player information by Sleeper IDs. Essential for resolving Sleeper roster "
            "player IDs to real player names and stats. Use when analyzing league rosters, trending "
            "players from Sleeper, or matchup lineups to convert Sleeper's player_id format into "
            "actionable player data for trade evaluation and waiver wire recommendations."
        )
    )
    def get_players_by_sleeper_id_tool(sleeper_ids: list[str]) -> list[dict]:
        return get_players_by_sleeper_id(supabase, sleeper_ids)

    @mcp.tool(
        description="""
        Fetch comprehensive player profile combining basic info and all available stats in a single call.

        This unified tool reduces the need for 3-4 separate tool calls by combining:
        - Basic player information (name, team, position, height, weight, age, identifiers)
        - Advanced receiving statistics (for WR/TE/RB positions)
        - Advanced passing statistics (for QB positions)
        - Advanced rushing statistics (for RB/QB positions)

        Use for: trade evaluation, breakout identification, sell-high/buy-low analysis, dynasty valuation,
        start/sit decisions, and roster construction. Perfect for one-stop player analysis when you need
        the complete picture for fantasy decisions.

        - Optional filters: player_names (partial matches), season_list, metrics.
        - Optional controls: limit (default 25, max rows per stats category).

        Returns a unified dict with keys: playerInfo, receivingStats, passingStats, rushingStats.
        Stats categories may be empty for positions that don't typically record those stats.

        For detailed metric definitions, use the get_metrics_metadata tool.
        """
    )
    def get_player_profile(
        player_names: list[str],
        season_list: list[int] | None = None,
        metrics: list[str] | None = None,
        limit: int | None = 25,
    ) -> dict:
        return _get_player_profile(
            supabase,
            player_names,
            season_list,
            metrics,
            limit,
        )
