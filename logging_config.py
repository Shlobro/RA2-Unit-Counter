import logging
import sys
from logging.handlers import RotatingFileHandler


def setup_logging(log_to_console=False, log_file="app.log", max_size=5_000_000, backup_count=5):
    """
    Sets up logging for the application. Logs to console or a rotating file.

    :param log_to_console: If True, logs to console. Otherwise, logs to a file.
    :param log_file: The file to log to (only used when log_to_console=False).
    :param max_size: Maximum file size in bytes before rotation.
    :param backup_count: Number of backup log files to keep.
    """
    log_format = '%(asctime)s - %(levelname)s - %(message)s'

    handlers = []

    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(log_format))
        handlers.append(console_handler)
    else:
        # Rotating log handler: keeps logs within size limits
        file_handler = RotatingFileHandler(log_file, maxBytes=max_size, backupCount=backup_count)
        file_handler.setFormatter(logging.Formatter(log_format))
        handlers.append(file_handler)

    logging.basicConfig(
        level=logging.INFO,  # Adjust the level as needed
        handlers=handlers,
        format=log_format
    )

    logging.info("Logging setup complete")



setup_logging()