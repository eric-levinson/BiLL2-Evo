#!/usr/bin/env python3
"""
Unit test for get_defensive_players_game_stats migration to build_player_stats_query.
Verifies that the refactored function correctly delegates to the generic helper.
"""
import sys
import os

# Add the fantasy-tools-mcp directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'fantasy-tools-mcp'))

from unittest.mock import Mock, patch
from tools.league.info import get_defensive_players_game_stats


def test_defensive_stats_uses_build_player_stats_query():
    """Test that get_defensive_players_game_stats uses build_player_stats_query with correct params"""
    print("Testing get_defensive_players_game_stats uses build_player_stats_query...")

    # Mock build_player_stats_query
    with patch('tools.league.info.build_player_stats_query') as mock_build:
        mock_build.return_value = {"defGameStats": []}

        mock_supabase = Mock()

        # Call the function
        result = get_defensive_players_game_stats(
            supabase=mock_supabase,
            player_names=["Parsons"],
            season_list=[2023],
            weekly_list=[1, 2],
            metrics=["tackles"],
            order_by_metric="tackles",
            limit=10,
            positions=["LB"]
        )

        # Verify build_player_stats_query was called
        assert mock_build.called, "build_player_stats_query should be called"

        # Get the call arguments
        call_args = mock_build.call_args
        kwargs = call_args.kwargs if call_args.kwargs else call_args[1] if len(call_args) > 1 else {}

        # Verify key parameters
        assert kwargs.get("table_name") == "nflreadr_nfl_player_stats_defense", "Table name should be nflreadr_nfl_player_stats_defense"
        assert kwargs.get("player_name_column") == "player_display_name", "Player name column should be player_display_name"
        assert kwargs.get("position_column") == "position", "Position column should be position"
        assert kwargs.get("return_key") == "defGameStats", "Return key should be defGameStats"

        # Verify base columns
        base_columns = kwargs.get("base_columns", [])
        expected_base = ["season", "week", "player_display_name", "team", "position"]
        assert set(base_columns) == set(expected_base), f"Base columns should be {expected_base}, got {base_columns}"

        # Verify default positions
        default_positions = kwargs.get("default_positions", [])
        expected_defaults = ["CB", "DB", "DE", "DL", "LB", "S"]
        assert set(default_positions) == set(expected_defaults), f"Default positions should be {expected_defaults}, got {default_positions}"

        # Verify parameters were passed through
        assert kwargs.get("player_names") == ["Parsons"], "player_names should be passed through"
        assert kwargs.get("season_list") == [2023], "season_list should be passed through"
        assert kwargs.get("weekly_list") == [1, 2], "weekly_list should be passed through"
        assert kwargs.get("metrics") == ["tackles"], "metrics should be passed through"
        assert kwargs.get("order_by_metric") == "tackles", "order_by_metric should be passed through"
        assert kwargs.get("limit") == 10, "limit should be passed through"
        assert kwargs.get("positions") == ["LB"], "positions should be passed through"

        print("✅ get_defensive_players_game_stats uses build_player_stats_query correctly")


def test_defensive_stats_return_value():
    """Test that return value is passed through correctly"""
    print("Testing return value...")

    with patch('tools.league.info.build_player_stats_query') as mock_build:
        expected_data = [{"season": 2023, "player_display_name": "Test Player"}]
        mock_build.return_value = {"defGameStats": expected_data}

        mock_supabase = Mock()
        result = get_defensive_players_game_stats(supabase=mock_supabase)

        assert result == {"defGameStats": expected_data}, "Return value should match build_player_stats_query output"

        print("✅ Return value is correct")


def test_defensive_stats_signature_preserved():
    """Test that function signature is preserved"""
    print("Testing function signature preservation...")

    import inspect
    sig = inspect.signature(get_defensive_players_game_stats)
    params = list(sig.parameters.keys())

    expected_params = [
        "supabase",
        "player_names",
        "season_list",
        "weekly_list",
        "metrics",
        "order_by_metric",
        "limit",
        "positions"
    ]

    assert params == expected_params, f"Function signature should be {expected_params}, got {params}"

    # Check default values
    assert sig.parameters["player_names"].default is None, "player_names default should be None"
    assert sig.parameters["season_list"].default is None, "season_list default should be None"
    assert sig.parameters["weekly_list"].default is None, "weekly_list default should be None"
    assert sig.parameters["metrics"].default is None, "metrics default should be None"
    assert sig.parameters["order_by_metric"].default is None, "order_by_metric default should be None"
    assert sig.parameters["limit"].default == 25, "limit default should be 25"
    assert sig.parameters["positions"].default is None, "positions default should be None"

    print("✅ Function signature is preserved")


def test_defensive_stats_docstring_preserved():
    """Test that docstring is preserved"""
    print("Testing docstring preservation...")

    docstring = get_defensive_players_game_stats.__doc__
    assert docstring is not None, "Docstring should be present"
    assert "Fetch defensive weekly game stats for NFL players" in docstring, "Docstring should contain description"
    assert "supabase" in docstring.lower(), "Docstring should document supabase parameter"
    assert "player_names" in docstring.lower(), "Docstring should document player_names parameter"

    print("✅ Docstring is preserved")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing get_defensive_players_game_stats migration")
    print("=" * 60)

    try:
        test_defensive_stats_uses_build_player_stats_query()
        test_defensive_stats_return_value()
        test_defensive_stats_signature_preserved()
        test_defensive_stats_docstring_preserved()

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
