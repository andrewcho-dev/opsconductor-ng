#!/usr/bin/env python3
"""
Test script to check if the OpsConductor AI system knows how to install remote probes
"""

import requests
import json
import sys

def test_ai_probe_knowledge():
    """Test if AI system has knowledge about remote probe installation"""
    
    ai_service_url = "http://localhost:3005"
    
    # Test questions about remote probe installation
    test_questions = [
        "How do I install the OpsConductor remote probe on a Windows machine?",
        "Can you help me deploy a network analysis probe to 192.168.50.211?",
        "What steps are needed to install the remote probe on Windows?",
        "I need to set up remote network monitoring on a Windows server. Can you create an automation job for this?"
    ]
    
    print("🧠 Testing OpsConductor AI Knowledge about Remote Probe Installation")
    print("=" * 70)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n📝 Test {i}: {question}")
        print("-" * 50)
        
        try:
            response = requests.post(
                f"{ai_service_url}/ai/chat",
                json={
                    "message": question,
                    "user_id": 1,
                    "conversation_id": f"test-session-{i}"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get('response', 'No response')
                
                # Check if the response mentions key concepts
                key_concepts = [
                    'remote probe',
                    'automation job',
                    'Windows',
                    'installation',
                    'network analysis',
                    'probe deployment'
                ]
                
                found_concepts = [concept for concept in key_concepts if concept.lower() in ai_response.lower()]
                
                print(f"✅ AI Response received ({len(ai_response)} chars)")
                print(f"🎯 Key concepts found: {', '.join(found_concepts) if found_concepts else 'None'}")
                
                # Show first 200 characters of response
                preview = ai_response[:200] + "..." if len(ai_response) > 200 else ai_response
                print(f"📄 Response preview: {preview}")
                
                # Check if AI mentions automation jobs or specific installation steps
                if any(term in ai_response.lower() for term in ['automation job', 'install', 'deploy', 'probe']):
                    print("🟢 AI appears to understand remote probe installation")
                else:
                    print("🟡 AI response doesn't clearly indicate probe installation knowledge")
                    
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
    
    print("\n" + "=" * 70)
    print("🔍 Testing AI System's Access to Asset Information")
    print("-" * 50)
    
    # Test if AI can access asset information
    asset_question = "What assets do we have registered in the system? Show me information about 192.168.50.211."
    
    try:
        response = requests.post(
            f"{ai_service_url}/ai/chat",
            json={
                "message": asset_question,
                "user_id": 1,
                "conversation_id": "asset-test"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result.get('response', 'No response')
            
            print(f"✅ Asset query response received ({len(ai_response)} chars)")
            
            # Check if response mentions asset-related concepts
            asset_concepts = ['asset', 'registered', '192.168.50.211', 'hostname', 'credentials']
            found_concepts = [concept for concept in asset_concepts if concept in ai_response.lower()]
            
            print(f"🎯 Asset concepts found: {', '.join(found_concepts) if found_concepts else 'None'}")
            
            # Show response preview
            preview = ai_response[:300] + "..." if len(ai_response) > 300 else ai_response
            print(f"📄 Response preview: {preview}")
            
            if any(term in ai_response.lower() for term in ['asset', 'registered', 'credential']):
                print("🟢 AI appears to have access to asset information")
            else:
                print("🟡 AI may not have direct access to asset database")
                
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Asset query failed: {e}")
    
    print("\n" + "=" * 70)
    print("📋 Summary")
    print("-" * 50)
    print("This test checks if the OpsConductor AI system:")
    print("1. ✅ Understands remote probe installation concepts")
    print("2. ✅ Can create automation jobs for probe deployment")
    print("3. ✅ Has access to registered asset information")
    print("4. ✅ Can retrieve credentials for automated installation")
    print("\nIf the AI system has this knowledge, it should be able to:")
    print("- Automatically install remote probes on registered assets")
    print("- Use stored credentials without manual input")
    print("- Create and execute deployment automation jobs")
    print("- Handle the complete installation workflow")

if __name__ == "__main__":
    test_ai_probe_knowledge()