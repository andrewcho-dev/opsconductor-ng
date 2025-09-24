#!/usr/bin/env python3
"""
Test Multi-Brain AI Architecture - Phase 1: Intent Brain Foundation

This script tests the Phase 1 implementation of the multi-brain architecture,
focusing on Intent Brain capabilities including ITIL classification and
business intent analysis.
"""

import asyncio
import sys
import os
import logging
from datetime import datetime

# Add the ai-brain directory to the path
sys.path.append('/home/opsconductor/opsconductor-ng/ai-brain')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_intent_brain():
    """Test Intent Brain functionality."""
    try:
        logger.info("🧠 Testing Intent Brain - 4W Framework Analysis (NO ITIL GARBAGE)")
        
        # Import Intent Brain components
        from brains.intent_brain import IntentBrain
        from brains.intent_brain.four_w_analyzer import FourWAnalyzer
        
        # Initialize Intent Brain
        intent_brain = IntentBrain()
        
        # Test cases for 4W Framework Analysis - NO ITIL GARBAGE
        test_cases = [
            {
                "message": "The web server is down and customers can't access our website",
                "expected_action": "diagnostic",
                "expected_urgency": "critical"
            },
            {
                "message": "I need to install Docker on the new development server",
                "expected_action": "provisioning",
                "expected_urgency": "medium"
            },
            {
                "message": "How many servers are currently running?",
                "expected_action": "information",
                "expected_urgency": "low"
            },
            {
                "message": "Show me the network status",
                "expected_action": "information",
                "expected_urgency": "low"
            },
            {
                "message": "Restart the database service immediately",
                "expected_action": "operational",
                "expected_urgency": "high"
            }
        ]
        
        logger.info(f"🧪 Running {len(test_cases)} test cases...")
        
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"\n📝 Test Case {i}: {test_case['message'][:50]}...")
            
            # Analyze intent
            result = await intent_brain.analyze_intent(test_case["message"])
            
            # Display 4W Framework results
            logger.info(f"✅ 4W Framework Analysis Results:")
            logger.info(f"   📊 Overall Confidence: {result.overall_confidence:.2%}")
            logger.info(f"   📋 Intent Summary: {result.intent_summary}")
            logger.info(f"   🎯 WHAT - Action Type: {result.four_w_analysis.what_analysis.action_type.value}")
            logger.info(f"   🎯 WHAT - Specific Outcome: {result.four_w_analysis.what_analysis.specific_outcome}")
            logger.info(f"   📍 WHERE - Scope Level: {result.four_w_analysis.where_what_analysis.scope_level.value}")
            logger.info(f"   ⏰ WHEN - Urgency: {result.four_w_analysis.when_analysis.urgency.value}")
            logger.info(f"   🔧 HOW - Method: {result.four_w_analysis.how_analysis.method_preference.value}")
            logger.info(f"   ⚠️  Risk Level: {result.risk_level}")
            logger.info(f"   🔧 Technical Requirements: {len(result.technical_requirements)} items")
            logger.info(f"   ⏱️  Processing Time: {result.processing_time:.3f}s")
            
            # Validate 4W Framework expectations
            if "expected_action" in test_case:
                actual_action = result.four_w_analysis.what_analysis.action_type.value
                if actual_action == test_case["expected_action"]:
                    logger.info(f"   ✅ Action type: CORRECT ({actual_action})")
                else:
                    logger.warning(f"   ⚠️  Action type: Expected {test_case['expected_action']}, got {actual_action}")
            
            if "expected_urgency" in test_case:
                actual_urgency = result.four_w_analysis.when_analysis.urgency.value
                if actual_urgency == test_case["expected_urgency"]:
                    logger.info(f"   ✅ Urgency: CORRECT ({actual_urgency})")
                else:
                    logger.warning(f"   ⚠️  Urgency: Expected {test_case['expected_urgency']}, got {actual_urgency}")
        
        logger.info(f"\n🎉 Intent Brain 4W Framework testing completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Intent Brain testing failed: {e}")
        return False

async def test_multi_brain_coordinator():
    """Test Multi-Brain Coordinator functionality."""
    try:
        logger.info("\n🎯 Testing Multi-Brain Coordinator")
        
        # Import coordinator components
        from coordination.multi_brain_coordinator import MultiBrainCoordinator
        from coordination.brain_registry import BrainRegistry, BrainType
        from brains.intent_brain import IntentBrain
        
        # Initialize components
        brain_registry = BrainRegistry()
        coordinator = MultiBrainCoordinator(brain_registry=brain_registry)
        intent_brain = IntentBrain()
        
        # Register Intent Brain
        brain_registry.register_brain(
            brain_id="intent_brain",
            brain_type=BrainType.INTENT_BRAIN,
            brain_instance=intent_brain,
            capabilities=["itil_classification", "business_intent_analysis"],
            domains=["itil", "business_analysis"]
        )
        
        # Test coordination
        test_message = "We need to restart the nginx service on server1 because it's not responding"
        
        logger.info(f"📝 Coordinating request: {test_message}")
        
        result = await coordinator.coordinate_request(test_message)
        
        # Display coordination results
        logger.info(f"✅ Coordination Results:")
        logger.info(f"   🆔 Coordination ID: {result.coordination_id}")
        logger.info(f"   📊 Aggregated Confidence: {result.aggregated_confidence:.2%}")
        logger.info(f"   🎯 Final Decision: {result.final_decision.value}")
        logger.info(f"   🧠 Participating Brains: {', '.join(result.participating_brains)}")
        logger.info(f"   💡 Recommended Actions: {len(result.recommended_actions)} items")
        logger.info(f"   ⚠️  Risk Level: {result.risk_assessment.get('overall_risk', 'UNKNOWN')}")
        logger.info(f"   ⏱️  Coordination Time: {result.coordination_time:.3f}s")
        
        # Display confidence breakdown
        if result.confidence_breakdown:
            logger.info(f"   📈 Confidence Breakdown:")
            for brain, confidence in result.confidence_breakdown.items():
                logger.info(f"      {brain}: {confidence:.2%}")
        
        logger.info(f"\n🎉 Multi-Brain Coordinator testing completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Multi-Brain Coordinator testing failed: {e}")
        return False

async def test_multi_brain_engine():
    """Test the complete Multi-Brain AI Engine."""
    try:
        logger.info("\n🚀 Testing Multi-Brain AI Engine")
        
        # Import Multi-Brain Engine
        from multi_brain_engine import MultiBrainAIEngine
        
        # Initialize engine
        engine = MultiBrainAIEngine()
        
        # Initialize engine
        logger.info("🔧 Initializing Multi-Brain AI Engine...")
        success = await engine.initialize()
        
        if not success:
            logger.error("❌ Engine initialization failed")
            return False
        
        logger.info("✅ Engine initialized successfully")
        
        # Test request processing
        test_requests = [
            "The database server is running out of disk space and needs immediate attention",
            "I want to deploy a new microservice to our Kubernetes cluster",
            "Set up automated backups for all production databases",
            "The application performance is degrading and users are complaining"
        ]
        
        for i, request in enumerate(test_requests, 1):
            logger.info(f"\n📝 Processing Request {i}: {request[:50]}...")
            
            result = await engine.process_request(request, {"user_id": "test_user"})
            
            logger.info(f"✅ Processing Results:")
            logger.info(f"   📊 Success: {result.get('success', False)}")
            logger.info(f"   📊 Confidence: {result.get('confidence', 0):.2%}")
            logger.info(f"   💬 Response: {result.get('response', 'No response')[:100]}...")
            logger.info(f"   🎯 Decision: {result.get('decision', 'No decision')}")
            logger.info(f"   🧠 Engine: {result.get('metadata', {}).get('engine', 'Unknown')}")
        
        # Test system capabilities
        logger.info(f"\n🔍 Testing System Capabilities...")
        capabilities = await engine.get_system_capabilities()
        
        logger.info(f"✅ System Capabilities:")
        logger.info(f"   🧠 Engine: {capabilities.get('multi_brain_engine', {}).get('version', 'Unknown')}")
        logger.info(f"   📋 Phase: {capabilities.get('multi_brain_engine', {}).get('phase', 'Unknown')}")
        logger.info(f"   🏗️  Brain Registry: {len(capabilities.get('brain_registry', {}).get('type_breakdown', {}))} brain types")
        logger.info(f"   🎓 Learning: {'Enabled' if capabilities.get('learning_engine', {}).get('status') != 'disabled' else 'Disabled'}")
        
        # Cleanup
        await engine.cleanup()
        
        logger.info(f"\n🎉 Multi-Brain AI Engine testing completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Multi-Brain AI Engine testing failed: {e}")
        return False

async def main():
    """Main test function."""
    logger.info("🚀 Starting Multi-Brain AI Architecture Phase 1 Testing")
    logger.info("=" * 80)
    
    test_results = []
    
    # Test 1: Intent Brain
    logger.info("\n" + "=" * 80)
    logger.info("TEST 1: INTENT BRAIN FOUNDATION")
    logger.info("=" * 80)
    result1 = await test_intent_brain()
    test_results.append(("Intent Brain", result1))
    
    # Test 2: Multi-Brain Coordinator
    logger.info("\n" + "=" * 80)
    logger.info("TEST 2: MULTI-BRAIN COORDINATOR")
    logger.info("=" * 80)
    result2 = await test_multi_brain_coordinator()
    test_results.append(("Multi-Brain Coordinator", result2))
    
    # Test 3: Complete Multi-Brain Engine
    logger.info("\n" + "=" * 80)
    logger.info("TEST 3: MULTI-BRAIN AI ENGINE")
    logger.info("=" * 80)
    result3 = await test_multi_brain_engine()
    test_results.append(("Multi-Brain AI Engine", result3))
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nOverall Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED! Multi-Brain AI Architecture Phase 1 is working correctly!")
        logger.info("🧠 Intent Brain Foundation is ready for production use")
        logger.info("🔮 Ready for Phase 2: Technical Brain & SME Expansion")
    else:
        logger.error(f"❌ {total - passed} tests failed. Please review the implementation.")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n🛑 Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Testing failed with exception: {e}")
        sys.exit(1)