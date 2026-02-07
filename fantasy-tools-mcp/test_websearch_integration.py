"""
Integration test for web search tool.
This script verifies the search_web function works correctly with Tavily API.
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.websearch.info import search_web


def test_web_search_basic():
    """Test basic web search functionality"""
    print("=" * 60)
    print("TEST 1: Basic Web Search - Patrick Mahomes News")
    print("=" * 60)

    query = "Patrick Mahomes latest news NFL 2026"
    print(f"\nQuery: {query}")

    result = search_web(query, max_results=3)

    if "error" in result:
        print(f"\n❌ FAILED: {result['error']}")
        return False

    print(f"\n✅ SUCCESS: Found {len(result.get('results', []))} results")

    for i, item in enumerate(result.get('results', []), 1):
        print(f"\n  Result {i}:")
        print(f"    Title: {item.get('title', 'N/A')}")
        print(f"    URL: {item.get('url', 'N/A')}")
        print(f"    Snippet: {item.get('snippet', 'N/A')[:100]}...")

    # Verify structure
    assert 'results' in result, "Missing 'results' key"
    assert len(result['results']) > 0, "No results returned"

    for item in result['results']:
        assert 'title' in item, "Missing 'title' in result"
        assert 'url' in item, "Missing 'url' in result"
        assert 'snippet' in item, "Missing 'snippet' in result"

    return True


def test_web_search_injury():
    """Test web search for injury status"""
    print("\n" + "=" * 60)
    print("TEST 2: Injury Status Search - Christian McCaffrey")
    print("=" * 60)

    query = "Christian McCaffrey CMC injury status 2026"
    print(f"\nQuery: {query}")

    result = search_web(query, max_results=5)

    if "error" in result:
        print(f"\n❌ FAILED: {result['error']}")
        return False

    print(f"\n✅ SUCCESS: Found {len(result.get('results', []))} results")

    for i, item in enumerate(result.get('results', []), 1):
        print(f"\n  Result {i}:")
        print(f"    Title: {item.get('title', 'N/A')}")
        print(f"    URL: {item.get('url', 'N/A')}")
        snippet = item.get('snippet', 'N/A')
        print(f"    Snippet: {snippet[:150]}...")

    return True


def test_api_key_validation():
    """Test that API key is configured"""
    print("\n" + "=" * 60)
    print("TEST 3: API Key Configuration")
    print("=" * 60)

    api_key = os.getenv("TAVILY_API_KEY")

    if not api_key:
        print("\n❌ FAILED: TAVILY_API_KEY not set in .env")
        return False

    if api_key.startswith("tvly-"):
        print(f"\n✅ SUCCESS: API key is configured (starts with 'tvly-')")
        return True
    else:
        print(f"\n⚠️  WARNING: API key format unexpected (doesn't start with 'tvly-')")
        return True


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("WEB SEARCH INTEGRATION TEST")
    print("=" * 60)

    tests = [
        ("API Key Configuration", test_api_key_validation),
        ("Basic Web Search", test_web_search_basic),
        ("Injury Status Search", test_web_search_injury),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n❌ EXCEPTION in {test_name}: {str(e)}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"TEST SUMMARY: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed == 0:
        print("\n✅ ALL TESTS PASSED - Web search integration is working!")
        sys.exit(0)
    else:
        print(f"\n❌ {failed} TEST(S) FAILED - Please review errors above")
        sys.exit(1)
