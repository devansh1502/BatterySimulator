import logging


def configure_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.ERROR)
    formatter = logging.Formatter(
        "%(asctime)s:%(levelname)s:%(filename)s:%(lineno)d: %(message)s",
        datefmt="%d-%m-%Y %H:%M:%S",
    )
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


logger = configure_logger()
