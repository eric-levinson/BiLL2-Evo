from supabase import Client
from tools.fantasy.sleeper_wrapper.user import User
from tools.fantasy.sleeper_wrapper.league import League
from tools.fantasy.sleeper_wrapper.players import Players
from tools.fantasy.sleeper_wrapper.drafts import Drafts

#Test league ID:
#1225572389929099264


def _resolve_player_ids(supabase: Client, player_ids: list[str]) -> list[dict]:
    """Convert Sleeper player IDs to compact player info via Supabase (not Sleeper API).

    Returns list of {name, position, team} dicts in the same order as input IDs.
    Non-numeric IDs (e.g. team defense "HOU") are kept as-is since they won't
    exist in the player table.
    """
    if not player_ids:
        return []

    # sleeper_id is numeric in the DB — filter out non-numeric IDs (team defenses like "HOU")
    numeric_ids = [pid for pid in player_ids if pid.isdigit()]

    lookup = {}
    if numeric_ids:
        # Use in_ filter for a single clean query
        response = (
            supabase.table("vw_nfl_players_with_dynasty_ids")
            .select("sleeper_id, display_name, latest_team, position")
            .in_("sleeper_id", [int(pid) for pid in numeric_ids])
            .execute()
        )
        for row in response.data:
            lookup[str(int(row["sleeper_id"]))] = {
                "name": row.get("display_name", "Unknown"),
                "position": row.get("position", ""),
                "team": row.get("latest_team", ""),
            }

    # Return in same order as input; non-numeric IDs (team defenses) get a readable fallback
    return [lookup.get(str(pid), {"name": pid, "position": "DEF" if not pid.isdigit() else "", "team": pid if not pid.isdigit() else ""}) for pid in player_ids]

#tool definition to get sleeper leagues from an EXACT username with verbose option
def get_sleeper_leagues_by_username(username: str, verbose: bool = False) -> list[dict]:
    """
    Fetch sleeper leagues for a specific user by their username.
    """
    if not username:
        return [{"error": "Please provide a valid username as a string."}]
    try:
        user = User(username)
        leagues = user.get_all_leagues("nfl", 2025)
        default_keys = [
            "status", "name", "draft_id", "season_type", "season", "total_rosters", "league_id"
        ]
        verbose_keys = ["scoring_settings", "settings", "roster_positions"]
        filtered_leagues = []
        for league in leagues:
            filtered = {k: league.get(k) for k in default_keys}
            if verbose:
                for k in verbose_keys:
                    filtered[k] = league.get(k)
            filtered_leagues.append(filtered)
        return filtered_leagues
    except Exception as e:
        return Exception(f"Error fetching sleeper leagues: {str(e)}")

def get_sleeper_league_rosters(league_id: str, summary: bool = False, supabase: Client | None = None) -> list[dict]:
    """Retrieve rosters for a given Sleeper league ID, annotated with usernames.

    Args:
        league_id: The Sleeper league ID.
        summary: If True, returns compact roster info with player names/positions/teams
                 instead of full roster objects. If False (default), returns full data.
        supabase: Supabase client (required when summary=True).
    """

    if not league_id:
        return [{"error": "Please provide a valid league_id as a string."}]
    try:
        league = League(league_id)
        rosters = league.get_rosters()
        users = league.get_users()
        user_map = league.map_users_to_team_name(users)

        for roster in rosters:
            owner = roster.get("owner_id")
            roster["owner_name"] = user_map.get(owner)

        if not summary:
            return rosters

        summary_rosters = []
        for roster in rosters:
            summary_roster = {
                "roster_id": roster.get("roster_id"),
                "owner_name": roster.get("owner_name"),
            }

            player_ids = roster.get("players") or []
            summary_roster["players"] = _resolve_player_ids(supabase, player_ids)

            starter_ids = roster.get("starters") or []
            if starter_ids:
                summary_roster["starters"] = _resolve_player_ids(supabase, starter_ids)

            summary_rosters.append(summary_roster)

        return summary_rosters
    except Exception as e:
        raise Exception(f"Error fetching sleeper leagues: {str(e)}")


def get_sleeper_league_users(league_id: str) -> list[dict]:
    """Retrieve users for a given Sleeper league ID."""
    if not league_id:
        return [{"error": "Please provide a valid league_id as a string."}]
    try:
        league = League(league_id)
        return league.get_users()
    except Exception as e:
        raise Exception(f"Error fetching sleeper leagues: {str(e)}")


def get_sleeper_league_matchups(league_id: str, week: int, summary: bool = False, supabase: Client | None = None) -> list[dict]:
    """Retrieve matchups for a given Sleeper league and week.

    Args:
        league_id: The Sleeper league ID.
        week: The week number to retrieve matchups for.
        summary: If True, returns compact matchup info with player names/positions/teams
                 instead of full player ID arrays. If False (default), returns full data.
        supabase: Supabase client (required when summary=True).

    The caller must supply the target week. Each matchup is annotated with
    the username of the roster's owner.
    """
    if not league_id:
        return [{"error": "Please provide a valid league_id as a string."}]
    if week is None:
        return [{"error": "Please provide the target week as an integer."}]
    try:
        league = League(league_id)
        matchups = league.get_matchups(week)
        rosters = league.get_rosters()
        users = league.get_users()
        roster_to_owner = league.map_rosterid_to_ownerid(rosters)
        user_map = league.map_users_to_team_name(users)
        for matchup in matchups:
            rid = matchup.get("roster_id")
            owner = roster_to_owner.get(rid)
            matchup["owner_name"] = user_map.get(owner)

        if not summary:
            return matchups

        summary_matchups = []
        for matchup in matchups:
            summary_matchup = {
                "matchup_id": matchup.get("matchup_id"),
                "roster_id": matchup.get("roster_id"),
                "owner_name": matchup.get("owner_name"),
                "points": matchup.get("points"),
            }

            player_ids = matchup.get("players") or []
            summary_matchup["players"] = _resolve_player_ids(supabase, player_ids)

            starter_ids = matchup.get("starters") or []
            if starter_ids:
                summary_matchup["starters"] = _resolve_player_ids(supabase, starter_ids)

            summary_matchups.append(summary_matchup)

        return summary_matchups
    except Exception as e:
        raise Exception(f"Error fetching sleeper matchups: {str(e)}")


def get_sleeper_league_transactions(
    league_id: str, week: int, txn_type: str | None = None
) -> list[dict]:
    """Retrieve transactions for a given Sleeper league and week.

    Optionally filter the results by transaction type (e.g., "trade",
    "waiver", or "free_agent"). Each transaction includes the creator's
    username and the usernames of the involved rosters.
    """

    if not league_id:
        return [{"error": "Please provide a valid league_id as a string."}]
    if week is None:
        return [{"error": "Please provide the target week as an integer."}]
    if txn_type is not None:
        if not isinstance(txn_type, str):
            return [{"error": "txn_type must be a string if provided."}]
        allowed_types = {"trade", "waiver", "free_agent"}
        if txn_type not in allowed_types:
            return [
                {
                    "error": (
                        "txn_type must be one of 'trade', 'waiver', or 'free_agent'."
                    )
                }
            ]
    try:
        league = League(league_id)
        transactions = league.get_transactions(week)
        if txn_type:
            transactions = [t for t in transactions if t.get("type") == txn_type]

        rosters = league.get_rosters()
        users = league.get_users()
        roster_to_owner = league.map_rosterid_to_ownerid(rosters)
        # Use the same logic as League.map_users_to_team_name
        user_map = {}
        for user in users:
            try:
                user_map[user["user_id"]] = user["metadata"]["team_name"]
            except:
                user_map[user["user_id"]] = user.get("display_name")

        for txn in transactions:
            creator_id = txn.get("creator")
            txn["creator_owner_name"] = user_map.get(creator_id)
            roster_ids = txn.get("roster_ids", []) or []
            txn["roster_owner_names"] = [
                user_map.get(roster_to_owner.get(rid)) for rid in roster_ids
            ]
        return transactions
    except Exception as e:
        raise Exception(f"Error fetching sleeper transactions: {str(e)}")


def get_sleeper_trending_players(
    sport: str = "nfl", add_drop: str = "add", hours: int = 24, limit: int = 25
) -> list[dict]:
    """Retrieve trending players from Sleeper.

    Args:
        sport: The sport to query (e.g., "nfl", "nba", "lcs").
        add_drop: Whether to return trending adds ("add") or drops ("drop").
        hours: Number of hours to look back.
        limit: Maximum number of players to return.

    Returns:
        A list of dictionaries containing the player ID and the corresponding
        count of adds or drops.
    """

    if not isinstance(sport, str):
        return [{"error": "sport must be a string."}]
    if add_drop not in {"add", "drop"}:
        return [
            {
                "error": "add_drop must be either 'add' or 'drop'.",
            }
        ]
    if not isinstance(hours, int) or hours <= 0:
        return [{"error": "hours must be a positive integer."}]
    if not isinstance(limit, int) or limit <= 0:
        return [{"error": "limit must be a positive integer."}]

    try:
        players = Players()
        return players.get_trending_players(sport, add_drop, hours, limit)
    except Exception as e:
        raise Exception(f"Error fetching trending players: {str(e)}")


def get_sleeper_user_drafts(
    username: str, sport: str = "nfl", season: int = 2025
) -> list[dict]:
    """Retrieve all drafts for a given Sleeper user.

    Args:
        username: The Sleeper username.
        sport: The sport to query (default "nfl").
        season: The season year (default 2025).

    Returns:
        A list of draft objects as returned by the Sleeper API.
    """

    if not username:
        return [{"error": "Please provide a valid username as a string."}]
    try:
        user = User(username)
        return user.get_all_drafts(sport, season)
    except Exception as e:
        raise Exception(f"Error fetching sleeper drafts: {str(e)}")

def get_sleeper_league_by_id(league_id: str, summary: bool = False) -> dict:
    """Retrieve a Sleeper league by its ID.

    Args:
        league_id: The Sleeper league ID.
        summary: If True, returns compact league data without nested settings objects.
                 If False (default), returns full data.
    """
    if not league_id:
        return {"error": "Please provide a valid league_id as a string."}
    try:
        league = League(league_id)
        league_data = league.get_league()

        if not summary:
            return league_data

        # Summary mode: return only essential league info, exclude heavy nested objects
        default_keys = [
            "status", "name", "draft_id", "season_type", "season", "total_rosters", "league_id"
        ]
        summary_data = {k: league_data.get(k) for k in default_keys}
        return summary_data
    except Exception as e:
        raise Exception(f"Error fetching sleeper league: {str(e)}")

def get_sleeper_draft_by_id(draft_id: str) -> dict:
    """Retrieve a Sleeper draft by its ID."""
    if not draft_id:
        return {"error": "Please provide a valid draft_id as a string."}
    try:
        draft = Drafts(draft_id)
        return draft.get_specific_draft()
    except Exception as e:
        raise Exception(f"Error fetching sleeper draft: {str(e)}")

def get_sleeper_all_draft_picks_by_id(draft_id: str) -> dict:
    """Return all draft picks for a draft ID wrapped in a dict (serializable)."""
    if not draft_id:
        return {"error": "Please provide a valid draft_id as a string."}
    try:
        draft = Drafts(draft_id)
        picks = draft.get_all_picks()
        if isinstance(picks, Exception):
            return {"error": str(picks)}
        # If the wrapper returns a list, wrap it under a key so MCP can serialize
        if isinstance(picks, list):
            return {"picks": picks}
        # If it's already a dict, pass it through
        if isinstance(picks, dict):
            return picks
        # Fallback for other types
        return {"result": picks}
    except Exception as e:
        return {"error": f"Error fetching sleeper draft picks: {str(e)}"}

#[{
#      "co_owners": null,
#      "keepers": null,
#      "league_id": "1225572389929099264",
#      "metadata": null,
#      "owner_id": "471503535968612352",
#      "player_map": null,
#      "players": null,
#      "reserve": null,
#      "roster_id": 3,
#      "settings": {
#            "fpts": 0,
#            "losses": 0,
#            "ties": 0,
#            "total_moves": 0,
#            "waiver_budget_used": 0,
#            "waiver_position": 6,
#            "wins": 0
#      },
#      "starters": [
#            "0",
#            "0",
#            "0",
#            "0",
#            "0",
#            "0",
#            "0",
#            "0",
#            "0",
#            "0",
#            "0",
#            "0",
#            "0",
#            "0",
#            "0"
#      ],
#      "taxi": null,
#      "owner_name": "filthy606"
#}]