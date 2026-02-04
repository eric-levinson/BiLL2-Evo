import asyncio
import os
import sys
import types
import traceback

# Ensure repo root is on sys.path so `import team_playground` works when this
# script is run directly (e.g., `python tests/smoke_crawl.py`). Insert the
# parent directory of the tests folder at the front of sys.path.
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Provide a minimal stub for the `googlesearch` package which some agno tool
# modules import at import-time. This avoids requiring `googlesearch-python`
# to be installed for local smoke tests.
if 'googlesearch' not in sys.modules:
    mod = types.ModuleType('googlesearch')
    def _search(query, num_results=10, stop=10):
        # return an empty iterator/list for test purposes
        return []
    mod.search = _search
    sys.modules['googlesearch'] = mod

# Ensure repo root is importable
# Run this script with: PYTHONPATH=. python tests/smoke_crawl.py

# No discord stub needed; `team_playground` no longer imports DiscordClient at module scope.

from team_playground import build_team

async def main():
    try:
        team = build_team()
    except Exception:
        print("Failed to build team:")
        traceback.print_exc()
        return

    web_agent = None
    for m in getattr(team, "members", []) or []:
        if getattr(m, "name", None) == "Web Search Agent":
            web_agent = m
            break

    if web_agent is None:
        print("Web agent not found in team members. Members:")
        print([getattr(m, "name", repr(m)) for m in getattr(team, "members", []) or []])
        return

    print("Found web agent:", web_agent.name)
    tools = getattr(web_agent, "tools", []) or []
    print("Web agent tools:", [type(t).__name__ for t in tools])

    # find a crawl-capable tool
    crawl_tool = None
    for t in tools:
        # prefer exact name match or presence of crawl/invoke
        if type(t).__name__.lower().startswith("crawl") or hasattr(t, "crawl") or hasattr(t, "invoke"):
            crawl_tool = t
            break

    if crawl_tool is None:
        print("No crawl-capable tool found on web agent.")
        return

    print("Using tool:", type(crawl_tool).__name__, "repr:", repr(crawl_tool))

    # attempt a single crawl
    url = "https://example.com"
    fn = getattr(crawl_tool, "crawl", None) or getattr(crawl_tool, "invoke", None) or getattr(crawl_tool, "__call__", None)
    if fn is None:
        print("Tool has no callable crawl/invoke")
        return

    try:
        res = fn(url)
        if asyncio.iscoroutine(res):
            out = await asyncio.wait_for(res, timeout=20)
        else:
            loop = asyncio.get_running_loop()
            out = await loop.run_in_executor(None, res)
        print("Crawl returned type:", type(out))
        text = str(out)
        print("Preview (first 1000 chars):\n", text[:1000])
    except Exception:
        print("Crawl raised an exception:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
