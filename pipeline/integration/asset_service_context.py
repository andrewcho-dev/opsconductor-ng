"""
Asset-Service Context Module

This module provides compact schema information and selection scoring
for the asset-service integration with the AI-BRAIN.

Key Features:
- Compact schema context (~80 tokens)
- Deterministic selection scoring
- Dynamic context injection heuristic
- Infrastructure keyword detection

Expert-validated and production-ready.
"""

from typing import Dict, Any, Set


# =============================================================================
# Asset-Service Schema Definition
# =============================================================================

ASSET_SERVICE_SCHEMA = {
    "service_name": "asset-service",
    "purpose": "Infrastructure inventory and asset management",
    "base_url": "http://asset-service:3002",
    "capabilities": [
        "query_asset_by_name",
        "query_asset_by_ip", 
        "query_asset_by_hostname",
        "list_assets_by_type",
        "get_asset_services"
    ],
    "queryable_fields": [
        "name", "hostname", "ip_address", "os_type", "service_type",
        "environment", "status", "tags", "location", "owner"
    ],
    "required_fields": [
        "id", "name", "hostname", "ip_address", "environment", 
        "status", "updated_at"
    ]
}


# =============================================================================
# Infrastructure Keywords for Selection Scoring
# =============================================================================

INFRA_NOUNS: Set[str] = {
    "server", "host", "hostname", "node", "asset", "database", 
    "db", "ip", "instance", "machine", "infrastructure", "vm",
    "container", "pod", "cluster", "datacenter", "rack"
}


# =============================================================================
# Compact Context Generation
# =============================================================================

def get_compact_asset_context() -> str:
    """
    Generate compact asset-service context for LLM prompts.
    
    This function returns a concise description of the asset-service
    that enables LLM reasoning without verbose explanations.
    
    Returns:
        str: Compact context string (~80 tokens)
        
    Example:
        >>> context = get_compact_asset_context()
        >>> print(context)
        ASSET-SERVICE: Infrastructure inventory API
        - Query assets by: name, hostname, IP, OS, service, environment, tags
        - Get: server details, services, location, status (NOT credentials)
        - Endpoints: GET /?search={term}, GET /{id}
        - Use for: "What's the IP of X?", "Show servers in Y"
    """
    return """
ASSET-SERVICE: Infrastructure inventory API
- Query assets by: name, hostname, IP, OS, service, environment, tags
- Get: server details, services, location, status (NOT credentials)
- Endpoints: GET /?search={term}, GET /{id}
- Use for: "What's the IP of X?", "Show servers in Y"
""".strip()


# =============================================================================
# Selection Scoring (Deterministic)
# =============================================================================

def selection_score(
    user_text: str, 
    entities: Dict[str, Any], 
    intent: str
) -> float:
    """
    Calculate selection score for asset-service tool.
    
    This is a deterministic scoring formula that combines three signals:
    1. Presence of hostname or IP entity (50% weight)
    2. Presence of infrastructure nouns in request (30% weight)
    3. Information intent (20% weight)
    
    Decision thresholds:
    - S ≥ 0.6: SELECT asset-service-query tool
    - 0.4 ≤ S < 0.6: ASK clarifying question
    - S < 0.4: DO NOT SELECT
    
    Args:
        user_text: The user's request text
        entities: Extracted entities dict (e.g., {"hostname": "web-prod-01"})
        intent: Classified intent (e.g., "information", "automation")
    
    Returns:
        float: Selection score between 0.0 and 1.0
        
    Examples:
        >>> # Strong signal: hostname + infra noun + info intent
        >>> score = selection_score(
        ...     "What's the IP of web-prod-01?",
        ...     {"hostname": "web-prod-01"},
        ...     "information"
        ... )
        >>> assert score == 1.0
        
        >>> # Medium signal: infra noun + info intent, no entity
        >>> score = selection_score(
        ...     "Show all servers",
        ...     {},
        ...     "information"
        ... )
        >>> assert score == 0.5
        
        >>> # Weak signal: no infrastructure context
        >>> score = selection_score(
        ...     "How do I center a div?",
        ...     {},
        ...     "information"
        ... )
        >>> assert score == 0.2
    """
    t = user_text.lower()
    
    # Signal 1: Hostname or IP entity present (50% weight)
    has_host_or_ip = 1.0 if (
        entities.get("hostname") or 
        entities.get("ip") or
        entities.get("ip_address")
    ) else 0.0
    
    # Signal 2: Infrastructure noun in request (30% weight)
    infra_noun = 1.0 if any(w in t for w in INFRA_NOUNS) else 0.0
    
    # Signal 3: Information intent (20% weight)
    info_intents = {
        "information", "lookup", "list", "where", "what", 
        "show", "get", "find", "search", "query"
    }
    info_intent = 1.0 if intent.lower() in info_intents else 0.0
    
    # Weighted sum
    score = 0.5 * has_host_or_ip + 0.3 * infra_noun + 0.2 * info_intent
    
    return score


# =============================================================================
# Dynamic Context Injection Heuristic
# =============================================================================

def should_inject_asset_context(user_request: str) -> bool:
    """
    Fast heuristic: should we inject asset-service context?
    
    This is a performance optimization that only injects the asset-service
    context (+80 tokens) when the request contains infrastructure keywords.
    
    Expected savings: 40-60% of requests (non-infrastructure queries)
    
    Args:
        user_request: The user's request text
    
    Returns:
        bool: True if asset-service context should be injected
        
    Examples:
        >>> should_inject_asset_context("What's the IP of web-prod-01?")
        True
        
        >>> should_inject_asset_context("How do I center a div in CSS?")
        False
        
        >>> should_inject_asset_context("Show all database servers")
        True
    """
    request_lower = user_request.lower()
    return any(kw in request_lower for kw in INFRA_NOUNS)


# =============================================================================
# Helper Functions
# =============================================================================

def get_required_fields() -> Set[str]:
    """
    Get the set of required fields for schema validation.
    
    Returns:
        Set[str]: Required field names
    """
    return set(ASSET_SERVICE_SCHEMA["required_fields"])


def get_queryable_fields() -> Set[str]:
    """
    Get the set of queryable fields.
    
    Returns:
        Set[str]: Queryable field names
    """
    return set(ASSET_SERVICE_SCHEMA["queryable_fields"])


def get_capabilities() -> list:
    """
    Get the list of asset-service capabilities.
    
    Returns:
        list: Capability names
    """
    return ASSET_SERVICE_SCHEMA["capabilities"]


# =============================================================================
# Logging and Observability
# =============================================================================

def log_selection_decision(
    user_text: str,
    score: float,
    selected: bool,
    entities: Dict[str, Any],
    intent: str
) -> Dict[str, Any]:
    """
    Create a log entry for selection decision.
    
    This is used for observability and tuning the selection threshold.
    
    Args:
        user_text: The user's request text
        score: Calculated selection score
        selected: Whether the tool was selected
        entities: Extracted entities
        intent: Classified intent
    
    Returns:
        dict: Log entry with all relevant information
    """
    return {
        "user_text": user_text,
        "selection_score": score,
        "tool_selected": selected,
        "entities": entities,
        "intent": intent,
        "threshold": 0.6,
        "decision": "select" if score >= 0.6 else "clarify" if score >= 0.4 else "skip"
    }


# =============================================================================
# Module Info
# =============================================================================

__version__ = "1.0.0"
__author__ = "OpsConductor Team"
__status__ = "Production"


if __name__ == "__main__":
    # Demo usage
    print("Asset-Service Context Module")
    print("=" * 60)
    print()
    
    print("Compact Context:")
    print("-" * 60)
    print(get_compact_asset_context())
    print()
    
    print("Selection Scoring Examples:")
    print("-" * 60)
    
    test_cases = [
        ("What's the IP of web-prod-01?", {"hostname": "web-prod-01"}, "information"),
        ("Show all servers", {}, "information"),
        ("How do I center a div?", {}, "information"),
        ("Restart nginx on db-prod-01", {"hostname": "db-prod-01", "service": "nginx"}, "automation"),
    ]
    
    for text, entities, intent in test_cases:
        score = selection_score(text, entities, intent)
        inject = should_inject_asset_context(text)
        print(f"Query: \"{text}\"")
        print(f"  Score: {score:.2f}")
        print(f"  Inject Context: {inject}")
        print(f"  Decision: {'SELECT' if score >= 0.6 else 'CLARIFY' if score >= 0.4 else 'SKIP'}")
        print()