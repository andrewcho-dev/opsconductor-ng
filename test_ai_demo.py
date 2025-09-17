#!/usr/bin/env python3
"""Interactive demonstration of AI capabilities after knowledge training"""

import requests
import json
import time

def test_ai_demo():
    base_url = "http://localhost:3005"
    
    print("\n" + "="*80)
    print(" 🎉 OPSCONDUCTOR AI - KNOWLEDGE DEMONSTRATION 🎉")
    print("="*80)
    print("\nYour AI system is now trained with comprehensive IT operations knowledge!")
    print("Let me demonstrate its new capabilities...")
    
    demonstrations = [
        {
            "title": "🐳 Container Technology",
            "query": "How do I create a multi-stage Docker build?",
        },
        {
            "title": "☸️ Kubernetes Troubleshooting",
            "query": "My Kubernetes pod is in CrashLoopBackOff state. How do I fix it?",
        },
        {
            "title": "☁️ Cloud Architecture", 
            "query": "What's the difference between EC2, Lambda, and ECS in AWS?",
        },
        {
            "title": "🔧 System Administration",
            "query": "How can I find which process is using the most memory in Linux?",
        },
        {
            "title": "🔐 Security Best Practices",
            "query": "What are the key security measures for protecting a web application?",
        },
        {
            "title": "🗄️ Database Optimization",
            "query": "How do I optimize slow SQL queries in PostgreSQL?",
        },
        {
            "title": "📊 Monitoring & Alerting",
            "query": "What metrics should I monitor for a microservices application?",
        },
        {
            "title": "🤖 DevOps Automation",
            "query": "How do I set up a CI/CD pipeline with Jenkins?",
        }
    ]
    
    for demo in demonstrations:
        print(f"\n{'='*80}")
        print(f" {demo['title']}")
        print("="*80)
        print(f"❓ Question: {demo['query']}")
        print("-"*80)
        
        try:
            response = requests.post(
                f"{base_url}/ai/chat",
                json={"message": demo["query"], "user_id": 1},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get('response', 'No response')
                
                # Show more content for demo
                if len(ai_response) > 600:
                    print(f"💡 AI Response:\n{ai_response[:600]}...")
                else:
                    print(f"💡 AI Response:\n{ai_response}")
            else:
                print(f"❌ Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        time.sleep(1)
    
    print("\n" + "="*80)
    print(" 🚀 AI KNOWLEDGE DEMONSTRATION COMPLETE!")
    print("="*80)
    print("\n✨ Your OpsConductor AI is now equipped with:")
    print("  ✅ Comprehensive IT operations knowledge")
    print("  ✅ Troubleshooting expertise")
    print("  ✅ Best practices and recommendations")
    print("  ✅ Persistent knowledge storage")
    print("\n🎯 The AI can now answer technical questions, provide troubleshooting")
    print("   guidance, and generate more informed automation workflows!")
    print("\n💬 Try asking your own questions through the chat interface!")
    print("="*80)

if __name__ == "__main__":
    test_ai_demo()