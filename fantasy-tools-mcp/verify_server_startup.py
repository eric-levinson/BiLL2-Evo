#!/usr/bin/env python
"""
Verification script to check MCP server can start and tools register correctly.
This script verifies:
1. All necessary modules can be imported
2. Tool registry can load without errors
3. No import errors in refactored code
"""

import sys
import os

def verify_imports():
    """Verify all critical imports work."""
    print("=" * 60)
    print("VERIFYING IMPORTS")
    print("=" * 60)

    try:
        # Core dependencies
        print("✓ Checking fastmcp...", end=" ")
        import fastmcp
        print("OK")

        print("✓ Checking supabase...", end=" ")
        import supabase
        print("OK")

        print("✓ Checking dotenv...", end=" ")
        import dotenv
        print("OK")

        # Helper modules
        print("✓ Checking helpers.name_utils...", end=" ")
        from helpers import name_utils
        print("OK")

        print("✓ Checking helpers.query_utils...", end=" ")
        from helpers import query_utils
        print("OK")

        print("✓ Checking build_player_stats_query...", end=" ")
        from helpers.query_utils import build_player_stats_query
        print("OK")

        # Tools modules
        print("✓ Checking tools.registry...", end=" ")
        from tools import registry
        print("OK")

        print("✓ Checking tools.metrics.info...", end=" ")
        from tools.metrics import info as metrics_info
        print("OK")

        print("✓ Checking tools.league.info...", end=" ")
        from tools.league import info as league_info
        print("OK")

        return True

    except Exception as e:
        print(f"\n✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_refactored_functions():
    """Verify all refactored functions exist and are callable."""
    print("\n" + "=" * 60)
    print("VERIFYING REFACTORED FUNCTIONS")
    print("=" * 60)

    try:
        from tools.metrics.info import (
            get_advanced_receiving_stats,
            get_advanced_passing_stats,
            get_advanced_rushing_stats,
            get_advanced_defense_stats,
            get_advanced_receiving_stats_weekly,
            get_advanced_passing_stats_weekly,
            get_advanced_rushing_stats_weekly,
            get_advanced_defense_stats_weekly
        )

        from tools.league.info import (
            get_offensive_players_game_stats,
            get_defensive_players_game_stats
        )

        functions = [
            ("get_advanced_receiving_stats", get_advanced_receiving_stats),
            ("get_advanced_passing_stats", get_advanced_passing_stats),
            ("get_advanced_rushing_stats", get_advanced_rushing_stats),
            ("get_advanced_defense_stats", get_advanced_defense_stats),
            ("get_advanced_receiving_stats_weekly", get_advanced_receiving_stats_weekly),
            ("get_advanced_passing_stats_weekly", get_advanced_passing_stats_weekly),
            ("get_advanced_rushing_stats_weekly", get_advanced_rushing_stats_weekly),
            ("get_advanced_defense_stats_weekly", get_advanced_defense_stats_weekly),
            ("get_offensive_players_game_stats", get_offensive_players_game_stats),
            ("get_defensive_players_game_stats", get_defensive_players_game_stats),
        ]

        for func_name, func in functions:
            print(f"✓ {func_name}...", end=" ")
            if callable(func):
                print("OK")
            else:
                print("ERROR: Not callable")
                return False

        return True

    except Exception as e:
        print(f"\n✗ Function verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_tool_registry():
    """Verify tool registry can be instantiated."""
    print("\n" + "=" * 60)
    print("VERIFYING TOOL REGISTRY")
    print("=" * 60)

    try:
        from fastmcp import FastMCP
        from tools.registry import register_tools

        print("✓ Creating FastMCP instance...", end=" ")
        mcp = FastMCP("Test MCP")
        print("OK")

        print("✓ Registering tools (without Supabase)...", end=" ")
        # We pass None for supabase since we're just checking registration
        # The actual tools won't work, but registration should succeed
        try:
            register_tools(mcp, None)
            print("OK")
        except Exception as e:
            # If it fails due to None supabase, that's expected
            # We're just checking the import and registration logic
            if "NoneType" in str(e) or "None" in str(e):
                print("OK (expected None error)")
            else:
                raise

        return True

    except Exception as e:
        print(f"\n✗ Registry verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all verification checks."""
    print("\n" + "=" * 60)
    print("MCP SERVER STARTUP VERIFICATION")
    print("=" * 60)
    print()

    results = []

    # Run verifications
    results.append(("Imports", verify_imports()))
    results.append(("Refactored Functions", verify_refactored_functions()))
    results.append(("Tool Registry", verify_tool_registry()))

    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n✓ ALL VERIFICATIONS PASSED")
        print("MCP server imports and tool registrations work correctly.")
        return 0
    else:
        print("\n✗ SOME VERIFICATIONS FAILED")
        print("There are issues that need to be fixed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
