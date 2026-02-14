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
            "Fetch basic information for players such as: name, latest team, position, "
            "height, weight, birthdate (age) and identifiers"
        )
    )
    def get_player_info_tool(player_names: list[str]) -> list[dict]:
        return get_player_info(supabase, player_names)

    @mcp.tool(description="Fetch basic information for players by their Sleeper IDs.")
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
