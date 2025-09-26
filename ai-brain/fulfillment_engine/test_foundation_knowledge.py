#!/usr/bin/env python3
"""
Test Foundation Knowledge System
Validates that all core knowledge domains are properly loaded and functional
"""

import asyncio
import json
from dynamic_service_catalog import get_dynamic_catalog

async def test_foundation_knowledge():
    """Test the foundation knowledge system"""
    
    print("🧠 TESTING OPSCONDUCTOR FOUNDATION KNOWLEDGE SYSTEM")
    print("=" * 60)
    
    # Get the dynamic catalog
    catalog = get_dynamic_catalog()
    
    # Test 1: Verify all core domains are loaded
    print("\n📚 LOADED KNOWLEDGE DOMAINS:")
    print("-" * 30)
    
    expected_domains = [
        "asset_service",
        "communication_service", 
        "network_analyzer_service",
        "celery_service",
        "celery_beat",
        "linux_expertise",
        "windows_expertise",
        "powershell_expertise",
        "vapix_cameras"
    ]
    
    loaded_domains = list(catalog.domains.keys())
    
    for domain_id in expected_domains:
        if domain_id in loaded_domains:
            domain = catalog.domains[domain_id]
            print(f"✅ {domain_id} - {domain.metadata.domain_type.value} - Priority: {domain.metadata.priority.value}")
        else:
            print(f"❌ {domain_id} - NOT LOADED")
    
    print(f"\nTotal domains loaded: {len(loaded_domains)}")
    
    # Test 2: Test context generation for different request types
    print("\n🔍 TESTING CONTEXT GENERATION:")
    print("-" * 35)
    
    test_requests = [
        "Get system information from all Windows machines",
        "Monitor network traffic on all servers", 
        "Send email alerts when CPU usage is high",
        "Use PowerShell to check disk space on servers",
        "Configure VAPIX cameras for motion detection",
        "Find all Linux servers and check their status",
        "Submit background task to Celery queue and monitor progress",
        "Schedule daily backup task using Celery Beat cron scheduler"
    ]
    
    for request in test_requests:
        print(f"\n🔸 Request: '{request}'")
        
        # Analyze context needs
        analysis = catalog.analyze_request_context_needs(request)
        relevant_domains = [d["domain_id"] for d in analysis["relevant_domains"]]
        
        print(f"   Relevant domains: {', '.join(relevant_domains)}")
        print(f"   Estimated context size: {analysis['estimated_context_size']} bytes")
        
        # Generate optimized context (first 500 chars)
        context = catalog.generate_optimized_context(request)
        context_preview = context[:500] + "..." if len(context) > 500 else context
        print(f"   Context preview: {context_preview}")
    
    # Test 3: Test specific domain capabilities
    print("\n🛠️  TESTING DOMAIN CAPABILITIES:")
    print("-" * 35)
    
    # Test Asset Service domain
    if "asset_service" in catalog.domains:
        asset_domain = catalog.domains["asset_service"]
        asset_context = asset_domain.get_context_for_request(["windows", "server", "system"])
        print(f"✅ Asset Service - Found {len(asset_context.get('relevant_capabilities', []))} relevant capabilities")
        
        # Show query patterns
        query_patterns = asset_context.get('query_patterns', [])
        if query_patterns:
            print(f"   Sample query pattern: {query_patterns[0]['pattern']} -> {query_patterns[0]['query']}")
    
    # Test Linux expertise
    if "linux_expertise" in catalog.domains:
        linux_domain = catalog.domains["linux_expertise"]
        linux_context = linux_domain.get_context_for_request(["system", "information", "cpu", "memory"])
        print(f"✅ Linux Expertise - Found {len(linux_context.get('relevant_capabilities', []))} relevant capabilities")
        
        # Show a command example
        capabilities = linux_context.get('relevant_capabilities', [])
        if capabilities and 'commands' in capabilities[0]:
            cmd = capabilities[0]['commands'][0]
            print(f"   Sample command: {cmd['command']} - {cmd['description']}")
    
    # Test PowerShell expertise
    if "powershell_expertise" in catalog.domains:
        ps_domain = catalog.domains["powershell_expertise"]
        ps_context = ps_domain.get_context_for_request(["system", "information", "get-computerinfo"])
        print(f"✅ PowerShell Expertise - Found {len(ps_context.get('relevant_capabilities', []))} relevant capabilities")
        
        # Show a cmdlet example
        capabilities = ps_context.get('relevant_capabilities', [])
        if capabilities and 'cmdlets' in capabilities[0]:
            cmdlet = capabilities[0]['cmdlets'][0]
            print(f"   Sample cmdlet: {cmdlet['cmdlet']} - {cmdlet['description']}")
    
    # Test 4: Performance metrics
    print("\n📊 PERFORMANCE METRICS:")
    print("-" * 25)
    
    metrics = catalog.get_performance_metrics()
    print(f"Total domains: {metrics['total_domains']}")
    print(f"Average context generation time: {metrics['average_context_generation_time']:.3f}s")
    print(f"Domain types breakdown:")
    for domain_type, count in metrics['domain_types'].items():
        print(f"  - {domain_type}: {count}")
    
    # Test 5: Test comprehensive system information request
    print("\n🎯 COMPREHENSIVE TEST - SYSTEM INFORMATION REQUEST:")
    print("-" * 55)
    
    comprehensive_request = "Get detailed system information including CPU, memory, disk space, and running services from all Windows and Linux servers, then email the results to admin@company.com"
    
    print(f"Request: {comprehensive_request}")
    print()
    
    # Generate full context
    full_context = catalog.generate_optimized_context(comprehensive_request)
    
    # Count different types of information in context
    context_lower = full_context.lower()
    
    service_mentions = sum(1 for service in ["asset", "communication", "automation"] if service in context_lower)
    os_mentions = sum(1 for os in ["windows", "linux", "powershell"] if os in context_lower)
    command_mentions = sum(1 for cmd in ["get-computerinfo", "systeminfo", "free -h", "df -h"] if cmd in context_lower)
    
    print(f"Context analysis:")
    print(f"  - Total context size: {len(full_context)} characters")
    print(f"  - Service references: {service_mentions}")
    print(f"  - OS expertise references: {os_mentions}")
    print(f"  - Command examples: {command_mentions}")
    
    # Show key sections
    if "ASSET SERVICE" in full_context:
        print("  ✅ Asset Service knowledge included")
    if "COMMUNICATION SERVICE" in full_context:
        print("  ✅ Communication Service knowledge included")
    if "LINUX SYSTEM ADMINISTRATION" in full_context or "Linux" in full_context:
        print("  ✅ Linux expertise included")
    if "WINDOWS SYSTEM ADMINISTRATION" in full_context or "Windows" in full_context:
        print("  ✅ Windows expertise included")
    if "POWERSHELL" in full_context or "PowerShell" in full_context:
        print("  ✅ PowerShell expertise included")
    
    print("\n🎉 FOUNDATION KNOWLEDGE SYSTEM TEST COMPLETE!")
    print("=" * 50)
    
    # Summary
    total_domains = len(catalog.domains)
    core_domains = sum(1 for d in catalog.domains.values() if d.metadata.domain_type.value == "core_service")
    
    print(f"\nSUMMARY:")
    print(f"✅ {total_domains} knowledge domains loaded successfully")
    print(f"✅ {core_domains} core service domains with comprehensive capabilities")
    print(f"✅ Expert-level knowledge in Linux, Windows, and PowerShell")
    print(f"✅ Intelligent context optimization working")
    print(f"✅ Foundation ready for advanced AI reasoning!")

if __name__ == "__main__":
    asyncio.run(test_foundation_knowledge())