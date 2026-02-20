"""
Player deep dive composite tool for comprehensive single-player analysis.

Fetches player bio, season stats with positional percentile ranks, consistency
metrics, dynasty rankings, optional weekly game log, and usage trends in parallel
using ThreadPoolExecutor. Returns a data-only bundle with zero analysis or
opinions — the LLM interprets the data.
"""

from concurrent.futures import ThreadPoolExecutor

from supabase import Client

from helpers.query_utils import build_player_stats_query
from tools.metrics.info import (
    get_advanced_passing_stats,
    get_advanced_receiving_stats,
    get_advanced_rushing_stats,
)
from tools.player.info import get_player_info
from tools.ranks.info import get_fantasy_ranks

# Position-appropriate metrics (043)
# Receiving pctile columns live in mv_receiving_percentile_ranks (separate MV)
# because vw_advanced_receiving_analytics has a LATERAL join that makes inline
# PERCENT_RANK() too expensive. Pctile data is fetched separately and merged.
_RECEIVING_METRICS = [
    "targets",
    "receptions",
    "receiving_yards",
    "receiving_tds",
    "fantasy_points",
    "fantasy_points_ppr",
    "target_share",
    "catch_percentage",
    "avg_yac",
    "receiving_air_yards",
    "receiving_first_downs",
    "receiving_yards_after_catch",
]

_RECEIVING_PCTILE_COLS = [
    "targets_pctile",
    "target_share_pctile",
    "receiving_yards_pctile",
    "fantasy_points_ppr_pctile",
    "catch_percentage_pctile",
    "avg_yac_pctile",
]

_PASSING_METRICS = [
    "passing_yards",
    "passing_tds",
    "passer_rating",
    "completion_percentage",
    "epa_total",
    "fantasy_points",
    "fantasy_points_ppr",
    "aggressiveness",
    "avg_time_to_throw",
    "passing_yards_pctile",
    "passing_tds_pctile",
    "passer_rating_pctile",
    "completion_percentage_pctile",
    "epa_total_pctile",
    "fantasy_points_ppr_pctile",
]

_RUSHING_METRICS = [
    "carries",
    "rushing_yards",
    "rushing_tds",
    "rushing_epa",
    "fantasy_points",
    "fantasy_points_ppr",
    "avg_rush_yards",
    "rushing_first_downs",
    "rushing_fumbles",
    "carries_pctile",
    "rushing_yards_pctile",
    "rushing_tds_pctile",
    "rushing_epa_pctile",
    "fantasy_points_ppr_pctile",
    "avg_rush_yards_pctile",
]


def get_player_deep_dive(
    supabase: Client,
    player_name: str,
    scoring_format: str = "ppr",
    include_game_log: bool = False,
    recent_weeks: int = 6,
) -> dict:
    """
    Assemble comprehensive player analysis data in a single call.

    Fetches player bio, position-appropriate season stats with positional percentile
    ranks, consistency metrics, dynasty rankings, optional weekly game log, and
    target share / snap count trends. All internal fetches run in parallel.

    Single tool call replaces the common pattern of:
    get_player_profile + get_advanced_stats + get_player_consistency + get_fantasy_ranks

    Args:
        supabase: The Supabase client instance
        player_name: Player name to analyze
        scoring_format: Scoring format ("ppr", "half_ppr", "standard")
        include_game_log: If True, includes recent weekly game log data
        recent_weeks: Number of recent weeks for game log (default 6)

    Returns:
        dict: Deep dive bundle with keys:
            - player_info: Basic bio data (name, position, team, age, experience)
            - season_stats: Position-appropriate stats with percentile ranks
            - consistency: Consistency metrics (avg FP, floor/ceiling, boom/bust)
            - dynasty_ranking: Dynasty ECR and positional rank
            - game_log: Recent weekly game log (if requested, else null)
            - usage_trends: Target share and snap count weekly trends
            - scoring_format: Scoring format string
            - data_season: Most recent season in the data
    """
    if not player_name or not player_name.strip():
        raise ValueError("player_name is required")

    name = player_name.strip()
    safe_recent_weeks = min(max(int(recent_weeks), 1), 18)

    # --- Internal fetch functions ---

    def _fetch_info() -> list[dict] | None:
        try:
            return get_player_info(supabase, [name])
        except Exception:
            return None

    def _fetch_receiving() -> list[dict]:
        try:
            result = get_advanced_receiving_stats(
                supabase=supabase, player_names=[name], metrics=_RECEIVING_METRICS, limit=3
            )
            return result.get("advReceivingStats", [])
        except Exception:
            return []

    def _fetch_passing() -> list[dict]:
        try:
            result = get_advanced_passing_stats(
                supabase=supabase, player_names=[name], metrics=_PASSING_METRICS, limit=3
            )
            return result.get("advPassingStats", [])
        except Exception:
            return []

    def _fetch_rushing() -> list[dict]:
        try:
            result = get_advanced_rushing_stats(
                supabase=supabase, player_names=[name], metrics=_RUSHING_METRICS, limit=3
            )
            return result.get("advRushingStats", [])
        except Exception:
            return []

    def _fetch_consistency() -> dict | None:
        try:
            result = build_player_stats_query(
                supabase=supabase,
                table_name="mv_player_consistency",
                base_columns=[
                    "player_name",
                    "merge_name",
                    "season",
                    "ff_position",
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
                player_name_column="merge_name",
                position_column="ff_position",
                default_positions=["QB", "RB", "WR", "TE"],
                return_key="consistency",
                player_names=[name],
                limit=1,
            )
            data = result.get("consistency", [])
            return data[0] if data else None
        except Exception:
            return None

    def _fetch_receiving_pctile() -> list[dict]:
        try:
            result = build_player_stats_query(
                supabase=supabase,
                table_name="mv_receiving_percentile_ranks",
                base_columns=["merge_name", "ff_position", "season"],
                player_name_column="merge_name",
                position_column="ff_position",
                default_positions=["WR", "TE", "RB"],
                return_key="recvPctile",
                player_names=[name],
                metrics=_RECEIVING_PCTILE_COLS,
                limit=3,
            )
            return result.get("recvPctile", [])
        except Exception:
            return []

    def _fetch_dynasty_ranks() -> list[dict]:
        try:
            return get_fantasy_ranks(supabase=supabase, limit=500)
        except Exception:
            return []

    def _fetch_game_log() -> list[dict]:
        if not include_game_log:
            return []
        try:
            result = build_player_stats_query(
                supabase=supabase,
                table_name="nflreadr_nfl_player_stats",
                base_columns=["season", "week", "player_display_name", "recent_team", "position"],
                player_name_column="player_display_name",
                position_column="position",
                default_positions=["QB", "RB", "WR", "TE"],
                return_key="gameLog",
                player_names=[name],
                metrics=["fantasy_points", "fantasy_points_ppr"],
                limit=safe_recent_weeks,
                player_sort_column="player_display_name",
            )
            return result.get("gameLog", [])
        except Exception:
            return []

    def _fetch_usage_trends() -> list[dict]:
        """Fetch recent weekly receiving stats for target share / usage trends."""
        try:
            result = build_player_stats_query(
                supabase=supabase,
                table_name="vw_advanced_receiving_analytics_weekly",
                base_columns=["season", "week", "player_name", "ff_team", "ff_position"],
                player_name_column="merge_name",
                position_column="ff_position",
                default_positions=["WR", "TE", "RB"],
                return_key="usageTrends",
                player_names=[name],
                metrics=["target_share", "avg_separation", "avg_cushion"],
                limit=safe_recent_weeks,
            )
            return result.get("usageTrends", [])
        except Exception:
            return []

    # --- Parallel fetch ---
    worker_count = 8 if include_game_log else 7
    max_workers = min(worker_count, 10)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        info_future = executor.submit(_fetch_info)
        recv_future = executor.submit(_fetch_receiving)
        recv_pctile_future = executor.submit(_fetch_receiving_pctile)
        pass_future = executor.submit(_fetch_passing)
        rush_future = executor.submit(_fetch_rushing)
        consistency_future = executor.submit(_fetch_consistency)
        rankings_future = executor.submit(_fetch_dynasty_ranks)
        game_log_future = executor.submit(_fetch_game_log)
        usage_future = executor.submit(_fetch_usage_trends)

        info_list = info_future.result()
        recv_data = recv_future.result()
        recv_pctile_data = recv_pctile_future.result()
        pass_data = pass_future.result()
        rush_data = rush_future.result()
        consistency_data = consistency_future.result()
        all_rankings = rankings_future.result()
        game_log = game_log_future.result()
        usage_trends = usage_future.result()

    # --- Merge receiving percentile ranks from MV into receiving stats ---
    if recv_data and recv_pctile_data:
        pctile_by_season = {r.get("season"): r for r in recv_pctile_data}
        for row in recv_data:
            pctile = pctile_by_season.get(row.get("season"))
            if pctile:
                for col in _RECEIVING_PCTILE_COLS:
                    if col in pctile:
                        row[col] = pctile[col]

    # --- Build player info ---
    player_info = info_list[0] if info_list else None
    if not player_info:
        return {
            "error": f"Player not found: {name}",
            "player_info": None,
            "season_stats": {},
            "consistency": None,
            "dynasty_ranking": None,
            "game_log": None,
            "usage_trends": [],
            "scoring_format": scoring_format,
            "data_season": None,
            "missing_required_data": None,
        }

    display_name = player_info.get("display_name", name)

    # --- Build season stats ---
    data_season: int | None = None
    season_stats: dict = {}
    for label, stat_data in [
        ("receiving", recv_data),
        ("passing", pass_data),
        ("rushing", rush_data),
    ]:
        if stat_data:
            season_stats[label] = stat_data
            for row in stat_data:
                s = row.get("season")
                if s and (data_season is None or s > data_season):
                    data_season = s

    # --- Build dynasty ranking ---
    rankings_by_name: dict[str, dict] = {}
    for entry in all_rankings:
        pname = entry.get("player", "").lower()
        if pname:
            rankings_by_name[pname] = entry

    rank_data = rankings_by_name.get(name.lower()) or rankings_by_name.get(display_name.lower())
    dynasty_ranking = None
    if rank_data:
        dynasty_ranking = {
            "ecr": rank_data.get("ecr"),
            "positional_rank": f"{rank_data.get('pos', '')}{rank_data.get('ecr', '')}",
            "team": rank_data.get("team"),
        }

    # --- Validate required fields (percentile ranks + consistency) ---
    missing_required: list[str] = []
    if consistency_data is None:
        missing_required.append(f"{display_name}: consistency metrics unavailable")
    has_pctile = any(
        any(k.endswith("_pctile") for k in row) for cat in season_stats.values() if isinstance(cat, list) for row in cat
    )
    if season_stats and not has_pctile:
        missing_required.append(f"{display_name}: positional percentile ranks unavailable")

    return {
        "player_info": {
            "player_name": display_name,
            "position": player_info.get("position"),
            "team": player_info.get("latest_team"),
            "age": player_info.get("age"),
            "years_of_experience": player_info.get("years_of_experience"),
            "height": player_info.get("height"),
            "weight": player_info.get("weight"),
        },
        "season_stats": season_stats,
        "consistency": consistency_data,
        "dynasty_ranking": dynasty_ranking,
        "game_log": game_log if include_game_log else None,
        "usage_trends": usage_trends,
        "scoring_format": scoring_format,
        "data_season": data_season,
        "missing_required_data": missing_required if missing_required else None,
    }
