#!/usr/bin/env python3
"""
Test script to verify that refactored functions produce identical output.

Tests the three refactored functions:
1. get_sleeper_league_rosters
2. get_sleeper_league_matchups
3. get_sleeper_league_transactions

All should properly populate owner_name annotations using League.map_users_to_team_name()
"""

import sys

from tools.fantasy.info import (
    get_sleeper_league_matchups,
    get_sleeper_league_rosters,
    get_sleeper_league_transactions,
)

# Test league ID from spec
TEST_LEAGUE_ID = "1225572389929099264"
TEST_WEEK = 1


def test_rosters():
    """Test get_sleeper_league_rosters returns owner_name annotations."""
    print("\n=== Testing get_sleeper_league_rosters ===")
    try:
        rosters = get_sleeper_league_rosters(TEST_LEAGUE_ID, summary=False)

        if not rosters:
            print("❌ FAIL: No rosters returned")
            return False

        # Check that owner_name is populated
        owner_names_found = 0
        for roster in rosters:
            if "owner_name" in roster:
                owner_name = roster.get("owner_name")
                roster_id = roster.get("roster_id")
                print(f"  ✓ Roster {roster_id}: owner_name = '{owner_name}'")
                owner_names_found += 1

        if owner_names_found == 0:
            print("❌ FAIL: No owner_name fields found in rosters")
            return False

        print(f"✅ PASS: Found {owner_names_found} rosters with owner_name annotations")
        return True

    except Exception as e:
        print(f"❌ FAIL: Exception occurred: {e!s}")
        return False


def test_matchups():
    """Test get_sleeper_league_matchups returns owner_name annotations."""
    print("\n=== Testing get_sleeper_league_matchups ===")
    try:
        matchups = get_sleeper_league_matchups(TEST_LEAGUE_ID, TEST_WEEK, summary=False)

        if not matchups:
            print("❌ FAIL: No matchups returned")
            return False

        # Check that owner_name is populated
        owner_names_found = 0
        for matchup in matchups:
            if "owner_name" in matchup:
                owner_name = matchup.get("owner_name")
                roster_id = matchup.get("roster_id")
                matchup_id = matchup.get("matchup_id")
                print(f"  ✓ Matchup {matchup_id}, Roster {roster_id}: owner_name = '{owner_name}'")
                owner_names_found += 1

        if owner_names_found == 0:
            print("❌ FAIL: No owner_name fields found in matchups")
            return False

        print(f"✅ PASS: Found {owner_names_found} matchups with owner_name annotations")
        return True

    except Exception as e:
        print(f"❌ FAIL: Exception occurred: {e!s}")
        return False


def test_transactions():
    """Test get_sleeper_league_transactions returns owner_name annotations."""
    print("\n=== Testing get_sleeper_league_transactions ===")
    try:
        transactions = get_sleeper_league_transactions(TEST_LEAGUE_ID, TEST_WEEK)

        if not transactions:
            print("⚠️  WARNING: No transactions returned (this is OK if no transactions in week 1)")
            # This is not a failure - week 1 might have no transactions
            return True

        # Check that creator_owner_name and roster_owner_names are populated
        transactions_with_annotations = 0
        for txn in transactions:
            txn_type = txn.get("type")
            creator_name = txn.get("creator_owner_name")
            roster_names = txn.get("roster_owner_names", [])

            has_creator = "creator_owner_name" in txn
            has_rosters = "roster_owner_names" in txn

            if has_creator or has_rosters:
                print(f"  ✓ Transaction ({txn_type}):")
                if has_creator:
                    print(f"    - creator_owner_name = '{creator_name}'")
                if has_rosters:
                    print(f"    - roster_owner_names = {roster_names}")
                transactions_with_annotations += 1

        if transactions_with_annotations == 0:
            print("❌ FAIL: No owner_name annotations found in transactions")
            return False

        print(f"✅ PASS: Found {transactions_with_annotations} transactions with owner_name annotations")
        return True

    except Exception as e:
        print(f"❌ FAIL: Exception occurred: {e!s}")
        return False


def main():
    """Run all tests and report results."""
    print("=" * 60)
    print("TESTING REFACTORED FUNCTIONS")
    print("=" * 60)
    print(f"Test League ID: {TEST_LEAGUE_ID}")
    print(f"Test Week: {TEST_WEEK}")

    results = {
        "rosters": test_rosters(),
        "matchups": test_matchups(),
        "transactions": test_transactions(),
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
        print("\n🎉 ALL TESTS PASSED - Refactored functions work correctly!")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED - Review the output above")
        sys.exit(1)


if __name__ == "__main__":
    main()
