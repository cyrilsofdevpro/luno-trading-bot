"""
TradingView Webhook Test Script
================================
Test the webhook endpoint with various scenarios.

Usage:
    python test_tradingview_webhook.py

This script will:
1. Check if webhook is running
2. Test BUY signal
3. Test SELL signal
4. Test invalid signals
5. Test missing fields
6. Display results
"""

import requests
import json
import sys
from datetime import datetime

# Change this to your webhook URL
WEBHOOK_URL = "http://localhost:5000/tv-webhook"
STATUS_URL = "http://localhost:5000/tv-webhook/status"

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_header(text):
    """Print colored section header."""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{text:^60}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")


def print_success(text):
    """Print success message."""
    print(f"{GREEN}✅ {text}{RESET}")


def print_error(text):
    """Print error message."""
    print(f"{RED}❌ {text}{RESET}")


def print_info(text):
    """Print info message."""
    print(f"{BLUE}ℹ️  {text}{RESET}")


def print_request(method, url, data=None):
    """Print request details."""
    print(f"{YELLOW}→ {method} {url}{RESET}")
    if data:
        print(f"  Payload: {json.dumps(data, indent=2)}")


def print_response(resp):
    """Print response details."""
    try:
        data = resp.json()
        print(f"  Status: {resp.status_code}")
        print(f"  Response: {json.dumps(data, indent=2)}")
        return data
    except:
        print(f"  Status: {resp.status_code}")
        print(f"  Response: {resp.text}")
        return None


def test_webhook_status():
    """Test if webhook is running."""
    print_header("Test 1: Webhook Health Check")
    try:
        print_request("GET", STATUS_URL)
        resp = requests.get(STATUS_URL, timeout=5)
        data = print_response(resp)
        
        if resp.status_code == 200 and data.get("status") == "healthy":
            print_success("Webhook is running and healthy!")
            
            # Print details
            print(f"\n  Credentials: {GREEN if data.get('credentials_configured') else RED}{data.get('credentials_configured')}{RESET}")
            print(f"  Luno API: {data.get('luno_api_status')}")
            return True
        else:
            print_error(f"Webhook returned unexpected status: {data}")
            return False
            
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to webhook at {WEBHOOK_URL}")
        print_info("Make sure to run: python dashboard.py")
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_buy_signal():
    """Test BUY signal."""
    print_header("Test 2: BUY Signal")
    
    payload = {
        "signal": "buy",
        "pair": "XBTNGN",
        "volume": 0.001
    }
    
    try:
        print_request("POST", WEBHOOK_URL, payload)
        resp = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        data = print_response(resp)
        
        if resp.status_code == 200 and data and data.get("status") == "ok":
            print_success("BUY signal processed successfully!")
            if data.get("order_id"):
                print_info(f"Order ID: {data.get('order_id')}")
            return True
        else:
            print_error(f"BUY signal failed: {data.get('message') if data else resp.text}")
            return False
            
    except Exception as e:
        print_error(f"Error sending BUY signal: {e}")
        return False


def test_sell_signal():
    """Test SELL signal."""
    print_header("Test 3: SELL Signal")
    
    payload = {
        "signal": "sell",
        "pair": "XBTNGN",
        "volume": 0.001
    }
    
    try:
        print_request("POST", WEBHOOK_URL, payload)
        resp = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        data = print_response(resp)
        
        if resp.status_code == 200 and data and data.get("status") == "ok":
            print_success("SELL signal processed successfully!")
            if data.get("order_id"):
                print_info(f"Order ID: {data.get('order_id')}")
            return True
        else:
            print_error(f"SELL signal failed: {data.get('message') if data else resp.text}")
            return False
            
    except Exception as e:
        print_error(f"Error sending SELL signal: {e}")
        return False


def test_invalid_signal():
    """Test invalid signal (should fail gracefully)."""
    print_header("Test 4: Invalid Signal (Expected to Fail)")
    
    payload = {
        "signal": "hold",  # Invalid - should be buy/sell
        "pair": "XBTNGN"
    }
    
    try:
        print_request("POST", WEBHOOK_URL, payload)
        resp = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        data = print_response(resp)
        
        if resp.status_code != 200 and data and data.get("status") == "error":
            print_success("Invalid signal correctly rejected!")
            return True
        else:
            print_error("Invalid signal should have been rejected")
            return False
            
    except Exception as e:
        print_error(f"Error testing invalid signal: {e}")
        return False


def test_missing_pair():
    """Test missing pair field (should fail gracefully)."""
    print_header("Test 5: Missing Pair Field (Expected to Fail)")
    
    payload = {
        "signal": "buy"
        # Missing 'pair' field
    }
    
    try:
        print_request("POST", WEBHOOK_URL, payload)
        resp = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        data = print_response(resp)
        
        if resp.status_code != 200 and data and data.get("status") == "error":
            print_success("Missing pair correctly rejected!")
            return True
        else:
            print_error("Missing pair should have been rejected")
            return False
            
    except Exception as e:
        print_error(f"Error testing missing pair: {e}")
        return False


def test_invalid_volume():
    """Test invalid volume (should fail gracefully)."""
    print_header("Test 6: Invalid Volume (Expected to Fail)")
    
    payload = {
        "signal": "buy",
        "pair": "XBTNGN",
        "volume": -0.001  # Negative volume - invalid
    }
    
    try:
        print_request("POST", WEBHOOK_URL, payload)
        resp = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        data = print_response(resp)
        
        if resp.status_code != 200 and data and data.get("status") == "error":
            print_success("Invalid volume correctly rejected!")
            return True
        else:
            print_error("Invalid volume should have been rejected")
            return False
            
    except Exception as e:
        print_error(f"Error testing invalid volume: {e}")
        return False


def test_different_pair():
    """Test with different trading pair (ETHNGN)."""
    print_header("Test 7: Different Pair (ETHNGN)")
    
    payload = {
        "signal": "buy",
        "pair": "ETHNGN",
        "volume": 0.01
    }
    
    try:
        print_request("POST", WEBHOOK_URL, payload)
        resp = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        data = print_response(resp)
        
        if resp.status_code == 200 and data and data.get("status") == "ok":
            print_success("Different pair works correctly!")
            if data.get("order_id"):
                print_info(f"Order ID: {data.get('order_id')}")
            return True
        else:
            print_error(f"Different pair test failed: {data.get('message') if data else resp.text}")
            return False
            
    except Exception as e:
        print_error(f"Error testing different pair: {e}")
        return False


def main():
    """Run all tests."""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{'TradingView Webhook Test Suite':^60}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    print(f"Webhook URL: {WEBHOOK_URL}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results = []
    
    # Run tests
    results.append(("Webhook Health Check", test_webhook_status()))
    
    if results[0][1]:  # Only continue if webhook is healthy
        results.append(("BUY Signal", test_buy_signal()))
        results.append(("SELL Signal", test_sell_signal()))
        results.append(("Invalid Signal (Error Case)", test_invalid_signal()))
        results.append(("Missing Pair (Error Case)", test_missing_pair()))
        results.append(("Invalid Volume (Error Case)", test_invalid_volume()))
        results.append(("Different Pair (ETHNGN)", test_different_pair()))
    
    # Print summary
    print_header("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{GREEN}PASSED{RESET}" if result else f"{RED}FAILED{RESET}"
        print(f"  {test_name:<40} {status}")
    
    print(f"\n  {BLUE}{'='*40}{RESET}")
    print(f"  Total: {GREEN}{passed}/{total}{RESET} tests passed")
    print(f"  {'='*40}\n")
    
    if passed == total:
        print_success("All tests passed! Webhook is working correctly. ✨\n")
        return 0
    else:
        print_error(f"Some tests failed. Please check the output above.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
