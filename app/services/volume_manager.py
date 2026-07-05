"""
OAMI Enterprise
Volume Manager
"""

import json
from pathlib import Path


class VolumeManager:

    def __init__(self):

        data_file = (
            Path(__file__).parent.parent
            / "data"
            / "average_volume.json"
        )

        with open(data_file, "r") as f:
            self.average_volume = json.load(f)

    def average(self, symbol):

        return self.average_volume.get(symbol, 1)


# Global Singleton

volume_manager = VolumeManager()