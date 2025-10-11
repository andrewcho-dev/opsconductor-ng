#!/usr/bin/env python3
"""
Test script for Stage AB semantic retrieval deployment
"""
import requests
import json
import time

def test_semantic_retrieval():
    """Test the semantic retrieval system with a sample request"""
    
    # Test request
    test_request = {
        "request": "List all files in the current directory",
        "context": {}
    }
    
    print("🧪 Testing Stage AB Semantic Retrieval")
    print("=" * 60)
    print(f"📝 Request: {test_request['request']}")
    print()
    
    # Send request to pipeline
    url = "http://localhost:3005/pipeline"
    
    try:
        print("📤 Sending request to pipeline...")
        start_time = time.time()
        
        response = requests.post(url, json=test_request, timeout=60)
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Request successful ({elapsed:.2f}s)")
            print()
            print("📊 Response:")
            print(json.dumps(result, indent=2))
            print()
            
            # Check if semantic retrieval was used
            if "stage_ab" in result:
                stage_ab = result["stage_ab"]
                print("🔍 Stage AB Details:")
                print(f"  - Version: {stage_ab.get('version', 'N/A')}")
                print(f"  - Tools Selected: {len(stage_ab.get('selected_tools', []))}")
                
                if stage_ab.get('selected_tools'):
                    print(f"  - Selected Tool IDs: {[t['tool_id'] for t in stage_ab['selected_tools']]}")
                
                print()
            
            return True
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - is the pipeline running?")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def check_telemetry():
    """Check the telemetry table for semantic retrieval logs"""
    import psycopg2
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    print()
    print("📊 Checking Stage AB Telemetry")
    print("=" * 60)
    
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", 5432)),
            database=os.getenv("POSTGRES_DB", "opsconductor"),
            user=os.getenv("POSTGRES_USER", "opsconductor"),
            password=os.getenv("POSTGRES_PASSWORD", "opsconductor_secure_2024")
        )
        
        cursor = conn.cursor()
        
        # Get latest telemetry entries
        cursor.execute("""
            SELECT 
                request_id,
                user_intent,
                catalog_size,
                candidates_before_budget,
                rows_sent,
                budget_used,
                headroom_left,
                selected_tool_ids,
                total_time_ms,
                created_at
            FROM tool_catalog.stage_ab_telemetry
            ORDER BY created_at DESC
            LIMIT 5
        """)
        
        rows = cursor.fetchall()
        
        if rows:
            print(f"📈 Latest {len(rows)} telemetry entries:")
            print()
            for row in rows:
                request_id, user_intent, catalog_size, candidates, rows_sent, budget_used, headroom, selected_ids, total_time, created = row
                print(f"  Request ID: {request_id}")
                print(f"  User Intent: {user_intent[:60]}...")
                print(f"  Catalog Size: {catalog_size}")
                print(f"  Candidates Before Budget: {candidates}")
                print(f"  Rows Sent to LLM: {rows_sent}")
                print(f"  Budget Used: {budget_used} tokens")
                print(f"  Headroom Left: {headroom}%")
                print(f"  Selected Tool IDs: {selected_ids}")
                print(f"  Total Time: {total_time}ms")
                print(f"  Created: {created}")
                print()
        else:
            print("  No telemetry entries found yet")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking telemetry: {str(e)}")

if __name__ == "__main__":
    # Test semantic retrieval
    success = test_semantic_retrieval()
    
    # Check telemetry
    if success:
        time.sleep(1)  # Give it a moment to write telemetry
        check_telemetry()
    
    print()
    print("=" * 60)
    if success:
        print("✅ Semantic Retrieval Deployment Test PASSED")
    else:
        print("❌ Semantic Retrieval Deployment Test FAILED")