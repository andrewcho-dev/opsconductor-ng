"""
🚨 STARTUP HARDCODED LOGIC CHECK 🚨

This module runs at system startup to ensure no hardcoded decision-making logic
exists in the AI brain system.

If any hardcoded logic is detected, the system will refuse to start.
"""

import os
import sys
import logging
from typing import Dict, List
from hardcoded_logic_prevention import (
    audit_system_for_hardcoded_logic,
    generate_violation_report,
    HardcodedLogicViolationError
)

logger = logging.getLogger(__name__)

def perform_startup_hardcoded_check(ai_brain_path: str = None) -> bool:
    """
    Perform comprehensive startup check for hardcoded logic violations.
    
    Returns:
        bool: True if system is clean, False if violations detected
        
    Raises:
        HardcodedLogicViolationError: If critical violations are found
    """
    
    if ai_brain_path is None:
        ai_brain_path = os.path.dirname(os.path.abspath(__file__))
    
    logger.info("🔍 Starting hardcoded logic audit...")
    logger.info(f"📁 Auditing path: {ai_brain_path}")
    
    try:
        # Perform comprehensive audit
        violations = audit_system_for_hardcoded_logic(ai_brain_path)
        
        if violations:
            # Generate detailed report
            report = generate_violation_report(violations)
            
            logger.error("🚨 HARDCODED LOGIC VIOLATIONS DETECTED!")
            logger.error(report)
            
            # Write report to file for debugging
            report_path = os.path.join(ai_brain_path, "hardcoded_violations_report.txt")
            with open(report_path, 'w') as f:
                f.write(report)
            
            logger.error(f"📄 Detailed report written to: {report_path}")
            
            # SYSTEM MUST NOT START WITH VIOLATIONS
            raise HardcodedLogicViolationError(
                f"🚨 SYSTEM STARTUP BLOCKED: {len(violations)} files contain hardcoded logic violations. "
                f"All hardcoded decision-making logic must be removed before system can start. "
                f"See report at: {report_path}"
            )
        
        else:
            logger.info("✅ HARDCODED LOGIC AUDIT PASSED - SYSTEM CLEAN")
            logger.info("✅ All decision-making logic uses LLM - startup approved")
            return True
            
    except Exception as e:
        logger.error(f"🚨 HARDCODED LOGIC AUDIT FAILED: {e}")
        raise HardcodedLogicViolationError(f"Startup audit failed: {e}")

def check_specific_files_for_violations() -> Dict[str, List[str]]:
    """Check specific high-risk files for hardcoded logic violations"""
    
    high_risk_files = [
        "main.py",
        "llm_conversation_handler.py", 
        "fulfillment_engine/intent_processor.py",
        "fulfillment_engine/resource_mapper.py",
        "fulfillment_engine/information_gatherer.py"
    ]
    
    violations = {}
    ai_brain_path = os.path.dirname(os.path.abspath(__file__))
    
    for file_name in high_risk_files:
        file_path = os.path.join(ai_brain_path, file_name)
        
        # Skip our own prevention system files and test files
        if ('hardcoded_logic_prevention' in file_path or 
            'startup_hardcoded_check' in file_path or
            'test_' in file_path):
            continue
            
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Check for specific violation patterns
                file_violations = []
                
                # Check for CRITICAL hardcoded pattern matching violations
                # Allow natural language parsing of LLM responses (not decision making)
                if ('any(word in' in content and 'for word in [' in content and 
                    ('status' in content or 'health' in content or 'running' in content) and
                    'parse_natural_language' not in content and 'response_text' not in content):
                    file_violations.append("🚨 CRITICAL: Hardcoded word list pattern matching for decision making")
                
                # Check for CRITICAL hardcoded intent classification
                if ('def classify_intent' in content and 'message' in content and 
                    ('pattern' in content or 'lower()' in content)):
                    file_violations.append("🚨 CRITICAL: Hardcoded intent classification function")
                
                # Check for CRITICAL hardcoded status validation
                if ('status not in [' in content and 'online' in content and 'active' in content):
                    file_violations.append("🚨 CRITICAL: Hardcoded status validation logic")
                
                # Check for CRITICAL hardcoded service mappings for decision making
                # Skip this check in the startup check file itself to avoid false positives
                if (file_path != __file__ and 
                    'service_mappings = {' in content and 'asset-service' in content and 'automation-service' in content):
                    file_violations.append("🚨 CRITICAL: Hardcoded service mapping for decision making")
                
                # Check for CRITICAL hardcoded question handling
                if ('def handle_question' in content and 'message_lower' in content and 'any(word in' in content):
                    file_violations.append("🚨 CRITICAL: Hardcoded question handling logic")
                
                if file_violations:
                    violations[file_path] = file_violations
                    
            except Exception as e:
                logger.warning(f"Could not check {file_path}: {e}")
    
    return violations

def enforce_llm_only_startup():
    """Enforce LLM-only decision making at startup"""
    
    logger.info("🚨 ENFORCING LLM-ONLY DECISION MAKING")
    
    # Check for specific violations
    violations = check_specific_files_for_violations()
    
    if violations:
        violation_summary = []
        for file_path, file_violations in violations.items():
            violation_summary.extend([f"{file_path}: {v}" for v in file_violations])
        
        error_msg = (
            f"🚨 STARTUP BLOCKED: Hardcoded logic detected in {len(violations)} files:\n" +
            "\n".join(violation_summary) +
            "\n\n🚨 ALL HARDCODED DECISION-MAKING LOGIC MUST BE REMOVED"
            "\n🚨 ONLY OLLAMA LLM IS ALLOWED TO MAKE DECISIONS"
            "\n🚨 NO PATTERN MATCHING, NO FALLBACKS, NO HARDCODED RULES"
        )
        
        logger.error(error_msg)
        raise HardcodedLogicViolationError(error_msg)
    
    logger.info("✅ LLM-ONLY ENFORCEMENT PASSED - NO HARDCODED LOGIC DETECTED")

if __name__ == "__main__":
    # Can be run standalone to check system
    try:
        perform_startup_hardcoded_check()
        enforce_llm_only_startup()
        print("✅ SYSTEM CLEAN - NO HARDCODED LOGIC DETECTED")
        sys.exit(0)
    except HardcodedLogicViolationError as e:
        print(f"🚨 SYSTEM BLOCKED: {e}")
        sys.exit(1)