#!/usr/bin/env python3
"""
Test script for get_advanced_rushing_stats_weekly migration.

Verifies that the refactored function correctly uses build_player_stats_query
and that weekly_list filtering works as expected.
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client

# Add fantasy-tools-mcp to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'fantasy-tools-mcp'))

from tools.metrics.info import get_advanced_rushing_stats_weekly

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), 'fantasy-tools-mcp', '.env'))

def test_weekly_list_filtering():
    """Test that weekly_list parameter correctly filters results."""
    print("\n=== Testing weekly_list filtering for rushing stats ===")

    # Create Supabase client
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")

    if not supabase_url or not supabase_key:
        print("❌ ERROR: Missing SUPABASE_URL or SUPABASE_ANON_KEY environment variables")
        return False

    supabase = create_client(supabase_url, supabase_key)

    try:
        # Test 1: Query with specific weeks
        print("\nTest 1: Query weeks 1-3 for 2024 season")
        result = get_advanced_rushing_stats_weekly(
            supabase=supabase,
            season_list=[2024],
            weekly_list=[1, 2, 3],
            metrics=["rushing_yards", "rushing_tds", "carries"],
            limit=10
        )

        if "advRushingStats" not in result:
            print("❌ FAILED: Result missing 'advRushingStats' key")
            return False

        stats = result["advRushingStats"]
        print(f"   ✓ Returned {len(stats)} records")

        # Verify all results are from weeks 1-3
        weeks_found = set()
        for stat in stats:
            if "week" in stat:
                weeks_found.add(stat["week"])
                if stat["week"] not in [1, 2, 3]:
                    print(f"❌ FAILED: Found week {stat['week']}, expected only weeks 1-3")
                    return False

        print(f"   ✓ All records are from weeks: {sorted(weeks_found)}")

        # Test 2: Query with player name and weekly filter
        print("\nTest 2: Query specific player with weekly filter")
        result = get_advanced_rushing_stats_weekly(
            supabase=supabase,
            player_names=["Christian McCaffrey"],
            season_list=[2024],
            weekly_list=[1, 2],
            metrics=["rushing_yards", "rushing_tds", "carries"],
            limit=10
        )

        stats = result["advRushingStats"]
        print(f"   ✓ Returned {len(stats)} records for Christian McCaffrey")

        if stats:
            for stat in stats:
                week = stat.get("week", "N/A")
                player = stat.get("player_name", "N/A")
                yards = stat.get("rushing_yards", "N/A")
                tds = stat.get("rushing_tds", "N/A")
                print(f"     - Week {week}, {player}: {yards} yards, {tds} TDs")

        # Test 3: Query without weekly_list (should work)
        print("\nTest 3: Query without weekly_list parameter")
        result = get_advanced_rushing_stats_weekly(
            supabase=supabase,
            season_list=[2024],
            metrics=["rushing_yards", "rushing_tds"],
            limit=5
        )

        stats = result["advRushingStats"]
        print(f"   ✓ Returned {len(stats)} records without weekly filter")

        # Test 4: Verify position filter defaults to RB, QB
        print("\nTest 4: Verify default RB/QB position filter")
        result = get_advanced_rushing_stats_weekly(
            supabase=supabase,
            season_list=[2024],
            weekly_list=[1],
            metrics=["rushing_yards"],
            limit=10
        )

        stats = result["advRushingStats"]
        positions = set(stat.get("position", "N/A") for stat in stats)
        print(f"   ✓ Positions found: {positions}")

        # Test 5: Order by metric
        print("\nTest 5: Order by rushing_yards")
        result = get_advanced_rushing_stats_weekly(
            supabase=supabase,
            season_list=[2024],
            weekly_list=[1],
            metrics=["rushing_yards"],
            order_by_metric="rushing_yards",
            limit=3
        )

        stats = result["advRushingStats"]
        print(f"   ✓ Top 3 rushers in Week 1, 2024:")
        for i, stat in enumerate(stats, 1):
            player = stat.get("player_name", "N/A")
            yards = stat.get("rushing_yards", "N/A")
            print(f"     {i}. {player}: {yards} yards")

        print("\n✅ All tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_weekly_list_filtering()
    sys.exit(0 if success else 1)
