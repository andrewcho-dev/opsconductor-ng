#!/usr/bin/env python3
"""
Comprehensive test to verify that the AI system fully knows about network analyzer capabilities.

This test validates that:
1. Network analyzer knowledge is properly loaded in the AI brain
2. The LLM conversation handler includes network analysis in its system prompt
3. Service capabilities include network analyzer services
4. Workflow generator can create network analysis workflows
5. Intent processor recognizes network analysis patterns
6. The AI can provide intelligent network troubleshooting recommendations
"""

import sys
import os
import asyncio
import logging
from typing import Dict, Any

# Add the ai-brain directory to the Python path
sys.path.insert(0, '/home/opsconductor/opsconductor-ng/ai-brain')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NetworkAnalyzerAIKnowledgeTest:
    """Test suite for network analyzer AI knowledge integration"""
    
    def __init__(self):
        self.test_results = []
        self.passed_tests = 0
        self.total_tests = 0
    
    def log_test_result(self, test_name: str, passed: bool, details: str = ""):
        """Log a test result"""
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            logger.info(f"✅ {test_name}: PASSED {details}")
        else:
            logger.error(f"❌ {test_name}: FAILED {details}")
        
        self.test_results.append({
            'test': test_name,
            'passed': passed,
            'details': details
        })
    
    async def test_brain_engine_knowledge_loading(self):
        """Test that the brain engine properly loads network analyzer knowledge"""
        try:
            from brain_engine import AIBrainEngine
            
            # Initialize brain engine
            brain = AIBrainEngine()
            
            # Check if network analyzer knowledge is loaded
            has_network_knowledge = hasattr(brain, 'network_analyzer_knowledge')
            
            if has_network_knowledge:
                # Test accessing network analyzer capabilities
                capabilities = brain.network_analyzer_knowledge.capabilities
                has_packet_capture = 'packet_capture' in capabilities
                has_monitoring = 'real_time_monitoring' in capabilities
                has_protocol_analysis = 'protocol_analysis' in capabilities
                has_ai_analysis = 'ai_anomaly_detection' in capabilities
                has_remote_analysis = 'remote_analysis' in capabilities
                
                all_capabilities_present = all([
                    has_packet_capture, has_monitoring, has_protocol_analysis,
                    has_ai_analysis, has_remote_analysis
                ])
                
                self.log_test_result(
                    "Brain Engine Network Knowledge Loading",
                    all_capabilities_present,
                    f"Capabilities: packet_capture={has_packet_capture}, monitoring={has_monitoring}, "
                    f"protocol_analysis={has_protocol_analysis}, ai_analysis={has_ai_analysis}, "
                    f"remote_analysis={has_remote_analysis}"
                )
            else:
                self.log_test_result(
                    "Brain Engine Network Knowledge Loading",
                    False,
                    "network_analyzer_knowledge attribute not found in brain engine"
                )
                
        except Exception as e:
            self.log_test_result(
                "Brain Engine Network Knowledge Loading",
                False,
                f"Exception: {str(e)}"
            )
    
    async def test_llm_conversation_handler_system_prompt(self):
        """Test that the LLM conversation handler includes network analysis in system prompt"""
        try:
            from llm_conversation_handler import LLMConversationHandler
            from integrations.llm_client import LLMEngine
            
            # Create a mock LLM engine
            llm_engine = LLMEngine("http://localhost:11434", "test-model")
            
            # Initialize conversation handler
            handler = LLMConversationHandler(llm_engine)
            
            # Check system prompt for network analysis content
            system_prompt = handler.system_prompt.lower()
            
            network_keywords = [
                'network analysis',
                'packet capture',
                'protocol analysis',
                'anomaly detection',
                'network troubleshooting',
                'tcpdump',
                'tshark',
                'scapy'
            ]
            
            found_keywords = [keyword for keyword in network_keywords if keyword in system_prompt]
            coverage_percentage = (len(found_keywords) / len(network_keywords)) * 100
            
            self.log_test_result(
                "LLM System Prompt Network Knowledge",
                len(found_keywords) >= 6,  # At least 75% coverage
                f"Found {len(found_keywords)}/{len(network_keywords)} keywords ({coverage_percentage:.1f}%): {found_keywords}"
            )
            
        except Exception as e:
            self.log_test_result(
                "LLM System Prompt Network Knowledge",
                False,
                f"Exception: {str(e)}"
            )
    
    async def test_service_capabilities_network_analyzer(self):
        """Test that service capabilities include network analyzer"""
        try:
            from system_model.service_capabilities import ServiceCapabilitiesManager
            
            manager = ServiceCapabilitiesManager()
            capabilities = manager.get_all_capabilities()
            
            # Check for network analyzer service
            has_network_analyzer = 'network-analyzer-service' in capabilities
            
            if has_network_analyzer:
                network_service = capabilities['network-analyzer-service']
                required_capabilities = [
                    'packet_analysis', 'network_monitoring', 'protocol_analysis',
                    'ai_network_analysis', 'remote_analysis'
                ]
                
                service_capabilities = network_service.get('capabilities', [])
                found_capabilities = [cap for cap in required_capabilities if cap in service_capabilities]
                
                self.log_test_result(
                    "Service Capabilities Network Analyzer",
                    len(found_capabilities) == len(required_capabilities),
                    f"Found {len(found_capabilities)}/{len(required_capabilities)} capabilities: {found_capabilities}"
                )
            else:
                self.log_test_result(
                    "Service Capabilities Network Analyzer",
                    False,
                    "network-analyzer-service not found in capabilities"
                )
                
        except Exception as e:
            self.log_test_result(
                "Service Capabilities Network Analyzer",
                False,
                f"Exception: {str(e)}"
            )
    
    async def test_workflow_generator_network_analysis(self):
        """Test that workflow generator can create network analysis workflows"""
        try:
            from job_engine.workflow_generator import WorkflowGenerator
            
            generator = WorkflowGenerator()
            
            # Check for network analysis workflow types
            workflow_types = generator.workflow_types
            network_workflow_types = [
                'NETWORK_ANALYSIS', 'NETWORK_MONITORING', 'NETWORK_TROUBLESHOOTING'
            ]
            
            found_workflow_types = [wt for wt in network_workflow_types if hasattr(generator.workflow_types, wt)]
            
            # Check for network analysis step types
            step_types = generator.step_types
            network_step_types = [
                'NETWORK_CAPTURE', 'NETWORK_MONITOR', 'PROTOCOL_ANALYSIS', 'AI_NETWORK_DIAGNOSIS'
            ]
            
            found_step_types = [st for st in network_step_types if hasattr(generator.step_types, st)]
            
            total_found = len(found_workflow_types) + len(found_step_types)
            total_expected = len(network_workflow_types) + len(network_step_types)
            
            self.log_test_result(
                "Workflow Generator Network Analysis",
                total_found >= (total_expected * 0.75),  # At least 75% coverage
                f"Workflow types: {found_workflow_types}, Step types: {found_step_types}"
            )
            
        except Exception as e:
            self.log_test_result(
                "Workflow Generator Network Analysis",
                False,
                f"Exception: {str(e)}"
            )
    
    async def test_intent_processor_network_patterns(self):
        """Test that intent processor recognizes network analysis patterns"""
        try:
            from processing.intent_processor import IntentProcessor
            
            processor = IntentProcessor()
            
            # Check for network analysis intent patterns
            intent_patterns = processor.intent_patterns
            
            network_intents = [
                'network_analysis', 'packet_capture', 'protocol_analysis',
                'network_monitoring', 'network_troubleshooting'
            ]
            
            found_intents = []
            for intent_type, patterns in intent_patterns.items():
                if any(network_intent in intent_type.lower() for network_intent in network_intents):
                    found_intents.append(intent_type)
            
            # Also check pattern descriptions for network-related content
            network_pattern_count = 0
            for patterns in intent_patterns.values():
                for pattern in patterns:
                    pattern_text = pattern.get('description', '').lower()
                    if any(keyword in pattern_text for keyword in ['network', 'packet', 'protocol', 'bandwidth']):
                        network_pattern_count += 1
            
            self.log_test_result(
                "Intent Processor Network Patterns",
                len(found_intents) > 0 or network_pattern_count > 0,
                f"Network intent types: {found_intents}, Network patterns: {network_pattern_count}"
            )
            
        except Exception as e:
            self.log_test_result(
                "Intent Processor Network Patterns",
                False,
                f"Exception: {str(e)}"
            )
    
    async def test_network_knowledge_accessibility(self):
        """Test that network analyzer knowledge is accessible and functional"""
        try:
            from knowledge_engine.network_analyzer_knowledge import network_analyzer_knowledge
            
            # Test capability access
            capabilities = network_analyzer_knowledge.capabilities
            capability_count = len(capabilities)
            
            # Test troubleshooting scenarios
            scenarios = network_analyzer_knowledge.troubleshooting_scenarios
            scenario_count = len(scenarios)
            
            # Test protocol knowledge
            protocol_knowledge = network_analyzer_knowledge.protocol_knowledge
            protocol_count = len(protocol_knowledge)
            
            # Test use case patterns
            use_cases = network_analyzer_knowledge.use_case_patterns
            use_case_count = len(use_cases)
            
            # Test specific methods
            tcp_knowledge = network_analyzer_knowledge.get_protocol_knowledge('tcp')
            has_tcp_knowledge = tcp_knowledge is not None
            
            # Test workflow recommendation
            workflow = network_analyzer_knowledge.recommend_analysis_workflow(
                'performance_troubleshooting',
                ['slow response times', 'high latency']
            )
            has_workflow_recommendation = len(workflow) > 0
            
            all_tests_passed = all([
                capability_count >= 5,
                scenario_count >= 4,
                protocol_count >= 4,
                use_case_count >= 3,
                has_tcp_knowledge,
                has_workflow_recommendation
            ])
            
            self.log_test_result(
                "Network Knowledge Accessibility",
                all_tests_passed,
                f"Capabilities: {capability_count}, Scenarios: {scenario_count}, "
                f"Protocols: {protocol_count}, Use cases: {use_case_count}, "
                f"TCP knowledge: {has_tcp_knowledge}, Workflow rec: {has_workflow_recommendation}"
            )
            
        except Exception as e:
            self.log_test_result(
                "Network Knowledge Accessibility",
                False,
                f"Exception: {str(e)}"
            )
    
    async def test_ai_network_troubleshooting_intelligence(self):
        """Test AI's ability to provide intelligent network troubleshooting recommendations"""
        try:
            from knowledge_engine.network_analyzer_knowledge import network_analyzer_knowledge
            
            # Test scenario-based recommendations
            symptoms = ['slow response times', 'connection timeouts', 'high latency']
            relevant_scenarios = network_analyzer_knowledge.get_troubleshooting_scenarios(symptoms)
            
            # Test AI suggestions based on mock analysis results
            mock_results = {
                'packet_loss': 5.2,
                'latency': 150,
                'anomalies': ['unusual_traffic_pattern'],
                'protocol_errors': ['tcp_retransmissions']
            }
            
            ai_suggestions = network_analyzer_knowledge.get_ai_suggestions(mock_results)
            
            has_relevant_scenarios = len(relevant_scenarios) > 0
            has_ai_suggestions = len(ai_suggestions) > 0
            suggestions_are_relevant = any(
                keyword in ' '.join(ai_suggestions).lower() 
                for keyword in ['packet loss', 'latency', 'anomal', 'protocol']
            )
            
            self.log_test_result(
                "AI Network Troubleshooting Intelligence",
                has_relevant_scenarios and has_ai_suggestions and suggestions_are_relevant,
                f"Scenarios: {len(relevant_scenarios)}, Suggestions: {len(ai_suggestions)}, "
                f"Relevant: {suggestions_are_relevant}"
            )
            
        except Exception as e:
            self.log_test_result(
                "AI Network Troubleshooting Intelligence",
                False,
                f"Exception: {str(e)}"
            )
    
    async def run_all_tests(self):
        """Run all network analyzer AI knowledge tests"""
        logger.info("🚀 Starting Network Analyzer AI Knowledge Tests")
        logger.info("=" * 60)
        
        # Run all tests
        await self.test_brain_engine_knowledge_loading()
        await self.test_llm_conversation_handler_system_prompt()
        await self.test_service_capabilities_network_analyzer()
        await self.test_workflow_generator_network_analysis()
        await self.test_intent_processor_network_patterns()
        await self.test_network_knowledge_accessibility()
        await self.test_ai_network_troubleshooting_intelligence()
        
        # Print summary
        logger.info("=" * 60)
        logger.info(f"🏁 Test Summary: {self.passed_tests}/{self.total_tests} tests passed")
        
        if self.passed_tests == self.total_tests:
            logger.info("🎉 ALL TESTS PASSED! The AI system fully knows about network analyzer capabilities.")
        else:
            logger.warning(f"⚠️  {self.total_tests - self.passed_tests} tests failed. AI system knowledge may be incomplete.")
        
        return self.passed_tests == self.total_tests

async def main():
    """Main test execution"""
    test_suite = NetworkAnalyzerAIKnowledgeTest()
    success = await test_suite.run_all_tests()
    
    if success:
        print("\n✅ CONCLUSION: The AI system fully knows about the network analyzer capabilities!")
        print("The AI can now intelligently recommend network analysis workflows,")
        print("provide troubleshooting guidance, and utilize all network analyzer features.")
    else:
        print("\n❌ CONCLUSION: The AI system has incomplete knowledge about network analyzer capabilities.")
        print("Some components may need additional integration work.")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)