"""
Waiver wire context composite tool for assembling pickup decision data.

Fetches trending players from Sleeper, enriches each with season stats including
positional percentile ranks, consistency metrics, dynasty rankings, and league
roster availability. All internal fetches run in parallel via ThreadPoolExecutor.
Returns a data-only bundle with zero analysis or opinions — the LLM interprets the data.
"""

from concurrent.futures import ThreadPoolExecutor

from supabase import Client

from helpers.query_utils import build_player_stats_query
from tools.fantasy.info import get_sleeper_league_rosters, get_sleeper_trending_players
from tools.metrics.info import (
    get_advanced_passing_stats,
    get_advanced_receiving_stats,
    get_advanced_rushing_stats,
)
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
]

_RECEIVING_PCTILE_COLS = [
    "targets_pctile",
    "target_share_pctile",
    "receiving_yards_pctile",
    "fantasy_points_ppr_pctile",
    "catch_percentage_pctile",
]

_PASSING_METRICS = [
    "passing_yards",
    "passing_tds",
    "passer_rating",
    "completion_percentage",
    "fantasy_points",
    "fantasy_points_ppr",
    "passing_yards_pctile",
    "passing_tds_pctile",
    "passer_rating_pctile",
    "completion_percentage_pctile",
    "fantasy_points_ppr_pctile",
]

_RUSHING_METRICS = [
    "carries",
    "rushing_yards",
    "rushing_tds",
    "fantasy_points",
    "fantasy_points_ppr",
    "avg_rush_yards",
    "carries_pctile",
    "rushing_yards_pctile",
    "rushing_tds_pctile",
    "fantasy_points_ppr_pctile",
    "avg_rush_yards_pctile",
]


def get_waiver_context(
    supabase: Client,
    league_id: str,
    position_filter: str | None = None,
    scoring_format: str = "ppr",
    top_n: int = 10,
) -> dict:
    """
    Assemble all data needed for waiver wire decisions in a single call.

    Fetches trending players from Sleeper (adds), enriches each with season stats
    including positional percentile ranks, consistency metrics, dynasty rankings,
    and checks roster availability in the specified league. Phase 1 fetches trending
    players, rankings, and rosters in parallel. Phase 2 enriches each trending
    player with stats and consistency in parallel.

    Args:
        supabase: The Supabase client instance
        league_id: Sleeper league ID for roster availability check
        position_filter: Optional position to filter trending players (e.g., "WR", "RB")
        scoring_format: Scoring format ("ppr", "half_ppr", "standard")
        top_n: Number of trending players to return (default 10, max 25)

    Returns:
        dict: Waiver context bundle with keys:
            - trending_players: List of enriched player data bundles
            - league_id: The league ID used
            - scoring_format: Scoring format string
            - data_season: Most recent season in the data
            - players_without_stats: Names with no stats found
    """
    if not league_id:
        raise ValueError("league_id is required for waiver context")

    safe_top_n = min(max(int(top_n), 1), 25)

    # --- Internal fetch functions ---

    def _fetch_trending() -> list[dict]:
        try:
            return get_sleeper_trending_players(
                sport="nfl", add_drop="add", hours=24, limit=safe_top_n, supabase=supabase
            )
        except Exception:
            return []

    def _fetch_dynasty_ranks() -> list[dict]:
        try:
            return get_fantasy_ranks(supabase=supabase, limit=500)
        except Exception:
            return []

    def _fetch_rosters() -> list[dict]:
        try:
            return get_sleeper_league_rosters(league_id, summary=False, supabase=supabase)
        except Exception:
            return []

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

    # --- Phase 1: Fetch trending players, rankings, and rosters in parallel ---
    with ThreadPoolExecutor(max_workers=3) as executor:
        trending_future = executor.submit(_fetch_trending)
        rankings_future = executor.submit(_fetch_dynasty_ranks)
        rosters_future = executor.submit(_fetch_rosters)

        trending_raw = trending_future.result()
        all_rankings = rankings_future.result()
        rosters = rosters_future.result()

    # Apply position filter if specified
    if position_filter:
        pos_upper = position_filter.upper()
        trending_raw = [p for p in trending_raw if (p.get("position") or "").upper() == pos_upper]

    # Build rostered player IDs set for availability check
    rostered_ids: set[str] = set()
    for roster in rosters:
        players = roster.get("players") or []
        rostered_ids.update(str(pid) for pid in players)

    # Build rankings lookup
    rankings_by_name: dict[str, dict] = {}
    for entry in all_rankings:
        pname = entry.get("player", "").lower()
        if pname:
            rankings_by_name[pname] = entry

    # --- Phase 2: Enrich each trending player with stats and consistency ---
    player_names_to_enrich = []
    for tp in trending_raw:
        name = tp.get("player_name") or tp.get("display_name")
        if name:
            player_names_to_enrich.append(name)

    worker_count = len(player_names_to_enrich) * 5  # recv + recv_pctile + pass + rush + consistency
    max_workers = min(max(worker_count, 1), 12)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        recv_futures = {n: executor.submit(_fetch_receiving, n) for n in player_names_to_enrich}
        recv_pctile_futures = {n: executor.submit(_fetch_receiving_pctile, n) for n in player_names_to_enrich}
        pass_futures = {n: executor.submit(_fetch_passing, n) for n in player_names_to_enrich}
        rush_futures = {n: executor.submit(_fetch_rushing, n) for n in player_names_to_enrich}
        consistency_futures = {n: executor.submit(_fetch_consistency, n) for n in player_names_to_enrich}

        receiving = {n: f.result() for n, f in recv_futures.items()}
        recv_pctile = {n: f.result() for n, f in recv_pctile_futures.items()}
        passing = {n: f.result() for n, f in pass_futures.items()}
        rushing = {n: f.result() for n, f in rush_futures.items()}
        consistency = {n: f.result() for n, f in consistency_futures.items()}

    # --- Merge receiving percentile ranks from MV into receiving stats ---
    for name in player_names_to_enrich:
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

    # --- Assemble player bundles ---
    players_without_stats: list[str] = []
    data_season: int | None = None

    player_bundles = []
    for tp in trending_raw:
        player_name = tp.get("player_name") or tp.get("display_name")
        if not player_name:
            continue

        player_id = str(tp.get("player_id", ""))
        is_available = player_id not in rostered_ids if player_id else None

        bundle: dict = {
            "player_name": player_name,
            "position": tp.get("position"),
            "team": tp.get("team"),
            "trending_add_count": tp.get("count"),
            "is_available_in_league": is_available,
        }

        # Season stats with percentile ranks
        season_stats: dict = {}
        has_stats = False
        for label, stat_data in [
            ("receiving", receiving.get(player_name, [])),
            ("passing", passing.get(player_name, [])),
            ("rushing", rushing.get(player_name, [])),
        ]:
            if stat_data:
                season_stats[label] = stat_data
                has_stats = True
                for row in stat_data:
                    s = row.get("season")
                    if s and (data_season is None or s > data_season):
                        data_season = s
        bundle["season_stats"] = season_stats

        if not has_stats:
            players_without_stats.append(player_name)

        # Consistency metrics (required)
        bundle["consistency"] = consistency.get(player_name)

        # Dynasty ranking
        rank_data = rankings_by_name.get(player_name.lower())
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
        "trending_players": player_bundles,
        "league_id": league_id,
        "scoring_format": scoring_format,
        "data_season": data_season,
        "players_without_stats": players_without_stats,
        "missing_required_data": missing_required if missing_required else None,
    }
