from flask import Flask
from flask_bootstrap import Bootstrap5
from pfu.db import configure_db
from pfu.utils import format_datetime, truncate_filename
from pfu.config import config_class
from pfu.routes import main
from pfu.routes_auth import auth
from pfu.auth import login_manager


def create_app(config_class=config_class):
    app = Flask(__name__)
    app.config.from_object(config_class)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    app.jinja_env.filters['datetime'] = format_datetime
    app.jinja_env.filters['filename_truncate'] = truncate_filename
    bootstrap = Bootstrap5()
    bootstrap.init_app(app)
    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True
    app.register_blueprint(main)
    app.register_blueprint(auth)
    configure_db(app)
    return app
