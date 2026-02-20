"""
Start/sit context composite tool for assembling weekly decision data.

Fetches player season stats with positional percentile ranks, weekly performance,
consistency metrics, and dynasty rankings in parallel using ThreadPoolExecutor.
Returns a data-only bundle with zero analysis or opinions — the LLM interprets the data.
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
    "carries_pctile",
    "rushing_yards_pctile",
    "rushing_tds_pctile",
    "rushing_epa_pctile",
    "fantasy_points_ppr_pctile",
    "avg_rush_yards_pctile",
]


def get_start_sit_context(
    supabase: Client,
    player_names: list[str],
    week: int,
    season: int | None = None,
    scoring_format: str = "ppr",
) -> dict:
    """
    Assemble all data needed for a fantasy start/sit decision in a single call.

    Fetches player info, position-appropriate season stats with positional percentile
    ranks, weekly performance for the specified week, consistency metrics, and dynasty
    rankings. All internal fetches run in parallel via ThreadPoolExecutor.

    Args:
        supabase: The Supabase client instance
        player_names: Players to evaluate for start/sit (1-8 names)
        week: NFL week number (1-18) to evaluate
        season: Optional season year filter (defaults to most recent)
        scoring_format: Scoring format ("ppr", "half_ppr", "standard")

    Returns:
        dict: Start/sit context bundle with keys:
            - players: List of player data bundles
            - week: The evaluated week
            - scoring_format: Scoring format string
            - data_season: Most recent season in the data
            - players_not_found: Names that couldn't be resolved
    """
    if not player_names:
        raise ValueError("player_names must contain at least one player")
    if len(player_names) > 8:
        raise ValueError("Maximum 8 players for start/sit comparison")
    if not isinstance(week, int) or week < 1 or week > 18:
        raise ValueError("week must be an integer between 1 and 18")

    unique_names = list(dict.fromkeys(player_names))

    # --- Internal fetch functions ---

    def _fetch_info(name: str) -> list[dict] | None:
        try:
            return get_player_info(supabase, [name])
        except Exception:
            return None

    def _fetch_receiving(name: str) -> list[dict]:
        try:
            result = get_advanced_receiving_stats(
                supabase=supabase, player_names=[name], metrics=_RECEIVING_METRICS, limit=3
            )
            return result.get("advReceivingStats", [])
        except Exception:
            return []

    def _fetch_passing(name: str) -> list[dict]:
        try:
            result = get_advanced_passing_stats(
                supabase=supabase, player_names=[name], metrics=_PASSING_METRICS, limit=3
            )
            return result.get("advPassingStats", [])
        except Exception:
            return []

    def _fetch_rushing(name: str) -> list[dict]:
        try:
            result = get_advanced_rushing_stats(
                supabase=supabase, player_names=[name], metrics=_RUSHING_METRICS, limit=3
            )
            return result.get("advRushingStats", [])
        except Exception:
            return []

    def _fetch_weekly(name: str) -> list[dict]:
        try:
            result = build_player_stats_query(
                supabase=supabase,
                table_name="nflreadr_nfl_player_stats",
                base_columns=["season", "week", "player_display_name", "recent_team", "position"],
                player_name_column="player_display_name",
                position_column="position",
                default_positions=["QB", "RB", "WR", "TE"],
                return_key="weeklyStats",
                player_names=[name],
                weekly_list=[week],
                season_list=[season] if season else None,
                metrics=["fantasy_points", "fantasy_points_ppr"],
                limit=5,
                player_sort_column="player_display_name",
            )
            return result.get("weeklyStats", [])
        except Exception:
            return []

    def _fetch_consistency(name: str) -> dict | None:
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

    def _fetch_receiving_pctile(name: str) -> list[dict]:
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

    # --- Parallel fetch (single phase — all queries at once) ---
    worker_count = len(unique_names) * 6 + 1  # 6 fetches per player + rankings
    max_workers = min(worker_count, 12)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        info_futures = {n: executor.submit(_fetch_info, n) for n in unique_names}
        recv_futures = {n: executor.submit(_fetch_receiving, n) for n in unique_names}
        recv_pctile_futures = {n: executor.submit(_fetch_receiving_pctile, n) for n in unique_names}
        pass_futures = {n: executor.submit(_fetch_passing, n) for n in unique_names}
        rush_futures = {n: executor.submit(_fetch_rushing, n) for n in unique_names}
        weekly_futures = {n: executor.submit(_fetch_weekly, n) for n in unique_names}
        consistency_futures = {n: executor.submit(_fetch_consistency, n) for n in unique_names}
        rankings_future = executor.submit(_fetch_dynasty_ranks)

        infos = {n: f.result() for n, f in info_futures.items()}
        receiving = {n: f.result() for n, f in recv_futures.items()}
        recv_pctile = {n: f.result() for n, f in recv_pctile_futures.items()}
        passing = {n: f.result() for n, f in pass_futures.items()}
        rushing = {n: f.result() for n, f in rush_futures.items()}
        weekly = {n: f.result() for n, f in weekly_futures.items()}
        consistency = {n: f.result() for n, f in consistency_futures.items()}
        all_rankings = rankings_future.result()

    # --- Merge receiving percentile ranks from MV into receiving stats ---
    for name in unique_names:
        recv_rows = receiving.get(name, [])
        pctile_rows = recv_pctile.get(name, [])
        if recv_rows and pctile_rows:
            pctile_by_season = {r.get("season"): r for r in pctile_rows}
            for row in recv_rows:
                pctile = pctile_by_season.get(row.get("season"))
                if pctile:
                    for col in _RECEIVING_PCTILE_COLS:
                        if col in pctile:
                            row[col] = pctile[col]

    # --- Build rankings lookup ---
    rankings_by_name: dict[str, dict] = {}
    for entry in all_rankings:
        pname = entry.get("player", "").lower()
        if pname:
            rankings_by_name[pname] = entry

    # --- Assemble player bundles ---
    players_not_found: list[str] = []
    data_season: int | None = None

    player_bundles = []
    for name in unique_names:
        info_list = infos.get(name)
        player_info = info_list[0] if info_list else None

        if not player_info:
            players_not_found.append(name)
            continue

        display_name = player_info.get("display_name", name)

        bundle: dict = {
            "player_name": display_name,
            "position": player_info.get("position"),
            "team": player_info.get("latest_team"),
            "age": player_info.get("age"),
        }

        # Position-appropriate season stats with percentile ranks
        season_stats: dict = {}
        for label, stat_data in [
            ("receiving", receiving.get(name, [])),
            ("passing", passing.get(name, [])),
            ("rushing", rushing.get(name, [])),
        ]:
            if stat_data:
                season_stats[label] = stat_data
                for row in stat_data:
                    s = row.get("season")
                    if s and (data_season is None or s > data_season):
                        data_season = s
        bundle["season_stats"] = season_stats

        # Weekly performance for specified week
        bundle["weekly_stats"] = weekly.get(name, [])

        # Consistency metrics (required)
        bundle["consistency"] = consistency.get(name)

        # Dynasty ranking
        rank_data = rankings_by_name.get(name.lower()) or rankings_by_name.get(display_name.lower())
        if rank_data:
            bundle["dynasty_ranking"] = {
                "ecr": rank_data.get("ecr"),
                "positional_rank": f"{rank_data.get('pos', '')}{rank_data.get('ecr', '')}",
                "team": rank_data.get("team"),
            }
        else:
            bundle["dynasty_ranking"] = None

        player_bundles.append(bundle)

    # --- Validate required fields (percentile ranks + consistency) ---
    missing_required: list[str] = []
    for bundle in player_bundles:
        pname = bundle["player_name"]
        if bundle.get("consistency") is None:
            missing_required.append(f"{pname}: consistency metrics unavailable")
        stats = bundle.get("season_stats", {})
        has_pctile = any(
            any(k.endswith("_pctile") for k in row) for cat in stats.values() if isinstance(cat, list) for row in cat
        )
        if stats and not has_pctile:
            missing_required.append(f"{pname}: positional percentile ranks unavailable")

    return {
        "players": player_bundles,
        "week": week,
        "scoring_format": scoring_format,
        "data_season": data_season,
        "players_not_found": players_not_found,
        "missing_required_data": missing_required if missing_required else None,
    }
