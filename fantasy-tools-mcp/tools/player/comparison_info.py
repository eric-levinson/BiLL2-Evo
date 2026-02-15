"""
Player comparison logic for side-by-side analysis.
"""

from concurrent.futures import ThreadPoolExecutor

from supabase import Client

from tools.player.info import get_player_profile


def compare_players(
    supabase: Client,
    player_names: list[str],
    metrics: list[str] | None = None,
    season: int | None = None,
    summary: bool = False,
) -> dict:
    """
    Compare 2-5 players side-by-side with their stats and profiles.

    Fetches comprehensive player profiles in parallel and structures the output
    for easy markdown table rendering or programmatic comparison.

    Args:
        supabase: The Supabase client instance
        player_names: List of 2-5 player names to compare
        metrics: Optional list of specific metrics to include (defaults to position-relevant metrics)
        season: Optional season year to filter stats (defaults to all available seasons)
        summary: If True, returns compact output with key metrics only (default False)

    Returns:
        dict: Structured comparison data with keys:
            - players: List of player names being compared
            - playerInfo: Side-by-side basic info for each player
            - receivingStats: Side-by-side receiving stats (if applicable)
            - passingStats: Side-by-side passing stats (if applicable)
            - rushingStats: Side-by-side rushing stats (if applicable)
            - summary: Comparison summary with key differences (if summary=True)

    Raises:
        ValueError: If player_names list is not 2-5 players
        Exception: If fetching player profiles fails
    """
    try:
        # Validate input
        if not player_names or len(player_names) < 2:
            raise ValueError("Please provide at least 2 player names to compare")
        if len(player_names) > 5:
            raise ValueError("Maximum 5 players can be compared at once")

        # Build season filter
        season_list = [season] if season else None

        # Fetch all player profiles in parallel using threads
        # (ThreadPoolExecutor avoids asyncio.run() conflicts with FastMCP's event loop)
        def _fetch_profile(name):
            return get_player_profile(
                supabase=supabase,
                player_names=[name],
                season_list=season_list,
                metrics=metrics,
                limit=25,
            )

        with ThreadPoolExecutor(max_workers=len(player_names)) as executor:
            profiles = list(executor.map(_fetch_profile, player_names))

        # Structure the comparison output
        comparison = {
            "players": player_names,
            "playerInfo": [],
            "receivingStats": [],
            "passingStats": [],
            "rushingStats": [],
        }

        # Extract data for each player
        for idx, profile in enumerate(profiles):
            if not profile:
                continue

            # Add player info
            player_info = profile.get("playerInfo", [])
            if player_info:
                comparison["playerInfo"].append(
                    {
                        "player": player_names[idx],
                        "info": player_info[0] if player_info else None,
                    }
                )

            # Add stats by category
            receiving = profile.get("receivingStats", [])
            if receiving:
                comparison["receivingStats"].append(
                    {
                        "player": player_names[idx],
                        "stats": receiving,
                    }
                )

            passing = profile.get("passingStats", [])
            if passing:
                comparison["passingStats"].append(
                    {
                        "player": player_names[idx],
                        "stats": passing,
                    }
                )

            rushing = profile.get("rushingStats", [])
            if rushing:
                comparison["rushingStats"].append(
                    {
                        "player": player_names[idx],
                        "stats": rushing,
                    }
                )

        # Add summary if requested
        if summary:
            comparison["summary"] = _generate_summary(comparison)

        return comparison

    except ValueError:
        raise
    except Exception as e:
        raise Exception(f"Error comparing players: {e!s}") from e


def _generate_summary(comparison: dict) -> dict:
    """
    Generate a summary highlighting key differences between players.

    Args:
        comparison: The full comparison dict

    Returns:
        dict: Summary with key metrics and differences
    """
    summary = {
        "player_count": len(comparison["players"]),
        "positions": [],
        "key_differences": [],
    }

    # Extract positions
    for player_data in comparison["playerInfo"]:
        info = player_data.get("info")
        if info:
            summary["positions"].append(
                {
                    "player": player_data["player"],
                    "position": info.get("position"),
                    "team": info.get("latest_team"),
                    "age": info.get("age"),
                    "experience": info.get("years_of_experience"),
                }
            )

    # Identify which stat categories are relevant
    has_receiving = len(comparison["receivingStats"]) > 0
    has_passing = len(comparison["passingStats"]) > 0
    has_rushing = len(comparison["rushingStats"]) > 0

    summary["stat_categories"] = {
        "receiving": has_receiving,
        "passing": has_passing,
        "rushing": has_rushing,
    }

    return summary
