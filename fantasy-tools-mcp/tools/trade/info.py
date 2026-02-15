"""
Trade context composite tool for assembling trade evaluation data.

Fetches player profiles, dynasty rankings, consistency metrics, and optional
league context in parallel using ThreadPoolExecutor. Returns a data-only bundle
with zero analysis or opinions — the LLM interprets the data.
"""

from concurrent.futures import ThreadPoolExecutor

from supabase import Client

from helpers.query_utils import build_player_stats_query
from tools.player.info import get_player_profile
from tools.ranks.info import get_fantasy_ranks


def get_trade_context(
    supabase: Client,
    give_player_names: list[str],
    receive_player_names: list[str],
    league_id: str | None = None,
    scoring_format: str = "ppr",
    include_weekly: bool = False,
    recent_weeks: int = 4,
) -> dict:
    """
    Assemble all data needed for fantasy trade evaluation in a single call.

    Fetches player info, season stats with fantasy points (PPR and standard),
    dynasty rankings, consistency metrics, and optional league context. All
    internal fetches run in parallel via ThreadPoolExecutor to avoid event loop
    conflicts with FastMCP's async runtime.

    Args:
        supabase: The Supabase client instance
        give_player_names: Players being given away (1-5 names)
        receive_player_names: Players being received (1-5 names)
        league_id: Optional Sleeper league ID for league context
        scoring_format: Scoring format ("ppr", "half_ppr", "standard")
        include_weekly: If True, includes recent weekly performance data
        recent_weeks: Number of recent weeks to include (default 4)

    Returns:
        dict: Trade context bundle with keys:
            - give_side: Player data bundles for the give side
            - receive_side: Player data bundles for the receive side
            - league_context: League info dict or None
            - scoring_format: Scoring format string
            - data_season: Most recent season in the data
            - players_not_found: Names that couldn't be resolved
            - rankings_not_found: Players without dynasty rankings

    Raises:
        ValueError: If player lists are empty or exceed 5 per side
    """
    # --- Validate inputs ---
    if not give_player_names:
        raise ValueError("give_player_names must contain at least one player")
    if not receive_player_names:
        raise ValueError("receive_player_names must contain at least one player")
    if len(give_player_names) > 5:
        raise ValueError("Maximum 5 players per side (give_player_names exceeds limit)")
    if len(receive_player_names) > 5:
        raise ValueError("Maximum 5 players per side (receive_player_names exceeds limit)")

    # Deduplicate while preserving order
    all_names = list(dict.fromkeys(give_player_names + receive_player_names))

    # --- Internal fetch functions (each handles its own errors for graceful degradation) ---

    def _fetch_profile(name: str) -> dict | None:
        try:
            return get_player_profile(
                supabase=supabase,
                player_names=[name],
                metrics=["fantasy_points", "fantasy_points_ppr"],
                limit=3,
            )
        except Exception:
            return None

    def _fetch_dynasty_ranks() -> list[dict]:
        try:
            return get_fantasy_ranks(supabase=supabase, limit=500)
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

    def _fetch_league_context(lid: str) -> dict | None:
        try:
            from tools.fantasy.sleeper_wrapper.league import League

            league = League(lid)
            league_data = league.get_league()
            return {
                "league_id": lid,
                "name": league_data.get("name"),
                "total_rosters": league_data.get("total_rosters"),
                "roster_positions": league_data.get("roster_positions"),
                "scoring_settings": league_data.get("scoring_settings"),
                "season": league_data.get("season"),
                "status": league_data.get("status"),
            }
        except Exception:
            return None

    def _fetch_weekly_trend(name: str, weeks: int) -> list[dict]:
        try:
            result = build_player_stats_query(
                supabase=supabase,
                table_name="nflreadr_nfl_player_stats",
                base_columns=[
                    "season",
                    "week",
                    "player_display_name",
                    "recent_team",
                    "position",
                ],
                player_name_column="player_display_name",
                position_column="position",
                default_positions=["QB", "RB", "WR", "TE"],
                return_key="weeklyTrend",
                player_names=[name],
                metrics=["fantasy_points", "fantasy_points_ppr"],
                limit=weeks,
                player_sort_column="player_display_name",
            )
            return result.get("weeklyTrend", [])
        except Exception:
            return []

    # --- Parallel fetch ---
    worker_count = len(all_names) * 2 + 2
    if include_weekly:
        worker_count += len(all_names)
    max_workers = min(worker_count, 12)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        profile_futures = {name: executor.submit(_fetch_profile, name) for name in all_names}
        rankings_future = executor.submit(_fetch_dynasty_ranks)
        consistency_futures = {name: executor.submit(_fetch_consistency, name) for name in all_names}
        league_future = executor.submit(_fetch_league_context, league_id) if league_id else None
        weekly_futures = {}
        if include_weekly:
            weekly_futures = {name: executor.submit(_fetch_weekly_trend, name, recent_weeks) for name in all_names}

        profiles = {name: f.result() for name, f in profile_futures.items()}
        all_rankings = rankings_future.result()
        consistency = {name: f.result() for name, f in consistency_futures.items()}
        league_context = league_future.result() if league_future else None
        weekly_data = {name: f.result() for name, f in weekly_futures.items()} if include_weekly else {}

    # --- Build rankings lookup (by lowercased player name) ---
    rankings_by_name: dict[str, dict] = {}
    for rank_entry in all_rankings:
        player_name = rank_entry.get("player", "").lower()
        if player_name:
            rankings_by_name[player_name] = rank_entry

    # --- Assemble player bundles ---
    players_not_found: list[str] = []
    rankings_not_found: list[str] = []
    data_season: int | None = None

    def _build_player_bundle(name: str) -> dict | None:
        nonlocal data_season

        profile = profiles.get(name)
        player_info = None
        if profile:
            info_list = profile.get("playerInfo", [])
            if info_list:
                player_info = info_list[0]

        if not player_info:
            players_not_found.append(name)
            return None

        display_name = player_info.get("display_name", name)

        bundle: dict = {
            "player_name": display_name,
            "position": player_info.get("position"),
            "team": player_info.get("latest_team"),
            "age": player_info.get("age"),
            "years_of_experience": player_info.get("years_of_experience"),
        }

        # Season stats (includes fantasy_points and fantasy_points_ppr per category)
        season_stats: dict = {}
        for label, stat_key in [
            ("receiving", "receivingStats"),
            ("passing", "passingStats"),
            ("rushing", "rushingStats"),
        ]:
            stats = profile.get(stat_key, [])
            if stats:
                season_stats[label] = stats
                for row in stats:
                    s = row.get("season")
                    if s and (data_season is None or s > data_season):
                        data_season = s
        bundle["season_stats"] = season_stats

        # Dynasty ranking lookup (try input name, then display name)
        rank_data = rankings_by_name.get(name.lower())
        if not rank_data:
            rank_data = rankings_by_name.get(display_name.lower())

        if rank_data:
            bundle["dynasty_ranking"] = {
                "ecr": rank_data.get("ecr"),
                "positional_rank": f"{rank_data.get('pos', '')}{rank_data.get('ecr', '')}",
                "team": rank_data.get("team"),
            }
        else:
            bundle["dynasty_ranking"] = None
            rankings_not_found.append(display_name)

        # Consistency metrics
        bundle["consistency"] = consistency.get(name)

        # Weekly trend (if requested)
        if include_weekly:
            bundle["weekly_trend"] = weekly_data.get(name, [])

        return bundle

    give_side = []
    for name in give_player_names:
        bundle = _build_player_bundle(name)
        if bundle:
            give_side.append(bundle)

    receive_side = []
    for name in receive_player_names:
        bundle = _build_player_bundle(name)
        if bundle:
            receive_side.append(bundle)

    return {
        "give_side": give_side,
        "receive_side": receive_side,
        "league_context": league_context,
        "scoring_format": scoring_format,
        "data_season": data_season,
        "players_not_found": players_not_found,
        "rankings_not_found": rankings_not_found,
    }
