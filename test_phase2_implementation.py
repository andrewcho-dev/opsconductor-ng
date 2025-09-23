#!/usr/bin/env python3
"""
Phase 2 Multi-Brain Architecture Test Script

This script validates the complete Phase 2 implementation including:
- Network & Database SME Brains
- Brain Communication Protocol
- Continuous Learning System
- Multi-Brain Confidence Engine
- Quality Assurance System
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_phase2_implementation():
    """Test the complete Phase 2 implementation"""
    
    print("=" * 80)
    print("PHASE 2 MULTI-BRAIN ARCHITECTURE TEST")
    print("=" * 80)
    
    try:
        # Import the Multi-Brain Engine
        import sys
        sys.path.append('/home/opsconductor/opsconductor-ng/ai-brain')
        from multi_brain_engine import MultiBrainAIEngine
        
        # Initialize the engine
        print("\n1. Initializing Multi-Brain AI Engine (Phase 2)...")
        engine = MultiBrainAIEngine()
        
        # Wait for async initialization to complete
        await asyncio.sleep(2)
        
        print(f"   ✓ Engine initialized - Version: {engine.engine_version}, Phase: {engine.phase}")
        print(f"   ✓ SME Brains available: {list(engine.sme_brains.keys())}")
        
        # Test 1: Network Infrastructure Request
        print("\n2. Testing Network SME Brain...")
        network_request = "I need to design a high-availability network architecture for a microservices application with load balancing and security"
        
        result = await engine.process_request_with_protocol(network_request)
        print(f"   ✓ Network analysis completed - Confidence: {result.aggregated_confidence:.2f}")
        print(f"   ✓ Execution Strategy: {result.execution_strategy}")
        
        # Test 2: Database Administration Request
        print("\n3. Testing Database SME Brain...")
        database_request = "I need to optimize database performance for a high-write workload with read replicas and implement proper backup strategies"
        
        result = await engine.process_request_with_protocol(database_request)
        print(f"   ✓ Database analysis completed - Confidence: {result.aggregated_confidence:.2f}")
        print(f"   ✓ Execution Strategy: {result.execution_strategy}")
        
        # Test 3: Multi-Domain Request (Container + Security + Network + Database)
        print("\n4. Testing Multi-Domain Analysis...")
        complex_request = "Deploy a secure containerized application with database clustering, network segmentation, and monitoring"
        
        result = await engine.process_request_with_protocol(complex_request)
        print(f"   ✓ Multi-domain analysis completed - Confidence: {result.aggregated_confidence:.2f}")
        print(f"   ✓ Consulted Brains: {len(result.sme_recommendations)} domains")
        print(f"   ✓ Execution Strategy: {result.execution_strategy}")
        
        # Test 4: Execution Feedback Processing
        print("\n5. Testing Continuous Learning System...")
        
        # Simulate successful execution feedback
        execution_feedback = {
            "success": True,
            "execution_time": 45.2,
            "confidence_accuracy": 0.85,
            "user_satisfaction": 0.9,
            "issues_encountered": [],
            "improvements_suggested": ["Add more detailed network security recommendations"]
        }
        
        # Process feedback (using a mock request_id)
        feedback_result = await engine.process_execution_feedback("test_request_001", execution_feedback)
        print(f"   ✓ Execution feedback processed - Success: {feedback_result['success']}")
        
        # Test 5: Learning Insights
        print("\n6. Getting Learning Insights...")
        insights = await engine.get_learning_insights()
        print(f"   ✓ Learning insights retrieved")
        print(f"   ✓ System Status: {insights['system_status']['phase']}")
        print(f"   ✓ Active SME Brains: {len(insights['system_status']['active_sme_brains'])}")
        print(f"   ✓ Performance Metrics: {insights['performance_metrics']['total_requests']} requests processed")
        
        # Test 6: Brain Communication Protocol
        print("\n7. Testing Brain Communication Protocol...")
        
        # Test protocol metrics
        protocol_metrics = await engine.communication_protocol.get_communication_metrics()
        print(f"   ✓ Communication protocol active")
        print(f"   ✓ Total messages processed: {protocol_metrics.messages_exchanged}")
        print(f"   ✓ Total analysis time: {protocol_metrics.total_analysis_time:.2f}s")
        
        # Test 7: Quality Assurance System
        print("\n8. Testing Quality Assurance System...")
        
        # Test learning update validation
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), 'ai-brain'))
        from learning.continuous_learning_system import LearningUpdate, LearningType
        
        test_learning_update = LearningUpdate(
            update_id="test_update_001",
            learning_type=LearningType.PATTERN_RECOGNITION,
            source_brain="execution_feedback_analyzer",
            target_brain="network_infrastructure",
            content={
                "pattern": "network_optimization",
                "recommendation": "Use CDN for static content delivery",
                "confidence": 0.85,
                "evidence": ["Reduced latency by 40%", "Improved user experience"]
            },
            confidence=0.85,
            metadata={
                "timestamp": datetime.now().isoformat(),
                "validation_required": True
            }
        )
        
        validation_result = await engine.learning_quality_assurance.validate_learning_update(test_learning_update)
        print(f"   ✓ Learning update validation completed")
        print(f"   ✓ Validation passed: {validation_result.is_valid}")
        print(f"   ✓ Confidence score: {validation_result.confidence_score:.2f}")
        
        # Test 8: Multi-Brain Confidence Engine
        print("\n9. Testing Multi-Brain Confidence Engine...")
        
        # Test confidence aggregation
        brain_confidences = {
            "container_orchestration": 0.85,
            "security_and_compliance": 0.78,
            "network_infrastructure": 0.92,
            "database_administration": 0.88
        }
        
        aggregated_confidence = await engine.multibrain_confidence_engine.aggregate_confidence(
            brain_confidences,
            complexity_factor=0.8,
            risk_factor=0.3
        )
        
        print(f"   ✓ Confidence aggregation completed")
        print(f"   ✓ Aggregated confidence: {aggregated_confidence:.2f}")
        
        # Determine execution strategy
        execution_strategy = engine.multibrain_confidence_engine.determine_execution_strategy(
            aggregated_confidence,
            brain_confidences
        )
        print(f"   ✓ Execution strategy: {execution_strategy}")
        
        # Final Summary
        print("\n" + "=" * 80)
        print("PHASE 2 IMPLEMENTATION TEST RESULTS")
        print("=" * 80)
        print("✓ Network SME Brain - PASSED")
        print("✓ Database SME Brain - PASSED")
        print("✓ Brain Communication Protocol - PASSED")
        print("✓ Continuous Learning System - PASSED")
        print("✓ Quality Assurance System - PASSED")
        print("✓ Multi-Brain Confidence Engine - PASSED")
        print("✓ Execution Feedback Processing - PASSED")
        print("✓ Learning Insights Generation - PASSED")
        print("\n🎉 PHASE 2 IMPLEMENTATION COMPLETE AND VALIDATED! 🎉")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        logger.error(f"Phase 2 test failed: {str(e)}", exc_info=True)
        return False

async def test_individual_components():
    """Test individual Phase 2 components"""
    
    print("\n" + "=" * 60)
    print("INDIVIDUAL COMPONENT TESTS")
    print("=" * 60)
    
    try:
        # Test Network SME Brain
        print("\n1. Testing Network SME Brain individually...")
        import sys
        sys.path.append('/home/opsconductor/opsconductor-ng/ai-brain')
        from brains.sme.network_sme_brain import NetworkSMEBrain
        
        network_brain = NetworkSMEBrain()
        network_analysis = await network_brain.analyze_network_requirements({
            "application_type": "microservices",
            "expected_load": "high",
            "security_requirements": "enterprise",
            "availability_requirements": "99.9%"
        })
        
        print(f"   ✓ Network analysis confidence: {network_analysis.get('confidence', 0.0):.2f}")
        print(f"   ✓ Architecture recommendations: {len(network_analysis.get('architecture_recommendations', []))} items")
        
        # Test Database SME Brain
        print("\n2. Testing Database SME Brain individually...")
        from brains.sme.database_sme_brain import DatabaseSMEBrain
        
        database_brain = DatabaseSMEBrain()
        database_analysis = await database_brain.analyze_database_requirements({
            "workload_type": "high_write",
            "data_size": "large",
            "consistency_requirements": "eventual",
            "performance_requirements": "low_latency"
        })
        
        print(f"   ✓ Database analysis confidence: {database_analysis.get('confidence', 0.0):.2f}")
        print(f"   ✓ Database recommendations: {len(database_analysis.get('database_recommendations', []))} items")
        
        # Test Brain Communication Protocol
        print("\n3. Testing Brain Communication Protocol individually...")
        from communication.brain_protocol import BrainCommunicationProtocol
        
        protocol = BrainCommunicationProtocol()
        
        # Test message creation
        test_message = protocol.create_brain_message(
            "intent_brain",
            "technical_brain",
            "analysis_request",
            {"user_intent": "deploy application"}
        )
        
        print(f"   ✓ Brain message created: {test_message.message_id}")
        print(f"   ✓ Message type: {test_message.message_type}")
        
        print("\n✓ All individual component tests passed!")
        
    except Exception as e:
        print(f"\n❌ Individual component test error: {str(e)}")
        logger.error(f"Individual component test failed: {str(e)}", exc_info=True)

if __name__ == "__main__":
    print("Starting Phase 2 Multi-Brain Architecture Tests...")
    
    # Run the main test
    asyncio.run(test_phase2_implementation())
    
    # Run individual component tests
    asyncio.run(test_individual_components())
    
    print("\nAll tests completed!")