"""
Web search tools for fantasy football research and analysis.
"""
import os
from tavily import TavilyClient
from helpers.retry_utils import retry_with_backoff


@retry_with_backoff()
def search_web(query: str, max_results: int = 5) -> dict:
    """
    Search the web for current NFL news, injury reports, fantasy analysis, and breaking stories.

    Uses Tavily API to retrieve relevant, up-to-date information from across the web.
    Results are formatted for easy consumption by the AI agent.

    Args:
        query: The search query string (e.g., "Patrick Mahomes injury update", "CMC fantasy outlook")
        max_results: Maximum number of results to return (default: 5, max: 10)

    Returns:
        Dictionary containing:
            - results: List of search results, each with:
                - title: Article/page title
                - url: Source URL
                - content: Relevant snippet/excerpt
                - score: Relevance score (0-1)
                - published_date: Publication date (if available)
            - answer: AI-generated summary answer (if available)
            - query: The original search query

    Raises:
        Exception: If API call fails after retry attempts
    """
    try:
        # Validate input
        if not query or not query.strip():
            return {
                "error": "Please provide a search query",
                "results": [],
                "query": query
            }

        # Get API key
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            return {
                "error": "TAVILY_API_KEY environment variable not set. Please configure your API key.",
                "results": [],
                "query": query
            }

        # Initialize client
        client = TavilyClient(api_key=api_key)

        # Limit max_results to reasonable bounds (1-10)
        max_results = min(max(1, max_results), 10)

        # Perform search with advanced depth for better quality results
        # include_answer provides an AI-generated summary
        # include_raw_content=False keeps response concise
        response = client.search(
            query=query,
            max_results=max_results,
            search_depth="advanced",
            include_answer=True,
            include_raw_content=False
        )

        # Format results for consistency
        formatted_results = []
        for result in response.get("results", []):
            formatted_result = {
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "content": result.get("content", ""),  # Tavily calls it 'content', notes call it 'snippet'
                "score": result.get("score", 0.0),
            }
            # Add published_date if available (Tavily may not always provide this)
            if "published_date" in result:
                formatted_result["published_date"] = result["published_date"]

            formatted_results.append(formatted_result)

        return {
            "results": formatted_results,
            "answer": response.get("answer", ""),  # AI-generated summary
            "query": query,
            "response_time": response.get("response_time", 0)
        }

    except Exception as e:
        # Let retry_with_backoff handle retryable errors
        # For non-retryable errors or exhausted retries, raise with context
        raise Exception(f"Error performing web search for query '{query}': {str(e)}")
