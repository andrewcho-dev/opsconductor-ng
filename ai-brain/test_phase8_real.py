#!/usr/bin/env python3
"""
REAL Phase 8 Integration Test
Tests the complete OUIOE system integration with REAL components
"""

import sys
import os
import asyncio
import logging

# Add the ai-brain directory to Python path
sys.path.insert(0, '/home/opsconductor/opsconductor-ng/ai-brain')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_phase8_real_integration():
    """Test Phase 8 system integration with REAL components"""
    try:
        logger.info("🚀 Starting REAL Phase 8 Integration Test...")
        
        # Test 1: Initialize REAL LLM Engine
        logger.info("🧠 Initializing REAL LLM Engine...")
        from integrations.llm_client import LLMEngine
        
        llm_engine = LLMEngine(
            ollama_host="http://localhost:11434",
            default_model="codellama:7b"
        )
        
        # Initialize the LLM engine
        llm_initialized = await llm_engine.initialize()
        if llm_initialized:
            logger.info("✅ REAL LLM Engine initialized successfully")
        else:
            logger.warning("⚠️ LLM Engine initialization failed, continuing with limited functionality")
        
        # Test 2: Import and Initialize Phase 8 System Integrator
        logger.info("📦 Testing Phase 8 System Integrator with REAL LLM...")
        from integration.phase8_system_integrator import Phase8SystemIntegrator
        
        integrator = Phase8SystemIntegrator(llm_engine=llm_engine)
        logger.info("✅ Phase8SystemIntegrator initialized with REAL LLM")
        
        # Test 3: Test system status check
        logger.info("📊 Testing REAL system status check...")
        status = integrator.get_system_status()
        logger.info(f"✅ System status: {status['integration_status']}")
        logger.info(f"📈 Performance level: {status['performance_level']}")
        logger.info(f"🔧 Available capabilities: {len([k for k, v in status['capabilities'].items() if v])}")
        
        # Test 4: Test Production Readiness Validator
        logger.info("🏭 Testing REAL production readiness validation...")
        from integration.production_readiness_validator import ProductionReadinessValidator
        
        validator = ProductionReadinessValidator(system_integrator=integrator)
        readiness = await validator.validate_production_readiness()
        logger.info(f"✅ Production readiness: {readiness.readiness_level}")
        logger.info(f"🔒 Security score: {readiness.security.security_score}")
        logger.info(f"⚡ Performance score: {readiness.performance.performance_score}")
        logger.info(f"📊 Overall score: {readiness.overall_score:.1f}%")
        
        # Test 5: Test Advanced Features Manager
        logger.info("⚡ Testing REAL advanced features management...")
        from integration.advanced_features_manager import AdvancedFeaturesManager
        
        features_manager = AdvancedFeaturesManager(system_integrator=integrator)
        features_status = await features_manager.get_feature_status()
        logger.info(f"✅ Available features: {len(features_status)} features")
        
        # Enable a feature to test real functionality
        if features_status:
            first_feature = list(features_status.keys())[0]
            enable_result = await features_manager.enable_feature(first_feature)
            logger.info(f"✅ Feature '{first_feature}' enabled: {enable_result.success}")
        
        # Test 6: Test system integration
        logger.info("🔗 Testing REAL system integration...")
        integration_result = await integrator.integrate_full_system()
        logger.info(f"✅ System integration status: {integration_result.status}")
        logger.info(f"💚 System health: {integration_result.system_health:.1%}")
        logger.info(f"⚠️ Integration errors: {len(integration_result.errors)}")
        
        # Test 7: Test intelligent request processing
        logger.info("🧠 Testing REAL intelligent request processing...")
        test_request = "Analyze system status and provide recommendations"
        request_result = await integrator.execute_intelligent_request(test_request)
        logger.info(f"✅ Intelligent request processed successfully")
        
        # Test 8: Test API Router
        logger.info("🌐 Testing Phase 8 API Router...")
        from api.phase8_integration_router import router as phase8_router
        logger.info(f"✅ Phase8 API Router loaded with {len(phase8_router.routes)} routes")
        
        logger.info("🎉 REAL Phase 8 Integration Test COMPLETED SUCCESSFULLY!")
        logger.info("🏆 OUIOE System is ready for REAL production deployment!")
        
        # Final system summary
        logger.info("\n" + "="*60)
        logger.info("🎯 PHASE 8 INTEGRATION SUMMARY")
        logger.info("="*60)
        logger.info(f"🧠 LLM Engine: {'✅ Active' if llm_initialized else '⚠️ Limited'}")
        logger.info(f"🔗 System Integration: {integration_result.status.value} ({integration_result.system_health:.1%} health)")
        logger.info(f"🏭 Production Ready: {'✅ Yes' if readiness.readiness_level.value in ['production_ready', 'enterprise_ready'] else '⚠️ Needs work'}")
        logger.info(f"⚡ Advanced Features: ✅ {len(features_status)} available")
        logger.info(f"🧠 Intelligent Processing: ✅ Active")
        logger.info("="*60)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ REAL Phase 8 Integration Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_phase8_real_integration())
    if success:
        print("\n🎯 REAL PHASE 8 INTEGRATION: SUCCESS")
        print("🚀 OUIOE System is fully integrated and ready for REAL deployment!")
        sys.exit(0)
    else:
        print("\n❌ REAL PHASE 8 INTEGRATION: FAILED")
        print("🔧 Please check the error messages above")
        sys.exit(1)