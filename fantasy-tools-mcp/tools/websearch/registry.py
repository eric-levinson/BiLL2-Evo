from fastmcp import FastMCP
from supabase import Client

from .info import search_web

# Web search queries external APIs but is still read-only and non-destructive.
# openWorldHint=True because results depend on external web state.
_TOOL_ANNOTATIONS = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": False,
    "openWorldHint": True,
}


def register_tools(mcp: FastMCP, supabase: Client):
    """
    Register web search tools with the FastMCP instance.
    """

    @mcp.tool(
        annotations=_TOOL_ANNOTATIONS,
        description=(
            "Search the web for current NFL news, injury reports, fantasy analysis, and breaking stories. "
            "Use for breaking player news, trade rumors, snap count reports, depth chart changes, practice participation, "
            "and fantasy-relevant updates. Returns up-to-date information with AI-generated summaries."
        ),
    )
    def search_web_tool(query: str, max_results: int = 5) -> dict:
        return search_web(query, max_results)
