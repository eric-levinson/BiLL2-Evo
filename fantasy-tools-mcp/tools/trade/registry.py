"""
MCP tool registration for trade context.
"""

from fastmcp import FastMCP
from supabase import Client

from .info import get_trade_context as _get_trade_context


def register_tools(mcp: FastMCP, supabase: Client):
    """Register trade evaluation tools with the FastMCP instance."""

    @mcp.tool(
        description=(
            "Fetch all data needed for a fantasy trade evaluation in a single call. "
            "This composite tool replaces 5-6 sequential tool calls by assembling "
            "player info, season stats with fantasy points (both PPR and standard), "
            "dynasty rankings, consistency metrics, and optional league context in parallel.\n\n"
            "Returns a data-only bundle with zero analysis or opinions — the LLM interprets the data.\n\n"
            "Use for: trade evaluation, buy-low/sell-high analysis, dynasty valuation, "
            "trade offer construction, multi-player package assessment.\n\n"
            "Parameters:\n"
            "- give_player_names: Players being traded away (1-5 names)\n"
            "- receive_player_names: Players being received (1-5 names)\n"
            "- league_id: Optional Sleeper league ID for league-specific context\n"
            "- scoring_format: 'ppr' (default), 'half_ppr', or 'standard'\n"
            "- include_weekly: If True, includes recent weekly fantasy point data\n"
            "- recent_weeks: Number of recent weeks when include_weekly=True (default 4)\n\n"
            "Each player bundle includes: basic info (name, position, team, age), "
            "season stats with fantasy_points and fantasy_points_ppr, dynasty ranking "
            "(ECR, positional rank), and consistency metrics (avg FP, floor/ceiling, boom/bust).\n\n"
            "Keywords: trade evaluation, buy-low, sell-high, dynasty valuation, trade calculator, "
            "trade analyzer, package deal, roster move"
        )
    )
    def get_trade_context(
        give_player_names: list[str],
        receive_player_names: list[str],
        league_id: str | None = None,
        scoring_format: str = "ppr",
        include_weekly: bool = False,
        recent_weeks: int = 4,
    ) -> dict:
        return _get_trade_context(
            supabase,
            give_player_names,
            receive_player_names,
            league_id,
            scoring_format,
            include_weekly,
            recent_weeks,
        )
