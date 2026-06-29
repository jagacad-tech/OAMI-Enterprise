from app.core.config import config
from app.core.logger import logger

from app.database.base import Base
from app.database.session import engine


def main():

    Base.metadata.create_all(bind=engine)

    logger.info("Database Initialized")

    logger.info("Starting OAMI Enterprise")

    print("=" * 60)

    print(config.settings.app.name)

    print(config.settings.app.version)

    print("=" * 60)


if __name__ == "__main__":
    main()