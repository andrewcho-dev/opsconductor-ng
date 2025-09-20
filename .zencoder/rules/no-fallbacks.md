---
alwaysApply: true
---

# CRITICAL RULE: NO FALLBACKS ALLOWED

## ABSOLUTE PROHIBITION ON FALLBACK CODE

**NEVER CREATE FALLBACK CODE WITHOUT EXPLICIT PERMISSION**

When implementing any functionality, you are STRICTLY FORBIDDEN from creating fallback mechanisms, try-catch blocks that silently continue, or any code that masks failures by providing alternative behavior.

### What is PROHIBITED:

1. **Exception handling that continues execution**:
   ```python
   # FORBIDDEN
   try:
       critical_function()
   except Exception as e:
       logger.warning("Function failed, using fallback")
       fallback_function()  # THIS IS FORBIDDEN
   ```

2. **Conditional fallbacks**:
   ```python
   # FORBIDDEN
   if not primary_system_available():
       use_backup_system()  # THIS IS FORBIDDEN
   ```

3. **Silent failure handling**:
   ```python
   # FORBIDDEN
   try:
       validate_request()
   except ValidationError:
       pass  # THIS IS FORBIDDEN - silently ignoring errors
   ```

### What you MUST do instead:

1. **Let failures fail fast and loud**:
   ```python
   # CORRECT
   try:
       critical_function()
   except Exception as e:
       logger.error(f"Critical function failed: {e}")
       raise  # Re-raise the exception
   ```

2. **Ask for permission before creating fallbacks**:
   - If you think a fallback is needed, STOP and ask the user first
   - Explain why you think a fallback is necessary
   - Get explicit approval before implementing any fallback logic

3. **Make failures visible**:
   - Use proper error handling that exposes the root cause
   - Return error responses that clearly indicate what failed
   - Log errors at appropriate levels (ERROR, CRITICAL)

### WHY THIS RULE EXISTS:

- Fallbacks mask real problems and prevent proper debugging
- They create false confidence in broken systems
- They make it impossible to know what's actually working
- They lead to silent failures that are discovered too late
- They prevent proper testing of the main code paths

### ENFORCEMENT:

- Any code that includes unauthorized fallbacks will be rejected
- You must explicitly ask before implementing any fallback mechanism
- All exceptions must be handled explicitly, not silently ignored
- All failures must be visible and traceable

### REMEMBER:

**IT IS BETTER FOR THE SYSTEM TO FAIL VISIBLY THAN TO WORK INCORRECTLY IN SILENCE**

If something is broken, we need to know about it immediately so we can fix it properly, not mask it with fallback code.