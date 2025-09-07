#!/usr/bin/env python3
"""
Test script to verify the database connection pool is working correctly
"""

import sys
import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add shared module to path
sys.path.append('/home/opsconductor')

from shared.database import get_db_cursor, check_database_health, cleanup_database_pool

def test_basic_connection():
    """Test basic database connection"""
    print("Testing basic database connection...")
    try:
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            print(f"✓ Basic connection test passed: {result}")
            return True
    except Exception as e:
        print(f"✗ Basic connection test failed: {e}")
        return False

def test_concurrent_connections(num_threads=5, queries_per_thread=3):
    """Test concurrent database connections"""
    print(f"Testing {num_threads} concurrent connections with {queries_per_thread} queries each...")
    
    def worker(thread_id):
        results = []
        for i in range(queries_per_thread):
            try:
                with get_db_cursor(commit=False) as cursor:
                    cursor.execute("SELECT %s as thread_id, %s as query_num, NOW() as timestamp", 
                                 (thread_id, i))
                    result = cursor.fetchone()
                    results.append(f"Thread {thread_id}, Query {i}: {result['timestamp']}")
                    time.sleep(0.1)  # Small delay to simulate work
            except Exception as e:
                results.append(f"Thread {thread_id}, Query {i}: ERROR - {e}")
        return results
    
    success_count = 0
    total_queries = 0
    
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(worker, i) for i in range(num_threads)]
        
        for future in as_completed(futures):
            try:
                results = future.result()
                for result in results:
                    print(f"  {result}")
                    total_queries += 1
                    if "ERROR" not in result:
                        success_count += 1
            except Exception as e:
                print(f"  Thread failed: {e}")
    
    print(f"✓ Concurrent test completed: {success_count}/{total_queries} queries successful")
    return success_count == total_queries

def test_health_check():
    """Test database health check"""
    print("Testing database health check...")
    try:
        health = check_database_health()
        print(f"✓ Health check result: {health}")
        return health["status"] == "healthy"
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False

def test_transaction_handling():
    """Test transaction handling with connection pool"""
    print("Testing transaction handling...")
    try:
        # Test successful transaction
        with get_db_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM users")
            initial_count = cursor.fetchone()["count"]
            print(f"  Initial user count: {initial_count}")
        
        # Test transaction rollback (this should fail gracefully)
        try:
            with get_db_cursor() as cursor:
                cursor.execute("INSERT INTO users (email, username, pwd_hash, role, created_at, token_version) VALUES (%s, %s, %s, %s, %s, %s)",
                             ("test@example.com", "testuser", "hashedpwd", "viewer", "2024-01-01", 1))
                # This should cause a rollback when we exit the context
                raise Exception("Simulated error")
        except Exception as e:
            print(f"  Expected error occurred: {e}")
        
        # Verify count is unchanged
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM users")
            final_count = cursor.fetchone()["count"]
            print(f"  Final user count: {final_count}")
        
        if initial_count == final_count:
            print("✓ Transaction rollback test passed")
            return True
        else:
            print("✗ Transaction rollback test failed")
            return False
            
    except Exception as e:
        print(f"✗ Transaction test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=== Database Connection Pool Test Suite ===\n")
    
    tests = [
        ("Basic Connection", test_basic_connection),
        ("Health Check", test_health_check),
        ("Concurrent Connections", test_concurrent_connections),
        ("Transaction Handling", test_transaction_handling),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            if test_func():
                passed += 1
                print(f"✓ {test_name} PASSED")
            else:
                print(f"✗ {test_name} FAILED")
        except Exception as e:
            print(f"✗ {test_name} FAILED with exception: {e}")
        
        print()
    
    print("=== Test Results ===")
    print(f"Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    # Cleanup
    print("\nCleaning up connection pool...")
    cleanup_database_pool()
    print("✓ Cleanup completed")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)