"""
Player information tools for fantasy football analysis.
"""
from supabase import Client
from helpers.name_utils import sanitize_name
from tools.metrics.info import (
    get_advanced_receiving_stats,
    get_advanced_passing_stats,
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
        query = supabase.table("vw_nfl_players_with_dynasty_ids").select(
            "display_name, latest_team, position, height, weight, age, sleeper_id, gsis_id, years_of_experience"
        )
        if sanitized_names:
            or_filter = ",".join([f"merge_name.ilike.%{name}%" for name in sanitized_names])
            query = query.or_(or_filter)
        response = query.limit(35).execute()
        return response.data
    except Exception as e:
        raise Exception(f"Error fetching player info: {str(e)}")

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
        query = supabase.table("vw_nfl_players_with_dynasty_ids").select(
            "display_name, latest_team, position, height, weight, age, sleeper_id, gsis_id, years_of_experience"
        )
        if sanitized_ids:
            or_filter = ",".join([f"sleeper_id.eq.{sleeper_id}" for sleeper_id in sanitized_ids])
            query = query.or_(or_filter)
        response = query.limit(35).execute()
        return response.data
    except Exception as e:
        raise Exception(f"Error fetching player info by Sleeper ID: {str(e)}")


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

        # Fetch basic player info
        player_info = get_player_info(supabase, player_names)

        # Fetch all stats categories (let each function handle position defaults)
        receiving_stats = get_advanced_receiving_stats(
            supabase=supabase,
            player_names=player_names,
            season_list=season_list,
            metrics=metrics,
            limit=limit,
        )

        passing_stats = get_advanced_passing_stats(
            supabase=supabase,
            player_names=player_names,
            season_list=season_list,
            metrics=metrics,
            limit=limit,
        )

        rushing_stats = get_advanced_rushing_stats(
            supabase=supabase,
            player_names=player_names,
            season_list=season_list,
            metrics=metrics,
            limit=limit,
        )

        # Combine all results into unified response
        return {
            "playerInfo": player_info,
            "receivingStats": receiving_stats.get("advReceivingStats", []),
            "passingStats": passing_stats.get("advPassingStats", []),
            "rushingStats": rushing_stats.get("advRushingStats", []),
        }

    except Exception as e:
        raise Exception(f"Error fetching player profile: {str(e)}")
