#!/usr/bin/env python3
"""
Unit test to verify get_advanced_passing_stats_weekly migration structure.
Tests function signature and call structure without requiring database connection.
"""
import sys
import os

# Add fantasy-tools-mcp to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'fantasy-tools-mcp'))

from unittest.mock import Mock, patch
from tools.metrics.info import get_advanced_passing_stats_weekly

def test_passing_weekly_stats_structure():
    """Test that get_advanced_passing_stats_weekly uses build_player_stats_query correctly."""
    print("Testing get_advanced_passing_stats_weekly migration structure...")
    print("=" * 60)

    # Mock supabase client
    mock_supabase = Mock()

    # Test that the function calls build_player_stats_query with correct params
    print("\n1. Testing function signature and parameters:")
    try:
        with patch('tools.metrics.info.build_player_stats_query') as mock_build:
            # Set up mock return value
            mock_build.return_value = {"advPassingStats": []}

            # Call the function with all parameters
            result = get_advanced_passing_stats_weekly(
                supabase=mock_supabase,
                player_names=["Mahomes"],
                season_list=[2024],
                weekly_list=[1, 2, 3],
                metrics=["passing_yards", "passing_tds", "interceptions"],
                order_by_metric="passing_yards",
                limit=10,
                positions=["QB"]
            )

            # Verify build_player_stats_query was called
            assert mock_build.called, "Should call build_player_stats_query"
            print("   ✓ Calls build_player_stats_query")

            # Verify the call arguments
            call_args = mock_build.call_args
            assert call_args is not None, "Should have call arguments"

            # Check kwargs
            kwargs = call_args.kwargs
            print(f"   ✓ Called with kwargs: {list(kwargs.keys())}")

            # Verify correct parameters
            assert kwargs["table_name"] == "vw_advanced_passing_analytics_weekly", f"Wrong table: {kwargs.get('table_name')}"
            print("   ✓ Correct table_name: vw_advanced_passing_analytics_weekly")

            assert kwargs["base_columns"] == ["season", "week", "player_name", "team", "position"], f"Wrong base_columns: {kwargs.get('base_columns')}"
            print("   ✓ Correct base_columns: ['season', 'week', 'player_name', 'team', 'position']")

            assert kwargs["player_name_column"] == "merge_name", f"Wrong player_name_column: {kwargs.get('player_name_column')}"
            print("   ✓ Correct player_name_column: merge_name")

            assert kwargs["position_column"] == "position", f"Wrong position_column: {kwargs.get('position_column')}"
            print("   ✓ Correct position_column: position")

            assert kwargs["default_positions"] == ["QB"], f"Wrong default_positions: {kwargs.get('default_positions')}"
            print("   ✓ Correct default_positions: ['QB']")

            assert kwargs["return_key"] == "advPassingStats", f"Wrong return_key: {kwargs.get('return_key')}"
            print("   ✓ Correct return_key: advPassingStats")

            assert kwargs["player_names"] == ["Mahomes"], f"Wrong player_names: {kwargs.get('player_names')}"
            print("   ✓ Passes through player_names")

            assert kwargs["season_list"] == [2024], f"Wrong season_list: {kwargs.get('season_list')}"
            print("   ✓ Passes through season_list")

            assert kwargs["weekly_list"] == [1, 2, 3], f"Wrong weekly_list: {kwargs.get('weekly_list')}"
            print("   ✓ Passes through weekly_list: [1, 2, 3]")

            assert kwargs["metrics"] == ["passing_yards", "passing_tds", "interceptions"], f"Wrong metrics: {kwargs.get('metrics')}"
            print("   ✓ Passes through metrics")

            assert kwargs["order_by_metric"] == "passing_yards", f"Wrong order_by_metric: {kwargs.get('order_by_metric')}"
            print("   ✓ Passes through order_by_metric")

            assert kwargs["limit"] == 10, f"Wrong limit: {kwargs.get('limit')}"
            print("   ✓ Passes through limit")

            assert kwargs["positions"] == ["QB"], f"Wrong positions: {kwargs.get('positions')}"
            print("   ✓ Passes through positions")

            # Verify return value
            assert result == {"advPassingStats": []}, "Should return result from build_player_stats_query"
            print("   ✓ Returns result from build_player_stats_query")

    except AssertionError as e:
        print(f"   ❌ Failed: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n2. Testing with None weekly_list (should still pass it through):")
    try:
        with patch('tools.metrics.info.build_player_stats_query') as mock_build:
            mock_build.return_value = {"advPassingStats": []}

            result = get_advanced_passing_stats_weekly(
                supabase=mock_supabase,
                season_list=[2024],
                weekly_list=None,
                limit=5
            )

            kwargs = mock_build.call_args.kwargs
            assert kwargs["weekly_list"] is None, f"Should pass through None weekly_list: {kwargs.get('weekly_list')}"
            print("   ✓ Correctly passes through None weekly_list")

    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False

    print("\n3. Testing default parameter values:")
    try:
        with patch('tools.metrics.info.build_player_stats_query') as mock_build:
            mock_build.return_value = {"advPassingStats": []}

            # Call with minimal parameters
            result = get_advanced_passing_stats_weekly(
                supabase=mock_supabase
            )

            kwargs = mock_build.call_args.kwargs
            assert kwargs["player_names"] is None, "Default player_names should be None"
            assert kwargs["season_list"] is None, "Default season_list should be None"
            assert kwargs["weekly_list"] is None, "Default weekly_list should be None"
            assert kwargs["metrics"] is None, "Default metrics should be None"
            assert kwargs["order_by_metric"] is None, "Default order_by_metric should be None"
            assert kwargs["limit"] == 25, "Default limit should be 25"
            assert kwargs["positions"] is None, "Default positions should be None"
            print("   ✓ All default parameter values are correct")

    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False

    print("\n✅ All unit tests passed!")
    print("\nMigration verified:")
    print("  - Function now uses build_player_stats_query helper")
    print("  - All parameters are correctly passed through")
    print("  - weekly_list parameter is properly handled")
    print("  - Eliminates ~70 lines of duplicated query logic")
    return True

if __name__ == "__main__":
    success = test_passing_weekly_stats_structure()
    sys.exit(0 if success else 1)
