#!/usr/bin/env python3
"""
Cleanup stuck sessions from stress testing.

Usage:
    python3 tests/cleanup_sessions.py
"""

import requests

BASE_URL = "https://idem307-image-metadata-generator.onrender.com"

# Check current status
resp = requests.get(f"{BASE_URL}/api/health")
health = resp.json()

print(f"Current status:")
print(f"  Active sessions: {health['capacity']['active_sessions']}")
print(f"  Max sessions: {health['capacity']['max_sessions']}")
print(f"  Available: {health['capacity']['available']}")

# Note: The production app doesn't have a cleanup endpoint
# Sessions are only removed on export or after timeout
# You'll need to either:
# 1. Wait for timeout cleanup (if enabled)
# 2. Restart the Render service (clears in-memory active_sessions dict)
# 3. Add a manual cleanup endpoint

print("\nTo clear stuck sessions:")
print("  Option 1: Restart service in Render dashboard")
print("  Option 2: Wait for session timeout cleanup")
print("  Option 3: SSH to Render and delete /tmp/sessions/*.json")
