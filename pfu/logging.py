import colorlog
import logging
import warnings
from pfu.__version__ import __version__

# A bit of fluff for the startup message
logging.addLevelName(100, 'WELCOME')

formatter = colorlog.ColoredFormatter(
    '%(log_color)s[%(asctime)s] [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S %Z',
    log_colors={'DEBUG': 'blue', 'INFO': 'white', 'WARNING': 'yellow', 'ERROR': 'red', 'CRITICAL': 'red', 'WELCOME': 'green'}
)

logger = colorlog.getLogger()
logger.addHandler(logging.StreamHandler())
logger.handlers[0].setFormatter(formatter)

# Suppress annoyingly verbose timezone warning when running in docker and no timezone is configured
warnings.filterwarnings('ignore', message='.*timezone configuration.*', module='tzlocal')

# Catch Python warnings and send them to the logging system
logging.captureWarnings(True)
warnings_logger = logging.getLogger('py.warnings')
warnings_logger.addHandler(logger.handlers[0])

logger.log(100, f"Logging initialised, starting pfu server v{__version__}")
