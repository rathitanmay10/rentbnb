import logging
import os
import sys

from app.config.settings import settings


def setup_logging():
    """
    Configure logging for the application.
    """
    logging_level = logging.INFO
    if settings.DEBUG:
        logging_level = logging.DEBUG

    handlers = [logging.StreamHandler(sys.stdout)]

    log_file = "logs/app.log"

    if not os.path.exists("logs"):
        os.makedirs("logs")
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    handlers.append(file_handler)

    logging.basicConfig(
        level=logging_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
    )

    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
