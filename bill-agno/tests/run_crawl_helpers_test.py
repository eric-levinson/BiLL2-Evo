import asyncio
from helpers import crawl_helpers as ch


def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


def test_summarize_text_deterministic():
    short = "This is short."
    assert ch.summarize_text_deterministic(short, max_chars=50) == short

    long = ("Sentence one. " * 50).strip()
    out = ch.summarize_text_deterministic(long, max_chars=100)
    print("deterministic summary len:", len(out))
    print(out[:200])


def test_summary_cache():
    c = ch.SummaryCache(max_size=2)
    c.put("a", "A")
    c.put("b", "B")
    print("get a:", c.get("a"))
    c.put("c", "C")
    print("get b (may be evicted):", c.get("b"))


def test_extract_text():
    resp = {"content": "This is the content.", "meta": {"author": "x"}, "rows": ["row1", {"t": "nested"}]}
    flat = ch.extract_text_from_mcp_response(resp)
    print("flattened:", flat)


def test_summarize_mcp_none():
    resp = {"content": "This is some long content. " * 20}
    out = ch.summarize_mcp_response_sync(None, resp, max_length=200)
    print("summarize_mcp_response_sync (None model) len:", len(out))
    print(out[:200])


def test_summarize_with_dummy_model_fallback():
    class Dummy:
        pass

    long = ("Fact about something. " * 40).strip()
    out = run_async(ch.summarize_with_model_async(Dummy(), long, max_length=150))
    print("summarize_with_model_async fallback len:", len(out))
    print(out[:300])


if __name__ == "__main__":
    print("Running crawl_helpers tests...")
    test_summarize_text_deterministic()
    test_summary_cache()
    test_extract_text()
    test_summarize_mcp_none()
    test_summarize_with_dummy_model_fallback()
    print("Done.")
