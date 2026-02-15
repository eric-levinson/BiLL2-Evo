"""
Player information tools for fantasy football analysis.
"""

from concurrent.futures import ThreadPoolExecutor

from supabase import Client

from helpers.name_utils import sanitize_name
from tools.metrics.info import (
    get_advanced_passing_stats,
    get_advanced_receiving_stats,
    get_advanced_rushing_stats,
)


def get_player_info(supabase: Client, player_names: list[str]) -> list[dict]:
    """
    Fetch basic information for players such as: name, latest team, position,
    height, weight, birthdate (age) and identifiers.

    Args:
        supabase: The Supabase client instance
        player_names: List of player names to search for
    """
    try:
        if not player_names:
            return [{"error": "Please submit list of player names to search for as array of strings"}]
        sanitized_names = [sanitize_name(name) for name in player_names]
        query = supabase.table("mv_player_id_lookup").select(
            "display_name, latest_team, position, height, weight, age, sleeper_id, gsis_id, years_of_experience"
        )
        if sanitized_names:
            or_filter = ",".join([f"merge_name.ilike.%{name}%,display_name.ilike.%{name}%" for name in sanitized_names])
            query = query.or_(or_filter)
        response = query.limit(35).execute()
        return response.data
    except Exception as e:
        raise Exception(f"Error fetching player info: {e!s}") from None


def get_players_by_sleeper_id(supabase: Client, sleeper_ids: list[str]) -> list[dict]:
    """
    Fetch basic information for players by their Sleeper IDs.

    Args:
        supabase: The Supabase client instance
        sleeper_ids: List of Sleeper IDs to search for
    """
    try:
        if not sleeper_ids:
            return [{"error": "Please submit list of Sleeper IDs to search for as array of strings"}]
        sanitized_ids = [sanitize_name(sleeper_id) for sleeper_id in sleeper_ids]
        query = supabase.table("mv_player_id_lookup").select(
            "display_name, latest_team, position, height, weight, age, sleeper_id, gsis_id, years_of_experience"
        )
        if sanitized_ids:
            or_filter = ",".join([f"sleeper_id.eq.{sleeper_id}" for sleeper_id in sanitized_ids])
            query = query.or_(or_filter)
        response = query.limit(35).execute()
        return response.data
    except Exception as e:
        raise Exception(f"Error fetching player info by Sleeper ID: {e!s}") from None


def get_player_profile(
    supabase: Client,
    player_names: list[str],
    season_list: list[int] | None = None,
    metrics: list[str] | None = None,
    limit: int | None = 25,
) -> dict:
    """
    Fetch comprehensive player profile combining basic info and all available stats.

    This is a unified tool that combines basic player information with receiving,
    passing, and rushing stats in a single call, reducing the need for 3-4 separate
    tool calls to build a complete player profile.

    Args:
        supabase: The Supabase client instance
        player_names: List of player names to search for
        season_list: Optional list of seasons to include
        metrics: Optional list of metric codes to return
        limit: Optional max rows to return per stats category (defaults to 25)

    Returns:
        dict: Unified player profile with keys:
            - playerInfo: Basic player information (name, team, position, etc.)
            - receivingStats: Advanced receiving statistics (may be empty for non-receivers)
            - passingStats: Advanced passing statistics (may be empty for non-QBs)
            - rushingStats: Advanced rushing statistics (may be empty for non-rushers)
    """
    try:
        if not player_names:
            return {
                "error": "Please submit list of player names to search for as array of strings",
                "playerInfo": [],
                "receivingStats": [],
                "passingStats": [],
                "rushingStats": [],
            }

        # Fetch player info and all stats categories in parallel
        # (ThreadPoolExecutor avoids asyncio.run() conflicts with FastMCP's event loop)
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_info = executor.submit(get_player_info, supabase, player_names)
            future_receiving = executor.submit(
                get_advanced_receiving_stats,
                supabase=supabase,
                player_names=player_names,
                season_list=season_list,
                metrics=metrics,
                limit=limit,
            )
            future_passing = executor.submit(
                get_advanced_passing_stats,
                supabase=supabase,
                player_names=player_names,
                season_list=season_list,
                metrics=metrics,
                limit=limit,
            )
            future_rushing = executor.submit(
                get_advanced_rushing_stats,
                supabase=supabase,
                player_names=player_names,
                season_list=season_list,
                metrics=metrics,
                limit=limit,
            )
            player_info = future_info.result()
            receiving_stats = future_receiving.result()
            passing_stats = future_passing.result()
            rushing_stats = future_rushing.result()

        return {
            "playerInfo": player_info,
            "receivingStats": receiving_stats.get("advReceivingStats", []),
            "passingStats": passing_stats.get("advPassingStats", []),
            "rushingStats": rushing_stats.get("advRushingStats", []),
        }

    except Exception as e:
        raise Exception(f"Error fetching player profile: {e!s}") from None
