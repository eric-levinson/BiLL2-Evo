#!/usr/bin/env python3
"""
Test script to verify get_advanced_defense_stats migration to build_player_stats_query.
Compares output structure and validates the migration.
"""
import os
import sys
from dotenv import load_dotenv

# Add fantasy-tools-mcp to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'fantasy-tools-mcp'))

load_dotenv()

from supabase import create_client, Client
from tools.metrics.info import get_advanced_defense_stats

def test_defense_stats_migration():
    """Test that get_advanced_defense_stats returns expected data structure."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")

    if not supabase_url or not supabase_key:
        print("❌ Missing SUPABASE_URL or SUPABASE_ANON_KEY environment variables")
        print("   Please ensure .env file exists with these values")
        return False

    supabase: Client = create_client(supabase_url, supabase_key)

    print("Testing get_advanced_defense_stats migration...")
    print("=" * 60)

    # Test 1: Basic query with limit
    print("\n1. Basic query (limit=5):")
    try:
        result = get_advanced_defense_stats(supabase, limit=5)
        assert "advDefenseStats" in result, "Missing 'advDefenseStats' key"
        assert isinstance(result["advDefenseStats"], list), "advDefenseStats should be a list"
        assert len(result["advDefenseStats"]) <= 5, "Should respect limit"
        print(f"   ✓ Returns {len(result['advDefenseStats'])} records")
        if result["advDefenseStats"]:
            first = result["advDefenseStats"][0]
            print(f"   ✓ Sample record keys: {list(first.keys())}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False

    # Test 2: Query with player name filter
    print("\n2. Query with player name filter (player_names=['Parsons']):")
    try:
        result = get_advanced_defense_stats(supabase, player_names=["Parsons"], limit=5)
        assert "advDefenseStats" in result
        print(f"   ✓ Returns {len(result['advDefenseStats'])} records")
        if result["advDefenseStats"]:
            names = [r.get("player_name", "") for r in result["advDefenseStats"]]
            print(f"   ✓ Player names: {names}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False

    # Test 3: Query with season filter
    print("\n3. Query with season filter (season_list=[2024]):")
    try:
        result = get_advanced_defense_stats(supabase, season_list=[2024], limit=5)
        assert "advDefenseStats" in result
        print(f"   ✓ Returns {len(result['advDefenseStats'])} records")
        if result["advDefenseStats"]:
            seasons = set(r.get("season") for r in result["advDefenseStats"])
            print(f"   ✓ Seasons in results: {seasons}")
            assert seasons == {2024}, "Should only return 2024 season"
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False

    # Test 4: Query with position filter
    print("\n4. Query with position filter (positions=['LB']):")
    try:
        result = get_advanced_defense_stats(supabase, positions=["LB"], limit=5)
        assert "advDefenseStats" in result
        print(f"   ✓ Returns {len(result['advDefenseStats'])} records")
        if result["advDefenseStats"]:
            positions = set(r.get("position") for r in result["advDefenseStats"])
            print(f"   ✓ Positions in results: {positions}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False

    # Test 5: Query with metrics and ordering
    print("\n5. Query with metrics=['tackles', 'sacks'] and order_by_metric='sacks':")
    try:
        result = get_advanced_defense_stats(
            supabase,
            season_list=[2024],
            metrics=["tackles", "sacks"],
            order_by_metric="sacks",
            limit=5
        )
        assert "advDefenseStats" in result
        print(f"   ✓ Returns {len(result['advDefenseStats'])} records")
        if result["advDefenseStats"]:
            first = result["advDefenseStats"][0]
            print(f"   ✓ Record keys include: {list(first.keys())}")
            assert "tackles" in first or "sacks" in first, "Should include requested metrics"
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False

    print("\n" + "=" * 60)
    print("✅ All tests passed! Migration successful.")
    return True

if __name__ == "__main__":
    success = test_defense_stats_migration()
    sys.exit(0 if success else 1)
