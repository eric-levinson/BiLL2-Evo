"""
Test script to verify get_advanced_receiving_stats migration to build_player_stats_query.
This test verifies the function can be called and returns the expected data structure.
"""

import os
from dotenv import load_dotenv
from supabase import create_client
from tools.metrics.info import get_advanced_receiving_stats

load_dotenv()

def test_receiving_stats_basic():
    """Test basic call with default parameters"""
    print("\n=== Test 1: Basic call with limit ===")

    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_ANON_KEY")
    )

    try:
        result = get_advanced_receiving_stats(supabase=supabase, limit=5)

        # Check structure
        assert "advReceivingStats" in result, "Missing 'advReceivingStats' key"
        assert isinstance(result["advReceivingStats"], list), "Data should be a list"
        assert len(result["advReceivingStats"]) <= 5, "Should respect limit"

        # Check base columns present
        if result["advReceivingStats"]:
            first_row = result["advReceivingStats"][0]
            assert "season" in first_row, "Missing 'season' column"
            assert "player_name" in first_row, "Missing 'player_name' column"
            assert "ff_team" in first_row, "Missing 'ff_team' column"
            assert "ff_position" in first_row, "Missing 'ff_position' column"

        print(f"✓ PASS: Returned {len(result['advReceivingStats'])} rows")
        print(f"  Sample: {result['advReceivingStats'][0]['player_name'] if result['advReceivingStats'] else 'No data'}")

    except Exception as e:
        print(f"✗ FAIL: {str(e)}")
        raise

def test_receiving_stats_with_filters():
    """Test with player name and season filters"""
    print("\n=== Test 2: With player name and season filters ===")

    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_ANON_KEY")
    )

    try:
        result = get_advanced_receiving_stats(
            supabase=supabase,
            player_names=["Jefferson"],
            season_list=[2023, 2024],
            limit=10
        )

        assert "advReceivingStats" in result, "Missing 'advReceivingStats' key"
        assert isinstance(result["advReceivingStats"], list), "Data should be a list"

        # Check filtering worked
        if result["advReceivingStats"]:
            for row in result["advReceivingStats"]:
                assert row["season"] in [2023, 2024], f"Season filter failed: {row['season']}"

        print(f"✓ PASS: Returned {len(result['advReceivingStats'])} rows")
        if result["advReceivingStats"]:
            print(f"  Sample: {result['advReceivingStats'][0]['player_name']} - {result['advReceivingStats'][0]['season']}")

    except Exception as e:
        print(f"✗ FAIL: {str(e)}")
        raise

def test_receiving_stats_with_metrics():
    """Test with specific metrics requested"""
    print("\n=== Test 3: With specific metrics ===")

    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_ANON_KEY")
    )

    try:
        metrics = ["targets", "receptions", "receiving_yards"]
        result = get_advanced_receiving_stats(
            supabase=supabase,
            metrics=metrics,
            limit=5
        )

        assert "advReceivingStats" in result, "Missing 'advReceivingStats' key"

        # Check metrics present
        if result["advReceivingStats"]:
            first_row = result["advReceivingStats"][0]
            for metric in metrics:
                assert metric in first_row, f"Missing requested metric: {metric}"

        print(f"✓ PASS: Returned {len(result['advReceivingStats'])} rows with metrics")
        if result["advReceivingStats"]:
            print(f"  Sample metrics: targets={result['advReceivingStats'][0].get('targets')}, receptions={result['advReceivingStats'][0].get('receptions')}")

    except Exception as e:
        print(f"✗ FAIL: {str(e)}")
        raise

def test_receiving_stats_with_positions():
    """Test with custom position filter"""
    print("\n=== Test 4: With custom positions (WR only) ===")

    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_ANON_KEY")
    )

    try:
        result = get_advanced_receiving_stats(
            supabase=supabase,
            positions=["WR"],
            limit=5
        )

        assert "advReceivingStats" in result, "Missing 'advReceivingStats' key"

        # Check position filtering
        if result["advReceivingStats"]:
            for row in result["advReceivingStats"]:
                assert row["ff_position"] == "WR", f"Position filter failed: {row['ff_position']}"

        print(f"✓ PASS: Returned {len(result['advReceivingStats'])} rows, all WR")

    except Exception as e:
        print(f"✗ FAIL: {str(e)}")
        raise

def test_receiving_stats_with_ordering():
    """Test with order_by_metric"""
    print("\n=== Test 5: With order_by_metric ===")

    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_ANON_KEY")
    )

    try:
        result = get_advanced_receiving_stats(
            supabase=supabase,
            metrics=["receiving_yards"],
            order_by_metric="receiving_yards",
            limit=5
        )

        assert "advReceivingStats" in result, "Missing 'advReceivingStats' key"

        # Check ordering (should be descending by metric)
        if len(result["advReceivingStats"]) > 1:
            first_yards = result["advReceivingStats"][0].get("receiving_yards")
            second_yards = result["advReceivingStats"][1].get("receiving_yards")
            if first_yards is not None and second_yards is not None:
                assert first_yards >= second_yards, "Ordering should be descending"

        print(f"✓ PASS: Returned {len(result['advReceivingStats'])} rows ordered by receiving_yards")
        if result["advReceivingStats"]:
            print(f"  Top: {result['advReceivingStats'][0]['player_name']} - {result['advReceivingStats'][0].get('receiving_yards')} yards")

    except Exception as e:
        print(f"✗ FAIL: {str(e)}")
        raise

if __name__ == "__main__":
    print("=" * 60)
    print("Testing get_advanced_receiving_stats migration")
    print("=" * 60)

    try:
        test_receiving_stats_basic()
        test_receiving_stats_with_filters()
        test_receiving_stats_with_metrics()
        test_receiving_stats_with_positions()
        test_receiving_stats_with_ordering()

        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)

    except Exception as e:
        print("\n" + "=" * 60)
        print("✗ TESTS FAILED")
        print("=" * 60)
        raise
