import requests
import json

# Login
session = requests.Session()
login_data = {'email': 'israelchristopher406@gmail.com', 'password': 'ISRAEL123'}
r = session.post('http://127.0.0.1:5000/login', data=login_data)
print(f"✅ Logged in")

# Get account balances
r = session.get('http://127.0.0.1:5000/api/account/balances')
balances = r.json().get('balances', [])

print(f"\n📊 YOUR ACCOUNT BALANCES:")
print("=" * 60)
for bal in balances:
    asset = bal.get('asset', '')
    available = float(bal.get('balance', 0)) - float(bal.get('reserved', 0))
    if available > 0.00001:  # Only show if balance > dust
        print(f"  {asset:10} → {available:15.8f} available")

print("\n" + "=" * 60)

# Check SOL specifically
sol_balance = 0
for bal in balances:
    if bal.get('asset') == 'SOL':
        sol_balance = float(bal.get('balance', 0)) - float(bal.get('reserved', 0))
        break

print(f"\n🔍 SOL STATUS:")
print(f"  Current SOL: {sol_balance:.8f}")
print(f"  Minimum to trade: 0.01")

if sol_balance < 0.01:
    shortage = 0.01 - sol_balance
    print(f"  Status: ❌ TOO SMALL (need {shortage:.8f} more)")
    print(f"\n💡 OPTIONS:")
    print(f"  1. Buy {shortage:.8f} more SOL via dashboard")
    print(f"  2. Wait for more SOL to arrive")
    print(f"  3. Hold as dust, trade later")
else:
    print(f"  Status: ✅ CAN TRADE!")
    print(f"\n📝 TO SELL YOUR SOL:")
    print(f"  1. Open dashboard: http://localhost:5000")
    print(f"  2. Go to Manual Trade card")
    print(f"  3. Pair: SOLNGN")
    print(f"  4. Side: SELL")
    print(f"  5. Amount: {sol_balance:.8f}")
    print(f"  6. Click Trade button")
