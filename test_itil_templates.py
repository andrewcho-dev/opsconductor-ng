#!/usr/bin/env python3
"""
Test script to validate all ITIL intent templates are working correctly.
"""

import asyncio
import sys
import os

# Add the ai-brain directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai-brain'))

from brains.intent_brain.itil_classifier import ITILOperationsClassifier, ITILOperationsType

async def test_all_itil_categories():
    """Test all ITIL operations categories with sample messages."""
    
    classifier = ITILOperationsClassifier()
    
    # Test cases for each ITIL operations type
    test_cases = {
        ITILOperationsType.INCIDENT_MANAGEMENT: [
            "The production server is down and users cannot access the application",
            "Database connection timeout errors are occurring",
            "Website is returning 503 service unavailable errors"
        ],
        ITILOperationsType.PROBLEM_MANAGEMENT: [
            "We need to investigate the root cause of recurring database timeouts",
            "There's a pattern of network failures every Tuesday morning",
            "Frequent application crashes need underlying analysis"
        ],
        ITILOperationsType.CHANGE_ENABLEMENT: [
            "Need to update the operating system to the latest version",
            "Plan to migrate the database to a new server",
            "Modify firewall configuration to allow new traffic"
        ],
        ITILOperationsType.DEPLOYMENT_MANAGEMENT: [
            "Deploy the new application version to production",
            "Rollout the updated software package to all servers",
            "Need to rollback the last release due to issues"
        ],
        ITILOperationsType.INFRASTRUCTURE_PLATFORM_MANAGEMENT: [
            "Update the CMDB with new server configurations",
            "Maintain inventory of all network assets",
            "Document the current system baseline configuration"
        ],
        ITILOperationsType.SERVICE_REQUEST_FULFILLMENT: [
            "Install new software on my workstation",
            "Create a new user account with database access",
            "Provision additional storage for the project"
        ],
        ITILOperationsType.TECHNICAL_SUPPORT: [
            "Grant admin privileges to the new team member",
            "Setup authentication for the new application",
            "Provide technical guidance for server configuration"
        ],
        ITILOperationsType.PERFORMANCE_CAPACITY_MANAGEMENT: [
            "Scale up the server resources for increased load",
            "Optimize database performance for better throughput",
            "Expand storage capacity for growing data needs"
        ],
        ITILOperationsType.NETWORK_OPERATIONS: [
            "Setup redundancy to meet 99.9% uptime SLA",
            "Configure failover for critical services",
            "Troubleshoot network connectivity issues"
        ],
        ITILOperationsType.MAINTENANCE_OPERATIONS: [
            "Develop disaster recovery plan for data center",
            "Test business continuity procedures",
            "Setup backup strategy for critical systems"
        ],
        ITILOperationsType.NETWORK_SECURITY_OPERATIONS: [
            "Configure firewall rules for new application",
            "Install SSL certificates on web servers",
            "Review security policies and access controls"
        ],
        ITILOperationsType.MONITORING_EVENT_MANAGEMENT: [
            "Setup monitoring for application performance",
            "Configure alerts for system health checks",
            "Create dashboard for infrastructure metrics"
        ],
        ITILOperationsType.NETWORK_CAPACITY_PLANNING: [
            "Plan network bandwidth for new office",
            "Analyze network traffic patterns",
            "Optimize network capacity utilization"
        ]
    }
    
    print("=" * 80)
    print("ITIL INTENT TEMPLATES VALIDATION TEST")
    print("=" * 80)
    
    total_tests = 0
    passed_tests = 0
    
    for expected_type, messages in test_cases.items():
        print(f"\n🔍 Testing {expected_type.value.upper().replace('_', ' ')}")
        print("-" * 60)
        
        for i, message in enumerate(messages, 1):
            total_tests += 1
            
            try:
                # Classify the message
                classification = await classifier.classify_intent(message)
                
                # Check if classification matches expected type
                if classification.operations_type == expected_type:
                    passed_tests += 1
                    status = "✅ PASS"
                else:
                    status = f"❌ FAIL (got {classification.operations_type.value})"
                
                print(f"  {i}. {status}")
                print(f"     Message: {message[:60]}...")
                print(f"     Classified as: {classification.operations_type.value}")
                print(f"     Category: {classification.category}")
                print(f"     Subcategory: {classification.subcategory}")
                print(f"     Confidence: {classification.confidence:.2f}")
                print(f"     Priority: {classification.priority.value}")
                print(f"     Urgency: {classification.urgency.value}")
                print()
                
            except Exception as e:
                print(f"  {i}. ❌ ERROR: {str(e)}")
                print(f"     Message: {message[:60]}...")
                print()
    
    print("=" * 80)
    print("ITIL TEMPLATES TEST RESULTS")
    print("=" * 80)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL ITIL INTENT TEMPLATES ARE FULLY DEVELOPED AND WORKING! 🎉")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} templates need improvement")
    
    print("=" * 80)
    
    # Test coverage summary
    print("\n📊 ITIL SERVICE TYPE COVERAGE:")
    print("-" * 40)
    for service_type in ITILServiceType:
        if service_type in test_cases:
            print(f"✅ {service_type.value.replace('_', ' ').title()}")
        else:
            print(f"❌ {service_type.value.replace('_', ' ').title()}")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    asyncio.run(test_all_itil_categories())