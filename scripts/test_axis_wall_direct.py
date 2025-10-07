#!/usr/bin/env python3
"""
Direct test of Axis camera PTZ wall preset command
"""

import requests
from requests.auth import HTTPDigestAuth

# Camera configuration
camera_ip = "192.168.10.90"
username = "root"
password = "Enabled123!"

# Get current position before moving
print("=" * 80)
print("Getting current PTZ position...")
print("=" * 80)

url_position = f"http://{camera_ip}/axis-cgi/com/ptz.cgi?query=position"
response = requests.get(url_position, auth=HTTPDigestAuth(username, password))

print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")

# Move to wall preset
print("\n" + "=" * 80)
print("Moving to 'wall' preset...")
print("=" * 80)

url_wall = f"http://{camera_ip}/axis-cgi/com/ptz.cgi?gotoserverpresetname=wall"
response = requests.get(url_wall, auth=HTTPDigestAuth(username, password))

print(f"Status Code: {response.status_code}")
print(f"Response: {response.text if response.text else '(empty - success)'}")

# Wait a moment for camera to move
import time
print("\nWaiting 3 seconds for camera to move...")
time.sleep(3)

# Get position after moving
print("\n" + "=" * 80)
print("Getting PTZ position after move...")
print("=" * 80)

response = requests.get(url_position, auth=HTTPDigestAuth(username, password))

print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")

print("\n" + "=" * 80)
print("✅ Test complete!")
print("=" * 80)