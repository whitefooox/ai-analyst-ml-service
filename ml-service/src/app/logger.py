import logging


def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    stream_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)

    return logger


logger = setup_logger()
