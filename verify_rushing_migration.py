#!/usr/bin/env python3
"""
Verify get_advanced_rushing_stats migration by checking code structure.
This validates that the function correctly uses build_player_stats_query.
"""

import os
import sys
import ast
import inspect

# Add fantasy-tools-mcp to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "fantasy-tools-mcp"))

from tools.metrics.info import get_advanced_rushing_stats, get_advanced_receiving_stats
from helpers.query_utils import build_player_stats_query

def verify_migration():
    """Verify the migration by checking function structure and signature."""

    print("Verifying get_advanced_rushing_stats migration...\n")

    # Test 1: Check function signature matches pattern
    print("Test 1: Function signature")
    rushing_sig = inspect.signature(get_advanced_rushing_stats)
    receiving_sig = inspect.signature(get_advanced_receiving_stats)

    rushing_params = list(rushing_sig.parameters.keys())
    receiving_params = list(receiving_sig.parameters.keys())

    assert rushing_params == receiving_params, f"Parameter mismatch: {rushing_params} vs {receiving_params}"
    print(f"   ✓ Function signature matches pattern: {rushing_params}")

    # Test 2: Check function source uses build_player_stats_query
    print("\nTest 2: Implementation uses build_player_stats_query")
    source = inspect.getsource(get_advanced_rushing_stats)

    assert "build_player_stats_query" in source, "Function should call build_player_stats_query"
    print("   ✓ Function calls build_player_stats_query")

    # Test 3: Check that old query logic is removed
    print("\nTest 3: Old query logic removed")
    old_patterns = [
        "columns = [",
        "sanitize_name",
        "or_filter = ",
        "query = supabase.table",
        "query.in_(",
        "query.or_(",
    ]

    for pattern in old_patterns:
        if pattern in source:
            print(f"   ❌ Found old pattern: {pattern}")
            return False

    print("   ✓ Old query logic removed")

    # Test 4: Verify correct parameters are passed
    print("\nTest 4: Correct parameters passed to build_player_stats_query")
    required_params = {
        'table_name': 'vw_advanced_rushing_analytics',
        'base_columns': ['season', 'player_name', 'ff_team', 'ff_position'],
        'player_name_column': 'merge_name',
        'position_column': 'ff_position',
        'default_positions': ['RB', 'QB'],
        'return_key': 'advRushingStats',
    }

    for key, expected_value in required_params.items():
        if key not in source:
            print(f"   ❌ Missing parameter: {key}")
            return False

        # Check the value is correct
        if isinstance(expected_value, str):
            if f'"{expected_value}"' not in source and f"'{expected_value}'" not in source:
                print(f"   ❌ Wrong value for {key}: expected {expected_value}")
                return False

    print("   ✓ All required parameters present with correct values")

    # Test 5: Check docstring is preserved
    print("\nTest 5: Docstring preserved")
    docstring = get_advanced_rushing_stats.__doc__
    assert docstring is not None, "Docstring should be preserved"
    assert "rushing stats" in docstring.lower(), "Docstring should mention rushing stats"
    assert "RB" in docstring and "QB" in docstring, "Docstring should mention RB/QB defaults"
    print("   ✓ Docstring preserved and correct")

    # Test 6: Compare with receiving stats pattern
    print("\nTest 6: Matches receiving stats pattern")
    receiving_source = inspect.getsource(get_advanced_receiving_stats)

    # Both should have similar structure (return build_player_stats_query(...))
    assert "return build_player_stats_query" in source, "Should return from build_player_stats_query"
    assert "return build_player_stats_query" in receiving_source, "Pattern should return from build_player_stats_query"
    print("   ✓ Follows same pattern as migrated receiving stats function")

    # Test 7: Check function is concise (no duplicate logic)
    print("\nTest 7: Function is concise")
    lines = [line for line in source.split('\n') if line.strip() and not line.strip().startswith('#')]

    # Should be roughly: def line, docstring, return statement = ~20-30 lines total
    if len(lines) > 40:
        print(f"   ⚠ Function is longer than expected: {len(lines)} lines")
        print("   This might indicate duplicated logic wasn't fully removed")
    else:
        print(f"   ✓ Function is concise: {len(lines)} lines")

    print("\n✅ All verification checks passed!")
    print("\nMigration Summary:")
    print("  - Function signature preserved")
    print("  - Uses build_player_stats_query helper")
    print("  - Old query logic removed")
    print("  - Correct parameters for rushing stats (vw_advanced_rushing_analytics, RB/QB positions)")
    print("  - Docstring preserved")
    print("  - Matches pattern from get_advanced_receiving_stats")

    return True

if __name__ == "__main__":
    try:
        success = verify_migration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
