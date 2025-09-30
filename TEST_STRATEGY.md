# OpsConductor NEWIDEA.MD Architecture - Comprehensive Test Strategy

## OVERVIEW

This document defines the **EXHAUSTIVE TESTING STRATEGY** for the complete transformation to NEWIDEA.MD architecture. Every component will be tested to outlier cases and limitations with **100% REPEATABLE** test suites.

## TESTING PRINCIPLES

1. **EXHAUSTIVE COVERAGE**: Test every component to its limits and edge cases
2. **REPEATABLE EXECUTION**: All tests must be deterministic and repeatable
3. **CUMULATIVE VALIDATION**: Each phase includes regression tests for all previous phases
4. **LIMITATION DISCOVERY**: Identify and document every limitation and boundary condition
5. **CLEAN ORGANIZATION**: Tests organized by phase, component, and scenario type

## TEST FRAMEWORK ARCHITECTURE

### Test Infrastructure
```python
# Base test framework structure
tests/
├── conftest.py                 # Pytest configuration and fixtures
├── test_config.py             # Test configuration and constants
├── utils/
│   ├── test_helpers.py        # Common test utilities
│   ├── mock_services.py       # Mock service implementations
│   ├── data_generators.py     # Test data generation
│   └── assertion_helpers.py   # Custom assertion functions
├── fixtures/
│   ├── llm_responses/         # Mock LLM response data
│   ├── capability_manifests/  # Test capability manifests
│   ├── user_requests/         # Test user request samples
│   └── expected_outputs/      # Expected test outputs
└── [phase_directories]/       # Phase-specific test directories
```

### Test Categories
1. **UNIT TESTS**: Individual component testing
2. **INTEGRATION TESTS**: Component interaction testing
3. **SYSTEM TESTS**: Full pipeline testing
4. **PERFORMANCE TESTS**: Load and stress testing
5. **EDGE CASE TESTS**: Boundary condition testing
6. **FAILURE MODE TESTS**: Error scenario testing
7. **REGRESSION TESTS**: Previous functionality validation

## PHASE-BY-PHASE TEST SPECIFICATIONS

### PHASE 0: FOUNDATION TESTING
**Test Count**: 25 tests
**Focus**: Infrastructure and base components

#### Test Categories:
1. **Infrastructure Tests** (10 tests)
   - JSON schema validation framework
   - Logging system functionality
   - Configuration management
   - Database connectivity
   - LLM connectivity

2. **Base Component Tests** (10 tests)
   - Pipeline stage base class
   - Error handling mechanisms
   - State management
   - Monitoring integration
   - Security framework

3. **Cleanup Validation Tests** (5 tests)
   - Verify no old code remains
   - Validate new directory structure
   - Confirm dependency cleanup
   - Test new dependency functionality
   - Validate configuration migration

#### Sample Test Implementation:
```python
# tests/phase_0/test_infrastructure.py
import pytest
from opsconductor.pipeline.base import PipelineStage
from opsconductor.validation import JSONSchemaValidator

class TestInfrastructure:
    def test_json_schema_validator_valid_input(self):
        """Test JSON schema validation with valid input"""
        validator = JSONSchemaValidator("decision_v1.json")
        valid_decision = {
            "mode": "act",
            "intent": "system_status",
            "confidence": 0.95,
            "entities": {"hostname": "server01"},
            "missing_fields": []
        }
        result = validator.validate(valid_decision)
        assert result.is_valid
        assert result.errors == []

    def test_json_schema_validator_invalid_input(self):
        """Test JSON schema validation with invalid input"""
        validator = JSONSchemaValidator("decision_v1.json")
        invalid_decision = {
            "mode": "invalid_mode",  # Invalid mode
            "confidence": 1.5,       # Invalid confidence range
            "entities": "not_dict"   # Invalid type
        }
        result = validator.validate(invalid_decision)
        assert not result.is_valid
        assert len(result.errors) >= 3

    def test_pipeline_stage_base_class(self):
        """Test pipeline stage base class functionality"""
        class TestStage(PipelineStage):
            def process(self, input_data):
                return {"processed": True}
        
        stage = TestStage("test_stage")
        assert stage.name == "test_stage"
        assert stage.process({"test": "data"}) == {"processed": True}
```

---

### PHASE 1: STAGE A - CLASSIFIER TESTING
**Test Count**: 75 tests
**Focus**: Decision classification and confidence scoring

#### Test Categories:

##### 1. Intent Classification Tests (25 tests)
```python
# tests/phase_1/test_classifier_intents.py
class TestIntentClassification:
    
    @pytest.mark.parametrize("request,expected_intent,min_confidence", [
        ("Check system status on server01", "system_status", 0.8),
        ("Restart nginx service", "service_restart", 0.9),
        ("Show me the logs for application", "log_retrieval", 0.85),
        ("Deploy version 2.1.0 to production", "deployment", 0.9),
        ("What is the CPU usage?", "system_metrics", 0.8),
    ])
    def test_high_confidence_intent_classification(self, request, expected_intent, min_confidence):
        """Test high-confidence intent classification"""
        classifier = StageAClassifier()
        result = classifier.process({"user_request": request})
        
        assert result["intent"] == expected_intent
        assert result["confidence"] >= min_confidence
        assert result["mode"] == "act"

    @pytest.mark.parametrize("ambiguous_request", [
        "Fix the thing that's broken",
        "Make it work better",
        "Check that server",
        "Do something with the database",
        "Handle the issue we discussed",
    ])
    def test_ambiguous_requests_trigger_clarification(self, ambiguous_request):
        """Test that ambiguous requests trigger clarification mode"""
        classifier = StageAClassifier()
        result = classifier.process({"user_request": ambiguous_request})
        
        assert result["mode"] == "clarify"
        assert result["confidence"] < 0.7
        assert len(result["missing_fields"]) > 0

    @pytest.mark.parametrize("unknown_request", [
        "Bake me a cake",
        "What's the weather like?",
        "Translate this to French",
        "Play some music",
        "Order pizza for the team",
    ])
    def test_unknown_intents_handled_safely(self, unknown_request):
        """Test that unknown intents are handled safely"""
        classifier = StageAClassifier()
        result = classifier.process({"user_request": unknown_request})
        
        assert result["intent"] == "unknown"
        assert result["mode"] == "clarify"
        assert result["confidence"] < 0.5

    def test_multi_intent_request_handling(self):
        """Test handling of requests with multiple intents"""
        request = "Check system status and restart nginx if needed"
        classifier = StageAClassifier()
        result = classifier.process({"user_request": request})
        
        # Should either pick primary intent or request clarification
        assert result["intent"] in ["system_status", "service_restart"] or result["mode"] == "clarify"
        if result["mode"] == "clarify":
            assert "multiple operations" in result["clarification_needed"].lower()
```

##### 2. Confidence Scoring Tests (20 tests)
```python
class TestConfidenceScoring:
    
    def test_confidence_score_ranges(self):
        """Test that confidence scores are within valid ranges"""
        classifier = StageAClassifier()
        test_requests = [
            "Check system status",  # Should be high confidence
            "Fix the problem",      # Should be low confidence
            "Restart service xyz",  # Should be medium-high confidence
        ]
        
        for request in test_requests:
            result = classifier.process({"user_request": request})
            assert 0.0 <= result["confidence"] <= 1.0

    def test_confidence_calibration_accuracy(self):
        """Test that confidence scores correlate with actual accuracy"""
        classifier = StageAClassifier()
        
        # High confidence requests should have high accuracy
        high_conf_requests = [
            ("Check system status on server01", "system_status"),
            ("Restart nginx service", "service_restart"),
            ("Show application logs", "log_retrieval"),
        ]
        
        for request, expected_intent in high_conf_requests:
            result = classifier.process({"user_request": request})
            if result["confidence"] > 0.8:
                assert result["intent"] == expected_intent

    @pytest.mark.parametrize("confidence_threshold", [0.5, 0.6, 0.7, 0.8, 0.9])
    def test_confidence_threshold_behavior(self, confidence_threshold):
        """Test behavior at different confidence thresholds"""
        classifier = StageAClassifier(confidence_threshold=confidence_threshold)
        
        ambiguous_request = "Fix the issue"
        result = classifier.process({"user_request": ambiguous_request})
        
        if result["confidence"] < confidence_threshold:
            assert result["mode"] == "clarify"
        else:
            assert result["mode"] in ["act", "info"]
```

##### 3. Entity Extraction Tests (20 tests)
```python
class TestEntityExtraction:
    
    @pytest.mark.parametrize("request,expected_entities", [
        ("Check status of server01", {"hostname": "server01"}),
        ("Restart nginx on 192.168.1.100", {"service": "nginx", "ip_address": "192.168.1.100"}),
        ("Deploy app-v2.1.0 to production", {"application": "app", "version": "v2.1.0", "environment": "production"}),
        ("Show logs for user-service from last 1 hour", {"service": "user-service", "time_range": "1 hour"}),
    ])
    def test_entity_extraction_accuracy(self, request, expected_entities):
        """Test accurate entity extraction from requests"""
        classifier = StageAClassifier()
        result = classifier.process({"user_request": request})
        
        for entity_type, entity_value in expected_entities.items():
            assert entity_type in result["entities"]
            assert result["entities"][entity_type] == entity_value

    def test_malformed_entity_handling(self):
        """Test handling of malformed entities"""
        malformed_requests = [
            "Check status of server01.invalid..domain",
            "Restart service with port 99999999",
            "Deploy version v..2.1.0",
            "Connect to 999.999.999.999",
        ]
        
        classifier = StageAClassifier()
        for request in malformed_requests:
            result = classifier.process({"user_request": request})
            # Should either extract corrected entities or request clarification
            assert result["mode"] in ["act", "clarify"]

    def test_missing_required_entities(self):
        """Test detection of missing required entities"""
        incomplete_requests = [
            ("Restart service", ["service"]),  # Missing service name
            ("Deploy to environment", ["application", "version"]),  # Missing app and version
            ("Check status", ["target"]),  # Missing target system
        ]
        
        classifier = StageAClassifier()
        for request, missing_entities in incomplete_requests:
            result = classifier.process({"user_request": request})
            
            if result["mode"] == "clarify":
                for missing_entity in missing_entities:
                    assert missing_entity in result["missing_fields"]
```

##### 4. Error Handling Tests (10 tests)
```python
class TestClassifierErrorHandling:
    
    def test_llm_timeout_handling(self):
        """Test handling of LLM timeout scenarios"""
        classifier = StageAClassifier(llm_timeout=0.1)  # Very short timeout
        
        with patch('opsconductor.llm.OllamaClient.generate') as mock_llm:
            mock_llm.side_effect = TimeoutError("LLM request timed out")
            
            result = classifier.process({"user_request": "Check system status"})
            
            assert result["mode"] == "clarify"
            assert "system temporarily unavailable" in result["clarification_needed"].lower()

    def test_invalid_json_response_handling(self):
        """Test handling of invalid JSON responses from LLM"""
        classifier = StageAClassifier()
        
        with patch('opsconductor.llm.OllamaClient.generate') as mock_llm:
            mock_llm.return_value = "This is not valid JSON at all"
            
            result = classifier.process({"user_request": "Check system status"})
            
            # Should trigger JSON repair mechanism
            assert isinstance(result, dict)
            assert "mode" in result

    def test_schema_validation_failure_recovery(self):
        """Test recovery from schema validation failures"""
        classifier = StageAClassifier()
        
        with patch('opsconductor.llm.OllamaClient.generate') as mock_llm:
            # Return JSON that doesn't match schema
            mock_llm.return_value = '{"invalid_field": "value", "mode": "invalid_mode"}'
            
            result = classifier.process({"user_request": "Check system status"})
            
            # Should either repair or fallback gracefully
            assert result["mode"] in ["act", "info", "clarify"]
```

---

### PHASE 2: STAGE B - SELECTOR TESTING
**Test Count**: 60 tests
**Focus**: Tool selection and risk assessment

#### Test Categories:

##### 1. Tool Selection Tests (20 tests)
```python
class TestToolSelection:
    
    def test_single_tool_selection_accuracy(self):
        """Test accurate selection of single tools"""
        selector = StageBSelector()
        
        decision = {
            "mode": "act",
            "intent": "system_status",
            "entities": {"hostname": "server01"},
            "confidence": 0.9
        }
        
        capability_manifest = {
            "system_monitoring": {
                "tools": ["system_status_checker", "performance_monitor"],
                "risk_level": "low",
                "required_permissions": ["read"]
            }
        }
        
        result = selector.process({
            "decision": decision,
            "capability_manifest": capability_manifest
        })
        
        assert "system_status_checker" in result["selected_tools"]
        assert result["risk_assessment"]["level"] == "low"

    def test_multi_tool_selection_optimization(self):
        """Test optimal selection of multiple tools"""
        selector = StageBSelector()
        
        decision = {
            "mode": "act",
            "intent": "deployment",
            "entities": {"application": "web-app", "environment": "staging"},
            "confidence": 0.85
        }
        
        result = selector.process({"decision": decision, "capability_manifest": DEPLOYMENT_MANIFEST})
        
        # Should select complementary tools, not redundant ones
        selected_tools = result["selected_tools"]
        assert len(selected_tools) >= 2
        assert not any(tool1["conflicts_with"] == tool2["name"] 
                      for tool1 in selected_tools for tool2 in selected_tools)

    @pytest.mark.parametrize("missing_capability", [
        "nonexistent_service",
        "unsupported_operation",
        "invalid_tool_name",
    ])
    def test_missing_capability_handling(self, missing_capability):
        """Test handling of missing capabilities"""
        selector = StageBSelector()
        
        decision = {
            "mode": "act",
            "intent": missing_capability,
            "confidence": 0.8
        }
        
        result = selector.process({"decision": decision, "capability_manifest": {}})
        
        assert result["status"] == "capability_not_found"
        assert len(result["selected_tools"]) == 0
        assert missing_capability in result["missing_capabilities"]
```

##### 2. Risk Assessment Tests (20 tests)
```python
class TestRiskAssessment:
    
    @pytest.mark.parametrize("operation,expected_risk", [
        ("system_status", "low"),
        ("log_retrieval", "low"),
        ("service_restart", "medium"),
        ("deployment", "high"),
        ("database_migration", "critical"),
    ])
    def test_risk_level_calculation(self, operation, expected_risk):
        """Test accurate risk level calculation"""
        selector = StageBSelector()
        
        decision = {"mode": "act", "intent": operation, "confidence": 0.9}
        result = selector.process({"decision": decision, "capability_manifest": FULL_MANIFEST})
        
        assert result["risk_assessment"]["level"] == expected_risk

    def test_production_environment_risk_escalation(self):
        """Test risk escalation for production environments"""
        selector = StageBSelector()
        
        # Same operation, different environments
        staging_decision = {
            "mode": "act",
            "intent": "service_restart",
            "entities": {"environment": "staging"},
            "confidence": 0.9
        }
        
        production_decision = {
            "mode": "act",
            "intent": "service_restart", 
            "entities": {"environment": "production"},
            "confidence": 0.9
        }
        
        staging_result = selector.process({"decision": staging_decision, "capability_manifest": FULL_MANIFEST})
        production_result = selector.process({"decision": production_decision, "capability_manifest": FULL_MANIFEST})
        
        # Production should have higher risk
        staging_risk = RISK_LEVELS[staging_result["risk_assessment"]["level"]]
        production_risk = RISK_LEVELS[production_result["risk_assessment"]["level"]]
        assert production_risk > staging_risk

    def test_confidence_impact_on_risk(self):
        """Test how confidence levels impact risk assessment"""
        selector = StageBSelector()
        
        high_confidence = {"mode": "act", "intent": "deployment", "confidence": 0.95}
        low_confidence = {"mode": "act", "intent": "deployment", "confidence": 0.6}
        
        high_conf_result = selector.process({"decision": high_confidence, "capability_manifest": FULL_MANIFEST})
        low_conf_result = selector.process({"decision": low_confidence, "capability_manifest": FULL_MANIFEST})
        
        # Low confidence should increase risk or trigger approval
        assert (low_conf_result["approval_required"] or 
                RISK_LEVELS[low_conf_result["risk_assessment"]["level"]] >= 
                RISK_LEVELS[high_conf_result["risk_assessment"]["level"]])
```

##### 3. Policy Enforcement Tests (20 tests)
```python
class TestPolicyEnforcement:
    
    def test_least_privilege_enforcement(self):
        """Test least-privilege tool selection"""
        selector = StageBSelector()
        
        decision = {"mode": "act", "intent": "log_retrieval", "confidence": 0.9}
        
        result = selector.process({"decision": decision, "capability_manifest": FULL_MANIFEST})
        
        # Should select read-only tools, not admin tools
        for tool in result["selected_tools"]:
            assert "write" not in tool["required_permissions"]
            assert "admin" not in tool["required_permissions"]

    def test_production_restriction_enforcement(self):
        """Test production environment restrictions"""
        selector = StageBSelector()
        
        production_decision = {
            "mode": "act",
            "intent": "database_migration",
            "entities": {"environment": "production"},
            "confidence": 0.9
        }
        
        result = selector.process({"decision": production_decision, "capability_manifest": FULL_MANIFEST})
        
        # Should require approval for production operations
        assert result["approval_required"] == True
        assert result["approval_level"] in ["manager", "admin", "security"]

    def test_policy_violation_blocking(self):
        """Test blocking of policy violations"""
        selector = StageBSelector()
        
        # Attempt high-risk operation with low confidence
        violation_decision = {
            "mode": "act",
            "intent": "system_shutdown",
            "entities": {"environment": "production"},
            "confidence": 0.4  # Too low for such a risky operation
        }
        
        result = selector.process({"decision": violation_decision, "capability_manifest": FULL_MANIFEST})
        
        assert result["status"] == "policy_violation"
        assert len(result["selected_tools"]) == 0
        assert "confidence too low" in result["violation_reason"].lower()
```

---

### PHASE 3: STAGE C - PLANNER TESTING
**Test Count**: 80 tests
**Focus**: Execution planning and safety mechanisms

#### Test Categories:

##### 1. Plan Generation Tests (25 tests)
```python
class TestPlanGeneration:
    
    def test_simple_linear_plan_generation(self):
        """Test generation of simple linear execution plans"""
        planner = StageCPlanner()
        
        input_data = {
            "decision": {"mode": "act", "intent": "system_status"},
            "selected_tools": [{"name": "system_status_checker", "type": "monitoring"}],
            "risk_assessment": {"level": "low"}
        }
        
        result = planner.process(input_data)
        
        assert len(result["execution_plan"]["steps"]) >= 1
        assert result["execution_plan"]["steps"][0]["tool"] == "system_status_checker"
        assert result["execution_plan"]["execution_type"] == "linear"

    def test_complex_multi_step_plan_generation(self):
        """Test generation of complex multi-step plans"""
        planner = StageCPlanner()
        
        input_data = {
            "decision": {"mode": "act", "intent": "deployment"},
            "selected_tools": [
                {"name": "health_checker", "type": "monitoring"},
                {"name": "deployer", "type": "deployment"},
                {"name": "smoke_tester", "type": "testing"}
            ],
            "risk_assessment": {"level": "high"}
        }
        
        result = planner.process(input_data)
        
        plan = result["execution_plan"]
        assert len(plan["steps"]) >= 3
        
        # Should have proper ordering: health check -> deploy -> smoke test
        step_tools = [step["tool"] for step in plan["steps"]]
        assert step_tools.index("health_checker") < step_tools.index("deployer")
        assert step_tools.index("deployer") < step_tools.index("smoke_tester")

    def test_parallel_execution_plan_generation(self):
        """Test generation of parallel execution plans"""
        planner = StageCPlanner()
        
        input_data = {
            "decision": {"mode": "act", "intent": "multi_server_status"},
            "selected_tools": [
                {"name": "server1_monitor", "type": "monitoring", "target": "server1"},
                {"name": "server2_monitor", "type": "monitoring", "target": "server2"},
                {"name": "server3_monitor", "type": "monitoring", "target": "server3"}
            ],
            "risk_assessment": {"level": "low"}
        }
        
        result = planner.process(input_data)
        
        plan = result["execution_plan"]
        
        # Should identify parallel execution opportunities
        parallel_groups = [step for step in plan["steps"] if step.get("parallel_group")]
        assert len(parallel_groups) >= 2  # At least some steps should be parallelizable

    @pytest.mark.parametrize("complexity_level", ["simple", "medium", "complex", "very_complex"])
    def test_plan_complexity_scaling(self, complexity_level):
        """Test plan generation scales with complexity"""
        planner = StageCPlanner()
        
        complexity_configs = {
            "simple": {"tools": 1, "min_steps": 1, "max_steps": 3},
            "medium": {"tools": 3, "min_steps": 3, "max_steps": 7},
            "complex": {"tools": 5, "min_steps": 5, "max_steps": 12},
            "very_complex": {"tools": 8, "min_steps": 8, "max_steps": 20}
        }
        
        config = complexity_configs[complexity_level]
        input_data = generate_test_input_for_complexity(config)
        
        result = planner.process(input_data)
        plan = result["execution_plan"]
        
        assert config["min_steps"] <= len(plan["steps"]) <= config["max_steps"]
        assert len(plan["rollback_steps"]) >= len(plan["steps"]) // 2  # At least half should have rollback
```

##### 2. Safety Mechanism Tests (25 tests)
```python
class TestSafetyMechanisms:
    
    def test_precondition_validation_generation(self):
        """Test generation of appropriate preconditions"""
        planner = StageCPlanner()
        
        input_data = {
            "decision": {"mode": "act", "intent": "service_restart"},
            "selected_tools": [{"name": "service_restarter", "type": "control"}],
            "risk_assessment": {"level": "medium"}
        }
        
        result = planner.process(input_data)
        
        # Should have preconditions for service restart
        preconditions = result["execution_plan"]["steps"][0]["preconditions"]
        assert any("service_exists" in pc["check"] for pc in preconditions)
        assert any("service_running" in pc["check"] for pc in preconditions)

    def test_rollback_procedure_generation(self):
        """Test generation of rollback procedures"""
        planner = StageCPlanner()
        
        input_data = {
            "decision": {"mode": "act", "intent": "configuration_update"},
            "selected_tools": [{"name": "config_updater", "type": "configuration"}],
            "risk_assessment": {"level": "high"}
        }
        
        result = planner.process(input_data)
        
        plan = result["execution_plan"]
        
        # High-risk operations should have detailed rollback procedures
        for step in plan["steps"]:
            if step["risk_level"] in ["high", "critical"]:
                assert "rollback_procedure" in step
                assert len(step["rollback_procedure"]["steps"]) > 0

    def test_safety_check_insertion(self):
        """Test insertion of safety checks in plans"""
        planner = StageCPlanner()
        
        input_data = {
            "decision": {"mode": "act", "intent": "database_migration"},
            "selected_tools": [{"name": "db_migrator", "type": "database"}],
            "risk_assessment": {"level": "critical"}
        }
        
        result = planner.process(input_data)
        
        plan = result["execution_plan"]
        
        # Critical operations should have safety checks
        safety_steps = [step for step in plan["steps"] if step["type"] == "safety_check"]
        assert len(safety_steps) >= 2  # Before and after main operation

    def test_failure_detection_mechanisms(self):
        """Test generation of failure detection mechanisms"""
        planner = StageCPlanner()
        
        input_data = {
            "decision": {"mode": "act", "intent": "deployment"},
            "selected_tools": [{"name": "deployer", "type": "deployment"}],
            "risk_assessment": {"level": "high"}
        }
        
        result = planner.process(input_data)
        
        plan = result["execution_plan"]
        
        # Should have failure detection for each critical step
        for step in plan["steps"]:
            if step["risk_level"] in ["high", "critical"]:
                assert "failure_detection" in step
                assert "timeout" in step["failure_detection"]
                assert "success_criteria" in step["failure_detection"]
```

##### 3. DAG Execution Tests (30 tests)
```python
class TestDAGExecution:
    
    def test_simple_dag_generation(self):
        """Test generation of simple DAG structures"""
        planner = StageCPlanner()
        
        input_data = {
            "decision": {"mode": "act", "intent": "canary_deployment"},
            "selected_tools": [
                {"name": "health_checker", "type": "monitoring"},
                {"name": "canary_deployer", "type": "deployment"},
                {"name": "traffic_shifter", "type": "networking"},
                {"name": "rollback_manager", "type": "deployment"}
            ],
            "risk_assessment": {"level": "high"}
        }
        
        result = planner.process(input_data)
        
        plan = result["execution_plan"]
        
        # Should create DAG with proper dependencies
        assert plan["execution_type"] == "dag"
        assert "dependencies" in plan
        
        # Verify dependency structure
        deps = plan["dependencies"]
        assert "health_checker" in deps["canary_deployer"]["depends_on"]
        assert "canary_deployer" in deps["traffic_shifter"]["depends_on"]

    def test_complex_dependency_resolution(self):
        """Test resolution of complex dependencies"""
        planner = StageCPlanner()
        
        # Complex scenario with multiple interdependencies
        input_data = create_complex_dag_scenario()
        
        result = planner.process(input_data)
        plan = result["execution_plan"]
        
        # Verify no circular dependencies
        assert not has_circular_dependencies(plan["dependencies"])
        
        # Verify all dependencies are satisfiable
        assert all_dependencies_satisfiable(plan["dependencies"], plan["steps"])

    def test_parallel_branch_execution(self):
        """Test parallel branch execution in DAG"""
        planner = StageCPlanner()
        
        input_data = {
            "decision": {"mode": "act", "intent": "multi_service_deployment"},
            "selected_tools": [
                {"name": "service_a_deployer", "type": "deployment", "service": "a"},
                {"name": "service_b_deployer", "type": "deployment", "service": "b"},
                {"name": "service_c_deployer", "type": "deployment", "service": "c"},
                {"name": "integration_tester", "type": "testing"}
            ],
            "risk_assessment": {"level": "high"}
        }
        
        result = planner.process(input_data)
        plan = result["execution_plan"]
        
        # Services A, B, C should be deployable in parallel
        parallel_deployments = find_parallel_groups(plan["dependencies"])
        assert len(parallel_deployments) >= 1
        assert all(service in parallel_deployments[0] 
                  for service in ["service_a_deployer", "service_b_deployer", "service_c_deployer"])

    def test_conditional_execution_branches(self):
        """Test conditional execution branches in DAG"""
        planner = StageCPlanner()
        
        input_data = {
            "decision": {"mode": "act", "intent": "conditional_deployment"},
            "selected_tools": [
                {"name": "environment_checker", "type": "monitoring"},
                {"name": "staging_deployer", "type": "deployment"},
                {"name": "production_deployer", "type": "deployment"},
                {"name": "rollback_manager", "type": "deployment"}
            ],
            "risk_assessment": {"level": "high"}
        }
        
        result = planner.process(input_data)
        plan = result["execution_plan"]
        
        # Should have conditional branches
        conditional_steps = [step for step in plan["steps"] if "condition" in step]
        assert len(conditional_steps) >= 2  # staging vs production deployment
        
        # Verify mutually exclusive conditions
        staging_condition = next(step["condition"] for step in conditional_steps 
                               if "staging" in step["tool"])
        production_condition = next(step["condition"] for step in conditional_steps 
                                  if "production" in step["tool"])
        assert staging_condition != production_condition
```

---

### PERFORMANCE TESTING SPECIFICATIONS

#### Load Testing Requirements
```python
# tests/performance/test_load_performance.py
class TestLoadPerformance:
    
    @pytest.mark.performance
    def test_single_stage_performance(self):
        """Test performance of individual stages under load"""
        stages = [StageAClassifier(), StageBSelector(), StageCPlanner()]
        
        for stage in stages:
            start_time = time.time()
            
            # Process 100 requests concurrently
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(stage.process, generate_test_input()) 
                          for _ in range(100)]
                results = [future.result() for future in futures]
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Performance requirements
            assert total_time < 30  # 100 requests in under 30 seconds
            assert all(result is not None for result in results)
            assert len(results) == 100

    @pytest.mark.performance
    def test_full_pipeline_performance(self):
        """Test performance of full pipeline under load"""
        pipeline = OpsConductorPipeline()
        
        test_requests = [generate_realistic_request() for _ in range(50)]
        
        start_time = time.time()
        results = []
        
        for request in test_requests:
            result = pipeline.process(request)
            results.append(result)
        
        end_time = time.time()
        avg_time_per_request = (end_time - start_time) / len(test_requests)
        
        # Performance requirements
        assert avg_time_per_request < 10  # Under 10 seconds per request
        assert all(result["status"] in ["success", "requires_approval"] for result in results)

    @pytest.mark.performance
    def test_concurrent_pipeline_performance(self):
        """Test concurrent pipeline performance"""
        pipeline = OpsConductorPipeline()
        
        def process_request():
            return pipeline.process(generate_realistic_request())
        
        start_time = time.time()
        
        # Process 20 requests concurrently
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(process_request) for _ in range(20)]
            results = [future.result() for future in futures]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should handle concurrent requests efficiently
        assert total_time < 60  # 20 concurrent requests in under 60 seconds
        assert len(results) == 20
        assert all(result is not None for result in results)
```

#### Memory and Resource Testing
```python
class TestResourceUsage:
    
    @pytest.mark.performance
    def test_memory_usage_limits(self):
        """Test memory usage stays within limits"""
        import psutil
        import gc
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        pipeline = OpsConductorPipeline()
        
        # Process many requests to test memory leaks
        for i in range(100):
            request = generate_test_request()
            result = pipeline.process(request)
            
            if i % 10 == 0:  # Check memory every 10 requests
                current_memory = process.memory_info().rss
                memory_growth = current_memory - initial_memory
                
                # Memory growth should be reasonable (under 100MB)
                assert memory_growth < 100 * 1024 * 1024
        
        # Force garbage collection and check final memory
        gc.collect()
        final_memory = process.memory_info().rss
        total_growth = final_memory - initial_memory
        
        # Total memory growth should be minimal (under 50MB)
        assert total_growth < 50 * 1024 * 1024

    @pytest.mark.performance
    def test_llm_connection_pooling(self):
        """Test LLM connection pooling efficiency"""
        classifier = StageAClassifier()
        
        # Process multiple requests and verify connection reuse
        start_time = time.time()
        
        for _ in range(20):
            result = classifier.process({"user_request": "Check system status"})
            assert result is not None
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # With connection pooling, should be much faster than 20 individual connections
        assert total_time < 40  # Under 2 seconds per request on average
```

## REGRESSION TEST STRATEGY

### Cumulative Test Execution
```python
# tests/regression/test_cumulative_regression.py
class TestCumulativeRegression:
    
    def test_phase_1_regression_after_phase_2(self):
        """Ensure Phase 1 functionality still works after Phase 2 implementation"""
        # Run all Phase 1 tests
        phase_1_results = run_test_suite("tests/phase_1/")
        assert phase_1_results.passed == phase_1_results.total
        
        # Run integration tests between Phase 1 and 2
        integration_results = run_test_suite("tests/integration/phase_1_2/")
        assert integration_results.passed == integration_results.total

    def test_full_system_regression(self):
        """Run complete regression test suite"""
        all_test_suites = [
            "tests/phase_0/",
            "tests/phase_1/", 
            "tests/phase_2/",
            "tests/phase_3/",
            "tests/integration/",
            "tests/performance/",
        ]
        
        for suite in all_test_suites:
            if os.path.exists(suite):  # Only test implemented phases
                results = run_test_suite(suite)
                assert results.passed == results.total, f"Regression failure in {suite}"
```

## TEST EXECUTION AUTOMATION

### Continuous Testing Pipeline
```yaml
# .github/workflows/newidea-testing.yml
name: NEWIDEA Architecture Testing

on:
  push:
    branches: [ newidea-transformation ]
  pull_request:
    branches: [ newidea-transformation ]

jobs:
  phase-testing:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        phase: [0, 1, 2, 3, 4, 5, 6]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements-test.txt
    
    - name: Run Phase ${{ matrix.phase }} Tests
      run: |
        pytest tests/phase_${{ matrix.phase }}/ -v --tb=short
        
    - name: Run Regression Tests
      run: |
        pytest tests/regression/phase_${{ matrix.phase }}_regression/ -v
  
  integration-testing:
    needs: phase-testing
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Run Integration Tests
      run: |
        pytest tests/integration/ -v --tb=short
    
    - name: Run Performance Tests
      run: |
        pytest tests/performance/ -v --tb=short -m "not slow"
  
  full-system-testing:
    needs: [phase-testing, integration-testing]
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Run Full System Tests
      run: |
        pytest tests/ -v --tb=short --cov=opsconductor --cov-report=html
    
    - name: Upload Coverage Reports
      uses: codecov/codecov-action@v3
```

## SUCCESS METRICS

### Test Coverage Requirements
- **Unit Test Coverage**: 95%+ for each stage
- **Integration Test Coverage**: 90%+ for stage combinations  
- **Edge Case Coverage**: 100% of identified edge cases tested
- **Performance Test Coverage**: All performance requirements validated

### Quality Gates
- **Zero Test Failures**: All tests must pass before phase completion
- **Performance Benchmarks**: All performance requirements must be met
- **Memory Limits**: No memory leaks or excessive resource usage
- **Documentation Coverage**: Every test documented with purpose and expected behavior

### Continuous Monitoring
- **Automated Test Execution**: Every code change triggers full test suite
- **Performance Regression Detection**: Automated performance comparison
- **Test Result Tracking**: Historical test result analysis
- **Coverage Trend Monitoring**: Test coverage trend analysis

This comprehensive test strategy ensures **EXHAUSTIVE VALIDATION** of every component in the NEWIDEA.MD architecture transformation with **100% REPEATABLE** test execution and **COMPLETE LIMITATION DISCOVERY**.