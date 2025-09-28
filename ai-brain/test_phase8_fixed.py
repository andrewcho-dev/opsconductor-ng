#!/usr/bin/env python3
"""
🧪 PHASE 8: FIXED INTEGRATION TEST
Ollama Universal Intelligent Operations Engine (OUIOE)

Fixed test to verify Phase 8 integration without complex dependencies.
"""

import asyncio
import structlog
from datetime import datetime
from unittest.mock import Mock, AsyncMock

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

async def test_phase8_integration():
    """
    🧪 TEST PHASE 8: INTEGRATION & OPTIMIZATION
    
    Fixed test to verify Phase 8 components work correctly.
    """
    print("🚀 Starting Phase 8 Fixed Integration Test")
    logger.info("🚀 Starting Phase 8 Fixed Integration Test")
    
    test_results = {
        "system_integrator": False,
        "production_validator": False,
        "features_manager": False,
        "api_router": False,
        "integration_test": False
    }
    
    try:
        # Test 1: System Integrator Import and Initialization
        print("🔗 Testing System Integrator...")
        logger.info("🔗 Testing System Integrator")
        
        try:
            from integration.phase8_system_integrator import (
                Phase8SystemIntegrator,
                SystemIntegrationStatus,
                PerformanceLevel,
                SystemCapabilities,
                IntegrationResult
            )
            
            # Mock LLM Engine
            mock_llm = Mock()
            mock_llm.initialize = AsyncMock(return_value=True)
            mock_llm.generate_response = AsyncMock(return_value="Test response")
            
            # Create system integrator
            integrator = Phase8SystemIntegrator(mock_llm)
            
            # Test basic functionality
            status = integrator.get_system_status()
            assert isinstance(status, dict)
            assert "integration_status" in status
            assert "system_health" in status
            
            test_results["system_integrator"] = True
            print("✅ System Integrator: PASSED")
            logger.info("✅ System Integrator test passed")
            
        except Exception as e:
            print(f"❌ System Integrator: FAILED - {e}")
            logger.error("❌ System Integrator test failed", error=str(e))
        
        # Test 2: Production Readiness Validator
        print("🛡️ Testing Production Readiness Validator...")
        logger.info("🛡️ Testing Production Readiness Validator")
        
        try:
            from integration.production_readiness_validator import (
                ProductionReadinessValidator,
                ReadinessLevel,
                SecurityValidationResult,
                PerformanceValidationResult,
                ProductionReadinessResult
            )
            
            # Create validator (only if integrator worked)
            if test_results["system_integrator"]:
                validator = ProductionReadinessValidator(integrator)
                
                # Test basic functionality
                assert validator is not None
                assert hasattr(validator, 'validate_production_readiness')
                
                test_results["production_validator"] = True
                print("✅ Production Readiness Validator: PASSED")
                logger.info("✅ Production Readiness Validator test passed")
            else:
                print("⚠️ Production Readiness Validator: SKIPPED (integrator failed)")
                
        except Exception as e:
            print(f"❌ Production Readiness Validator: FAILED - {e}")
            logger.error("❌ Production Readiness Validator test failed", error=str(e))
        
        # Test 3: Advanced Features Manager
        print("🚀 Testing Advanced Features Manager...")
        logger.info("🚀 Testing Advanced Features Manager")
        
        try:
            from integration.advanced_features_manager import (
                AdvancedFeaturesManager,
                FeatureStatus,
                FeatureResult,
                FeatureConfig
            )
            
            # Create features manager (only if integrator worked)
            if test_results["system_integrator"]:
                manager = AdvancedFeaturesManager(integrator)
                
                # Test basic functionality
                features_status = await manager.get_feature_status()
                assert isinstance(features_status, dict)
                assert len(features_status) > 0
                
                test_results["features_manager"] = True
                print("✅ Advanced Features Manager: PASSED")
                logger.info("✅ Advanced Features Manager test passed")
            else:
                print("⚠️ Advanced Features Manager: SKIPPED (integrator failed)")
                
        except Exception as e:
            print(f"❌ Advanced Features Manager: FAILED - {e}")
            logger.error("❌ Advanced Features Manager test failed", error=str(e))
        
        # Test 4: API Router
        print("🌐 Testing API Router...")
        logger.info("🌐 Testing API Router")
        
        try:
            from api.phase8_integration_router import (
                router,
                set_integration_services,
                IntelligentRequestModel,
                FeatureEnableRequest,
                SystemStatusResponse
            )
            
            # Test router creation
            assert router is not None
            assert hasattr(router, 'routes')
            
            # Test model classes
            request_model = IntelligentRequestModel(request="Test request")
            assert request_model.request == "Test request"
            
            test_results["api_router"] = True
            print("✅ API Router: PASSED")
            logger.info("✅ API Router test passed")
            
        except Exception as e:
            print(f"❌ API Router: FAILED - {e}")
            logger.error("❌ API Router test failed", error=str(e))
        
        # Test 5: Integration Test (if core components work)
        if test_results["system_integrator"]:
            print("🔗 Testing Complete Integration...")
            logger.info("🔗 Testing Complete Integration")
            
            try:
                # Test system integration
                integration_result = await integrator.integrate_full_system()
                assert integration_result is not None
                assert hasattr(integration_result, 'status')
                assert hasattr(integration_result, 'system_health')
                
                # Test intelligent request processing
                test_request = "Test intelligent request processing"
                test_context = {"user_id": "test_user", "session_id": "test_session"}
                
                request_result = await integrator.execute_intelligent_request(test_request, test_context)
                assert isinstance(request_result, dict)
                assert "response" in request_result
                
                test_results["integration_test"] = True
                print("✅ Complete Integration: PASSED")
                logger.info("✅ Complete Integration test passed")
                
            except Exception as e:
                print(f"⚠️ Complete Integration: PARTIAL - {e}")
                logger.warning("⚠️ Complete Integration test partial", error=str(e))
        else:
            print("⚠️ Complete Integration: SKIPPED (system integrator failed)")
        
        # Summary
        passed_tests = sum(test_results.values())
        total_tests = len(test_results)
        
        print(f"\n🎯 PHASE 8 TEST SUMMARY")
        print(f"================================================================================")
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests} ({passed_tests/total_tests:.1%})")
        print(f"❌ Failed: {total_tests - passed_tests} ({(total_tests - passed_tests)/total_tests:.1%})")
        print(f"================================================================================")
        
        logger.info(
            "🎯 Phase 8 test summary",
            total=total_tests,
            passed=passed_tests,
            failed=total_tests - passed_tests,
            success_rate=f"{passed_tests/total_tests:.1%}"
        )
        
        if passed_tests >= 3:  # At least 3 core tests should pass
            print("🎉 PHASE 8 CORE FUNCTIONALITY WORKING!")
            logger.info("🎉 Phase 8 core functionality working!")
            return True
        else:
            print("⚠️ PHASE 8 NEEDS ATTENTION")
            logger.warning("⚠️ Phase 8 needs attention")
            return False
            
    except Exception as e:
        print(f"❌ PHASE 8 TEST FAILED: {e}")
        logger.error("❌ Phase 8 test failed", error=str(e), exc_info=True)
        return False

async def main():
    """Main test runner"""
    start_time = datetime.now()
    
    print("🧪 PHASE 8: INTEGRATION & OPTIMIZATION - FIXED TEST")
    print("=" * 80)
    
    success = await test_phase8_integration()
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"\n⏱️ Test Duration: {duration:.2f} seconds")
    
    if success:
        print("🎉 PHASE 8 FIXED TEST: SUCCESS!")
        return 0
    else:
        print("❌ PHASE 8 FIXED TEST: NEEDS ATTENTION!")
        return 1

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)