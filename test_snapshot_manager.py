"""
Test Snapshot Manager
"""

from app.market.models import MarketSnapshot
from app.services.snapshot_manager import SnapshotManager


def main():

    manager = SnapshotManager()

    # Create snapshot
    snapshot = MarketSnapshot(
        symbol="RELIANCE",
        ltp=2965.25,
        volume=125000
    )

    # Store snapshot
    manager.update(snapshot)

    # Retrieve snapshot
    latest = manager.get("RELIANCE")

    print("=" * 60)
    print("SNAPSHOT MANAGER TEST")
    print("=" * 60)

    print(latest)

    print("\nExists:", manager.exists("RELIANCE"))

    print("Total Snapshots:", len(manager.all()))

    manager.clear()

    print("After Clear:", len(manager.all()))


if __name__ == "__main__":
    main()