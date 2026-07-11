"""
OAMI Enterprise
Depth Engine
"""


class DepthEngine:

    def analyze(self, snapshot):

        # ---------------------------------------
        # No depth available
        # ---------------------------------------

        if not snapshot.depth:

            print(f"{snapshot.symbol:<12} Depth = NOT AVAILABLE")

            return snapshot

        print(f"{snapshot.symbol:<12} Depth = AVAILABLE")

        return snapshot