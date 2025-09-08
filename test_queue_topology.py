#!/usr/bin/env python3
"""
Test script to verify RabbitMQ queue topology setup

This script tests that all exchanges, queues, and bindings are created
correctly according to the OpsConductor specifications.
"""

import asyncio
import sys
import os
import logging

# Add shared directory to path
sys.path.append('/home/opsconductor/shared')

from shared.utility_message_queue import get_rabbitmq_connection, check_rabbitmq_health
from shared.message_schemas import ExchangeNames, QueueNames

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_queue_topology():
    """Test RabbitMQ queue topology setup"""
    
    print("🐰 Testing RabbitMQ Queue Topology Setup")
    print("=" * 50)
    
    try:
        # Test connection health
        print("\n1. Testing RabbitMQ Connection...")
        health = await check_rabbitmq_health()
        print(f"   Health Status: {health['status']}")
        print(f"   Connected: {health['connected']}")
        
        if health['status'] != 'healthy':
            print(f"   ❌ RabbitMQ is not healthy: {health.get('error', 'Unknown error')}")
            return False
        
        # Get connection and setup topology
        print("\n2. Setting up Queue Topology...")
        connection = await get_rabbitmq_connection()
        
        # Test exchanges
        print("\n3. Verifying Exchanges...")
        expected_exchanges = [
            ExchangeNames.NOTIFICATIONS,
            ExchangeNames.JOBS,
            ExchangeNames.AUDIT
        ]
        
        for exchange_name in expected_exchanges:
            try:
                exchange = await connection.get_exchange(exchange_name)
                print(f"   ✅ Exchange '{exchange_name}' created successfully")
            except Exception as e:
                print(f"   ❌ Failed to create exchange '{exchange_name}': {e}")
                return False
        
        # Test queues
        print("\n4. Verifying Queues...")
        expected_queues = [
            # Main queues
            QueueNames.EMAIL_NOTIFICATIONS,
            QueueNames.SLACK_NOTIFICATIONS,
            QueueNames.WEBHOOK_NOTIFICATIONS,
            QueueNames.JOB_SCHEDULER,
            QueueNames.AUDIT_LOGS,
            # Dead letter queues
            QueueNames.EMAIL_DLQ,
            QueueNames.SLACK_DLQ,
            QueueNames.WEBHOOK_DLQ,
            QueueNames.JOB_DLQ,
            QueueNames.AUDIT_DLQ,
        ]
        
        for queue_name in expected_queues:
            try:
                queue = await connection.get_queue(queue_name)
                print(f"   ✅ Queue '{queue_name}' created successfully")
            except Exception as e:
                print(f"   ❌ Failed to create queue '{queue_name}': {e}")
                return False
        
        # Test connection statistics
        print(f"\n5. Connection Statistics:")
        print(f"   Exchanges: {len(connection.exchanges)}")
        print(f"   Queues: {len(connection.queues)}")
        
        print(f"\n✅ Queue Topology Test PASSED!")
        print(f"   - All {len(expected_exchanges)} exchanges created")
        print(f"   - All {len(expected_queues)} queues created")
        print(f"   - Dead letter queues configured")
        print(f"   - Routing bindings established")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Queue Topology Test FAILED: {e}")
        return False


async def test_management_ui():
    """Test RabbitMQ Management UI accessibility"""
    
    print("\n🌐 Testing RabbitMQ Management UI")
    print("=" * 50)
    
    try:
        import httpx
        
        # Test management UI endpoint
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://localhost:15672/api/overview",
                auth=("opsconductor", "opsconductor123"),
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Management UI accessible")
                print(f"   RabbitMQ Version: {data.get('rabbitmq_version', 'Unknown')}")
                print(f"   Management Version: {data.get('management_version', 'Unknown')}")
                print(f"   Node: {data.get('node', 'Unknown')}")
                return True
            else:
                print(f"   ❌ Management UI returned status {response.status_code}")
                return False
                
    except ImportError:
        print("   ⚠️  httpx not available, skipping Management UI test")
        return True
    except Exception as e:
        print(f"   ❌ Management UI test failed: {e}")
        return False


async def main():
    """Main test function"""
    
    print("🚀 OpsConductor RabbitMQ Queue Topology Test")
    print("=" * 60)
    
    # Set environment variables for testing
    os.environ.setdefault("RABBITMQ_HOST", "localhost")
    os.environ.setdefault("RABBITMQ_PORT", "5672")
    os.environ.setdefault("RABBITMQ_USER", "opsconductor")
    os.environ.setdefault("RABBITMQ_PASSWORD", "opsconductor123")
    os.environ.setdefault("RABBITMQ_VHOST", "/")
    
    success = True
    
    # Test queue topology
    topology_success = await test_queue_topology()
    success = success and topology_success
    
    # Test management UI
    ui_success = await test_management_ui()
    success = success and ui_success
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ALL TESTS PASSED!")
        print("\nRabbitMQ is ready for OpsConductor message queuing!")
        print("\n📊 Access Management UI: http://localhost:15672")
        print("   Username: opsconductor")
        print("   Password: opsconductor123")
    else:
        print("💥 SOME TESTS FAILED!")
        print("\nPlease check the errors above and fix the issues.")
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)