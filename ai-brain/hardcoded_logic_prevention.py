"""
🚨 HARDCODED LOGIC PREVENTION SYSTEM 🚨

This module contains safeguards to prevent any hardcoded decision-making logic
from being introduced into the OpsConductor AI system.

ALL DECISIONS MUST BE MADE BY OLLAMA LLM - NO EXCEPTIONS

This file serves as:
1. A permanent reminder of the no-hardcoded-logic policy
2. Utility functions to detect hardcoded patterns
3. Enforcement mechanisms to prevent hardcoded fallbacks
4. Clear error messages when LLM fails

VIOLATION OF THESE RULES WILL RESULT IN SYSTEM FAILURE
"""

import re
import logging
from typing import List, Dict, Any, Optional
from functools import wraps

logger = logging.getLogger(__name__)

# 🚨 FORBIDDEN PATTERNS 🚨
# These patterns indicate hardcoded decision-making logic
FORBIDDEN_PATTERNS = [
    # Pattern matching for intent classification (CRITICAL VIOLATIONS)
    r'if\s+any\s*\(\s*word\s+in\s+.*\.lower\(\).*for\s+word\s+in\s+\[',
    r'for\s+pattern\s+in\s+.*_patterns:',
    r'if\s+.*\.lower\(\)\s*in\s*\[.*status.*health.*running',
    # Note: Removed endswith('?') check as it's legitimate string formatting, not decision logic
    
    # Hardcoded word lists for decision making (CRITICAL VIOLATIONS)
    r'question_patterns\s*=\s*\[.*what.*how.*when',
    r'job_patterns\s*=\s*\[.*restart.*stop.*start',
    r'status_words\s*=\s*\[.*online.*active.*running',
    r'action_words\s*=\s*\[.*create.*make.*automate',
    
    # Hardcoded status validation (CRITICAL VIOLATIONS)
    r'if\s+.*\.status\s+not\s+in\s+\[.*online.*active.*running',
    r'if\s+.*\.status\s*==\s*[\'\"](online|active|running)[\'\"]\s*:',
    
    # Hardcoded service mappings for decision making (CRITICAL VIOLATIONS)
    r'service_mappings\s*=\s*\{.*asset-service.*automation-service',
    r'if\s+service_name\s+in\s+text\s*:.*detected_services',
    
    # Hardcoded intent classification functions (CRITICAL VIOLATIONS)
    r'def\s+classify_intent\s*\(.*message.*\)\s*:',
    r'def\s+handle_question\s*\(.*message.*\)\s*:',
]

# 🚨 FORBIDDEN IMPORTS 🚨
# These imports often indicate hardcoded pattern matching
FORBIDDEN_IMPORTS = [
    'import re  # for pattern matching',
    'from re import',
]

# 🚨 FORBIDDEN FUNCTIONS 🚨
# These function names indicate hardcoded decision making
FORBIDDEN_FUNCTION_NAMES = [
    'classify_intent',
    'parse_intent_patterns', 
    'match_keywords',
    'detect_intent_type',
    'categorize_message',
    'pattern_match',
]

class HardcodedLogicViolationError(Exception):
    """Raised when hardcoded decision-making logic is detected"""
    pass

def no_hardcoded_logic(func):
    """Decorator to prevent hardcoded logic in functions"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        function_name = func.__name__
        
        # Check if function name itself is forbidden
        if function_name in FORBIDDEN_FUNCTION_NAMES:
            raise HardcodedLogicViolationError(
                f"🚨 HARDCODED LOGIC VIOLATION: Function '{function_name}' "
                f"indicates hardcoded decision-making. Use LLM instead!"
            )
        
        logger.info(f"Executing {function_name} - ensuring LLM-only decision making")
        
        try:
            result = await func(*args, **kwargs)
            logger.info(f"✅ {function_name} completed using LLM decisions only")
            return result
        except Exception as e:
            if "pattern" in str(e).lower() or "hardcoded" in str(e).lower():
                raise HardcodedLogicViolationError(
                    f"🚨 HARDCODED LOGIC DETECTED in {function_name}: {e}"
                )
            raise
    
    return wrapper

def validate_no_hardcoded_patterns(code_content: str, file_path: str) -> List[str]:
    """Validate that code doesn't contain hardcoded decision-making patterns"""
    violations = []
    
    # Skip validation for the hardcoded logic prevention files themselves
    if 'hardcoded_logic_prevention.py' in file_path or 'startup_hardcoded_check.py' in file_path:
        return violations
    
    for pattern in FORBIDDEN_PATTERNS:
        matches = re.finditer(pattern, code_content, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            line_num = code_content[:match.start()].count('\n') + 1
            violations.append(
                f"🚨 HARDCODED PATTERN in {file_path}:{line_num}: {match.group()}"
            )
    
    return violations

def llm_only_decision(decision_context: str, llm_service, prompt: str) -> Any:
    """Enforce that all decisions go through LLM - no fallbacks allowed"""
    try:
        logger.info(f"Making LLM-only decision for: {decision_context}")
        
        response = llm_service.generate_response(prompt)
        
        if not response:
            raise HardcodedLogicViolationError(
                f"🚨 LLM DECISION FAILED for {decision_context}. "
                f"NO HARDCODED FALLBACK ALLOWED. Fix LLM interaction instead."
            )
        
        logger.info(f"✅ LLM decision completed for: {decision_context}")
        return response
        
    except Exception as e:
        raise HardcodedLogicViolationError(
            f"🚨 LLM DECISION FAILED for {decision_context}: {e}. "
            f"HARDCODED FALLBACKS ARE FORBIDDEN. Fix the LLM prompt or service."
        )

def enforce_llm_only_parsing(response_text: str, context: str) -> Dict[str, Any]:
    """Enforce that parsing failures result in clear errors, not hardcoded fallbacks"""
    try:
        import json
        return json.loads(response_text)
    except json.JSONDecodeError as e:
        raise HardcodedLogicViolationError(
            f"🚨 LLM PARSING FAILED for {context}: {e}. "
            f"LLM response: '{response_text[:200]}...'. "
            f"HARDCODED PARSING FALLBACKS ARE FORBIDDEN. "
            f"Fix the LLM prompt to produce valid JSON instead."
        )

def create_anti_hardcoded_prompt(base_prompt: str) -> str:
    """Create a prompt that explicitly prevents hardcoded-style responses"""
    return f"""
{base_prompt}

🚨 CRITICAL INSTRUCTIONS:
- Use your natural language understanding, not pattern matching
- Make intelligent decisions based on context, not keyword matching  
- Provide structured JSON responses when requested
- Do not fall back to simple word matching or pattern detection
- Think contextually about what the user actually wants to accomplish

Your response will be parsed programmatically, so follow the requested format exactly.
"""

# 🚨 SYSTEM INTEGRITY CHECKS 🚨

def audit_system_for_hardcoded_logic(ai_brain_path: str) -> Dict[str, List[str]]:
    """Audit the entire AI brain system for hardcoded logic violations"""
    import os
    
    violations = {}
    
    for root, dirs, files in os.walk(ai_brain_path):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    file_violations = validate_no_hardcoded_patterns(content, file_path)
                    if file_violations:
                        violations[file_path] = file_violations
                        
                except Exception as e:
                    logger.warning(f"Could not audit {file_path}: {e}")
    
    return violations

def generate_violation_report(violations: Dict[str, List[str]]) -> str:
    """Generate a comprehensive report of hardcoded logic violations"""
    if not violations:
        return "✅ NO HARDCODED LOGIC VIOLATIONS DETECTED - SYSTEM CLEAN"
    
    report = "🚨 HARDCODED LOGIC VIOLATIONS DETECTED:\n\n"
    
    total_violations = 0
    for file_path, file_violations in violations.items():
        report += f"📁 {file_path}:\n"
        for violation in file_violations:
            report += f"   {violation}\n"
            total_violations += 1
        report += "\n"
    
    report += f"🚨 TOTAL VIOLATIONS: {total_violations}\n"
    report += "🚨 ALL VIOLATIONS MUST BE FIXED BEFORE SYSTEM CAN OPERATE\n"
    report += "🚨 REPLACE ALL HARDCODED LOGIC WITH LLM DECISION-MAKING\n"
    
    return report

# 🚨 PERMANENT ENFORCEMENT 🚨

class HardcodedLogicEnforcer:
    """Permanent enforcement system to prevent hardcoded logic"""
    
    def __init__(self):
        self.violations_detected = 0
        self.enforcement_active = True
    
    def check_function_call(self, function_name: str, args: tuple, kwargs: dict):
        """Check if a function call violates hardcoded logic rules"""
        if not self.enforcement_active:
            return
        
        # Check for forbidden function names
        if function_name in FORBIDDEN_FUNCTION_NAMES:
            self.violations_detected += 1
            raise HardcodedLogicViolationError(
                f"🚨 FORBIDDEN FUNCTION CALL: {function_name} "
                f"indicates hardcoded decision-making logic!"
            )
        
        # Check for pattern matching in arguments
        for arg in args:
            if isinstance(arg, str) and any(pattern in arg.lower() for pattern in ['pattern', 'match', 'keyword']):
                self.violations_detected += 1
                raise HardcodedLogicViolationError(
                    f"🚨 HARDCODED PATTERN DETECTED in {function_name} arguments: {arg}"
                )
    
    def get_violation_count(self) -> int:
        """Get total number of violations detected"""
        return self.violations_detected
    
    def reset_violations(self):
        """Reset violation counter"""
        self.violations_detected = 0

# Global enforcer instance
ENFORCER = HardcodedLogicEnforcer()

# 🚨 FINAL WARNING 🚨
"""
THIS SYSTEM IS DESIGNED TO PREVENT ANY HARDCODED DECISION-MAKING LOGIC
FROM BEING INTRODUCED INTO THE OPSCONDUCTOR AI SYSTEM.

ALL INTELLIGENCE MUST COME FROM OLLAMA LLM.

IF YOU NEED TO MAKE A DECISION:
1. Create a clear, specific prompt for the LLM
2. Send it to the LLM service
3. Parse the LLM response
4. If parsing fails, improve the prompt - DO NOT ADD FALLBACKS

NEVER:
- Use pattern matching for intent classification
- Create hardcoded word lists for decision making
- Add fallback logic that bypasses the LLM
- Use simple keyword matching for complex decisions

THE LLM IS INTELLIGENT ENOUGH TO HANDLE ALL DECISION-MAKING.
TRUST THE LLM. DO NOT HARDCODE.

🚨 VIOLATION OF THESE RULES WILL RESULT IN SYSTEM FAILURE 🚨
"""