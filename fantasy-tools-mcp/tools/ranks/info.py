"""
Dynasty ranks tools for MCP
"""

from supabase import Client

# Tool 1: Get distinct page_type values for context


def get_fantasy_rank_page_types(supabase: Client) -> list[str]:
    """
    Returns a list of distinct page_type values from vw_dynasty_ranks for context.
    """
    try:
        response = supabase.rpc("get_distinct_dynasty_rank_page_types").execute()
        return [row["page_type"] for row in response.data]
    except Exception as e:
        raise Exception(f"Error fetching page_type values: {e!s}") from None


# Tool 2: Get dynasty ranks, filtered by position (optional), limited to 150 rows


def get_fantasy_ranks(
    supabase: Client, position: str | None = None, page_type: str | None = None, limit: int = 30
) -> list[dict]:
    """
    Returns fantasy ranks from vw_dynasty_ranks, filtered by position and/or page_type if provided.

    Parameters:
    - supabase: Supabase client
    - position: optional position filter (e.g., 'RB', 'WR')
    - page_type: optional page_type filter
    - limit: maximum number of rows to return (defaults to 30)

    Selects the most pertinent columns for fantasy analysis.
    """
    columns = [
        "player",
        "team",
        "pos",
        "ecr",
        "age",
        "years_of_experience",
        "team_nfl",
        "team_full",
        "player_owned_avg",
    ]
    try:
        query = supabase.table("vw_dynasty_ranks").select(",".join(columns))
        if position:
            query = query.eq("pos", position)
        if page_type:
            query = query.eq("page_type", page_type)

        # enforce a sensible cap to avoid accidental huge responses
        max_limit = 500
        safe_limit = min(int(limit) if limit and int(limit) > 0 else 30, max_limit)
        response = query.order("ecr", desc=False).limit(safe_limit).execute()
        return response.data
    except Exception as e:
        raise Exception(f"Error fetching dynasty ranks: {e!s}") from None


#        # Sanitize player names (escape single quotes for SQL)
#        sanitized_names = [name.replace("'", "").replace(".", "") for name in player_names]
#
#        # Build the OR filter - use comma separation for Python client
#        or_filter = ",".join([f"display_name.ilike.%{name}%" for name in sanitized_names])
