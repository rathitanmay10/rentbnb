import logging
import sys

from app.config.settings import settings


def setup_logging():
    """
    Configure logging for the application.
    """
    logging_level = logging.INFO
    if settings.DEBUG:
        logging_level = logging.DEBUG

    logging.basicConfig(
        level=logging_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
