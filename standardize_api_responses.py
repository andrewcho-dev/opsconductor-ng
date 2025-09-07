#!/usr/bin/env python3
"""
API Response Standardization Script
Systematically updates all services to use standardized response patterns
"""

import os
import re
import sys
from pathlib import Path

# Service directories to process
SERVICES = [
    "auth-service",
    "user-service", 
    "credentials-service",
    "notification-service",
    "jobs-service",
    "targets-service",
    "scheduler-service",
    "executor-service",
    "discovery-service",
    "step-libraries-service"
]

def analyze_response_patterns(service_dir):
    """Analyze current response patterns in a service"""
    main_py = Path(service_dir) / "main.py"
    if not main_py.exists():
        return []
    
    with open(main_py, 'r') as f:
        content = f.read()
    
    patterns = []
    
    # Find simple message returns
    message_returns = re.findall(r'return\s+\{\s*["\']message["\']\s*:\s*["\'][^"\']+["\']\s*\}', content)
    patterns.extend([("simple_message", match) for match in message_returns])
    
    # Find HTTPException raises
    http_exceptions = re.findall(r'raise\s+HTTPException\([^)]+\)', content)
    patterns.extend([("http_exception", match) for match in http_exceptions])
    
    # Find direct data returns (harder to detect automatically)
    # This would need more sophisticated parsing
    
    return patterns

def generate_standardization_report():
    """Generate a report of response patterns across all services"""
    print("=== API Response Standardization Analysis ===\n")
    
    total_patterns = 0
    
    for service in SERVICES:
        service_path = Path("/home/opsconductor") / service
        if not service_path.exists():
            print(f"⚠️  {service}: Directory not found")
            continue
            
        patterns = analyze_response_patterns(service_path)
        total_patterns += len(patterns)
        
        print(f"📊 {service}:")
        print(f"   Simple message returns: {len([p for p in patterns if p[0] == 'simple_message'])}")
        print(f"   HTTPException raises: {len([p for p in patterns if p[0] == 'http_exception'])}")
        print()
    
    print(f"📈 Total patterns to standardize: {total_patterns}")
    
    return total_patterns

def create_standardization_plan():
    """Create a detailed plan for standardizing responses"""
    plan = {
        "phase1_simple_messages": [
            "Replace simple {'message': '...'} returns with create_success_response()",
            "Add data context where appropriate",
            "Ensure consistent message formatting"
        ],
        "phase2_error_handling": [
            "Replace HTTPException with shared error classes",
            "Use handle_database_error() for database exceptions", 
            "Add proper error context and logging"
        ],
        "phase3_data_responses": [
            "Wrap single item responses in StandardResponse",
            "Use PaginatedResponse for list endpoints",
            "Add metadata where beneficial"
        ],
        "phase4_bulk_operations": [
            "Use BulkOperationResult for bulk operations",
            "Add detailed success/failure reporting",
            "Include operation summaries"
        ]
    }
    
    print("=== Standardization Plan ===\n")
    for phase, tasks in plan.items():
        print(f"🎯 {phase.replace('_', ' ').title()}:")
        for task in tasks:
            print(f"   • {task}")
        print()
    
    return plan

def show_examples():
    """Show before/after examples of standardization"""
    examples = [
        {
            "title": "Simple Message Response",
            "before": 'return {"message": "Target deleted successfully"}',
            "after": '''return create_success_response(
    message="Target deleted successfully",
    data={"target_id": target_id}
)'''
        },
        {
            "title": "Error Handling",
            "before": 'raise HTTPException(status_code=404, detail="Target not found")',
            "after": 'raise NotFoundError("Target not found")'
        },
        {
            "title": "Data Response",
            "before": 'return target_data',
            "after": '''return create_success_response(
    data=target_data,
    message="Target retrieved successfully"
)'''
        },
        {
            "title": "List Response",
            "before": 'return {"targets": targets, "total": total}',
            "after": '''return PaginatedResponse.create(
    items=targets,
    page=page,
    per_page=per_page,
    total_items=total
)'''
        }
    ]
    
    print("=== Standardization Examples ===\n")
    for example in examples:
        print(f"🔄 {example['title']}:")
        print(f"   Before: {example['before']}")
        print(f"   After:  {example['after']}")
        print()

def main():
    """Main function to run the analysis"""
    print("🚀 Starting API Response Standardization Analysis...\n")
    
    # Generate analysis report
    total_patterns = generate_standardization_report()
    
    # Show standardization plan
    create_standardization_plan()
    
    # Show examples
    show_examples()
    
    print("=== Next Steps ===")
    print("1. Review the analysis above")
    print("2. Start with Phase 1: Simple message standardization")
    print("3. Progress through each phase systematically")
    print("4. Test each service after standardization")
    print("5. Update API documentation to reflect new response formats")
    
    print(f"\n✅ Analysis complete. Found {total_patterns} patterns to standardize.")

if __name__ == "__main__":
    main()