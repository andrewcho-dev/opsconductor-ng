"""
Test Phase 3: Asset-Service Integration in Step Generator

This test suite validates that the step generator correctly creates
execution steps for asset-service tools.
"""

import pytest
from datetime import datetime, timezone
from pipeline.stages.stage_c.step_generator import StepGenerator
from pipeline.schemas.decision_v1 import (
    DecisionV1, IntentV1, EntityV1, DecisionType, 
    ConfidenceLevel, RiskLevel
)
from pipeline.schemas.selection_v1 import (
    SelectionV1, SelectedTool, ExecutionPolicy, RiskLevel as SelectionRiskLevel
)


def create_test_selection(selected_tools, decision_id="dec_test_001", requires_approval=False):
    """Helper to create SelectionV1 for testing"""
    return SelectionV1(
        selection_id=f"sel_test_{decision_id}",
        decision_id=decision_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        selected_tools=selected_tools,
        total_tools=len(selected_tools),
        policy=ExecutionPolicy(
            requires_approval=requires_approval,
            production_environment=False,
            risk_level=SelectionRiskLevel.LOW,
            max_execution_time=300,
            parallel_execution=False,
            rollback_required=False
        ),
        additional_inputs_needed=[],
        environment_requirements={},
        selection_confidence=0.9,
        next_stage="stage_c",
        ready_for_execution=True
    )


def test_asset_query_step_generation_by_hostname():
    """Test that asset-service-query step is generated correctly for hostname queries"""
    
    # Create decision with hostname entity
    decision = DecisionV1(
        decision_id="dec_test_asset_001",
        decision_type=DecisionType.INFO,
        timestamp=datetime.now(timezone.utc).isoformat(),
        original_request="What's the IP address of web-server-01?",
        intent=IntentV1(
            action="query_infrastructure",
            category="info_request",
            confidence=0.95
        ),
        entities=[
            EntityV1(type="hostname", value="web-server-01", confidence=0.9)
        ],
        overall_confidence=0.95,
        confidence_level=ConfidenceLevel.HIGH,
        risk_level=RiskLevel.LOW,
        requires_approval=False,
        next_stage="stage_b"
    )
    
    # Create selection with asset-service-query tool
    selected_tool = SelectedTool(
        tool_name="asset-service-query",
        justification="Query asset-service for server IP address",
        execution_order=1,
        inputs_needed=["hostname"],
        depends_on=[]
    )
    
    selection = create_test_selection([selected_tool], decision_id="dec_test_asset_001")
    
    # Generate steps
    generator = StepGenerator()
    steps = generator.generate_steps(decision, selection)
    
    # Assertions
    assert len(steps) == 1, "Should generate exactly one step"
    
    step = steps[0]
    assert step.tool == "asset-service-query", "Tool should be asset-service-query"
    assert step.inputs["query_type"] == "get_by_hostname", "Should use get_by_hostname query type"
    assert step.inputs["hostname"] == "web-server-01", "Should extract hostname from entities"
    assert "asset_service_available" in step.preconditions, "Should check asset-service availability"
    assert "asset_data_retrieved" in step.success_criteria, "Should verify data retrieval"
    assert step.estimated_duration == 8, "Should use correct duration estimate"
    
    print(f"✅ Asset query step generated successfully")
    print(f"   Step ID: {step.id}")
    print(f"   Description: {step.description}")
    print(f"   Query type: {step.inputs['query_type']}")
    print(f"   Hostname: {step.inputs['hostname']}")


def test_asset_query_step_generation_search():
    """Test that asset-service-query step is generated for search queries"""
    
    decision = DecisionV1(
        decision_id="dec_test_asset_002",
        decision_type=DecisionType.INFO,
        timestamp=datetime.now(timezone.utc).isoformat(),
        original_request="Show me all production database servers",
        intent=IntentV1(
            action="list_infrastructure",
            category="info_request",
            confidence=0.9
        ),
        entities=[
            EntityV1(type="environment", value="production", confidence=0.95),
            EntityV1(type="service_name", value="database", confidence=0.85)
        ],
        overall_confidence=0.9,
        confidence_level=ConfidenceLevel.HIGH,
        risk_level=RiskLevel.LOW,
        requires_approval=False,
        next_stage="stage_b"
    )
    
    selected_tool = SelectedTool(
        tool_name="asset-service-query",
        justification="Query asset-service for production database servers",
        execution_order=1,
        inputs_needed=["filters"],
        depends_on=[]
    )
    
    selection = create_test_selection([selected_tool], decision_id="dec_test_asset_002")
    
    generator = StepGenerator()
    steps = generator.generate_steps(decision, selection)
    
    assert len(steps) == 1
    step = steps[0]
    
    assert step.tool == "asset-service-query"
    assert "filters" in step.inputs
    assert step.inputs["filters"].get("environment") == "production"
    assert step.inputs["filters"].get("service_type") == "database"
    
    print(f"✅ Asset search step generated successfully")
    print(f"   Filters: {step.inputs['filters']}")
    print(f"   Limit: {step.inputs['limit']}")


def test_asset_credentials_step_generation():
    """Test that asset-credentials-read step is generated with proper gating"""
    
    decision = DecisionV1(
        decision_id="dec_test_asset_003",
        decision_type=DecisionType.ACTION,
        timestamp=datetime.now(timezone.utc).isoformat(),
        original_request="I need SSH access to prod-db-01 for emergency maintenance",
        intent=IntentV1(
            action="request_credentials",
            category="credential_access",
            confidence=0.9
        ),
        entities=[
            EntityV1(type="hostname", value="prod-db-01", confidence=0.95)
        ],
        overall_confidence=0.9,
        confidence_level=ConfidenceLevel.HIGH,
        risk_level=RiskLevel.HIGH,
        requires_approval=True,
        next_stage="stage_b"
    )
    
    selected_tool = SelectedTool(
        tool_name="asset-credentials-read",
        justification="Retrieve SSH credentials for emergency access",
        execution_order=1,
        inputs_needed=["asset_id", "justification", "credential_type"],
        depends_on=[]
    )
    
    selection = create_test_selection([selected_tool], decision_id="dec_test_asset_003", requires_approval=True)
    
    generator = StepGenerator()
    steps = generator.generate_steps(decision, selection)
    
    assert len(steps) == 1
    step = steps[0]
    
    assert step.tool == "asset-credentials-read"
    assert step.inputs["requires_approval"] == True, "Should require approval"
    assert "justification" in step.inputs, "Should include justification"
    assert "user_has_credential_read_permission" in step.preconditions, "Should check permissions"
    assert "approval_granted" in step.preconditions, "Should require approval"
    assert "audit_log_created" in step.success_criteria, "Should create audit log"
    assert "REQUIRES APPROVAL" in step.description, "Description should indicate approval requirement"
    
    print(f"✅ Asset credentials step generated successfully")
    print(f"   Requires approval: {step.inputs['requires_approval']}")
    print(f"   Justification: {step.inputs['justification'][:50]}...")
    print(f"   Preconditions: {len(step.preconditions)}")


def test_asset_query_parameter_extraction():
    """Test the _extract_asset_query_params helper method"""
    
    decision = DecisionV1(
        decision_id="dec_test_asset_004",
        decision_type=DecisionType.INFO,
        timestamp=datetime.now(timezone.utc).isoformat(),
        original_request="Find servers in staging environment running nginx",
        intent=IntentV1(
            action="search_infrastructure",
            category="info_request",
            confidence=0.9
        ),
        entities=[
            EntityV1(type="environment", value="staging", confidence=0.95),
            EntityV1(type="service_name", value="nginx", confidence=0.9)
        ],
        overall_confidence=0.9,
        confidence_level=ConfidenceLevel.HIGH,
        risk_level=RiskLevel.LOW,
        requires_approval=False,
        next_stage="stage_b"
    )
    
    selected_tool = SelectedTool(
        tool_name="asset-service-query",
        justification="Search for nginx servers in staging",
        execution_order=1,
        inputs_needed=[],
        depends_on=[]
    )
    
    generator = StepGenerator()
    params = generator._extract_asset_query_params(decision, selected_tool)
    
    assert "filters" in params
    assert params["filters"]["environment"] == "staging"
    assert params["filters"]["service_type"] == "nginx"
    assert params["query_type"] in ["search", "list_all"]
    
    print(f"✅ Query parameter extraction working correctly")
    print(f"   Query type: {params['query_type']}")
    print(f"   Filters: {params['filters']}")


def test_asset_query_with_ip_address():
    """Test asset query step generation with IP address entity"""
    
    decision = DecisionV1(
        decision_id="dec_test_asset_005",
        decision_type=DecisionType.INFO,
        timestamp=datetime.now(timezone.utc).isoformat(),
        original_request="What server has IP 10.0.1.50?",
        intent=IntentV1(
            action="lookup_by_ip",
            category="info_request",
            confidence=0.95
        ),
        entities=[
            EntityV1(type="ip_address", value="10.0.1.50", confidence=0.95)
        ],
        overall_confidence=0.95,
        confidence_level=ConfidenceLevel.HIGH,
        risk_level=RiskLevel.LOW,
        requires_approval=False,
        next_stage="stage_b"
    )
    
    selected_tool = SelectedTool(
        tool_name="asset-service-query",
        justification="Search asset by IP address",
        execution_order=1,
        inputs_needed=[],
        depends_on=[]
    )
    
    selection = create_test_selection([selected_tool], decision_id="dec_test_asset_005")
    
    generator = StepGenerator()
    steps = generator.generate_steps(decision, selection)
    
    assert len(steps) == 1
    step = steps[0]
    
    assert step.tool == "asset-service-query"
    assert step.inputs["query_type"] == "search"
    assert step.inputs["search_term"] == "10.0.1.50"
    
    print(f"✅ IP address query step generated successfully")
    print(f"   Search term: {step.inputs['search_term']}")


def test_multiple_tools_including_asset_service():
    """Test that asset-service tools work alongside other tools"""
    
    decision = DecisionV1(
        decision_id="dec_test_asset_006",
        decision_type=DecisionType.INFO,
        timestamp=datetime.now(timezone.utc).isoformat(),
        original_request="Get the IP of web-server-01 and check if nginx is running",
        intent=IntentV1(
            action="check_service_status",
            category="monitor_system",
            confidence=0.9
        ),
        entities=[
            EntityV1(type="hostname", value="web-server-01", confidence=0.95),
            EntityV1(type="service_name", value="nginx", confidence=0.9)
        ],
        overall_confidence=0.9,
        confidence_level=ConfidenceLevel.HIGH,
        risk_level=RiskLevel.LOW,
        requires_approval=False,
        next_stage="stage_b"
    )
    
    selected_tools = [
        SelectedTool(
            tool_name="asset-service-query",
            justification="Get server IP from asset-service",
            execution_order=1,
            inputs_needed=["hostname"],
            depends_on=[]
        ),
        SelectedTool(
            tool_name="systemctl",
            justification="Check nginx service status",
            execution_order=2,
            inputs_needed=["service"],
            depends_on=["asset-service-query"]
        )
    ]
    
    selection = create_test_selection(selected_tools, decision_id="dec_test_asset_006")
    
    generator = StepGenerator()
    steps = generator.generate_steps(decision, selection)
    
    assert len(steps) == 2, "Should generate two steps"
    
    # First step should be asset query
    assert steps[0].tool == "asset-service-query"
    assert steps[0].inputs["hostname"] == "web-server-01"
    
    # Second step should be systemctl
    assert steps[1].tool == "systemctl"
    assert steps[1].inputs["service"] == "nginx"
    
    print(f"✅ Multiple tools including asset-service work correctly")
    print(f"   Step 1: {steps[0].tool} - {steps[0].description}")
    print(f"   Step 2: {steps[1].tool} - {steps[1].description}")


def test_asset_tool_templates_registered():
    """Test that asset-service tools are registered in tool_templates"""
    
    generator = StepGenerator()
    
    assert "asset-service-query" in generator.tool_templates, \
        "asset-service-query should be in tool_templates"
    assert "asset-credentials-read" in generator.tool_templates, \
        "asset-credentials-read should be in tool_templates"
    
    assert "asset-service-query" in generator.default_durations, \
        "asset-service-query should have duration estimate"
    assert "asset-credentials-read" in generator.default_durations, \
        "asset-credentials-read should have duration estimate"
    
    print(f"✅ Asset-service tools properly registered")
    print(f"   Query duration: {generator.default_durations['asset-service-query']}s")
    print(f"   Credentials duration: {generator.default_durations['asset-credentials-read']}s")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("PHASE 3 TESTS: Asset-Service Step Generator Integration")
    print("="*70 + "\n")
    
    try:
        test_asset_tool_templates_registered()
        print()
        
        test_asset_query_step_generation_by_hostname()
        print()
        
        test_asset_query_step_generation_search()
        print()
        
        test_asset_credentials_step_generation()
        print()
        
        test_asset_query_parameter_extraction()
        print()
        
        test_asset_query_with_ip_address()
        print()
        
        test_multiple_tools_including_asset_service()
        print()
        
        print("="*70)
        print("✅ ALL PHASE 3 TESTS PASSED")
        print("="*70)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        raise