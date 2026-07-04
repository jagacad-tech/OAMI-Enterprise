import time

from app.openalgo.client import OpenAlgoClient

client = OpenAlgoClient()

start = time.perf_counter()

response = client.get_quotes(
    exchange="NSE",
    symbol="RELIANCE"
)

elapsed = (time.perf_counter() - start) * 1000

print(response)
print(f"\nLatency : {elapsed:.2f} ms")