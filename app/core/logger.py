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

    # Configure the root logger
    handlers = [logging.StreamHandler(sys.stdout)]

    # Add FileHandler
    log_file = "logs/app.log"
    try:
        if not os.path.exists("logs"):
            os.makedirs("logs")
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        handlers.append(file_handler)
    except Exception as e:
        # If we can't write to file, just print to stderr
        print(f"Failed to setup file logging: {e}", file=sys.stderr)

    logging.basicConfig(
        level=logging_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
    )

    # Set the logging level for 'app' logger specifically if needed,
    # or for third-party libraries like uvicorn.
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
