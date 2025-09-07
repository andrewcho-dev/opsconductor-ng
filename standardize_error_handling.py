#!/usr/bin/env python3
"""
Error Handling Standardization Script - Phase 2 of API Standardization
Systematically replaces HTTPException patterns with standardized error classes
"""

import os
import re
import glob
from typing import Dict, List, Tuple

# Error pattern mappings - handles both single-line and multi-line patterns
ERROR_PATTERNS = {
    # Multi-line HTTPException patterns (most common in our codebase)
    r'HTTPException\(\s*status_code=status\.HTTP_404_NOT_FOUND,\s*detail="([^"]+)"\s*\)': r'NotFoundError("\1")',
    r'HTTPException\(\s*status_code=status\.HTTP_400_BAD_REQUEST,\s*detail="([^"]+)"\s*\)': r'ValidationError("\1")',
    r'HTTPException\(\s*status_code=status\.HTTP_401_UNAUTHORIZED,\s*detail="([^"]+)"\s*\)': r'AuthError("\1")',
    r'HTTPException\(\s*status_code=status\.HTTP_403_FORBIDDEN,\s*detail="([^"]+)"\s*\)': r'PermissionError("\1")',
    r'HTTPException\(\s*status_code=status\.HTTP_500_INTERNAL_SERVER_ERROR,\s*detail="([^"]+)"\s*\)': r'DatabaseError("\1")',
    r'HTTPException\(\s*status_code=status\.HTTP_503_SERVICE_UNAVAILABLE,\s*detail="([^"]+)"\s*\)': r'ServiceCommunicationError("unknown", "\1")',
    r'HTTPException\(\s*status_code=status\.HTTP_409_CONFLICT,\s*detail="([^"]+)"\s*\)': r'ValidationError("\1")',
    
    # Single-line patterns (fallback)
    r'HTTPException\(status_code=404,\s*detail="([^"]+)"\)': r'NotFoundError("\1")',
    r'HTTPException\(status_code=400,\s*detail="([^"]+)"\)': r'ValidationError("\1")',
    r'HTTPException\(status_code=401,\s*detail="([^"]+)"\)': r'AuthError("\1")',
    r'HTTPException\(status_code=403,\s*detail="([^"]+)"\)': r'PermissionError("\1")',
    r'HTTPException\(status_code=500,\s*detail="([^"]+)"\)': r'DatabaseError("\1")',
    r'HTTPException\(status_code=503,\s*detail="([^"]+)"\)': r'ServiceCommunicationError("unknown", "\1")',
    r'HTTPException\(status_code=409,\s*detail="([^"]+)"\)': r'ValidationError("\1")',
}

# Services to update
SERVICES = [
    'discovery-service',
    'targets-service', 
    'credentials-service',
    'notification-service',
    'scheduler-service',
    'jobs-service',
    'user-service',
    'executor-service',
    'step-libraries-service'
]

def analyze_error_patterns():
    """Analyze current HTTPException patterns across all services"""
    print("🔍 Analyzing HTTPException patterns across services...")
    
    pattern_counts = {}
    service_patterns = {}
    
    for service in SERVICES:
        service_path = f"/home/opsconductor/{service}/main.py"
        if not os.path.exists(service_path):
            continue
            
        with open(service_path, 'r') as f:
            content = f.read()
            
        # Find all HTTPException patterns
        http_exceptions = re.findall(r'HTTPException\([^)]+\)', content)
        
        service_patterns[service] = len(http_exceptions)
        
        for exc in http_exceptions:
            if exc not in pattern_counts:
                pattern_counts[exc] = []
            pattern_counts[exc].append(service)
    
    print(f"\n📊 HTTPException Pattern Analysis:")
    print(f"{'Service':<25} {'Count':<10}")
    print("-" * 35)
    
    total_patterns = 0
    for service, count in service_patterns.items():
        print(f"{service:<25} {count:<10}")
        total_patterns += count
    
    print("-" * 35)
    print(f"{'TOTAL':<25} {total_patterns:<10}")
    
    return pattern_counts, service_patterns, total_patterns

def check_imports(service_path: str) -> Dict[str, bool]:
    """Check which error classes are already imported"""
    with open(service_path, 'r') as f:
        content = f.read()
    
    imports = {
        'NotFoundError': 'NotFoundError' in content,
        'ValidationError': 'ValidationError' in content,
        'AuthError': 'AuthError' in content,
        'PermissionError': 'PermissionError' in content,
        'DatabaseError': 'DatabaseError' in content,
        'ServiceCommunicationError': 'ServiceCommunicationError' in content,
        'handle_database_error': 'handle_database_error' in content
    }
    
    return imports

def add_missing_imports(service_path: str, needed_imports: List[str]):
    """Add missing error class imports to a service"""
    with open(service_path, 'r') as f:
        lines = f.readlines()
    
    # Find the shared.errors import line
    errors_import_line = -1
    for i, line in enumerate(lines):
        if 'from shared.errors import' in line:
            errors_import_line = i
            break
    
    if errors_import_line == -1:
        print(f"⚠️  Could not find shared.errors import in {service_path}")
        return False
    
    # Parse current imports
    current_line = lines[errors_import_line].strip()
    if current_line.endswith('\\'):
        # Multi-line import, find the end
        end_line = errors_import_line
        while end_line < len(lines) and lines[end_line].strip().endswith('\\'):
            end_line += 1
        end_line += 1
        
        # Combine all import lines
        import_text = ''.join(lines[errors_import_line:end_line])
        import_text = import_text.replace('\\\n', ' ').replace('\n', '')
    else:
        import_text = current_line
        end_line = errors_import_line + 1
    
    # Extract current imports
    import_match = re.search(r'from shared\.errors import (.+)', import_text)
    if not import_match:
        print(f"⚠️  Could not parse imports in {service_path}")
        return False
    
    current_imports = [imp.strip() for imp in import_match.group(1).split(',')]
    
    # Add missing imports
    all_imports = list(set(current_imports + needed_imports))
    all_imports.sort()
    
    # Create new import line
    new_import = f"from shared.errors import {', '.join(all_imports)}"
    
    # Replace the import lines
    lines[errors_import_line:end_line] = [new_import + '\n']
    
    # Write back to file
    with open(service_path, 'w') as f:
        f.writelines(lines)
    
    return True

def update_service_errors(service: str) -> Tuple[int, List[str]]:
    """Update HTTPException patterns in a service"""
    service_path = f"/home/opsconductor/{service}/main.py"
    if not os.path.exists(service_path):
        return 0, [f"Service {service} not found"]
    
    with open(service_path, 'r') as f:
        content = f.read()
    
    original_content = content
    replacements_made = 0
    issues = []
    
    # Check current imports
    current_imports = check_imports(service_path)
    needed_imports = []
    
    # Handle multi-line HTTPException patterns with DOTALL flag
    multiline_patterns = {
        r'raise\s+HTTPException\(\s*status_code=status\.HTTP_404_NOT_FOUND,\s*detail="([^"]+)"\s*\)': r'raise NotFoundError("\1")',
        r'raise\s+HTTPException\(\s*status_code=status\.HTTP_400_BAD_REQUEST,\s*detail="([^"]+)"\s*\)': r'raise ValidationError("\1")',
        r'raise\s+HTTPException\(\s*status_code=status\.HTTP_401_UNAUTHORIZED,\s*detail="([^"]+)"\s*\)': r'raise AuthError("\1")',
        r'raise\s+HTTPException\(\s*status_code=status\.HTTP_403_FORBIDDEN,\s*detail="([^"]+)"\s*\)': r'raise PermissionError("\1")',
        r'raise\s+HTTPException\(\s*status_code=status\.HTTP_500_INTERNAL_SERVER_ERROR,\s*detail="([^"]+)"\s*\)': r'raise DatabaseError("\1")',
        r'raise\s+HTTPException\(\s*status_code=status\.HTTP_503_SERVICE_UNAVAILABLE,\s*detail="([^"]+)"\s*\)': r'raise ServiceCommunicationError("unknown", "\1")',
        r'raise\s+HTTPException\(\s*status_code=status\.HTTP_409_CONFLICT,\s*detail="([^"]+)"\s*\)': r'raise ValidationError("\1")',
    }
    
    # Apply multi-line pattern replacements first
    for pattern, replacement in multiline_patterns.items():
        matches = re.findall(pattern, content, re.DOTALL)
        if matches:
            content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            replacements_made += len(matches)
            
            # Determine needed imports based on replacement
            if 'NotFoundError' in replacement and not current_imports['NotFoundError']:
                needed_imports.append('NotFoundError')
            elif 'ValidationError' in replacement and not current_imports['ValidationError']:
                needed_imports.append('ValidationError')
            elif 'AuthError' in replacement and not current_imports['AuthError']:
                needed_imports.append('AuthError')
            elif 'PermissionError' in replacement and not current_imports['PermissionError']:
                needed_imports.append('PermissionError')
            elif 'DatabaseError' in replacement and not current_imports['DatabaseError']:
                needed_imports.append('DatabaseError')
            elif 'ServiceCommunicationError' in replacement and not current_imports['ServiceCommunicationError']:
                needed_imports.append('ServiceCommunicationError')
    
    # Apply single-line pattern replacements
    for pattern, replacement in ERROR_PATTERNS.items():
        matches = re.findall(pattern, content)
        if matches:
            content = re.sub(pattern, replacement, content)
            replacements_made += len(matches)
            
            # Determine needed imports based on replacement
            if 'NotFoundError' in replacement and not current_imports['NotFoundError']:
                needed_imports.append('NotFoundError')
            elif 'ValidationError' in replacement and not current_imports['ValidationError']:
                needed_imports.append('ValidationError')
            elif 'AuthError' in replacement and not current_imports['AuthError']:
                needed_imports.append('AuthError')
            elif 'PermissionError' in replacement and not current_imports['PermissionError']:
                needed_imports.append('PermissionError')
            elif 'DatabaseError' in replacement and not current_imports['DatabaseError']:
                needed_imports.append('DatabaseError')
            elif 'ServiceCommunicationError' in replacement and not current_imports['ServiceCommunicationError']:
                needed_imports.append('ServiceCommunicationError')
    
    # Add missing imports
    if needed_imports:
        needed_imports = list(set(needed_imports))  # Remove duplicates
        if not add_missing_imports(service_path, needed_imports):
            issues.append(f"Failed to add imports: {needed_imports}")
    
    # Write updated content if changes were made
    if content != original_content:
        with open(service_path, 'w') as f:
            f.write(content)
    
    return replacements_made, issues

def main():
    """Main execution function"""
    print("🚀 Starting Error Handling Standardization - Phase 2")
    print("=" * 60)
    
    # Analyze current state
    pattern_counts, service_patterns, total_patterns = analyze_error_patterns()
    
    if total_patterns == 0:
        print("✅ No HTTPException patterns found - error handling already standardized!")
        return
    
    print(f"\n🎯 Target: Replace {total_patterns} HTTPException patterns with standardized error classes")
    print("\n🔄 Processing services...")
    
    total_replacements = 0
    all_issues = []
    
    for service in SERVICES:
        if service not in service_patterns or service_patterns[service] == 0:
            continue
            
        print(f"\n📝 Processing {service}...")
        replacements, issues = update_service_errors(service)
        
        if replacements > 0:
            print(f"   ✅ Replaced {replacements} patterns")
            total_replacements += replacements
        else:
            print(f"   ⏭️  No patterns to replace")
        
        if issues:
            print(f"   ⚠️  Issues: {', '.join(issues)}")
            all_issues.extend(issues)
    
    print("\n" + "=" * 60)
    print("📊 STANDARDIZATION SUMMARY")
    print("=" * 60)
    print(f"✅ Total patterns replaced: {total_replacements}")
    print(f"🎯 Services updated: {len([s for s in SERVICES if s in service_patterns and service_patterns[s] > 0])}")
    
    if all_issues:
        print(f"\n⚠️  Issues encountered:")
        for issue in all_issues:
            print(f"   - {issue}")
    
    print(f"\n🏆 Error handling standardization {'completed successfully!' if not all_issues else 'completed with issues'}")
    
    # Final verification
    print("\n🔍 Verifying results...")
    final_patterns, final_service_patterns, final_total = analyze_error_patterns()
    
    if final_total == 0:
        print("✅ Verification successful - all HTTPException patterns have been standardized!")
    else:
        print(f"⚠️  {final_total} HTTPException patterns remain - manual review may be needed")

if __name__ == "__main__":
    main()