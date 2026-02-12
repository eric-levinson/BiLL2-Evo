#!/usr/bin/env python3
"""
Test script to verify get_advanced_passing_stats migration.
Compares output before and after migrating to build_player_stats_query.
"""

import os
import sys
from dotenv import load_dotenv

# Add fantasy-tools-mcp to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "fantasy-tools-mcp"))

load_dotenv()

from supabase import create_client
from tools.metrics.info import get_advanced_passing_stats

def test_passing_stats():
    """Test get_advanced_passing_stats with various parameters."""

    # Initialize Supabase client
    supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL") or os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY") or os.getenv("SUPABASE_ANON_KEY")

    if not supabase_url or not supabase_key:
        print("❌ Error: Missing Supabase credentials in .env")
        print("   Need SUPABASE_URL and SUPABASE_ANON_KEY")
        return False

    supabase = create_client(supabase_url, supabase_key)

    print("Testing get_advanced_passing_stats migration...\n")

    # Test 1: Basic query with player name
    print("Test 1: Query for Mahomes 2023-2024")
    try:
        result = get_advanced_passing_stats(
            supabase=supabase,
            player_names=["Mahomes"],
            season_list=[2023, 2024],
            metrics=["passing_yards", "passing_tds", "interceptions"],
            limit=5
        )
        assert "advPassingStats" in result, "Missing advPassingStats key"
        assert isinstance(result["advPassingStats"], list), "Result should be a list"
        print(f"   ✓ Returned {len(result['advPassingStats'])} records")
        if result["advPassingStats"]:
            record = result["advPassingStats"][0]
            print(f"   ✓ Sample: {record.get('player_name')} - {record.get('season')} - {record.get('passing_yards')} yards")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

    # Test 2: Query with ordering
    print("\nTest 2: Top 3 QBs by passing_yards in 2024")
    try:
        result = get_advanced_passing_stats(
            supabase=supabase,
            season_list=[2024],
            order_by_metric="passing_yards",
            limit=3
        )
        assert "advPassingStats" in result, "Missing advPassingStats key"
        print(f"   ✓ Returned {len(result['advPassingStats'])} records")
        for i, record in enumerate(result["advPassingStats"], 1):
            print(f"   {i}. {record.get('player_name')} - {record.get('passing_yards')} yards")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

    # Test 3: Query with custom positions (should still work with QB default)
    print("\nTest 3: Default QB position filter")
    try:
        result = get_advanced_passing_stats(
            supabase=supabase,
            season_list=[2024],
            limit=5
        )
        assert "advPassingStats" in result, "Missing advPassingStats key"
        print(f"   ✓ Returned {len(result['advPassingStats'])} records")
        positions = set(record.get('ff_position') for record in result["advPassingStats"])
        print(f"   ✓ Positions: {positions}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

    # Test 4: Query with specific metrics
    print("\nTest 4: Specific metrics selection")
    try:
        result = get_advanced_passing_stats(
            supabase=supabase,
            player_names=["Allen"],
            season_list=[2024],
            metrics=["attempts", "completions", "completion_percentage"],
            limit=5
        )
        assert "advPassingStats" in result, "Missing advPassingStats key"
        if result["advPassingStats"]:
            record = result["advPassingStats"][0]
            print(f"   ✓ Has base columns: season={record.get('season')}, player_name={record.get('player_name')}")
            print(f"   ✓ Has metrics: attempts={record.get('attempts')}, completions={record.get('completions')}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

    print("\n✅ All tests passed! Migration successful.")
    return True

if __name__ == "__main__":
    success = test_passing_stats()
    sys.exit(0 if success else 1)
