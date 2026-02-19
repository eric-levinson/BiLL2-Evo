"""
MCP Tool Usage Analytics — middleware, log writer, and summary functions.

Intercepts every tool call via FastMCP middleware to record structured
metrics (tool name, duration, success/failure, approximate token counts).
Logs are written to stdout (for container log aggregation) and appended
to a rotating JSONL file for local analysis.
"""

from __future__ import annotations

import json
import logging
import time
from collections import defaultdict
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path

from fastmcp.server.middleware import Middleware, MiddlewareContext

# ---------------------------------------------------------------------------
# Log writer (async-safe via logging module — non-blocking in default config)
# ---------------------------------------------------------------------------

_LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
_LOG_FILE = _LOG_DIR / "tool_usage.jsonl"
_MAX_BYTES = 50 * 1024 * 1024  # 50 MB
_BACKUP_COUNT = 3

# Dedicated logger so analytics records don't pollute the root logger
_analytics_logger = logging.getLogger("tool_analytics")
_analytics_logger.setLevel(logging.INFO)
_analytics_logger.propagate = False


def _ensure_handlers() -> None:
    """Lazily attach handlers on first use (avoids import-time side effects)."""
    if _analytics_logger.handlers:
        return

    _LOG_DIR.mkdir(parents=True, exist_ok=True)

    # Rotating file handler — 50 MB cap, 3 backups
    file_handler = RotatingFileHandler(
        str(_LOG_FILE),
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(logging.Formatter("%(message)s"))
    _analytics_logger.addHandler(file_handler)

    # Stdout handler for container/Vercel log aggregation
    stdout_handler = logging.StreamHandler()
    stdout_handler.setFormatter(logging.Formatter("%(message)s"))
    _analytics_logger.addHandler(stdout_handler)


def _approx_tokens(text: str | None) -> int:
    """Approximate token count as character count / 4."""
    if not text:
        return 0
    return len(text) // 4


def log_tool_call(
    tool_name: str,
    duration_ms: float,
    *,
    success: bool,
    error_message: str | None = None,
    input_text: str | None = None,
    output_text: str | None = None,
) -> None:
    """Write a structured JSON record for a single tool invocation."""
    _ensure_handlers()

    record = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tool": tool_name,
        "duration_ms": round(duration_ms, 1),
        "success": success,
        "input_approx_tokens": _approx_tokens(input_text),
        "output_approx_tokens": _approx_tokens(output_text),
    }
    if error_message:
        record["error_message"] = error_message[:500]  # truncate long errors

    _analytics_logger.info(json.dumps(record, separators=(",", ":")))


# ---------------------------------------------------------------------------
# FastMCP Middleware
# ---------------------------------------------------------------------------


class ToolAnalyticsMiddleware(Middleware):
    """FastMCP middleware that instruments every tool call with timing and logging."""

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        tool_name = context.message.name
        input_text = json.dumps(context.message.arguments) if context.message.arguments else None

        start = time.monotonic()
        try:
            result = await call_next(context)
            duration_ms = (time.monotonic() - start) * 1000

            # Serialize result for token estimation
            output_text = str(result) if result is not None else None

            log_tool_call(
                tool_name,
                duration_ms,
                success=True,
                input_text=input_text,
                output_text=output_text,
            )
            return result
        except Exception as e:
            duration_ms = (time.monotonic() - start) * 1000
            log_tool_call(
                tool_name,
                duration_ms,
                success=False,
                error_message=str(e),
                input_text=input_text,
            )
            raise


# ---------------------------------------------------------------------------
# Summary / analysis functions
# ---------------------------------------------------------------------------


def read_log_records(
    log_path: str | Path | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
) -> list[dict]:
    """Read and optionally filter JSONL log records."""
    path = Path(log_path) if log_path else _LOG_FILE
    if not path.exists():
        return []

    records: list[dict] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue

            if since or until:
                try:
                    ts = datetime.fromisoformat(rec["ts"].replace("Z", "+00:00"))
                except (KeyError, ValueError):
                    continue
                if since and ts < since:
                    continue
                if until and ts > until:
                    continue

            records.append(rec)
    return records


def _percentile(values: list[float], pct: float) -> float:
    """Compute the given percentile from a sorted list of values."""
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    k = (len(sorted_vals) - 1) * (pct / 100)
    f = int(k)
    c = f + 1
    if c >= len(sorted_vals):
        return sorted_vals[f]
    return sorted_vals[f] + (k - f) * (sorted_vals[c] - sorted_vals[f])


def generate_summary(
    log_path: str | Path | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
) -> dict:
    """Produce an analytics summary from tool usage logs.

    Returns a dict with:
      - total_calls: int
      - time_range: {first, last} ISO timestamps
      - top_called: list of {tool, count} (top 10)
      - slowest_p95: list of {tool, p95_ms} (top 10)
      - failure_rates: list of {tool, total, failures, rate}
      - overall_failure_rate: float
    """
    records = read_log_records(log_path, since=since, until=until)
    if not records:
        return {"total_calls": 0, "message": "No records found"}

    call_counts: dict[str, int] = defaultdict(int)
    durations: dict[str, list[float]] = defaultdict(list)
    failures: dict[str, int] = defaultdict(int)
    totals: dict[str, int] = defaultdict(int)
    timestamps: list[str] = []

    for rec in records:
        tool = rec.get("tool", "unknown")
        call_counts[tool] += 1
        totals[tool] += 1
        durations[tool].append(rec.get("duration_ms", 0))
        if not rec.get("success", True):
            failures[tool] += 1
        if "ts" in rec:
            timestamps.append(rec["ts"])

    # Top 10 most-called tools
    top_called = sorted(call_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    # Top 10 slowest tools by p95 duration
    p95_by_tool = {tool: _percentile(durs, 95) for tool, durs in durations.items()}
    slowest_p95 = sorted(p95_by_tool.items(), key=lambda x: x[1], reverse=True)[:10]

    # Failure rate per tool
    failure_rates = []
    for tool in sorted(totals.keys()):
        total = totals[tool]
        fails = failures.get(tool, 0)
        rate = (fails / total * 100) if total > 0 else 0
        failure_rates.append({"tool": tool, "total": total, "failures": fails, "rate": round(rate, 1)})

    total_calls = sum(call_counts.values())
    total_failures = sum(failures.values())

    return {
        "total_calls": total_calls,
        "time_range": {
            "first": min(timestamps) if timestamps else None,
            "last": max(timestamps) if timestamps else None,
        },
        "top_called": [{"tool": t, "count": c} for t, c in top_called],
        "slowest_p95": [{"tool": t, "p95_ms": round(p, 1)} for t, p in slowest_p95],
        "failure_rates": failure_rates,
        "overall_failure_rate": round((total_failures / total_calls * 100) if total_calls > 0 else 0, 1),
    }


def print_summary(
    log_path: str | Path | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
) -> None:
    """Print a human-readable analytics summary to stdout."""
    summary = generate_summary(log_path, since=since, until=until)

    if summary["total_calls"] == 0:
        print("No tool usage records found.")
        return

    time_range = summary["time_range"]
    print(f"\n{'=' * 60}")
    print("  MCP Tool Usage Analytics Summary")
    print(f"{'=' * 60}")
    print(f"  Total calls: {summary['total_calls']}")
    print(f"  Period: {time_range['first']} to {time_range['last']}")
    print(f"  Overall failure rate: {summary['overall_failure_rate']}%")

    print(f"\n{'-' * 60}")
    print("  Top 10 Most-Called Tools")
    print(f"{'-' * 60}")
    for i, item in enumerate(summary["top_called"], 1):
        print(f"  {i:2}. {item['tool']:<45} {item['count']:>5} calls")

    print(f"\n{'-' * 60}")
    print("  Top 10 Slowest Tools (p95 duration)")
    print(f"{'-' * 60}")
    for i, item in enumerate(summary["slowest_p95"], 1):
        print(f"  {i:2}. {item['tool']:<45} {item['p95_ms']:>8.1f} ms")

    print(f"\n{'-' * 60}")
    print("  Failure Rate by Tool")
    print(f"{'-' * 60}")
    for item in summary["failure_rates"]:
        marker = " (!)" if item["rate"] > 0 else ""
        print(f"  {item['tool']:<45} {item['failures']:>3}/{item['total']:<5} ({item['rate']}%){marker}")

    print(f"\n{'=' * 60}\n")
