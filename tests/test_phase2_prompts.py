"""
Test Phase 2: Prompt Enhancement
Verify that prompts have been updated with asset-service context
"""

import sys
sys.path.insert(0, '/home/opsconductor/opsconductor-ng')

from llm.prompt_manager import PromptManager, PromptType


def test_entity_extraction_prompt():
    """Test that entity extraction prompt includes asset-service context"""
    pm = PromptManager()
    prompts = pm.get_prompt(PromptType.ENTITY_EXTRACTION, user_request="test")
    
    system_prompt = prompts["system"]
    
    # Check for asset-service context
    assert "ASSET-SERVICE" in system_prompt, "Missing ASSET-SERVICE section"
    assert "Infrastructure inventory API" in system_prompt, "Missing description"
    assert "Query assets by" in system_prompt, "Missing query capabilities"
    assert "hostname, IP, OS, service, environment, tags" in system_prompt, "Missing query fields"
    assert "NOT credentials" in system_prompt, "Missing credential warning"
    
    print("✅ Entity extraction prompt includes asset-service context")
    print(f"   Prompt length: {len(system_prompt)} chars (~{len(system_prompt.split())} words)")


def test_tool_selection_prompt():
    """Test that tool selection prompt includes asset-service awareness"""
    pm = PromptManager()
    prompts = pm.get_prompt(
        PromptType.TOOL_SELECTION,
        decision='{"intent": "test"}',
        available_tools='[]'
    )
    
    system_prompt = prompts["system"]
    
    # Check for asset-service awareness
    assert "AVAILABLE DATA SOURCES" in system_prompt, "Missing data sources section"
    assert "ASSET-SERVICE" in system_prompt, "Missing ASSET-SERVICE"
    assert "Infrastructure inventory" in system_prompt, "Missing description"
    assert "asset-service-query" in system_prompt, "Missing query tool"
    assert "asset-credentials-read" in system_prompt, "Missing credentials tool"
    
    # Check for selection rubric
    assert "SELECTION RUBRIC" in system_prompt, "Missing selection rubric"
    assert "hostname/IP present" in system_prompt, "Missing strong signals"
    assert "infrastructure nouns" in system_prompt, "Missing medium signals"
    assert "S ≥ 0.6" in system_prompt, "Missing scoring threshold"
    
    # Check for updated responsibilities
    assert "Consult asset-service for infrastructure information queries" in system_prompt, \
        "Missing asset-service responsibility"
    assert "Use asset-service for infrastructure queries BEFORE attempting other tools" in system_prompt, \
        "Missing priority guidance"
    
    print("✅ Tool selection prompt includes asset-service awareness")
    print(f"   Prompt length: {len(system_prompt)} chars (~{len(system_prompt.split())} words)")


def test_planning_prompt():
    """Test that planning prompt is still functional"""
    pm = PromptManager()
    prompts = pm.get_prompt(
        PromptType.PLANNING,
        decision='{"intent": "test"}',
        selection='{"tools": []}',
        sop_snippets='[]'
    )
    
    system_prompt = prompts["system"]
    
    # Check core planning elements
    assert "CORE RESPONSIBILITIES" in system_prompt, "Missing core responsibilities"
    assert "PLANNING PRINCIPLES" in system_prompt, "Missing planning principles"
    assert "Discovery first" in system_prompt, "Missing discovery-first principle"
    assert "SAFETY CONSIDERATIONS" in system_prompt, "Missing safety section"
    
    print("✅ Planning prompt is functional")
    print(f"   Prompt length: {len(system_prompt)} chars (~{len(system_prompt.split())} words)")


def test_prompt_token_estimates():
    """Estimate token counts for updated prompts"""
    pm = PromptManager()
    
    # Entity extraction
    entity_prompts = pm.get_prompt(PromptType.ENTITY_EXTRACTION, user_request="test")
    entity_words = len(entity_prompts["system"].split())
    entity_tokens = int(entity_words * 1.3)  # Rough estimate: 1 token ≈ 0.75 words
    
    # Tool selection
    tool_prompts = pm.get_prompt(
        PromptType.TOOL_SELECTION,
        decision='{"intent": "test"}',
        available_tools='[]'
    )
    tool_words = len(tool_prompts["system"].split())
    tool_tokens = int(tool_words * 1.3)
    
    # Planning
    planning_prompts = pm.get_prompt(
        PromptType.PLANNING,
        decision='{"intent": "test"}',
        selection='{"tools": []}',
        sop_snippets='[]'
    )
    planning_words = len(planning_prompts["system"].split())
    planning_tokens = int(planning_words * 1.3)
    
    print("\n📊 Token Estimates:")
    print(f"   Entity Extraction: ~{entity_tokens} tokens (target: ~230)")
    print(f"   Tool Selection: ~{tool_tokens} tokens (target: ~450)")
    print(f"   Planning: ~{planning_tokens} tokens (unchanged)")
    
    # Verify within acceptable ranges (allow some flexibility)
    assert 150 <= entity_tokens <= 280, f"Entity extraction tokens out of range: {entity_tokens}"
    assert 350 <= tool_tokens <= 550, f"Tool selection tokens out of range: {tool_tokens}"
    
    print("✅ All prompts within acceptable token ranges")


if __name__ == "__main__":
    print("=" * 60)
    print("PHASE 2: PROMPT ENHANCEMENT TESTS")
    print("=" * 60)
    print()
    
    try:
        test_entity_extraction_prompt()
        print()
        test_tool_selection_prompt()
        print()
        test_planning_prompt()
        print()
        test_prompt_token_estimates()
        print()
        print("=" * 60)
        print("✅ ALL PHASE 2 TESTS PASSED")
        print("=" * 60)
    except AssertionError as e:
        print()
        print("=" * 60)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 60)
        sys.exit(1)
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ ERROR: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        sys.exit(1)