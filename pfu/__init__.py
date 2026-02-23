import json
import os
from flask import Flask
from flask_bootstrap import Bootstrap5
from pfu.__version__ import __version__
from pfu.auth import login_manager
from pfu.config import config
from pfu.db import configure_db
from pfu.logging import logger
from pfu.routes_admin import admin
from pfu.routes_api import api
from pfu.routes_auth import auth
from pfu.routes_main import main
from pfu.scheduler import scheduler
from pfu.utils import format_datetime


def create_app() -> Flask:
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
    import pfu.tasks  # noqa: F401 (Importing here to register tasks via decorators)

    @app.context_processor
    def inject_globals() -> dict[str, str | dict]:
        anomalies: dict[str, str] = {}
        anomalies_file = os.path.join(config.DATA_DIR, 'anomalies.json')
        if os.path.exists(anomalies_file):
            try:
                with open(anomalies_file, 'r') as f:
                    anomalies = json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return {'app_version': __version__, 'integrity_anomalies': anomalies}

    return app
