import os

from dotenv import load_dotenv
from fastmcp import FastMCP
from supabase import create_client

from helpers.tool_analytics import ToolAnalyticsMiddleware
from tools.registry import register_tools

load_dotenv()  # Loads variables from .env

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Initialize FastMCP
mcp = FastMCP("Gridiron Tools MCP")

# Register analytics middleware (instruments every tool call)
mcp.add_middleware(ToolAnalyticsMiddleware())

# Register all tools
register_tools(mcp, supabase)

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)

# Add a simple health check (if FastMCP supports it)
