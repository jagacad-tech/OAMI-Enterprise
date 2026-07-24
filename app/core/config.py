"""
OAMI Enterprise
Configuration Manager
"""

import os
import yaml

from dotenv import load_dotenv


# Load .env
load_dotenv()


class Settings:

    def __init__(self):

        # Load YAML
        with open("config/settings.yaml", "r") as f:
            config = yaml.safe_load(f)

        # Application
        self.app = config.get("app", {})

        # OpenAlgo
        self.openalgo = {
            "host": os.getenv("OPENALGO_HOST"),
            "api_key": os.getenv("OPENALGO_API_KEY"),
            **config.get("openalgo", {})
        }

        # Market
        self.market = config.get("market", {})

        # Dashboard
        self.dashboard = config.get("dashboard", {})

        # Logging
        self.logging = config.get("logging", {})

        # Passive lifecycle observability outputs
        self.observability = config.get("observability", {})


settings = Settings()
