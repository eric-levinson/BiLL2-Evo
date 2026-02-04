from fastmcp import FastMCP
from supabase import Client
from .info import get_player_info, get_players_by_sleeper_id

def register_tools(mcp: FastMCP, supabase: Client):
    """
    Register player info tools with the FastMCP instance.
    """
    @mcp.tool(
        description="Fetch basic information for players such as: name, latest team, position, height, weight, birthdate (age) and identifiers"
    )
    def get_player_info_tool(player_names: list[str]) -> list[dict]:
        return get_player_info(supabase, player_names)
    
    @mcp.tool(
        description="Fetch basic information for players by their Sleeper IDs."
    )
    def get_players_by_sleeper_id_tool(sleeper_ids: list[str]) -> list[dict]:
        return get_players_by_sleeper_id(supabase, sleeper_ids)
