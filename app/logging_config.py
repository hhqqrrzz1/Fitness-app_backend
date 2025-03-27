from loguru import logger

def configure_logger():
    logger.remove()
    logger.add('logs/app.log', rotation='1 week', retention='1 month', level='INFO')
    return logger

logger = configure_logger()
