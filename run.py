import pfu
import logging
from waitress import serve

# TODO: Logs formatting, figure out access logs, add logging support in general lol
# TODO: Let user select log level
waitress_logger = logging.getLogger('waitress')
waitress_logger.setLevel(logging.INFO)

# pfu_logger = logging.getLogger('pfu')
# pfu_logger.setLevel(logging.INFO)

pfu_app = pfu.app

serve(pfu_app)
