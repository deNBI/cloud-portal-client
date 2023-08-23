import logging
from logging.handlers import RotatingFileHandler

DEFAULT_MAX_BYTES = 1073741824  # 1 GB in bytes


def setup_logger(config):
    # Load configuration from YAML file
    logger_config = config.get("logger", None)
    if not logger_config:
        log_file_path = "log/portal_client_debug.log"
        max_bytes = DEFAULT_MAX_BYTES
        backup_count = 3
    else:
        log_file_path = logger_config.get(
            "log_file", "log/portal_client_debug.log"
        )  ## default for not breaking things
        max_bytes = logger_config.get("max_bytes", DEFAULT_MAX_BYTES)
        backup_count = logger_config.get("backup_count", 3)
    # Create a logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # Create a RotatingFileHandler for log rotation
    fh = RotatingFileHandler(
        log_file_path, maxBytes=max_bytes, backupCount=backup_count
    )
    fh.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(funcName)s  - %(levelname)s - %(message)s"
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger
