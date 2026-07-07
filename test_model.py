from app.market.models import MarketSnapshot

snapshot = MarketSnapshot(symbol="TEST")

print(snapshot)

print()

print("Strike :", snapshot.strike)
print("Expiry :", snapshot.expiry)
print("Action :", snapshot.action)
print("Signal :", snapshot.signal)