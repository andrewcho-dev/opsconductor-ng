"""
Smoke tests for Selector v3.

Quick sanity checks that the selector API is working.
"""

import json
import os
import sys
import urllib.request
from urllib.error import HTTPError, URLError


def test_selector_search():
    """Test /api/selector/search endpoint."""
    base_url = os.getenv("SELECTOR_URL", "http://localhost:3003")
    
    test_cases = [
        {
            "name": "Basic search",
            "url": f"{base_url}/api/selector/search?query=network&k=3",
            "expected_fields": ["query", "k", "results", "from_cache", "duration_ms"]
        },
        {
            "name": "Search with platform",
            "url": f"{base_url}/api/selector/search?query=windows%20networking&platform=windows&k=3",
            "expected_fields": ["query", "k", "platforms", "results", "from_cache", "duration_ms"]
        },
        {
            "name": "Search with multiple platforms",
            "url": f"{base_url}/api/selector/search?query=scan&platform=linux&platform=windows&k=5",
            "expected_fields": ["query", "k", "platforms", "results", "from_cache", "duration_ms"]
        }
    ]
    
    for test in test_cases:
        print(f"Testing: {test['name']}")
        try:
            with urllib.request.urlopen(test["url"], timeout=5) as response:
                if response.status != 200:
                    print(f"  ❌ FAIL: Expected 200, got {response.status}")
                    return False
                
                data = json.load(response)
                
                # Check expected fields
                for field in test["expected_fields"]:
                    if field not in data:
                        print(f"  ❌ FAIL: Missing field '{field}'")
                        return False
                
                # Check results is a list
                if not isinstance(data.get("results"), list):
                    print(f"  ❌ FAIL: 'results' is not a list")
                    return False
                
                print(f"  ✅ PASS: {len(data['results'])} results, from_cache={data['from_cache']}")
        
        except HTTPError as e:
            print(f"  ❌ FAIL: HTTP {e.code} - {e.reason}")
            return False
        except URLError as e:
            print(f"  ❌ FAIL: Connection error - {e.reason}")
            return False
        except Exception as e:
            print(f"  ❌ FAIL: {type(e).__name__}: {e}")
            return False
    
    return True


def test_metrics_endpoint():
    """Test /metrics endpoint."""
    base_url = os.getenv("SELECTOR_URL", "http://localhost:3003")
    url = f"{base_url}/metrics"
    
    print("Testing: Metrics endpoint")
    
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            if response.status != 200:
                print(f"  ❌ FAIL: Expected 200, got {response.status}")
                return False
            
            text = response.read().decode("utf-8")
            
            # Check for required metric families
            required_metrics = [
                "selector_requests_total",
                "selector_request_duration_seconds",
                "selector_cache_entries",
                "selector_cache_ttl_seconds",
                "selector_cache_evictions_total",
                "selector_db_errors_total",
                "selector_build_info"
            ]
            
            missing = []
            for metric in required_metrics:
                if metric not in text:
                    missing.append(metric)
            
            if missing:
                print(f"  ❌ FAIL: Missing metrics: {', '.join(missing)}")
                return False
            
            print(f"  ✅ PASS: All required metrics present")
            return True
    
    except HTTPError as e:
        print(f"  ❌ FAIL: HTTP {e.code} - {e.reason}")
        return False
    except URLError as e:
        print(f"  ❌ FAIL: Connection error - {e.reason}")
        return False
    except Exception as e:
        print(f"  ❌ FAIL: {type(e).__name__}: {e}")
        return False


def main():
    """Run all smoke tests."""
    print("=" * 60)
    print("Selector v3 Smoke Tests")
    print("=" * 60)
    
    results = []
    
    # Test selector search
    results.append(("Selector Search", test_selector_search()))
    
    # Test metrics
    results.append(("Metrics Endpoint", test_metrics_endpoint()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} passed")
    
    if passed == total:
        print("\n🎉 All smoke tests passed!")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())