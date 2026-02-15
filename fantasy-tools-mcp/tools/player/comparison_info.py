"""
Player comparison logic for side-by-side analysis.
"""

from concurrent.futures import ThreadPoolExecutor

from supabase import Client

from helpers.query_utils import build_player_stats_query
from tools.player.info import get_player_profile
from tools.ranks.info import get_fantasy_ranks


def compare_players(
    supabase: Client,
    player_names: list[str],
    metrics: list[str] | None = None,
    season: int | None = None,
    summary: bool = False,
    scoring_format: str = "ppr",
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
        scoring_format: Scoring format for fantasy points ("ppr", "half_ppr", "standard") (default "ppr")

    Returns:
        dict: Structured comparison data with keys:
            - players: List of player names being compared
            - playerInfo: Side-by-side basic info for each player
            - receivingStats: Side-by-side receiving stats (if applicable)
            - passingStats: Side-by-side passing stats (if applicable)
            - rushingStats: Side-by-side rushing stats (if applicable)
            - dynastyRankings: Dynasty rankings for each player (if available)
            - commonMetrics: Cross-position flex comparison metrics
            - consistency: Consistency metrics for each player (if available)
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

        # Fetch all player profiles, dynasty rankings, and consistency data in parallel
        # (ThreadPoolExecutor avoids asyncio.run() conflicts with FastMCP's event loop)
        def _fetch_profile(name):
            return get_player_profile(
                supabase=supabase,
                player_names=[name],
                season_list=season_list,
                metrics=metrics,
                limit=25,
            )

        def _fetch_dynasty_rankings():
            try:
                return get_fantasy_ranks(supabase=supabase, limit=500)
            except Exception:
                return []

        def _fetch_consistency(name):
            try:
                result = build_player_stats_query(
                    supabase=supabase,
                    table_name="mv_player_consistency",
                    base_columns=[
                        "player_name",
                        "games_played",
                        "avg_fp_ppr",
                        "fp_stddev_ppr",
                        "fp_floor_p10",
                        "fp_ceiling_p90",
                        "boom_games_20plus",
                        "bust_games_under_5",
                        "consistency_coefficient",
                    ],
                    player_name_column="player_name",
                    position_column="ff_position",
                    default_positions=["QB", "RB", "WR", "TE"],
                    return_key="consistency",
                    player_names=[name],
                    limit=1,
                )
                return result.get("consistency", [])
            except Exception:
                return []

        with ThreadPoolExecutor(max_workers=len(player_names) * 2 + 1) as executor:
            # Fetch profiles
            profile_futures = [executor.submit(_fetch_profile, name) for name in player_names]
            # Fetch dynasty rankings once
            rankings_future = executor.submit(_fetch_dynasty_rankings)
            # Fetch consistency data for each player
            consistency_futures = [executor.submit(_fetch_consistency, name) for name in player_names]

            profiles = [f.result() for f in profile_futures]
            all_rankings = rankings_future.result()
            consistency_data = [f.result() for f in consistency_futures]

        # Structure the comparison output
        comparison = {
            "players": player_names,
            "playerInfo": [],
            "receivingStats": [],
            "passingStats": [],
            "rushingStats": [],
            "dynastyRankings": [],
            "commonMetrics": [],
            "consistency": [],
        }

        # Create rankings lookup by player name
        rankings_by_player = {}
        for rank_entry in all_rankings:
            player_name = rank_entry.get("player", "").lower()
            if player_name:
                rankings_by_player[player_name] = rank_entry

        # Extract data for each player
        for idx, profile in enumerate(profiles):
            if not profile:
                continue

            player_name = player_names[idx]
            player_name_lower = player_name.lower()

            # Add player info
            player_info = profile.get("playerInfo", [])
            if player_info:
                comparison["playerInfo"].append(
                    {
                        "player": player_name,
                        "info": player_info[0] if player_info else None,
                    }
                )

            # Add stats by category
            receiving = profile.get("receivingStats", [])
            if receiving:
                comparison["receivingStats"].append(
                    {
                        "player": player_name,
                        "stats": receiving,
                    }
                )

            passing = profile.get("passingStats", [])
            if passing:
                comparison["passingStats"].append(
                    {
                        "player": player_name,
                        "stats": passing,
                    }
                )

            rushing = profile.get("rushingStats", [])
            if rushing:
                comparison["rushingStats"].append(
                    {
                        "player": player_name,
                        "stats": rushing,
                    }
                )

            # Add dynasty rankings if found
            rank_data = rankings_by_player.get(player_name_lower)
            if rank_data:
                comparison["dynastyRankings"].append(
                    {
                        "player": player_name,
                        "ranking": rank_data,
                    }
                )

            # Add consistency data if available
            consistency_info = consistency_data[idx]
            if consistency_info:
                comparison["consistency"].append(
                    {
                        "player": player_name,
                        "consistency": consistency_info[0] if consistency_info else None,
                    }
                )

        # Build common metrics for cross-position comparison
        comparison["commonMetrics"] = _build_common_metrics(comparison, scoring_format)

        # Add summary if requested
        if summary:
            comparison["summary"] = _generate_summary(comparison)

        return comparison

    except ValueError:
        raise
    except Exception as e:
        raise Exception(f"Error comparing players: {e!s}") from e


def _compute_fantasy_points(stats: dict, scoring_format: str) -> float | None:
    """
    Compute format-weighted fantasy points from stats.

    Args:
        stats: Stats dict with keys like receptions, receiving_yards, receiving_tds, etc.
        scoring_format: "ppr", "half_ppr", or "standard"

    Returns:
        float | None: Total fantasy points or None if insufficient data
    """
    try:
        fp = 0.0

        # Receiving points
        rec_yards = stats.get("receiving_yards") or stats.get("rec_yards") or 0
        rec_tds = stats.get("receiving_tds") or stats.get("rec_tds") or 0
        receptions = stats.get("receptions") or stats.get("rec") or 0

        fp += rec_yards * 0.1  # 0.1 per yard
        fp += rec_tds * 6  # 6 per TD

        if scoring_format == "ppr":
            fp += receptions * 1.0
        elif scoring_format == "half_ppr":
            fp += receptions * 0.5

        # Rushing points
        rush_yards = stats.get("rushing_yards") or stats.get("rush_yards") or 0
        rush_tds = stats.get("rushing_tds") or stats.get("rush_tds") or 0

        fp += rush_yards * 0.1
        fp += rush_tds * 6

        # Passing points (4 pt passing TD)
        pass_yards = stats.get("passing_yards") or stats.get("pass_yards") or 0
        pass_tds = stats.get("passing_tds") or stats.get("pass_tds") or 0
        interceptions = stats.get("interceptions") or stats.get("ints") or 0

        fp += pass_yards * 0.04
        fp += pass_tds * 4
        fp -= interceptions * 2

        return fp if fp > 0 else None
    except Exception:
        return None


def _build_common_metrics(comparison: dict, scoring_format: str) -> list[dict]:
    """
    Build common metrics for cross-position flex comparison.

    Args:
        comparison: The comparison dict
        scoring_format: "ppr", "half_ppr", or "standard"

    Returns:
        list[dict]: Common metrics for each player
    """
    common = []

    for player_data in comparison["playerInfo"]:
        player_name = player_data["player"]
        info = player_data.get("info", {})

        # Get dynasty ranking if available
        dynasty_rank = None
        positional_rank = None
        for rank_data in comparison.get("dynastyRankings", []):
            if rank_data["player"] == player_name:
                dynasty_rank = rank_data["ranking"].get("ecr")
                # Extract positional rank from ECR and position
                pos = rank_data["ranking"].get("pos")
                if pos and dynasty_rank:
                    positional_rank = f"{pos}{dynasty_rank}"
                break

        # Compute fantasy points from most recent season stats
        total_fp = None
        # Try to get from most recent receiving/rushing/passing stats
        for stats_category in ["receivingStats", "passingStats", "rushingStats"]:
            stats_list = comparison.get(stats_category, [])
            for stats_data in stats_list:
                if stats_data["player"] == player_name and stats_data.get("stats"):
                    # Get most recent season (stats are ordered by season DESC)
                    recent_stats = stats_data["stats"][0] if stats_data["stats"] else None
                    if recent_stats:
                        fp = _compute_fantasy_points(recent_stats, scoring_format)
                        if fp is not None:
                            total_fp = (total_fp or 0) + fp

        common.append(
            {
                "player": player_name,
                "position": info.get("position"),
                "age": info.get("age"),
                "years_of_experience": info.get("years_of_experience"),
                "dynasty_ecr": dynasty_rank,
                "positional_rank": positional_rank,
                "fantasy_points": total_fp,
                "scoring_format": scoring_format,
            }
        )

    return common


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
