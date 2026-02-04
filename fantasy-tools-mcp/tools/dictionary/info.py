"""
Dictionary info tools
"""
from supabase import Client

def get_dictionary_info(supabase: Client, search_criteria: list[str] = None) -> list[dict]:
    """
    Fetches rows from the vw_dictionary_combined view, optionally filtering by search criteria in the description field.

    Args:
        supabase: The Supabase client instance
        search_criteria: List of strings to search for in the description (optional)

    Returns:
        List of dictionaries containing matching rows from vw_dictionary_combined.
    """
    try:
        query = supabase.table("vw_dictionary_combined").select("field", "description", "source_table")
        # Apply search criteria if provided
        if search_criteria:
            # Build OR filter for partial matches in description
            or_filter = ",".join([f"description.ilike.%{term}%" for term in search_criteria])
            query = query.or_(or_filter)
        response = query.execute()
        return response.data
    except Exception as e:
        raise Exception(f"Error fetching dictionary info: {str(e)}")

