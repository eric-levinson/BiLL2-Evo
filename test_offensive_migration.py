#!/usr/bin/env python3
"""
Unit test for get_offensive_players_game_stats migration to build_player_stats_query.
Verifies that the refactored function correctly delegates to the generic helper.
"""
import sys
import os

# Add the fantasy-tools-mcp directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'fantasy-tools-mcp'))

from unittest.mock import Mock, MagicMock, call
from tools.league.info import get_offensive_players_game_stats


def test_offensive_stats_delegation():
    """Test that get_offensive_players_game_stats correctly delegates to build_player_stats_query"""
    print("Testing get_offensive_players_game_stats delegation...")

    # Create a mock supabase client
    mock_supabase = Mock()
    mock_table = Mock()
    mock_select = Mock()
    mock_query = Mock()
    mock_response = Mock()

    # Setup the mock chain
    mock_supabase.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.in_.return_value = mock_query
    mock_query.in_.return_value = mock_query
    mock_query.or_.return_value = mock_query
    mock_query.not_ = Mock()
    mock_query.not_.is_ = Mock(return_value=mock_query)
    mock_query.order.return_value = mock_query
    mock_query.limit.return_value = mock_query

    mock_response.data = [
        {
            "season": 2023,
            "week": 1,
            "player_display_name": "Patrick Mahomes",
            "recent_team": "KC",
            "position": "QB",
            "passing_yards": 350
        }
    ]
    mock_query.execute.return_value = mock_response

    # Test call with all parameters
    result = get_offensive_players_game_stats(
        supabase=mock_supabase,
        player_names=["Mahomes"],
        season_list=[2023],
        weekly_list=[1, 2],
        metrics=["passing_yards", "passing_tds"],
        order_by_metric="passing_yards",
        limit=10,
        positions=["QB"]
    )

    # Verify the table was called with correct name
    mock_supabase.table.assert_called_once_with("nflreadr_nfl_player_stats")

    # Verify select was called with correct columns
    select_call = mock_table.select.call_args[0][0]
    expected_columns = ["season", "week", "player_display_name", "recent_team", "position", "passing_yards", "passing_tds"]
    actual_columns = select_call.split(",")
    assert set(actual_columns) == set(expected_columns), f"Expected columns {expected_columns}, got {actual_columns}"

    # Verify return format
    assert "offGameStats" in result, "Result should have 'offGameStats' key"
    assert isinstance(result["offGameStats"], list), "offGameStats should be a list"

    print("✅ get_offensive_players_game_stats delegates correctly")


def test_offensive_stats_default_positions():
    """Test that default positions are applied correctly"""
    print("Testing default positions...")

    # Create a mock supabase client
    mock_supabase = Mock()
    mock_table = Mock()
    mock_select = Mock()
    mock_query = Mock()
    mock_response = Mock()

    # Setup the mock chain
    mock_supabase.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.in_.return_value = mock_query
    mock_query.in_.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.limit.return_value = mock_query

    mock_response.data = []
    mock_query.execute.return_value = mock_response

    # Test call without positions parameter (should use defaults)
    result = get_offensive_players_game_stats(
        supabase=mock_supabase,
        season_list=[2023],
        limit=10
    )

    # Verify position filter was applied with default positions
    # The mock should have been called with .in_("position", ["QB", "WR", "TE", "RB"])
    in_calls = [call_obj for call_obj in mock_select.method_calls if call_obj[0] == 'in_']
    position_call = [c for c in in_calls if c[1][0] == "position"]

    assert len(position_call) > 0, "Position filter should be applied"
    positions = position_call[0][1][1]
    assert set(positions) == {"QB", "WR", "TE", "RB"}, f"Expected default positions [QB, WR, TE, RB], got {positions}"

    print("✅ Default positions applied correctly")


def test_offensive_stats_return_key():
    """Test that return key is correct"""
    print("Testing return key...")

    # Create a mock supabase client
    mock_supabase = Mock()
    mock_table = Mock()
    mock_select = Mock()
    mock_query = Mock()
    mock_response = Mock()

    # Setup the mock chain
    mock_supabase.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.in_.return_value = mock_query
    mock_query.in_.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.limit.return_value = mock_query

    mock_response.data = [{"test": "data"}]
    mock_query.execute.return_value = mock_response

    result = get_offensive_players_game_stats(
        supabase=mock_supabase,
        limit=5
    )

    # Verify return key
    assert "offGameStats" in result, "Result should have 'offGameStats' key"
    assert result["offGameStats"] == [{"test": "data"}], "Return data should match query result"

    print("✅ Return key is correct")


def test_offensive_stats_base_columns():
    """Test that base columns are correct"""
    print("Testing base columns...")

    # Create a mock supabase client
    mock_supabase = Mock()
    mock_table = Mock()
    mock_select = Mock()
    mock_query = Mock()
    mock_response = Mock()

    # Setup the mock chain
    mock_supabase.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.in_.return_value = mock_query
    mock_query.in_.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.limit.return_value = mock_query

    mock_response.data = []
    mock_query.execute.return_value = mock_response

    # Test call without metrics
    result = get_offensive_players_game_stats(
        supabase=mock_supabase,
        limit=5
    )

    # Verify select was called with base columns only
    select_call = mock_table.select.call_args[0][0]
    expected_base_columns = ["season", "week", "player_display_name", "recent_team", "position"]
    actual_columns = select_call.split(",")
    assert set(actual_columns) == set(expected_base_columns), f"Expected base columns {expected_base_columns}, got {actual_columns}"

    print("✅ Base columns are correct")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing get_offensive_players_game_stats migration")
    print("=" * 60)

    try:
        test_offensive_stats_delegation()
        test_offensive_stats_default_positions()
        test_offensive_stats_return_key()
        test_offensive_stats_base_columns()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
