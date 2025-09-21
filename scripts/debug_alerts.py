#!/usr/bin/env python3
"""
Debug the alert system to understand where the 4 stale alerts are coming from
"""

import sys
import os
sys.path.append('/home/opsconductor/opsconductor-ng')

from shared.ai_monitoring import AIMonitoringDashboard, MetricsCollector
import asyncio
import json

async def debug_alerts():
    """Debug the alert system"""
    
    print("🔍 Debugging AI Monitoring Alert System")
    print("=" * 50)
    
    # Create monitoring components
    metrics_collector = MetricsCollector()
    dashboard = AIMonitoringDashboard()
    
    print(f"📋 Configured services to monitor:")
    for service_name, service_url in metrics_collector.service_urls.items():
        print(f"  - {service_name}: {service_url}")
    
    print("\n🔄 Collecting current metrics...")
    try:
        # Collect current metrics
        current_metrics = await metrics_collector.collect_metrics()
        print(f"✅ Metrics collected at {current_metrics['timestamp']}")
        
        print(f"\n📊 Service status:")
        for service_name, metrics in current_metrics['services'].items():
            print(f"  - {service_name}: {metrics['status']} (response_time: {metrics.get('response_time', 'N/A')})")
        
        # Analyze and generate alerts
        print(f"\n🧠 Running analysis...")
        analysis = await dashboard.analyze_metrics([current_metrics])
        
        print(f"\n🚨 Generated alerts ({len(analysis.get('alerts', []))}):")
        for i, alert in enumerate(analysis.get('alerts', []), 1):
            print(f"  {i}. [{alert['severity'].upper()}] {alert['service']}: {alert['message']}")
        
        print(f"\n💡 Recommendations ({len(analysis.get('recommendations', []))}):")
        for i, rec in enumerate(analysis.get('recommendations', []), 1):
            print(f"  {i}. {rec}")
        
        print(f"\n📈 Overall health: {analysis.get('overall_health', 'unknown')}")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await metrics_collector.http_client.aclose()

if __name__ == "__main__":
    asyncio.run(debug_alerts())