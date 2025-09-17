#!/usr/bin/env python3

# Read the file
with open('/home/opsconductor/opsconductor-ng/ai-command/query_handlers/automation_queries.py', 'r') as f:
    lines = f.readlines()

# Fix the specific problematic lines by line number
fixes = {
    866: '            response += f".\\WinRM-DirectoryList.ps1 -ComputerName \\"192.168.1.100\\"\\n\\n"\n',
    868: '            response += f".\\WinRM-DirectoryList.ps1 -ComputerName \\"server01\\" -Username \\"domain\\\\administrator\\"\\n\\n"\n',
    870: '            response += f".\\WinRM-DirectoryList.ps1 -ComputerName \\"server01\\" -Username \\"admin\\" -UseSSL\\n"\n',
    877: '            response += "winrm set winrm/config/service \'@{AllowUnencrypted=\\"true\\"}\'\\n"\n',
    878: '            response += "winrm set winrm/config/service/auth \'@{Basic=\\"true\\"}\'\\n"\n'
}

for line_num, replacement in fixes.items():
    if line_num <= len(lines):
        lines[line_num - 1] = replacement

# Write back
with open('/home/opsconductor/opsconductor-ng/ai-command/query_handlers/automation_queries.py', 'w') as f:
    f.writelines(lines)

print("Applied targeted fixes to specific lines")