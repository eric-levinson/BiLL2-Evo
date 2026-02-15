"""
Tests for _resolve_player_ids batching and caching fix.

Verifies:
1. Empty ID lists return []
2. Non-numeric IDs (team defenses) get DEF fallback
3. IDs not found in the database get a fallback entry
4. Batching splits large lists into chunks of 50
5. Cache prevents redundant Supabase queries
6. Result order matches input order
"""

import os
import sys
import time
from unittest.mock import MagicMock

# Add parent directory to path so we can import from fantasy-tools-mcp root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools.fantasy.info import (
    _player_cache,
    _player_cache_lock,
    _resolve_player_ids,
)


def _clear_cache():
    """Clear the module-level cache between tests."""
    with _player_cache_lock:
        _player_cache.clear()


def _mock_supabase(db_rows: list[dict]) -> MagicMock:
    """Create a mock Supabase client that returns the given rows."""
    mock = MagicMock()
    response = MagicMock()
    response.data = db_rows

    mock.table.return_value.select.return_value.in_.return_value.execute.return_value = response
    return mock


def test_empty_list():
    """Empty input returns empty output without hitting Supabase."""
    print("\nTEST 1: Empty ID list")
    _clear_cache()

    mock_sb = _mock_supabase([])
    result = _resolve_player_ids(mock_sb, [])

    assert result == [], f"Expected [], got {result}"
    mock_sb.table.assert_not_called()
    print("  PASSED: Returns [] and does not call Supabase")
    return True


def test_non_numeric_ids():
    """Non-numeric IDs (team defenses) get DEF fallback without Supabase query."""
    print("\nTEST 2: Non-numeric IDs (team defenses)")
    _clear_cache()

    mock_sb = _mock_supabase([])
    result = _resolve_player_ids(mock_sb, ["HOU", "DAL", "KC"])

    assert len(result) == 3, f"Expected 3 results, got {len(result)}"
    for i, team in enumerate(["HOU", "DAL", "KC"]):
        assert result[i]["name"] == team, f"Expected name={team}, got {result[i]['name']}"
        assert result[i]["position"] == "DEF", f"Expected position=DEF, got {result[i]['position']}"
        assert result[i]["team"] == team, f"Expected team={team}, got {result[i]['team']}"

    # No numeric IDs, so Supabase should not be queried
    mock_sb.table.assert_not_called()
    print("  PASSED: Non-numeric IDs return DEF fallback, no Supabase call")
    return True


def test_ids_not_found():
    """Numeric IDs not in the database get a fallback entry."""
    print("\nTEST 3: IDs not found in database")
    _clear_cache()

    # Supabase returns empty — none of the IDs exist
    mock_sb = _mock_supabase([])
    result = _resolve_player_ids(mock_sb, ["99999", "88888"])

    assert len(result) == 2
    for i, pid in enumerate(["99999", "88888"]):
        assert result[i]["name"] == pid, f"Expected name={pid}, got {result[i]['name']}"
        assert result[i]["position"] == "", f"Expected empty position, got {result[i]['position']}"
        assert result[i]["team"] == "", f"Expected empty team, got {result[i]['team']}"

    print("  PASSED: Not-found IDs return fallback entries")
    return True


def test_mixed_ids():
    """Mixed numeric + non-numeric IDs are handled correctly."""
    print("\nTEST 4: Mixed numeric and non-numeric IDs")
    _clear_cache()

    db_rows = [
        {"sleeper_id": 1234, "display_name": "Patrick Mahomes", "latest_team": "KC", "position": "QB"},
    ]
    mock_sb = _mock_supabase(db_rows)
    result = _resolve_player_ids(mock_sb, ["1234", "HOU", "9999"])

    assert len(result) == 3
    assert result[0]["name"] == "Patrick Mahomes"
    assert result[0]["position"] == "QB"
    assert result[0]["team"] == "KC"
    assert result[1]["name"] == "HOU"
    assert result[1]["position"] == "DEF"
    assert result[2]["name"] == "9999"  # not found fallback
    assert result[2]["position"] == ""

    print("  PASSED: Mixed IDs resolved correctly in order")
    return True


def test_batching():
    """Large ID lists are split into batches of 100."""
    print("\nTEST 5: Batching into chunks of 100")
    _clear_cache()

    # 250 IDs should produce 3 batches: 100, 100, 50
    all_ids = [str(i) for i in range(1, 251)]

    # Track in_() calls to verify batching
    call_batches = []

    def capture_in(column, ids):
        call_batches.append(ids)
        response = MagicMock()
        response.data = [
            {"sleeper_id": pid, "display_name": f"Player {pid}", "latest_team": "TST", "position": "WR"} for pid in ids
        ]
        execute_mock = MagicMock()
        execute_mock.execute.return_value = response
        return execute_mock

    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value.in_ = capture_in

    result = _resolve_player_ids(mock_sb, all_ids)

    assert len(result) == 250, f"Expected 250 results, got {len(result)}"

    # Verify batches are <= 100
    for i, batch in enumerate(call_batches):
        assert len(batch) <= 100, f"Batch {i} has {len(batch)} items, expected <= 100"
    assert len(call_batches) == 3, f"Expected 3 batches, got {len(call_batches)}"

    # Verify sizes: 100, 100, 50
    sizes = sorted([len(b) for b in call_batches], reverse=True)
    assert sizes == [100, 100, 50], f"Expected batch sizes [100, 100, 50], got {sizes}"

    print(f"  PASSED: {len(call_batches)} batches with sizes {sizes}")
    return True


def test_cache_prevents_redundant_queries():
    """Cached IDs are not re-queried from Supabase."""
    print("\nTEST 6: Cache prevents redundant queries")
    _clear_cache()

    db_rows = [
        {"sleeper_id": 100, "display_name": "Player 100", "latest_team": "NYG", "position": "RB"},
        {"sleeper_id": 200, "display_name": "Player 200", "latest_team": "LAR", "position": "WR"},
    ]
    mock_sb = _mock_supabase(db_rows)

    # First call — should query Supabase
    result1 = _resolve_player_ids(mock_sb, ["100", "200"])
    assert len(result1) == 2
    assert result1[0]["name"] == "Player 100"
    first_call_count = mock_sb.table.call_count

    # Second call with same IDs — should use cache, no new Supabase query
    result2 = _resolve_player_ids(mock_sb, ["100", "200"])
    assert len(result2) == 2
    assert result2[0]["name"] == "Player 100"
    assert mock_sb.table.call_count == first_call_count, (
        f"Expected no new Supabase calls, but call count went from {first_call_count} to {mock_sb.table.call_count}"
    )

    print("  PASSED: Second call uses cache, no new Supabase queries")
    return True


def test_cache_ttl_expiry():
    """Expired cache entries trigger a re-query."""
    print("\nTEST 7: Cache TTL expiry")
    _clear_cache()

    # Manually insert an expired cache entry
    expired_time = time.monotonic() - 999  # well past TTL
    with _player_cache_lock:
        _player_cache["555"] = ({"name": "Old Name", "position": "QB", "team": "OLD"}, expired_time)

    db_rows = [
        {"sleeper_id": 555, "display_name": "New Name", "latest_team": "NEW", "position": "QB"},
    ]
    mock_sb = _mock_supabase(db_rows)

    result = _resolve_player_ids(mock_sb, ["555"])
    assert result[0]["name"] == "New Name", f"Expected 'New Name', got {result[0]['name']}"
    assert mock_sb.table.call_count > 0, "Expected Supabase to be called for expired entry"

    print("  PASSED: Expired cache entry triggers re-query")
    return True


def test_result_order_preserved():
    """Output order matches input order regardless of DB return order."""
    print("\nTEST 8: Result order matches input order")
    _clear_cache()

    # DB returns rows in reverse order
    db_rows = [
        {"sleeper_id": 333, "display_name": "Player C", "latest_team": "C", "position": "TE"},
        {"sleeper_id": 111, "display_name": "Player A", "latest_team": "A", "position": "QB"},
        {"sleeper_id": 222, "display_name": "Player B", "latest_team": "B", "position": "WR"},
    ]
    mock_sb = _mock_supabase(db_rows)

    result = _resolve_player_ids(mock_sb, ["111", "222", "333"])

    assert result[0]["name"] == "Player A"
    assert result[1]["name"] == "Player B"
    assert result[2]["name"] == "Player C"

    print("  PASSED: Output order matches input order")
    return True


def test_duplicate_ids():
    """Duplicate IDs in input produce correct results with only one query per unique ID."""
    print("\nTEST 9: Duplicate IDs")
    _clear_cache()

    db_rows = [
        {"sleeper_id": 42, "display_name": "Player 42", "latest_team": "SF", "position": "RB"},
    ]
    mock_sb = _mock_supabase(db_rows)

    result = _resolve_player_ids(mock_sb, ["42", "42", "42"])

    assert len(result) == 3
    for r in result:
        assert r["name"] == "Player 42"

    print("  PASSED: Duplicate IDs handled correctly")
    return True


def run_all_tests():
    """Run all tests and report results."""
    print("=" * 70)
    print("_resolve_player_ids BATCHING + CACHING TEST SUITE")
    print("=" * 70)

    tests = [
        ("Empty list", test_empty_list),
        ("Non-numeric IDs", test_non_numeric_ids),
        ("IDs not found", test_ids_not_found),
        ("Mixed IDs", test_mixed_ids),
        ("Batching (chunks of 50)", test_batching),
        ("Cache prevents re-queries", test_cache_prevents_redundant_queries),
        ("Cache TTL expiry", test_cache_ttl_expiry),
        ("Result order preserved", test_result_order_preserved),
        ("Duplicate IDs", test_duplicate_ids),
    ]

    results = []
    for name, test_fn in tests:
        try:
            passed = test_fn()
            results.append((name, passed))
        except Exception as e:
            print(f"  FAILED with exception: {e}")
            results.append((name, False))

    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {status}: {name}")

    print(f"\nRESULTS: {passed}/{total} tests passed")

    if passed == total:
        print("\nAll edge cases verified for _resolve_player_ids fix.")
        return 0
    else:
        print(f"\n{total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
