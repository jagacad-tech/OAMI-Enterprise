import inspect
from openalgo import api

print("=" * 60)
print("OPENALGO SDK SIGNATURES")
print("=" * 60)

print("connect")
print(inspect.signature(api.connect))

print()

print("subscribe_quote")
print(inspect.signature(api.subscribe_quote))

print()

print("subscribe_ltp")
print(inspect.signature(api.subscribe_ltp))

print()

print("subscribe_depth")
print(inspect.signature(api.subscribe_depth))