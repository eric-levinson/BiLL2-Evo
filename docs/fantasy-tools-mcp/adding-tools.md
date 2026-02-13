# Adding a New MCP Tool

## Step-by-Step

### 1. Create the business logic (`tools/{category}/info.py`)

```python
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_example_data(player_name: str, season: int = 2024) -> dict:
    """Fetch example data from Supabase.

    Args:
        player_name: NFL player name (e.g., "Justin Jefferson")
        season: NFL season year

    Returns:
        dict with 'data' key containing results, or 'error' key on failure
    """
    try:
        response = (
            supabase.table("example_table")
            .select("*")
            .ilike("player_name", f"%{player_name}%")
            .eq("season", season)
            .limit(50)
            .execute()
        )
        return {"data": response.data}
    except Exception as e:
        return {"error": str(e)}
```

### 2. Register with MCP (`tools/{category}/registry.py`)

```python
from tools.{category}.info import get_example_data


def register_example_tools(mcp):
    @mcp.tool()
    def get_example_data_tool(player_name: str, season: int = 2024) -> dict:
        """Fetch example data for an NFL player.

        Args:
            player_name: NFL player name (e.g., "Justin Jefferson")
            season: NFL season year (default: 2024)
        """
        return get_example_data(player_name, season)
```

### 3. Wire into central registry (`tools/registry.py`)

Add the import and call in `register_all_tools()`:

```python
from tools.{category}.registry import register_example_tools

def register_all_tools(mcp):
    # ... existing registrations ...
    register_example_tools(mcp)
```

### 4. Validate

```bash
ruff check .
python main.py  # Verify tool appears in server output
```
