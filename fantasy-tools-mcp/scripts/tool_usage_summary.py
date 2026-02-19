#!/usr/bin/env python3
"""
Standalone script to print MCP tool usage analytics summary.

Usage:
    python scripts/tool_usage_summary.py [--log-path PATH] [--since YYYY-MM-DD] [--until YYYY-MM-DD]

Reads logs/tool_usage.jsonl and prints:
  - Top 10 most-called tools
  - Top 10 slowest tools (p95 duration)
  - Failure rate per tool
  - Total calls in time period
"""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

# Allow running from project root or scripts/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from helpers.tool_analytics import print_summary


def main():
    parser = argparse.ArgumentParser(description="MCP Tool Usage Analytics Summary")
    parser.add_argument(
        "--log-path",
        type=str,
        default=None,
        help="Path to tool_usage.jsonl (default: logs/tool_usage.jsonl)",
    )
    parser.add_argument(
        "--since",
        type=str,
        default=None,
        help="Start date filter (ISO 8601, e.g. 2026-02-01)",
    )
    parser.add_argument(
        "--until",
        type=str,
        default=None,
        help="End date filter (ISO 8601, e.g. 2026-02-28)",
    )
    args = parser.parse_args()

    since = None
    until = None
    if args.since:
        since = datetime.fromisoformat(args.since).replace(tzinfo=timezone.utc)
    if args.until:
        until = datetime.fromisoformat(args.until).replace(tzinfo=timezone.utc)

    print_summary(log_path=args.log_path, since=since, until=until)


if __name__ == "__main__":
    main()
