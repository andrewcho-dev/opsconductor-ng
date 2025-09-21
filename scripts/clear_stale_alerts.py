#!/usr/bin/env python3
"""
Clear stale alerts and monitoring data for removed assets/services
"""

import asyncio
import redis.asyncio as redis
import json
import os
from datetime import datetime

async def clear_stale_monitoring_data():
    """Clear stale monitoring data from Redis"""
    
    # Connect to Redis
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_client = redis.from_url(redis_url, decode_responses=True)
    
    try:
        print("🧹 Clearing stale monitoring data...")
        
        # Clear current metrics
        await redis_client.delete("ai:metrics:current")
        print("✅ Cleared current metrics")
        
        # Clear analysis data
        await redis_client.delete("ai:analysis:latest")
        print("✅ Cleared latest analysis")
        
        # Clear time series data (last 24 hours)
        current_time = datetime.now().timestamp()
        for i in range(288):  # 24 hours * 12 (5-minute buckets)
            bucket_time = current_time - (i * 300)  # 5 minutes ago
            ts_key = f"ai:metrics:ts:{int(bucket_time / 300)}"
            await redis_client.delete(ts_key)
        
        print("✅ Cleared historical time series data")
        
        # Clear any asset-related cache keys
        asset_keys = []
        async for key in redis_client.scan_iter(match="*asset*"):
            asset_keys.append(key)
        
        if asset_keys:
            await redis_client.delete(*asset_keys)
            print(f"✅ Cleared {len(asset_keys)} asset-related cache keys")
        
        # Clear any monitoring-related cache keys
        monitoring_keys = []
        async for key in redis_client.scan_iter(match="*monitor*"):
            monitoring_keys.append(key)
        
        if monitoring_keys:
            await redis_client.delete(*monitoring_keys)
            print(f"✅ Cleared {len(monitoring_keys)} monitoring cache keys")
        
        # Clear any alert-related cache keys
        alert_keys = []
        async for key in redis_client.scan_iter(match="*alert*"):
            alert_keys.append(key)
        
        if alert_keys:
            await redis_client.delete(*alert_keys)
            print(f"✅ Cleared {len(alert_keys)} alert cache keys")
        
        print("🎉 Successfully cleared all stale monitoring data!")
        print("💡 The dashboard should now show fresh data without stale alerts.")
        
    except Exception as e:
        print(f"❌ Error clearing stale data: {e}")
    
    finally:
        await redis_client.close()

if __name__ == "__main__":
    asyncio.run(clear_stale_monitoring_data())