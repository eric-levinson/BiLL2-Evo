"""
Advanced NFL metrics query functions.

This module provides functions to query advanced receiving, passing, rushing, and defensive
statistics for NFL players. All query functions have been refactored to use the generic
build_player_stats_query helper from helpers.query_utils to eliminate code duplication
and ensure consistent query behavior across all stats types.

The refactoring reduced ~639 lines of duplicated query logic down to a single reusable
helper function plus thin wrapper functions that specify table-specific parameters.
"""

import logging

from supabase import Client

from docs.metrics_catalog import metrics_catalog
from helpers.query_utils import build_player_stats_query

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
    return build_player_stats_query(
        supabase=supabase,
        table_name="vw_advanced_receiving_analytics_weekly",
        base_columns=["season", "week", "player_name", "ff_team", "ff_position"],
        player_name_column="merge_name",
        position_column="ff_position",
        default_positions=["WR", "TE", "RB"],
        return_key="advReceivingStats",
        player_names=player_names,
        season_list=season_list,
        weekly_list=weekly_list,
        metrics=metrics,
        order_by_metric=order_by_metric,
        limit=limit,
        positions=positions,
    )


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
    return build_player_stats_query(
        supabase=supabase,
        table_name="vw_advanced_passing_analytics_weekly",
        base_columns=["season", "week", "player_name", "team", "position"],
        player_name_column="merge_name",
        position_column="position",
        default_positions=["QB"],
        return_key="advPassingStats",
        player_names=player_names,
        season_list=season_list,
        weekly_list=weekly_list,
        metrics=metrics,
        order_by_metric=order_by_metric,
        limit=limit,
        positions=positions,
    )


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
    return build_player_stats_query(
        supabase=supabase,
        table_name="vw_advanced_rushing_analytics_weekly",
        base_columns=["season", "week", "player_name", "team", "position"],
        player_name_column="merge_name",
        position_column="position",
        default_positions=["RB", "QB"],
        return_key="advRushingStats",
        player_names=player_names,
        season_list=season_list,
        weekly_list=weekly_list,
        metrics=metrics,
        order_by_metric=order_by_metric,
        limit=limit,
        positions=positions,
    )


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
    return build_player_stats_query(
        supabase=supabase,
        table_name="vw_advanced_def_analytics_weekly",
        base_columns=["season", "week", "player_name", "team", "position"],
        player_name_column="merge_name",
        position_column="position",
        default_positions=["CB", "DB", "DE", "DL", "LB", "S"],
        return_key="advDefenseStats",
        player_names=player_names,
        season_list=season_list,
        weekly_list=weekly_list,
        metrics=metrics,
        order_by_metric=order_by_metric,
        limit=limit,
        positions=positions,
    )


def get_player_consistency(
    supabase: Client,
    player_names: list[str] | None = None,
    season_list: list[int] | None = None,
    metrics: list[str] | None = None,
    order_by_metric: str | None = None,
    limit: int | None = 25,
    positions: list[str] | None = None,
) -> dict:
    """
    Fetch player consistency metrics from the mv_player_consistency materialized view.

    Consistency metrics include avg PPR points, standard deviation, floor (P10), ceiling (P90),
    boom/bust game counts, and consistency coefficient (stddev/mean). Lower coefficient = more
    consistent (safer floor).

    Args:
        supabase: Supabase client
        player_names: optional list of player names (partial matches supported)
        season_list: optional list of seasons to include
        metrics: optional list of metric codes to return
        order_by_metric: optional metric/column to order by (DESC)
        limit: optional max rows to return (defaults to 25). Enforced cap applied.
        positions: optional list of positions to filter (ff_position column). Defaults to all offensive positions.

    Returns:
        dict: Player consistency data with keys: season, player_name, ff_position, ff_team,
              games_played, avg_fp_ppr, fp_stddev_ppr, fp_floor_p10, fp_ceiling_p90,
              fp_median_ppr, boom_games_20plus, bust_games_under_5, consistency_coefficient
    """
    return build_player_stats_query(
        supabase=supabase,
        table_name="mv_player_consistency",
        base_columns=[
            "season",
            "player_name",
            "ff_position",
            "ff_team",
            "games_played",
            "avg_fp_ppr",
            "fp_stddev_ppr",
            "fp_floor_p10",
            "fp_ceiling_p90",
            "fp_median_ppr",
            "boom_games_20plus",
            "bust_games_under_5",
            "consistency_coefficient",
        ],
        player_name_column="player_name",
        position_column="ff_position",
        default_positions=["QB", "RB", "WR", "TE"],
        return_key="playerConsistency",
        player_names=player_names,
        season_list=season_list,
        weekly_list=None,
        metrics=metrics,
        order_by_metric=order_by_metric,
        limit=limit,
        positions=positions,
    )
