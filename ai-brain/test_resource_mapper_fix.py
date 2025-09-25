#!/usr/bin/env python3

import asyncio
import sys
import os

# Add the ai-brain directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from fulfillment_engine.resource_mapper import ResourceMapper
from fulfillment_engine.intent_processor import ProcessedIntent, IntentType, RiskLevel

class MockLLMEngine:
    """Mock LLM engine for testing"""
    
    async def generate(self, prompt):
        """Return a natural language response instead of JSON"""
        return {
            "generated_text": """
            For this ping job request, I need to analyze what services are required:

            1. AUTOMATION-SERVICE is needed to execute the actual ping commands to the target IP address 192.168.50.210
            2. CELERY-BEAT is needed to schedule the recurring execution every 10 seconds

            The execution order should be:
            1. First, set up the automation service to handle ping execution
            2. Then, configure celery-beat to schedule the recurring task

            This is a relatively simple operation that should complete within 60 seconds for setup.
            The automation-service will handle the ping execution, and celery-beat will manage the scheduling.
            """
        }

async def test_resource_mapper_natural_language():
    """Test the resource mapper with natural language parsing"""
    print("🧪 Testing Resource Mapper with Natural Language Parsing...")
    
    # Create mock processed intent
    processed_intent = ProcessedIntent(
        intent_id="test-ping-123",
        intent_type=IntentType.AUTOMATION,
        description="Create a job that pings 192.168.50.210 every 10 seconds",
        original_message="create a job that pings 192.168.50.210 every 10 seconds",
        risk_level=RiskLevel.LOW,
        confidence=0.95,
        target_systems=["192.168.50.210"],
        operations=["ping"],
        parameters={"interval": "10s", "target": "192.168.50.210"},
        requires_asset_info=False,
        requires_network_info=False,
        requires_credentials=False
    )
    
    # Create resource mapper with mock LLM
    mock_llm = MockLLMEngine()
    resource_mapper = ResourceMapper(llm_engine=mock_llm)
    
    try:
        # Test resource mapping
        resource_mapping = await resource_mapper.map_intent_to_resources(processed_intent)
        
        print(f"✅ Resource mapping successful!")
        print(f"   Intent ID: {resource_mapping.intent_id}")
        print(f"   Requirements: {len(resource_mapping.requirements)}")
        print(f"   Execution Order: {[service.value for service in resource_mapping.execution_order]}")
        print(f"   Estimated Duration: {resource_mapping.estimated_duration}s")
        
        # Verify expected services
        service_names = [req.service.value for req in resource_mapping.requirements]
        print(f"   Services: {service_names}")
        
        if "automation-service" in service_names:
            print("   ✅ Automation service correctly identified")
        else:
            print("   ❌ Automation service missing")
            
        if "celery-beat" in service_names:
            print("   ✅ Celery-beat service correctly identified")
        else:
            print("   ❌ Celery-beat service missing")
            
        return True
        
    except Exception as e:
        print(f"❌ Resource mapping failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_resource_mapper_natural_language())
    if success:
        print("\n🎉 Natural language resource mapping test PASSED!")
    else:
        print("\n💥 Natural language resource mapping test FAILED!")
        sys.exit(1)