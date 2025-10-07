#!/usr/bin/env python3
"""
Test script for Axis camera API execution through Pipeline V2
Tests end-to-end flow: Chat -> Pipeline V2 -> Execution Engine -> API Call
"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pipeline.orchestrator_v2 import PipelineOrchestratorV2


async def test_axis_camera_autofocus():
    """Test Axis camera autofocus command via API"""
    
    # Load environment variables
    load_dotenv()
    
    print("=" * 80)
    print("Testing Axis Camera API Execution")
    print("=" * 80)
    
    # Verify configuration
    print("\n📋 Configuration:")
    print(f"  LLM Provider: {os.getenv('LLM_PROVIDER', 'not set')}")
    print(f"  LLM Base URL: {os.getenv('LLM_BASE_URL', 'not set')}")
    print(f"  Database URL: {os.getenv('DATABASE_URL', 'not set')}")
    
    # Create orchestrator
    print("\n🔧 Initializing Pipeline Orchestrator V2...")
    orchestrator = PipelineOrchestratorV2()
    
    # Initialize and connect to LLM
    print("🔌 Connecting to LLM...")
    await orchestrator.initialize()
    
    # User request for Axis camera PTZ wall preset
    user_message = "Send a GET request to the Axis camera at 192.168.10.90 path /axis-cgi/com/ptz.cgi with parameter gotoserverpresetname=wall using credentials root/Enabled123! with digest auth"
    
    print(f"\n📝 User Request: {user_message}")
    print(f"🔧 Target: Axis camera at 192.168.10.90")
    print(f"🔑 Credentials: root / Enabled123!")
    print(f"🎯 Action: Move PTZ to wall preset")
    print("\n" + "=" * 80)
    
    try:
        # Execute through Pipeline V2
        print("\n🚀 Starting Pipeline V2 execution...")
        response = await orchestrator.process_request(
            user_request=user_message,
            session_id="test-session-axis-ptz-wall-v1"  # New session for PTZ wall preset
        )
        
        print("\n" + "=" * 80)
        print("✅ Pipeline V2 Execution Complete!")
        print("=" * 80)
        
        # Display results
        print(f"\n📊 Response:")
        print(f"   Success: {response.success}")
        print(f"   Message: {response.response.message[:300]}..." if len(response.response.message) > 300 else f"   Message: {response.response.message}")
        
        # Display metrics
        print(f"\n⏱️  Performance Metrics:")
        print(f"   Total Duration: {response.metrics.total_duration_ms:.2f}ms")
        print(f"   Stage AB: {response.metrics.stage_durations.get('stage_ab', 0):.2f}ms")
        print(f"   Stage C: {response.metrics.stage_durations.get('stage_c', 0):.2f}ms")
        print(f"   Stage D: {response.metrics.stage_durations.get('stage_d', 0):.2f}ms")
        print(f"   Stage E: {response.metrics.stage_durations.get('stage_e', 0):.2f}ms")
        
        # Display intermediate results
        print(f"\n🔍 Intermediate Results Keys: {list(response.intermediate_results.keys())}")
        
        # Display Stage C plan
        if 'stage_c' in response.intermediate_results:
            stage_c = response.intermediate_results['stage_c']
            print(f"\n📋 Stage C Plan:")
            if hasattr(stage_c, 'plan') and hasattr(stage_c.plan, 'steps'):
                print(f"   Steps: {len(stage_c.plan.steps)}")
                for i, step in enumerate(stage_c.plan.steps, 1):
                    print(f"\n   Step {i}: {step.description}")
                    print(f"      Tool: {step.tool}")
                    print(f"      Inputs: {step.inputs}")
        
        # Display execution details if available
        if 'stage_e' in response.intermediate_results:
            exec_result = response.intermediate_results['stage_e']
            print(f"\n📈 Execution Details:")
            print(f"   Execution ID: {exec_result.execution_id}")
            print(f"   Status: {exec_result.status}")
            print(f"   Total Steps: {exec_result.total_steps}")
            print(f"   Completed Steps: {exec_result.completed_steps}")
            print(f"   Failed Steps: {exec_result.failed_steps}")
            print(f"   Progress: {exec_result.progress_percentage:.1f}%")
            
            if exec_result.result:
                print(f"\n📋 Execution Result:")
                result = exec_result.result
                
                if 'steps' in result:
                    print(f"\n   Steps Executed:")
                    for i, step in enumerate(result['steps'], 1):
                        print(f"\n   Step {i}: {step.get('step_name', 'Unknown')}")
                        print(f"      Status: {step.get('status', 'unknown')}")
                        
                        if 'output_data' in step:
                            output = step['output_data']
                            print(f"      Output:")
                            
                            if 'http_status' in output:
                                print(f"         HTTP Status: {output['http_status']}")
                            
                            if 'response' in output:
                                resp_text = str(output['response'])
                                if len(resp_text) > 200:
                                    print(f"         Response: {resp_text[:200]}...")
                                else:
                                    print(f"         Response: {resp_text}")
                            
                            if 'url' in output:
                                print(f"         URL: {output['url']}")
                            
                            if 'method' in output:
                                print(f"         Method: {output['method']}")
                            
                            if 'connection_type' in output:
                                print(f"         Connection Type: {output['connection_type']}")
                            
                            if 'error' in output:
                                print(f"         ❌ Error: {output['error']}")
            
            if exec_result.error_message:
                print(f"\n   ❌ Error: {exec_result.error_message}")
        
        print("\n" + "=" * 80)
        print("✅ Test completed successfully!")
        print("=" * 80)
        
        return response
        
    except Exception as e:
        print("\n" + "=" * 80)
        print(f"❌ Test failed with error: {e}")
        print("=" * 80)
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Run the test
    result = asyncio.run(test_axis_camera_autofocus())
    
    # Exit with appropriate code
    sys.exit(0 if result else 1)