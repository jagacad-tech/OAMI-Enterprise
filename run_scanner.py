import time

from app.market.scanner import Scanner

scanner = Scanner()

while True:

    results = scanner.scan()

    print("\n================ RANKING ================\n")

    for i, snapshot in enumerate(results, start=1):

        print(
            f"{i:02d}. "
            f"{snapshot.symbol:<12}"
            f"Score={snapshot.score:<4}"
            f"Trend={snapshot.trend}"
        )

    time.sleep(5)