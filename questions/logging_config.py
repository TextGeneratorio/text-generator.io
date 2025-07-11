import logging
import os
import sys

from colorama import Fore, Style, init as colorama_init

colorama_init()

LEVEL_COLORS = {
    logging.DEBUG: Fore.CYAN,
    logging.INFO: Fore.GREEN,
    logging.WARNING: Fore.YELLOW,
    logging.ERROR: Fore.RED,
    logging.CRITICAL: Fore.MAGENTA,
}

class ColorFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        level_color = LEVEL_COLORS.get(record.levelno, '')
        record.levelname = f"{level_color}{record.levelname}{Style.RESET_ALL}"
        return super().format(record)

def setup_logging(level: int = logging.INFO, use_cloud: bool = False) -> None:
    """Configure root logger.

    Environment variables:
        LOG_LEVEL: Override log level (e.g. "DEBUG").
        COLOR_LOGS: Set to "0" to disable color output.
        LOG_FILE: If set, also log to this file.
        GOOGLE_CLOUD_LOGGING: Enable Google Cloud Logging when set.

    """
    env_level = os.environ.get("LOG_LEVEL")
    if env_level:
        level = logging.getLevelName(env_level.upper())  # type: ignore[arg-type]
    if os.environ.get("GOOGLE_CLOUD_LOGGING"):
        use_cloud = True


    root_logger = logging.getLogger()
    if root_logger.handlers:
        return
    root_logger.setLevel(level)
    use_color = os.environ.get("COLOR_LOGS", "1") != "0"
    fmt = '%(asctime)s [%(levelname)s] %(name)s:%(funcName)s:%(lineno)d - %(message)s'
    formatter_cls = ColorFormatter if use_color else logging.Formatter
    formatter = formatter_cls(fmt, '%Y-%m-%d %H:%M:%S')

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    log_file = os.environ.get("LOG_FILE")
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # if use_cloud:
    #     try:
    #         import google.cloud.logging  # type: ignore
    #         client = google.cloud.logging.Client()
    #         cloud_handler = client.get_default_handler()
    #         cloud_handler.setFormatter(formatter)
    #         root_logger.addHandler(cloud_handler)
    #         client.setup_logging(log_level=level)
    #     except Exception as e:  # pragma: no cover - environment may lack gcloud
    #         root_logger.error("Failed to initialize Google Cloud Logging: %s", e)


def get_logger(name: str) -> logging.Logger:
    """Get a logger, initializing logging if needed."""
    if not logging.getLogger().handlers:
        setup_logging()
    return logging.getLogger(name)

