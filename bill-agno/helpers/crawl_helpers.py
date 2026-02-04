"""Helpers for preprocessing and summarizing large crawl / MCP responses.

Goals:
- Provide a cheap-model summarizer async helper that will call a provided model
  (prefer async model APIs when available).
- Provide a deterministic fallback summarizer to quickly truncate/keep sentences
  without invoking a model (safe, fast).
- Provide a small in-memory LRU cache for summaries to avoid recomputing.

Recommended flow (from Agno docs):
- Use a small/cheap model or deterministic summarizer to compress large texts
  into short facts (store in agent memory). Use the main/expensive model only
  for final reasoning/generation. MemoryManager/SessionSummarizer patterns in
  Agno show similar architectures.
"""
from __future__ import annotations

import asyncio
import hashlib
from collections import OrderedDict
from typing import Any, Dict, Iterable, Optional
import functools
from agno.tools.crawl4ai import Crawl4aiTools
from agno.memory.v2.memory import Memory
from agno.memory.v2.schema import UserMemory


def summarize_text_deterministic(text: str, max_chars: int = 2000) -> str:
    """Deterministic, zero-cost summarizer.

    - Keeps the first ~max_chars characters, preferring to cut on sentence
      boundaries. Use as a safe fallback or quick prototype before adding a
      cheap-model summarizer.
    """
    if not text:
        return ""
    text = text.strip()
    if len(text) <= max_chars:
        return text

    # Prefer whole sentences up to the limit
    parts = text.split('. ')
    out = []
    length = 0
    for p in parts:
        piece = (p + '.').strip()
        if length + len(piece) + 1 > max_chars:
            break
        out.append(piece)
        length += len(piece) + 1

    if out:
        return ' '.join(out)

    # Fallback hard truncate
    return text[: max_chars].rsplit(' ', 1)[0]


class SummaryCache:
    """A tiny thread-safe LRU cache for summarized text.

    Keys are sha256(text) hex digests. Value is the summary string.
    """

    def __init__(self, max_size: int = 1024):
        self.max_size = max_size
        self._cache: "OrderedDict[str, str]" = OrderedDict()

    def _key(self, text: str) -> str:
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def get(self, text: str) -> Optional[str]:
        k = self._key(text)
        try:
            v = self._cache.pop(k)
            # mark as recently used
            self._cache[k] = v
            return v
        except KeyError:
            return None

    def put(self, text: str, summary: str) -> None:
        k = self._key(text)
        if k in self._cache:
            # refresh position
            self._cache.pop(k)
        self._cache[k] = summary
        # evict oldest
        while len(self._cache) > self.max_size:
            self._cache.popitem(last=False)


_GLOBAL_SUMMARY_CACHE = SummaryCache(max_size=2048)


async def summarize_with_model_async(
    model: Any,
    text: str,
    system_instructions: Optional[str] = None,
    max_length: int = 800,
    use_cache: bool = True,
) -> str:
    """Summarize `text` using a provided model instance.

    - model: a model object (preferably Agno/OpenAIChat compatible).
      We try several common async call signatures:
        - model.ainvoke(...) or model.ainvoke_stream(...)
        - model.invoke(...) or model.invoke_stream(...)
      If none exist, falls back to deterministic summarizer.
    - Returns the summary string.

    Notes: This helper is intentionally conservative about calling model APIs so
    it works with a range of model wrappers used in Agno examples.
    """
    if not text:
        return ""

    if use_cache:
        cached = _GLOBAL_SUMMARY_CACHE.get(text)
        if cached is not None:
            return cached

    # Build a short prompt for summarization if the model will be used.
    prompt = (
        (system_instructions or "")
        + "\n\nSummarize the following content into a concise bulleted list of key facts (max "
        + str(max_length)
        + " characters):\n\n"
        + text
    )

    # Try common async model call shapes
    summary = None
    # prefer explicit async 'ainvoke' style
    if hasattr(model, 'ainvoke'):
        try:
            # agno model wrappers often accept a message string
            res = await model.ainvoke(prompt)
            summary = getattr(res, 'text', None) or str(res)
        except Exception:
            summary = None

    if summary is None and hasattr(model, 'ainvoke_stream'):
        try:
            # some libs offer streaming; collect the output
            chunks = []
            async for part in model.ainvoke_stream(prompt):
                chunks.append(getattr(part, 'text', str(part)))
            summary = ''.join(chunks)
        except Exception:
            summary = None

    # fallback to sync-like invoke if available
    if summary is None and hasattr(model, 'invoke'):
        try:
            res = model.invoke(prompt)
            summary = getattr(res, 'text', None) or str(res)
        except Exception:
            summary = None

    if summary is None:
        # Last-resort deterministic summarizer
        summary = summarize_text_deterministic(text, max_chars=max_length)

    # Post-process: trim
    summary = summary.strip()

    if use_cache:
        _GLOBAL_SUMMARY_CACHE.put(text, summary)

    return summary


def extract_text_from_mcp_response(resp: Any) -> str:
    """Flatten an MCP/tool response into a textual blob suitable for summarization.

    Tries a few common field names and falls back to str(resp).
    """
    if resp is None:
        return ""

    # If it's a dict-like, find textual fields
    if isinstance(resp, dict):
        parts = []
        # common fields
        for k in ('content', 'text', 'body', 'result', 'summary'):
            if k in resp and isinstance(resp[k], str):
                parts.append(resp[k])

        # also flatten nested dicts/lists
        for v in resp.values():
            if isinstance(v, str):
                parts.append(v)
            elif isinstance(v, (list, tuple)):
                for item in v:
                    if isinstance(item, str):
                        parts.append(item)
                    else:
                        parts.append(str(item))
            else:
                parts.append(str(v))

        return '\n'.join(p for p in parts if p)

    if isinstance(resp, (list, tuple)):
        out = []
        for item in resp:
            if isinstance(item, str):
                out.append(item)
            elif isinstance(item, dict):
                out.append(extract_text_from_mcp_response(item))
            else:
                out.append(str(item))
        return '\n'.join(out)

    return str(resp)


async def summarize_mcp_response(model: Any, resp: Any, max_length: int = 800) -> str:
    """Convenience: extract text from MCP response then summarize it (async).

    - model: optional small/cheap model to perform compression. If None, falls back
      to deterministic summarizer.
    """
    text = extract_text_from_mcp_response(resp)
    if not text:
        return ""
    if model is None:
        return summarize_text_deterministic(text, max_chars=max_length)
    return await summarize_with_model_async(model, text, max_length=max_length)


def summarize_mcp_response_sync(model: Any, resp: Any, max_length: int = 800) -> str:
    """Sync wrapper around `summarize_mcp_response` for convenience.

    If an async model is used, this will run the coroutine.
    """
    coro = summarize_mcp_response(model, resp, max_length=max_length)
    try:
        return asyncio.get_event_loop().run_until_complete(coro)
    except RuntimeError:
        # No running loop; create a new one
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


class SummarizingCrawl4aiTools(Crawl4aiTools):
    """Wrapper around a Crawl4aiTools instance that summarizes results,
    stores a summary into the provided Memory, and returns the compressed
    summary string to callers.

    This keeps summarization logic colocated with other crawl helpers and
    avoids duplicating the implementation in multiple places.
    """

    def __init__(self, inner: Crawl4aiTools, memory: Optional[Memory], *, model: Any = None, max_length: int = 800, user_id: str = "web_agent_crawls"):
        self.inner = inner
        self.memory = memory
        self.model = model
        self.max_length = max_length
        self.user_id = user_id

    def __getattr__(self, name):
        return getattr(self.inner, name)

    async def crawl(self, *args, user_id: Optional[str] = None, **kwargs) -> str:
        """Async crawl wrapper.

        - Calls the underlying tool's crawl/invoke (supports sync, async callables).
        - Extracts/derives a per-call user_id (from kwarg `user_id` or fallback to "anonymous").
        - Summarizes the response using the async summarizer and stores it in
          the Memory backend in a thread executor to avoid blocking the loop.
        - Returns the compressed summary string.
        """
        fn = getattr(self.inner, "crawl", None) or getattr(self.inner, "invoke", None) or getattr(self.inner, "__call__", None)
        if fn is None:
            raise RuntimeError("Underlying Crawl4aiTools has no callable crawl/invoke")

        # Execute the underlying tool call. If it's async, await it. If it's
        # sync, run it in the default thread executor so we don't block the loop.
        try:
            res = fn(*args, **kwargs)
        except TypeError:
            # Fallback to calling without forwarded args
            res = fn()

        if asyncio.iscoroutine(res):
            res = await res
        else:
            # run sync call in executor
            loop = asyncio.get_running_loop()
            res = await loop.run_in_executor(None, functools.partial(lambda x: x, res))

        # Summarize using the async summarizer (uses deterministic fallback if model is None)
        try:
            summary = await summarize_mcp_response(self.model, res, max_length=self.max_length)
        except Exception:
            # last-resort deterministic path
            summary = summarize_text_deterministic(extract_text_from_mcp_response(res), max_chars=self.max_length)

        # Determine per-user id and persist the summary (best-effort)
        per_user_id = None
        if user_id:
            per_user_id = str(user_id)
        elif isinstance(kwargs.get("user_id"), str):
            per_user_id = kwargs.get("user_id")
        else:
            per_user_id = "anonymous"

        if self.memory is not None and summary:
            try:
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(
                    None,
                    functools.partial(
                        self.memory.add_user_memory,
                        memory=UserMemory(memory=summary, topics=["crawl_summary"]),
                        user_id=f"user:{per_user_id}",
                    ),
                )
            except Exception:
                # swallow memory write errors
                pass

        return summary
