"""
MCP tool registration for start/sit context.
"""

from fastmcp import FastMCP
from supabase import Client

from .info import get_start_sit_context as _get_start_sit_context

# All BiLL2 tools are read-only queries with no write-back capability
_TOOL_ANNOTATIONS = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": False,
}


def register_tools(mcp: FastMCP, supabase: Client):
    """Register start/sit evaluation tools with the FastMCP instance."""

    @mcp.tool(
        annotations=_TOOL_ANNOTATIONS,
        description=(
            "Fetch all data needed for a fantasy start/sit decision in a single call. "
            "This composite tool replaces 4-5 sequential tool calls by assembling "
            "player season stats with positional percentile ranks, weekly performance "
            "for the target week, consistency metrics (floor/ceiling/boom-bust), and "
            "dynasty rankings in parallel.\n\n"
            "Returns a data-only bundle with zero analysis or opinions — the LLM interprets the data.\n\n"
            "Use for: start/sit decisions, weekly lineup optimization, matchup analysis, "
            "flex spot evaluation, streaming decisions, DFS lineup construction.\n\n"
            "Parameters:\n"
            "- player_names: Players to compare for start/sit (1-8 names)\n"
            "- week: NFL week number (1-18) to evaluate\n"
            "- season: Optional season year (defaults to most recent)\n"
            "- scoring_format: 'ppr' (default), 'half_ppr', or 'standard'\n\n"
            "Each player bundle includes: basic info (name, position, team, age), "
            "season stats with positional percentile ranks (e.g. target_share_pctile: 95 means "
            "top 5% at position), weekly performance for the specified week, consistency metrics "
            "(avg FP, floor/ceiling, boom/bust counts, consistency coefficient), and dynasty ranking.\n\n"
            "Keywords: start/sit, lineup decision, who do I start, weekly lineup, matchup analysis, "
            "flex play, streaming, DFS, daily fantasy"
        ),
    )
    def get_start_sit_context(
        player_names: list[str],
        week: int,
        season: int | None = None,
        scoring_format: str = "ppr",
    ) -> dict:
        return _get_start_sit_context(
            supabase,
            player_names,
            week,
            season,
            scoring_format,
        )
