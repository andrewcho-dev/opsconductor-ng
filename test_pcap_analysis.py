#!/usr/bin/env python3
"""
Test script to verify PCAP analysis works
"""

import sys
sys.path.append('/home/opsconductor/opsconductor-ng/network-analyzer-service')

import asyncio
from analyzers.protocol_analyzer import ProtocolAnalyzer
from models.analysis_models import NetworkProtocol

async def test_pcap_analysis():
    """Test PCAP file analysis directly"""
    analyzer = ProtocolAnalyzer()
    
    try:
        print("Testing HTTP protocol analysis on sample PCAP file...")
        
        result = await analyzer.analyze_protocol(
            protocol=NetworkProtocol.HTTP,
            data_source="/tmp/sample_http_traffic.pcap",
            filters={"port": 80}
        )
        
        print("Analysis completed successfully!")
        print(f"Results: {result}")
        
        return result
        
    except Exception as e:
        print(f"Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(test_pcap_analysis())
    if result:
        print("\n✅ PCAP Analysis SUCCESS!")
        print(f"Statistics: {result.get('statistics', {})}")
        print(f"Recommendations: {result.get('recommendations', [])}")
    else:
        print("\n❌ PCAP Analysis FAILED!")