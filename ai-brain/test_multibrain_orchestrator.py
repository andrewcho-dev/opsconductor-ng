"""
Multi-Brain System Orchestrator Test
Tests the complete Phase 3 multi-brain orchestration system
"""

import asyncio
import logging
from datetime import datetime
import json

# Import the orchestrator and related components
from orchestration.multibrain_orchestrator import (
    MultibrainOrchestrator,
    ProcessingContext,
    ProcessingStrategy
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultibrainOrchestratorTest:
    """Test suite for the multi-brain orchestrator system"""
    
    def __init__(self):
        self.test_results = []
        self.orchestrator = MultibrainOrchestrator()
    
    async def test_sequential_processing(self):
        """Test sequential processing strategy"""
        logger.info("➡️  Testing Sequential Processing...")
        
        try:
            context = ProcessingContext(
                user_id="test_user",
                session_id="test_session_seq",
                request_timestamp=datetime.now(),
                priority_level="normal"
            )
            
            result = await self.orchestrator.process_request(
                "Show me the status of all servers in the production environment",
                context
            )
            
            success = (
                result.success and
                result.processing_strategy == ProcessingStrategy.SEQUENTIAL and
                len(result.brain_responses) > 0 and
                result.confidence_score > 0.0
            )
            
            self.test_results.append({
                "test": "Sequential Processing",
                "success": success,
                "strategy": result.processing_strategy.value,
                "brain_count": len(result.brain_responses),
                "confidence": result.confidence_score,
                "processing_time": result.total_processing_time,
                "details": f"Processed with {len(result.brain_responses)} brains"
            })
            
            logger.info(f"✅ Sequential Processing: {result.confidence_score:.2f} confidence")
            
        except Exception as e:
            self.test_results.append({
                "test": "Sequential Processing",
                "success": False,
                "error": str(e)
            })
            logger.error(f"❌ Sequential Processing failed: {e}")
    
    async def test_parallel_processing(self):
        """Test parallel processing strategy"""
        logger.info("🔄 Testing Parallel Processing...")
        
        try:
            context = ProcessingContext(
                user_id="test_user",
                session_id="test_session_par",
                request_timestamp=datetime.now(),
                priority_level="critical"  # Critical priority triggers parallel
            )
            
            result = await self.orchestrator.process_request(
                "Urgent: Analyze network performance issues and provide immediate recommendations",
                context
            )
            
            success = (
                result.success and
                result.processing_strategy == ProcessingStrategy.PARALLEL and
                len(result.brain_responses) > 0 and
                result.confidence_score > 0.0
            )
            
            self.test_results.append({
                "test": "Parallel Processing",
                "success": success,
                "strategy": result.processing_strategy.value,
                "brain_count": len(result.brain_responses),
                "confidence": result.confidence_score,
                "processing_time": result.total_processing_time,
                "details": f"Processed with {len(result.brain_responses)} brains in parallel"
            })
            
            logger.info(f"✅ Parallel Processing: {result.confidence_score:.2f} confidence")
            
        except Exception as e:
            self.test_results.append({
                "test": "Parallel Processing",
                "success": False,
                "error": str(e)
            })
            logger.error(f"❌ Parallel Processing failed: {e}")
    
    async def test_hierarchical_processing(self):
        """Test hierarchical processing strategy"""
        logger.info("🏗️  Testing Hierarchical Processing...")
        
        try:
            context = ProcessingContext(
                user_id="test_user",
                session_id="test_session_hier",
                request_timestamp=datetime.now(),
                priority_level="high"
            )
            
            result = await self.orchestrator.process_request(
                "Integrate multiple monitoring systems and coordinate security policies across cloud environments",
                context
            )
            
            success = (
                result.success and
                result.processing_strategy == ProcessingStrategy.HIERARCHICAL and
                len(result.brain_responses) > 0 and
                result.confidence_score > 0.0
            )
            
            self.test_results.append({
                "test": "Hierarchical Processing",
                "success": success,
                "strategy": result.processing_strategy.value,
                "brain_count": len(result.brain_responses),
                "confidence": result.confidence_score,
                "processing_time": result.total_processing_time,
                "details": f"Processed hierarchically with {len(result.brain_responses)} brains"
            })
            
            logger.info(f"✅ Hierarchical Processing: {result.confidence_score:.2f} confidence")
            
        except Exception as e:
            self.test_results.append({
                "test": "Hierarchical Processing",
                "success": False,
                "error": str(e)
            })
            logger.error(f"❌ Hierarchical Processing failed: {e}")
    
    async def test_adaptive_processing(self):
        """Test adaptive processing strategy"""
        logger.info("🎯 Testing Adaptive Processing...")
        
        try:
            context = ProcessingContext(
                user_id="test_user",
                session_id="test_session_adapt",
                request_timestamp=datetime.now(),
                priority_level="normal"
            )
            
            result = await self.orchestrator.process_request(
                "Analyze application performance and suggest optimization strategies",
                context
            )
            
            success = (
                result.success and
                result.processing_strategy == ProcessingStrategy.ADAPTIVE and
                len(result.brain_responses) > 0 and
                result.confidence_score > 0.0
            )
            
            self.test_results.append({
                "test": "Adaptive Processing",
                "success": success,
                "strategy": result.processing_strategy.value,
                "brain_count": len(result.brain_responses),
                "confidence": result.confidence_score,
                "processing_time": result.total_processing_time,
                "details": f"Adaptively processed with {len(result.brain_responses)} brains"
            })
            
            logger.info(f"✅ Adaptive Processing: {result.confidence_score:.2f} confidence")
            
        except Exception as e:
            self.test_results.append({
                "test": "Adaptive Processing",
                "success": False,
                "error": str(e)
            })
            logger.error(f"❌ Adaptive Processing failed: {e}")
    
    async def test_external_knowledge_integration(self):
        """Test external knowledge integration"""
        logger.info("🌐 Testing External Knowledge Integration...")
        
        try:
            context = ProcessingContext(
                user_id="test_user",
                session_id="test_session_ext",
                request_timestamp=datetime.now()
            )
            
            result = await self.orchestrator.process_request(
                "What are the latest security vulnerabilities I should be aware of?",
                context
            )
            
            success = (
                result.success and
                result.external_knowledge_used and
                len(result.brain_responses) > 0
            )
            
            self.test_results.append({
                "test": "External Knowledge Integration",
                "success": success,
                "external_knowledge_used": result.external_knowledge_used,
                "brain_count": len(result.brain_responses),
                "confidence": result.confidence_score,
                "details": f"External knowledge {'used' if result.external_knowledge_used else 'not used'}"
            })
            
            logger.info(f"✅ External Knowledge: {'Used' if result.external_knowledge_used else 'Not used'}")
            
        except Exception as e:
            self.test_results.append({
                "test": "External Knowledge Integration",
                "success": False,
                "error": str(e)
            })
            logger.error(f"❌ External Knowledge Integration failed: {e}")
    
    async def test_confidence_calculation(self):
        """Test confidence calculation across multiple brains"""
        logger.info("📊 Testing Confidence Calculation...")
        
        try:
            context = ProcessingContext(
                user_id="test_user",
                session_id="test_session_conf",
                request_timestamp=datetime.now()
            )
            
            result = await self.orchestrator.process_request(
                "Provide comprehensive analysis of system performance metrics",
                context
            )
            
            # Test confidence calculation logic
            individual_confidences = [r.confidence for r in result.brain_responses]
            has_reasonable_confidence = (
                result.confidence_score > 0.0 and
                result.confidence_score <= 1.0 and
                len(individual_confidences) > 0
            )
            
            success = (
                result.success and
                has_reasonable_confidence and
                len(result.brain_responses) > 0
            )
            
            self.test_results.append({
                "test": "Confidence Calculation",
                "success": success,
                "combined_confidence": result.confidence_score,
                "individual_confidences": individual_confidences,
                "brain_count": len(result.brain_responses),
                "details": f"Combined confidence: {result.confidence_score:.2f}"
            })
            
            logger.info(f"✅ Confidence Calculation: {result.confidence_score:.2f}")
            
        except Exception as e:
            self.test_results.append({
                "test": "Confidence Calculation",
                "success": False,
                "error": str(e)
            })
            logger.error(f"❌ Confidence Calculation failed: {e}")
    
    async def test_consensus_detection(self):
        """Test consensus detection among brain responses"""
        logger.info("🤝 Testing Consensus Detection...")
        
        try:
            context = ProcessingContext(
                user_id="test_user",
                session_id="test_session_consensus",
                request_timestamp=datetime.now()
            )
            
            result = await self.orchestrator.process_request(
                "Recommend best practices for container orchestration deployment",
                context
            )
            
            has_consensus_data = 'consensus' in result.metadata
            
            success = (
                result.success and
                len(result.brain_responses) > 0 and
                has_consensus_data
            )
            
            consensus_reached = result.metadata.get('consensus', False)
            consensus_data = result.metadata.get('consensus_data', {})
            
            self.test_results.append({
                "test": "Consensus Detection",
                "success": success,
                "consensus_reached": consensus_reached,
                "consensus_data": consensus_data,
                "brain_count": len(result.brain_responses),
                "details": f"Consensus: {'Reached' if consensus_reached else 'Not reached'}"
            })
            
            logger.info(f"✅ Consensus Detection: {'Reached' if consensus_reached else 'Not reached'}")
            
        except Exception as e:
            self.test_results.append({
                "test": "Consensus Detection",
                "success": False,
                "error": str(e)
            })
            logger.error(f"❌ Consensus Detection failed: {e}")
    
    async def test_learning_integration(self):
        """Test learning system integration"""
        logger.info("🎓 Testing Learning Integration...")
        
        try:
            context = ProcessingContext(
                user_id="test_user",
                session_id="test_session_learning",
                request_timestamp=datetime.now()
            )
            
            result = await self.orchestrator.process_request(
                "Help me optimize database performance for high-traffic applications",
                context
            )
            
            # Complete the learning cycle with simulated feedback
            user_feedback = {
                'satisfaction': 0.8,
                'usefulness': 0.9,
                'accuracy': 0.85
            }
            
            await self.orchestrator.complete_request_learning(
                result.request_id, result, user_feedback
            )
            
            success = (
                result.success and
                result.learning_applied and
                len(result.brain_responses) > 0
            )
            
            self.test_results.append({
                "test": "Learning Integration",
                "success": success,
                "learning_applied": result.learning_applied,
                "request_id": result.request_id,
                "feedback_provided": True,
                "details": f"Learning cycle completed for request {result.request_id}"
            })
            
            logger.info(f"✅ Learning Integration: Applied for {result.request_id}")
            
        except Exception as e:
            self.test_results.append({
                "test": "Learning Integration",
                "success": False,
                "error": str(e)
            })
            logger.error(f"❌ Learning Integration failed: {e}")
    
    async def test_recommendation_generation(self):
        """Test recommendation generation"""
        logger.info("💡 Testing Recommendation Generation...")
        
        try:
            context = ProcessingContext(
                user_id="test_user",
                session_id="test_session_rec",
                request_timestamp=datetime.now()
            )
            
            result = await self.orchestrator.process_request(
                "I need guidance on implementing microservices architecture",
                context
            )
            
            has_recommendations = len(result.recommendations) > 0
            
            success = (
                result.success and
                has_recommendations and
                len(result.brain_responses) > 0
            )
            
            self.test_results.append({
                "test": "Recommendation Generation",
                "success": success,
                "recommendations_count": len(result.recommendations),
                "recommendations": result.recommendations,
                "brain_count": len(result.brain_responses),
                "details": f"Generated {len(result.recommendations)} recommendations"
            })
            
            logger.info(f"✅ Recommendation Generation: {len(result.recommendations)} recommendations")
            
        except Exception as e:
            self.test_results.append({
                "test": "Recommendation Generation",
                "success": False,
                "error": str(e)
            })
            logger.error(f"❌ Recommendation Generation failed: {e}")
    
    def test_system_status(self):
        """Test system status reporting"""
        logger.info("📋 Testing System Status...")
        
        try:
            status = self.orchestrator.get_system_status()
            
            required_fields = ['status', 'processing_stats', 'brain_components', 'last_updated']
            has_required_fields = all(field in status for field in required_fields)
            
            success = (
                has_required_fields and
                status['status'] == 'operational' and
                isinstance(status['processing_stats'], dict) and
                isinstance(status['brain_components'], dict)
            )
            
            self.test_results.append({
                "test": "System Status",
                "success": success,
                "status": status['status'],
                "brain_components": len(status['brain_components']),
                "processing_stats": status['processing_stats'],
                "details": f"System status: {status['status']}"
            })
            
            logger.info(f"✅ System Status: {status['status']}")
            
        except Exception as e:
            self.test_results.append({
                "test": "System Status",
                "success": False,
                "error": str(e)
            })
            logger.error(f"❌ System Status failed: {e}")
    
    async def run_all_tests(self):
        """Run all multi-brain orchestrator tests"""
        logger.info("🧠 AI-Intent-Based Strategy - Multi-Brain Orchestrator Test")
        logger.info("Complete Phase 3 System Integration Testing")
        logger.info("=" * 80)
        logger.info("🚀 Starting Multi-Brain Orchestrator Tests")
        logger.info("=" * 80)
        
        # Run processing strategy tests
        await self.test_sequential_processing()
        await self.test_parallel_processing()
        await self.test_hierarchical_processing()
        await self.test_adaptive_processing()
        
        # Run integration tests
        await self.test_external_knowledge_integration()
        await self.test_confidence_calculation()
        await self.test_consensus_detection()
        await self.test_learning_integration()
        await self.test_recommendation_generation()
        
        # Run system tests
        self.test_system_status()
        
        # Generate summary
        self.generate_test_summary()
    
    def generate_test_summary(self):
        """Generate and display test summary"""
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results if result["success"])
        success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
        
        logger.info("=" * 80)
        logger.info("📋 MULTI-BRAIN ORCHESTRATOR TEST SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Successful: {successful_tests}")
        logger.info(f"Failed: {total_tests - successful_tests}")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        
        logger.info("\n📊 Detailed Results:")
        logger.info("-" * 60)
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            logger.info(f"{status} {result['test']}")
            if "details" in result and isinstance(result["details"], str):
                logger.info(f"    {result['details']}")
            elif "error" in result:
                logger.info(f"    Error: {result['error']}")
        
        # Feature validation summary
        logger.info("\n🎯 Multi-Brain System Features Validated:")
        logger.info("-" * 60)
        
        feature_status = {
            "Sequential Processing": any("Sequential" in r["test"] for r in self.test_results if r["success"]),
            "Parallel Processing": any("Parallel" in r["test"] for r in self.test_results if r["success"]),
            "Hierarchical Processing": any("Hierarchical" in r["test"] for r in self.test_results if r["success"]),
            "Adaptive Processing": any("Adaptive" in r["test"] for r in self.test_results if r["success"]),
            "External Knowledge Integration": any("External Knowledge" in r["test"] for r in self.test_results if r["success"]),
            "Confidence Calculation": any("Confidence" in r["test"] for r in self.test_results if r["success"]),
            "Consensus Detection": any("Consensus" in r["test"] for r in self.test_results if r["success"]),
            "Learning Integration": any("Learning" in r["test"] for r in self.test_results if r["success"]),
            "Recommendation Generation": any("Recommendation" in r["test"] for r in self.test_results if r["success"]),
            "System Status Monitoring": any("System Status" in r["test"] for r in self.test_results if r["success"])
        }
        
        for feature, validated in feature_status.items():
            status = "✅" if validated else "❌"
            logger.info(f"{status} {feature}")
        
        # Overall assessment
        if success_rate >= 90:
            logger.info(f"\n🎉 Multi-Brain Orchestrator: EXCELLENT ({success_rate:.1f}% pass rate)")
        elif success_rate >= 75:
            logger.info(f"\n✅ Multi-Brain Orchestrator: SUCCESSFUL ({success_rate:.1f}% pass rate)")
        elif success_rate >= 50:
            logger.info(f"\n⚠️  Multi-Brain Orchestrator: PARTIAL ({success_rate:.1f}% pass rate)")
        else:
            logger.info(f"\n❌ Multi-Brain Orchestrator: NEEDS WORK ({success_rate:.1f}% pass rate)")
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"multibrain_orchestrator_test_results_{timestamp}.json"
        
        detailed_results = {
            "timestamp": datetime.now().isoformat(),
            "phase": "Phase 3 - Multi-Brain Orchestrator",
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "success_rate": success_rate
            },
            "detailed_results": self.test_results,
            "feature_validation": feature_status
        }
        
        try:
            with open(results_file, 'w') as f:
                json.dump(detailed_results, f, indent=2, default=str)
            logger.info(f"\n📄 Detailed results saved to: {results_file}")
        except Exception as e:
            logger.error(f"Failed to save results: {e}")

async def main():
    """Main test execution"""
    test_suite = MultibrainOrchestratorTest()
    await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())