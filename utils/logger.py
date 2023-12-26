import typing
import logging

from loguru import logger
from pathlib import Path
from datetime import datetime

import utils.settings as setting
import sys
import io

BASE_LOG_DIR = Path(f"{setting.CWD}/log")


def ensure_log_dir(log_dir: Path):
    log_dir.mkdir(parents=True, exist_ok=True)


def setup_logger():
    # Ensure the logger directory exists
    year = datetime.now().strftime("%Y")
    month = datetime.now().strftime("%m")
    log_dir = BASE_LOG_DIR / year / month
    ensure_log_dir(log_dir)

    # Define log file path
    log_file_path = log_dir / "project_1024_{time}.log"

    # Configure logger
    logger.level("NORMAL", no=25, color="<white>")
    logger.add(
        str(log_file_path),
        rotation="500 MB",
        retention="7 days",
        compression="zip",
        format="{time:YYYY-MM-DD at HH:mm:ss} {level} | {message}",
    )


setup_logger()


class StreamToLogger(io.TextIOBase):

    def __init__(self, original_stream: io.TextIOBase | typing.Any, level="INFO"):
        self.original_stream = original_stream
        self.level = level

    def write(self, buffer):
        self.original_stream.write(buffer)

        for line in buffer.rstrip().splitlines():
            logger.log(self.level, line)

    def flush(self):
        self.original_stream.flush()


class InterceptHandler(logging.Handler):
    def emit(self, record):

        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


# Configure logging
logging.basicConfig(handlers=[InterceptHandler()], level=0)

logging.getLogger("uvicorn").handlers = [InterceptHandler()]
logging.getLogger("uvicorn.access").handlers = [InterceptHandler()]
logging.getLogger("uvicorn.error").handlers = [InterceptHandler()]
logging.getLogger("fastapi").handlers = [InterceptHandler()]

sys.stdout = StreamToLogger(sys.stdout, "INFO")
sys.stderr = StreamToLogger(sys.stderr, "ERROR")
