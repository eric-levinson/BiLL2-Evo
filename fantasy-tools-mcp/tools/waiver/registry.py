"""
MCP tool registration for waiver wire context.
"""

from fastmcp import FastMCP
from supabase import Client

from .info import get_waiver_context as _get_waiver_context

# All BiLL2 tools are read-only queries with no write-back capability
_TOOL_ANNOTATIONS = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": False,
}


def register_tools(mcp: FastMCP, supabase: Client):
    """Register waiver wire evaluation tools with the FastMCP instance."""

    @mcp.tool(
        annotations=_TOOL_ANNOTATIONS,
        description=(
            "Fetch all data needed for waiver wire decisions in a single call. "
            "This composite tool replaces 3-4 sequential tool calls by assembling "
            "trending player adds from Sleeper, season stats with positional percentile "
            "ranks, consistency metrics, dynasty rankings, and league roster availability "
            "in parallel.\n\n"
            "Returns a data-only bundle with zero analysis or opinions — the LLM interprets the data.\n\n"
            "Use for: waiver wire pickups, free agent evaluation, must-add identification, "
            "roster improvement, streaming targets, league winner hunting.\n\n"
            "Parameters:\n"
            "- league_id: Sleeper league ID (required for roster availability check)\n"
            "- position_filter: Optional position filter ('QB', 'RB', 'WR', 'TE')\n"
            "- scoring_format: 'ppr' (default), 'half_ppr', or 'standard'\n"
            "- top_n: Number of trending players to evaluate (default 10, max 25)\n\n"
            "Each player bundle includes: trending add count, roster availability in your league, "
            "season stats with positional percentile ranks, consistency metrics "
            "(avg FP, floor/ceiling, boom/bust), and dynasty ranking.\n\n"
            "Keywords: waiver wire, free agent, pickup, must-add, streaming, roster move, "
            "add/drop, FAAB, waiver priority, league winner"
        ),
    )
    def get_waiver_context(
        league_id: str,
        position_filter: str | None = None,
        scoring_format: str = "ppr",
        top_n: int = 10,
    ) -> dict:
        return _get_waiver_context(
            supabase,
            league_id,
            position_filter,
            scoring_format,
            top_n,
        )
