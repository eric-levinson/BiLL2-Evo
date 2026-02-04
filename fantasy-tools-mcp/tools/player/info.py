"""
Player information tools for fantasy football analysis.
"""
from supabase import Client
from helpers.name_utils import sanitize_name


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
        query = supabase.table("vw_nfl_players_with_dynasty_ids").select("display_name, latest_team, position, height, weight, age, sleeper_id, gsis_id, years_of_experience")
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
        query = supabase.table("vw_nfl_players_with_dynasty_ids").select("display_name, latest_team, position, height, weight, age, sleeper_id, gsis_id, years_of_experience")
        if sanitized_ids:
            or_filter = ",".join([f"sleeper_id.eq.{sleeper_id}" for sleeper_id in sanitized_ids])
            query = query.or_(or_filter)
        response = query.limit(35).execute()
        return response.data
    except Exception as e:
        raise Exception(f"Error fetching player info by Sleeper ID: {str(e)}")