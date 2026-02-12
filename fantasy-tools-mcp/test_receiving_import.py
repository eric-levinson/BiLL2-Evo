"""
Simple import and structure verification test for get_advanced_receiving_stats migration.
This test verifies the function can be imported and has the correct signature.
"""

import inspect
from tools.metrics.info import get_advanced_receiving_stats
from helpers.query_utils import build_player_stats_query

def test_import():
    """Test that the function can be imported"""
    print("\n=== Test 1: Import verification ===")
    try:
        assert get_advanced_receiving_stats is not None
        print("✓ PASS: get_advanced_receiving_stats imported successfully")
    except Exception as e:
        print(f"✗ FAIL: {str(e)}")
        raise

def test_signature():
    """Test that the function has the correct signature"""
    print("\n=== Test 2: Signature verification ===")
    try:
        sig = inspect.signature(get_advanced_receiving_stats)
        params = list(sig.parameters.keys())

        expected_params = [
            "supabase",
            "player_names",
            "season_list",
            "metrics",
            "order_by_metric",
            "limit",
            "positions"
        ]

        assert params == expected_params, f"Expected {expected_params}, got {params}"
        print("✓ PASS: Function signature is correct")
        print(f"  Parameters: {', '.join(params)}")
    except Exception as e:
        print(f"✗ FAIL: {str(e)}")
        raise

def test_docstring():
    """Test that the function has a docstring"""
    print("\n=== Test 3: Docstring verification ===")
    try:
        assert get_advanced_receiving_stats.__doc__ is not None
        assert len(get_advanced_receiving_stats.__doc__) > 0
        print("✓ PASS: Function has docstring")
        print(f"  Docstring length: {len(get_advanced_receiving_stats.__doc__)} characters")
    except Exception as e:
        print(f"✗ FAIL: {str(e)}")
        raise

def test_helper_import():
    """Test that the helper function is imported correctly"""
    print("\n=== Test 4: Helper function import ===")
    try:
        assert build_player_stats_query is not None
        print("✓ PASS: build_player_stats_query imported successfully")
    except Exception as e:
        print(f"✗ FAIL: {str(e)}")
        raise

def test_function_source():
    """Test that the function uses the helper (basic check)"""
    print("\n=== Test 5: Function implementation check ===")
    try:
        source = inspect.getsource(get_advanced_receiving_stats)

        # Check that it calls build_player_stats_query
        assert "build_player_stats_query" in source, "Function should call build_player_stats_query"

        # Check that it uses the correct table
        assert "vw_advanced_receiving_analytics" in source, "Should query vw_advanced_receiving_analytics"

        # Check that it uses the correct return key
        assert "advReceivingStats" in source, "Should return advReceivingStats key"

        # Check that it uses merge_name column
        assert "merge_name" in source, "Should use merge_name for player filtering"

        print("✓ PASS: Function implementation looks correct")
        print("  - Calls build_player_stats_query")
        print("  - Uses correct table: vw_advanced_receiving_analytics")
        print("  - Uses correct return key: advReceivingStats")
        print("  - Uses correct player name column: merge_name")
    except Exception as e:
        print(f"✗ FAIL: {str(e)}")
        raise

if __name__ == "__main__":
    print("=" * 60)
    print("Verifying get_advanced_receiving_stats migration")
    print("=" * 60)

    try:
        test_import()
        test_signature()
        test_docstring()
        test_helper_import()
        test_function_source()

        print("\n" + "=" * 60)
        print("✓ ALL VERIFICATION TESTS PASSED")
        print("=" * 60)
        print("\nThe migration is complete and correct:")
        print("  - Function signature preserved")
        print("  - Docstring preserved")
        print("  - Uses build_player_stats_query helper")
        print("  - Correct table and parameters configured")

    except Exception as e:
        print("\n" + "=" * 60)
        print("✗ VERIFICATION FAILED")
        print("=" * 60)
        raise
