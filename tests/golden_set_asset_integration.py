"""
Golden Set Test Cases for Asset-Service Integration

This module contains 20 carefully designed test cases to validate
the asset-service integration with the AI-BRAIN.

Test Distribution:
- 5 exact match queries (direct server lookups)
- 5 fuzzy/filtered queries (list/filter operations)
- 5 multi-match scenarios (disambiguation testing)
- 5 error paths / should NOT select (negative cases)

Usage:
    python -m pytest tests/golden_set_asset_integration.py -v
    
    Or run the golden set directly:
    python tests/golden_set_asset_integration.py
"""

from typing import NamedTuple, Set
from enum import Enum


class QueryMode(str, Enum):
    """Expected query mode for asset-service."""
    SEARCH = "search"
    FILTER = "filter"
    GET_BY_ID = "get_by_id"
    NONE = ""  # Should not select asset-service


class GoldenCase(NamedTuple):
    """
    Golden set test case for asset-service integration.
    
    Attributes:
        text: User query text
        should_select_tool: Whether asset-service-query should be selected
        expected_mode: Expected query mode (search/filter/get_by_id)
        expect_keys: Expected fields in response
        description: Human-readable description of test case
        expected_score: Expected selection score (0.0-1.0)
        category: Test category for reporting
    """
    text: str
    should_select_tool: bool
    expected_mode: str
    expect_keys: Set[str]
    description: str
    expected_score: float = 0.0
    category: str = "general"


# =============================================================================
# GOLDEN SET: 20 Test Cases
# =============================================================================

GOLDEN_SET = [
    # =========================================================================
    # Category 1: Exact Match Queries (5 cases)
    # These should have high selection scores (0.8-1.0)
    # =========================================================================
    
    GoldenCase(
        text="What's the IP of web-prod-01?",
        should_select_tool=True,
        expected_mode=QueryMode.SEARCH,
        expect_keys={"ip_address"},
        description="Direct server IP lookup",
        expected_score=1.0,
        category="exact_match"
    ),
    
    GoldenCase(
        text="Show me details for server db-prod-01",
        should_select_tool=True,
        expected_mode=QueryMode.SEARCH,
        expect_keys={"hostname", "ip_address", "environment"},
        description="Server details query",
        expected_score=1.0,
        category="exact_match"
    ),
    
    GoldenCase(
        text="Get the hostname of 10.0.1.50",
        should_select_tool=True,
        expected_mode=QueryMode.SEARCH,
        expect_keys={"hostname"},
        description="Reverse IP lookup",
        expected_score=1.0,
        category="exact_match"
    ),
    
    GoldenCase(
        text="What environment is api-staging-02 in?",
        should_select_tool=True,
        expected_mode=QueryMode.SEARCH,
        expect_keys={"environment"},
        description="Environment lookup",
        expected_score=1.0,
        category="exact_match"
    ),
    
    GoldenCase(
        text="Is server web-prod-01 active?",
        should_select_tool=True,
        expected_mode=QueryMode.SEARCH,
        expect_keys={"status", "is_active"},
        description="Status check",
        expected_score=1.0,
        category="exact_match"
    ),
    
    # =========================================================================
    # Category 2: Fuzzy/Filtered Queries (5 cases)
    # These should have medium-high selection scores (0.6-0.8)
    # =========================================================================
    
    GoldenCase(
        text="List all production Linux servers",
        should_select_tool=True,
        expected_mode=QueryMode.FILTER,
        expect_keys={"hostname", "environment", "os_type"},
        description="Filtered list query",
        expected_score=0.8,
        category="filtered"
    ),
    
    GoldenCase(
        text="Show me database servers in staging",
        should_select_tool=True,
        expected_mode=QueryMode.FILTER,
        expect_keys={"hostname", "service_type", "environment"},
        description="Service + environment filter",
        expected_score=0.8,
        category="filtered"
    ),
    
    GoldenCase(
        text="Find all inactive servers",
        should_select_tool=True,
        expected_mode=QueryMode.FILTER,
        expect_keys={"hostname", "is_active"},
        description="Status filter",
        expected_score=0.8,
        category="filtered"
    ),
    
    GoldenCase(
        text="What servers are running Ubuntu?",
        should_select_tool=True,
        expected_mode=QueryMode.FILTER,
        expect_keys={"hostname", "os_type"},
        description="OS filter",
        expected_score=0.8,
        category="filtered"
    ),
    
    GoldenCase(
        text="List all web servers",
        should_select_tool=True,
        expected_mode=QueryMode.FILTER,
        expect_keys={"hostname", "service_type"},
        description="Service type filter",
        expected_score=0.8,
        category="filtered"
    ),
    
    # =========================================================================
    # Category 3: Multi-Match Scenarios (5 cases)
    # These test disambiguation logic
    # =========================================================================
    
    GoldenCase(
        text="Show me all prod servers",
        should_select_tool=True,
        expected_mode=QueryMode.FILTER,
        expect_keys={"hostname", "environment"},
        description="Broad query - many results",
        expected_score=0.8,
        category="multi_match"
    ),
    
    GoldenCase(
        text="Find servers with 'web' in the name",
        should_select_tool=True,
        expected_mode=QueryMode.SEARCH,
        expect_keys={"hostname"},
        description="Partial name match",
        expected_score=0.8,
        category="multi_match"
    ),
    
    GoldenCase(
        text="What servers are in datacenter-1?",
        should_select_tool=True,
        expected_mode=QueryMode.FILTER,
        expect_keys={"hostname", "location"},
        description="Location-based query",
        expected_score=0.8,
        category="multi_match"
    ),
    
    GoldenCase(
        text="Show all servers",
        should_select_tool=True,
        expected_mode=QueryMode.FILTER,
        expect_keys={"hostname"},
        description="Very broad query",
        expected_score=0.5,
        category="multi_match"
    ),
    
    GoldenCase(
        text="List production databases",
        should_select_tool=True,
        expected_mode=QueryMode.FILTER,
        expect_keys={"hostname", "environment", "service_type"},
        description="Combined filter",
        expected_score=0.8,
        category="multi_match"
    ),
    
    # =========================================================================
    # Category 4: Error Paths / Should NOT Select (5 cases)
    # These should have low selection scores (<0.4)
    # =========================================================================
    
    GoldenCase(
        text="How do I center a div in CSS?",
        should_select_tool=False,
        expected_mode=QueryMode.NONE,
        expect_keys=set(),
        description="Unrelated question",
        expected_score=0.2,
        category="negative"
    ),
    
    GoldenCase(
        text="What's the weather today?",
        should_select_tool=False,
        expected_mode=QueryMode.NONE,
        expect_keys=set(),
        description="Non-infrastructure query",
        expected_score=0.2,
        category="negative"
    ),
    
    GoldenCase(
        text="Explain the service mesh architecture",
        should_select_tool=False,
        expected_mode=QueryMode.NONE,
        expect_keys=set(),
        description="'service' in business context",
        expected_score=0.3,
        category="negative"
    ),
    
    GoldenCase(
        text="Calculate 2 + 2",
        should_select_tool=False,
        expected_mode=QueryMode.NONE,
        expect_keys=set(),
        description="Math question",
        expected_score=0.2,
        category="negative"
    ),
    
    GoldenCase(
        text="What's the pricing for our cloud service?",
        should_select_tool=False,
        expected_mode=QueryMode.NONE,
        expect_keys=set(),
        description="Business/pricing question",
        expected_score=0.2,
        category="negative"
    ),
]


# =============================================================================
# Test Runner
# =============================================================================

def run_golden_set(eval_fn):
    """
    Run golden set evaluation.
    
    Args:
        eval_fn: Function that takes a GoldenCase and returns (passed, detail)
                 Signature: eval_fn(case: GoldenCase) -> Tuple[bool, str]
    
    Returns:
        List of (case_num, passed, detail) tuples
    """
    results = []
    category_stats = {}
    
    print("=" * 80)
    print("GOLDEN SET EVALUATION: Asset-Service Integration")
    print("=" * 80)
    print()
    
    for i, case in enumerate(GOLDEN_SET, 1):
        passed, detail = eval_fn(case)
        results.append((i, passed, detail))
        
        # Track category stats
        if case.category not in category_stats:
            category_stats[case.category] = {"total": 0, "passed": 0}
        category_stats[case.category]["total"] += 1
        if passed:
            category_stats[case.category]["passed"] += 1
        
        # Print result
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"Case {i:2d}: {status} - {case.description}")
        print(f"         Query: \"{case.text}\"")
        print(f"         Category: {case.category}")
        print(f"         Expected Score: {case.expected_score}")
        if not passed:
            print(f"         ❌ Detail: {detail}")
        print()
    
    # Print summary
    total = len(results)
    passed_count = sum(1 for _, p, _ in results if p)
    failed_count = total - passed_count
    pass_rate = (100 * passed_count // total) if total > 0 else 0
    
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total Cases:  {total}")
    print(f"Passed:       {passed_count} ({pass_rate}%)")
    print(f"Failed:       {failed_count}")
    print()
    
    # Print category breakdown
    print("CATEGORY BREAKDOWN:")
    print("-" * 80)
    for category, stats in sorted(category_stats.items()):
        cat_pass_rate = (100 * stats["passed"] // stats["total"]) if stats["total"] > 0 else 0
        print(f"  {category:15s}: {stats['passed']:2d}/{stats['total']:2d} passed ({cat_pass_rate:3d}%)")
    print()
    
    # Print target vs actual
    print("TARGET: ≥ 90% pass rate (18/20 cases)")
    if pass_rate >= 90:
        print("✅ TARGET MET!")
    else:
        print(f"❌ TARGET NOT MET (need {18 - passed_count} more passing cases)")
    print("=" * 80)
    
    return results


def get_category_cases(category: str):
    """Get all test cases for a specific category."""
    return [case for case in GOLDEN_SET if case.category == category]


def get_case_by_index(index: int):
    """Get a specific test case by index (1-based)."""
    if 1 <= index <= len(GOLDEN_SET):
        return GOLDEN_SET[index - 1]
    return None


# =============================================================================
# Example Evaluation Function (for testing)
# =============================================================================

def dummy_eval(case: GoldenCase):
    """
    Dummy evaluation function for testing the golden set runner.
    
    Replace this with actual evaluation logic that:
    1. Runs the query through the AI-BRAIN pipeline
    2. Checks if asset-service-query was selected
    3. Validates the selection score
    4. Verifies the query mode and expected fields
    
    Returns:
        Tuple[bool, str]: (passed, detail_message)
    """
    # This is just a placeholder - replace with real evaluation
    import random
    passed = random.choice([True, True, True, False])  # 75% pass rate for demo
    detail = "Not implemented - replace with actual evaluation" if not passed else ""
    return (passed, detail)


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    print("Golden Set Test Cases for Asset-Service Integration")
    print()
    print(f"Total test cases: {len(GOLDEN_SET)}")
    print()
    
    # Print category distribution
    categories = {}
    for case in GOLDEN_SET:
        categories[case.category] = categories.get(case.category, 0) + 1
    
    print("Category Distribution:")
    for category, count in sorted(categories.items()):
        print(f"  - {category:15s}: {count} cases")
    print()
    
    # Run with dummy evaluation
    print("Running golden set with dummy evaluation...")
    print("(Replace dummy_eval with actual evaluation function)")
    print()
    
    results = run_golden_set(dummy_eval)
    
    print()
    print("To use this golden set in your tests:")
    print("  1. Import: from tests.golden_set_asset_integration import GOLDEN_SET, run_golden_set")
    print("  2. Create your evaluation function")
    print("  3. Run: results = run_golden_set(your_eval_function)")