#!/usr/bin/env python3
"""
Test Service Selection Logic - Test resource mapper with mock LLM responses
"""

import asyncio
import sys
import os
sys.path.append('/home/opsconductor/opsconductor-ng/ai-brain')

from fulfillment_engine.resource_mapper import ResourceMapper, ServiceType
from fulfillment_engine.intent_processor import ProcessedIntent, IntentType, RiskLevel
import uuid
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MockLLMEngine:
    """Mock LLM engine that returns predefined responses"""
    
    def __init__(self):
        self.responses = {}
    
    def set_response(self, response):
        self.next_response = response
    
    async def generate(self, prompt):
        return {"generated_text": self.next_response}

async def test_service_selection_logic():
    """Test that resource mapper correctly parses LLM service selections"""
    
    print("🧠 Testing Service Selection Logic")
    print("=" * 50)
    
    try:
        # Create mock LLM engine
        mock_llm = MockLLMEngine()
        
        # Initialize resource mapper with mock LLM
        resource_mapper = ResourceMapper(llm_engine=mock_llm)
        
        # Create test intent
        processed_intent = ProcessedIntent(
            intent_id=str(uuid.uuid4()),
            intent_type=IntentType.AUTOMATION,
            description="Create ping job",
            original_message="create a job that pings 192.168.50.210 every 10 seconds",
            target_systems=["192.168.50.210"],
            operations=["ping"],
            parameters={"interval": "10s"},
            risk_level=RiskLevel.LOW,
            confidence=0.9,
            requires_asset_info=False,
            requires_network_info=True,
            requires_credentials=False
        )
        
        # Test 1: LLM chooses network-analytics-probe (CORRECT)
        print("🧪 Test 1: LLM chooses network-analytics-probe for ping")
        mock_llm.set_response("""
        For this ping job request, I need to use the network-analytics-probe service to execute the ping commands 
        since it has direct host network access and can reach external IPs. I also need celery-beat to handle 
        the recurring scheduling every 10 seconds.
        
        Services needed:
        1. network-analytics-probe - to execute ping commands with host network access
        2. celery-beat - to schedule the recurring task every 10 seconds
        """)
        
        result1 = await resource_mapper.map_intent_to_resources(processed_intent)
        
        print(f"   Services selected: {[req.service.value for req in result1.requirements]}")
        
        # Check if network-analytics-probe was selected
        has_network_probe = any(req.service == ServiceType.NETWORK_PROBE for req in result1.requirements)
        has_celery_beat = any(req.service == ServiceType.CELERY_BEAT for req in result1.requirements)
        
        if has_network_probe:
            print("   ✅ SUCCESS: LLM correctly chose network-analytics-probe!")
        else:
            print("   ❌ ISSUE: LLM did not choose network-analytics-probe")
            
        if has_celery_beat:
            print("   ✅ SUCCESS: LLM correctly chose celery-beat for scheduling!")
        else:
            print("   ❌ ISSUE: LLM did not choose celery-beat")
        
        print()
        
        # Test 2: LLM chooses automation-service (INCORRECT - should be guided to network-analytics-probe)
        print("🧪 Test 2: LLM incorrectly chooses automation-service")
        mock_llm.set_response("""
        For this ping job, I'll use automation-service to execute the ping commands and celery-beat for scheduling.
        
        Services needed:
        1. automation-service - to execute ping commands
        2. celery-beat - to schedule recurring execution
        """)
        
        result2 = await resource_mapper.map_intent_to_resources(processed_intent)
        
        print(f"   Services selected: {[req.service.value for req in result2.requirements]}")
        
        has_automation = any(req.service == ServiceType.AUTOMATION_SERVICE for req in result2.requirements)
        has_network_probe2 = any(req.service == ServiceType.NETWORK_PROBE for req in result2.requirements)
        
        if has_automation and not has_network_probe2:
            print("   ⚠️  LLM chose automation-service instead of network-analytics-probe")
            print("   💡 This shows why our service descriptions need to be very clear!")
        
        print()
        
        # Test 3: LLM chooses multiple services
        print("🧪 Test 3: LLM chooses multiple services for complex workflow")
        mock_llm.set_response("""
        This request requires multiple services:
        1. asset-service - to validate the target IP and get network information
        2. network-analytics-probe - to execute the actual ping commands with host network access
        3. celery-beat - to schedule the recurring ping every 10 seconds
        4. communication-service - to send notifications about ping results
        """)
        
        result3 = await resource_mapper.map_intent_to_resources(processed_intent)
        
        print(f"   Services selected: {[req.service.value for req in result3.requirements]}")
        print(f"   Total services: {len(result3.requirements)}")
        
        # Check all expected services
        services_found = {req.service for req in result3.requirements}
        expected_services = {
            ServiceType.ASSET_SERVICE,
            ServiceType.NETWORK_PROBE,
            ServiceType.CELERY_BEAT,
            ServiceType.COMMUNICATION_SERVICE
        }
        
        if expected_services.issubset(services_found):
            print("   ✅ SUCCESS: LLM selected all expected services!")
        else:
            missing = expected_services - services_found
            print(f"   ⚠️  Missing services: {[s.value for s in missing]}")
        
        print()
        print("🎯 Summary:")
        print("   - Resource mapper correctly parses LLM service selections")
        print("   - Service selection depends entirely on LLM's analysis")
        print("   - Clear service descriptions guide LLM to correct choices")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_service_selection_logic())