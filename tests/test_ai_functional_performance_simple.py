"""
Simplified AI Functional Performance Test Suite

This test suite evaluates the AI's actual performance across realistic operational scenarios.
Tests focus on real-world functionality rather than security edge cases.
"""

import pytest
import time
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass

# Import individual components for direct testing
from pipeline.stages.stage_a.intent_classifier import IntentClassifier
from pipeline.stages.stage_a.entity_extractor import EntityExtractor
from pipeline.stages.stage_a.confidence_scorer import ConfidenceScorer
from pipeline.stages.stage_a.risk_assessor import RiskAssessor
from pipeline.schemas.decision_v1 import RiskLevel
from llm.client import LLMClient


@dataclass
class TestScenario:
    """Represents a single test scenario"""
    id: str
    user_input: str
    expected_intent_category: str
    expected_intent_action: str
    expected_entities: List[Tuple[str, str]]  # (type, value) pairs
    expected_risk_level: RiskLevel
    expected_confidence_min: float
    description: str
    complexity_level: str  # simple, medium, complex, expert
    input_quality: str     # clean, messy, ambiguous, broken


class TestAIFunctionalPerformanceSimple:
    """Simplified AI functional performance testing"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Mock LLM client for testing
        from unittest.mock import MagicMock
        self.llm_client = MagicMock()
        
        # Set up components
        self.intent_classifier = IntentClassifier(self.llm_client)
        self.entity_extractor = EntityExtractor(self.llm_client)
        self.confidence_scorer = ConfidenceScorer(self.llm_client)
        self.risk_assessor = RiskAssessor(self.llm_client)
        
        # Track performance metrics
        self.performance_metrics = {
            'total_scenarios': 0,
            'successful_classifications': 0,
            'successful_extractions': 0,
            'avg_processing_time_ms': 0,
            'intent_accuracy': 0,
            'entity_accuracy': 0,
            'risk_assessment_accuracy': 0
        }
    
    def get_realistic_operational_scenarios(self) -> List[TestScenario]:
        """Generate realistic operational scenarios based on internal services"""
        scenarios = []
        
        # === MICROSERVICES MANAGEMENT ===
        microservices = [
            'user-service', 'auth-service', 'payment-service', 'notification-service',
            'inventory-service', 'order-service', 'shipping-service', 'analytics-service'
        ]
        
        # Clean, professional requests
        for service in microservices[:4]:
            scenarios.extend([
                TestScenario(
                    id=f"ms_clean_{service}_status",
                    user_input=f"Check the status of {service}",
                    expected_intent_category="monitor_system",
                    expected_intent_action="check_service_status",
                    expected_entities=[("service_name", service)],
                    expected_risk_level=RiskLevel.LOW,
                    expected_confidence_min=0.8,
                    description=f"Clean status check for {service}",
                    complexity_level="simple",
                    input_quality="clean"
                ),
                TestScenario(
                    id=f"ms_restart_{service}",
                    user_input=f"Restart the {service} please",
                    expected_intent_category="restart_service",
                    expected_intent_action="restart_service",
                    expected_entities=[("service_name", service)],
                    expected_risk_level=RiskLevel.MEDIUM,
                    expected_confidence_min=0.7,
                    description=f"Service restart for {service}",
                    complexity_level="medium",
                    input_quality="clean"
                ),
                TestScenario(
                    id=f"ms_logs_{service}",
                    user_input=f"Show me the logs for {service} from the last hour",
                    expected_intent_category="view_logs",
                    expected_intent_action="get_recent_logs",
                    expected_entities=[("service_name", service), ("time_range", "1 hour")],
                    expected_risk_level=RiskLevel.LOW,
                    expected_confidence_min=0.8,
                    description=f"Log viewing for {service}",
                    complexity_level="medium",
                    input_quality="clean"
                )
            ])
        
        # Messy, real-world requests
        scenarios.extend([
            TestScenario(
                id="ms_messy_user_service_issue",
                user_input="hey the user-service is acting up again, can u check whats wrong?? its been slow all morning",
                expected_intent_category="troubleshoot",
                expected_intent_action="investigate_performance",
                expected_entities=[("service_name", "user-service"), ("issue_type", "performance")],
                expected_risk_level=RiskLevel.LOW,
                expected_confidence_min=0.6,
                description="Messy troubleshooting request",
                complexity_level="medium",
                input_quality="messy"
            ),
            TestScenario(
                id="ms_urgent_payment_down",
                user_input="URGENT!!! payment-service is completely down, customers are complaining, need to fix ASAP!!!",
                expected_intent_category="troubleshoot",
                expected_intent_action="emergency_response",
                expected_entities=[("service_name", "payment-service"), ("severity", "critical")],
                expected_risk_level=RiskLevel.HIGH,
                expected_confidence_min=0.7,
                description="Urgent service outage",
                complexity_level="complex",
                input_quality="messy"
            )
        ])
        
        # === DATABASE OPERATIONS ===
        databases = ['user-db', 'product-db', 'order-db', 'analytics-db']
        
        for db in databases:
            scenarios.extend([
                TestScenario(
                    id=f"db_status_{db}",
                    user_input=f"Check if {db} is running and healthy",
                    expected_intent_category="monitor_system",
                    expected_intent_action="check_database_status",
                    expected_entities=[("database", db)],
                    expected_risk_level=RiskLevel.LOW,
                    expected_confidence_min=0.8,
                    description=f"Database health check for {db}",
                    complexity_level="simple",
                    input_quality="clean"
                ),
                TestScenario(
                    id=f"db_backup_{db}",
                    user_input=f"Create a backup of {db} before the maintenance window",
                    expected_intent_category="backup",
                    expected_intent_action="create_database_backup",
                    expected_entities=[("database", db), ("timing", "before_maintenance")],
                    expected_risk_level=RiskLevel.MEDIUM,
                    expected_confidence_min=0.8,
                    description=f"Database backup for {db}",
                    complexity_level="medium",
                    input_quality="clean"
                )
            ])
        
        # === INFRASTRUCTURE MONITORING ===
        servers = ['web-01', 'web-02', 'api-01', 'api-02', 'db-01', 'db-02']
        
        for server in servers:
            scenarios.extend([
                TestScenario(
                    id=f"infra_cpu_{server}",
                    user_input=f"Check CPU usage on {server}",
                    expected_intent_category="monitor_system",
                    expected_intent_action="check_cpu_usage",
                    expected_entities=[("hostname", server)],
                    expected_risk_level=RiskLevel.LOW,
                    expected_confidence_min=0.9,
                    description=f"CPU monitoring for {server}",
                    complexity_level="simple",
                    input_quality="clean"
                ),
                TestScenario(
                    id=f"infra_disk_{server}",
                    user_input=f"{server} disk space is getting low, can you check how much is left?",
                    expected_intent_category="monitor_system",
                    expected_intent_action="check_disk_usage",
                    expected_entities=[("hostname", server), ("issue_type", "disk_space")],
                    expected_risk_level=RiskLevel.MEDIUM,
                    expected_confidence_min=0.8,
                    description=f"Disk space check for {server}",
                    complexity_level="medium",
                    input_quality="messy"
                )
            ])
        
        # === DEPLOYMENT AND CONFIGURATION ===
        environments = ['dev', 'staging', 'prod']
        applications = ['web-app', 'api-gateway']
        
        for env in environments:
            for app in applications:
                scenarios.append(
                    TestScenario(
                        id=f"deploy_{app}_{env}",
                        user_input=f"Deploy {app} version 1.2.3 to {env} environment",
                        expected_intent_category="deployment",
                        expected_intent_action="deploy_application",
                        expected_entities=[
                            ("application", app),
                            ("version", "1.2.3"),
                            ("environment", env)
                        ],
                        expected_risk_level=RiskLevel.HIGH if env == 'prod' else RiskLevel.MEDIUM,
                        expected_confidence_min=0.8,
                        description=f"Application deployment: {app} to {env}",
                        complexity_level="medium",
                        input_quality="clean"
                    )
                )
        
        # === SECURITY AND COMPLIANCE ===
        scenarios.extend([
            TestScenario(
                id="security_ssl_expiry",
                user_input="SSL certificate for api.company.com expires in 7 days, need to renew it",
                expected_intent_category="security",
                expected_intent_action="renew_ssl_certificate",
                expected_entities=[
                    ("hostname", "api.company.com"),
                    ("certificate_type", "ssl"),
                    ("expiry_time", "7 days")
                ],
                expected_risk_level=RiskLevel.HIGH,
                expected_confidence_min=0.8,
                description="SSL certificate renewal",
                complexity_level="medium",
                input_quality="clean"
            ),
            TestScenario(
                id="security_failed_logins",
                user_input="seeing a lot of failed login attempts from IP 192.168.1.100, might be a brute force attack",
                expected_intent_category="security",
                expected_intent_action="investigate_security_threat",
                expected_entities=[
                    ("ip_address", "192.168.1.100"),
                    ("threat_type", "brute_force"),
                    ("event_type", "failed_logins")
                ],
                expected_risk_level=RiskLevel.HIGH,
                expected_confidence_min=0.8,
                description="Security threat investigation",
                complexity_level="complex",
                input_quality="messy"
            )
        ])
        
        # === NETWORK AND CONNECTIVITY ===
        scenarios.extend([
            TestScenario(
                id="network_connectivity_test",
                user_input="Test connectivity between web-01 and db-01",
                expected_intent_category="network",
                expected_intent_action="test_connectivity",
                expected_entities=[
                    ("source_host", "web-01"),
                    ("target_host", "db-01")
                ],
                expected_risk_level=RiskLevel.LOW,
                expected_confidence_min=0.9,
                description="Network connectivity test",
                complexity_level="simple",
                input_quality="clean"
            ),
            TestScenario(
                id="network_latency_issue",
                user_input="users are reporting slow response times, can you check network latency between the load balancer and api servers?",
                expected_intent_category="troubleshoot",
                expected_intent_action="investigate_network_latency",
                expected_entities=[
                    ("component", "load_balancer"),
                    ("component", "api_servers"),
                    ("issue_type", "latency")
                ],
                expected_risk_level=RiskLevel.MEDIUM,
                expected_confidence_min=0.7,
                description="Network latency investigation",
                complexity_level="medium",
                input_quality="messy"
            )
        ])
        
        # === AMBIGUOUS AND EDGE CASES ===
        scenarios.extend([
            TestScenario(
                id="ambiguous_something_wrong",
                user_input="something is wrong with the system, users are complaining",
                expected_intent_category="troubleshoot",
                expected_intent_action="general_investigation",
                expected_entities=[("issue_type", "user_complaints")],
                expected_risk_level=RiskLevel.MEDIUM,
                expected_confidence_min=0.4,
                description="Vague system issue report",
                complexity_level="complex",
                input_quality="ambiguous"
            ),
            TestScenario(
                id="ambiguous_performance",
                user_input="everything is slow today",
                expected_intent_category="troubleshoot",
                expected_intent_action="investigate_performance",
                expected_entities=[("issue_type", "performance")],
                expected_risk_level=RiskLevel.MEDIUM,
                expected_confidence_min=0.3,
                description="Vague performance complaint",
                complexity_level="medium",
                input_quality="ambiguous"
            ),
            TestScenario(
                id="typos_and_errors",
                user_input="chekc the staus of ngnix servce on web-01 plese",
                expected_intent_category="monitor_system",
                expected_intent_action="check_service_status",
                expected_entities=[
                    ("service_name", "nginx"),
                    ("hostname", "web-01")
                ],
                expected_risk_level=RiskLevel.LOW,
                expected_confidence_min=0.6,
                description="Request with multiple typos",
                complexity_level="simple",
                input_quality="broken"
            )
        ])
        
        return scenarios
    
    def test_intent_classification_rule_based_performance(self):
        """Test intent classification using rule-based fallback (works without LLM)"""
        scenarios = self.get_realistic_operational_scenarios()
        
        correct_classifications = 0
        total_scenarios = len(scenarios)
        processing_times = []
        
        print(f"\nTesting intent classification on {total_scenarios} scenarios...")
        
        for i, scenario in enumerate(scenarios):
            if i % 20 == 0:
                print(f"Progress: {i}/{total_scenarios} ({i/total_scenarios*100:.1f}%)")
            
            start_time = time.time()
            
            try:
                # Use rule-based classification (doesn't require LLM)
                intent = self.intent_classifier._rule_based_classification(scenario.user_input)
                
                processing_time = (time.time() - start_time) * 1000
                processing_times.append(processing_time)
                
                # Check intent classification accuracy
                if (intent.category == scenario.expected_intent_category and
                    intent.confidence >= scenario.expected_confidence_min):
                    correct_classifications += 1
                
            except Exception as e:
                print(f"Error processing scenario {scenario.id}: {e}")
                continue
        
        accuracy = correct_classifications / total_scenarios
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        print(f"\nIntent Classification Results:")
        print(f"Total scenarios: {total_scenarios}")
        print(f"Correct classifications: {correct_classifications}")
        print(f"Accuracy: {accuracy:.3f} ({accuracy*100:.1f}%)")
        print(f"Average processing time: {avg_processing_time:.2f}ms")
        
        # Update metrics
        self.performance_metrics['total_scenarios'] = total_scenarios
        self.performance_metrics['successful_classifications'] = correct_classifications
        self.performance_metrics['intent_accuracy'] = accuracy
        self.performance_metrics['avg_processing_time_ms'] = avg_processing_time
        
        # Assert minimum performance standards for rule-based system
        assert accuracy >= 0.6, f"Intent classification accuracy {accuracy:.3f} below minimum 0.6"
        assert avg_processing_time <= 50, f"Average processing time {avg_processing_time:.2f}ms too slow"
    
    def test_entity_extraction_rule_based_performance(self):
        """Test entity extraction using rule-based patterns (works without LLM)"""
        scenarios = self.get_realistic_operational_scenarios()
        
        correct_extractions = 0
        total_entities_expected = 0
        total_entities_found = 0
        
        print(f"\nTesting entity extraction on {len(scenarios)} scenarios...")
        
        for i, scenario in enumerate(scenarios):
            if i % 20 == 0:
                print(f"Progress: {i}/{len(scenarios)} ({i/len(scenarios)*100:.1f}%)")
            
            try:
                # Use rule-based extraction (doesn't require LLM)
                entities = self.entity_extractor._extract_with_patterns(scenario.user_input)
                
                # Count expected entities
                expected_entities = set(scenario.expected_entities)
                total_entities_expected += len(expected_entities)
                
                # Count found entities
                found_entities = set((entity.type, entity.value) for entity in entities)
                total_entities_found += len(found_entities)
                
                # Count correct matches
                correct_matches = len(expected_entities.intersection(found_entities))
                correct_extractions += correct_matches
                
            except Exception as e:
                print(f"Error processing scenario {scenario.id}: {e}")
                continue
        
        precision = correct_extractions / total_entities_found if total_entities_found > 0 else 0
        recall = correct_extractions / total_entities_expected if total_entities_expected > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        print(f"\nEntity Extraction Results:")
        print(f"Total entities expected: {total_entities_expected}")
        print(f"Total entities found: {total_entities_found}")
        print(f"Correct extractions: {correct_extractions}")
        print(f"Precision: {precision:.3f}")
        print(f"Recall: {recall:.3f}")
        print(f"F1 Score: {f1_score:.3f}")
        
        # Update metrics
        self.performance_metrics['successful_extractions'] = correct_extractions
        self.performance_metrics['entity_accuracy'] = f1_score
        
        # Assert minimum performance standards for rule-based system
        assert f1_score >= 0.4, f"Entity extraction F1 score {f1_score:.3f} below minimum 0.4"
        assert precision >= 0.3, f"Entity extraction precision {precision:.3f} below minimum 0.3"
    
    def test_risk_assessment_rule_based_performance(self):
        """Test risk assessment using rule-based logic (works without LLM)"""
        scenarios = self.get_realistic_operational_scenarios()
        
        correct_risk_assessments = 0
        total_scenarios = len(scenarios)
        
        print(f"\nTesting risk assessment on {total_scenarios} scenarios...")
        
        for i, scenario in enumerate(scenarios):
            if i % 20 == 0:
                print(f"Progress: {i}/{total_scenarios} ({i/total_scenarios*100:.1f}%)")
            
            try:
                # Create mock intent and entities for risk assessment
                from pipeline.schemas.decision_v1 import IntentV1, EntityV1
                
                intent = IntentV1(
                    category=scenario.expected_intent_category,
                    action=scenario.expected_intent_action,
                    confidence=0.8
                )
                
                entities = [
                    EntityV1(type=etype, value=evalue, confidence=0.8)
                    for etype, evalue in scenario.expected_entities
                ]
                
                # Use rule-based risk assessment
                risk_data = self.risk_assessor._rule_based_risk_assessment(
                    scenario.user_input, intent, entities
                )
                
                # Check if risk level matches expected
                if risk_data["risk_level"] == scenario.expected_risk_level:
                    correct_risk_assessments += 1
                
            except Exception as e:
                print(f"Error processing scenario {scenario.id}: {e}")
                continue
        
        accuracy = correct_risk_assessments / total_scenarios
        
        print(f"\nRisk Assessment Results:")
        print(f"Total scenarios: {total_scenarios}")
        print(f"Correct risk assessments: {correct_risk_assessments}")
        print(f"Accuracy: {accuracy:.3f} ({accuracy*100:.1f}%)")
        
        # Assert minimum performance standards for rule-based system
        assert accuracy >= 0.5, f"Risk assessment accuracy {accuracy:.3f} below minimum 0.5"
    
    def test_complexity_level_performance(self):
        """Test performance across different complexity levels"""
        scenarios = self.get_realistic_operational_scenarios()
        
        complexity_results = {
            'simple': {'total': 0, 'correct': 0, 'times': []},
            'medium': {'total': 0, 'correct': 0, 'times': []},
            'complex': {'total': 0, 'correct': 0, 'times': []},
            'expert': {'total': 0, 'correct': 0, 'times': []}
        }
        
        print(f"\nTesting performance by complexity level...")
        
        for scenario in scenarios:
            complexity = scenario.complexity_level
            complexity_results[complexity]['total'] += 1
            
            start_time = time.time()
            
            try:
                intent = self.intent_classifier._rule_based_classification(scenario.user_input)
                processing_time = (time.time() - start_time) * 1000
                complexity_results[complexity]['times'].append(processing_time)
                
                if (intent.category == scenario.expected_intent_category and
                    intent.confidence >= scenario.expected_confidence_min):
                    complexity_results[complexity]['correct'] += 1
                    
            except Exception as e:
                continue
        
        print(f"\nComplexity Level Results:")
        for level, results in complexity_results.items():
            if results['total'] > 0:
                accuracy = results['correct'] / results['total']
                avg_time = sum(results['times']) / len(results['times']) if results['times'] else 0
                print(f"{level.capitalize()}: {accuracy:.3f} accuracy, {avg_time:.2f}ms avg time ({results['total']} scenarios)")
        
        # Assert performance degrades gracefully with complexity
        simple_accuracy = complexity_results['simple']['correct'] / max(complexity_results['simple']['total'], 1)
        
        assert simple_accuracy >= 0.7, f"Simple scenario accuracy {simple_accuracy:.3f} too low"
    
    def test_input_quality_robustness(self):
        """Test robustness across different input quality levels"""
        scenarios = self.get_realistic_operational_scenarios()
        
        quality_results = {
            'clean': {'total': 0, 'correct': 0},
            'messy': {'total': 0, 'correct': 0},
            'ambiguous': {'total': 0, 'correct': 0},
            'broken': {'total': 0, 'correct': 0}
        }
        
        print(f"\nTesting robustness by input quality...")
        
        for scenario in scenarios:
            quality = scenario.input_quality
            quality_results[quality]['total'] += 1
            
            try:
                intent = self.intent_classifier._rule_based_classification(scenario.user_input)
                
                if (intent.category == scenario.expected_intent_category and
                    intent.confidence >= scenario.expected_confidence_min):
                    quality_results[quality]['correct'] += 1
                    
            except Exception as e:
                continue
        
        print(f"\nInput Quality Results:")
        for quality, results in quality_results.items():
            if results['total'] > 0:
                accuracy = results['correct'] / results['total']
                print(f"{quality.capitalize()}: {accuracy:.3f} accuracy ({results['total']} scenarios)")
        
        # Assert robustness standards
        clean_accuracy = quality_results['clean']['correct'] / max(quality_results['clean']['total'], 1)
        
        assert clean_accuracy >= 0.6, f"Clean input accuracy {clean_accuracy:.3f} too low"
    
    def test_performance_summary(self):
        """Generate comprehensive performance summary"""
        print(f"\n" + "="*60)
        print("AI FUNCTIONAL PERFORMANCE SUMMARY")
        print("="*60)
        
        # Run all tests to populate metrics
        self.test_intent_classification_rule_based_performance()
        self.test_entity_extraction_rule_based_performance()
        self.test_risk_assessment_rule_based_performance()
        
        metrics = self.performance_metrics
        
        print(f"Total Scenarios Tested: {metrics['total_scenarios']}")
        print(f"Intent Classification Accuracy: {metrics['intent_accuracy']:.3f} ({metrics['intent_accuracy']*100:.1f}%)")
        print(f"Entity Extraction Accuracy: {metrics['entity_accuracy']:.3f} ({metrics['entity_accuracy']*100:.1f}%)")
        print(f"Average Processing Time: {metrics['avg_processing_time_ms']:.2f}ms")
        
        # Overall grade
        overall_score = (
            metrics['intent_accuracy'] * 0.4 +
            metrics['entity_accuracy'] * 0.4 +
            (1.0 if metrics['avg_processing_time_ms'] < 100 else 0.5) * 0.2
        )
        
        print(f"\nOverall AI Performance Score: {overall_score:.3f} ({overall_score*100:.1f}%)")
        
        if overall_score >= 0.7:
            grade = "GOOD"
        elif overall_score >= 0.5:
            grade = "ACCEPTABLE"
        else:
            grade = "NEEDS IMPROVEMENT"
        
        print(f"Performance Grade: {grade}")
        print("="*60)
        
        # Assert overall performance standards for rule-based system
        assert overall_score >= 0.5, f"Overall AI performance score {overall_score:.3f} below minimum 0.5"


# Run individual test methods for comprehensive coverage
if __name__ == "__main__":
    test_suite = TestAIFunctionalPerformanceSimple()
    test_suite.setup_method()
    
    print("Starting AI functional performance testing...")
    print("This will test realistic operational scenarios using rule-based AI components")
    
    # Run all tests
    test_suite.test_performance_summary()
    
    print("\nAll AI functional performance tests completed!")