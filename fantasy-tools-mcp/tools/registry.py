"""
Central registry for all MCP tools.
"""

import importlib.util
import os
import sys

from fastmcp import FastMCP
from supabase import Client

from tools.dictionary.registry import register_tools as register_dictionary_tools
from tools.fantasy.registry import register_tools as register_fantasy_tools
from tools.league.registry import register_tools as _register_league_tools
from tools.metrics.registry import register_tools as register_metrics_tools
from tools.player.registry import register_tools as register_player_tools
from tools.ranks.registry import register_tools as register_ranks_tools
from tools.trade.registry import register_tools as register_trade_tools
from tools.websearch.registry import register_tools as register_websearch_tools


def register_tools(mcp: FastMCP, supabase: Client):
    """
    Register all tools and resources with the FastMCP instance.

    Args:
        mcp: The FastMCP instance
        supabase: The Supabase client instance
    """

    # Register Resources
    _register_resources(mcp)

    # Register player tools from submodule
    register_player_tools(mcp, supabase)

    # Register ranks tools from submodule
    register_ranks_tools(mcp, supabase)

    # Register fantasy tools from submodule
    register_fantasy_tools(mcp, supabase)

    # Register dictionary tools from submodule
    register_dictionary_tools(mcp, supabase)

    # Register metrics
    register_metrics_tools(mcp, supabase)

    # Register league tools
    _register_league_tools(mcp, supabase)

    # Register trade tools
    register_trade_tools(mcp, supabase)

    # Register websearch tools
    register_websearch_tools(mcp, supabase)


def _register_resources(mcp: FastMCP):
    """Register MCP resources."""

    @mcp.resource("metrics://catalog")
    def get_metrics_catalog() -> str:
        """
        Complete NFL metrics catalog with definitions for all categories and subcategories.
        """
        return _load_metrics_catalog()

    @mcp.resource("metrics://receiving")
    def get_receiving_metrics() -> str:
        """
        NFL receiving metrics definitions organized by volume, efficiency, and situational categories.
        """
        catalog = _load_metrics_catalog_dict()
        return str(catalog.get("receiving", {}))

    @mcp.resource("metrics://passing")
    def get_passing_metrics() -> str:
        """
        NFL passing metrics definitions organized by volume, efficiency, and situational categories.
        """
        catalog = _load_metrics_catalog_dict()
        return str(catalog.get("passing", {}))

    @mcp.resource("metrics://rushing")
    def get_rushing_metrics() -> str:
        """
        NFL rushing metrics definitions organized by volume, efficiency, and situational categories.
        """
        catalog = _load_metrics_catalog_dict()
        return str(catalog.get("rushing", {}))

    @mcp.resource("metrics://defense")
    def get_defense_metrics() -> str:
        """
        NFL defensive metrics definitions organized by volume, efficiency, and situational categories.
        """
        catalog = _load_metrics_catalog_dict()
        return str(catalog.get("defense", {}))


def _load_metrics_catalog() -> str:
    """Load the complete metrics catalog as a formatted string."""
    catalog = _load_metrics_catalog_dict()

    # Format as readable text
    result = "# NFL Metrics Catalog\n\n"

    for category, subcategories in catalog.items():
        result += f"## {category.title()} Metrics\n\n"

        for subcat, metrics in subcategories.items():
            result += f"### {subcat.replace('_', ' ').title()}\n"
            for metric, definition in metrics.items():
                result += f"- **{metric}**: {definition}\n"
            result += "\n"

    return result


def _load_metrics_catalog_dict() -> dict:
    """Load the metrics catalog dictionary from docs/metrics_catalog.py"""
    current_dir = os.path.dirname(__file__)
    docs_dir = os.path.abspath(os.path.join(current_dir, "..", "docs"))
    metrics_file = os.path.join(docs_dir, "metrics_catalog.py")

    if docs_dir not in sys.path:
        sys.path.insert(0, docs_dir)

    try:
        spec = importlib.util.spec_from_file_location("metrics_catalog", metrics_file)
        metrics_catalog_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(metrics_catalog_module)
        return metrics_catalog_module.metrics_catalog
    except Exception as e:
        return {"error": f"Could not load metrics catalog: {e}"}
    finally:
        if docs_dir in sys.path:
            sys.path.remove(docs_dir)

    # You can add more tools here as you create them
    # For example:
    # @mcp.tool(description="Get player stats")
    # def get_player_stats(player_id: str) -> dict:
    #     return _get_player_stats(supabase, player_id)
