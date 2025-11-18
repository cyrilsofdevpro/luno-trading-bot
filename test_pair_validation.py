#!/usr/bin/env python3
"""Test the error handling for invalid pair formats."""

import requests
import json

BASE_URL = 'http://127.0.0.1:5000'

# Create session
session = requests.Session()

# Log in
login_data = {'email': 'israelchristopher406@gmail.com', 'password': 'ISRAEL123'}
resp = session.post(f'{BASE_URL}/login', json=login_data)
print(f"Login: {resp.status_code}")

# Test 1: Invalid pair format (SOL instead of SOLNGN)
print("\n=== TEST 1: Invalid pair format (SOL) ===")
test_data = {'pair': 'SOL'}
resp = session.post(f'{BASE_URL}/api/autosell/sell-now', json=test_data)
print(f"Status: {resp.status_code}")
print(f"Response: {json.dumps(resp.json(), indent=2)}")

# Test 2: Correct pair format (SOLNGN)
print("\n=== TEST 2: Correct pair format (SOLNGN) ===")
test_data = {'pair': 'SOLNGN'}
resp = session.post(f'{BASE_URL}/api/autosell/sell-now', json=test_data)
print(f"Status: {resp.status_code}")
print(f"Response: {json.dumps(resp.json(), indent=2)}")

# Test 3: Another invalid format (XRPNG instead of XRPNGN)
print("\n=== TEST 3: Invalid format (XRPNG instead of XRPNGN) ===")
test_data = {'pair': 'XRPNG'}
resp = session.post(f'{BASE_URL}/api/autosell/sell-now', json=test_data)
print(f"Status: {resp.status_code}")
print(f"Response: {json.dumps(resp.json(), indent=2)}")
