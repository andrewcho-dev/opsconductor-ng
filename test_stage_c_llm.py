#!/usr/bin/env python3
"""
Test script to verify Stage C now uses LLM for planning
"""
import asyncio
import sys
from pipeline.stages.stage_c.planner import StageCPlanner
from pipeline.schemas.decision_v1 import DecisionV1, IntentV1, DecisionType, ConfidenceLevel, RiskLevel
from pipeline.schemas.selection_v1 import SelectionV1, SelectedTool, ExecutionPolicy, RiskLevel as SelectionRiskLevel
from llm.ollama_client import OllamaClient

async def test_stage_c_llm():
    """Test that Stage C uses LLM for planning"""
    
    # Initialize LLM client
    llm_config = {
        "base_url": "http://localhost:11434",
        "default_model": "qwen2.5:7b-instruct-q4_k_m",
        "timeout": 120
    }
    llm_client = OllamaClient(llm_config)
    await llm_client.connect()
    
    # Initialize Stage C with LLM
    stage_c = StageCPlanner(llm_client=llm_client)
    
    # Create test decision
    decision = DecisionV1(
        decision_id="test_001",
        decision_type=DecisionType.INFO,
        timestamp="2025-01-01T00:00:00",
        intent=IntentV1(
            category="information",
            action="list_assets",
            confidence=0.95
        ),
        entities=[],
        overall_confidence=0.95,
        confidence_level=ConfidenceLevel.HIGH,
        risk_level=RiskLevel.LOW,
        original_request="list all assets",
        context={},
        requires_approval=False,
        next_stage="stage_b"
    )
    
    # Create test selection
    selection = SelectionV1(
        selection_id="sel_001",
        decision_id="test_001",
        timestamp="2025-01-01T00:00:00",
        selected_tools=[
            SelectedTool(
                tool_name="asset-service-query",
                justification="Query asset database to list all assets",
                execution_order=1
            )
        ],
        total_tools=1,
        policy=ExecutionPolicy(
            requires_approval=False,
            risk_level=SelectionRiskLevel.LOW,
            max_execution_time=30
        ),
        selection_confidence=0.95,
        next_stage="stage_c"
    )
    
    print("=" * 80)
    print("Testing Stage C with LLM-based planning")
    print("=" * 80)
    print(f"User Query: {decision.original_request}")
    print(f"Selected Tool: {selection.selected_tools[0].tool_name}")
    print()
    
    try:
        # Create plan using LLM
        print("🧠 Calling Stage C to create plan using LLM...")
        print(f"   LLM client connected: {llm_client.is_connected}")
        print(f"   Stage C has LLM client: {stage_c.llm_client is not None}")
        plan = await stage_c.create_plan(decision, selection)
        
        print("✅ Plan created successfully!")
        print()
        print("=" * 80)
        print("EXECUTION STEPS:")
        print("=" * 80)
        
        for step in plan.plan.steps:
            print(f"\nStep ID: {step.id}")
            print(f"Tool: {step.tool}")
            print(f"Description: {step.description}")
            print(f"Inputs: {step.inputs}")
            print(f"  - query_type: {step.inputs.get('query_type')}")
            print(f"  - fields: {step.inputs.get('fields')}")
            print(f"  - filters: {step.inputs.get('filters')}")
        
        print()
        print("=" * 80)
        print("VERIFICATION:")
        print("=" * 80)
        
        # Verify that fields were intelligently selected
        first_step = plan.plan.steps[0]
        fields = first_step.inputs.get('fields', [])
        
        if fields and len(fields) > 0:
            print(f"✅ SUCCESS: LLM selected {len(fields)} specific fields")
            print(f"   Fields: {', '.join(fields)}")
            print()
            print("🎉 Stage C is now using LLM for intelligent planning!")
            print("🎉 No more hardcoded rules!")
            return True
        else:
            print(f"❌ FAILED: No fields selected (fields={fields})")
            print("   LLM should have selected specific fields for 'list all assets' query")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await llm_client.disconnect()

if __name__ == "__main__":
    result = asyncio.run(test_stage_c_llm())
    sys.exit(0 if result else 1)