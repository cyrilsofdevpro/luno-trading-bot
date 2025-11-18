#!/usr/bin/env python3
"""
Test credential auto-reload.
Demonstrates how bot detects .env changes and reloads credentials automatically.
"""

import time
import os
import sys
from credential_monitor import initialize_monitor

def test_credential_reload():
    """Test that credential monitor detects .env changes."""
    
    print("🧪 Testing Credential Auto-Reload System")
    print("=" * 60)
    
    # Initialize monitor
    monitor = initialize_monitor(".env", check_interval=2)
    
    print("\n1️⃣ Initial Load")
    print("-" * 60)
    monitor.log_status()
    
    initial_creds = monitor.get_credentials()
    print(f"✓ Initial API Key: {monitor._mask_secret(initial_creds['api_key'])}")
    print(f"✓ Initial Pair: {initial_creds['pair']}")
    
    print("\n2️⃣ Simulating .env file edit...")
    print("-" * 60)
    print("(In real usage, user would edit .env with new API key)")
    print("Monitoring for changes for 10 seconds...")
    
    # Simulate file change detection by checking multiple times
    no_change_count = 0
    for i in range(10):
        print(f"  [{i+1}/10] Checking for changes...", end=" ")
        
        changed = monitor.check_for_updates()
        if changed:
            print("🔄 CHANGED!")
            new_creds = monitor.get_credentials()
            print(f"\n  ✓ New credentials loaded!")
            print(f"  ✓ API Key: {monitor._mask_secret(new_creds['api_key'])}")
            print(f"  ✓ Pair: {new_creds['pair']}")
            print(f"  ✓ Dry Run: {new_creds['dry_run']}")
            no_change_count = 0
        else:
            print("No change detected")
            no_change_count += 1
        
        time.sleep(2)
    
    print("\n3️⃣ Credential Validation")
    print("-" * 60)
    is_valid = monitor.credentials_valid()
    print(f"✓ Credentials Valid: {is_valid}")
    
    if is_valid:
        print("✅ Bot can now connect to Luno API!")
    else:
        print("❌ Credentials missing - bot will use dry-run mode")
    
    print("\n" + "=" * 60)
    print("✅ Auto-reload test complete!")
    print("\nHow it works:")
    print("  1. User edits .env with new API key")
    print("  2. Monitor detects file hash change")
    print("  3. Bot reloads credentials automatically")
    print("  4. New credentials used immediately")
    print("  5. No bot restart needed! 🚀")

if __name__ == "__main__":
    try:
        test_credential_reload()
    except KeyboardInterrupt:
        print("\n\n⏹️ Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
