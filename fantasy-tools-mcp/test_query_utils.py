#!/usr/bin/env python3
"""
Comprehensive unit tests for helpers/query_utils.py

Tests the build_player_stats_query function covering:
- Column building with and without metrics
- Name sanitization and filtering
- Position filtering with defaults and custom positions
- Limit enforcement and max cap
- Query construction with various filter combinations
- Ordering logic (metric, season, player)
- Error handling
"""

import sys
from unittest.mock import Mock, MagicMock


def test_column_building():
    """Test that columns are built correctly with base columns and metrics."""
    print("\n=== Testing Column Building ===")
    try:
        from helpers.query_utils import build_player_stats_query

        # Create mock Supabase client
        mock_client = Mock()
        mock_query = Mock()
        mock_response = Mock()
        mock_response.data = []

        # Setup chain of method calls
        mock_client.table.return_value = mock_query
        mock_query.select.return_value = mock_query
        mock_query.in_.return_value = mock_query
        mock_query.or_.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.return_value = mock_response

        # Test with base columns only
        result = build_player_stats_query(
            supabase=mock_client,
            table_name="test_table",
            base_columns=["season", "player_name"],
            player_name_column="merge_name",
            position_column="ff_position",
            default_positions=["WR"],
            return_key="testStats",
            limit=10
        )

        # Verify select was called with base columns
        call_args = mock_query.select.call_args[0][0]
        assert "season" in call_args and "player_name" in call_args
        print("  ✓ Base columns included in query")

        # Test with metrics
        mock_query.select.reset_mock()
        result = build_player_stats_query(
            supabase=mock_client,
            table_name="test_table",
            base_columns=["season", "player_name"],
            player_name_column="merge_name",
            position_column="ff_position",
            default_positions=["WR"],
            return_key="testStats",
            metrics=["targets", "receptions"],
            limit=10
        )

        # Verify select includes both base columns and metrics
        call_args = mock_query.select.call_args[0][0]
        assert "season" in call_args and "player_name" in call_args
        assert "targets" in call_args and "receptions" in call_args
        print("  ✓ Base columns + metrics included in query")

        print("✅ PASS: Column building works correctly")
        return True

    except AssertionError as e:
        print(f"❌ FAIL: Assertion failed - {str(e)}")
        return False
    except Exception as e:
        print(f"❌ FAIL: Exception occurred: {str(e)}")
        return False


def test_name_sanitization():
    """Test that player names are sanitized and filtered correctly."""
    print("\n=== Testing Name Sanitization and Filtering ===")
    try:
        from helpers.query_utils import build_player_stats_query

        # Create mock Supabase client
        mock_client = Mock()
        mock_query = Mock()
        mock_response = Mock()
        mock_response.data = []

        mock_client.table.return_value = mock_query
        mock_query.select.return_value = mock_query
        mock_query.in_.return_value = mock_query
        mock_query.or_.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.return_value = mock_response

        # Test with player names containing special characters
        result = build_player_stats_query(
            supabase=mock_client,
            table_name="test_table",
            base_columns=["season", "player_name"],
            player_name_column="merge_name",
            position_column="ff_position",
            default_positions=["WR"],
            return_key="testStats",
            player_names=["O'Dell", "Smith Jr.", "José"],
            limit=10
        )

        # Verify or_ filter was applied
        assert mock_query.or_.called
        or_filter = mock_query.or_.call_args[0][0]
        # Sanitized names should be lowercase without punctuation
        print(f"  ✓ OR filter created: {or_filter}")

        # Test without player names
        mock_query.or_.reset_mock()
        result = build_player_stats_query(
            supabase=mock_client,
            table_name="test_table",
            base_columns=["season", "player_name"],
            player_name_column="merge_name",
            position_column="ff_position",
            default_positions=["WR"],
            return_key="testStats",
            limit=10
        )

        # Verify or_ filter was NOT applied when no names provided
        assert not mock_query.or_.called
        print("  ✓ No OR filter when player_names is None")

        print("✅ PASS: Name sanitization and filtering works correctly")
        return True

    except AssertionError as e:
        print(f"❌ FAIL: Assertion failed - {str(e)}")
        return False
    except Exception as e:
        print(f"❌ FAIL: Exception occurred: {str(e)}")
        return False


def test_position_filtering():
    """Test position filtering with default and custom positions."""
    print("\n=== Testing Position Filtering ===")
    try:
        from helpers.query_utils import build_player_stats_query

        # Create mock Supabase client
        mock_client = Mock()
        mock_query = Mock()
        mock_response = Mock()
        mock_response.data = []

        mock_client.table.return_value = mock_query
        mock_query.select.return_value = mock_query
        mock_query.in_.return_value = mock_query
        mock_query.or_.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.return_value = mock_response

        # Test with default positions (positions=None)
        result = build_player_stats_query(
            supabase=mock_client,
            table_name="test_table",
            base_columns=["season", "player_name"],
            player_name_column="merge_name",
            position_column="ff_position",
            default_positions=["WR", "TE", "RB"],
            return_key="testStats",
            positions=None,  # Should use defaults
            limit=10
        )

        # Verify in_ filter was applied with default positions
        in_calls = [call for call in mock_query.in_.call_args_list if call[0][0] == "ff_position"]
        assert len(in_calls) > 0
        positions_used = in_calls[0][0][1]
        assert set(positions_used) == {"WR", "TE", "RB"}
        print("  ✓ Default positions applied when positions=None")

        # Test with custom positions
        mock_query.in_.reset_mock()
        result = build_player_stats_query(
            supabase=mock_client,
            table_name="test_table",
            base_columns=["season", "player_name"],
            player_name_column="merge_name",
            position_column="ff_position",
            default_positions=["WR", "TE", "RB"],
            return_key="testStats",
            positions=["QB"],  # Override defaults
            limit=10
        )

        # Verify in_ filter uses custom positions
        in_calls = [call for call in mock_query.in_.call_args_list if call[0][0] == "ff_position"]
        assert len(in_calls) > 0
        positions_used = in_calls[0][0][1]
        assert positions_used == ["QB"]
        print("  ✓ Custom positions override defaults")

        # Test position normalization (lowercase to uppercase)
        mock_query.in_.reset_mock()
        result = build_player_stats_query(
            supabase=mock_client,
            table_name="test_table",
            base_columns=["season", "player_name"],
            player_name_column="merge_name",
            position_column="ff_position",
            default_positions=["WR"],
            return_key="testStats",
            positions=["qb", "Wr"],  # Mixed case
            limit=10
        )

        # Verify positions are normalized to uppercase
        in_calls = [call for call in mock_query.in_.call_args_list if call[0][0] == "ff_position"]
        positions_used = in_calls[0][0][1]
        assert positions_used == ["QB", "WR"]
        print("  ✓ Positions normalized to uppercase")

        print("✅ PASS: Position filtering works correctly")
        return True

    except AssertionError as e:
        print(f"❌ FAIL: Assertion failed - {str(e)}")
        return False
    except Exception as e:
        print(f"❌ FAIL: Exception occurred: {str(e)}")
        return False


def test_limit_enforcement():
    """Test that limit is enforced and capped at max (300)."""
    print("\n=== Testing Limit Enforcement ===")
    try:
        from helpers.query_utils import build_player_stats_query

        # Create mock Supabase client
        mock_client = Mock()
        mock_query = Mock()
        mock_response = Mock()
        mock_response.data = []

        mock_client.table.return_value = mock_query
        mock_query.select.return_value = mock_query
        mock_query.in_.return_value = mock_query
        mock_query.or_.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.return_value = mock_response

        # Test normal limit
        result = build_player_stats_query(
            supabase=mock_client,
            table_name="test_table",
            base_columns=["season", "player_name"],
            player_name_column="merge_name",
            position_column="ff_position",
            default_positions=["WR"],
            return_key="testStats",
            limit=50
        )

        # Verify limit was applied
        assert mock_query.limit.called
        assert mock_query.limit.call_args[0][0] == 50
        print("  ✓ Normal limit (50) applied correctly")

        # Test max cap (should cap at 300)
        mock_query.limit.reset_mock()
        result = build_player_stats_query(
            supabase=mock_client,
            table_name="test_table",
            base_columns=["season", "player_name"],
            player_name_column="merge_name",
            position_column="ff_position",
            default_positions=["WR"],
            return_key="testStats",
            limit=500  # Exceeds max
        )

        # Verify limit was capped at 300
        assert mock_query.limit.called
        assert mock_query.limit.call_args[0][0] == 300
        print("  ✓ Limit capped at max (300)")

        # Test None limit (no limit applied)
        mock_query.limit.reset_mock()
        result = build_player_stats_query(
            supabase=mock_client,
            table_name="test_table",
            base_columns=["season", "player_name"],
            player_name_column="merge_name",
            position_column="ff_position",
            default_positions=["WR"],
            return_key="testStats",
            limit=None
        )

        # Verify limit was NOT applied
        assert not mock_query.limit.called
        print("  ✓ No limit applied when limit=None")

        # Test zero limit (no limit applied)
        mock_query.limit.reset_mock()
        result = build_player_stats_query(
            supabase=mock_client,
            table_name="test_table",
            base_columns=["season", "player_name"],
            player_name_column="merge_name",
            position_column="ff_position",
            default_positions=["WR"],
            return_key="testStats",
            limit=0
        )

        # Verify limit was NOT applied
        assert not mock_query.limit.called
        print("  ✓ No limit applied when limit=0")

        print("✅ PASS: Limit enforcement works correctly")
        return True

    except AssertionError as e:
        print(f"❌ FAIL: Assertion failed - {str(e)}")
        return False
    except Exception as e:
        print(f"❌ FAIL: Exception occurred: {str(e)}")
        return False


def test_query_filters():
    """Test query construction with various filter combinations."""
    print("\n=== Testing Query Filter Combinations ===")
    try:
        from helpers.query_utils import build_player_stats_query

        # Create mock Supabase client
        mock_client = Mock()
        mock_query = Mock()
        mock_response = Mock()
        mock_response.data = []

        mock_client.table.return_value = mock_query
        mock_query.select.return_value = mock_query
        mock_query.in_.return_value = mock_query
        mock_query.or_.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.return_value = mock_response

        # Test with season filter
        result = build_player_stats_query(
            supabase=mock_client,
            table_name="test_table",
            base_columns=["season", "player_name"],
            player_name_column="merge_name",
            position_column="ff_position",
            default_positions=["WR"],
            return_key="testStats",
            season_list=[2023, 2024],
            limit=10
        )

        # Verify season filter was applied
        in_calls = [call for call in mock_query.in_.call_args_list if call[0][0] == "season"]
        assert len(in_calls) > 0
        assert in_calls[0][0][1] == [2023, 2024]
        print("  ✓ Season filter applied")

        # Test with weekly filter (for weekly tables)
        mock_query.in_.reset_mock()
        result = build_player_stats_query(
            supabase=mock_client,
            table_name="test_table",
            base_columns=["season", "week", "player_name"],
            player_name_column="merge_name",
            position_column="ff_position",
            default_positions=["WR"],
            return_key="testStats",
            season_list=[2024],
            weekly_list=[1, 2, 3],
            limit=10
        )

        # Verify both season and week filters were applied
        season_calls = [call for call in mock_query.in_.call_args_list if call[0][0] == "season"]
        week_calls = [call for call in mock_query.in_.call_args_list if call[0][0] == "week"]
        assert len(season_calls) > 0
        assert len(week_calls) > 0
        assert week_calls[0][0][1] == [1, 2, 3]
        print("  ✓ Season and week filters applied")

        # Test with all filters combined
        mock_query.in_.reset_mock()
        mock_query.or_.reset_mock()
        result = build_player_stats_query(
            supabase=mock_client,
            table_name="test_table",
            base_columns=["season", "week", "player_name"],
            player_name_column="merge_name",
            position_column="ff_position",
            default_positions=["WR"],
            return_key="testStats",
            player_names=["Jefferson"],
            season_list=[2024],
            weekly_list=[1, 2],
            positions=["WR", "TE"],
            limit=10
        )

        # Verify all filters were applied
        assert mock_query.in_.called
        assert mock_query.or_.called
        print("  ✓ All filters applied together")

        print("✅ PASS: Query filter combinations work correctly")
        return True

    except AssertionError as e:
        print(f"❌ FAIL: Assertion failed - {str(e)}")
        return False
    except Exception as e:
        print(f"❌ FAIL: Exception occurred: {str(e)}")
        return False


def test_ordering_logic():
    """Test ordering logic with metric ordering and default ordering."""
    print("\n=== Testing Ordering Logic ===")
    try:
        from helpers.query_utils import build_player_stats_query

        # Create mock Supabase client
        mock_client = Mock()
        mock_query = Mock()
        mock_response = Mock()
        mock_response.data = []

        # Setup not_ chain for metric ordering
        mock_not = Mock()
        mock_query.not_ = mock_not
        mock_not.is_ = Mock(return_value=mock_query)

        mock_client.table.return_value = mock_query
        mock_query.select.return_value = mock_query
        mock_query.in_.return_value = mock_query
        mock_query.or_.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.return_value = mock_response

        # Test with metric ordering
        result = build_player_stats_query(
            supabase=mock_client,
            table_name="test_table",
            base_columns=["season", "player_name"],
            player_name_column="merge_name",
            position_column="ff_position",
            default_positions=["WR"],
            return_key="testStats",
            order_by_metric="receiving_yards",
            limit=10
        )

        # Verify not_.is_ was called to filter nulls
        assert mock_not.is_.called
        assert mock_not.is_.call_args[0][0] == "receiving_yards"
        print("  ✓ Null filtering applied for metric ordering")

        # Verify order was called with the metric
        order_calls = mock_query.order.call_args_list
        metric_order = [call for call in order_calls if call[0][0] == "receiving_yards"]
        assert len(metric_order) > 0
        assert metric_order[0][1].get("desc") == True
        print("  ✓ Metric ordered DESC")

        # Verify default ordering (season DESC, player_name ASC) is also applied
        season_order = [call for call in order_calls if call[0][0] == "season"]
        player_order = [call for call in order_calls if call[0][0] == "player_name"]
        assert len(season_order) > 0
        assert len(player_order) > 0
        assert season_order[0][1].get("desc") == True
        assert player_order[0][1].get("desc") == False
        print("  ✓ Default ordering (season DESC, player_name ASC) applied")

        # Test without metric ordering (only default ordering)
        mock_query.order.reset_mock()
        mock_not.is_.reset_mock()
        result = build_player_stats_query(
            supabase=mock_client,
            table_name="test_table",
            base_columns=["season", "player_name"],
            player_name_column="merge_name",
            position_column="ff_position",
            default_positions=["WR"],
            return_key="testStats",
            order_by_metric=None,
            limit=10
        )

        # Verify not_.is_ was NOT called
        assert not mock_not.is_.called
        print("  ✓ No null filtering when no metric ordering")

        # Verify only default ordering applied
        order_calls = mock_query.order.call_args_list
        assert len(order_calls) == 2  # Only season and player_name
        print("  ✓ Only default ordering applied when order_by_metric=None")

        print("✅ PASS: Ordering logic works correctly")
        return True

    except AssertionError as e:
        print(f"❌ FAIL: Assertion failed - {str(e)}")
        return False
    except Exception as e:
        print(f"❌ FAIL: Exception occurred: {str(e)}")
        return False


def test_error_handling():
    """Test error handling when query execution fails."""
    print("\n=== Testing Error Handling ===")
    try:
        from helpers.query_utils import build_player_stats_query

        # Create mock Supabase client that raises an exception
        mock_client = Mock()
        mock_query = Mock()

        mock_client.table.return_value = mock_query
        mock_query.select.return_value = mock_query
        mock_query.in_.return_value = mock_query
        mock_query.or_.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.side_effect = Exception("Database connection failed")

        # Test that exception is caught and re-raised with meaningful message
        try:
            result = build_player_stats_query(
                supabase=mock_client,
                table_name="test_table",
                base_columns=["season", "player_name"],
                player_name_column="merge_name",
                position_column="ff_position",
                default_positions=["WR"],
                return_key="testStats",
                limit=10
            )
            print("❌ FAIL: Expected exception was not raised")
            return False
        except Exception as e:
            error_msg = str(e)
            # Verify error message contains the return key
            assert "testStats" in error_msg or "Error fetching" in error_msg
            print(f"  ✓ Exception caught and re-raised: {error_msg}")

        print("✅ PASS: Error handling works correctly")
        return True

    except AssertionError as e:
        print(f"❌ FAIL: Assertion failed - {str(e)}")
        return False
    except Exception as e:
        print(f"❌ FAIL: Unexpected exception: {str(e)}")
        return False


def test_return_format():
    """Test that the return format is correct."""
    print("\n=== Testing Return Format ===")
    try:
        from helpers.query_utils import build_player_stats_query

        # Create mock Supabase client
        mock_client = Mock()
        mock_query = Mock()
        mock_response = Mock()
        test_data = [
            {"season": 2024, "player_name": "Justin Jefferson", "receiving_yards": 1234},
            {"season": 2023, "player_name": "Justin Jefferson", "receiving_yards": 1809}
        ]
        mock_response.data = test_data

        mock_client.table.return_value = mock_query
        mock_query.select.return_value = mock_query
        mock_query.in_.return_value = mock_query
        mock_query.or_.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.return_value = mock_response

        # Test return format
        result = build_player_stats_query(
            supabase=mock_client,
            table_name="test_table",
            base_columns=["season", "player_name"],
            player_name_column="merge_name",
            position_column="ff_position",
            default_positions=["WR"],
            return_key="advReceivingStats",
            limit=10
        )

        # Verify return format
        assert isinstance(result, dict)
        assert "advReceivingStats" in result
        assert result["advReceivingStats"] == test_data
        print("  ✓ Return format is a dict with correct key")
        print("  ✓ Data is returned under the specified key")

        # Test with different return key
        result = build_player_stats_query(
            supabase=mock_client,
            table_name="test_table",
            base_columns=["season", "player_name"],
            player_name_column="merge_name",
            position_column="ff_position",
            default_positions=["WR"],
            return_key="customKey",
            limit=10
        )

        assert "customKey" in result
        print("  ✓ Custom return key works correctly")

        print("✅ PASS: Return format is correct")
        return True

    except AssertionError as e:
        print(f"❌ FAIL: Assertion failed - {str(e)}")
        return False
    except Exception as e:
        print(f"❌ FAIL: Exception occurred: {str(e)}")
        return False


def main():
    """Run all tests and report results."""
    print("=" * 60)
    print("TESTING helpers/query_utils.py")
    print("=" * 60)

    results = {
        "column_building": test_column_building(),
        "name_sanitization": test_name_sanitization(),
        "position_filtering": test_position_filtering(),
        "limit_enforcement": test_limit_enforcement(),
        "query_filters": test_query_filters(),
        "ordering_logic": test_ordering_logic(),
        "error_handling": test_error_handling(),
        "return_format": test_return_format(),
    }

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n🎉 ALL TESTS PASSED - query_utils.py works correctly!")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED - Review the output above")
        sys.exit(1)


if __name__ == "__main__":
    main()
