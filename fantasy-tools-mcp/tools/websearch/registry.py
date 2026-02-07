from fastmcp import FastMCP
from supabase import Client
from .info import search_web

def register_tools(mcp: FastMCP, supabase: Client):
    """
    Register web search tools with the FastMCP instance.
    """
    @mcp.tool(
        description="Search the web for current NFL news, injury reports, fantasy analysis, and breaking stories. Returns up-to-date information with AI-generated summaries."
    )
    def search_web_tool(query: str, max_results: int = 5) -> dict:
        return search_web(query, max_results)
