#!/bin/bash
# Test script for tool_generator.py with automated inputs

# Simulate user inputs for creating a simple tool
cat <<EOF | docker exec -i opsconductor-ai-pipeline python3 /app/scripts/tool_generator.py
test_tool
1.0
A test tool for demonstration
linux
system
high
cached
direct
y
test_binary
binary
y
n
y
test_capability
Execute test operations
y
test_pattern
Basic test execution
Run test commands
1000
2
0.4
single
full
Test limitations
10
n
y
y
command
string
y
Command to execute
n
y
result
string
y
Command result
n
n
n
y
y
y
EOF