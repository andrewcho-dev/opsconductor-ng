---
description: "OpsConductor Developer Guide Requirements - Essential reading for all development work"
alwaysApply: true
---

# OpsConductor Developer Guide Requirements

## 🚨 CRITICAL: Required Reading

**BEFORE starting any development work on OpsConductor, you MUST read and follow the [Developers Guide](DEVELOPERS_GUIDE.md) and [Implementation Plan](implementation_plan.md).**

This is not optional - it contains essential information that prevents code duplication and ensures consistency across the project.

## 📋 Pre-Development Checklist

Before writing any new code, you MUST:

1. ✅ **Read the complete [Developers Guide](DEVELOPERS_GUIDE.md)**
2. ✅ **Review the [Implementation Plan](implementation_plan.md)** for current project status
3. ✅ **Check for existing utility modules** with `utility_` prefix
4. ✅ **Review shared modules** in `/shared/` directory
5. ✅ **Search other services** for similar functionality
6. ✅ **Use custom error classes** instead of `HTTPException`

## 🔧 Utility Modules System

**ALWAYS check for existing utility modules before implementing new functionality:**

### Available Utility Modules (Notification Service)
- `utility_email_sender.py` - Email notification functionality
- `utility_webhook_sender.py` - Slack, Teams, and generic webhooks
- `utility_template_renderer.py` - Jinja2 template rendering
- `utility_user_preferences.py` - User preference management
- `utility_notification_processor.py` - Core notification processing

### Usage Pattern
```python
# Import utility modules
import utility_email_sender as email_utility
import utility_webhook_sender as webhook_utility

# Initialize utilities
email_utility.set_smtp_config(SMTP_CONFIG)
utility.set_db_cursor_func(get_db_cursor)

# Use in endpoints
success = await email_utility.send_email_notification(id, dest, payload)
```

## 🚫 What NOT to Do

- ❌ **DO NOT** use `HTTPException` directly - use custom error classes
- ❌ **DO NOT** duplicate functionality that exists in utility modules
- ❌ **DO NOT** create new modules without checking existing ones first
- ❌ **DO NOT** skip reading the Developer Guide

## ✅ What TO Do

- ✅ **USE** existing utility modules with `utility_` prefix
- ✅ **USE** custom error classes from `shared.errors`
- ✅ **FOLLOW** established patterns from notification service
- ✅ **DOCUMENT** new utility modules in the Developer Guide
- ✅ **TEST** thoroughly with both unit and integration tests

## 📚 Required Documentation

### Primary Documents
1. **[Developers Guide](DEVELOPERS_GUIDE.md)** - Complete development documentation
2. **[Implementation Plan](implementation_plan.md)** - Current project status and roadmap
3. **[README.md](README.md)** - Project overview and quick start
4. **Service-specific READMEs** - Individual service documentation

### Error Handling Standards
```python
from shared.errors import (
    DatabaseError,        # Database operation failures (500)
    ValidationError,      # Input validation failures (400)
    NotFoundError,        # Resource not found (404)
    AuthError,           # Authentication failures (401)
    PermissionError,     # Authorization failures (403)
    ServiceCommunicationError  # Inter-service communication (503)
)
```

## 🔄 Development Workflow

1. **Plan** - Check Developers Guide and Implementation Plan for existing solutions
2. **Design** - Follow established patterns and naming conventions
3. **Implement** - Use utility modules and proper error handling
4. **Test** - Comprehensive unit and integration tests
5. **Document** - Update Developers Guide if adding new utilities
6. **Review** - Ensure compliance with this checklist

## 🎯 Key Principles

- **Reusability** - Use and create reusable utility modules
- **Consistency** - Follow established patterns and conventions
- **Documentation** - Document everything for future developers
- **Testing** - Test thoroughly to ensure reliability
- **Team Sharing** - Commit utility modules for team use

## 📞 Support

If you have questions about:
- **Utility modules** - Check the Developers Guide examples
- **Error handling** - Use custom error classes as documented
- **Patterns** - Follow notification service as reference
- **Architecture** - Review the Developers Guide architecture section
- **Current status** - Check the Implementation Plan for latest updates

---

**Remember**: The Developers Guide and Implementation Plan are your primary resources. Reading them thoroughly will save time and ensure your code follows OpsConductor standards and aligns with the current project direction.