"""
MCP tool registration for player comparison.
"""

from fastmcp import FastMCP
from supabase import Client

from .comparison_info import compare_players as _compare_players


def register_comparison_tools(mcp: FastMCP, supabase: Client):
    """
    Register player comparison tools with the FastMCP instance.
    """

    @mcp.tool(
        description="""
        Compare 2-5 players side-by-side with their stats and profiles.

        Fetches comprehensive player profiles in parallel and structures the output
        for easy markdown table rendering or programmatic comparison. Useful for:
        - Draft decisions (comparing players in the same tier)
        - Trade evaluations (comparing players being swapped)
        - Start/sit decisions (comparing weekly matchups)
        - Dynasty value assessment (comparing age, experience, production)

        Returns structured data with:
        - Basic player info (name, team, position, age, experience)
        - Receiving stats (for WR/TE/RB positions)
        - Passing stats (for QB positions)
        - Rushing stats (for RB/QB positions)

        The tool automatically fetches position-relevant stats. Stats categories
        may be empty for positions that don't typically record those stats.

        Use the `summary` parameter for a compact view with key differences highlighted.
        Use the `metrics` parameter to focus on specific stats of interest.
        Use the `season` parameter to compare single-season performance.

        For detailed metric definitions, use the get_metrics_metadata tool.

        Keywords: sell-high, buy-low, league winner, breakout candidate, smash spot, target hog, workhorse back
        """
    )
    def compare_players(
        player_names: list[str],
        metrics: list[str] | None = None,
        season: int | None = None,
        summary: bool = False,
    ) -> dict:
        return _compare_players(
            supabase,
            player_names,
            metrics,
            season,
            summary,
        )
