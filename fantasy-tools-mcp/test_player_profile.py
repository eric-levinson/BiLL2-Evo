#!/usr/bin/env python3
"""
Test script to verify get_player_profile function works correctly.

Tests the unified player profile tool with different player types:
1. WR/TE (should have receiving stats)
2. QB (should have passing + rushing stats)
3. RB (should have rushing + receiving stats)
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client
from tools.player.info import get_player_profile

# Load environment variables from the main monorepo's fantasy-tools-mcp directory
# This handles both worktree and main repo contexts
current_dir = Path(__file__).parent
possible_env_paths = [
    current_dir / ".env",  # Current directory (for main repo)
    current_dir.parent.parent.parent.parent.parent / "fantasy-tools-mcp" / ".env",  # Worktree context
]

env_loaded = False
for env_path in possible_env_paths:
    if env_path.exists():
        load_dotenv(env_path)
        env_loaded = True
        print(f"Loaded environment from: {env_path}")
        break

if not env_loaded:
    print("WARNING: No .env file found. Using system environment variables.")

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


def test_wide_receiver():
    """Test get_player_profile with a WR (Justin Jefferson)."""
    print("\n=== Testing WR: Justin Jefferson ===")
    try:
        result = get_player_profile(
            supabase=supabase,
            player_names=["Justin Jefferson"],
            season_list=[2023, 2024],
            limit=25,
        )

        # Verify response structure
        if not isinstance(result, dict):
            print(f"❌ FAIL: Expected dict, got {type(result)}")
            return False

        required_keys = ["playerInfo", "receivingStats", "passingStats", "rushingStats"]
        for key in required_keys:
            if key not in result:
                print(f"❌ FAIL: Missing key '{key}' in response")
                return False

        # Verify player info is populated
        if not result["playerInfo"]:
            print("❌ FAIL: playerInfo is empty")
            return False

        player = result["playerInfo"][0]
        print(f"  ✓ Player: {player.get('display_name')}")
        print(f"  ✓ Position: {player.get('position')}")
        print(f"  ✓ Team: {player.get('latest_team')}")

        # Verify receiving stats are populated (WR should have receiving stats)
        if result["receivingStats"]:
            print(f"  ✓ Receiving stats: {len(result['receivingStats'])} records")
        else:
            print("  ⚠️  WARNING: No receiving stats found (unexpected for WR)")

        # Passing stats should be empty or minimal for WR
        print(f"  ✓ Passing stats: {len(result['passingStats'])} records (expected 0 for WR)")

        # Rushing stats might be empty for pure WR
        print(f"  ✓ Rushing stats: {len(result['rushingStats'])} records")

        print("✅ PASS: WR test successful")
        return True

    except Exception as e:
        print(f"❌ FAIL: Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_quarterback():
    """Test get_player_profile with a QB (Patrick Mahomes)."""
    print("\n=== Testing QB: Patrick Mahomes ===")
    try:
        result = get_player_profile(
            supabase=supabase,
            player_names=["Patrick Mahomes"],
            season_list=[2023, 2024],
            limit=25,
        )

        # Verify response structure
        if not isinstance(result, dict):
            print(f"❌ FAIL: Expected dict, got {type(result)}")
            return False

        required_keys = ["playerInfo", "receivingStats", "passingStats", "rushingStats"]
        for key in required_keys:
            if key not in result:
                print(f"❌ FAIL: Missing key '{key}' in response")
                return False

        # Verify player info is populated
        if not result["playerInfo"]:
            print("❌ FAIL: playerInfo is empty")
            return False

        player = result["playerInfo"][0]
        print(f"  ✓ Player: {player.get('display_name')}")
        print(f"  ✓ Position: {player.get('position')}")
        print(f"  ✓ Team: {player.get('latest_team')}")

        # Verify passing stats are populated (QB should have passing stats)
        if result["passingStats"]:
            print(f"  ✓ Passing stats: {len(result['passingStats'])} records")
        else:
            print("  ❌ FAIL: No passing stats found (unexpected for QB)")
            return False

        # QBs often have rushing stats
        if result["rushingStats"]:
            print(f"  ✓ Rushing stats: {len(result['rushingStats'])} records")
        else:
            print("  ⚠️  WARNING: No rushing stats found (some QBs don't rush)")

        # Receiving stats should be empty for QB
        print(f"  ✓ Receiving stats: {len(result['receivingStats'])} records (expected 0 for QB)")

        print("✅ PASS: QB test successful")
        return True

    except Exception as e:
        print(f"❌ FAIL: Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_running_back():
    """Test get_player_profile with a RB (Christian McCaffrey)."""
    print("\n=== Testing RB: Christian McCaffrey ===")
    try:
        result = get_player_profile(
            supabase=supabase,
            player_names=["Christian McCaffrey"],
            season_list=[2023, 2024],
            limit=25,
        )

        # Verify response structure
        if not isinstance(result, dict):
            print(f"❌ FAIL: Expected dict, got {type(result)}")
            return False

        required_keys = ["playerInfo", "receivingStats", "passingStats", "rushingStats"]
        for key in required_keys:
            if key not in result:
                print(f"❌ FAIL: Missing key '{key}' in response")
                return False

        # Verify player info is populated
        if not result["playerInfo"]:
            print("❌ FAIL: playerInfo is empty")
            return False

        player = result["playerInfo"][0]
        print(f"  ✓ Player: {player.get('display_name')}")
        print(f"  ✓ Position: {player.get('position')}")
        print(f"  ✓ Team: {player.get('latest_team')}")

        # Verify rushing stats are populated (RB should have rushing stats)
        if result["rushingStats"]:
            print(f"  ✓ Rushing stats: {len(result['rushingStats'])} records")
        else:
            print("  ❌ FAIL: No rushing stats found (unexpected for RB)")
            return False

        # RBs often have receiving stats
        if result["receivingStats"]:
            print(f"  ✓ Receiving stats: {len(result['receivingStats'])} records")
        else:
            print("  ⚠️  WARNING: No receiving stats found (some RBs don't catch)")

        # Passing stats should be empty for RB
        print(f"  ✓ Passing stats: {len(result['passingStats'])} records (expected 0 for RB)")

        print("✅ PASS: RB test successful")
        return True

    except Exception as e:
        print(f"❌ FAIL: Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests and report results."""
    print("=" * 60)
    print("TESTING get_player_profile FUNCTION")
    print("=" * 60)

    results = {
        "Wide Receiver (Justin Jefferson)": test_wide_receiver(),
        "Quarterback (Patrick Mahomes)": test_quarterback(),
        "Running Back (Christian McCaffrey)": test_running_back(),
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
        print("\n🎉 ALL TESTS PASSED - get_player_profile works correctly!")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED - Review the output above")
        sys.exit(1)


if __name__ == "__main__":
    main()
