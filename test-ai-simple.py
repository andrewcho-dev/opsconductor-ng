#!/usr/bin/env python3
import requests
import json

response = requests.post(
    "http://localhost:3005/ai/chat",
    json={
        "message": "Install the OpsConductor remote probe on 192.168.50.211",
        "user_id": 1,
        "conversation_id": "test"
    },
    timeout=30
)

if response.status_code == 200:
    result = response.json()
    print("AI Response:")
    print("=" * 50)
    print(result.get('response', 'No response'))
    print("=" * 50)
    print(f"Intent: {result.get('intent', 'unknown')}")
else:
    print(f"Error: {response.status_code}")
    print(response.text)