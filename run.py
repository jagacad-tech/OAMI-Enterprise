"""
OAMI Enterprise Startup
"""

from app.core.config import config
from app.core.logger import logger


def main():

    logger.info("Starting OAMI Enterprise")

    logger.info(
        "Trading Mode : %s",
        config.settings.trading.mode,
    )

    logger.info(
        "Capital : %s",
        config.settings.trading.capital,
    )

    logger.info("Scanner Enabled : %s",
                config.settings.scanner.enabled)

    print("=" * 60)
    print(config.settings.app.name)
    print(config.settings.app.version)
    print("=" * 60)


if __name__ == "__main__":
    main()