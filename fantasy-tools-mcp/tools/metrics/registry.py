from fastmcp import FastMCP
from supabase import Client
from .info import get_advanced_receiving_stats as _get_advanced_receiving_stats
from .info import get_advanced_passing_stats as _get_advanced_passing_stats
from .info import get_advanced_rushing_stats as _get_advanced_rushing_stats
from .info import get_advanced_defense_stats as _get_advanced_defense_stats
from .info import get_advanced_receiving_stats_weekly as _get_advanced_receiving_stats_weekly
from .info import get_advanced_passing_stats_weekly as _get_advanced_passing_stats_weekly
from .info import get_advanced_rushing_stats_weekly as _get_advanced_rushing_stats_weekly
from .info import get_advanced_defense_stats_weekly as _get_advanced_defense_stats_weekly
from docs.metrics_catalog import metrics_catalog
from .info import get_advanced_receiving_stats as _get_advanced_receiving_stats
from .info import get_advanced_passing_stats as _get_advanced_passing_stats
from .info import get_advanced_rushing_stats as _get_advanced_rushing_stats
from .info import get_advanced_defense_stats as _get_advanced_defense_stats
from .info import get_advanced_receiving_stats_weekly as _get_advanced_receiving_stats_weekly
from .info import get_advanced_passing_stats_weekly as _get_advanced_passing_stats_weekly
from .info import get_advanced_rushing_stats_weekly as _get_advanced_rushing_stats_weekly
from .info import get_advanced_defense_stats_weekly as _get_advanced_defense_stats_weekly

from fastmcp import FastMCP
from supabase import Client



def register_tools(mcp: FastMCP, supabase: Client):
    """Register fantasy-related tools with the FastMCP instance."""
    
    @mcp.tool(
        description="Returns metric definitions by category for receiving, passing, rushing, and defense advanced NFL statistics. Use subcategory to pick one of: basic_info, volume_metrics, efficiency_metrics, situational_metrics, weekly."
    )
    def get_metrics_metadata(category: str | None = None, subcategory: str | None = None) -> dict:
        """Return metadata from the embedded metrics_catalog.

        If category is None, return the full catalog. If subcategory is supplied,
        return only that subset for the requested category.
        """
        if category is None:
            return metrics_catalog
        cat = metrics_catalog.get(category)
        if not cat:
            return {"error": f"unknown category: {category}"}
        if subcategory is None:
            return cat
        sub = cat.get(subcategory)
        if sub is None:
            return {"error": f"unknown subcategory: {subcategory} for category: {category}"}
        return sub
    
    @mcp.tool(
        description="""
        Fetch advanced seasonal receiving stats for NFL players.

        - Optional filters: player_names (partial matches), season_list, metrics.
        - Optional controls: order_by_metric (sort DESC), limit (default 100, capped by implementation), positions (defaults to ['WR','TE','RB']).
        - Safety: fully-unfiltered queries (no name/season/position) are refused unless allow_unfiltered=True.

        For detailed metric definitions and categories, use the get_metrics_metadata tool.

        Volume Metrics: (workhorse, production, usage)
        games, targets, receptions, receiving_yards, receiving_tds, fantasy_points, fantasy_points_ppr, air_yards_share, receiving_air_yards, receiving_first_downs, receiving_2pt_conversions, receiving_yards_after_catch, gs, td, ybc, yds, team_abbr, player_position, height, weight
        
        Efficiency Metrics: (how well a player converted their opportunities)
        dom, racr, ay_sh, ry_sh, w8dom, ppr_sh, rfd_sh, rtd_sh, tgt_sh, wopr_x, wopr_y, yac_sh, yptmpa, rtdfd_sh, target_share, receiving_epa, receiving_tds, int, rat, x1d, adot, yac_r, ybc_r, rec_br, brk_tkl, drop_percent, avg_yac, avg_expected_yac, catch_percentage, avg_intended_air_yards, avg_yac_above_expectation, percent_share_of_intended_air_yards
        
        Situational/Advanced Metrics: (what situations/roles, context stats)
        receiving_2pt_conversions, receiving_first_downs, avg_cushion, avg_separation, player_display_name, receiving_yards_after_catch, age, drop
        
        Basic player info (season, player_name, ff_team, merge_name) is always included.
        """
    )
    def get_advanced_receiving_stats(
        player_names: list[str] | None = None,
        season_list: list[int] | None = None,
        metrics: list[str] | None = None,
        order_by_metric: str | None = None,
        limit: int | None = 100,
        positions: list[str] | None = None,
    ) -> dict:        
        return _get_advanced_receiving_stats(
            supabase,
            player_names,
            season_list,
            metrics,
            order_by_metric,
            limit,
            positions
        )

    @mcp.tool(
        description="""
        Fetch advanced seasonal passing stats for NFL quarterbacks and passers.
        - Optional filters: player_names (partial matches), season_list, metrics.
        - Optional controls: order_by_metric (sort DESC), limit (default 100, capped by implementation), positions (defaults to ['QB']).
        - Query by player names, season, and choose which metrics to include by category or individually.
        - Supports three metric categories: Volume, Efficiency, and Situational/Advanced.

        Volume Metrics: (production, usage, and play counts)
        qb_plays, times_hit, times_sacked, times_blitzed, times_hurried, times_pressured, exp_sack, passing_drops, receiving_drop, def_times_hitqb, def_times_blitzed, def_times_hurried

        Efficiency Metrics: (conversion rates, accuracy, and advanced efficiency)
        passer_rating, completion_percentage, avg_air_distance, avg_intended_air_yards, avg_air_yards_to_sticks, avg_completed_air_yards, avg_air_yards_differential, max_air_distance, max_completed_air_distance, expected_completion_percentage, completion_percentage_above_expectation, qbr_raw, qbr_total, qbr_rank, epa_total, times_pressured_pct

        Situational/Advanced Metrics: (pressure, turnover, and contextual passing stats)
        aggressiveness, avg_time_to_throw, passing_bad_throws, passing_bad_throw_pct, passing_drop_pct, receiving_drop_pct, pfr_player_id, pfr_player_name, merge_name, team, position, season, week, height, weight

        For detailed metric definitions and categories, use the get_metrics_metadata tool.
        Basic player info (season, week, player_name, team, position, merge_name, height, weight) is always included.
        """
    )
    def get_advanced_passing_stats(
        player_names: list[str] | None = None,
        season_list: list[int] | None = None,
        metrics: list[str] | None = None,
        order_by_metric: str | None = None,
        limit: int | None = 100,
        positions: list[str] | None = None,
    ) -> dict:
        return _get_advanced_passing_stats(
            supabase,
            player_names,
            season_list,
            metrics,
            order_by_metric,
            limit,
            positions,
        )

    
    @mcp.tool(
        description="""
        Fetch advanced seasonal rushing stats for NFL running backs, hybrid backs, and runners.
        - Optional filters: player_names (partial matches), season_list, metrics.
        - Optional controls: order_by_metric (sort DESC), limit (default 100, capped by implementation), positions (defaults to ['RB','QB']).
        - Query by player names, season, and choose which metrics to include by category or individually.
        - Supports three metric categories: Volume, Efficiency, and Situational/Advanced.

        Volume Metrics: (production, usage, and play counts)
        games, carries, rushing_yards, rushing_tds, rushing_first_downs, targets, receptions, receiving_yards, receiving_tds, rush_attempts, rush_touchdowns, gs, td, yds, att

        Efficiency Metrics: (rate stats and advanced context)
        dom, ry_sh, w8dom, ppr_sh, yac_sh, yptmpa, rushing_epa, receiving_epa, target_share, fantasy_points, fantasy_points_ppr, rushing_fumbles, rushing_fumbles_lost, rushing_yards_after_catch, receiving_yards_after_catch, att_br, brk_tkl, yac, ybc, yac_att, ybc_att, avg_rush_yards, efficiency, expected_rush_yards, rush_pct_over_expected, rush_yards_over_expected, rush_yards_over_expected_per_att, percent_attempts_gte_eight_defenders, avg_time_to_los

        Situational/Advanced Metrics: (goal-line, context, and next-level situational stats)
        rushing_2pt_conversions, receiving_2pt_conversions, rushing_first_downs, x1d, age, rushing_yards_after_catch

        For detailed metric definitions and categories, use the get_metrics_metadata tool.
        Basic player info (season, player_name, ff_team, merge_name) is always included.
        """
    )
    def get_advanced_rushing_stats(
        player_names: list[str] | None = None,
        season_list: list[int] | None = None,
        metrics: list[str] | None = None,
        order_by_metric: str | None = None,
        limit: int | None = 100,
        positions: list[str] | None = None,
    ) -> dict:
        return _get_advanced_rushing_stats(
            supabase,
            player_names,
            season_list,
            metrics,
            order_by_metric,
            limit,
            positions,
        )

    @mcp.tool(
        description="""
        Fetch advanced seasonal defensive stats for NFL defenders and defensive playmakers.

        - Optional filters: player_names (partial matches), season_list, metrics.
        - Optional controls: order_by_metric (sort DESC), limit (default 100, capped by implementation), positions (defaults to ['CB','DB','DE','DL','LB','S']).
        - Query by player names, season, and choose which metrics to include by category or individually.
        - Supports three metric categories: Volume, Efficiency, and Situational/Advanced.

        Volume Metrics: (production, usage, and appearance counts)
        g, gs, sk, td, air, cmp, int, tgt, prss, bltz, hrry, qbkd, comb, m_tkl, loaded

        Efficiency Metrics: (coverage, tackling, and pressure rates)
        cmp_percent, m_tkl_percent, yds_cmp, yds_tgt, rat, yds, yac

        Situational/Advanced Metrics: (contextual and advanced defensive stats)
        dadot, age, pos, pfr_id, gsis_id, merge_name, team, player_name, height, weight

        For detailed metric definitions and categories, use the get_metrics_metadata tool.
        Basic player info (season, week, player_name, team, position, merge_name, height, weight) is always included.
        """
    )
    def get_advanced_defense_stats(
        player_names: list[str] | None = None,
        season_list: list[int] | None = None,
        metrics: list[str] | None = None,
        order_by_metric: str | None = None,
        limit: int | None = 100,
        positions: list[str] | None = None,
    ) -> dict:
        """Fetch advanced seasonal defensive stats (for tools/agents).

        Parameters mirror the implementation in `tools/metrics/info.py` and are forwarded
        to the underlying helper `_get_advanced_defense_stats`.
        """
        return _get_advanced_defense_stats(
            supabase,
            player_names,
            season_list,
            metrics,
            order_by_metric,
            limit,
            positions,
        )
    
    @mcp.tool(
        description="""
        Fetch advanced weekly receiving stats for NFL players.

        - Optional filters: player_names (partial matches), season_list, weekly_list, metrics.
        - Optional controls: order_by_metric (sort DESC), limit (default 100, capped by implementation), positions (defaults to ['WR','TE','RB']).
        - Query by player names, season, week, and choose which metrics to include by category or individually.
        - Supports three metric categories: Volume, Efficiency, and Situational/Advanced.

        Volume Metrics: (workhorse, production, usage)
        passing_drops, receiving_int, receiving_drop, rushing_broken_tackles, receiving_broken_tackles

        Efficiency Metrics: (conversion, catch rates, and advanced context)
        receiving_rat, passing_drop_pct, receiving_drop_pct, avg_yac, avg_expected_yac, catch_percentage, avg_intended_air_yards, avg_yac_above_expectation, percent_share_of_intended_air_yards

        Situational/Advanced Metrics: (separation, context, and team info)
        avg_cushion, avg_separation, player_position, player_display_name, ngr_team

        For detailed metric definitions and categories, use the get_metrics_metadata tool.
        Basic player info (season, week, player_name, ff_team, ff_position, merge_name, height, weight) is always included.
        """
    )
    def get_advanced_receiving_stats_weekly(
        player_names: list[str] | None = None,
        season_list: list[int] | None = None,
        weekly_list: list[int] | None = None,
        metrics: list[str] | None = None,
        order_by_metric: str | None = None,
        limit: int | None = 100,
        positions: list[str] | None = None,
    ) -> dict:
        return _get_advanced_receiving_stats_weekly(
            supabase,
            player_names,
            season_list,
            weekly_list,
            metrics,
            order_by_metric,
            limit,
            positions,
        )
    
    @mcp.tool(
        description="""
        Fetch advanced weekly passing stats for NFL quarterbacks and passers.

        - Optional filters: player_names (partial matches), season_list, weekly_list, metrics.
        - Optional controls: order_by_metric (sort DESC), limit (default 100, capped by implementation), positions (defaults to ['QB']).
        - Query by player names, season, week, and choose which metrics to include by category or individually.
        - Supports three metric categories: Volume, Efficiency, and Situational/Advanced.

        Volume Metrics: (production, usage, and play counts)
        qb_plays, times_hit, times_sacked, times_blitzed, times_hurried, times_pressured, exp_sack, passing_drops, receiving_drop, def_times_hitqb, def_times_blitzed, def_times_hurried

        Efficiency Metrics: (conversion rates, accuracy, and advanced efficiency)
        passer_rating, completion_percentage, avg_air_distance, avg_intended_air_yards, avg_air_yards_to_sticks, avg_completed_air_yards, avg_air_yards_differential, max_air_distance, max_completed_air_distance, expected_completion_percentage, completion_percentage_above_expectation, qbr_raw, qbr_total, qbr_rank, epa_total, times_pressured_pct

        Situational/Advanced Metrics: (pressure, turnover, and contextual passing stats)
        aggressiveness, avg_time_to_throw, passing_bad_throws, passing_bad_throw_pct, passing_drop_pct, receiving_drop_pct, pfr_player_id, pfr_player_name, merge_name, team, position, season, week, height, weight

        For detailed metric definitions and categories, use the get_metrics_metadata tool.
        Basic player info (season, week, player_name, team, position, merge_name, height, weight) is always included.
        """
    )
    def get_advanced_passing_stats_weekly(
        player_names: list[str] | None = None,
        season_list: list[int] | None = None,
        weekly_list: list[int] | None = None,
        metrics: list[str] | None = None,
        order_by_metric: str | None = None,
        limit: int | None = 100,
        positions: list[str] | None = None,
    ) -> dict:
        return _get_advanced_passing_stats_weekly(
            supabase,
            player_names,
            season_list,
            weekly_list,
            metrics,
            order_by_metric,
            limit,
            positions,
        )
    
    @mcp.tool(
        description="""
        Fetch advanced weekly rushing stats for NFL running backs, hybrid backs, and runners.
        - Optional filters: player_names (partial matches), season_list, weekly_list, metrics.
        - Optional controls: order_by_metric (sort DESC), limit (default 100, capped by implementation), positions (defaults to ['RB','QB']).
        - Query by player names, season, week, and choose which metrics to include by category or individually.
        - Supports three metric categories: Volume, Efficiency, and Situational/Advanced.

        Volume Metrics: (production, usage, and play counts)
        rush_attempts, rush_touchdowns

        Efficiency Metrics: (rate stats and advanced context)
        efficiency, avg_rush_yards, avg_time_to_los, expected_rush_yards, rush_pct_over_expected, rush_yards_over_expected, rush_yards_over_expected_per_att, percent_attempts_gte_eight_defenders

        Situational/Advanced Metrics: (broken tackles, contact, and context)
        rushing_broken_tackles, receiving_broken_tackles, rushing_yards_after_contact, rushing_yards_before_contact, rushing_yards_after_contact_avg, rushing_yards_before_contact_avg

        For detailed metric definitions and categories, use the get_metrics_metadata tool.
        Basic player info (season, week, player_name, team, position, merge_name, height, weight) is always included.
        """
    )
    def get_advanced_rushing_stats_weekly(
        player_names: list[str] | None = None,
        season_list: list[int] | None = None,
        weekly_list: list[int] | None = None,
        metrics: list[str] | None = None,
        order_by_metric: str | None = None,
        limit: int | None = 100,
        positions: list[str] | None = None,
    ) -> dict:
        return _get_advanced_rushing_stats_weekly(
            supabase,
            player_names,
            season_list,
            weekly_list,
            metrics,
            order_by_metric,
            limit,
            positions,
        )
    
    @mcp.tool(
        description="""
        Fetch advanced weekly defensive stats for NFL defenders and defensive playmakers.
        - Optional filters: player_names (partial matches), season_list, weekly_list, metrics.
        - Optional controls: order_by_metric (sort DESC), limit (default 100, capped by implementation), positions (defaults to ['CB','DB','DE','DL','LB','S']).
        - Query by player names, season, week, and choose which metrics to include by category or individually.
        - Supports three metric categories: Volume, Efficiency, and Situational/Advanced.

        Volume Metrics: (production, usage, and appearance counts)
        def_tackles_combined, def_sacks, def_ints, def_targets, def_pressures, def_times_blitzed, def_times_hurried, def_times_hitqb

        Efficiency Metrics: (coverage, tackling, and pressure rates)
        def_completion_pct, def_missed_tackles, def_missed_tackle_pct, def_completions_allowed, def_yards_allowed, def_yards_allowed_per_cmp, def_yards_allowed_per_tgt, def_passer_rating_allowed

        Situational/Advanced Metrics: (contextual and advanced defensive stats)
        def_adot, def_yards_after_catch, def_air_yards_completed, def_receiving_td_allowed, game_id, game_type, opponent, pfr_game_id, pfr_player_id, pfr_player_name

        For detailed metric definitions and categories, use the get_metrics_metadata tool.
        Basic player info (season, week, player_name, team, position, merge_name, height, weight) is always included.
        """
    )
    def get_advanced_defense_stats_weekly(
        player_names: list[str] | None = None,
        season_list: list[int] | None = None,
        weekly_list: list[int] | None = None,
        metrics: list[str] | None = None,
        order_by_metric: str | None = None,
        limit: int | None = 100,
        positions: list[str] | None = None,
    ) -> dict:
        return _get_advanced_defense_stats_weekly(supabase, player_names, season_list, weekly_list, metrics, order_by_metric, limit, positions)
    
