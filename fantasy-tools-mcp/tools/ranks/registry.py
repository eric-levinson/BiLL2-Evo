from fastmcp import FastMCP
from supabase import Client

from .info import (
    get_fantasy_rank_page_types as _get_fantasy_rank_page_types,
)
from .info import (
    get_fantasy_ranks as _get_fantasy_ranks,
)

# All BiLL2 tools are read-only queries with no write-back capability
_TOOL_ANNOTATIONS = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": False,
}


def register_tools(mcp: FastMCP, supabase: Client):
    """Register ranks-related tools with the FastMCP instance."""

    @mcp.tool(
        annotations=_TOOL_ANNOTATIONS,
        description=(
            "Get distinct dynasty rank page types for context. Discover available dynasty ranking sources "
            "for trade value assessment. Returns a list of unique page_type values from vw_dynasty_ranks."
        ),
    )
    def get_fantasy_rank_page_types() -> list[str]:
        return _get_fantasy_rank_page_types(supabase)

    @mcp.tool(
        annotations=_TOOL_ANNOTATIONS,
        description=(
            "Fetch dynasty ranks from vw_dynasty_ranks, filtered by position and/or page_type (optional). "
            "Use for dynasty trade value assessment, player valuation, buy-low/sell-high target identification, "
            "positional rankings, and expert consensus ranking (ECR). "
            "Accepts an optional `limit` (default 30) to control rows returned. Returns the most pertinent columns for fantasy analysis."
        ),
    )
    def get_fantasy_ranks(
        position: str | None = None, page_type: str | None = None, limit: int | None = 30
    ) -> list[dict]:
        return _get_fantasy_ranks(supabase, position, page_type, limit)
