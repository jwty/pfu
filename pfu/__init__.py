from flask import Flask
from flask_bootstrap import Bootstrap5
from pfu.logging import logger
from pfu.auth import login_manager
from pfu.config import config
from pfu.db import configure_db
from pfu.routes_admin import admin
from pfu.routes_api import api
from pfu.routes_auth import auth
from pfu.routes_main import main
from pfu.scheduler import scheduler
from pfu.utils import format_datetime


def create_app():
    app = Flask(__name__)
    app.config.from_object(config)
    logger.setLevel(config.LOG_LEVEL)
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
    app.register_blueprint(admin)
    configure_db(app)
    scheduler.init_app(app)
    scheduler.start()
    import pfu.tasks  # Importing here to register tasks via decorators
    return app
