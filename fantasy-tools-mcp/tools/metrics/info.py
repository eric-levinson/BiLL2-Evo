import logging
from supabase import Client
from helpers.name_utils import sanitize_name
from helpers.query_utils import build_player_stats_query
from docs.metrics_catalog import metrics_catalog

logger = logging.getLogger(__name__)


def get_metrics_metadata(category: str, subcategory: str | None = None) -> dict:
    """
    Returns metric definitions by category for receiving, passing, or rushing advanced NFL statistics.

    Args:
        category: "receiving", "passing", or "rushing"
        subcategory: "basic_info", "volume_metrics", "efficiency_metrics", "situational_metrics", or None

    Returns:
        dict: Metric definitions for the given category and subcategory.
    """
    if category not in metrics_catalog:
        raise ValueError(f"Unknown category: {category}")

    if subcategory is None:
        return metrics_catalog[category]
    else:
        return {subcategory: metrics_catalog[category].get(subcategory, {})}


def get_advanced_receiving_stats(
    supabase: Client,
    player_names: list[str] | None = None,
    season_list: list[int] | None = None,
    metrics: list[str] | None = None,
    order_by_metric: str | None = None,
    limit: int | None = 25,
    positions: list[str] | None = None,
) -> dict:
    """
    Fetch advanced seasonal receiving stats for NFL players.

    Args:
        supabase: Supabase client
        player_names: optional list of player names (partial matches supported)
        season_list: optional list of seasons to include
        metrics: list of metric codes to return (optional)
        order_by_metric: optional metric/column to order by (str). If provided, orders by this metric desc.
        limit: optional max rows to return (defaults to 25). Enforced cap applied.
        positions: optional list of positions to filter (ff_position column). Defaults to ["WR","TE","RB"] if not provided.

    Returns:
        dict: Advanced receiving stats data
    """
    return build_player_stats_query(
        supabase=supabase,
        table_name="vw_advanced_receiving_analytics",
        base_columns=["season", "player_name", "ff_team", "ff_position"],
        player_name_column="merge_name",
        position_column="ff_position",
        default_positions=["WR", "TE", "RB"],
        return_key="advReceivingStats",
        player_names=player_names,
        season_list=season_list,
        weekly_list=None,
        metrics=metrics,
        order_by_metric=order_by_metric,
        limit=limit,
        positions=positions,
    )


def get_advanced_passing_stats(
    supabase: Client,
    player_names: list[str] | None = None,
    season_list: list[int] | None = None,
    metrics: list[str] | None = None,
    order_by_metric: str | None = None,
    limit: int | None = 25,
    positions: list[str] | None = None,
) -> dict:
    """
    Fetch advanced seasonal passing stats for NFL quarterbacks and passers.

    Args:
        supabase: Supabase client
        player_names: optional list of player names (partial matches supported)
        season_list: optional list of seasons to include
        metrics: optional list of metric codes to return
        order_by_metric: optional metric/column to order by (DESC)
        limit: optional max rows to return (defaults to 25). Enforced cap applied.
        positions: optional list of positions to filter (ff_position column). Defaults to ["QB"].

    Returns:
        dict: Advanced passing stats data
    """
    return build_player_stats_query(
        supabase=supabase,
        table_name="vw_advanced_passing_analytics",
        base_columns=["season", "player_name", "ff_team", "ff_position"],
        player_name_column="merge_name",
        position_column="ff_position",
        default_positions=["QB"],
        return_key="advPassingStats",
        player_names=player_names,
        season_list=season_list,
        weekly_list=None,
        metrics=metrics,
        order_by_metric=order_by_metric,
        limit=limit,
        positions=positions,
    )

def get_advanced_rushing_stats(
    supabase: Client,
    player_names: list[str] | None = None,
    season_list: list[int] | None = None,
    metrics: list[str] | None = None,
    order_by_metric: str | None = None,
    limit: int | None = 25,
    positions: list[str] | None = None,
) -> dict:
    """
    Fetch advanced seasonal rushing stats for NFL players.

    Args:
        supabase: Supabase client
        player_names: optional list of player names (partial matches supported)
        season_list: optional list of seasons to include
        metrics: optional list of metric codes to return
        order_by_metric: optional metric/column to order by (DESC)
        limit: optional max rows to return (defaults to 25). Enforced cap applied.
        positions: optional list of positions to filter (ff_position column). Defaults to ["RB","QB"].

    Returns:
        dict: Advanced rushing stats data
    """
    return build_player_stats_query(
        supabase=supabase,
        table_name="vw_advanced_rushing_analytics",
        base_columns=["season", "player_name", "ff_team", "ff_position"],
        player_name_column="merge_name",
        position_column="ff_position",
        default_positions=["RB", "QB"],
        return_key="advRushingStats",
        player_names=player_names,
        season_list=season_list,
        weekly_list=None,
        metrics=metrics,
        order_by_metric=order_by_metric,
        limit=limit,
        positions=positions,
    )


def get_advanced_defense_stats(
    supabase: Client,
    player_names: list[str] | None = None,
    season_list: list[int] | None = None,
    metrics: list[str] | None = None,
    order_by_metric: str | None = None,
    limit: int | None = 25,
    positions: list[str] | None = None,
) -> dict:
    """
    Fetch advanced seasonal defensive stats for NFL defensive players.

    Args:
        supabase: Supabase client
        player_names: optional list of player names (partial matches supported)
        season_list: optional list of seasons to include in results
        metrics: optional list of metric codes to return
        order_by_metric: optional metric/column to order by (DESC)
        limit: optional max rows to return (defaults to 25). Enforced cap applied.
        positions: optional list of positions to filter (position column).
                   Defaults to common defensive roles if not provided.

    Returns:
        dict: Advanced defensive stats data
    """
    return build_player_stats_query(
        supabase=supabase,
        table_name="vw_advanced_def_analytics",
        base_columns=["season", "player_name", "team", "position"],
        player_name_column="merge_name",
        position_column="position",
        default_positions=["CB", "DB", "DE", "DL", "LB", "S"],
        return_key="advDefenseStats",
        player_names=player_names,
        season_list=season_list,
        weekly_list=None,
        metrics=metrics,
        order_by_metric=order_by_metric,
        limit=limit,
        positions=positions,
    )

def get_advanced_receiving_stats_weekly(
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
    Fetch advanced weekly receiving stats for NFL players.

    Args:
        supabase: The Supabase client instance
        player_names: optional list of player names (partial matches supported)
        season_list: optional list of seasons to include
        weekly_list: optional list of weeks to include
        metrics: optional list of metric codes to return
        order_by_metric: optional metric/column to order by (DESC)
        limit: optional max rows to return (defaults to 25). Enforced cap applied.
        positions: optional list of positions to filter (ff_position column). Defaults to ["WR","TE","RB"].

    Returns:
        dict: Advanced receiving stats data
    """
    # base columns always returned
    columns = ["season", "week", "player_name", "ff_team", "ff_position"]
    metrics = metrics or []
    if metrics:
        columns.extend(metrics)

    # sanitize and build optional name filter
    sanitized_names = [sanitize_name(name) for name in player_names] if player_names else []
    or_filter = ",".join([f"merge_name.ilike.%{name}%" for name in sanitized_names]) if sanitized_names else None

    # handle position filter (default to WR/TE/RB)
    positions_list = positions if positions is not None else ["WR", "TE", "RB"]
    positions_list = [p.upper() for p in positions_list] if positions_list else None

    # enforce sensible cap
    max_limit = 300
    safe_limit = None
    if limit and int(limit) > 0:
        safe_limit = min(int(limit), max_limit)

    try:
        query = supabase.table("vw_advanced_receiving_analytics_weekly").select(",".join(columns))

        if season_list:
            query = query.in_("season", season_list)

        if weekly_list:
            query = query.in_("week", weekly_list)

        if positions_list:
            query = query.in_("ff_position", positions_list)

        if or_filter:
            query = query.or_(or_filter)

        # apply ordering: prefer explicit metric, otherwise by season desc, player asc
        if order_by_metric:
            query = query.not_.is_(order_by_metric, "null")
            query = query.order(order_by_metric, desc=True)
        query = query.order("season", desc=True).order("player_name", desc=False)

        if safe_limit:
            query = query.limit(safe_limit)

        response = query.execute()
        return {"advReceivingStats": response.data}

    except Exception as e:
        raise Exception(f"Error fetching receiving stats: {str(e)}")

def get_advanced_passing_stats_weekly(
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
    Fetch advanced weekly passing stats for NFL quarterbacks and passers.

    Args:
        supabase: The Supabase client instance
        player_names: optional list of player names (partial matches supported)
        season_list: optional list of seasons to include
        weekly_list: optional list of weeks to include
        metrics: optional list of metric codes to return
        order_by_metric: optional metric/column to order by (DESC)
        limit: optional max rows to return (defaults to 25). Enforced cap applied.
        positions: optional list of positions to filter (position column). Defaults to ["QB"].

    Returns:
        dict: Advanced passing stats data
    """
    # base columns always returned
    columns = ["season", "week", "player_name", "team", "position"]
    metrics = metrics or []
    if metrics:
        columns.extend(metrics)

    # sanitize and build optional name filter
    sanitized_names = [sanitize_name(name) for name in player_names] if player_names else []
    or_filter = ",".join([f"merge_name.ilike.%{name}%" for name in sanitized_names]) if sanitized_names else None

    # handle position filter (default to QB)
    positions_list = positions if positions is not None else ["QB"]
    positions_list = [p.upper() for p in positions_list] if positions_list else None

    # enforce sensible cap
    max_limit = 300
    safe_limit = None
    if limit and int(limit) > 0:
        safe_limit = min(int(limit), max_limit)

    try:
        query = supabase.table("vw_advanced_passing_analytics_weekly").select(",".join(columns))

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
        query = query.order("season", desc=True).order("player_name", desc=False)

        if safe_limit:
            query = query.limit(safe_limit)

        response = query.execute()
        return {"advPassingStats": response.data}

    except Exception as e:
        raise Exception(f"Error fetching passing stats: {str(e)}")
    
def get_advanced_rushing_stats_weekly(
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
    Fetch advanced weekly rushing stats for NFL players.

    Args:
        supabase: The Supabase client instance
        player_names: optional list of player names (partial matches supported)
        season_list: optional list of seasons to include
        weekly_list: optional list of weeks to include
        metrics: optional list of metric codes to return
        order_by_metric: optional metric/column to order by (DESC)
        limit: optional max rows to return (defaults to 25). Enforced cap applied.
        positions: optional list of positions to filter (position column). Defaults to ["RB","QB"].

    Returns:
        dict: Advanced rushing stats data
    """
    # base columns always returned
    columns = ["season", "week", "player_name", "team", "position"]
    metrics = metrics or []
    if metrics:
        columns.extend(metrics)

    # sanitize and build optional name filter
    sanitized_names = [sanitize_name(name) for name in player_names] if player_names else []
    or_filter = ",".join([f"merge_name.ilike.%{name}%" for name in sanitized_names]) if sanitized_names else None

    # handle position filter (default to RB/QB)
    positions_list = positions if positions is not None else ["RB", "QB"]
    positions_list = [p.upper() for p in positions_list] if positions_list else None

    # enforce sensible cap
    max_limit = 300
    safe_limit = None
    if limit and int(limit) > 0:
        safe_limit = min(int(limit), max_limit)

    try:
        query = supabase.table("vw_advanced_rushing_analytics_weekly").select(",".join(columns))

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
        query = query.order("season", desc=True).order("player_name", desc=False)

        if safe_limit:
            query = query.limit(safe_limit)

        response = query.execute()
        return {"advRushingStats": response.data}

    except Exception as e:
        raise Exception(f"Error fetching rushing stats: {str(e)}")
    
def get_advanced_defense_stats_weekly(
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
    Fetch advanced weekly defensive stats for NFL defensive players.

    Args:
        supabase: The Supabase client instance
        player_names: optional list of player names (partial matches supported)
        season_list: optional list of seasons to include
        weekly_list: optional list of weeks to include
        metrics: optional list of metric codes to return
        order_by_metric: optional metric/column to order by (DESC)
        limit: optional max rows to return (defaults to 25). Enforced cap applied.
        positions: optional list of positions to filter (position column).
                   Defaults to common defensive roles if not provided.

    Returns:
        dict: Advanced defensive stats data
    """
    # base columns always returned
    columns = ["season", "week", "player_name", "team", "position"]
    metrics = metrics or []
    if metrics:
        columns.extend(metrics)

    # sanitize and build optional name filter
    sanitized_names = [sanitize_name(name) for name in player_names] if player_names else []
    or_filter = ",".join([f"merge_name.ilike.%{name}%" for name in sanitized_names]) if sanitized_names else None

    # handle position filter (default to common defensive positions)
    positions_list = positions if positions is not None else ["CB", "DB", "DE", "DL", "LB", "S"]
    positions_list = [p.upper() for p in positions_list] if positions_list else None

    # enforce sensible cap
    max_limit = 300
    safe_limit = None
    if limit and int(limit) > 0:
        safe_limit = min(int(limit), max_limit)

    try:
        query = supabase.table("vw_advanced_def_analytics_weekly").select(",".join(columns))

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
        query = query.order("season", desc=True).order("player_name", desc=False)

        if safe_limit:
            query = query.limit(safe_limit)

        response = query.execute()
        return {"advDefenseStats": response.data}

    except Exception as e:
        raise Exception(f"Error fetching defense stats: {str(e)}")
