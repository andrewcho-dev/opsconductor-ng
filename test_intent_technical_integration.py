#!/usr/bin/env python3
"""
Test Intent-to-Technical Integration Bridge

This test verifies that the 4W Framework Intent Brain can successfully
integrate with the Technical Brain through the Intent-to-Technical Bridge.

Test Coverage:
1. 4W Framework analysis generation
2. Intent-to-Technical Bridge conversion
3. Technical Brain input compatibility
4. End-to-end Intent → Technical flow
5. Error handling and fallback scenarios
"""

import asyncio
import sys
import os
import json
from datetime import datetime
from typing import Dict, Any

# Add the project root to Python path
sys.path.insert(0, '/home/opsconductor/opsconductor-ng')
sys.path.insert(0, '/home/opsconductor/opsconductor-ng/ai-brain')

from brains.intent_brain.intent_brain import IntentBrain
from brains.technical_brain import TechnicalBrain
from brains.intent_brain.intent_technical_bridge import IntentTechnicalBridge

class IntentTechnicalIntegrationTester:
    """Test the Intent-to-Technical integration bridge"""
    
    def __init__(self):
        self.intent_brain = IntentBrain()
        self.technical_brain = TechnicalBrain()
        self.bridge = IntentTechnicalBridge()
        self.test_results = []
    
    async def run_all_tests(self):
        """Run all integration tests"""
        print("🔗 Intent-to-Technical Integration Bridge Tests")
        print("=" * 60)
        
        test_cases = [
            {
                "name": "Information Request Integration",
                "message": "What is the status of the web server?",
                "expected_itil": "information_request",
                "expected_complexity": "LOW"
            },
            {
                "name": "Provisioning Request Integration", 
                "message": "Install monitoring on all production servers",
                "expected_itil": "service_request",
                "expected_complexity": "HIGH"
            },
            {
                "name": "Diagnostic Request Integration",
                "message": "The database is running slow, please investigate",
                "expected_itil": "incident_management", 
                "expected_complexity": "MEDIUM"
            },
            {
                "name": "Operational Request Integration",
                "message": "Restart the API service during maintenance window",
                "expected_itil": "service_request",
                "expected_complexity": "MEDIUM"
            },
            {
                "name": "Complex Multi-System Integration",
                "message": "Deploy new microservice to production cluster with monitoring and alerting",
                "expected_itil": "service_request",
                "expected_complexity": "HIGH"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🧪 Test {i}: {test_case['name']}")
            print("-" * 40)
            
            try:
                # Step 1: Intent Brain Analysis
                intent_result = await self.intent_brain.analyze_intent(test_case["message"])
                print(f"✅ Intent Analysis: {intent_result.four_w_analysis.what_analysis.action_type.value}")
                
                # Step 2: Bridge Conversion
                technical_input = self.intent_brain.get_technical_brain_input(intent_result)
                print(f"✅ Bridge Conversion: {technical_input['itil_service_type']}")
                
                # Step 3: Technical Brain Processing
                technical_plan = await self.technical_brain.create_execution_plan(technical_input)
                print(f"✅ Technical Plan: {technical_plan.name}")
                
                # Verify expectations
                success = True
                if technical_input["itil_service_type"] != test_case["expected_itil"]:
                    print(f"⚠️  ITIL mismatch: expected {test_case['expected_itil']}, got {technical_input['itil_service_type']}")
                    success = False
                
                if technical_input["resource_complexity"] != test_case["expected_complexity"]:
                    print(f"⚠️  Complexity mismatch: expected {test_case['expected_complexity']}, got {technical_input['resource_complexity']}")
                    success = False
                
                # Record results
                self.test_results.append({
                    "test_name": test_case["name"],
                    "success": success,
                    "intent_confidence": intent_result.overall_confidence,
                    "technical_confidence": technical_plan.confidence_score,
                    "itil_service_type": technical_input["itil_service_type"],
                    "resource_complexity": technical_input["resource_complexity"],
                    "steps_generated": len(technical_plan.steps),
                    "processing_time": intent_result.processing_time + (technical_input.get("processing_time", 0))
                })
                
                if success:
                    print(f"✅ Test PASSED - End-to-end integration successful")
                else:
                    print(f"❌ Test FAILED - Expectations not met")
                    
            except Exception as e:
                print(f"❌ Test FAILED with error: {e}")
                self.test_results.append({
                    "test_name": test_case["name"],
                    "success": False,
                    "error": str(e)
                })
        
        # Print summary
        await self._print_test_summary()
        
        # Test bridge statistics
        await self._test_bridge_statistics()
        
        return self.test_results
    
    async def _print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 60)
        print("🎯 INTEGRATION TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results if result.get("success", False))
        
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {total_tests - successful_tests}")
        print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")
        
        if successful_tests > 0:
            successful_results = [r for r in self.test_results if r.get("success", False)]
            avg_intent_confidence = sum(r["intent_confidence"] for r in successful_results) / len(successful_results)
            avg_technical_confidence = sum(r["technical_confidence"] for r in successful_results) / len(successful_results)
            avg_processing_time = sum(r["processing_time"] for r in successful_results) / len(successful_results)
            
            print(f"\nPerformance Metrics:")
            print(f"  Average Intent Confidence: {avg_intent_confidence:.2%}")
            print(f"  Average Technical Confidence: {avg_technical_confidence:.2%}")
            print(f"  Average Processing Time: {avg_processing_time:.3f}s")
        
        # ITIL Service Type Distribution
        itil_types = {}
        complexity_levels = {}
        
        for result in self.test_results:
            if result.get("success", False):
                itil_type = result.get("itil_service_type", "unknown")
                complexity = result.get("resource_complexity", "unknown")
                
                itil_types[itil_type] = itil_types.get(itil_type, 0) + 1
                complexity_levels[complexity] = complexity_levels.get(complexity, 0) + 1
        
        if itil_types:
            print(f"\nITIL Service Type Distribution:")
            for itil_type, count in itil_types.items():
                print(f"  {itil_type}: {count}")
        
        if complexity_levels:
            print(f"\nResource Complexity Distribution:")
            for complexity, count in complexity_levels.items():
                print(f"  {complexity}: {count}")
    
    async def _test_bridge_statistics(self):
        """Test bridge statistics functionality"""
        print("\n" + "=" * 60)
        print("📊 BRIDGE STATISTICS TEST")
        print("=" * 60)
        
        try:
            stats = self.intent_brain.get_bridge_stats()
            print(f"✅ Bridge Statistics Retrieved:")
            print(f"  Total Conversions: {stats.get('total_conversions', 0)}")
            print(f"  Average Confidence: {stats.get('average_confidence', 0):.2%}")
            print(f"  Bridge Version: {stats.get('bridge_version', 'unknown')}")
            
            if stats.get('itil_service_types'):
                print(f"  ITIL Service Types: {stats['itil_service_types']}")
            
            if stats.get('resource_complexity_distribution'):
                print(f"  Complexity Distribution: {stats['resource_complexity_distribution']}")
                
        except Exception as e:
            print(f"❌ Bridge Statistics Test Failed: {e}")
    
    async def test_error_handling(self):
        """Test error handling and fallback scenarios"""
        print("\n" + "=" * 60)
        print("🛡️ ERROR HANDLING TEST")
        print("=" * 60)
        
        try:
            # Test with empty message
            print("Testing empty message handling...")
            intent_result = await self.intent_brain.analyze_intent("")
            technical_input = self.intent_brain.get_technical_brain_input(intent_result)
            
            if technical_input.get("error_info"):
                print("✅ Error handling working - fallback used")
            else:
                print("✅ Empty message handled gracefully")
                
        except Exception as e:
            print(f"❌ Error handling test failed: {e}")

async def main():
    """Main test execution"""
    print("🚀 Starting Intent-to-Technical Integration Tests")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    tester = IntentTechnicalIntegrationTester()
    
    # Run main integration tests
    results = await tester.run_all_tests()
    
    # Test error handling
    await tester.test_error_handling()
    
    # Final assessment
    successful_tests = sum(1 for result in results if result.get("success", False))
    total_tests = len(results)
    
    print("\n" + "🎯" * 20)
    print("FINAL ASSESSMENT")
    print("🎯" * 20)
    
    if successful_tests == total_tests and total_tests > 0:
        print("🎉 ALL TESTS PASSED! Intent-to-Technical integration is working perfectly!")
        print("✅ 4W Framework → Technical Brain bridge is operational")
        print("✅ Ready for Phase 4 multi-brain orchestration")
        return True
    elif successful_tests > 0:
        print(f"⚠️  PARTIAL SUCCESS: {successful_tests}/{total_tests} tests passed")
        print("🔧 Some integration issues need attention")
        return False
    else:
        print("❌ ALL TESTS FAILED! Integration bridge needs debugging")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)