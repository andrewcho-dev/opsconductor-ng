#!/usr/bin/env python3

import requests
import json

def test_ai_query(query):
    """Test AI query and check for verbose response format"""
    
    print(f"Testing query: '{query}'")
    print("=" * 60)
    
    # Make request to AI endpoint
    response = requests.post(
        "http://localhost:3005/ai/chat",
        json={
            "message": query,
            "context": {}
        },
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        ai_response = data.get('response', '')
        intent = data.get('intent', '')
        
        print("AI Response:")
        print("=" * 50)
        print(ai_response)
        print("=" * 50)
        print(f"Intent: {intent}")
        print(f"Status: {response.status_code}")
        print()
        
        # Check for verbose format indicators
        verbose_indicators = [
            "**ANALYZE THE USER'S INTENT:**",
            "**IDENTIFY RELEVANT INFORMATION:**", 
            "**CROSS-REFERENCE DATA:**",
            "**RESOLVE CONFLICTS:**",
            "**SYNTHESIZE INTELLIGENTLY:**",
            "**SANITY CHECK:**",
            "Based on the provided intelligence sources"
        ]
        
        has_verbose_format = any(indicator in ai_response for indicator in verbose_indicators)
        
        if has_verbose_format:
            print("❌ VERBOSE FORMAT DETECTED - Response contains meta-analysis headers")
            return False
        else:
            print("✅ CLEAN FORMAT - Response is direct and readable")
            return True
    else:
        print(f"❌ ERROR: HTTP {response.status_code}")
        print(response.text)
        return False

if __name__ == "__main__":
    # Test different types of queries
    queries = [
        "how many Windows 11 machines do we have?",
        "list all Windows machines",
        "what servers are running Ubuntu?",
        "show me the database servers",
        "how many total assets do we have?"
    ]
    
    results = []
    for query in queries:
        result = test_ai_query(query)
        results.append(result)
        print()
    
    print("=" * 60)
    print("SUMMARY:")
    print(f"Clean responses: {sum(results)}/{len(results)}")
    if all(results):
        print("✅ ALL QUERIES RETURNED CLEAN RESPONSES")
    else:
        print("❌ SOME QUERIES STILL HAVE VERBOSE FORMAT ISSUES")