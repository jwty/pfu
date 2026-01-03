from flask import Flask
from flask_bootstrap import Bootstrap5
from pfu.db import initialize_db
from pfu.config import Config
from pfu.routes import bp

bootstrap = Bootstrap5()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    bootstrap.init_app(app)
    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True
    app.register_blueprint(bp)
    database = initialize_db(app)

    @app.before_request
    def before_request():
        database.connect()

    @app.after_request
    def after_request(response):
        database.close()
        return response

    return app
