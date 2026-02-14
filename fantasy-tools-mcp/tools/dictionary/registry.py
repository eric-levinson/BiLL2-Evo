from fastmcp import FastMCP
from supabase import Client

from .info import get_dictionary_info as _get_dictionary_info


def register_tools(mcp: FastMCP, supabase: Client):
    """Register dictionary-related tools with the FastMCP instance."""

    @mcp.tool(
        description=(
            "Fetch rows from the combined dictionary view, optionally filtering "
            "by search criteria in the description. Parameter: search_criteria "
            "(list[str], optional)."
        )
    )
    def get_dictionary_info(search_criteria: list[str] | None = None) -> list[dict]:
        return _get_dictionary_info(supabase, search_criteria)
