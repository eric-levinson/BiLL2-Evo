#!/usr/bin/env python3
"""
Comprehensive test script for get_metrics_metadata() function.
Tests all valid categories, subcategories, and error handling.
"""

import sys

from tools.metrics.info import get_metrics_metadata


def test_category_subcategory(category: str, subcategory: str, test_name: str) -> bool:
    """Test a specific category/subcategory combination."""
    try:
        result = get_metrics_metadata(category, subcategory)

        # Verify result is a dict
        if not isinstance(result, dict):
            print(f"❌ {test_name}: Expected dict, got {type(result)}")
            return False

        # Verify subcategory exists in result
        if subcategory not in result:
            print(f"❌ {test_name}: Subcategory '{subcategory}' not in result")
            return False

        # Verify the subcategory has expected structure
        subcategory_data = result[subcategory]
        if not isinstance(subcategory_data, dict):
            print(f"❌ {test_name}: Subcategory data is not a dict")
            return False

        # Verify 'fields' key exists (or description for empty subcategories)
        if "fields" not in subcategory_data and "description" not in subcategory_data:
            print(f"❌ {test_name}: Subcategory missing 'fields' and 'description' keys")
            return False

        print(f"✅ {test_name}")
        return True
    except Exception as e:
        print(f"❌ {test_name}: {e}")
        return False


def test_full_category(category: str, test_name: str) -> bool:
    """Test fetching a full category (subcategory=None)."""
    try:
        result = get_metrics_metadata(category, None)

        # Verify result is a dict
        if not isinstance(result, dict):
            print(f"❌ {test_name}: Expected dict, got {type(result)}")
            return False

        # Verify it has multiple subcategories
        if len(result) < 1:
            print(f"❌ {test_name}: Category has no subcategories")
            return False

        # Verify all subcategories are dicts
        for subcat_name, subcat_data in result.items():
            if not isinstance(subcat_data, dict):
                print(f"❌ {test_name}: Subcategory '{subcat_name}' is not a dict")
                return False

        print(f"✅ {test_name} ({len(result)} subcategories)")
        return True
    except Exception as e:
        print(f"❌ {test_name}: {e}")
        return False


def test_invalid_category(category: str, test_name: str) -> bool:
    """Test that invalid category raises ValueError."""
    try:
        result = get_metrics_metadata(category, None)
        print(f"❌ {test_name}: Should have raised ValueError but returned {result}")
        return False
    except ValueError as e:
        if "Unknown category" in str(e):
            print(f"✅ {test_name}: Correctly raised ValueError")
            return True
        else:
            print(f"❌ {test_name}: Wrong error message: {e}")
            return False
    except Exception as e:
        print(f"❌ {test_name}: Wrong exception type: {e}")
        return False


def test_invalid_subcategory(category: str, subcategory: str, test_name: str) -> bool:
    """Test that invalid subcategory returns empty dict for that subcategory."""
    try:
        result = get_metrics_metadata(category, subcategory)

        # According to the code, invalid subcategory returns {subcategory: {}}
        if not isinstance(result, dict):
            print(f"❌ {test_name}: Expected dict, got {type(result)}")
            return False

        if subcategory not in result:
            print(f"❌ {test_name}: Subcategory key not in result")
            return False

        if result[subcategory] != {}:
            print(f"❌ {test_name}: Expected empty dict for invalid subcategory, got {result[subcategory]}")
            return False

        print(f"✅ {test_name}: Correctly returned empty dict")
        return True
    except Exception as e:
        print(f"❌ {test_name}: {e}")
        return False


def main():
    """Run all test cases."""
    print("=" * 70)
    print("Testing get_metrics_metadata() - All Categories & Subcategories")
    print("=" * 70)

    passed = 0
    failed = 0

    # Define all valid categories and their subcategories
    test_cases = [
        # Receiving tests
        ("receiving", "basic_info", "Receiving: basic_info"),
        ("receiving", "volume_metrics", "Receiving: volume_metrics"),
        ("receiving", "efficiency_metrics", "Receiving: efficiency_metrics"),
        ("receiving", "situational_metrics", "Receiving: situational_metrics"),
        ("receiving", "weekly", "Receiving: weekly"),
        # Passing tests
        ("passing", "basic_info", "Passing: basic_info"),
        ("passing", "volume_metrics", "Passing: volume_metrics"),
        ("passing", "efficiency_metrics", "Passing: efficiency_metrics"),
        ("passing", "situational_metrics", "Passing: situational_metrics"),
        ("passing", "weekly", "Passing: weekly"),
        # Rushing tests
        ("rushing", "basic_info", "Rushing: basic_info"),
        ("rushing", "volume_metrics", "Rushing: volume_metrics"),
        ("rushing", "efficiency_metrics", "Rushing: efficiency_metrics"),
        ("rushing", "situational_metrics", "Rushing: situational_metrics"),
        ("rushing", "weekly", "Rushing: weekly"),
        # Defense tests
        ("defense", "basic_info", "Defense: basic_info"),
        ("defense", "volume_metrics", "Defense: volume_metrics"),
        ("defense", "efficiency_metrics", "Defense: efficiency_metrics"),
        ("defense", "situational_metrics", "Defense: situational_metrics"),
        ("defense", "weekly", "Defense: weekly"),
    ]

    print("\n--- Testing Valid Category/Subcategory Combinations ---")
    for category, subcategory, test_name in test_cases:
        if test_category_subcategory(category, subcategory, test_name):
            passed += 1
        else:
            failed += 1

    # Test full category retrieval (subcategory=None)
    print("\n--- Testing Full Category Retrieval (subcategory=None) ---")
    full_category_tests = [
        ("receiving", "Receiving: full category"),
        ("passing", "Passing: full category"),
        ("rushing", "Rushing: full category"),
        ("defense", "Defense: full category"),
    ]

    for category, test_name in full_category_tests:
        if test_full_category(category, test_name):
            passed += 1
        else:
            failed += 1

    # Test invalid categories
    print("\n--- Testing Invalid Category Error Handling ---")
    invalid_category_tests = [
        ("invalid_category", "Invalid category: 'invalid_category'"),
        ("special_teams", "Invalid category: 'special_teams'"),
        ("", "Invalid category: empty string"),
    ]

    for category, test_name in invalid_category_tests:
        if test_invalid_category(category, test_name):
            passed += 1
        else:
            failed += 1

    # Test invalid subcategories
    print("\n--- Testing Invalid Subcategory Handling ---")
    invalid_subcategory_tests = [
        ("receiving", "invalid_subcat", "Receiving: invalid subcategory"),
        ("passing", "nonexistent", "Passing: nonexistent subcategory"),
        ("rushing", "bad_metric_type", "Rushing: bad_metric_type subcategory"),
    ]

    for category, subcategory, test_name in invalid_subcategory_tests:
        if test_invalid_subcategory(category, subcategory, test_name):
            passed += 1
        else:
            failed += 1

    # Print summary
    print("\n" + "=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed out of {passed + failed} tests")
    print("=" * 70)

    if failed > 0:
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
