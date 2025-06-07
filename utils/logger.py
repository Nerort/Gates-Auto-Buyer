from loguru import logger
import logging
import sys


class InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except KeyError:
            level = record.levelno

        logger.log(level, record.getMessage())


def setup_logger():
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
               "<level>{message}</level>",
        level="INFO",
        enqueue=True,
    )
    logger.add(
        "logs/bot_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="1 week",
        compression="zip",
        enqueue=True,
    )

    logging.basicConfig(handlers=[InterceptHandler()], level=logging.INFO)
    for logger_name in ("aiogram", "aiogram.dispatcher", "asyncio"):
        logging.getLogger(logger_name).setLevel(logging.INFO)

    return logger


log = setup_logger()
