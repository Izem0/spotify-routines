import logging
import sys


def setup_logger(
    name: str = __name__,
    datefmt: str = "%Y-%m-%d %H:%M:%S%z",
    handlers: list = None,
    level="INFO",
) -> logging.Logger:
    if not handlers:
        handlers = [logging.StreamHandler(sys.stdout)]  # print to console

    logging.basicConfig(
        format="%(name)s | [%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s",
        datefmt=datefmt,
        handlers=handlers,
    )

    logger = logging.getLogger(name)
    logger.setLevel(level)
    return logger
