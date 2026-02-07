from fastmcp import FastMCP
from .info import search_web

def register_tools(mcp: FastMCP):
    """
    Register web search tools with the FastMCP instance.
    """
    @mcp.tool(
        description="Search the web for current NFL news, injury reports, fantasy analysis, and breaking stories. Returns relevant articles with titles, URLs, snippets, and source citations."
    )
    def web_search_tool(query: str, max_results: int = 5) -> dict:
        return search_web(query, max_results)
