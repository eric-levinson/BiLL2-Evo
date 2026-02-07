"""
Web search tools for fantasy football research and analysis.
"""
import os
from tavily import TavilyClient


def web_search(query: str, max_results: int = 5) -> list[dict]:
    """
    Perform a web search using Tavily API for fantasy football information.

    Args:
        query: The search query string
        max_results: Maximum number of results to return (default: 5, max: 10)

    Returns:
        List of search results with title, url, content, and score
    """
    try:
        if not query:
            return [{"error": "Please provide a search query"}]

        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise Exception("TAVILY_API_KEY environment variable not set")

        client = TavilyClient(api_key=api_key)

        # Limit max_results to reasonable bounds
        max_results = min(max(1, max_results), 10)

        response = client.search(
            query=query,
            max_results=max_results,
            search_depth="advanced",
            include_answer=True,
            include_raw_content=False
        )

        return response.get("results", [])
    except Exception as e:
        raise Exception(f"Error performing web search: {str(e)}")
