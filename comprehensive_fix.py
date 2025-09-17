#!/usr/bin/env python3

# Read the file
with open('/home/opsconductor/opsconductor-ng/ai-command/query_handlers/automation_queries.py', 'r') as f:
    content = f.read()

# Fix all instances of quadruple backslashes to double backslashes
content = content.replace('\\\\\\\\', '\\\\')

# Fix f-strings with curly braces by converting them to regular strings
content = content.replace('f"winrm set winrm/config/service \'@{AllowUnencrypted=', '"winrm set winrm/config/service \'@{AllowUnencrypted=')
content = content.replace('f"winrm set winrm/config/service/auth \'@{Basic=', '"winrm set winrm/config/service/auth \'@{Basic=')

# Write back
with open('/home/opsconductor/opsconductor-ng/ai-command/query_handlers/automation_queries.py', 'w') as f:
    f.write(content)

print("Applied comprehensive fixes")