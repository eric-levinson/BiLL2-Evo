import os
import importlib.util
import logging
from supabase import Client
from helpers.name_utils import sanitize_name

logger = logging.getLogger(__name__)

import os
import importlib.util

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
    # base columns always returned
    columns = ["season", "week", "player_display_name", "recent_team", "position"]
    metrics = metrics or []
    if metrics:
        columns.extend(metrics)

    # sanitize and build optional name filter
    sanitized_names = [sanitize_name(name) for name in player_names] if player_names else []
    or_filter = ",".join([f"player_display_name.ilike.%{name}%" for name in sanitized_names]) if sanitized_names else None

    # handle position filter (default to WR/TE/RB)
    positions_list = positions if positions is not None else ["QB", "WR", "TE", "RB"]
    positions_list = [p.upper() for p in positions_list] if positions_list else None

    # enforce sensible cap
    max_limit = 300
    safe_limit = None
    if limit and int(limit) > 0:
        safe_limit = min(int(limit), max_limit)

    try:
        query = supabase.table("nflreadr_nfl_player_stats").select(",".join(columns))

        if season_list:
            query = query.in_("season", season_list)

        if weekly_list:
            query = query.in_("week", weekly_list)

        if positions_list:
            query = query.in_("position", positions_list)

        if or_filter:
            query = query.or_(or_filter)

        # apply ordering: prefer explicit metric, otherwise by season desc, player asc
        if order_by_metric:
            query = query.not_.is_(order_by_metric, "null")
            query = query.order(order_by_metric, desc=True)
        query = query.order("season", desc=True).order("player_display_name", desc=False)

        if safe_limit:
            query = query.limit(safe_limit)

        response = query.execute()
        return {"offGameStats": response.data}

    except Exception as e:
        raise Exception(f"Error fetching offensive player game stats: {str(e)}")
    
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
        positions: optional list of positions to filter (position column). Defaults to ["WR","TE","RB"].

    Returns:
        dict: Defensive player game stats data
    """
    # base columns always returned
    columns = ["season", "week", "player_display_name", "team", "position"]
    metrics = metrics or []
    if metrics:
        columns.extend(metrics)

    # sanitize and build optional name filter
    sanitized_names = [sanitize_name(name) for name in player_names] if player_names else []
    or_filter = ",".join([f"player_display_name.ilike.%{name}%" for name in sanitized_names]) if sanitized_names else None

    # handle position filter
    positions_list = positions if positions is not None else ["CB", "DB", "DE", "DL", "LB", "S"]
    positions_list = [p.upper() for p in positions_list] if positions_list else None

    # enforce sensible cap
    max_limit = 300
    safe_limit = None
    if limit and int(limit) > 0:
        safe_limit = min(int(limit), max_limit)

    try:
        query = supabase.table("nflreadr_nfl_player_stats_defense").select(",".join(columns))

        if season_list:
            query = query.in_("season", season_list)

        if weekly_list:
            query = query.in_("week", weekly_list)

        if positions_list:
            query = query.in_("position", positions_list)

        if or_filter:
            query = query.or_(or_filter)

        # apply ordering: prefer explicit metric, otherwise by season desc, player asc
        if order_by_metric:
            query = query.not_.is_(order_by_metric, "null")
            query = query.order(order_by_metric, desc=True)
        query = query.order("season", desc=True).order("player_display_name", desc=False)

        if safe_limit:
            query = query.limit(safe_limit)

        response = query.execute()
        return {"defGameStats": response.data}

    except Exception as e:
        raise Exception(f"Error fetching defensive player game stats: {str(e)}")
