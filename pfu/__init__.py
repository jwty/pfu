from flask import Flask
from flask_bootstrap import Bootstrap5
from pfu.db import configure_db
from pfu.config import config_class
from pfu.routes import bp


def create_app(config_class=config_class):
    app = Flask(__name__)
    app.config.from_object(config_class)
    bootstrap = Bootstrap5()
    bootstrap.init_app(app)
    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True
    app.register_blueprint(bp)
    configure_db(app)
    return app
