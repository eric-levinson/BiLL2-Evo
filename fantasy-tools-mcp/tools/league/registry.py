from fastmcp import FastMCP
from supabase import Client

from .info import (
    get_defensive_players_game_stats as _get_defensive_players_game_stats,
)
from .info import (
    get_offensive_players_game_stats as _get_offensive_players_game_stats,
)
from .info import (
    get_stats_metadata as _get_stats_metadata,
)

# All BiLL2 tools are read-only queries with no write-back capability
_TOOL_ANNOTATIONS = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": False,
}


def register_tools(mcp: FastMCP, supabase: Client):
    """Register league-related tools with the FastMCP instance."""

    @mcp.tool(
        annotations=_TOOL_ANNOTATIONS,
        description=(
            "Return game-stat field definitions for NFL offense/defense. Use to understand what game stat "
            "fields mean for deeper fantasy analysis. "
            "Category: 'offense'|'defense' (aliases: 'off','o','def','d'). "
            "Offense subcategories: overall, passing, rushing, receiving, "
            "pressure_and_sacks, special_teams, seasonal. "
            "Defense subcategories: overall, tackling, pressure, coverage, "
            "turnovers, penalties. Case-insensitive; omit subcategory to return full category."
        ),
    )
    def get_stats_metadata(category: str, subcategory: str | None = None) -> dict:
        return _get_stats_metadata(category, subcategory)

    @mcp.tool(
        annotations=_TOOL_ANNOTATIONS,
        description="""
        Fetch offensive weekly game stats for NFL players.

        Use for: weekly fantasy performance analysis, game log review, matchup evaluation, boom/bust assessment,
        start/sit decisions, recent performance validation.

        Optional filters:
        - player_names: list of partial/full player name strings to match (case-insensitive partial matching supported).
        - season_list: list of seasons (ints) to restrict results to specific years.
        - weekly_list: list of week numbers (ints) to restrict results to specific game weeks.
        - metrics: list of metric names to include; if omitted a default set of core offensive metrics is returned.

        Controls:
        - order_by_metric: metric name to sort results by (descending).
        - limit: maximum number of rows to return (default 100; implementation may enforce a maximum cap).
        - positions: list of offensive positions to include (defaults to typical offensive roles, e.g. ['QB', 'RB', 'WR', 'TE']).

        Behavior and notes:
        - This function returns per-game (weekly) offensive statistics suitable for tools and agents; basic player info (season, week, player_name, team, position, merge_name, height, weight) is always included.
        - Typical metric categories available include:
            - Volume: passing yards, rushing yards, receiving yards, touchdowns, targets, snaps.
            - Efficiency/context: completion percentage, yards per attempt, yards after catch, missed tackle rate.
            - Situational/advanced: red zone efficiency, third down conversion rate, game identifiers, opponent, and other contextual fields.
        - For safety and performance, fully unfiltered queries (no player_names, season_list, weekly_list, or positions specified) may be refused or limited by the implementation; prefer narrowing queries by name, season, week, or position.
        - Returns: dict containing the queried rows and any metadata or error information.
        """,
    )
    def get_offensive_players_game_stats(
        player_names: list[str] | None = None,
        season_list: list[int] | None = None,
        weekly_list: list[int] | None = None,
        metrics: list[str] | None = None,
        order_by_metric: str | None = None,
        limit: int | None = 100,
        positions: list[str] | None = None,
    ) -> dict:
        return _get_offensive_players_game_stats(
            supabase,
            player_names=player_names,
            season_list=season_list,
            weekly_list=weekly_list,
            metrics=metrics,
            order_by_metric=order_by_metric,
            limit=limit,
            positions=positions,
        )

    @mcp.tool(
        annotations=_TOOL_ANNOTATIONS,
        description="""
        Fetch defensive weekly game stats for NFL players.

        Use for: streaming defense evaluation, matchup difficulty assessment, defensive playmaker identification,
        IDP league analysis, weekly performance validation.

        Optional filters:
        - player_names: list of partial/full player name strings to match (case-insensitive partial matching supported).
        - season_list: list of seasons (ints) to restrict results to specific years.
        - weekly_list: list of week numbers (ints) to restrict results to specific game weeks.
        - metrics: list of metric names to include; if omitted a default set of core defensive metrics is returned.

        Controls:
        - order_by_metric: metric name to sort results by (descending).
        - limit: maximum number of rows to return (default 100; implementation may enforce a maximum cap).
        - positions: list of defensive positions to include (defaults to typical defensive roles, e.g. ['CB', 'DB', 'DE', 'DL', 'LB', 'S']).

        Behavior and notes:
        - This function returns per-game (weekly) defensive statistics suitable for tools and agents; basic player info (season, week, player_name, team, position, merge_name, height, weight) is always included.
        - Typical metric categories available include:
            - Volume: tackles, assisted tackles, sacks, interceptions, targets, pressures, pass breakups.
            - Efficiency/context: completion percentage allowed, yards allowed, yards per target, passer rating allowed, missed tackle rate.
            - Situational/advanced: yards after catch allowed, air yards completed, receiving TDs allowed, game identifiers, opponent, and other contextual fields.
        - For safety and performance, fully unfiltered queries (no player_names, season_list, weekly_list, or positions specified) may be refused or limited by the implementation; prefer narrowing queries by name, season, week, or position.
        - Returns: dict containing the queried rows and any metadata or error information.
        """,
    )
    def get_defensive_players_game_stats(
        player_names: list[str] | None = None,
        season_list: list[int] | None = None,
        weekly_list: list[int] | None = None,
        metrics: list[str] | None = None,
        order_by_metric: str | None = None,
        limit: int | None = 100,
        positions: list[str] | None = None,
    ) -> dict:
        return _get_defensive_players_game_stats(
            supabase,
            player_names=player_names,
            season_list=season_list,
            weekly_list=weekly_list,
            metrics=metrics,
            order_by_metric=order_by_metric,
            limit=limit,
            positions=positions,
        )
