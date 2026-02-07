from fastmcp import FastMCP
from .info import web_search

def register_tools(mcp: FastMCP):
    """
    Register web search tools with the FastMCP instance.
    """
    @mcp.tool(
        description="Perform a web search for fantasy football information, news, and analysis. Returns relevant articles and content from across the web."
    )
    def web_search_tool(query: str, max_results: int = 5) -> list[dict]:
        return web_search(query, max_results)
