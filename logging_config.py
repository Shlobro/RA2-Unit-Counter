import logging
import os
import sys
from logging.handlers import RotatingFileHandler


class LineCappedRotatingFileHandler(RotatingFileHandler):
    def __init__(self, filename, max_lines=10000, *args, **kwargs):
        self.max_lines = max_lines
        self._line_count = 0
        super().__init__(filename, *args, **kwargs)
        self._line_count = self._count_existing_lines()

    def emit(self, record):
        super().emit(record)
        self._line_count += 1
        if self._line_count > self.max_lines:
            self._trim_to_latest_lines()

    def doRollover(self):
        super().doRollover()
        self._line_count = self._count_existing_lines()

    def _count_existing_lines(self):
        if not os.path.exists(self.baseFilename):
            return 0
        with open(self.baseFilename, "r", encoding=self.encoding or "utf-8", errors="replace") as log_file:
            return sum(1 for _ in log_file)

    def _trim_to_latest_lines(self):
        if self.stream:
            self.stream.flush()

        with open(self.baseFilename, "r", encoding=self.encoding or "utf-8", errors="replace") as log_file:
            lines = log_file.readlines()

        if len(lines) <= self.max_lines:
            self._line_count = len(lines)
            return

        with open(self.baseFilename, "w", encoding=self.encoding or "utf-8", errors="replace") as log_file:
            log_file.writelines(lines[-self.max_lines:])

        self._line_count = self.max_lines

        if self.stream:
            self.stream.close()
            self.stream = self._open()


def setup_logging(log_to_console=False, log_file="app.log", max_size=5_000_000, backup_count=5, max_lines=10000):
    """
    Sets up logging for the application. Logs to console or a rotating file.

    :param log_to_console: If True, logs to console. Otherwise, logs to a file.
    :param log_file: The file to log to (only used when log_to_console=False).
    :param max_size: Maximum file size in bytes before rotation.
    :param backup_count: Number of backup log files to keep.
    :param max_lines: Maximum number of lines to keep in the active log file.
    """
    log_format = '%(asctime)s - %(levelname)s - %(message)s'

    handlers = []

    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(log_format))
        handlers.append(console_handler)
    else:
        # Keep the active log bounded both by size and by latest-line count.
        file_handler = LineCappedRotatingFileHandler(
            log_file,
            max_lines=max_lines,
            maxBytes=max_size,
            backupCount=backup_count,
            encoding="utf-8"
        )
        file_handler.setFormatter(logging.Formatter(log_format))
        handlers.append(file_handler)

    logging.basicConfig(
        level=logging.INFO,  # Adjust the level as needed
        handlers=handlers,
        format=log_format
    )

    logging.info("Logging setup complete")



setup_logging()
