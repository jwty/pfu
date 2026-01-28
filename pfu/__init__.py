import logging
import colorlog
from flask import Flask
from flask_bootstrap import Bootstrap5
from pfu.auth import login_manager
from pfu.config import config_class
from pfu.db import configure_db
from pfu.routes_api import api
from pfu.routes_auth import auth
from pfu.routes_main import main
from pfu.tasks import scheduler
from pfu.utils import format_datetime


formatter = colorlog.ColoredFormatter(
    '%(log_color)s[%(asctime)s] [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S %Z',
    log_colors = {'DEBUG': 'blue', 'INFO': 'white', 'WARNING': 'yellow', 'ERROR': 'red', 'CRITICAL': 'red'}
)


logger = colorlog.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())
logger.handlers[0].setFormatter(formatter)


def create_app(config_class=config_class):
    logger.info("Starting pfu server")
    app = Flask(__name__)
    app.config.from_object(config_class)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    app.jinja_env.filters['datetime'] = format_datetime
    bootstrap = Bootstrap5()
    bootstrap.init_app(app)
    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True
    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(api)
    configure_db(app)
    scheduler.init_app(app)
    scheduler.start()
    return app
