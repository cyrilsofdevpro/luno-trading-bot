import requests

# Get current SOL/NGN ticker
r = requests.get('https://api.luno.com/api/1/ticker?pair=SOLNGN')
ticker = r.json()

bid = float(ticker.get('bid', 0))
ask = float(ticker.get('ask', 0))

print(f"Current SOL/NGN Price:")
print(f"  Bid (selling): {bid:.2f} NGN per SOL")
print(f"  Ask (buying):  {ask:.2f} NGN per SOL")
print()
print(f"To buy 0.0072 SOL:")
cost = 0.0072 * ask
print(f"  Cost: {cost:.2f} NGN")
print()
print(f"You have: 56.61 NGN")
print(f"Status: {'✅ ENOUGH!' if cost < 56.61 else '❌ NOT ENOUGH'}")
