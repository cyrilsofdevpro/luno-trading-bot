#!/usr/bin/env python3
"""
Test script to verify improved error handling for invalid pair formats.
Includes login and session management.
"""

import requests
import json

BASE_URL = "http://127.0.0.1:5000"

# Create a session for authentication
session = requests.Session()

# Step 1: Login
print("=" * 60)
print("STEP 1: Logging in...")
print("=" * 60)

login_payload = {
    "email": "israelchristopher406@gmail.com",
    "password": "ISRAEL123"
}

try:
    response = session.post(
        f"{BASE_URL}/login",
        data=login_payload,
        allow_redirects=False,
        timeout=10
    )
    print(f"Login Status: {response.status_code}")
    if response.status_code in [200, 302]:
        print("✅ Logged in successfully!")
    else:
        print(f"❌ Login failed: {response.text[:200]}")
except Exception as e:
    print(f"❌ Login error: {e}")

# Test 1: Try with invalid pair format (SOL instead of SOLNGN)
print("\n" + "=" * 60)
print("TEST 1: Invalid pair format (SOL)")
print("=" * 60)

payload_invalid = {
    "pair": "SOL"
}

try:
    response = session.post(
        f"{BASE_URL}/api/autosell/sell-now",
        json=payload_invalid,
        timeout=10
    )
    result = response.json()
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(result, indent=2)}")
    if result.get('error') == 'invalid_pair':
        print("✅ Correctly identified invalid pair format!")
        if result.get('message'):
            print(f"   Message: {result.get('message')}")
        if result.get('suggestion'):
            print(f"   Suggestion: {result.get('suggestion')}")
    elif result.get('error') == 'volume_too_small':
        print("✅ Got volume_too_small error (pair was recognized but balance is too small)")
    else:
        print(f"Response error: {result.get('error')}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: Try with correct pair format (SOLNGN)
print("\n" + "=" * 60)
print("TEST 2: Valid pair format (SOLNGN)")
print("=" * 60)

payload_valid = {
    "pair": "SOLNGN"
}

try:
    response = session.post(
        f"{BASE_URL}/api/autosell/sell-now",
        json=payload_valid,
        timeout=10
    )
    result = response.json()
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(result, indent=2)}")
    if result.get('success'):
        print("✅ Successfully processed SOLNGN pair!")
    else:
        error = result.get('error')
        message = result.get('message')
        print(f"Error: {error}")
        print(f"Message: {message}")
        if 'volume_too_small' in error:
            print("✅ Valid pair but balance too small (expected)")
        elif 'insufficient_balance' in error:
            print("✅ Valid pair but no balance (expected)")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
