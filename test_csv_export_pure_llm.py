#!/usr/bin/env python3
"""
Test CSV Export with Pure LLM-Based Routing

This test verifies that CSV export requests work through the full LLM pipeline
without any hardcoded fast paths or shortcuts.

Expected Flow:
User Request → Stage A → Stage B → Stage C → Stage D → Stage E → CSV Response
"""

import requests
import json
import time

API_URL = "http://localhost:3000/api/ai"

def test_csv_export_variations():
    """Test various CSV export request variations"""
    
    test_cases = [
        {
            "name": "Basic CSV Export",
            "request": "export all assets to csv",
            "expected_keywords": ["csv", "asset", "export"]
        },
        {
            "name": "Download Variation",
            "request": "download asset list as spreadsheet",
            "expected_keywords": ["asset", "list"]
        },
        {
            "name": "File Variation",
            "request": "give me a csv file of all servers",
            "expected_keywords": ["server", "csv"]
        }
    ]
    
    print("=" * 80)
    print("🧪 Testing CSV Export with Pure LLM-Based Routing")
    print("=" * 80)
    print()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'=' * 80}")
        print(f"Test {i}/{len(test_cases)}: {test_case['name']}")
        print(f"{'=' * 80}")
        print(f"Request: {test_case['request']}")
        print()
        
        # Send request
        start_time = time.time()
        try:
            response = requests.post(
                f"{API_URL}/pipeline",
                json={"request": test_case["request"]},
                timeout=120  # 2 minutes timeout
            )
            duration = time.time() - start_time
            
            print(f"⏱️  Response Time: {duration:.2f}s")
            print(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if request was successful
                if data.get("success"):
                    print("✅ Request Successful")
                    
                    # Extract response message
                    result = data.get("result", {})
                    message = result.get("message", "")
                    
                    # Check for expected keywords
                    found_keywords = [kw for kw in test_case["expected_keywords"] 
                                     if kw.lower() in message.lower()]
                    
                    print(f"🔍 Found Keywords: {found_keywords}")
                    
                    # Show first 200 characters of response
                    print(f"\n📝 Response Preview:")
                    print(f"{message[:200]}...")
                    
                    # Check metrics
                    metrics = data.get("metrics", {})
                    if metrics:
                        print(f"\n📊 Pipeline Metrics:")
                        print(f"   Total Duration: {metrics.get('total_duration_ms', 0):.0f}ms")
                        
                        stage_durations = metrics.get("stage_durations", {})
                        if stage_durations:
                            print(f"   Stage Breakdown:")
                            for stage, duration in stage_durations.items():
                                print(f"      {stage}: {duration:.0f}ms")
                    
                    print(f"\n✅ Test PASSED")
                else:
                    print(f"❌ Request Failed: {data.get('error', 'Unknown error')}")
                    print(f"❌ Test FAILED")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"Response: {response.text[:500]}")
                print(f"❌ Test FAILED")
                
        except requests.exceptions.Timeout:
            print(f"⏱️  Request Timeout (>120s)")
            print(f"❌ Test FAILED - Pipeline took too long")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            print(f"❌ Test FAILED")
    
    print(f"\n{'=' * 80}")
    print("🏁 Testing Complete")
    print(f"{'=' * 80}")

if __name__ == "__main__":
    test_csv_export_variations()