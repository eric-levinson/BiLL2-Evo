#!/usr/bin/env python3
"""
Unit test to verify get_advanced_defense_stats migration structure.
Tests function signature and call structure without requiring database connection.
"""
import sys
import os

# Add fantasy-tools-mcp to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'fantasy-tools-mcp'))

from unittest.mock import Mock, patch
from tools.metrics.info import get_advanced_defense_stats

def test_defense_stats_structure():
    """Test that get_advanced_defense_stats uses build_player_stats_query correctly."""
    print("Testing get_advanced_defense_stats migration structure...")
    print("=" * 60)

    # Mock supabase client
    mock_supabase = Mock()

    # Test that the function calls build_player_stats_query with correct params
    print("\n1. Testing function signature and parameters:")
    try:
        with patch('tools.metrics.info.build_player_stats_query') as mock_build:
            # Set up mock return value
            mock_build.return_value = {"advDefenseStats": []}

            # Call the function with all parameters
            result = get_advanced_defense_stats(
                supabase=mock_supabase,
                player_names=["Parsons"],
                season_list=[2024],
                metrics=["tackles", "sacks"],
                order_by_metric="sacks",
                limit=10,
                positions=["LB"]
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
            assert kwargs["table_name"] == "vw_advanced_def_analytics", f"Wrong table: {kwargs.get('table_name')}"
            print("   ✓ Correct table_name: vw_advanced_def_analytics")

            assert kwargs["base_columns"] == ["season", "player_name", "team", "position"], f"Wrong base_columns: {kwargs.get('base_columns')}"
            print("   ✓ Correct base_columns: ['season', 'player_name', 'team', 'position']")

            assert kwargs["player_name_column"] == "merge_name", f"Wrong player_name_column: {kwargs.get('player_name_column')}"
            print("   ✓ Correct player_name_column: merge_name")

            assert kwargs["position_column"] == "position", f"Wrong position_column: {kwargs.get('position_column')}"
            print("   ✓ Correct position_column: position")

            assert kwargs["default_positions"] == ["CB", "DB", "DE", "DL", "LB", "S"], f"Wrong default_positions: {kwargs.get('default_positions')}"
            print("   ✓ Correct default_positions: ['CB', 'DB', 'DE', 'DL', 'LB', 'S']")

            assert kwargs["return_key"] == "advDefenseStats", f"Wrong return_key: {kwargs.get('return_key')}"
            print("   ✓ Correct return_key: advDefenseStats")

            assert kwargs["player_names"] == ["Parsons"], f"Wrong player_names: {kwargs.get('player_names')}"
            print("   ✓ Passes through player_names")

            assert kwargs["season_list"] == [2024], f"Wrong season_list: {kwargs.get('season_list')}"
            print("   ✓ Passes through season_list")

            assert kwargs["weekly_list"] is None, f"Wrong weekly_list: {kwargs.get('weekly_list')}"
            print("   ✓ Sets weekly_list to None (seasonal function)")

            assert kwargs["metrics"] == ["tackles", "sacks"], f"Wrong metrics: {kwargs.get('metrics')}"
            print("   ✓ Passes through metrics")

            assert kwargs["order_by_metric"] == "sacks", f"Wrong order_by_metric: {kwargs.get('order_by_metric')}"
            print("   ✓ Passes through order_by_metric")

            assert kwargs["limit"] == 10, f"Wrong limit: {kwargs.get('limit')}"
            print("   ✓ Passes through limit")

            assert kwargs["positions"] == ["LB"], f"Wrong positions: {kwargs.get('positions')}"
            print("   ✓ Passes through positions")

            # Verify return value
            assert result == {"advDefenseStats": []}, "Should return result from build_player_stats_query"
            print("   ✓ Returns result from build_player_stats_query")

    except AssertionError as e:
        print(f"   ❌ Failed: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n2. Testing default parameters:")
    try:
        with patch('tools.metrics.info.build_player_stats_query') as mock_build:
            mock_build.return_value = {"advDefenseStats": []}

            # Call with minimal parameters
            result = get_advanced_defense_stats(supabase=mock_supabase)

            kwargs = mock_build.call_args.kwargs
            assert kwargs["player_names"] is None, "player_names should default to None"
            assert kwargs["season_list"] is None, "season_list should default to None"
            assert kwargs["metrics"] is None, "metrics should default to None"
            assert kwargs["order_by_metric"] is None, "order_by_metric should default to None"
            assert kwargs["limit"] == 25, "limit should default to 25"
            assert kwargs["positions"] is None, "positions should default to None (uses default_positions)"
            print("   ✓ All default parameters passed correctly")

    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False

    print("\n" + "=" * 60)
    print("✅ All unit tests passed! Migration structure is correct.")
    return True

if __name__ == "__main__":
    success = test_defense_stats_structure()
    sys.exit(0 if success else 1)
