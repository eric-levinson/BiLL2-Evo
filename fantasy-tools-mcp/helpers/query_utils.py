import logging
from supabase import Client
from helpers.name_utils import sanitize_name

logger = logging.getLogger(__name__)


def build_player_stats_query(
    supabase: Client,
    table_name: str,
    base_columns: list[str],
    player_name_column: str,
    position_column: str,
    default_positions: list[str],
    return_key: str,
    player_names: list[str] | None = None,
    season_list: list[int] | None = None,
    weekly_list: list[int] | None = None,
    metrics: list[str] | None = None,
    order_by_metric: str | None = None,
    limit: int | None = 25,
    positions: list[str] | None = None,
    player_sort_column: str = "player_name",
) -> dict:
    """
    Generic query builder for player stats across different tables.

    This function encapsulates the common query logic shared across all advanced stats
    and game stats functions, reducing code duplication and ensuring consistent behavior.

    Args:
        supabase: Supabase client instance
        table_name: Name of the table/view to query (e.g., "vw_advanced_receiving_analytics")
        base_columns: Base columns always returned (e.g., ["season", "player_name", "ff_team", "ff_position"])
        player_name_column: Column name to use for player name filtering (e.g., "merge_name", "player_display_name")
        position_column: Column name to use for position filtering (e.g., "ff_position", "position")
        default_positions: Default positions to filter if positions param is None (e.g., ["WR", "TE", "RB"])
        return_key: Key to use in the returned dict (e.g., "advReceivingStats")
        player_names: Optional list of player names (partial matches supported)
        season_list: Optional list of seasons to include
        weekly_list: Optional list of weeks to include (for weekly tables)
        metrics: Optional list of metric codes to return in addition to base columns
        order_by_metric: Optional metric/column to order by (DESC). If None, orders by season DESC, player_name ASC
        limit: Optional max rows to return (defaults to 25). Capped at 300.
        positions: Optional list of positions to filter. If None, uses default_positions.
        player_sort_column: Column name for secondary sort (ASC). Defaults to "player_name".
            Tables using "player_display_name" (e.g. nflreadr_nfl_player_stats) should pass that instead.

    Returns:
        dict: Query results with the specified return_key

    Raises:
        Exception: If query execution fails

    Examples:
        # Seasonal receiving stats
        >>> build_player_stats_query(
        ...     supabase=client,
        ...     table_name="vw_advanced_receiving_analytics",
        ...     base_columns=["season", "player_name", "ff_team", "ff_position"],
        ...     player_name_column="merge_name",
        ...     position_column="ff_position",
        ...     default_positions=["WR", "TE", "RB"],
        ...     return_key="advReceivingStats",
        ...     player_names=["Jefferson"],
        ...     season_list=[2023, 2024],
        ...     metrics=["targets", "receptions", "receiving_yards"],
        ...     limit=50
        ... )

        # Weekly passing stats
        >>> build_player_stats_query(
        ...     supabase=client,
        ...     table_name="vw_advanced_passing_analytics_weekly",
        ...     base_columns=["season", "week", "player_name", "team", "position"],
        ...     player_name_column="merge_name",
        ...     position_column="position",
        ...     default_positions=["QB"],
        ...     return_key="advPassingStats",
        ...     player_names=["Mahomes"],
        ...     season_list=[2024],
        ...     weekly_list=[1, 2, 3],
        ...     metrics=["passing_yards", "passing_tds"],
        ...     order_by_metric="passing_yards"
        ... )
    """
    # Build columns list: base columns + metrics
    columns = base_columns.copy()
    metrics = metrics or []
    if metrics:
        columns.extend(metrics)

    # Sanitize and build optional name filter
    sanitized_names = [sanitize_name(name) for name in player_names] if player_names else []
    or_filter = ",".join([f"{player_name_column}.ilike.%{name}%" for name in sanitized_names]) if sanitized_names else None

    # Handle position filter (use defaults if not provided)
    positions_list = positions if positions is not None else default_positions
    # Normalize to uppercase strings
    positions_list = [p.upper() for p in positions_list] if positions_list else None

    # Enforce sensible cap
    max_limit = 300
    safe_limit = None
    if limit and int(limit) > 0:
        safe_limit = min(int(limit), max_limit)

    try:
        # Build base query
        query = supabase.table(table_name).select(",".join(columns))

        # Apply filters
        if season_list:
            query = query.in_("season", season_list)

        if weekly_list:
            query = query.in_("week", weekly_list)

        if positions_list:
            query = query.in_(position_column, positions_list)

        if or_filter:
            query = query.or_(or_filter)

        # Apply ordering: prefer explicit metric, otherwise by season desc, player asc
        if order_by_metric:
            query = query.not_.is_(order_by_metric, "null")
            query = query.order(order_by_metric, desc=True)
        query = query.order("season", desc=True).order(player_sort_column, desc=False)

        if safe_limit:
            query = query.limit(safe_limit)

        # Execute query
        response = query.execute()
        return {return_key: response.data}

    except Exception as e:
        raise Exception(f"Error fetching {return_key}: {str(e)}")
