"""
NFL game stats query functions for offensive and defensive players.

This module provides functions to query weekly game stats for NFL offensive and defensive
players. Both query functions have been refactored to use the generic build_player_stats_query
helper from helpers.query_utils to eliminate code duplication and ensure consistent query
behavior.

The refactoring reduced ~140 lines of duplicated query logic across the two functions down
to a single reusable helper function plus thin wrapper functions that specify table-specific
parameters.
"""
import os
import importlib.util
import logging
from supabase import Client
from helpers.query_utils import build_player_stats_query

logger = logging.getLogger(__name__)

def get_stats_metadata(category: str, subcategory: str | None = None) -> dict:
    """
    Return game-stat field definitions for NFL offense/defense.

    Args:
        category: "offense" or "defense" (case-insensitive; also accepts "off"/"def").
        subcategory: optional sub-block name (e.g., "passing", "rushing", "receiving",
                     "pressure_and_sacks", "special_teams", "seasonal").
                     If omitted, returns the entire category block.

    Returns:
        dict: If subcategory is None, returns the category dict.
              Otherwise returns {<subcategory>: <fields>} (empty dict if unknown).
    """
    # Get the path to game_stats_catalog.py
    current_dir = os.path.dirname(__file__)
    metrics_file = os.path.abspath(os.path.join(current_dir, '..', '..', 'docs', 'game_stats_catalog.py'))

    # Check if the file exists
    if not os.path.exists(metrics_file):
        raise FileNotFoundError(f"game_stats_catalog.py not found at {metrics_file}")

    try:
        # Use importlib to dynamically load the module
        spec = importlib.util.spec_from_file_location("game_stats_catalog", metrics_file)
        game_stats_catalog_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(game_stats_catalog_module)  # type: ignore[attr-defined]
        game_stats_catalog = game_stats_catalog_module.game_stats_catalog
    except Exception as e:
        raise ImportError(f"Could not import game_stats_catalog: {e}")

    # Normalize category (allow short aliases)
    cat = (category or "").strip().lower()
    if cat in {"off", "o"}:
        cat = "offense"
    elif cat in {"def", "d"}:
        cat = "defense"

    if cat not in game_stats_catalog:
        available = ", ".join(sorted(game_stats_catalog.keys()))
        raise ValueError(f"Unknown category: '{category}'. Available: {available}")

    if subcategory is None:
        return game_stats_catalog[cat]

    # Case-insensitive subcategory lookup; preserve original key casing in output
    sub = (subcategory or "").strip()
    sub_map = game_stats_catalog[cat]
    for key in sub_map.keys():
        if key.lower() == sub.lower():
            return {key: sub_map[key]}

    # Preserve your original behavior: unknown subcategory returns empty dict for that key
    return {sub: {}}


def get_offensive_players_game_stats(
    supabase: Client,
    player_names: list[str] | None = None,
    season_list: list[int] | None = None,
    weekly_list: list[int] | None = None,
    metrics: list[str] | None = None,
    order_by_metric: str | None = None,
    limit: int | None = 25,
    positions: list[str] | None = None,
) -> dict:
    """
    Fetch offensive weekly game stats for NFL players.

    Args:
        supabase: The Supabase client instance
        player_names: optional list of player names (partial matches supported)
        season_list: optional list of seasons to include
        weekly_list: optional list of weeks to include
        metrics: optional list of metric codes to return
        order_by_metric: optional metric/column to order by (DESC)
        limit: optional max rows to return (defaults to 25). Enforced cap applied.
        positions: optional list of positions to filter (position column). Defaults to ["WR","TE","RB"].

    Returns:
        dict: Offensive player game stats data
    """
    return build_player_stats_query(
        supabase=supabase,
        table_name="nflreadr_nfl_player_stats",
        base_columns=["season", "week", "player_display_name", "recent_team", "position"],
        player_name_column="player_display_name",
        position_column="position",
        default_positions=["QB", "WR", "TE", "RB"],
        return_key="offGameStats",
        player_names=player_names,
        season_list=season_list,
        weekly_list=weekly_list,
        metrics=metrics,
        order_by_metric=order_by_metric,
        limit=limit,
        positions=positions,
        player_sort_column="player_display_name",
    )
    
def get_defensive_players_game_stats(
    supabase: Client,
    player_names: list[str] | None = None,
    season_list: list[int] | None = None,
    weekly_list: list[int] | None = None,
    metrics: list[str] | None = None,
    order_by_metric: str | None = None,
    limit: int | None = 25,
    positions: list[str] | None = None,
) -> dict:
    """
    Fetch defensive weekly game stats for NFL players.

    Args:
        supabase: The Supabase client instance
        player_names: optional list of player names (partial matches supported)
        season_list: optional list of seasons to include
        weekly_list: optional list of weeks to include
        metrics: optional list of metric codes to return
        order_by_metric: optional metric/column to order by (DESC)
        limit: optional max rows to return (defaults to 25). Enforced cap applied.
        positions: optional list of positions to filter (position column). Defaults to ["CB","DB","DE","DL","LB","S"].

    Returns:
        dict: Defensive player game stats data
    """
    return build_player_stats_query(
        supabase=supabase,
        table_name="nflreadr_nfl_player_stats_defense",
        base_columns=["season", "week", "player_display_name", "team", "position"],
        player_name_column="player_display_name",
        position_column="position",
        default_positions=["CB", "DB", "DE", "DL", "LB", "S"],
        return_key="defGameStats",
        player_names=player_names,
        season_list=season_list,
        weekly_list=weekly_list,
        metrics=metrics,
        order_by_metric=order_by_metric,
        limit=limit,
        positions=positions,
        player_sort_column="player_display_name",
    )
