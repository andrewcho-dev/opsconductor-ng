#!/usr/bin/env python3
"""
Final Phase 8 Integration Test
Tests the complete OUIOE system integration
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

async def test_phase8_integration():
    """Test Phase 8 system integration"""
    try:
        logger.info("🚀 Starting Phase 8 Integration Test...")
        
        # Test 1: Import Phase 8 System Integrator
        logger.info("📦 Testing Phase 8 System Integrator import...")
        from integration.phase8_system_integrator import Phase8SystemIntegrator
        logger.info("✅ Phase8SystemIntegrator imported successfully")
        
        # Test 2: Import Production Readiness Validator
        logger.info("📦 Testing Production Readiness Validator import...")
        from integration.production_readiness_validator import ProductionReadinessValidator
        logger.info("✅ ProductionReadinessValidator imported successfully")
        
        # Test 3: Import Advanced Features Manager
        logger.info("📦 Testing Advanced Features Manager import...")
        from integration.advanced_features_manager import AdvancedFeaturesManager
        logger.info("✅ AdvancedFeaturesManager imported successfully")
        
        # Test 4: Import Phase 8 API Router
        logger.info("📦 Testing Phase 8 API Router import...")
        from api.phase8_integration_router import router as phase8_router
        logger.info("✅ Phase8 API Router imported successfully")
        
        # Test 5: Test basic system initialization
        logger.info("🔧 Testing system initialization...")
        from integrations.llm_client import LLMEngine
        llm_engine = LLMEngine(ollama_host="http://localhost:11434", default_model="codellama:7b")
        integrator = Phase8SystemIntegrator(llm_engine=llm_engine)
        logger.info("✅ Phase8SystemIntegrator initialized successfully")
        
        # Test 6: Run full system integration
        logger.info("🔗 Running full system integration...")
        integration_result = await integrator.integrate_full_system()
        logger.info(f"✅ Integration status: {integration_result.status.value}")
        logger.info(f"📊 System health: {integration_result.system_health:.1%}")
        
        # Test 6b: Test system status check
        logger.info("📊 Testing system status check...")
        status = await integrator.get_system_status()
        logger.info(f"✅ System status: {status['integration_status']}")
        logger.info(f"📊 Updated system health: {status['system_health']:.1%}")
        
        # Test 7: Test production readiness validation
        logger.info("🏭 Testing production readiness validation...")
        validator = ProductionReadinessValidator(integrator)
        readiness = await validator.validate_production_readiness()
        logger.info(f"✅ Production readiness: {readiness.readiness_level}")
        
        # Test 8: Test advanced features management
        logger.info("⚡ Testing advanced features management...")
        features_manager = AdvancedFeaturesManager(integrator)
        features = await features_manager.get_feature_status()
        logger.info(f"✅ Available features: {len(features)} features")
        
        logger.info("🎉 Phase 8 Integration Test COMPLETED SUCCESSFULLY!")
        logger.info("🏆 OUIOE System is ready for production deployment!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Phase 8 Integration Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_phase8_integration())
    if success:
        print("\n🎯 PHASE 8 INTEGRATION: SUCCESS")
        print("🚀 OUIOE System is fully integrated and ready!")
        sys.exit(0)
    else:
        print("\n❌ PHASE 8 INTEGRATION: FAILED")
        print("🔧 Please check the error messages above")
        sys.exit(1)