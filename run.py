"""
OAMI Enterprise Startup
"""

import uvicorn

from app.core.logger import logger


def main():

    logger.info("Starting OAMI Enterprise Server")

    uvicorn.run(
        "app.presentation.app:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()