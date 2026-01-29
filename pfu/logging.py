import colorlog
import logging


logging.addLevelName(100, 'SPECIAL')


formatter = colorlog.ColoredFormatter(
    '%(log_color)s[%(asctime)s] [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S %Z',
    log_colors = {'DEBUG': 'blue', 'INFO': 'white', 'WARNING': 'yellow', 'ERROR': 'red', 'CRITICAL': 'red', 'SPECIAL': 'green'}
)


logger = colorlog.getLogger()
logger.addHandler(logging.StreamHandler())
logger.handlers[0].setFormatter(formatter)
logger.log(100, "Logging initialised, starting pfu server")
