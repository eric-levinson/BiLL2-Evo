"""
MCP tool registration for player deep dive.
"""

from fastmcp import FastMCP
from supabase import Client

from .info import get_player_deep_dive as _get_player_deep_dive

# All BiLL2 tools are read-only queries with no write-back capability
_TOOL_ANNOTATIONS = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": False,
}


def register_tools(mcp: FastMCP, supabase: Client):
    """Register player deep dive tools with the FastMCP instance."""

    @mcp.tool(
        annotations=_TOOL_ANNOTATIONS,
        description=(
            "Fetch comprehensive player analysis data in a single call. "
            "This composite tool replaces 4-6 sequential tool calls by assembling "
            "player bio, season stats with positional percentile ranks, consistency "
            "metrics (floor/ceiling/boom-bust), dynasty rankings, optional weekly game "
            "log, and target share / usage trends in parallel.\n\n"
            "Returns a data-only bundle with zero analysis or opinions — the LLM interprets the data.\n\n"
            "Use for: player evaluation, deep dive analysis, breakout identification, "
            "sell-high/buy-low assessment, dynasty valuation, keeper decisions, "
            "draft preparation, trade target research.\n\n"
            "Parameters:\n"
            "- player_name: The player to analyze\n"
            "- scoring_format: 'ppr' (default), 'half_ppr', or 'standard'\n"
            "- include_game_log: If True, includes recent weekly game log (default False)\n"
            "- recent_weeks: Number of recent weeks for game log and trends (default 6)\n\n"
            "Returns: player bio (name, position, team, age, experience, height, weight), "
            "season stats with positional percentile ranks (e.g. target_share_pctile: 95 means "
            "top 5% at position), consistency metrics (avg FP, stddev, floor P10, ceiling P90, "
            "boom/bust counts, consistency coefficient), dynasty ranking (ECR, positional rank), "
            "weekly game log with fantasy points (if requested), and target share / usage trends.\n\n"
            "Keywords: player evaluation, deep dive, breakout, sell-high, buy-low, dynasty value, "
            "keeper, draft prep, player research, scouting report, player profile"
        ),
    )
    def get_player_deep_dive(
        player_name: str,
        scoring_format: str = "ppr",
        include_game_log: bool = False,
        recent_weeks: int = 6,
    ) -> dict:
        return _get_player_deep_dive(
            supabase,
            player_name,
            scoring_format,
            include_game_log,
            recent_weeks,
        )
