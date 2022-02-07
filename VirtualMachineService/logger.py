import logging


def setup_custom_logger(name):
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(funcName)s  - %(levelname)s - %(message)s"
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    # file_handler = logging.FileHandler("log/portal_client.log")
    # file_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    # logger.addHandler(file_handler)
    return logger
