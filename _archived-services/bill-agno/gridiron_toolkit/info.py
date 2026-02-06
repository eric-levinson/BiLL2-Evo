import asyncio
import os
from typing import Any, List, Optional, Dict, Callable
from collections import OrderedDict

from agno.tools import Toolkit
from agno.tools.mcp import MCPTools


# All known remote MCP tool names (expand if you add more)
ALL_TOOL_NAMES = [
    "get_player_info_tool",
    "get_players_by_sleeper_id_tool",
    "get_metrics_metadata",
    "get_advanced_receiving_stats",
    "get_advanced_passing_stats",
    "get_advanced_rushing_stats",
    "get_advanced_defense_stats",
    "get_advanced_receiving_stats_weekly",
    "get_advanced_passing_stats_weekly",
    "get_advanced_rushing_stats_weekly",
    "get_advanced_defense_stats_weekly",
    "get_sleeper_leagues_by_username",
    "get_sleeper_league_rosters",
    "get_sleeper_league_users",
    "get_sleeper_league_matchups",
    "get_sleeper_league_transactions",
    "get_sleeper_trending_players",
    "get_sleeper_user_drafts",
    "get_fantasy_rank_page_types",
    "get_fantasy_ranks",
    "get_dictionary_info",
    "get_stats_metadata",
    "get_offensive_players_game_stats",
    "get_defensive_players_game_stats",
]


class GridironTools(Toolkit):
    """
    Reusable Toolkit that exposes selected remote MCP tools.

    Usage:
      - In an agent: tools=[GridironTools(include_tools=["get_player_info_tool"])]
      - If include_tools is None, the toolkit registers wrappers for ALL_TOOL_NAMES.
      - Callbacks are async and awaited by the Agent.
    """

    def __init__(
        self,
        url: Optional[str] = None,
        transport: str = "streamable-http",
        include_tools: Optional[List[str]] = None,
        exclude_tools: Optional[List[str]] = None,
    ):
        if url is None:
            url = os.getenv("MCP_SERVER_URL", "http://localhost:8000/mcp/")
        # decide which remote tool names to expose
        if include_tools is None:
            tool_names = list(ALL_TOOL_NAMES)
        else:
            tool_names = list(include_tools)

        # dynamically create async wrapper callables named after remote tools
        wrappers: List[Callable[..., Any]] = []

        def make_wrapper(tname: str) -> Callable[..., Any]:
            # Agent passes itself as the first arg for tool calls; preserve and forward it.
            async def _wrapper(agent, *args, **kwargs):
                return await self._call_remote(tname, agent, *args, **kwargs)

            # set the function name so Toolkit registration & introspection work
            try:
                _wrapper.__name__ = tname
            except Exception:
                pass
            return _wrapper

        for tn in tool_names:
            wrappers.append(make_wrapper(tn))

        # register the wrapper callables with Toolkit so Agents can use them
        super().__init__(name="gridiron_tools", tools=wrappers, include_tools=include_tools, exclude_tools=exclude_tools)

        # underlying MCP client; pass include_tools so the MCP client only registers those remote tools
        self._mcp = MCPTools(transport=transport, url=url, include_tools=include_tools, exclude_tools=exclude_tools)
        self._connected = False
        # keep a mapping of wrapper callables so callers can look them up if needed
        self._wrappers_map = {getattr(w, "__name__", f"wrapper_{i}"): w for i, w in enumerate(wrappers)}

    async def connect(self) -> None:
        if self._connected:
            return
        await self._mcp.connect()
        if hasattr(self._mcp, "initialize"):
            try:
                await self._mcp.initialize()
            except Exception:
                pass
        self._connected = True

    async def close(self) -> None:
        # best-effort close — swallow expected errors coming from async generators / event-loop teardown
        try:
            await self._mcp.close()
        except Exception as e:
            # ignore anyio/cancel-scope / event-loop-closed noise that frequently shows during shutdown
            try:
                from exceptiongroup import ExceptionGroup  # type: ignore
                if isinstance(e, ExceptionGroup):
                    # swallow grouped exceptions from anyio taskgroups
                    pass
                else:
                    pass
            except Exception:
                pass
        finally:
            self._connected = False

    async def _call_remote(self, tool_name: str, /, *args, **kwargs) -> Any:
        # accept optional agent as first positional param
        agent = None
        if len(args) and getattr(args[0], "__class__", None):
            # caller likely passed agent as first arg
            agent, args = args[0], args[1:]

        await self.connect()
        funcs = getattr(self._mcp, "functions", {}) or {}
        # normalize funcs whether dict or list
        if isinstance(funcs, dict):
            func_obj = funcs.get(tool_name)
        else:
            func_obj = next((f for f in funcs if getattr(f, "name", None) == tool_name), None)

        # fallback to .tools mapping if present
        if func_obj is None:
            tools_map = getattr(self._mcp, "tools", {}) or {}
            func_obj = tools_map.get(tool_name)

        if func_obj is None:
            raise RuntimeError(f"Remote MCP tool '{tool_name}' is not available")

        # preferred callable is entrypoint (Function.entrypoint) else object itself
        call_target = getattr(func_obj, "entrypoint", None) or func_obj

        # forward agent if entrypoint expects it
        if agent is not None:
            result = call_target(agent, *args, **kwargs)
        else:
            result = call_target(*args, **kwargs)
        if asyncio.iscoroutine(result):
            return await result
        return result

    # helper: produce a name->Function mapping for callers who want to inspect remote functions
    def available_functions(self) -> Dict[str, Any]:
        funcs = getattr(self._mcp, "functions", {}) or {}
        if isinstance(funcs, dict):
            return dict(funcs)
        return OrderedDict((getattr(f, "name", getattr(f, "__name__", str(i))), f) for i, f in enumerate(funcs))

    # helper: get the local async wrapper callable for a tool name
    def wrapper_for(self, tool_name: str) -> Optional[Callable[..., Any]]:
        return self._wrappers_map.get(tool_name)