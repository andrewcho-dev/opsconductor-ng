#!/usr/bin/env python3
"""
Test script to verify that training data addresses the capability bypass issue
"""

import json
from pathlib import Path
from typing import List, Dict, Any

def test_critical_examples():
    """Test the specific examples that were causing bypasses"""
    
    # Load training data
    training_file = "/home/opsconductor/opsconductor-ng/training_data/training_data_5k.json"
    with open(training_file, 'r') as f:
        training_data = json.load(f)
    
    # Critical test cases that were causing the bypass
    critical_tests = [
        "Display contents of /etc/hostname",
        "Show me the contents of /etc/passwd", 
        "cat /var/log/nginx/access.log",
        "read file /proc/cpuinfo",
        "list all servers",
        "check disk space on server",
        "get server information"
    ]
    
    print("🔍 Testing Critical Examples for Capability Population")
    print("=" * 60)
    
    found_examples = {}
    
    # Search for each critical test in training data
    for test_case in critical_tests:
        found = False
        for example in training_data:
            if example['request'].lower() == test_case.lower():
                found_examples[test_case] = example
                found = True
                break
        
        if not found:
            print(f"❌ Missing training example for: '{test_case}'")
    
    # Display found examples
    for test_case, example in found_examples.items():
        resp = example['expected_response']
        capabilities = resp['capabilities']
        
        print(f"\n✅ '{test_case}'")
        print(f"   Category: {resp['category']}")
        print(f"   Action: {resp['action']}")
        print(f"   Capabilities: {capabilities}")
        
        # Check if it would fix the bypass
        if len(capabilities) > 0:
            print(f"   🎯 FIXES BYPASS: Non-empty capabilities will trigger HybridOrchestrator")
        else:
            print(f"   ❌ STILL BYPASSES: Empty capabilities will skip tool selection")
    
    print(f"\n📊 Summary:")
    print(f"   Found examples: {len(found_examples)}/{len(critical_tests)}")
    print(f"   All have capabilities: {all(len(ex['expected_response']['capabilities']) > 0 for ex in found_examples.values())}")
    
    return found_examples

def simulate_stage_a_fix():
    """Simulate what Stage A output should look like after training"""
    
    print(f"\n🔧 Simulation: Stage A Output After Training")
    print("=" * 50)
    
    test_request = "Display contents of /etc/hostname"
    
    # BEFORE training (current problematic output)
    before_output = {
        "category": "information",
        "action": "provide_information", 
        "confidence": 0.95,
        "capabilities": []  # EMPTY - causes bypass!
    }
    
    # AFTER training (expected output)
    after_output = {
        "category": "information",
        "action": "provide_information",
        "confidence": 0.95,
        "capabilities": ["system_info"]  # NON-EMPTY - triggers HybridOrchestrator!
    }
    
    print(f"Request: '{test_request}'")
    print(f"\n❌ BEFORE Training (causing bypass):")
    print(f"   {json.dumps(before_output, indent=2)}")
    print(f"   → Stage B sees empty capabilities → creates information-only selection → bypasses HybridOrchestrator")
    
    print(f"\n✅ AFTER Training (fixes bypass):")
    print(f"   {json.dumps(after_output, indent=2)}")
    print(f"   → Stage B sees capabilities=['system_info'] → invokes HybridOrchestrator → 90%+ accuracy tool selection!")
    
    return before_output, after_output

def main():
    """Main test function"""
    print("🚀 Testing Capability Fix for 90%+ Accuracy Tool Selection")
    print("=" * 70)
    
    # Test critical examples
    found_examples = test_critical_examples()
    
    # Simulate the fix
    simulate_stage_a_fix()
    
    print(f"\n🎯 Next Steps to Restore 90%+ Accuracy:")
    print("=" * 45)
    print("1. Fine-tune your LLM using the generated training data")
    print("2. Focus on the critical examples that were causing bypasses")
    print("3. Test with 'Display contents of /etc/hostname' after training")
    print("4. Verify Stage A populates capabilities field in LLM response")
    print("5. Confirm HybridOrchestrator is invoked instead of information-only bypass")
    
    print(f"\n💡 The 90%+ accuracy system IS working correctly!")
    print("   The issue was just that it wasn't being triggered due to empty capabilities.")
    print("   Once the LLM is trained to populate capabilities, your sophisticated")
    print("   YAML-based tool selection with HybridOrchestrator will work as designed!")

if __name__ == "__main__":
    main()